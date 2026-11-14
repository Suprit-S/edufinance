# Changelog

All notable changes are documented here. Format: [Keep a Changelog](https://keepachangelog.com/),
versioning: [Semantic Versioning](https://semver.org/).

## [0.3.0] – Sprint 3: insight and release

### Added
- Reports for a month, year, life phase or the whole journey: earned, spent, net, top categories,
  spending per phase, earnings by source, month-by-month chart (`/api/reports`).
- Cost of going abroad and cost of the degree (`/api/reports/costs`), net-worth timeline
  (`/api/reports/net-worth`), loan payoff timeline (`/api/reports/loans`).
- Full dashboard: total balance in base currency, target progress, loans, current phase, wallets,
  alerts, 30-day spending (`/api/dashboard`).
- Data export as JSON (`GET /api/account/export`) and account deletion with password
  (`DELETE /api/account`).
- Demo account `demo@edufinance.app` / `Demo#2026` (`flask seed-demo [--reset]`, loaded by Docker
  when `SEED_DEMO=true`) and a "Fill in demo login" button.
- Production setup: `docker-compose.prod.yml`, `deploy/Caddyfile` (HTTPS, security headers),
  [deployment guide](docs/deployment.md).
- Performance script `backend/scripts/perf_dashboard.py` (TC-P01).
- ADR-0012; ADR-0010 addendum; glossary terms *Demo account*, *Net worth*, *Payoff month*, *Period*.

### Changed
- Exchange-rate cache: one row per currency, date **and source** (migration 0002), so a live rate on
  the fallback date no longer overwrites the fallback table (TC-FX07).
- Accessibility: readable button text in the dark theme (`--on-accent`), darker warning colour,
  correct heading order on wallet and loan cards, theme switch on the login page reachable for
  screen readers.

### Removed
- "Coming soon" placeholder page and component (all pages now exist).

## [0.2.0] – Sprint 2: money flows

### Added
- Remittances between own wallets, from outside and to outside, with effective rate, market rate,
  hidden cost and fees (`/api/remittances`). Same-currency transfers between own wallets (FR-18).
- Monthly Plan with automatic, locked EMI lines and the minimum monthly target (`/api/plan`).
- Target to Earn with earnings by source, plan vs. actual and a six-month chart (`/api/target`).
- Loan Planner: loans, EMI and part-payments, payoff forecast and schedule, interest saved, undo of
  the latest payment, part-payment affordability check (`/api/loans`).
- Runway and burn rate per wallet (`runway` in `/api/wallets`), low-funds alert on the dashboard.
- Pages: Remittances, Monthly Plan, Target to Earn, Loans, Loan detail; charts with table view;
  chart pages are loaded on demand.
- ADR-0011; sequence diagrams for "record remittance" and "record part-payment".

### Changed
- Every API error rolls back the database session (no half-saved changes).
- Wide tables scroll inside their card on phones.

## [0.1.0] – Sprint 1: foundation

### Added
- Registration, login, logout with token revocation, password change, profile edit (`/api/auth/*`, `/api/me`).
- Life phases: system phases from profile dates, custom phases, automatic and manual assignment,
  re-assignment when dates change (`/api/phases`).
- Wallets with balances, archive, delete-if-empty (`/api/wallets`).
- System and custom categories (`/api/categories`).
- Transactions with frozen base/home values and rate source; filters, search, pagination
  (`/api/transactions`).
- Exchange-rate service: USD-based daily cache, provider, 7-day stale cache, fallback table;
  `/api/fx/rate` for forms.
- Frontend: login, registration, wallets, wallet detail, transactions, profile & phases, dashboard
  (phase and wallets); modal dialogs; phone layout.
- 41 new backend tests, 8 new frontend tests; test-case catalogue updated.

### Changed
- Development JWT secret lengthened to ≥ 32 bytes (HMAC recommendation).

## [0.0.1] – Skeleton

### Added
- Project skeleton: Docker Compose (frontend, backend, db), GitHub Actions CI.
- Complete database schema (Alembic migration `0001_initial`): users, life phases, wallets,
  transactions, remittances, monthly plan, loans, loan payments, master data, FX cache.
- Master-data seed: 37 currencies, 46 countries, 52 categories, fallback exchange rates.
- Exact money helpers (`services/money.py`).
- Public endpoints: `GET /api/health`, `/api/currencies`, `/api/countries`; JSON error format.
- React app shell with design system, light/dark mode, responsive navigation, placeholder pages.
- Documentation: project plan, requirements, glossary, test cases, traceability, architecture
  (arc42), UML diagrams, 10 ADRs, technical debt.
