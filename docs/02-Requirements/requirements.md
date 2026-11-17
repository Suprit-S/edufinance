# Requirements – EduFinance

Requirements describe **what** the system must do, not **how** it is built. Design decisions are
recorded separately as [ADRs](../03-Architecture-documentation/adr/). Each functional requirement
traces to a user story (US) in the [project plan](../01-Project-management/project-plan.md) and to
test cases in the [test-case catalogue](test-cases.md).

Priority: **M** = must, **S** = should, **C** = could (MoSCoW).

## 1. Stakeholders

| Stakeholder | Interest |
|---|---|
| International student (primary user) | Know how long money lasts, what to earn, when loans are repaid |
| Family supporting the student (indirect) | Transparent use of money sent |
| Tutor / examiner | Traceable requirements, working software, documentation |
| Developer (author) | Maintainable code, reproducible setup |

## 2. Functional requirements

### 2.1 Account and profile

| ID | Requirement | Prio | US |
|---|---|---|---|
| FR-01 | The system shall let a person register with full name, e-mail, password, date of birth, optional gender (female / male / diverse / prefer not to say), home currency, base currency, destination country, planning start date, arrival date, study start date and planned study end date. | M | US-01 |
| FR-02 | The system shall reject a registration whose e-mail is already registered, whose dates are not in a plausible order (planning ≤ arrival, study start < study end) or whose currencies/country are unknown. | M | US-01 |
| FR-03 | The system shall show the user's age, derived from the date of birth, without storing the age. | C | US-01 |
| FR-04 | The system shall let a registered user log in with e-mail and password and log out again. | M | US-02 |
| FR-05 | The system shall let the user change profile data, currencies and all study dates at any time. | M | US-01 |
| FR-06 | The system shall let the user change the password after confirming the current one. | S | US-02 |

### 2.2 Life phases

| ID | Requirement | Prio | US |
|---|---|---|---|
| FR-07 | On registration the system shall create the phases *Pre-departure* (planning start → day before arrival), *Settling in* (arrival + configurable number of days, default 60), *Study* (study start → study end) and *Work* (after study end, open-ended). | M | US-03 |
| FR-08 | The user shall be able to rename phases and add, re-date and delete custom phases such as *Job search*. The dates of the four system phases follow the journey dates in the profile. | M | US-03 |
| FR-09 | Every transaction shall belong to exactly one phase, determined by its date unless the user chose a phase explicitly. Where phases overlap, the shorter (more specific) phase applies. | M | US-03 |
| FR-10 | When phase dates change, transactions whose phase was determined by date shall be re-assigned; manually assigned transactions shall keep their phase. | M | US-03 |

### 2.3 Wallets, categories and transactions

| ID | Requirement | Prio | US |
|---|---|---|---|
| FR-11 | The user shall be able to create, rename, archive and delete wallets; each wallet has exactly one currency, a type (bank, cash, savings, proof of funds) and an opening balance. | M | US-04 |
| FR-12 | The system shall provide predefined income and expense categories grouped by topic and typical phase, and let the user add own categories. | M | US-05 |
| FR-13 | The user shall be able to record, edit and delete income and expense transactions with wallet, category, amount, date, optional note and optional phase. | M | US-05 |
| FR-14 | The system shall store for each transaction its value in the user's base and home currency, using the exchange rate valid when the transaction was saved. | M | US-06 |
| FR-15 | Exchange rates stored with a transaction shall never change afterwards, even if market rates change. | M | US-06 |
| FR-16 | When recording a foreign-currency transaction, the system shall propose the current market rate and let the user overwrite it. | M | US-06 |
| FR-17 | The system shall show each wallet's current balance (opening balance plus all its transactions). | M | US-04 |
| FR-18 | The user shall be able to move money between two own wallets without it counting as income or expense (delivered with remittances, Sprint 2). | S | US-07 |
| FR-19 | Only known currencies and existing categories shall be accepted. | M | US-05 |

### 2.4 Remittances (international transfers)

