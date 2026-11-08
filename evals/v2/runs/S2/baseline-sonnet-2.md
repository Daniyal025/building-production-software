# Nightly central-bank FX rate job: plan

## Schema
- `fx_rate(rate_date date, currency text, rate numeric(18,8), source_run_id bigint, PRIMARY KEY (rate_date, currency))`. One current row per day per currency; use `numeric`, never float.
- `fx_rate_history(rate_date, currency, old_rate, new_rate, changed_at, run_id)`. Insert a row only when an upsert actually changes a value. This makes bank revisions auditable and answers "what did we believe on date X?".
- `fx_ingest_run(id, started_at, finished_at, status ['ok'|'failed'|'layout_changed'], rows_seen, rows_inserted, rows_revised, file_sha256, error text)`. One row per nightly run. It is the source for monitoring and for debugging.
- Keep the raw CSV (bytea or object storage), keyed by `file_sha256`, for every run. It allows replay when the parser is fixed and is the evidence for any revision dispute.

## Job
- Cron or the existing scheduler runs it nightly after the bank's usual publish time, with a retry or two at +1h and +3h. If the bank is late, a retry is cheaper than a clever wait.
- Fetch with `requests`, a timeout, and a status check. Compute the sha256. If it equals the last successful run's hash, record "no change" and exit.
- Validate the header against an explicit expected column set before parsing any rows. A mismatch raises `LayoutChanged`, marks the run `layout_changed`, stores nothing, and alerts. Never guess columns by position.
- Parse strictly. Reject a row if the date or rate does not parse, the rate is not positive, or the currency is not in the allow-list. If more than a small share of rows are rejected, fail the whole run instead of loading a partial file.
- Load in a single transaction. Use `INSERT ... ON CONFLICT (rate_date, currency) DO UPDATE ... WHERE fx_rate.rate IS DISTINCT FROM EXCLUDED.rate`. Write history rows from the same statement via `RETURNING` and a CTE. The job is idempotent, so a rerun or backfill is safe.
- Process the whole file every night, not just the newest day. This is the simplest way to pick up revisions, and the file is small. Set a hard sanity bound on revisions: if a past rate moves more than X% (say 10%), still load it but flag it in the run log and the alert.
- Add a CLI flag `--file path.csv` to replay a stored CSV. Use it for backfills and for recovery after a layout change.

## Tests
- Unit tests for the parser using fixture CSVs: normal file, a revised-days file, a reordered-columns file, a renamed-column file, an extra-column file, a blank or truncated file, a bad number, and a decimal-comma/date-format variant if the bank has ever used one.
- DB integration tests against a real Postgres (not mocks), covering these cases: first load inserts N rows; reloading the same file changes nothing and writes no history; a revised file updates the rate and writes exactly one history row; a failed validation leaves the table untouched (rollback).
- A contract test with a saved real sample of the bank's file, so the fixture is the real format and not our guess. Refresh it by hand when the bank changes layout.
- Stub the HTTP layer (`responses` or a local file server). The tests make no real network calls. Optionally run one weekly live smoke test in CI that only checks the header.

## Knowing it broke
- Alert on any run whose status is not `ok`, sent to the team channel or email with the error text and the run id. Layout changes get a distinct message, because they need a human.
- Dead-man check: alert if there is no `ok` run in the last 36 hours. This catches the silent failure where the job or the scheduler never ran.
- Freshness check: alert if `max(rate_date)` is more than 3 business days old. This catches the case where the job succeeds but the bank has stopped publishing or the file is stale.
- Log `rows_seen`, `rows_inserted` and `rows_revised` on every run. Alert when `rows_seen` drops sharply compared with the previous run, which usually means a truncated or restructured file.
- Write a short runbook: how to replay a stored CSV, how to update the expected-header constant, and how to read `fx_rate_history`.
