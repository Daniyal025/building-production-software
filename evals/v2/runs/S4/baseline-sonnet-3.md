# Plan: "order paid" consumer (at-least-once, Postgres stock reservation, confirmation email)

## Consumer
- One long-running worker; pull a message, handle it, ack only after the DB transaction commits. Never ack before.
- Validate the payload at the boundary (event_id, order_id, line items). Malformed messages go straight to a dead-letter queue (DLQ) with the reason; do not retry them.
- Idempotency key is the event_id (or order_id if events can be re-issued for the same order). Duplicates are expected, so treat them as normal, not as errors.
- Dedupe with a Postgres table: `INSERT INTO processed_events(event_id) ... ON CONFLICT DO NOTHING` inside the same transaction as the reservation. If no row was inserted, ack and skip.
- Reserve stock in that same transaction with a guarded update: `UPDATE stock SET available = available - :q WHERE sku = :sku AND available >= :q`. Zero rows updated means insufficient stock.
- Lock rows in a consistent order (sort by sku) to avoid deadlocks between concurrent consumers. Retry on deadlock or serialization failure.
- Insufficient stock is a business outcome, not a crash: record the order as `backorder` or `reservation_failed`, ack the message, and flag it for a human or a refund flow. Do not retry it forever.
- Email goes through a transactional outbox: in the same transaction, insert a row into `email_outbox(order_id, status='pending')`. A separate sender loop sends the email and marks the row `sent`. This avoids both "reserved but no email" and "email sent but rolled back".
- Make the send idempotent: unique constraint on `email_outbox(order_id, kind)`, and pass an idempotency key to the email provider if it supports one. A crash between send and mark-sent may produce a rare duplicate email. Accept that and document it.
- Retry transient failures (DB or email provider down) with exponential backoff and jitter. After N attempts, send to the DLQ.

## Data changes
- A migration adds `processed_events(event_id pk, processed_at)`, `stock_reservations(order_id, sku, qty, status, created_at)` with a unique `(order_id, sku)`, and `email_outbox(id, order_id, kind, status, attempts, last_error, sent_at)`.
- Add `CHECK (available >= 0)` on the stock table as a last line of defense. Make the migration backward compatible (additive only) so it deploys before the consumer.

## Tests
- Unit tests for payload validation and the reservation logic (enough stock, exact stock, insufficient stock, multi-SKU partial failure rolls back everything).
- Integration tests against a real Postgres (testcontainers or a CI service), not mocks: deliver the same event twice and assert one reservation and one outbox row.
- Concurrency test: two consumers process different orders for the same SKU, and stock never goes negative. Add a crash test that kills the worker after commit but before ack, then redelivers.
- Outbox sender test with a fake email provider: failure then success, and no double-send after a mark-sent failure.

## Operations
- Metrics and alerts: queue depth and oldest-message age, processing latency, DLQ count (alert on any growth), outbox pending age, and reservation-failure rate.
- Structured logs carry event_id and order_id. Add a runbook for DLQ replay (safe because of idempotency) and for low-stock or failed-reservation orders.
- Roll out behind a flag or on a shadow consumer first, then scale workers horizontally. Keep the connection pool small and set a statement timeout. Shut down gracefully on SIGTERM by finishing the in-flight message before exit.
