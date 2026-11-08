# Test-Case Catalogue

Each test case names the requirement it verifies, concrete input values and the expected
behaviour. Automated tests carry the test-case ID in their name (e.g. `test_tc_m01_...`), so every
row can be found in the code. Status: ✅ passing · ⏳ planned for the sprint shown.

**Sprint 1 totals:** 57 backend tests (service-layer coverage 95 %), 19 frontend tests – all passing.

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

## Sprint 1 – Accounts and security (`test_auth.py`)

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-A01 | FR-01, FR-07 | Register Ananya Rao, INR → EUR, DE, planning 2025-06-01, arrival 2025-09-25, study 2025-10-01 → 2027-09-30, password `Demo#2026` | 201, token returned; phases PRE_DEPARTURE, SETTLING_IN, STUDY, WORK | `test_tc_a01_...` | ✅ |
| TC-A02 | FR-02 | Register again with `ANANYA@example.com` | 409 `CONFLICT`; still one user | `test_tc_a02_...` | ✅ |
| TC-A03 | FR-02, FR-19 | Home currency `XYZ` | 422, field error on `home_currency` | `test_tc_a03_...` | ✅ |
| TC-A03b | FR-02 | Arrival 2025-05-01 (before planning), study end 2025-09-01 (before start) | 422, errors on `arrival_date` and `study_end_date` | `test_tc_a03b_...` | ✅ |
| TC-A03c | FR-01 | Password `abcdefgh` (no digit) and unknown field `x` | 422, errors on `password` and `x` | `test_tc_a03c_...` | ✅ |
| TC-A04 | FR-04 | Wrong password; unknown e-mail | Both 401 with identical body "E-mail or password is incorrect." | `test_tc_a04_...` | ✅ |
| TC-A05 | FR-04 | Login with ` Ananya@Example.com ` | 200, `expires_in` = 3600 s | `test_tc_a05_...` | ✅ |
| TC-A06 | FR-06 | Change password with wrong current one; then with `Demo#2026` → `NewPass2026` | 422; then 204 and login with new password works | `test_tc_a06_...` | ✅ |
| TC-A07 | FR-03 | `GET /api/me` | Name, computed age (int); no password field | `test_tc_a07_...` | ✅ |
| TC-SEC01 | NFR-04 | Register, inspect response and DB row | Response does not contain the password; hash starts with `$2b$` | `test_tc_sec01_...` | ✅ |
| TC-SEC02 | NFR-05 | Logout, then `GET /api/me` with the old token | 401 `UNAUTHORIZED` | `test_tc_sec02_...` | ✅ |
| TC-SEC02b | NFR-05 | Token expired 1 s ago | 401 `SESSION_EXPIRED` | `test_tc_sec02b_...` | ✅ |
| TC-SEC03 | NFR-06 | Every route/method in the URL map except the 5 public ones, without token | 401 for all (≥ 20 checked) | `test_tc_sec03_...` | ✅ |

## Sprint 1 – Life phases (`test_phases.py`)

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-PH01 | FR-07 | Planning 2025-06-01, arrival 2025-09-25, study 2025-10-01 → 2027-09-30, settling 60 days | Pre-departure 2025-06-01–2025-09-24; Settling in 2025-09-25–2025-11-23; Study 2025-10-01–2027-09-30; Work from 2027-10-01 (open) | `test_tc_ph01_...` | ✅ |
| TC-PH02 | FR-09 | Date 2025-08-10 | Pre-departure | `test_tc_ph02_...` | ✅ |
| TC-PH03 | FR-09 | Dates 2025-10-15, 2025-12-01, 2031-01-01 | Settling in (shorter overlapping phase wins), Study, Work | `test_tc_ph03_...` | ✅ |
| TC-PH04 | FR-10 | Automatic and manual (Study) expense on 2025-09-22; then arrival moved to 2025-09-20 | Automatic → Settling in; manual stays Study | `test_tc_ph04_...` | ✅ |
| TC-PH05 | FR-09 | Date before all phases; date in a gap between two phases | First phase; closest earlier phase | `test_tc_ph05_...` | ✅ |
| TC-PH06 | US-14 | Phase 1–10 Oct on 5 Oct / before / after; open-ended phase | 50 %, 0 %, 100 %, none | `test_tc_ph06_...` | ✅ |
| TC-PH07 | FR-08 | Expense 2027-11-15 (Work); add "Job search" 2027-10-01–2028-01-31; delete it | Moves to Job search; back to Work after delete | `test_tc_ph07_...` | ✅ |
| TC-PH08 | FR-08 | Rename Study; change Study start via phases API; delete Study; add phase of type STUDY | 200; 422 (dates come from profile); 409; 422 | `test_tc_ph08_...` | ✅ |

## Sprint 1 – Exchange rates (`test_fx.py`)

Cached test rates: 1 USD = 0.86 EUR = 91.5 INR. Fallback table: 1 USD = 0.858 EUR = 91.0 INR.

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-FX01 | NFR-08 | INR → EUR, today's rates cached | 0.00939891, LIVE; provider not called | `test_tc_fx01_...` | ✅ |
| TC-FX02 | NFR-08 | No cache; provider returns EUR 0.85, INR 90 (+ unknown code) | EUR→INR 105.88235294 LIVE; second pair served from cache (1 provider call) | `test_tc_fx02_...` | ✅ |
| TC-FX03 | NFR-08 | Provider down; cache 5 days old (EUR 0.80, INR 88) | 110.00000000, estimated | `test_tc_fx03_...` | ✅ |
| TC-FX04 | NFR-08 | Provider down; newest cache 10 days old | Fallback table: 106.06060606, estimated, rate date 2026-01-01 | `test_tc_fx04_...` | ✅ |
| TC-FX05 | FR-14 | Cross rates from USD table | INR→EUR 0.00939891; EUR→INR 106.39534884; EUR→EUR 1; missing GBP → none | `test_tc_fx05_...` | ✅ |
| TC-FX06 | FR-16 | `GET /api/fx/rate?from=inr&to=EUR`; `from=XYZ` | 200 rate "0.00939891", not estimated; 422 | `test_tc_fx06_...` | ✅ |

