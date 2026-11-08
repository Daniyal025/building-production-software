# Order-paid consumer: plan

Scope: this service is production (real orders, real stock, more than one developer), so the plan covers production-level safeguards. It would need more if the reservation started touching payments or a second service.

## Consumer

- Handle each message in one database transaction: check the processed-events table, reserve stock, record the outcome, then commit. Only acknowledge the message after the commit. A redelivery after a crash is then harmless.
- Use a dedupe key of `order_paid:<order_id>` with a unique constraint, inserted in the same transaction as the stock change, so a duplicate delivery finds the row and does nothing.
- Set the handler timeout below the broker's visibility or ack timeout, so a slow message is not redelivered while it is still running.
- Cap consumer concurrency at a fixed worker count so one slow database does not pile up unacknowledged messages.
- Retry transient errors (database connection, provider timeouts) with exponential backoff and jitter, up to a fixed attempt count.
- Send messages that exhaust retries, or that fail validation (unknown SKU, bad schema), to a dead-letter queue with the payload and the reason. Do not retry validation failures.

## Data changes

- Add a `processed_events` table: `event_key` primary key, `received_at`, `outcome`. Add a nightly sweep that deletes rows older than the broker's maximum redelivery window plus a margin.
- Add a `stock_reservations` table: unique `(order_id, sku)`, `qty` with a CHECK that it is greater than zero, a foreign key to the order and product, and a status column.
- Reserve stock with one guarded statement: `UPDATE stock SET reserved = reserved + $qty WHERE sku = $1 AND on_hand - reserved >= $qty`. Zero rows updated means insufficient stock; record that outcome visibly. Do not read, check in Python, then write.
- Send the confirmation email after the reservation commits, driven by an outbox row (`email_status`, `sent_at`). The send uses the provider's idempotency key set to the order id, and the outbox row is marked sent only after the provider accepts. A crash between reserve and send then leaves a retryable row, not a lost email.
- Ship the schema migration before the consumer code. Keep it additive and guarded so it can run twice. Test it on an empty database and on a restored copy of production data.
- The service connects as a least-privilege role, not the table owner or a superuser, with grants only on the tables it writes.

## Tests (each one watched failing first)

- Delivering the same `order_paid` event twice reduces stock once and sends one email.
- Two real database connections process the same order at the same moment; the stock is reserved once. Removing the lock or the unique constraint must make this test fail.
- Insufficient stock produces a visible failed outcome, sends no confirmation, and is not acknowledged as a success.
- Email goes to a fake provider in tests, with no network in CI. Backoff tests use an injected clock. CI keeps a known-failure baseline and never relaxes a gate to go green.

## Operations

- Dashboards and alerts: consumer rate, error rate and p95 duration; queue depth and oldest-message age; dead-letter queue depth. Alert when the dead-letter queue is non-empty or the oldest message is older than the agreed limit. Each alert links to a runbook.
- Structured logs carry `order_id` as the correlation id. Log each failure once, where it is handled, with context.
- The runbook covers inspecting the dead-letter queue, pausing the consumer first to stop the damage, fixing the cause, then replaying with a replay tool. Mitigate before root-causing.
- Roll out behind a flag so the consumer can be paused without a deploy. Add an external check and a "is it working" view that includes data freshness, such as time since the last processed order.
- Any serious incident gets a blameless postmortem; each action gets an owner and a date and becomes a test or an alert.
