# Plan: "order paid" consumer (reserve stock, send confirmation email)

The main idea is to split the work in two. Stock reservation is a database operation, so it can be made exactly-once with a transaction. Email is an outside side effect, so it can't. Put the email behind an outbox and make each half safe to repeat.

## Consumer

- **Validate at the boundary.** Parse the event into a typed model (order_id, event_id, version, lines of sku and qty). A malformed or unknown-version event goes straight to the dead-letter queue with the reason. Retrying it can't help.
- **One transaction per message, ack only after commit.** The transaction does three things:
  - insert `processed_events(event_id PRIMARY KEY)`;
  - reserve stock;
  - insert the email outbox row.
  A duplicate delivery hits the unique key, does nothing, and is acked.
- **Reserve atomically, with no read-then-write.** Use `UPDATE stock SET available = available - :qty WHERE sku = :sku AND available >= :qty`. Zero rows updated means insufficient stock. Update SKUs in a fixed sorted order so two orders can't deadlock.
- **Insufficient stock is a recorded outcome, not an error.** Write the reservation as `backordered` or `failed` with the reason, then ack. Do not retry in a loop and do not drop it. Whatever changes the customer-facing result (email wording, a refund or ops task) hangs off that status.
- **Tolerate out-of-order events.** An "order cancelled" event can arrive before "paid". Key the reservation by `(order_id, sku)` and carry the event version. Ignore any event older than the one already applied.
- **Bounded retries.** Transient failures (DB down, deadlock) are retried with exponential backoff and jitter, up to a maximum attempt count. Then the message goes to the DLQ with the error. Keep a small replay command for the DLQ.
- **Handler timeout is shorter than the queue's visibility/ack timeout.** Otherwise the message is redelivered while it is still being processed. Bound consumer concurrency to the DB pool size, and shut down gracefully so in-flight messages finish or are released.

## Data changes

- **Additive migration, applied before the consumer ships.** Tables:
  - `processed_events`;
  - `stock_reservations(order_id, sku, qty, status, event_version, created_at)` with `UNIQUE(order_id, sku)`;
  - `email_outbox(order_id UNIQUE, to_address, template, status, attempts, sent_at, last_error)`.
- **Let the database enforce the rules.** Use `CHECK (available >= 0)` on stock, a CHECK list on status values, foreign keys, and NOT NULL. Even a buggy code path then can't oversell.
- **Migration safety.** The migration is guarded and safe to run twice. Test it from an empty database and from a copy of production. Never edit it once applied. The consumer connects as its own role with only the grants it needs, never as the owner.
- **Retention.** Sweep `processed_events` nightly, keeping longer than the queue's maximum redelivery window. Prune sent outbox rows after a retention period. Record actor/origin (`order-paid-consumer`) and time on every write.

## Email

- **Separate sender worker polls the outbox.** It uses `SELECT ... FOR UPDATE SKIP LOCKED`, calls the provider with an idempotency key of the order id (or checks the sent-marker first), then sets `sent_at`. A crash between "sent" and "marked" can still produce one duplicate email if the provider has no idempotency support. Accept that and note it.
- **Email failure never blocks stock.** The reservation is already committed. The sender retries with backoff, then marks the row `failed` and alerts.

## Tests

- **Write each test first and watch it fail.** Don't mock the unit under test.
- **Duplicate and crash cases.**
  - Deliver the same event twice and assert one reservation, one decrement, one outbox row.
  - Kill the handler between commit and ack, redeliver, and assert nothing doubles.
  - For the sender, fail after the provider call but before the marker and assert the retry reuses the idempotency key.
- **Concurrency with two real DB connections.** Two orders race for the last unit. Exactly one wins and stock never goes negative. This test must fail if the conditional UPDATE is removed.
- **Edge cases.** Insufficient stock, a multi-line order where one line fails (whole order rolls back to `backordered`, no partial decrement), an older version arriving after a newer one, and a malformed payload going to the DLQ. Inject the clock so retry and backoff tests don't depend on the date.

## Operating it

- **Rollout order.** Migration first, then the consumer. Start with one consumer instance, check the first real events end to end, then scale. Readiness checks the schema version.
- **Metrics and logs.** Structured logs carry event_id and order_id on every line. Track rate, errors, and duration (p95/p99) for the handler and the sender. Also track queue depth, age of the oldest message, and DLQ depth.
- **Alert on what customers see.** Page on:
  - the oldest message getting too old;
  - DLQ depth above zero;
  - time from "paid" to "email sent" breaching its target.
  Each alert links a runbook covering how to inspect the DLQ, fix the cause, replay, and the safe way to manually release a reservation.
- **Reconciliation.** A daily job compares paid orders against reservations and outbox rows and reports any gap. It catches what the other checks miss.
- **Later, only if needed.** Distributed tracing across the producer, queue, and consumer, and consumer contract tests with the producing team once the event schema starts changing.
