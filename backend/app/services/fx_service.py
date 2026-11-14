"""Market exchange rates with cache and fallback (ADR-0003, NFR-08).

All rates are stored against USD (1 USD = x currency), one row per currency
and day. Any pair is calculated as a cross rate:

    rate(A -> B) = usd[B] / usd[A]

Lookup order for a date ``on``:

1. API rates cached for exactly that date               -> LIVE
2. if today's API rates are not cached yet, fetch them  -> (cached)
3. cached API rates at most 7 days away from ``on``    -> FALLBACK (estimated)
4. seeded fallback table                                -> FALLBACK (estimated)

The provider only offers *latest* rates, so step 2 always stores under
today's date. Old (back-dated) transactions therefore get an estimated rate,
which the user can overwrite - and remittances always use the user's amounts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

import requests
from flask import current_app
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.extensions import db
from app.models import Currency, FxRate, FxSource, RateSource
from app.seed.master_data import FALLBACK_RATE_DATE

from .money import rate as round_rate
from .money import to_decimal

log = logging.getLogger(__name__)
PIVOT = "USD"


@dataclass(frozen=True)
class RateResult:
    """A market rate: 1 ``from_currency`` = ``rate`` ``to_currency``."""

    from_currency: str
    to_currency: str
    rate: Decimal
    source: RateSource
    rate_date: date

    @property
    def estimated(self) -> bool:
        return self.source == RateSource.FALLBACK

    def to_dict(self) -> dict:
        return {
            "from": self.from_currency,
            "to": self.to_currency,
            "rate": str(self.rate),
            "source": self.source.value,
            "rate_date": self.rate_date.isoformat(),
            "estimated": self.estimated,
        }


class UnknownCurrency(ValueError):
    pass


# ---------------------------------------------------------------------------
# Pure helper
# ---------------------------------------------------------------------------
def cross_rate(usd_rates: dict[str, Decimal], from_ccy: str, to_ccy: str) -> Decimal | None:
    """Cross rate via USD, or None if a currency is missing (TC-FX05)."""
    if from_ccy == to_ccy:
        return Decimal("1")
    a, b = usd_rates.get(from_ccy), usd_rates.get(to_ccy)
    if not a or not b:
        return None
    return round_rate(to_decimal(b) / to_decimal(a))


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------
def fetch_usd_rates() -> dict[str, Decimal]:
    """Call the provider. Returns {} on any failure (never raises)."""
    url = current_app.config.get("FX_API_URL")
    if not url:
        return {}
    try:
        res = requests.get(url.format(base=PIVOT), timeout=current_app.config["FX_TIMEOUT_SECONDS"])
        res.raise_for_status()
        payload = res.json()
        if payload.get("result") != "success":
            raise ValueError(payload.get("error-type", "unexpected response"))
        return {code: Decimal(str(value)) for code, value in payload["rates"].items()}
    except (requests.RequestException, ValueError, KeyError) as exc:
        log.warning("Exchange-rate provider unavailable: %s", exc)
        return {}


def _store_api_rates(rates: dict[str, Decimal], on: date) -> None:
    known = set(db.session.scalars(select(Currency.code)))
    rows = [
        {
            "base_currency": PIVOT,
            "quote_currency": code,
            "rate": round_rate(value),
            "rate_date": on,
            "source": FxSource.API,
        }
        for code, value in rates.items()
        if code in known and value > 0
    ]
    if not rows:
        return
    stmt = insert(FxRate).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_fx_rates_pair_date_source",
        set_={"rate": stmt.excluded.rate},
    )
    db.session.execute(stmt)
    db.session.flush()


# ---------------------------------------------------------------------------
# Cache access
# ---------------------------------------------------------------------------
def _rates_on(on: date, source: FxSource) -> dict[str, Decimal]:
    rows = db.session.execute(
        select(FxRate.quote_currency, FxRate.rate).where(
            FxRate.base_currency == PIVOT, FxRate.rate_date == on, FxRate.source == source
        )
    ).all()
    return {code: value for code, value in rows}


def _nearest_api_date(on: date, max_days: int) -> date | None:
    """Closest date (either side) with cached API rates, within ``max_days``."""
    low, high = on - timedelta(days=max_days), on + timedelta(days=max_days)
    dates = db.session.scalars(
        select(FxRate.rate_date)
        .where(
            FxRate.base_currency == PIVOT,
            FxRate.source == FxSource.API,
            FxRate.rate_date.between(low, high),
        )
        .group_by(FxRate.rate_date)
    ).all()
    if not dates:
        return None
    return min(dates, key=lambda d: (abs((d - on).days), -d.toordinal()))


def _ensure_today_cached(today: date) -> None:
    has_today = db.session.scalar(
        select(func.count())
        .select_from(FxRate)
        .where(FxRate.rate_date == today, FxRate.source == FxSource.API)
    )
    if not has_today:
        rates = fetch_usd_rates()
        if rates:
            _store_api_rates(rates, today)


def get_rate(from_ccy: str, to_ccy: str, on: date | None = None) -> RateResult:
    """Market rate for a pair on a date, following the lookup order above."""
    today = date.today()
    on = on or today
    from_ccy, to_ccy = from_ccy.upper(), to_ccy.upper()
    if from_ccy == to_ccy:
        return RateResult(from_ccy, to_ccy, Decimal("1"), RateSource.IDENTITY, on)

    # 1. exact date
    value = cross_rate(_rates_on(on, FxSource.API), from_ccy, to_ccy)
    if value is not None:
        return RateResult(from_ccy, to_ccy, value, RateSource.LIVE, on)

    # 2. fetch today's rates once per day
    if on > today - timedelta(days=current_app.config["FX_MAX_STALE_DAYS"]):
        _ensure_today_cached(today)
        if on == today:
            value = cross_rate(_rates_on(today, FxSource.API), from_ccy, to_ccy)
            if value is not None:
                return RateResult(from_ccy, to_ccy, value, RateSource.LIVE, today)

    # 3. nearby cached rates (estimated)
    near = _nearest_api_date(on, current_app.config["FX_MAX_STALE_DAYS"])
    if near is not None:
        value = cross_rate(_rates_on(near, FxSource.API), from_ccy, to_ccy)
        if value is not None:
            return RateResult(from_ccy, to_ccy, value, RateSource.FALLBACK, near)

    # 4. seeded fallback table (estimated)
    value = cross_rate(_rates_on(FALLBACK_RATE_DATE, FxSource.FALLBACK), from_ccy, to_ccy)
    if value is not None:
        return RateResult(from_ccy, to_ccy, value, RateSource.FALLBACK, FALLBACK_RATE_DATE)

    raise UnknownCurrency(f"No exchange rate available for {from_ccy} -> {to_ccy}.")
