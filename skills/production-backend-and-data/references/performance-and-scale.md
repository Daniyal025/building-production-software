# Performance and scale

Use when a page or endpoint is slow, adding caching, pagination or background processing, preparing for more users or data, load testing, or setting performance budgets.

Tiers: **T1** every project · **T2** production · **T3** high-stakes. Apply items at or below the project's tier.

## Checklist (read first)

**T1**

- [ ] Measure before optimising: profile one real request end to end.

**T2**

- [ ] Every list endpoint paginated with a maximum page size; request body size capped.
- [ ] Performance budget per user action, tracked at p95/p99, not averages.
- [ ] Query count per request asserted in tests for hot paths (catches N+1).
- [ ] Slow work moved to background jobs (202 + status) instead of long requests.
- [ ] Caches have explicit invalidation; stampede protection (single-flight, jittered TTL).

**T3**

- [ ] Load test critical paths with production-like data volumes before launch; know the knee and keep headroom.
- [ ] Keyset (cursor) pagination for large tables; capacity plan revisited each quarter.

## Rules

### 1. Budgets at the tail, measured not guessed
- Set a budget per user action at p95/p99; profile one real request end to end before changing code.
- Assert query counts per request in tests for hot paths.
- **Why:** Most slowness is your own code doing repeated work, and averages hide it.
- **Source:** Industry practice — Google SRE book ch. 4 (latency SLIs); Django/SQLAlchemy query-count assertions.
- **Look up:** Tail latency; N+1 detection.

### 2. Bound every list and every body
- Pagination with a maximum page size on every list endpoint; keyset (cursor) pagination for large tables.
- Cap request body sizes and upload sizes.
- **Why:** Unbounded endpoints are how one client takes the service down.
- **Source:** Industry practice — Use The Index, Luke (keyset pagination); OWASP API Security Top 10 (API4: unrestricted resource consumption).
- **Look up:** Keyset pagination; resource limits.

### 3. Move slow work off the request path
- Return 202 with a status resource; do the work in a bounded job queue.
- Make the job idempotent and observable.
- **Why:** Long requests tie up workers and time out at proxies.
- **Source:** Industry practice — Microsoft Azure Architecture Center: Asynchronous Request-Reply pattern.
- **Look up:** Async request-reply.

### 4. Cache with an invalidation story
- Every cache states its key, its invalidation trigger and its maximum staleness.
- Protect against stampedes: single-flight, jittered TTLs, serve-stale-while-revalidate.
- **Why:** Caches without invalidation serve wrong data; caches without stampede protection fall over on expiry.
- **Source:** Industry practice — RFC 5861 (stale-while-revalidate); "Cache stampede" literature (XFetch).
- **Look up:** Cache invalidation; thundering herd.

### 5. Load test before launch
- Test critical paths with production-like data volumes; find the knee of the latency curve; keep headroom.
- Re-run after major changes; revisit capacity each quarter.
- **Why:** The first real load test should not be launch day.
- **Source:** Industry practice — Google SRE book ch. 18 (load testing); k6/Locust documentation.
- **Look up:** Capacity planning; load testing.

