# Production Concierge Thread Isolation E2E Evidence — 2026-10-22

## Scope

Documentation-only follow-up to merged PR #3309 (merge commit `1b384d9dcbd341803af940bfedc6e5d893a4cbb8`). This record separates observed frontend/API behavior from product decisions and remaining security QA. No production code, configuration, database, or consultation data changes.

## Evidence provided by Mother Ship

- Two authenticated QA account screenshots for the same URL path `/concierge?tid=92` on 2026-10-22 circa 17:01 JST. One screenshot shows consultation-specific recommendation content and another shows no consultation-specific recommendation content.
- Account identities differ per Mother's statement. The screenshots do not themselves contain sufficient account identification to independently bind each API request to its user.
- In the earlier `tid=88` investigation, a screenshot of an Incognito window showing consultation-specific content existed **before** PR #3309 was merged. That phenomenon was not conclusively explained by the confirmed local-cache defect. Do not carry forward a passing Incognito result from old tests.

## Production Render API evidence

For `GET /api/concierge-threads/92/` (JST, 2026-10-22):

| Time | HTTP |
| --- | --- |
| 17:01:02 | 200 |
| 17:01:07 | 200 |
| 17:01:19 | 404 |
| 17:01:23 | 404 |

These observations are consistent with the UI contrast (authorized content displayed versus denied/no-content view). The server access log does not independently identify the account behind each response. No raw requests, secrets, cookies, consultation text, account emails, or IPs are reproduced here.

## Assessment

- **UI account-separation smoke test:** PASS-equivalent based on Mother Ship screenshots and reported account switch.
- **API denial occurrence:** VERIFIED (404); other requests returned 200. Account-to-response association remains indirect.
- **Full cross-account authorization E2E:** NOT FORMALLY CLOSED pending bounded re-test.
- **Fresh Incognito unauthorized request after PR #3309:** NOT EXECUTED / NO PASS CLAIM.
- **Authenticated + signed anonymous-cookie on a shared browser:** PRODUCT-CONTRACT DECISION PENDING. Existing backend logic permits access to ownerless threads matching that browser's signed anonymous cookie, even when another authenticated account is active. This is not the same as authenticated account A's owned thread being shared with B.

## Mother Ship gate: anonymous cookie handling on shared devices

Unresolved policy question: should an anonymous consultation associated with a shared browser remain accessible after an account change, or should that association be isolated/cleared at an authentication boundary? No behavioral changes may be inferred or implemented from this record. Record an explicit Mother Ship decision and required guest-to-login preservation behavior before any change.

## Remaining QA (authorized test data only)

1. On confirmed production deployment containing PR #3309, open an owned test thread in account A. Expect content and a 200 for the detail API.
2. In a separately authenticated account B, open exactly the same A-owned test thread URL. Expect no A private content and a 404 for the detail API. Correlate requests by timestamp and browser Network status. Do not log personal content.
3. In a **new** Incognito window without login or previously created anonymous consultation, open the same URL. Expect 404 and no consultation-specific content. Confirm Network status, not merely UI appearance.
4. Independently confirm an anonymous visitor can reopen its own anonymous test consultation in the same browser identity.
5. Observe behavior after anonymous guest → login and account-switch on a shared test browser, and refer any desired policy change to Mother Ship.

## Gate status

```text
PR_3309 = MERGED
ACCOUNT_SEPARATION_UI_SMOKE = PASS_EQUIVALENT
DETAIL_API_200_AND_404 = OBSERVED
FRESH_INCOGNITO_PRODUCTION_QA = OPEN
ANONYMOUS_COOKIE_SHARED_DEVICE_POLICY = MOTHER_SHIP_DECISION_PENDING
PRODUCTION_SECURITY_E2E = OPEN
```

STOP: Do not mark formal security E2E closed or claim new Incognito verification until real evidence is recorded.

## Mother Ship decision — B (2026-10-22)

