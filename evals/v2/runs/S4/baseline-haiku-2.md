# Plan: "order paid" consumer (reserve stock + confirmation email)

Assumes at-least-once delivery, so every message can arrive more than once and out of order. The design goal is that a duplicate changes nothing.

## Consumer

- Ack a message only after its Postgres transaction commits. A crash before the ack causes a redelivery, which the dedupe below absorbs.
- Dedupe on the event ID. The first statement in the transaction is `INSERT INTO processed_events (event_id) VALUES ($1) ON CONFLICT DO NOTHING`. If zero rows are inserted, ack and skip.
- Process one message in one DB transaction: dedupe insert, stock reservation, order status update, and email outbox insert. Either all of it commits or none of it does.
- Keep the handler idempotent by key: the reservation is keyed `(order_id, sku)`, so a retry cannot reserve twice even if dedupe is bypassed.
- Make reservation a conditional update: `UPDATE stock SET reserved = reserved + $qty WHERE sku = $1 AND on_hand - reserved >= $qty`. Zero rows updated means insufficient stock, which is a business outcome, not an error to retry.
- For insufficient stock, record the order as `reservation_failed` and ack. Do not loop on it.
- Send the confirmation email from an outbox row, not inline. A separate sender picks up unsent rows, so a rollback never sends mail and an email outage never rolls back the reservation.
- Handle out-of-order events: only move an order to `paid` if its current status allows it. Ignore a paid event for an order already cancelled or refunded, and log it.
- Retry transient failures (DB connection, deadlock) with bounded exponential backoff. After N attempts, send the message to a dead-letter queue with the error attached.
- Set the broker visibility timeout above the worst-case processing time, and drain in-flight messages on SIGTERM before exit.

## Data changes

- `processed_events(event_id text primary key, received_at timestamptz default now())`, for dedupe. Add a retention job that deletes rows older than the redelivery window.
- `stock(sku primary key, on_hand int, reserved int, check (reserved >= 0 and reserved <= on_hand))`. The check constraint is the last line of defence against overselling.
- `reservations(order_id, sku, qty, primary key (order_id, sku))`, so a reservation is unique per order line.
- `email_outbox(id, order_id unique, template, payload, status, attempts, sent_at, created_at)`, with the unique order_id preventing a second confirmation email for the same order.

## Tests

- Unit tests for the handler with an in-memory fake of the repository: happy path, insufficient stock, unknown SKU, cancelled order.
- Integration tests against a real Postgres (not mocks), because the conditional update and unique constraints are what matter.
- Duplicate delivery: send the same event twice and assert one reservation, one outbox row, and stock reserved only once.
- Crash simulation: force a failure after the DB commit but before the ack, redeliver, and assert no double effect.
- Concurrency: two consumers process two events for the last unit of stock and assert exactly one succeeds.
- Email failure: make the sender fail and assert the reservation still commits and the outbox row retries.

## Operations

- Metrics and alerts: consumer lag, processing time, redelivery rate, DLQ depth (alert on any growth), reservation_failed count, and outbox backlog age.
- Nightly reconciliation job: compare paid orders against reservations and outbox rows, and report mismatches. Run it after every release.
- DLQ runbook: inspect the error, fix the cause, then replay. Replay is safe because of the dedupe and unique keys.
- Structured logs with event_id and order_id on every line, so one order can be traced end to end.
- Deploy with a feature flag or a consumer-group switch so the new consumer can be turned off without a rollback.
- Run the migrations before the consumer deploys, and keep them backward compatible for one release.

Skipped for now: a separate reservation service, exactly-once broker features, and per-SKU locking. Add per-SKU locking if contention on hot SKUs shows up in metrics.
