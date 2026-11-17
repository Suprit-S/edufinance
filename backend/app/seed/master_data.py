"""Idempotent seed of master data: currencies, countries, system categories
and the offline fallback exchange-rate table.

Run with ``flask seed-master``. Running it again updates existing rows and
inserts missing ones; it never creates duplicates.
"""

from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import Category, CategoryKind, Country, Currency, FxRate, FxSource, PhaseType

# (code, name, symbol, minor_units) - currencies most relevant for
# international students (origin and destination countries).
CURRENCIES = [
    ("AED", "UAE Dirham", "د.إ", 2),
    ("AUD", "Australian Dollar", "A$", 2),
    ("BDT", "Bangladeshi Taka", "৳", 2),
    ("BRL", "Brazilian Real", "R$", 2),
    ("CAD", "Canadian Dollar", "C$", 2),
    ("CHF", "Swiss Franc", "CHF", 2),
    ("CNY", "Chinese Yuan", "¥", 2),
    ("CZK", "Czech Koruna", "Kč", 2),
    ("DKK", "Danish Krone", "kr", 2),
    ("EGP", "Egyptian Pound", "E£", 2),
    ("EUR", "Euro", "€", 2),
    ("GBP", "Pound Sterling", "£", 2),
    ("GHS", "Ghanaian Cedi", "₵", 2),
    ("HUF", "Hungarian Forint", "Ft", 2),
    ("IDR", "Indonesian Rupiah", "Rp", 2),
    ("INR", "Indian Rupee", "₹", 2),
    ("IRR", "Iranian Rial", "﷼", 2),
    ("JPY", "Japanese Yen", "¥", 0),
    ("KES", "Kenyan Shilling", "KSh", 2),
    ("KRW", "South Korean Won", "₩", 0),
    ("LKR", "Sri Lankan Rupee", "Rs", 2),
    ("MXN", "Mexican Peso", "MX$", 2),
    ("MYR", "Malaysian Ringgit", "RM", 2),
    ("NGN", "Nigerian Naira", "₦", 2),
    ("NOK", "Norwegian Krone", "kr", 2),
    ("NPR", "Nepalese Rupee", "Rs", 2),
    ("NZD", "New Zealand Dollar", "NZ$", 2),
    ("PHP", "Philippine Peso", "₱", 2),
    ("PKR", "Pakistani Rupee", "Rs", 2),
    ("PLN", "Polish Zloty", "zł", 2),
    ("SEK", "Swedish Krona", "kr", 2),
    ("SGD", "Singapore Dollar", "S$", 2),
    ("THB", "Thai Baht", "฿", 2),
    ("TRY", "Turkish Lira", "₺", 2),
    ("USD", "US Dollar", "$", 2),
    ("VND", "Vietnamese Dong", "₫", 0),
    ("ZAR", "South African Rand", "R", 2),
]

# (ISO alpha-2, name, default currency)
COUNTRIES = [
    ("AE", "United Arab Emirates", "AED"),
    ("AT", "Austria", "EUR"),
    ("AU", "Australia", "AUD"),
    ("BD", "Bangladesh", "BDT"),
    ("BE", "Belgium", "EUR"),
    ("BR", "Brazil", "BRL"),
    ("CA", "Canada", "CAD"),
    ("CH", "Switzerland", "CHF"),
    ("CN", "China", "CNY"),
    ("CZ", "Czechia", "CZK"),
    ("DE", "Germany", "EUR"),
    ("DK", "Denmark", "DKK"),
    ("EG", "Egypt", "EGP"),
    ("ES", "Spain", "EUR"),
    ("FI", "Finland", "EUR"),
    ("FR", "France", "EUR"),
    ("GB", "United Kingdom", "GBP"),
    ("GH", "Ghana", "GHS"),
    ("HU", "Hungary", "HUF"),
    ("ID", "Indonesia", "IDR"),
    ("IE", "Ireland", "EUR"),
    ("IN", "India", "INR"),
    ("IR", "Iran", "IRR"),
    ("IT", "Italy", "EUR"),
    ("JP", "Japan", "JPY"),
    ("KE", "Kenya", "KES"),
    ("KR", "South Korea", "KRW"),
    ("LK", "Sri Lanka", "LKR"),
    ("MX", "Mexico", "MXN"),
    ("MY", "Malaysia", "MYR"),
    ("NG", "Nigeria", "NGN"),
    ("NL", "Netherlands", "EUR"),
    ("NO", "Norway", "NOK"),
    ("NP", "Nepal", "NPR"),
    ("NZ", "New Zealand", "NZD"),
    ("PH", "Philippines", "PHP"),
    ("PK", "Pakistan", "PKR"),
    ("PL", "Poland", "PLN"),
    ("PT", "Portugal", "EUR"),
    ("SE", "Sweden", "SEK"),
    ("SG", "Singapore", "SGD"),
    ("TH", "Thailand", "THB"),
    ("TR", "Türkiye", "TRY"),
    ("US", "United States", "USD"),
    ("VN", "Vietnam", "VND"),
    ("ZA", "South Africa", "ZAR"),
]

