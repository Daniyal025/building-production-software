# Order-paid consumer plan (at-least-once delivery)

## Consumer

- Consume `order paid` events with a manual ack. Ack only after the DB transaction commits and the email step has either succeeded or been queued.
- Treat every delivery as possibly duplicate and possibly out of order. Key all work on the event's unique ID (or `order_id` plus event type if the producer gives no ID).
- Validate the payload at the boundary (schema, required fields, quantities > 0). Reject malformed messages to a dead-letter queue (DLQ) instead of retrying them forever.
- Retry transient failures (DB deadlocks, connection errors, SMTP timeouts) with exponential backoff and a max attempt count. After the limit, send to the DLQ with the error attached.
- Run consumers with a bounded prefetch and a fixed worker count, so one slow email does not block the queue.
- Handle SIGTERM by finishing the in-flight message and then stopping consumption, so a deploy does not leave half-processed work.

## Data changes (Postgres)

- Add a `processed_events` table (`event_id` primary key, `processed_at`, `status`). The unique key makes a repeat delivery a no-op.
- Add a `stock_reservations` table (`order_id`, `sku`, `qty`, unique on `(order_id, sku)`) so reservations are idempotent per order line.
- Reserve stock in one transaction: insert the `processed_events` row, insert the reservations, and decrement `available` with a guarded `UPDATE ... WHERE available >= qty`. Any shortfall rolls back the whole event.
- Add a `CHECK (available >= 0)` constraint on the stock table as a backstop against overselling under concurrency.
- Send the confirmation email through an outbox table (`email_outbox`, written in the same transaction) and a separate sender loop. This avoids sending mail for a rolled-back reservation, and a crash between DB commit and send is retried, not lost.
- The email sender uses the outbox row ID as the idempotency key where the provider supports it. Otherwise accept the rare duplicate email and say so.

## Tests

- Unit test the reservation logic with the same event delivered twice: one reservation, one decrement, one outbox row.
- Test the insufficient-stock path: no reservation, no email row, event marked failed or routed to the DLQ.
- Concurrency test: two consumers race on the last unit of a SKU; exactly one succeeds. Run against real Postgres, not a mock.
- Crash test: kill the process after commit and before ack; on redelivery, nothing is double-applied.
- Email sender test: a provider timeout is retried and the outbox row is not lost.
- Poison message test: malformed payload lands in the DLQ and the consumer keeps running.

## Operations

- Export metrics: messages consumed, duplicates skipped, reservation failures, DLQ depth, outbox lag (oldest unsent row age), and consumer lag on the queue.
- Alert on DLQ depth above zero, outbox lag over a few minutes, and consumer lag growing for more than a set window.
- Provide a documented replay runbook: how to re-drive DLQ messages safely, which the idempotency keys make safe.
- Keep a retention rule for `processed_events` (for example 30 days) so the table does not grow forever, and make sure the retention window is longer than the queue's maximum redelivery window.

Skipped: exactly-once delivery machinery, a separate saga service, and a stock-ledger event store. Add them when duplicate or lost-reservation incidents show the current design is not enough.
