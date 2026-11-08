# Nightly central-bank FX rate job: plan

Assumption: this is a production feed that other things read, but it does not move money. If rates drive payments or accounting postings, add an audit trail and a second reviewer on parser changes.

## Schema (3 tables)

- **`fx_rate`**: `(source, rate_date, base_ccy, quote_ccy)` is the primary key. `rate NUMERIC(18,8) NOT NULL`, plus `first_seen_at`, `updated_at` and `raw_payload_id`. Store the rate as `Decimal` parsed from the source text. Never use float, and send it as a string in any JSON.
- **`fx_rate_revision`**: append-only. Whenever an upsert changes an existing rate, write `(key, old_rate, new_rate, changed_at, payload_id)`. The latest value stays queryable in `fx_rate`, and "what did we believe on day X" is still answerable.
- **`fx_payload`**: raw CSV bytes, `sha256` unique, `fetched_at`, and a header fingerprint. Identical downloads dedupe. A parser fix can replay history from this table.
- **`fx_run`**: one row per job run, with `started_at`, `status` (`ok`, `not_published`, `unparseable`, `zero_rows`, `implausible`, `error`), rows read, rows inserted, rows revised, and the error text.
- Add a CHECK that `rate > 0`. Missing rates stay absent rather than becoming 0 or the previous day's value, so a gap is visible to readers.

## The job

- **Fetch** with one HTTP client: timeout, a few retries with backoff on 5xx and timeouts, TLS verification on. Save the raw bytes before parsing.
- **Re-read a trailing window** (say the last 30 days, or whatever the bank's revision window actually is) every night, not just yesterday. Upsert with `INSERT ... ON CONFLICT DO UPDATE ... WHERE rate IS DISTINCT FROM EXCLUDED.rate`, and write a revision row in the same transaction. A second run on the same file must change zero rows.
- **Find columns by header text** (normalised: trimmed, case-folded, BOM stripped, explicit encoding), not by position. Expected headers are a small mapping in one place.
- **Layout change is a loud failure.** If a required header is missing, or the parser reads zero rows, the run is marked `unparseable` or `zero_rows`. It names the file and the missing header and writes nothing. Do not guess a new layout.
- **Plausibility checks before writing**: the rate is positive, and its day-over-day move is within a band (for example 20%) unless it is an explicit revision. Each currency expected yesterday must still be present. Fail the whole batch rather than writing part of it.
- **Weekends and holidays**: "bank hasn't published yet" is the one quiet outcome (`not_published`). It is distinguished from "published but unreadable", which is a failure.
- **Scheduling**: a single run at a time (Postgres advisory lock), and an idempotent entrypoint so a manual re-run or backfill is safe.

## Tests (write each one and watch it fail first)

- **Fixtures**: save one real CSV per layout the bank has used, plus a deliberately renamed-header version and a reordered-columns version. Test that reordered columns still parse and that a renamed header fails loudly.
- **Idempotency**: run the same file twice and assert the second run changes zero rows and adds zero revision rows.
- **Revision**: load a file, then a later file with one past day changed. Assert `fx_rate` holds the new value and `fx_rate_revision` holds the old one.
- **Bad input**: an empty file, an HTML error page served with a 200, a negative or zero rate, a comma-decimal value, and a truncated download. Each must produce the right `fx_run.status` and write nothing.
- **Run these against a real Postgres** (the upsert and constraints are the point), not a mock.

## Knowing when it breaks

- **Staleness alert, independent of the job**: a separate check (cron or the monitoring system) that fires if `max(rate_date)` is older than expected for a business day, or if no `fx_run` row exists for today. A dead scheduler can't report its own death, so this check must not live inside the job.
- **Failure alerts**: page on `unparseable`, `zero_rows` or `implausible`, and on N consecutive `error` runs. The message carries the run id, the file hash and the parser error, so it is actionable from the alert alone.
- **Revision visibility**: log or count revisions per run. A big revision (many days or large moves) goes to a channel for a human to look at. It is not a page.
- **Retention**: a nightly sweep deletes raw payloads and run rows past a retention period (for example 1 year). Keep the rate and revision tables indefinitely.

## Later, only if needed

- Per-currency source fallbacks, tracing, and a dashboard beyond the freshness query. Add them once a second source or a second consumer exists.
