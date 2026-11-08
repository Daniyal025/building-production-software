# Shared expenses prototype: what to set up and what to skip

## Set up

- One package manager and one lockfile, plus a README with the exact run steps, so a friend can start it in one try.
- Keep secrets (if any) in a local `.env` file read from the environment, and add `.env` and the database file to `.gitignore`.
- Add a secret scanner (gitleaks) as a pre-commit hook. It takes a minute and catches the one mistake that is hard to undo.
- Store every amount as integer cents, or as Decimal. Never use floats for money, or the balances will drift by a cent here and there.
- Create the schema from a single SQL migration file that is never edited after it is applied. Changes go in a new file.
- Put every expense write through one function that validates the input (amount above zero, payer and participants exist, split adds up to the total) and then saves it.
- Validate request bodies with typed models at the API boundary, so bad input is rejected with a clear message.
- Let the "who owes whom" calculation return an error or a visible "unknown" when inputs are incomplete, never a zero that looks like a settled balance.
- Write one runnable self-check for the settlement logic: a few expenses in, the expected transfers out, and a check that all balances sum to zero. This is the part most likely to be wrong, so it gets the test.
- Once friends start entering real expenses, copy the database file somewhere else each day. A plain file copy is enough.
- Keep a short list in the README of what you skipped and what would make you add each item.

## Skip

- Real accounts. Use a plain list of names for the five of you, or one shared passcode. No sign-up, no password reset, no password storage.
- Frameworks and ORMs beyond what the backend needs. Plain SQL and a small HTTP layer are enough.
- Docker, CI pipelines, branch protection, staging environments, and deploy scripts. Run it on your laptop.
- A full frontend build setup. One HTML page with a few fetch calls is enough.
- Payment integrations (Venmo, bank transfers). Record that a payment happened; do not move money.
- Multi-currency, group permissions, edit history, and audit logs.
- Structured logging, metrics, caching, background jobs, and load testing.
- Tests beyond the one settlement self-check.

## What would change this

If the app starts holding real money movements, real friends' accounts with passwords, data that must survive beyond the demo, or a public URL, stop and add accounts, backups with a tested restore, and proper tests before going further.
