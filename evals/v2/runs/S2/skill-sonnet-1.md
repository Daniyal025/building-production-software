# Nightly central-bank FX rate job: plan

Scope: a real-data feed we have to keep running, but not regulated trading infrastructure. I'd build it as one table set, one job and one alert. If the rates start driving payments or reporting we're legally accountable for, add an audit/role split (last bullet).

## Schema

1. **`fx_rate` is append-only revisions, not overwrite.** Columns: `rate_date date`, `currency char(3)`, `rate numeric(18,8)`, `revision_no int`, `is_current bool`, `valid_from timestamptz`, `superseded_at timestamptz`, `source_payload_id` (FK). A partial unique index on `(rate_date, currency) WHERE is_current` gives one live value per day while keeping history. This answers "what did we think the rate was last Tuesday?".
2. **Exact types end to end.** Parse from the CSV text straight into `Decimal`, store as `NUMERIC`, never go through float. Add a `CHECK (rate > 0)`, plus NOT NULL and a primary key.
3. **One `supersede()` function is the only writer.** It runs in one transaction, locks the key, flips the old row to `is_current=false`, and inserts revision + 1. Don't use `ON CONFLICT DO NOTHING` on `(date, currency)`: it would silently discard exactly the revisions the bank publishes.
4. **`raw_payload` table.** Store the downloaded bytes, a `sha256` (unique), `fetched_at`, the URL and the detected layout. Re-downloading identical bytes inserts nothing. When the layout changes and we fix the parser, we can replay history instead of hoping the bank still serves the old files.
5. **`ingest_run` table.** One row per run: started/finished, status (`not_published | unparseable | ok`), rows parsed, rows inserted, rows revised, error text, payload id. Every row written records its origin (run id) and time, so provenance is a fact in the data and not something we infer.
6. **Migrations only, additive, idempotent.** Use the project's migration tool, don't edit applied files, and deploy the schema before the code. The job runs as its own DB role with INSERT/UPDATE on these tables only, not as the owner or a superuser.
7. **Retention.** Raw payloads and run logs are kept for a stated period (say 13 months), pruned by a nightly sweep. Rates themselves are kept forever.

## The job

8. **Fetch with one HTTP client.** Explicit timeout, retry with backoff on 5xx and timeouts, TLS verification on. If the bank hasn't published yet (404 or an unchanged file), that's a quiet "not published" and the next night's run still works.
9. **Parse by header name, not column position.** Normalise the header text (case, whitespace, BOM), map known aliases to canonical fields, and use an explicit encoding and delimiter. If a required header is missing or an unknown layout appears, fail the run loudly and name the file and the missing header. Never guess.
10. **Plausibility checks before any write.** Reject non-positive rates, unknown currency codes, unparseable dates, and a day-over-day move beyond a sane threshold (e.g. more than 20%) unless explicitly allowed. A suspicious file fails the whole run, not just the odd row, so we never half-load a shifted-column file.
11. **Zero rows is a failure, not a success.** A file that parses to zero rows, or to far fewer currencies than yesterday, fails the run.
12. **Re-read the revision window every night.** Reload the whole file (or the last N days, matching how far back the bank revises, e.g. 30). Compare each row to the current revision: unchanged means no write, changed calls `supersede()`, new means insert revision 1. The job is idempotent: a second run on the same file makes zero changes.
13. **All-or-nothing per run.** Parse and validate everything first, then write inside one transaction, so a bad file can't leave a partial day.
14. **Schedule with a lock.** An advisory lock stops overlapping runs. The nightly time should be after the bank's usual publication time, with a retry later the same day if it isn't out yet.

## Tests

15. **Fixtures from real files.** Save one real CSV per layout the bank has used, plus a deliberately changed layout (renamed header, reordered columns, extra column, decimal comma, BOM). Tests cover: old layout parses, reordered columns parse identically, a missing required header fails with the file named, zero rows fails.
16. **Revision behaviour.** Load day 1, load again with day 1's rate changed, and assert revision 2 is current and revision 1 is kept and superseded. Load the same file twice and assert zero writes the second time. Write each test, watch it fail first (e.g. with a naive upsert), then make it pass.
17. **Hermetic.** The clock is injected, the HTTP layer is a fake serving fixtures (no live network in the default suite; one opt-in live smoke test), and each test owns its own data. A concurrency test with two real connections confirms the lock really blocks double-runs.

## How we'll know it's broken

18. **Freshness alert, independent of the job.** A separate check (cron or the monitoring system, not the job itself) alerts when `max(rate_date)` is older than expected for a business day plus a grace period. This catches the job not running at all, which no in-job logging can.
19. **Failure alerts from the run table.** Alert on any `unparseable` run, and on N consecutive `not_published` runs. A layout change should page someone the same morning with the file name and header that failed. Add a run-summary log line (rows, inserts, revisions, duration) as structured logs with the run id, and chart "days since last good run" and revisions per run on one dashboard. A sudden spike in revisions is itself a signal worth looking at. Each alert links to a short runbook: how to check the bank's page, how to save the new file as a fixture, and how to replay stored payloads after a parser fix.
20. **What would make me add more:** if these rates feed money movement or regulated reporting, add a full role split with audit tables, a second-source cross-check against another provider, and formal SLOs with an on-call rotation. Until then, this is the right-sized plan.
