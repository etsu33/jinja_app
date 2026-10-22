# Anonymous Concierge Identity Boundary B — Stage 1 Contract Audit（2026-10-22）

## 1. Status

```text
B_POLICY                         = DECIDED（Mother Ship; PR #3310 record）
STAGE_1_CONTRACT_AUDIT           = COMPLETE（this record）
GUEST_TO_LOGIN_HANDOFF           = UNRESOLVED → STOP（Mother Ship decision required, §6）
STAGE_2_IMPLEMENTATION           = NOT STARTED（no runtime change in this branch）
PRODUCTION_SECURITY_E2E          = OPEN
```

- Base: `origin/develop@1b384d9`（PR #3309 merge）
- Inputs read: `docs/audit/anonymous-concierge-identity-boundary-b-preflight-2026-10-22.md` and
  `docs/audit/production-concierge-isolation-e2e-2026-10-22.md`. Both are in **open PR #3310**
  （branch `audit/production-concierge-isolation-e2e-20261022`, not on develop）.
- Everything below was verified against code on `develop`. No cookie value, token, consultation content
  or personal data is recorded.

---

## 2. `concierge_anon_id` lifecycle（verified）

| step | location | behavior |
| --- | --- | --- |
| issue | `backend/temples/services/plan_service.py::resolve_plan_context` → `anonymous_id.get_or_create_anonymous_id` | **unauthenticated** requests only. Reuses a valid cookie; otherwise a new `uuid4`. Authenticated requests get `anon_id = None` |
| sign | `anonymous_id._sign_anon_id` | `django.core.signing.dumps(raw, salt=...)`（timestamped） |
| verify | `anonymous_id._unsign_anon_id` | `signing.loads(..., max_age=None)` → **no server-side expiry**; a valid value is accepted indefinitely |
| set（backend origin） | `attach_anonymous_cookie`（chat: `api_views_concierge.py`; weekly compass: `api_views_compass_weekly.py`） | HttpOnly, max-age 90 days, path `/`, `SameSite=None; Secure` when not DEBUG |
| value in JSON body | `_build_chat_response` → `body["_anon_cookie_value"]`（anonymous plan） | the **signed value** is returned in the response body |
| set（Web origin） | `apps/web/src/app/api/concierge/chat/route.ts::attachAnonCookieFromBody` → `lib/server/authCookies.ts::setAnonymousConciergeCookie` | HttpOnly, `Lax`, path `/`, 90 days. The backend `Set-Cookie` is also forwarded（two writers, same value） |
| forward | `lib/server/backend.ts::djFetch`, `lib/server/bffFetch.ts::bffFetchWithAuthFromReq` | forward the browser's **whole Web-origin `Cookie` header**（anon cookie + tokens）to Django |
| read（ownership） | `backend/temples/api/views/concierge.py::ConciergeThreadDetailView` | own thread by `user`; **else, also for authenticated requests**, an ownerless thread with matching `anonymous_id` |
| write（ownership） | `concierge_history.append_chat` | authenticated → `user=…, anonymous_id=None`; guest → `user=None, anonymous_id=<anon>` |
| list | `ConciergeThreadListView`（`IsAuthenticated`） | `filter(user=request.user)` only. Anonymous threads never appear |
| clear / rotate | — | **none anywhere.** `/api/auth/login` and `/api/auth/logout` touch only `access_token` / `refresh_token`. `AuthProvider` clears only localStorage / sessionStorage（PR #3309）and cannot delete an HttpOnly cookie |
| claim / migrate | — | **none.** No code assigns an anonymous thread to a user |
| mobile | `apps/mobile/lib/http.ts`, `lib/consultationHistory.ts` | Bearer token straight to the backend. Whether the native cookie store keeps the backend anon cookie is **NOT_VERIFIED** from source |

Additional findings that do not depend on the handoff decision:

- **F1 — the signed identity reaches browser JavaScript.** The BFF returns the backend body unchanged,
  including `_anon_cookie_value`（asserted by `app/api/concierge/chat/__tests__/route.test.ts`）. HttpOnly
  is therefore not a protection for the anonymous identity: any script on the page can read it.
- **F2 — no server-side expiry.** `max_age=None`, so the 90-day lifetime is enforced only by the
  browser.
- **F3 — the anonymous identity survives every auth transition** in the same browser profile, across all
  tabs, because nothing rotates or clears it.

Other anonymous-owned data keyed by the same identity（weekly compass snapshots, the anonymous chat
quota）is outside consultation ownership. A change to the cookie lifecycle would affect it too.

---

## 3. Scenario matrix — current behavior（same browser profile）

| scenario | anonymous consultation T（made as guest, `user IS NULL`） | account-owned threads |
| --- | --- | --- |
| guest reopens own `?tid=T` | 200（cookie match） | n/a |
| other guest, other browser / Incognito | 404 | 404 |
| guest → login as A（same person） | **200 for A**（fallback）; T is **not** in A's history | A's own: 200 |
| A → logout → guest | **200**（cookie unchanged） | A's: 404 |
| A → logout → login as B（another person） | **200 for B**（← B-policy violation） | A's: 404 for B |
| A → B without logout（login over a session） | **200 for B**（← violation） | 404 |
| failed login | unchanged（no transfer; cookie untouched） | unchanged |
| token refresh（`bffFetch` / chat route） | unchanged（refresh touches only tokens） | unchanged |
| multiple tabs | one cookie for the whole profile; a transition in one tab applies to all | — |
| cookie expired in the browser（> 90 days） | 404（no cookie sent） | — |
| leftover or captured signed value replayed | **200**（no server expiry; F2） | — |

