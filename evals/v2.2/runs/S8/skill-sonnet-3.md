# Room booking tool: what to set up, what to skip

Treat this as a throwaway-grade internal tool: 10 users, 3 rooms, low stakes, one week. Spend the time on the one thing that can actually go wrong (double-booking) and keep everything else boring.

## Set up

- **Simplest stack.** One Python web framework (Flask or FastAPI) with server-rendered pages (Jinja, plus a bit of HTMX if you want). Skip a separate SPA. Put one line in the README on how to run it.
- **SQLite for storage.** One file, no database server. Keep it on a disk that survives restarts, because free hosts often wipe local disk.
- **Make double-booking impossible in the database, not just in the code.** Store `room`, `start`, `end` and `booked_by`. Check for overlap and insert in a single transaction. The overlap rule is `new_start < existing_end AND new_end > existing_start`. Back it up with a constraint or a transaction lock. Two people clicking Book at the same moment is the real failure mode here.
- **One runnable self-check for the overlap logic.** A small `test_*.py` or an `assert` script is enough. It should cover back-to-back bookings (10:00-11:00 followed by 11:00-12:00 must be allowed), full containment, partial overlap, and a booking whose end is before its start. Watch it fail once before you trust it.
- **Validate input at the form.** Reject end before start, bookings in the past, unknown rooms, and absurd lengths. Show a clear message when a slot is taken, instead of failing silently or showing a stack trace.
- **Decide time handling up front.** Store UTC, or use one fixed office timezone throughout. Mixed timezones and daylight-saving shifts cause the nastiest bugs in booking tools.
- **A gate so only colleagues get in.** At minimum a shared passphrase. Better, sign-in through your company SSO or Google Workspace if your host makes that cheap, so each booking has a real name on it. Do not build your own password system.
- **Secrets in a git-ignored env file.** Never put them in code.
- **One-command start and a simple home.** Use a small VM, an internal box, or a cheap PaaS. Make sure the app restarts if it crashes.
- **A copy of the data somewhere else.** A nightly copy of the SQLite file to another location is enough. People will notice if bookings vanish.
- **A short "skipped" list in the README.** Write down what you left out and what would make you add it, so the shortcuts are decisions and not surprises.

## Deliberately skip

- **CI pipelines, linters in pre-commit, secret scanners, and Docker/Kubernetes.** Add these when a second developer arrives.
- **Migration tooling, multiple database roles, and Postgres.** Add them if the data model starts changing under live users or you outgrow one file.
- **Email, Slack or calendar sync, recurring bookings, an admin panel, and a fancy calendar widget.** Ask the 10 users after a week which one they actually miss. A plain day-view table is fine.
- **Monitoring stacks, structured logging, and API versioning.** Ordinary logs plus checking in on it yourself is enough at this size.

## What would make you add more

If it grows past one office or one team, or people start depending on it for client-facing meetings, or a second person starts maintaining it, then add automated tests in CI, Postgres, per-user roles, and monitoring. Until then, that would be effort with nobody calling it.
