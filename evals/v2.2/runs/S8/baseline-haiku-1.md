# Room booking tool for 10 colleagues and 3 rooms: set up vs skip

## Set up

- One small Python web app (Flask or FastAPI) with plain server-rendered HTML pages. Use whichever you already know.
- SQLite as a single database file. Ten users and three rooms will never outgrow it.
- One `bookings` table (room, user, start, end). Make the database reject overlapping bookings for the same room, not just the UI. This is the one rule that must hold.
- Store times in UTC and display them in office local time.
- A day view per room plus a simple form to book and cancel.
- Users can cancel only their own bookings; one admin flag can override. Without this, anyone can delete anyone's booking.
- Login through whatever your company already has (SSO via a proxy, or a shared invite link). Do not build your own password system.
- Server-side validation: end after start, no bookings in the past, a maximum duration.
- A few tests for overlap rejection and cancel permissions. These are the parts that fail silently.
- Run it on one office machine or small VM with a daily backup of the SQLite file, and a log line for each booking or cancel.

## Skip

- Registration, password reset, email verification, and roles beyond one admin flag.
- Email or Slack notifications and Outlook or Google calendar sync. Add later if people ask.
- Recurring bookings, waitlists, approval flows, and capacity or equipment rules.
- A JavaScript framework or build step. Plain HTML forms are enough; refresh the page to see changes.
- Real-time updates with WebSockets. Polling is unnecessary at this scale.
- Docker orchestration, Kubernetes, Redis, Celery, or a message queue.
- An ORM and a migration tool. One `schema.sql` file is enough.
- A native mobile app, analytics dashboards, multi-office support, and translations.
- A CI pipeline, staging environment, or full test coverage.
