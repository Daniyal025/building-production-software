# Before asking for review

**Get the branch current**

- Rebase onto main (or merge, per your team's convention) now. Three weeks and 60 commits means real conflicts. Resolve them on purpose, not by taking one side.
- The migration is the riskiest part. Main has probably added migrations too, so renumber yours (or use a timestamp) and check that the order is still valid.
- After the rebase, run the full suite plus type-check and lint, using the same commands CI runs. "Passes locally" on a 3-week-old base proves little. A clean text merge can still break behaviour, such as a main-side caller of one of your renamed helpers.
- Grep the whole tree for the old helper names. Main may have added new callers, and dynamic uses (strings, config, docs) won't fail a build.

**Handle the stack**

- Restack the two dependent branches onto the rebased one, in order (`git rebase --onto` or `--update-refs`).
- Push the rewritten history with `--force-with-lease`, never plain `--force`, and tell the owners of the stacked branches.
- Run the tests on the combined tree of all three branches, not just each on its own.
- State the merge order in the PR. If you can, ask whether the stack really needs to be three deep or whether the lower branch can land first.

**Make the diff reviewable**

- Put the helper renames in their own mechanical commit, or their own PR if the team prefers. That way reviewers can skip them and read the behaviour change on its own.
- Self-review the full diff against main. Remove debug code and squash fixup commits.

**Prove the migration**

- Run it three ways: from an empty database through the seed, on a copy of production data, and a second time to confirm it is safe to re-run.
- Run it as the runtime role, not the owner or a superuser.
- Never edit a migration that has already been applied. Fix forward with a new file.

**Re-measure the 40%**

- The timing run was against old main. Re-run it on the rebased branch, with the same data size, a warm-up, and several runs. Report the median and the spread, plus the script that produced it.

# What the PR description should contain

- **What and why:** one or two sentences, plus the linked issue. The headline is the page speedup and the change that causes it.
- **Where it sits:** it is the base of a 3-branch stack, with the merge order and links to the two dependent branches.
- **Performance evidence:** before and after numbers measured on the rebased branch, the method, and a reproducing script. Don't claim "40% faster" without these.
- **Migration notes:** what it changes, whether it takes locks or is slow on large tables, whether it is reversible, and the deploy order (migration before code). Say which states you tested it from.
- **Renames:** list old name to new name, say they are behaviour-neutral and sit in a separate commit, and say whether any public or external caller is affected.
- **Testing:** what you ran (full suite on the rebased result, CI link), and what you did not test.
- **Risks, rollback and review focus:** how to undo it (including the migration), and where you most want reviewers to look: the migration and the logic behind the speedup.
