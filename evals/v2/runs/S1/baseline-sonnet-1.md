# Plan: LLM-proposed price change, admin-confirmed, with history

## Database (one migration)
- Add `product_price_history(id, product_id FK, price NUMERIC(12,2) CHECK (price >= 0), currency, valid_from timestamptz NOT NULL, valid_to timestamptz NULL, changed_by, source ('admin'|'agent'), reason, proposal_id NULL)`.
- Partial unique index on `(product_id) WHERE valid_to IS NULL` so a product has only one current price.
- Keep `products.price` as the current-price cache (existing readers keep working); history table is the source of truth.
- Backfill: one open row per product from today's `products.price`, `valid_from = migration time`.
- Add `price_proposals(id, product_id, old_price, new_price, status 'pending'|'confirmed'|'rejected'|'expired', proposed_by_session, created_at, decided_by, decided_at, expires_at)`. Proposals must be persisted so the confirm step can't be forged by the LLM.
- Index `(product_id, valid_from DESC)` for history reads; migration reversible (down drops both tables).

## API route
- `POST /products/{id}/price-proposals` (agent-callable): validates price > 0, differs from current, creates a `pending` row, and does NOT touch the price.
- `POST /price-proposals/{id}/confirm` (admin only, auth dependency): one transaction does `SELECT ... FOR UPDATE` on the proposal, checks status is pending and not expired, checks the current price still equals `old_price` (else 409 stale), closes the open history row (`valid_to = now()`), inserts the new row, updates `products.price`, and marks the proposal confirmed.
- `POST /price-proposals/{id}/reject` (admin): sets status rejected.
- `GET /products/{id}/price-history`: returns the history rows, newest first.
- Confirm is idempotent: a second call on a confirmed proposal returns the same result, not a double write.
- Pydantic schemas with `Decimal` (never float) for price.

## Agent tool
- Tool `propose_price_change(product_id, new_price, reason)` only calls the proposal endpoint or service. It never has a write path to the price.
- Tool returns the proposal id plus old and new price, and the model is told to ask the admin to confirm.
- Confirmation is done by the admin's own UI action or authenticated chat button hitting the confirm route, not by the model re-calling a tool with "yes". The admin's identity comes from the session, not from tool arguments.
- Tool schema constrains `new_price` to a positive number with a max, and rate-limits proposals per session.
- Optional read tool `get_price_history(product_id)` so the assistant can answer "what was it before?".

## Tests
- Migration test: backfill creates exactly one open row per product, and the unique partial index rejects a second open row.
- Service test: confirm closes the old row, opens the new row, and updates the cache atomically; a forced failure mid-transaction rolls everything back.
- Route tests: non-admin gets 403 on confirm; the agent-side proposal never changes the price; the stale-price case returns 409; expired and double-confirm cases are covered; negative, zero and non-numeric prices return 422.
- Concurrency test: two simultaneous confirms yield one history row.
- Agent tool test with a stubbed LLM: the tool creates a pending proposal only, and the product price is unchanged afterwards.
- End-to-end test: propose, confirm, then `GET /price-history` shows both rows with the correct `valid_from`/`valid_to` and `source='agent'`.

## Later (not now)
- Proposal expiry job, audit-log export, bulk price changes.
