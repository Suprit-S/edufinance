"""Reports and dashboard (FR-37 to FR-41, ADR-0012).

* Every report is calculated for a period: MONTH, YEAR, PHASE or LIFETIME.
* Income and expenses use the frozen base-currency values of the
  transactions, so past reports never change.
* Net worth = wallet balances - outstanding loans, both valued at *today's*
  exchange rate (constant-rate view, ADR-0012), so the curve shows what the
  student did, not how currencies moved.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import case, func, select

from app.errors import ApiError
from app.extensions import db
from app.models import (
    Category,
    LifePhase,
    LoanStatus,
    PhaseType,
    Transaction,
    TransactionKind,
    User,
    Wallet,
)

from . import fx_service, loan_service, plan_service, runway_service, wallet_service
from .money import ZERO, convert, money

PERIOD_KINDS = ("MONTH", "YEAR", "PHASE", "LIFETIME")
TOP_CATEGORIES = 8
ABROAD_PHASES = (PhaseType.PRE_DEPARTURE, PhaseType.SETTLING_IN)


@dataclass(frozen=True)
class Period:
    kind: str
    start: date
    end: date
    label: str
    phase_id: uuid.UUID | None = None  # PHASE reports count the phase's transactions

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "label": self.label,
        }


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
def months_between(start: date, end: date) -> list[date]:
    """First days of all months touched by [start, end] (TC-RP06)."""
    months, current = [], start.replace(day=1)
    while current <= end:
        months.append(current)
        current = plan_service.add_months(current, 1)
    return months


def fold_top(rows: list[tuple[str, Decimal]], top: int = TOP_CATEGORIES) -> list[dict]:
    """Largest ``top`` rows, the rest folded into 'Other' (TC-RP07)."""
    rows = sorted(rows, key=lambda r: r[1], reverse=True)
    result = [{"name": name, "amount": money(amount)} for name, amount in rows[:top]]
    rest = money(sum((amount for _, amount in rows[top:]), ZERO))
    if rest > 0:
        result.append({"name": "Other", "amount": rest})
    return result


def outstanding_on(loan_created: date, payments: list, current: Decimal, day: date) -> Decimal:
    """Outstanding balance of a loan at the end of ``day`` from its payment
    history: balance after the last payment on/before the day, otherwise the
    balance before the first payment (TC-RP05)."""
    if day < loan_created:
        return ZERO
    before = [p for p in payments if p.paid_on <= day]
    if before:
        return before[-1].balance_after
    if payments:
        return payments[0].balance_before
    return current


# ---------------------------------------------------------------------------
# Periods
# ---------------------------------------------------------------------------
def lifetime_start(user: User) -> date:
    first_txn = db.session.scalar(
        select(func.min(Transaction.txn_date)).where(Transaction.user_id == user.id)
    )
    return min(user.planning_start_date, first_txn) if first_txn else user.planning_start_date


def resolve_period(user: User, kind: str, value: str | None, today: date | None = None) -> Period:
    """Turn ?period=…&value=… into dates (FR-37)."""
    today = today or date.today()
    kind = (kind or "MONTH").upper()
    if kind not in PERIOD_KINDS:
        raise ApiError(
            "Unknown period.", 422, "VALIDATION_ERROR", {"period": [f"One of {PERIOD_KINDS}."]}
        )
    if kind == "MONTH":
        start = plan_service.parse_month(value, today)
        return Period(kind, start, plan_service.month_end(start), start.strftime("%B %Y"))
    if kind == "YEAR":
        try:
            year = int(value) if value else today.year
            start = date(year, 1, 1)
        except ValueError as exc:
            raise ApiError(
                "Use a year like 2026.", 422, "VALIDATION_ERROR", {"value": ["Use YYYY."]}
            ) from exc
        return Period(kind, start, date(year, 12, 31), str(year))
    if kind == "PHASE":
        phase = None
        try:
            phase = db.session.get(LifePhase, uuid.UUID(str(value))) if value else None
        except ValueError:
            phase = None
        if phase is None or phase.user_id != user.id:
            raise ApiError(
                "Choose one of your phases.",
                422,
                "VALIDATION_ERROR",
                {"value": ["Unknown phase."]},
            )
        end = phase.end_date or max(today, phase.start_date)
        return Period(kind, phase.start_date, end, phase.name, phase.id)
    return Period(kind, lifetime_start(user), today, "Since you started planning")


# ---------------------------------------------------------------------------
# Aggregates
# ---------------------------------------------------------------------------
def _sum_expenses(user_id, *conditions) -> Decimal:
    return money(
        db.session.scalar(
            select(func.coalesce(func.sum(Transaction.amount_base), 0)).where(
                Transaction.user_id == user_id,
                Transaction.kind == TransactionKind.EXPENSE,
                *conditions,
            )
        )
    )


def _scope(user_id: uuid.UUID, period: Period) -> list:
    """SQL conditions of a period: its dates, and for PHASE reports the phase
    itself - transactions are counted where they are assigned (FR-37)."""
    conditions = [
        Transaction.user_id == user_id,
        Transaction.txn_date.between(period.start, period.end),
    ]
    if period.phase_id is not None:
        conditions = [Transaction.user_id == user_id, Transaction.phase_id == period.phase_id]
    return conditions


def monthly_series(user_id: uuid.UUID, period: Period) -> list[dict]:
    """Earned and spent per month in one query (FR-38)."""
    month = func.date_trunc("month", Transaction.txn_date)
    earned = case(
        (
            (Transaction.kind == TransactionKind.INCOME) & Category.counts_as_earned.is_(True),
            Transaction.amount_base,
        ),
        else_=0,
    )
    spent = case((Transaction.kind == TransactionKind.EXPENSE, Transaction.amount_base), else_=0)
    rows = db.session.execute(
        select(month, func.sum(earned), func.sum(spent))
        .outerjoin(Category, Category.id == Transaction.category_id)
        .where(*_scope(user_id, period))
        .group_by(month)
    ).all()
    by_month = {m.date(): (e, s) for m, e, s in rows}
    months = months_between(period.start, period.end)
    if by_month and period.phase_id is not None:  # manual entries may lie outside the dates
        months = months_between(min(min(by_month), period.start), max(max(by_month), period.end))
    return [
        {
            "month": m.strftime("%Y-%m"),
            "earned": str(money(by_month.get(m, (0, 0))[0])),
            "spent": str(money(by_month.get(m, (0, 0))[1])),
        }
        for m in months
    ]


def period_report(user: User, period: Period) -> dict:
    """Earned, spent, net, top categories, spend per phase, monthly series (FR-38)."""
    scope = _scope(user.id, period)
    income_rows = db.session.execute(
        select(Category.name, Category.counts_as_earned, func.sum(Transaction.amount_base))
        .join(Category, Category.id == Transaction.category_id)
        .where(*scope, Transaction.kind == TransactionKind.INCOME)
        .group_by(Category.name, Category.counts_as_earned)
    ).all()
    by_source = fold_top([(n, a) for n, earned, a in income_rows if earned], 20)
    earned = money(sum((r["amount"] for r in by_source), ZERO))
    other_income = money(sum((a for _, e, a in income_rows if not e), ZERO))
    cat_rows = db.session.execute(
        select(Category.name, func.sum(Transaction.amount_base))
        .join(Category, Category.id == Transaction.category_id)
        .where(*scope, Transaction.kind == TransactionKind.EXPENSE)
        .group_by(Category.name)
    ).all()
    spent = money(sum((a for _, a in cat_rows), ZERO))
    phase_rows = db.session.execute(
        select(LifePhase.name, LifePhase.start_date, func.sum(Transaction.amount_base))
        .join(LifePhase, LifePhase.id == Transaction.phase_id)
        .where(*scope, Transaction.kind == TransactionKind.EXPENSE)
        .group_by(LifePhase.id)
        .order_by(LifePhase.start_date)
    ).all()
    return {
        "period": period.to_dict(),
        "currency": user.base_currency,
        "earned": str(earned),
        "other_income": str(other_income),
        "spent": str(spent),
        "net": str(money(earned - spent)),
        "by_source": [{"name": r["name"], "amount": str(r["amount"])} for r in by_source],
        "top_categories": [
            {"name": r["name"], "amount": str(r["amount"])} for r in fold_top(list(cat_rows))
        ],
        "by_phase": [{"name": n, "amount": str(money(a))} for n, _, a in phase_rows],
        "monthly": monthly_series(user.id, period),
    }


def cost_reports(user: User, today: date | None = None) -> dict:
    """Total cost of going abroad and cost of the degree (FR-39)."""
    today = today or date.today()
    abroad_ids = [p.id for p in user.phases if p.phase_type in ABROAD_PHASES]
    abroad = _sum_expenses(user.id, Transaction.phase_id.in_(abroad_ids)) if abroad_ids else ZERO
    abroad_groups = db.session.execute(
        select(Category.group_name, func.sum(Transaction.amount_base))
        .join(Category, Category.id == Transaction.category_id)
        .where(
            Transaction.user_id == user.id,
            Transaction.kind == TransactionKind.EXPENSE,
            Transaction.phase_id.in_(abroad_ids),
        )
        .group_by(Category.group_name)
    ).all()
    degree_end = min(user.study_end_date, today)
    degree = _sum_expenses(
        user.id, Transaction.txn_date.between(lifetime_start(user), user.study_end_date)
    )
    total_days = (user.study_end_date - user.study_start_date).days or 1
    elapsed = max(0, min((today - user.study_start_date).days, total_days))
    return {
        "currency": user.base_currency,
        "going_abroad": {
            "total": str(abroad),
            "by_group": [
                {"name": r["name"], "amount": str(r["amount"])}
                for r in fold_top(list(abroad_groups), 6)
            ],
        },
        "degree": {
            "total_so_far": str(degree),
            "until": user.study_end_date.isoformat(),
            "complete": today >= user.study_end_date,
            "study_progress_pct": round(elapsed * 100 / total_days),
            "as_of": degree_end.isoformat(),
        },
    }


def _today_rates(user: User, currencies: set[str], on: date) -> tuple[dict, bool]:
    rates, estimated = {}, False
    for ccy in currencies:
        r = fx_service.get_rate(ccy, user.base_currency, on)
        rates[ccy], estimated = r.rate, estimated or r.estimated
    return rates, estimated


def net_worth_timeline(user: User, today: date | None = None) -> dict:
    """Monthly net worth from the first month to today (FR-40, ADR-0012)."""
    today = today or date.today()
    months = months_between(lifetime_start(user), today)
    wallets = list(db.session.scalars(select(Wallet).where(Wallet.user_id == user.id)))
    loans = loan_service.list_loans(user.id)
    rates, estimated = _today_rates(
        user, {w.currency_code for w in wallets} | {loan.currency_code for loan in loans}, today
    )

    # Signed sums per wallet and month in one query, then running totals.
    signed = case(
        (Transaction.kind.in_(wallet_service.INFLOW), Transaction.amount),
        else_=-Transaction.amount,
    )
    month = func.date_trunc("month", Transaction.txn_date)
    rows = db.session.execute(
        select(Transaction.wallet_id, month, func.sum(signed))
        .where(Transaction.user_id == user.id, Transaction.txn_date <= today)
        .group_by(Transaction.wallet_id, month)
    ).all()
    deltas: dict[tuple, Decimal] = {(w, m.date()): v for w, m, v in rows}

    points = []
    running = {w.id: ZERO for w in wallets}
    for m in months:
        end = min(plan_service.month_end(m), today)
        assets = ZERO
        for w in wallets:
            running[w.id] += deltas.get((w.id, m), ZERO)
            if w.opening_date <= end:
                assets += convert(w.opening_balance + running[w.id], rates[w.currency_code])
        debt = ZERO
        for loan in loans:
            owed = outstanding_on(
                loan.created_at.date(), loan.payments, loan.outstanding_amount, end
            )
            debt += convert(owed, rates[loan.currency_code])
        points.append(
            {
                "month": m.strftime("%Y-%m"),
                "assets": str(money(assets)),
                "debt": str(money(debt)),
                "net_worth": str(money(assets - debt)),
            }
        )
    return {"currency": user.base_currency, "estimated_rates": estimated, "points": points}


def loan_timeline(user: User, today: date | None = None, max_months: int = 360) -> dict:
    """Projected total outstanding of active loans until debt-free (FR-40)."""
    today = today or date.today()
    current = today.replace(day=1)
    loans = [loan for loan in loan_service.list_loans(user.id) if loan.status == LoanStatus.ACTIVE]
    rates, estimated = _today_rates(user, {loan.currency_code for loan in loans}, today)
    totals: dict[int, Decimal] = {}
    payoff = []
    horizon = 0
    for loan in loans:
        sim = loan_service.simulate(
            loan.outstanding_amount, loan.annual_rate_pct, loan.emi_amount, keep_schedule=True
        )
        first = max(current, (loan.emi_start_date or today).replace(day=1))
        offset = (first.year - current.year) * 12 + first.month - current.month
        rate = rates[loan.currency_code]
        # until the first EMI the balance stays as it is (no prediction, TD-04)
        for i in range(min(offset + 1, max_months)):
            totals[i] = totals.get(i, ZERO) + convert(loan.outstanding_amount, rate)
        for row in sim.schedule:
            i = offset + row["month"]
            if i < max_months:
                totals[i] = totals.get(i, ZERO) + convert(Decimal(row["balance"]), rate)
        if sim.months is None:
            horizon = max_months
        else:
            horizon = max(horizon, min(offset + sim.months + 1, max_months))
            payoff.append(
                {
                    "loan_id": str(loan.id),
                    "name": loan.name,
                    "payoff_month": plan_service.add_months(first, sim.months - 1).strftime("%Y-%m")
                    if sim.months
                    else None,
                }
            )
    points = [
        {
            "month": plan_service.add_months(current, i).strftime("%Y-%m"),
            "outstanding": str(money(totals.get(i, ZERO))),
        }
        for i in range(horizon)
    ]
    debt_free = max((p["payoff_month"] for p in payoff if p["payoff_month"]), default=None)
    return {
        "currency": user.base_currency,
        "estimated_rates": estimated,
        "debt_free_month": debt_free,
        "loans": payoff,
        "points": points,
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def dashboard(user: User, today: date | None = None) -> dict:
    """Everything the dashboard shows, in as few queries as possible (FR-41)."""
    today = today or date.today()
    wallets = [w for w in wallet_service.list_wallets(user.id) if not w.is_archived]
    balances = wallet_service.balances(user.id, as_of=today)
    runways = runway_service.wallet_runways(user.id, today)
    loans = [loan for loan in loan_service.list_loans(user.id) if loan.status == LoanStatus.ACTIVE]
    rates, estimated = _today_rates(
        user, {w.currency_code for w in wallets} | {loan.currency_code for loan in loans}, today
    )

    wallet_rows, total = [], ZERO
    for w in wallets:
        bal = balances.get(w.id, w.opening_balance)
        in_base = convert(bal, rates[w.currency_code])
        total += in_base
        wallet_rows.append(
            {
                "id": str(w.id),
                "name": w.name,
                "currency_code": w.currency_code,
                "balance": str(bal),
                "balance_base": str(in_base),
                "runway": runways[w.id].to_dict() if w.id in runways else None,
            }
        )

    month = today.replace(day=1)
    target = plan_service.minimum_target(user, month, today)
    totals = plan_service.month_totals(user.id, month, today)
    goal = target["total"]

    debt = money(
        sum((convert(ln.outstanding_amount, rates[ln.currency_code]) for ln in loans), ZERO)
    )
    emi_now = money(
        sum(
            (
                convert(ln.emi_amount, rates[ln.currency_code])
                for ln in loans
                if not ln.emi_start_date or ln.emi_start_date <= plan_service.month_end(month)
            ),
            ZERO,
        )
    )
    payoff_months = [loan_service.loan_summary(ln, today)["payoff_month"] for ln in loans]

    start30 = today - timedelta(days=29)
    cat_rows = db.session.execute(
        select(Category.name, func.sum(Transaction.amount_base))
        .join(Category, Category.id == Transaction.category_id)
        .where(
            Transaction.user_id == user.id,
            Transaction.kind == TransactionKind.EXPENSE,
            Transaction.txn_date.between(start30, today),
        )
        .group_by(Category.name)
    ).all()
    spending = fold_top(list(cat_rows), 5)

    current_phase = next(
        (
            p
            for p in sorted(user.phases, key=lambda p: (p.end_date is None, p.start_date))
            if p.start_date <= today and (p.end_date is None or today <= p.end_date)
        ),
        None,
    )

    return {
        "currency": user.base_currency,
        "estimated_rates": estimated or target["estimated"],
        "total_balance": str(money(total)),
        "wallets": wallet_rows,
        "alerts": [
            r
            for r in wallet_rows
            if r["runway"] and r["runway"]["status"] in ("WARNING", "CRITICAL")
        ],
        "this_month": {
            "month": month.strftime("%Y-%m"),
            "target": str(goal),
            "earned": str(totals["earned"]),
            "spent": str(totals["spent"]),
            "still_to_earn": str(max(money(goal - totals["earned"]), ZERO)),
            "progress_pct": float(round(totals["earned"] * 100 / goal, 1)) if goal > 0 else None,
        },
        "loans": {
            "active": len(loans),
            "outstanding": str(debt),
            "emi_this_month": str(emi_now),
            "debt_free_month": max((m for m in payoff_months if m), default=None)
            if all(payoff_months)
            else None,
        },
        "current_phase_id": str(current_phase.id) if current_phase else None,
        "spending_30d": {
            "total": str(money(sum((r["amount"] for r in spending), ZERO))),
            "categories": [{"name": r["name"], "amount": str(r["amount"])} for r in spending],
        },
    }
