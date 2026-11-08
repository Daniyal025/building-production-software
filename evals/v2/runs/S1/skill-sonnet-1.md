# Plan: LLM-proposed price changes, admin-confirmed, with history

Principle: the model only proposes; server code decides and writes. There is exactly one function that changes a price, and both the admin UI and the chat confirmation go through it.

## Database (one additive migration)
- `product_price` table: `id`, `product_id` FK, `price NUMERIC(12,2) NOT NULL CHECK (price >= 0)`, `currency`, `revision_no`, `is_current bool`, `valid_from timestamptz`, `changed_by` (admin id), `origin` (CHECK: `ui` / `agent_confirmed`), `proposing_model` (nullable), `reason`.
- Partial unique index `(product_id) WHERE is_current` so two current prices are impossible. Unique `(product_id, revision_no)`.
- Money is NUMERIC end to end, never float. In JSON it travels as a string.
- History is append-only: a price change inserts a new row and flips the old `is_current` to false. Nothing is updated in place or deleted. The app role gets INSERT/SELECT plus an UPDATE limited to `is_current`.
- Backfill: one row per existing product from its current price, `revision_no=1`, `origin='migration'`. Keep `products.price` only as a read-through until callers move, then drop it in a later migration.
- `pending_price_change` table: `id` (uuid), `product_id`, `base_revision_no`, `old_price`, `new_price`, `proposing_model`, `conversation_id`, `proposed_at`, `expires_at`, `status` (CHECK: pending / confirmed / rejected / expired), `confirmed_by`.
- Migration is guarded and safe to run twice. Test it from an empty database with seed, from a copy of production data, and on a second run. Update the seed in the same PR.
- The write endpoint needs the new schema, so deploy the migration first, then the code. Readiness should check the schema version.

## API route and the single write path
- `change_price(product_id, new_price, base_revision_no, actor, origin, model)` is the one write function. In one transaction it locks the product row, re-checks that the current revision equals `base_revision_no`, inserts the new row, flips the old one and writes the audit info.
- A stale base revision returns 409 with a message saying what the current price is.
- `PUT /products/{id}/price` takes `{price: "12.50", base_revision_no}`, requires admin, and calls `change_price` with `origin='ui'`. Use a Pydantic model that rejects NaN/Infinity and more than 2 decimals, and bounds the value (an upper limit the business owner agrees on, recorded next to the code).
- `POST /price-proposals/{id}/confirm` and `/reject`. Confirm loads the pending row, checks it is pending and unexpired, re-checks that the caller is an admin, then calls `change_price` with `origin='agent_confirmed'` and the proposing model. Make the transition `pending -> confirmed` with a conditional UPDATE so two simultaneous confirms yield one write.
- `GET /products/{id}/price-history` returns the rows newest first.
- One error shape `{code, message}`, with 4xx for expected failures. Log each change with product, actor, old and new price.

## Agent tool
- `propose_price_change(product_id, new_price)` never writes. It validates arguments on the server (type, positive, 2 decimals, within the allowed range, product exists). It refuses ambiguous input and says what to send instead, for example "send the price in whole currency units as a string like '12.50'".
- It stores a `pending_price_change` row with the current revision, a 15-minute expiry and the proposing model, and returns old -> new plus the percentage change so the admin can see a 100x mistake.
- Confirmation is a button in the chat carrying the pending id. The model has no confirm argument and no tool that confirms. Text such as "yes" or "I confirm" inside a tool result or a model message does nothing.
- Only the admin's own session can confirm. Check permission again at confirm time, not only at proposal time.
- The agent may state a price only if it came from a tool result in the same turn.

## Tests (write each one first and watch it fail)
- Migration: backfill gives one current row per product; a second current row is rejected by the index; runs twice cleanly; runs as the runtime role.
- `change_price`: history grows by one row, the old row is no longer current, and the old price is still readable. Stale `base_revision_no` gives 409 and no write. Negative price, NaN, 3 decimals and an absurd value are all refused.
- Race: two real connections confirm the same proposal at once and exactly one write happens. This test must fail if the row lock is removed.
- Confirm refusals: non-admin, expired, already confirmed, rejected, and wrong proposal id.
- Agent tool: it never writes (the price is unchanged after a proposal); a model-supplied "confirm=true" argument is ignored; "yes" inside tool output is refused; a prompt-injection string in a product name does not confirm anything; a scripted refuse -> retry conversation works, including 2.1 versus 21.0 style unit mistakes.
- Audit: a confirmed change records the admin, `origin='agent_confirmed'` and the model name; a UI change records `origin='ui'`.
- Tests use an injected clock for expiry and own their data.

## Later (not now)
- Retention policy for expired proposals, per-user proposal budgets, an eval set built from real chat transcripts, and bulk price changes.
