# Deployment and operations

Use when deploying, writing a runbook, setting up containers, backups, monitoring, health checks, upgrading images or runtimes, or working on the dev environment.

## Checklist (read first)

- [ ] SHA images; previous kept; deploy script; small releases.
- [ ] Build → migrate → swap; health periods from worst case.
- [ ] Every runbook command executed; ON_ERROR_STOP.
- [ ] Offsite encrypted backups; rehearsed restore.
- [ ] Uptime check; job fail-pings; freshness visible.
- [ ] Non-root, pinned, limited containers; upgrade notes read; dev mirrors prod.
- [ ] Post-deploy items tracked; docs updated in the same commit.

## Rules

### 1. Immutable, small, reversible releases
- SHA-tagged images; keep the previous one; one deploy script: backup → pull → migrate → start → verify → prune.
- Release often; each release note lists migrations, downtime and paired deploys.
- **Why:** Rollback must not require a rebuild or a data loss.
- **Real case:** Images tagged `:local` meant rollback = rebuild + restore that lost user data.
- **Look up:** Release engineering.

### 2. Order deploys for their failure window
- Build → migrate (additively) → swap.
- Size health-check and grace periods from measured worst cases.
- **Why:** Old code briefly runs against the new schema.
- **Real case:** Migrating before building let the old API read a dropped column.
- **Look up:** Zero-downtime deploys.

### 3. Every documented command is executed
- Run each runbook command on a clean machine; `ON_ERROR_STOP` so failures exit non-zero; grep docs when behaviour changes.
- **Why:** A runbook that exits 0 on failure is worse than none.
- **Real case:** A documented `psql -f` silently didn't apply the migration.
- **Look up:** Executable docs.

### 4. Backups are proven by restores
- Offsite, encrypted backups; restore-check in a throwaway container; timed quarterly rehearsal; back up config too.
- **Why:** Same-disk backups die with the disk.
- **Real case:** Backups sat on the same SSD as production.
- **Look up:** RPO/RTO.

### 5. Visible health and freshness
- External uptime check; fail-ping on job failure; `/health` cheap and never raises; freshness on a screen operators read.
- **Why:** Nobody reads logs until something is already wrong.
- **Real case:** A scraper failed for weeks unnoticed.
- **Look up:** Observability.

### 6. Container and environment hygiene
- Non-root USER; digest-pinned images; memory and log limits on every service.
- Read upgrade notes before bumping majors; mount directories, not files; test with production env vars.
- Dev machine mirrors production (DB in containers); check port ownership; UTF-8 without BOM.
- **Why:** Defaults change between versions; local quirks hide real behaviour.
- **Real case:** A database image moved its data path; two servers shared one port on Windows; a local DB made timings 2× off.
- **Look up:** Dev/prod parity.

### 7. Done includes post-deploy steps and docs
- Migrations, backfills and real-device checks are unchecked items until done.
- Docs change in the same commit as behaviour; no volatile counts in docs.
- **Why:** Code-complete isn't user-complete; stale docs mislead the next engineer.
- **Real case:** A "start here" doc said a console was live while seven of its routes returned 404.
- **Look up:** Definition of done.

