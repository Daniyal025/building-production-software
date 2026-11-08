# Nightly FX rate job: plan

## Schema
- `fx_raw_file`: one row per downloaded file, keyed by `sha256` (bytes stored as-is, plus `fetched_at`, `source_url`). Lets us re-parse any past file after a parser fix.
- `fx_rate_observation`: append-only. `source`, `rate_date`, `currency_pair`, `rate numeric(18,6)`, `file_sha256` (FK to `fx_raw_file`), `observed_at`. Unique on `(source, rate_date, currency_pair, rate, file_sha256)`.
- Revisions are never updated in place. A changed rate for an existing day is a new observation row, so history is kept.
- `fx_rate_current`: view returning the newest observation per `(source, rate_date, currency_pair)`. Consumers read this view, never the raw table.
- `fx_ingest_run`: one row per nightly run with `status` (ok / failed / skipped_unchanged), `layout_version`, `rows_parsed`, `rows_inserted`, `rows_revised`, `error`, `started_at`, `finished_at`. This table drives monitoring.

## Job
- Schedule nightly after the bank's usual publish time; retry hourly until success or a cutoff hour.
- Download with a timeout and capped retries. Store the raw bytes and sha256 before parsing anything.
- If the sha256 matches the last successful file, record `skipped_unchanged` and stop.
- Parse by header name, not column position. Each known layout is one entry in a dict. An unknown header fails the run; never guess.
- Validate before writing: dates parse, rates are numeric and positive, expected pairs are present, row count is within a band of the previous day.
- Write the run's observations in one transaction. Insert new rows and revised rows together, or nothing.
- Rows the bank drops are flagged in the run record, not deleted.
- Re-running the same file inserts zero rows (idempotent).

## Tests
- Parser unit tests against checked-in sample CSVs, one per known layout, plus a header-changed sample.
- Unit tests that an unknown header, a missing column, and a bad number each raise and write nothing.
- Integration test on a scratch Postgres: run twice on the same file (second run inserts nothing); run with a revised file (one new observation, `fx_rate_current` shows the new value).
- HTTP is mocked in tests. No live bank calls in CI.

## Knowing it breaks
- Alert when there is no `ok` run in the last 26 hours.
- Alert on any `failed` run, and always on the "unknown layout" error, which is the main signal that the bank changed the CSV.
- Alert when a run parses zero rows or the row count drops sharply against the previous day.
- Alert when the latest `rate_date` is older than the last expected business day.
- Keep a daily one-line summary from `fx_ingest_run` so silence is visibly healthy.

Skipped: a queue, a generic ETL framework, and automatic layout inference. Add a queue when feeds multiply, and revisit inference only if layout changes become frequent.
