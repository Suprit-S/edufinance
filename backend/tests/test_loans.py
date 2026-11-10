"""Loan Planner (TC-L01..L10)."""

from datetime import date
from decimal import Decimal

from app.services.loan_service import (
    affordability_verdict,
    monthly_interest,
    part_payment_effect,
    simulate,
    split_emi,
)
from app.services.plan_service import add_months

from .conftest import category_id, make_wallet

TODAY = date.today()


def _loan(client, auth, **extra):
    payload = {
        "name": "SBI education loan",
        "lender": "SBI",
        "currency_code": "INR",
        "annual_rate_pct": "8.5",
        "sanctioned_amount": "850000",
        "outstanding_amount": "520000",
        "emi_amount": "14000",
        **extra,
    }
    res = client.post("/api/loans", json=payload, headers=auth)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def _pay(client, auth, loan_id, **payload):
    payload.setdefault("payment_type", "EMI")
    payload.setdefault("paid_on", TODAY.isoformat())
    return client.post(f"/api/loans/{loan_id}/payments", json=payload, headers=auth)


# --- pure formulas ---------------------------------------------------------
def test_tc_l01_emi_split():
    assert monthly_interest("100000", "12") == Decimal("1000.00")
    assert split_emi("100000", "12", "10000") == (Decimal("1000.00"), Decimal("9000.00"))
    # payment smaller than the interest only pays interest
    assert split_emi("100000", "12", "500") == (Decimal("500.00"), Decimal("0.00"))


def test_tc_l02_payoff_simulation():
    sim = simulate("100000", "12", "10000", keep_schedule=True)
    assert sim.months == 11
    assert sim.total_interest == Decimal("5898.48")
    assert sim.schedule[0] == {
        "month": 1,
        "payment": "10000.00",
        "interest": "1000.00",
        "principal": "9000.00",
        "balance": "91000.00",
    }
    assert sim.schedule[-1]["balance"] == "0.00"
    assert simulate("100000", "12", "1000").months is None  # EMI = interest: never ends
    assert simulate("0", "12", "1000").months == 0


def test_tc_l03_part_payment_effect():
    saved, emis = part_payment_effect("100000", "12", "10000", "20000")
    assert saved == Decimal("2088.94")  # 5,898.48 - 3,809.54
    assert emis == 2


def test_tc_l06_l07_affordability_verdict():
    ok = affordability_verdict("300", "0.20", "94.05")
    assert ok["status"] == "AFFORDABLE" and ok["buffered_surplus"] == Decimal("240.00")
    save = affordability_verdict("50", "0.20", "200")
    assert save["status"] == "SAVE" and save["months_needed"] == 5
    none = affordability_verdict("-20", "0.20", "200")
    assert none["status"] == "NOT_AFFORDABLE" and none["months_needed"] is None


# --- API ------------------------------------------------------------------
def test_tc_l01b_emi_paid_from_wallet(client, auth):
    home = make_wallet(
        client, auth, name="Home Account", currency_code="INR", opening_balance="100000"
    )
    loan = _loan(client, auth, default_wallet_id=home["id"])
    res = _pay(client, auth, loan["id"], amount="14000")
    assert res.status_code == 201, res.get_json()
    pay = res.get_json()
    assert pay["interest_part"] == "3683.33" and pay["principal_part"] == "10316.67"
    assert pay["balance_after"] == "509683.33"
    wallet = client.get(f"/api/wallets/{home['id']}", headers=auth).get_json()
    assert wallet["balance"] == "86000.00"
    detail = client.get(f"/api/loans/{loan['id']}", headers=auth).get_json()
    assert detail["outstanding_amount"] == "509683.33"
    assert detail["summary"]["interest_paid"] == "3683.33"
    assert detail["summary"]["months_to_payoff"] > 30
    assert len(detail["summary"]["schedule"]) == detail["summary"]["months_to_payoff"]


def test_tc_l03b_part_payment_via_api(client, auth):
    loan = _loan(
        client,
        auth,
        annual_rate_pct="12",
        outstanding_amount="100000",
        emi_amount="10000",
        sanctioned_amount="100000",
    )
    pay = _pay(
        client, auth, loan["id"], payment_type="PART_PAYMENT", amount="20000", wallet_id=None
    ).get_json()
    assert pay["interest_part"] == "0.00" and pay["balance_after"] == "80000.00"
    assert pay["interest_saved"] == "2088.94" and pay["emis_saved"] == 2
    detail = client.get(f"/api/loans/{loan['id']}", headers=auth).get_json()
    assert detail["summary"]["months_to_payoff"] == 9
    assert detail["summary"]["interest_saved"] == "2088.94"
    assert detail["summary"]["repaid_pct"] == 20.0


