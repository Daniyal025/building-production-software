# Plan: "order paid" consumer (at-least-once, Postgres stock reservation, confirmation email)

## Core idea
At-least-once delivery means duplicates and redeliveries are normal. Make the handler idempotent: the DB is the source of truth for "already done", and the email is sent through a transactional outbox so a crash cannot lose or double it.

## Consumer
- One long-running worker process: poll/subscribe, handle one message at a time per worker, scale by adding workers (partition or competing-consumer key = order_id so one order is never handled concurrently).
- Parse and validate the payload (order_id, event_id, line items: sku, qty). Malformed messages go straight to a dead-letter queue (DLQ), not retried forever.
- Ack only after the DB transaction commits. Never ack before; a crash then just causes a redelivery.
- Retry transient failures (DB timeout, deadlock) with exponential backoff and jitter, capped at N attempts, then DLQ. Business failures (insufficient stock) are not retried; they are recorded as an outcome.
- Graceful shutdown on SIGTERM: finish the in-flight message, then exit.

## Data changes (one migration, additive and backward compatible)
- `processed_events(event_id PK, order_id, processed_at)`: insert with `ON CONFLICT DO NOTHING` as the first statement in the transaction; zero rows inserted means duplicate, so ack and skip.
- `stock_reservations(order_id, sku, qty, status, PRIMARY KEY(order_id, sku))`: unique key is a second idempotency guard.
- Reserve with a conditional update: `UPDATE stock SET available = available - :q WHERE sku = :s AND available >= :q`; if 0 rows updated, mark the order `backorder/failed` rather than going negative. Add `CHECK (available >= 0)` as a backstop. Lock rows in sorted SKU order to avoid deadlocks.
- `email_outbox(id, order_id UNIQUE, to_addr, template, status, attempts, sent_at)`: inserted in the same transaction as the reservation, so "reserved" and "email owed" commit atomically.

## Email
- A separate sender loop reads pending outbox rows (`FOR UPDATE SKIP LOCKED`), sends, then marks sent. Pass the order_id as the provider's idempotency key if supported, so a crash between send and mark does not double-send (otherwise accept rare duplicate emails and document it).
- Email provider outages never block stock reservation; the outbox just backs up and drains later.

## Tests
- Unit: payload validation, reservation logic, insufficient-stock path.
- Integration against real Postgres (testcontainers or CI service): same event delivered twice yields one reservation and one outbox row; concurrent delivery of the same event from two workers; two orders racing for the last unit never oversell.
- Failure injection: crash after commit but before ack (redelivery is a no-op); email provider failing then recovering; poison message ends up in the DLQ.
- Migration test: applies cleanly on a copy of production-shaped data and is safe to roll back.

## Operations
- Metrics and alerts: queue depth and age of oldest message, processing latency, retry and DLQ counts, outbox backlog age, stock-reservation failure rate. Alert on DLQ above zero and on a growing oldest-message age.
- Structured logs with event_id and order_id on every line for tracing.
- DLQ runbook: inspect, fix the cause, replay (safe because the handler is idempotent). Retention on `processed_events` (e.g. prune after 30 days, longer than the queue's maximum redelivery window).
- Rollout: deploy migration first, then consumer behind a flag or on a canary worker; keep the old path until the new one matches; rollback is stopping the consumer, since messages stay queued.
