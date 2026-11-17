"""Burn rate and runway per wallet (FR-35, FR-36, ADR-0006).

burn rate = expenses of the last 30 days (wallet currency) / 30
runway    = balance / burn rate, rounded down to whole days
status    = Healthy > 90 days, OK 60-90, Warning 30-60, Critical < 30

Only EXPENSE transactions count as spending; money moved to another own
wallet (TRANSFER_OUT) is not spent.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_FLOOR, Decimal

from flask import current_app
from sqlalchemy import func, select

from app.extensions import db
from app.models import Transaction, TransactionKind

from . import wallet_service
from .money import ZERO, money

HEALTHY, OK, WARNING, CRITICAL = "HEALTHY", "OK", "WARNING", "CRITICAL"


@dataclass(frozen=True)
class Runway:
    balance: Decimal
    spent_window: Decimal
    burn_rate: Decimal  # per day, rounded to cents for display
    days: int | None  # None = no spending -> unlimited
    status: str

    def to_dict(self) -> dict:
        return {
            "balance": str(self.balance),
            "spent_last_window": str(self.spent_window),
            "burn_rate_per_day": str(self.burn_rate),
            "days": self.days,
            "status": self.status,
        }


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------
def classify(days: int | None, healthy: int = 90, ok: int = 60, warning: int = 30) -> str:
    """Status for a runway in days (thresholds from configuration)."""
    if days is None or days > healthy:
        return HEALTHY
    if days >= ok:
        return OK
    if days >= warning:
        return WARNING
    return CRITICAL


def compute_runway(
    balance: Decimal, spent_window: Decimal, window_days: int = 30, thresholds=(90, 60, 30)
) -> Runway:
    """Runway from a balance and the spending of the last ``window_days`` (TC-RW01/02)."""
    balance, spent_window = money(balance), money(spent_window)
    if spent_window <= 0:
        return Runway(balance, ZERO, ZERO, None, classify(None, *thresholds))
    daily = Decimal(spent_window) / Decimal(window_days)
    if balance <= 0:
        days = 0
    else:
        days = int((balance / daily).to_integral_value(rounding=ROUND_FLOOR))
    return Runway(balance, spent_window, money(daily), days, classify(days, *thresholds))


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def _config():
    cfg = current_app.config
    return (
        cfg["BURN_RATE_WINDOW_DAYS"],
        (cfg["RUNWAY_HEALTHY_DAYS"], cfg["RUNWAY_OK_DAYS"], cfg["RUNWAY_WARNING_DAYS"]),
    )


def spent_by_wallet(user_id: uuid.UUID, start: date, end: date) -> dict[uuid.UUID, Decimal]:
    rows = db.session.execute(
        select(Transaction.wallet_id, func.sum(Transaction.amount))
        .where(
            Transaction.user_id == user_id,
            Transaction.kind == TransactionKind.EXPENSE,
            Transaction.txn_date.between(start, end),
        )
        .group_by(Transaction.wallet_id)
    ).all()
    return {wid: total for wid, total in rows}


def wallet_runways(user_id: uuid.UUID, today: date | None = None) -> dict[uuid.UUID, Runway]:
    """Runway of every wallet of the user, keyed by wallet id."""
    today = today or date.today()
    window, thresholds = _config()
    balances = wallet_service.balances(user_id, as_of=today)
    spent = spent_by_wallet(user_id, today - timedelta(days=window - 1), today)
    return {
        wid: compute_runway(balance, spent.get(wid, ZERO), window, thresholds)
        for wid, balance in balances.items()
    }
