# REST API Reference (v0.3.0)

Base URL: `/api`. JSON in and out. Money and exchange rates are **strings** (e.g. `"41.20"`,
`"0.00939891"`) so no precision is lost. Dates are ISO `YYYY-MM-DD`.

**Authentication:** `Authorization: Bearer <token>` (60-minute JWT from register/login).
All endpoints require it except those marked *public*.

**Errors** always look like this (see `backend/app/errors.py`):

```json
{"error": {"code": "VALIDATION_ERROR", "message": "Some fields are invalid.",
           "details": {"amount": ["Must be greater than 0."]}}}
```

| Status | Code | When |
|---|---|---|
| 401 | `UNAUTHORIZED`, `SESSION_EXPIRED`, `INVALID_CREDENTIALS` | Missing/invalid/revoked/expired token; wrong login |
| 404 | `NOT_FOUND` | Unknown ID **or another user's ID** (NFR-07) |
| 409 | `CONFLICT` | Duplicate name/e-mail; delete blocked by existing data |
| 422 | `VALIDATION_ERROR` | Invalid or unknown fields; business-rule violation |

## Public

| Method | Path | Description |
|---|---|---|
| GET | `/health` | `{"status":"ok","database":"ok"}` |
| GET | `/currencies` | ISO currencies `{code, name, symbol, minor_units}` |
| GET | `/countries` | `{code, name, default_currency}` |
| POST | `/auth/register` | Body: `full_name, email, password, date_of_birth, gender?, home_currency, base_currency, destination_country, planning_start_date, arrival_date, study_start_date, study_end_date, settling_in_days?` → 201 `{access_token, expires_in, user}` |
| POST | `/auth/login` | `{email, password}` → `{access_token, expires_in, user}` |

## Account and phases

| Method | Path | Description |
|---|---|---|
| POST | `/auth/logout` | Revokes the current token → 204 |
| POST | `/auth/password` | `{current_password, new_password}` → 204 |
| GET | `/me` | Profile incl. `age` and `phases[]` (`is_current`, `progress_pct`) |
| PATCH | `/me` | Any profile field; journey dates re-sync system phases and re-assign transactions |
| GET | `/phases` | All phases of the user |
| POST | `/phases` | `{name, phase_type: JOB_SEARCH\|CUSTOM, start_date, end_date?}` → 201 |
| PATCH | `/phases/{id}` | `name` for any phase; `start_date`/`end_date` for custom phases only |
| DELETE | `/phases/{id}` | Custom phases only → 204 (transactions re-assigned) |

## Wallets and categories

| Method | Path | Description |
|---|---|---|
| GET | `/wallets` | Wallets with current `balance` (own currency) and `runway` `{balance, spent_last_window, burn_rate_per_day, days (null = unlimited), status: HEALTHY\|OK\|WARNING\|CRITICAL}` (null for archived) |
| POST | `/wallets` | `{name, currency_code, wallet_type: BANK\|CASH\|SAVINGS\|PROOF_OF_FUNDS, opening_balance, opening_date}` → 201 |
| GET | `/wallets/{id}` | One wallet with balance and runway |
| PATCH | `/wallets/{id}` | Fields above + `is_archived`; currency only while empty |
| DELETE | `/wallets/{id}` | Only if it has no transactions (else 409 – archive instead) |
| GET | `/categories?kind=INCOME\|EXPENSE` | System + own categories |
| POST | `/categories` | `{name, kind, group_name?, counts_as_earned?}` → 201 |
| DELETE | `/categories/{id}` | Own, unused categories only |

## Transactions and rates

| Method | Path | Description |
|---|---|---|
| GET | `/transactions` | Query: `wallet_id, kind, category_id, phase_id, date_from, date_to, q, page, per_page (≤200)` → `{items, total, page, per_page}` newest first |
| POST | `/transactions` | `{kind: INCOME\|EXPENSE, wallet_id, category_id, amount, txn_date, note?, phase_id?, rate_to_base?, rate_to_home?}` → 201. Omitted rates = market rate, frozen. |
| GET | `/transactions/{id}` | One transaction |
| PATCH | `/transactions/{id}` | `category_id, amount, txn_date, note, phase_id (null = automatic), rate_to_base, rate_to_home` – stored rates kept unless a new rate is given |
| DELETE | `/transactions/{id}` | 204 (409 if it belongs to a remittance or loan payment – manage it there) |
| GET | `/fx/rate?from=INR&to=EUR&date=` | `{from, to, rate, source, rate_date, estimated}` for pre-filling forms |

**Transaction fields returned:** `id, wallet_id, kind, category_id, category_name, amount,
currency_code, txn_date, note, phase_id, phase_name, phase_is_manual, rate_to_base, rate_to_home,
amount_base, amount_home, rate_source (IDENTITY|USER|LIVE|FALLBACK), estimated, remittance_id`.

## Remittances (Sprint 2)

