# API evolution and change management

Use when changing a public or internal API, event schema or database contract used by other teams or clients, versioning, deprecating, or rolling out risky changes with feature flags.

Tiers: **T1** every project · **T2** production · **T3** high-stakes. Apply items at or below the project's tier.

## Checklist (read first)

**T1**

- [ ] Changes additive by default: never change the type or meaning of an existing field.

**T2**

- [ ] Clients tolerant of unknown fields; servers tolerant of missing optional fields.
- [ ] Breaking change → new version + deprecation notice (Deprecation/Sunset headers) + usage telemetry before removal.
- [ ] Risky changes behind feature flags with an owner and an expiry date; kill switch for critical paths.

**T3**

- [ ] Consumer-driven contract tests between services/clients.
- [ ] Expand/contract across long-lived clients (mobile apps, partners); old versions supported for a published period.

## Rules

### 1. Additive by default; tolerant on both sides
- Never change the type or meaning of an existing field; add new fields instead.
- Clients ignore unknown fields; servers treat new optional fields as optional.
- **Why:** Most breaking changes are accidental renames or type changes.
- **Source:** Industry practice — Postel's robustness principle; Google API Design Guide (compatibility).
- **Look up:** Backward compatibility; tolerant reader.

### 2. Break deliberately: version, announce, measure, remove
- A breaking change gets a new version, Deprecation/Sunset headers or notices, and usage telemetry.
- Remove the old version only when telemetry shows it unused or the published period ends.
- **Why:** Long-lived clients (mobile apps, partners) can't upgrade on your schedule.
- **Source:** Industry practice — RFC 8594 (Sunset header); Stripe API versioning.
- **Look up:** API versioning; deprecation policy.

### 3. Feature flags with owners and expiry
- Risky changes ship dark behind a flag; critical paths get a kill switch.
- Every flag has an owner and a removal date; remove it after rollout.
- **Why:** Flags decouple deploy from release, but forgotten flags become permanent complexity.
- **Source:** Industry practice — Martin Fowler / Pete Hodgson "Feature Toggles".
- **Look up:** Feature toggles; dark launches.

### 4. Contract tests between producers and consumers
- Consumers publish the expectations they rely on; providers run them in CI.
- **Why:** Integration tests across teams are slow and flaky; contract tests catch the break at the source.
- **Source:** Industry practice — Pact; consumer-driven contracts (Ian Robinson).
- **Look up:** Consumer-driven contracts.

