"""Monthly Plan, minimum monthly target and Target to Earn (FR-23 to FR-27, ADR-0008).

* A plan item is a recurring monthly obligation valid from/to a date and,
  optionally, only during one life phase.
* Every loan has one plan item for its EMI, created and kept in sync by the
  loan service; it cannot be edited here.
* Minimum monthly target = sum of the items active in a month, converted to
  the base currency (rate of the month's first day for past months, today's
  rate for the current and future months).
* Earned = income in categories with ``counts_as_earned`` (salary, family
  support, scholarship ...); loan disbursements and own transfers are not
  earned. Spent = all expenses.
"""

from __future__ import annotations

import calendar
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.errors import ApiError, Conflict, NotFound
from app.extensions import db
from app.models import (
    Category,
    CategoryKind,
    LifePhase,
    LoanPayment,
    LoanPaymentType,
    MonthlyPlanItem,
    Transaction,
    TransactionKind,
    User,
)

from . import category_service, fx_service
from .money import ZERO, convert, money

LOAN_EMI_CATEGORY = "Loan EMI"


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
def parse_month(value: str | None, today: date | None = None) -> date:
    """'2026-11' -> date(2026, 11, 1); None -> current month."""
    today = today or date.today()
    if not value:
        return today.replace(day=1)
    try:
        year, month = (int(x) for x in value.split("-"))
        return date(year, month, 1)
    except (ValueError, TypeError) as exc:
        raise ApiError(
            "Use the format YYYY-MM.", 422, "VALIDATION_ERROR", {"month": ["Use YYYY-MM."]}
        ) from exc


def month_end(start: date) -> date:
    return start.replace(day=calendar.monthrange(start.year, start.month)[1])


