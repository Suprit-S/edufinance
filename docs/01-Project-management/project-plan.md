# Project Plan – EduFinance

| | |
|---|---|
| Course | DLMCSPSE01 – Project: Software Engineering (Task 1: web application) |
| Author | Suprit Somashekaraiah (4250964) |
| Tutor | Holger Klus |
| Methodology | Scrum (adapted for a one-person team) |
| Status | Phase 2 – Development / reflection |

## 1. Project profile (short)

**Problem.** International students manage money in two currencies at once: a *home currency* for
education loans and family support, and a *base (abroad) currency* for daily life. Their costs start
months before departure (language tests, applications, visa, proof of funds, flights) and their
loan repayments continue for years after graduation. General finance apps assume one currency and
ignore these life phases.

**Objective.** Deliver a web application that lets a student record every cost and income from the
first day of planning until loans are repaid, in any currency, and that answers three questions at
any time: *How long will my money last? How much must I earn this month? When will my loan be
paid off?*

**Target group.** International students before, during and after their studies abroad, who earn
or borrow in one currency and spend in another, often with limited part-time work allowed by their
visa.

**Scope (in).** Browser-based SPA, multi-currency wallets, life phases, transactions with frozen
exchange rates, remittances with user-entered rates, monthly plan and minimum target, target to
earn, loan planner with part-payment affordability, runway/burn rate, reports per month / year /
phase / lifetime, dashboard, Docker deployment on a cloud VM.

**Scope (out).** Native mobile apps, bank-account integration, multi-user/family sharing, push
notifications, investment tracking (see [technical debt](../technical-debt.md)).

## 2. Methodology: Scrum for a one-person team

Scrum was chosen because the requirements of a student finance tool become clearer by using it
(e.g. how loans are really repaid), and short sprints deliver a working, tested increment every
week. The three Scrum roles are held by one person but are kept separate in thinking and in the
documentation:

| Role | Responsibility in this project |
|---|---|
| Product Owner | Owns and prioritises the product backlog, writes user stories and acceptance criteria, accepts increments in the sprint review |
| Scrum Master | Guards the time-box, the Definition of Done and the process; runs the retrospective |
| Development Team | Designs, implements, tests and documents the increment |

**Events (adapted).**

| Event | Time-box | Output |
|---|---|---|
| Sprint planning | 1 h at sprint start | Sprint goal + selected backlog items |
| Daily check | 10 min | Short note of done / next / blockers (in sprint notes) |
| Sprint review | 30 min at sprint end | Demo of the running increment, accepted stories |
| Retrospective | 20 min at sprint end | 1–3 improvements for the next sprint |

**Artefacts.** Product backlog (§4), sprint backlog (§6), increment (tagged Git release),
[sprint notes](sprint-notes.md), burndown (§7).

**Definition of Done (DoD).** A backlog item is *done* when:

1. the code is implemented according to the acceptance criteria;
2. business logic is in the service layer and covered by automated tests;
3. all tests pass and the linters report no errors (CI green);
4. API errors use the standard JSON error format;
5. the UI works from 360 px to 1920 px width;
6. affected documentation (requirements, architecture, test cases, ADRs) is updated;
7. the change is committed with a conventional commit message and recorded in `CHANGELOG.md`.

## 3. Milestones

| Milestone | Date | Content |
|---|---|---|
| M1 – Concept approved | 27 Jul 2026 | Phase 1 submitted (24 Jul) and accepted by the tutor |
| M2 – Release v0.1.0 | 12 Nov 2026 | Skeleton + Sprint 1: accounts, phases, wallets, transactions, FX |
| M3 – Release v0.2.0 | 19 Nov 2026 | Sprint 2: remittances, monthly plan, target, loans, runway |
| M4 – Release v0.3.0 | 26 Nov 2026 | Sprint 3: reports, dashboard, demo data, deployment |
| M5 – Phase 2 submission | 28 Nov 2026 | Composite PDF + written explanation |
| M6 – Phase 3 submission | after tutor feedback | Final product, abstract, ZIP folder, v1.0.0 |

## 4. Product backlog (user stories)

Priority uses MoSCoW (M = must, S = should, C = could). Story points (SP) use the Fibonacci scale.

| ID | User story | Prio | SP | Sprint |
|---|---|---|---|---|
| US-01 | As a student, I want to register with my currencies, destination and study dates, so that the app fits my situation. | M | 5 | 1 |
| US-02 | As a student, I want to log in and out securely, so that only I can see my finances. | M | 3 | 1 |
| US-03 | As a student, I want my life phases (before departure, settling in, study, job search, work) to be created automatically and be editable, so that every cost is assigned to the right period. | M | 5 | 1 |
| US-04 | As a student, I want several wallets in different currencies, so that I can mirror my real accounts. | M | 3 | 1 |
| US-05 | As a student, I want to log income and expenses with category, date and note, so that I know where my money goes. | M | 5 | 1 |
| US-06 | As a student, I want each foreign-currency transaction converted with a rate that never changes afterwards, so that past reports stay correct. | M | 5 | 1 |
| US-07 | As a student, I want to record a transfer with the amount sent and the amount received, so that the real rate and the hidden cost are known. | M | 5 | 2 |
| US-08 | As a student, I want a monthly plan of fixed costs (including loan EMIs), so that I know my minimum monthly earning target. | M | 5 | 2 |
| US-09 | As a student, I want to see per month what I earned, spent and still need, so that I can plan my part-time work. | M | 5 | 2 |
| US-10 | As a student, I want to record loans, EMIs and part-payments, so that I see interest paid, interest saved and months to payoff. | M | 8 | 2 |
| US-11 | As a student, I want to know whether I can afford my minimum part-payment, so that I can repay my loan faster without running out of money. | S | 3 | 2 |
| US-12 | As a student, I want each wallet's runway in days with a status and an alert, so that I never run out of money unexpectedly. | M | 3 | 2 |
| US-13 | As a student, I want reports per month, year, life phase and lifetime, including "cost of going abroad" and "cost of my degree". | M | 8 | 3 |
| US-14 | As a student, I want a dashboard with balances, target progress, alerts, loans and my current phase. | M | 5 | 3 |
| US-15 | As a student, I want to export all my data and delete my account, so that I stay in control of my data (GDPR). | S | 3 | 3 |
| US-16 | As an examiner, I want realistic demo data, so that every feature can be tried immediately. | M | 3 | 3 |
| US-17 | As an examiner, I want to start the system with one command and reach it in the cloud. | M | 3 | 3 |
| US-18 | As a student, I want light and dark mode and a layout that works on my phone. | S | 3 | 1–3 |

