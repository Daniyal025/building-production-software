# Nightly central-bank FX rate job: plan

## Schema
- `fx_rate(rate_date date, currency text, rate numeric(18,8), source_fetch_id bigint, PRIMARY KEY (rate_date, currency))`. One current row per day and currency. Use `numeric`, never float.
- `fx_rate_history(rate_date, currency, old_rate, new_rate, changed_at, fetch_id)`. Append a row whenever an upsert changes an existing value, so revisions are auditable and not silently overwritten.
- `fx_fetch(id, started_at, finished_at, status, http_status, sha256, row_count, rows_inserted, rows_revised, header_signature, error)`. One row per run. This is the single source for monitoring.
- Keep the raw CSV (a `bytea` or text column on `fx_fetch`, or object storage). It is cheap, and it lets you replay after a layout change without re-downloading, since the bank may not serve old files.

## Job
- A single entrypoint, `python -m app.jobs.fx_rates`, run by cron or the existing scheduler at a fixed time after the bank publishes. Add retries with backoff (3 tries) for network errors and 5xx responses only.
- Take `pg_advisory_lock` so overlapping runs cannot happen.
- Fetch with a timeout and `raise_for_status`. If the sha256 matches the last successful fetch, record `status=unchanged` and stop.
- Validate the header before parsing: compare the column names against an expected set. On mismatch, fail loudly with status `layout_changed`, write nothing, and keep the raw file. Never guess at columns. A column rename should be a one-line mapping change in code, not a silent reparse.
- Parse into typed rows, rejecting bad dates, non-positive rates and duplicate keys within the file. Reject the whole file if more than a small fraction of rows are bad.
- Load in one transaction: `INSERT ... ON CONFLICT (rate_date, currency) DO UPDATE ... WHERE fx_rate.rate IS DISTINCT FROM EXCLUDED.rate`. Write the history rows in the same transaction. Re-running the job is idempotent.
- Reprocess the full file each night, not just "today". This catches revisions to past days at no extra cost, provided the CSV carries a window of recent days. If it carries only one day, widen the fetch to a rolling re-fetch of the last N days.

## Tests
- Parser unit tests use fixture CSVs checked into `tests/fixtures/fx/`: a normal file, one with a revised day, one with a renamed column, one with an extra column, one with bad rows, and an empty file.
- DB integration tests run against a real Postgres, not mocks. They cover: first load; a second identical load leaves 0 changes; a revised rate updates `fx_rate` and adds one history row; a failed parse leaves the tables untouched (transaction rollback).
- Mock HTTP at the boundary, with `responses` or `httpx.MockTransport`. Cover timeout, 500 then success on retry, and a 200 with an HTML error page (which should hit the header check).
- One test asserts that the layout-change path writes a `layout_changed` row to `fx_fetch` and exits non-zero.

## Knowing when it breaks
- Exit non-zero on any failure, and have the scheduler alert on a non-zero exit (email or Slack). This covers the loud failures.
- Add a staleness check, because a job that never runs raises no error: alert if `max(finished_at) WHERE status IN ('ok','unchanged')` is older than about 36 hours, or if `max(rate_date)` lags by more than the bank's normal publishing gap (allow weekends and holidays).
- Track `row_count` against a trailing median per run. Alert on a drop of more than 50%, which indicates a silent truncation or a partial layout change.
- Revision alert: log a warning, and notify if `rows_revised` is unusually large, or if a revision exceeds a set percentage (for example 5%). That usually means a bad upstream file or a parsing mistake, not a real revision.
- Runbook line in the README: how to replay from a stored raw file (`--from-fetch <id>`), and where the header mapping lives.

## Skipped, add when needed
- Multiple sources or fallback providers: add only if the bank's uptime becomes a business problem.
- A generic schema-inference layer for layouts: unnecessary, since a strict header check plus a quick code fix is simpler.
