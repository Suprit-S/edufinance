"""SQLAlchemy models. Importing this package registers every table with the
metadata, which Alembic needs for autogeneration."""

from .enums import (  # noqa: F401
    CategoryKind,
    FxSource,
    Gender,
    LoanPaymentType,
    LoanStatus,
    PhaseType,
    RateSource,
    TransactionKind,
    WalletType,
)
from .loan import Loan, LoanPayment  # noqa: F401
from .master import Category, Country, Currency, FxRate  # noqa: F401
from .plan import MonthlyPlanItem  # noqa: F401
from .user import LifePhase, RevokedToken, User  # noqa: F401
from .wallet import Remittance, Transaction, Wallet  # noqa: F401
