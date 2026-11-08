# Plan: "order paid" consumer (stock reservation + confirmation email)

Assumes real customer and stock data, so build it production-grade. If the message carries card data or more personal data than order and email details, tighten security before building.

## Consumer
- Ack only after the database transaction commits. A crash before ack means redelivery, which the idempotency below absorbs.
- Validate the payload at the edge (schema, version, integer quantities). Invalid payloads go straight to the dead-letter queue with the reason; they are not retried.
- Retry transient failures (DB timeout, email provider 5xx) with exponential backoff and jitter, max 5 attempts, then dead-letter with the error attached.
- Handler timeout below the broker's ack/visibility timeout, so one message is never worked by two consumers at once. Start with one worker; raise concurrency after a load test.

## Data changes
- `processed_messages(message_id PK, processed_at)`: first statement in the reservation transaction. A conflict means "already done": ack and stop.
- `stock(sku PK, on_hand, reserved)` with `CHECK (reserved >= 0)` and `CHECK (reserved <= on_hand)`, so the database refuses overselling even if app code is wrong.
- `reservations(order_id, sku, qty, status, reason, PK(order_id, sku))`: one row per order line, so a redelivered order cannot reserve twice.
- Reserve each line with one conditional update: `UPDATE stock SET reserved = reserved + $qty WHERE sku = $sku AND on_hand - reserved >= $qty`. Zero rows updated means insufficient stock. No read-then-write.
- All lines of an order reserve in one transaction (all or nothing), with SKUs locked in sorted order to avoid deadlocks between orders sharing items.
- Insufficient stock is a visible outcome (`status = 'rejected'`, with reason), not a silent success or a retry loop. Decide what the customer gets (backorder, notify, cancel) before launch.
- `email_outbox(id PK, order_id, template, recipient, status, attempts, sent_at)` is written in the same transaction as the reservation. Email is never sent inside the transaction.
- Retention: keep `processed_messages` longer than the broker's maximum redelivery window, or a late duplicate slips through. Purge sent outbox rows after a set period.
- Cancel/refund events must release reservations, or stock leaks. Confirm that event exists before building the release path.

## Email
- A separate outbox sender picks unsent rows and sends with the provider idempotency key set to the outbox id, then marks the row sent. A crash between send and mark resends at most once, and the provider drops the duplicate.

## Tests (each one seen failing first, against real Postgres)
- The same message delivered twice gives one reservation, one stock decrement, one outbox row.
- Two real connections race for the last unit: exactly one succeeds. Removing the conditional update makes this fail.
- A crash after commit but before ack, then redelivery, changes nothing.
- Email provider down: the reservation stays committed, the outbox row retries, and no duplicate is sent after recovery.
- Poison payload goes to the dead-letter queue with its reason. Clock injected so backoff is deterministic.

## Operations
- Alerts on queue depth, oldest-message age, consumer lag, dead-letter depth and outbox backlog age, each with a runbook link.
- Structured logs carry message_id and order_id on every line. Errors are logged once, where handled.
- A dead-letter replay tool, safe to re-run because of the idempotency. The runbook says to read the reason before replaying.
- The app connects as a least-privilege role (not owner, not superuser), with a statement timeout set on that role.
- Rollout: deploy the schema first, then the consumer at one worker. Watch lag and error rate, then scale. Rollback means stopping the consumer; messages wait in the queue.
