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
