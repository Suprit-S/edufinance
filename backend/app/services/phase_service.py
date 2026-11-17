"""Life phases: creation from profile dates, assignment of transactions (ADR-0005).

Phase rules
-----------
* System phases are derived from the profile and kept in sync with it:
  PRE_DEPARTURE  planning start  -> day before arrival
  SETTLING_IN    arrival         -> arrival + settling_in_days - 1
  STUDY          study start     -> study end
  WORK           day after study end -> open-ended
* A date can fall into several phases (Settling in lies inside Study). The
  **shortest** phase wins because it is the most specific; open-ended phases
  count as infinitely long. Ties: later start, then sort order.
* A date outside every phase belongs to the closest phase that started
  before it, or - if it is before all phases - to the first phase.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select

from app.errors import ApiError, NotFound
from app.extensions import db
from app.models import LifePhase, PhaseType, Transaction, User

SYSTEM_ORDER = {
    PhaseType.PRE_DEPARTURE: 10,
    PhaseType.SETTLING_IN: 20,
    PhaseType.STUDY: 30,
    PhaseType.JOB_SEARCH: 40,
    PhaseType.WORK: 50,
    PhaseType.CUSTOM: 60,
}

DEFAULT_NAMES = {
    PhaseType.PRE_DEPARTURE: "Pre-departure",
    PhaseType.SETTLING_IN: "Settling in",
    PhaseType.STUDY: "Study",
    PhaseType.WORK: "Work",
}

CUSTOM_TYPES = {PhaseType.JOB_SEARCH, PhaseType.CUSTOM}


@dataclass(frozen=True)
class PhaseSpan:
    """Minimal phase view used by the pure assignment function."""

    id: uuid.UUID
    start: date
    end: date | None
    sort_order: int = 0

    def contains(self, d: date) -> bool:
        return self.start <= d and (self.end is None or d <= self.end)

    @property
    def length_days(self) -> float:
        return float("inf") if self.end is None else (self.end - self.start).days


# ---------------------------------------------------------------------------
# Pure functions (no database) - unit-tested directly
# ---------------------------------------------------------------------------
def system_phase_dates(
    planning_start: date,
    arrival: date,
    study_start: date,
    study_end: date,
    settling_in_days: int,
) -> dict[PhaseType, tuple[date, date | None]]:
    """Start/end dates of the four system phases (TC-PH01)."""
    pre_end = max(planning_start, arrival - timedelta(days=1))
    settling_end = arrival + timedelta(days=max(settling_in_days, 1) - 1)
    return {
        PhaseType.PRE_DEPARTURE: (planning_start, pre_end),
        PhaseType.SETTLING_IN: (arrival, settling_end),
        PhaseType.STUDY: (study_start, study_end),
        PhaseType.WORK: (study_end + timedelta(days=1), None),
    }


def phase_for_date(phases: list[PhaseSpan], d: date) -> uuid.UUID:
    """Return the id of the phase a date belongs to (FR-09)."""
    if not phases:
        raise ValueError("User has no phases.")
    matching = [p for p in phases if p.contains(d)]
    if matching:
        best = min(matching, key=lambda p: (p.length_days, -p.start.toordinal(), p.sort_order))
        return best.id
    before = [p for p in phases if p.start <= d]
    if before:
        return max(before, key=lambda p: (p.start, -p.sort_order)).id
    return min(phases, key=lambda p: (p.start, p.sort_order)).id


def progress_in_phase(start: date, end: date | None, today: date) -> int | None:
    """Percentage of a phase that has passed (0-100); None for open-ended phases."""
    if end is None:
        return None
    total = (end - start).days + 1
    done = (min(max(today, start - timedelta(days=1)), end) - start).days + 1
    return max(0, min(100, round(done * 100 / total)))


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------
def _spans(user_id: uuid.UUID) -> list[PhaseSpan]:
    rows = db.session.scalars(select(LifePhase).where(LifePhase.user_id == user_id)).all()
    return [PhaseSpan(p.id, p.start_date, p.end_date, p.sort_order) for p in rows]


def create_system_phases(user: User) -> list[LifePhase]:
    """Create the four system phases for a new user (FR-07)."""
    dates = system_phase_dates(
        user.planning_start_date,
        user.arrival_date,
        user.study_start_date,
        user.study_end_date,
        user.settling_in_days,
    )
    phases = []
    for phase_type, (start, end) in dates.items():
        phase = LifePhase(
            user_id=user.id,
            phase_type=phase_type,
            name=DEFAULT_NAMES[phase_type],
            start_date=start,
            end_date=end,
            is_system=True,
            sort_order=SYSTEM_ORDER[phase_type],
        )
        db.session.add(phase)
        phases.append(phase)
    db.session.flush()
    return phases


def sync_system_phases(user: User) -> None:
    """Update system phase dates after profile dates changed, then re-assign
    automatic transactions (FR-10). Names chosen by the user are kept."""
    dates = system_phase_dates(
        user.planning_start_date,
        user.arrival_date,
        user.study_start_date,
        user.study_end_date,
        user.settling_in_days,
    )
    existing = {
        p.phase_type: p
        for p in db.session.scalars(
            select(LifePhase).where(LifePhase.user_id == user.id, LifePhase.is_system.is_(True))
        )
    }
    for phase_type, (start, end) in dates.items():
        phase = existing.get(phase_type)
        if phase is None:  # recreated if it was somehow missing
            phase = LifePhase(
                user_id=user.id,
                phase_type=phase_type,
                name=DEFAULT_NAMES[phase_type],
                is_system=True,
                sort_order=SYSTEM_ORDER[phase_type],
            )
            db.session.add(phase)
        phase.start_date, phase.end_date = start, end
    db.session.flush()
    reassign_transactions(user.id)


def assign_phase(user_id: uuid.UUID, d: date) -> uuid.UUID:
    return phase_for_date(_spans(user_id), d)


def reassign_transactions(user_id: uuid.UUID) -> int:
    """Re-assign all automatic (non-manual) transactions. Returns rows changed."""
    spans = _spans(user_id)
    rows = db.session.execute(
        select(Transaction.id, Transaction.txn_date, Transaction.phase_id).where(
            Transaction.user_id == user_id, Transaction.phase_is_manual.is_(False)
        )
    ).all()
    changes = []
    for txn_id, txn_date, current in rows:
        target = phase_for_date(spans, txn_date)
        if target != current:
            changes.append({"id": txn_id, "phase_id": target})
    if changes:
        db.session.execute(db.update(Transaction), changes)
    return len(changes)


def get_phase(user_id: uuid.UUID, phase_id: uuid.UUID) -> LifePhase:
    phase = db.session.get(LifePhase, phase_id)
    if phase is None or phase.user_id != user_id:
        raise NotFound("Phase")
    return phase


def create_custom_phase(user_id: uuid.UUID, data: dict) -> LifePhase:
    """Add a user-defined phase such as *Job search* (FR-08)."""
    phase_type = data.get("phase_type", PhaseType.CUSTOM)
    if phase_type not in CUSTOM_TYPES:
        raise ApiError("Only 'Job search' or custom phases can be added.", 422, "VALIDATION_ERROR")
    phase = LifePhase(
        user_id=user_id,
        phase_type=phase_type,
        name=data["name"],
        start_date=data["start_date"],
        end_date=data.get("end_date"),
        is_system=False,
        sort_order=SYSTEM_ORDER[phase_type],
    )
    db.session.add(phase)
    db.session.flush()
    reassign_transactions(user_id)
    return phase


def update_phase(user_id: uuid.UUID, phase_id: uuid.UUID, data: dict) -> LifePhase:
    """Rename any phase; change dates of custom phases. Dates of system phases
    come from the profile (single source of truth, ADR-0005)."""
    phase = get_phase(user_id, phase_id)
    if "name" in data:
        phase.name = data["name"]
    if phase.is_system and ({"start_date", "end_date"} & data.keys()):
        raise ApiError(
            "Dates of this phase come from your profile. Change your study dates instead.",
            422,
            "VALIDATION_ERROR",
            {"start_date": ["Edit the dates in your profile."]},
        )
    if "start_date" in data:
        phase.start_date = data["start_date"]
    if "end_date" in data:
        phase.end_date = data["end_date"]
    if phase.end_date is not None and phase.end_date < phase.start_date:
        raise ApiError(
            "End date must not be before start date.",
            422,
            "VALIDATION_ERROR",
            {"end_date": ["Must not be before the start date."]},
        )
    db.session.flush()
    reassign_transactions(user_id)
    return phase


def delete_phase(user_id: uuid.UUID, phase_id: uuid.UUID) -> None:
    """Delete a custom phase. Its transactions (also manual ones) are assigned
    automatically again."""
    phase = get_phase(user_id, phase_id)
    if phase.is_system:
        raise ApiError("System phases cannot be deleted.", 409, "CONFLICT")
    remaining = [s for s in _spans(user_id) if s.id != phase.id]
    rows = db.session.execute(
        select(Transaction.id, Transaction.txn_date).where(Transaction.phase_id == phase.id)
    ).all()
    if rows:
        db.session.execute(
            db.update(Transaction),
            [
                {"id": tid, "phase_id": phase_for_date(remaining, d), "phase_is_manual": False}
                for tid, d in rows
            ],
        )
    db.session.delete(phase)
    db.session.flush()
    reassign_transactions(user_id)
