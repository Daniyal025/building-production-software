# S1 baseline (no skill) — claude-sonnet-5-5

**Plan: LLM-proposed price change, admin-confirmed, with history**

Database (one migration)
- `product_price_history(id, product_id FK, price NUMERIC(12,2) CHECK >= 0, currency, valid_from timestamptz, valid_to timestamptz NULL, changed_by, source ('admin'|'agent'), reason, proposal_id NULL)`.
- Partial unique index `(product_id) WHERE valid_to IS NULL` → at most one current price per product.
- Exclusion constraint on `tstzrange(valid_from, valid_to)` per product (if btree_gist available) to forbid overlapping periods.
- Backfill: one history row per product from current `products.price`, `valid_from = now()`, `source='backfill'`.
- Keep `products.price` as the current-price column for existing readers; it's only ever written in the same transaction as history (never by a separate code path).
- `price_proposals(id, product_id, old_price, new_price, status ('pending'|'confirmed'|'rejected'|'expired'), proposed_by_session, expires_at, decided_by, decided_at)`.
- Migration reversible (down script).

API
- `POST /products/{id}/price-proposals` (called by agent tool): validates product exists, price via Pydantic (Decimal, > 0, sane max), stores `pending`, returns proposal id + old/new price. No price change.
- `POST /price-proposals/{id}/confirm` — admin-only (existing auth dependency). In one transaction: `SELECT ... FOR UPDATE` on proposal and product; check status still `pending`, not expired, and product's current price still equals `old_price` (else 409 stale); close current history row (`valid_to = now()`), insert new history row, update `products.price`, mark proposal `confirmed`.
- Confirm is idempotent: re-confirming returns the same result / 409, never double-writes.
- `POST /price-proposals/{id}/reject` — admin-only.
- `GET /products/{id}/price-history` — ordered by `valid_from`.
- All endpoints use parameterized SQL; audit fields (who/when) written on every state change.

Agent tool
- `propose_price_change(product_id, new_price, reason)` → calls propose route with the agent's session identity; has no confirm capability.
- Tool returns a summary ("Proposed 10.00 → 12.00, awaiting admin confirmation").
- System prompt: the model must never claim the price changed until a confirmation result arrives.
- Confirmation happens in chat: only an admin's explicit confirm message (passed to the confirm route by the server, not the model) can trigger the write. A non-admin "yes" does nothing.
- Cap proposals per session; reject a new pending proposal for the same product while one is open.

Tests
- Migration: backfill creates exactly one open row per product; unique index blocks a second open row.
- Propose: creates pending proposal; `products.price` and history unchanged.
- Confirm happy path: old row closed, new row open, `products.price` updated, proposal `confirmed`.
- Confirm by non-admin → 403, nothing changes.
- Confirm idempotency: double confirm / concurrent confirms (race) → exactly one history row.
- Stale confirm: price changed after proposal → 409, no write.
- Expired / rejected proposal cannot be confirmed.
- Validation: negative, zero, non-numeric, huge price, unknown product → 422/404.
- Agent tool test: tool only calls propose; model-supplied confirm text never reaches the write path.
- Rollback: failure midway through confirm leaves history and `products.price` untouched.
- History endpoint returns correct ordering and no gaps/overlaps.
- Run full existing suite to confirm other `products.price` readers still pass.
