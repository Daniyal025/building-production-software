---
name: production-frontend
description: Use when building web UI, forms, editable tables or grids, API clients, loading and saving states, mobile layouts, accessibility or internationalisation, or rendering server or LLM-generated HTML.
---

# Production Frontend

## Overview
Part of the **building-production-software** plugin: production rules for frontend, each backed by a real case from a production system or an industry source. **Core principle: the system must never look more correct than it is.**

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
| Frontend and UX — building UI, forms, editable grids, API clients, loading/saving states, mobile layouts or rendering server/LLM HTML | `references/frontend.md` |

For project kickoff, trade-offs, stack equivalents and the habits behind most review findings, see the `building-production-software` skill.
