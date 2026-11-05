# ADR-0004: UUID primary keys for user data

**Status:** Accepted

## Context
Sequential IDs in URLs (`/api/wallets/17`) reveal how many records exist and invite guessing other
users' IDs.

## Decision
All user-owned tables use random UUIDv4 primary keys. Master tables use their natural ISO code
(`currencies.code`, `countries.code`). Every query on user data is additionally filtered by the
authenticated user's ID; a foreign ID returns 404 (NFR-07).

## Consequences
IDs are not guessable and can be created before saving. They are longer in URLs and logs, which is
acceptable.
