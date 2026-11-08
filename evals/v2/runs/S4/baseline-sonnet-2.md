# Plan: "order paid" consumer (at-least-once queue, Postgres stock reservation, confirmation email)

## Consumer
- Single loop: receive message, parse and validate (order_id, event_id, lines[sku, qty], customer email), process in one handler, ack only after the handler commits. Bad payloads go straight to a dead-letter queue, no retries.
- Idempotency key is the event_id (or order_id, if one paid event per order is guaranteed). Duplicates and redeliveries must be harmless.
- One DB transaction per message: insert into `processed_events(event_id pk)` with ON CONFLICT DO NOTHING. If zero rows were inserted, ack and stop. Otherwise reserve stock in the same transaction.
- Reserve stock with a conditional update: `UPDATE stock SET available = available - :q, reserved = reserved + :q WHERE sku = :s AND available >= :q`. Check the row count. Add a CHECK (available >= 0) as a backstop.
- Lock SKUs in sorted order so concurrent orders cannot deadlock. Retry on serialization or deadlock errors a few times, then nack.
- Insufficient stock is a business outcome, not an error. Record `reservations.status = 'backorder'`, roll back partial reservations for that order, and trigger a different email or a ticket. Do not retry forever.
- Email goes through a transactional outbox: in the same transaction, insert an `outbox_email(order_id unique, status='pending')` row. A separate sender loop (`FOR UPDATE SKIP LOCKED`) sends mail and marks it sent. This avoids the "committed but never emailed" and "emailed but rolled back" failures.
- Pass the order_id as an idempotency key to the email provider. A crash between send and mark-sent is then a possible duplicate email at worst, never a lost one.

## Data changes (one migration)
- `processed_events` (event_id pk, processed_at).
- `reservations` (order_id, sku, qty, status, created_at), unique on (order_id, sku).
- `outbox_email` (id, order_id unique, payload jsonb, status, attempts, sent_at, last_error).
- Add the CHECK constraint on stock and an index on outbox status for the sender.
- The migration is additive and backwards compatible, so it ships before the consumer code.

## Tests
- Unit tests for payload validation and the reservation SQL against a real Postgres (testcontainers or a CI service), not mocks.
- Idempotency: deliver the same event twice and in parallel. Assert one reservation, stock decremented once, one outbox row.
- Concurrency: many orders competing for the last units of a SKU. Assert stock never goes negative and there are no deadlocks (multi-SKU orders in opposite order).
- Failure injection: crash after the reservation but before the ack (redelivery is a no-op). Email provider down (outbox retries, order not lost). Insufficient stock (backorder path, no partial reservation).
- One end-to-end smoke test with a real broker locally: publish, consume, assert DB state and a fake SMTP/provider call.

## Operating it
- Rollout: migration first, then the consumer behind a flag with a canary of one instance. Consumers are stateless, so scale horizontally and size prefetch to a small number.
- Retries use backoff with a max attempts count, then the DLQ. Write a short runbook for replaying DLQ messages, which is safe because the handler is idempotent.
- Metrics and alerts: queue depth and oldest message age, processing latency, DLQ count above zero, backorder rate, outbox pending age, email failure rate. Logs carry event_id and order_id.
- Retention: prune `processed_events` and sent outbox rows after N days (longer than the queue's max redelivery window). Back up Postgres as usual.
