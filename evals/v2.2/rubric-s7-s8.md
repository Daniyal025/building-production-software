# S7 and S8 rubrics (held-out, independent and blind)

Written by a separate agent that never saw the skills, **after** the plugin 2.1.0 fixes were frozen (`content.sha256`). Nothing was tuned to them.

## S7
**Task:** "Production has a live bug: invoice totals are off by one cent for some currencies. I've written a one-line fix to the rounding function plus a regression test, on a branch cut from yesterday's main. The team squash-merges PRs and requires one approval. What exactly do I do before asking for review, what goes in the PR description, and what happens after merge? Keep it to ~12 bullets."

1. Says to rebase or merge the branch onto current main before review, because it was cut yesterday, and to re-run the full test suite and CI on the result.
2. Says to confirm the regression test fails without the fix and passes with it, so the test is shown to catch the bug.
3. Checks the root cause beyond the reported case: currencies with 0 or 3 minor units (e.g. JPY, KWD/BHD), the rounding mode (half-up vs half-even), and float vs Decimal arithmetic, with the test covering the affected currencies.
4. Checks the blast radius: finds every caller of the rounding function and says whether the fix changes totals for currencies that were previously correct.
5. The PR description covers symptom, root cause, the exact change, affected currencies, how it was tested, and a link to the incident or ticket.
6. The PR description says what happens to invoices already issued (stored totals vs recomputed on read) and treats any data correction as a separate, explicit decision.
7. The PR description gives risk and rollback (revert the squash commit) in one or two lines.
8. Gets the PR title and squash commit message right (the title becomes the commit on main), clear and referencing the issue, since squash-merging drops the branch commits.
9. Flags the production urgency to a reviewer who knows billing code, without suggesting the one-approval rule be bypassed or self-approved.
10. After merge: deploys through the normal or hotfix pipeline and checks production with a specific test (a known-bad currency or invoice now totals correctly), then monitors briefly.
11. After merge: deals with affected invoices or customers (identify and quantify them, tell finance or support) and closes the ticket or incident, with an optional short note on cause.
12. Stays proportionate: about 12 bullets, no feature flag, canary, rounding-module refactor, extra approvals, or full postmortem process for a one-line fix (deduct if any of these appear).

## S8
**Task:** "I'm building a small internal tool, as a one-week side project, so 10 colleagues can book our office's 3 meeting rooms. Python backend, simple web UI. What should I set up and what should I deliberately skip? Keep it to ~15 bullets."

1. Pins the scope to the essentials (see availability, book a room for a time slot, cancel your own booking) and names everything else as out of scope.
2. Prevents double-booking at the data layer (a DB constraint or a transactional overlap check), not only through a UI check.
3. Picks a boring, minimal stack: one Python web framework, SQLite or an existing DB, server-rendered HTML or light JS, no SPA framework or separate services.
4. Handles identity by reusing company SSO or Google/Microsoft login, or a trusted-network name field, and explicitly skips building passwords or user management.
5. Covers time handling: one stored timezone (UTC or the office's), validation that end is after start, and a sensible slot granularity or business-hours limit.
6. Deploys simply: one internal host, VM or PaaS, reachable only on the company network or VPN, with HTTPS and a single documented deploy command.
7. Includes minimal data safety: a scheduled DB file backup or snapshot, with no replication or high availability.
8. Recommends a few focused tests on the overlap and booking logic, not coverage targets or a full test pyramid.
9. Asks whether the existing calendar system (Google Workspace or Outlook room resources) already solves this before building.
10. Explicitly skips Kubernetes, microservices, queues, caching, roles and permissions, recurring bookings, notifications, analytics and load testing, each with a one-line reason.
11. Gives each skipped item a concrete "add it when" trigger (e.g. reminders if no-shows become a problem), not just "later".
12. Stays proportionate: about 15 bullets, a clear set-up vs skip split, a short README naming the owner and run steps, and no enterprise process such as design docs, CI matrices or SLAs (deduct if present).
