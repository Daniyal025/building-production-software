# Before asking for review

- Merge the current main (the 60 new commits) into the feature branch, resolve conflicts by hand, and regenerate lockfiles and generated files instead of hand-merging them.
- Run the full test suite on the merged tree, not only your branch's tests, and run CI's exact lint, type-check and test commands with CI's flags. Confirm CI actually runs on the PR.
- Rebase the two stacked branches in order onto the updated feature branch, keep the stack no deeper than 2 or 3, and test the combined result before the final run.
- Split the helper renames into their own behaviour-neutral change, and grep every caller of the old names across all three branches, including tests, scripts and docs.
- Check the migration's number against the migrations main added in the last 60 commits. Keep it a new file and never touch an applied one.
- Make the migration guarded, idempotent and additive. Test it on an empty database with seed data, on a production-like copy, and on a second run, as the app's runtime role rather than the owner.
- Run EXPLAIN (ANALYZE, BUFFERS) on realistic data for any new index and keep the plan for the PR.
- Re-run the timing test on the merged tree against the new main baseline. Save the script and raw numbers, and check that the page's output is unchanged.
- Confirm each new test fails before the fix, and that no test depends on today's date or on your shell environment.

# PR description

- One sentence on the purpose, and whether the change is behaviour-neutral or changes behaviour.
- The base branch, this PR's place in the stack, and the merge order of the stacked PRs.
- The main commit merged in, and the full-suite result on the merged tree.
- The migration: file name and number, what it adds, that it is guarded and additive, the deploy order (schema before code), and the forward-fix plan if it fails.
- The renamed helpers as a list of old name to new name, with confirmation that every caller was updated.
- The 40% figure with the page, the percentile, the data volume, the method, the script path and the raw before and after numbers. State only what was measured.
- Evidence: the tests added with their red-to-green proof, the CI commands run and their results, and the EXPLAIN plan.
- Anything not verified or deferred, with each deferral linked to an issue. Re-read the whole description against the final diff before asking for review.
