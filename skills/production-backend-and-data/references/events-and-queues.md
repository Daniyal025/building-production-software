# Events, queues and background work

Use when building message consumers or producers, queues, webhooks handlers, outbox/event publishing, retries, dead-letter queues or async workflows.

Tiers: **T1** every project · **T2** production · **T3** high-stakes. Apply items at or below the project's tier.

## Checklist (read first)

**T1**

- [ ] Consumers idempotent: dedupe on a message/business key or natural-key upsert.
- [ ] Never "commit then publish" as two independent steps without a recovery path.

**T2**

- [ ] Transactional outbox (or CDC) so state changes and events can't diverge.
- [ ] Bounded retries with exponential backoff + jitter, then a dead-letter queue with the reason; DLQ depth alerted.
- [ ] Handler timeout shorter than the visibility/ack timeout; bounded consumer concurrency.
- [ ] Queue depth and oldest-message age monitored; consumer lag alerted.
- [ ] Side effects outside the DB (email, payments) keyed for idempotency at the provider or guarded by a sent-marker.

**T3**

- [ ] Ordering relied on only per key/partition; events carry a version; consumers tolerate out-of-order.
- [ ] Versioned event schemas, additive changes only; consumer contract tests; a replay tool for the DLQ.

## Rules

### 1. Assume at-least-once delivery: make every consumer idempotent
- Dedupe on a message id or business key (processed-message table, or a natural-key upsert) inside the same transaction as the state change.
- Side effects outside the database (email, payment) use the provider's idempotency key or a sent-marker row checked before sending.
- **Why:** Every mainstream broker can redeliver; exactly-once is a property you build, not one you get.
- **Source:** Industry practice — Enterprise Integration Patterns (Idempotent Receiver); AWS SQS and Kafka delivery semantics docs.
- **Look up:** Idempotent receiver; at-least-once delivery.

### 2. Never dual-write: use a transactional outbox
- Write the event row in the same transaction as the state change; a relay publishes it and marks it sent.
- Or use change-data-capture from the database log.
- **Why:** "Commit then publish" loses events on a crash between the two; "publish then commit" announces things that never happened.
- **Source:** Industry practice — microservices.io Transactional Outbox; Debezium outbox pattern.
- **Look up:** Transactional outbox; dual-write problem.

### 3. Bound retries, then dead-letter with a reason
- Exponential backoff with jitter; a maximum attempt count.
- Then a dead-letter queue carrying the error; alert on DLQ depth; keep a replay tool.
- **Why:** Poison messages otherwise block the queue or burn cost forever.
- **Source:** Industry practice — AWS Architecture Blog "Exponential backoff and jitter"; broker DLQ documentation.
- **Look up:** Poison message; dead-letter queue.

### 4. Respect timeouts and ordering limits
- Handler timeout < visibility/ack timeout, or the message is redelivered while still being processed.
- Rely on ordering only per key/partition; give events a version and let consumers ignore older versions.
- **Why:** Global ordering doesn't exist at scale; overlapping redelivery causes duplicate work.
- **Source:** Industry practice — Kafka partition ordering guarantees; SQS visibility timeout docs.
- **Look up:** Visibility timeout; per-key ordering.

### 5. Make queues observable and contracts explicit
- Monitor depth, age of the oldest message and consumer lag.
- Version event schemas; only additive changes; consumer contract tests.
- **Why:** A growing queue is the earliest sign of an outage; a silent schema change breaks consumers you don't own.
- **Source:** Industry practice — Google SRE Workbook (monitoring pipelines); Pact consumer-driven contracts.
- **Look up:** Consumer lag; schema evolution.

