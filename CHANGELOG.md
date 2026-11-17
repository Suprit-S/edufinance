# Changelog

All notable changes are documented here. Format: [Keep a Changelog](https://keepachangelog.com/),
versioning: [Semantic Versioning](https://semver.org/).

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
