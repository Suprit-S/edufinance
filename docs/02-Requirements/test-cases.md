# Test-Case Catalogue

Each test case names the requirement it verifies, concrete input values and the expected
behaviour. Automated tests carry the test-case ID in their name (e.g. `test_tc_m01_...`), so every
row can be found in the code. Status: ✅ passing · ⏳ planned for the sprint shown.

How to run: `cd backend && pytest` (backend) · `cd frontend && npm test` (frontend).

## Money arithmetic (service `money`) – NFR-09

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-M01 | NFR-09 | `money("2.345")`, `money("2.344")`, `money("-2.345")` | 2.35, 2.34, −2.35 (half-up) | `test_money.py::test_tc_m01_money_rounds_half_up` | ✅ |
| TC-M02 | NFR-09 | `to_decimal(0.1)` (a float) | `TypeError` – floats are rejected | `test_tc_m02_float_is_rejected` | ✅ |
| TC-M03 | NFR-09 | `to_decimal("12,50€")` | `ValueError` | `test_tc_m03_invalid_number_is_rejected` | ✅ |
| TC-M04 | FR-14 | Convert 14,000 INR at 0.00940512 | 131.67 EUR | `test_tc_m04_convert_inr_to_eur` | ✅ |
| TC-M05 | FR-14 | Invert 106 (EUR→INR) | 0.00943396 (INR→EUR) | `test_tc_m05_invert_rate` | ✅ |
| TC-M06 | FR-14 | Invert 0 | `ValueError` | `test_tc_m06_invert_rate_rejects_zero` | ✅ |
| TC-M07 | NFR-09 | `rate("0.123456789")`; 0.1 + 0.2 | 0.12345679; exactly 0.30 | `test_tc_m07_rate_keeps_eight_decimals` | ✅ |

## Skeleton / infrastructure

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-S01 | NFR-10 | `GET /api/health` | 200, `{"status":"ok","database":"ok"}` | `test_skeleton.py::test_tc_s01_...` | ✅ |
| TC-S02 | FR-19 | `GET /api/currencies` (no login) | 200, list contains INR and EUR, sorted by code | `test_tc_s02_...` | ✅ |
| TC-S03 | FR-01 | `GET /api/countries` | Germany (DE) has default currency EUR | `test_tc_s03_...` | ✅ |
| TC-S04 | – | `GET /api/does-not-exist` | 404 with JSON body `error.code = "NOT_FOUND"` | `test_tc_s04_...` | ✅ |
| TC-S05 | FR-12 | Run master-data seed twice | Number of system categories unchanged (52) | `test_tc_s05_...` | ✅ |
| TC-S06 | FR-27 | Category "Loan disbursement" | `counts_as_earned = false`; "Part-time salary" = true | `test_tc_s06_...` | ✅ |
| TC-S07 | FR-02 | Save user with study end 2025-01-01 < study start 2025-10-01 | Database rejects the row (CHECK constraint) | `test_tc_s07_...` | ✅ |
| TC-S08 | FR-03 | DOB 2000-05-17; age on 2026-05-16 and 2026-05-17 | 25 and 26; no `age` column exists | `test_tc_s08_...` | ✅ |
| TC-S09 | NFR-09 | Read fallback rate USD→EUR | Returned as exact `Decimal("0.85800000")` | `test_tc_s09_...` | ✅ |

## Frontend

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-F01 | FR-17 | `formatMoney("1234.5","EUR")`, `formatMoney("-14000","INR")` | "€1,234.50", "-₹14,000.00" | `format.test.js` | ✅ |
| TC-F02 | FR-37 | `formatPercent(22.645)`, `formatDate("2026-11-05")` | "22.6%", "5 Nov 2026" | `format.test.js` | ✅ |
| TC-F03 | NFR-02 | Render sidebar at `/wallets` | All 8 links visible; "Wallets" active | `Sidebar.test.jsx` | ✅ |
| TC-F04 | US-18 | Click "Dark", then "Auto" | `data-theme="dark"` set and stored; removed again on Auto | `Sidebar.test.jsx` | ✅ |
| TC-F05 | – | API error 422 with body; network failure | Code/message/details kept; `NETWORK_ERROR` | `client.test.js` | ✅ |

