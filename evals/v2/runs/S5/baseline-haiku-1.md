# Weekend prototype: shared expenses for 5 friends

## Set up
- One Python file with FastAPI, plus SQLite (one file on disk). No Postgres.
- Three tables: `people`, `expenses` (payer_id, description, date, amount in cents), `expense_splits` (expense_id, person_id, share_cents). Store money as integer cents, never floats.
- Create tables with `CREATE TABLE IF NOT EXISTS` on startup. No migration tool.
- Equal split only. Remainder cents go to the first N people so shares add up exactly.
- Validate at the boundary: amount > 0, payer and participants exist, at least one participant.
- Balances endpoint: net per person (paid minus owed). Settle-up = match the biggest debtor to the biggest creditor, repeat. About 20 lines.
- Endpoints: list/add people, list/add/delete expenses, get balances. Delete and re-add instead of editing.
- UI: one static HTML page with a form, an expenses table and a balances table, using plain `fetch`. Served by the same FastAPI app, so no build step and no CORS.
- Pick-your-name dropdown on the page instead of login.
- One pytest file with a single check: balances sum to zero, and a 3-way split with odd cents adds up. Run it once.
- Run on one laptop; friends on the same Wi-Fi use its IP, remote friends use a tunnel tool.

## Skip
- Accounts, passwords, auth. Name dropdown is enough. Add when the app holds real money data.
- Postgres, Docker, ORM, React or any build tooling. Add when you deploy for real or the UI outgrows a page.
- Custom splits (percent, shares, itemized), currencies, receipt photos or OCR. Add when friends ask for them.
- Notifications, email, Venmo or other payment integration. Add after people actually use it.
- Multiple groups, cloud hosting, HTTPS, CI, monitoring. Add when it lives beyond this weekend.
