# Weekend expense-splitter prototype: set up vs. skip

Treat this as a throwaway demo for 5 friends. Do the cheap things that prevent embarrassing failures, and skip anything built for scale or other developers.

## Set up (cheap, worth it)

- **Money as integer cents (or Decimal), never floats.** "Who owes whom" is the whole product. A float rounding bug (0.1 + 0.2) shows up in front of your friends within minutes. Store `amount_cents` as an int and convert for display only.
- **Handle uneven splits explicitly.** $100 split 3 ways is 33.34 / 33.33 / 33.33. Decide who absorbs the extra cent so balances always sum to exactly zero.
- **One small self-check for the settle-up logic.** A single `test_balances.py` or an `assert` demo. For example: A pays 90 for A, B and C, and B pays 30 for A and B. Assert the exact net balances. Write it first and watch it fail once. This is the only logic worth testing.
- **Pick the simplest stack that runs.** FastAPI or Flask, SQLite, and server-rendered templates (Jinja plus a little HTMX) or one static page. One `requirements.txt` or `pyproject.toml`, one lockfile.
- **SQLite with a tiny schema.** `people`, `expenses`, and `expense_shares` (expense_id, person_id, share_cents), with primary keys, foreign keys and NOT NULL. Create it from one `schema.sql` file. Skip a migration framework until the schema starts changing under real data.
- **A shared passphrase or per-person link.** Don't leave the app open on a public URL. One shared secret in an env var is enough. This is the one security item to keep, because strangers can otherwise write to your data.
- **Secrets out of git.** Put the passphrase in `.env`, add `.env` to `.gitignore`, and optionally add a pre-commit secret scan.
- **Honest UI feedback.** Show "Saved" only after the server confirms. Show the server's error message on bad input (empty amount, negative amount, no participants) and validate inputs on the server. Never silently show 0 when something fails.
- **Make mistakes fixable.** Allow delete or edit of an expense. Friends will enter wrong amounts, and the balances should recompute from the expense list, not from stored running totals.
- **A README with a run command, plus a copy of the SQLite file.** Copy the `.db` file elsewhere before the demo, since it will hold your friends' real entries.

## Deliberately skip (and what would make you add it)

- **User accounts, password reset, OAuth.** Use a name picker plus the shared passphrase. Add real auth if strangers or more groups appear.
- **Multi-group, multi-currency and recurring expenses.** One group, one currency. Add them only when someone asks for a second group.
- **Postgres, ORM, migrations, DB roles.** SQLite is enough. Move when you have concurrent users or data you can't lose.
- **CI, Docker, deploy pipeline, monitoring.** Run it on your laptop, or on one cheap host or tunnel for the evening. Add these if it becomes something people use daily.
- **Separate React frontend, generated API types, a full test suite, accessibility audits, caching, pagination, rate limiting.** Add them when there is a second developer or real traffic.

## What would move this up to a "real" product

Real money flowing through the app (payments), strangers signing up, personal data you'd be liable for, or you wanting to keep it running for months. At that point add real auth, Postgres with migrations, backups, CI and an audit trail of who changed which expense.
