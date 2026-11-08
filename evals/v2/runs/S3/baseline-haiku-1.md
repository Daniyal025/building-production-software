# Before asking for review

- Bring the branch up to date with main. Merge or rebase main into the feature branch, since main is 60 commits ahead. Resolve conflicts, then re-run the full test suite on the result. Passing tests from before the update do not count.
- Rebase the stacked branches onto the updated feature branch, in order, bottom first. Use `git rebase --update-refs` if available, or `git rebase --onto`. Check that each stacked branch still has only its own commits.
- Use `--force-with-lease` for any force push, and only after the rebase is verified. Never use a plain `--force`.
- Check the migration number against main. Main has moved on, so another migration may already use the number you chose. Renumber if needed, and make sure the stacked branches still run in the right order.
- Run the migration on a fresh database and on a copy of realistic data. Confirm it applies cleanly, note whether it can be reversed, and check whether it locks large tables.
- Rename the helpers in one commit, separate from the behaviour change. Grep the whole repo for the old names, including tests, the stacked branches and code that arrived from main, so nothing still calls the old names.
- Run the linter, formatter and type checker along with the tests on the rebased branch.
- Re-measure the 40% speed-up on the rebased code. The number was taken before main changed, so it may no longer hold. Record the method: same data, same machine, several runs, before and after numbers.
- Read your own diff against main (`git diff main...<branch>`). Remove debug code, stray files and unrelated edits.

# PR description

- Summary: what the change does and why, in two or three sentences.
- Base branch and stack: the branch this PR targets, the two stacked PRs on top of it, and the merge order.
- Migration: its number, what it changes, whether it is reversible, expected lock time, and whether it must run before the code deploys.
- Renamed helpers: a list of old name to new name, and confirmation that all callers were updated.
- Performance: the measured speed-up, the page measured, the method, the data size, and the before and after timings. Say that the numbers come from the rebased code.
- Testing: the commands run, the results, and the commit tested.
- Rollback: how to revert, including what happens to the migration.
- Review focus: the parts you most want checked, such as the migration and the renamed call sites.
