# ADR-0010: Hosting on a cloud VM with Docker Compose

**Status:** Accepted

## Context
The assignment requires a cloud-hosted, directly accessible front end and a docker-compose
configuration. Grading may take up to six weeks after submission, so the app must not sleep or
lose its database in that time. Budget: free.

## Options
| Option | Pros | Cons |
|---|---|---|
| **Azure for Students – Linux VM + Docker Compose** | Free credit without credit card for students; always on; identical to local setup | VM administration (updates, firewall) |
| Render (web service) + Neon (Postgres) | No server administration | Free web services sleep after 15 min idle (cold start); two providers; compose file not used in production |
| Render free Postgres | Simple | Free database expires after 30 days – unacceptable for grading |
| AWS / GCP free tiers | Mature | Require a credit card; free tier limits are complex |

## Decision
Azure for Students, one small Ubuntu VM (B-series) running the same `docker-compose.yml`, with a
reverse proxy (Caddy) for automatic HTTPS. A budget alert protects the credit. Render + Neon is the
documented fallback.

## Consequences
Production equals development, and the examiner can reproduce it with one command. The author
maintains the VM (security updates) – documented in the deployment guide (Sprint 3).

## Addendum (Sprint 3): implementation
- `docker-compose.prod.yml` adds a **Caddy** service as the only public entry point (ports 80/443)
  and removes the published frontend port. `deploy/Caddyfile` sets security headers
  (HSTS, `nosniff`, `DENY` framing, referrer and permissions policy).
- Secrets have **no defaults** in production (`${VAR:?}`); the stack does not start with
  development secrets.
- VM size: **B2ats v2** (2 vCPU, 1 GiB, inside the Azure for Students free hours) plus a 2 GB swap
  file for the frontend build. The Azure DNS label (`*.cloudapp.azure.com`) avoids buying a domain;
  Caddy obtains the Let's Encrypt certificate for it.
- Step-by-step guide, operations and troubleshooting: [deployment.md](../../deployment.md).
