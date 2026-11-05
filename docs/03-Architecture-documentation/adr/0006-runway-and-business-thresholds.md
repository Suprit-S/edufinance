# ADR-0006: Runway calculation and configurable thresholds

**Status:** Accepted

## Context
Students need an early warning before a wallet runs empty.

## Decision
* Burn rate = sum of **expenses** of the wallet in the last 30 days ÷ 30. Transfers to own wallets
  are not spending and are excluded.
* Runway (days) = balance ÷ burn rate, rounded down; no spending → unlimited.
* Status: Healthy > 90 days, OK 60–90, Warning 30–60, Critical < 30.
* All numbers (window, thresholds, settling-in default, affordability buffer) live in
  configuration (`app/config.py`, environment variables), not in code.

## Consequences
Thresholds can be tuned without code changes. A 30-day average reacts to one-off large expenses
(e.g. annual insurance); this is acceptable for an early-warning signal and documented.