def add_months(start: date, n: int) -> date:
    index = start.year * 12 + start.month - 1 + n
    return date(index // 12, index % 12 + 1, 1)


def overlaps(a_from: date, a_to: date | None, b_from: date, b_to: date | None) -> bool:
    """Do two date ranges (None = open end) overlap?"""
    return (a_to is None or a_to >= b_from) and (b_to is None or b_to >= a_from)


def item_active(
    valid_from: date,
    valid_to: date | None,
    month_start: date,
    phase_range: tuple[date, date | None] | None = None,
) -> bool:
    """Is a plan item part of the target of a month? (TC-PL02, TC-PL03)"""
    end = month_end(month_start)
    if not overlaps(valid_from, valid_to, month_start, end):
        return False
    return phase_range is None or overlaps(phase_range[0], phase_range[1], month_start, end)


# ---------------------------------------------------------------------------
# Plan items
# ---------------------------------------------------------------------------
def get_item(user_id: uuid.UUID, item_id: uuid.UUID) -> MonthlyPlanItem:
    item = db.session.get(MonthlyPlanItem, item_id)
    if item is None or item.user_id != user_id:
        raise NotFound("Plan item")
    return item


def list_items(user_id: uuid.UUID) -> list[MonthlyPlanItem]:
    return list(
        db.session.scalars(
            select(MonthlyPlanItem)
            .where(MonthlyPlanItem.user_id == user_id)
            .order_by(
                MonthlyPlanItem.loan_id.is_not(None),
                MonthlyPlanItem.valid_from,
                MonthlyPlanItem.name,
            )
        )
    )


def _check_category(user_id, category_id) -> None:
    cat = category_service.get_category(user_id, category_id)
    if cat.kind != CategoryKind.EXPENSE:
        raise ApiError(
            "Plan items are expenses.",
            422,
            "VALIDATION_ERROR",
            {"category_id": ["Choose an expense category."]},
        )


def _check_phase(user_id, phase_id) -> None:
    if phase_id is not None:
        phase = db.session.get(LifePhase, phase_id)
        if phase is None or phase.user_id != user_id:
            raise NotFound("Phase")


def _check_range(valid_from, valid_to) -> None:
    if valid_to is not None and valid_to < valid_from:
        raise ApiError(
            "End must not be before start.",
            422,
            "VALIDATION_ERROR",
            {"valid_to": ["Must not be before 'valid from'."]},
        )


def create_item(user_id: uuid.UUID, data: dict) -> MonthlyPlanItem:
    _check_category(user_id, data["category_id"])
    _check_phase(user_id, data.get("phase_id"))
    _check_range(data["valid_from"], data.get("valid_to"))
    item = MonthlyPlanItem(
        user_id=user_id,
        name=data["name"],
        category_id=data["category_id"],
        amount=money(data["amount"]),
        currency_code=data["currency_code"],
        valid_from=data["valid_from"],
        valid_to=data.get("valid_to"),
        phase_id=data.get("phase_id"),
    )
    db.session.add(item)
    db.session.flush()
    return item


def update_item(user_id: uuid.UUID, item_id: uuid.UUID, data: dict) -> MonthlyPlanItem:
    item = get_item(user_id, item_id)
    if item.loan_id is not None:
        raise Conflict("This EMI line follows its loan. Change the EMI in the Loan Planner.")
    if "category_id" in data:
        _check_category(user_id, data["category_id"])
    if "phase_id" in data:
        _check_phase(user_id, data["phase_id"])
    _check_range(data.get("valid_from", item.valid_from), data.get("valid_to", item.valid_to))
    for key in ("name", "category_id", "currency_code", "valid_from", "valid_to", "phase_id"):
        if key in data:
            setattr(item, key, data[key])
    if "amount" in data:
        item.amount = money(data["amount"])
    db.session.flush()
    return item


def delete_item(user_id: uuid.UUID, item_id: uuid.UUID) -> None:
    item = get_item(user_id, item_id)
    if item.loan_id is not None:
        raise Conflict("This EMI line belongs to a loan. Close or delete the loan instead.")
    db.session.delete(item)
    db.session.flush()


def sync_loan_item(loan, valid_from: date, valid_to: date | None) -> MonthlyPlanItem:
    """Create/update the EMI line of a loan (called by the loan service)."""
    item = db.session.scalar(select(MonthlyPlanItem).where(MonthlyPlanItem.loan_id == loan.id))
    if item is None:
        item = MonthlyPlanItem(
            user_id=loan.user_id,
            loan_id=loan.id,
            category_id=db.session.scalar(
                select(Category.id).where(
                    Category.user_id.is_(None),
                    Category.name == LOAN_EMI_CATEGORY,
                    Category.kind == CategoryKind.EXPENSE,
                )
            ),
        )
        db.session.add(item)
    item.name = f"EMI – {loan.name}"[:60]
    item.amount = loan.emi_amount
    item.currency_code = loan.currency_code
    item.valid_from = valid_from
    item.valid_to = valid_to
    db.session.flush()
    return item


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------
@dataclass
class _Rates:
    """Caches market rates to the base currency for one month."""

    base: str
    on: date
    cache: dict
    estimated: bool = False

    def to_base(self, ccy: str) -> Decimal:
        if ccy not in self.cache:
            result = fx_service.get_rate(ccy, self.base, self.on)
            self.cache[ccy] = result.rate
            self.estimated = self.estimated or result.estimated
        return self.cache[ccy]


def _rates_for(user: User, month_start: date, today: date) -> _Rates:
    on = today if month_end(month_start) >= today else month_start
    return _Rates(user.base_currency, on, {})


def minimum_target(user: User, month_start: date, today: date | None = None) -> dict:
    """Plan lines active in a month, converted to base currency (FR-25)."""
    today = today or date.today()
    rates = _rates_for(user, month_start, today)
    phases = {p.id: (p.start_date, p.end_date) for p in user.phases}
    lines, total = [], ZERO
    for item in list_items(user.id):
        if not item_active(item.valid_from, item.valid_to, month_start, phases.get(item.phase_id)):
            continue
        amount_base = convert(item.amount, rates.to_base(item.currency_code))
        total += amount_base
        lines.append(
            {"item": item, "amount_base": amount_base, "rate": rates.cache[item.currency_code]}
        )
    return {"lines": lines, "total": money(total), "estimated": rates.estimated, "rates": rates}


def month_totals(user_id: uuid.UUID, start: date, end: date) -> dict:
    """Earned, spent and earnings by source in base currency (FR-26, FR-27)."""
    earned_rows = db.session.execute(
        select(Category.name, func.sum(Transaction.amount_base))
        .join(Category, Category.id == Transaction.category_id)
        .where(
            Transaction.user_id == user_id,
            Transaction.kind == TransactionKind.INCOME,
            Category.counts_as_earned.is_(True),
            Transaction.txn_date.between(start, end),
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount_base).desc())
    ).all()
    spent = db.session.scalar(
        select(func.coalesce(func.sum(Transaction.amount_base), 0)).where(
            Transaction.user_id == user_id,
            Transaction.kind == TransactionKind.EXPENSE,
            Transaction.txn_date.between(start, end),
        )
    )
    by_source = [{"source": name, "amount": money(total)} for name, total in earned_rows]
    earned = money(sum((s["amount"] for s in by_source), ZERO))
    return {"earned": earned, "spent": money(spent), "by_source": by_source}


