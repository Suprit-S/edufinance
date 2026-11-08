"""Wallets, categories and transactions (TC-W01..W04, TC-T01..T08, TC-C01, TC-SEC04)."""

from decimal import Decimal

from app.models import RateSource
from app.services.transaction_service import combine_sources

from .conftest import category_id, make_wallet


def _txn(client, headers, **overrides):
    payload = {
        "kind": "EXPENSE",
        "category_id": category_id(client, headers, overrides.pop("category", "Groceries")),
        "amount": "41.20",
        "txn_date": "2026-11-03",
        "note": "Lidl",
        **overrides,
    }
    return client.post("/api/transactions", json=payload, headers=headers)


def test_tc_w01_balance_follows_transactions(client, auth):
    wallet = make_wallet(client, auth)
    _txn(client, auth, wallet_id=wallet["id"])
    _txn(
        client,
        auth,
        wallet_id=wallet["id"],
        kind="INCOME",
        category="Part-time salary",
        amount="250",
    )
    body = client.get(f"/api/wallets/{wallet['id']}", headers=auth).get_json()
    assert body["balance"] == "708.80"


def test_tc_w02_wallet_rules(client, auth):
    wallet = make_wallet(client, auth)
    dup = client.post(
        "/api/wallets",
        json={
            **{k: wallet[k] for k in ("currency_code", "wallet_type", "opening_date")},
            "name": "daily spending",
        },
        headers=auth,
    )
    assert dup.status_code == 409
    _txn(client, auth, wallet_id=wallet["id"])
    change = client.patch(
        f"/api/wallets/{wallet['id']}", json={"currency_code": "INR"}, headers=auth
    )
    assert change.status_code == 422
    assert client.delete(f"/api/wallets/{wallet['id']}", headers=auth).status_code == 409
    archived = client.patch(
        f"/api/wallets/{wallet['id']}", json={"is_archived": True}, headers=auth
    )
    assert archived.status_code == 200 and archived.get_json()["is_archived"]
    blocked = _txn(client, auth, wallet_id=wallet["id"])
    assert blocked.status_code == 422


def test_tc_w03_empty_wallet_can_be_deleted(client, auth):
    wallet = make_wallet(client, auth, name="Cash", wallet_type="CASH")
    assert client.delete(f"/api/wallets/{wallet['id']}", headers=auth).status_code == 204
    assert client.get("/api/wallets", headers=auth).get_json() == []


def test_tc_t01_inr_expense_uses_live_rate(client, auth, api_rates):
    from datetime import date

    api_rates()
    wallet = make_wallet(
        client, auth, name="Home Account", currency_code="INR", opening_balance="200000"
    )
    res = _txn(
        client,
        auth,
        wallet_id=wallet["id"],
        category="Language test",
        amount="2000",
        txn_date=date.today().isoformat(),
    )
    assert res.status_code == 201, res.get_json()
    body = res.get_json()
    assert body["amount_base"] == "18.80"  # 2000 x 0.00939891
    assert body["amount_home"] == "2000.00"
    assert body["rate_source"] == "LIVE" and body["estimated"] is False


def test_tc_t02_user_rate_overrides_market(client, auth, api_rates):
    api_rates()
    wallet = make_wallet(client, auth, name="Home Account", currency_code="INR")
    res = _txn(client, auth, wallet_id=wallet["id"], amount="2000", rate_to_base="0.0100")
    body = res.get_json()
    assert body["amount_base"] == "20.00"
    assert body["rate_to_base"] == "0.01000000"
    assert body["rate_source"] == "USER"


def test_tc_t03_rate_stays_frozen_when_market_changes(client, auth, api_rates):
    from datetime import date

    from app.extensions import db
    from app.models import FxRate

    api_rates()
    wallet = make_wallet(client, auth, name="Home Account", currency_code="INR")
    txn = _txn(
        client, auth, wallet_id=wallet["id"], amount="2000", txn_date=date.today().isoformat()
    ).get_json()
    for row in FxRate.query.filter_by(rate_date=date.today()).all():
        row.rate = row.rate * 2
    db.session.commit()
    again = client.get(f"/api/transactions/{txn['id']}", headers=auth).get_json()
    assert again["amount_base"] == "18.80"


def test_tc_t04_invalid_amounts_and_categories(client, auth):
    wallet = make_wallet(client, auth)
    for amount in ("-5", "0", "abc"):
        res = _txn(client, auth, wallet_id=wallet["id"], amount=amount)
        assert res.status_code == 422, amount
    wrong_kind = _txn(client, auth, wallet_id=wallet["id"], kind="INCOME")
    assert wrong_kind.status_code == 422
    assert "category_id" in wrong_kind.get_json()["error"]["details"]


def test_tc_t05_combined_rate_source():
    assert combine_sources(RateSource.IDENTITY, RateSource.LIVE) == RateSource.LIVE
    assert combine_sources(RateSource.USER, RateSource.LIVE) == RateSource.USER
    assert combine_sources(RateSource.USER, RateSource.FALLBACK) == RateSource.FALLBACK
    assert combine_sources(RateSource.IDENTITY, RateSource.IDENTITY) == RateSource.IDENTITY


