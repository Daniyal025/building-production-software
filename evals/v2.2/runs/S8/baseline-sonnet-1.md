# Room booking tool: what to set up, what to skip

Scope: 10 users, 3 rooms, one week. Build the smallest thing that stops double-booking.

## Set up

- **FastAPI** (or Flask) with one process and a handful of routes. Don't use Django for this.
- **SQLite** with the stdlib `sqlite3` module or SQLModel. One file, no server, trivial backups.
- **Two tables:** `rooms` (3 rows, seeded) and `bookings` (id, room_id, user_name, start, end, title).
- **Double-booking prevented in the database transaction,** not only in app code. Check for overlap (`start < new_end AND end > new_start`) inside the same transaction as the insert. This is the one piece of real logic, so write one test for it.
- **Server-rendered UI** with Jinja2 templates and a little HTMX or plain forms. A page per day showing the 3 rooms as columns or rows, plus a booking form and a cancel button.
- **Native inputs:** `<input type="datetime-local">` or date plus time selects. No calendar library.
- **Simple identity:** a shared company SSO or reverse-proxy auth header if you already have one. Otherwise a name dropdown or cookie ("who are you?"). 10 trusted colleagues don't need passwords.
- **Validation at the edges:** end after start, a sane duration, and a room that exists. Return clear error messages in the UI.
- **Time handling:** store everything in one timezone (the office's), or UTC with conversion at display. Decide up front, because this is where bugs come from.
- **Deploy:** one small VM or internal box, run with `uvicorn` behind systemd or a single Docker container. Back up the SQLite file nightly with cron.

## Deliberately skip

- **Accounts, passwords, roles, admin panel:** edit the 3 rooms with a SQL statement if they ever change.
- **Recurring bookings:** the biggest scope trap. Add it only if people actually ask. Meanwhile they can book weekly slots by hand.
- **Calendar integrations** (Google/Outlook sync, ICS feeds, email invites): add later if the manual workflow hurts.
- **Notifications and reminders:** colleagues can see the page.
- **SPA frontend, React, build tooling, a separate API/frontend split:** none of it pays off at this size.
- **Postgres, Redis, Celery, Kubernetes, CI pipelines, microservices:** SQLite and one process handle 10 users with room to spare.
- **Fancy conflict resolution, waitlists, approval flows, room capacity or equipment filters:** first-come-first-served is enough.

## Rough week plan

- Days 1-2: schema, booking and overlap logic, the test.
- Days 3-4: day view, booking form, cancel.
- Day 5: identity, deploy, backup.
- Then ask colleagues what annoyed them before building anything else.
