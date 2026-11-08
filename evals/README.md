# Evaluation

Does loading these skills make an AI agent give better engineering answers and write more robust code? This folder holds every prompt, answer, rubric, grade and script, so you can check the numbers or rerun them.

## Bottom line

- **Code:** the skills reliably improve unstated production robustness. Solutions written with the skills passed **27/27** hidden tests; those written without them passed **22/27**. Every baseline run accepted a float price, and most stored `NaN`.
- **Planning, where the skills hold knowledge the model lacks** (data ingestion with revisions, permission-aware RAG, AI-that-writes-data, at-least-once consumers): consistent gains of **+0.8 to +1.7 out of 12**, larger for the smaller model.
- **Planning on general process tasks a strong model already does well** (a hotfix PR, a small internal tool): **no measurable gain**. On the hotfix task the skills made Sonnet's answer longer and it missed task-specific points (−1.3), while Haiku still improved (+1.5).
- **Across the three held-out tasks** (written after the design, never tuned to): **+0.47/12, p = 0.075. Promising but not statistically established.**

## Rounds

| Round (plugin version) | Scenarios | Baseline | Skills | Difference | Significance |
|---|---|---|---|---|---|
| v1 (1.0.0) | S1–S3, 1 run each, author-written rubric | 74% | 97% | — | **Not credible:** the rubric was circular |
| v2.0 (pre-release) | S1–S5 × 5 runs × 2 models, blind | 9.18/12 | 9.22/12 | +0.04 | p = 0.46: **no effect** |
| v2.1 (2.0.0) | S1–S6 × 5 × 2, blind | 8.90/12 | 9.53/12 | +0.63 | p = 0.008; 95% CI [−0.02, +1.25] |
| v2.2 (2.1.0): targeted fixes | S3, S5 re-run, blind | 8.90/12 | 10.65/12 | **+1.75** | p = 0.0006; 95% CI [+0.75, +2.75] |
| v2.2 (2.1.0): new held-out | S7, S8 (new tasks and rubrics) | 8.95/12 | 8.90/12 | −0.05 | p = 0.62: **no effect** |
| All held-out tasks | S6 (2.0.0) + S7, S8 (2.1.0) | 8.73/12 | 9.20/12 | +0.47 | p = 0.075; 95% CI [−0.30, +1.27] |
| Code task | hidden tests, 3 runs per arm | 22/27 | 27/27 (pre-release and 2.0.0; 2.1.0 didn't change backend rules) | +5 tests | every baseline run failed a robustness test |

**Best current estimate per scenario** (mean score out of 12, n = 5 per arm). S3, S5, S7 and S8 were measured on 2.1.0. S1, S2, S4 and S6 were measured on 2.0.0; 2.1.0 changed only the git/PR and kickoff/deploy rules, which those tasks don't exercise.

| Scenario | Baseline | Skills | Δ |
|---|---|---|---|
| S1 LLM proposes a price change, admin confirms | 9.10 | 10.00 | +0.90 |
| S2 Nightly exchange-rate import | 8.40 | 10.10 | +1.70 |
| S3 Stale stacked branch → review-ready PR | 9.20 | 10.90 | +1.70 |
| S4 At-least-once order consumer | 9.90 | 10.70 | +0.80 |
| S5 Weekend prototype (proportionality) | 8.60 | 10.40 | +1.80 |
| S6 RAG over restricted docs (held-out) | 8.30 | 9.80 | +1.50 |
| S7 Hotfix PR for a live billing bug (held-out) | 9.10 | 8.90 | −0.20 |
| S8 One-week internal booking tool (held-out) | 8.80 | 8.90 | +0.10 |
| **Mean** | **8.93 (74%)** | **9.96 (83%)** | **+1.04** |

The mean mixes two plugin versions and includes tasks that were iterated on. Quote the held-out row above when you need a clean number.

## Method

- **Models:** `claude-sonnet-5-5` (3 runs per arm) and `claude-haiku-5-5` (2 runs per arm), each in a fresh context.
  - *Baseline:* "Answer from your own knowledge; do not read files or use skills."
  - *Skills:* "Read `building-production-software/SKILL.md` and follow its How-to-use steps." Answers were told not to mention the skill, tiers or checklists.
- **Rubrics:** 12 items per task, written by a separate agent prompted as a principal engineer. It saw **only the task text, never the skills**, and was told to reward proportionality and penalise over-engineering.
  - S1–S5: `v2/rubric.md`.
  - S6: `v2.1/rubric-s6.md`, written after the 2.0.0 fixes.
  - S7–S8: `v2.2/rubric-s7-s8.md`, written after the 2.1.0 content was frozen (`v2.2/content.sha256`).
- **Blind grading:** answers were shuffled under random IDs. A scan checked the text for anything revealing the condition. The flags were reviewed: "free tier" hosting mentions appeared in both arms, and two "tier" phrasings in v2.1 were neutralised in the blinded copies only.
  - One grader agent per scenario scored all ten answers (0 / 0.5 / 1 per item) using the prompt in `v2.1/grading/grader-prompt.md`.
  - The key mapping IDs back to conditions was applied afterwards (`*/grading/blind-key.json`).
  - Re-runs mix the original baseline answers with the new skill answers in one blind batch, so each comparison shares a grader.
- **Statistics:** a permutation test stratified by scenario × model (20,000 shuffles) and a bootstrap 95% CI on the difference of means.
- **Code task** (`v2/code-task/`): agents got `task.md` and `schema.sql` and wrote `price_store.py` with no database access. Hidden tests ran against Postgres 18. They were validated first: a reference solution passes 9/9 and a naive one fails 6.
  - 5 tests check the stated spec, including two-connection races; all solutions in both arms pass them.
  - 4 tests check unstated robustness: rejecting a float price, rejecting NaN/Infinity, and 6-way concurrency. Baseline solutions failed 5 of 12; skill solutions failed 0 of 24.
- **Process note:** one 2.1.0 S3 skill run could not write its file and returned its answer inline. The orchestrator saved it verbatim (`v2.2/runs/S3/skill-sonnet-1.md`).

## How the skills changed between rounds, and why

1. **v2.0 → 2.0.0.** Graders found *checklist crowding* (generic items displacing task-specific essentials) and an over-heavy prototype tier.
   - **Fix:** solve the task first, use the checklists only as a gap-check, never pad; lockfiles, scanners and migration tooling moved from T1 to T2.
2. **2.0.0 → 2.1.0.** PR-preparation answers dropped basics (`--force-with-lease`, telling stacked-branch owners, self-review, risks/rollback/reviewer focus), and prototype answers never said where the app runs.
   - **Fix:** a "review-ready pull request" recipe, and T1 items for the deploy path and storage that survives restarts.

Both fixes were informed by grader notes, so the gains on the scenarios they targeted (S1–S5) are not independent evidence. **S6, S7 and S8 are the clean tests.**

## Limitations, read before quoting

- **The held-out evidence is mixed.** One clear win (S6) and two nulls (S7, S8). The pooled held-out effect is not statistically significant.
- **Verbosity risk on strong models.** On S7, Sonnet with the skills wrote longer answers, added follow-ups, and missed task-specific points.
- **The graders and rubric authors are Claude models,** the same family as the answerers. There is a single grader per answer and no inter-rater reliability measure. Independent re-runs with non-Claude graders are the most valuable contribution you could make.
- **n is small:** 5 runs per arm per scenario.
- **Planning answers are not shipped systems.** Only the code task executes anything.

## Reproduce

Run each prompt in a fresh session with and without the plugin. Shuffle and blind the answers, grade them with the grader prompt, and score with `*/grading/score.py`.
