"""Realistic demo user (US-16, FR-43): ``flask seed-demo [--reset]``.

Ananya Rao from Bengaluru (INR) studies M.Sc. Informatics in Munich (EUR).
Her data runs from her first IELTS fee in June 2025 up to *today*, so every
page shows meaningful numbers whenever the app is started.

All entries are created through the normal services (transactions,
remittances, loans), so they follow exactly the same rules as user input.

Exchange rates: a smooth, plausible daily EUR/INR/USD history is stored
in the rate cache for the demo period (rows that already exist, e.g. real
API rates, are never overwritten). Remittances get a provider margin of
1-2.5 % against that market rate, so their hidden cost is realistic.

The script is idempotent: if the demo user exists nothing happens; with
``--reset`` the demo user is deleted and created again.
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.extensions import db
from app.models import (
    Category,
    CategoryKind,
    FxRate,
    FxSource,
    Gender,
    Loan,
    Transaction,
    User,
    Wallet,
)
from app.services import (
    account_service,
    auth_service,
    fx_service,
    loan_service,
    plan_service,
    remittance_service,
    transaction_service,
    wallet_service,
)
from app.services.money import money

DEMO_EMAIL = "demo@edufinance.app"
DEMO_PASSWORD = "Demo#2026"  # noqa: S105 - published demo credentials
RATE_HISTORY_START = date(2025, 5, 1)

PROFILE = {
    "full_name": "Ananya Rao",
    "email": DEMO_EMAIL,
    "password": DEMO_PASSWORD,
    "date_of_birth": date(2001, 3, 14),
    "gender": Gender.FEMALE,
    "home_currency": "INR",
    "base_currency": "EUR",
    "destination_country": "DE",
    "planning_start_date": date(2025, 6, 1),
    "arrival_date": date(2025, 9, 25),
    "study_start_date": date(2025, 10, 1),
    "study_end_date": date(2027, 9, 30),
}


# ---------------------------------------------------------------------------
# Rate history
# ---------------------------------------------------------------------------
def demo_rates(day: date) -> dict[str, Decimal]:
    """Plausible USD-based rates for a day: 1 EUR moves from ~97.5 to ~104.5 INR
    with small waves; 1 USD ~0.885 -> 0.858 EUR."""
    t = (day - date(2025, 6, 1)).days / 548
    inr_per_eur = 97.5 + 7.0 * t + 1.1 * math.sin(t * 6 * math.pi)
    eur_per_usd = 0.885 - 0.027 * t + 0.006 * math.sin(t * 4 * math.pi + 1)
    return {
        "USD": Decimal("1"),
        "EUR": Decimal(f"{eur_per_usd:.6f}"),
        "INR": Decimal(f"{inr_per_eur * eur_per_usd:.6f}"),
    }


def store_rate_history(start: date, end: date) -> int:
    rows = []
    day = start
    while day <= end:
        for code, value in demo_rates(day).items():
            rows.append(
                {
                    "base_currency": "USD",
                    "quote_currency": code,
                    "rate": value,
                    "rate_date": day,
                    "source": FxSource.API,
                }
            )
        day += timedelta(days=1)
    for i in range(0, len(rows), 1000):
        db.session.execute(insert(FxRate).values(rows[i : i + 1000]).on_conflict_do_nothing())
    db.session.flush()
    return len(rows)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------
class _Demo:
    def __init__(self, user: User, today: date):
        self.user, self.today = user, today
        self.cats = {
            (c.name, c.kind): c.id
            for c in db.session.scalars(select(Category).where(Category.user_id.is_(None)))
        }
        self.w: dict[str, Wallet] = {}

    def cat(self, name: str, kind: CategoryKind = CategoryKind.EXPENSE):
        return self.cats[(name, kind)]

    def wallet(self, key, name, ccy, wtype, opening, opened):
        self.w[key] = wallet_service.create_wallet(
            self.user.id,
            {
                "name": name,
                "currency_code": ccy,
                "wallet_type": wtype,
                "opening_balance": Decimal(opening),
                "opening_date": opened,
            },
        )

    def spend(self, wallet, day, category, amount, note=None):
        if day <= self.today:
            transaction_service.create_transaction(
                self.user,
                {
                    "kind": "EXPENSE",
                    "wallet_id": self.w[wallet].id,
                    "category_id": self.cat(category),
                    "amount": Decimal(str(amount)),
                    "txn_date": day,
                    "note": note,
                },
            )

    def earn(self, wallet, day, category, amount, note=None):
        if day <= self.today:
            transaction_service.create_transaction(
                self.user,
                {
                    "kind": "INCOME",
                    "wallet_id": self.w[wallet].id,
                    "category_id": self.cat(category, CategoryKind.INCOME),
                    "amount": Decimal(str(amount)),
                    "txn_date": day,
                    "note": note,
                },
            )

    def transfer(
        self, day, sent, from_wallet=None, to_wallet=None, received=None, margin="0.015", **kw
    ):
        """Remittance; if ``received`` is None it is derived from the market
        rate minus the provider margin."""
        if day > self.today:
            return
        sent = Decimal(str(sent))
        from_ccy = self.w[from_wallet].currency_code if from_wallet else kw["sent_currency"]
        to_ccy = self.w[to_wallet].currency_code if to_wallet else kw["received_currency"]
        if received is None:
            market = fx_service.get_rate(from_ccy, to_ccy, day).rate
            received = money(sent * market * (Decimal(1) - Decimal(margin)))
        remittance_service.create_remittance(
            self.user,
            {
                "from_wallet_id": self.w[from_wallet].id if from_wallet else None,
                "to_wallet_id": self.w[to_wallet].id if to_wallet else None,
                "sent_amount": sent,
                "received_amount": Decimal(str(received)),
                "remit_date": day,
                **kw,
            },
        )

    def plan(self, name, category, amount, valid_from, valid_to=None, phase=None):
        plan_service.create_item(
            self.user.id,
            {
                "name": name,
                "category_id": self.cat(category),
                "amount": Decimal(amount),
                "currency_code": "EUR",
                "valid_from": valid_from,
                "valid_to": valid_to,
                "phase_id": phase,
            },
        )


def _months(start: date, today: date):
    m = start.replace(day=1)
    while m <= today:
        yield m
        m = plan_service.add_months(m, 1)


def _vary(base: str, month: date, spread: int, salt: int = 0) -> Decimal:
    """Deterministic variation so the months do not look copy-pasted."""
    wave = math.sin(month.toordinal() / 29 + salt) * spread
    return Decimal(str(base)) + Decimal(str(round(wave, 2))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def build(user: User, today: date) -> None:
    d = _Demo(user, today)
    D = date  # noqa: N806 - short alias keeps the timeline readable

    # --- wallets ------------------------------------------------------------
    d.wallet("home", "Home Account (SBI)", "INR", "BANK", "450000", D(2025, 6, 1))
    d.wallet("blocked", "Blocked Account", "EUR", "PROOF_OF_FUNDS", "0", D(2025, 8, 1))
    d.wallet("daily", "Daily Spending (DKB)", "EUR", "BANK", "0", D(2025, 9, 20))
    d.wallet("savings", "Emergency Savings", "EUR", "SAVINGS", "0", D(2025, 9, 20))

    # --- pre-departure (paid in India) ----------------------------------------
    d.spend("home", D(2025, 6, 14), "Language test", 18500, "IELTS Academic, Bengaluru")
    d.spend(
        "home", D(2025, 6, 20), "Credential evaluation (uni-assist/APS)", 18000, "APS certificate"
    )
    d.spend("home", D(2025, 6, 28), "Courier & postage", 1850, "Documents to APS New Delhi")
    d.spend(
        "home", D(2025, 7, 2), "University application", 7300, "uni-assist: TU Munich, RWTH Aachen"
    )
    d.spend(
        "home",
        D(2025, 7, 5),
        "Document translation & attestation",
        4200,
        "Transcripts, sworn translation",
    )
    d.earn("home", D(2025, 7, 20), "Family support", 350000, "Appa & Amma - savings for my studies")
    d.earn(
        "home", D(2025, 8, 5), "Loan disbursement", 600000, "SBI education loan - 1st disbursement"
    )
    # blocked account: sent amount from market rate + 1.8 % margin
    market = fx_service.get_rate("EUR", "INR", D(2025, 8, 7)).rate
    sent = (Decimal("11904") * market * Decimal("1.018")).quantize(Decimal("1"))
    d.transfer(
        D(2025, 8, 7),
        sent,
        "home",
        "blocked",
        received="11904.00",
        provider="Expatrio",
        fee_amount=Decimal("1450"),
        note="Blocked account deposit",
    )
    d.spend("home", D(2025, 8, 12), "Visa fee", 7500, "German national visa (EUR 75)")
    d.spend("home", D(2025, 8, 12), "Biometrics & appointments", 2150, "VFS Global Bengaluru")
    d.spend("home", D(2025, 8, 18), "Medical check & vaccinations", 3500)
    d.spend(
        "home",
        D(2025, 8, 20),
        "Travel health insurance",
        4800,
        "Incoming insurance until enrolment",
    )
    d.spend("home", D(2025, 8, 28), "Flight", 54600, "BLR -> MUC, Lufthansa")
    d.spend(
        "home",
        D(2025, 9, 10),
        "Luggage & shopping for departure",
        22500,
        "Winter clothes, pressure cooker",
    )
    d.transfer(
        D(2025, 9, 20),
        60000,
        "home",
        "daily",
        provider="Wise",
        margin="0.012",
        note="Start money for Munich",
    )

    # --- settling in (Munich) -------------------------------------------------
    d.spend("daily", D(2025, 9, 25), "Temporary stay", 310, "Hostel, 5 nights")
    d.spend("daily", D(2025, 9, 29), "Accommodation deposit", 850, "Studentenwerk deposit")
    d.spend("daily", D(2025, 9, 30), "Furniture & household", 265, "IKEA")
    d.spend("daily", D(2025, 10, 1), "SIM card & phone", 20, "Prepaid SIM")
    d.spend("daily", D(2025, 10, 2), "Semester fee", Decimal("162.40"), "Semester fee WS 25/26")
    d.spend("daily", D(2025, 10, 5), "Furniture & household", 140, "Kitchen things")
    d.spend("daily", D(2025, 10, 12), "Leisure & travel", 120, "Used bike")
    d.spend(
        "daily", D(2025, 11, 20), "City registration & residence permit", 100, "Residence permit"
    )

    # --- blocked account releases (12 x EUR 992) ------------------------------
    for i in range(12):
        day = plan_service.add_months(D(2025, 9, 1), i).replace(day=26)
        d.transfer(day, "992", "blocked", "daily", received="992", note="Monthly release")

    # --- monthly life -----------------------------------------------------------
    for m in _months(D(2025, 10, 1), today):
        rent = "435" if m >= D(2026, 4, 1) else "420"
        d.spend("daily", m, "Rent", rent, "Studentenwerk, shared flat")
        d.spend("daily", m.replace(day=2), "Health insurance", Decimal("138.10"), "TK student rate")
        d.spend("daily", m.replace(day=3), "Phone & internet", 15, "Mobile plan")
        d.spend("daily", m.replace(day=3), "Public transport", 58, "Deutschlandticket")
        d.spend("daily", m.replace(day=15), "Subscriptions", Decimal("5.99"), "Spotify student")
        for i, day in enumerate((4, 11, 18, 25)):
            d.spend("daily", m.replace(day=day), "Groceries", _vary("49", m, 11, i), "Lidl / Aldi")
        d.spend("daily", m.replace(day=9), "Eating out", _vary("17", m, 6, 1), "Mensa & döner")
        d.spend(
            "daily", m.replace(day=22), "Eating out", _vary("21", m, 7, 2), "Dinner with flatmates"
        )
        d.spend("daily", m.replace(day=14), "Personal care", _vary("15", m, 4, 3), "dm")
        d.spend(
            "daily", m.replace(day=19), "Leisure & travel", _vary("45", m, 15, 5), "Cinema, cafés"
        )
        d.spend("daily", m.replace(day=27), "Other expense", _vary("15", m, 6, 6), "Misc.")
        if m >= D(2026, 2, 1):
            d.transfer(
                m.replace(day=2), "100", "daily", "savings", received="100", note="Monthly saving"
            )

    # --- one-off costs ----------------------------------------------------------
    d.spend("daily", D(2025, 10, 20), "Books & study materials", 45, "Textbooks")
    d.spend("daily", D(2025, 11, 8), "Clothing", 89, "Winter jacket")
    d.spend("daily", D(2025, 12, 13), "Leisure & travel", 35, "Christmas market")
    d.spend("daily", D(2025, 12, 27), "Leisure & travel", 320, "New Year in Paris")
    d.spend("daily", D(2026, 3, 14), "Clothing", 45)
    d.spend("daily", D(2026, 4, 2), "Semester fee", Decimal("162.40"), "Semester fee SS 26")
    d.spend("daily", D(2026, 4, 18), "Leisure & travel", 148, "Weekend in Prague")
    d.spend("daily", D(2026, 4, 21), "Books & study materials", 38)
    d.spend("daily", D(2026, 7, 11), "Leisure & travel", 96, "Salzburg day trip")
    d.spend("daily", D(2026, 7, 25), "Leisure & travel", 420, "Summer trip to Italy")
    d.spend("daily", D(2026, 9, 20), "Laptop & electronics", 149, "Headphones")
    d.spend("daily", D(2026, 10, 2), "Semester fee", Decimal("162.40"), "Semester fee WS 26/27")
    d.spend("daily", D(2026, 10, 17), "Clothing", 60)
    d.spend("daily", D(2026, 11, 6), "Medicine & doctor", 25, "Pharmacy")

    # --- income -----------------------------------------------------------------
    for m in (D(2025, 11, 1), D(2025, 12, 1)):
        d.earn("daily", plan_service.month_end(m), "Mini-job / freelance", 538, "Mini-job, café")
    for m in _months(D(2026, 1, 1), today):
        pay_day = plan_service.month_end(m)
        if pay_day > today:
            continue
        full_time = m.month in (8, 9)  # semester break: more hours allowed
        amount = "1250" if full_time else _vary("860", m, 40, 4)
        d.earn("daily", pay_day, "Part-time salary", amount, "Werkstudent, software QA")
    d.earn("daily", D(2026, 7, 24), "Tax refund", Decimal("212.30"), "Income tax 2025")

    # --- family -----------------------------------------------------------------
    d.transfer(
        D(2025, 10, 18),
        "100",
        "daily",
        None,
        received_currency="INR",
        margin="0.015",
        provider="Wise",
        note="Diwali gift for Amma",
    )
    for day in (D(2025, 12, 5), D(2026, 3, 5), D(2026, 7, 6), D(2026, 10, 5)):
        d.transfer(
            day,
            "25000",
            None,
            "daily",
            sent_currency="INR",
            margin="0.022",
            provider="Bank transfer",
            note="From Appa",
        )

    # --- loans --------------------------------------------------------------------
    d.earn(
        "home", D(2026, 8, 4), "Loan disbursement", 250000, "SBI education loan - 2nd disbursement"
    )
    sbi = loan_service.create_loan(
        user,
        {
            "name": "SBI education loan",
            "lender": "State Bank of India",
            "currency_code": "INR",
            "annual_rate_pct": Decimal("8.5"),
            "sanctioned_amount": Decimal("850000"),
            "outstanding_amount": Decimal("919050")
            if today >= D(2026, 8, 4)
            else Decimal("600000"),
            "emi_amount": Decimal("12000"),
            "emi_start_date": D(2028, 4, 5),
            "min_part_payment": Decimal("10000"),
            "default_wallet_id": d.w["home"].id,
            "note": "Outstanding incl. moratorium interest, as on the bank statement",
        },
    )
    sbi.created_at = datetime(2025, 8, 5, tzinfo=UTC)

    if today >= D(2026, 1, 15):
        laptop = loan_service.create_loan(
            user,
            {
                "name": "Laptop (0 % instalment)",
                "lender": "MediaMarkt / Santander",
                "currency_code": "EUR",
                "annual_rate_pct": Decimal("0"),
                "sanctioned_amount": Decimal("1200"),
                "outstanding_amount": Decimal("1200"),
                "emi_amount": Decimal("100"),
                "emi_start_date": D(2026, 1, 15),
                "default_wallet_id": d.w["daily"].id,
            },
        )
        laptop.created_at = datetime(2026, 1, 10, tzinfo=UTC)
        for m in _months(D(2026, 1, 1), today):
            day = m.replace(day=15)
            if day <= today and laptop.outstanding_amount > 0:
                loan_service.record_payment(
                    user, laptop.id, {"payment_type": "EMI", "amount": "100", "paid_on": day}
                )

    # --- monthly plan -----------------------------------------------------------
    study = next(p.id for p in user.phases if p.phase_type.value == "STUDY")
    d.plan("Rent", "Rent", "420", D(2025, 10, 1), D(2026, 3, 31))
    d.plan("Rent", "Rent", "435", D(2026, 4, 1))
    d.plan("Health insurance (TK)", "Health insurance", "138.10", D(2025, 10, 1))
    d.plan("Groceries", "Groceries", "200", D(2025, 10, 1))
    d.plan("Deutschlandticket", "Public transport", "58", D(2025, 10, 1), phase=study)
    d.plan("Mobile plan", "Phone & internet", "15", D(2025, 10, 1))

    # The blocked account is empty after the last release -> archive it.
    if today >= D(2026, 8, 26):
        d.w["blocked"].is_archived = True
    db.session.flush()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def seed_demo(reset: bool = False, today: date | None = None) -> str:
    today = today or date.today()
    existing = db.session.scalar(select(User).where(func.lower(User.email) == DEMO_EMAIL))
    if existing and not reset:
        return "Demo user already exists (use --reset to recreate)."
    if existing:
        account_service.delete_all_data(existing.id)
    store_rate_history(RATE_HISTORY_START, today)
    user = auth_service.register(dict(PROFILE))
    build(user, today)
    db.session.commit()

    def count(model):
        return db.session.scalar(
            select(func.count()).select_from(model).where(model.user_id == user.id)
        )

    return (
        f"Demo user {DEMO_EMAIL} created: {count(Wallet)} wallets, "
        f"{count(Transaction)} transactions, {count(Loan)} loans."
    )
