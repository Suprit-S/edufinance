"""Enumerations shared by models, services and API schemas.

Stored in PostgreSQL as native ENUM types (by name), so invalid values are
rejected by the database itself and not only by the API layer.
"""

import enum


class Gender(enum.StrEnum):
    FEMALE = "FEMALE"
    MALE = "MALE"
    DIVERSE = "DIVERSE"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"


class PhaseType(enum.StrEnum):
    """Life phases of an international student (see glossary: Life phase)."""

    PRE_DEPARTURE = "PRE_DEPARTURE"
    SETTLING_IN = "SETTLING_IN"
    STUDY = "STUDY"
    JOB_SEARCH = "JOB_SEARCH"
    WORK = "WORK"
    CUSTOM = "CUSTOM"


class CategoryKind(enum.StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class WalletType(enum.StrEnum):
    BANK = "BANK"
    CASH = "CASH"
    SAVINGS = "SAVINGS"
    PROOF_OF_FUNDS = "PROOF_OF_FUNDS"


class TransactionKind(enum.StrEnum):
    """INCOME/EXPENSE change the user's net position; TRANSFER_* only move
    money between the user's own wallets and are excluded from earned/spent."""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


class RateSource(enum.StrEnum):
    """Where a frozen exchange rate came from (FR: rate freezing, ADR-0003)."""

    IDENTITY = "IDENTITY"  # same currency, rate = 1
    USER = "USER"  # entered by the user (mandatory for remittances)
    LIVE = "LIVE"  # fetched from the FX API (or its 24h cache)
    FALLBACK = "FALLBACK"  # stale cache or seeded table -> shown as "estimated"


class FxSource(enum.StrEnum):
    API = "API"
    FALLBACK = "FALLBACK"


class LoanStatus(enum.StrEnum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class LoanPaymentType(enum.StrEnum):
    EMI = "EMI"
    PART_PAYMENT = "PART_PAYMENT"
