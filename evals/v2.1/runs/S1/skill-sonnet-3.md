# Plan: LLM-proposed price changes, admin-confirmed, with history

Core rule: the agent tool never writes. It stores a pending proposal; only an admin's confirmation, checked by server code, calls the same guarded write function the normal admin UI/API uses.

## Database (one forward-only migration)

- `product_prices`: `id`, `product_id` FK, `price NUMERIC(12,2) NOT NULL CHECK (price >= 0)`, `currency` (CHECK list), `revision_no`, `is_current bool`, `valid_from`, `superseded_at`, `actor_id`, `origin` (CHECK: `admin_ui | agent_confirmed | migration`), `proposed_by_model` (nullable), `reason`.
- Partial unique index `ON product_prices(product_id) WHERE is_current` so two current prices are impossible. Unique `(product_id, revision_no)`.
- Backfill: one row per product from the existing `products.price`, `revision_no = 1`, `origin = 'migration'`. Migration is guarded and idempotent, so a second run changes nothing.
- Keep `products.price` for now as a read copy updated in the same transaction, and drop it in a later migration. Check for readers or hardcoded copies of it before dropping.
- `price_proposals`: `id` (public UUID), `product_id`, `base_revision_no`, `old_price`, `new_price` NUMERIC, `proposing_model`, `conversation_id`, `requested_by`, `status` (CHECK: `pending | confirmed | rejected | expired`), `expires_at`, `created_at`, `decided_by`, `decided_at`.
- Runtime role gets INSERT/SELECT on `product_prices` (no UPDATE/DELETE except through the supersede function). The app does not connect as owner.
- Ship the schema before the code, and make the readiness check verify the migration version.
- Never edit applied migrations. Fix forward.

## One guarded write path

- A single `set_price(product_id, new_price, expected_revision_no, actor, origin, model=None)` function does the writing. The existing admin price endpoint is refactored to call it, so there is no second write path.
- Inside one transaction it locks the product row (`SELECT ... FOR UPDATE`) and compares `expected_revision_no` with the current revision. If they differ it raises a 409. Otherwise it flips the old row to `is_current = false` with `superseded_at`, inserts revision + 1, and updates the read copy.
- A no-op price (same as current) is rejected. It does not create a revision.

## API routes

- `POST /products/{id}/price-proposals` is internal, used by the agent tool. It validates the price, then creates a pending proposal with a 15-minute expiry.
- `POST /price-proposals/{proposal_id}/confirm` and `/reject` are admin-only. Confirm checks the role again at execution time, checks status is `pending` and not expired, then calls `set_price` with the proposal's `base_revision_no`. It marks the proposal `confirmed` in the same transaction.
- Confirm takes only the proposal id (from a button in chat). Nothing the model wrote can confirm. A typed "yes" is not accepted unless it comes from the human's own message and matches an allowlist.
- Concurrent double-confirm: the proposal row is locked and the status flips only once, so there is one write and the second caller gets 409.
- `GET /products/{id}/price-history` returns revisions with prices as strings in JSON, never floats.
- Responses: 404 unknown product, 403 non-admin, 409 stale or already decided, 410 expired, 422 bad price.

## Agent tool

- `propose_price_change(product_id, new_price)` has a Pydantic schema as the only source of truth. It validates on the server: Decimal parsed from a string, > 0, max 2 decimals, and a sanity band (for example, reject more than ±50% from current and say what to send instead).
- The tool returns `{data: {proposal_id, old_price, new_price, pct_change, expires_at}}`. The chat UI renders old → new with Confirm and Reject buttons carrying the proposal id. The tool has no `confirm` argument.
- It records the proposing model name on the proposal, and that name is copied into the price row on confirm.
- The tool description says "proposes only; does not change prices", so the model does not tell the user the price has changed. The reply must come from the confirm result, not the model's guess.

## Tests (each seen failing first)

- Migration: empty DB → seed, a production-like copy with the backfill, and a second run changing nothing. Run as the runtime role, not the owner.
- `set_price`: creates revision 2 and flips the old row; the partial unique index blocks two current rows; a stale `expected_revision_no` gives 409; a no-op is refused.
- Concurrency: two real connections confirming the same proposal give exactly one new revision. The test fails if the lock is removed.
- Agent safety: a model-chosen "confirm" argument is refused; "yes" appearing inside tool output or a product description is refused; a non-admin is refused; an expired proposal is refused; a proposal made against revision N is refused after someone changes the price to N+1.
- Tool validation: 0.021-vs-2.1 style errors, negative, 3 decimals, string "NaN", and a huge jump all refused with a message that tells the model what to send. Script the refuse → retry conversation.
- Money stays exact: 19.99 round-trips as the string "19.99" through the DB and JSON.
- History: after three changes, the history endpoint returns three revisions in order with actor, origin and model, and "price as of date X" is correct. The clock is injected.

## Later (not now)

- Per-user rate limit on proposals, a nightly sweep of old expired proposals, and bulk price changes.
