# Changelog

## 2.1.0 — 2026-11-09

- **New rule:** "Recipe: a review-ready pull request" in `production-delivery/references/git-and-ci.md`:
  - bring the branch current and get CI green on the result;
  - `--force-with-lease` and restack stacked branches, telling their owners;
  - self-review and squash the diff;
  - a description with risks, rollback and reviewer focus;
  - scale the ceremony to the change.
- **New T1 items:** where the app runs and how to (re)deploy it in one command, with data on storage that survives restarts (kickoff and deploy-and-ops).
- **Evals (round v2.2):**
  - the PR-preparation regression is fixed: S3 went from −1.5 to +1.7/12, and S5 from +0.4 to +1.8/12;
  - two new held-out tasks (S7 hotfix PR, S8 internal tool) showed **no effect** (−0.05/12);
  - pooled held-out effect: +0.47/12, p = 0.075.

  Reported as measured; see `evals/README.md`.

## 2.0.0 — 2026-11-09

**Breaking:** the single skill is split into five skills with narrow triggers. `building-production-software` is now the core, alongside `production-backend-and-data`, `production-ai-agents`, `production-frontend` and `production-delivery`. Templates moved to the skills that use them.

- **Proportionality tiers:** all 141 checklist items are tagged T1 every project, T2 production or T3 high-stakes. Claude sets the tier first and applies only the items at or below it.
- **Solve-first workflow:** answer the task from your own expertise first, then use the checklists as a gap-check, and never pad. This fixed the "checklist crowding" found in the v2.0 eval.
- **New areas, from industry practice with cited sources:** events and queues, observability and incidents, performance and scale, API evolution. Also threat modelling, dependency hygiene, privacy, accessibility, i18n, LLM eval gating and cost visibility.
- **Rules are labelled by origin:** *Real case* (from the source project) or *Source* (an industry reference).
- **Blind, independent evals:** 6 scenarios × 5 runs × 2 models, rubrics written by an agent that never saw the skills, blind grading, a held-out scenario, and a code task scored by hidden tests. The v1 self-graded eval is marked superseded.
- Contributor guide and issue templates.

**Known limitation:** advice on preparing a PR regresses with the skills (see `evals/README.md`). A "review-ready PR" recipe is planned.

## 1.0.0 — 2026-11-09

- First public release: one skill, 11 phase references, kickoff, trade-offs, stack equivalents, tested templates, the playbook.
