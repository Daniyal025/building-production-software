# Shipping the one-cent invoice rounding fix

**Before asking for review**

- Fetch origin, then rebase your branch onto the current `main`. It was cut from yesterday's main, so this pulls in anything merged since.
- Find every caller of the rounding function before you trust the one-line fix. A fix in the shared function covers all callers; a fix at only the path the report names leaves the others broken.
- Confirm the regression test fails on the old code and passes with the fix. A test that never failed proves nothing.
- Run the full test suite, not just the new test, and compare against the last full run on `main`.
- Stage files by path (`git add <file> <test-file>`), never `git commit -a`, so stray local edits stay out.
- Write a commit message that says what was wrong and what changed. Leave out any Claude or AI attribution line, per the team and user rules.
- Push the branch and open the PR against `main`.

**What goes in the PR description**

- Symptom: which currencies show totals off by one cent, and an example invoice with the wrong and right totals.
- Root cause: the rounding step, and why it rounds differently for those currencies (for example, currencies with no minor unit or a different minor unit).
- The fix, and the regression test that pins it, with the case it covers.
- How you verified it: the test run, the full suite result, and whether the test failed before the fix.
- Scope and risk: every caller of the function and the impact on each.
- Existing data: whether invoices already saved with the wrong total need a correction, and how you plan to handle them. The code fix does not repair stored totals.

**After the merge**

- The PR is squash-merged, so the PR title becomes the single commit on `main`. Make the title clear, for example `fix(invoices): round totals to the currency's minor unit`.
- Under the team's rules, the manager does the merge. Do not merge it yourself unless you have an explicit OK.
- Once `main` is deployed, check a known invoice in an affected currency and confirm its total is now correct.
- Handle the already-saved wrong totals as agreed (a correction script or a note to the owner), then close the linked issue.
- Pull `main` locally and delete the merged branch.
