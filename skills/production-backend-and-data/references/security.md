# Security

Use when adding authentication or authorisation, exposing a service publicly, handling secrets, setting up proxies, tunnels or webhooks, copying production data.

Tiers: **T1** every project · **T2** production · **T3** high-stakes. Apply items at or below the project's tier.

## Checklist (read first)

**T1**

- [ ] Anything other people can reach has a gate — one shared secret or passphrase is enough for a prototype.
- [ ] No secrets committed (env file git-ignored); a leaked secret is rotated, not just deleted.
- [ ] If you store passwords at all (prefer not to in a prototype): argon2id/bcrypt, never logged.

**T2**

- [ ] Default-deny auth on the whole router; only health is public.
- [ ] Secret scanner in pre-commit and CI.
- [ ] A test walks every route: 401 without a token, 403 for the wrong role.
- [ ] Secrets as files (mode 600) per service; never in URLs, logs or command lines.
- [ ] Behind a proxy: proxy sets X-Forwarded-*; progressive delay not hard lockout; CSRF origin checks on writes.
- [ ] Dependencies updated automatically (Dependabot/Renovate) and audited in CI; lockfiles committed.
- [ ] Personal data classified; retention and deletion path defined; encrypted in transit and at rest.

**T3**

- [ ] Threat model (e.g. STRIDE) for features handling money, personal data or external input.
- [ ] Public tunnels behind an identity gate; webhooks verified by HMAC signature with a replay window.
- [ ] Dev data scrubbed; test-DB guard by role + host; config without a safe default fails at start-up.

## Rules

### 1. Default deny at the router
- Auth dependency on the whole router; only `/health` public.
- A test walks every route asserting 401 without token and 403 for wrong role.
- API docs off in production; CORS = own origin, never `*` with credentials.
- **Why:** Per-route auth gets forgotten; UI hiding is not authorisation.
- **Real case:** A well-built auth module protected only a few routes; every write was open.
- **Look up:** OWASP A01 Broken access control.

### 2. Secrets hygiene
- Secret scanner in pre-commit and CI; a leaked secret is public — rotate it; never reuse passwords.
- Secrets in files (mode 600) mounted only into the service that needs them; never in URLs, logs or command lines.
- **Why:** Git history is forever; env vars appear in inspect/ps output.
- **Real case:** A real password sat in a test fallback URL and doubled as another system's password; an access log printed a token from a query string.
- **Look up:** Secret rotation; log redaction.

### 3. Proxies, tunnels and webhooks
- The proxy strips and sets X-Forwarded-*; the backend trusts that hop only.
- Progressive delay instead of hard lockout; identity gate (OAuth) in front of any public tunnel; Origin/Sec-Fetch-Site check on writes.
- Machine callbacks get their own route with HMAC signature verification; use official provider APIs only.
- **Why:** Client-supplied headers are attacker-controlled; secret URLs leak.
- **Real case:** Spoofed XFF beat a rate limiter, while 10 bad logins via the shared proxy IP locked the only account.
- **Look up:** IP spoofing; CSRF; webhook signatures.

### 4. Developer data and defaults
- Dev dumps exclude auth and conversation tables; track every copy with a deletion date.
- Test-database guard = a role that doesn't exist in production + local host.
- Config without a safe default fails at start-up; never default to production; uniform responses to avoid enumeration.
- **Why:** Laptops leak; name-based guards match "latest".
- **Real case:** A test guard accepted any DB name containing "test".
- **Look up:** Data minimisation; secure defaults.

### 5. Threat-model features that handle money, personal data or external input
- Before building, walk STRIDE (spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege) for the feature's data flows.
- Turn each credible threat into a test, control or accepted risk with an owner.
- **Why:** Most security bugs are design omissions, not coding slips.
- **Source:** Industry practice — OWASP Threat Modeling Cheat Sheet; Microsoft STRIDE.
- **Look up:** Threat modelling; STRIDE.

### 6. Keep dependencies updated and audited
- Automated update PRs (Dependabot/Renovate); vulnerability audit in CI; lockfiles committed.
- Generate an SBOM for released artefacts when customers or regulators ask.
- **Why:** Known-vulnerable dependencies are the cheapest attack there is.
- **Source:** Industry practice — OWASP Top 10 A06 (vulnerable components); SLSA; CISA SBOM guidance.
- **Look up:** Supply-chain security; SBOM.

### 7. Classify personal data and plan its lifecycle
- Know which columns hold personal data; encrypt in transit and at rest; minimise what you collect.
- Define retention and a deletion path (right to erasure) before launch.
- **Why:** Data you don't hold can't leak; deletion retrofitted later is expensive.
- **Source:** Industry practice — GDPR Art. 5 & 17; OWASP Privacy Risks.
- **Look up:** Data minimisation; right to erasure.

