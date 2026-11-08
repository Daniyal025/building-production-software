# Plan: "order paid" consumer (reserve stock, send confirmation email)

Scope assumption: real customers and real inventory, more than one developer, so this is built as a production service. It becomes high-stakes if reservations drive payments or refunds, or if several teams consume the same events. Say so and revisit then.

## Consumer

- **Dedupe inside the transaction.** In one Postgres transaction: `INSERT INTO processed_events(event_id) ... ON CONFLICT DO NOTHING`. If it inserts zero rows, the event was already handled: ack and stop. Redelivery then does no work.
- **Ack only after commit.** A crash between commit and ack causes a redelivery, which the dedupe row absorbs. Never ack first.
- **Reserve stock with a conditional update.** Use `UPDATE stock SET available = available - $q WHERE sku = $s AND available >= $q`, and check the row count. Don't read-then-write. Lock SKUs in sorted order inside the transaction so two multi-line orders can't deadlock.
- **Make the reservation itself idempotent.** `reservations` has a unique key on `(order_id, sku)`, so a bug or replay can't reserve twice even if the dedupe table were bypassed.
- **Insufficient stock is a business outcome, not an exception.** Record the reservation as `backorder` or `failed` with a reason, and emit a visible signal (status plus metric). Never ack as if it succeeded and never retry forever.
- **Email goes through an outbox row, not inline.** In the same transaction, insert an `email_outbox` row keyed by `order_id`. A separate sender loop (`FOR UPDATE SKIP LOCKED`) sends the email and sets `sent_at`. The database commit and the email can't diverge, and a failed send retries without touching stock.
- **Guard against double sends.** Pass the provider's idempotency key (`order_id`) if it supports one. Otherwise check `sent_at` before sending and accept the small window where a crash after sending but before marking could send a duplicate. Write that residual risk down.
- **Bound retries.** Use exponential backoff with jitter and a maximum attempt count. After that, move the message to a dead-letter queue with the error attached. Distinguish permanent failures (malformed payload, unknown SKU) from transient ones (DB down, SMTP timeout). Permanent ones go straight to the DLQ.
- **Timeouts and concurrency.** The handler timeout must be shorter than the queue's visibility/ack timeout, otherwise the message is redelivered while still running. Cap consumer concurrency to the DB pool size.
- **Validate the payload at the boundary.** Parse and type-check with a schema (quantities as integers, ids required). Reject bad messages to the DLQ rather than guessing defaults. Don't rely on ordering between events.

## Data changes

- **Migration is additive and forward-only.** It adds `processed_events(event_id PK, processed_at)`, `reservations(order_id, sku, qty, status, reason, created_at; unique order_id+sku; FK to stock)`, and `email_outbox(order_id PK, to_address, payload, attempts, sent_at, last_error)`.
- **Constraints do the guarding.** Add `CHECK (available >= 0)` on stock (as `NOT VALID`, then `VALIDATE` if the table is large), `NOT NULL` where the code assumes a value, and a CHECK list on `status`.
- **Deploy order.** Schema first, then the consumer. The readiness probe checks that the new tables exist. The service connects as a least-privilege role, not the table owner.
- **Retention.** Add a nightly sweep that deletes old `processed_events` and sent `email_outbox` rows. Keep the dedupe window longer than the longest possible redelivery horizon.

## Tests

- **Write each test first and watch it fail.** Run order: duplicate delivery of the same event produces one reservation, one stock decrement and one email row.
- **Race test with two real connections.** Two consumers handle events for the last unit at the same moment, and exactly one wins. Confirm the test fails when the conditional update is replaced with read-then-write.
- **Crash-point tests.** Kill the handler after commit but before ack, and again mid-transaction. The end state must be correct in both cases, with nothing half-applied.
- **Email failure test.** The provider errors, the stock stays reserved, the sender retries, and exactly one email is eventually sent. Use a fake provider that records idempotency keys, and inject the clock for backoff.
- **Bad-input and out-of-stock tests.** A malformed payload goes to the DLQ with a reason. An out-of-stock order produces a visible `backorder` status, not a silent success.

## Operations

- **Metrics and alerts.** Track throughput, error rate and handler duration (p50/p95/p99). Alert on queue depth, age of the oldest message and DLQ depth (any message at all is worth a look). Page on symptoms such as orders not confirmed within N minutes, each with a runbook link.
- **Structured logs.** Carry `event_id` and `order_id` on every line, and log each error once where it is handled. Add a data-freshness check (the latest reservation is recent relative to the latest paid order).
- **Runbook and replay.** Document how to inspect the DLQ, fix the cause and replay messages. Replay is safe because the consumer is idempotent. Also cover how to release a stuck reservation and how to resend an email by hand.
- **Rollout.** Ship behind a flag or on a single consumer first, compare reservation counts against paid orders for a day, then scale out. Roll back by stopping consumers; the queue holds messages and idempotency makes resuming safe.
