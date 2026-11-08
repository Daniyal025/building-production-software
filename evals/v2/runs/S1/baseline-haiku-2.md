# Plan: LLM-proposed price changes with admin confirmation and price history

## Database
- Add `price_history` as an append-only table: `id`, `product_id` (FK), `price` (numeric, CHECK > 0), `effective_from` (timestamptz), `changed_by` (user id, nullable for system), `source` (`admin`, `agent`, `import`), `reason` (text), `created_at`.
- Add `price_proposals`: `id`, `product_id` (FK), `proposed_price` (CHECK > 0), `reason`, `proposed_by` (agent/session id), `status` (`pending`, `confirmed`, `rejected`, `expired`), `created_at`, `decided_at`, `decided_by`.
- Partial unique index on `price_proposals(product_id) WHERE status = 'pending'` so only one open proposal per product.
- Keep `products.price` as the current price, updated in the same transaction as the history insert.
- Backfill: insert one `price_history` row per existing product from its current price, `effective_from` = migration time.
- Add a DB-level guard that rejects UPDATE and DELETE on `price_history` (trigger), so history cannot be rewritten.
- Migration is plain SQL in the existing migration folder, next free number, and runs in one transaction.

## API
- `POST /products/{id}/price-proposals`: creates a pending proposal. Validates price and product exists. Does not touch `products`.
- `GET /price-proposals?status=pending`: lists open proposals for the admin chat view.
- `POST /price-proposals/{id}/confirm`: admin only. In one transaction: lock the proposal (`SELECT ... FOR UPDATE`), require `status = 'pending'`, set `products.price`, insert `price_history`, set status `confirmed` and `decided_by`.
- `POST /price-proposals/{id}/reject`: admin only, sets status `rejected`.
- `GET /products/{id}/price-history`: returns history ordered by `effective_from` desc.
- Confirm is idempotent-safe: a second confirm on a non-pending proposal returns 409, not a second price change.

## Agent tool
- `propose_price_change(product_id, new_price, reason)`: calls the proposal endpoint only. Returns the proposal id and a one-line summary (old price, new price, product name) for the chat.
- The tool has no write path to `products`. The agent cannot confirm its own proposal.
- Confirmation flow: the admin replies with an explicit CONFIRM in chat, and only then does the agent call the confirm endpoint with that proposal id. Any other reply leaves it pending.
- Stale proposals: a scheduled or on-read expiry sets `expired` after a set age, so old proposals cannot be confirmed against a changed price.

## Tests
- Migration test: tables, constraints, backfill count equals product count, UPDATE/DELETE on `price_history` raises.
- Proposal create: valid price creates pending row, `products.price` unchanged.
- Invalid input: zero or negative price and unknown product are rejected.
- Confirm: sets product price and writes one history row with the admin as `changed_by`.
- Confirm twice: second call returns 409 and writes no extra history row.
- Reject: status `rejected`, price and history unchanged.
- Non-admin confirm or reject returns 403 and changes nothing.
- Concurrency: two parallel confirms on one proposal apply the price once.
- Agent tool: calling it with a valid product creates a proposal and never changes `products.price` (assert on the row).
- Chat flow: a reply without CONFIRM does not call the confirm endpoint.
- Expiry: an expired proposal cannot be confirmed.
- Price history endpoint returns rows in descending order with the source recorded.
