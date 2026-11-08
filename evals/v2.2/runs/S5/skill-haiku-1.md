# Weekend expense-splitter prototype: what to set up and what to skip

## Set up

- **Stack:** Python with FastAPI or Flask, one SQLite file, and server-rendered HTML pages with plain forms. No frontend build step.
- **Tables:** `people` (5 rows), `expenses` (id, description, `amount_cents`, `paid_by`, `created_at`), and `expense_splits` (expense_id, person_id, `share_cents`).
- **Money as integer cents.** Never floats. Parse the form's amount string straight into cents.
- **Equal splits that add up exactly.** Give each person the floor of total/n, then hand the leftover cents out one at a time, so 100 split three ways is 34/33/33 and the shares always sum to the total.
- **Balances:** for each person, total paid minus total owed. Then match the people who owe with the people who are owed, largest first, to produce "A pays B X".
- **One runnable self-check:** a short script with `assert`s covering the split remainder and one balance example. Run it with `python`. No test framework.
- **Form validation at the boundary:** amounts must be positive, and the payer and the split people must exist. A bad input shows a visible error. It never saves a zero.
- **Secrets and config in a git-ignored `.env`:** the shared passphrase and the database path. Also git-ignore the `.db` file.
- **A shared passphrase gate** on every page, since anyone with the link could otherwise edit everything.
- **Create tables on startup** with `CREATE TABLE IF NOT EXISTS`. That replaces a migration tool.
- **One-line start command in the README,** plus a note of what you skipped and what would make you add each item.
- **Hosting with a persistent disk.** Use a small VM or a tunnel to your own machine. Free tiers often wipe local files on restart, which would erase the expenses.
- **Copy the SQLite file somewhere else** before the demo, so one mistake doesn't lose the data.

## Skip deliberately

- **User accounts, sign-up and password reset.** Five friends can share one passphrase.
- **Postgres, Docker, an ORM and a migration framework.** Raw SQL on SQLite is enough. Add Postgres when there is real data to protect or more than one developer.
- **A React or TanStack frontend.** Plain forms do the job.
- **CI, pre-commit hooks, linters and secret scanners.** Add them when the project has a second developer.
- **Multi-currency, receipt uploads, recurring expenses and custom splits.** Add a split type only when someone needs it.
- **A full test suite, monitoring and structured logging.** The self-check and printed errors are enough for a weekend.
