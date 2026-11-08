# Nightly exchange-rate job: plan

## Schema
- `fx_source_file(id, source_url, fetched_at, http_status, sha256 UNIQUE, body)`: keep the raw CSV, deduplicated by hash, so a parser fix can replay past days.
- `fx_run(id, started_at, finished_at, status ok|failed|not_published, rows_parsed, source_file_id, error_text)`: every run writes a row, including failures.
- `fx_rate(id, base, quote, rate_date, rate NUMERIC(20,8), revision_no, is_current, valid_from, superseded_at, source_file_id, run_id)`: append-only. A partial unique index on (base, quote, rate_date) WHERE is_current keeps one live value per day.
- CHECK rate > 0, NOT NULL on rate_date and rate, FKs to the file and run rows.
- Parse rates with Decimal from the source text; send them as strings in JSON, never floats.
- One `supersede_rate()` function is the only writer: lock the key, check the expected current revision, flip the old row to not current, insert revision + 1 with actor and time. No ON CONFLICT DO NOTHING.
- Retention: raw bodies and run rows swept after a set period (say 180 days); rates kept indefinitely.

## Job
- Fetch with one HTTP client: timeout set, retry with backoff only on timeouts and 5xx, TLS verification on, explicit encoding.
- Map columns by header name, not position. An unknown or missing required header fails the run and names the file.
- Re-read a rolling window (start with 30 days, set from the longest revision lag we observe) every night, since the bank revises past days.
- Insert a revision only when the value differs from the current one. A second run on the same file writes nothing.
- Plausibility checks before any write: zero rows or HTML instead of CSV fails the run; a day-on-day move above a set threshold is held for review, not written.
- Each file is written in one transaction.

## Tests
- Save a real CSV per layout version as a fixture. Add one hand-edited fixture where a past day has changed.
- Parser: the current layout gives exact Decimal values; reordered columns still parse; a renamed header fails with the file name; an empty file or an HTML error page fails, not "0 rows".
- Revision: load a day, load a file where that day changed, expect one new revision, the old row not current, and a second run to write zero rows.
- Race: two real connections run the job at once; a duplicate revision must be impossible. Confirm the test fails when the lock is removed.
- Clock is injected; no test depends on today's date. Each test is seen failing before the fix.

## Detecting breakage
- One structured log line per run with the run id; the error is logged once, where it is handled.
- Alert after two consecutive failed runs, with the parser error in the message.
- Staleness alert from a separate check: no successful run in 26 hours, or the newest rate_date older than expected. It must not depend on the job itself.
- Track rows parsed, revisions written and last success time; a spike in revisions or a drop in rows is the early sign of a layout change.

Skipped: role split, distributed tracing, SLO dashboards, and a formal game day. Add them when more services or real money depend on these rates.