**DECIDED:** Separate anonymous consultation access when changing authenticated accounts or crossing the login/logout identity boundary. Do not leave an earlier browser user's anonymous consultation readable merely because a signed anonymous cookie persists. **This is a product-security requirement, not an implementation approval.** Existing anonymous consultations must remain usable by their rightful anonymous owner; guest-to-login continuation must be explicitly specified and tested before runtime changes. The production security E2E gate remains OPEN until implementation, deployment, and QA.

## Existing implementation audit (develop after PR #3309)

- `backend/temples/services/anonymous_id.py`: `concierge_anon_id` is an HttpOnly signed cookie, issued with a 90-day max age and path `/`; no cookie-clearing operation is defined in this module.
- `backend/temples/api/views/concierge.py`: `ConciergeThreadDetailView` first filters by authenticated user ownership and then, when no owned thread is found, falls back to an ownerless thread matching the request's signed anonymous ID. Hence an authenticated account can still read a preceding guest's ownerless thread on a shared browser if the signed cookie remains available. No evidence of bypassing ownership of *authenticated-owned* threads was found in this inspected code.
- `apps/web/src/lib/auth/AuthProvider.tsx`: login clears `concierge:eventsByThread` while intentionally preserving same-tab anonymous snapshot; logout clears the thread cache and anonymous snapshot. Neither operation deletes the backend-scope HttpOnly `concierge_anon_id` cookie.
- `apps/web/src/lib/concierge/conciergeLocalState.ts`: the helper removes only browser localStorage/sessionStorage entries, not HttpOnly cookies.

## Design requirement and proposed implementation contract (NOT YET APPROVED)

1. **Separate ownership from browser identity.** An authenticated request must not implicitly gain access to an ownerless thread via a cookie inherited from a previous browser user. The server must enforce this, not rely solely on clearing the frontend cache.
2. **Preserve guest flow.** An anonymous visitor who created a consultation must be able to revisit it within their valid anonymous session until a defined identity-boundary transition occurs.
3. **Preserve guest-to-login continuity.** Determine whether the original guest's consultation will be explicitly claimed (with proof of anonymous possession, atomic ownership transition, and replay protection), or shown through a time-bounded migration handoff. Do not silently claim all anonymous threads or delete existing historical records.
4. **Make identity transitions explicit.** Audit login, logout, account switch, refresh, failed login, multi-tab sessions, and the frontend BFF/backend cookie boundaries. Any cookie invalidation/rotation must occur in the HTTP response from the component that can modify the cookie; JavaScript cannot delete an HttpOnly backend cookie directly.
5. **Fail closed.** Authentication or network failure must not be interpreted as successful identity transfer. Preserve public shrine access and keep private consultation data hidden until the rightful identity is verified.
6. **Validate cookie transport.** Identify which origin actually sets and forwards `concierge_anon_id` in production, and audit the effective SameSite, Secure, domain, expiration, and proxy behavior before choosing an implementation.
7. **No production change in this audit PR.** A separate Codex implementation PR must own minimal changes, new backend/frontend isolation tests, and migration-safe behavior. No DB schema, ranking, or consultation history modifications without explicit justification.

### Required Codex implementation preflight

- Map every anonymous-cookie issue/read/clear/forward call site and auth BFF endpoint.
- Establish exact guest-to-login persistence semantics and account-switch invalidation semantics against existing tests.
- Reproduce the shared-browser risk with two authorized QA identities and one guest identity (test-only data).
- Propose a small contract with expected results for guest→login, A→logout→B, failed login, anonymous reopen, multi-tab and expired-cookie behavior.
- STOP for Mother Ship review if continuity cannot be preserved without a product-contract choice.

### Updated gate status

```text
ANONYMOUS_COOKIE_SHARED_DEVICE_POLICY = B_DECIDED
ANONYMOUS_COOKIE_B_IMPLEMENTATION = NOT_STARTED
ANONYMOUS_COOKIE_B_PRODUCTION_QA = NOT_RUN
PRODUCTION_SECURITY_E2E = OPEN
```
