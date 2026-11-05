# Sprint Notes

Short record of each sprint: goal, what was delivered, problems, and the retrospective.
These notes are the evidence that the Scrum process was followed.

## Sprint 0 – Conception (1–24 Jul 2026)

**Goal:** Concept, requirements and architecture approved.
**Delivered:** Project profile, requirements, glossary, context diagram, building-block view
(Phase 1 submission, 24 Jul 2026).
**Review (tutor feedback, 27 Jul 2026):** Project, target group, risks and agile approach accepted.
Improvements requested: agile project plan with work packages and estimates, measurable NFRs
without solution details, UML component diagram, rationale for the technology stack, concrete test
cases, alphabetical glossary. → addressed in WP1 (see [phase-1-feedback.md](phase-1-feedback.md)).
**Retrospective:**
- *Keep:* clear problem statement and target group.
- *Improve:* separate requirements (what) from design (how); make every NFR testable.

## Sprint 1 – Foundation (6–12 Nov 2026)

**Goal:** A student can register, sees her life phases, and logs income and expenses in any
currency with frozen rates.

### Day 1 – Skeleton (6 Nov)
- Repository structure, Docker Compose (frontend, backend, db), GitHub Actions CI.
- Complete database schema as Alembic migration `0001_initial` (data model approved before coding).
- Master data seed: 37 currencies, 46 countries, 52 categories, fallback exchange rates.
- Design system (light/dark, responsive shell), navigation and placeholder pages.
- Tests: 16 backend (money arithmetic, health, master data, DB constraints), 11 frontend.

### Review
*to be filled at sprint end*

### Retrospective
*to be filled at sprint end*

## Sprint 2 – Money flows (13–19 Nov 2026)
*to be filled*

## Sprint 3 – Insight and release (20–26 Nov 2026)
*to be filled*
