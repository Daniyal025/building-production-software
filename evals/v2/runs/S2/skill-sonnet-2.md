# Nightly central-bank FX rates job: plan

**Scope:** real data we must keep running, so I'm planning for production, not a spike. I'm leaving out distributed tracing, an on-call rotation and a full role split. I'd add them if other teams start depending on these rates or money moves off them.

## Schema

- **`fx_rate`** holds one row per (`rate_date`, `currency`, `revision_no`). The `rate` column is `NUMERIC`, parsed from the source text with `Decimal`, never float. Add `is_current`, `superseded_at`, `source_hash`, `run_id` and `fetched_at`. A partial unique index on (`rate_date`, `currency`) `WHERE is_current` guarantees exactly one current value per day.
- **Revisions are appended, not overwritten.** A single `supersede()` function is the only writer. In one transaction it locks the key, marks the old row `is_current = false`, and inserts revision + 1. Unchanged rows are no-ops. Don't use a bare `ON CONFLICT DO NOTHING`, because that silently drops a revised rate. This also lets us answer "what did we publish last Tuesday?".
- **`fx_raw_payload`** stores the raw CSV bytes, deduplicated by sha256. When the layout changes and we fix the parser, we can replay history instead of re-downloading.
- **`fx_run`** has one row per night with status (`not_published`, `unparseable`, `ok`), rows seen, rows inserted, rows revised, error text, and the payload hash. This table is what the monitoring reads.
- **Constraints:** NOT NULL on the rate, date and currency columns, a `CHECK (rate > 0)`, a `CHECK` list on `status`, and a foreign key to the payload. All of this goes in as a forward-only migration. The app connects as a non-owner role.
- **Retention:** a nightly sweep deletes raw payloads and run rows after N months. Rate rows are kept forever.

## The job

- **Fetch:** use one HTTP client with a timeout, retry with backoff on 5xx and timeouts, and TLS verification on. If the bank hasn't published today (weekend, holiday), that is a quiet, recorded "not published". Anything else that fails is loud.
- **Parse by header text, not column position.** Normalise header names (case, whitespace, BOM) and require the exact expected set. If a required header is missing or renamed, fail the run and name the file and the missing header. Never guess a mapping.
- **Plausibility checks before any write:** rate > 0, dates parse, no duplicate (date, currency) in the file, and a day-over-day move beyond a threshold is rejected or flagged. A file that parses to zero rows fails the run.
- **Re-read the revision window.** Each night, upsert the last N days (use the longest lookback the bank is known to revise, say 30). The job compares each value to the current row and calls `supersede()` only on a real change. A second run on the same file must change zero rows.
- **Write in one transaction per run, and guard against overlap.** Use a Postgres advisory lock so a retry or overlapping cron can't double-run. A failed run leaves rates untouched and records the error on `fx_run`.
- **Missing stays missing.** If a currency or date has no value, store nothing. Never carry yesterday's rate forward as a default.

## Tests

- **Fixtures:** keep one saved real CSV per known layout, plus a "layout changed" file (renamed header, reordered columns, extra column) and a decimal-comma or odd-date-format file. Write each test first and watch it fail before the code exists.
- **Behaviour tests against a real Postgres, with the clock injected:**
  - A first load inserts the rows.
  - A rerun with the same file changes zero rows.
  - A file with one revised past day creates revision 2, flips `is_current`, and keeps the old row.
  - Reordered columns parse correctly.
  - A renamed required header, an empty file and garbage bytes each fail the run with a message naming the problem and write no rate rows.
  - A not-published response is recorded and is not an error.
- **Race test:** two real connections run the job at once, and the test fails if the lock is removed.

## Knowing when it breaks

- **Alert on staleness independently of the job.** A separate check, driven by the DB and not by the job's own logs, pages when the newest `rate_date` on a business day is older than the bank's usual publish time plus a grace period. If the job never starts, this still fires.
- **Alert on failures:** notify on any `unparseable` run and on 2 consecutive failed runs. Each alert links to a short runbook saying how to look at the stored payload and where to fix the parser. Add a "rows revised" metric and a warning if a night revises an unusually large number of rows, since that often means a unit or layout change.
- **One freshness view for people:** latest `rate_date`, last run status, rows loaded and revised per night, and days since last success. Logs are structured, each carrying the run id, and an error is logged once with context.
