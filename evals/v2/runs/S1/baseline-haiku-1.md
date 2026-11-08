# Plan: LLM-proposed price changes with history

## Database
- Add `product_prices` as an append-only history table: `id`, `product_id` (FK, not null), `price numeric(12,2)` with `CHECK (price >= 0)`, `effective_from timestamptz not null default now()`, `changed_by`, `source` ('admin' or 'agent-confirmed'), `proposal_id` (nullable FK), `created_at`.
- Index `(product_id, effective_from desc)`; unique `(product_id, effective_from)`.
- Keep `products.price` as the current price for cheap reads, updated in the same transaction as each history insert.
- Add `price_change_proposals`: `id`, `product_id` (FK), `proposed_price`, `price_at_proposal`, `status` (CHECK in 'pending', 'confirmed', 'rejected', 'expired'), `proposed_by`, `reason`, `created_at`, `expires_at`, `decided_at`, `decided_by`.
- Partial unique index so a product has at most one pending proposal at a time.
- Migration is one numbered SQL file in the existing migration folder, no ORM. Backfill one history row per existing product from its current price.
- Enforce append-only at the DB level: revoke UPDATE/DELETE on `product_prices` from the app role (or a trigger that raises).

## API
- `POST /products/{id}/price-proposals`: creates a pending proposal, validates price > 0 and product exists, records `price_at_proposal`. Does not touch the price.
- `POST /price-proposals/{id}/confirm` (admin only): in one transaction, lock the product row (`SELECT ... FOR UPDATE`), check status is pending and not expired, check the current price still equals `price_at_proposal` (else 409, re-propose), insert the history row, update `products.price`, mark the proposal confirmed.
- `POST /price-proposals/{id}/reject` (admin only): sets status rejected, no price change.
- `GET /products/{id}/prices`: history newest first, paginated.
- Errors: 404 unknown id, 409 wrong status or stale price, 403 for non-admin confirm or reject, 422 bad input.

## Agent tool
- `propose_price_change(product_id, new_price, reason)`: validates args against a JSON schema, calls the same service function as the POST route, returns the proposal id and a one-line summary ("Proposed 12.00 to 14.50 for product 7. Reply CONFIRM to apply").
- The tool has no way to change a price. Only the admin's chat confirmation calls the confirm service, and only for the proposal id shown to the admin in that conversation.
- Tool errors go back to the model as text (unknown product, bad price), with no row written.

## Tests
- Migration: backfill gives one history row per product; CHECK rejects negative price; second pending proposal for the same product is rejected.
- Confirm happy path: one history row, `products.price` updated, proposal confirmed, all in one transaction.
- Confirm failure mid-way (fake a DB error on the update) leaves no history row and no price change.
- Confirm on a rejected, expired, or already-confirmed proposal returns 409 and adds no row.
- Stale proposal (price changed since proposal) returns 409.
- Concurrency: two confirms at once produce exactly one history row.
- Auth: non-admin confirm and reject return 403; agent credentials cannot reach confirm.
- Agent tool: unknown product returns an error and writes nothing; valid call writes a pending proposal and leaves `products.price` unchanged.
- Chat flow with a stubbed LLM: a proposal alone changes no price; an admin CONFIRM changes it once; any other reply changes nothing.
- `GET /products/{id}/prices` returns newest first and pages correctly.

Skipped: a separate audit log table (the history table already records who and when), add when a non-price field needs history too. Skipped: automatic expiry job, expiry is checked at confirm time, add a sweeper when the pending list gets long.
