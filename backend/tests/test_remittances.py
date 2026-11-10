"""Remittances (TC-R01..R07)."""

from decimal import Decimal

from app.services.remittance_service import effective_rate, side_rates, transfer_maths

from .conftest import category_id, make_wallet


def _wallets(client, auth):
    home = make_wallet(
        client, auth, name="Home Account", currency_code="INR", opening_balance="200000"
    )
    daily = make_wallet(
        client, auth, name="Daily Spending", currency_code="EUR", opening_balance="100"
    )
    return home, daily


def _remit(client, auth, **payload):
    payload.setdefault("remit_date", __import__("datetime").date.today().isoformat())
    return client.post("/api/remittances", json=payload, headers=auth)


def _txns(client, auth, remittance_id):
    items = client.get("/api/transactions?per_page=200", headers=auth).get_json()["items"]
    return [t for t in items if t["remittance_id"] == remittance_id]


def test_tc_r01_effective_rate_and_frozen_user_rates(client, auth, api_rates):
    api_rates(eur="0.963", inr="90")  # market INR->EUR = 0.0107
    home, daily = _wallets(client, auth)
    res = _remit(
        client,
        auth,
        from_wallet_id=home["id"],
        to_wallet_id=daily["id"],
        sent_amount="50000",
        received_amount="520",
        provider="Wise",
    )
    assert res.status_code == 201, res.get_json()
    rem = res.get_json()
    assert rem["effective_rate"] == "0.01040000" and rem["direction"] == "OWN"
    txns = {t["kind"]: t for t in _txns(client, auth, rem["id"])}
    out, inn = txns["TRANSFER_OUT"], txns["TRANSFER_IN"]
    assert out["amount"] == "50000.00" and out["amount_base"] == "520.00"
    assert out["rate_source"] == "USER"
    assert inn["amount"] == "520.00" and inn["amount_home"] == "50000.00"
    assert inn["rate_to_home"] == "96.15384615"
    wallets = client.get("/api/wallets", headers=auth).get_json()
    balances = {w["name"]: w["balance"] for w in wallets}
    assert balances == {"Home Account": "150000.00", "Daily Spending": "620.00"}


def test_tc_r02_hidden_cost_with_fee(client, auth, api_rates):
    api_rates(eur="0.963", inr="90")
    home, daily = _wallets(client, auth)
    rem = _remit(
        client,
        auth,
        from_wallet_id=home["id"],
        to_wallet_id=daily["id"],
        sent_amount="50000",
        received_amount="520",
    ).get_json()
    assert rem["market_rate"] == "0.01070000"
    assert rem["hidden_cost_base"] == "15.00"  # 50,000 x 0.0107 - 520
    with_fee = _remit(
        client,
        auth,
        from_wallet_id=home["id"],
        to_wallet_id=daily["id"],
        sent_amount="50000",
        received_amount="520",
        fee_amount="100",
    ).get_json()
    assert with_fee["hidden_cost_base"] == "16.07"  # + 100 x 0.0107
    fee = [t for t in _txns(client, auth, with_fee["id"]) if t["kind"] == "EXPENSE"]
    assert fee[0]["category_name"] == "Transfer fees" and fee[0]["amount"] == "100.00"
    listing = client.get("/api/remittances", headers=auth).get_json()
    assert listing["summary"]["hidden_cost_total"] == "31.07"


def test_tc_r03_money_from_family_is_income(client, auth):
    _, daily = _wallets(client, auth)
    rem = _remit(
        client,
        auth,
        to_wallet_id=daily["id"],
        sent_currency="INR",
        sent_amount="25000",
        received_amount="250",
        note="From Appa",
    ).get_json()
    assert rem["direction"] == "IN"
    (txn,) = _txns(client, auth, rem["id"])
    assert txn["kind"] == "INCOME" and txn["category_name"] == "Family support"
    assert txn["amount_home"] == "25000.00" and txn["rate_source"] == "USER"


