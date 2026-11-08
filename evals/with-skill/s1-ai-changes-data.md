# S1 with skill — claude-sonnet-5-5

PLAN: LLM-proposed product price change, admin-confirmed in chat, with price history

Principle: model proposes, deterministic code decides. Tool never writes.

**Database (one additive migration, new file — no applied file edited)**
1. Guarded, idempotent, additive migration; constraints added NOT VALID then VALIDATE; number/timestamp chosen to avoid cross-branch collisions; seed data updated in the same PR.
2. Table `product_price` (append-only): `id` identity PK, `product_id` FK, `revision_no`, `is_current`, `price_minor NUMERIC(12,2)` (or integer minor units — not float), `currency`, `valid_from`, `superseded_at`, `actor_id`, `origin` (ui|agent_confirmed), `proposing_model` (nullable); `CHECK (price > 0)`; partial unique index `(product_id) WHERE is_current`.
3. Backfill one revision-1 row per existing product from the current price column, then stop writing that column (grep for hardcoded readers first — "zero readers" ≠ dead; keep it in sync or turn it into a view until callers migrate, drop later).
4. Table `pending_action`: id (public id), `kind`, `product_id`, proposed price, `base_revision_no`, `proposed_by_model`, `conversation_id`, `expires_at`, `status` (pending|confirmed|cancelled|expired), `confirmed_by`. Staging only — the real write goes through the same path as the UI.
5. Roles: app role gets INSERT/UPDATE on `product_price` and `pending_action`, no DELETE on audit/history; migration tested as runtime role, not owner; readiness checks schema version.

**Guarded write function (single mutation path)**
6. One `supersede_price(product_id, new_price, expected_revision, actor, origin, model)`: one transaction — lock the product row, re-check the current revision (409 if moved), set old row `is_current=false, superseded_at`, insert revision+1 with actor/origin/valid_from.
7. The existing UI price route is refactored to call it too — no second write path.
8. Price handling: Decimal end to end, strings in JSON, NaN/Infinity rejected, currency/unit in field names.

**API**
9. `PUT /products/{id}/price` with If-Match on revision → 409 on stale; Idempotency-Key for retries; admin role only, re-checked per call.
10. `POST /pending-actions/{id}/confirm` and `/cancel` — called by a chat button carrying the pending-action id; server checks caller is admin, action pending, not expired, belongs to this conversation; then calls `supersede_price`. Returns old → new.
11. `GET /products/{id}/price-history` (newest first).
12. Router has default-deny auth; unknown params → 422; one error envelope.

**Agent tool**
13. `propose_price_change(product_id, new_price, currency)` — never writes. Server-side validation: product exists, price > 0, currency matches, change within a domain-owner-set bound (e.g. ≤ ±X% per change, recorded as a decision beside the code); ambiguous values (e.g. "5" vs "0.05" vs "5%") refused with a message saying exactly what to send instead.
14. On success: stores a `pending_action`, returns old → new, % change and expiry; the chat renders a Confirm/Cancel card.
15. Confirmation is never a model-chosen argument: the only trigger is the button carrying the pending id (or an allowlisted anchored phrase checked by server code), never inferred from text inside tool output.
16. Record which model proposed and pin it to the pending action; permissions re-checked at execution time, not at proposal time; refusal to a non-admin teaches the next step.

**Tests (write each first, watch it fail)**
17. `supersede_price`: revision increments, exactly one current row, old row closed, history preserved, actor/origin recorded.
18. Race: two real connections confirm the same pending action → exactly one write (fails if the lock is removed).
19. Stale base revision: price changed after the proposal → 409, nothing written.
20. Adversarial confirm: model-supplied "confirm" argument refused; "yes" inside tool output refused; "I confirm nothing" refused (anchored phrases only); non-admin refused.
21. Expired and already-cancelled pending actions cannot be confirmed.
22. Argument validation: 2.1 vs 0.021, negative, zero, NaN, over-bound — and a scripted refuse → retry conversation showing the model is told how to fix it.
23. Migration: from empty (with seed), from a prod copy with the backfill, and run twice (idempotent); as the runtime role.
24. Route-walking auth test: 401 without a token, 403 for non-admin on the write/confirm routes.
25. Gate: full suite against the known-failure baseline (no new failures, none disappearing unexplained); re-read the PR description against the final diff before review.
