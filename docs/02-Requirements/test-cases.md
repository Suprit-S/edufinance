# Test-Case Catalogue

Each test case names the requirement it verifies, concrete input values and the expected
behaviour. Automated tests carry the test-case ID in their name (e.g. `test_tc_m01_...`), so every
row can be found in the code. Status: ✅ passing · ⏳ planned for the sprint shown.

**Totals after Sprint 2:** 88 backend tests (service-layer coverage 96 %), 28 frontend tests – all passing.

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

## Sprint 2 – Remittances (`test_remittances.py`)

Cached test rates: 1 USD = 0.963 EUR = 90 INR, so the market rate INR → EUR is 0.0107.

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-R01 | FR-20, FR-21 | Home Account ₹200,000 → Daily Spending €100: sent ₹50,000, received €520 | Effective rate 0.01040000; TRANSFER_OUT ₹50,000 (= €520.00, USER rate), TRANSFER_IN €520 (= ₹50,000.00, rate 96.15384615); balances ₹150,000.00 / €620.00 | `test_tc_r01_...` | ✅ |
| TC-R02 | FR-22 | Same transfer; again with fee ₹100 | Market rate 0.0107; hidden cost €15.00 (50,000 × 0.0107 − 520); with fee €16.07; fee booked as "Transfer fees"; total €31.07 | `test_tc_r02_...` | ✅ |
| TC-R03 | FR-20, FR-27 | Parents send ₹25,000 (no sender wallet), €250 received | One INCOME "Family support" €250, home value ₹25,000.00, USER rate | `test_tc_r03_...` | ✅ |
| TC-R04 | FR-20 | €100 sent home from Daily Spending, ₹9,500 received outside | One EXPENSE "Gifts & family" €100, rate to home 95, home value ₹9,500.00 | `test_tc_r04_...` | ✅ |
| TC-R05 | FR-18 | €60 from Daily Spending to Savings (same currency) | Rate 1, hidden cost €0.00, TRANSFER_IN + TRANSFER_OUT (not income/expense) | `test_tc_r05_...` | ✅ |
| TC-R06 | FR-20 | No own wallet; same wallet twice; fee with outside sender; outside sender without currency; income transfer with expense category; amount 0 | 422 each (field errors where applicable) | `test_tc_r06_...` | ✅ |
| TC-R07 | FR-20 | Edit/delete a transfer's transaction; delete the transfer | 409, 409; 204 – its transactions are gone and balances restored | `test_tc_r07_...` | ✅ |

## Sprint 2 – Monthly Plan and Target to Earn (`test_plan_target.py`)

Rate for EMIs: 1 INR = 0.00940512 EUR.

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-PL01 | FR-24, FR-25 | Rent €420, insurance €135, loan EMI ₹14,000 | Minimum target €686.67; EMI line "EMI – SBI education loan" = €131.67 | `test_tc_pl01_...` | ✅ |
| TC-PL02 | FR-24 | Loan with first EMI 2028-04-05 | Target 2027-11 = €0.00; 2028-04 = €131.67 | `test_tc_pl02_...` | ✅ |
| TC-PL03 | FR-23 | Semester ticket €58 only during *Study*; laptop €100 until 2026-09-30; month "2026-13" | 2026-05 = €158.00; 2028-01 = €0.00; 422 | `test_tc_pl03_...` | ✅ |
| TC-PL04 | FR-23, FR-24 | Edit/delete EMI line; plan item with income category; valid_to before valid_from; change rent to €450 | 409, 409; 422; 422; €450.00 | `test_tc_pl04_...` | ✅ |
| TC-TE01 | FR-26 | Plan €1,104.67 (incl. EMI); this month salary €250, loan disbursement €3,000, rent paid €420 | Target €1,104.67; earned €250.00; still to earn €854.67; 22.6 %; spent €420.00; net −€170.00; rent actual €420.00; 6 history months | `test_tc_te01_...` | ✅ |
| TC-TE02 | FR-27 | Same – the €3,000 loan disbursement | Not counted as earned | `test_tc_te01_...` | ✅ |
| TC-TE03 | FR-26 | Plan €420; salary €612.50 | Still to earn €0.00; surplus €192.50 | `test_tc_te03_...` | ✅ |
| TC-TE04 | FR-26 | EMI ₹14,000 and part-payment ₹20,000 in the same month | EMI line: planned €131.67, actual €131.67 (part-payments are extra, not the plan) | `test_tc_te04_...` | ✅ |
| TC-PL05 | FR-23 | Month helpers: parse "2026-02", end of Feb 2028, +3 / −1 months, item/phase overlap | 2026-02-01; 2028-02-29; 2027-02-01 / 2025-12-01; correct active flags | `test_pure_month_helpers` | ✅ |

