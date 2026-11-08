# Weekend expense-splitter: set up vs. skip

A weekend demo for 5 friends needs very little process. Spend the time on the few things that make the numbers trustworthy and keep you from a nasty surprise, and skip the rest.

## Set up (do these)

- **One stack, one lockfile, a README.** Use FastAPI, plus SQLite or a single Postgres. Pick one package manager (`uv` or `pip` plus a lock) and write a README with "how to run it" in three lines. Your friends or future you will need it.
- **Store money as integer cents (or Decimal), never floats.** This is the one correctness trap that bites an expense app. Splitting 10.00 three ways with floats gives wrong balances. Decide up front who gets the extra cent, for example the payer or the first person in the list.
- **Settle up with one small, pure function.** It takes expenses and returns net balances, then "A pays B X". Write one runnable check for it (an `assert` script or one `test_*.py`). Test an uneven split, a payer who is also a participant, and balances that sum to exactly zero.
- **Show a proper error when input is bad.** Reject negative or zero amounts, unknown people, and an empty participant list at the API boundary. Don't turn them into a silent 0.
- **Use a database with real constraints.** Give it primary keys, foreign keys, and NOT NULL on amount and payer. If you use plain SQL, keep the schema in one `schema.sql` file you only append to, rather than hand-editing the DB. A full migration tool is optional at this size.
- **Keep secrets out of git.** Anything like a DB URL or session key goes in env or a `.env` that is in `.gitignore`. A secret-scanning pre-commit hook takes two minutes and is worth it.
- **Put a minimal gate on it if it's reachable from the internet.** If you host it anywhere your friends can reach, add one shared passphrase or a per-person link, and require it on every route by default (only `/health` open). Money data with no login on a public URL is the one thing here I would not skip. If it only runs on your laptop or LAN, skip this.
- **Make the data survive and be recoverable.** Keep the DB file or volume somewhere that isn't just your temp folder. Copy it once before the demo day, since this is the only real data you will have.
- **Show balances you can verify.** Put the expense list next to the "who owes whom" view, so a friend can spot a wrong entry. Also allow deleting or fixing an entry. A wrong number that looks right is the worst outcome.

## Deliberately skip (and what would make you add it)

- **CI, branch protection, Docker/compose, deploy scripts.** Run it with one command locally or on a single free host. Add these once other people are contributing code or it needs to stay up.
- **Full auth system (signup, password reset, roles).** The shared passphrase is enough. Add real accounts when strangers use it or people ask for their own groups.
- **Multi-group or multi-currency support, recurring expenses, receipts upload.** None of these is needed to prove the idea. Add them when a friend actually asks.
- **Frontend framework and API type generation.** Server-rendered templates (Jinja plus a bit of htmx) or one plain HTML page is plenty. Move to React when the UI has real state to manage.
- **Heavy test suite, logging and monitoring, rate limiting, DB role split, and an audit trail.** The one settle-up check covers the risky logic. Add the rest when real people depend on it and you are keeping it running.

## Write down the skip list

Keep a short "not done yet, and what would make me add it" list in the README. For example: "no accounts: add if it goes beyond this friend group"; "no backups beyond manual copy: add if we keep real history." That turns every skipped item into a deliberate choice instead of a gap.
