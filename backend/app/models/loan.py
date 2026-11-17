"""Loans and loan payments (ADR-0007: user-maintained outstanding balance)."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, SmallInteger, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, Money, TimestampMixin, UUIDPkMixin, pg_enum
from .enums import LoanPaymentType, LoanStatus


class Loan(UUIDPkMixin, TimestampMixin, Base):
    """A loan the user repays. The outstanding balance is entered by the user
    and can be corrected at any time (e.g. when the bank adds interest during
    the moratorium); recorded payments reduce it automatically."""

    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint("annual_rate_pct >= 0 AND annual_rate_pct < 100", name="rate_range"),
        CheckConstraint("sanctioned_amount > 0", name="sanctioned_positive"),
        CheckConstraint("outstanding_amount >= 0", name="outstanding_non_negative"),
        CheckConstraint("emi_amount > 0", name="emi_positive"),
        CheckConstraint(
            "min_part_payment IS NULL OR min_part_payment > 0", name="min_part_payment_positive"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    lender: Mapped[str | None] = mapped_column(String(80))
    currency_code: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )
    annual_rate_pct: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    sanctioned_amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    outstanding_amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    emi_amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    # First month the EMI is due; NULL = already repaying. Before this date the
    # EMI line is not part of the Monthly Plan (e.g. during the moratorium).
    emi_start_date: Mapped[date | None] = mapped_column(Date)
    # User-chosen minimum part-payment, used by the affordability check.
    min_part_payment: Mapped[Decimal | None] = mapped_column(Money)
    default_wallet_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("wallets.id", ondelete="SET NULL")
    )
    status: Mapped[LoanStatus] = mapped_column(
        pg_enum(LoanStatus), nullable=False, default=LoanStatus.ACTIVE
    )
    note: Mapped[str | None] = mapped_column(String(255))

    payments: Mapped[list["LoanPayment"]] = relationship(
        back_populates="loan",
        cascade="all, delete-orphan",
        order_by="LoanPayment.paid_on",
    )


class LoanPayment(UUIDPkMixin, TimestampMixin, Base):
    """An EMI or part-payment. The split and savings are frozen at save time;
    only the latest payment of a loan may be undone (ADR-0007)."""

    __tablename__ = "loan_payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("balance_after >= 0", name="balance_non_negative"),
    )

    loan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    payment_type: Mapped[LoanPaymentType] = mapped_column(pg_enum(LoanPaymentType), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    paid_on: Mapped[date] = mapped_column(Date, nullable=False)
    interest_part: Mapped[Decimal] = mapped_column(Money, nullable=False)
    principal_part: Mapped[Decimal] = mapped_column(Money, nullable=False)
    balance_before: Mapped[Decimal] = mapped_column(Money, nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Money, nullable=False)
    interest_saved: Mapped[Decimal] = mapped_column(Money, nullable=False, default=Decimal("0"))
    emis_saved: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("transactions.id", ondelete="SET NULL")
    )
    note: Mapped[str | None] = mapped_column(String(255))

    loan: Mapped[Loan] = relationship(back_populates="payments")
