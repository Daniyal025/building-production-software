# Room booking tool: set up vs. skip

Ten users, three rooms, one week. Treat it as a prototype that happens to be used daily: spend your effort on the one thing that must be correct (no double-bookings) and skip everything else.

## Set up

- **One small app, one process.** FastAPI or Flask serving server-rendered pages (Jinja plus a little HTMX or plain forms). Skip a separate SPA and build step.
- **SQLite, one file, or Postgres if your company already runs one.** At this scale SQLite is fine. Back it up by copying the file nightly with a cron job.
- **Make the database refuse double-bookings.** This is the core rule. Do the overlap check and the insert in one transaction (`BEGIN IMMEDIATE` on SQLite). On Postgres, use an exclusion constraint on `(room_id, tstzrange(start, end))`. Don't rely on "check then insert" in app code, because two people clicking at once will both pass the check.
- **Validate input on the server.** End must be after start. Reject bookings in the past. Use a fixed slot size (15 or 30 minutes), and limit the maximum length and how far ahead people can book. Show clear error messages such as "Room 2 is taken 14:00-15:00 by Sara". Never fail silently.
- **Store times in UTC and display them in the office time zone.** Use `zoneinfo`. Test one booking across a DST change, because this is the classic bug in booking tools.
- **Know who booked.** Use your company SSO or a trusted-header proxy if it is cheap. Otherwise use a shared password plus a name picked from a fixed list of the 10 people. Record `booked_by` on every row. Only the owner (or an admin) can cancel.
- **Cancel and edit through the same code path as create.** One function validates, checks overlap and writes. Don't add a second path for edits that skips the checks.
- **A day or week grid view per room.** This is the screen people will actually use, so make it readable on a phone. Seed the three rooms from a config file or a migration.
- **A handful of tests for the booking function.** Cover exact overlap, partial overlap, back-to-back bookings (which must be allowed), the concurrent-insert case, and the DST case. Write each test, watch it fail, then make it pass.
- **Deploy simply.** One small VM or internal box, a systemd service or one Docker container, behind your existing internal network or VPN. Keep config and secrets in environment variables. Add a `/health` route and have the process log errors to stdout.

## Deliberately skip

- **Calendar sync, email or Slack notifications, and recurring bookings.** Each is a real project of its own. Add them only when colleagues ask for them in week two or later.
- **Roles and permissions, an admin UI, and user management.** Ten known people don't need these. Edit rooms and users in the database or config file.
- **Microservices, queues, caching, an ORM-heavy architecture, Kubernetes, and performance tuning.** Three rooms and ten users is a handful of rows a day.
- **Heavy CI/CD, a staging environment, and formal monitoring or alerting.** Run the tests locally. Add basic CI later if other people start contributing. A weekly look at the logs is enough.
- **Internationalisation, a design system, and an API versioning strategy.** Nobody needs these for ten colleagues in one office.

## What would make you upgrade

Add more rigour if the tool becomes something other teams depend on, if it needs to hold personal or sensitive data, or if a second developer joins. At that point add proper SSO, automated backups with a restore test, and CI.
