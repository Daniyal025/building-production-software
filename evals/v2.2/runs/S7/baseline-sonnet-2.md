# Hotfix: one-cent rounding bug in invoice totals

## Before asking for review

- **Rebase onto current main.** Your branch is cut from yesterday's main, so fetch and rebase (or merge main in) first. This catches any change to the rounding function or its callers from the last day.
- **Run the regression test against the old code.** Revert your one-line fix, confirm the new test fails, then restore the fix and confirm it passes. A test that passes both ways proves nothing.
- **Run the full suite and linters locally**, then let CI run on the rebased branch. Don't rely on a green run from before the rebase.
- **Grep every caller of the rounding function.** Your fix changes behaviour for all of them (invoices, tax, refunds, exports), not just the invoice total. Check that none depends on the old result.
- **Check the edge cases.** Test the currencies that failed, plus 0-decimal currencies (JPY) and 3-decimal currencies (KWD, BHD). Also check negative amounts (credit notes, refunds) and half-way values. Make sure the fix doesn't just move the off-by-one to other currencies.
- **Keep the PR to the fix and its test only.** No refactors or cleanups. That keeps the one-approval review quick and the rollback simple.

## PR description

- **Symptom and impact:** invoice totals are off by 1 cent for some currencies. State which currencies, since when, and a rough count of affected invoices.
- **Root cause:** what the rounding function did wrong (for example the wrong rounding mode or wrong minor-unit handling), in one or two sentences.
- **The fix and the test:** what the one-line change does, and which test reproduces the bug. Include the before and after values for a concrete example.
- **Risk and rollout:** which other callers are affected, and how you checked them. Say how to revert (a clean revert of the single squashed commit), and ask for a fast-tracked review given that production is affected. Add the incident or ticket link.
- **Data remediation:** say whether already-issued invoices need correcting. Either way, list it as a follow-up and don't fold it into this PR.

## After merge

- **Squash-merge, then watch the deploy.** Use a clear commit title that carries the PR number and the ticket, because the squash message is what ends up in history. Confirm the deploy pipeline picks up the merge commit.
- **Verify in production.** Check a known affected invoice or currency (or a read-only recompute) and confirm the totals are now right. Watch the error and reconciliation dashboards for a while.
- **Close the loop.** Delete the branch, resolve the incident ticket, and tell support and finance. Then handle the already-issued invoices (reissue, credit, or accept) as a separate tracked task, and add a post-incident note if your process requires one.
