# S3 baseline (no skill) — claude-sonnet-5-5

**Before asking for review**
- Rebase (or merge) onto current main first — don't ask for review against a 60-commit-stale base. Resolve conflicts, then re-run the full test suite on the rebased result (your "passes locally" was on the old base).
- Your two stacked branches depend on this one: after rebasing, rebase each of them onto the updated parent (`git rebase --onto`) and force-push with `--force-with-lease`; tell their owners if they're not you.
- Check the migration against main's migrations: renumber/re-timestamp it if there's a collision or ordering conflict, and confirm it still applies cleanly on top of main's schema. Run it up and down on a fresh DB and on a copy with realistic data.
- Check migration safety for a live table: lock duration, backfill size, whether old code still works during/after it runs (deploy order: migrate first, then code).
- For the renames: grep the whole repo — including the two stacked branches, other open PRs, docs, scripts, and dynamic/string references — for the old names. Main may have added new callers in those 60 commits. Consider a deprecated alias if anything outside the repo uses them.
- Split the renames into their own commit (or separate PR) so reviewers can see the behavior change without the mechanical noise.
- Re-run the timing test on the rebased code, several times, with the same data size and machine, and record before/after numbers — main's changes may have shifted the baseline.
- Clean up history: squash fixup commits, write meaningful commit messages (migration, renames, feature as separate commits).
- Run linters, type checks, and any CI-equivalent checks locally; self-review the full diff once.

**PR description should contain**
- What and why: one-paragraph summary of the feature and the problem it solves, plus a link to the issue/ticket.
- Stack info: this PR is the base; list the two dependent PRs and the merge order. Mark dependents "do not merge before this".
- Migration: file name, what it changes, whether it's reversible, lock/backfill impact, deploy order and rollback steps.
- Renames: list old → new names, note they're behavior-neutral, and where callers were updated; flag anything external that needs action.
- Performance: the 40% claim with method, before/after numbers, dataset size, number of runs, and what exactly was measured (which page, which metric).
- Testing: what you ran (unit/integration/manual), that it was rebased on main as of a date, and anything not covered. Screenshots if UI changed.
- Review guidance and risks: suggested order to read commits, areas needing close attention, known follow-ups.
