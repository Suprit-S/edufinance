"""Wallets, transactions and remittances (international transfers)."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, Money, Rate, TimestampMixin, UUIDPkMixin, pg_enum
from .enums import RateSource, TransactionKind, WalletType


class Wallet(UUIDPkMixin, TimestampMixin, Base):
    """A named pot of money held in exactly one currency."""

    __tablename__ = "wallets"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_wallets_user_name"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )
    wallet_type: Mapped[WalletType] = mapped_column(pg_enum(WalletType), nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(Money, nullable=False, default=Decimal("0"))
    opening_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="wallet", cascade="all, delete-orphan"
    )


class Remittance(UUIDPkMixin, TimestampMixin, Base):
    """A real currency exchange entered by the user (ADR-0003).

    ``from_wallet_id`` NULL = money came from outside (e.g. parents);
    ``to_wallet_id`` NULL = money left to outside (e.g. sent home to family).
    """

    __tablename__ = "remittances"
    __table_args__ = (
        CheckConstraint(
            "from_wallet_id IS NOT NULL OR to_wallet_id IS NOT NULL", name="has_own_wallet"
        ),
        CheckConstraint("sent_amount > 0 AND received_amount > 0", name="amounts_positive"),
        CheckConstraint("fee_amount IS NULL OR fee_amount >= 0", name="fee_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_wallet_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("wallets.id", ondelete="SET NULL")
    )
    to_wallet_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("wallets.id", ondelete="SET NULL")
    )
    sent_amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    sent_currency: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )
    received_amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    received_currency: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )
    fee_amount: Mapped[Decimal | None] = mapped_column(Money)  # in sent currency
    provider: Mapped[str | None] = mapped_column(String(60))
    remit_date: Mapped[date] = mapped_column(Date, nullable=False)
    effective_rate: Mapped[Decimal] = mapped_column(Rate, nullable=False)  # received / sent
    market_rate: Mapped[Decimal | None] = mapped_column(Rate)
    hidden_cost_base: Mapped[Decimal | None] = mapped_column(Money)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="SET NULL")
    )
    note: Mapped[str | None] = mapped_column(String(255))

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="remittance")


class Transaction(UUIDPkMixin, TimestampMixin, Base):
    """One money movement in one wallet, always in the wallet's currency.

    Converted values are frozen at save time and never recalculated
    (rate freezing, ADR-0003). Rates mean: 1 unit of ``currency_code`` =
    ``rate_to_base`` units of the user's base currency.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("rate_to_base > 0 AND rate_to_home > 0", name="rates_positive"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="RESTRICT")
    )
    kind: Mapped[TransactionKind] = mapped_column(pg_enum(TransactionKind), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    currency_code: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )
    txn_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(String(255))
    phase_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("life_phases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # True when the user picked the phase by hand; such rows are not
    # re-assigned when phase dates change (ADR-0005).
    phase_is_manual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rate_to_base: Mapped[Decimal] = mapped_column(Rate, nullable=False)
    rate_to_home: Mapped[Decimal] = mapped_column(Rate, nullable=False)
    amount_base: Mapped[Decimal] = mapped_column(Money, nullable=False)
    amount_home: Mapped[Decimal] = mapped_column(Money, nullable=False)
    rate_source: Mapped[RateSource] = mapped_column(pg_enum(RateSource), nullable=False)
    remittance_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("remittances.id", ondelete="CASCADE"), index=True
    )

    wallet: Mapped[Wallet] = relationship(back_populates="transactions")
    remittance: Mapped[Remittance | None] = relationship(back_populates="transactions")
