# Nightly central-bank FX rate job: plan

## Schema

- **`fx_rate` (append-only revisions).** Columns: `rate_date date`, `currency char(3)`, `rate numeric(18,8)` (never float), `revision_no int`, `is_current bool`, `superseded_at`, `source_payload_id` (FK), `run_id` (FK), `created_at`. Primary key is an identity `id`. A partial unique index on `(rate_date, currency) WHERE is_current` guarantees one current rate per key. NOT NULL on everything the code assumes.
- **One `supersede()` function is the only write path.** In one transaction it locks the key, compares the incoming rate to the current one, and does nothing if they are equal. If they differ, it flips the old row to `is_current = false` and inserts `revision_no + 1`. Never use `ON CONFLICT DO NOTHING` on `(date, currency)`: it would silently drop a revised rate. Past revisions stay queryable ("what did we think on Tuesday?").
- **`fx_raw_payload`.** Stores the raw CSV bytes, `sha256` (unique), `fetched_at` and `layout_version`. Identical downloads are stored once, so a no-change night adds no payload row. A parser fix can replay history from it. Retention of N days, enforced by a nightly sweep.
- **`fx_ingest_run`.** Columns: `started_at`, `finished_at`, `status` (CHECK in `ok`, `not_published`, `unparseable`, `zero_rows`, `implausible`, `http_error`), `rows_seen`, `rows_inserted`, `rows_revised`, `error_text`, `payload_id`. Same retention sweep. This table is what monitoring reads.
- **Migrations.** Use the existing migration tool, additive and re-runnable, with the seed updated in the same PR. The job connects as a dedicated role with INSERT/UPDATE on these tables only, never the owner or a superuser.

## The job

- **One HTTP client.** Timeout, retry with backoff on 5xx and timeouts only, TLS verification on, and a descriptive User-Agent. Don't retry 4xx. The client runs once per night; the scheduler (cron or the existing one) is separate from the API process.
- **Hash the download first.** If the hash matches the last stored payload, record a `no change` run and stop. Otherwise store the payload, then parse.
- **Parse by header name.** Look columns up by header text (normalised for case, whitespace and BOM), not by position. Read the rate with `Decimal(str)` straight into NUMERIC, and parse dates with an explicit format and explicit encoding. If a required header is missing, fail the run with `unparseable`, naming the file and the missing column. Don't guess a mapping.
- **Zero rows is a failure.** "Bank hasn't published yet" is the only quiet outcome. A file that parses to zero rows, or has unknown headers, fails the run loudly and writes nothing.
- **Plausibility checks before writing.** Reject rates that are non-positive, or that jump more than X% against the previous day for the same currency, or that cover far fewer currencies than yesterday. A rejected batch writes nothing and records `implausible`.
- **Re-read the revision window.** Each night upsert the whole file (or the last N days the bank can still revise, e.g. 30), not just "today". Every row goes through `supersede()`. Running it twice produces zero changes, which is the idempotency check.
- **Write the batch in one transaction** (all or nothing), then finalise the run row with counts. A crash mid-run leaves the previous data intact.

## Tests

- **Fixtures.** Keep a saved real CSV for each layout the bank has used (plus the current one), a revised-day file, a zero-row file, a renamed-header file, and a file with a garbage value. Use fixtures, not live network calls; a live test is opt-in only.
- **Cases, each seen failing before it passes (red then green):**
  - Same file twice gives zero changes.
  - A revised day creates revision 2, flips revision 1 to not-current, and the partial unique index holds.
  - Reordered columns still parse.
  - Renamed or missing header fails the run and writes no rows.
  - Zero rows fails.
  - A decimal like `1.2345678` survives exactly.
  - A failing parse mid-file rolls back the whole batch.
- **Concurrency.** Run two real DB connections calling `supersede()` on the same key at once. The test should fail if the lock is removed.
- **Hermetic.** Inject the clock, so the tests don't depend on today's date, and have each test create its own data.

## How we'll know it breaks

- **Alert on staleness, independent of the job.** A separate check (query or cron) alerts if `max(rate_date)` for the main currencies is older than the bank's expected publishing lag, plus a grace period (e.g. more than 2 business days). This catches the case where the job itself never ran.
- **Alert on failure.** Notify on any run with a failed status, and escalate after 2 consecutive failures. The message includes the run id, the error text and the payload hash so the on-call person can replay it.
- **Alert on silent oddities.** An unusually large revision count in one run, or a sudden drop in rows seen, goes to the same channel as a warning.
- **Logs and dashboard.** Structured logs with the run id, and the error logged once where it is handled. One small dashboard shows the latest run status, rows per run, and data freshness per currency.
- **Runbook.** Say what to do for each failure status: fetch the stored payload, fix the parser, replay from `fx_raw_payload`. A layout change then becomes a one-fixture, one-test fix rather than a data gap.

## Deliberately skipped, with the trigger to add it

- Distributed tracing and full RED/SLO dashboards: add them if this grows into several jobs or services.
- Separate owner/migrator/service role split: add it if more services use this database.
- Schema auto-detection of new layouts: build it only if the bank changes layout more than about twice a year.
