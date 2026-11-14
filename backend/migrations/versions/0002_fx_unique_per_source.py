"""FX cache: API and fallback rates may coexist for the same pair and day.

The unique key of ``fx_rates`` now includes ``source``. Before, a live rate
fetched on the fallback table's date (2026-01-01) replaced the fallback row.

Revision ID: 0002_fx_unique_per_source
Revises: 0001_initial
"""

from alembic import op

revision = "0002_fx_unique_per_source"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("fx_rates") as batch_op:
        batch_op.drop_constraint("uq_fx_rates_pair_date", type_="unique")
        batch_op.create_unique_constraint(
            "uq_fx_rates_pair_date_source",
            ["base_currency", "quote_currency", "rate_date", "source"],
        )


def downgrade():
    # Keep one row per pair and day (prefer the API rate) before restoring the old key.
    op.execute(
        "DELETE FROM fx_rates f USING fx_rates a "
        "WHERE f.source = 'FALLBACK' AND a.source = 'API' "
        "AND f.base_currency = a.base_currency AND f.quote_currency = a.quote_currency "
        "AND f.rate_date = a.rate_date"
    )
    with op.batch_alter_table("fx_rates") as batch_op:
        batch_op.drop_constraint("uq_fx_rates_pair_date_source", type_="unique")
        batch_op.create_unique_constraint(
            "uq_fx_rates_pair_date", ["base_currency", "quote_currency", "rate_date"]
        )
