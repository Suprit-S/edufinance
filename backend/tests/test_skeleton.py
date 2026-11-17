"""Skeleton tests: health, master data, error format and database constraints
(test cases TC-S01..TC-S08)."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Category, CategoryKind, User
from app.seed.master_data import CATEGORIES, seed_master_data


def test_tc_s01_health_reports_database_ok(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok", "database": "ok"}


def test_tc_s02_currencies_are_public_and_sorted(client):
    data = client.get("/api/currencies").get_json()
    codes = [c["code"] for c in data]
    assert "INR" in codes and "EUR" in codes
    assert codes == sorted(codes)


def test_tc_s03_countries_include_default_currency(client):
    data = client.get("/api/countries").get_json()
    germany = next(c for c in data if c["code"] == "DE")
    assert germany["default_currency"] == "EUR"


def test_tc_s04_unknown_route_returns_json_error(client):
    res = client.get("/api/does-not-exist")
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "NOT_FOUND"


def test_tc_s05_seed_is_idempotent(app):
    seed_master_data()
    seed_master_data()
    count = Category.query.filter_by(user_id=None).count()
    assert count == len(CATEGORIES)


def test_tc_s06_loan_disbursement_does_not_count_as_earned(app):
    cat = Category.query.filter_by(
        user_id=None, name="Loan disbursement", kind=CategoryKind.INCOME
    ).one()
    assert cat.counts_as_earned is False
    salary = Category.query.filter_by(user_id=None, name="Part-time salary").one()
    assert salary.counts_as_earned is True


def _user(**overrides):
    data = dict(
        full_name="Test User",
        email="test@example.com",
        password_hash="x",
        date_of_birth=date(2000, 5, 17),
        home_currency="INR",
        base_currency="EUR",
        destination_country="DE",
        planning_start_date=date(2025, 6, 1),
        arrival_date=date(2025, 9, 25),
        study_start_date=date(2025, 10, 1),
        study_end_date=date(2027, 9, 30),
    )
    data.update(overrides)
    return User(**data)


def test_tc_s07_database_rejects_study_end_before_start(app):
    db.session.add(_user(study_end_date=date(2025, 1, 1)))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_tc_s08_age_is_computed_not_stored(app):
    user = _user()
    assert user.age_on(date(2026, 5, 16)) == 25
    assert user.age_on(date(2026, 5, 17)) == 26
    assert not hasattr(User, "age")


def test_tc_s09_money_columns_return_exact_decimals(app):
    from app.models import FxRate

    row = FxRate.query.filter_by(base_currency="USD", quote_currency="EUR").first()
    assert isinstance(row.rate, Decimal)
    assert row.rate == Decimal("0.85800000")
