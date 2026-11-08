# Plan: "order paid" consumer (reserve stock, send confirmation email)

Scope: real customers and real stock, so this is built as a production service, not a spike. It stays lean: no event sourcing, no extra services. I list what would justify more at the end.

## Consumer

1. **Dedupe inside the DB transaction.** Add a `processed_events(event_id PK, order_id, processed_at)` table. The handler opens one transaction, inserts the event id, and reserves stock. A duplicate hits the PK conflict, so the handler skips the reservation and acks. Also key the reservation by `order_id` (unique), so a redelivery under a different message id can't double-reserve.
2. **Reserve atomically, no read-then-write.** Use `UPDATE stock SET available = available - $q WHERE sku = $s AND available >= $q`. Zero rows updated means insufficient stock. Lock SKUs in sorted order for multi-line orders to avoid deadlocks.
3. **Insufficient stock is a business outcome, not an exception.** Record the order as `backorder` or `needs_review`, then ack. Don't retry it forever and don't send the normal confirmation. Product has to decide what the customer is told.
4. **Never let the email be a dual-write.** In the same transaction as the reservation, insert an `email_outbox(order_id UNIQUE, status='pending', ...)` row. The reservation and the intent to email commit or roll back together.
5. **A separate sender drains the outbox.** It picks pending rows with `FOR UPDATE SKIP LOCKED`, sends, then marks `sent`. Use the email provider's idempotency key (the `order_id`) so a crash between send and mark can't produce two emails. If the provider has no such key, check the sent-marker before sending and accept the rare duplicate, documented.
6. **Ack only after commit.** Ack the message after the DB transaction commits. A crash before the ack means redelivery, which step 1 makes safe.
7. **Bounded retries, then dead-letter.** Retry transient errors (DB down, provider 5xx) with exponential backoff and jitter, with a maximum attempt count. Then route to a dead-letter queue carrying the error reason. Validate the payload up front, and send malformed events straight to the DLQ.
8. **Timeouts and concurrency.** The handler timeout must be shorter than the queue's visibility/ack timeout, or messages get redelivered while still running. Cap worker concurrency to stay under the DB pool size. Don't rely on message ordering; the handler must be correct for any order (a late "paid" for a cancelled order is checked against current order state).

## Data changes

9. **One additive migration, run before the code deploys.** It creates `processed_events`, the unique reservation record (`stock_reservations` with `order_id`, sku, qty, created_at), and `email_outbox`. Add `CHECK (available >= 0)` on stock so the database enforces "never oversell" even if app code is wrong. Add it `NOT VALID`, then `VALIDATE`, so it can't lock or abort on old data.
10. **Exact types and real keys.** Quantities are integers, ids have FKs, and columns are NOT NULL where the code assumes a value. Record `created_at` and the source event id on every write.
11. **Retention.** Add a nightly sweep for `processed_events` and sent outbox rows, with the retention window longer than the broker's maximum redelivery window. Otherwise old duplicates slip past dedupe.
12. **Least privilege.** The consumer connects as its own role with grants only on these tables, not as owner or superuser. Readiness checks that the schema version is present.

## Tests

13. **Write each test first and watch it fail.** The core ones:
    - same event delivered twice gives one reservation and one outbox row
    - insufficient stock gives a backorder with no email
    - a crash after commit but before ack, then redelivery, gives no double effect
    - a crash after send but before marking sent gives no second email
14. **Test the race with two real DB connections.** Two different orders competing for the last unit: exactly one wins and stock never goes negative. This test must fail if the conditional UPDATE is replaced by read-then-write. Run the same event on two workers concurrently and confirm that dedupe holds.
15. **Hermetic.** Each test owns its data, the clock is injected, and the email provider is a fake that records calls. Add one opt-in test against the provider's sandbox. Run the migration test from an empty database and again on a second run.

## Operations

16. **Structured logs with a correlation id.** Carry `event_id` and `order_id` through the consumer, outbox and sender. Log each error once, where it is handled, with context.
17. **Metrics and alerts on symptoms:**
    - queue depth and oldest-message age
    - consumer lag
    - DLQ depth (page when above zero for N minutes)
    - outbox pending age (the "paid but no email" symptom)
    - handler error rate and p95 duration
    - count of reservations that hit insufficient stock

    Each alert links to a runbook.
18. **A replay tool for the DLQ.** It's safe to use because the consumer is idempotent. The runbook covers: poison message, provider outage (outbox just backs up and drains later), and DB failover.
19. **Rollout.** Deploy the migration, then the consumer behind a flag. Shadow or run one low-volume partition first, compare reservations against orders, then ramp. Rollback is to switch the flag off; messages stay in the queue.
20. **Reconciliation job (daily).** Compare paid orders against reservations and outbox rows, and report any order with no reservation or no email. This is the safety net for bugs nobody thought of.

## Deliberately not doing now

Distributed tracing, versioned event-schema contract tests, and a full role split with a separate migrator are all deferred. I'd add them if more teams start producing or consuming these events, or if payment capture moves into this service.
