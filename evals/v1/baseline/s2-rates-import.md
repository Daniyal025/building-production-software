# S2 baseline (no skill) — claude-sonnet-5-5

**Schema**
- `fx_rate_current(rate_date date, currency text, rate numeric(18,8), source_file_id bigint, PRIMARY KEY (rate_date, currency))` — what everything reads.
- `fx_rate_history` — append-only (rate_date, currency, rate, fetched_at, source_file_id); insert only when a value actually changes, so revisions are auditable and nothing is silently overwritten.
- `fx_fetch_run(id, started_at, finished_at, status, http_status, sha256, row_count, rows_inserted, rows_revised, error)` — one row per run; doubles as the raw-file record.
- Store the raw CSV (bytea on the run row, or on disk keyed by sha256) so a layout change can be replayed without re-downloading.
- Constraints: `rate > 0`, currency `CHAR(3)` with check, NOT NULL everywhere.

**Job**
- Plain script (`python -m app.jobs.fx_rates`) triggered by cron/existing scheduler at a fixed time after the bank publishes; takes a Postgres advisory lock so overlapping runs are impossible.
- Fetch with timeout + 3 retries with backoff; fail on non-200 or empty body.
- If sha256 matches the last successful run → record "unchanged" and exit.
- Parse by header names, never column positions; validate the header set against an explicit expected set and fail loudly on mismatch (don't guess new layouts).
- Validate parsed rows: dates parse, rates positive, no duplicate keys, row count within a sane range of the last run (e.g. ≥80%).
- Single transaction: upsert into `fx_rate_current` comparing old vs new; for differing rows, write the old value to history and count it as a revision. Idempotent — re-running the same file changes nothing.
- Always re-read the full file each night (not just "today's" row) — that's how revisions are caught.

**Tests**
- Parser unit tests on fixture CSVs: normal file, file with a revised past day, reordered columns (should pass), renamed/missing column (must fail with clear error), bad rates, duplicates.
- DB tests against a real Postgres: first load, idempotent re-run (zero changes), revision (current updated + history row written), failed validation (nothing committed).
- Mocked HTTP for 500, timeout, empty body.
- One small contract test asserting the expected header set is a constant — changing it is a deliberate diff.

**Knowing when it breaks**
- Any non-success run exits non-zero and sends an alert (email/Slack webhook) with the error and run id.
- Separate staleness check (independent of the job): alert if no successful `fx_fetch_run` in the last 36h, or `max(rate_date)` is older than N business days — catches the job never running at all, which failure alerts can't.
- Log revision count per run; alert if unusually large (e.g. >30 revised rows) since that often signals a unit or layout change.
- Surface `/health`-style freshness (latest rate_date, last success time) so it can be eyeballed.

**Later, only if needed:** per-currency source-of-truth rules, backfill CLI, holiday calendar awareness for the staleness alert.