def test_tc_t06_eur_expense_gets_home_value(client, auth, api_rates):
    from datetime import date

    api_rates()
    wallet = make_wallet(client, auth)
    body = _txn(
        client, auth, wallet_id=wallet["id"], amount="100", txn_date=date.today().isoformat()
    ).get_json()
    assert body["amount_base"] == "100.00"
    assert body["amount_home"] == "10639.53"
    assert body["rate_source"] == "LIVE"


def test_tc_t07_edit_keeps_frozen_rate(client, auth, api_rates):
    api_rates()
    wallet = make_wallet(client, auth, name="Home Account", currency_code="INR")
    txn = _txn(
        client, auth, wallet_id=wallet["id"], amount="2000", rate_to_base="0.0100"
    ).get_json()
    res = client.patch(
        f"/api/transactions/{txn['id']}", json={"amount": "3000", "note": "IELTS"}, headers=auth
    )
    body = res.get_json()
    assert body["amount_base"] == "30.00" and body["note"] == "IELTS"
    res = client.patch(
        f"/api/transactions/{txn['id']}", json={"rate_to_base": "0.0095"}, headers=auth
    )
    assert res.get_json()["amount_base"] == "28.50"
    assert client.delete(f"/api/transactions/{txn['id']}", headers=auth).status_code == 204


def test_tc_t08_list_filters_and_pagination(client, auth):
    wallet = make_wallet(client, auth)
    for i in range(3):
        _txn(client, auth, wallet_id=wallet["id"], txn_date=f"2026-11-0{i + 1}", note=f"Shop {i}")
    _txn(
        client,
        auth,
        wallet_id=wallet["id"],
        kind="INCOME",
        category="Scholarship",
        amount="300",
        note="DAAD",
    )
    page = client.get("/api/transactions?per_page=2", headers=auth).get_json()
    assert page["total"] == 4 and len(page["items"]) == 2
    assert page["items"][0]["txn_date"] >= page["items"][1]["txn_date"]
    income = client.get("/api/transactions?kind=INCOME", headers=auth).get_json()
    assert [t["note"] for t in income["items"]] == ["DAAD"]
    found = client.get("/api/transactions?q=shop 1", headers=auth).get_json()
    assert found["total"] == 1
    bad = client.get("/api/transactions?page=0", headers=auth)
    assert bad.status_code == 422


def test_tc_c01_custom_categories(client, auth):
    res = client.post(
        "/api/categories",
        json={"name": "Badminton club", "kind": "EXPENSE", "group_name": "Lifestyle"},
        headers=auth,
    )
    assert res.status_code == 201
    dup = client.post(
        "/api/categories", json={"name": "groceries", "kind": "EXPENSE"}, headers=auth
    )
    assert dup.status_code == 409
    system = category_id(client, auth, "Rent")
    assert client.delete(f"/api/categories/{system}", headers=auth).status_code == 409
    assert client.delete(f"/api/categories/{res.get_json()['id']}", headers=auth).status_code == 204
    incomes = client.get("/api/categories?kind=INCOME", headers=auth).get_json()
    assert all(c["kind"] == "INCOME" for c in incomes)


def test_tc_sec04_users_cannot_see_each_others_data(client, register):
    alice, _ = register()
    bob, _ = register(email="bob@example.com", full_name="Bob Lee")
    wallet = make_wallet(client, alice)
    txn = _txn(client, alice, wallet_id=wallet["id"]).get_json()
    custom = client.post(
        "/api/categories", json={"name": "Private", "kind": "EXPENSE"}, headers=alice
    ).get_json()

    assert client.get(f"/api/wallets/{wallet['id']}", headers=bob).status_code == 404
    assert (
        client.patch(f"/api/wallets/{wallet['id']}", json={"name": "x"}, headers=bob).status_code
        == 404
    )
    assert client.get(f"/api/transactions/{txn['id']}", headers=bob).status_code == 404
    assert client.delete(f"/api/transactions/{txn['id']}", headers=bob).status_code == 404
    assert client.get("/api/transactions", headers=bob).get_json()["total"] == 0
    assert client.get("/api/wallets", headers=bob).get_json() == []
    names = [c["name"] for c in client.get("/api/categories", headers=bob).get_json()]
    assert "Private" not in names
    # Bob cannot book into Alice's wallet or use her category or phase
    bob_wallet = make_wallet(client, bob)
    res = _txn(client, bob, wallet_id=wallet["id"])
    assert res.status_code == 404
    res = client.post(
        "/api/transactions",
        json={
            "kind": "EXPENSE",
            "wallet_id": bob_wallet["id"],
            "category_id": custom["id"],
            "amount": "1",
            "txn_date": "2026-11-01",
        },
        headers=bob,
    )
    assert res.status_code == 404
    alice_phase = client.get("/api/phases", headers=alice).get_json()[0]["id"]
    res = _txn(client, bob, wallet_id=bob_wallet["id"], phase_id=alice_phase)
    assert res.status_code == 404
    assert Decimal(
        client.get(f"/api/wallets/{wallet['id']}", headers=alice).get_json()["balance"]
    ) == Decimal("458.80")
