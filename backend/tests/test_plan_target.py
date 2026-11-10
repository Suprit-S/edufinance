"""Monthly Plan and Target to Earn (TC-PL01..PL04, TC-TE01..TE03)."""

from datetime import date

from app.services.plan_service import add_months, item_active, month_end, parse_month

from .conftest import category_id, make_wallet

THIS_MONTH = date.today().replace(day=1)


def _item(client, auth, name, category, amount, currency="EUR", **extra):
    payload = {
        "name": name,
        "category_id": category_id(client, auth, category),
        "amount": amount,
        "currency_code": currency,
        "valid_from": "2025-10-01",
        **extra,
    }
    res = client.post("/api/plan", json=payload, headers=auth)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


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


def test_tc_pl01_minimum_target_includes_emi(client, auth, api_rates):
    api_rates(eur="0.940512", inr="100")  # 1 INR = 0.00940512 EUR
    _item(client, auth, "Rent", "Rent", "420")
    _item(client, auth, "Health insurance (TK)", "Health insurance", "135")
    _loan(client, auth)
    plan = client.get("/api/plan", headers=auth).get_json()
    assert plan["minimum_target"] == "686.67"  # 420 + 135 + 14,000 x 0.00940512
    emi = next(i for i in plan["items"] if i["loan_id"])
    assert emi["name"] == "EMI – SBI education loan" and emi["amount_base"] == "131.67"


def test_tc_pl02_emi_counts_from_its_start_month(client, auth, api_rates):
    api_rates(eur="0.940512", inr="100")
    _loan(client, auth, emi_start_date="2028-04-05")
    before = client.get("/api/plan?month=2027-11", headers=auth).get_json()
    after = client.get("/api/plan?month=2028-04", headers=auth).get_json()
    assert before["minimum_target"] == "0.00"
    assert after["minimum_target"] == "131.67"


def test_tc_pl03_item_limited_to_a_phase_and_date_range(client, auth):
    study = next(
        p for p in client.get("/api/phases", headers=auth).get_json() if p["phase_type"] == "STUDY"
    )
    _item(client, auth, "Semester ticket", "Public transport", "58", phase_id=study["id"])
    _item(client, auth, "Laptop instalment", "Instalment plan", "100", valid_to="2026-09-30")
    in_study = client.get("/api/plan?month=2026-05", headers=auth).get_json()
    after_study = client.get("/api/plan?month=2028-01", headers=auth).get_json()
    assert in_study["minimum_target"] == "158.00"
    assert after_study["minimum_target"] == "0.00"
    assert client.get("/api/plan?month=2026-13", headers=auth).status_code == 422


def test_tc_pl04_rules(client, auth):
    loan = _loan(client, auth)
    emi = next(
        i
        for i in client.get("/api/plan", headers=auth).get_json()["items"]
        if i["loan_id"] == loan["id"]
    )
    assert (
        client.patch(f"/api/plan/{emi['id']}", json={"amount": "1"}, headers=auth).status_code
        == 409
    )
    assert client.delete(f"/api/plan/{emi['id']}", headers=auth).status_code == 409
    bad = client.post(
        "/api/plan",
        json={
            "name": "Salary",
            "category_id": category_id(client, auth, "Part-time salary"),
            "amount": "1",
            "currency_code": "EUR",
            "valid_from": "2026-01-01",
        },
        headers=auth,
    )
    assert bad.status_code == 422
    rent = _item(client, auth, "Rent", "Rent", "420")
    res = client.patch(f"/api/plan/{rent['id']}", json={"valid_to": "2025-01-01"}, headers=auth)
    assert res.status_code == 422
    res = client.patch(f"/api/plan/{rent['id']}", json={"amount": "450"}, headers=auth)
    assert res.get_json()["amount"] == "450.00"
    assert client.delete(f"/api/plan/{rent['id']}", headers=auth).status_code == 204


def test_tc_te01_target_to_earn_for_the_month(client, auth, api_rates):
    api_rates(eur="0.940512", inr="100")
    for name, cat, amount in [
        ("Rent", "Rent", "420"),
        ("Insurance", "Health insurance", "135"),
        ("Groceries", "Groceries", "300"),
        ("Ticket", "Public transport", "58"),
        ("Phone", "Phone & internet", "15"),
        ("Laptop", "Instalment plan", "45"),
    ]:
        _item(client, auth, name, cat, amount)
    _loan(client, auth)
    wallet = make_wallet(client, auth, opening_balance="2000")
    day = THIS_MONTH.isoformat()

    def txn(kind, cat, amount):
        res = client.post(
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
        assert res.status_code == 201

    txn("INCOME", "Part-time salary", "250")
    txn("INCOME", "Loan disbursement", "3000")  # TC-TE02: not earned
    txn("EXPENSE", "Rent", "420")

    body = client.get("/api/target", headers=auth).get_json()
    assert body["target"] == "1104.67"
    assert body["earned"] == "250.00"
    assert body["still_to_earn"] == "854.67"
    assert body["progress_pct"] == 22.6
    assert body["spent"] == "420.00" and body["net"] == "-170.00"
    assert body["by_source"] == [{"source": "Part-time salary", "amount": "250.00"}]
    rent = next(line for line in body["lines"] if line["name"] == "Rent")
    assert rent["actual"] == "420.00" and rent["difference"] == "0.00"
    assert len(body["history"]) == 6 and body["history"][-1]["earned"] == "250.00"


def test_tc_te03_surplus_when_target_reached(client, auth):
    _item(client, auth, "Rent", "Rent", "420")
    wallet = make_wallet(client, auth)
    client.post(
        "/api/transactions",
        json={
            "kind": "INCOME",
            "wallet_id": wallet["id"],
            "category_id": category_id(client, auth, "Part-time salary"),
            "amount": "612.50",
            "txn_date": THIS_MONTH.isoformat(),
        },
        headers=auth,
    )
    body = client.get("/api/target", headers=auth).get_json()
    assert body["still_to_earn"] == "0.00" and body["surplus_over_target"] == "192.50"


def test_pure_month_helpers():
    assert parse_month("2026-02") == date(2026, 2, 1)
    assert month_end(date(2028, 2, 1)) == date(2028, 2, 29)
    assert add_months(date(2026, 11, 1), 3) == date(2027, 2, 1)
    assert add_months(date(2026, 1, 1), -1) == date(2025, 12, 1)
    assert item_active(date(2026, 1, 15), None, date(2026, 1, 1))
    assert not item_active(date(2026, 2, 1), None, date(2026, 1, 1))
    assert not item_active(date(2025, 1, 1), date(2025, 12, 31), date(2026, 1, 1))
    assert not item_active(
        date(2025, 1, 1), None, date(2026, 1, 1), (date(2026, 2, 1), date(2026, 3, 1))
    )


def test_tc_te04_emi_line_actual_counts_only_emis(client, auth, api_rates):
    api_rates(eur="0.940512", inr="100")
    loan = _loan(client, auth)
    day = THIS_MONTH.isoformat()
    for ptype, amount in (("EMI", "14000"), ("PART_PAYMENT", "20000")):
        res = client.post(
            f"/api/loans/{loan['id']}/payments",
            json={"payment_type": ptype, "amount": amount, "paid_on": day},
            headers=auth,
        )
        assert res.status_code == 201
    line = client.get("/api/target", headers=auth).get_json()["lines"][0]
    assert line["planned"] == "131.67" and line["actual"] == "131.67"