| ID | Requirement | Prio | US |
|---|---|---|---|
| FR-20 | The user shall be able to record a transfer by entering the amount sent (currency A) and the amount received (currency B), with optional fee and provider, in both directions (from family / to family / between own wallets). | M | US-07 |
| FR-21 | The system shall derive the effective rate (received ÷ sent) and use it for the resulting transactions. | M | US-07 |
| FR-22 | The system shall show the market rate of that day next to the effective rate and the resulting hidden cost in the base currency. | S | US-07 |

### 2.5 Monthly plan and Target to Earn

| ID | Requirement | Prio | US |
|---|---|---|---|
| FR-23 | The user shall be able to maintain a list of recurring monthly obligations (name, category, amount, currency, valid from/to, optional phase). | M | US-08 |
| FR-24 | Every active loan's EMI shall automatically be part of the monthly plan from its first due month. | M | US-08 |
| FR-25 | The system shall calculate the minimum monthly target as the sum of all obligations valid in that month, converted to the base currency. | M | US-08 |
| FR-26 | For any month the system shall show target, earned, spent, shortfall or surplus, earnings by source and plan vs. actual per plan line. | M | US-09 |
| FR-27 | Money that is not earned (e.g. a loan disbursement, transfers between own wallets) shall not count as earned. | M | US-09 |

### 2.6 Loans

| ID | Requirement | Prio | US |
|---|---|---|---|
| FR-28 | The user shall be able to record loans in any currency with name, lender, interest rate, sanctioned amount, outstanding amount, EMI, optional first EMI date and optional minimum part-payment. | M | US-10 |
| FR-29 | The user shall be able to correct the outstanding amount at any time. | M | US-10 |
| FR-30 | The user shall be able to record EMIs and part-payments, optionally paid from a wallet (which then shows the expense). | M | US-10 |
| FR-31 | For each payment the system shall show the interest part, principal part and the balance afterwards. | M | US-10 |
| FR-32 | For each loan the system shall show months to payoff at the current EMI, future interest, interest paid and interest saved by part-payments. | M | US-10 |
| FR-33 | The user shall be able to undo the most recent payment of a loan. | S | US-10 |
| FR-34 | The system shall estimate whether the user can afford the minimum part-payment this month from the average monthly surplus, keeping a safety buffer, and otherwise estimate in how many months it becomes affordable. | S | US-11 |

### 2.7 Runway, reports and dashboard

| ID | Requirement | Prio | US |
|---|---|---|---|
| FR-35 | For each wallet the system shall calculate the average daily spending of the last 30 days and the number of days the balance lasts. | M | US-12 |
| FR-36 | Each wallet shall be classified as Healthy (> 90 days), OK (60–90), Warning (30–60) or Critical (< 30), and Warning/Critical wallets shall raise an alert on the dashboard. | M | US-12 |
| FR-37 | Every report shall be available for a selectable period: month, year, life phase or lifetime (since planning start). | M | US-13 |
| FR-38 | Reports shall show earned, spent, net, top categories and spending per phase in the base currency. | M | US-13 |
| FR-39 | The system shall report the total cost of going abroad (pre-departure + settling in) and the cost of the degree (everything up to study end). | M | US-13 |
| FR-40 | The system shall show a net-worth timeline (all wallets minus outstanding loans) and a loan payoff timeline. | S | US-13 |
| FR-41 | The dashboard shall show total balance, this month's earned vs. target, runway alerts, loan summary, current phase with progress and the last 30 days' spending by category. | M | US-14 |
| FR-42 | The user shall be able to export all own data and to delete the own account with all data. | S | US-15 |
| FR-43 | The system shall offer a demo account with realistic data. | M | US-16 |

## 3. Non-functional requirements

Each NFR has a measurable target and a verification method.