EXP, INC = CategoryKind.EXPENSE, CategoryKind.INCOME
P = PhaseType

# (name, kind, group, default phase, counts_as_earned)
CATEGORIES = [
    # --- Before departure ---------------------------------------------------
    ("Language test", EXP, "Exams & tests", P.PRE_DEPARTURE, True),
    ("Entrance exam (GRE/GMAT)", EXP, "Exams & tests", P.PRE_DEPARTURE, True),
    ("University application", EXP, "Applications", P.PRE_DEPARTURE, True),
    ("Credential evaluation (uni-assist/APS)", EXP, "Applications", P.PRE_DEPARTURE, True),
    ("Document translation & attestation", EXP, "Applications", P.PRE_DEPARTURE, True),
    ("Courier & postage", EXP, "Applications", P.PRE_DEPARTURE, True),
    ("Visa fee", EXP, "Visa & immigration", P.PRE_DEPARTURE, True),
    ("Biometrics & appointments", EXP, "Visa & immigration", P.PRE_DEPARTURE, True),
    ("Proof of funds / blocked account", EXP, "Visa & immigration", P.PRE_DEPARTURE, True),
    ("Medical check & vaccinations", EXP, "Health", P.PRE_DEPARTURE, True),
    ("Travel health insurance", EXP, "Health", P.PRE_DEPARTURE, True),
    ("Flight", EXP, "Travel", P.PRE_DEPARTURE, True),
    ("Luggage & shopping for departure", EXP, "Travel", P.PRE_DEPARTURE, True),
    # --- Settling in --------------------------------------------------------
    ("Accommodation deposit", EXP, "Housing", P.SETTLING_IN, True),
    ("Temporary stay", EXP, "Housing", P.SETTLING_IN, True),
    ("Furniture & household", EXP, "Housing", P.SETTLING_IN, True),
    ("City registration & residence permit", EXP, "Visa & immigration", P.SETTLING_IN, True),
    ("SIM card & phone", EXP, "Communication", P.SETTLING_IN, True),
    # --- Daily life / study -------------------------------------------------
    ("Rent", EXP, "Housing", P.STUDY, True),
    ("Utilities", EXP, "Housing", P.STUDY, True),
    ("Broadcasting fee", EXP, "Housing", P.STUDY, True),
    ("Groceries", EXP, "Living", P.STUDY, True),
    ("Eating out", EXP, "Living", P.STUDY, True),
    ("Clothing", EXP, "Living", P.STUDY, True),
    ("Personal care", EXP, "Living", P.STUDY, True),
    ("Health insurance", EXP, "Health", P.STUDY, True),
    ("Medicine & doctor", EXP, "Health", P.STUDY, True),
    ("Public transport", EXP, "Transport", P.STUDY, True),
    ("Phone & internet", EXP, "Communication", P.STUDY, True),
    ("Semester fee", EXP, "Education", P.STUDY, True),
    ("Tuition fee", EXP, "Education", P.STUDY, True),
    ("Books & study materials", EXP, "Education", P.STUDY, True),
    ("Laptop & electronics", EXP, "Education", P.STUDY, True),
    ("Leisure & travel", EXP, "Lifestyle", P.STUDY, True),
    ("Subscriptions", EXP, "Lifestyle", P.STUDY, True),
    ("Gifts & family", EXP, "Lifestyle", None, True),
    ("Loan EMI", EXP, "Loans", None, True),
    ("Loan part-payment", EXP, "Loans", None, True),
    ("Instalment plan", EXP, "Loans", None, True),
    ("Transfer fees", EXP, "Banking", None, True),
    ("Bank charges", EXP, "Banking", None, True),
    ("Taxes", EXP, "Taxes", P.WORK, True),
    ("Other expense", EXP, "Other", None, True),
    # --- Income -------------------------------------------------------------
    ("Part-time salary", INC, "Work", P.STUDY, True),
    ("Mini-job / freelance", INC, "Work", P.STUDY, True),
    ("Full-time salary", INC, "Work", P.WORK, True),
    ("Family support", INC, "Support", None, True),
    ("Scholarship", INC, "Support", P.STUDY, True),
    ("Tax refund", INC, "Refunds", None, True),
    ("Deposit refund", INC, "Refunds", None, True),
    # Loan money pays costs but is not "earned" (ADR-0008).
    ("Loan disbursement", INC, "Loans", None, False),
    ("Other income", INC, "Other", None, True),
]

