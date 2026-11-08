# Hotfix: invoice rounding (one-cent bug)

## Before asking for review

- **Rebase onto current main.** Your branch is from yesterday's main. Run `git fetch && git rebase origin/main` (or merge main in). Re-run the tests on the result, because the rounding function or its callers may have changed since yesterday.
- **Prove the test fails without the fix.** Revert the one-line fix temporarily, or run the new test on main. It should fail on the affected currencies. Then restore the fix and confirm it passes. A regression test that never failed proves nothing.
- **Cover the real failure cases.** Include the currencies that are off, and include zero-decimal (JPY) and three-decimal (KWD, BHD) currencies. Add half-way values such as x.xx5. Check whether the bug is binary float error or the rounding mode (half-up vs half-even). Use `Decimal` if the cause is float.
- **Grep every caller of the rounding function.** A shared function fixed once fixes all callers. If any call site has its own rounding, it is still broken.
- **Run the full suite, lint and type checks locally.** Don't rely on CI to find problems.
- **Keep the diff minimal.** Only the fix and the test, with no drive-by refactors. Squash-merge uses the PR title as the commit message, so make it something like `fix(invoicing): correct cent rounding for <currencies>`.

## PR description

- **Symptom and impact:** which currencies, how many invoices, and the size of the error (1 cent).
- **Root cause:** one or two sentences on why the old rounding was wrong.
- **The fix and the test:** what changed and what the regression test covers.
- **Evidence:** the test fails on main and passes on the branch.
- **Rollout and risk:** whether already-issued invoices are affected. State whether a backfill or correction is needed, and who owns that. Include rollback (a plain revert of the squash commit) and a link to the incident or ticket.

## After merge

- **Watch the deploy and verify in production.** Confirm the pipeline passes and the fix is live. Check a known-bad invoice or a sample for the affected currencies, and watch error rates and reconciliation alerts.
- **Follow up on existing data.** Identify invoices already issued with wrong totals and fix them (credit notes or corrections) with finance. Close the incident or ticket and delete the branch. If the fix needs backporting to a release branch, do it now.
