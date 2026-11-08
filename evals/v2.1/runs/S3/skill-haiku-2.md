# Before asking for review

- Integrate main first. Merge or rebase onto the current main (60 commits ahead), resolve conflicts, and then run the full test suite on that combined result. Local passes on the old base do not count.
- Restack the two branches bottom-up. Rebase the feature, then the branch on it, then the top branch, so each one sits directly on the one below. Check the merge order with `git merge-tree` before you push.
- Check the migration number. Main has moved, so another migration may already use the same number. Renumber yours if so. Never edit a migration that has already been applied.
- Check the migration against the stacked branches too. Confirm the order of migrations across the stack and that it applies cleanly to a fresh database and to a copy of current main.
- Run CI's exact commands, not just a local "N passed". Use the same flags and environment as CI.
- Watch the new tests fail on the old code first. A test that never failed proves nothing.
- Grep the whole repo for each old helper name, including tests, scripts, docs and the two stacked branches. Any caller you miss will break on rebase.
- Put the renames in their own commit, separate from the feature and the migration. That lets reviewers read the logic change without the noise.
- Re-measure the 40% claim before you write it down. Use the same data size and environment for before and after, and run it more than once. Record the numbers and how you got them. If it was one local run, say so.
- Re-read the PR description against the final diff. Remove any claim the diff does not prove.

# What the PR description should contain

- What changed and why, in two or three sentences, plus the issue link.
- Stack position: the base branch, which branch this one depends on, which branches sit on top of it, and the merge order.
- Migration: file name and number, the tables and columns it changes, whether it can be reversed, and how long it takes on production-sized data.
- Renamed helpers: a table of old name to new name, with a note that every caller was updated.
- Performance: the page measured, the method, the data size, the before and after numbers, and the environment. Say what is not proven.
- Tests: the exact commands run, the results, and the main commit the result was tested against.
- Risks and rollback: what could break, and how to revert (including whether the migration needs a down step before the code can roll back).
- How a reviewer can check it by hand, step by step.
- What is out of scope, so reviewers do not look for it.
