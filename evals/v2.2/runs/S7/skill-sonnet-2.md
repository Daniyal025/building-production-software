# Hotfix PR: rounding bug in invoice totals

**Before asking for review**

- **Bring the branch up to today's main.** It was cut from yesterday's main, so rebase or merge per team convention. Resolve any conflicts deliberately, then run the full suite (not just the new test) on the result. Push and get CI green on the pushed branch.
- **Run CI's exact commands locally first** (lint, type-check, tests, same flags). "Passes on my laptop" isn't evidence.
- **Reproduce on current main before trusting the fix.** Confirm the bug still shows there with the same currencies, and that nobody has already fixed it.
- **Watch the regression test fail first.** Run it against unfixed main, see it fail for the right reason, then see it pass with your change. Make sure it covers the currencies that actually break, including the half-cent boundary and any 0- or 3-decimal currencies. A single USD-style case proves nothing.
- **Check the fix is at the root, not just the symptom.**
  - Grep every caller of the rounding function.
  - Look for a second copy of the rounding logic elsewhere (PDF or export code, tax or discount paths, the frontend).
  - Check that money stays Decimal end to end and never goes through float.
  - Fix it once where all paths route through, or list the siblings you checked.
- **Self-review the whole diff against main.** Remove debug code, squash fixups, and keep the PR to this one purpose with no drive-by refactors.

**PR description**

- **What and why:** the symptom (totals off by one cent in currencies X, Y), the root cause in one or two sentences, and a link to the incident or issue.
- **Squash-merge note:** the title and description become the commit on main, so write them as a clean commit message. Use something like "Fix invoice rounding for <currencies>". Don't leave "address review comments" noise in there.
- **Testing done and not done:**
  - Say which test fails before the fix and passes after, and which full-suite run is green.
  - Include a before/after example, such as an invoice that came out 100.01 and should have been 100.00.
  - Say plainly what you did not verify (for example, no check against real production invoices).
- **Risk and review focus:**
  - Rounding changes can shift totals that were previously "right" for other currencies, so point reviewers at those cases.
  - Say whether already-issued invoices are affected.
  - There are no migration or deploy-ordering concerns if none apply. Say so.
- **Rollback:** revert the squash commit and redeploy the previous image. Note that it needs no data change.

**After merge**

- **Confirm main, then the deploy.** Check CI is green on the squashed commit on main, watch the release go out (SHA-tagged, previous image kept), and verify in production. Compute a known-bad invoice or case and check the total, then watch error and mismatch metrics.
- **Handle the already-wrong invoices as a separate, tracked step.** The code fix doesn't correct totals already stored or sent. Open an issue with an owner. Decide whether to find the affected invoices with a query, then correct them via credit notes or a reviewed, audited backfill. Don't edit recorded money in place silently. Tell finance or support what the affected range is.
- **Close the loop.** Delete the branch, link the issue to the PR, and write a short incident note covering why tests missed it and which other currencies or paths were checked. Open an issue for any follow-up you deferred, such as a property test over all currencies.
