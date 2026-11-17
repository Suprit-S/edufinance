"""Master (reference) data: currencies, countries, categories, FX rate cache.

Validating against master tables instead of free text gives referential
integrity (Phase 1, FR10).
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Rate, UUIDPkMixin, pg_enum, utcnow
from .enums import CategoryKind, FxSource, PhaseType


class Currency(Base):
    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)  # ISO 4217
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    symbol: Mapped[str] = mapped_column(String(5), nullable=False)
    minor_units: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=2)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "symbol": self.symbol,
            "minor_units": self.minor_units,
        }


class Country(Base):
    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(String(2), primary_key=True)  # ISO 3166-1 alpha-2
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    default_currency: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )

    def to_dict(self) -> dict:
        return {"code": self.code, "name": self.name, "default_currency": self.default_currency}


class Category(UUIDPkMixin, Base):
    """Income/expense category. ``user_id`` NULL means a system category
    visible to everyone; otherwise it is a user's custom category."""

    __tablename__ = "categories"
    __table_args__ = (
        # NULLS NOT DISTINCT: also prevents duplicate *system* categories.
        UniqueConstraint(
            "user_id",
            "name",
            "kind",
            name="uq_categories_user_name_kind",
            postgresql_nulls_not_distinct=True,
        ),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    kind: Mapped[CategoryKind] = mapped_column(pg_enum(CategoryKind), nullable=False)
    group_name: Mapped[str] = mapped_column(String(40), nullable=False)
    default_phase_type: Mapped[PhaseType | None] = mapped_column(pg_enum(PhaseType))
    # False for money that is not really "earned", e.g. a loan disbursement
    # (it must not count towards the Target to Earn; ADR-0008).
    counts_as_earned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "kind": self.kind.value,
            "group_name": self.group_name,
            "default_phase_type": self.default_phase_type.value
            if self.default_phase_type
            else None,
            "counts_as_earned": self.counts_as_earned,
            "is_system": self.is_system,
        }


class FxRate(UUIDPkMixin, Base):
    """Cached exchange rate: 1 ``base_currency`` = ``rate`` ``quote_currency``."""

    __tablename__ = "fx_rates"
    __table_args__ = (
        UniqueConstraint(
            "base_currency", "quote_currency", "rate_date", name="uq_fx_rates_pair_date"
        ),
        CheckConstraint("rate > 0", name="rate_positive"),
    )

    base_currency: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )
    quote_currency: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )
    rate: Mapped[Decimal] = mapped_column(Rate, nullable=False)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[FxSource] = mapped_column(pg_enum(FxSource), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
