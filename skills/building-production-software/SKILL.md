---
name: building-production-software
description: Use when starting a new software or AI project, deciding how much engineering rigour a project needs, writing a spec or design, deciding what to build, writing a handover or status update, or preparing work for review.
---

# Building Production Software

## Overview
Engineering rules learned the hard way on a real production system (Python API, Postgres, React, web scrapers, an LLM agent, Docker deploy), generalised for any stack and extended with established industry practice. Rules from the real project cite a **real case**; rules from industry practice cite a **source**.

**Core principle: the system must never look more correct than it is** — no silent failures, no unverified claims, no second unguarded write path.

## Tiers — decide first
| Tier | Name | Applies to |
|---|---|---|
| T1 | Every project | Prototypes, spikes, internal tools, demos. Cheap rules that prevent the worst failures. Apply all of them. |
| T2 | Production | Real users or real data, more than one developer, or anything you must keep running. Apply T1 + T2. |
| T3 | High-stakes | Money, regulated or personal data, multiple teams/services, or an AI that can change data. Apply T1 + T2 + T3. |

## How to use
1. **Set the tier** (T1 every project · T2 production · T3 high-stakes). Pick the tier first. Apply every item at or below it. Adding a higher-tier item to a lower-tier project needs a stated reason — otherwise it is speculative work (YAGNI). When in doubt between two tiers, take the lower one and write down what would move you up.
2. **Solve the task first, from your own expertise.** Work out the domain-specific design, the failure modes of *this* system and what the user actually asked for, in the length and format they asked for. The rules here do not replace that thinking.
3. **Then gap-check.** Open the reference checklist for each area the task touches and look for items at or below the tier that you missed *and that change this task's outcome*. Add those by replacing your weakest point — don't grow the answer past what was asked.
4. **Never pad.** Don't add generic process items (lockfiles, hooks, scanners, CI) unless the task is about project setup or delivery. Don't paste the checklist or report it item by item unless the user asks for a review or audit.
5. Starting a project? Read `references/project-kickoff.md`. A rule seems wrong here? Check `references/tradeoffs.md`. Not on Python/Postgres/React? Use `references/stack-equivalents.md`.

## Where the rules live
| Area | Skill | Reference |
|---|---|---|
| Requirements and design | `building-production-software` | `references/requirements-and-design.md` |
| Working with people | `building-production-software` | `references/working-with-people.md` |
| Database and migrations | `production-backend-and-data` | `references/database.md` |
| Backend and concurrency | `production-backend-and-data` | `references/backend-and-concurrency.md` |
| Security | `production-backend-and-data` | `references/security.md` |
| Events, queues and background work | `production-backend-and-data` | `references/events-and-queues.md` |
| Data ingestion and scrapers | `production-backend-and-data` | `references/data-ingestion.md` |
| Performance and scale | `production-backend-and-data` | `references/performance-and-scale.md` |
| API evolution and change management | `production-backend-and-data` | `references/api-evolution.md` |
| AI and LLM features | `production-ai-agents` | `references/ai-agents.md` |
| Frontend and UX | `production-frontend` | `references/frontend.md` |
| Testing | `production-delivery` | `references/testing.md` |
| Git, pull requests and CI | `production-delivery` | `references/git-and-ci.md` |
| Deployment and operations | `production-delivery` | `references/deploy-and-ops.md` |
| Observability and incidents | `production-delivery` | `references/observability-and-incidents.md` |

If a sibling skill isn't loaded, read its file directly from the plugin's `skills/<skill>/references/` folder.

Typical bundles:
- **New project:** this skill (kickoff) → set the tier → the areas you will build.
- **AI/LLM changes data:** production-ai-agents + production-backend-and-data (database, backend, security) + production-delivery (testing).
- **New write endpoint:** production-backend-and-data (backend, database, security) + production-delivery (testing).
- **Queue consumer or scraper:** production-backend-and-data (events or ingestion, database) + production-delivery (observability).
- **PR, merge or release:** production-delivery (git-and-ci — start with its review-ready PR recipe — testing, deploy-and-ops).

## Habits that cause most review findings

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
| "I'll add the guard to this one route" | Second write paths are the costliest bug class. Reuse the one guarded path. |
| "It passed locally" | Run CI's exact commands; local "N passed" is not evidence. |
| "Just a comment in an old migration" | Checksums change; every database refuses. Fix forward. |
| "Loosen the test, it's too strict" | Fix the cause; only the owner moves a gate, on the record. |
| "Might need it later" | Name the caller now, or it's above this project's tier. |
| "Production-grade from day one" | Rigour beyond the tier is cost without a caller. Apply the tier, note what would move you up. |
| "The model will send the right unit" | Validate tool args on the server like any untrusted input. |
| "The checklist has 12 items — I'll cover them all" | The user asked a specific question. Answer it first; checklist items are a gap-check, not content. |

## Related skills
This plugin says *what good looks like*; process skills say *how to work*. If available, use `superpowers:test-driven-development`, `superpowers:verification-before-completion`, `superpowers:systematic-debugging` and `superpowers:brainstorming` for the process, and an ADR skill for recording decisions.
