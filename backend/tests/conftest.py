"""Test fixtures.

Tests run against a real PostgreSQL database (``TEST_DATABASE_URL``) so that
NUMERIC precision, native enums and CHECK constraints behave exactly as in
production. The schema is built once per session by running the Alembic
migrations, which also tests the migrations themselves.
"""

import pytest
from flask_migrate import downgrade, upgrade
from sqlalchemy import text

from app import create_app
from app.extensions import db
from app.seed.master_data import seed_master_data

# Tables holding user data, children first; emptied after every test.
# DELETE (not TRUNCATE ... CASCADE) so that system categories survive.
USER_TABLES = (
    "loan_payments",
    "monthly_plan_items",
    "transactions",
    "remittances",
    "loans",
    "wallets",
    "revoked_tokens",
    "life_phases",
    "categories",
    "users",
)


@pytest.fixture(scope="session")
def app():
    app = create_app("test")
    with app.app_context():
        downgrade(revision="base")  # start from an empty schema
        upgrade()
        seed_master_data()
        yield app
        db.session.remove()


@pytest.fixture(autouse=True)
def _clean_user_data(app):
    yield
    db.session.rollback()
    for table in USER_TABLES:
        where = " WHERE user_id IS NOT NULL" if table == "categories" else ""
        db.session.execute(text(f"DELETE FROM {table}{where}"))
    # cached market rates of one test (e.g. the demo rate history) must not leak
    db.session.execute(text("DELETE FROM fx_rates WHERE source = 'API'"))
    db.session.commit()


@pytest.fixture()
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Helpers for API tests
# ---------------------------------------------------------------------------
ANANYA = {
    "full_name": "Ananya Rao",
    "email": "ananya@example.com",
    "password": "Demo#2026",
    "date_of_birth": "2001-03-14",
    "gender": "FEMALE",
    "home_currency": "INR",
    "base_currency": "EUR",
    "destination_country": "DE",
    "planning_start_date": "2025-06-01",
    "arrival_date": "2025-09-25",
    "study_start_date": "2025-10-01",
    "study_end_date": "2027-09-30",
}


@pytest.fixture()
def register(client):
    """Register a user; returns (headers, user_json)."""

    def _register(**overrides):
        payload = {**ANANYA, **overrides}
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 201, res.get_json()
        body = res.get_json()
        return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]

    return _register


@pytest.fixture()
def auth(register):
    """Headers of a registered default user (Ananya, INR -> EUR)."""
    headers, _ = register()
    return headers


@pytest.fixture()
def api_rates(app):
    """Store USD-based API rates for a date: 1 USD = 0.86 EUR = 91.5 INR."""
    from datetime import date
    from decimal import Decimal

    from app.models import FxRate, FxSource

    def _store(on=None, eur="0.86", inr="91.5", extra=None):
        on = on or date.today()
        values = {"USD": "1", "EUR": eur, "INR": inr, **(extra or {})}
        for code, value in values.items():
            db.session.merge(
                FxRate(
                    base_currency="USD",
                    quote_currency=code,
                    rate=Decimal(value),
                    rate_date=on,
                    source=FxSource.API,
                )
            )
        db.session.commit()

    yield _store
    db.session.execute(text("DELETE FROM fx_rates WHERE source = 'API'"))  # also demo rates
    db.session.commit()


def category_id(client, headers, name):
    cats = client.get("/api/categories", headers=headers).get_json()
    return next(c["id"] for c in cats if c["name"] == name)


def make_wallet(client, headers, **overrides):
    payload = {
        "name": "Daily Spending",
        "currency_code": "EUR",
        "wallet_type": "BANK",
        "opening_balance": "500.00",
        "opening_date": "2025-09-25",
        **overrides,
    }
    res = client.post("/api/wallets", json=payload, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()
