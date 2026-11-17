"""Reports, dashboard and data rights (TC-RP01..RP09, TC-DB01, TC-EX01..EX02)."""

from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

from app.extensions import db
from app.models import Transaction, User
from app.services.plan_service import add_months
from app.services.report_service import fold_top, months_between, outstanding_on

from .conftest import ANANYA, category_id, make_wallet

TODAY = date.today()
THIS_MONTH = TODAY.replace(day=1)


def _txn(client, auth, wallet_id, cat, amount, on, kind="EXPENSE", **extra):
    res = client.post(
        "/api/transactions",
        json={
            "kind": kind,
            "wallet_id": wallet_id,
            "category_id": category_id(client, auth, cat),
            "amount": amount,
            "txn_date": on,
            **extra,
        },
        headers=auth,
    )
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def _journey(client, auth):
    """€100 pre-departure, €200 settling in, €50 + €30 study, salary €400."""
    w = make_wallet(client, auth, opening_balance="2000", opening_date="2025-06-01")
    _txn(client, auth, w["id"], "Visa fee", "100", "2025-08-10")
    _txn(client, auth, w["id"], "Accommodation deposit", "200", "2025-10-15")
    _txn(client, auth, w["id"], "Groceries", "50", "2026-03-01")
    _txn(client, auth, w["id"], "Groceries", "30", "2026-03-20")
    _txn(client, auth, w["id"], "Part-time salary", "400", "2026-03-31", kind="INCOME")
    _txn(client, auth, w["id"], "Loan disbursement", "900", "2026-03-15", kind="INCOME")
    return w


# --- pure helpers ----------------------------------------------------------
def test_tc_rp05_outstanding_from_payment_history():
    pays = [
        SimpleNamespace(
            paid_on=date(2026, 3, 5), balance_before=Decimal("1000"), balance_after=Decimal("800")
        ),
        SimpleNamespace(
            paid_on=date(2026, 4, 5), balance_before=Decimal("800"), balance_after=Decimal("600")
        ),
    ]
    created = date(2026, 1, 1)
    assert outstanding_on(created, pays, Decimal("600"), date(2025, 12, 31)) == 0
    assert outstanding_on(created, pays, Decimal("600"), date(2026, 2, 28)) == Decimal("1000")
    assert outstanding_on(created, pays, Decimal("600"), date(2026, 3, 31)) == Decimal("800")
    assert outstanding_on(created, pays, Decimal("600"), date(2026, 5, 1)) == Decimal("600")
    assert outstanding_on(created, [], Decimal("750"), date(2026, 5, 1)) == Decimal("750")


def test_tc_rp06_months_between():
    assert months_between(date(2025, 11, 20), date(2026, 2, 3)) == [
        date(2025, 11, 1),
        date(2025, 12, 1),
        date(2026, 1, 1),
        date(2026, 2, 1),
    ]


def test_tc_rp07_fold_top_into_other():
    rows = [("A", Decimal("5")), ("B", Decimal("50")), ("C", Decimal("20")), ("D", Decimal("1"))]
    assert fold_top(rows, 2) == [
        {"name": "B", "amount": Decimal("50.00")},
        {"name": "C", "amount": Decimal("20.00")},
        {"name": "Other", "amount": Decimal("6.00")},
    ]


# --- reports ---------------------------------------------------------------
def test_tc_rp01_cost_of_going_abroad_and_degree(client, auth):
    _journey(client, auth)
    body = client.get("/api/reports/costs", headers=auth).get_json()
    assert body["going_abroad"]["total"] == "300.00"  # pre-departure + settling in
    groups = {g["name"]: g["amount"] for g in body["going_abroad"]["by_group"]}
    assert groups == {"Housing": "200.00", "Visa & immigration": "100.00"}
    assert body["degree"]["total_so_far"] == "380.00"
    assert 0 <= body["degree"]["study_progress_pct"] <= 100


