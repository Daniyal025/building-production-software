# Project kickoff

Set the tier first. Then set up the items for that tier before the first feature — each was expensive to retrofit on a real project.

## T1 — every project (even a weekend prototype)

- [ ] The simplest stack that works (e.g. one web framework + SQLite + server-rendered pages); a README line on how to run it.
- [ ] Secrets in a git-ignored env file, never in code.
- [ ] Money as integer minor units or Decimal, with a deterministic rounding rule.
- [ ] One runnable self-check for the non-trivial logic — no suite, no CI.
- [ ] Where it runs and how: a one-command start or deploy (a simple host or a tunnel), with data on storage that survives restarts — free hosts often wipe local disk.
- [ ] A gate (shared secret/passphrase) if anyone else can reach it.
- [ ] If the data matters: a copy of it somewhere else.
- [ ] A list of what you deliberately skipped and what would make you add it.

Everything else (lockfiles discipline, migration tooling, CI, scanners, roles, monitoring) is T2: add it when real users, real data or a second developer arrive.

## T2/T3 — production and high-stakes

### Product
- [ ] Decision log file (ID, source, date, replaced-by) and a `current-state.md` that says what exists today.
- [ ] Collect the client's real artefacts (spreadsheets, reports, samples) into the repo as fixtures, with hashes.
- [ ] Write acceptance criteria as worked examples with exact values.

### Repository
- [ ] One package manager and one lockfile per language; locked installs (`--frozen`) in CI and images.
- [ ] Pre-commit: formatter, linter, secret scanner (gitleaks).
- [ ] CI on every PR runs lint, type-check, tests and the image build; branch protection makes it binding from day one.
- [ ] `.gitignore` and `.dockerignore` cover dumps, env files, data and docs.

### Database
- [ ] Migration ledger table + one migrate tool used by every environment.
- [ ] Roles: owner (no login), migrator, one role per service with grants only, break-glass superuser.
- [ ] Conventions: identity PKs, FKs everywhere, NUMERIC for numbers, `created_at`/`actor`/`origin` audit columns, append-only history for changeable facts.
- [ ] Tenant/model id from day one if a second one is on the roadmap.

### Backend
- [ ] Auth dependency on the whole router (default deny); only `/health` public.
- [ ] One error envelope `{code, message}` with global handlers.
- [ ] Structured JSON logging with a request id; never `print()`.
- [ ] Connection pool sized by formula; per-role statement and idle timeouts.
- [ ] Typed request models (Decimal, date, enums) — no raw dicts or floats.

### Frontend
- [ ] One request layer: auth, error parsing, schema validation, global 401.
- [ ] Generated API types from OpenAPI (or zod at the boundary).
- [ ] One mutation hook pattern with honest pending/success/error states.

### AI features
- [ ] Provider-neutral message types behind one adapter; provider, model and keys are config.
- [ ] Per-call ledger: provider, model, tokens (incl. cached), latency.
- [ ] Token, latency and prompt-size budgets as tests; an eval set of real questions from the first demo.
- [ ] Server-side validation and human confirmation for every action with side effects.

### Operations
- [ ] Images tagged by commit SHA; a deploy script (backup → pull → migrate → start → verify).
- [ ] Offsite encrypted backups and a rehearsed restore before go-live.
- [ ] External uptime check; alert on failed jobs and on stale data.
- [ ] Secrets in files (mode 600) per service, never env vars in compose output or URLs.
