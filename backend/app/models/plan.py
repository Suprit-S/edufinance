"""Monthly Plan: recurring obligations that define the minimum monthly target."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Money, TimestampMixin, UUIDPkMixin


class MonthlyPlanItem(UUIDPkMixin, TimestampMixin, Base):
    """One recurring obligation, e.g. "Rent 420 EUR".

    A line with ``loan_id`` set is the EMI of that loan; it is created and kept
    in sync automatically, so every EMI is part of the target (ADR-0008).
    """

    __tablename__ = "monthly_plan_items"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="valid_range"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    currency_code: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
    phase_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("life_phases.id", ondelete="SET NULL")
    )
    loan_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("loans.id", ondelete="CASCADE"), unique=True
    )
