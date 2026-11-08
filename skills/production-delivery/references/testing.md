# Testing

Use when writing or reviewing tests, fixing a flaky test, adding a CI gate, testing concurrency, migrations or parity with a reference.

Tiers: **T1** every project · **T2** production · **T3** high-stakes. Apply items at or below the project's tier.

## Checklist (read first)

**T1**

- [ ] Every new test seen failing before the fix (red → green).
- [ ] No mocking of the unit under test; no skipped tests hiding failures.

**T2**

- [ ] Tests independent of today's date and the developer's shell (clock injected, env set by the test).
- [ ] Each test owns its data; network tests opt-in; tolerances from the domain's real precision.
- [ ] Known-failure baseline compared on every full run; gates never bent to pass.
- [ ] Behaviour tested, not config text (pin strings only for true invariants, with a reason).

**T3**

- [ ] Concurrency tested with two real connections (fails if the lock is removed).
- [ ] Parity/golden tests against the reference with a written exception list.

## Rules

### 1. A test must be able to fail for its bug
- Watch it fail before the fix (red → green) and say so in the PR.
- Never mock the unit under test; never let a helper skip the defect case; a skipped test is a hidden failure.
- Tolerances come from the domain's real precision.
- **Why:** Tests that can't fail give false confidence.
- **Real case:** A check sampled only first and last cells; a helper skipped exactly the bug case.
- **Look up:** TDD; mutation testing.

### 2. Hermetic and time-independent
- Inject the clock; derive periods from fixtures; set every env var the test reads.
- Each test owns its data; network tests opt-in; skips on the narrowest fixture.
- **Why:** Tests that depend on today's date or your shell break on someone else's machine — or on the 1st of the month.
- **Real case:** Tests pinned to a month that became the past; tests needing an API key in the developer's shell.
- **Look up:** Clock injection; test isolation.

### 3. Test the race, not the ordering
- Two real connections interleaved at the dangerous point.
- Ask: would this fail if I deleted the lock?
- **Why:** Single-connection tests prove ordering only.
- **Real case:** A lock test wrote inside the lock-holding transaction.
- **Look up:** Race testing.

### 4. Parity tests and known-failure baselines
- A run is good only if no new failure appears and no known one disappears unexplained.
- Report shortfalls as shortfalls; never redefine a gate to make it pass.
- **Why:** Baselines make regressions visible; moving gates hides them.
- **Real case:** A parity gate lists every difference with its reason.
- **Look up:** Golden master; ratchet.

### 5. Test behaviour, not config text
- Prefer smoke tests that exercise the thing; pin strings only for true invariants and say why.
- **Why:** Change-detector tests break on every edit and catch nothing.
- **Real case:** A deploy test spent 130 of 146 lines asserting file text.
- **Look up:** Brittle tests.

