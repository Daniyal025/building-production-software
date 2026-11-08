# S2 with skill — claude-sonnet-5-5

**Plan: Nightly central-bank FX rate ingest (Python + Postgres)**

*Schema*
1. `fx_rate` — append-only, keyed by natural identity: `id`, `rate_date`, `base_ccy`, `quote_ccy`, `rate NUMERIC(18,8) NOT NULL`, `revision_no`, `is_current`, `valid_from`, `superseded_at`, `source_run_id` FK, `source_sha256`. Partial unique index `(rate_date, base_ccy, quote_ccy) WHERE is_current`; CHECK `rate > 0`.
2. One `supersede()` function is the only writer: in one transaction, lock the key, compare incoming vs current; if equal do nothing, if different set `is_current=false, superseded_at=now()` and insert `revision_no+1`. No `ON CONFLICT DO NOTHING` — a bank revision must never be silently dropped, and "what was the rate as of last Tuesday" stays answerable.
3. `fx_ingest_run(id, started_at, finished_at, status ['ok','failed','not_published'], raw_sha256, rows_parsed, rows_inserted, rows_revised, error, layout_version)` — the parser's error text is stored on the run row.
4. `fx_raw_payload(sha256 PK, fetched_at, bytes)` — raw CSV stored deduped by hash so a parser fix can replay history.
5. Migration: new numbered file, guarded, idempotent, additive; tested on an empty DB, a copy of real data, and run twice — as the runtime role. The job's DB role gets only the grants it needs.
6. Rates are `Decimal` from the CSV text straight into `NUMERIC` — never float; reject NaN/inf/non-positive.

*Job*
7. A single script (`python -m app.jobs.fx_ingest`) triggered by cron or the existing scheduler. Take a Postgres advisory lock so two runs can't overlap; reap runs left `running` for more than N minutes; handle SIGTERM by finishing or rolling back the transaction.
8. One HTTP client with timeout, retry with backoff on transient errors only, TLS verification on. Save the raw bytes first; if the hash is unchanged, skip parsing. If the bank hasn't published today's file (404 / no row for the expected date) the run is `not_published` — quiet at first, but it counts toward the staleness alert.
9. The parser finds columns by header text, not position; normalise encoding, BOM, delimiter, decimal comma and date format explicitly. Every required column must be present — otherwise the run fails with the missing header named. Unknown extra columns are logged, not fatal.
10. Plausibility checks before writing: a rate moving more than X% day-on-day, or fewer rows than the last good run, fails the run and writes nothing. Thresholds are recorded as a decision next to the code.
11. Each run re-reads the full file (or at least the last N days the bank may still revise) and passes every row through `supersede()`; backfills are idempotent (second run → zero changes). The whole file is applied in one transaction, so a bad file leaves the previous data intact.
12. Zero parsed rows → failed run. A failure must never be stored as a value; a missing day stays missing, never filled with yesterday's rate.

*Tests* (each seen failing first)
13. One saved real CSV fixture per layout, plus a changed layout (renamed/reordered column, new delimiter, decimal comma) — the layout-change case must fail loudly naming the header.
14. Revision test: ingest the same date with a new value → two rows, one current, `revision_no=2`, history queryable; re-ingest the same file → zero changes.
15. Race test: two real connections on one key — the advisory lock and the partial unique index hold ("would this fail if I deleted the lock?").
16. Failure-mode tests: zero rows, truncated file, 500, 404, wild value — each leaves the DB unchanged and records a failed/`not_published` run with a message. Clock injected; no network; each test owns its data.

*Knowing if it breaks*
17. The job pings a dead-man's switch (healthchecks.io style) on success and on failure — a run that never starts is caught because the ping doesn't arrive.
18. A freshness query (`max(rate_date)` of current rows vs the expected business day) is exposed on `/health/data` or an ops page; alert when data is overdue or after N consecutive failed/`not_published` runs. `/health` itself stays cheap and never raises.
19. JSON logs with one line per run (counts, `layout_version`, `raw_sha256`); alert on an unusually high revision count (it can mean a parser misread or a big bank restatement).

*Rollout*
20. Ship the migration first, then the job. Dry run against a dev DB, then one manual prod run. A short runbook (how to replay from `fx_raw_payload` after a parser fix, how to check freshness), with every command in it executed once before merge; docs updated in the same commit.
