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
| ~~TD-10~~ | ~~Wallet balances are shown in their own currency only; no total in base currency yet~~ | **Resolved in Sprint 3:** dashboard shows the total balance in the base currency at today's rates | – | – |
| TD-11 | A remittance cannot be edited, only deleted and recorded again | Keeps linked transactions consistent | One extra step for corrections | Edit = delete + recreate in one transaction |
| TD-12 | Loan payments only from a wallet in the loan currency | Avoids a second, hidden exchange rate | Cross-currency EMI needs a remittance first | Payment with an embedded remittance |
| TD-13 | Hidden cost uses the market rate of the cache/fallback; back-dated transfers compare against an estimated rate | Free provider has no history | Hidden cost of old transfers is approximate | Historical-rate provider |
| TD-14 | Plan lines sharing one category show the same "actual" | No link from a transaction to a plan line | Slightly misleading actuals when two lines share a category | Optional plan-line link on transactions |
| TD-15 | A loan's history before its first recorded payment uses the outstanding amount at that payment (or the current amount if there is none) | Only payments are stored, no balance history (ADR-0007) | Interest added during a moratorium is not visible in the net-worth line | Store a balance snapshot whenever the user corrects the outstanding amount |
| TD-16 | The demo's exchange-rate history is generated (smooth trend with small daily changes), not real market data | The free provider has no historical rates | Demo values are realistic but not exact | Import a public historical rate file for the demo period |
| TD-17 | Net worth is valued at today's rates for all months (ADR-0012) | Shows behaviour, not currency swings; no historic rates needed | Past net-worth values differ from what the user saw at that time | Optional "at historic rates" toggle once a historical-rate source exists |
| TD-18 | Chart library (Recharts) adds about 115 KB (gzip) on the Target and Reports pages; Lighthouse performance 57–67 there, other pages 85–91 (local preview server without compression; nginx compresses in production) | Lazy-loaded already; the server answers in < 25 ms (TC-P01) | First visit of a chart page is slower on mobile networks | Lighter chart library or server-rendered SVG for the simple line charts |
| TD-19 | No automatic database backup on the cloud VM | Free tier; single VM | Data loss if the VM disk is lost | Nightly `pg_dump` via cron to Azure Blob Storage |
| TD-20 | Usability test with three first-time users (TC-U02) not yet run | Needs other people | NFR-03 not yet verified | Run with fellow students before Phase 3 |
