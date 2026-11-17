# ADR-0007: Loan model with user-maintained outstanding balance

**Status:** Accepted (change request CR-03)

## Context
Education loans differ by bank: disbursements in tranches, simple or compound interest during the
moratorium, capitalisation rules, changing rates. Modelling every rule is out of scope and would
still differ from the bank statement.

## Decision
* The user enters and may correct the **outstanding amount** at any time; it is the source of
  truth (as on the bank statement).
* Disbursements that pay costs are recorded as normal transactions (income "Loan disbursement",
  which does not count as earned, plus the expense).
* Payment split for an EMI: interest = outstanding × annual rate ÷ 12 (rounded to cents);
  principal = amount − interest. A part-payment is 100 % principal.
* Months to payoff and future interest are simulated month by month at the current EMI.
* **Interest saved** by a part-payment = future interest without it − future interest with it,
  both at the normal EMI; **EMIs saved** = difference in months.
* Split and savings are **frozen** on the payment row. Only the latest payment can be undone, which
  restores `balance_before` – this keeps the history consistent.
* An optional `emi_start_date` (e.g. after the moratorium) controls from when the EMI is part of
  the Monthly Plan.

## Consequences
Simple, always matches the bank after a correction. The app does not predict moratorium interest
(documented as technical debt TD-04).