def test_tc_rp02_phase_report_counts_only_that_phase(client, auth):
    _journey(client, auth)
    phases = {p["phase_type"]: p["id"] for p in client.get("/api/phases", headers=auth).get_json()}
    study = client.get(
        f"/api/reports?period=PHASE&value={phases['STUDY']}", headers=auth
    ).get_json()
    # the 15 Oct deposit lies in the Study dates but belongs to Settling in
    assert study["spent"] == "80.00" and study["earned"] == "400.00"
    assert study["other_income"] == "900.00" and study["net"] == "320.00"
    lifetime = client.get("/api/reports?period=LIFETIME", headers=auth).get_json()
    assert lifetime["spent"] == "380.00"
    assert [p["name"] for p in lifetime["by_phase"]] == ["Pre-departure", "Settling in", "Study"]
    assert lifetime["period"]["start"] == "2025-06-01"


def test_tc_rp04_period_resolution(client, auth, register):
    _journey(client, auth)
    month = client.get("/api/reports?period=MONTH&value=2026-03", headers=auth).get_json()
    assert month["period"]["start"] == "2026-03-01" and month["period"]["end"] == "2026-03-31"
    assert month["spent"] == "80.00"
    assert month["top_categories"] == [{"name": "Groceries", "amount": "80.00"}]
    assert month["monthly"] == [{"month": "2026-03", "earned": "400.00", "spent": "80.00"}]
    year = client.get("/api/reports?period=YEAR&value=2025", headers=auth).get_json()
    assert year["spent"] == "300.00" and len(year["monthly"]) == 12
    other, _ = register(email="other@example.com")
    foreign = client.get("/api/phases", headers=other).get_json()[0]["id"]
    assert client.get(f"/api/reports?period=PHASE&value={foreign}", headers=auth).status_code == 422
    assert client.get("/api/reports?period=WEEK", headers=auth).status_code == 422
    assert client.get("/api/reports?period=YEAR&value=abc", headers=auth).status_code == 422


def test_tc_rp03_net_worth_timeline(client, auth, api_rates):
    api_rates(eur="0.9", inr="90")  # 1 INR = 0.01 EUR
    w = make_wallet(client, auth, opening_balance="1000", opening_date="2026-01-01")
    _txn(client, auth, w["id"], "Rent", "200", "2026-02-10")
    client.post(
        "/api/loans",
        json={
            "name": "SBI",
            "currency_code": "INR",
            "annual_rate_pct": "8.5",
            "sanctioned_amount": "100000",
            "outstanding_amount": "100000",
            "emi_amount": "5000",
        },
        headers=auth,
    )
    body = client.get("/api/reports/net-worth", headers=auth).get_json()
    points = {p["month"]: p for p in body["points"]}
    assert points["2025-12"]["assets"] == "0.00"  # wallet opened in January
    assert points["2026-01"]["net_worth"] == "1000.00"
    assert points["2026-02"]["net_worth"] == "800.00"
    now = points[TODAY.strftime("%Y-%m")]
    assert now["debt"] == "1000.00" and now["net_worth"] == "-200.00"


def test_tc_rp08_loan_timeline(client, auth):
    client.post(
        "/api/loans",
        json={
            "name": "Laptop",
            "currency_code": "EUR",
            "annual_rate_pct": "12",
            "sanctioned_amount": "1000",
            "outstanding_amount": "1000",
            "emi_amount": "500",
        },
        headers=auth,
    )
    body = client.get("/api/reports/loans", headers=auth).get_json()
    assert [p["outstanding"] for p in body["points"]] == ["1000.00", "510.00", "15.10", "0.00"]
    assert body["debt_free_month"] == add_months(THIS_MONTH, 2).strftime("%Y-%m")


