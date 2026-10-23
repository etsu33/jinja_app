# Anonymous Concierge Identity Boundary — B Policy Design Preflight (2026-10-22)

## Decision and limits

Mother Ship selected B: isolate anonymous consultation access across authenticated identity transitions and shared-device account switching. This is approved policy, NOT permission to silently reassign ownership or delete any existing consultation. Follow-up implementation requires a separate PR and tests.

## Verified code pathways on develop

| Layer | Path | Existing behavior |
| --- | --- | --- |
| Django identity | `backend/temples/services/anonymous_id.py` | Signed `concierge_anon_id` HttpOnly cookie; 90-day max age; backend Secure/SameSite based on DEBUG. No clearing helper in this module. |
| BFF cookie writer | `apps/web/src/lib/server/authCookies.ts` | Web-origin `concierge_anon_id` HttpOnly, Lax, path /; 90-day max age. |
| Concierge BFF | `apps/web/src/app/api/concierge/chat/route.ts` | Proxies chat; passes backend Set-Cookie and may write Web-origin signed anonymous cookie from response body. Audit duplicate writers before editing. |
| Thread BFF | `apps/web/src/app/api/concierge-threads/[id]/route.ts` | Forwards request through auth-aware BFF helper; inspect forwarding details before changing. |
| Django detail | `backend/temples/api/views/concierge.py` | User-owned lookup first, then ownerless thread matching signed anonymous cookie, including when authenticated. |
| Web login | `apps/web/src/app/api/auth/login/route.ts` | Sets access/refresh tokens; does not clear anonymous cookie. |
| Web logout | `apps/web/src/app/api/auth/logout/route.ts` | Clears access/refresh token cookies; does not clear anonymous cookie. |
| Auth client | `apps/web/src/lib/auth/AuthProvider.tsx` | Clears local thread cache on login; clears thread cache and session snapshot on logout. It cannot delete HttpOnly backend cookies. |

## Proposed contract requiring Mother Ship review before implementation

Security invariants that follow from B:

1. A different authenticated account may not access an ownerless consultation simply by inheriting a shared browser's anonymous cookie.
2. A different account must never gain ownership of pre-existing anonymous consultation data via implicit mass claim.
3. Preserve anonymous visitor's legitimate consultation access until a defined identity boundary; do not delete historical threads.
4. At logout/account switch, old anonymous identity access must not be inherited by a new browser user; server-side authorization must enforce it even with leftover/forged cookies.
5. Session and token refresh, simultaneous tabs, and failed login must be tested; failure must not transfer access.

**Handoff point requiring explicit contract:** Guest -> successful login of the *same person*. Two supported directions need product selection:
- explicit, authenticated, single-use claim of chosen guest threads with signed-cookie possession proof and atomic ownership assignment; OR
- retain anonymous consultations separately without automatic claim, defining a secure and understandable revisit flow before invalidating their anonymous identity.

DO NOT choose between them by inference, and do not implement merely a cookie clear at login that strands a guest's legitimate consultation. Distinguish an account-switch boundary from first guest-to-account transition using evidence, not a frontend guess.

## Codex bounded task

1. Trace all writes, reads, forwards and deletes of `concierge_anon_id` across Web/BFF/Django (and Mobile-direct path).
2. Inventory when the same browser changes guest->account A, A->logout->B, account A->B, guest logout, and account refresh.
3. Produce before/after security contract and risk table; identify the handoff choice and STOP for Mother Ship if unresolved.
4. After explicit handoff contract is approved, implement smallest server-enforced boundary in a separate branch/PR. Keep historical data, ranking, DB schema, and authorized anonymous read behavior intact.
5. Tests: guest own thread; other guest; A own; B accessing A; B accessing prior guest thread from same browser; guest->A preservation; A->logout->B; token refresh; failed login; cookie expiry; concurrency/multi-tab; BFF proxy; Web cache 404 behavior.
6. Do not expose cookie values, tokens, consultation content or personal data in evidence, commits or test output.
7. Stop after PR creation. No self-merge, no production security gate closure.

## Gate

```text
B_POLICY = DECIDED
COOKIE_PATH_PRELIMINARY_AUDIT = RECORDED
GUEST_TO_LOGIN_HANDOFF = MOTHER_SHIP_CONTRACT_DECISION_PENDING
B_IMPLEMENTATION = NOT_STARTED
PRODUCTION_SECURITY_E2E = OPEN
```
