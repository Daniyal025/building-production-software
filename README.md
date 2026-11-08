# building-production-software

[![template tests](https://github.com/Daniyal025/building-production-software/actions/workflows/test-templates.yml/badge.svg)](https://github.com/Daniyal025/building-production-software/actions/workflows/test-templates.yml)

A Claude Code plugin of **production engineering rules with proportionality tiers**, plus a human-readable playbook. The rules were distilled from a real project's architecture review, more than a hundred pull-request reviews and about two thousand commits. They were then generalised for any stack and filled out with established industry practice.

> **Core principle: the system must never look more correct than it is.**
> No silent failures, no unverified claims, no second unguarded write path.

## Does it work? (blind-graded)

| Test | Without | With | |
|---|---|---|---|
| 6 planning tasks × 5 runs × 2 models, independent blind rubric | 74% | **79%** | +0.63/12, p = 0.008 |
| Held-out task (internal RAG over restricted docs), never seen during design | 8.3/12 | **9.8/12** | +1.5, p = 0.009 |
| Code task scored by 9 hidden tests (concurrency, money types, NaN) | 22/27 | **27/27** | every baseline run accepted a float price |

There is one known regression: advice on preparing a pull request is weaker with the skills (−1.5/12). Full method, every answer, the grades and the limits are in [`evals/`](evals/README.md). An earlier version showed **no** effect under blind grading; that result is published too.

## What you get

**Five skills with narrow triggers**, so only the relevant one loads:

| Skill | Loads when you… | Covers |
|---|---|---|
| `building-production-software` | start a project, decide how much rigour it needs, write a spec, hand over work | Tiers, kickoff, requirements and design, working with people, trade-offs, stack equivalents, and a router to the others |
| `production-backend-and-data` | design schemas or migrations, add routes or write paths, handle money/units/auth, caching, locks, jobs, queues, scrapers, API versions, slow endpoints | Database, backend and concurrency, security, events and queues, data ingestion, performance and scale, API evolution, plus templates |
| `production-ai-agents` | build an LLM agent, RAG or tool-calling feature, choose models, change prompts, manage cost/latency, let an AI change data | Server-decided consent, tool contracts, grounding, memory and caching, evals, budgets |
| `production-frontend` | build UI, forms, editable grids, API clients, save states, accessibility, i18n | Request layer, honest feedback, state ownership, a11y, i18n, sanitising HTML |
| `production-delivery` | write tests, set up CI, open/merge PRs, deploy, set up backups, monitoring, on-call, incidents | Testing, git and CI, deploy and ops, observability and incidents, plus CI and pre-commit templates |

**Proportionality tiers.** Every one of the 141 checklist items is tagged:
- **T1, every project.** Even a weekend prototype: exact money types, secrets out of git, one self-check, a gate if it's reachable.
- **T2, production.** Real users or data.
- **T3, high-stakes.** Money, personal data, several teams, or an AI that changes data.

Claude picks the tier first and applies only the items at or below it.

**Rules with their evidence.** 103 rules. Each has *Why*, then a **Real case** (something that happened in the source project) or a **Source** (a named industry reference), then a concept to look up.

**Tested templates.**
- A forward-only migration runner with a checksummed ledger.
- An append-only `supersede()` writer for Postgres.
- A route-auth fitness test for FastAPI (works on the latest FastAPI, where included routers are no longer flattened into `app.routes`).
- A binding CI workflow and a pre-commit config.

The first three are covered by 7 tests, including a two-connection race test that fails if the lock is removed.

**Playbook.** [`docs/Software-and-AI-Engineering-Playbook.docx`](docs/) has the same rules as a study guide: tiers, a day-0 checklist, the eight habits, trade-offs, 103 flashcards and a glossary.

## Install

**Claude Code plugin** (recommended, gets updates):
```
/plugin marketplace add Daniyal025/building-production-software
/plugin install building-production-software@daniyal025-skills
```

**Manual:**
```bash
git clone https://github.com/Daniyal025/building-production-software
cp -r building-production-software/skills/* ~/.claude/skills/
```

## How it works

When a task matches, Claude:
1. **sets the tier** (prototype, production or high-stakes);
2. **solves the task first** from its own expertise: the domain design, this system's failure modes, and what you asked for, in your format;
3. **gap-checks** against the relevant checklists, adding only items at or below the tier that change the outcome, by replacing weaker points rather than growing the answer;
4. **never pads**: no generic process items unless the task is about setup or delivery, and no checklist dumps unless you ask for an audit.

You can also invoke it directly:
- *"Set up this new repo with building-production-software; it's a prototype."*
- *"Review this PR against production-delivery."*
- *"Plan this RAG feature with production-ai-agents."*

## The eight habits

1. **Claim only what the diff proves.** Every number needs a reproducing script.
2. **Failure must never look like a value.** Missing in → missing out, with a visible mark.
3. **Name the caller before you add code.** No caller, no code.
4. **One guarded write path per resource.** Validate, authorise, lock, version-check and audit in one place.
5. **Watch every test fail first.** Never bend a gate to make it pass.
6. **Keep branches short-lived.** Integrate daily; stacks of 2–3 at most.
7. **Exact numbers stay exact.** Decimal from the source text to NUMERIC; strings in JSON.
8. **Applied history is immutable.** Never edit an applied migration; fix forward.

## Works with

This plugin covers *what good looks like*. Process skills cover *how to work*. It defers to [superpowers](https://github.com/obra/superpowers) (`test-driven-development`, `verification-before-completion`, `systematic-debugging`, `brainstorming`) and to any ADR skill.

## Run the template tests

```bash
pip install "psycopg[binary]" pytest fastapi httpx
DATABASE_URL=postgresql://user@localhost/throwaway_db pytest skills/production-backend-and-data/templates/tests
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Most wanted:
- rule feedback from other stacks and domains;
- real failure cases;
- eval scenarios;
- independent re-runs of the evals, especially with non-Claude graders.

## License

[MIT](LICENSE) © 2026 Syed Daniyal Ali
