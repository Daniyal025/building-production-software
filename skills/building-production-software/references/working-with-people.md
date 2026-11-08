# Working with people

Use when writing handovers, merge guides, status updates or design docs, answering review comments, asking clients questions, or claiming a bug is fixed.

Tiers: **T1** every project · **T2** production · **T3** high-stakes. Apply items at or below the project's tier.

## Checklist (read first)

**T1**

- [ ] Claims reproduced on real data with scope and frequency before calling something a bug or a fix.
- [ ] Explicit approval before anything irreversible (merges, pushes, data changes).

**T2**

- [ ] Handover docs: what, order, failure modes, why — for the reader's role.
- [ ] Own judgement calls labelled in designs.

## Rules

### 1. Write for the person who acts
- Say what to do, in what order, what will go wrong and why — for the reader's role.
- Number questions and quote the source; record answers as decisions.
- **Why:** The reader doesn't share your context.
- **Real case:** Merge guides for a manager listed order, expected conflicts and reasons in plain words.
- **Look up:** Stakeholder communication.

### 2. Verify before you claim; ask before the irreversible
- Reproduce on real data and state scope and frequency before calling something a bug or a fix.
- Label your own judgement calls in designs; get explicit approval for merges, pushes and data changes.
- **Why:** Trust is the currency of review.
- **Real case:** Specs that separated "the owner's decisions" from "my calls" made review fast.
- **Look up:** Evidence-based engineering.