Acceptance criteria for every story are listed in [requirements.md](../02-Requirements/requirements.md#user-stories-and-acceptance-criteria).

## 5. Work packages and estimates

| WP | Work package | Estimate (h) | Sprint |
|---|---|---|---|
| WP1 | Revise Phase 1 documents (tutor feedback: plan, NFRs, UML, stack rationale, test cases, glossary) | 12 | 1 |
| WP2 | Repository, Docker, CI, database schema, master data, design system (skeleton) | 10 | 1 |
| WP3 | Registration, login/logout, profile, life phases (US-01–03) | 14 | 1 |
| WP4 | Wallets, categories, transactions, FX service with cache and fallback (US-04–06) | 16 | 1 |
| WP5 | Remittances (US-07) | 8 | 2 |
| WP6 | Monthly plan, minimum target, target to earn (US-08–09) | 12 | 2 |
| WP7 | Loan planner, payments, interest saved, affordability (US-10–11) | 16 | 2 |
| WP8 | Runway / burn rate and alerts (US-12) | 5 | 2 |
| WP9 | Reports and dashboard (US-13–14) | 16 | 3 |
| WP10 | Data export/delete, demo data, accessibility and performance checks (US-15–16, US-18) | 10 | 3 |
| WP11 | Cloud deployment and installation guide (US-17) | 8 | 3 |
| WP12 | Phase 2 composite PDF and written explanation | 10 | 3 |
| | **Total** | **137** | |

## 6. Sprint plan

Sprints are one week long (time-box). Capacity is about 45 hours per sprint.

| Sprint | Dates | Sprint goal | Work packages | Planned h |
|---|---|---|---|---|
| Sprint 0 | 1–24 Jul 2026 | Concept, requirements and architecture approved | Phase 1 | done |
| Sprint 1 | 6–12 Nov 2026 | A student can register, sees her life phases, and logs income and expenses in any currency with frozen rates. | WP1–WP4 | 52 |
| Sprint 2 | 13–19 Nov 2026 | Money flows work end-to-end: transfers, monthly target, loans with part-payments and wallet runway. | WP5–WP8 | 41 |
| Sprint 3 | 20–26 Nov 2026 | Insight and release: reports, dashboard, demo data, cloud deployment and Phase 2 documents. | WP9–WP12 | 44 |
| Sprint 4–5 | after feedback | Polish, technical debt, final abstract (Phase 3) | – | – |

Sprint 1 is above capacity because WP1 (document revision) runs in parallel; if needed, the
"custom category" part of WP4 moves to Sprint 2.

## 7. Progress tracking (burndown)

Remaining story points are recorded at the end of each sprint and plotted in the Phase 2 PDF.

| Point in time | Remaining SP (of 80) |
|---|---|
| Start Sprint 1 (6 Nov) | 80 |
| End Sprint 1 (12 Nov) | *to be filled* |
| End Sprint 2 (19 Nov) | *to be filled* |
| End Sprint 3 (26 Nov) | *to be filled* |

## 8. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Scope creep beyond one person's time | High | High | Fixed backlog per sprint; new ideas go to the backlog or technical debt ([change requests](change-requests.md)) |
| Exchange-rate API unavailable or changes | Medium | Medium | 24 h cache, 7-day stale cache, seeded fallback table, rates flagged as "estimated" |
| Rounding errors in money calculations | Medium | High | Decimal arithmetic only, NUMERIC columns, unit tests with concrete values |
| Not enough time for manual testing | Medium | Medium | Automated tests in CI on every push |
| Cloud credit or host limits | Low | High | Small VM, budget alert, Docker Compose allows moving to another host in minutes |
| Data privacy (financial data) | Medium | High | Hashed passwords, JWT on every endpoint, per-user data isolation tests, data export/delete |

## 9. Version and release control

* Git repository on GitHub (public), branch `main`; conventional commits (`feat:`, `fix:`, `docs:`, `test:`).
* Every sprint ends with a tagged release (`v0.1.0`, `v0.2.0`, `v0.3.0`; final `v1.0.0`) and a
  `CHANGELOG.md` entry.
* Architecture documentation lives in the same repository (`/docs`) and is versioned with the code.
* CI (GitHub Actions) runs lint and tests on every push.
