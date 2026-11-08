# Before asking for review

- Integrate main first. Merge or rebase the 60 new commits into your branch, resolve conflicts, and keep a note of the main SHA you integrated.
- Fix the stack order. Rebase the bottom branch first, then each stacked branch on top of it. Stacks should stay at most 2-3 deep, so two branches on top of this one is the limit; do not add a third layer.
- Renumber the migration if needed. Check that its number and name do not collide with any migration that landed on main. Never edit a migration that has already been applied, not even a comment.
- Apply the migration to a copy of a database that is at main's latest migration. Confirm it runs cleanly and that the stacked branches still run their migrations in order.
- Run CI's exact commands on the rebased branch, not only your local pytest run. Do this after the last rebase, since "it passed locally" is not evidence.
- Test the combined result. Run the feature branch, and each stacked branch on top of it, against the integrated code.
- Find every caller of each renamed helper. Search the whole repo, including tests, scripts, docs and the two stacked branches. Update every caller in the same change so nothing still calls the old name.
- Keep the rename in its own commit. A rename-only commit makes the review diff readable and easy to revert.
- Watch the new tests fail first. Confirm the timing test and any new unit tests fail on the old code before the fix goes in.
- Re-measure the speed-up on the rebased code. Main's 60 commits may have changed the timing. Use the same data, machine and number of runs before and after, and record those conditions.
- Re-read the PR description against the final diff. Remove any claim the diff or the measurements do not prove.
- Set the PR base to the branch below yours, not main. Say in the description when it should be retargeted after the lower branch merges.

# What the PR description should contain

- One or two sentences on what the change does and why it is needed.
- Stack position: the base branch, the PRs above and below it, and the intended merge order.
- Main integration: the main SHA merged or rebased onto, the date, and how conflicts were resolved.
- Migration: its number and name, what it changes, which migration it follows, whether it can be reversed, its effect on data, and any lock or runtime concern on large tables.
- Renamed helpers: a list of old name to new name, and confirmation that every caller is updated.
- Performance: the page measured, the before and after times, the data size, the environment, the number of runs, and the commit measured on.
- Tests: the exact commands run on the final rebased branch, with their results, and which new tests were seen to fail before the fix.
- Known gaps: what is not covered by tests or measurements.
- Review focus: the specific files or decisions you want the reviewer to check first.
- Rollback: how to back out the change, including the migration, and the order in which the stack must be reverted.
- Follow-ups: anything deliberately left out of scope.
