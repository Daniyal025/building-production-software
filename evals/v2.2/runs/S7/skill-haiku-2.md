# Shipping the invoice rounding fix

- **Bring your branch up to date first.** Your branch is a day behind main. Merge main in, resolve any conflicts, and re-run the full CI commands locally, not only the new test.
- **Find every caller of the rounding function.** It is shared, so the one-line fix has to hold for all of them. If any caller rounds on its own, it is a second path and needs the same fix or an explicit note in the PR.
- **Watch the regression test fail first.** Run it against current main and confirm it fails for the production case. Then apply the fix and confirm it passes. A test that never failed proves nothing.
- **Use the exact production case in the test.** Take the real currency and amount from the bad invoice, written as text, and assert the expected total.
- **Check zero- and three-decimal currencies.** Currencies such as JPY or KWD are where off-by-one-cent bugs usually hide. Add cases for them if the test doesn't cover them.
- **Keep the arithmetic exact.** Money should use Decimal with an explicit rounding mode, not float. Confirm the fix does that.
- **Commit the fix and the test together.** Stage by path only, never `git commit -a`.
- **Write the PR title as the squash subject.** Squash merge turns the title into the single commit message on main, so make it state the fix and that it corrects invoice totals.
- **Write the PR description from the diff.** Cover the symptom (which currencies, how far off, since when), the root cause in one or two sentences, the one-line change and the callers you checked, the regression test and that it failed before the fix, and the CI commands you ran. Reread it against the final diff before requesting review.
- **State what this does not change.** Invoice totals already stored with the wrong cent are not corrected by this code. Say so in the description and name who decides how to handle them.
- **Request the one approval and flag the impact.** Tell the reviewer it is a live production fix and which invoices will change. Do not approve your own PR. Once approved and green, the squash merge goes ahead.
- **After merge, verify in production.** Confirm the deploy went out, check one known affected invoice now shows the right total, and check a sample of unaffected invoices did not move. Report it as verified only after those checks, not when the PR merges, and delete the branch.
