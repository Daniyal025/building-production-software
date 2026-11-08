# Hotfix PR: invoice rounding off-by-one-cent

## Before asking for review

- **Rebase onto current main.** Your branch is cut from yesterday's main, so fetch and rebase. This makes sure you test against what will actually ship, and it catches any change to the rounding function or its callers made since.
- **Prove the test fails without the fix.** Stash or revert the one-line fix, run the regression test, and confirm it fails. Then restore the fix and confirm it passes. A regression test that never failed proves nothing.
- **Cover the affected currencies in the test.** Include the failing cases from production (specific amounts and currencies), plus the edge cases: 0-decimal currencies (JPY), 3-decimal currencies (KWD, BHD), and exact half-cent values. Check that the fix works for all of them and is not a symptom patch for one currency.
- **Grep every caller of the rounding function.** The fix changes behavior for every caller, not only invoice totals (tax, refunds, discounts, exports). Confirm each is either correct with the new behavior or covered by a test.
- **Run the full test suite and lint/CI locally.** Check that nothing else relied on the old rounding.
- **Keep the PR to the one-line fix plus the test.** No drive-by cleanups, since a hotfix needs to be easy to review and easy to revert.

## PR description

- **Symptom and impact:** invoice totals are off by 1 cent for which currencies, since when, and roughly how many invoices are affected.
- **Root cause:** why the old rounding was wrong (for example, float or banker's rounding, or the wrong minor-unit precision), in a sentence or two.
- **What changed and how it was verified:** the fix, the test that fails before and passes after, the callers you checked, and a link to the incident or ticket.
- **Rollout and risk notes:** it is safe to revert, there is no data migration, and already-issued invoices are not changed by this fix. State whether they need a separate correction or backfill, and flag that for finance or support.

## After merge

- **Squash-merge after one approval.** Use a clear commit title that names the bug, since the squash message becomes the history. Delete the branch.
- **Deploy and verify in production.** Watch CI/CD, then check a known-affected currency, either an invoice or a query comparing computed totals with expected ones, and keep an eye on error and support channels. Roll back by reverting the squash commit if something looks wrong.
- **Follow up on the damage already done.** Decide with finance whether the already-issued incorrect invoices need credit notes or a backfill. Then close the incident ticket and write a short note on why the bug escaped (missing currency coverage in tests).
