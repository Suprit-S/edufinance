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

## Addendum (Sprint 2)
* **Wallet currency:** a payment can only be booked from a wallet in the loan currency. Paying an
  INR loan from a EUR account is recorded as a remittance to the INR wallet first – this keeps the
  real exchange rate in one place.
* **Payment order:** payments must be recorded in date order, because each payment's split is
  calculated from the balance left by the previous one.
* **Small payments:** a payment smaller than the month's interest is all interest; the balance does
  not change.
* **Final payment:** an EMI may be at most balance + this month's interest; the error message names
  that amount.
* **Wallet expenses of payments** are managed by the loan (read-only in the transaction API). If
  the loan is deleted, these expenses stay as normal transactions – the money was really paid.
* **Closing:** when the balance reaches 0 the loan is CLOSED and its EMI plan line ends in the
  month of the last payment; correcting the outstanding amount above 0 re-opens it.
