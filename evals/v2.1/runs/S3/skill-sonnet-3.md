## Before asking for review

1. **Rebase onto current main, bottom of the stack first.** Your branch is 3 weeks and 60 commits behind, so integration cost is already high. Rebase (or merge main into) your branch, then rebase the two stacked branches onto the result in order. Tell the owners of those branches before you rewrite history under them.
2. **Test the combined tree, not just your branch.** Clean text merges can still break logic. After the rebase, run the full suite, type-check and build on your branch, then on the top of the stack.
3. **Run CI's exact commands locally** (lint, type-check, tests, same flags). "Passes locally" before the rebase is not evidence for the post-rebase code.
4. **Fix the migration number and ordering.** In 3 weeks main has probably taken your migration's number or timestamp. Renumber or re-slot it after main's latest, and check the stacked branches don't carry migrations that collide with it.
5. **Re-test the migration from three states:** an empty database seeded, a copy of production data, and a second run (must be a no-op). Run it as the runtime role, not the owner. Keep it additive and guarded, and change seed data in the same PR. Never edit it after it has been applied anywhere.
6. **Check deploy order.** The schema must ship before the code that needs it, and readiness should check the schema version. Say whether the migration is backwards compatible with the code currently running during rollout.
7. **Make the renames safe.** Grep every caller, including main's 60 new commits, the two stacked branches, tests, scripts, docs and any dynamic or string references. Main may have added callers of the old names. If any are public or used elsewhere, keep a deprecated alias or note the break.
8. **Split behaviour-neutral renames from the behaviour change if you can.** Ideally a separate commit, or a separate PR. If not, say in the description which hunks are pure renames, so the reviewer can skim them and focus on the real logic.
9. **Redo the timing test on the rebased code,** since main's changes may have shifted the numbers. Run it multiple times against realistic data volume and compare before and after on the same machine. Record p95, not just a single average. If the speedup comes from a new index or query change, attach the `EXPLAIN (ANALYZE, BUFFERS)` plan.
10. **Re-read your own diff** as a reviewer would, and delete leftover debug code and unrelated changes.

## What the PR description should contain

11. **Purpose and scope in a few lines,** with a note that it is stacked, the base branch, and which two branches sit on top. Link the issue.
12. **The migration:** what it does, why it is safe (additive, idempotent, tested from the three states), the deploy order, and the rollback plan. Rollback means fixing forward with a new migration, not editing this one.
13. **The performance claim, reproducible:** what was measured (page, data size, machine, number of runs), before and after numbers, how to rerun it (script or command), and the plan if an index was added. Say "40% faster in this setup" rather than a general claim, and re-check the figure against the final diff.
14. **The renames:** a list of old name to new name, how you verified there are no remaining callers, and whether any compatibility alias exists. Note that these are mechanical so reviewers can skim them.
15. **Review guidance and honesty about gaps:** where to look first, what was and wasn't tested (including the combined-stack test run), and any follow-ups. Each "later" item should link to an issue. Re-read the whole description against the final diff after every review round.
