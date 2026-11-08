# Nightly central bank exchange-rate job: plan

Scope: production-grade for one nightly job, not a bigger system. Revisit (role split, offsite backups, alerting service) if these rates start driving payments or any automated write.

## Schema
- `fx_fetch`: one row per run (id, started_at, finished_at, status `ok` / `not_published` / `unparseable` / `zero_rows` / `unchanged`, rows_parsed, rows_changed, error text, payload_sha256). This is the run log that monitoring reads.
- `fx_raw_payload`: sha256 primary key, the raw CSV bytes, fetched_at. Insert only when the hash is new, so a parser fix can replay history.
- `fx_rate`: id, base_ccy, quote_ccy, rate_date (the bank's date, not ours), rate NUMERIC(18,6) NOT NULL with CHECK (rate > 0), revision_no, is_current, valid_from, superseded_at, fetch_id FK, created_at.
- Partial unique index on (base_ccy, quote_ccy, rate_date) WHERE is_current, so there is one live rate per day and pair.

## Job
- A revised day is a new revision, never an overwrite: lock the key, mark the old row not current, insert revision_no + 1. No ON CONFLICT DO NOTHING, which would silently drop a changed rate.
- Each night re-read a fixed window (say the last 30 days) so restatements are caught; the second run on an unchanged file writes zero rows.
- Parse columns by header name, never by position. Read rates as Decimal from the text, never float.
- Refuse implausible values (non-positive, or a day-on-day move beyond a set threshold) and fail the run rather than write them.
- Write one run's rows in one transaction: all or nothing.
- Use one HTTP client: timeout, retries with backoff on timeouts and 5xx only, TLS verification on. A 404 or a not-yet-published day is recorded as `not_published`, which is quiet; it is not an error.
- Take a Postgres advisory lock so two overlapping runs cannot both write.
- Connect as a role with INSERT/UPDATE/SELECT on these tables only, not the table owner.

## Tests (write each one red first)
- Saved real CSV fixtures: one per known layout, a revised-day pair, a zero-row file, and a file with a renamed header.
- Revised day produces revision 2 and keeps revision 1; a second identical run produces zero changes.
- Reordered columns still parse; a missing required header fails the run and the error names the file.
- Two real connections racing for the lock; the test must fail if the lock is removed.
- Clock injected, no network in the default suite; the live fetch is an opt-in test.
- The whole suite runs against a throwaway Postgres in CI, not against the dev database.

## Knowing it broke
- Alert after N consecutive failed runs, and separately when the newest rate_date is older than expected. The staleness check must not depend on the job itself, since a job that never ran cannot report that it failed.
- Alert on any parse failure or zero-row file, with the error text and a runbook link in the alert.
- Keep a weekly count of revisions and of days with a missing currency; a sudden jump usually means a layout or source change.
- Sweep raw payloads and run rows older than the retention period nightly.
