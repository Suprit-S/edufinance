"""Accounts: registration, login, logout, password and profile (FR-01 to FR-06).

Passwords are only ever stored as salted bcrypt hashes (NFR-04, ADR-0009).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import bcrypt
from sqlalchemy import func, select

from app.errors import ApiError, Conflict
from app.extensions import db
from app.models import RevokedToken, User

from . import phase_service

GENERIC_LOGIN_ERROR = "E-mail or password is incorrect."
PROFILE_FIELDS = (
    "full_name",
    "date_of_birth",
    "gender",
    "home_currency",
    "base_currency",
    "destination_country",
    "planning_start_date",
    "arrival_date",
    "study_start_date",
    "study_end_date",
    "settling_in_days",
)
PHASE_FIELDS = {
    "planning_start_date",
    "arrival_date",
    "study_start_date",
    "study_end_date",
    "settling_in_days",
}


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Validation shared by registration and profile edit
# ---------------------------------------------------------------------------
def validate_dates(values: dict) -> None:
    """Plausible order of journey dates (FR-02). Raises 422 with field errors."""
    errors: dict[str, list[str]] = {}
    planning, arrival = values["planning_start_date"], values["arrival_date"]
    start, end = values["study_start_date"], values["study_end_date"]
    dob = values.get("date_of_birth")
    if arrival < planning:
        errors["arrival_date"] = ["Arrival cannot be before you started planning."]
    if end <= start:
        errors["study_end_date"] = ["Study end must be after study start."]
    if arrival > end:
        errors.setdefault("arrival_date", []).append("Arrival must be before your study ends.")
    if dob is not None and dob >= planning:
        errors["date_of_birth"] = ["Date of birth must be before your planning start."]
    if errors:
        raise ApiError("Please check your dates.", 422, "VALIDATION_ERROR", errors)


def _email_taken(email: str, exclude: uuid.UUID | None = None) -> bool:
    stmt = select(User.id).where(func.lower(User.email) == email.lower())
    if exclude:
        stmt = stmt.where(User.id != exclude)
    return db.session.scalar(stmt) is not None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def register(data: dict, settling_in_default: int = 60) -> User:
    """Create a user and the four system phases (FR-01, FR-07)."""
    email = data["email"].strip().lower()
    if _email_taken(email):
        raise Conflict("An account with this e-mail already exists.")
    values = {k: data.get(k) for k in PROFILE_FIELDS}
    if values["settling_in_days"] is None:
        values["settling_in_days"] = settling_in_default
    validate_dates(values)
    user = User(email=email, password_hash=hash_password(data["password"]), **values)
    db.session.add(user)
    db.session.flush()
    phase_service.create_system_phases(user)
    return user


def authenticate(email: str, password: str) -> User:
    """Return the user for valid credentials; one generic error otherwise, so
    the response does not reveal whether the e-mail exists."""
    user = db.session.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))
    if user is None or not check_password(password, user.password_hash):
        raise ApiError(GENERIC_LOGIN_ERROR, 401, "INVALID_CREDENTIALS")
    return user


def revoke_token(jti: str, user_id: uuid.UUID, expires_ts: int) -> None:
    """Logout: the token's id is stored and rejected from now on (NFR-05)."""
    if db.session.get(RevokedToken, jti) is None:
        db.session.add(
            RevokedToken(
                jti=jti,
                user_id=user_id,
                expires_at=datetime.fromtimestamp(expires_ts, tz=UTC),
            )
        )
    # Housekeeping: expired entries are no longer needed.
    db.session.execute(db.delete(RevokedToken).where(RevokedToken.expires_at < datetime.now(UTC)))
    db.session.flush()


def change_password(user: User, current: str, new: str) -> None:
    if not check_password(current, user.password_hash):
        raise ApiError(
            "Current password is incorrect.",
            422,
            "VALIDATION_ERROR",
            {"current_password": ["Incorrect password."]},
        )
    user.password_hash = hash_password(new)
    db.session.flush()


def update_profile(user: User, data: dict) -> User:
    """Change profile data. When journey dates change, system phases and
    automatic transaction phases follow (FR-05, FR-10)."""
    if "email" in data:
        email = data["email"].strip().lower()
        if _email_taken(email, exclude=user.id):
            raise Conflict("An account with this e-mail already exists.")
        user.email = email
    merged = {k: data.get(k, getattr(user, k)) for k in PROFILE_FIELDS}
    validate_dates(merged)
    for key in PROFILE_FIELDS:
        if key in data:
            setattr(user, key, data[key])
    db.session.flush()
    if PHASE_FIELDS & data.keys():
        phase_service.sync_system_phases(user)
    return user
