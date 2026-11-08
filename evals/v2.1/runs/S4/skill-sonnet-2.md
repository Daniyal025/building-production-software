# Plan: "order paid" consumer (reserve stock + confirmation email)

Scope: production service with real orders and stock, so I'm building for real users but not a multi-team platform. What would justify more rigour is listed at the end.

## Consumer

- **One transaction per message.** Validate the payload (order id, event id, lines with sku and integer qty), then in a single Postgres transaction: dedupe, reserve stock, queue the email. Ack the message only after commit. A crash before ack means redelivery, which the dedupe makes harmless.
- **Dedupe inside that transaction.** `INSERT INTO processed_events (event_id PRIMARY KEY, order_id, processed_at) ON CONFLICT DO NOTHING`. If no row was inserted, it's a duplicate: ack and stop. Also put a unique constraint on `(order_id, sku)` in reservations, so a redelivery under a *different* event id for the same order still can't double-reserve.
- **Reserve atomically in SQL, not read-then-write.** `UPDATE stock SET available = available - $qty WHERE sku = $sku AND available >= $qty`. Zero rows updated means insufficient stock. Add a `CHECK (available >= 0)` as the backstop. Lock SKUs in sorted order so two orders with overlapping SKUs can't deadlock.
- **Out of stock is a business outcome, not a retry.** The whole order is reserved or not at all (the same transaction rolls back partial lines). Record the order as `backordered` and route it to a person or a backorder flow. Never retry it forever, and never send a "confirmed" email for it.
- **The email never happens inside the DB transaction.** Insert a row in `email_outbox (order_id UNIQUE, status, attempts, sent_at)` in the same transaction as the reservation. A separate sender loop picks up pending rows (`FOR UPDATE SKIP LOCKED`), sends, and marks them sent. This way a mail outage can't roll back or re-run the reservation.
- **Make the send itself idempotent.** Pass `order_id` as the provider's idempotency key if it supports one. Otherwise accept that a crash between send and mark-sent can produce one duplicate email, and say so in the runbook. A duplicate confirmation is far cheaper than a lost one.
- **Failures have a ceiling.** Bounded retries with exponential backoff and jitter, then dead-letter with the error reason. Handler timeout is shorter than the queue's visibility/ack timeout, so a slow handler isn't redelivered while still running. Consumer concurrency is capped, and the DB pool is sized to match.
- **Don't assume order.** If a later event for an order arrives first, or "paid" arrives for an unknown order, park it for a bounded retry and then DLQ. Don't guess.

## Data changes

- **Additive migration only, forward-fixing.** New tables: `processed_events`, `reservations (order_id, sku, qty, status, UNIQUE(order_id, sku))`, `email_outbox`. Plus the `CHECK` on stock. Roll out in the order migration, then consumer; never edit an applied migration.
- **Existing stock rows may already violate the new CHECK.** Run a pre-check query on production data before applying the constraint, and decide how to fix any negative rows rather than discovering them mid-deploy.
- **A retention job for `processed_events`.** Keep it longer than the queue's maximum redelivery window (for example 30 days), then prune in batches.

## Tests

- **Write each test first and watch it fail.** Run them against a real Postgres, not a mock, because the guarantees live in constraints and locks.
- **Duplicate delivery.** The same event twice, and the same order under two event ids, leaves exactly one reservation, one stock decrement and one outbox row.
- **Concurrency.** N consumers racing on the last unit of a SKU: exactly one wins, stock never goes below zero. Also two orders with overlapping SKUs in opposite order, to show no deadlock.
- **Crash points.** Kill the consumer after commit but before ack (redelivery is a no-op), and mid-transaction (nothing partial persists). For the email sender, fail before the send, and between send and mark-sent.
- **Failure paths.** Insufficient stock produces `backordered` with no confirmation email. A malformed payload goes to the DLQ with its reason rather than being retried. An email-provider outage leaves stock reserved exactly once and the email retried later.

## Operations

- **Structured logs carrying event id and order id** on every line, logged once where the error is handled. Metrics: processed, duplicate, backordered and failed counts, handler duration p95/p99, and email-sent count.
- **Alerts on symptoms, each linked to a runbook.** Oldest-message age and queue depth (consumer stuck or lagging), DLQ depth greater than zero, email outbox oldest pending age, and a sharp rise in backorders.
- **A DLQ replay tool** that is safe to run because the consumer is idempotent. Document the manual steps for a backordered order and for a suspected duplicate email.
- **Deploy and shutdown.** On SIGTERM, stop pulling, finish the in-flight message, then exit. Roll out one consumer first and watch the metrics before scaling up.
- **What would move this up a tier:** stock reservations that feed payments or invoicing, multiple teams consuming the event (add versioned schemas and contract tests), or strict ordering needs per order (add event versions).
