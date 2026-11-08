## Before asking for review

1. **Bring the branch current with main first.** 60 commits and 3 weeks is where the real risk is. Rebase (or merge, if that's your team's convention) onto today's main and resolve conflicts deliberately, not by taking "ours".
2. **Renumber the migration.** Someone else has very likely taken your migration number or timestamp in 60 commits. Re-order it after main's latest migration. Never edit a migration that main already applied.
3. **Test the migration three ways:** empty DB to seed, a copy of production data, and a second run (it must be idempotent and additive). Run it as the runtime DB role, not the owner. Update seed data in the same PR.
4. **Run CI's exact commands on the rebased result.** Lint, type-check, full test suite and build. "Passes locally" on a 3-week-old base is not evidence. Expect semantic conflicts: a clean text merge can still fail tests, especially around the renamed helpers that new main code may call under the old names.
5. **Grep for every remaining use of the old helper names** (code, tests, docs, scripts, other branches). If any are called through strings, reflection or config, a type-check won't catch them.
6. **Push with `--force-with-lease`** after the rebase. Never plain `--force`.
7. **Restack the two dependent branches in order** (`git rebase --onto` or `--update-refs`), re-run tests on each, and tell their owners. State the stack order and merge order in the PR. A stack this deep on a stale base should be merged soon and not allowed to age further.
8. **Self-review the whole diff against main.** Remove debug code and squash fixups. Put the helper renames in their own mechanical commit, separate from the behaviour change, so reviewers can skim them. If the renames aren't needed for the feature, split them into a separate PR.
9. **Re-measure the 40%.** The number came from the old base. Re-run the timing on the rebased branch, on realistic data volume, against main as the baseline, several runs, and keep the script. If a new index is involved, include the `EXPLAIN (ANALYZE, BUFFERS)` plan.

## What the PR description should contain

10. **What and why, plus the linked issue.** Keep it to one purpose, and match it to the final diff after the rebase and after every review round.
11. **Performance claim, reproducible.** Say what was measured (page, data size, before and after numbers, how many runs, environment) and link or attach the script. Say "40% on X", not just "40% faster". Don't imply the speedup applies elsewhere.
12. **Migration notes.** Say what it changes, whether it's additive and reversible, whether it takes locks or rewrites a table, and the deploy order: schema first, then code. Say how you tested it (the three states above).
13. **Rename notes.** List old to new names, point to the mechanical commit, and say whether anything outside the repo (other services, scripts, the two stacked branches) depends on the old names.
14. **Testing done and not done.** Include the CI run link. Say plainly what you didn't test, such as production-scale data or the stacked branches combined.
15. **Risks, rollback, focus, and stack position.** Say where reviewers should look hardest (the migration and the query change). Say how to roll back (revert the code; whether the migration is safe to leave in place). Say which PR this is in the stack, what depends on it and the merge order.
