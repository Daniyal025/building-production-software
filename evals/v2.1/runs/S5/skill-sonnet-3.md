# Weekend expense-splitter prototype: what to set up, what to skip

## Set up (the few things that bite even in a demo)

- **One small stack:** FastAPI (or Flask) + SQLite + server-rendered Jinja pages, with a sprinkle of HTMX or plain forms. One process, one file DB, no separate frontend build. Put a "how to run" line in the README.
- **Money as integer cents:** never floats. "Split 10.00 three ways" must not leak or invent a cent.
- **A deterministic rounding rule for splits:** give the leftover cents to the payer, or to the first N people in a fixed order. Whatever you pick, make it the same every time so the totals always reconcile.
- **Store expenses, derive balances:** keep rows of (payer, amount, participants/shares, description, date). Compute "who owes whom" on read. Don't store balances you'd have to keep in sync.
- **Settle-up logic in one pure function:** net each person's balance, then greedily match the biggest debtor to the biggest creditor. That gives the fewest payments. This is the one piece of real logic, so it deserves care.
- **One runnable self-check for that function:** a few asserts, for example that balances sum to exactly zero, an uneven split, and a payer who isn't a participant. No test framework or CI.
- **Basic input validation at the form:** positive amount, known people, at least one participant, a sane max length. A typo like "-50" or an empty participant list shouldn't silently produce a wrong balance.
- **A shared passphrase or secret link:** the demo will sit on a public URL, and a basic gate is cheap. Keep it in an env file that's git-ignored, never in code.
- **Fixed people list, no accounts:** seed your 5 friends and use a "who are you?" dropdown, or a name stored in a cookie.
- **Make edits and deletes visible:** use soft delete, or just show an "edited" mark. Friends will fix mistakes, and a balance that silently changes with no trace makes the demo look untrustworthy.
- **Copy the DB file somewhere else once before the demo:** a one-line `cp` is enough. If it dies mid-demo you can restore it.

## Deliberately skip (and what would make you add it)

- **Real auth (passwords, OAuth, sessions, roles):** add when strangers or non-friends can reach it.
- **Postgres, migrations, an ORM:** add when you have a second developer, or data you can't afford to lose or recreate.
- **A separate React/SPA frontend, API versioning, OpenAPI client generation:** add when the UI outgrows server-rendered forms.
- **CI, Docker, linters, pre-commit, monitoring, structured logging:** add when anyone other than you depends on it staying up.
- **Multi-currency, groups, recurring expenses, receipts upload, notifications, payment integrations:** add when a friend actually asks for one after using it. Keep a one-line "later" list so you don't lose the ideas.

The principle behind both lists: skip anything that has no caller in this demo, but never skip anything that could make the numbers look right while being wrong. For this app that means integer cents, the rounding rule, balances summing to zero, and validated input.
