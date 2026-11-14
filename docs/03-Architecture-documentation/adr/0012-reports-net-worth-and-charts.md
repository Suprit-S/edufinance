# ADR-0012: Reports – net worth valuation and chart forms

**Status:** Accepted (Sprint 3)

## Context
Sprint 3 adds reports for a month, a year, a life phase and the whole journey, a net-worth line
and a loan payoff projection (FR-37 – FR-41). Two questions needed a decision:

1. **Valuation of net worth over time.** Wallets and loans are held in different currencies
   (e.g. an INR loan, EUR wallets). Valuing each past month at that month's exchange rate mixes two
   effects: the student's own saving/spending and currency movements (INR has lost value against
   EUR). Historic daily rates are also not available for every past date from the free API
   (ADR-0003).
2. **Chart form for category shares.** The first idea was a donut chart for "where the money
   went".

## Options
| Question | Option | Pros | Cons |
|---|---|---|---|
| Valuation | Rate of each month | Shows the "true" value at that time | Mixes currency effects into the user's behaviour; needs rates for every month-end; estimated rates for most of the history |
| | **Today's rate for all months** (constant rate) | Line only moves when the user saves, spends or repays; one rate set; stable and explainable | Past values differ from what the user saw at that time |
| Category shares | Donut chart | Familiar | Angles are hard to compare; many slices; colour-only identity fails for colour-blind users |
| | **Horizontal bar list (top 5 + "Other")** | Lengths are easy to compare; label and value as text; works at 360 px; no chart library needed | Less "decorative" |

## Decision
- Net worth = Σ wallet balances − Σ loan outstanding, **all converted at today's rates**. The
  report states this under the chart. A loan's past outstanding is reconstructed from its payments
  (`outstanding_on`).
- Category, phase and source shares use a **bar list** in plain HTML (top 5 + "Other", fixed
  order by amount, text values, percentage). Time series use Recharts with the validated two-colour
  palette (earned / spent) and a "Show as table" alternative.

## Consequences
- The net-worth line is understandable for non-experts and needs no historic rate per month.
- Currency gains/losses are not visible in the net-worth line; the cost reports (in base currency
  at the frozen transaction rates) and the remittance hidden-cost report cover the currency aspect.
- Before a loan's first recorded payment, its history uses the current outstanding (TD-15).
