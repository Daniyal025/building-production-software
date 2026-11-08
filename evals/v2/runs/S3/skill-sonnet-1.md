# Before you ask for review

This is production work (a real migration, stacked branches), so treat it as a normal production PR. If it touches money, personal data or a service other teams depend on, add extra rigor. Passing locally is not enough yet.

## What to do first

- **Rebase onto main now.** A 3-week-old branch with 60 commits behind it will conflict, and git can't see the logic conflicts. Resolve the textual ones, then run the full suite, type-check and build on the combined tree. Zero text conflicts can still produce failures.
- **Fix the migration number.** If main gained migrations while you were away, yours may collide or be out of order. Renumber (or re-timestamp) it. Never edit a migration that main has already applied.
- **Test the migration from three states.** Empty DB to seed, a restored production copy, and a second run (it must be safe to run twice). Run it as the runtime role, not the owner. Update seed data in the same PR. Keep it additive, and put any destructive step in a later change.
- **Check deploy order.** Schema must ship before the code that needs it. Confirm the readiness check fails if the migration hasn't run.
- **Handle the stack deliberately.** Merge the rebased base first and retarget the two child branches onto it, rebasing each in order. Don't rebase the children onto the old base. Run the full suite on the top of the stack too, since the combined tree is what ships. A stack of 3 is the limit; land the base quickly.
- **Run CI's exact commands locally** (lint, type-check, tests, same flags) before pushing. "N passed" on your laptop isn't evidence. Compare the full-suite result against main's known-failure baseline, so you know any new failures are yours.
- **Check the renames.** Grep for every caller, including the other two stacked branches, scripts, docs, and anything that imports them by string. If any renamed helper is part of a public or cross-team surface, keep a deprecated alias. Better still, split the pure renames into their own behaviour-neutral commit (or PR) so the reviewer can wave it through separately.
- **Re-measure the 40%.** Your timing test was on a 3-week-old base. Re-run on the rebased code, with realistic data volumes, and report p95 rather than a single average. If the speedup comes from a new index, run `EXPLAIN (ANALYZE, BUFFERS)` on realistic data and keep the plan. Add a query-count assertion if the win came from removing repeated queries.
- **Make sure each new test failed first.** For any test you added, watch it fail without the fix, then pass. Remove any dependence on today's date or your shell.

## What the PR description must contain

- **Purpose:** one sentence on what the feature does and why. Say what's behaviour-neutral (the renames) separately from what changes behaviour.
- **Stack position:** base branch, which two PRs sit on top, and the merge order. Say what each child needs retargeted after this lands.
- **Migration:** file name and number, what it does, that it is additive and idempotent, and the three-state test results. Note that the schema must deploy before the code, plus the rollback or fix-forward plan.
- **Performance claim:** the 40% with before/after numbers, the commit and data size they came from, the exact script or command to reproduce it, and the EXPLAIN plan if an index is involved. State it as "X ms to Y ms at p95 on N rows", not just "40% faster".
- **Renames:** a table of old name to new name, plus the grep or tool command that proves no callers remain. Say whether any are public or need an alias.
- **Evidence:** the CI run link, the combined-tree result (rebased on main plus the stack), and any known failures from the baseline. Re-read this whole description against the final diff before you request review, and again after each review round.
- **Follow-ups:** anything deferred, each with a linked issue. Mention any rollout risk and, if it's risky, a feature flag with an owner and an expiry date.
