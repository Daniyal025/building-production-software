## Set up (the cheap things that keep a demo from embarrassing you)

- **One small framework, one file to start.** FastAPI (or Flask) with a single `main.py` until it hurts. Serve the UI from the same app, so there is one process and one URL to share.
- **SQLite, not Postgres.** One file, no server, stdlib driver. Use plain SQL with no ORM. Moving to Postgres later is easy because the schema is only three tables: `people`, `expenses`, `splits`.
- **Store money as integer cents.** Never floats. The classic demo failure is "owes 33.329999". Show it as dollars only at the edge, in the UI.
- **Make the split math a pure function and test it.** For example `balances(expenses) -> {person: net_cents}`. Handle the remainder when 100.00 is split 3 ways, so it sums to exactly zero. Write one small test for this before you wire up any UI, and watch it fail first. It is the only logic that can be wrong in a way your friends will notice.
- **Settle-up as a second small function.** Turn the net balances into "A pays B $X" using a greedy match of the biggest debtor against the biggest creditor. That gives "who owes whom" in a few lines, and it is a nice demo moment.
- **Validate input at the boundary.** Use a Pydantic model so that amount > 0, payer and participants exist, and participants are non-empty. Reject bad input with a clear message rather than saving junk. Friends will type "abc" into the amount box.
- **Never show a wrong number as if it were right.** If a request fails, show an error in the UI. Don't render 0 or a stale balance.
- **Make delete a soft undo, or at least a confirm.** Someone will mis-tap, and editing history in a shared ledger is the thing that starts arguments. Keep it to one "delete expense" action.
- **Seed script with realistic sample data.** Include a trip, a dinner, and an uneven split. The app should open already looking alive, and you can reset it between demos.
- **A short README with a run command.** Something like `uvicorn main:app --reload`, plus the one line for sharing it, such as `ngrok http 8000` or a free host. The person who wants to try it on their phone is the one who will ask.

## Deliberately skip

- **Accounts, passwords, auth.** Use a shared link and a "who are you?" dropdown. Five friends do not need login, and it is the biggest time sink. The cost is that anyone with the link can edit. That is acceptable for a trusted weekend demo and not acceptable once it is public, so don't post the URL.
- **Migrations, ORM, CI, Docker, linting, type-checking, hooks.** Rebuilding the SQLite file from the schema script is fine. Add these when a second developer or real users show up.
- **A JS frontend build.** Use server-rendered templates or one HTML page with htmx or a little vanilla JS. A React/Vite toolchain will eat your Saturday.
- **Multi-currency, recurring expenses, receipts, notifications, groups, and percentage or itemized splits.** Support equal split and maybe "custom amounts" only. Pick the one feature that makes the demo land and stop there.
- **Scaling, caching, queues, monitoring.** Five users produce no load. A plain log line on errors is enough.

## What would move you up from "prototype"

Real strangers using it, real money being settled through it, or anyone you don't personally know having the link. At that point add auth, Postgres with backups, and an audit trail on edits and deletes.
