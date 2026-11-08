# Rubric

Fixed before the with-skill runs were read. Each item scores 1 (clearly present), 0.5 (partly or implied) or 0 (absent). 12 items per scenario.

## S1 — An LLM proposes a price change, an admin confirms, prices keep history

1. Append-only history with a database-enforced single current row
2. Exact decimal type end to end (NUMERIC + Decimal, numbers as strings in JSON)
3. Unit or ambiguity handling (absolute vs percent, currency) refused on the server with a fix message
4. Actor and origin recorded on every write
5. The tool never writes; it creates a pending action with an expiry
6. Confirmation verified by server code, not by a model-chosen argument
7. Permissions re-checked at execution time
8. The proposing model is recorded
9. One guarded write function shared by the human path and the agent path
10. Stale-revision check under a lock, answered with 409
11. Concurrency tested with two real connections
12. Adversarial confirmation tests (model-supplied "confirm", text inside tool output, non-admin)

## S2 — Nightly exchange-rate CSV import; the source revises past days and changes layout

1. Append-only revision history (no silent overwrite)
2. Re-reads the window the source can still revise
3. Raw payload stored and deduplicated by hash
4. Parses by header names, with a fixture per layout
5. Unparseable file, layout mismatch or zero rows = failed run that names the document
6. Staleness alert independent of the job itself
7. Per-job lock, safe to run twice
8. Stale "running" rows reaped at startup and/or SIGTERM handled
9. Python `Decimal` (not float) as well as NUMERIC
10. One HTTP client with retry/backoff and TLS verification kept on
11. Plausibility checks on values
12. Retention policy for raw payloads and run logs

## S3 — Three-week-old branch, two stacked branches, main 60 commits ahead, a migration, a 40% speed claim, renames

1. Integrates main and runs the full suite on the result
2. Restacks dependents and tests the combined tree
3. Runs CI's exact commands locally (lint, type-check, build)
4. Migration: number-collision check and tests from empty, production copy and re-run
5. Deploy order: schema before code (expand/contract)
6. Splits behaviour-neutral renames from the behaviour change
7. Speed claim reproducible (script, repeated runs) or labelled as a one-off
8. Re-reads the description against the final diff
9. New tests seen failing first
10. Reduces stack depth / lands the base soon (work-in-progress limit)
11. Deferred follow-ups linked to issues
12. Semantic-conflict awareness (renamed symbols searched in other open branches, rule tests)
