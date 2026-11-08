# Weekend prototype: shared expense tracker

## Set up

- **FastAPI + uvicorn.** One `main.py` is enough to start. You get a JSON API and auto-generated `/docs` for free, so you can poke at it before the UI exists.
- **SQLite via stdlib `sqlite3`.** It's one file with no server to run. Skip the ORM. You need about three tables: `people`, `expenses`, `splits`.
- **Store money as integer cents.** Never use floats. Rounding errors in a "who owes whom" app will embarrass you in front of friends.
- **Model each expense as: payer, amount, and a list of participants.** The default is an equal split. Put the leftover cent(s) on the payer or on the first participant, and keep that rule deterministic.
- **Compute balances on read.** Net balance per person = paid minus share. Don't store balances. Derived data can't go out of sync.
- **Add a "settle up" view with a greedy algorithm.** Match the biggest debtor to the biggest creditor. It gives few enough transactions for 5 people, and it's about 15 lines.
- **Write one test for the balance and settle logic.** Check that balances sum to zero and that the settlements clear every balance. This is the only logic that can quietly be wrong, so it's the only thing worth testing this weekend.
- **UI: one HTML page with htmx or plain `fetch`, served by FastAPI.** Use Jinja2 templates or a static file. You need a form (who paid, how much, who's in), an expense list, and a balances panel.
- **Use Pico.css or similar via CDN.** It looks decent with no CSS work.
- **Skip login by letting people pick their name from a dropdown.** Hardcode your 5 friends or add them on first use. A shared link is enough access control for a demo.
- **Add a delete button (or an undo) for expenses.** People will mis-enter things during the demo, and you need a way to fix it.
- **Deploy with a tunnel or a cheap host.** Run `ngrok` or Cloudflare Tunnel from your laptop. If you want it always on, use Fly.io or Render with the SQLite file on a volume.

## Deliberately skip

- **Real auth, accounts, and password reset.** This is the biggest time sink and nobody will miss it in a 5-person demo.
- **Postgres, migrations, Docker, CI, and a React/SPA frontend.** None of it helps you learn whether the idea works. Add them if the prototype survives.
- **Multi-currency, groups, receipts, recurring expenses, notifications, and unequal or percentage splits.** Note them on a "later" list. Add unequal splits first if your friends ask, because that is the most likely real need.

## Cheap insurance

- Back up the SQLite file by copying it before the demo. Then a bad entry or a bug can't cost you the data.
