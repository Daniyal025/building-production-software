# Plan: assistant proposes a price change, admin confirms in chat

This change touches money and lets an AI change data, so every safety rule below applies.

## Database
- Add `price_changes` as an append-only history: `id`, `product_id` (FK), `revision_no`, `price NUMERIC(12,2)`, `currency`, `is_current`, `valid_from`, `superseded_at`, `actor`, `origin`, `created_at`.
- Add a partial unique index on `(product_id) WHERE is_current`, and a unique `(product_id, revision_no)`.
- CHECK `price >= 0` and CHECK `origin` against a fixed list (`admin_direct`, `agent_confirmed`).
- Add `pending_price_changes`: public id (UUID), `product_id`, `base_revision_no`, `proposed_price`, `old_price`, `currency`, `proposing_model`, `proposed_by`, `status` (CHECK list: pending, confirmed, cancelled, expired, superseded), `created_at`, `expires_at`.
- Keep `products.price` as the current value, written only by the same supersede function in the same transaction.
- Make the migration additive and idempotent: guard it, backfill revision 1 from each existing `products.price` with `WHERE NOT EXISTS`, and never edit a migration already applied.
- Grant the app role INSERT and SELECT on `price_changes`, no DELETE, and UPDATE only on `is_current` and `superseded_at`. The owner and migrator stay separate roles.
- Deploy the migration before the code that reads it. The readiness check verifies the schema version.
- Nightly sweep marks expired pending rows; price history is kept, not swept.

## Guarded write path
- One function `set_product_price(product_id, new_price, currency, expected_revision, actor, origin, model)` is the only writer. It locks the product row, re-checks `expected_revision` (409 if moved), validates, supersedes the old row, inserts revision + 1, and updates `products.price`.
- Both the admin's direct route and the agent's confirm route call this function. No second write path.
- Money is parsed with `Decimal` from the request string, rejected if NaN, Infinity, negative, over two decimals, or outside bounds the domain owner sets.

## API routes
- `GET /products/{id}/price-history`: revisions, prices as strings.
- `PUT /products/{id}/price`: admin only, takes `If-Match` revision, returns 409 on mismatch. Uses the guarded function.
- `POST /price-proposals/{pending_id}/confirm`: admin only, takes an `Idempotency-Key`. Flips status with `UPDATE ... WHERE status = 'pending' RETURNING`, so a second confirm finds nothing. Refuses if expired (410) or stale base revision (409). Re-checks the admin's permission at execution time.
- Errors use one envelope `{code, message}`. Default-deny auth on the router, only `/health` public.

## Agent tool
- `propose_price_change(product, new_price, currency)` validates arguments on the server and stores a pending row with the proposing model id and expiry. It never writes to `products`.
- The tool has no `confirm` argument. Confirmation is only the admin's button press carrying the `pending_id`.
- Refusals say what to send instead, for example "send 12.50, not 12.5%".
- The tool result is data only (`{data, citations}`): old price, new price, pending id, expiry. The reply may quote figures only from this turn's tool result.
- Cap pending proposals per user and count tokens on every turn, including errors.

## Tests (each seen failing first)
- Migration runs from an empty DB with seed, from a restored copy, and twice with zero changes. Run as the runtime role, not the owner.
- Partial unique index rejects a second current row. The app role cannot DELETE history or change `price`.
- Two real connections confirm the same pending row: one write, one 409. Removing the lock makes this test fail.
- Stale base revision is refused. Expired and already-confirmed pending rows are refused. Expiry uses an injected clock.
- Route walk: 401 without a token, 403 for a non-admin on the confirm and price routes.
- Agent: a model-chosen "confirm" argument is refused; "yes" inside tool output is refused; a product name containing an instruction to confirm does not trigger a write.
- Invalid prices (negative, NaN, three decimals, out of bounds) are refused with guidance; a scripted refuse-then-retry conversation ends with a valid proposal.
- Invariant: `products.price` equals the current revision after every path. Direct admin edit and agent confirm produce identical rows, with origin and model recorded.
- Run CI's exact commands and compare against the known-failure baseline. Update the project's current-state doc in the same commit.
