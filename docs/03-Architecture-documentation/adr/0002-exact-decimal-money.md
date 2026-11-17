# ADR-0002: Exact decimal arithmetic for money

**Status:** Accepted

## Context
Binary floating point cannot represent most decimal fractions (0.1 + 0.2 = 0.30000000000000004).
In a finance tool, such errors accumulate over thousands of transactions and break trust.

## Options
1. Floats everywhere – simple, but inexact.
2. Integers in minor units (cents) – exact, but awkward for exchange rates and currencies with 0
   decimals.
3. **Decimal types end-to-end** – `NUMERIC` in PostgreSQL, `decimal.Decimal` in Python, strings
   in JSON.

## Decision
Option 3.
* Amounts: `NUMERIC(14,2)`; exchange rates: `NUMERIC(18,8)`; interest rates: `NUMERIC(6,3)`.
* All arithmetic in the service layer uses `app.services.money` (`money()`, `rate()`,
  `convert()`); creating a Decimal from a float raises an error.
* Rounding: commercial half-up, to cents, only when a value is stored or displayed.
* The API sends amounts as strings; the frontend formats them but never calculates totals.

## Consequences
Exact results, verified by test cases TC-M01–M07. Slightly more verbose code than floats.
