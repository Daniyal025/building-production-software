# Plan: "order paid" consumer (reserve stock + confirmation email)

## Consumer
- Ack the message only after the database transaction has committed. Never ack first.
- Set the handler timeout below the broker's visibility/ack timeout, so a slow message is not redelivered while it is still running.
- Cap concurrency per worker, and cap total workers against the Postgres pool size.
- Validate the payload at the boundary (required fields, order id, quantities as integers, amounts as strings). A malformed message goes straight to the dead-letter queue with the reason. It is not retried.
- Retry transient failures (DB unavailable, provider 5xx) with exponential backoff and jitter, up to a fixed attempt count. Then dead-letter with the error and the original payload.
- Use the order id as the business key. If the event carries a version or timestamp, ignore events older than the one already applied for that order.

## Data changes
- `processed_events(event_key PK, order_id, processed_at)`. Insert it in the same transaction as the reservation. A duplicate insert means the work is already done, so skip it.
- `inventory(sku PK, on_hand, reserved)` with `CHECK (reserved >= 0 AND reserved <= on_hand)`. The database refuses an oversell even if the code has a bug.
- Reserve with one guarded `UPDATE inventory SET reserved = reserved + $qty WHERE sku = $sku AND on_hand - reserved >= $qty`, and check the row count. No read-then-write.
- `stock_reservations(order_id, sku, qty, status, reason, created_at)` with `UNIQUE (order_id, sku)` and `CHECK (qty > 0)`. Write the reserved or rejected status, with the reason, in the same transaction.
- Decide the policy for a partial shortage (all-or-nothing per order is the safer default). Confirm it with the product owner before coding.
- `email_outbox(order_id, template, status, attempts, sent_at, provider_message_id)`, written in the same transaction as the reservation. A separate sender does the sending, so no email is sent inside the database transaction. Pass `order_id + template` as the provider's idempotency key.
- Record actor, origin and time on every write. Give the consumer its own database role with grants only on these tables. It must not be a superuser or table owner.
- Nightly sweep of `processed_events` after a retention period longer than the broker's redelivery window.

## Tests (real Postgres, no mocks of the reservation logic)
- Write the duplicate-delivery test first and watch it fail: the same event twice must reserve stock once and queue one email. Then add the guard.
- Race test with two real connections: two orders competing for the last unit must not oversell. It must fail if the guarded UPDATE is replaced by read-then-write.
- Failure injection: the email provider returns 5xx, and the database drops mid-transaction. Expect no ack, a redelivery, no duplicate email and no partial reservation.
- Poison-message test: a malformed payload lands in the dead-letter queue with its reason.
- Each test owns its data and injects the clock. No test depends on today's date or the developer's shell.

## Operations
- Metrics per handler: rate, error rate, p50/p95/p99 duration. Queue depth, oldest-message age and dead-letter depth. Alert on oldest-message age and dead-letter growth, each with a runbook link.
- Structured logs carrying order id and message id as the correlation id. Log each failure once, where it is handled.
- A runbook for the dead-letter queue: inspect, fix, replay. Replay is safe because the consumer is idempotent.
- Monitor the email outbox backlog age and failed sends separately from the consumer.
- Deploy the additive schema first, then the consumer. Readiness checks the schema version.
- A "paid orders confirmed on time" dashboard, so stale data is visible to users.
