# Security

Use when adding authentication or authorisation, exposing a service publicly, handling secrets, setting up proxies, tunnels or webhooks, copying production data.

## Checklist (read first)

- [ ] Default-deny router; route-walking 401/403 test; docs off; strict CORS.
- [ ] Secret scanner; rotation on leak; secrets as 600 files per service.
- [ ] Proxy-set XFF; progressive delay; OAuth on tunnels; HMAC webhooks; CSRF checks.
- [ ] Scrubbed dev data; role+host test guard; fail-closed config.

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

