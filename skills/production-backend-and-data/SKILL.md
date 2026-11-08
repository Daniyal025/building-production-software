---
name: production-backend-and-data
description: Use when designing a database schema or migration, adding API routes or write paths, handling auth, permissions or secrets, money, units or dates, caching, locks or connection pools, background jobs, queues or event consumers, scrapers or ETL, versioning an API, or fixing slow endpoints.
---

# Production Backend and Data

## Overview
Part of the **building-production-software** plugin: production rules for backend and data, each backed by a real case from a production system or an industry source. **Core principle: the system must never look more correct than it is.**

## Tiers
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

## References
| Area | File |
|---|---|
| Database and migrations — designing a schema, writing or reviewing a migration, adding a table, column, index or constraint, setting up roles, restoring a dump | `references/database.md` |
| Backend and concurrency — writing API routes, business logic, caching, background jobs or schedulers; handling money, rates, dates or units; anything with locks, pools, retries or concurrent users | `references/backend-and-concurrency.md` |
| Security — adding authentication or authorisation, exposing a service publicly, handling secrets, setting up proxies, tunnels or webhooks, copying production data | `references/security.md` |
| Events, queues and background work — building message consumers or producers, queues, webhooks handlers, outbox/event publishing, retries, dead-letter queues or async workflows | `references/events-and-queues.md` |
| Data ingestion and scrapers — building scrapers, PDF/HTML/CSV parsers, ETL jobs, webhooks consumers or any pipeline that reads external data | `references/data-ingestion.md` |
| Performance and scale — a page or endpoint is slow, adding caching, pagination or background processing, preparing for more users or data, load testing, or setting performance budgets | `references/performance-and-scale.md` |
| API evolution and change management — changing a public or internal API, event schema or database contract used by other teams or clients, versioning, deprecating, or rolling out risky changes with feature flags | `references/api-evolution.md` |

## Templates
Working, tested starting points in `templates/` (adapt names and paths):
- `templates/migrate.py`
- `templates/supersede.sql`
- `templates/test_route_auth.py`

Self-tests: `templates/tests/` (needs a throwaway Postgres in `DATABASE_URL`).

For project kickoff, trade-offs, stack equivalents and the habits behind most review findings, see the `building-production-software` skill.
