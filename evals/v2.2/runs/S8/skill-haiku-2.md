# Room booking tool: what to set up and what to skip

For 10 colleagues and 3 rooms, the real risks are two people booking the same room at the same time, wrong times, and anyone being able to cancel anyone else's booking. Everything below serves those.

## Set up

- **One database, SQLite or Postgres.** SQLite is enough for this load and needs no server. Use Postgres only if you already run it.
- **Store times in UTC, show them in office local time.** Reject end times that are not after start times, and reject bookings in the past.
- **One function that creates a booking.** It checks for overlaps, saves the row and writes an audit line inside one transaction. Every route goes through it, so there is no second write path.
- **Prevent double-booking in the database, not just in the code.** Use a Postgres exclusion constraint on (room, time range), or in SQLite run the overlap check and insert inside `BEGIN IMMEDIATE`. A check in Python alone fails when two people click at once.
- **Validate input at the API boundary.** Check room ids, dates and lengths on the server even if the web form already checks them.
- **Know who is booking.** Put the app behind the company login or the office reverse proxy, and record the user on each booking. Do not build your own sign-up or password system. Only the booker or an admin can cancel.
- **Tests for the overlap rule, written first.** Write the back-to-back, overlapping and same-slot cases, watch them fail, then make them pass. Add one test that fires two bookings at the same slot at once.
- **Keep secrets and config in environment variables.** Keep the database file and any `.env` out of git.
- **Log errors with a stack trace and a daily copy of the database file.** A failed booking must show an error to the user, never a silent "saved".

## Skip

- **Frontend framework and build pipeline.** Plain server-rendered HTML with a little JavaScript is enough. Add a framework only when the page needs much more.
- **ORM and migration tool.** Write one schema file. Add a migration tool only after the schema has to change in a database people already use.
- **Live updates, websockets, queues, Redis or background workers.** A refresh button or a page reload every minute is enough at this size.
- **Calendar sync, email or Slack notifications, recurring bookings, waiting lists and approval flows.** Each one is a week of work on its own. Ask for them after the first version is used.
- **Fine-grained roles and permissions.** Booker-or-admin is enough.
- **Pagination, caching and load testing.** A few hundred bookings a month needs none of them.
- **Docker, Kubernetes, CI pipelines and a monitoring stack.** Run one process on one office machine or small VM. Add a pipeline only if you deploy often.
- **Coverage targets.** Test the booking rule and the cancel rule well. Do not chase a percentage.

Move up to a stricter setup if the tool holds data beyond names and room times, if it is reachable from outside the office, or if people rely on it after this week. Then add proper backups, monitoring and a security review.
