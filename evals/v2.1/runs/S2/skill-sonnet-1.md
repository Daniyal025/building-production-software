# Nightly exchange-rate ingest: plan

**Schema**
- `fx_raw_file(id, source_url, fetched_at, sha256 UNIQUE, bytes, header_row)`: store every downloaded CSV, deduplicated by hash. A parser fix can then replay history, and an unchanged file is a cheap no-op.
- `fx_rate(rate_date, currency, rate NUMERIC(18,8), source_file_id, first_seen_at, updated_at, PRIMARY KEY (rate_date, currency))`. Use `Decimal` from the CSV text to NUMERIC. Never use float.
- `fx_rate_revision(rate_date, currency, old_rate, new_rate, source_file_id, changed_at)`: append-only. Overwrites of past days go here, so you can answer "what did we think on day X?".
- `fx_ingest_run(id, started_at, finished_at, status, file_id, rows_parsed, rows_inserted, rows_revised, error)`: one row per run. It holds the parser error text and drives the alerts.

**The job**
- Run nightly from cron or the scheduler, in a separate process from the web API. Take a `pg_try_advisory_lock` so two overlapping runs can't both write.
- Use one HTTP client with a timeout, retry with backoff on 5xx and timeouts, and TLS verification on. If the bank hasn't published yet, record "not published" and exit quietly. A fetch or parse failure is a hard failure.
- Parse by header text, never by column position. Normalise the headers (case, whitespace, BOM) and map them through a small alias table. If a required header is missing, the run fails and the error names the missing column and the headers actually found.
- Reject bad data before any write: zero rows, an unparseable date or number, a duplicate (date, currency) pair, a non-positive rate, or a day-over-day move beyond a threshold (say 20%) that looks like a layout or unit shift. One bad row fails the whole file, and nothing is written.
- Re-read the full window the bank can still revise (set it from observed behaviour, e.g. the last 30 days, and compare it with the whole file). Upsert in one transaction. Only rows whose value differs are updated, and each change writes a `fx_rate_revision` row. Running the same file twice must give zero changes.
- Never write a default, a zero, or yesterday's rate for a missing currency or day. A gap stays a gap, and a gap inside the expected window is reported in the run row.

**Tests (write each one, watch it fail first)**
- Keep a saved real CSV per layout the bank has used (current, plus each old or odd one). Cover the edge cases: BOM, different delimiter, decimal comma, a renamed or reordered column, and a date format change.
- Behaviour tests against a real Postgres: first load; the same file again (zero changes, no new revisions); a revised past day (rate updated, revision row written, other days untouched); an empty file; a file with a missing header; one bad row (nothing written); a failed fetch.
- Test the hash dedup, and the advisory lock (a second concurrent run exits without writing).

**How we'll know it breaks**
- Staleness alert, independent of the job: if `max(rate_date)` is older than the expected business day plus a grace period, page or message someone. This catches the job not running at all, which a job-level alert can't.
- Alert on a failed run, and on N consecutive "not published" runs. The message carries the run id and the parser error, and links to a short runbook (check the bank's site, fetch the raw file from `fx_raw_file`, add a header alias, replay).
- Log structured JSON with the run id: rows parsed, inserted and revised, duration, and file hash. Put revision counts on the dashboard. A spike in revisions is a signal (the bank corrected a lot, or our parser is wrong).
- Retention: a nightly sweep deletes raw files and run rows older than a set period (e.g. 1 year raw, 2 years runs). Keep it separate from the ingest job and make it log what it deleted.
- First step when the layout changes: fix the alias or parser, then replay the stored raw files to confirm the existing data is reproduced exactly, so a parser change can't silently alter history.

**Open question (tier moves up if yes)**
- If these rates feed money movement or customer-facing prices, treat it as high-stakes. That adds an owner sign-off on large revisions and a hold on publishing flagged rates until someone approves them.
