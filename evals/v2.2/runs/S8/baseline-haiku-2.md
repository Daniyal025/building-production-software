# Meeting-room booking tool: set up vs. skip (one week, 10 users, 3 rooms)

## Set up

- **One Python web framework (Flask or FastAPI), one app file.** Server-rendered HTML forms are enough; no separate frontend build step.
- **SQLite in one file.** Ten people and three rooms will never outgrow it. Use plain SQL with a single `schema.sql` run at startup; no ORM, no migrations tool.
- **Tables: `rooms` and `bookings`.** Store times in UTC and show them in office local time.
- **Overlap check on the server, inside a transaction.** The UI can be friendly, but only the server check prevents double-booking.
- **Basic rules in code:** no bookings in the past, minimum 15-minute slots, a maximum length (say 4 hours), and users can cancel only their own bookings.
- **Identity from the existing login, not a new account system.** If the office has SSO or a reverse proxy that passes the user's name or email, trust that header. Otherwise a name typed once and stored in a cookie is enough for ten people.
- **One page per day, with a column per room.** Plain HTML plus a few lines of JS to refresh. Enough to see free slots at a glance.
- **Run it on one small machine behind Caddy or nginx for HTTPS.** A systemd service or a scheduled task keeps it up.
- **Nightly copy of the SQLite file** to another drive or cloud folder. This is the one piece of ops that matters.
- **A handful of pytest cases** for the overlap check and the cancel rule. These are the two things that must not break.
- **Pin dependencies in `requirements.txt`** and keep the list to the framework plus a test runner.

## Skip

- **Passwords, sign-up, password reset, email verification.** Use the existing login or a trusted header.
- **An admin panel.** Add or rename rooms with a config list or a direct DB edit.
- **Calendar integration (Outlook or Google sync).** Add it only if people ask after a week of use.
- **Recurring bookings, waitlists, approvals, reminders, Slack bots.** Nobody needs them to book three rooms.
- **Postgres, Redis, Docker, Kubernetes, background job queues, websockets.** None of them earns its keep at this scale.
- **A React or Vite frontend.** Plain HTML does the job.
- **CI pipelines, coverage targets, full test suites.** The handful of tests above is enough.

Skipped: calendar sync, admin panel, and recurring bookings. Add them when the team asks for them after a week of real use.
