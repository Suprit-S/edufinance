# ADR-0001: Technology stack – React + Flask + PostgreSQL

**Status:** Accepted (Phase 1, confirmed 06 Nov 2026)

## Context
A single developer must build a browser-based, multi-currency finance application with exact
calculations, a clear UI and a one-command deployment within about 140 hours. The stack must be
well documented, free, and familiar enough to avoid learning risk.

## Options considered
| Layer | Options | Decision |
|---|---|---|
| Frontend | React, Angular, Vue, server-rendered Jinja | **React 19 + Vite** |
| Backend | Flask, Django + DRF, FastAPI, Node/Express | **Flask 3** |
| Database | PostgreSQL, MySQL, SQLite, MongoDB | **PostgreSQL 16** |
| Deployment | Docker Compose, PaaS buildpacks, bare VM install | **Docker Compose** |

## Decision and rationale
* **React** – largest ecosystem for charts (Recharts) and testing (React Testing Library);
  component model fits a dashboard-style UI. Angular brings more structure than a one-person
  project needs; Vue would work equally well but the author has more React experience.
* **Flask** – small core, explicit blueprints that map 1:1 to the modules in the building-block
  view, and Python's `decimal` module for exact money arithmetic. Django adds an admin and ORM
  conventions that are not needed; FastAPI's async model gives no benefit for this CRUD-heavy,
  database-bound workload.
* **PostgreSQL** – exact `NUMERIC` type, CHECK constraints, native enums and
  `NULLS NOT DISTINCT` unique constraints enforce business rules in the database itself. MongoDB
  lacks relational integrity for linked records (transactions ↔ wallets ↔ loans); SQLite has no
  real `NUMERIC` type and no concurrent writers.
* **Docker Compose** – the same three containers run on the developer laptop, in CI and on the
  cloud VM (NFR-10), and the assignment requires a docker-compose configuration.

## Consequences
* Two languages (Python, JavaScript) – accepted; each is the standard in its layer.
* Schema changes require Alembic migrations – this also gives a versioned schema history.
