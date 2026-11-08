# Requirements and design

Use when gathering requirements, replacing a spreadsheet or legacy tool, writing a spec, choosing an architecture, deciding what to build.

## Checklist (read first)

- [ ] Every behaviour of the replaced tool listed and decided; parity test with pinned exceptions.
- [ ] Acceptance criteria as exact-value examples; visual mockup signed off.
- [ ] Decision log entry for every client/owner answer; evidence files committed and checked.
- [ ] Every new module/route/table has a caller in this change.
- [ ] Second tenant/model on the roadmap? Id column + lookup table + URL namespace now.
- [ ] Searched for an existing implementation before writing a new one.
- [ ] Cross-cutting rules enforced in one place and tested across all routes.

## Rules

### 1. Reverse-engineer the artefact you are replacing
- List every cell or behaviour of the existing tool: formulas, hand-typed values, blanks, fill, undo, freeze panes, export shape.
- Build a parity (golden-master) test from its real outputs, with a written list of accepted differences.
- Ask the client numbered questions that quote the exact cells; label anything you invented as your own decision.
- **Why:** Users judge the new system against the old one, including behaviour nobody wrote down.
- **Real case:** A calculation engine matched most — not all — of the spreadsheet's formulas; the design doc described the gaps wrongly, and a date range that only reflected where the spreadsheet happened to end became a hard product limit.
- **Look up:** Characterization testing; principle of least surprise.

### 2. Specify by example and mock up before styling
- Turn 2–3 cells of the client's real sample into acceptance tests with exact values.
- For visual work, get a quick HTML mockup signed off before building.
- Ask which parts of a format are fixed and which vary per request.
- **Why:** Words like "exact format" hide many decisions; examples and mockups expose them cheaply.
- **Real case:** A table was restyled tight → roomy → narrow in five days; mockup-first features barely churned.
- **Look up:** Specification by example; low-fidelity prototyping.

### 3. Keep a decision log, and keep its evidence
- Every client/owner/manager answer gets an ID, a source, a date and a replaced-by link.
- Commit, or hash and date, every external file a test or decision depends on — and open it to check it says what you claim.
- **Why:** Six weeks later nobody remembers why; an ID lets code, tests and people point at the same decision.
- **Real case:** A committed "client answers" file turned out to be the blank questionnaire.
- **Look up:** Architecture Decision Records; provenance.

### 4. Build exactly what was asked; ask before deviating
- Check every acceptance line against the code before opening the PR.
- If you think the request is wrong, ask and record the answer before building an alternative.
- **Why:** Silent deviations get discovered late, when they are most expensive to undo.
- **Real case:** A feature was built "the other way round" from the issue and had to be re-decided at the end of the queue.
- **Look up:** Acceptance criteria; change control.

### 5. Name the caller or don't build it
- No module, route, table or option without a caller in the same change.
- A registry, factory or role system with one entry is just constants until a second entry exists.
- Delete one-shot scripts after they run.
- **Why:** Unused code still has to be read, reviewed, migrated and secured.
- **Real case:** A review listed thousands of cuttable lines: one-entry registries, a role table nothing read, backends with no UI.
- **Look up:** YAGNI; speculative generality.

### 6. Give known multiplicity room early — but don't abstract early
- If a second tenant/model/region is committed, add its id column, a lookup table (not an ENUM) and a URL namespace on day one.
- Extract interfaces/adapters only when the second real instance arrives (rule of three).
- **Why:** Ids and namespaces are cheap at the start and very expensive to retrofit; abstractions built for imagined cases are usually wrong.
- **Real case:** Retrofitting a model id needed enum migrations, moved every route and forced a paired frontend/backend deploy.
- **Look up:** Multi-tenancy with a discriminator; rule of three.

### 7. One rule, one implementation, enforced at one choke point
- Before writing a check, writer or client, grep the codebase and installed dependencies.
- Put auth, concurrency control and audit in one dependency or write function.
- Add a test that iterates the app's route table and asserts the rule for every route.
- **Why:** Copies drift; every new route that "forgets" a rule is a new bug.
- **Real case:** A revision check added once was forgotten by five later write routes; a route-walking test caught a missing admin check.
- **Look up:** DRY; architecture fitness functions.

### 8. Use explicit mapping tables, never name matching
- Mappings between sources live in a reviewed table; fuzzy matching may only suggest.
- Test the full mapped list (count and members).
- **Why:** Names collide in ways nobody predicts.
- **Real case:** An item in one source was joined to a same-named item in another when the agreed mapping pointed to a different item.
- **Look up:** Entity resolution.

### 9. Own your build and configuration
- Replace scaffold-generated config with the few lines you need; delete dead routes the day you create them.
- Config is cached with a TTL; override files contain only keys that differ from defaults.
- **Why:** Generated config hides behaviour and supply-chain risk; full-copy overrides silently pin old defaults.
- **Real case:** A config file was stat-ed 30,068 times in one request (~7.7 s); an override copied from defaults kept an old model name.
- **Look up:** Configuration layering; supply-chain risk.

### 10. If people fix data by hand in production, build the missing feature
- Overrides are their own layer ranked above the source — never edit the source row.
- Every override is visible, undoable and resettable.
- **Why:** Hand SQL has no audit, no undo, and the next import overwrites it.
- **Real case:** Corrections were made with ad-hoc SQL on production because the app refused the edit.
- **Look up:** Layered data; audit trail.