The violation is the B-row only: an authenticated user inherits a previous browser user's anonymous
consultations. Account-owned threads are already isolated（PR #3309 audit and tests）.

---

## 4. Why the handoff decides the implementation

The B fix has two parts:

1. the backend must stop serving ownerless threads to authenticated requests based on the cookie; and/or
2. the identity must rotate at the login / logout boundary.

Either part also removes the **only** path through which a guest who logs in can still see their
own anonymous result:

- The history list is user-only.
- No claim exists. PR #3307 documents "a thread created anonymously is not moved to the account after
  login".
- The save CTA (#3307) redirects a guest to login. After login, the guest's own result is visible today
  only through the anonymous fallback that B removes.

Therefore:

```text
Guest consultation preservation across login REQUIRES an ownership decision.
"Clear / rotate the cookie at login" alone strands the guest's consultation.
"Keep the fallback for authenticated requests" alone leaves the B violation in place.
```

The backend cannot tell the same person（guest → login）from a different person（A logs out, B logs in on
a shared browser）from the cookie alone. Both look like "authenticated request + leftover anonymous
cookie". Any distinction has to come from an explicit, user-driven step, not from inference.

---

## 5. Proposed contract invariants（from B; independent of the handoff option）

1. An authenticated request never reads an ownerless thread **implicitly**（no cookie fallback for
   authenticated principals）. The server enforces this; frontend clearing is not relied on.
2. A guest can always reopen their own anonymous threads while unauthenticated in the same browser
   identity.
3. Logout ends the previous user's access to any anonymous identity created **before** that logout. How
   this is done（rotation vs retention）follows the option chosen in §6.
4. Failed login, token refresh and indeterminate auth never transfer or widen access（fail closed）.
5. No thread is deleted. No thread changes owner except through an explicit, authenticated, atomic,
   single-use step（if one is chosen）.

---

## 6. Decision required from Mother Ship（STOP）

### H — guest → login handoff（choose one）

| option | behavior | pros | cons / cost |
| --- | --- | --- | --- |
| **H1. Explicit claim（recommended）** | After login, the user explicitly chooses "save this consultation to my account" for an anonymous thread. The server checks: authenticated; a valid signed cookie whose `anonymous_id` matches; the thread is ownerless; the claim is single-use. It then sets `user=…` atomically. The anonymous fallback is removed for authenticated requests | matches the existing save CTA intent（#3307）; ownership becomes explicit and auditable; B satisfied | new endpoint + UI step + tests; owner change is a one-way data write（per explicit user action） |
| **H2. Separate retention, no claim** | Anonymous threads stay anonymous. After login they are not visible（fallback removed）. Revisiting needs logging out to the same guest identity | smallest backend change; no ownership writes | guest who logs in to save loses sight of the result; contradicts the save CTA's purpose; needs a clear UI message |
| **H3. Time-bounded handoff** | The fallback for authenticated requests stays only for anonymous threads created in this browser **within N minutes before** this login, then stops | no UI step | does not distinguish the same person from a different person within N minutes; weaker B; needs a timestamp contract |

### L — logout / account switch（choose one）

| option | behavior | trade-off |
| --- | --- | --- |
| **L1. Rotate at logout（recommended with H1）** | Logout response sets a fresh signed anon cookie in both origins | prior guest threads become unreachable from that browser（not deleted）. Irreversible for that browser |
| **L2. Keep cookie; rely on invariant 1** | With the fallback removed, B can no longer read the guest threads while authenticated. After logout, the next guest still can | simpler; a later guest on a shared browser still sees the earlier guest's threads |

### Independent hardening（approval each; small）

| id | change | effect |
| --- | --- | --- |
| X1 | strip `_anon_cookie_value` from the browser-facing BFF response | closes F1; the cookie is still set server-side |
| X2 | `signing.loads(..., max_age=90 days)` | closes F2. Cookies older than 90 days stop working, which matches the browser max-age |

Recommendation: **H1 + L1 + X1**. X2 only after confirming no flow depends on older cookies. H1 adds an
explicit ownership write, so it needs Mother Ship approval as a data-ownership contract. No DB migration
is needed: the `user` / `anonymous_id` columns exist, and the check constraint already allows
`user IS NOT NULL`.

---

## 7. Stage 3 test plan（after the decision）

- **Backend:**
  - guest reads own thread;
  - other guest reads it → 404;
  - A reads own thread;
  - B reads A's thread → 404;
  - B with a leftover guest cookie reads the guest's thread → 404;
  - a forged cookie → 404;
  - an expired signature（X2）→ 404;
  - under H1: claim succeeds only with a matching cookie; claiming another identity's thread → 404;
    double claim → idempotent no-op; concurrent claims → one winner.
- **BFF:**
  - login / logout cookie transitions（L1 rotation in the Web origin）;
  - refresh does not change the anon identity;
  - failed login leaves everything unchanged;
  - X1: no `_anon_cookie_value` in the browser body.
- **Web:**
  - guest → login continuity per H;
  - A → logout → B on `?tid=` → no content（API 404）;
  - multi-tab: a logout in one tab is reflected server-side in another;
  - the PR #3309 cache-isolation tests stay green.
- **Production QA:** the PR #3310 steps plus guest → login, A → logout → B and a fresh Incognito window,
  using QA accounts and test data only.

---

## 8. Not done

```text
runtime / backend / BFF / frontend code   UNCHANGED
cookies / tokens / DB / migrations         UNCHANGED
consultation records                       UNCHANGED（none deleted or reassigned）
ranking / shrine data / billing            UNCHANGED
PRODUCTION_SECURITY_E2E                    OPEN
```
