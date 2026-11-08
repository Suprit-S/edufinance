# ADR-0003: Exchange rates – sources, freezing and fallback

**Status:** Accepted (refined by change request CR-02)

## Context
Users hold money in several currencies but need one total in their base currency. Two different
situations exist:
1. **A real exchange happened** (a remittance): the student knows exactly how much was sent and
   received; the true rate includes the provider's margin.
2. **No exchange happened** (an INR exam fee paid from an INR account): there is no "own" rate,
   but reports still need the EUR value.

Past reports must not change when market rates move.

## Decision
* **Remittances** always use the user's amounts: effective rate = received ÷ sent (`USER`).
* **Other foreign-currency transactions** get the day's market rate pre-filled (`LIVE`); the user
  may overwrite it (`USER`).
* Same currency → rate 1 (`IDENTITY`).
* Every transaction stores `rate_to_base`, `rate_to_home`, `amount_base`, `amount_home` and
  `rate_source` at save time and they are **never recalculated** (rate freezing).
* Market rates come from ExchangeRate-API's free open-access endpoint
  (`open.er-api.com`, no key, daily updates; attribution shown in the UI).
* Lookup order for a market rate (NFR-08):
  1. today's rate in the `fx_rates` cache (≤ 24 h old);
  2. provider call, result cached;
  3. newest cached rate ≤ 7 days old → flagged **estimated** (`FALLBACK`);
  4. seeded fallback table (rates vs. USD, cross-calculated) → flagged **estimated**.
* Rates are cached per base currency per day, so one provider call serves all pairs.

## Options rejected
* Only user-entered rates – burdens the user for every foreign expense and makes the hidden-cost
  comparison impossible.
* Recalculating historical values with today's rate – makes past reports drift.
* Paid APIs with historical data – cost and API keys; not needed because rates are frozen.

## Consequences
* Reports in base currency are stable and reproducible.
* Changing the base currency later does not convert history (documented as technical debt TD-03).
* The app works offline from the provider; estimated values are labelled.

## Addendum (Sprint 1)
* **Storage:** rates are cached as *1 USD = x currency* per day; any pair is a cross rate
  (`usd[B] / usd[A]`). One provider call per day serves every pair.
* **Back-dated entries:** the free provider only returns today's rates, so an entry dated more than
  7 days ago gets the fallback table rate and is flagged *estimated*. The form shows this and
  invites the user to type the real rate (technical debt TD-09).
* **Rate source of a transaction:** each transaction has two rates (to base, to home). Its single
  `rate_source` is the least certain of both: FALLBACK > USER > LIVE > IDENTITY, so an estimated
  part is never hidden.
* **Edits:** changing amount or date keeps the frozen rates; only an explicitly entered new rate
  replaces one.
