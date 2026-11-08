# Nightly central-bank FX rate job: plan

## Schema
- `fx_rate(rate_date date, currency text, rate numeric(18,8), source_run_id bigint, PRIMARY KEY (rate_date, currency))`. One row per day and currency, so a revision updates a row and never duplicates it. Use `numeric`, not float.
- `fx_rate_revision(rate_date, currency, old_rate, new_rate, changed_at, source_run_id)`. Append a row whenever an upsert changes a stored value. This keeps an audit trail of the bank's revisions, and it is cheap (a trigger or one extra statement).
- `fx_ingest_run(id, started_at, finished_at, status ['ok','failed','schema_changed'], rows_seen, rows_inserted, rows_revised, csv_sha256, error text)`. Every run writes one row. This is the source of truth for health.
- Optionally keep the raw CSV for each run (a `bytea`/text column or a file path keyed by `csv_sha256`). It allows replay after a parser fix without re-downloading, and the bank may not serve old files.

## The job
- A cron entry or the existing scheduler runs one script nightly, after the bank's usual publish time, with a small retry (3 tries, backoff) for HTTP 5xx and timeouts. Set a request timeout and check the status code.
- Skip the work if the `csv_sha256` equals the last successful run's. This is an idempotent no-op.
- Parse with the stdlib `csv` module. Locate columns by header name, not position, and normalise headers (strip, lowercase, BOM). Before writing anything, validate that the required headers exist, the dates parse, and the rates are positive numerics.
- On a layout mismatch, mark the run `schema_changed`, write nothing, and alert. Never guess at columns, because a wrong guess silently stores bad rates.
- Do all the writes in a single transaction using `INSERT ... ON CONFLICT (rate_date, currency) DO UPDATE ... WHERE fx_rate.rate IS DISTINCT FROM EXCLUDED.rate`. Count the changed rows as revisions and log them to `fx_rate_revision`. Re-running the job is always safe.
- Sanity guards before commit: reject the file if the row count falls well below the previous run (for example under 50%), or if a rate moves more than N% from the prior day. Fail loudly rather than store it. The bank's real revisions are small, so the threshold is a config constant.

## Tests (pytest, a real Postgres, no network)
- Parser unit tests on fixture CSVs: the normal file, a BOM file, reordered columns, extra columns, missing columns (expect `schema_changed`), a bad date, a negative rate, and an empty file.
- Upsert tests against Postgres: a first load, an identical re-run (zero changes), and a revised rate (updated row plus one revision row). Check the primary key prevents duplicates.
- Job-level test with a stubbed HTTP fetch: the success path, a 500 followed by a successful retry, a permanent failure (run row `failed`, no rate rows touched), and the transaction rollback on a mid-file error.

## Knowing when it breaks
- Alert (Slack/email, whichever the team already has) when a run ends `failed` or `schema_changed`. Include the error and the first line of the CSV header.
- A separate freshness check, because a job that never runs can't report its own failure: alert if `max(finished_at)` of an `ok` run is older than 26 hours, or if the latest `rate_date` is more than 2 business days old. Run it from a different place than the job (a dead-man's-switch ping such as healthchecks.io, or an existing monitor).
- Surface a revision count in the run log. Many revisions in a single run is a signal worth a human glance, and the guards above already block the extreme cases.
- Write a short runbook (three lines) in the README: how to re-run for a date range, how to replay the stored CSV after a parser fix, and who gets the alert.
