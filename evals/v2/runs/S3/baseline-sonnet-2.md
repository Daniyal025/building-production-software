# Before asking for review, and what the PR description needs

## Before review

- **Rebase onto current main first.** The branch is 3 weeks old and main has moved 60 commits. Review the rebased diff, not a stale one. Fix conflicts now, not in the reviewer's time.
- **Check your migration number.** Another branch may have taken the same number during those 60 commits. Renumber it, and confirm there is a single linear head or no number gap.
- **Run the migration for real.** Apply it to a copy of the current main schema (or a prod-like dump), not only a fresh DB. Check it is safe on a populated table: locks, backfill time, defaults. Test the rollback or downgrade if you support one.
- **Re-run the full test suite after the rebase**, not just the tests for your feature. "Passes locally" on a 3-week-old base proves little about today's main. Also run lint and type checks.
- **Grep for every caller of the renamed helpers**, including code added to main since you branched. Rebasing can silently leave a new call site using the old name. Check tests, docs, scripts, and any dynamic or string references too.
- **Re-run the timing test on the rebased code.** Compare against current main, not the old base. Use the same data size, several runs, and report the variance.
- **Check the stacked branches.** The two branches above yours will break when you rebase. Tell their owners. After your branch is rebased, rebase each onto it in order (`git rebase --onto`). Make sure they still build and pass.
- **Decide the merge order and say so.** Yours must merge first. Retarget the stacked PRs to main after yours lands. Don't force-push over your branch after review has started without warning people.
- **Review your own diff first.** Strip debug code and unrelated changes. If the helper renames are noisy, put them in a separate commit (or a separate PR) so the behavioural change is easy to read.

## PR description

- **What and why:** one or two sentences on the feature and the problem it solves, plus a link to the issue.
- **Migration:** the migration file name, what it changes, how long it takes and whether it locks, whether it is reversible, and the deploy order (migrate before or after the code).
- **Performance evidence:** the 40% claim with method, before and after numbers, dataset, environment, and number of runs. Say whether it was measured against the rebased code.
- **Renames:** list old name to new name, say that behaviour is unchanged, and say how you checked callers. Point reviewers to the commit that holds only renames.
- **Stack and merge order:** state that two branches depend on this one, give their PR links, and say that this PR merges first.
- **Testing and risk:** what you ran (suite, manual checks), anything not covered, and the rollout and rollback plan.
