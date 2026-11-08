"""Wallets and balances (FR-11, FR-17)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import case, func, select, true

from app.errors import ApiError, Conflict, NotFound
from app.extensions import db
from app.models import Transaction, TransactionKind, Wallet

from .money import ZERO, money

# Sign of each transaction kind for a wallet balance.
INFLOW = (TransactionKind.INCOME, TransactionKind.TRANSFER_IN)


def balance_delta(kind: TransactionKind, amount: Decimal) -> Decimal:
    """+amount for money coming in, -amount for money going out (TC-W02)."""
    return amount if kind in INFLOW else -amount


def get_wallet(user_id: uuid.UUID, wallet_id: uuid.UUID) -> Wallet:
    """Return the user's wallet or 404 - also for other users' wallets (NFR-07)."""
    wallet = db.session.get(Wallet, wallet_id)
    if wallet is None or wallet.user_id != user_id:
        raise NotFound("Wallet")
    return wallet


def list_wallets(user_id: uuid.UUID, include_archived: bool = True) -> list[Wallet]:
    stmt = select(Wallet).where(Wallet.user_id == user_id)
    if not include_archived:
        stmt = stmt.where(Wallet.is_archived.is_(False))
    return list(db.session.scalars(stmt.order_by(Wallet.is_archived, Wallet.created_at)))


def balances(user_id: uuid.UUID, as_of=None) -> dict[uuid.UUID, Decimal]:
    """Current balance of every wallet of a user in its own currency:
    opening balance + inflows - outflows (optionally up to a date)."""
    signed = case(
        (Transaction.kind.in_(INFLOW), Transaction.amount),
        else_=-Transaction.amount,
    )
    stmt = (
        select(Wallet.id, Wallet.opening_balance, func.coalesce(func.sum(signed), 0))
        .outerjoin(
            Transaction,
            (Transaction.wallet_id == Wallet.id)
            & ((Transaction.txn_date <= as_of) if as_of else true()),
        )
        .where(Wallet.user_id == user_id)
        .group_by(Wallet.id)
    )
    return {wid: money(opening + delta) for wid, opening, delta in db.session.execute(stmt)}


def _name_taken(user_id, name, exclude_id=None) -> bool:
    stmt = select(Wallet.id).where(
        Wallet.user_id == user_id, func.lower(Wallet.name) == name.lower()
    )
    if exclude_id:
        stmt = stmt.where(Wallet.id != exclude_id)
    return db.session.scalar(stmt) is not None


def create_wallet(user_id: uuid.UUID, data: dict) -> Wallet:
    if _name_taken(user_id, data["name"]):
        raise Conflict(f"You already have a wallet called '{data['name']}'.")
    wallet = Wallet(
        user_id=user_id,
        name=data["name"],
        currency_code=data["currency_code"],
        wallet_type=data["wallet_type"],
        opening_balance=money(data.get("opening_balance", ZERO)),
        opening_date=data["opening_date"],
    )
    db.session.add(wallet)
    db.session.flush()
    return wallet


def has_transactions(wallet_id: uuid.UUID) -> bool:
    return (
        db.session.scalar(select(Transaction.id).where(Transaction.wallet_id == wallet_id).limit(1))
        is not None
    )


def update_wallet(user_id: uuid.UUID, wallet_id: uuid.UUID, data: dict) -> Wallet:
    wallet = get_wallet(user_id, wallet_id)
    if "name" in data and _name_taken(user_id, data["name"], wallet.id):
        raise Conflict(f"You already have a wallet called '{data['name']}'.")
    if (
        "currency_code" in data
        and data["currency_code"] != wallet.currency_code
        and has_transactions(wallet.id)
    ):
        raise ApiError(
            "The currency cannot change once the wallet has transactions.",
            422,
            "VALIDATION_ERROR",
            {"currency_code": ["Wallet already has transactions."]},
        )
    for field in ("name", "currency_code", "wallet_type", "opening_date", "is_archived"):
        if field in data:
            setattr(wallet, field, data[field])
    if "opening_balance" in data:
        wallet.opening_balance = money(data["opening_balance"])
    db.session.flush()
    return wallet


def delete_wallet(user_id: uuid.UUID, wallet_id: uuid.UUID) -> None:
    """Only empty wallets can be deleted; otherwise archive (keeps history)."""
    wallet = get_wallet(user_id, wallet_id)
    if has_transactions(wallet.id):
        raise Conflict("This wallet has transactions. Archive it instead to keep your history.")
    db.session.delete(wallet)
    db.session.flush()