def test_tc_l04_only_latest_payment_can_be_undone(client, auth):
    home = make_wallet(
        client, auth, name="Home Account", currency_code="INR", opening_balance="100000"
    )
    loan = _loan(client, auth, default_wallet_id=home["id"])
    first = _pay(client, auth, loan["id"], amount="14000", paid_on="2026-10-05").get_json()
    second = _pay(client, auth, loan["id"], amount="14000", paid_on="2026-11-05").get_json()
    url = f"/api/loans/{loan['id']}/payments"
    assert client.delete(f"{url}/{first['id']}", headers=auth).status_code == 409
    assert client.delete(f"{url}/{second['id']}", headers=auth).status_code == 204
    detail = client.get(f"/api/loans/{loan['id']}", headers=auth).get_json()
    assert detail["outstanding_amount"] == first["balance_after"]
    wallet = client.get(f"/api/wallets/{home['id']}", headers=auth).get_json()
    assert wallet["balance"] == "86000.00"
    # the wallet expense of a payment is managed by the loan
    assert (
        client.delete(f"/api/transactions/{first['transaction_id']}", headers=auth).status_code
        == 409
    )


def test_tc_l05_payment_validation(client, auth):
    eur = make_wallet(client, auth)
    loan = _loan(client, auth, outstanding_amount="10000", sanctioned_amount="10000")
    wrong_wallet = _pay(client, auth, loan["id"], amount="1000", wallet_id=eur["id"])
    assert "wallet_id" in wrong_wallet.get_json()["error"]["details"]
    too_much = _pay(client, auth, loan["id"], amount="14000")
    assert too_much.status_code == 422 and "10070.83" in too_much.get_json()["error"]["message"]
    too_big_part = _pay(client, auth, loan["id"], payment_type="PART_PAYMENT", amount="10001")
    assert too_big_part.status_code == 422
    _pay(client, auth, loan["id"], amount="1000", paid_on="2026-11-05")
    earlier = _pay(client, auth, loan["id"], amount="1000", paid_on="2026-10-01")
    assert "paid_on" in earlier.get_json()["error"]["details"]


def test_tc_l08_full_repayment_closes_loan_and_plan_line(client, auth):
    loan = _loan(client, auth, outstanding_amount="10000", sanctioned_amount="10000")
    res = _pay(client, auth, loan["id"], amount="10070.83")
    assert res.status_code == 201
    detail = client.get(f"/api/loans/{loan['id']}", headers=auth).get_json()
    assert detail["status"] == "CLOSED" and detail["outstanding_amount"] == "0.00"
    assert detail["summary"]["months_to_payoff"] == 0
    emi = next(i for i in client.get("/api/plan", headers=auth).get_json()["items"] if i["loan_id"])
    assert emi["valid_to"] is not None
    nxt = add_months(TODAY.replace(day=1), 1).strftime("%Y-%m")
    assert client.get(f"/api/plan?month={nxt}", headers=auth).get_json()["minimum_target"] == "0.00"
    assert _pay(client, auth, loan["id"], amount="1").status_code == 409


def test_tc_l09_correcting_outstanding_and_editing_emi(client, auth, api_rates):
    api_rates(eur="0.940512", inr="100")
    loan = _loan(client, auth, emi_start_date="2028-04-05")
    res = client.patch(
        f"/api/loans/{loan['id']}",
        json={"outstanding_amount": "548000", "emi_amount": "15000"},
        headers=auth,
    )
    body = res.get_json()
    assert body["outstanding_amount"] == "548000.00"
    assert body["summary"]["payoff_month"] >= "2028-04"
    plan = client.get("/api/plan?month=2028-05", headers=auth).get_json()
    assert plan["minimum_target"] == "141.08"  # 15,000 x 0.00940512
    assert client.delete(f"/api/loans/{loan['id']}", headers=auth).status_code == 204
    assert client.get("/api/plan?month=2028-05", headers=auth).get_json()["items"] == []


def test_tc_l10_affordability_from_last_three_months(client, auth, api_rates):
    api_rates(eur="0.940512", inr="100")
    wallet = make_wallet(client, auth, opening_balance="5000")
    for i in range(1, 4):
        day = add_months(TODAY.replace(day=1), -i).replace(day=10).isoformat()
        for kind, cat, amount in (
            ("INCOME", "Part-time salary", "1000"),
            ("EXPENSE", "Rent", "700"),
        ):
            client.post(
                "/api/transactions",
                json={
                    "kind": kind,
                    "wallet_id": wallet["id"],
                    "category_id": category_id(client, auth, cat),
                    "amount": amount,
                    "txn_date": day,
                },
                headers=auth,
            )
    loan = _loan(client, auth, min_part_payment="10000")
    aff = loan["affordability"]
    assert aff["status"] == "AFFORDABLE"
    assert aff["avg_surplus"] == "300.00" and aff["buffered_surplus"] == "240.00"
    assert aff["min_part_payment_base"] == "94.05"
    assert Decimal(aff["interest_saved_if_paid"]) > 0 and aff["emis_saved_if_paid"] >= 0
    no_min = _loan(
        client,
        auth,
        name="Laptop",
        currency_code="EUR",
        annual_rate_pct="0",
        sanctioned_amount="1200",
        outstanding_amount="600",
        emi_amount="100",
    )
    assert no_min["affordability"] is None
    assert no_min["summary"]["months_to_payoff"] == 6
