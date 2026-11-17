"""Runway and burn rate (TC-RW01..RW04)."""

from datetime import date, timedelta
from decimal import Decimal

from app.services.runway_service import classify, compute_runway

from .conftest import category_id, make_wallet


def test_tc_rw01_runway_from_balance_and_spending():
    r = compute_runway(Decimal("613.79"), Decimal("1150"))
    assert r.burn_rate == Decimal("38.33") and r.days == 16 and r.status == "CRITICAL"


def test_tc_rw02_no_spending_is_unlimited():
    r = compute_runway(Decimal("500"), Decimal("0"))
    assert r.days is None and r.status == "HEALTHY"
    assert compute_runway(Decimal("-5"), Decimal("100")).days == 0


def test_tc_rw03_status_boundaries():
    assert [classify(d) for d in (91, 90, 60, 59, 30, 29, 0)] == [
        "HEALTHY",
        "OK",
        "OK",
        "WARNING",
        "WARNING",
        "CRITICAL",
        "CRITICAL",
    ]


def test_tc_rw04_wallet_endpoint_counts_only_expenses(client, auth):
    daily = make_wallet(client, auth, opening_balance="1763.79")
    savings = make_wallet(client, auth, name="Savings", wallet_type="SAVINGS", opening_balance="0")
    today = date.today()
    for days_ago, amount in ((2, "800"), (20, "350"), (40, "999")):  # 40 days: outside window
        client.post(
            "/api/transactions",
            json={
                "kind": "EXPENSE",
                "wallet_id": daily["id"],
                "category_id": category_id(client, auth, "Rent"),
                "amount": amount,
                "txn_date": (today - timedelta(days=days_ago)).isoformat(),
            },
            headers=auth,
        )
    client.post(
        "/api/remittances",
        json={
            "from_wallet_id": daily["id"],
            "to_wallet_id": savings["id"],
            "sent_amount": "1",
            "received_amount": "1",
            "remit_date": today.isoformat(),
        },
        headers=auth,
    )
    body = client.get(f"/api/wallets/{daily['id']}", headers=auth).get_json()
    # balance 1763.79 - 800 - 350 - 999 - 1 = -386.21 -> 0 days
    assert body["runway"]["spent_last_window"] == "1150.00"
    assert body["runway"]["burn_rate_per_day"] == "38.33"
    assert body["runway"]["days"] == 0 and body["runway"]["status"] == "CRITICAL"
    listing = {w["name"]: w["runway"] for w in client.get("/api/wallets", headers=auth).get_json()}
    assert listing["Savings"]["days"] is None and listing["Savings"]["status"] == "HEALTHY"
