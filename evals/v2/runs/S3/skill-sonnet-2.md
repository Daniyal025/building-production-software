Assumption: this is a production app (real users/data, more than one developer). If it is a prototype, drop the migration-rehearsal and flag items. If it touches money or regulated data, add role and permission tests for the migration.

## Before asking for review

- **Fix the stack first.** The branch is 3 weeks old with two branches on top and main 60 commits ahead. Integration cost grows fast with age. Merge or rebase main into the base branch now, then restack the two children onto it, one at a time. Do this before anything else, because every later check is only valid on the rebased code. Afterwards, tell the owners of the child branches. Better still, land the base quickly or flatten the stack, because 3 deep is the limit.
- **Re-run the full suite on the rebased tree, and on the combined stack.** "Passes locally" on a 3-week-old base proves little. Clean text merges can still break logic (a merge can produce failures with zero conflicts), so also run type-check, lint and build. Regenerate lockfiles and generated files instead of hand-merging them.
- **Run CI's exact commands locally** before pushing, or trigger CI and link the run. A laptop "N passed" is not evidence.
- **Renumber the migration.** After 60 commits on main, someone else probably took your migration number or timestamp. Check for a collision and for an ordering conflict. Never edit a migration that is already applied anywhere. If the number moves, only move your own unapplied file.
- **Rehearse the migration three ways:** on an empty database plus seed, on a restored copy of production data, and a second run (it must be a no-op). Run it as the runtime role, not the owner, because permission bugs only show up there. Make it guarded, idempotent and additive. Update the seed data in the same PR. If it adds an index, paste the `EXPLAIN (ANALYZE, BUFFERS)` output on realistic data into the PR.
- **Plan the deploy order.** The schema must go out before the code that needs it. Confirm the readiness check fails if the migration hasn't run, so you don't get a green health check with a broken write path. Make sure the old code still works against the new schema, in case you roll back.
- **Check the renames.** Grep the whole repo, including the two stacked branches and main's new code, for the old helper names. Main has moved, so there may be new callers you have never seen. If any renamed helper is imported by other services or clients, tests, or scripts, or is exposed in an API, treat it as a breaking change. Keep a deprecated alias, or version and announce it. Better still, do the renames in a separate behaviour-neutral commit, or a separate PR.
- **Back up the 40% claim.** One timing run is an anecdote. Re-measure on the rebased code, with the same data and setup before and after, repeated runs, and p95 rather than the average. State the hardware, data size and the script that reproduces it. Also check that nothing else changed the speed in those 60 commits. Add a query-count assertion if the win came from fewer queries.
- **Make sure the tests can fail.** Each new test should be seen failing without your change, then passing with it. Compare the full-suite results against the known-failure baseline, so that no new failure appears and no old one disappears unexplained. Don't loosen or skip any test to get green.
- **Check the PR for scope.** One purpose per PR. If the renames, the speed-up and the feature are separable, split them. A reviewer can't verify "behaviour unchanged" in a PR that also changes behaviour.
- **Open the PR against the right base** and say it is stacked, with the children listed, so no one merges out of order.

## What the PR description should contain

- **What and why:** one paragraph on the feature and the problem it solves, plus a link to the issue.
- **Scope and non-scope:** what changed, what deliberately didn't, and which parts are mechanical renames (list old name to new name) as opposed to behaviour changes.
- **Migration:** the file name, what it does, that it is additive and re-runnable, how you tested it (empty database, production copy, second run), the deploy order (schema first, then code), the rollback plan, and the `EXPLAIN` plan if there is an index.
- **Performance evidence:** before and after numbers (p95, not only the average), the script or command to reproduce, the environment and data size, and the caveat that it was measured on the rebased code.
- **Compatibility and risk:** anything that calls the renamed helpers, whether an alias exists, what could break, and how you'd roll it back.
- **Testing:** the new tests, a note that they were seen failing first, the CI run link, and the known-failure baseline result.
- **Stack and merge order:** the base, the two dependent branches, and what has to land when. Note that you rebased on main as of a given commit.
- **Follow-ups:** anything deferred, each linked to an issue. Re-read the whole description against the final diff after every review round, and fix anything that no longer matches.
