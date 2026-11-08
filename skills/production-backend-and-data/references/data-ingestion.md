# Data ingestion and scrapers

Use when building scrapers, PDF/HTML/CSV parsers, ETL jobs, webhooks consumers or any pipeline that reads external data.

Tiers: **T1** every project · **T2** production · **T3** high-stakes. Apply items at or below the project's tier.

## Checklist (read first)

**T1**

- [ ] A document that parses to zero rows, or can't be parsed, fails the run and names the document.
- [ ] Columns found by header text, not position; exact types from source text.

**T2**

- [ ] Staleness alert: expected data overdue → alert, independent of the job itself.
- [ ] Raw payload stored, deduplicated by hash, so a parser fix can replay history.
- [ ] One HTTP client with timeout, retry with backoff on transient errors, TLS verification on.
- [ ] Re-read the window the source can still revise; backfills idempotent (second run → zero changes).
- [ ] Retention period for raw payloads and run logs, enforced by a nightly sweep.
- [ ] Saved real-page fixture per layout and per sign; plausibility checks before writing.

**T3**

- [ ] Security-relevant text matched against anchored allowlists; Unicode normalised; explicit encodings.

## Rules

### 1. Zero rows is a failure; staleness is an alert
- Distinguish not-published, fetched-but-unparseable, and parsed-N-rows; only the first is quiet.
- Store the parser's error on the run row; alert after N consecutive failures and when expected data is overdue.
- **Why:** Silent ingestion failures are discovered by customers.
- **Real case:** A table shifted 23pt on the page: 288 runs reported "nothing new"; a date-format change skipped 21 notices.
- **Look up:** Data-freshness SLOs.

### 2. Expect format change
- Locate columns by header text, not coordinates; one saved real page per layout and per sign as a fixture.
- Store raw bytes deduped by hash so fixes can replay history; reject implausible values.
- One HTTP client: retry with backoff, rate limits, TLS verification always on.
- **Why:** Every external source changes eventually.
- **Real case:** Decreases written in words parsed as increases; "Sept" crashed a run; one stack had TLS verification off.
- **Look up:** Brittle scraping; raw/bronze layer.

### 3. Treat external text as hostile
- Security decisions match the whole input against an allowlist — never "contains" or unanchored regex.
- Normalise Unicode (quotes, apostrophes) before matching; always pass an explicit encoding.
- **Why:** Humans write variants your test fixtures don't.
- **Real case:** An unanchored consent regex accepted "I confirm nothing" and "Don’t apply it".
- **Look up:** Allowlist vs denylist.

