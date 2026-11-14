# Phase 2 – Written explanation (draft)

*About half a page. Copy into the Phase 2 composite PDF and adapt the wording as needed.*

---

In Phase 2, I turned the concept from Phase 1 into a working web application, **EduFinance**. It is
a finance planner for international students that follows the whole journey: from the first
application fee, through settling in and studying abroad, to the job and the last loan EMI. Every
entry stores its value in the home and the base currency, so students see what their degree really
costs in both currencies.

**Tutor feedback.** I addressed all seven points of the Phase 1 feedback before coding started:
- an agile project plan with a product backlog, story points, work packages with hour estimates
  and one-week sprints;
- measurable non-functional requirements;
- requirements separated from solutions (the solutions are recorded in architecture decision
  records);
- a UML component diagram;
- a technology comparison;
- a test-case catalogue with concrete inputs and expected results;
- an alphabetical glossary.

The [feedback table](phase-1-feedback.md) shows where each point is resolved.

**Approach.** I worked in three Scrum sprints. Each sprint ended with a tested, tagged release:
- **v0.1.0:** accounts, life phases, wallets, transactions with frozen exchange rates;
- **v0.2.0:** remittances with hidden costs, monthly plan and earning target including loan EMIs,
  loan planner with part-payment affordability, runway alerts;
- **v0.3.0:** reports per month, year, life phase and lifetime; dashboard; data export and
  account deletion; demo account; cloud deployment.

Each sprint has a review and a retrospective in the [sprint notes](sprint-notes.md). Scope
changes are recorded as [change requests](change-requests.md). For example, the user enters
the loan outstanding amount instead of the system modelling disbursements, and EMIs became part
of the earning target.

**Quality.** The results are measured, not assumed:
- 102 backend tests (96 % service-layer coverage) and 32 frontend tests run in CI on every push;
- the dashboard answers in 20 ms (95th percentile) for a user with 2,000 transactions (target: 2 s);
- automated accessibility audits report no WCAG 2.1 AA violations, with a Lighthouse accessibility
  score of 100 on every page;
- every page works from 360 px to 1920 px without horizontal scrolling.

Building realistic demo data uncovered a real defect in the exchange-rate cache. I fixed it with a
database migration and a regression test.

**Open points for Phase 3** are listed openly in the [technical debt](../technical-debt.md) list:
- the usability test with three first-time users;
- the uptime check of the cloud deployment;
- optional historical exchange rates.

The application starts with one command (`docker compose up --build`) and runs in the cloud as
described in the [deployment guide](../deployment.md). The demo login is
`demo@edufinance.app` / `Demo#2026`.
