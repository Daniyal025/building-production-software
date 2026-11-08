# Weekend prototype: shared-expense tracker for 5 friends

## Set up (the things worth the time)

- **Simplest stack that works.** One FastAPI (or Flask) app, SQLite, and server-rendered Jinja pages with a sprinkle of HTMX or plain forms. One process, one file for the DB, no separate frontend build.
- **Money as integer cents.** Store amounts as integer minor units (or `Decimal`), never floats. Floats will make "who owes whom" drift by a cent and your friends will notice.
- **Deterministic split rounding.** Decide the rule up front: split 10.00 three ways gives 3.34 / 3.33 / 3.33, with the leftover cents going to the first participants in a fixed order. Totals must always sum back to the expense.
- **Keep the data model tiny.** `people`, `expenses` (payer, amount, description, date), and `shares` (expense, person, amount). Store each person's share explicitly rather than recomputing it later, so unequal splits come for free.
- **Compute balances from the ledger.** Balance = paid minus owed, per person, derived on read. Don't store running balances you'd have to keep in sync.
- **Simple settle-up view.** Net everyone's balance, then greedily match the biggest debtor to the biggest creditor. That gives at most 4 payments for 5 people, which is plenty.
- **One runnable self-check for the balance logic.** A single `assert`-based script or one `test_balances.py`: uneven split, a cent of remainder, and "all balances sum to zero". That's the only logic that can silently lie, so it's the only thing that gets a test.
- **A shared passphrase gate.** The moment you share a link with anyone, put a single shared password (or a secret token in the URL) in front of it. Keep it in a git-ignored `.env`, not in the code.
- **Validate input at the form.** Reject negative or zero amounts, empty payer, and shares that don't sum to the total. It's a few lines and it stops the "I typo'd 500 instead of 50" evening.
- **Make edits and deletes possible.** Friends will enter things wrong. Allow deleting or editing an expense (even if it's just delete and re-add), and show who's owed what immediately afterwards.
- **A README with the run command, plus a copy of the DB.** One line on how to start it, and a habit of copying the SQLite file somewhere before the demo day. If your friends' real money records matter, that's your only backup.

## Deliberately skip

- **Accounts, login flows, password reset, OAuth.** Pick-your-name from a dropdown behind the shared passphrase is enough for 5 people who trust each other. Add real auth if strangers or a second group show up.
- **Migrations tooling, Postgres, Docker, CI, linters, monitoring, pre-commit hooks.** None has a caller yet. `create_all` on startup is fine; add the rest when there are real users or a second developer.
- **Multi-currency, receipts upload, recurring expenses, notifications, payments integration.** Nobody asked for them in the first weekend. Write them on a "later" list.
- **A SPA frontend and a big test suite.** Server-rendered pages and one self-check cover a demo. Revisit if the UI needs real interactivity.

## Write down what would change your mind

Keep a short "skipped" list in the README, with a trigger next to each item: real auth when people outside the group use it, Postgres and backups when the data becomes something you can't re-enter, tests and CI when someone else starts contributing. That keeps the shortcuts honest, and you'll know exactly what to add if the prototype turns into something people keep using.
