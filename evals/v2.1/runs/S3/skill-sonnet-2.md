## Before asking for review

- **Integrate main first.** Rebase (or merge) the 60 new commits into your branch now, not at review time. Resolve conflicts, then rebuild and re-run the full suite, type-check and lint. A clean text merge can still break logic, so "tests passed 3 weeks ago" says nothing about the combined tree.
- **Fix the migration number.** After 3 weeks, another branch has probably taken your migration's number or timestamp. Renumber it on top of main's latest. Do this before anything else touches the schema.
- **Test the migration from three states.** Run it on an empty DB plus seed, on a copy of production data, and a second time to prove it is safe to re-run. Run it as the runtime/migrator role, not the owner. Change any seed data in the same PR.
- **Make it additive and ordered.** The schema should deploy before the code that needs it, and the old code should still work against the new schema so you can roll back. If the migration drops or rewrites anything, archive the rows first and split that into a later step.
- **Run CI's exact commands locally**, with the same flags. "Passes locally" is not evidence. Better, push and link the green CI run on the rebased branch.
- **Check the renames for missed callers.** Grep the whole repo, including the 60 new commits, tests, scripts, docs and string-based lookups. Main may now call the old helper names. Also check that the two stacked branches don't use them.
- **Keep the renames reviewable.** If the renames are behaviour-neutral, put them in their own commit (or a separate PR) so the reviewer can skim them. Don't let them hide the real change.
- **Re-measure the 40%.** Re-run the timing on the rebased branch against current main, on realistic data volume. Run it several times and report the spread. If a new index is involved, include the `EXPLAIN (ANALYZE, BUFFERS)` plan for the query before and after. Keep the script in the repo or PR so anyone can reproduce it.
- **Handle the stack.** Retarget and rebase the two stacked branches onto the updated base, in order. Test the combined tree of all three before the final run. Don't open all three PRs for review against a stale base. Stacks should be at most 2–3 deep, so land this one quickly.

## What the PR description should contain

- **Purpose, in one or two sentences.** Say what changed and why. If the renames and the feature are separable, say which commits are which.
- **Migration section.** Give the file name and number, what it adds, whether it is additive and re-runnable, and what you tested it against. Say when it must run relative to the deploy (schema first). Note the rollback path.
- **Performance claim with proof.** State the numbers as "before X ms, after Y ms", with the data size, number of runs, the environment, and the command that reproduces them. Say that it was measured after the rebase. Don't write "40% faster" without these.
- **Renames list.** Give old name to new name, say that behaviour is unchanged, and say how you checked for callers.
- **Stack and merge order.** Name the two dependent branches or PRs, say what order to merge in, and say what each depends on.
- **Test evidence.** Say what you ran (the exact CI commands and the CI run link) and what is not covered. Re-read the finished description against the final diff, and again after each review round, so it claims only what the diff proves.
