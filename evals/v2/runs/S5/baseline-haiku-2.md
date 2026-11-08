# Weekend prototype: shared expense splitter (5 friends)

## Set up

- One Python file or small package with FastAPI (or Flask) for the backend. Pick whichever you already know.
- SQLite as the database. One file, zero setup, enough for 5 users.
- Three tables: `people`, `expenses` (payer, amount, description, date), `expense_shares` (expense_id, person_id, amount owed). Store amounts as integer cents, never floats.
- Three endpoints: add a person, add an expense with a split, get balances.
- A balance function that nets every expense into one number per person, then lists who pays whom. Keep it a pure function so you can test it.
- Equal split by default, with an optional custom amount per person. That covers most real cases.
- A single HTML page with a plain form to add an expense and a table showing balances. No framework, no build step; plain JS fetch calls are enough.
- A few asserts or one small test file for the balance math. Rounding and "who owes whom" are where bugs hide.
- A `.env` or a constant for the port and DB path. Nothing else configurable.
- Run it on one machine (your laptop) and share your screen or a local tunnel for the demo.

## Skip on purpose

- User accounts, passwords, login, and sessions. Pick names from a dropdown or type them; the demo doesn't need security.
- Hosting, Docker, CI, and a production server. Add these only if the friends keep using it after the demo.
- A full frontend framework, a component library, or a design system. Plain HTML is enough to show the idea.
- Multi-currency, receipts/photo upload, and recurring expenses. None are needed to show the core idea.
- Settle-up payments and integrations with Venmo or bank APIs. Show the "who owes whom" list and stop there.
- Editing and deleting expenses. Add an expense, and if you make a mistake, fix the database by hand.
- Automated migrations. Recreate the SQLite file as needed.

Skipped: auth, deployment, multi-currency, payments, edit/delete. Add auth before real people use it on a shared network; add edit/delete once the demo is working and people want it.
