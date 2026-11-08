# Shared-expense prototype: weekend plan

## Set up

- **FastAPI + uvicorn.** One `main.py` is enough to start. You get a JSON API and free `/docs` for poking at it.
- **SQLite via stdlib `sqlite3`.** One file, no server, no ORM. Two or three tables: `people`, `expenses`, `splits`.
- **Money as integer cents.** Never floats. Splitting 10.00 three ways must not lose a cent, so give the remainder cents to the first few people.
- **One pure `balances()` function.** It takes the expenses and returns net balance per person (paid minus share). This is the core of the app.
- **Settle-up as a second small function.** Greedy matching of the biggest debtor to the biggest creditor gives "who pays whom" with few transfers. Put an `assert`-based check on both functions, since this is the only logic that can quietly be wrong.
- **Equal split first, "paid by X, split among Y" in the data model.** The schema supports uneven splits later without changing the tables, but the UI only offers equal.
- **UI: one server-rendered HTML page with Jinja2, or htmx, or a single static page with `fetch`.** Three parts: an add-expense form, an expense list, and a balances panel with "Alice pays Bob 12.50". Plain CSS, mobile-friendly, because friends will open it on phones.
- **Identity by name picker.** Everyone opens the link, picks their name from a dropdown (or types one), and carries on. Store it in localStorage.
- **Deploy so friends can actually reach it.** Use a tunnel (cloudflared or ngrok) from your laptop, or a free tier on Fly, Render or Railway. A demo nobody can open is worthless.
- **Seed script with fake data.** Seeding 5 people and about 10 expenses means the demo looks alive from the first second.

## Deliberately skip

- **Auth, passwords and accounts.** You trust five friends. Add it only if the app outlives the weekend.
- **Postgres, Docker, migrations, CI.** SQLite plus `pip install` is the whole setup. If the schema changes, delete the db file.
- **Multi-group, invites and currencies.** One hard-coded group, one currency.
- **A React/SPA build chain.** It would cost you half a day of tooling for no demo benefit.
- **Edit/delete history, receipts, notifications and exports.** Delete-and-re-add is fine. If you do add one extra, make it delete, since typos will happen.
- **Test suites and polish beyond the balance logic.** Skip them, but do keep a backup copy of the db file before the demo.
