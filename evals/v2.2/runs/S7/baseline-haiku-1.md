# Shipping the one-cent invoice rounding fix

- **Sync the branch first.** It was cut from yesterday's main, so fetch and rebase onto the current `origin/main` (or merge it in, whichever the team uses) and resolve any conflicts before anything else.
- **Grep every caller of the rounding function.** The one-line fix belongs in the shared function, so confirm all invoice paths route through it and none reimplement rounding themselves.
- **Prove the regression test catches the bug.** Run it against the unfixed code and confirm it fails with the one-cent error, then apply the fix and confirm it passes. Make sure the test uses the currencies that are actually wrong in production.
- **Run the full test suite and the linter locally.** Compare against the last green run so you know nothing else moved.
- **Stage by path only.** Use `git add <file> <test>`, not `git add -A`, so unrelated local files stay out of the commit.
- **Commit with a clear message** such as `fix(invoices): round totals correctly for <currencies>`. The team squash-merges, so this message plus the PR title becomes the commit on main. Leave out any attribution line that your memory rules say to omit.
- **Push the branch** and open the PR against `main`.
- **PR description, part 1: the problem.** State which currencies show the one-cent error, since when, and which invoices are affected.
- **PR description, part 2: cause, fix and proof.** Name the root cause, describe the one-line change and why it sits in the shared function, link the regression test, and report the before/after test results and the full suite run.
- **PR description, part 3: risk and rollout.** Note the callers covered, state that stored totals are not recalculated by the fix, and say whether historical invoices need a separate correction.
- **Ask for review and wait.** Do not merge yourself. The PR needs one approval, and merging happens only after that and with the team's explicit go-ahead.
- **After merge, verify in production.** Confirm the deploy picked up the squash commit, re-check an affected invoice in a failing currency, and delete the feature branch. If old invoices carry wrong totals, raise a separate data correction task.
