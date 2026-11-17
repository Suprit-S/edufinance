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
    db.session.commit()


@pytest.fixture()
def client(app):
    return app.test_client()
