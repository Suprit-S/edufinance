"""Exchange-rate service (TC-FX01..FX06)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models import RateSource
from app.services import fx_service
from app.services.fx_service import cross_rate


def test_tc_fx05_cross_rate_via_usd():
    usd = {"EUR": Decimal("0.86"), "INR": Decimal("91.5")}
    # 1 INR = 0.86 / 91.5 EUR
    assert cross_rate(usd, "INR", "EUR") == Decimal("0.00939891")
    assert cross_rate(usd, "EUR", "INR") == Decimal("106.39534884")
    assert cross_rate(usd, "EUR", "EUR") == Decimal("1")
    assert cross_rate(usd, "EUR", "GBP") is None


def test_tc_fx01_cached_rate_for_today_is_used_without_provider(app, api_rates, monkeypatch):
    api_rates()
    monkeypatch.setattr(fx_service, "fetch_usd_rates", lambda: pytest.fail("no call expected"))
    result = fx_service.get_rate("INR", "EUR")
    assert result.rate == Decimal("0.00939891")
    assert result.source == RateSource.LIVE and not result.estimated


def test_tc_fx02_provider_rates_are_fetched_and_cached(app, api_rates, monkeypatch):
    calls = []

    def fake():
        calls.append(1)
        return {"USD": Decimal("1"), "EUR": Decimal("0.85"), "INR": Decimal("90"), "XXX": 1}

    monkeypatch.setattr(fx_service, "fetch_usd_rates", fake)
    first = fx_service.get_rate("EUR", "INR")
    second = fx_service.get_rate("INR", "EUR")
    assert first.rate == Decimal("105.88235294") and first.source == RateSource.LIVE
    assert second.rate == Decimal("0.00944444")
    assert len(calls) == 1  # cached after the first call; unknown codes ignored


def test_tc_fx03_provider_down_uses_rate_up_to_7_days_old(app, api_rates, monkeypatch):
    five_days_ago = date.today() - timedelta(days=5)
    api_rates(on=five_days_ago, eur="0.80", inr="88")
    monkeypatch.setattr(fx_service, "fetch_usd_rates", lambda: {})
    result = fx_service.get_rate("EUR", "INR")
    assert result.rate == Decimal("110.00000000")
    assert result.estimated and result.rate_date == five_days_ago


def test_tc_fx04_provider_down_and_old_cache_uses_fallback_table(app, api_rates, monkeypatch):
    api_rates(on=date.today() - timedelta(days=10))
    monkeypatch.setattr(fx_service, "fetch_usd_rates", lambda: {})
    result = fx_service.get_rate("EUR", "INR")
    # fallback table: 1 USD = 0.858 EUR = 91.0 INR
    assert result.rate == Decimal("106.06060606")
    assert result.estimated and result.rate_date == date(2026, 1, 1)


def test_tc_fx06_rate_endpoint_for_forms(client, auth, api_rates):
    api_rates()
    res = client.get("/api/fx/rate?from=inr&to=EUR", headers=auth)
    assert res.status_code == 200
    body = res.get_json()
    assert body["rate"] == "0.00939891" and body["estimated"] is False
    bad = client.get("/api/fx/rate?from=XYZ&to=EUR", headers=auth)
    assert bad.status_code == 422


def test_fetch_usd_rates_handles_errors(app, monkeypatch):
    import requests

    class Boom:
        def __call__(self, *a, **k):
            raise requests.ConnectionError("down")

    app.config["FX_API_URL"] = "https://example.invalid/{base}"
    try:
        monkeypatch.setattr(fx_service.requests, "get", Boom())
        assert fx_service.fetch_usd_rates() == {}

        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"result": "success", "rates": {"EUR": 0.86}}

        monkeypatch.setattr(fx_service.requests, "get", lambda *a, **k: Resp())
        assert fx_service.fetch_usd_rates() == {"EUR": Decimal("0.86")}
    finally:
        app.config["FX_API_URL"] = ""


def test_tc_fx07_api_rate_on_fallback_date_keeps_fallback_table(app, api_rates, monkeypatch):
    """Regression: a real rate fetched on 2026-01-01 must not replace the
    fallback table row of that date (migration 0002)."""
    from app.seed.master_data import FALLBACK_RATE_DATE

    api_rates(on=FALLBACK_RATE_DATE, eur="0.80", inr="88")
    assert fx_service.get_rate("EUR", "INR", FALLBACK_RATE_DATE).rate == Decimal("110.00000000")
    monkeypatch.setattr(fx_service, "fetch_usd_rates", lambda: {})
    api_rates(on=date.today() - timedelta(days=30))
    later = fx_service.get_rate("EUR", "INR", date.today())
    assert later.rate == Decimal("106.06060606") and later.estimated  # fallback still there
