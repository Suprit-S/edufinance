# Traceability Matrix

Links each requirement to the user story, the code that implements it and the test cases that
verify it. Updated at the end of every sprint. Module names follow the
[component diagram](../03-Architecture-documentation/diagrams/component-diagram.puml).

| Requirement | User story | Backend | Frontend | Test cases | Sprint |
|---|---|---|---|---|---|
| FR-01, FR-02 | US-01 | `api/auth.py`, `api/schemas.py`, `services/auth_service.py` | `RegisterPage` | TC-A01–A03c, TC-S07, TC-E2E01 | 1 ✅ |
| FR-03 | US-01 | `models/user.User.age_on` | `ProfilePage` | TC-S08, TC-A07 | ✅ |
| FR-04, FR-06 | US-02 | `api/auth.py`, `services/auth_service.py` | `LoginPage`, `ProfilePage` (password) | TC-A04–A06, TC-SEC02, TC-F08, TC-F09 | 1 ✅ |
| FR-05 | US-01 | `api/profile.py`, `auth_service.update_profile` | `ProfilePage` | TC-PH04 | 1 ✅ |
| FR-07 – FR-10 | US-03 | `services/phase_service.py`, `api/profile.py` | `ProfilePage` | TC-PH01–PH08 | 1 ✅ |
| FR-11, FR-17 | US-04 | `api/wallets.py`, `services/wallet_service.py` | `WalletsPage`, `WalletDetailPage`, `WalletForm` | TC-W01–W03 | 1 ✅ |
| FR-18 | US-07 | `services/remittance_service.py` | `RemittancesPage` | TC-R05 | 2 ✅ |
| FR-12, FR-19 | US-05 | `seed/master_data.py`, `services/category_service.py`, `api/schemas.py` | `TransactionForm` | TC-S02, TC-S05, TC-C01, TC-A03, TC-T04 | 1 ✅ |
| FR-13 | US-05 | `api/transactions.py`, `services/transaction_service.py` | `TransactionsPage`, `TransactionForm`, `TransactionList` | TC-T04, TC-T08, TC-F06 | 1 ✅ |
| FR-14 – FR-16 | US-06 | `services/fx_service.py`, `services/transaction_service.py`, `services/money.py` | `TransactionForm` (rate pre-fill) | TC-M04, TC-M05, TC-T01–T03, TC-T05–T07, TC-FX01–FX06, TC-F07 | 1 ✅ |
| FR-20 – FR-22 | US-07 | `services/remittance_service.py`, `api/remittances.py` | `RemittancesPage`, `RemittanceForm` | TC-R01–R07, TC-F13 | 2 ✅ |
| FR-23 – FR-25 | US-08 | `services/plan_service.py`, `api/plan.py` | `PlanPage` | TC-PL01–PL05 | 2 ✅ |
| FR-26, FR-27 | US-09 | `plan_service.target_to_earn`, `month_totals` | `TargetPage`, `TargetHistoryChart` | TC-S06, TC-TE01–TE04, TC-R03 | 2 ✅ |
| FR-28 – FR-33 | US-10 | `services/loan_service.py`, `api/loans.py` | `LoansPage`, `LoanDetailPage`, `LoanForm` | TC-L01–L05, TC-L08, TC-L09 | 2 ✅ |
| FR-34 | US-11 | `loan_service.affordability`, `affordability_verdict` | `AffordabilityCard` | TC-L06, TC-L07, TC-L10, TC-F11 | 2 ✅ |
| FR-35, FR-36 | US-12 | `services/runway_service.py`, `api/wallets.py` | `RunwayBadge`, Wallets, Dashboard alert | TC-RW01–RW04, TC-F12 | 2 ✅ |
| FR-37, FR-38 | US-13 | `services/report_service.py` (`resolve_period`, `period_report`, `fold_top`), `api/reports.py` | `ReportsPage`, `BarList`, `EarnedSpentChart` | TC-RP02, TC-RP04, TC-RP06, TC-RP07, TC-F14, TC-E2E03 | 3 ✅ |
| FR-39 | US-13 | `report_service.cost_reports` | `ReportsPage` (whole journey) | TC-RP01, TC-DEMO01 | 3 ✅ |
| FR-40 | US-13 | `report_service.net_worth_timeline`, `outstanding_on`, `loan_timeline` | `ReportsPage`, `MonthLineChart` | TC-RP03, TC-RP05, TC-RP08, TC-RP09 | 3 ✅ |
| FR-41 | US-14 | `report_service.dashboard`, `api/reports.py` (`/dashboard`) | `DashboardPage`, `BarList` | TC-DB01, TC-F14, TC-E2E03 | 3 ✅ |
| FR-42 | US-15 | `services/account_service.py`, `api/reports.py` (`/account`) | `DataPrivacy` (Profile) | TC-EX01, TC-EX02, TC-F16, TC-E2E03 | 3 ✅ |
| FR-43 | US-16 | `seed/demo_data.py`, `flask seed-demo`, `entrypoint.sh` | `LoginPage` (demo hint) | TC-DEMO01, TC-F15 | 3 ✅ |
| NFR-01 | US-14 | aggregate SQL in `report_service`, `scripts/perf_dashboard.py` | lazy-loaded chart pages | TC-P01 | 3 ✅ |
| NFR-02, NFR-12 | US-18 | – | design system (`styles/`), `--on-accent` token, text values in `BarList`, chart tables | TC-F03, TC-F12, TC-F14, TC-U01, TC-U03 | 3 ✅ |
| NFR-03 | US-05 | – | Transaction form | TC-U02 | ⏳ (user test) |
| NFR-04 – NFR-07 | US-02 | `auth_service`, JWT callbacks in `app/__init__.py`, `require_auth`, `get_*` ownership checks | `api/client.js` (401 → logout) | TC-SEC01–SEC04 | 1 ✅ |
| NFR-08 | US-06 | `services/fx_service.py` | "est." tag, rate hint | TC-FX03, TC-FX04, TC-E2E01 | 1 ✅ |
| NFR-09 | – | `services/money`, NUMERIC columns | `lib/format` | TC-M01–M07, TC-S09, TC-F01 | skeleton |
| NFR-10, NFR-13 | US-17 | `docker-compose.yml`, `docker-compose.prod.yml`, `deploy/Caddyfile`, Dockerfiles, [deployment guide](../deployment.md) | nginx | TC-S01, TC-D01, TC-D02 | 3 (D01/D02 after deployment) |
| NFR-11 | – | CI workflow | CI workflow | coverage report | all |
