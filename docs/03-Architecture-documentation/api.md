# REST API Reference (v0.1.0)

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
| GET | `/wallets` | Wallets with current `balance` (own currency) |
| POST | `/wallets` | `{name, currency_code, wallet_type: BANK\|CASH\|SAVINGS\|PROOF_OF_FUNDS, opening_balance, opening_date}` → 201 |
| GET | `/wallets/{id}` | One wallet with balance |
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
| DELETE | `/transactions/{id}` | 204 (409 if it belongs to a remittance/loan payment) |
| GET | `/fx/rate?from=INR&to=EUR&date=` | `{from, to, rate, source, rate_date, estimated}` for pre-filling forms |

**Transaction fields returned:** `id, wallet_id, kind, category_id, category_name, amount,
currency_code, txn_date, note, phase_id, phase_name, phase_is_manual, rate_to_base, rate_to_home,
amount_base, amount_home, rate_source (IDENTITY|USER|LIVE|FALLBACK), estimated, remittance_id`.
