# Weekend shared-expenses prototype: what to set up and what to skip

Keep it a prototype for five trusted friends. The one part that must be right is the money maths, so the rest stays minimal.

## Set up

- **Backend:** one Python file with FastAPI (or Flask) serving JSON and one HTML page.
- **Database:** SQLite in a single file. Five users don't need Postgres. Create the tables at startup with `CREATE TABLE IF NOT EXISTS`.
- **Schema:** `people(id, name)`, `expenses(id, payer_id, description, amount_cents, date)` and `shares(expense_id, person_id, share_cents)`.
- **Money as integer cents.** Never floats. Store and compute in cents, format only for display.
- **One write path:** a single `add_expense()` function that validates, then inserts the expense and its shares in one transaction. Every route calls it.
- **Validation at the boundary:** the amount is positive, the payer and participants exist, and the shares add up exactly to the total. Reject anything else with a clear error.
- **Splits:** equal split by default. When cents don't divide evenly, give the leftover cent(s) to named people, not silently to whoever comes first.
- **Balances as a pure function:** net per person from expenses and shares, then a greedy "who pays whom" list. Five people makes greedy fine.
- **Tests:** a few pytest cases for the balance and split functions (uneven split, a payer who is also a participant, all-settled). Write them first and watch them fail, since a passing test you never saw fail proves nothing.
- **UI:** one HTML page with a plain form (payer, amount, description, who shares it), the expense list, and the balances. No build step.
- **Missing data shows as missing:** an unknown person or an empty field gives a visible error, never a 0 balance.
- **Running it:** one command locally. If friends are remote, a tunnel such as ngrok or cloudflared is enough. Don't deploy.

## Skip

- **Accounts, logins and passwords.** Pick your name from a dropdown of the five people. Anyone can add an expense, which is fine among friends. Say so to them.
- **Editing expenses.** To fix a mistake, delete and re-add through the same write path.
- **Multiple currencies.** Use one currency and state it on the page.
- **Docker, CI, a migrations tool, an ORM.** Raw `sqlite3` with parameterised queries is the same effort.
- **A React or other frontend build.** Plain HTML is enough.
- **Audit logs, event sourcing, pagination, caching, background jobs, notifications.** None has a caller yet.

Revisit if the friends start using it for real money at scale or want accounts; that is when Postgres, auth and a proper test suite earn their place.
