# ADR-0008: What counts as "earned", EMIs in the target, part-payment affordability

**Status:** Accepted (change request CR-04)

## Context
The Target to Earn compares what a student must pay each month with what came in. Some incoming
money is not earned (loan disbursements, moving money between own wallets). EMIs must be paid
every month, so they must be part of the target.

## Decision
* Categories carry a flag `counts_as_earned`. Salary, family support, scholarships and refunds
  count; "Loan disbursement" does not. Transfers between own wallets are never income.
* Each active loan automatically has a Monthly Plan line with its EMI (`monthly_plan_items.loan_id`),
  valid from its `emi_start_date`; editing the loan's EMI updates the line. Hence the minimum
  target always includes EMIs.
* **Affordability of the minimum part-payment:** average monthly surplus (earned − spent) over the
  last 3 complete months, reduced by a 20 % safety buffer, is compared with the user's minimum
  part-payment (converted to base currency).
  * buffered surplus ≥ minimum → "affordable now";
  * buffered surplus > 0 → months needed = ⌈minimum ÷ buffered surplus⌉;
  * otherwise → "not affordable at the current surplus".
  Look-back months and buffer are configurable (ADR-0006).

## Consequences
The target reflects real obligations, and the affordability hint is conservative. It is an
estimate, labelled as such in the UI, not financial advice.
