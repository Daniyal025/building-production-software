## Before you ask for review

- **Reproduce on today's main first.** Your branch is cut from yesterday's main. Rebase (or merge, per team convention) onto current main, then confirm the bug still shows there. Someone may have already fixed it, or touched the same function. Note which build showed the symptom.
- **Prove the regression test can fail.** On the rebased branch, revert the one-line fix and run the test. It must fail with the off-by-one-cent result. Then restore the fix and watch it pass. A test that never failed proves nothing.
- **Cover the whole bug, not one case.** "Some currencies" suggests the cause is a rounding-mode or minor-unit issue. The test should include a currency that failed, a zero-decimal one (JPY) and a three-decimal one (KWD or BHD). It should also pin the exact half-cent boundary values. Check that money stays `Decimal` end to end, with no float anywhere in the path.
- **Grep every caller of the rounding function.** One fix in the shared function repairs all callers. Check that nothing else reimplements the rounding inline, and that no other path (PDF, export, tax lines) still disagrees with the fixed function.
- **Run CI's exact commands locally on the rebased result.** That means lint, type-check and the full suite, not only the new test. Self-review the whole diff, remove debug code and squash fixups. The diff should be the fix and the test and nothing else.

## What goes in the PR description

- **What and why:** the symptom (totals off by one cent for currencies X, Y), the root cause in one sentence, and the linked incident or issue. Keep the claims to what the diff proves.
- **Testing:** the regression test, and the fail-before and pass-after result. Also say what you did not test, for example a replay of real invoices.
- **Blast radius and data:** state whether already-issued invoices stay wrong. A code fix does not correct them. If they need a backfill or credit notes, say so and name an owner. Do not edit recorded invoice data in place.
- **Risk, rollback and review focus:** the risk is that totals change for in-flight invoices. Rollback is reverting the squash commit, with no migration involved. Point the reviewer at the rounding mode and the boundary cases.

## After merge

- **Re-run the suite on main and confirm the deploy.** The squash commit is what ships, so check CI on main, deploy it with the normal single-command deploy (SHA-tagged image, previous one kept), and verify.
- **Verify in production.** Check a known-bad currency's invoice total, and watch the invoice-total error or reconciliation metric. Do not call the incident closed until you have seen the fixed total in production.
- **Close the loop.** Raise an issue for any deferred work (affected-invoice correction, a broader money-rounding audit) so it does not become an untracked "later". Update any docs that described the old rounding behaviour in the same change. Then close the incident and write a short note on how this slipped past testing.
