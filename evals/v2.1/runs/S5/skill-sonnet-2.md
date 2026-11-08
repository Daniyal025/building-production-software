# Weekend expense-splitter prototype: what to set up, what to skip

## Set up (the few things that bite you in a demo)

- **Simplest stack that works.** FastAPI (or Flask) + SQLite + one server-rendered page (Jinja + a sprinkle of HTMX or plain `fetch`). One process, one file DB, no build step.
- **Money as integer cents.** Store `amount_cents` as an int. Never floats; "who owes whom" is the one thing that must add up exactly.
- **Deterministic split rounding.** For a 10.00 expense between 3 people, someone gets the extra cent. Pick a rule (e.g. the payer or first participant absorbs the remainder), so shares always sum to the total.
- **Model it as expenses + shares, derive balances.** Store who paid and each person's share per expense. Compute net balance per person on read. Don't store balances: they drift.
- **Settle up with a simple greedy pass.** Net balances, then match biggest debtor to biggest creditor. It gives few transactions and is about 20 lines.
- **One runnable self-check.** A single `assert`-based test: uneven split, balances sum to zero, settle-up zeroes everyone out. No test framework setup or CI.
- **Validate input at the form.** Reject negative or zero amounts, empty names, and a payer who is not in the group. This is cheap and stops a friend from corrupting your demo.
- **A shared passphrase or group link.** If 5 friends can reach it from a URL, put a shared secret (or an unguessable group token) in front. No accounts needed.
- **Secrets in a git-ignored `.env`.** Passphrase and anything else stay out of the repo.
- **Seed data and a README line.** A `seed.py` with a believable trip, and one line on how to run it, so the demo never starts on an empty screen.
- **Back up the DB file.** If you care about the data after the weekend, copy the SQLite file somewhere. A cron `cp` is enough.

## Deliberately skip (and what would make you add it)

- **Real auth, signup, password reset.** Add when strangers, or more than one real group, use it.
- **Migrations, ORM, Docker, CI, linters, scanners, monitoring.** Add when a second developer arrives or you keep the app running. Recreate the SQLite file while you iterate.
- **Multi-currency, recurring expenses, receipts, notifications, edit history.** Add when a friend actually asks for it after using it.
- **A JS SPA or API-first design.** Add if the simple page stops being enough or you want a mobile client.
- **Keep a short "skipped" list in the README.** Those lines are your answer when a friend asks "does it do X?" and your trigger list for what to build next.
