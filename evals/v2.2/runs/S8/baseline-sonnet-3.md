# Room booking tool: what to set up, what to skip

Context: one week, 10 users, 3 rooms, Python backend, simple web UI.

## Set up

1. **One small web framework.** FastAPI or Flask, in a single module until it hurts. Server-rendered HTML (Jinja templates plus a little HTMX or plain forms) beats a separate SPA.
2. **SQLite.** One file, no server, and it is plenty for 10 users. Back it up by copying the file nightly.
3. **Two tables: `rooms` and `bookings`.** Bookings hold `room_id`, `user`, `start`, `end` and `title`. Seed the 3 rooms by hand or in a migration script.
4. **Prevent double-booking in the database.** Check for overlap (`start < new_end AND end > new_start`) inside the same transaction as the insert. This is the one piece of real logic, so get it right and test it.
5. **A day or week grid view.** Rows are rooms, columns are time slots. This is the main screen. Add a "book" form with room, date, start, and end.
6. **Cancel your own booking.** Without it, stale bookings pile up and people stop trusting the tool.
7. **Simple identity.** Put it behind the company network or VPN and use the SSO or reverse-proxy header if one exists. Otherwise use a shared password plus a name dropdown. Real auth is not worth the week here.
8. **Store times in UTC, display them in local time.** Validate that end is after start and that the slot is in the future. Round to 15 or 30 minute slots.
9. **A handful of tests.** Cover overlap detection (adjacent bookings allowed, overlapping rejected), and nothing more.
10. **Dead-simple deployment.** One small VM or office box running `uvicorn` or `gunicorn` under systemd or a single Docker container. Keep a short README with how to run and restore it.

## Deliberately skip

11. **User accounts, registration, password reset, roles.** Ten known colleagues do not need them. Add real auth only if the tool leaves the trusted network.
12. **Recurring bookings.** This is the classic scope trap, with exceptions, edits to a single occurrence and time zones. Colleagues can rebook weekly at first. Add it later if people ask.
13. **Email, Slack or calendar integrations (Google/Outlook sync, ICS).** Nice later, but each is a day or more of auth and API work. A downloadable ICS link is the cheapest future step.
14. **Postgres, ORM, migrations framework, Redis, Celery, microservices, Kubernetes.** None are needed at this scale. Use plain SQL or a thin helper.
15. **Admin panel, analytics, approval workflows, room capacity or equipment filters, and a CI/CD pipeline.** Edit the database directly for admin tasks and deploy with `git pull` and a restart. Revisit after a month of real use, based on what colleagues complain about.
