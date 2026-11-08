# Plan: agent-proposed price changes with admin confirmation and price history

## Database (one migration)
- Add `product_price_history` (id, product_id FK, price NUMERIC(12,2) CHECK > 0, currency, valid_from timestamptz, valid_to timestamptz NULL, changed_by, source `'admin'|'agent'`, change_id FK NULL).
- Add a partial unique index on `(product_id) WHERE valid_to IS NULL` so a product can have only one current price row.
- Add `price_change_proposals` (id, product_id, old_price, new_price, status `pending|confirmed|rejected|expired`, proposed_by, conversation_id, created_at, decided_by, decided_at, expires_at).
- Backfill: insert one open history row per product from `products.price`, with `valid_from = now()` and source `'backfill'`.
- Keep `products.price` as the denormalised current value so existing readers don't change. Only the new code path writes it, in the same transaction as the history row.
- The migration is forward-only and idempotent, and uses the project's existing migration numbering.

## API
- `POST /products/{id}/price-proposals` is called by the agent tool. It validates the price (positive, within a sane delta of the old price), stores a `pending` proposal and returns the proposal id. It writes no live data.
- `POST /price-proposals/{id}/confirm` is admin-only, via the existing auth dependency. In one transaction it:
  - locks the proposal and product rows (`SELECT ... FOR UPDATE`);
  - checks the status is `pending`, it hasn't expired, and the current price still equals `old_price` (otherwise 409, stale);
  - closes the open history row (`valid_to = now()`), inserts the new row, updates `products.price`, and marks the proposal `confirmed`.
- `POST /price-proposals/{id}/reject` is admin-only and sets the status to `rejected`.
- `GET /products/{id}/price-history` returns the rows ordered by `valid_from`.
- Confirm is idempotent: repeating it on an already confirmed proposal returns 200 with the same result, not a second write.
- The agent's credentials can only call the propose endpoint. They never reach confirm, so the server enforces the rule that only an admin changes live data.

## Agent tool
- Add the `propose_price_change(product_id, new_price, reason)` tool. It calls only the propose endpoint.
- The tool returns a summary (product, old price, new price, proposal id) and tells the model to ask the admin to confirm.
- The chat layer shows the admin a Confirm / Reject action. A confirmation reply from the admin calls the confirm endpoint, never the model.
- The model cannot confirm its own proposal. The confirm step does not go through a tool call.
- Update the system prompt so the model states clearly that the change is pending until confirmed.

## Tests (write first)
- Migration: backfill gives exactly one open row per product, and the partial unique index rejects a second open row.
- Propose: a valid request creates a `pending` proposal and leaves `products.price` and the history untouched. Invalid prices (zero, negative, non-numeric) return 422.
- Confirm happy path: the old row is closed, the new row is open, `products.price` is updated, and the proposal is `confirmed`.
- Confirm authorisation: a non-admin gets 403 and the agent credential gets 403.
- Confirm stale: if the price changed after the proposal, the result is 409 and nothing is written.
- Confirm race: two concurrent confirms produce exactly one new history row.
- Confirm on an expired or rejected proposal returns 409.
- Reject: the status changes and no price changes.
- History: the endpoint returns rows in order with no gaps or overlaps between `valid_to` and the next `valid_from`.
- Agent tool: a unit test with a mocked API checks the tool calls only propose, plus one test that the tool registry does not expose confirm.
- Run the full suite and compare it with the previous run before finishing.

## Later (not now)
- Auto-expire sweeper for old proposals.
- Notifications to the admin outside the chat.
