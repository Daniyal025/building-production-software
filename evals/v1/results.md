> **Superseded.** This v1 evaluation used a rubric written by the skill's author from the skill's own rules, so the 74% → 97% result is circular. See `../README.md` for the blind, independently graded v2 results.

# Results: baseline vs with skill

Three realistic tasks, each answered twice by the same model (`claude-sonnet-5-5`, fresh context): once with no skill, and once with this skill available. All six answers are in `baseline/` and `with-skill/`. They were scored against `rubric.md`, which was fixed before the with-skill answers were read.

| Scenario | Baseline | With skill |
|---|---|---|
| S1 — LLM proposes a price change, admin confirms | 9 / 12 | 12 / 12 |
| S2 — Nightly exchange-rate import (revisions, layout changes) | 9 / 12 | 11 / 12 |
| S3 — Stale stacked branch → review-ready PR | 8.5 / 12 | 12 / 12 |
| **Total** | **26.5 / 36 (74%)** | **35 / 36 (97%)** |

## Where the skill made the difference

The baseline already knew the mainstream practices: history tables, pending proposals, parse-by-header, rebasing before review. The skill added the less obvious rules the baseline missed:

- **S1:** it refuses ambiguous units with a fix message (`2.1` vs `0.021`), records the proposing model, sends the UI and the agent through one shared write function, sends numbers as strings in JSON, and checks the migration as the runtime role.
- **S2:** it reaps stale "running" rows and handles SIGTERM, uses Python `Decimal` and not just NUMERIC, keeps TLS verification on, adds a dead-man's-switch ping, never fills a missing day with yesterday's value, and executes the runbook before merge.
- **S3:** it watches tests fail first, caps the stack depth, links every "later" to an issue, re-reads the description against the final diff, compares against a known-failure baseline, and makes readiness check the schema version.

The one item still missed: **retention** for raw payloads and run logs (S2.12). A good next rule to make more prominent.

## Cost

With the skill, each agent read 3–6 extra short files. Total tokens per task were about 15% higher (≈88k vs ≈76k, including the system prompt).

## Limits — read before quoting these numbers

- One run per condition (n = 1). Model outputs vary between runs.
- The rubric was written by the skill's author and is drawn from the skill's own rules, so it rewards what the skill teaches. Treat this as evidence that the skill *changes behaviour in the intended direction*, not as an independent benchmark.
- Planning answers were graded, not shipped code.

To reproduce, run each prompt in `evals/README.md` in a fresh session with and without the skill installed, then score both against `rubric.md`.