## Planned – Sprint 1 (account, phases, wallets, transactions, FX)

| ID | Requirement | Input | Expected result | Status |
|---|---|---|---|---|
| TC-A01 | FR-01 | Register Ananya Rao, INR/EUR, DE, valid dates, password `Demo#2026` | 201, token returned; 4 phases created | ⏳ S1 |
| TC-A02 | FR-02 | Register again with the same e-mail | 409 `CONFLICT`, no second user | ⏳ S1 |
| TC-A03 | FR-02 | Currency "XYZ" | 422, field error on `home_currency` | ⏳ S1 |
| TC-A04 | FR-04 | Login with wrong password | 401 "E-mail or password is incorrect" | ⏳ S1 |
| TC-SEC01 | NFR-04 | Register, then read DB row and all API responses | Stored value starts with `$2b$`; no response contains `password` | ⏳ S1 |
| TC-SEC02 | NFR-05 | Logout, then call `/api/me` with the old token | 401 | ⏳ S1 |
| TC-SEC03 | NFR-06 | Call every non-public route without token | 401 for all | ⏳ S1 |
| TC-SEC04 | NFR-07 | User B requests user A's wallet ID | 404 | ⏳ S1 |
| TC-PH01 | FR-07 | Planning 2025-06-01, arrival 2025-09-25, study 2025-10-01 → 2027-09-30, settling 60 days | Pre-departure 2025-06-01–2025-09-24; Settling in 2025-09-25–2025-11-23; Study 2025-10-01–2027-09-30; Work from 2027-10-01 | ⏳ S1 |
| TC-PH02 | FR-09 | Expense dated 2025-08-10 | Phase Pre-departure | ⏳ S1 |
| TC-PH03 | FR-09 | Expense dated 2025-10-15 (inside Settling in and Study) | Settling in (when phases overlap, the shorter, more specific phase wins) | ⏳ S1 |
| TC-PH04 | FR-10 | Move arrival to 2025-09-20; one automatic and one manual transaction on 2025-09-22 | Automatic → Settling in; manual unchanged | ⏳ S1 |
| TC-W01 | FR-17 | Wallet opening €500; income €250; expense €41.20 | Balance €708.80 | ⏳ S1 |
| TC-T01 | FR-14 | Expense ₹2,000 in INR wallet, rate INR→EUR 0.0094 | amount_base €18.80, amount_home ₹2,000.00, rate source LIVE | ⏳ S1 |
| TC-T02 | FR-16 | Same with user rate 0.0100 | amount_base €20.00, rate source USER | ⏳ S1 |
| TC-T03 | FR-15 | Change cached market rate afterwards | Stored amount_base still €18.80 | ⏳ S1 |
| TC-T04 | FR-19 | Expense with amount −5 or 0 | 422 | ⏳ S1 |
| TC-FX01 | NFR-08 | Rate for today already cached | No provider call; cached rate used | ⏳ S1 |
| TC-FX02 | NFR-08 | No cache; provider returns EUR base rates | Rates stored with source API; result not estimated | ⏳ S1 |
| TC-FX03 | NFR-08 | Provider down; cached rate 5 days old | That rate used, flagged estimated | ⏳ S1 |
| TC-FX04 | NFR-08 | Provider down; newest cache 10 days old | Fallback table used (cross rate via USD), flagged estimated | ⏳ S1 |

## Planned – Sprint 2 (remittances, plan, target, loans, runway)

