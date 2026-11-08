# Plan: assistant proposes a price change, admin confirms in chat

Risk level: high. The assistant can change money, so every write goes through a human confirmation checked by server code.

## Database
- Add `product_price_revisions`: `id`, `product_id` (FK), `revision_no`, `price NUMERIC(12,2)` with `CHECK (price >= 0)`, `currency` (CHECK list), `is_current`, `valid_from` (timestamptz, UTC), `superseded_at`, `actor_id`, `origin` (`admin_ui` | `agent_confirmed`), `proposal_id` (nullable FK), `proposing_model` (nullable).
- Unique (`product_id`, `revision_no`) and a partial unique index on `product_id` WHERE `is_current`, so there is exactly one current price per product.
- Add `price_change_proposals`: `id` (public uuid), `product_id`, `base_revision_no`, `new_price NUMERIC(12,2)`, `currency`, `proposing_model`, `status` (`pending` | `confirmed` | `expired` | `superseded`), `created_at`, `expires_at`, `confirmed_at`, `confirmed_by`.
- Migration is additive and guarded: create tables, then backfill revision 1 from each product's current price in the same file, then add constraints `NOT VALID` and `VALIDATE` in a second step.
- Do not keep a second price column on products that could drift. Read the current price through the partial index. Only add a cache later if a query measures slow.
- Grant the runtime role INSERT/SELECT on history; the supersede function is the only writer. The app never connects as the table owner.
- Test the migration from an empty database with seed, from a restored production copy, and on a second run, all as the runtime role.
- Deploy the migration before the code that reads it; readiness checks the schema version.

## Write path (one guarded function)
- One function `set_product_price(...)` is the only writer. It locks the product row, re-checks that `base_revision_no` is still current (409 if it moved), sets the old row `is_current = false` with `superseded_at`, inserts revision + 1 with actor, origin and `valid_from`, and marks the proposal `confirmed`. All in one transaction.
- The admin UI and the agent both call this function. No second write path.
- Confirming an already-confirmed proposal is a no-op with the same result, so a double click cannot write twice.

## API route
- `GET /products/{id}/price-history`: the full revision chain, prices as strings.
- `GET /price-proposals/{id}`: shows old and new price, status and expiry.
- `POST /price-proposals/{id}/confirm`: admin only, requires `Idempotency-Key`, rechecks permission and expiry at execution time, calls `set_product_price`, returns 200 with the new revision or 409/410 with an error envelope `{code, message}`.
- Typed request models; unknown parameters are 422 in dev and test. Prices travel as strings.
- Add a test that walks every route: 401 without a token, 403 for a non-admin.

## Agent tool
- `propose_price_change(product, new_price, currency)` validates on the server (decimal parse, reject NaN, Infinity, negative, more than 2 decimals, unknown currency, unknown product). A refusal says what to send instead; a missing product is an error, never a price of 0.
- It reads the current revision, stores a pending proposal with base revision, proposing model and a short expiry, and returns old to new. It never writes.
- The model gets no `confirm` argument. Confirmation only comes from the admin's button press carrying the proposal id, checked by the server.
- If the chat fallback is an allowlisted phrase, match it anchored with no partial matches. "yes" or "I confirm nothing" must not pass.
- Keep the tool description (not the global system prompt) carrying the rules for when to propose.

## Tests (write each one red first)
- Adversarial confirmation: model-chosen confirm refused; "yes" inside tool output refused; "I confirm nothing" refused.
- Non-admin confirm refused; expired proposal refused; stale base revision gives 409.
- Two real connections confirm the same proposal at once: exactly one new revision. Confirm the test fails if the lock is removed.
- Clock injected for expiry; no test depends on today's date.
- Invalid inputs (NaN, negative, too many decimals, wrong currency) are refused with a message, and no proposal is stored.
- Scripted refuse-and-retry conversation through the agent tool.
- Eval set from real chat transcripts, re-run on every prompt or model change, with a pass threshold.
- Traces leave out price and chat content by default.

## Rollout
- Put the agent tool behind a feature flag with a named owner and a removal date, and a kill switch that turns off proposals.
- Record the proposing model and prompt version on each proposal so a bad change can be traced and rolled back.
