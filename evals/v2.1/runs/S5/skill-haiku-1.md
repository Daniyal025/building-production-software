# Shared expenses prototype: what to set up and what to skip

**Set up**

- One small Python project with FastAPI and a single SQLite file. No server to install, and the data survives restarts.
- Three tables: `people`, `expenses` (payer, description, date, total in integer cents), and `expense_shares` (expense, person, amount owed in cents). Storing each person's share explicitly means unequal splits work without a rewrite.
- Money as integer cents, never floats. Before saving, check that the shares add up to the total and reject the request with a clear error if they do not.
- Validate on the server: amount above zero, payer and participants must exist, at least one participant.
- A pure function that computes each person's net balance, and a second one that turns balances into "A pays B X" settlements. Keep both free of database calls so they are easy to test.
- Four endpoints: list people, add expense, list expenses, get balances. Add a delete-expense endpoint too, since mistakes will happen during the demo.
- One plain HTML page with a form and two tables (expenses and balances), served by the same backend. No framework and no build step.
- One test file with a few asserts: an even split, an uneven split, a rejected mismatched total, and balances that sum to zero. Break the split logic once to confirm the test fails.

**Skip**

- Logins, passwords and sessions. Pick a name from a dropdown, and keep the link private to the five of you. Do not put it on the open internet.
- Postgres, Docker, a migrations tool and an ORM. One `CREATE TABLE IF NOT EXISTS` at startup is enough.
- Notifications, background jobs, websockets and real-time updates.
- Multiple currencies, receipt photos, recurring expenses and editing an expense (delete and re-add instead).
- Any real payment or bank link. Settlements are shown on screen only, and nobody moves money through the app.
- CI, linting setup, coverage targets and a staging environment.
- A frontend framework, a component library, dark mode and pagination.

If the prototype starts holding real money, needs to keep data after the weekend, or gets opened to people outside the group, that is the point to add a proper database, real login and migrations.
