# Nightly exchange-rate ingest: plan

**Schema**
- `fx_rate_revision` (append-only): `base_ccy`, `quote_ccy`, `rate_date`, `rate numeric(18,8)`, `fetched_at timestamptz`, `source_sha256`, with PK `(base_ccy, quote_ccy, rate_date, fetched_at)`. A revised day adds a row; old values are never overwritten, so history is kept.
- `fx_rate_latest` as a view: `DISTINCT ON (base_ccy, quote_ccy, rate_date)` ordered by `fetched_at desc`. Readers use this view.
- CHECK constraints: `rate > 0` and `base_ccy <> quote_ccy`. Enforce in the database, not only in code.
- `fx_ingest_run`: `id`, `started_at`, `finished_at`, `status` (ok / unchanged / failed), `source_sha256`, `rows_parsed`, `rows_written`, `error`. This table is the audit trail and the basis for alerts.

**Job**
- One entry point, run nightly by the existing scheduler. Keep it out of the API process.
- Download with a timeout and 3 retries with backoff. Store the raw bytes and their sha256 before parsing, so any run can be replayed.
- If the sha256 matches the last successful run, record `unchanged` and stop.
- Parse columns by header name, never by position. A missing required header fails the run and writes nothing. This covers the layout-change case.
- Validate every row: date parses, rate is numeric and > 0, no duplicate keys in the file. Abort the whole file on any bad row, not just skip it.
- Re-fetch a rolling window (last ~30 days) on every run so revisions are caught. Insert a revision row only when the rate differs from the latest stored value for that key.
- Write everything in one transaction. Use parameterised upserts via the existing DB driver. No new dependency is needed for CSV (stdlib `csv`).
- Idempotent: running twice on the same file writes nothing the second time.
- Skipped: a generic CSV-mapping config, a schema-versioned parser registry, and a retry queue. Add when a second bank source or a second layout actually appears.

**Tests**
- Parser unit tests on saved fixture files: current layout, reordered columns, a revised past day, a malformed row, an empty file, and an HTML error page returned with status 200.
- Layout-change test: a renamed or removed header fails the run, and the DB has zero new rows.
- Revision test: same date, different rate, produces a second revision row, `fx_rate_latest` shows the new value, and the old row remains.
- Idempotency test: two runs on identical bytes produce one set of rows.
- Rollback test against the test database: a bad row mid-file leaves no partial writes.

**Detecting breakage**
- Alert when there is no `ok` run in the last 26 hours, or when the latest run is `failed`. This is the main signal.
- Alert immediately on any header-mismatch failure. Layout changes should be loud, not silent.
- Flag (do not block) when the row count drops more than 20% versus the previous run, or when a rate moves more than a set threshold day on day. Both are usually real events worth a look.
- Freshness check: the latest `rate_date` should match the last expected business day. Run this check after the job.
- Deliver alerts through whatever channel the team already reads (email or chat webhook). Skipped: a dashboard. Add when someone asks for one.