| Method | Path | Description |
|---|---|---|
| GET | `/remittances` | `{items[], summary: {count, hidden_cost_total, hidden_cost_year, year}}` newest first |
| POST | `/remittances` | `{from_wallet_id?, to_wallet_id?, sent_amount, received_amount, sent_currency? (if no sender wallet), received_currency? (if no receiver wallet), fee_amount?, provider?, remit_date, category_id?, note?}` → 201. At least one own wallet. |
| GET | `/remittances/{id}` | One remittance: `direction (OWN\|IN\|OUT), effective_rate, market_rate, hidden_cost_base, …` |
| DELETE | `/remittances/{id}` | Deletes the remittance and its transactions → 204 |

## Monthly Plan and Target to Earn (Sprint 2)

| Method | Path | Description |
|---|---|---|
| GET | `/plan?month=YYYY-MM` | `{month, currency, minimum_target, estimated_rates, items[]}`; each item has `active_this_month` and `amount_base` |
| POST | `/plan` | `{name, category_id (expense), amount, currency_code, valid_from, valid_to?, phase_id?}` → 201 |
| PATCH | `/plan/{id}` | Any field above (409 for EMI lines – they follow their loan) |
| DELETE | `/plan/{id}` | 204 (409 for EMI lines) |
| GET | `/target?month=YYYY-MM` | `{target, earned, spent, still_to_earn, surplus_over_target, net, progress_pct, estimated_rates, by_source[], lines[] (planned, actual, difference), history[6] (month, target, earned, spent)}` |

## Loans (Sprint 2)

| Method | Path | Description |
|---|---|---|
| GET | `/loans` | Loans with `summary` and `affordability` |
| POST | `/loans` | `{name, lender?, currency_code, annual_rate_pct, sanctioned_amount, outstanding_amount, emi_amount, emi_start_date?, min_part_payment?, default_wallet_id? (same currency), note?}` → 201 |
| GET | `/loans/{id}` | Loan + `summary` (incl. `schedule[]`) + `affordability` + `payments[]` (newest first) |
| PATCH | `/loans/{id}` | Any field above; correcting `outstanding_amount` is allowed at any time |
| DELETE | `/loans/{id}` | Deletes loan, payments and EMI plan line; wallet expenses stay → 204 |
| POST | `/loans/{id}/payments` | `{payment_type: EMI\|PART_PAYMENT, amount, paid_on, wallet_id? (omit = loan default, null = none), note?}` → 201 with `interest_part, principal_part, balance_before, balance_after, interest_saved, emis_saved` |
| DELETE | `/loans/{id}/payments/{pid}` | Undo – only the latest payment (else 409) → 204 |

`summary`: `interest_paid, principal_paid, total_paid, interest_saved, emis_saved, months_to_payoff,
future_interest, payoff_month, emi_covers_interest, repaid_pct`.
`affordability` (null without a minimum part-payment): `status (AFFORDABLE|SAVE|NOT_AFFORDABLE),
months_needed, avg_surplus, buffered_surplus, min_part_payment_base, interest_saved_if_paid,
emis_saved_if_paid, lookback_months, buffer_pct, estimated_rate`.

## Reports and dashboard (Sprint 3)

All amounts are in the user's base currency, converted with the rates frozen on each transaction.
`estimated_rates: true` means today's rates came from the cache or the fallback table.

| Method | Path | Description |
|---|---|---|
| GET | `/reports?period=MONTH&value=2026-11` | Also `period=YEAR&value=2026`, `period=PHASE&value=<phase id>`, `period=LIFETIME` (planning start → today). → `{period {kind, start, end, label}, currency, earned, other_income (not earned, e.g. loan money), spent, net, by_source[], top_categories[] (top 5 + "Other"), by_phase[], monthly[] {month, earned, spent}}`. 422 for an unknown period, a malformed value or another user's phase |
| GET | `/reports/costs` | `{going_abroad {total, by_group[]}, degree {total_so_far, until, complete, study_progress_pct, as_of}}` |
| GET | `/reports/net-worth` | `{estimated_rates, points[] {month, assets, debt, net_worth}}` from planning start to this month, all at today's rates (ADR-0012) |
| GET | `/reports/loans` | `{debt_free_month, loans[] {loan_id, name, payoff_month}, points[] {month, outstanding}}`, projected with the current EMIs |
| GET | `/dashboard` | `{total_balance, wallets[] {id, name, currency_code, balance, balance_base, runway}, alerts[] (Warning/Critical wallets), this_month {month, target, earned, spent, still_to_earn, progress_pct}, loans {active, outstanding, emi_this_month, debt_free_month}, current_phase_id, spending_30d {total, categories[]}, estimated_rates}` |

## Data rights (Sprint 3)

| Method | Path | Description |
|---|---|---|
| GET | `/account/export` | JSON file download (`Content-Disposition: attachment`) with profile, phases, wallets, own categories, transactions, remittances, plan items, loans and payments. Never contains the password hash |
| DELETE | `/account` | `{password}` → 204; deletes the user and all their data; the token stops working. 422 for a wrong password |
