"""Reusable column types and mixins.

Money is ALWAYS stored as exact decimals (ADR-0002): NUMERIC(14,2) for
amounts and NUMERIC(18,8) for exchange rates. Floats are never used because
binary floating point cannot represent values such as 0.1 exactly.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db

Money = Numeric(14, 2, asdecimal=True)
Rate = Numeric(18, 8, asdecimal=True)


def utcnow() -> datetime:
    return datetime.now(UTC)


def pg_enum(enum_cls):
    """Native PostgreSQL enum stored by member *name* (e.g. 'EXPENSE')."""
    return Enum(enum_cls, name=enum_cls.__name__.lower(), native_enum=True)


class UUIDPkMixin:
    """UUID primary keys: IDs of user data cannot be guessed (ADR-0004)."""

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class Base(db.Model):
    __abstract__ = True
