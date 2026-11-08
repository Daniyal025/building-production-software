# Observability and incidents

Use when adding logging, metrics, tracing, dashboards, alerts or SLOs, setting up on-call, responding to an incident, or writing a postmortem.

Tiers: **T1** every project · **T2** production · **T3** high-stakes. Apply items at or below the project's tier.

## Checklist (read first)

**T1**

- [ ] Errors are visible to you: logged once with context, never swallowed.

**T2**

- [ ] Structured logs with a request/correlation id.
- [ ] An external uptime check on the user-facing endpoint.
- [ ] RED metrics (rate, errors, duration p50/p95/p99) per endpoint and job; USE for key resources.
- [ ] SLOs for the main user journeys; alerts on symptoms against the error budget, each with a runbook link.
- [ ] One "is it working for users?" dashboard, including data freshness.
- [ ] Incident basics: severity levels, one incident lead, a comms channel, mitigate before fixing.
- [ ] Blameless postmortem for every serious incident; actions have owners and dates; each becomes a test or alert.

**T3**

- [ ] Distributed tracing (OpenTelemetry) across services and queues.
- [ ] On-call rotation with alert-noise reviews; game days for the top failure modes.

## Rules

### 1. Three signals, one correlation id
- Structured logs, metrics and traces all carry the request/correlation id across services and queues (OpenTelemetry).
- Log an error once, where it is handled, with context — not at every layer.
- **Why:** Without correlation you debug by guessing timestamps.
- **Source:** Industry practice — OpenTelemetry specification; Google SRE book ch. 6.
- **Look up:** Observability; distributed tracing.

### 2. RED for services, USE for resources
- Rate, Errors, Duration (p50/p95/p99) per endpoint and job.
- Utilisation, Saturation, Errors for databases, pools, queues and hosts.
- **Why:** Averages hide the users who suffer; resource saturation predicts the next outage.
- **Source:** Industry practice — Tom Wilkie's RED method; Brendan Gregg's USE method.
- **Look up:** RED/USE methods; tail latency.

### 3. Alert on symptoms against SLOs
- Define SLOs for the main user journeys (availability, latency, data freshness).
- Page only on user-visible symptoms burning the error budget; every alert has a runbook link and is actionable.
- **Why:** Cause-based alerts create noise; noise teaches people to ignore pages.
- **Source:** Industry practice — Google SRE Workbook ch. 2 and 5 (SLOs, alerting on SLOs).
- **Look up:** SLO; error budget; alert fatigue.

### 4. Run incidents with roles and mitigate first
- Severity levels, one incident lead, one comms channel, a running timeline.
- Mitigate (rollback, flag off, scale) before root-causing.
- **Why:** Uncoordinated responders slow recovery and lose the timeline.
- **Source:** Industry practice — PagerDuty Incident Response guide; Google SRE book ch. 14.
- **Look up:** Incident command; MTTR.

### 5. Blameless postmortems that change the system
- Write one for every serious incident: impact, timeline, contributing factors, what went well.
- Each action has an owner and a date, and becomes a test, alert or guard.
- **Why:** Blame hides information; actions without owners never happen.
- **Source:** Industry practice — Google SRE book ch. 15; Etsy "Blameless PostMortems".
- **Look up:** Blameless postmortem.

