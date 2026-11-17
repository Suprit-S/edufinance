"""Remittances: real currency exchanges entered by the user (FR-18, FR-20 to FR-22).

The user enters what was **sent** and what was **received**; the effective
rate is derived from these amounts (ADR-0003, ADR-0011).

Directions and the transactions they create
-------------------------------------------
* own wallet  -> own wallet : TRANSFER_OUT + TRANSFER_IN (not income/expense)
* outside     -> own wallet : INCOME  (e.g. "Family support")
* own wallet  -> outside    : EXPENSE (e.g. "Gifts & family")
* a fee (in the sent currency) is booked as an extra EXPENSE "Transfer fees"
  in the sending wallet.

Where a side's currency equals the user's base or home currency on the other
side, the user's effective rate is frozen on the transaction (rate source
USER); other conversions use the market rate.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.errors import ApiError, NotFound
from app.extensions import db
from app.models import Category, CategoryKind, Remittance, Transaction, TransactionKind, User

from . import category_service, fx_service, transaction_service, wallet_service
from .money import ZERO, convert, money, rate, to_decimal

DEFAULT_INCOME_CATEGORY = "Family support"
DEFAULT_EXPENSE_CATEGORY = "Gifts & family"
FEE_CATEGORY = "Transfer fees"


@dataclass(frozen=True)
class TransferMaths:
    effective_rate: Decimal  # 1 sent unit = x received units
    market_rate: Decimal | None
    hidden_cost_received: Decimal | None  # in received currency, before fees


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------
def effective_rate(sent, received) -> Decimal:
    """Received / sent, 8 decimals (TC-R01)."""
    sent, received = to_decimal(sent), to_decimal(received)
    if sent <= 0 or received <= 0:
        raise ValueError("Amounts must be positive.")
    return rate(received / sent)


def transfer_maths(sent, received, market_rate) -> TransferMaths:
    """Effective rate and the amount lost against the market rate (TC-R02).

    hidden cost = sent x market rate - received   (in the received currency)
    """
    eff = effective_rate(sent, received)
    if market_rate is None:
        return TransferMaths(eff, None, None)
    lost = money(to_decimal(sent) * to_decimal(market_rate) - to_decimal(received))
    return TransferMaths(eff, rate(market_rate), lost)


def side_rates(
    own_ccy: str, other_ccy: str, rate_own_to_other: Decimal, base: str, home: str
) -> tuple[Decimal | None, Decimal | None]:
    """User rates to freeze on one side of a transfer.

    If the *other* currency is the user's base (or home) currency, the
    transfer itself tells us the true rate own -> base (or home). Otherwise
    None is returned and the market rate is used.
    """
    to_base = rate_own_to_other if other_ccy == base and own_ccy != base else None
    to_home = rate_own_to_other if other_ccy == home and own_ccy != home else None
    return to_base, to_home


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
def get_remittance(user_id: uuid.UUID, remittance_id: uuid.UUID) -> Remittance:
    rem = db.session.get(Remittance, remittance_id)
    if rem is None or rem.user_id != user_id:
        raise NotFound("Remittance")
    return rem


def list_remittances(user_id: uuid.UUID) -> list[Remittance]:
    return list(
        db.session.scalars(
            select(Remittance)
            .where(Remittance.user_id == user_id)
            .order_by(Remittance.remit_date.desc(), Remittance.created_at.desc())
        )
    )


def summary(remittances: list[Remittance], year: int) -> dict:
    """Total hidden cost (base currency) this year and overall."""

    def total(items):
        return money(sum((r.hidden_cost_base or ZERO for r in items), ZERO))

    this_year = [r for r in remittances if r.remit_date.year == year]
    return {
        "count": len(remittances),
        "hidden_cost_total": str(total(remittances)),
        "hidden_cost_year": str(total(this_year)),
        "year": year,
    }


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def _system_category(name: str, kind: CategoryKind) -> uuid.UUID:
    cat = db.session.scalar(
        select(Category).where(
            Category.user_id.is_(None), Category.name == name, Category.kind == kind
        )
    )
    if cat is None:  # pragma: no cover - seeded master data
        raise ApiError(f"Category '{name}' is missing.", 500, "INTERNAL_ERROR")
    return cat.id


def _invalid(field: str, message: str) -> ApiError:
    return ApiError(message, 422, "VALIDATION_ERROR", {field: [message]})


def create_remittance(user: User, data: dict) -> Remittance:
    """Record a transfer and its transactions in one database transaction."""
    from_w = (
        wallet_service.get_wallet(user.id, data["from_wallet_id"])
        if data.get("from_wallet_id")
        else None
    )
    to_w = (
        wallet_service.get_wallet(user.id, data["to_wallet_id"])
        if data.get("to_wallet_id")
        else None
    )
    if from_w is None and to_w is None:
        raise _invalid("to_wallet_id", "Choose at least one of your wallets.")
    if from_w is not None and to_w is not None and from_w.id == to_w.id:
        raise _invalid("to_wallet_id", "Choose two different wallets.")

    sent_ccy = from_w.currency_code if from_w else data.get("sent_currency")
    recv_ccy = to_w.currency_code if to_w else data.get("received_currency")
    if not sent_ccy:
        raise _invalid("sent_currency", "Which currency was sent?")
    if not recv_ccy:
        raise _invalid("received_currency", "Which currency was received?")

    sent, received = money(data["sent_amount"]), money(data["received_amount"])
    fee = money(data["fee_amount"]) if data.get("fee_amount") is not None else None
    if fee is not None and fee > 0 and from_w is None:
        raise _invalid("fee_amount", "A fee can only be booked from one of your wallets.")
    on: date = data["remit_date"]

    # Category for the outside side (income from family / expense to family).
    category_id = data.get("category_id")
    if from_w is None or to_w is None:
        kind = CategoryKind.INCOME if from_w is None else CategoryKind.EXPENSE
        if category_id is None:
            default = DEFAULT_INCOME_CATEGORY if from_w is None else DEFAULT_EXPENSE_CATEGORY
            category_id = _system_category(default, kind)
        else:
            cat = category_service.get_category(user.id, category_id)
            if cat.kind != kind:
                raise _invalid("category_id", f"Choose an {kind.value.lower()} category.")

    try:
        market = fx_service.get_rate(sent_ccy, recv_ccy, on).rate
    except fx_service.UnknownCurrency:
        market = None
    maths = transfer_maths(sent, received, market)

    hidden_base = None
    if maths.hidden_cost_received is not None:
        hidden_base = convert(
            maths.hidden_cost_received, fx_service.get_rate(recv_ccy, user.base_currency, on).rate
        )
        if fee:
            hidden_base = money(
                hidden_base
                + convert(fee, fx_service.get_rate(sent_ccy, user.base_currency, on).rate)
            )

    rem = Remittance(
        user_id=user.id,
        from_wallet_id=from_w.id if from_w else None,
        to_wallet_id=to_w.id if to_w else None,
        sent_amount=sent,
        sent_currency=sent_ccy,
        received_amount=received,
        received_currency=recv_ccy,
        fee_amount=fee,
        provider=data.get("provider"),
        remit_date=on,
        effective_rate=maths.effective_rate,
        market_rate=maths.market_rate,
        hidden_cost_base=hidden_base,
        category_id=category_id,
        note=data.get("note"),
    )
    db.session.add(rem)
    db.session.flush()

    inverse = rate(Decimal(1) / maths.effective_rate)
    common = {
        "txn_date": on,
        "note": data.get("note") or data.get("provider"),
        "remittance_id": rem.id,
    }

    if from_w is not None:
        to_base, to_home = side_rates(
            sent_ccy, recv_ccy, maths.effective_rate, user.base_currency, user.home_currency
        )
        transaction_service.record(
            user,
            wallet_id=from_w.id,
            kind=TransactionKind.TRANSFER_OUT if to_w else TransactionKind.EXPENSE,
            amount=sent,
            category_id=None if to_w else category_id,
            rate_to_base=to_base,
            rate_to_home=to_home,
            **common,
        )
        if fee:
            transaction_service.record(
                user,
                wallet_id=from_w.id,
                kind=TransactionKind.EXPENSE,
                amount=fee,
                category_id=_system_category(FEE_CATEGORY, CategoryKind.EXPENSE),
                **{**common, "note": f"Fee: {data.get('provider') or 'transfer'}"},
            )
    if to_w is not None:
        to_base, to_home = side_rates(
            recv_ccy, sent_ccy, inverse, user.base_currency, user.home_currency
        )
        transaction_service.record(
            user,
            wallet_id=to_w.id,
            kind=TransactionKind.TRANSFER_IN if from_w else TransactionKind.INCOME,
            amount=received,
            category_id=None if from_w else category_id,
            rate_to_base=to_base,
            rate_to_home=to_home,
            **common,
        )
    return rem


def delete_remittance(user: User, remittance_id: uuid.UUID) -> None:
    """Delete a remittance together with the transactions it created."""
    rem = get_remittance(user.id, remittance_id)
    for txn in db.session.scalars(select(Transaction).where(Transaction.remittance_id == rem.id)):
        db.session.delete(txn)
    db.session.flush()
    db.session.delete(rem)
    db.session.flush()
