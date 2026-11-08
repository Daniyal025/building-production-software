# Plan: agent-proposed price changes with confirmation and history

## Database
- Add `product_prices` as an append-only history: `id`, `product_id` (FK, NOT NULL), `revision_no`, `price NUMERIC(12,2)` (NOT NULL, CHECK price > 0), `is_current`, `valid_from`, `superseded_at`, `actor`, `origin` (CHECK in `admin_ui`, `agent_confirmed`), `model_name` (nullable), `created_at`.
- Partial unique index on `(product_id) WHERE is_current`, and unique `(product_id, revision_no)`.
- Add `price_proposals`: `id` (uuid, public), `product_id` (FK), `base_revision_no`, `new_price NUMERIC(12,2)`, `proposed_by_model`, `proposed_by_user`, `status` (CHECK in pending, confirmed, expired, cancelled), `expires_at`, `resolved_at`, `resolved_by`. Partial index on `status = 'pending'`.
- Put both in one new numbered migration, never an edit to an applied file. Use a guard so it is safe to re-run.
- Backfill each product's current price as revision 1 in the same migration, guarded so a second run changes nothing.
- Deploy the migration before the code, and have readiness check the schema version.
- Grant the app role only what it needs (SELECT and INSERT on the history, guarded UPDATE for the supersede step). The app never connects as the owner or a superuser.

## Write path
- One function `set_price(product_id, new_price, base_revision_no, actor, origin, model_name)` is the only writer. It takes the product row lock, re-checks the base revision (409 if it moved), marks the old row not current, and inserts revision + 1 in one transaction.
- Both the admin route and the chat confirm call this same function. No second write path.

## API
- `GET /products/{id}/prices`: history with revision, actor, origin and valid_from. Prices go out as strings.
- `POST /price-proposals/{id}/confirm` (admin only): checks the proposal is pending and unexpired, then calls `set_price`. Returns 403 for non-admins, 410 for expired, 409 for a stale base revision.
- Require an `Idempotency-Key` header on confirm so a double-click writes once.
- Typed request model: price arrives as a decimal string, parsed to Decimal. Reject NaN, Infinity, negatives, and more than two decimals, with an error envelope `{code, message}`.
- Add the new routes under the existing default-deny auth. Skipped: a cancel endpoint; expiry covers it, add when the admin asks for one.

## Agent tool
- `propose_price_change(product_id, new_price)` validates arguments on the server (product exists, decimal string, positive, two decimals) and stores a pending proposal with base revision, model name and expiry (15 minutes). It never writes a price.
- Refusals say what to send instead, for example "send new_price as a string like '19.99', not cents".
- The tool result is data only: `{data, citations, tables}` with the old and new price. Put the usage rules in the tool description, not the global system prompt.
- The tool has no `confirm` argument. Confirmation comes only from the admin's button, which carries the proposal id.
- Every figure in the agent's reply must come from a tool result in the same turn.
- Max change size is a business rule: ask the owner for the bound, do not invent one.

## Tests (write each one red first and say so in the PR)
- Migration: empty DB to seed gives revision 1 for every product; a second run changes nothing; run as the runtime role.
- Race: two real connections confirm the same proposal, and exactly one write happens. Removing the lock must make this fail.
- Race: two concurrent `set_price` calls on one product, one wins and the other gets 409.
- Stale base revision gives 409 and no new row.
- Expired proposal gives 410 and no write.
- Route walk: every new route gives 401 without a token and 403 for the wrong role.
- Decimal handling: `19.999`, `NaN`, `Infinity`, `-5`, a float `19.99` and `1e3` are refused; `19.90` round-trips as the string `"19.90"`.
- Scripted chat: the model sends `1999` meaning 19.99, the tool refuses with the fix, the retry succeeds.
- Adversarial: a "yes" inside tool output does not confirm; a model-chosen confirm argument is refused; a non-admin confirm is refused.
- Figures in the reply trace to this turn's tool result.
- Clock is injected so expiry tests do not depend on today's date.
- Run the full suite and compare it to the known-failure baseline before the PR.
