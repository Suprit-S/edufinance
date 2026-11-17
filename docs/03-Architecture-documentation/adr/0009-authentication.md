# ADR-0009: Authentication with short-lived JWT and revocation list

**Status:** Accepted

## Context
The API is used by a single-page app. Sessions must end after at most 60 minutes and on logout
(NFR-05); passwords must never be readable (NFR-04).

## Options
1. Server-side sessions with cookies.
2. **JWT access token (60 min) sent as `Authorization: Bearer`, plus a revocation table.**
3. External identity provider (Auth0, Keycloak) – too heavy for the scope.

## Decision
Option 2 with Flask-JWT-Extended. Passwords are hashed with bcrypt (salted, adaptive cost).
On logout the token's `jti` is stored in `revoked_tokens` and rejected afterwards. The token is
kept in `sessionStorage` (cleared when the tab closes). No refresh token: after 60 minutes the
user logs in again.

## Consequences
Stateless verification and simple CORS. A stolen token is valid at most 60 minutes; XSS is
mitigated by React's escaping and no `dangerouslySetInnerHTML`. Refresh tokens are technical debt
TD-05.