# Offline fallback rates: 1 USD = x currency. Approximate mid-market values
# (2026). Used ONLY when the live API and the 7-day cache are unavailable;
# results are flagged as "estimated" (NFR5, technical debt TD-02).
FALLBACK_USD_RATES = {
    "AED": "3.6725",
    "AUD": "1.53",
    "BDT": "121.5",
    "BRL": "5.45",
    "CAD": "1.38",
    "CHF": "0.80",
    "CNY": "7.15",
    "CZK": "21.2",
    "DKK": "6.40",
    "EGP": "48.5",
    "EUR": "0.858",
    "GBP": "0.75",
    "GHS": "11.2",
    "HUF": "335",
    "IDR": "16400",
    "INR": "91.0",
    "IRR": "42000",
    "JPY": "150",
    "KES": "129",
    "KRW": "1390",
    "LKR": "300",
    "MXN": "18.4",
    "MYR": "4.25",
    "NGN": "1530",
    "NOK": "10.1",
    "NPR": "145.6",
    "NZD": "1.70",
    "PHP": "57.5",
    "PKR": "281",
    "PLN": "3.65",
    "SEK": "9.45",
    "SGD": "1.29",
    "THB": "32.5",
    "TRY": "42.0",
    "USD": "1",
    "VND": "26200",
    "ZAR": "17.5",
}
FALLBACK_RATE_DATE = date(2026, 1, 1)


def seed_master_data() -> dict:
    """Insert or update all master data. Returns counts for logging."""
    for code, name, symbol, minor in CURRENCIES:
        db.session.merge(Currency(code=code, name=name, symbol=symbol, minor_units=minor))
    db.session.flush()

    for code, name, currency in COUNTRIES:
        db.session.merge(Country(code=code, name=name, default_currency=currency))

    for name, kind, group, phase, earned in CATEGORIES:
        cat = Category.query.filter_by(user_id=None, name=name, kind=kind).one_or_none()
        if cat is None:
            cat = Category(user_id=None, name=name, kind=kind, is_system=True)
            db.session.add(cat)
        cat.group_name = group
        cat.default_phase_type = phase
        cat.counts_as_earned = earned
        cat.is_system = True

    for quote, value in FALLBACK_USD_RATES.items():
        row = FxRate.query.filter_by(
            base_currency="USD", quote_currency=quote, rate_date=FALLBACK_RATE_DATE
        ).one_or_none()
        if row is None:
            row = FxRate(base_currency="USD", quote_currency=quote, rate_date=FALLBACK_RATE_DATE)
            db.session.add(row)
        row.rate = Decimal(value)
        row.source = FxSource.FALLBACK

    db.session.commit()
    return {
        "currencies": len(CURRENCIES),
        "countries": len(COUNTRIES),
        "categories": len(CATEGORIES),
        "fallback_rates": len(FALLBACK_USD_RATES),
    }
