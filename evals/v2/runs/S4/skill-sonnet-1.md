# Plan: "order paid" consumer (reserve stock, send confirmation email)

Scope: a real production service with real customers and one team, so I'm planning for solid production rigor. I'm deliberately leaving out heavy extras (distributed tracing, event-schema registry, on-call game days). I note below what would add them.

## Consumer

- **Dedupe inside the DB transaction.** Add `processed_events(event_id PK, order_id, processed_at)`. Handling starts with `INSERT ... ON CONFLICT DO NOTHING`. If it inserts 0 rows, the event is a duplicate: ack it and do nothing. The stock change and the dedupe row commit together, so a crash can't leave one without the other.
- **Ack only after commit.** Ack the message once the transaction commits. A crash before the ack means redelivery, and the dedupe row absorbs it.
- **Reserve stock atomically, with no read-then-write.** Use `UPDATE stock SET available = available - :q WHERE sku = :s AND available >= :q`, and treat 0 rows updated as "insufficient stock". Write a `reservations(order_id, sku, qty)` row in the same transaction, with a unique key on `(order_id, sku)` as a second guard.
- **Decide the out-of-stock path up front.** An order that is already paid but can't be reserved must not retry forever. Mark it `needs_attention`, emit an alert, and ack. This is a business outcome, not a transient error.
- **Don't send the email inside the stock transaction.** Write an `email_outbox(order_id, kind, status, sent_at)` row in the same transaction as the reservation. A separate sender loop (or the same worker after commit) sends the email and marks the row sent. This avoids the commit-then-send gap, where a crash would silently drop the email.
- **Make the email send idempotent.** Pass the provider's idempotency key (`order_id + kind`) if it supports one. If not, check the sent-marker before sending and accept the rare duplicate email. A duplicate email is better than a missing one, and you should state that tradeoff explicitly.
- **Retry transient failures, bounded.** Use exponential backoff with jitter and a max attempt count. Validation errors (a malformed event) skip the retries and go straight to the dead-letter queue (DLQ). Store the error reason with each dead-lettered message.
- **Timeouts and concurrency.** The handler timeout must be shorter than the queue's visibility/ack timeout, or messages get redelivered while still being processed. Cap consumer concurrency to the DB pool size. Two events for the same SKU may run concurrently, and the conditional UPDATE handles that.
- **Don't rely on ordering.** Handle "order paid" arriving twice or late (for example after a cancel). Carry a version or timestamp on the event and ignore stale ones.

## Data changes

- **One additive migration.** It creates `processed_events`, `reservations` and `email_outbox`. It makes no destructive changes and leaves existing tables alone. Test it from an empty database, from a copy of production, and on a second run.
- **Let the database enforce the rules.** Add primary and foreign keys, `NOT NULL`, `CHECK (available >= 0)` on stock, and a `CHECK` list on `email_outbox.status`. Use integer quantities.
- **Deploy order.** Run the migration before the consumer code ships. The consumer's readiness check should verify the schema version it needs.
- **Least privilege.** The service connects with a role that has only the grants it needs, not as owner or superuser. Run the migration tests as that runtime role.
- **Retention.** `processed_events` and the sent outbox rows grow forever. Add a retention period (for example 30 days, longer than the broker's max redelivery window) and a nightly sweep.

## Tests

- **Write each test first and watch it fail.** The key cases:
  - Same event delivered twice gives one reservation and one email.
  - Crash after commit but before ack, then redelivery, gives no double reserve.
  - Insufficient stock goes to `needs_attention` with no negative stock.
  - Email provider failure leaves the reservation intact and the email retried.
  - Malformed event goes to the DLQ with a reason.
- **Test the race with two real DB connections.** Run two concurrent events for the last unit of a SKU, and check that exactly one wins. The test should fail if you remove the conditional UPDATE. A single-connection test only proves ordering.
- **Keep tests hermetic.** Each test owns its data, the clock is injected, and the email provider is faked at the boundary. Don't mock the handler itself. Run against a real Postgres.

## Operating it

- **Observability.** Use structured logs with the event id and order id on every line, and log each error once with context. Track rate, errors and duration per handler. Monitor queue depth, oldest-message age and consumer lag.
- **Alerts with runbooks.** Alert on DLQ depth above 0, oldest-message age above a threshold, and `needs_attention` count. Each alert links to a short runbook. Include a replay procedure for DLQ messages, which is safe because the consumer is idempotent.
- **Rollout.** Deploy behind a flag or to a small share of traffic first. Know the rollback: stop the consumer and messages wait in the queue, which is safe because the schema change is additive.

## What would add more

- Money movement in this service, or multiple teams consuming the event, would justify versioned event schemas, consumer contract tests, and a formal DLQ replay tool.
- High volume on hot SKUs would justify per-key partitioning and a load test.
