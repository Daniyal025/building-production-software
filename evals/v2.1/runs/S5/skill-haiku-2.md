# Shared-expenses prototype: what to set up and what to skip

## Set up

- **Stack:** Python with FastAPI (or Flask), one SQLite file, and plain server-rendered HTML with a few forms. One README line says how to run it.
- **Config:** keep the app passphrase and any other settings in a git-ignored `.env` file, never in code.
- **Five fixed people:** seed their names once in the database or a config list. No sign-up flow.
- **Money as integer cents:** never floats. Split with one fixed rule: each person gets `total // n` cents, and the leftover cents go to the first few people in name order. The split then always adds up to the total.
- **One write path:** a single function records an expense and checks it first. The amount must be positive, the payer and every participant must be known people, and the shares must sum to the total. Every form and endpoint goes through it.
- **Balances from the expense list:** compute each person's net (paid minus owed) on each request. Don't store running totals, because they can drift.
- **Settle-up:** repeatedly match the biggest debtor with the biggest creditor. This gives a short list of "A pays B X".
- **Visible failures:** if a balance can't be computed, show an error. Never show 0 as a stand-in.
- **One self-check:** a small `test_*.py` or `__main__` block with asserts. Cover the cent split on an uneven amount and check that the settle-up nets to zero for a three-person example.
- **Gate:** if the app is reachable by your friends (for example through a tunnel link), require the shared passphrase.
- **Data copy:** copy the SQLite file somewhere else before the demo. It's the only thing worth protecting.

## Skip (add when the app leaves your friend group)

- **Accounts:** sign-up, password reset, per-user permissions. The shared passphrase covers the demo.
- **Heavier database and tooling:** Postgres, an ORM and a migration tool. Use `CREATE TABLE IF NOT EXISTS` on SQLite instead.
- **Deployment and quality tooling:** Docker, CI, pre-commit hooks, linters, secret scanners, and a full test suite.
- **Frontend machinery:** a JavaScript framework, a build step, or generated API types.
- **Operations:** structured logging, monitoring, uptime checks, and backups beyond the manual copy.
- **Extra features:** multiple groups, currencies, receipt uploads, notifications, and roles.
