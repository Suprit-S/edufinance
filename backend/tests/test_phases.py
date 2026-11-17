"""Life phases (TC-PH01..PH08)."""

import uuid
from datetime import date

from app.services.phase_service import (
    PhaseSpan,
    phase_for_date,
    progress_in_phase,
    system_phase_dates,
)

from .conftest import category_id, make_wallet


def test_tc_ph01_system_phase_dates():
    dates = system_phase_dates(
        date(2025, 6, 1), date(2025, 9, 25), date(2025, 10, 1), date(2027, 9, 30), 60
    )
    assert [(s.isoformat(), e.isoformat() if e else None) for s, e in dates.values()] == [
        ("2025-06-01", "2025-09-24"),
        ("2025-09-25", "2025-11-23"),
        ("2025-10-01", "2027-09-30"),
        ("2027-10-01", None),
    ]


def _spans():
    pre, settle, study, work = (uuid.uuid4() for _ in range(4))
    spans = [
        PhaseSpan(pre, date(2025, 6, 1), date(2025, 9, 24)),
        PhaseSpan(settle, date(2025, 9, 25), date(2025, 11, 23)),
        PhaseSpan(study, date(2025, 10, 1), date(2027, 9, 30)),
        PhaseSpan(work, date(2027, 10, 1), None),
    ]
    return spans, pre, settle, study, work


def test_tc_ph02_date_in_pre_departure():
    spans, pre, *_ = _spans()
    assert phase_for_date(spans, date(2025, 8, 10)) == pre


def test_tc_ph03_overlap_shorter_phase_wins():
    spans, _, settle, study, work = _spans()
    assert phase_for_date(spans, date(2025, 10, 15)) == settle
    assert phase_for_date(spans, date(2025, 12, 1)) == study
    assert phase_for_date(spans, date(2031, 1, 1)) == work


def test_tc_ph05_dates_outside_all_phases():
    spans, pre, *_ = _spans()
    assert phase_for_date(spans, date(2024, 12, 1)) == pre  # before planning
    gap_a, gap_b = uuid.uuid4(), uuid.uuid4()
    gap = [
        PhaseSpan(gap_a, date(2025, 1, 1), date(2025, 1, 31)),
        PhaseSpan(gap_b, date(2025, 3, 1), date(2025, 3, 31)),
    ]
    assert phase_for_date(gap, date(2025, 2, 15)) == gap_a  # closest earlier phase


def test_tc_ph06_progress_percentage():
    assert progress_in_phase(date(2025, 10, 1), date(2025, 10, 10), date(2025, 10, 5)) == 50
    assert progress_in_phase(date(2025, 10, 1), date(2025, 10, 10), date(2025, 9, 1)) == 0
    assert progress_in_phase(date(2025, 10, 1), date(2025, 10, 10), date(2026, 1, 1)) == 100
    assert progress_in_phase(date(2025, 10, 1), None, date(2026, 1, 1)) is None


def _expense(client, headers, wallet_id, on, **extra):
    payload = {
        "kind": "EXPENSE",
        "wallet_id": wallet_id,
        "category_id": category_id(client, headers, "Groceries"),
        "amount": "10.00",
        "txn_date": on,
        **extra,
    }
    res = client.post("/api/transactions", json=payload, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def test_tc_ph04_moving_arrival_reassigns_only_automatic_transactions(client, auth):
    wallet = make_wallet(client, auth)
    phases = {p["phase_type"]: p for p in client.get("/api/phases", headers=auth).get_json()}
    auto = _expense(client, auth, wallet["id"], "2025-09-22")
    manual = _expense(client, auth, wallet["id"], "2025-09-22", phase_id=phases["STUDY"]["id"])
    assert auto["phase_name"] == "Pre-departure"

    res = client.patch("/api/me", json={"arrival_date": "2025-09-20"}, headers=auth)
    assert res.status_code == 200
    settle = next(p for p in res.get_json()["phases"] if p["phase_type"] == "SETTLING_IN")
    assert settle["start_date"] == "2025-09-20"

    auto_now = client.get(f"/api/transactions/{auto['id']}", headers=auth).get_json()
    manual_now = client.get(f"/api/transactions/{manual['id']}", headers=auth).get_json()
    assert auto_now["phase_name"] == "Settling in"
    assert manual_now["phase_name"] == "Study" and manual_now["phase_is_manual"]


def test_tc_ph07_custom_job_search_phase(client, auth):
    wallet = make_wallet(client, auth)
    txn = _expense(client, auth, wallet["id"], "2027-11-15")
    assert txn["phase_name"] == "Work"
    res = client.post(
        "/api/phases",
        json={
            "name": "Job search",
            "phase_type": "JOB_SEARCH",
            "start_date": "2027-10-01",
            "end_date": "2028-01-31",
        },
        headers=auth,
    )
    assert res.status_code == 201
    phase_id = res.get_json()["id"]
    moved = client.get(f"/api/transactions/{txn['id']}", headers=auth).get_json()
    assert moved["phase_name"] == "Job search"

    assert client.delete(f"/api/phases/{phase_id}", headers=auth).status_code == 204
    back = client.get(f"/api/transactions/{txn['id']}", headers=auth).get_json()
    assert back["phase_name"] == "Work"


def test_tc_ph08_system_phases_rename_only(client, auth):
    study = next(
        p for p in client.get("/api/phases", headers=auth).get_json() if p["phase_type"] == "STUDY"
    )
    ok = client.patch(f"/api/phases/{study['id']}", json={"name": "M.Sc. TU Munich"}, headers=auth)
    assert ok.status_code == 200 and ok.get_json()["name"] == "M.Sc. TU Munich"
    bad = client.patch(
        f"/api/phases/{study['id']}", json={"start_date": "2025-11-01"}, headers=auth
    )
    assert bad.status_code == 422
    assert client.delete(f"/api/phases/{study['id']}", headers=auth).status_code == 409
    invalid = client.post(
        "/api/phases",
        json={"name": "X", "phase_type": "STUDY", "start_date": "2026-01-01"},
        headers=auth,
    )
    assert invalid.status_code == 422
