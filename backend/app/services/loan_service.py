"""Loan Planner (FR-28 to FR-34, ADR-0007, ADR-0008).

Formulas
--------
monthly interest   = outstanding x annual rate / 12, rounded to cents
EMI split          = interest first, the rest reduces the principal
part-payment       = 100 % principal
payoff simulation  = repeat the EMI month by month until the balance is 0
interest saved     = future interest without the part-payment
                     - future interest with it (both at the normal EMI)
EMIs saved         = months without - months with
affordability      = average monthly surplus (earned - spent, last 3 full
                     months) minus a 20 % safety buffer, compared with the
                     user's minimum part-payment
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from flask import current_app
from sqlalchemy import select

from app.errors import ApiError, Conflict, NotFound
from app.extensions import db
from app.models import (
    Category,
    CategoryKind,
    Loan,
    LoanPayment,
    LoanPaymentType,
    LoanStatus,
    Transaction,
    TransactionKind,
    User,
)

from . import fx_service, plan_service, transaction_service, wallet_service
from .money import ZERO, convert, money, to_decimal

MAX_MONTHS = 600  # 50 years: stop simulating loans that never end


@dataclass
class Simulation:
    months: int | None  # None = EMI does not cover the interest
    total_interest: Decimal
    schedule: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pure formulas
# ---------------------------------------------------------------------------
def monthly_interest(balance, annual_rate_pct) -> Decimal:
    """Interest for one month (TC-L01)."""
    return money(to_decimal(balance) * to_decimal(annual_rate_pct) / Decimal(1200))


def split_emi(balance, annual_rate_pct, amount) -> tuple[Decimal, Decimal]:
    """(interest part, principal part) of an EMI. A payment smaller than the
    interest only pays interest; the principal part never exceeds the balance."""
    balance, amount = money(balance), money(amount)
    interest = monthly_interest(balance, annual_rate_pct)
    interest_part = min(interest, amount)
    principal_part = min(money(amount - interest_part), balance)
    return interest_part, principal_part


def simulate(balance, annual_rate_pct, emi, keep_schedule: bool = False) -> Simulation:
    """Month-by-month repayment at a fixed EMI (TC-L02).

    The last payment is smaller: it is only the remaining balance plus interest.
    """
    balance, emi = money(balance), money(emi)
    if balance <= 0:
        return Simulation(0, ZERO)
    if emi <= monthly_interest(balance, annual_rate_pct):
        return Simulation(None, ZERO)
    total, months, rows = ZERO, 0, []
    while balance > 0 and months < MAX_MONTHS:
        interest = monthly_interest(balance, annual_rate_pct)
        principal = min(emi - interest, balance)
        balance = money(balance - principal)
        total += interest
        months += 1
        if keep_schedule:
            rows.append(
                {
                    "month": months,
                    "payment": str(money(interest + principal)),
                    "interest": str(interest),
                    "principal": str(principal),
                    "balance": str(balance),
                }
            )
    if balance > 0:  # pragma: no cover - only for absurd inputs
        return Simulation(None, money(total), rows)
    return Simulation(months, money(total), rows)


def part_payment_effect(balance, annual_rate_pct, emi, extra) -> tuple[Decimal, int]:
    """(interest saved, EMIs saved) by paying ``extra`` now (TC-L03)."""
    without = simulate(balance, annual_rate_pct, emi)
    with_extra = simulate(money(to_decimal(balance) - to_decimal(extra)), annual_rate_pct, emi)
    if without.months is None or with_extra.months is None:
        return ZERO, 0
    return money(
        without.total_interest - with_extra.total_interest
    ), without.months - with_extra.months


def affordability_verdict(avg_surplus, buffer_share, min_part_payment) -> dict:
    """Can the minimum part-payment be paid from the surplus? (TC-L06, TC-L07)"""
    avg = money(avg_surplus)
    buffered = money(avg * (Decimal(1) - to_decimal(buffer_share))) if avg > 0 else ZERO
    target = money(min_part_payment)
    if buffered >= target:
        status, months = "AFFORDABLE", 0
    elif buffered > 0:
        status, months = "SAVE", math.ceil(target / buffered)
    else:
        status, months = "NOT_AFFORDABLE", None
    return {
        "status": status,
        "months_needed": months,
        "avg_surplus": avg,
        "buffered_surplus": buffered,
        "min_part_payment_base": target,
    }


# ---------------------------------------------------------------------------
# Loans
# ---------------------------------------------------------------------------
def get_loan(user_id: uuid.UUID, loan_id: uuid.UUID) -> Loan:
    loan = db.session.get(Loan, loan_id)
    if loan is None or loan.user_id != user_id:
        raise NotFound("Loan")
    return loan


def list_loans(user_id: uuid.UUID) -> list[Loan]:
    return list(
        db.session.scalars(
            select(Loan).where(Loan.user_id == user_id).order_by(Loan.status, Loan.created_at)
        )
    )


def _plan_window(loan: Loan) -> tuple[date, date | None]:
    """From when to when the EMI belongs to the Monthly Plan."""
    start = (loan.emi_start_date or loan.created_at.date()).replace(day=1)
    if loan.status == LoanStatus.CLOSED:
        last = loan.payments[-1].paid_on if loan.payments else date.today()
        return start, max(start, plan_service.month_end(last))
    return start, None


def _sync_plan(loan: Loan) -> None:
    db.session.flush()
    valid_from, valid_to = _plan_window(loan)
    plan_service.sync_loan_item(loan, valid_from, valid_to)


def _check_wallet(user_id, wallet_id, currency) -> None:
    if wallet_id is None:
        return
    wallet = wallet_service.get_wallet(user_id, wallet_id)
    if wallet.currency_code != currency:
        raise ApiError(
            f"Choose a wallet in {currency} (the loan currency).",
            422,
            "VALIDATION_ERROR",
            {"wallet_id": [f"Wallet must be in {currency}."]},
        )


def create_loan(user: User, data: dict) -> Loan:
    _check_wallet(user.id, data.get("default_wallet_id"), data["currency_code"])
    loan = Loan(
        user_id=user.id,
        name=data["name"],
        lender=data.get("lender"),
        currency_code=data["currency_code"],
        annual_rate_pct=to_decimal(data["annual_rate_pct"]),
        sanctioned_amount=money(data["sanctioned_amount"]),
        outstanding_amount=money(data["outstanding_amount"]),
        emi_amount=money(data["emi_amount"]),
        emi_start_date=data.get("emi_start_date"),
        min_part_payment=money(data["min_part_payment"]) if data.get("min_part_payment") else None,
        default_wallet_id=data.get("default_wallet_id"),
        note=data.get("note"),
        status=LoanStatus.ACTIVE if money(data["outstanding_amount"]) > 0 else LoanStatus.CLOSED,
    )
    db.session.add(loan)
    _sync_plan(loan)
    return loan


def update_loan(user: User, loan_id: uuid.UUID, data: dict) -> Loan:
    """Edit a loan. Correcting ``outstanding_amount`` is allowed at any time
    (FR-29), e.g. when the bank added moratorium interest."""
    loan = get_loan(user.id, loan_id)
    if "currency_code" in data and data["currency_code"] != loan.currency_code and loan.payments:
        raise ApiError(
            "The currency cannot change once payments exist.",
            422,
            "VALIDATION_ERROR",
            {"currency_code": ["Loan already has payments."]},
        )
    _check_wallet(
        user.id, data.get("default_wallet_id"), data.get("currency_code", loan.currency_code)
    )
    for key in ("name", "lender", "currency_code", "emi_start_date", "default_wallet_id", "note"):
        if key in data:
            setattr(loan, key, data[key])
    for key in ("sanctioned_amount", "outstanding_amount", "emi_amount"):
        if key in data:
            setattr(loan, key, money(data[key]))
    if "annual_rate_pct" in data:
        loan.annual_rate_pct = to_decimal(data["annual_rate_pct"])
    if "min_part_payment" in data:
        loan.min_part_payment = (
            money(data["min_part_payment"]) if data["min_part_payment"] else None
        )
    if "outstanding_amount" in data:
        loan.status = LoanStatus.ACTIVE if loan.outstanding_amount > 0 else LoanStatus.CLOSED
    _sync_plan(loan)
    return loan


def delete_loan(user: User, loan_id: uuid.UUID) -> None:
    """Delete a loan, its payments and EMI plan line. Wallet expenses created
    by payments stay as normal (editable) transactions - the money was paid."""
    loan = get_loan(user.id, loan_id)
    db.session.delete(loan)
    db.session.flush()


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------
def record_payment(user: User, loan_id: uuid.UUID, data: dict) -> LoanPayment:
    """Record an EMI or part-payment; split and savings are frozen (ADR-0007)."""
    loan = get_loan(user.id, loan_id)
    if loan.status != LoanStatus.ACTIVE:
        raise Conflict("This loan is closed.")
    amount, paid_on = money(data["amount"]), data["paid_on"]
    ptype = LoanPaymentType(data["payment_type"])
    if loan.payments and paid_on < loan.payments[-1].paid_on:
        raise ApiError(
            "Payments must be recorded in date order.",
            422,
            "VALIDATION_ERROR",
            {"paid_on": [f"Must be on or after {loan.payments[-1].paid_on.isoformat()}."]},
        )

    before = loan.outstanding_amount
    saved, emis_saved = ZERO, 0
    if ptype == LoanPaymentType.EMI:
        interest, principal = split_emi(before, loan.annual_rate_pct, amount)
        if amount > money(interest + principal):
            maximum = money(interest + principal)
            raise ApiError(
                f"The final payment is {maximum}.",
                422,
                "VALIDATION_ERROR",
                {"amount": [f"At most {maximum} (balance plus this month's interest)."]},
            )
    else:
        if amount > before:
            raise ApiError(
                "Part-payment is larger than the outstanding amount.",
                422,
                "VALIDATION_ERROR",
                {"amount": [f"At most {before}."]},
            )
        interest, principal = ZERO, amount
        saved, emis_saved = part_payment_effect(
            before, loan.annual_rate_pct, loan.emi_amount, amount
        )

    # No "wallet_id" key -> the loan's default wallet; explicit null -> no wallet.
    wallet_id = data["wallet_id"] if "wallet_id" in data else loan.default_wallet_id
    _check_wallet(user.id, wallet_id, loan.currency_code)
    txn = None
    if wallet_id is not None:
        category = "Loan EMI" if ptype == LoanPaymentType.EMI else "Loan part-payment"
        txn = transaction_service.record(
            user,
            wallet_id=wallet_id,
            kind=TransactionKind.EXPENSE,
            amount=amount,
            txn_date=paid_on,
            category_id=_category_id(category),
            note=f"{loan.name}: {category}",
        )

    payment = LoanPayment(
        loan_id=loan.id,
        payment_type=ptype,
        amount=amount,
        paid_on=paid_on,
        interest_part=interest,
        principal_part=principal,
        balance_before=before,
        balance_after=money(before - principal),
        interest_saved=saved,
        emis_saved=emis_saved,
        transaction_id=txn.id if txn else None,
        note=data.get("note"),
    )
    db.session.add(payment)
    loan.outstanding_amount = payment.balance_after
    if loan.outstanding_amount == 0:
        loan.status = LoanStatus.CLOSED
    db.session.flush()
    db.session.refresh(loan)
    _sync_plan(loan)
    return payment


def _category_id(name: str) -> uuid.UUID:
    return db.session.scalar(
        select(Category.id).where(
            Category.user_id.is_(None), Category.name == name, Category.kind == CategoryKind.EXPENSE
        )
    )


def undo_payment(user: User, loan_id: uuid.UUID, payment_id: uuid.UUID) -> None:
    """Undo the most recent payment only; restores the balance (FR-33)."""
    loan = get_loan(user.id, loan_id)
    payment = db.session.get(LoanPayment, payment_id)
    if payment is None or payment.loan_id != loan.id:
        raise NotFound("Payment")
    latest = max(loan.payments, key=lambda p: (p.paid_on, p.created_at))
    if latest.id != payment.id:
        raise Conflict("Only the most recent payment can be undone.")
    loan.outstanding_amount = payment.balance_before
    loan.status = LoanStatus.ACTIVE
    txn_id = payment.transaction_id
    db.session.delete(payment)
    db.session.flush()
    if txn_id:
        txn = db.session.get(Transaction, txn_id)
        if txn is not None:
            db.session.delete(txn)
    db.session.flush()
    db.session.refresh(loan)
    _sync_plan(loan)


# ---------------------------------------------------------------------------
# Read models
# ---------------------------------------------------------------------------
def loan_summary(loan: Loan, today: date | None = None, schedule: bool = False) -> dict:
    """Totals, payoff forecast and (optionally) the remaining schedule (FR-32)."""
    today = today or date.today()
    sim = simulate(
        loan.outstanding_amount, loan.annual_rate_pct, loan.emi_amount, keep_schedule=schedule
    )
    first_due = max(today.replace(day=1), (loan.emi_start_date or today).replace(day=1))
    payoff = plan_service.add_months(first_due, sim.months - 1) if sim.months else None
    paid = loan.payments
    result = {
        "interest_paid": str(money(sum((p.interest_part for p in paid), ZERO))),
        "principal_paid": str(money(sum((p.principal_part for p in paid), ZERO))),
        "total_paid": str(money(sum((p.amount for p in paid), ZERO))),
        "interest_saved": str(money(sum((p.interest_saved for p in paid), ZERO))),
        "emis_saved": sum(p.emis_saved for p in paid),
        "months_to_payoff": sim.months,
        "future_interest": str(sim.total_interest),
        "payoff_month": payoff.strftime("%Y-%m") if payoff else None,
        "emi_covers_interest": sim.months is not None or loan.outstanding_amount == 0,
        "repaid_pct": float(
            round(
                (loan.sanctioned_amount - min(loan.outstanding_amount, loan.sanctioned_amount))
                * 100
                / loan.sanctioned_amount,
                1,
            )
        ),
    }
    if schedule:
        result["schedule"] = sim.schedule
    return result


def affordability(user: User, loan: Loan, today: date | None = None) -> dict | None:
    """Part-payment affordability estimate for a loan (FR-34)."""
    if not loan.min_part_payment or loan.status != LoanStatus.ACTIVE:
        return None
    today = today or date.today()
    cfg = current_app.config
    months = cfg["AFFORDABILITY_LOOKBACK_MONTHS"]
    current = today.replace(day=1)
    surpluses = []
    for i in range(1, months + 1):
        m = plan_service.add_months(current, -i)
        t = plan_service.month_totals(user.id, m, plan_service.month_end(m))
        surpluses.append(t["earned"] - t["spent"])
    avg = money(sum(surpluses, ZERO) / len(surpluses))
    fx = fx_service.get_rate(loan.currency_code, user.base_currency, today)
    min_base = convert(loan.min_part_payment, fx.rate)
    verdict = affordability_verdict(avg, cfg["AFFORDABILITY_SAFETY_BUFFER"], min_base)
    amount = min(loan.min_part_payment, loan.outstanding_amount)
    saved, emis = part_payment_effect(
        loan.outstanding_amount, loan.annual_rate_pct, loan.emi_amount, amount
    )
    return {
        **{k: (str(v) if isinstance(v, Decimal) else v) for k, v in verdict.items()},
        "currency": user.base_currency,
        "min_part_payment": str(loan.min_part_payment),
        "lookback_months": months,
        "buffer_pct": float(cfg["AFFORDABILITY_SAFETY_BUFFER"] * 100),
        "interest_saved_if_paid": str(saved),
        "emis_saved_if_paid": emis,
        "estimated_rate": fx.estimated,
    }
