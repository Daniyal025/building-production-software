# Meeting-room booking tool: what to set up, what to skip

With 10 users, 3 rooms and one week, the only thing that really has to be right is that two people can never hold the same room at the same time. Keep everything else boring.

## Set up

- **Stack:** FastAPI or Flask, with server-rendered Jinja templates and a little HTMX. Skip a separate JS front end. One process, one repo.
- **Database:** SQLite in WAL mode. At this size you don't need Postgres. Keep the schema to two tables, `rooms` and `bookings` (room, user, start, end, title).
- **No double-booking, enforced in the database.** Check for overlap and insert in one transaction (`BEGIN IMMEDIATE` on SQLite). If you later move to Postgres, use an exclusion constraint on the time range. An app-level "check, then insert" has a race. Fail loudly with a clear "room already booked 10:00-11:00" message.
- **Time handling:** store UTC, display in the office timezone, and snap bookings to 15- or 30-minute slots. Use half-open intervals, so a 10-11 booking and an 11-12 booking don't clash. Handle daylight saving changes deliberately, even if only with a note.
- **Input validation:** end must be after start, no bookings in the past, a maximum length, and a room that exists. Reject bad input with a visible error. Never quietly clamp it to something plausible.
- **Know who booked:** put the app behind your company SSO or reverse-proxy auth, or use a simple login with a shared team password plus a name picker. Every booking records a user.
- **Permissions:** anyone can book, but only the owner (or an admin, hard-coded as a short list) can cancel or edit a booking.
- **A usable day/week grid:** one view showing the three rooms by time, with free and busy slots visible at a glance. This view is the product. Spend the UI time here.
- **One focused test file:** overlap and boundary cases (back-to-back, contained, spanning midnight, the same slot booked concurrently). Write the test, watch it fail, then make it pass. This is the one piece of logic worth guarding.
- **Deploy simply:** one small VM or an internal box, running in Docker or under systemd, with HTTPS from the reverse proxy. Keep config (secret, DB path) in environment variables.
- **Backup:** a nightly cron copy of the SQLite file (`sqlite3 .backup`) to somewhere else. That's roughly five lines of work, and it is what saves you if someone corrupts the data.
- **Basic logging:** log each create and cancel with the user and a timestamp, so "who deleted my booking?" can be answered.

## Deliberately skip

- **Microservices, queues, caching, Redis, Kubernetes, an ORM migration framework.** None of them has a caller at this scale. Write the schema as a plain SQL file.
- **Recurring bookings, calendar sync, email or Slack notifications, an admin panel, and room-equipment features.** Add them only when colleagues ask. Recurring bookings are the likeliest first request, and they are also the biggest source of edge cases.
- **Heavy process:** a CI pipeline with many stages, metrics and dashboards, load testing, i18n, an API versioning policy. A README with run and backup instructions is enough.

**What would change this:** if it grows past one team, needs external guests, or becomes something people depend on daily, move to Postgres, add notifications and add monitoring.
