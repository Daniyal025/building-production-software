# Room booking tool: what to set up, what to skip

Context: 10 users, 3 rooms, one week, side project.

## Set up

- **One small framework, one process.** Flask or FastAPI with server-rendered Jinja templates. No separate SPA, no build step, no Node.
- **SQLite file for storage.** It handles 10 users easily. Back it up by copying the file in a nightly cron job.
- **Three tables:** `rooms`, `users` (or just a name/email string), and `bookings` (`room_id`, `user`, `start`, `end`, `title`).
- **Enforce double-booking prevention in one place.** Reject any booking where `start < existing_end AND end > existing_start` for the same room. Do it inside a transaction, or use a DB constraint or `BEGIN IMMEDIATE`. This is the one piece of real logic. Write 5 to 6 tests for it, covering back-to-back bookings, overlaps, and containment.
- **Validate input at the boundary.** End must be after start, no bookings in the past, and a sane maximum duration. Show a clear error message.
- **Simple auth.** Use your company SSO or Google/Microsoft login if it is cheap to add. Otherwise use one shared password behind the VPN or office network, with a name picker. Don't build password storage or reset flows.
- **One main page.** It shows a day or week grid per room, with a booking form and a "cancel my booking" button. Plain HTML and a little CSS. Use `<input type="datetime-local">` for time entry.
- **Store times in UTC, display in the office timezone.** Decide this on day one. It is the usual source of late bugs.
- **Deploy on one small box or internal VM.** Use gunicorn or uvicorn behind whatever reverse proxy you already have, or just run it under systemd. A Dockerfile is fine if the team already uses Docker.
- **A basic log and a `/health` endpoint.** That is enough to debug and monitor.

## Deliberately skip

- **Postgres, Redis, Celery, message queues, microservices.** Nothing here needs them at this scale.
- **A React/Vue frontend, an API-first design, and an OpenAPI client.** Server-rendered pages are faster to build.
- **Recurring bookings, waitlists, approvals, and room amenities or capacity filters.** Add them only if people ask after launch.
- **Calendar sync and Slack/email notifications.** Maybe an `.ics` download later. Don't integrate Outlook or Google Calendar in week one.
- **Roles and permissions, admin UI, and audit logs.** Anyone can book, and only the creator can cancel. Manage rooms by editing the DB or a seed script.
- **CI/CD pipelines, Kubernetes, and infrastructure as code.** Deploy with `git pull` and a restart.
- **Scale and perf work, such as caching and pagination.** Thirty rooms-days of data fits in memory.

## Cut order if the week slips

1. Cancel button
2. Overlap check and tests
3. Weekly grid view
4. Auth
5. Everything else

If the first two work, you have a useful tool.
