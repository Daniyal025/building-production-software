## Before asking for review

1. **Fix the stack first, bottom-up.** Merge or rebase main into your branch now, not after review. A 3-week-old branch with 60 main commits has drifted, and the two stacked branches will have to move again after you. Rebase yours, then each stacked branch in order. Don't resolve conflicts by hand in lockfiles or generated files. Regenerate them.
2. **Look for conflicts git can't see.** A clean text merge can still break logic. Your renamed helpers are the main risk. Main's 60 commits may call the old names, or add new callers that only break at runtime or in type-check. Grep main's new code for every old name, then run the type-check and the full suite on the merged tree.
3. **Check the migration number and order.** Someone else on main has probably taken the same number or timestamp. Renumber or reorder it. If main also changed the schema, check that your migration still makes sense on top of it.
4. **Test the migration properly, not just "tests pass".** Run it from an empty database through the seed, on a restored copy of real data, and a second time to prove it's safe to re-run. Run it as the runtime role, not the owner. Confirm it's additive, with any constraints added NOT VALID then validated, and that the seed changes ship in the same PR. Never edit an already-applied migration, even after the rebase. Fix forward with a new file.
5. **Define the deploy order.** Schema goes out before the code that needs it. State whether old code can still run against the new schema, and what the rollback is.
6. **Run CI's exact commands locally** (lint, type-check, tests, build), then confirm CI is green on the rebased branch. "Passes on my machine" from 3 weeks ago says nothing about the merged result.
7. **Make the 40% claim reproducible.** One timing test isn't enough. Re-measure after the rebase, on realistic data volume, with before and after numbers from the same machine and several runs. Report p95, not a single run. If the speedup came from a new index, paste the EXPLAIN (ANALYZE, BUFFERS) plan. It's easy to add an index the planner can't use.
8. **Separate the renames from the behaviour change.** Renames are behaviour-neutral, and mixing them into a performance or feature diff makes "nothing else changed" unverifiable. Ideally put them in their own commit, or their own small PR that merges first. At minimum, keep them in a separate commit and say so.
9. **Re-read your own diff** as a reviewer would. Remove dead code and anything with no caller in this change. Check that comments and docs match the final code.
10. **Plan the stacked branches.** Say in the PR which two branches sit on top of yours and the merge order. After your PR changes (review fixes, squash-merge), rebase them again. Keep the stack shallow. If they can be retargeted to main independently, do that.

## What the PR description should contain

11. **Purpose and scope:** what the feature does and why, in a few sentences, plus what is deliberately not included.
12. **Migration section:** the file name, what it changes, that it's additive and re-runnable, how you tested it (empty, production copy, re-run), the deploy order, and the rollback.
13. **Performance claim with proof:** the "40% faster" with the metric, the data size, before and after numbers, how many runs, and the exact command or script to reproduce it. Don't claim more than the measurement shows.
14. **Renames:** a list of old name to new name, noting that they are mechanical and behaviour-neutral. Say they live in a separate commit so reviewers can skim them. Mention any external callers or other branches affected.
15. **Verification and stack context:** what you ran (full suite on the rebased tree, CI link), anything you could not verify, and the dependent branches with the merge order. Link an issue for every "later" item, and write nothing in the description that the final diff doesn't back up.