## Sprint 2 – Loans (`test_loans.py`)

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-L01 | FR-31 | ₹100,000 at 12 %, EMI ₹10,000; payment ₹500 | Interest ₹1,000.00, principal ₹9,000.00; ₹500 → interest only | `test_tc_l01_...` | ✅ |
| TC-L01b | FR-30, FR-31 | ₹520,000 at 8.5 %, EMI ₹14,000 paid from Home Account (₹100,000) | Interest ₹3,683.33, principal ₹10,316.67, balance ₹509,683.33; wallet ₹86,000.00 | `test_tc_l01b_...` | ✅ |
| TC-L02 | FR-32 | ₹100,000 at 12 %, EMI ₹10,000 | 11 months; future interest ₹5,898.48; first row 10,000 / 1,000 / 9,000 / 91,000; EMI = interest → never | `test_tc_l02_...` | ✅ |
| TC-L03 | FR-32 | Part-payment ₹20,000 on that loan (pure + API) | Balance ₹80,000; interest saved ₹2,088.94; 2 EMIs saved; payoff 9 months; 20 % repaid | `test_tc_l03_...`, `test_tc_l03b_...` | ✅ |
| TC-L04 | FR-33 | Two EMIs; undo the first; undo the second; delete its wallet expense directly | 409; 204 and balance/wallet restored; 409 | `test_tc_l04_...` | ✅ |
| TC-L05 | FR-30 | EUR wallet for INR loan; EMI ₹14,000 on ₹10,000 balance; part-payment ₹10,001; payment dated before the last one | 422 each; final payment named (₹10,070.83) | `test_tc_l05_...` | ✅ |
| TC-L06 | FR-34 | Surplus €300, buffer 20 %, minimum €94.05 | AFFORDABLE, buffered €240.00 | `test_tc_l06_l07_...` | ✅ |
| TC-L07 | FR-34 | Surplus €50 → minimum €200; surplus −€20 | SAVE, 5 months; NOT_AFFORDABLE | `test_tc_l06_l07_...` | ✅ |
| TC-L08 | FR-30, FR-24 | Pay the final ₹10,070.83 | Loan CLOSED, 0 months left, EMI line ends this month, next month target €0.00; further payment 409 | `test_tc_l08_...` | ✅ |
| TC-L09 | FR-29 | Correct outstanding to ₹548,000 and EMI to ₹15,000; delete the loan | Plan for 2028-05 = €141.08; after delete no plan items | `test_tc_l09_...` | ✅ |
| TC-L10 | FR-34 | Last 3 months: salary €1,000 and rent €700 each; minimum part-payment ₹10,000 | Average surplus €300.00, buffered €240.00, minimum €94.05 → AFFORDABLE; interest saved > 0. 0 % laptop loan €600 / €100 → 6 months, no check | `test_tc_l10_...` | ✅ |

## Sprint 2 – Runway (`test_runway.py`)

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-RW01 | FR-35, FR-36 | Balance €613.79; €1,150 spent in 30 days | €38.33/day; 16 days; CRITICAL | `test_tc_rw01_...` | ✅ |
| TC-RW02 | FR-35 | No spending; negative balance with spending | Unlimited, HEALTHY; 0 days | `test_tc_rw02_...` | ✅ |
| TC-RW03 | FR-36 | 91 / 90 / 60 / 59 / 30 / 29 / 0 days | HEALTHY / OK / OK / WARNING / WARNING / CRITICAL / CRITICAL | `test_tc_rw03_...` | ✅ |
| TC-RW04 | FR-35 | Expenses 2 and 20 days ago (€800 + €350), one 40 days ago, €1 transfer to savings | Spent in window €1,150.00 (transfer and old expense ignored); €38.33/day; savings unlimited | `test_tc_rw04_...` | ✅ |

## Sprint 2 – Frontend

| ID | Requirement | Input | Expected result | Automated test | Status |
|---|---|---|---|---|---|
| TC-F10 | FR-26 | `addMonths("2026-11", 3)`, `addMonths("2026-01", -1)`, `monthLabel` | "2027-02", "2025-12", "Nov 2026" | `months.test.js` | ✅ |
| TC-F11 | FR-34 | Affordability card: AFFORDABLE, SAVE (5 months), no minimum | Matching sentence; buffered €240.00 shown; hint to set a minimum | `Sprint2Components.test.jsx` | ✅ |
| TC-F12 | FR-36 | Runway badge CRITICAL 16 days; HEALTHY no spending | "Critical · 16 days left" (text, not colour only) | `Sprint2Components.test.jsx` | ✅ |
| TC-F13 | FR-20, FR-22 | Transfer ₹50,000 → €520; "Received from outside" ₹25,000 → €250 | Live preview 1 EUR = 96.15 INR; payloads with both wallets / no sender wallet + sent currency | `RemittanceForm.test.jsx` | ✅ |

## Sprint 2 – Manual end-to-end check (browser)

| ID | Steps | Expected | Result |
|---|---|---|---|
| TC-E2E02 | Ananya with 6 months of salary/rent/groceries; plan items; transfer ₹50,000 → €520 (UI); money from family (UI); add SBI loan with minimum part-payment (UI); record EMI and ₹20,000 part-payment (UI); open Plan, Target, Wallets, Dashboard | Loan: interest ₹3,683.33 / principal ₹10,316.67; part-payment saves ₹6,860.63 and 2 EMIs, debt-free moves May 2030 → Mar 2030; EMI line in plan; low-funds alert on dashboard | ✅ |
| TC-U01 (partial) | All pages at 360 px | No horizontal page scrolling (wide tables scroll inside their card) | ✅ 0 px on all 9 pages |

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
