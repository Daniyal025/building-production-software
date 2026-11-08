# Before you ask for review

Treat this as production work: a real database migration and a stack of dependent branches. These steps assume that.

## What to do

- **Integrate main first.** Three weeks and 60 commits is the real risk, not your local tests. Rebase (or merge, per your team's habit) your branch onto current main now, then rebase the two stacked branches onto the result. Ask the stack owners before you rewrite their branches.
- **Rerun everything after the rebase.** A clean text merge can still break logic. Run the full suite, type-check, lint and build on the combined tree. Compare failures to a known baseline so a new failure and a vanished one both stand out.
- **Run CI's exact commands locally.** Use the same commands and flags CI uses. "Passes on my machine" is not evidence. Link the CI run in the PR.
- **Fix the migration numbering.** Main has probably added migrations in 3 weeks. Renumber or re-timestamp yours so it doesn't collide, and make sure it still applies in order after theirs. Never edit a migration that main has already applied.
- **Test the migration from three states.** Run it on an empty DB plus seed, on a restored copy of production data, and a second time (it must be safe to re-run). Run it as the app's runtime role, not the owner. Change seed data in the same PR.
- **Keep the migration additive, and deploy it first.** Schema goes out before the code that needs it. Check that the old code still works against the new schema, so you can roll back.
- **Check the renames for hidden callers.** Grep the whole repo, the two stacked branches, and anything outside the code (docs, scripts, scheduled jobs, string-based lookups). If any renamed helper is public or used by other services, keep a deprecated alias instead of a hard rename.
- **Separate the renames from the behaviour change.** Ideally the rename is its own commit, or its own PR, so the reviewer can check "behaviour unchanged" for it. If you keep it in one PR, make it a clearly separate commit.
- **Re-verify the 40% claim after the rebase.** Rerun the timing on the rebased code, on realistic data volumes, with several runs. Report p95 rather than a single average. Keep the script so a reviewer can reproduce it.
- **Prove the new tests can fail.** Every new test should have been seen failing before your change (red, then green). Say so in the PR.
- **Re-read your own diff.** Make sure there is no dead code, no stray debug code, and no new code without a caller in this PR.

## What the PR description should contain

- **What and why.** One purpose, in a few sentences, plus the issue link. State the base branch and the two stacked PRs that depend on this one, with the merge order.
- **Behaviour change vs. no behaviour change.** List the renamed helpers (old name to new name) and say they are behaviour-neutral. Name the callers you checked, and say whether an alias remains.
- **Migration details.** File name and number, what it changes, that it is additive and safe to re-run, and how you tested it (empty DB, production copy, second run). Say whether it must deploy before the code, and how to roll back.
- **Performance evidence.** The 40% figure with the method: before and after numbers, data size, number of runs, the script or command to reproduce, and the commit measured. Say whether it was re-measured after rebasing on main.
- **Test evidence.** What you ran (the CI commands), the result on the rebased tree, any known-failure baseline, and which new tests you saw fail first.
- **Risk and follow-ups.** What could go wrong, what to watch after deploy, and any deferred work with a linked issue. Last step: re-read the description against the final diff and delete any claim the diff doesn't support.
