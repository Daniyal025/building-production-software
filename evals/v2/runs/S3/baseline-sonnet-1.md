# Before asking for review, and what the PR description says

## Before asking for review

- **Rebase onto current main first.** Don't merge main in. The branch is 3 weeks old and main has moved 60 commits, so rebase and resolve conflicts once, while you still remember the code.
- **Handle the stacked branches deliberately.** Each of the two branches above yours has to be rebased onto the new tip of your branch. Use `git rebase --onto <new-base> <old-base> <branch>` so they don't replay your old commits. Do this before you push, or the PR bases will be wrong.
- **Push with `--force-with-lease`**, never plain `--force`. Do it for all three branches, and only after you've checked that nobody else has pushed to them.
- **Renumber the migration.** After 60 commits, someone has probably taken your migration number or timestamp. Check for a collision, a changed head or a second head, and rename it so it applies after main's latest migration.
- **Test the migration separately.** Apply it to a copy of a current main database, roll it back if you have a down step, and apply it again. Also run it against a table with realistic row counts, to find out whether it locks or runs for a long time.
- **Re-run the full test suite after the rebase.** Passing locally on the old base tells you nothing about the new base. Run lint and type checks too, using the same commands CI uses.
- **Grep for the renamed helpers across the whole repo.** Main has 60 commits of new code that may call the old names, and a rebase will not flag those calls. Check tests, scripts, docs and any dynamic or string-based references. If other branches or other teams use those helpers, say so, or leave a deprecated alias for one release.
- **Re-measure the 40% speedup on the rebased code.** Main's changes may have changed the baseline. Run the timing before and after on the same machine, with several runs, a warm cache and similar data. Record the numbers.
- **Self-review the diff on the PR page.** Remove leftover debug code. Pull the pure renames into their own commit, so reviewers can skim them and read the logic changes separately.
- **Check the PR's scope and base.** The PR should target main, or whichever branch is its parent in the stack. Say clearly which branches depend on it, so reviewers don't merge in the wrong order.

## PR description

- **What and why:** two or three sentences on the feature and the problem it solves, with a link to the issue.
- **Performance:** "page X went from A ms to B ms (40% faster)". Give how you measured it: the test, the data size, the number of runs, the machine. Note that the numbers are from after the rebase.
- **Migration:** what it changes, whether it is reversible, whether it locks tables or backfills data, how long it took on realistic data, and the deploy order (migrate before or after the code ships).
- **Renames:** list old name to new name, say whether any are public or used elsewhere, and note which commit holds the pure renames.
- **Stack and review order:** name the two PRs that depend on this one, give the merge order, and say that they will need rebasing after this one lands. Note that you rebased onto main on today's date.
- **Testing and risk:** what you ran (tests, the migration on a main copy, a manual check) and how to roll back.
