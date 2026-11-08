# Before asking for review

- Bring the branch up to date with main now. Rebase or merge main in, resolve conflicts, and re-run everything on the merged result. A 3-week branch 60 commits behind is the biggest risk here.
- Restack the two stacked branches in order: feature first, then each child onto the new tip of its parent. Dry-merge each step first so no child silently drops commits or reverts the feature.
- Run the exact commands CI runs (lint, type check, full test suite, migrations on a fresh database) on the rebased branch. A local "N passed" from before the rebase is not evidence.
- Check the migration: its number must not collide with main or the stacked branches, it must apply to a fresh database and to a copy of current data, and it must not edit any migration already applied anywhere. Estimate lock time on large tables.
- Audit the renames: grep the whole repo, including tests, templates, docs, config and dynamically built strings, plus both stacked branches, for every old helper name. A missed caller fails at runtime, not at build time.
- Re-run the timing test on the rebased branch against main, same data and machine, several runs each. The number from before the rebase does not count.
- Confirm the timing test can fail: run it against the old code and watch it miss the threshold before trusting a pass.
- Check that the faster path still handles missing input: a missing value must stay missing and visibly marked, not become 0 or a stale value.

# PR description

- Summary: one or two plain sentences on what changes and why.
- Migration: file name, what it changes, whether it can be reversed, expected runtime on current data, and that it is the only schema change (or list them all).
- Renamed helpers: a table of old name to new name, with the files where each caller was updated.
- Performance: the page or endpoint measured, data size, machine, number of runs, before and after timings, and the threshold. Write "X% faster on this page with this data", not "faster".
- Test evidence: the exact CI commands run on the rebased branch, their results, and the commit hash they ran on.
- Stack: base branch, the two branches stacked on this one, the required merge order, and confirmation that the children were rebased onto this head.
- Behaviour: anything that could change output, and what was verified about missing inputs.
- Known gaps: what was not tested (other pages, production-sized data, the stacked branches' own tests).
- Before posting, re-read the description against the final rebased diff. Remove any claim the diff does not show.
