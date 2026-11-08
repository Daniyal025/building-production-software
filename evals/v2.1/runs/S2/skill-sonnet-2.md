# Nightly central-bank FX rate job: plan

Assumption: this is production (real data, other code reads the rates). If the rates feed money movement or regulated reporting, add the "later" items at the end.

## Schema

- **`fx_raw_payload`**: `id`, `sha256` (unique), `fetched_at`, `source_url`, `bytes` (bytea). Keep every distinct download. If you fix the parser, or the bank changes layout, you can replay history instead of re-fetching.
- **`fx_rate`**: PK `(rate_date, currency)`. `rate NUMERIC(18,8)` (never float), `payload_id` FK, `first_seen_at`, `updated_at`. This is the current truth that other code reads.
- **`fx_rate_revision`**: append-only. A row is written (old rate, new rate, payload_id, time) only when the bank changes an already-stored value. This answers "what did we believe on day X" and shows how often the bank revises.
- **`fx_job_run`**: `started_at`, `finished_at`, `status` (`ok` / `no_change` / `failed`), `payload_id`, `rows_parsed`, `rows_inserted`, `rows_revised`, `error`. Every run writes one row, including failures.

## The job

- **Fetch** with a single HTTP client: timeout, retry with backoff on 5xx and timeouts, TLS verification on, and a clear User-Agent. Store the bytes in `fx_raw_payload` before parsing (skip the insert if the hash already exists).
- **Parse by header name, not column position.** Normalise headers (case, whitespace, BOM). Require a known set of headers; if one is missing, fail with a message naming the missing column and the payload hash. Never guess a new layout.
- **Keep exact values.** Parse rates with `Decimal` straight from the text. Reject rows that are empty, non-numeric, zero or negative. Handle the bank's decimal separator and date format explicitly.
- **Plausibility check before writing.** If a rate moves more than X% from the previous day, or the file has far fewer currencies or days than last time, fail the run and write nothing. A bad file must not overwrite good data.
- **Zero rows parsed is a failure**, not "nothing new". Only "file is identical to last hash" counts as the quiet case (`no_change`).
- **Re-read the whole window the bank can still revise** (e.g. the full file, or the last N days). Upsert in one transaction: insert new rows, update changed rows and log them to `fx_rate_revision`, leave identical rows alone. A second run on the same file must change nothing.
- **One run at a time:** take a Postgres advisory lock so overlapping or manually triggered runs can't interleave. Run it from cron or your existing scheduler at a time after the bank usually publishes, with a catch-up on the next night if it was late.

## Tests

- **Saved real files as fixtures:** one per layout version (old and new), plus one with a revised day. Write each test and watch it fail before you write the code.
- **Parser tests:** reordered columns still parse, a renamed or missing header fails loudly, an empty file fails, and bad values (`""`, `n/a`, `0`, a comma decimal) are rejected.
- **DB tests against real Postgres** (not mocks): first load, an identical re-run gives zero changes, a revised day updates `fx_rate` and adds one revision row, and a failed run (e.g. a plausibility failure) leaves `fx_rate` untouched.

## How we'll know it breaks

- **Failure alert:** page or notify when the run fails, with the stored error and payload hash. Alert after 2 consecutive failures to cut noise from a one-off network blip.
- **Freshness alert, independent of the job:** a separate check queries `max(rate_date)` and the last `ok` run. If it's older than expected (allow for weekends and bank holidays), alert. This catches the case where the job didn't run at all or silently thought there was nothing new.
- **Dashboard line and runbook:** show last successful run, latest rate date and revisions per week. The alert links to a short runbook: re-run command, how to replay a stored payload after a parser fix, and who owns the bank contact.

## Later (only if it becomes true)

- Money or regulatory use: add an audit trail of who triggered manual re-runs and a second-source cross-check of rates.
- Retention: sweep old raw payloads and run logs on a schedule once storage matters.
