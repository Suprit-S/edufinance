# ADR-0011: How a remittance becomes transactions

**Status:** Accepted (Sprint 2)

## Context
A remittance moves money across currencies. Reports must not count moving money between the
student's own wallets as income or spending, but money from family *is* income and money sent home
*is* an expense. The real exchange rate (with the provider's margin) is only known from the
amounts sent and received. Wallet balances must stay correct in both wallets.

## Options
1. One "transfer" record without transactions; balances add transfers separately.
2. **A remittance record plus linked transactions** in the wallets involved.
3. Two independent transactions entered by the user.

## Decision
Option 2. The remittance stores sent/received amounts and currencies, the effective rate
(received ÷ sent), the market rate of that day and the hidden cost. It creates:

| Direction | Transactions |
|---|---|
| own → own (incl. same currency, FR-18) | TRANSFER_OUT in the sender wallet, TRANSFER_IN in the receiver wallet |
| outside → own (e.g. parents) | INCOME, default category *Family support* |
| own → outside (e.g. sent home) | EXPENSE, default category *Gifts & family* |
| fee (optional, sent currency) | extra EXPENSE *Transfer fees* in the sender wallet |

* **Frozen rates:** on each side, if the other currency is the user's base or home currency, the
  effective rate (or its inverse) is frozen as a USER rate. Example: ₹50,000 → €520 gives the INR
  side `rate_to_base` 0.0104 and the EUR side `rate_to_home` 96.15384615 – both sides therefore
  show exactly ₹50,000 = €520.
* **Hidden cost** (base currency) = (sent × market rate − received) converted to base, plus the
  fee converted to base. A negative value means the user got a better rate than the market rate;
  the UI shows it as "better".
* Linked transactions are read-only in the transaction API (409); deleting the remittance deletes
  them. Editing a remittance means delete and record again (TD-11).
* TRANSFER_* transactions have no category and are excluded from earned, spent and burn rate.

## Consequences
Wallet balances, reports and runway use one uniform transaction table. The remittance keeps the
user-entered truth for the hidden-cost analysis.
