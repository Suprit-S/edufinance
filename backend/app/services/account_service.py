"""Data rights: export all own data, delete the account (FR-42, GDPR)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select

from app.errors import ApiError
from app.extensions import db
from app.models import (
    Category,
    LifePhase,
    Loan,
    LoanPayment,
    MonthlyPlanItem,
    Remittance,
    RevokedToken,
    Transaction,
    User,
    Wallet,
)

from . import auth_service

# Children first, so no foreign key ever points to a deleted row.
_DELETE_ORDER = (
    (LoanPayment, lambda uid: LoanPayment.loan_id.in_(select(Loan.id).where(Loan.user_id == uid))),
    (MonthlyPlanItem, lambda uid: MonthlyPlanItem.user_id == uid),
    (Transaction, lambda uid: Transaction.user_id == uid),
    (Remittance, lambda uid: Remittance.user_id == uid),
    (Loan, lambda uid: Loan.user_id == uid),
    (Wallet, lambda uid: Wallet.user_id == uid),
    (Category, lambda uid: Category.user_id == uid),
    (RevokedToken, lambda uid: RevokedToken.user_id == uid),
    (LifePhase, lambda uid: LifePhase.user_id == uid),
    (User, lambda uid: User.id == uid),
)


def _plain(value):
    if value is None or isinstance(value, bool | int | str):
        return value
    if hasattr(value, "value"):  # enums
        return value.value
    return str(value)  # Decimal, date, datetime, UUID


def _rows(model, condition) -> list[dict]:
    columns = [c.key for c in model.__table__.columns if c.key != "password_hash"]
    return [
        {c: _plain(getattr(row, c)) for c in columns}
        for row in db.session.scalars(select(model).where(condition))
    ]


def export_data(user: User) -> dict:
    """All data of the user as plain JSON. The password hash is never included."""
    uid = user.id
    return {
        "format": "edufinance-export",
        "version": 1,
        "exported_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "profile": _rows(User, User.id == uid)[0],
        "life_phases": _rows(LifePhase, LifePhase.user_id == uid),
        "wallets": _rows(Wallet, Wallet.user_id == uid),
        "custom_categories": _rows(Category, Category.user_id == uid),
        "transactions": _rows(Transaction, Transaction.user_id == uid),
        "remittances": _rows(Remittance, Remittance.user_id == uid),
        "monthly_plan": _rows(MonthlyPlanItem, MonthlyPlanItem.user_id == uid),
        "loans": _rows(Loan, Loan.user_id == uid),
        "loan_payments": _rows(
            LoanPayment, LoanPayment.loan_id.in_(select(Loan.id).where(Loan.user_id == uid))
        ),
    }


def delete_account(user: User, password: str) -> None:
    """Delete the user and every row that belongs to them, after the password
    was confirmed."""
    if not auth_service.check_password(password, user.password_hash):
        raise ApiError(
            "Password is incorrect.",
            422,
            "VALIDATION_ERROR",
            {"password": ["Incorrect password."]},
        )
    delete_all_data(user.id)


def delete_all_data(user_id) -> None:
    """Remove a user and all their rows (also used to reset the demo user)."""
    db.session.expunge_all()
    for model, condition in _DELETE_ORDER:
        db.session.execute(delete(model).where(condition(user_id)))
    db.session.flush()
