# Evaluation

Does loading these skills make an AI agent give better engineering answers and write more robust code? This folder holds every prompt, answer, rubric, grade and script, so you can check the numbers or rerun them.

## Headline results

| Round | What was tested | Baseline | With skills | Difference | Significance |
|---|---|---|---|---|---|
| **v2.1** (current) | 6 planning tasks × 5 runs × 2 models, blind-graded | 8.90 / 12 (74%) | 9.53 / 12 (79%) | **+0.63** | p = 0.008; 95% CI [−0.02, +1.25] |
| **v2.1 held-out** | S6 only: a task and rubric nobody had seen while designing the fixes | 8.30 / 12 | 9.80 / 12 | **+1.50** | p = 0.009; 95% CI [+0.60, +2.60] |
| **Code task** | Implement a concurrent price writer; scored by 9 hidden tests | 22 / 27 tests | 27 / 27 tests | **+5** | Every baseline run failed the unstated robustness tests |
| v2.0 (superseded) | 5 tasks × 5 runs × 2 models, blind-graded | 9.18 / 12 | 9.22 / 12 | +0.04 | p = 0.46: **no effect** |
| v1 (superseded) | 3 tasks × 1 run; rubric written by the skill's author | 74% | 97% | — | Not credible: the rubric was circular |

The honest summary:
- **The v2.0 skills did not help** under independent grading.
- The v2.1 fixes (solve-first workflow, slimmer prototype tier) produced a **modest, statistically detectable improvement overall**.
- There is a **clear improvement on a held-out task**, and a **robust improvement on unstated production qualities in code**.
- There is a **known regression on PR-preparation advice** (see Limitations).

## Per-scenario (v2.1, mean score out of 12, n = 5 per arm)

| Scenario | Baseline | Skills | Δ | Sonnet Δ | Haiku Δ |
|---|---|---|---|---|---|
| S1 LLM proposes a price change, admin confirms | 9.10 | 10.00 | +0.90 | −0.17 | +2.50 |
| S2 Nightly exchange-rate import (revisions, layout changes) | 8.40 | 10.10 | +1.70 | +1.50 | +2.00 |
| S3 Stale stacked branch → review-ready PR | 9.20 | 7.70 | **−1.50** | −1.33 | −1.75 |
| S4 At-least-once "order paid" consumer | 9.90 | 10.70 | +0.80 | +1.17 | +0.25 |
| S5 Weekend prototype (proportionality) | 8.50 | 8.90 | +0.40 | +0.67 | 0.00 |
| **S6 Internal RAG over restricted docs (held-out)** | 8.30 | 9.80 | **+1.50** | +1.17 | +2.00 |

The skills help the smaller model (Haiku) more: +0.84 vs +0.50 for Sonnet.

## Method

- **Models:** `claude-sonnet-5-5` (3 runs per arm) and `claude-haiku-5-5` (2 runs per arm), each in a fresh context.
  - *Baseline:* "Answer from your own knowledge; do not read files or use skills."
  - *With skills:* "Read `building-production-software/SKILL.md` and follow its How-to-use steps." Answers were told not to mention the skill, tiers or checklists.
- **Rubrics:** a separate agent, prompted as a principal engineer, wrote 12 items per task. It saw **only the task prompts, never the skills**, and was told to reward proportionality and penalise over-engineering.
  - S1–S5 rubrics: `v2/rubric.md`.
  - Held-out S6 rubric: `v2.1/rubric-s6.md`, written **after** the v2.1 fixes.
- **Blind grading:** answers were shuffled under random IDs (`R01`…`R10`). A scan removed any answer text revealing the condition; two uses of "tier" were reworded in the blinded copies only, and the originals are kept. One grader agent per scenario scored all ten answers against the rubric (0 / 0.5 / 1 per item) and wrote JSON. The key that maps IDs back to conditions was applied only afterwards (`*/grading/blind-key.json`).
- **v2.1 grading:** the existing baseline answers were mixed with the new v2.1 skill answers and **re-graded together in one blind batch**, so each comparison shares a grader.
- **Statistics:** a permutation test stratified by scenario × model (20,000 shuffles), and a bootstrap 95% CI on the difference of means (`v2.1/grading/score.py`).
- **Code task** (`v2/code-task/`): agents got `task.md` and `schema.sql` and wrote `price_store.py` with no database access. Hidden tests (`v2/code-task/hidden_tests/`) ran against Postgres 18. The tests were validated first: a reference solution passes 9/9 and a naive one fails 6/9.
  - 5 tests check the stated spec, including two-connection races. All 6 baseline and all 6 skill solutions pass all of them.
  - 4 tests check unstated production robustness: rejecting a float price, rejecting NaN/Infinity, and 6-way concurrency. Baseline solutions failed 5 of the 12 robustness checks across runs; skill solutions failed none, in both v2.0 and v2.1.

## What changed between v2.0 and v2.1, and why

The v2.0 graders' notes showed two failure modes:
1. **Checklist crowding.** Models spent their answer on generic checklist items and dropped task-specific essentials. For example, the S4 answers missed the reconciliation job, and one Haiku answer to the prototype task never named a stack.
2. **An over-heavy prototype tier.** Lockfiles, secret-scanner hooks and versioned schema files were penalised as padding for a weekend app.

v2.1 changed the *How to use* steps to: solve the task first; use the checklists only as a gap-check that replaces weak points; never pad. It also moved those items from T1 to T2. Rule content was otherwise unchanged; checksums are in `v2/frozen-content.sha256` and `v2.1/v2.1-content.sha256`.

**Disclosure:** these fixes were made after reading v2.0's grader notes, so the S1–S5 improvement is not fully independent evidence. **S6 is the clean test:** its task and rubric were created after the fixes, and nothing was tuned to it.

## Limitations, read before quoting

- **Regression on S3 (PR preparation).** With the skills, answers emphasise migration and integration rigour and drop basic PR craft: `--force-with-lease`, notifying the owners of stacked branches, self-reviewing the diff, and naming risks, rollback and reviewer focus. The git reference lacks a "review-ready PR" recipe. This is not fixed in the published version, to avoid tuning to the rubric; it is the top item for the next release.
- **S5 answers omitted where and how the prototype runs.** The T1 kickoff list has no "deploy path / persistent storage" item.
- **The graders and rubric author are Claude models,** the same family as the answerers. There is a single grader per answer and no inter-rater reliability measure.
- **n is small** (5 runs per arm per scenario), and the overall CI just touches zero. The held-out and code-task results are the strongest evidence.
- **Planning answers are not shipped systems.** Only the code task executes anything.

## Reproduce

Run each prompt (`v2/rubric.md` for S1–S5, `v2.1/rubric-s6.md` for S6) in a fresh session, with and without the plugin. Blind and shuffle the answers, grade them with the same grader prompt (in `v2.1/grading/`), and score with `v2.1/grading/score.py`. Contributions of independent re-runs, especially with non-Claude graders, are very welcome.
