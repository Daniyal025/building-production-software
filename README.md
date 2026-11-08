# building-production-software

[![template tests](https://github.com/Daniyal025/building-production-software/actions/workflows/test-templates.yml/badge.svg)](https://github.com/Daniyal025/building-production-software/actions/workflows/test-templates.yml)

A Claude Code skill (and a human-readable playbook) of **production engineering rules learned the hard way**. They were distilled from a real project's architecture review, more than a hundred pull-request reviews and about two thousand commits, then generalised for any stack.

> **Core principle: the system must never look more correct than it is.**
> No silent failures, no unverified claims, no second unguarded write path.

## What you get

| | |
|---|---|
| `skills/building-production-software/SKILL.md` | A short index. When to use the skill, which reference to open for each phase, typical bundles, the 8 habits that cause most review findings, and the rationalisations to reject. |
| `references/` (14 files) | One per phase: requirements and design, database, backend and concurrency, data ingestion, AI/LLM features, frontend, security, testing, git and CI, deploy and ops, working with people. Also project kickoff, trade-offs and stack equivalents. Each file starts with a checklist, followed by rules with *why*, a *real case* and a concept to look up. |
| `templates/` | Working code: a migration runner with a checksummed ledger, an append-only `supersede` writer for Postgres, a route-auth fitness test for FastAPI, a binding CI workflow, and a pre-commit config. |
| `templates/tests/` | Self-tests for the templates, including a two-connection race test that fails if the lock is removed. CI runs them on every push. |
| `evals/` | Baseline vs with-skill comparison on three realistic tasks: **74% → 97%** on a fixed rubric. The limits are stated honestly. |
| `docs/Software-and-AI-Engineering-Playbook.docx` | The same rules as a 40-page study guide with a day-0 checklist, trade-offs, 77 flashcards and a glossary. |

## Install

**As a Claude Code plugin** (gets updates):
```
/plugin marketplace add Daniyal025/building-production-software
/plugin install building-production-software@daniyal025-skills
```

**As a personal skill** (copy):
```bash
git clone https://github.com/Daniyal025/building-production-software
cp -r building-production-software/skills/building-production-software ~/.claude/skills/
```

**Per project:** copy the same folder to `.claude/skills/` inside the repository.

## How to use

Claude loads the skill automatically when a task matches. Examples: starting a project, writing a spec, designing a schema or migration, adding routes or auth, building scrapers or ETL, building an LLM agent, writing tests, opening a PR, merging, or deploying. Claude then:

1. picks the phases the task touches (for example, *AI changes data* = ai-agents + backend + database + security + testing);
2. reads each phase's **checklist first**, opening a full rule only when needed;
3. reports every item as applied, skipped (with the reason) or N/A.

You can also ask for it directly:

- *"Use building-production-software to set up this new repo."*
- *"Check this PR against building-production-software."*
- *"Plan this agent feature with the AI bundle from building-production-software."*

## The eight habits

1. **Claim only what the diff proves.** Re-read every PR claim against the final diff; numbers need a reproducing script.
2. **Failure must never look like a value.** Missing in → missing out, with a visible mark. Never 0 or a default.
3. **Name the caller before you add code.** No module, route or table without a caller in the same change.
4. **One guarded write path per resource.** Validate, authorise, lock, version-check and audit in one place.
5. **Watch every test fail first.** Never mock the unit under test or move a gate to make it pass.
6. **Keep branches short-lived.** Integrate daily, keep stacks at 2–3 at most, and test the combined tree.
7. **Exact numbers stay exact.** Decimal from the source text to NUMERIC; strings in JSON.
8. **Applied history is immutable.** Never edit an applied migration, not even a comment. Fix forward.

## Works with

This skill covers *what good looks like*. Process skills cover *how to work*. It points to them instead of repeating them: [superpowers](https://github.com/obra/superpowers) (`test-driven-development`, `verification-before-completion`, `systematic-debugging`, `brainstorming`) and any ADR/architecture skill.

## Run the template tests

```bash
pip install "psycopg[binary]" pytest fastapi httpx
DATABASE_URL=postgresql://user@localhost/throwaway_db pytest skills/building-production-software/templates/tests
```
Point `DATABASE_URL` at a throwaway database. Each test creates and drops its own schema.

## Contributing

Issues and PRs are welcome, especially rules backed by a real failure, stack equivalents, and new eval scenarios. Keep the format: a checklist line, then the rule with *why*, a *real case* and *look up*.

## License

[MIT](LICENSE) © 2026 Syed Daniyal Ali
