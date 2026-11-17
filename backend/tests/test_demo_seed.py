"""Demo data seed (TC-DEMO01)."""

from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import Transaction, User
from app.seed.demo_data import DEMO_EMAIL, seed_demo


def test_tc_demo01_seed_is_realistic_and_idempotent(app, client):
    today = date(2026, 11, 10)
    msg = seed_demo(today=today)
    assert "created" in msg
    assert "already exists" in seed_demo(today=today)
    count = db.session.query(Transaction).count()
    seed_demo(reset=True, today=today)
    assert db.session.query(Transaction).count() == count  # recreated, no duplicates
    assert db.session.query(User).filter_by(email=DEMO_EMAIL).count() == 1

    token = client.post(
        "/api/auth/login", json={"email": DEMO_EMAIL, "password": "Demo#2026"}
    ).get_json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    wallets = {w["name"]: w for w in client.get("/api/wallets", headers=h).get_json()}
    assert all(Decimal(w["balance"]) >= 0 for w in wallets.values())
    assert wallets["Blocked Account"]["is_archived"]
    assert count > 250
    # no estimated rates in the demo: every day has a stored rate
    items = client.get("/api/transactions?per_page=200", headers=h).get_json()["items"]
    assert not any(t["estimated"] for t in items)
    costs = client.get("/api/reports/costs", headers=h).get_json()
    assert Decimal(costs["going_abroad"]["total"]) > 3000
    loans = client.get("/api/loans", headers=h).get_json()
    sbi = next(loan for loan in loans if loan["name"] == "SBI education loan")
    assert sbi["affordability"] is not None
    assert {p["phase_type"] for p in client.get("/api/phases", headers=h).get_json()} >= {
        "PRE_DEPARTURE",
        "SETTLING_IN",
        "STUDY",
        "WORK",
    }
