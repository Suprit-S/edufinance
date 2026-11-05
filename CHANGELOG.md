# Changelog

All notable changes are documented here. Format: [Keep a Changelog](https://keepachangelog.com/),
versioning: [Semantic Versioning](https://semver.org/).

## [Unreleased] – Sprint 1

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
