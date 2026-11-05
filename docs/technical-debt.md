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
