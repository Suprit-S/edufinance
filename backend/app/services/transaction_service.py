"""Transactions with frozen exchange rates (FR-13 to FR-16, ADR-0003).

Every transaction is in its wallet's currency. At save time the values in the
user's base and home currency are calculated and stored together with the
rates and their source. They are never recalculated from market rates later;
only an explicit user correction changes them (rate freezing).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.errors import ApiError, Conflict, NotFound
from app.extensions import db
from app.models import (
    CategoryKind,
    LoanPayment,
    RateSource,
    Transaction,
    TransactionKind,
    User,
)

from . import category_service, fx_service, phase_service, wallet_service
from .money import convert, money, rate

# Most "uncertain" source wins, so an estimated part is never hidden.
SOURCE_PRIORITY = [RateSource.FALLBACK, RateSource.USER, RateSource.LIVE, RateSource.IDENTITY]


@dataclass(frozen=True)
class FrozenRates:
    rate_to_base: Decimal
    rate_to_home: Decimal
    source: RateSource


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
def combine_sources(*sources: RateSource) -> RateSource:
    """Single label for a transaction's rates (TC-T05)."""
    for candidate in SOURCE_PRIORITY:
        if candidate in sources:
            return candidate
    return RateSource.IDENTITY


def freeze_amounts(amount, frozen: FrozenRates) -> tuple[Decimal, Decimal]:
    """Base and home values of an amount with frozen rates (TC-T01)."""
    return convert(amount, frozen.rate_to_base), convert(amount, frozen.rate_to_home)


# ---------------------------------------------------------------------------
# Rates
# ---------------------------------------------------------------------------
def _one_rate(currency: str, target: str, on: date, user_rate) -> tuple[Decimal, RateSource]:
    if currency == target:
        return Decimal("1"), RateSource.IDENTITY
    if user_rate is not None:
        return rate(user_rate), RateSource.USER
    try:
        market = fx_service.get_rate(currency, target, on)
    except fx_service.UnknownCurrency as exc:
        raise ApiError(str(exc), 422, "VALIDATION_ERROR") from exc
    return market.rate, market.source


def resolve_rates(
    user: User, currency: str, on: date, user_rate_to_base=None, user_rate_to_home=None
) -> FrozenRates:
    """Rates for a new transaction: identity, user-entered, or market (FR-16).

    If the user enters only the base rate and home == base cannot be used,
    the home rate is still taken from the market.
    """
    to_base, src_base = _one_rate(currency, user.base_currency, on, user_rate_to_base)
    to_home, src_home = _one_rate(currency, user.home_currency, on, user_rate_to_home)
    return FrozenRates(to_base, to_home, combine_sources(src_base, src_home))


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
def get_transaction(user_id: uuid.UUID, txn_id: uuid.UUID) -> Transaction:
    txn = db.session.get(Transaction, txn_id)
    if txn is None or txn.user_id != user_id:
        raise NotFound("Transaction")
    return txn


