# Backend and concurrency

Use when writing API routes, business logic, caching, background jobs or schedulers; handling money, rates, dates or units; anything with locks, pools, retries or concurrent users.

## Checklist (read first)

- [ ] Decimal/NUMERIC, strings in JSON, non-finite rejected, dates parsed.
- [ ] Units in names; ambiguous values refused with a fix message.
- [ ] Missing → missing; fallbacks defined, tested, logged.
- [ ] Per-series latest; boundary tests.
- [ ] Cache key = inputs + code hash + date; invalidation test per write path; immutable cache values.
- [ ] Generated/validated API types; unknown params 422; one error envelope; JSON logs with request id.
- [ ] Lock → re-check → compute; one guarded write path; If-Match/409; Idempotency-Key.
- [ ] Narrow WHERE; lock order; transient-only retries; timeouts.
- [ ] Pool formula tested; bounded executors; finally; no transactions across network calls.
- [ ] Jobs: DB cadence, per-job lock, stale-run reaping, SIGTERM.

## Rules

### 1. Exact numbers and real types
- Decimal from source text to NUMERIC; strings in JSON; floats only for display.
- Reject NaN/Infinity at the boundary; parse dates before comparing.
- **Why:** Binary floats can't represent most decimals; errors compound and create phantom changes.
- **Real case:** A rate came out 0.010000000000000009; dates compared as strings sorted 2029-5-1 after 2029-06-01.
- **Look up:** Floating-point error; parse, don't validate.

### 2. Units are explicit; ambiguity is refused
- Put the unit in field names and schemas (`pct_fraction`, `rate_bp`); range-check on the server.
- Range bounds come from the domain owner and are recorded as a decision next to the code — don't invent them silently.
- When a value has two readings, refuse with a message that says how to fix it.
- **Why:** Guessing the unit is how 2.1% becomes 210%.
- **Real case:** An assistant sent 2.1 for 2.1% and staged a 210%-a-month change.
- **Look up:** Unit normalisation.

### 3. Missing in, missing out
- Missing or failed inputs propagate as missing, shown with a mark.
- A fallback exists only if the domain defines it, a test pins it and a log records it.
- **Why:** A plausible wrong number is the most dangerous output a system can produce.
- **Real case:** Missing drivers silently became 0% changes; a formula error rendered as 0.
- **Look up:** Fail fast; silent data corruption.

### 4. Compute "latest" per series and test boundaries
- Latest-actual and start dates per series, never a max across mixed series.
- Test: one series ahead of another, the first forecast period, a forward-dated announcement.
- **Why:** Real data arrives unevenly.
- **Real case:** A value published ahead of the rest of its month made that month look complete and emptied a projection.
- **Look up:** Ragged-edge data; off-by-one.

### 5. Cache keys cover data, code and time; cached values are immutable
- Key = everything the computation reads + a hash of the code + the date if logic reads today().
- One test per write path proves it invalidates the cache; return copies or frozen objects.
- **Why:** Stale caches are silent; manual version bumps get forgotten or collide on merge.
- **Real case:** A cache missed an input four separate times; a forgotten version bump served 1.30% instead of 0.39%.
- **Look up:** Cache invalidation; content addressing.

### 6. Separate compute from presentation
- A request that only changes the look re-renders the last result.
- Cache pure reads by canonical arguments + data version; never cache side effects.
- **Why:** Recomputing for formatting is slow and can change the numbers.
- **Real case:** "Remove the chart" re-ran a slow, non-deterministic computation.
- **Look up:** MVC; memoisation.

### 7. One API contract and one error shape
- Generate client types from OpenAPI or validate with zod; unknown query parameters are 422 in dev/test.
- One error envelope `{code, message}`; anticipated conditions are 4xx with a code; a 500 means a bug.
- Typed request models; commit transactions in routes only; JSON logs with request ids.
- **Why:** Hand-written clients drift silently; mixed error shapes hide the server's reason from users.
- **Real case:** The UI sent `start/end`, the server read `from/to`: every range was ignored with no error.
- **Look up:** Contract testing; RFC 7807.

### 8. Lock, re-check, compute
- Take the lock first, re-check the work is still needed, compute, in one transaction.
- Keep long reads out of write locks.
- **Why:** Check-then-lock is a race.
- **Real case:** A freshness check ran before the lock; inputs could change in between.
- **Look up:** TOCTOU.

### 9. One guarded write path; optimistic concurrency; idempotency
- Every mutation of a resource goes through one function (validate, authorise, lock, version-check, audit).
- ETag/revision on read, `If-Match` on write, 409 on mismatch; Idempotency-Key on POSTs.
- **Why:** Second write paths were the most expensive bug class in one review.
- **Real case:** Fill and undo bypassed the guard and silently overwrote concurrent edits.
- **Look up:** Optimistic locking; choke point.

### 10. Narrow scope, one lock order, retry only transient errors
- Every "my state" UPDATE filters by user/session/document.
- Document a lock order and follow it; retry deadlocks/serialisation failures; every wait has a timeout.
- **Why:** Broad updates leak across users and deadlock.
- **Real case:** An undo journal shared across sheets reverted edits users couldn't see.
- **Look up:** Lock ordering; deadlock avoidance.

### 11. Bound every resource
- Pool ≥ request threads + long-held consumers (streams, workers) — assert it in a test.
- Bounded executors; release in `finally`; every loop states its exit; no transaction across network I/O; timeouts per role.
- **Why:** Unbounded things fail under load, at night.
- **Real case:** A pool equal to thread count ignored 20 streaming sessions; a failed rollback leaked connections until restart.
- **Look up:** Resource exhaustion; bulkheads.

### 12. Jobs survive restarts and run twice safely
- Cadence from the DB, a per-job advisory lock, reap stale "running" rows at startup, handle SIGTERM, one timezone-aware clock.
- Delete steps that have no observable effect.
- **Why:** Schedulers restart; in-memory state doesn't.
- **Real case:** A restart ran all scrapers at once; killed runs stayed "running" forever.
- **Look up:** Thundering herd; idempotent jobs.

### 13. Declare dependencies and test the built artefact
- Import smoke test inside the built image; build for the target CPU architecture.
- **Why:** Your venv lies about what production has.
- **Real case:** An undeclared lazy import worked only because the package happened to be installed locally.
- **Look up:** Hermetic builds.

