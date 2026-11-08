# Git, pull requests and CI

Use when opening, describing or reviewing a PR, stacking branches, rebasing or merging, resolving conflicts, setting up or fixing CI, deferring work.

Tiers: **T1** every project · **T2** production · **T3** high-stakes. Apply items at or below the project's tier.

## Checklist (read first)

**T1**

- [ ] One purpose per PR; description matches the final diff; numbers reproducible.
- [ ] Before review: branch current with main, full suite green on the result, whole diff self-reviewed, fixups squashed.
- [ ] PR description: what and why + issue, testing done (and not done), risks, rollback, where reviewers should focus.

**T2**

- [ ] CI runs lint, type-check and tests on every PR.
- [ ] Rewritten history pushed with --force-with-lease; dependent branches restacked in order and their owners told.
- [ ] Branch protection makes CI binding; old debt baselined, only new violations gated.
- [ ] CI's exact commands run locally before pushing.
- [ ] Main merged daily; stacks ≤2–3 deep; the combined tree tested before the final run.
- [ ] Full suite after every merge; lockfiles and generated files regenerated, never hand-merged.
- [ ] Every "later" links an issue; waivers have an owner and a re-enable trigger.

**T3**

- [ ] Business-rule tests named after their decision IDs, so semantic conflicts fail CI.

## Rules

### 1. Recipe: a review-ready pull request
- Bring the branch current with main (rebase or merge, per team convention); resolve conflicts deliberately; re-run the full suite on the result and get CI green on the pushed branch.
- Rewrote history? Push with `--force-with-lease`, restack dependent branches in order (`git rebase --onto` or `--update-refs`) and tell their owners.
- Self-review the whole diff against main: remove debug code, squash fixups into logical commits, put mechanical changes (renames, formatting) in their own commit.
- Description: what and why plus the linked issue; how it was tested and what wasn't; deploy/migration notes (order, locks, reversibility); rollback plan; risks and where reviewers should focus; place in a stack and merge order.
- Scale the ceremony to the change: an urgent one-line fix needs these basics, not a design document.
- **Why:** Reviewers judge a PR by its diff and its description; a missing basic costs a review round trip and trust.
- **Real case:** Long-lived stacked branches needed dozens of rebase-repair commits, and PR descriptions drifted from their diffs.
- **Look up:** PR hygiene; force-with-lease; stacked diffs.

### 2. CI green and binding
- Branch protection from day one; baseline old debt and gate only new violations.
- Every disabled rule or waiver has an issue, owner and re-enable trigger.
- **Why:** A permanently red check trains everyone to ignore it.
- **Real case:** CI was red for months from lint debt with no branch protection; tests never ran in CI.
- **Look up:** Quality ratchet.

### 3. Run what CI runs before pushing
- CI's exact commands and flags locally; if CI doesn't run on PRs, trigger it and link the run.
- **Why:** "N tests passed" from your laptop isn't evidence.
- **Real case:** Merges turned main red on 5 lint + 15 type errors.
- **Look up:** Shift-left.

### 4. Short-lived branches, shallow stacks, tested combinations
- Integrate main daily; stacks ≤2–3; build and test the combined tree before final runs.
- Do big mechanical moves alone, scripted, at a quiet moment.
- **Why:** Integration cost grows super-linearly with branch age.
- **Real case:** Most open PRs forked from one stale commit; one combined tree had hundreds of test errors.
- **Look up:** Trunk-based development.

### 5. Expect conflicts git can't see
- Full suite, type-check and build after every merge.
- Name rule tests after their decision IDs so semantic conflicts fail CI.
- Regenerate lockfiles and generated files; avoid global counters across branches.
- **Why:** Clean text merges can still break logic.
- **Real case:** One merge gave 19 failures with zero text conflicts.
- **Look up:** Semantic merge conflicts.

### 6. One purpose per PR, honest description
- Separate behaviour-neutral changes from behaviour changes.
- Re-read the description against the final diff after every review round; numbers need reproducing scripts.
- **Why:** Mixed PRs can't be verified; stale descriptions mislead reviewers.
- **Real case:** A performance PR also changed answer text, so "accuracy unchanged" was unverifiable.
- **Look up:** Atomic PRs.

### 7. Track deferrals; reproduce before fixing
- Every "later" links an issue.
- Reproduce on the latest main before writing a fix; note which build showed the symptom.
- **Why:** Untracked "later" means never; fixing a bug main already fixed wastes a PR.
- **Real case:** A fix PR discovered main already contained the fix.
- **Look up:** Debt register.

