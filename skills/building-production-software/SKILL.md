---
name: building-production-software
description: Use when starting a new software or AI project, writing a spec, designing a schema or migration, adding API routes, auth or write paths, building scrapers, schedulers or ETL, building an LLM agent or tool-calling feature, writing tests, opening or reviewing a PR, merging or rebasing branches, or preparing a deployment, runbook or backup.
---

# Building Production Software

## Overview
Rules learned the hard way on a real production project (Python/FastAPI + Postgres + React + LLM agent + scrapers, Docker deploy), generalised for any stack. **Core principle: the system must never look more correct than it is** — no silent failures, no unverified claims, no second unguarded path.

## How to use
1. Pick every phase the task touches (bundles below) and open those reference files.
2. In each file read the **Checklist first**; open a numbered rule only for items you can't apply from the one-liner.
3. Report each checklist item as applied, skipped (why) or N/A.
4. Starting a brand-new project? Read `references/project-kickoff.md` first.
5. When a rule seems wrong for the situation, check `references/tradeoffs.md`. Not on Python/Postgres/React? Use `references/stack-equivalents.md`.
6. Need working code? `templates/` has a migration runner with a checksummed ledger, an append-only `supersede` writer, a route-auth fitness test, a CI workflow and a pre-commit config; the first three are covered by `templates/tests`.

## Related skills
This skill says *what good looks like*; process skills say *how to work*. If they are available, use them for the process and this skill for the rules — don't duplicate them:
- `superpowers:test-driven-development` for the red-green loop behind "watch every test fail first".
- `superpowers:verification-before-completion` for "claim only what the diff proves".
- `superpowers:systematic-debugging` before fixing any bug; `superpowers:brainstorming` before designing.
- An ADR/architecture skill for recording decisions (e.g. `engineering:architecture`).

| Phase | Read |
|---|---|
| Requirements and design | `references/requirements-and-design.md` |
| Database and migrations | `references/database.md` |
| Backend and concurrency | `references/backend-and-concurrency.md` |
| Data ingestion and scrapers | `references/data-ingestion.md` |
| AI and LLM features | `references/ai-agents.md` |
| Frontend and UX | `references/frontend.md` |
| Security | `references/security.md` |
| Testing | `references/testing.md` |
| Git, pull requests and CI | `references/git-and-ci.md` |
| Deployment and operations | `references/deploy-and-ops.md` |
| Working with people | `references/working-with-people.md` |
| Starting a new project | `references/project-kickoff.md` |

Typical bundles:
- **AI/LLM changes data:** ai-agents (rule 2 is the recipe) + backend-and-concurrency + database + security + testing.
- **New write endpoint:** backend-and-concurrency + database + security + testing.
- **New scraper/ETL job:** data-ingestion + database + backend-and-concurrency (jobs) + deploy-and-ops.
- **Opening a PR or merging:** git-and-ci + testing.

## Habits that cause most review findings (red flags)

- **Claim only what the diff proves.** Before asking for review, re-read the PR description, docs and comments against the final diff.
- **Failure must never look like a value.** A missing input gives a missing output with a visible mark — never 0, the previous value or a default.
- **Name the caller before you add code.** No module, route, table, registry or option without a caller in the same change.
- **One guarded write path per resource.** Every mutation goes through one function that validates, authorises, locks, version-checks and audits.
- **Watch every test fail first.** A test that never failed proves nothing.
- **Keep branches short-lived.** Integrate main daily, keep stacks at most 2–3 deep, and test the combined result before the final run.
- **Exact numbers stay exact.** Money, rates and measurements use Decimal from the source text to a NUMERIC column, and travel as strings in JSON.
- **Applied history is immutable.** Never edit an applied migration (not even a comment), a published API contract, or recorded data in place.

## Rationalizations to reject
| Thought | Reality |
|---|---|
| "The failure case is rare, a default is fine" | A plausible wrong value is worse than an error. Propagate missing; mark it. |
| "I'll add the guard to this one route" | Second write paths were the costliest bug class. Reuse the one guarded path. |
| "It passed locally" | Run CI's exact commands; local "N passed" is not evidence. |
| "Just a comment in an old migration" | Checksums change; every database refuses. Fix forward. |
| "The test is flaky/too strict, loosen it" | Fix the cause; only the owner moves a gate, on the record. |
| "Might need it later" | Name the caller now or don't build it. |
| "The model will send the right unit" | Validate tool args on the server like any untrusted input. |
| "The description is close enough" | Re-read it against the final diff; overstated claims cost trust. |
