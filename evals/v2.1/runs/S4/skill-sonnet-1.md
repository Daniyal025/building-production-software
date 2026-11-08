# Plan: "order paid" consumer (reserve stock + send confirmation email)

Assumption: real customers and real stock, so production-grade, not high-stakes. Moves up a notch if payments or regulated data flow through this service, or if it grows to several consuming services.

## Consumer

- **Dedupe inside the stock transaction.** In one Postgres transaction, `INSERT INTO processed_events (event_id PRIMARY KEY, order_id, processed_at) ON CONFLICT DO NOTHING`. If zero rows were inserted, it is a redelivery: ack and stop. If inserted, reserve stock in the same transaction. Commit, then ack.
- **Business-key backstop.** Put a unique constraint on `stock_reservations (order_id, sku)`. A producer that re-publishes the same order under a new event id still cannot reserve twice.
- **Atomic, race-free reservation.** Use `UPDATE stock SET available = available - :qty WHERE sku = :sku AND available >= :qty`. Check the rowcount; never read-then-write. Lock SKUs in a consistent order within an order to avoid deadlocks.
- **Insufficient stock is an outcome, not an exception.** Record the reservation as `backorder` or `failed` with a reason and emit or alert for it. Don't retry it forever, and don't silently drop it.
- **Ack only after commit.** Set the handler timeout well below the queue's visibility timeout. Bound the consumer's concurrency to what the DB pool can serve.
- **Retries and dead-letter queue.** Retry transient errors (DB, network) with exponential backoff and jitter, up to a maximum attempt count. Send poison messages (bad schema, unknown SKU) to a DLQ with the error attached, and keep a small replay script.
- **Validate the payload at the boundary.** Parse the quantity and money fields as Decimal or integers. An unparseable event goes to the DLQ with a visible reason. It never becomes a default of 0.

## Email

- **Don't send inside the DB transaction.** Insert an `email_outbox` row (`order_id` unique, status `pending`) in the same transaction as the reservation. A separate sender loop (`SELECT ... FOR UPDATE SKIP LOCKED`) sends pending rows and marks them `sent`.
- **Cover the crash window.** A crash between "provider accepted" and "mark sent" can still produce a duplicate. Pass `order_id` as the email provider's idempotency key if it supports one. If it doesn't, accept a rare duplicate confirmation and document that decision.
- **Email failure never rolls back stock.** The sender retries with a bounded backoff. After the limit the row is marked `failed` and alerts.

## Data changes

- **Forward-only, backwards-compatible migrations.** New tables: `processed_events`, `stock_reservations`, `email_outbox`, each with its constraints and an index on `status`. Add them with additive migrations and never edit one once applied.
- **Rollout order.** Deploy the migration first, then the code. A `CHECK (available >= 0)` on stock gives the database the last word against overselling. Backfill existing rows before enforcing it.

## Tests

- **Write each test, watch it fail, then make it pass.** Run against a real Postgres, not mocks, because the guarantees live in the constraints and locking.
- **Core cases:**
  - The same event delivered twice gives one reservation and one outbox row.
  - Two events for the same order with different event ids still give one reservation.
  - A crash after the DB commit but before the ack, then redelivery, causes no double effect.
  - Concurrent orders for the last unit: exactly one wins and stock never goes negative.
  - A malformed payload lands in the DLQ with a reason.
  - An email provider outage leaves the reservation intact and the email retried.
- **Contract test.** Pin the event schema fixture that the producer sends, so a field rename breaks CI instead of production.

## Operations

- **Structured logs.** Carry `event_id` and `order_id` on every line, and log each error once, where it is handled.
- **Metrics and alerts.** Track processed rate, error rate, handler duration p95, queue depth, age of the oldest message, DLQ depth, and email outbox age. Alert on a DLQ depth above 0, a growing oldest-message age, and outbox rows pending longer than a few minutes. Each alert links to a runbook.
- **Runbook, short.** Cover how to inspect and replay a DLQ message, how to resend a stuck email, and how to release a wrongly held reservation through the same guarded function. No ad-hoc SQL on stock.
- **Retention.** Prune `processed_events` after longer than the queue's maximum redelivery window (for example 30 days), never sooner.
