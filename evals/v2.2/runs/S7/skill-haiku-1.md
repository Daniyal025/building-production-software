# Rounding fix: before review, PR description, after merge

**Before asking for review**

- Reproduce the bug on today's main first. Record the affected currencies and one wrong invoice total, and confirm the fix is not already on main.
- Grep every caller of the rounding function and confirm invoice totals all route through it. If any total rounds somewhere else, a one-line fix in one place leaves that path wrong, so fix the shared path.
- Merge or rebase main into the branch (the team's convention), resolve conflicts deliberately, and re-run the full test suite on the result.
- Watch the regression test fail on the unfixed code, then pass after the one-line fix. Say so in the PR.
- Make the test use exact decimal amounts for the affected currencies, with no float tolerance and no mock of the rounding function.
- Run CI's exact lint, type-check and test commands locally, push, and confirm CI is green on the pushed branch.
- Self-review the diff against main: only the fix and its test, no debug code, no unrelated formatting. Squash any fixup commits.
- Request review only once CI is green and the description matches the final diff.

**PR description**

- What and why: the wrong totals, the affected currencies, the issue link, and one example invoice with its before and after totals.
- Testing: the test failed before the fix and passes after. Say what was not tested, e.g. no run against production data.
- Scope and risks: state that the fix does not correct invoice totals already stored wrong. Those need a separate backfill. Rollback is a revert of the one commit, provided no migration is involved. Point reviewers at the rounding rule for those currencies.

**After merge**

- The PR title becomes the single squash commit on main, so write it as a clear commit message.
- Deploy through the normal script (backup, pull, migrate, start, verify), then check the example invoice on production and spot-check other affected currencies.
- Track the backfill of wrong stored totals as its own unchecked item with an owner until it is done. Close the issue and delete the branch once the production check passes.
