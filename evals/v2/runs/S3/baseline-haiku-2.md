# Before asking for review

- Rebase the feature branch onto current `main` (60 commits behind). Resolve conflicts, then run the tests again. Your local pass was on the old base, so it doesn't count.
- Restack the two child branches in order, bottom to top, after the feature branch. Use `git rebase --update-refs` or `git rebase --onto <new-parent> <old-parent> <child>` so each branch sits on the rebased parent. Confirm each child's diff contains only its own commits.
- Check the migration number. Main may have added a migration in those 60 commits, so renumber yours if it collides. Confirm the migration applies cleanly on a fresh database and on top of main's current schema. Run it against the test database, not only the dev one.
- Check that the migration is safe on large tables: note any table rewrite, long lock, or backfill, and whether it can be rolled back. Note the deploy order if the code needs it.
- Find every use of the renamed helpers with a repo-wide search: source, tests, templates, docs, and the child branches. Update them all in the same commit. Dynamic references (strings, config, imports by name) are easy to miss.
- Re-run the timing test on the rebased code, on the same data and machine, with several runs. Keep the raw numbers. The 40% figure is only valid if it survives the rebase.
- Review your own diff against main (`git diff main...HEAD`) and remove debug prints, scratch files, and unrelated edits. Stage files by path, not with `-a`.
- Update any docs that describe the behaviour you changed, in the same commit.
- Set PR bases: the feature PR targets `main`; each child PR targets its parent branch. Write down the merge order.
- Push the branches. Do not merge anything yourself; wait for the owner's go-ahead.

# PR description

- **Title:** one line saying what changed and why.
- **Summary:** two or three sentences on the problem and the fix.
- **Stack:** this PR's base, the child PRs that depend on it, and the merge order.
- **Changes:** short bullets, one per logical change.
- **Migration:** file name and number, what it changes, rollback plan, and lock or runtime impact on large tables.
- **Renamed helpers:** a table of old name to new name, and where callers were updated.
- **Performance:** before and after timings, the method, data size, and machine. State that the test was rerun after the rebase.
- **Testing:** the exact commands run and their results, plus anything not tested.
- **Risks and rollback:** what could break and how to undo it.
- **Reviewer focus:** the one or two places most worth a close look.
- **Linked issue:** the issue number, if one exists.
- Omit any AI attribution line (your memory rule says no Claude attribution in PRs or commits).