def _actual_for_line(user_id, item: MonthlyPlanItem, start: date, end: date, rate) -> Decimal:
    """What was really paid for a plan line in the month (base currency).
    For an EMI line only EMIs count - part-payments are extra, not the plan."""
    if item.loan_id is not None:
        paid = db.session.scalar(
            select(func.coalesce(func.sum(LoanPayment.amount), 0)).where(
                LoanPayment.loan_id == item.loan_id,
                LoanPayment.payment_type == LoanPaymentType.EMI,
                LoanPayment.paid_on.between(start, end),
            )
        )
        return convert(paid, rate)
    return money(
        db.session.scalar(
            select(func.coalesce(func.sum(Transaction.amount_base), 0)).where(
                Transaction.user_id == user_id,
                Transaction.kind == TransactionKind.EXPENSE,
                Transaction.category_id == item.category_id,
                Transaction.txn_date.between(start, end),
            )
        )
    )


def target_to_earn(user: User, month_start: date, history_months: int = 6, today=None) -> dict:
    """Everything the Target to Earn page shows for one month (FR-26)."""
    today = today or date.today()
    end = month_end(month_start)
    target = minimum_target(user, month_start, today)
    totals = month_totals(user.id, month_start, end)

    lines = []
    for line in target["lines"]:
        item = line["item"]
        actual = _actual_for_line(user.id, item, month_start, end, line["rate"])
        lines.append(
            {
                "id": str(item.id),
                "name": item.name,
                "loan_id": str(item.loan_id) if item.loan_id else None,
                "planned": str(line["amount_base"]),
                "planned_original": str(item.amount),
                "currency_code": item.currency_code,
                "actual": str(actual),
                "difference": str(money(actual - line["amount_base"])),
            }
        )

    history = []
    for i in range(history_months - 1, -1, -1):
        m = add_months(month_start, -i)
        t = month_totals(user.id, m, month_end(m))
        history.append(
            {
                "month": m.strftime("%Y-%m"),
                "target": str(minimum_target(user, m, today)["total"]),
                "earned": str(t["earned"]),
                "spent": str(t["spent"]),
            }
        )

    goal = target["total"]
    earned = totals["earned"]
    return {
        "month": month_start.strftime("%Y-%m"),
        "currency": user.base_currency,
        "target": str(goal),
        "earned": str(earned),
        "spent": str(totals["spent"]),
        "still_to_earn": str(max(money(goal - earned), ZERO)),
        "surplus_over_target": str(max(money(earned - goal), ZERO)),
        "net": str(money(earned - totals["spent"])),
        "progress_pct": float(round(earned * 100 / goal, 1)) if goal > 0 else None,
        "estimated_rates": target["estimated"],
        "by_source": [
            {"source": s["source"], "amount": str(s["amount"])} for s in totals["by_source"]
        ],
        "lines": lines,
        "history": history,
    }
