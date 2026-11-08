This is money, so keep the basics tight, but an urgent one-line fix doesn't need a design doc.

**Before asking for review**

- **Reproduce on today's main first.** Your branch is a day old. Confirm the bug still shows on current main and that nobody has already fixed it.
- **Bring the branch current with main.** Rebase or merge, following the team's convention. Re-run the full suite on the result. A green run on yesterday's base proves little.
- **Run CI's exact commands locally** (lint, type-check, tests, same flags). Then push and wait for CI green on the branch itself.
- **Watch the regression test fail without the fix, then pass with it.** Revert the fix and run the test, then restore it. The test should use the actual currencies and amounts that broke. If it only covers one currency, add the others.
- **Check the whole rounding path, not just the function you changed.**
  - Grep every caller. A shared fix is right, but also look for code that does its own rounding.
  - Currencies with 0 or 3 decimals are a common cause of "off by one cent for some currencies".
  - Check the rounding mode (half-up vs half-even).
  - Check that amounts stay Decimal end to end and never pass through floats.
- **Self-review the diff against main.** Remove debug code. Keep one purpose in the PR, with no drive-by refactors. Squash fixup commits, which matters more than usual because the team squash-merges.

**PR description**

- **What and why.** Say which currencies are affected and give one concrete example (an input, the wrong total, the right total). Link the incident or issue.
- **Testing.** List what you ran: the new test, the full suite, and a before/after on a real or sample invoice. Say what you did not test.
- **Risk and rollback.**
  - Risk: totals for the affected currencies will change, so say whether the change is wanted.
  - Rollback: revert the squashed commit, which is safe because there is no migration.
  - Reviewer focus: the rounding mode and the callers.
- **Already-wrong invoices.** Say whether stored or issued invoices carry the bad total. If so, either note that a separate, tracked data-repair task exists (with its issue link) or state that none is needed. Don't claim more than the diff proves. Make the title a good commit message, since squash uses it.

**After merge**

- **Check that main is green after the squash merge.** Watch the deploy pipeline. Keep the previous image so you can roll back without a rebuild.
- **Verify in production.** Check an affected-currency invoice, or use a read-only query or log for totals that don't reconcile. Don't just assume the deploy worked.
- **Fix the existing bad data separately.**
  - Invoices already issued with the wrong total won't fix themselves.
  - Don't edit recorded invoices in place without a reviewed, audited correction (credit note or adjustment).
  - Decide with finance whether customers need to be told.
  - Link the tracking issue.
- **Close the loop.** Close the incident or issue, delete the branch, and add a short note to the postmortem or changelog covering the cause and why the test was missing. Consider a reconciliation check so a one-cent drift gets caught by an alert next time.
