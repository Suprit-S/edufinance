# Sprint Notes

Short record of each sprint: goal, what was delivered, problems, and the retrospective.
These notes are the evidence that the Scrum process was followed.

## Sprint 0 – Conception (Phase 1)

**Goal:** Concept, requirements and architecture approved.
**Delivered:** Project profile, requirements, glossary, context diagram, building-block view
(Phase 1 submission).
**Review (tutor feedback):** Project, target group, risks and agile approach accepted.
Improvements requested: agile project plan with work packages and estimates, measurable NFRs
without solution details, UML component diagram, rationale for the technology stack, concrete test
cases, alphabetical glossary. → addressed in WP1 (see [phase-1-feedback.md](phase-1-feedback.md)).
**Retrospective:**
- *Keep:* clear problem statement and target group.
- *Improve:* separate requirements (what) from design (how); make every NFR testable.

## Sprint 1 – Foundation

**Goal:** A student can register, sees her life phases, and logs income and expenses in any
currency with frozen rates.

### Skeleton
- Repository structure, Docker Compose (frontend, backend, db), GitHub Actions CI.
- Complete database schema as Alembic migration `0001_initial` (data model approved before coding).
- Master data seed: 37 currencies, 46 countries, 52 categories, fallback exchange rates.
- Design system (light/dark, responsive shell), navigation and placeholder pages.
- Tests: 16 backend (money arithmetic, health, master data, DB constraints), 11 frontend.

### Review
*to be filled at sprint end*

### Retrospective
*to be filled at sprint end*

## Sprint 2 – Money flows
*to be filled*

## Sprint 3 – Insight and release
*to be filled*