def list_transactions(
    user_id: uuid.UUID,
    *,
    wallet_id=None,
    kind=None,
    category_id=None,
    phase_id=None,
    date_from=None,
    date_to=None,
    search=None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[Transaction], int]:
    """Filtered, newest-first page of a user's transactions and the total count."""
    conditions = [Transaction.user_id == user_id]
    if wallet_id:
        conditions.append(Transaction.wallet_id == wallet_id)
    if kind:
        conditions.append(Transaction.kind == kind)
    if category_id:
        conditions.append(Transaction.category_id == category_id)
    if phase_id:
        conditions.append(Transaction.phase_id == phase_id)
    if date_from:
        conditions.append(Transaction.txn_date >= date_from)
    if date_to:
        conditions.append(Transaction.txn_date <= date_to)
    if search:
        conditions.append(Transaction.note.ilike(f"%{search}%"))

    total = db.session.scalar(select(func.count()).select_from(Transaction).where(*conditions))
    rows = db.session.scalars(
        select(Transaction)
        .where(*conditions)
        .options(selectinload(Transaction.category), selectinload(Transaction.phase))
        .order_by(Transaction.txn_date.desc(), Transaction.created_at.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    ).all()
    return list(rows), total or 0


def is_linked(txn: Transaction) -> bool:
    """Transactions created by a remittance or loan payment are managed there."""
    if txn.remittance_id is not None:
        return True
    return (
        db.session.scalar(select(LoanPayment.id).where(LoanPayment.transaction_id == txn.id))
        is not None
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def record(
    user: User,
    *,
    wallet_id: uuid.UUID,
    kind: TransactionKind,
    amount,
    txn_date: date,
    category_id: uuid.UUID | None = None,
    note: str | None = None,
    phase_id: uuid.UUID | None = None,
    rate_to_base=None,
    rate_to_home=None,
    remittance_id: uuid.UUID | None = None,
) -> Transaction:
    """Create any transaction. Used by the API and later by remittances and
    loan payments, so all money movements share the same rules."""
    wallet = wallet_service.get_wallet(user.id, wallet_id)
    if wallet.is_archived:
        raise ApiError(
            "This wallet is archived.", 422, "VALIDATION_ERROR", {"wallet_id": ["Archived."]}
        )
    amount = money(amount)
    if amount <= 0:
        raise ApiError(
            "Amount must be positive.", 422, "VALIDATION_ERROR", {"amount": ["Must be > 0."]}
        )

    if kind in (TransactionKind.INCOME, TransactionKind.EXPENSE):
        if category_id is None:
            raise ApiError(
                "Please choose a category.",
                422,
                "VALIDATION_ERROR",
                {"category_id": ["Required."]},
            )
        category = category_service.get_category(user.id, category_id)
        if category.kind.value != kind.value:
            raise ApiError(
                f"'{category.name}' is not an {kind.value.lower()} category.",
                422,
                "VALIDATION_ERROR",
                {"category_id": ["Category does not match the transaction type."]},
            )

    if phase_id is not None:
        phase_service.get_phase(user.id, phase_id)
        manual = True
    else:
        phase_id = phase_service.assign_phase(user.id, txn_date)
        manual = False

    frozen = resolve_rates(user, wallet.currency_code, txn_date, rate_to_base, rate_to_home)
    amount_base, amount_home = freeze_amounts(amount, frozen)

    txn = Transaction(
        user_id=user.id,
        wallet_id=wallet.id,
        category_id=category_id,
        kind=kind,
        amount=amount,
        currency_code=wallet.currency_code,
        txn_date=txn_date,
        note=note,
        phase_id=phase_id,
        phase_is_manual=manual,
        rate_to_base=frozen.rate_to_base,
        rate_to_home=frozen.rate_to_home,
        amount_base=amount_base,
        amount_home=amount_home,
        rate_source=frozen.source,
        remittance_id=remittance_id,
    )
    db.session.add(txn)
    db.session.flush()
    return txn


def create_transaction(user: User, data: dict) -> Transaction:
    """Income or expense entered by the user (FR-13)."""
    if data["kind"] not in (CategoryKind.INCOME.value, CategoryKind.EXPENSE.value):
        raise ApiError("Use a remittance for transfers.", 422, "VALIDATION_ERROR")
    return record(
        user,
        wallet_id=data["wallet_id"],
        kind=TransactionKind(data["kind"]),
        amount=data["amount"],
        txn_date=data["txn_date"],
        category_id=data["category_id"],
        note=data.get("note"),
        phase_id=data.get("phase_id"),
        rate_to_base=data.get("rate_to_base"),
        rate_to_home=data.get("rate_to_home"),
    )


def update_transaction(user: User, txn_id: uuid.UUID, data: dict) -> Transaction:
    """Edit an income/expense. Stored rates are kept unless the user enters a
    new rate; amounts are recalculated with the (frozen) rate (FR-15)."""
    txn = get_transaction(user.id, txn_id)
    if is_linked(txn):
        raise Conflict("This entry belongs to a transfer or loan payment. Edit it there.")

    if "category_id" in data:
        cat = category_service.get_category(user.id, data["category_id"])
        if cat.kind.value != txn.kind.value:
            raise ApiError(
                "Category does not match the transaction type.",
                422,
                "VALIDATION_ERROR",
                {"category_id": ["Category does not match the transaction type."]},
            )
        txn.category_id = cat.id
    if "note" in data:
        txn.note = data["note"]
    if "amount" in data:
        txn.amount = money(data["amount"])
    if "txn_date" in data:
        txn.txn_date = data["txn_date"]

    # Rate corrections by the user (all other rates stay frozen).
    targets = {"rate_to_base": user.base_currency, "rate_to_home": user.home_currency}
    needed = [k for k, ccy in targets.items() if txn.currency_code != ccy]
    overridden = [k for k in needed if data.get(k) is not None]
    for key in overridden:
        setattr(txn, key, rate(data[key]))
    if overridden:
        txn.rate_source = (
            RateSource.USER
            if set(overridden) == set(needed)
            else combine_sources(txn.rate_source, RateSource.USER)
        )
    txn.amount_base, txn.amount_home = freeze_amounts(
        txn.amount, FrozenRates(txn.rate_to_base, txn.rate_to_home, txn.rate_source)
    )

    if "phase_id" in data:
        if data["phase_id"] is None:
            txn.phase_is_manual = False
        else:
            phase_service.get_phase(user.id, data["phase_id"])
            txn.phase_id = data["phase_id"]
            txn.phase_is_manual = True
    if not txn.phase_is_manual:
        txn.phase_id = phase_service.assign_phase(user.id, txn.txn_date)
    db.session.flush()
    return txn


def delete_transaction(user: User, txn_id: uuid.UUID) -> None:
    txn = get_transaction(user.id, txn_id)
    if is_linked(txn):
        raise Conflict("This entry belongs to a transfer or loan payment. Delete it there.")
    db.session.delete(txn)
    db.session.flush()