| ID | Quality (ISO 25010) | Requirement and target | Verification |
|---|---|---|---|
| NFR-01 | Performance | The dashboard API responds in ≤ 2 s (95th percentile) for a user with 2,000 transactions. | Performance test script with generated data (TC-P01) |
| NFR-02 | Usability / portability | All pages are usable at viewport widths from 360 px to 1920 px without horizontal scrolling. | Manual check at 360, 768, 1280, 1920 px (TC-U01) |
| NFR-03 | Usability | A first-time user records an expense in ≤ 60 s without instructions. | Timed task with 3 test persons (TC-U02) |
| NFR-04 | Security | Passwords are never stored or returned in readable form. | Automated test on DB content and all API responses (TC-SEC01) |
| NFR-05 | Security | A session ends after at most 60 minutes; after logout the session can no longer be used. | Automated test (TC-SEC02) |
| NFR-06 | Security | Every endpoint except registration, login, health and public master data requires an authenticated session. | Automated route scan test (TC-SEC03) |
| NFR-07 | Security / privacy | A user can never read or change another user's data (requests for foreign IDs answer "not found"). | Automated test per resource (TC-SEC04) |
| NFR-08 | Reliability | If the exchange-rate provider is unreachable, conversions still succeed with a rate at most 7 days old (else the stored fallback table) and the result is marked as "estimated". | Automated test with provider disabled (TC-FX03, TC-FX04) |
| NFR-09 | Correctness | Money amounts are exact to the cent; rounding is commercial (half up) and happens only at defined points. | Unit tests (TC-M01–M07) |
| NFR-10 | Portability / installability | The complete system starts on a clean machine with Docker using one command within 5 minutes (excluding image download). | Fresh-machine test (TC-D01) |
| NFR-11 | Maintainability | ≥ 80 % line coverage of the service layer; linters report zero errors. | CI coverage report |
| NFR-12 | Accessibility | Text contrast ≥ 4.5 : 1 (WCAG AA); all form fields have labels; all functions work with the keyboard; status is never shown by colour alone. | Lighthouse accessibility audit ≥ 90 and manual keyboard test (TC-U03) |
| NFR-13 | Availability | The cloud deployment is reachable 24/7 during the grading period without cold starts. | Uptime check (TC-D02) |

## 4. User stories and acceptance criteria

Acceptance criteria are written as *Given / When / Then* where it helps.

**US-01 Register**
- Given valid data, when I register, then my account exists and I am logged in.
- An already used e-mail returns a clear message; no second account is created.
- Study end before study start is rejected with a message on the field.

**US-02 Log in / out**
- Correct credentials log me in; wrong ones show "E-mail or password is incorrect" (no hint which one).
- After logout, the previous session token is rejected.

**US-03 Life phases**
- After registration I see four phases with dates derived from my profile.
- When I move my arrival date, transactions without a manual phase move with it.

**US-04 Wallets** – I can create a wallet "Daily Spending – EUR" with opening balance €500 and see the balance update after each transaction.

**US-05 Transactions** – I can record "Groceries, €41.20, 3 Nov 2026, Lidl" in under 60 s; it appears in the wallet history and in the phase *Study*.

**US-06 Frozen rates** – An INR expense saved today keeps its EUR value when I look at it next month.

**US-07 Remittance** – Sent ₹50,000, received €520 → effective rate 0.0104 EUR/INR (96.15 INR/EUR) is shown with the market rate and hidden cost; the home wallet shows −₹50,000 and the EUR wallet +€520.

**US-08 Monthly plan** – Rent €420 + insurance €135 + EMI ₹14,000 (≈ €131.67) gives a target of €686.67.

**US-09 Target to Earn** – For November I see earned €250, target €1,104.67, still to earn €854.67, and per-line plan vs. actual.

**US-10 Loans** – Recording a ₹14,000 EMI on ₹520,000 at 8.5 % shows interest ₹3,683.33 and principal ₹10,316.67.

**US-11 Affordability** – With an average surplus of €300/month, a 20 % buffer and a minimum part-payment of ₹10,000 (≈ €94), the app says the part-payment is affordable now.

**US-12 Runway** – €613.79 balance with €1,150 spent in the last 30 days → 16 days, status Critical, alert on dashboard.

**US-13 Reports** – Switching between month, year, phase and lifetime changes all figures consistently.

**US-14 Dashboard** – All tiles load in ≤ 2 s for the demo user.

**US-15 Data rights** – Export produces a JSON file of all my data; account deletion removes all my rows.

**US-16 Demo data** – Logging in as `demo@edufinance.app` shows realistic data from June 2025 to today on every page.

**US-17 Deployment** – `docker compose up --build` starts the system; the cloud URL is reachable.

**US-18 Theme and layout** – I can switch light/dark/auto; the layout works on a 360 px phone.
