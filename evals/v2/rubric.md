# v2 rubric (independent and blind)

These rubrics were written by a separate agent, prompted as a principal engineer, which **never saw the skill**. It was given only the five task prompts. It was told to cover what a strong senior engineer would include, to avoid rewarding length or extra scope, and, for S5, to reward proportionality and penalise over-engineering. The skill's rules were frozen before these rubrics arrived; see `frozen-content.sha256`. Each item scores 0, 0.5 or 1.

## S1 — LLM proposes a price change, admin confirms in chat, prices keep history
1. Stores price history in an append-only table (product_id, price, currency, effective_at, changed_by, reason), with the price in NUMERIC or integer minor units, never float.
2. Keeps "current price" consistent with history. Either derive it from the latest row, or update products.price in the same transaction as the history insert, with a constraint (e.g. a partial unique index) allowing one current row per product.
3. Separates a proposal record (pending price change: status, proposed_by=agent, old-price snapshot, expires_at) from the applied change. The agent tool can only create proposals and never writes the price.
4. Confirmation is a human-originated action bound to a specific proposal id (UI button or server-issued token). It is not an LLM tool call, and "the admin said yes" text from the model or chat content is never trusted.
5. The server checks the confirming user's admin role from the authenticated session, not from anything the LLM passes in tool arguments.
6. Confirm is atomic and race-safe: a conditional UPDATE ... WHERE status='pending' RETURNING, plus a check that the price is unchanged since the proposal (expected old price/version). Otherwise it returns 409, which prevents double-apply and lost updates.
7. The API route spec covers validation (positive price, currency, an optional max-change bound) and correct status codes (403/404/409/422). Routes are idempotent on retry.
8. The agent tool has a strict typed schema (product_id, new_price as a decimal string, reason). It resolves or disambiguates the product before proposing and returns a human-readable before/after summary for the admin.
9. The migration is safe on a live table: it backfills one history row per existing product, avoids long locks or table rewrites, and states the rollback/forward-fix approach.
10. The audit trail records proposer, confirmer, timestamps and conversation/chat id. Rejected and expired proposals are kept, not deleted.
11. Tests run against real Postgres: confirm applies the price and writes history, non-admin is rejected, expired or stale proposals are rejected, and double or concurrent confirm applies once.
12. Agent tests use a mocked or recorded LLM. They assert the tool only creates proposals and that no path changes a price without confirmation, including prompt-injection text in product data. The answer stays near ~25 bullets.

## S2 — Nightly exchange-rate CSV import (revisions, layout changes)
1. The rates table has a natural-key unique constraint (rate_date, base, quote/currency), NUMERIC precision, and source/fetched_at columns.
2. Revisions are handled explicitly: upsert on the natural key while keeping prior values (revision table or valid/recorded-time columns), so past figures can be reproduced and audited.
3. Each run re-fetches a lookback window of recent days, not only "today", so the bank's revisions to past days are picked up.
4. Stores the raw downloaded file (or its hash plus a copy) with fetched_at for replay and debugging, and skips reprocessing when the content hash is unchanged.
5. Validates the layout by matching header names (not column positions) against the expected set. On an unknown layout it fails loudly with zero rows written.
6. Validates data: parseable dates and numbers, positive rates, expected currency set, and a plausibility check (e.g. a day-over-day jump threshold). Bad rows are rejected or quarantined, not silently loaded.
7. Loads atomically (staging table plus merge in one transaction). The job is idempotent and safe to re-run, with a date-range argument for backfill.
8. Network handling uses timeouts and bounded retries with backoff, and tells "not published yet / holiday / weekend" apart from a real failure.
9. Scheduling runs after the bank's publication time with explicit timezones. A lock (e.g. Postgres advisory lock) prevents overlapping runs.
10. Tests use saved real CSV fixtures (current layout, a revised day, a changed layout). They cover the parser, "layout change fails with no writes", revision history, and re-run idempotency against real Postgres.
11. Monitoring has a run log (status, rows inserted/updated/revised) and alerts on both failure and staleness: no new rate within N business days, i.e. a dead-man's switch, not only error alerts.
12. Defines what readers get for non-publication days (e.g. last available rate, flagged) and a short runbook for re-running or backfilling. The answer stays near ~20 bullets.

