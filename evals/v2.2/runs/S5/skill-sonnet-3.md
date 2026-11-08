# Weekend expense-splitter prototype: set up vs. skip

## Set up (the things that would actually hurt in front of friends)

- **Simplest stack that works.** One Python web framework (FastAPI or Flask), SQLite, and server-rendered pages with a bit of HTMX or plain forms. No separate SPA, no build step. Put a one-line "how to run it" in the README.
- **Money as integer cents.** Store amounts as integers (or Decimal), never floats. A float error of 0.01 on a "who owes whom" screen is the one bug friends will spot immediately.
- **A deterministic split rule.** Decide how to handle remainders (e.g. 10.00 split 3 ways gives 3.34 / 3.33 / 3.33, with the extra cent going to the payer or to the first person alphabetically). Write it down and apply it everywhere.
- **Compute balances from the expense log.** Store expenses, derive "who owes whom" on read. Don't store running balances, which drift when someone edits or deletes an entry.
- **Net out the debts.** Show a simplified settle-up list (A pays B 12.50) rather than a raw pairwise matrix. This is the feature that makes the demo feel useful.
- **One runnable self-check for the settle-up logic.** A single script or test with a few asserts: balances sum to zero, the 3-way split with a leftover cent, and a payer who is also a participant. No test suite, no CI.
- **A simple gate.** If the link is reachable by anyone, put a shared passphrase or a per-person link in front of it. Your friends' spending data shouldn't be public just because the URL leaked.
- **Pick who you are by name.** Choose-your-name from a dropdown on first visit (stored in a cookie) is enough "identity" for 5 people.
- **Basic input validation.** Reject empty amounts, negative or non-numeric values, and unknown participants. Show a visible error rather than saving something odd.
- **One-command start and somewhere to run it.** A tunnel from your laptop, or a cheap host. Check that the SQLite file sits on storage that survives restarts, because many free hosts wipe local disk.
- **Secrets in a git-ignored env file.** The passphrase and any keys stay out of the repo.
- **Copy the data somewhere.** If the group will actually use it after the demo, a nightly copy of the SQLite file is enough.

## Deliberately skip (add only when the trigger appears)

- **Real accounts, passwords, OAuth, email verification.** Add when strangers or more than one group use it.
- **Migrations tooling, CI, linters, Docker, monitoring, multi-environment setup.** Add when a second developer or real users arrive.
- **Multi-currency, receipts upload, recurring expenses, notifications, edit history.** Add when a friend asks for one after using the demo.

Keep a short "skipped, and what would make me add it" list in the README so the shortcuts are decisions, not accidents.
