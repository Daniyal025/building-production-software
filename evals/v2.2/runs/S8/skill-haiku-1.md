# Meeting room booking tool: what to set up and what to skip

**Set up**

- A small Python web framework (FastAPI or similar) serving plain HTML pages with a little JavaScript. No separate frontend build.
- One database. Use Postgres if you already run it, otherwise SQLite is fine for ten people. Keep the schema in one SQL file with `IF NOT EXISTS`.
- A bookings table with a foreign key to rooms, start and end as UTC timestamps, `NOT NULL` on every column that matters, and a `CHECK` that the end is after the start.
- The overlap rule enforced in the database: a Postgres exclusion constraint on (room, time range), or on SQLite a check and insert inside one transaction. A check in the UI alone lets two people book the same slot.
- One function that creates and cancels bookings, and every route calls it. Cancelling is allowed only for the person who booked, or an admin.
- An access gate: a name login, or at least a shared passphrase. Otherwise anyone who can reach the page can cancel anyone's booking.
- Secrets and the database password in a git-ignored `.env` file, plus a one-command start.
- A host whose disk survives restarts (an office PC, a small VM, or a tunnel to your own machine). Free-tier hosts often wipe local data, which loses every booking.
- A nightly copy of the database file kept somewhere else, and a note in the README on how to restore it.
- One runnable check of the overlap rules: back-to-back meetings allowed, overlaps rejected, and a booking in one room not blocking another.

**Skip for this week**

- Separate frontend and backend deploys, Docker or Kubernetes, and microservices.
- CI pipelines, pre-commit hooks, secret scanners, a migration framework, and a database role split.
- Audit history tables and revision numbers. `created_by` and `created_at` are enough for ten people.
- Calendar sync (Outlook or Google), email or Slack notifications, recurring bookings, and a mobile app. Add them only when colleagues ask for them.
- Monitoring, uptime alerts, load tests, coverage targets, and a UI framework. Revisit all of this if the tool spreads beyond the office or a second developer starts maintaining it.
