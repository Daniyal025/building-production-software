# Git, pull requests and CI

Use when opening, describing or reviewing a PR, stacking branches, rebasing or merging, resolving conflicts, setting up or fixing CI, deferring work.

## Checklist (read first)

- [ ] Branch protection; debt baselined; waivers owned.
- [ ] CI commands run locally before push.
- [ ] Main merged daily; stack ≤2–3; combined tree tested.
- [ ] Full suite after every merge; decision-named rule tests; lockfiles regenerated.
- [ ] One purpose; description matches final diff; numbers reproducible.
- [ ] "Later" has an issue; bug reproduced on current main.

## Rules

### 1. CI green and binding
- Branch protection from day one; baseline old debt and gate only new violations.
- Every disabled rule or waiver has an issue, owner and re-enable trigger.
- **Why:** A permanently red check trains everyone to ignore it.
- **Real case:** CI was red for months from lint debt with no branch protection; tests never ran in CI.
- **Look up:** Quality ratchet.

### 2. Run what CI runs before pushing
- CI's exact commands and flags locally; if CI doesn't run on PRs, trigger it and link the run.
- **Why:** "N tests passed" from your laptop isn't evidence.
- **Real case:** Merges turned main red on 5 lint + 15 type errors.
- **Look up:** Shift-left.

### 3. Short-lived branches, shallow stacks, tested combinations
- Integrate main daily; stacks ≤2–3; build and test the combined tree before final runs.
- Do big mechanical moves alone, scripted, at a quiet moment.
- **Why:** Integration cost grows super-linearly with branch age.
- **Real case:** Most open PRs forked from one stale commit; one combined tree had hundreds of test errors.
- **Look up:** Trunk-based development.

### 4. Expect conflicts git can't see
- Full suite, type-check and build after every merge.
- Name rule tests after their decision IDs so semantic conflicts fail CI.
- Regenerate lockfiles and generated files; avoid global counters across branches.
- **Why:** Clean text merges can still break logic.
- **Real case:** One merge gave 19 failures with zero text conflicts.
- **Look up:** Semantic merge conflicts.

### 5. One purpose per PR, honest description
- Separate behaviour-neutral changes from behaviour changes.
- Re-read the description against the final diff after every review round; numbers need reproducing scripts.
- **Why:** Mixed PRs can't be verified; stale descriptions mislead reviewers.
- **Real case:** A performance PR also changed answer text, so "accuracy unchanged" was unverifiable.
- **Look up:** Atomic PRs.

### 6. Track deferrals; reproduce before fixing
- Every "later" links an issue.
- Reproduce on the latest main before writing a fix; note which build showed the symptom.
- **Why:** Untracked "later" means never; fixing a bug main already fixed wastes a PR.
- **Real case:** A fix PR discovered main already contained the fix.
- **Look up:** Debt register.