| ID | Requirement | Input | Expected result | Status |
|---|---|---|---|---|
| TC-R01 | FR-21 | Sent ₹50,000 from home wallet, received €520 into EUR wallet | Effective rate 0.0104; −₹50,000 and +€520 transactions linked, both TRANSFER kind | ⏳ S2 |
| TC-R02 | FR-22 | Same, market rate 0.01070 | Hidden cost = 50,000 × 0.0107 − 520 = €15.00 | ⏳ S2 |
| TC-R03 | FR-27 | Parents send ₹25,000 (no sender wallet), received €250 | One INCOME "Family support" +€250; counts as earned | ⏳ S2 |
| TC-PL01 | FR-25 | Rent €420, insurance €135, EMI ₹14,000 at 0.00940512 | Target €686.67 | ⏳ S2 |
| TC-PL02 | FR-24 | Loan with first EMI 2028-04-05 | EMI not in target for 2027-11; included from 2028-04 | ⏳ S2 |
| TC-TE01 | FR-26 | Nov: target €1,104.67, earned €250 | Still to earn €854.67; 22.6 % | ⏳ S2 |
| TC-TE02 | FR-27 | Income "Loan disbursement" €3,000 | Earned unchanged | ⏳ S2 |
| TC-L01 | FR-31 | Outstanding ₹100,000, 12 % p.a., EMI ₹10,000 | Interest ₹1,000.00; principal ₹9,000.00; balance ₹91,000.00 | ⏳ S2 |
| TC-L02 | FR-32 | Outstanding ₹100,000, 12 %, EMI ₹10,000 | Payoff in 11 months; total future interest ₹5,898.48 (interest rounded to the cent each month) | ⏳ S2 |
| TC-L03 | FR-32 | Part-payment ₹20,000 on the same loan | Balance ₹80,000; payoff 9 months; interest saved ₹2,088.94 (5,898.48 − 3,809.54); EMIs saved = 2 | ⏳ S2 |
| TC-L04 | FR-33 | Undo a payment that is not the latest | 409 CONFLICT | ⏳ S2 |
| TC-L05 | FR-30 | EMI paid from "Home Account – INR" | Wallet expense "Loan EMI" ₹14,000 created and linked | ⏳ S2 |
| TC-L06 | FR-34 | Avg. surplus €300, buffer 20 %, min part-payment ₹10,000 (≈ €94.05) | Affordable now | ⏳ S2 |
| TC-L07 | FR-34 | Avg. surplus €50, buffer 20 %, min part-payment €200 | Not affordable; ≈ 5 months of saving | ⏳ S2 |
| TC-RW01 | FR-35/36 | Balance €613.79; €1,150 spent in last 30 days | 38.33 €/day; 16 days; Critical | ⏳ S2 |
| TC-RW02 | FR-36 | No spending in last 30 days | Runway "∞"; Healthy | ⏳ S2 |

## Planned – Sprint 3 (reports, dashboard, quality)

| ID | Requirement | Input | Expected result | Status |
|---|---|---|---|---|
| TC-RP01 | FR-39 | Demo user | Cost of going abroad = sum of Pre-departure + Settling in expenses | ⏳ S3 |
| TC-RP02 | FR-37 | Period = phase Study | Only transactions of that phase counted | ⏳ S3 |
| TC-RP03 | FR-40 | Net worth on a date | Σ wallet balances (base) − Σ loan outstanding (base) | ⏳ S3 |
| TC-EX01 | FR-42 | Export | JSON contains wallets, transactions, loans, plan; no password hash | ⏳ S3 |
| TC-EX02 | FR-42 | Delete account | All rows of the user removed; login fails | ⏳ S3 |
| TC-P01 | NFR-01 | 2,000 transactions, 50 dashboard requests | p95 ≤ 2 s | ⏳ S3 |
| TC-U01 | NFR-02 | Check every page at 360 / 768 / 1280 / 1920 px | No horizontal scrolling | ⏳ S3 |
| TC-U02 | NFR-03 | 3 first-time users record an expense | Each ≤ 60 s | ⏳ S3 |
| TC-U03 | NFR-12 | Lighthouse accessibility audit | Score ≥ 90 | ⏳ S3 |
| TC-D01 | NFR-10 | Clean machine: `docker compose up --build` | App on :8080 within 5 min | ⏳ S3 |
| TC-D02 | NFR-13 | Uptime check of the cloud URL for 7 days | No downtime, no cold start | ⏳ S3 |
