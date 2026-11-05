# Change Requests

Scope changes after the Phase 1 approval are recorded here. Each change was assessed against the
project goals and time budget before it entered the product backlog (Scrum: the Product Owner
re-orders the backlog; the approved product vision stays the same).

| ID | Date | Change | Reason | Impact | Decision |
|---|---|---|---|---|---|
| CR-01 | 05 Nov 2026 | Extend the app from "during studies" to the whole journey: life phases *pre-departure, settling in, study, job search, work*. Registration asks for planning start, arrival and study dates. | Costs start months before departure and loan repayment continues after graduation; a study-only view hides the real total cost of studying abroad. | New entity `life_phases`; reports per phase; +8 h | Accepted (US-03, US-13) |
| CR-02 | 05 Nov 2026 | Remittances use the amounts the user actually sent and received instead of a live rate. | The real rate includes the provider's margin and fees; only the user knows it. | New entity `remittances`; live rate still used for non-exchange conversions; +8 h | Accepted (US-07, ADR-0003) |
| CR-03 | 06 Nov 2026 | Loans are simplified: the user maintains the outstanding amount; no automatic moratorium or disbursement modelling. Loan disbursements paying costs are logged as normal transactions. | Bank rules differ widely; a user-maintained balance is always correct and simpler to use. | Fewer entities; one category flag `counts_as_earned`; −4 h | Accepted (ADR-0007) |
| CR-04 | 06 Nov 2026 | Add a part-payment affordability estimate with a user-defined minimum part-payment. | Students want to repay faster but must not run out of money. | New field `min_part_payment`; one service function; +3 h | Accepted (US-11) |
| CR-05 | 05 Nov 2026 | Multi-user accounts remain out of scope; native mobile app remains out of scope. | Time budget. | None | Kept out of scope (technical debt) |
