# Weekend expense-splitting prototype: set up vs. skip

Five friends, a weekend, throwaway data. Keep the setup cheap, and spend the care on the one thing that must be right: the money math.

## Set up (cheap, and painful to add later)

- **One tool, one lockfile, one README.** Pick `uv` (or pip plus a pinned `requirements.txt`). The README has the two commands to run the app, so a friend can run it without you.
- **Store money as integer cents.** Never floats. `0.1 + 0.2` errors in a "who owes whom" app make friends distrust the whole thing. Decimal also works, but cents are simplest.
- **Decide how uneven splits round.** For example, 100 split three ways is 33.34 / 33.33 / 33.33, and the extra cent goes to the payer. Write it down in one comment. Totals must always sum exactly.
- **Use SQLite, with a schema file or a few `CREATE TABLE IF NOT EXISTS` statements.** It's one file and needs no server. Tables: `people`, `expenses` (payer, amount_cents, description, date), `shares` (expense, person, share_cents).
- **Compute balances from the expense rows.** Never store a running "balance" column. The rows are the truth, and balances are a query you can re-derive.
- **Add one runnable self-check for the settle-up logic.** Write a single `test_settle.py` or an `assert` block with 3 or 4 cases:
  - an even split;
  - an uneven split with an odd cent;
  - someone who paid and also owes;
  - balances that net to exactly zero.

  This is the only logic where a bug quietly shows wrong numbers.
- **Make bad input fail loudly.** Reject negative or empty amounts and unknown people with a visible error. Don't fall back to 0 or a default. A silent wrong number looks plausible, and that's worse than an error message.
- **Keep secrets out of the repo.** If you add any config (a share password, a key), read it from an env var and add `.env` to `.gitignore`.
- **Use FastAPI or Flask with one HTML page.** Use server-rendered templates, or one static page plus htmx or a few `fetch` calls. Skip the SPA build chain.
- **Add a simple "who owes whom" view.** Net balances per person, plus a greedy settle-up list (debtors pay creditors) that minimises the number of payments.
- **Make the data easy to reset.** Add a seed script with fake data for the demo. Copy the SQLite file somewhere before you show friends real expenses, so a bad edit can't lose them.
- **Keep a "skipped on purpose" list in the README.** That way, "no login" reads as a decision and not an oversight.

## Deliberately skip

- **Real accounts, passwords and OAuth.** Pick a name from a dropdown, or share one link. Add real auth only if strangers will use it or it's exposed publicly. If you do host it on the internet, put a single shared passphrase in front of it.
- **Postgres, an ORM, migration tooling, Docker, CI, and cloud deploy.** Run it on a laptop, or use a tunnel for the demo. Add them if people start relying on it day to day.
- **Currency conversion, receipts and photos, recurring expenses, categories, charts, notifications, and edit history.** None of these affect whether the demo lands. Add what your friends ask for after they try it.
- **Heavy frontend and polish.** Skip React or a build step, skip responsive perfection, and skip a design system. The page only needs to be readable on a phone.
- **Observability, rate limiting, and extensive test suites.** One logic check is enough. Move up to full tests and monitoring if this turns into something people depend on, like an ongoing group ledger.

## What would make you upgrade

- **People rely on it** or enter data you'd hate to lose: add automated backups, then a real login.
- **It's on the public internet:** add auth, HTTPS and input limits first.
- **More than one developer** is working on it: add CI and a linter.
