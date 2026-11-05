"""User account, life phases and revoked JWTs."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPkMixin, pg_enum
from .enums import Gender, PhaseType


class User(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("arrival_date >= planning_start_date", name="arrival_after_planning"),
        CheckConstraint("study_end_date > study_start_date", name="study_end_after_start"),
        CheckConstraint("settling_in_days BETWEEN 0 AND 365", name="settling_in_range"),
    )

    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    # Only a salted bcrypt hash is stored; it is never serialised (NFR4).
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Age is computed from the date of birth and never stored.
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender | None] = mapped_column(pg_enum(Gender))
    home_currency: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )
    base_currency: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )
    destination_country: Mapped[str] = mapped_column(
        String(2), ForeignKey("countries.code"), nullable=False
    )
    planning_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    arrival_date: Mapped[date] = mapped_column(Date, nullable=False)
    study_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    study_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    settling_in_days: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=60)

    phases: Mapped[list["LifePhase"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="LifePhase.start_date",
    )

    def age_on(self, on: date) -> int:
        """Completed years of age on a given date."""
        dob = self.date_of_birth
        return on.year - dob.year - ((on.month, on.day) < (dob.month, dob.day))


class LifePhase(UUIDPkMixin, Base):
    """A period of the user's life (see ADR-0005). ``end_date`` NULL = open-ended."""

    __tablename__ = "life_phases"
    __table_args__ = (
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="end_after_start"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phase_type: Mapped[PhaseType] = mapped_column(pg_enum(PhaseType), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    # System phases are created from the profile dates and kept in sync with them.
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    user: Mapped[User] = relationship(back_populates="phases")


class RevokedToken(Base):
    """JWT IDs revoked on logout; checked on every authenticated request."""

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
