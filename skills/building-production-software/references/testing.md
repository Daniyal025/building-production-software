# Testing

Use when writing or reviewing tests, fixing a flaky test, adding a CI gate, testing concurrency, migrations or parity with a reference.

## Checklist (read first)

- [ ] Every new test seen failing; no mocked unit; no skips hiding failures.
- [ ] Clock injected; env set in test; own data; network opt-in.
- [ ] Concurrency tested with two connections.
- [ ] Known-failure baseline compared; gates never bent.
- [ ] Behaviour over config-text assertions.

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