## Sprint 1 – Wallets, categories, transactions (`test_wallets_transactions.py`)

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-W01 | FR-17 | Wallet opening €500; expense €41.20; income €250 | Balance €708.80 | `test_tc_w01_...` | ✅ |
| TC-W02 | FR-11 | Second wallet "daily spending"; change currency after a transaction; delete it; archive it; book into archived wallet | 409; 422; 409; 200; 422 | `test_tc_w02_...` | ✅ |
| TC-W03 | FR-11 | Delete an empty wallet | 204; wallet list empty | `test_tc_w03_...` | ✅ |
| TC-T01 | FR-14 | ₹2,000 expense today in INR wallet, cached rate | amount_base €18.80, amount_home ₹2,000.00, LIVE | `test_tc_t01_...` | ✅ |
| TC-T02 | FR-16 | Same with user rate 0.0100 | €20.00, rate 0.01000000, USER | `test_tc_t02_...` | ✅ |
| TC-T03 | FR-15 | Market rates doubled after saving | Stored amount_base still €18.80 | `test_tc_t03_...` | ✅ |
| TC-T04 | FR-13, FR-19 | Amount −5, 0, "abc"; income with expense category | 422 for all; error on `category_id` | `test_tc_t04_...` | ✅ |
| TC-T05 | FR-14 | Combine rate sources | IDENTITY+LIVE→LIVE; USER+LIVE→USER; USER+FALLBACK→FALLBACK | `test_tc_t05_...` | ✅ |
| TC-T06 | FR-14 | €100 expense in EUR wallet | amount_base €100.00; amount_home ₹10,639.53 | `test_tc_t06_...` | ✅ |
| TC-T07 | FR-15 | Edit amount ₹2,000 → ₹3,000 (rate 0.01); then rate → 0.0095 | €30.00 (frozen rate); €28.50; delete 204 | `test_tc_t07_...` | ✅ |
| TC-T08 | FR-13 | 4 transactions; `per_page=2`; `kind=INCOME`; `q=shop 1`; `page=0` | total 4, 2 items newest first; only "DAAD"; 1 hit; 422 | `test_tc_t08_...` | ✅ |
| TC-C01 | FR-12 | Custom "Badminton club"; duplicate "groceries"; delete system "Rent"; delete custom | 201; 409; 409; 204 | `test_tc_c01_...` | ✅ |
| TC-SEC04 | NFR-07 | User B reads/edits/deletes A's wallet and transaction; uses A's category, phase, wallet | 404 everywhere; B sees no data of A; A's balance unchanged | `test_tc_sec04_...` | ✅ |

## Frontend (Vitest + React Testing Library)

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-F01 | FR-17 | `formatMoney("1234.5","EUR")`, `formatMoney("-14000","INR")` | "€1,234.50", "-₹14,000.00" | `format.test.js` | ✅ |
| TC-F02 | FR-37 | `formatPercent(22.645)`, `formatDate("2026-11-05")` | "22.6%", "5 Nov 2026" | `format.test.js` | ✅ |
| TC-F03 | NFR-02 | Render sidebar at `/wallets` | All 9 links and the user visible; "Wallets" active | `Sidebar.test.jsx` | ✅ |
| TC-F04 | US-18 | Click "Dark", then "Auto" | `data-theme="dark"` set and stored; removed again on Auto | `Sidebar.test.jsx` | ✅ |
| TC-F05 | – | API error 422 with body; network failure | Code/message/details kept; `NETWORK_ERROR` | `client.test.js` | ✅ |
| TC-F05b | – | Details `{amount: ["Not a valid number.", "x"]}` | `{amount: "Not a valid number."}` | `client.test.js` | ✅ |
| TC-F06 | FR-13 | Transaction form: switch Expense → Income; save €41.20 Groceries "Lidl" | Only matching categories offered; POST without `rate_to_base` | `TransactionForm.test.jsx` | ✅ |
| TC-F07 | FR-16 | INR wallet: market rate 0.00939891 pre-filled; ₹2,000; user changes rate to 0.01 | Preview "€18.80"; POST contains `rate_to_base: "0.01"` | `TransactionForm.test.jsx` | ✅ |
| TC-F08 | FR-04 | Click "Log out" | `logout()` called | `Sidebar.test.jsx` | ✅ |
| TC-F09 | FR-04 | Login rejected (401); session expired notice | Generic error shown as alert; notice shown as status | `LoginPage.test.jsx` | ✅ |

## Sprint 1 – Manual end-to-end check (browser)

Performed at the end of Sprint 1 with the production build (Chromium, 1366 × 900 and 360 × 760).

| ID | Steps | Expected | Result |
|---|---|---|---|
| TC-E2E01 | Register Ananya → add wallets Home Account (₹350,000), Daily Spending (€0), Blocked Account (€11,904) → 4 INR pre-departure expenses (2 with own rate) → 4 EUR entries → add "Job search" phase → move arrival → dashboard → log out | Balances ₹266,200.00 and €713.30; phases assigned by date; own rates marked as USER, market rates "est." when the provider is unreachable; logged-out message shown | ✅ |
| TC-U01 (partial) | Dashboard, Transactions, Wallets, Profile at 360 px | No horizontal scrolling | ✅ (0 px overflow) |

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
