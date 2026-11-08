**Before asking for review**

- **Treat the branch as stale.** At 3 weeks old with main 60 commits ahead and two branches stacked on it, the main risk is conflicts and breakage in the combined code, not your own diff.
- **Bring it current with main.** Rebase or merge, following your team's convention. Resolve conflicts on purpose, not by taking one side.
- **Run the full suite on the result.** "Passes locally" on the old base proves little. Run CI's exact commands (lint, type-check, tests, build), then get CI green on the pushed branch.
- **Expect breakage with no text conflict.** After 60 commits, other people's changes may call helpers you renamed or rely on code you changed.
- **Restack the two dependent branches in order.** Use `git rebase --onto` or `--update-refs`. Push the rewritten history with `--force-with-lease`, and tell the owners of the two stacked branches. Run the tests on the combined tree, and think about merging the stack in smaller pieces.
- **Rename check.** Grep for every old helper name across the code, tests, docs and the stacked branches, including dynamic and string references. Put the renames in their own mechanical commit, or their own PR, so reviewers can skim them.
- **Migration, renumbering.** Main has probably added migrations in 3 weeks, so renumber yours if the numbers collide. Never edit one that is already applied.
- **Migration, testing.** Test it from an empty database plus seed, on a copy of production data, and on a second run to confirm it is safe to repeat. Run those tests as the runtime role, not the owner. Update the seed data in the same PR.
- **Migration, deploy order.** Keep the migration additive, and deploy the schema before the code that needs it. State whether it takes locks and how to reverse it.
- **Re-run the timing test.** The 40% result was measured on the old base. Re-run it on the rebased code with realistic data, and keep the script and the before and after numbers so anyone can reproduce them. If the migration adds an index, include an `EXPLAIN (ANALYZE, BUFFERS)` plan.
- **Self-review.** Read the whole diff against main, remove debug code, and squash fixup commits. Keep this PR to one purpose, so a behaviour change doesn't sit among pure renames.

**What the PR description should contain**

- **What and why**, with the linked issue.
- **Place in the stack.** Name the two branches above it and the merge order.
- **Testing.** What you ran after rebasing (full suite, CI link, combined-stack run), and what you didn't test.
- **Performance.** The 40% figure with how it was measured: data size, the script, before and after numbers, and the base commit.
- **Migration notes.** The number, what it does, the deploy order, locks, and how to reverse it.
- **Renames.** The old and new names, and a note that they are mechanical with no behaviour change (the dedicated commit).
- **Risks and rollback.** Where reviewers should focus, and how to back it out. Re-read the description against the final diff before requesting review, and again after each review round, so the claims stay true.
