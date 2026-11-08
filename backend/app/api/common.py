"""Helpers shared by all blueprints: authentication guard, input loading,
and JSON serialisation of models. Money and rates leave the API as strings so
no precision is lost (ADR-0002)."""

from datetime import date
from decimal import Decimal

from flask import request
from flask_jwt_extended import current_user, verify_jwt_in_request
from marshmallow import Schema

from app.models import LifePhase, Transaction, User, Wallet
from app.services.phase_service import progress_in_phase


def require_auth():
    """``before_request`` hook: every route of a protected blueprint needs a
    valid, non-revoked token (NFR-06). CORS pre-flight requests pass."""
    if request.method == "OPTIONS":
        return None
    verify_jwt_in_request()
    return None


def me() -> User:
    """The authenticated user (loaded by the JWT user loader)."""
    return current_user


def load(schema: Schema, *, partial: bool = False, source: str = "json") -> dict:
    """Validate the JSON body (or query string) with a marshmallow schema."""
    if source == "args":
        raw = request.args.to_dict()
    else:
        raw = request.get_json(silent=True)
        if raw is None:
            raw = {}
    return schema.load(raw, partial=partial)


def s(value) -> str | None:
    """Decimal -> str (None stays None)."""
    return None if value is None else str(value)


def d(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------
def phase_dict(phase: LifePhase, today: date | None = None) -> dict:
    today = today or date.today()
    return {
        "id": str(phase.id),
        "phase_type": phase.phase_type.value,
        "name": phase.name,
        "start_date": d(phase.start_date),
        "end_date": d(phase.end_date),
        "is_system": phase.is_system,
        "is_current": phase.start_date <= today
        and (phase.end_date is None or today <= phase.end_date),
        "progress_pct": progress_in_phase(phase.start_date, phase.end_date, today),
    }


def user_dict(user: User) -> dict:
    today = date.today()
    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "date_of_birth": d(user.date_of_birth),
        "age": user.age_on(today),
        "gender": user.gender.value if user.gender else None,
        "home_currency": user.home_currency,
        "base_currency": user.base_currency,
        "destination_country": user.destination_country,
        "planning_start_date": d(user.planning_start_date),
        "arrival_date": d(user.arrival_date),
        "study_start_date": d(user.study_start_date),
        "study_end_date": d(user.study_end_date),
        "settling_in_days": user.settling_in_days,
        "phases": [phase_dict(p, today) for p in user.phases],
    }


def wallet_dict(wallet: Wallet, balance: Decimal | None = None) -> dict:
    return {
        "id": str(wallet.id),
        "name": wallet.name,
        "currency_code": wallet.currency_code,
        "wallet_type": wallet.wallet_type.value,
        "opening_balance": s(wallet.opening_balance),
        "opening_date": d(wallet.opening_date),
        "is_archived": wallet.is_archived,
        "balance": s(balance if balance is not None else wallet.opening_balance),
    }


def transaction_dict(txn: Transaction) -> dict:
    return {
        "id": str(txn.id),
        "wallet_id": str(txn.wallet_id),
        "kind": txn.kind.value,
        "category_id": s(txn.category_id),
        "category_name": txn.category.name if txn.category else None,
        "amount": s(txn.amount),
        "currency_code": txn.currency_code,
        "txn_date": d(txn.txn_date),
        "note": txn.note,
        "phase_id": str(txn.phase_id),
        "phase_name": txn.phase.name if txn.phase else None,
        "phase_is_manual": txn.phase_is_manual,
        "rate_to_base": s(txn.rate_to_base),
        "rate_to_home": s(txn.rate_to_home),
        "amount_base": s(txn.amount_base),
        "amount_home": s(txn.amount_home),
        "rate_source": txn.rate_source.value,
        "estimated": txn.rate_source.value == "FALLBACK",
        "remittance_id": s(txn.remittance_id),
    }