## S3 — Stale stacked branch → review-ready PR
1. Brings the branch up to date with current main (rebase or merge, per team convention, stated). Resolves conflicts deliberately and does not blindly accept one side.
2. Checks for migrations added on main since the branch point and renumbers or re-parents its own migration so the chain is linear. Verifies upgrade (and downgrade, if supported) from main's current schema on a fresh DB.
3. Re-runs the full test suite after the rebase and gets CI green on the pushed branch. "Passed locally before rebase" is not enough.
4. Finds all call sites of the renamed helpers, including code added in main's 60 commits and in the stacked branches. Uses grep plus type checks or lint to catch misses.
5. Considers moving the rename into its own commit (or PR) separate from behaviour changes, or keeping a temporary alias, to cut review noise and conflicts for others.
6. Rebases the two stacked branches onto the new tip in order (e.g. `git rebase --onto` or `--update-refs`), re-runs their tests, and tells their owners.
7. Uses `--force-with-lease` for rewritten branches and never force-pushes shared branches without coordination.
8. Re-measures the 40% claim on the rebased code with a stated method: same environment and data size, multiple runs, median or variance, before/after numbers. A single timing run is not presented as proof.
9. Self-reviews the full diff against main: removes debug code, squashes fixup commits into logical ones, runs lint and type checks.
10. The PR description states what and why, links the issue, and summarizes changes, including a list of renamed functions (old → new).
11. The PR description has migration notes (reversibility, lock or runtime impact, deploy order or backfill), testing done, how to reproduce the perf measurement with its caveats, and the PR's place in the stack (base, dependents, merge order).
12. Names risks, rollback plan and where reviewers should focus. The answer stays proportionate (~15 bullets) with no unneeded ceremony.

## S4 — "Order paid" event consumer (at-least-once), reserve stock, send email
1. Idempotency comes from a processed-events table with a unique event_id, inserted in the same transaction as the stock reservation. A duplicate delivery is detected, skipped and acknowledged.
2. Reservations have a natural-key unique constraint (order_id, sku), so a retry cannot double-reserve even if the event id changes.
3. The stock decrement is race-free: a conditional `UPDATE ... SET available = available - qty WHERE available >= qty` or row locks, plus a `CHECK (available >= 0)`. No read-then-write in application code.
4. Email is never sent inside the DB transaction. A transactional outbox row is written in the same transaction and a separate sender delivers it, using a dedupe/idempotency key toward the provider.
5. Acknowledges the message only after commit, and explains why a crash between commit and ack is safe (redelivery hits the idempotency key).
6. Failures are classified: transient (DB or network) retries with backoff; permanent (malformed payload, unknown SKU) goes to a DLQ after N attempts so a poison message does not block the queue.
7. Defines the business path for insufficient stock (mark the order for attention, backorder, or emit a refund/cancel event) instead of an unhandled exception or endless retry.
8. Validates payloads against a versioned schema and considers out-of-order or conflicting events (e.g. cancel arriving before or after paid).
9. Safe with multiple consumer instances. Visibility timeout or ack deadline is longer than processing time, prefetch is bounded, and shutdown is graceful (finish or nack in-flight messages).
10. Tests run against real Postgres: duplicate delivery processes once, concurrent same-event and same-SKU handling, simulated crash between commit and ack, insufficient stock, and an email failure that does not roll back the reservation.
11. Operational signals: queue lag/depth, DLQ size alert, error rate, outbox backlog age. Structured logs carry event_id and order_id for correlation.
12. Runbook: safe DLQ replay (relying on idempotency), a periodic reconciliation of paid orders against reservations and sent emails, and a retention policy for the processed-events table. The answer stays near ~20 bullets.

## S5 — Weekend prototype for 5 friends (shared expenses)
1. Picks one simple stack: e.g. Flask or FastAPI with server-rendered templates or a single static page. No SPA framework or JS build chain unless justified.
2. Uses SQLite (or a single file) for storage. No separate Postgres server, ORM migration framework or cache layer.
3. The data model is minimal: people, expenses (payer, amount, description, participants or split), and optionally settlements. Nothing speculative.
4. Stores money as integer cents or Decimal, never float, and handles split rounding remainders deterministically.
5. Computes net balances correctly (they sum to zero) and reduces them to a short "who pays whom" list (e.g. a greedy creditor/debtor match).
6. Leaves one small runnable test or self-check of the split and balance logic, the only non-trivial code. No full test suite, coverage targets or CI pipeline.
7. Keeps access control minimal but present if the app is public: a shared password or secret link via env var or basic auth. No user accounts, OAuth or roles.
8. Deploys in one step to a free or simple host, or runs locally with a tunnel. No Docker or Kubernetes, IaC or multi-environment setup unless the author already uses them by habit.
9. Lists what is deliberately skipped (accounts, multi-currency, notifications, edit history, mobile app, scaling, background jobs, microservices) with a one-line trigger for revisiting each.
10. Notes the main data-loss risk (ephemeral disk on free hosts) and a trivial mitigation (persistent volume or occasional DB file copy).
11. Covers basic input sanity (positive amounts, valid participants) and relies on template auto-escaping. No heavyweight validation or security framework.
12. Stays within ~15 bullets and gives a concrete weekend-sized order of work. It does not pad with production-grade practices the prototype does not need.
