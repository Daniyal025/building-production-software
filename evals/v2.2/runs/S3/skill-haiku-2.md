# Before asking for review

- Bring the feature branch current with main first. Sixty commits is a lot, so resolve conflicts deliberately, not by taking one side wholesale.
- Restack the two dependent branches after that, in order (`git rebase --onto` or `--update-refs`). Push rewritten history with `--force-with-lease`, and tell the owners of the stacked branches.
- Re-run the full suite on the merged result. Your earlier "tests pass" was on the old base and is no longer evidence.
- Run CI's exact lint, type-check and test commands with CI's flags, push, and confirm CI is green on the pushed branch.
- Check the migration number against the migrations main added in those 60 commits. Renumber if it collides. Never edit an applied migration.
- Make the migration guarded, idempotent and additive. Test it on an empty database with seed data, on a production-like copy, and on a second run. Run it as the app's runtime role, not the owner. Use `NOT VALID` then `VALIDATE` for any new constraint.
- Run `EXPLAIN (ANALYZE, BUFFERS)` on realistic data for any new index and paste the plan in the PR.
- Put the renames in their own commit with no behaviour change. Grep every caller, including the two stacked branches and the tests, and fix them during the restack.
- Make the 40% claim reproducible: profile one real request end to end, measure p95 before and after at a stated data volume, and save the script or method. Don't claim a figure from a single run. Keep the timing change separate from any behaviour change.
- Confirm the new tests failed before the fix (red then green), that none are skipped, and that none mock the unit under test.
- Self-review the whole diff against main. Remove debug code and squash fixups.

# What the PR description should contain

- What changed and why, with the linked issue.
- Where the PR sits in the stack: its base branch, the two dependent PRs, and the merge order.
- Testing done, with the exact commands and results on the merged tree, plus what was not tested.
- Migration notes: what it adds, that schema deploys before code, lock and timing risk on large tables, and whether it can be reversed.
- Performance evidence: the page or endpoint, p95 before and after, data volume, the reproduction method, and query counts.
- The list of renamed functions (old to new name), noting the rename commit has no behaviour change.
- Rollback plan. If the migration is not reversible, say so and state the fix-forward path.
- Risks and where reviewers should focus.
- Any deferred work, each linked to an issue.
