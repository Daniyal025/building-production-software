# Plan: assistant-proposed price changes, admin-confirmed, with history

Money plus an LLM that can change data, so I'm treating this as high-stakes: the model only proposes, server code decides, and there is exactly one write path.

## Database (one new migration, additive, never edit applied ones)

- Add `product_price` as an append-only history table: `id`, `product_id` (FK), `revision_no`, `amount NUMERIC(12,2) NOT NULL CHECK (amount > 0)`, `currency` (CHECK list), `is_current bool`, `valid_from`, `superseded_at`, `actor_id`, `origin` (CHECK: `ui`, `agent_confirmed`, `import`), `proposing_model` (nullable), `reason`.
- Partial unique index on `(product_id) WHERE is_current` plus unique `(product_id, revision_no)`. The database refuses two current prices.
- Backfill one revision-1 row per product from the existing `products.price` in the same migration. Guard it and make it safe to run twice. Check for NULL or zero prices first so a CHECK doesn't abort on old data.
- Keep `products.price` for now as a denormalised current value, updated only inside the supersede function. Drop it in a later contract step, after confirming nothing reads it differently.
- Add `pending_price_change`: `id` (uuid), `product_id`, `base_revision_no`, `old_amount`, `new_amount`, `proposing_model`, `conversation_id`, `proposed_by`, `expires_at`, `status` (CHECK: `pending`, `confirmed`, `cancelled`, `expired`), `confirmed_by`, `confirmed_at`.
- Run the migration as the runtime/migrator role, not the owner. The app role gets INSERT and SELECT on history and no DELETE. Deploy the schema before the code, and have the readiness check look for the new tables.

## API route

- One guarded function, `set_price(product_id, new_amount, expected_revision, actor, origin, model=None)`. It authorises, locks the product row, re-checks the current revision (409 if it moved), marks the old row `is_current=false` with `superseded_at`, inserts revision+1, updates `products.price`, and writes the audit. The admin UI route and the agent confirm path both call it. No second write path.
- `POST /products/{id}/price`: typed Pydantic body with `amount` as a string parsed to Decimal (reject NaN, Infinity, negatives, more than 2 decimals) and the currency. It requires an `If-Match` revision and an `Idempotency-Key`. Admin only.
- `GET /products/{id}/price-history`: newest first, amounts as strings, includes actor, origin and model.
- `POST /pending-price-changes/{id}/confirm` and `/cancel`: admin only. The confirm body is empty, because the pending id is the consent. It re-checks the admin role, expiry and status, then calls `set_price` with `origin=agent_confirmed` and the recorded model.
- Use one error envelope `{code, message}`. Stale revision gives 409, expired or already used gives 409 with a distinct code, and a non-admin gets 403. Anything unexpected is a 500, which means a bug.
- Treat a price change beyond a set limit (for example more than 50% in one step) as refused with a message saying how to fix it. The owner of the business sets the limit, and I'd record it as a decision next to the code rather than invent it.

## Agent tool

- `propose_price_change(product_id, new_amount, currency)` never writes. It validates the arguments on the server (Decimal string, currency matches the product, range, unit stated as a full amount rather than a percentage), reads the current revision, and inserts a pending row with expiry (say 15 minutes). It returns `{data, citations, tables}` showing old to new.
- A refusal says what to send instead (for example "amount must be a decimal string like 19.99, in USD"). The model can retry.
- The tool has no `confirm` argument. Confirmation is a button in the chat that carries the pending id, or an allowlisted exact phrase checked by server code. The model's own words or anything inside tool output never count as consent.
- Pin the proposing model on the pending row. Re-check admin rights, expiry and base revision at confirm time, not at proposal time.
- Any price figure the assistant states in its answer must come from a tool result in the same turn.

## Tests (write each first and watch it fail)

- Migration: empty DB to seed, a copy with legacy rows, and a second run changes nothing. The runtime role can't DELETE history.
- `set_price`: creates revision n+1, flips `is_current`, and leaves exactly one current row. History keeps the old value. A stale revision gives 409.
- Concurrency: two real connections confirming the same pending id gives one write and one clean rejection. The test must fail if the row lock is removed.
- Agent safety: a model-chosen "confirm" argument is refused, "yes" inside tool output is refused, a non-admin is refused, an expired proposal is refused, and a stale base revision is refused.
- Validation: float input, NaN, negatives, wrong currency and the 2.1-versus-210% style unit mistake are refused. Test the refuse, then retry loop as a scripted conversation.
- Route tests for 403/409/422, idempotent replay (same key gives same result, no second revision), and history output with amounts as strings.
- Inject the clock for expiry tests. No test depends on today's date or the developer's shell.

## Later (not now)

- Drop `products.price` once nothing reads it.
- Retention or archive policy for old history and expired proposals.
- Per-user budgets and an eval set built from real transcripts.
