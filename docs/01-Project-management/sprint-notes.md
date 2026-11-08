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

### Step 1 – Skeleton
- Repository structure, Docker Compose (frontend, backend, db), GitHub Actions CI.
- Complete database schema as Alembic migration `0001_initial` (data model approved before coding).
- Master data seed: 37 currencies, 46 countries, 52 categories, fallback exchange rates.
- Design system (light/dark, responsive shell), navigation and placeholder pages.
- Tests: 16 backend (money arithmetic, health, master data, DB constraints), 11 frontend.

### Step 2 – Increment
- **Accounts:** registration with profile and journey dates, login, logout (token revocation),
  password change, profile edit. Age computed, never stored.
- **Life phases:** four system phases created from the profile; custom phases (e.g. *Job search*);
  automatic assignment by date (shortest overlapping phase wins); re-assignment when dates change;
  manual assignment kept.
- **Wallets & categories:** wallets in any currency with balances; archive instead of delete when
  history exists; custom categories.
- **Transactions:** income/expense with frozen base and home values; market rate pre-filled and
  overridable; edit keeps the frozen rate; filters, search, pagination.
- **Exchange rates:** USD-based daily cache, provider call once per day, 7-day stale cache and
  fallback table, both flagged "estimated".
- **Frontend:** login, registration, wallets, wallet detail, transactions with filters, profile &
  phases, Sprint-1 dashboard; phone layout with card-style transaction list.
- **Tests:** 57 backend (service coverage 95 %), 19 frontend, plus a scripted browser run
  (TC-E2E01).

### Review
Sprint goal **met**: a student can register, sees her life phases and logs income and expenses in
any currency with frozen rates. Accepted stories: US-01, US-02, US-03, US-04, US-05, US-06
(26 story points). US-18 (theme, phone layout) partly done – continues in every sprint.
Not done: FR-18 (moving money between own wallets) – moved to Sprint 2, because it is a special
case of a remittance (same data, sent = received).

**Demo observations**
- The exchange-rate provider was unreachable from the test environment; the app fell back to the
  stored table and marked values as "est." – exactly the designed behaviour (NFR-08).
- Back-dated foreign-currency entries always get an *estimated* rate because the free provider only
  offers today's rates. Accepted; the user can type the real rate (TD-09).

### Retrospective
- *Went well:* writing the service tests first with concrete numbers found two design questions
  early (overlapping phases, rate source when only one of two rates is entered by the user).
- *Went badly:* two redirects after registration raced each other (welcome message lost); found
  only by the browser run, not by unit tests.
- *Improve in Sprint 2:* keep one scripted browser run per sprint; decide rules (e.g. which rate a
  transfer uses) in an ADR *before* coding.

## Sprint 2 – Money flows
*to be filled*

## Sprint 3 – Insight and release
*to be filled*
