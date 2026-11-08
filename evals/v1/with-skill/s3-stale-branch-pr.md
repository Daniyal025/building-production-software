# S3 with skill — claude-sonnet-5-5

**Before asking for review**

1. **Rebase onto current main** (60 commits), not just merge — and treat it as a semantic-conflict risk: git can merge cleanly and still break logic.
2. **Restack the two dependent branches** onto your rebased branch (or tell their owners). Keep the stack at 2–3 deep or less; build and test the *combined* tree.
3. **Full suite + type-check + build after the rebase**, using CI's exact commands and flags — not just "N passed" locally. Compare against the known-failure baseline: no new failures, no known ones vanishing unexplained.
4. **Fix the migration's numbering.** Three weeks of drift means your number likely collides with one on main or a stacked branch — renumber, or use timestamps. Never edit an applied migration, not even a comment.
5. **Make the migration guarded, idempotent and additive** (constraints `NOT VALID` then validated). Run it from empty DB + seed, from a restored prod copy, and a second time; run it as the runtime role, not the owner. Update seed data in the same PR.
6. **Schema deploys before code.** Make sure the readiness probe checks the schema version, so a missed migration shows as not-ready rather than 500s behind a green /health.
7. **Handle the renames:** grep every caller on current main *and* on the two stacked branches — main's 60 new commits may call the old names. Better: put the pure renames in a separate behaviour-neutral commit (or PR) so reviewers can verify them apart from the feature.
8. **Re-run your new tests and confirm each failed first** (red → green); inject the clock; each test owns its data.
9. **Reproduce the 40% number on the rebased code.** A timing from the old base proves nothing about the new one.
10. **One purpose per PR.** Split off anything that isn't the feature (unrelated cleanups).

**PR description**

11. What the feature does, plus that it adds one migration (number and what it does) and the deploy order (migrate first, then code).
12. The performance claim, reproducibly: the script/command, before and after numbers, dataset, machine and the commit measured — or explicitly "measured once by hand on the pre-rebase base". Never just "40% faster".
13. The renames listed old → new, marked behaviour-neutral, with which stacked branches they affect.
14. Testing done and the baseline comparison: tests seen failing first, CI link/run, migration run on empty, prod copy and re-run. Say what you did not verify.
15. The stack: base branch, the two PRs on top, merge order, and a linked issue for any "later" item. Re-read the whole description against the final diff after every review round, and delete any claim the diff doesn't prove.
