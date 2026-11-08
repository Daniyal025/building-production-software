# Shared-expense prototype: set up vs. skip

## Set up (the few things that matter)

- **One web framework, SQLite, server-rendered pages.** FastAPI or Flask with Jinja templates and a single `.db` file. No separate frontend build, no JS framework. A sprinkle of HTMX or plain forms is enough.
- **Store money as integer cents (or Decimal), never floats.** Pick one rounding rule for uneven splits (e.g. 100 split 3 ways gives 34/33/33, with the extra cent going to the payer or to a deterministic first person) and use it everywhere.
- **Compute balances from the expense list, not from stored running totals.** Net balance per person = paid minus share owed. That keeps "who owes whom" always consistent with the log, and fixing or deleting an expense just works.
- **Settle up with a simple greedy pass.** Match biggest debtor to biggest creditor until everyone is zero. It gives few payments and is about 15 lines.
- **One runnable self-check for the split and settle logic.** A single `assert`-based test: splits sum exactly to the total, balances across all people sum to zero, and a known example gives the expected payments. This is the only place a bug would embarrass you in the demo, so it is the only test you need.
- **Make "who paid" and "who is in the split" explicit per expense.** Default to everyone, but allow unchecking people. Equal split first; leave exact amounts and percentages for later.
- **Show the balances view first, expense log second.** The "who owes whom" screen is the demo. Put effort into making it clear.
- **A shared passphrase or a secret link.** If your friends reach it over the internet, put something in front of it. Keep it in a git-ignored env file, not in code.
- **A one-command run and a one-line README.** Something like `uvicorn app:app` plus how to install. Deploy to a simple host or expose it with a tunnel (Cloudflare Tunnel, ngrok) for the demo.
- **Put the SQLite file somewhere that survives restarts.** Many free hosts wipe local disk on redeploy, which would erase the expenses halfway through the weekend. Use a mounted volume, or copy the file somewhere now and then.
- **Basic input validation.** Reject negative or empty amounts and blank names. It is cheap and stops the most common demo-day crash.
- **Seed a demo group with a few sample expenses.** The app looks alive on first open, and you can reset to it quickly.

## Deliberately skip (and what would make you add it)

- **Real accounts, passwords, OAuth, email verification.** Friends just pick their name from a list behind the shared passphrase. Add real auth when strangers or other groups use it.
- **Postgres, migrations tooling, ORM, Docker, CI, linters, secret scanners, monitoring, multi-environment setup.** Add them when it holds data people care about or a second developer joins.
- **Multi-currency, receipts and photos, recurring expenses, notifications, mobile app.** Add one only when a friend actually asks for it after the demo.

## Note on what would change this

If the group starts using it for real money over months, or other people's groups sign up, move up a level: real auth, a proper database with backups, and an audit trail of edits.
