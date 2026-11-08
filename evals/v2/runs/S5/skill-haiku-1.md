# Weekend expense-split prototype: set up vs. skip

**Set up**

- One package manager and one lockfile, plus a README with the exact run command, so a friend can start it from scratch.
- Keep secrets (database URL, any keys) in an env file that is git-ignored, and add a secret scanner to pre-commit if you use git.
- Store money as integer cents (or Python `Decimal`) and never as floats. `0.1 + 0.2` is how friends end up owing 0.30000000004.
- Keep the schema in one versioned SQL file that a script applies. Don't hand-edit the live database.
- Write one runnable self-check for the settlement logic: an `assert`-based `__main__` block or one small test file. Cover: an uneven split, a payer who is also in the split, and a debt cancelled by a reverse debt.
- Model the core as: people, expenses (payer, amount in cents, date, description), and expense shares (who owes what). Compute balances from these; don't store running balances.
- Make the "who owes whom" output a net-per-pair list, so A owes B 12.50 is shown once, not as two opposing debts.
- Show a visible error when a split doesn't add up to the expense total. Don't quietly round it away.
- Back up the database file or a dump before you share the link with the group, since it will hold real records.
- Use a plain HTML form and a small JSON endpoint or server-rendered page. Nothing more is needed for five users.
- Put a short note in the README listing what you skipped and what would make you add each item.

**Skip, on purpose**

- Real accounts and passwords. Use a name picker or a random share-link token, and say in the README that anyone with the link can see the data.
- Docker, CI pipelines, and deploy scripts. Run it on one laptop or one free host.
- Multi-currency, tax, and rounding policies beyond the nearest cent.
- An ORM, a frontend build chain, or a component library. One stylesheet is enough.
- Payments or settling up through a bank. Show the amounts; let people pay each other outside the app.
- Audit history, undo, and edit logs. A delete button is enough for a demo.
- Load testing, caching, and background jobs. Five people will not stress anything.

**Upgrade triggers:** move to real auth and a managed database if the group wants to keep using it after the demo, or if it starts holding real money records beyond the weekend.
