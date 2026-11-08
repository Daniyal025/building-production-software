# Plan: "order paid" consumer (reserve stock, send confirmation email)

## Consumer
- Process one message at a time per worker, with bounded concurrency; acknowledge the message only after its database transaction commits. A crash before the ack means redelivery, which the dedupe below absorbs.
- Use the order ID plus event type (for example `order_paid:<order_id>`) as the idempotency key, and make the whole handler one transaction that checks and records it.
- Set the handler timeout below the broker's visibility/ack timeout so a slow message is not redelivered while still running.
- Retry transient failures (deadlock, provider 5xx) with exponential backoff and jitter, up to a fixed attempt count, then move the message to a dead-letter queue with the error reason attached.
- Do not rely on message order. Carry a version on the event and ignore events older than the one already applied.

## Data changes
- `stock(sku, on_hand, reserved)` with CHECK constraints `reserved >= 0` and `reserved <= on_hand`, so the database itself prevents overselling.
- `reservations(order_id, sku, qty, status, actor, created_at)` with UNIQUE `(order_id, sku)`, so a redelivered event cannot create a second reservation for the same line.
- Reserve with one conditional statement: `UPDATE stock SET reserved = reserved + :qty WHERE sku = :sku AND on_hand - reserved >= :qty`. Zero rows updated means insufficient stock: record a failed reservation and do not treat it as success.
- `email_outbox(id, order_id, template, to_address, status, sent_at)` written in the same transaction as the reservation. A separate sender emails from this table and marks each row sent. A crash can then never lose the email or send one without a reservation.
- Migrations are additive and go through the migration ledger; the app role owns no tables and runs with only the grants it needs.
- A retention sweep for processed event keys (for example 90 days) so the dedupe table does not grow without limit.

## Tests (write each one failing first)
- Delivering the same order-paid message twice reserves stock once and sends one email.
- Two real Postgres connections processing the same order at the same time produce exactly one reservation; the test must fail if the conditional UPDATE is removed.
- Insufficient stock creates no reservation, records the failure, and sends no confirmation email.
- Kill the worker after the reservation commits but before the ack; on redelivery there is no double reservation and the email goes out once.
- Tests run against a real Postgres with an injected clock; only the email provider is stubbed, at its HTTP boundary.

## Operations
- Alert on queue depth, age of the oldest message, consumer lag, and dead-letter depth; track rate, error rate and duration for the consumer.
- Put the order ID in every log line and metric label so one order can be traced from the event to the email.
- Deploy the schema change before the consumer, and have the readiness check confirm the schema version the consumer needs.
- Write a runbook covering: inspecting and replaying dead-lettered messages after a fix, pausing the consumer, and rolling back.
- Run a nightly reconciliation that compares `stock.reserved` with the sum of active reservations and alerts on any drift.

Skipped for now: global ordering, a full event schema registry, and a separate relay service for the outbox (a simple polling sender is enough at this volume). Add each when a second consumer or much higher volume needs it.
