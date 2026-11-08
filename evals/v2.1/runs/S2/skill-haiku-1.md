# Nightly exchange-rate job: plan

**Schema**
- `fx_source_file`: id, fetched_at, sha256 (UNIQUE), content (bytea), header_fingerprint (hash of the header row), parser_version. A download with a hash we already hold inserts nothing.
- `fx_rate`: id, currency_pair (CHECK against the pairs we use), rate_date DATE, rate NUMERIC(20,8), revision_no, is_current, valid_from, superseded_at, source_file_id (FK), recorded_by, origin. Partial unique index on (currency_pair, rate_date) WHERE is_current. No `ON CONFLICT DO NOTHING`.
- `fx_ingest_run`: id, started_at, finished_at, status (CHECK: ok, unchanged, fetch_failed, parse_failed, zero_rows, implausible, layout_changed), rows_read, rows_changed, error_text. One row per night, including failures.
- Retention: source files and run rows kept 2 years, removed by a nightly sweep.

**Job**
- One HTTP client: 30 s timeout, TLS verification on, up to 3 retries with backoff on timeouts and 5xx only. A 404 or an HTML page where the CSV should be fails at once.
- Store the raw bytes and hash them first. Unchanged hash means status `unchanged`, no further work.
- Find columns by header name, never by position. Missing required header means `parse_failed`, and the error names it and lists what was found.
- Compare the header fingerprint with the last good run. A different fingerprint means `layout_changed`: write nothing, alert, and wait for a person to map the new layout. A delay beats guessing wrong numbers.
- Parse rates with Decimal from the source text. Reject thousands separators, "n/a", blanks and negatives, and name the row. Parse dates with one explicit format.
- Zero data rows is `zero_rows`, never `unchanged`.
- Plausibility check: a day-on-day move above a threshold we agree with the bank's users (placeholder 10%) is `implausible`, and nothing is written.
- Revisions: every run re-reads the last 30 days. Same rate means skip. A different rate runs one transaction: lock the key, mark the old row `is_current = false`, insert `revision_no + 1` with the source file id. A second run with the same file changes zero rows.
- The whole run is one transaction. A failure rolls back, so no half-written night exists.
- The job connects as a runtime role with INSERT/UPDATE/SELECT on the two fx tables only. Not the table owner, not a superuser.

**Tests** (watch each fail first)
- Saved real CSVs: current layout, previous layout, a restated day, a missing header, zero rows, an "n/a" value. Kept in the repo.
- Parser tests: reordered columns still parse; missing header, zero rows, bad number and changed fingerprint each fail with a message that names the cause.
- Idempotency test: run twice on the same file, second run changes zero rows.
- Revision test: a restated day creates revision 2, revision 1 stays readable, and a second current row for the same date is rejected by the database.
- HTTP tests against a local fake server: 503 then 200 succeeds, repeated timeouts fail after retries, 404 fails with no retry.
- Database tests run as the runtime role against the test database, not the owner.

**Knowing it breaks**
- Alert on any failed or `implausible` run, on two failed runs in a row, and on a `layout_changed` run (always page someone).
- Staleness alert on a separate schedule: no `ok` or `unchanged` run in 36 hours. It fires even if the job never starts.
- One status page: last good fetch, latest rate date, revisions in the last 7 days, and recent failed runs.
- Every alert links to a short runbook: how to read the fixture diff and how to map a new layout.

Skipped: a message queue, an ORM, a multi-source adapter, a full role split. Add a queue when a second source needs it, an adapter when a second source exists, and the role split when the database is shared with other services.
