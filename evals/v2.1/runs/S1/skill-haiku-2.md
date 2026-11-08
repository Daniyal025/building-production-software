# Plan: assistant-proposed price changes with admin confirmation and price history

## Database
- Add `product_price_revisions`: `product_id` (FK), `revision_no`, `price` NUMERIC(14,4) with a CHECK that it is greater than 0, `currency`, `is_current` boolean, `valid_from`, `superseded_at`, `actor_id`, `origin` (`admin_ui` or `agent_confirmed`), `proposed_by_model` (nullable), `created_at`.
- Partial unique index on `(product_id) WHERE is_current`, plus a unique `(product_id, revision_no)`.
- Backfill one revision 1 row per existing product from its current price, in the same migration, idempotently (`WHERE NOT EXISTS`).
- Add `price_change_proposals`: `id` (public UUID), `product_id`, `base_revision_no`, `new_price`, `proposed_by_model`, `proposed_by_user`, `status` (pending, confirmed, expired, superseded), `expires_at`, `created_at`, `confirmed_at`. CHECK on status values.
- Index `(status, expires_at)` for the expiry sweep; check it with EXPLAIN on realistic row counts.
- Migration is new-file only, guarded, and additive. Test it from empty→seed, from a production-like copy, and on a second run, as the runtime role.
- Keep the current price on `products` as a read convenience, updated only inside the same supersede transaction, or drop it and read from the current revision row.

## One guarded write path
- Write one `set_product_price(product_id, new_price, base_revision_no, actor, origin, model)` function. It validates, checks authorisation, takes a row lock on the product, re-checks `base_revision_no` (409 on mismatch), supersedes the current revision, inserts revision + 1, and writes the audit row, all in one transaction.
- Both the admin UI route and the agent confirm path call this function. No second write path.

## API route
- `POST /products/{id}/price` takes `new_price` as a string (Decimal), `If-Match` carrying the base revision, and an `Idempotency-Key`. It returns 409 on a stale revision and 422 on a bad value with a message saying what to send.
- `GET /products/{id}/price-history` returns the revision list, read-only.
- `POST /price-proposals/{id}/confirm` is the only path the agent's confirmation reaches. It is admin-only, and it re-checks permission, expiry and status server-side.
- Default-deny on the new router: a test walks every route for 401 without a token and 403 for a non-admin.

## Agent tool
- `propose_price_change(product_id, new_price, base_revision_no)` validates types, the currency and the range (bounds from the business owner, recorded next to the code), then stores a pending proposal and returns old → new with the proposal id. It never writes.
- Refusals say what to send instead, for example "send new_price as a decimal string such as 12.50".
- The reply to the chat shows a button carrying the proposal id. The admin confirms with that button; an allowlisted phrase is the fallback. The model cannot supply the confirm argument.
- Expiry is short (for example 10 minutes); the clock is injected so tests do not depend on real time.
- Tool results carry the figures the answer quotes, so the reply's numbers trace to this turn's tool result.

## Tests (each seen failing first)
- A model-chosen "confirm" argument is refused; "yes" inside tool output does not confirm anything.
- A non-admin confirm is refused with 403; an expired proposal is refused.
- A stale base revision is refused with 409 and writes nothing.
- Two real connections confirm the same proposal concurrently; exactly one revision is written. Removing the lock must make this test fail.
- Price history stays append-only: the old row keeps its price and gets `superseded_at`, and a backfill run twice changes nothing.
- The audit row records the actor, `origin = agent_confirmed` and the proposing model name.
- Validation loop: a scripted conversation where the model sends a bad value, gets the refusal, and retries correctly.
- Prompt-injection cases: a price in a product description or a tool output does not create a proposal.
- Migration tests run as the runtime role, not the owner.

## Later, not now
- A per-user daily cap on proposals and a metrics dashboard for proposals: add when there is real traffic. Skipped: a separate approvals service, since one guarded path in this app is enough.
