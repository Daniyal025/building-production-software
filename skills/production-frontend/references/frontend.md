# Frontend and UX

Use when building UI, forms, editable grids, API clients, loading/saving states, mobile layouts or rendering server/LLM HTML.

Tiers: **T1** every project · **T2** production · **T3** high-stakes. Apply items at or below the project's tier.

## Checklist (read first)

**T1**

- [ ] "Saved" only after the server confirms; no writes on page load.
- [ ] Format numbers from unit metadata, never from labels; never inject unsanitised HTML.

**T2**

- [ ] One request layer: auth header, every error shape parsed, server message shown.
- [ ] One mutation hook for optimistic update, rollback and invalidation; visible pending state.
- [ ] Editability and controls derived from the server's rules and permissions.
- [ ] State keyed per document/sheet/chat; cleared on sign-out; stale ids handled.
- [ ] Accessibility: keyboard reachable, labelled inputs, visible focus, WCAG AA contrast; axe check in CI.
- [ ] Dates stored in UTC and shown in the user's zone; numbers/currency via locale formatters; no string-concatenated UI text.

**T3**

- [ ] Real-device checks for touch and number input; Content-Security-Policy; removed features' saved state migrated.

## Rules

### 1. One request layer
- Attaches auth, normalises every error shape (incl. 422 validation), validates responses, handles 401 globally.
- Honour session expiry; cross-tab sign-out; a query-key factory.
- **Why:** Multiple clients mean multiple bugs and the server's reason never reaches the user.
- **Real case:** Three clients, three error parsers, only one sent the token.
- **Look up:** Single choke point.

### 2. Honest feedback
- One mutation hook owns optimistic update, rollback, refusal and invalidation.
- "Saved" only after the refreshed data renders; one status component; no writes on page load.
- **Why:** False success destroys trust faster than slowness.
- **Real case:** A green tick appeared before the server answered; a page load issued seven writes.
- **Look up:** Optimistic vs pessimistic UI.

### 3. Never offer what the server refuses
- Derive editability from the server's rule — ideally the server sends `editable`.
- Gate controls with the same permission the endpoint enforces.
- **Why:** Affordances are promises.
- **Real case:** Cells looked editable but every save failed a DB constraint.
- **Look up:** Affordances.

### 4. State belongs to its owner
- Key UI state per document/sheet/chat; persist what users expect back; clear on sign-out; handle stale ids.
- Never render or seed baselines with the previous key's state.
- **Why:** Reused components carry state across contexts.
- **Real case:** A sheet switch sent a write with no user action because a baseline was taken one render early.
- **Look up:** State colocation; keyed remount.

### 5. Format from metadata; extras opt-in; migrate removed features' state
- Formatting comes from unit metadata, never from labels.
- Optional extras (charts, highlights) are opt-in.
- Before removing a control, migrate or ignore saved settings only it could undo.
- **Why:** Labels lie; removed controls strand users.
- **Real case:** An exchange rate rendered as 28,000% because its name contained "rate".
- **Look up:** Progressive disclosure.

### 6. Mobile and safety basics
- On touch, select ≠ edit; test real iOS/Android keyboards and in-app browsers.
- Sanitise any injected HTML (DOMPurify allowlist) and set a CSP.
- **Why:** Emulators don't have real keyboards; one renderer change turns into stored XSS.
- **Real case:** The iPhone number pad has no minus key.
- **Look up:** Stored XSS; inputmode.

### 7. Accessibility is a requirement, not polish
- Keyboard reachable, labelled inputs, visible focus, WCAG 2.2 AA contrast, meaningful alt text.
- Run an automated check (axe) in CI and a keyboard-only pass before release.
- **Why:** Inaccessible UI excludes users and is a legal risk in many markets.
- **Source:** Industry practice — WCAG 2.2; Deque axe-core.
- **Look up:** WCAG; a11y.

### 8. Internationalise from the first screen
- Store times in UTC, display in the user's zone; format numbers, dates and currency with locale formatters.
- No string-concatenated UI text; keep copy in message catalogs.
- **Why:** Retrofitting i18n means touching every screen.
- **Source:** Industry practice — Unicode CLDR; ECMAScript Intl API.
- **Look up:** i18n; l10n.

