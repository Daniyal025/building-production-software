# Plan: LLM-proposed price change, admin-confirmed, with history

Principle: the agent never writes a price. It only creates a pending proposal; a human-authenticated admin route applies it. History is append-only.

## Database (one migration)

1. `product_price_history`: `id`, `product_id` FK, `price_cents` int `CHECK (price_cents >= 0)`, `currency`, `valid_from timestamptz NOT NULL`, `valid_to timestamptz NULL`, `changed_by` (admin user id), `source` (`admin` / `agent`), `proposal_id` FK NULL.
2. Partial unique index `ON product_price_history (product_id) WHERE valid_to IS NULL` so a product has at most one current row.
3. `price_change_proposals`: `id`, `product_id`, `old_price_cents`, `new_price_cents`, `reason`, `status` (`pending` / `confirmed` / `rejected` / `expired`), `proposed_by` (agent session or conversation id), `created_at`, `decided_by`, `decided_at`.
4. Backfill: insert one history row per product from its current price, with `valid_from = now()`. Keep `products.price_cents` as the denormalised current value.
5. Make the migration reversible, or write down the downgrade if the project's tooling doesn't support it.

## API

6. `POST /products/{id}/price-proposals`: called by the agent tool, but also checks the caller's auth. It validates the new price, stores `old_price_cents` from the DB (never from the LLM), and returns the proposal id. It makes no price change.
7. `POST /price-proposals/{id}/confirm`: admin-only. Requires a human admin session, not the agent's service credential.
8. Confirm runs in one transaction: `SELECT ... FOR UPDATE` on the proposal and the product, then check `status = 'pending'`.
9. Stale check: if the current price no longer equals `old_price_cents`, return 409 and mark the proposal `expired`.
10. On success: close the current history row (`valid_to = now()`), insert the new row, update `products.price_cents`, and set the proposal to `confirmed` with `decided_by` and `decided_at`.
11. `POST /price-proposals/{id}/reject`: admin-only. Sets `rejected` and writes no price.
12. `GET /products/{id}/price-history`: read-only, ordered by `valid_from`.
13. Idempotency: confirming an already-confirmed proposal returns 200 with the existing result and does not write twice. Confirming a rejected or expired proposal returns 409.
14. Proposals older than N hours cannot be confirmed (the TTL is a setting).

## Agent tool

15. Tool `propose_price_change(product_id, new_price, reason)`. It calls the proposal endpoint and returns the proposal id, the old and new price and the status "pending admin confirmation".
16. Give the tool no confirm capability. The system prompt says that a price changes only after the admin confirms.
17. The chat UI shows the proposal as a card (old price, new price, reason) with Confirm and Reject buttons. These call the admin routes directly with the admin's session. Typing "yes" in chat does not apply a change.
18. Tool-side validation: positive price, a sane maximum change (for example reject more than ±50% without an explicit flag), and a known product id. Return clear errors the model can read.

## Tests (pytest, real Postgres, test-first)

19. Migration: backfill creates one open history row per product, and the partial unique index rejects a second open row.
20. Proposal creation: it writes no change to `products` or history, and `old_price` comes from the DB.
21. Confirm happy path: product price updated, old history row closed, new row open, the two rows contiguous, proposal `confirmed`.
22. Authorization: the agent credential and non-admin users get 403 on confirm and reject.
23. Stale proposal: the price changed after the proposal, so confirm returns 409 and nothing is written.
24. Double confirm and concurrent confirm (two threads): exactly one history row is written.
25. Reject and expired paths write no price. Tool test: the tool calls only the proposal endpoint (mock the HTTP layer) and never the confirm route.

## Later (not now)

Bulk proposals, per-role approval limits, and notifying admins of pending proposals.
