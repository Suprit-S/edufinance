# Traceability Matrix

Links each requirement to the user story, the code that implements it and the test cases that
verify it. Updated at the end of every sprint. *Planned* modules are named as in the
[component diagram](../03-Architecture-documentation/diagrams/component-diagram.puml).

| Requirement | User story | Backend | Frontend | Test cases | Sprint |
|---|---|---|---|---|---|
| FR-01, FR-02 | US-01 | `api/auth`, `services/auth_service` | Register page | TC-A01–A03, TC-S07 | 1 |
| FR-03 | US-01 | `models/user.User.age_on` | Profile page | TC-S08 | skeleton |
| FR-04, FR-06 | US-02 | `api/auth`, `services/auth_service` | Login page | TC-A04, TC-SEC02 | 1 |
| FR-05 | US-01 | `api/profile` | Profile page | TC-PH04 | 1 |
| FR-07 – FR-10 | US-03 | `services/phase_service` | Profile & Phases | TC-PH01–PH04 | 1 |
| FR-11, FR-17, FR-18 | US-04 | `api/wallets`, `services/transaction_service` | Wallets | TC-W01 | 1 |
| FR-12, FR-19 | US-05 | `seed/master_data`, `api/categories` | Category picker | TC-S02, TC-S05, TC-T04 | skeleton / 1 |
| FR-13 | US-05 | `api/transactions` | Wallet detail | TC-T01 | 1 |
| FR-14 – FR-16 | US-06 | `services/fx_service`, `services/money` | Transaction form | TC-M04, TC-M05, TC-T01–T03, TC-FX01–FX04 | skeleton / 1 |
| FR-20 – FR-22 | US-07 | `services/remittance_service` | Remittances | TC-R01–R03 | 2 |
| FR-23 – FR-25 | US-08 | `services/plan_service` | Monthly Plan | TC-PL01, TC-PL02 | 2 |
| FR-26, FR-27 | US-09 | `services/plan_service` | Target to Earn | TC-S06, TC-TE01, TC-TE02 | 2 |
| FR-28 – FR-33 | US-10 | `services/loan_service` | Loan Planner | TC-L01–L05 | 2 |
| FR-34 | US-11 | `services/loan_service.affordability` | Loan Planner | TC-L06, TC-L07 | 2 |
| FR-35, FR-36 | US-12 | `services/runway_service` | Wallets, Dashboard | TC-RW01, TC-RW02 | 2 |
| FR-37 – FR-40 | US-13 | `services/report_service` | Reports | TC-RP01–RP03 | 3 |
| FR-41 | US-14 | `api/dashboard` | Dashboard | TC-P01 | 3 |
| FR-42 | US-15 | `api/account` | Profile | TC-EX01, TC-EX02 | 3 |
| FR-43 | US-16 | `seed/demo_data` | – | manual | 3 |
| NFR-01 | US-14 | – | – | TC-P01 | 3 |
| NFR-02, NFR-12 | US-18 | – | design system (`styles/`) | TC-F03, TC-U01, TC-U03 | skeleton / 3 |
| NFR-03 | US-05 | – | Transaction form | TC-U02 | 3 |
| NFR-04 – NFR-07 | US-02 | JWT config, `revoked_tokens`, ownership checks | API client | TC-SEC01–SEC04 | 1 |
| NFR-08 | US-06 | `services/fx_service` | "estimated" label | TC-FX03, TC-FX04 | 1 |
| NFR-09 | – | `services/money`, NUMERIC columns | `lib/format` | TC-M01–M07, TC-S09, TC-F01 | skeleton |
| NFR-10, NFR-13 | US-17 | `docker-compose.yml`, Dockerfiles | nginx | TC-S01, TC-D01, TC-D02 | skeleton / 3 |
| NFR-11 | – | CI workflow | CI workflow | coverage report | all |
