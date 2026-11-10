# Technical Debt

Known limitations and things deliberately not done, with the reason and a possible fix.
Updated every sprint.

| ID | Item | Reason | Impact | Possible fix |
|---|---|---|---|---|
| TD-01 | No native mobile app; responsive web only | Out of scope (time) | Works in mobile browsers | PWA manifest or React Native |
| TD-02 | Offline fallback rates are a static table (Jan 2026) | No free historical API without key | Estimated values may deviate when provider and cache are down > 7 days | Refresh table on each successful API call |
| TD-03 | Changing the base currency does not convert historical `amount_base` values | Rate freezing keeps history stable | Reports mix old and new base currency after a change | Store values per currency or re-freeze on change with user confirmation |
| TD-04 | Moratorium interest is not predicted; the user updates the outstanding amount | Bank rules differ (ADR-0007) | Outstanding may be outdated until corrected | Optional simple-interest projection |
| TD-05 | No refresh token; re-login after 60 minutes | Simplicity (ADR-0009) | Minor inconvenience | Refresh token in httpOnly cookie |
| TD-06 | No bank-account import or CSV import | Out of scope | Manual entry | CSV import of bank statements |
| TD-07 | Single user per account (no family sharing) | Out of scope (CR-05) | – | Shared wallets with roles |
| TD-08 | No rate limiting on login | Not in Sprint 1 scope | Password guessing is only slowed by bcrypt | Flask-Limiter on `/api/auth/login` |
| TD-09 | Back-dated foreign-currency entries get an estimated rate | Free provider has no historical rates | Values marked "est." until the user enters the real rate | Historical-rate provider or bulk "update estimated rates" action |
| TD-10 | Wallet balances are shown in their own currency only; no total in base currency yet | Planned for the Sprint 3 dashboard | – | Dashboard total with current rates |
| TD-11 | A remittance cannot be edited, only deleted and recorded again | Keeps linked transactions consistent | One extra step for corrections | Edit = delete + recreate in one transaction |
| TD-12 | Loan payments only from a wallet in the loan currency | Avoids a second, hidden exchange rate | Cross-currency EMI needs a remittance first | Payment with an embedded remittance |
| TD-13 | Hidden cost uses the market rate of the cache/fallback; back-dated transfers compare against an estimated rate | Free provider has no history | Hidden cost of old transfers is approximate | Historical-rate provider |
| TD-14 | Plan lines sharing one category show the same "actual" | No link from a transaction to a plan line | Slightly misleading actuals when two lines share a category | Optional plan-line link on transactions |

