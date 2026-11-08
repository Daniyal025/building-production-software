# Before asking for review, and what the PR description needs

## Before asking for review

- **Rebase onto current main** (60 commits behind). Prefer rebase over merging main in, for a clean diff. Resolve conflicts, especially in the helpers you renamed.
- **Grep for every use of the renamed helpers** on the rebased tree. Main may have added new callers of the old names that compile on neither side or silently break. Check strings, docs and config as well as code.
- **Renumber the migration.** After 60 commits main probably has new migrations, so check for a number or ordering clash and fix the revision chain or number. Make sure there is a single head.
- **Re-run the migration** on a fresh database and on a copy of current data. Test upgrade, and downgrade if you support it. Check lock time and backfill cost on big tables.
- **Re-run the full test suite and lint after the rebase.** "Pass locally" on a 3-week-old base proves little. Confirm CI is green.
- **Re-measure the 40%.** Run the timing test again on the rebased branch, against main as the baseline, on the same machine and data size, several runs. State the method, because old numbers may no longer hold.
- **Handle the two stacked branches.** Rebase them onto the updated feature branch (`git rebase --onto`) and force-push with `--force-with-lease`. Tell their owners. Check that each still passes tests, especially for the renames and the migration number.
- **Review your own diff first.** Separate the rename-only changes from the behavior changes. Ideally put the renames in their own commit so reviewers can skim it.
- **Keep the PR base correct.** Target main for this PR, and base the stacked PRs on this branch. Link them in order.

## PR description

- **What and why:** one or two sentences on the feature and the problem it solves.
- **Migration:** the file name, what it changes, whether it is reversible, expected runtime and locking, and the deploy order (migrate before or after the code).
- **Performance:** the 40% figure with method, before/after numbers, data size and environment, measured after the rebase.
- **Renames:** list old to new names, say they are mechanical with no behavior change, and say that all callers are updated.
- **Risk and rollback:** what could break, and how to revert (including the migration).
- **Stack:** link the two dependent PRs and the merge order.
- **Testing:** what you ran and any new tests. Say what a reviewer should look at first.
