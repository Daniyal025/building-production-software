# Nightly central bank exchange-rate job: plan

Scope: production grade. The job runs unattended against real data that feeds the financial models, so failures must be loud and revisions must be kept.

## Schema

- `fx_rate` table with an identity PK, `base_ccy`, `quote_ccy`, `rate_date`, `rate NUMERIC(18,8)`, `revision_no`, `is_current`, `valid_from`, `superseded_at`, `run_id` (FK), `raw_payload_id` (FK), `actor`, `origin`, `created_at`.
- Partial unique index on `(base_ccy, quote_ccy, rate_date) WHERE is_current`, so only one live rate per pair and day.
- Revisions go through one `record_rates()` function: lock the key, check the expected current revision (409-style abort if it moved), set the old row `is_current = false` with `superseded_at`, insert `revision_no + 1`. No `ON CONFLICT DO NOTHING` on the business key.
- `raw_payload` table: the exact CSV bytes, `sha256` UNIQUE, `fetched_at`, `parser_version`. Insert only when the hash is new, so a parser fix can replay old history.
- `ingest_run` table: `started_at`, `finished_at`, `status` (ok, no_change, failed), `rows_parsed`, `rows_changed`, `error` text. Every run writes a row, including failed ones.
- Migrations go through the project's ledger. The job connects as a least-privilege role, never as superuser or table owner.

## Job

- One HTTP client with a timeout, TLS verification on, and retry with backoff only on timeouts and 5xx. A non-200 fails the run.
- Locate columns by header name, never by position. A missing expected header fails the run and names the header. A layout change then becomes a loud failure, not a silent misread.
- Parse numbers from source text into `Decimal`, never float.
- Validate the whole file before writing anything: at least one row, parseable dates, no duplicate date rows, rate greater than zero, and a daily move within a plausibility band against the previous day.
- Zero rows is a failure unless the bank has published a not-yet-published notice, which is a distinct quiet status.
- Re-read a rolling window (for example the last 30 days) every night, since the bank restates past days. Re-running the same file writes zero rows, so backfills are idempotent.
- Write everything in one transaction, using only `record_rates()`. Any later backfill script uses the same function.
- Retention: keep raw payloads for a fixed period (for example 2 years) and delete older ones in a separate nightly sweep.

## Tests

- Saved real CSV fixtures: one per known layout, plus one file that restates a past day.
- Write each test first and watch it fail. Cover: reordered columns still parse, an unknown or missing header raises and names the column, an empty file fails, a restated day creates `revision_no = 2` and flips `is_current`, an unchanged re-run writes zero rows, an implausible value is rejected, and `Decimal` precision survives.
- Race test with two real database connections: two runs for the same day produce one revision. It must fail when the lock is removed.
- Real Postgres in tests, not a mocked database. Mock only the HTTP boundary, and feed it fixtures.
- Inject the clock so the rolling window is derived from the injected date, not from today. No network in CI.

## Knowing it broke

- Log structured lines with the run id. Failed runs keep their error text on the `ingest_run` row.
- Alert on any failed run and on two consecutive failures. Send the alert to the owner with the failing header name.
- A separate staleness check, not inside the job: if no new rate date has appeared by the expected publish time plus a margin, alert. A job that never starts cannot alert on itself.
- Notify (not page) when a run changes rates for days older than the window, because that means the bank restated history.
- One status view: last successful run, data freshness in days, and revisions in the last 7 days.

Skipped: paging integration, multi-bank sources, and a separate database role split. Add the role split and an allowlist for any parsed text when these rates start driving client-facing money or trades.
