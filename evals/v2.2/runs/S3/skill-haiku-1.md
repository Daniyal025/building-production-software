# Before asking for review

## What to do first

- Rebase or merge the feature branch onto current main and resolve conflicts deliberately.
- Restack the two dependent branches in order (`git rebase --onto` or `--update-refs`), then push with `--force-with-lease` and tell their owners.
- Run the full suite on the integrated result, and test the combined tree (feature plus both stacked branches on main) before the final run.
- Run CI's exact commands locally and confirm the pushed branch is green in CI.
- Put the renames in their own mechanical commit, separate from the behaviour change, and squash fixups.
- Check the migration: guarded and safe to run twice, a unique number against main and the stacked branches, tested from an empty database, a production-like copy and a second run, as the runtime role. Paste an `EXPLAIN (ANALYZE, BUFFERS)` plan for any new index.
- Re-run the timing test on the rebased code, since main's 60 commits may change the result, and keep the script that produced the 40%.
- Confirm the new tests failed before the fix and passed after it.

## What the PR description should contain

- What changed and why, with the linked issue and the place in the stack and merge order.
- Testing done (rebased-suite run, CI link, red-then-green evidence) and what was not tested.
- The timing result: method, data, before and after numbers, and steps to reproduce.
- Migration notes: deploy order, locks, reversibility, and the index EXPLAIN plan.
- Rollback plan, the risks, and where reviewers should focus (the migration and callers of the renamed helpers).

Would raise the bar if the migration touched money, regulated or personal data.