def test_tc_rp09_loan_timeline_waits_for_first_emi(client, auth):
    start = add_months(THIS_MONTH, 2)
    client.post(
        "/api/loans",
        json={
            "name": "Later",
            "currency_code": "EUR",
            "annual_rate_pct": "0",
            "sanctioned_amount": "300",
            "outstanding_amount": "300",
            "emi_amount": "100",
            "emi_start_date": start.isoformat(),
        },
        headers=auth,
    )
    points = client.get("/api/reports/loans", headers=auth).get_json()["points"]
    assert [p["outstanding"] for p in points] == [
        "300.00",
        "300.00",
        "300.00",
        "200.00",
        "100.00",
        "0.00",
    ]


def test_tc_db01_dashboard(client, auth, api_rates):
    api_rates(eur="0.9", inr="90")  # 1 INR = 0.01 EUR
    eur = make_wallet(client, auth, opening_balance="613.79", opening_date="2025-09-25")
    make_wallet(
        client,
        auth,
        name="Home Account",
        currency_code="INR",
        opening_balance="50000",
        opening_date="2025-06-01",
    )
    client.post(
        "/api/plan",
        json={
            "name": "Rent",
            "category_id": category_id(client, auth, "Rent"),
            "amount": "420",
            "currency_code": "EUR",
            "valid_from": "2025-10-01",
        },
        headers=auth,
    )
    day = (TODAY - timedelta(days=3)).isoformat()
    for cat, amount in (
        ("Rent", "420"),
        ("Groceries", "300"),
        ("Eating out", "100"),
        ("Clothing", "90"),
        ("Public transport", "80"),
        ("Leisure & travel", "60"),
        ("Subscriptions", "10"),
    ):
        _txn(client, auth, eur["id"], cat, amount, day)
    _txn(client, auth, eur["id"], "Part-time salary", "1150", TODAY.isoformat(), kind="INCOME")
    body = client.get("/api/dashboard", headers=auth).get_json()
    # 613.79 - 1060 + 1150 = 703.79 EUR plus 50,000 INR x 0.01 = 500 EUR
    assert body["total_balance"] == "1203.79"
    cats = body["spending_30d"]["categories"]
    assert len(cats) == 6 and cats[-1] == {"name": "Other", "amount": "70.00"}
    assert body["spending_30d"]["total"] == "1060.00"
    assert body["alerts"][0]["name"] == "Daily Spending"
    assert body["alerts"][0]["runway"]["status"] == "CRITICAL"  # 703.79 / 35.33 = 19 days
    month = body["this_month"]
    if TODAY.day > 3:  # spending date falls in this month
        assert month["target"] == "420.00"
    assert month["earned"] == "1150.00"
    assert body["loans"]["active"] == 0 and body["current_phase_id"]


# --- data rights -----------------------------------------------------------
def test_tc_ex01_export_contains_everything_but_the_password(client, auth):
    _journey(client, auth)
    res = client.get("/api/account/export", headers=auth)
    assert res.status_code == 200
    assert "attachment" in res.headers["Content-Disposition"]
    body = res.get_json()
    assert body["profile"]["email"] == ANANYA["email"]
    assert len(body["transactions"]) == 6 and len(body["life_phases"]) == 4
    assert "password_hash" not in res.get_data(as_text=True)
    assert "Demo#2026" not in res.get_data(as_text=True)


def test_tc_ex02_delete_account_needs_password(client, auth, register):
    _journey(client, auth)
    other, _ = register(email="keep@example.com")
    bad = client.delete("/api/account", json={"password": "wrong"}, headers=auth)
    assert bad.status_code == 422
    assert (
        client.delete("/api/account", json={"password": "Demo#2026"}, headers=auth).status_code
        == 204
    )
    assert client.get("/api/me", headers=auth).status_code == 401
    login = client.post("/api/auth/login", json={"email": ANANYA["email"], "password": "Demo#2026"})
    assert login.status_code == 401
    assert db.session.query(User).count() == 1  # the other user stays
    assert db.session.query(Transaction).count() == 0
    assert client.get("/api/me", headers=other).status_code == 200
