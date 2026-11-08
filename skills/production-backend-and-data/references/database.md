# Database and migrations

Use when designing a schema, writing or reviewing a migration, adding a table, column, index or constraint, setting up roles, restoring a dump.

Tiers: **T1** every project · **T2** production · **T3** high-stakes. Apply items at or below the project's tier.

## Checklist (read first)

**T1**

- [ ] Money and measurements in exact types (NUMERIC/DECIMAL or integer minor units).
- [ ] Primary keys, foreign keys and NOT NULL where the code assumes a value.

**T2**

- [ ] Schema changes only through migrations (framework or ledger tool); applied files never edited.
- [ ] Migrations guarded, idempotent, additive; tested from empty→seed, a production copy and a re-run; seed changed in the same PR.
- [ ] Schema deployed before the code that needs it; readiness checks the schema version.
- [ ] The app never connects as a superuser or table owner.
- [ ] Changeable facts append-only (revision_no, is_current, partial unique index) through one supersede helper; no unexplained ON CONFLICT DO NOTHING.
- [ ] Actor, origin and time recorded on every write.
- [ ] Retention period + nightly sweep for every growing table; raw payloads deduplicated by hash.
- [ ] EXPLAIN on realistic data for every new index; statement timeouts set per role, not server-wide.

**T3**

- [ ] Full role split: NOLOGIN owner, migrator, one role per service, break-glass superuser — with tests of ownership and grants.
- [ ] Constraints added NOT VALID then VALIDATE; migrations tested as the runtime role; restore re-creates roles.
- [ ] CHECK lists on text enums, payload_version beside JSON columns, public_id for client-facing rows.

## Rules

### 1. Use a migration ledger; applied files are immutable
- Table `schema_migrations(version, sha256, applied_at, applied_by)` and one migrate tool for every environment; one transaction per file; refuse checksum mismatches.
- Never edit an applied migration — not even a comment. Fix forward with a new file.
- **Why:** Without a ledger nobody can say what production has; edited files make two "identical" databases differ.
- **Real case:** A comment added to an old migration changed its checksum and blocked deploys everywhere.
- **Look up:** Forward-only migrations (Flyway/Liquibase style).

### 2. Write migrations that are guarded, idempotent and additive
- Open with a guard; safe to run twice; archive rows before deleting; add constraints `NOT VALID` then `VALIDATE`.
- Test from three states: empty DB → seed, restored production copy, second run.
- Change seed data in the same PR as the migration; run migration tests as the runtime role, not the owner.
- Avoid number collisions across branches: timestamps or allocate at merge.
- **Why:** Migrations meet data you have never seen, and run in environments you didn't test.
- **Real case:** A CHECK would have aborted on one old production row; a REVOKE with no grant-back broke every write but tests ran as owner.
- **Look up:** Expand/contract; idempotency.

### 3. Schema first, code second, readiness checks the schema
- Deploy additive schema before the code that uses it; destructive steps come later.
- The readiness probe verifies the schema version the code needs.
- **Why:** A green health check with a broken write path is worse than a red one.
- **Real case:** Every edit returned 500 while /health stayed green because a migration hadn't run.
- **Look up:** Readiness vs liveness.

### 4. Least-privilege roles from day one
- Owner (NOLOGIN), migrator (member of owner), one role per service with explicit grants, break-glass superuser.
- Test that nothing is owned by a superuser and grants are exactly as expected; audit tables are INSERT/SELECT only.
- **Why:** A superuser app can disable the triggers that protect your audit trail.
- **Real case:** Container images create the first user as superuser; one such role did everything for months.
- **Look up:** Principle of least privilege.

### 5. Changeable facts are append-only
- `revision_no` + `is_current` + a partial unique index `WHERE is_current`; one `supersede()` helper for every writer.
- `supersede()` = one function (app code or a SQL function), one transaction: lock the key, re-check the expected current revision (409 if it moved), set the old row `is_current = false` with `superseded_at`, insert revision + 1 with actor, origin and `valid_from`.
- Never `ON CONFLICT DO NOTHING` on a business key without writing down why losing that data is fine.
- Re-read the window a source can still revise; backfills are idempotent (second run → zero changes).
- **Why:** Sources restate, users correct, and audits ask what was true last Tuesday.
- **Real case:** A DO NOTHING silently dropped a changed rate; a 4-year re-check found 14 restatements and 896 missing rows.
- **Look up:** SCD type 2; bitemporal data.

### 6. One fact in one place, keyed by real identity, with actor and origin
- Before adding a table, check whether a view answers the need.
- Unique keys come from what distinguishes rows in reality (URL, content hash).
- Every write stores origin, actor and time; never infer provenance from side effects (e.g. "revision > 1 means user-typed").
- **Why:** Duplicated facts drift; inferred provenance lies.
- **Real case:** Weights in three drifting columns; documents keyed by month dropped the second document of a month.
- **Look up:** Normalisation; data lineage.

### 7. Let the database enforce rules
- Identity PKs, FKs on every reference, CHECK lists on text enums, NOT NULL where code assumes values.
- `payload_version` beside every JSON column; a `public_id` for anything clients see.
- **Why:** Application checks get bypassed; constraints don't.
- **Real case:** A free-text parameter stored rows no feature could ever reach again.
- **Look up:** Defensive schema.

### 8. Retention and dedupe before launch
- Every growing table has a retention period and a nightly sweep.
- Hash raw payloads and insert only when changed; don't log no-op runs.
- **Why:** Logs and raw captures quietly become most of your database.
- **Real case:** 80% of a database was one payload re-stored every five minutes.
- **Look up:** Data retention; content addressing.

### 9. Indexes match predicates — prove it
- `EXPLAIN (ANALYZE, BUFFERS)` on realistic data for each new index; paste the plan in the PR.
- Batch queries; look for N+1 before blaming the database; drop redundant indexes; enable `pg_stat_statements`.
- **Why:** An index the planner can't use is pure write cost.
- **Real case:** `IS NOT DISTINCT FROM` defeated a new index; a 52 s page was thousands of single-row round trips.
- **Look up:** Sargable predicates; N+1.

### 10. Dumps don't contain roles; rehearse restores
- Roles and other cluster objects live outside `pg_dump`; every restore re-runs role/ownership setup.
- CI restores the same way the runbook does; rehearse on throwaway clusters.
- **Why:** A restore that "works" can leave you with no roles and superuser-owned tables.
- **Real case:** A CI restore marked migrations as applied that created roles: 16, then 21 failures.
- **Look up:** Disaster-recovery drills.