def test_tc_r04_money_sent_home_is_expense(client, auth):
    _, daily = _wallets(client, auth)
    rem = _remit(
        client,
        auth,
        from_wallet_id=daily["id"],
        received_currency="INR",
        sent_amount="100",
        received_amount="9500",
    ).get_json()
    (txn,) = _txns(client, auth, rem["id"])
    assert txn["kind"] == "EXPENSE" and txn["category_name"] == "Gifts & family"
    assert txn["rate_to_home"] == "95.00000000" and txn["amount_home"] == "9500.00"


def test_tc_r05_same_currency_transfer_between_own_wallets(client, auth):
    _, daily = _wallets(client, auth)
    savings = make_wallet(client, auth, name="Savings", wallet_type="SAVINGS", opening_balance="0")
    rem = _remit(
        client,
        auth,
        from_wallet_id=daily["id"],
        to_wallet_id=savings["id"],
        sent_amount="60",
        received_amount="60",
    ).get_json()
    assert rem["effective_rate"] == "1.00000000" and rem["hidden_cost_base"] == "0.00"
    kinds = sorted(t["kind"] for t in _txns(client, auth, rem["id"]))
    assert kinds == ["TRANSFER_IN", "TRANSFER_OUT"]


def test_tc_r06_validation(client, auth):
    home, daily = _wallets(client, auth)
    none = _remit(
        client,
        auth,
        sent_currency="INR",
        received_currency="EUR",
        sent_amount="1",
        received_amount="1",
    )
    assert none.status_code == 422
    same = _remit(
        client,
        auth,
        from_wallet_id=daily["id"],
        to_wallet_id=daily["id"],
        sent_amount="1",
        received_amount="1",
    )
    assert same.status_code == 422
    fee = _remit(
        client,
        auth,
        to_wallet_id=daily["id"],
        sent_currency="INR",
        sent_amount="1000",
        received_amount="10",
        fee_amount="5",
    )
    assert "fee_amount" in fee.get_json()["error"]["details"]
    no_ccy = _remit(
        client, auth, to_wallet_id=daily["id"], sent_amount="1000", received_amount="10"
    )
    assert "sent_currency" in no_ccy.get_json()["error"]["details"]
    wrong_cat = _remit(
        client,
        auth,
        to_wallet_id=daily["id"],
        sent_currency="INR",
        sent_amount="1000",
        received_amount="10",
        category_id=category_id(client, auth, "Rent"),
    )
    assert wrong_cat.status_code == 422
    zero = _remit(
        client,
        auth,
        from_wallet_id=home["id"],
        to_wallet_id=daily["id"],
        sent_amount="0",
        received_amount="10",
    )
    assert zero.status_code == 422


def test_tc_r07_delete_removes_transactions_and_linked_are_read_only(client, auth):
    home, daily = _wallets(client, auth)
    rem = _remit(
        client,
        auth,
        from_wallet_id=home["id"],
        to_wallet_id=daily["id"],
        sent_amount="10000",
        received_amount="100",
        fee_amount="50",
    ).get_json()
    txn = _txns(client, auth, rem["id"])[0]
    assert (
        client.patch(f"/api/transactions/{txn['id']}", json={"note": "x"}, headers=auth).status_code
        == 409
    )
    assert client.delete(f"/api/transactions/{txn['id']}", headers=auth).status_code == 409
    assert client.delete(f"/api/remittances/{rem['id']}", headers=auth).status_code == 204
    assert _txns(client, auth, rem["id"]) == []
    wallets = client.get("/api/wallets", headers=auth).get_json()
    balances = {w["name"]: w["balance"] for w in wallets}
    assert balances == {"Home Account": "200000.00", "Daily Spending": "100.00"}
    assert client.get(f"/api/remittances/{rem['id']}", headers=auth).status_code == 404


def test_pure_helpers():
    assert effective_rate("50000", "520") == Decimal("0.01040000")
    maths = transfer_maths("50000", "520", None)
    assert maths.hidden_cost_received is None
    assert side_rates("INR", "EUR", Decimal("0.0104"), "EUR", "INR") == (Decimal("0.0104"), None)
    assert side_rates("USD", "GBP", Decimal("0.75"), "EUR", "INR") == (None, None)
