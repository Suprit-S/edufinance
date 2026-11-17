# ADR-0005: Life phases stored on each transaction

**Status:** Accepted (change request CR-01)

## Context
Reports must work per life phase (pre-departure, settling in, study, job search, work, custom).
Phases are derived from profile dates, but users can re-date or add phases, and may want to assign
a specific transaction to a phase by hand.

## Options
1. Compute the phase on the fly from the transaction date in every report query.
2. **Store `phase_id` on each transaction**, with a flag `phase_is_manual`.

## Decision
Option 2.
* On save, the phase is determined by date; if several phases contain the date, the **shortest**
  (most specific) one wins – e.g. *Settling in* inside *Study*.
* When phases change, all transactions with `phase_is_manual = false` are re-assigned in one
  update; manual ones keep their phase.
* System phases are created at registration from the profile dates and kept in sync when those
  dates change; custom phases are fully user-controlled.
* *Work* is open-ended (`end_date = NULL`): the app is not limited to the study years.

## Consequences
Phase reports are a simple `GROUP BY phase_id` (fast, NFR-01). Re-assignment costs one UPDATE
when phase dates change, which is rare.
