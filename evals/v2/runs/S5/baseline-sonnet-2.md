# Weekend prototype: shared expense tracker

## Set up

- **One FastAPI app, one process.** FastAPI (or Flask) serving both the JSON API and the static UI. One repo, one command to run.
- **SQLite, one file.** Python's built-in `sqlite3` is enough. No Postgres, no ORM. Delete the file to reset.
- **Three tables:** `people`, `expenses` (payer, amount, description, date), `splits` (expense, person, share). Splits as a table lets you do uneven splits later without a schema change.
- **Store money as integer cents.** Never floats. This is the one correctness thing worth getting right on day one.
- **Balance calculation as a pure function.** Net per person = paid minus owed. Write one small test for it, including a case where the split doesn't divide evenly (assign the leftover cent to someone).
- **Greedy settle-up.** Match the biggest debtor to the biggest creditor. That gives "who owes whom" with few transfers, in about 15 lines.
- **Simple UI.** One HTML page with HTMX or plain `fetch`, plus Pico.css or similar. A single page with an add-expense form, an expense list and a balances panel. No React, no build step.
- **Identity by picking a name.** A "who are you?" dropdown saved in localStorage. With five friends, you don't need real accounts.
- **Shareable link.** One group, a secret token in the URL, so friends open it on their phones. Deploy it on Fly.io or Render with a volume for the SQLite file, or run it locally with a tunnel (ngrok or Cloudflare Tunnel).
- **Seed data and a demo script.** Pre-load a fake trip so the demo starts with something to look at.

## Deliberately skip

- **Auth, passwords, email verification.** The secret URL is your access control for this demo.
- **Multiple groups, invites, user management.** Hardcode one group.
- **Currencies, receipts and photos, recurring expenses, categories.**
- **Edit history and permissions.** Offer delete and basic edit only, or just delete and re-add.
- **Migrations, Docker, CI, a frontend framework, and a test suite beyond the balance function.**
- **Polish.** Skip pagination, dark mode, notifications and real "mark as paid" payment flows. Settle-up shows the numbers and nothing more.

## Later, if friends actually use it

Real accounts, multiple groups, Postgres, and recording payments between people.
