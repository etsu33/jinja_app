# Anonymous Consultation Handoff — Security Contract Audit（2026-10-22）

## 1. Status

```text
B_POLICY                        = DECIDED（Mother Ship）
HANDOFF_CONTRACT                = PROPOSED（this record）→ STOP for Mother Ship approval（§12）
RUNTIME / DB / CONFIG CHANGES   = NONE（docs only）
PRODUCTION_SECURITY_E2E         = OPEN
```

- Base: `origin/develop@1b384d9`. Builds on
  `docs/audit/anonymous-concierge-identity-boundary-b-contract-audit-2026-10-22.md`（Stage 1, same branch）.
- **Fact** = verified in source on develop. **Inference** = follows from facts but not executed.
  **Proposal** = design for approval. No cookie value, token, consultation content or personal data is recorded.

---

## 2. Verified facts（investigation items 1–3）

### 2.1 Ownership and storage（item 1）

| # | fact | source |
| --- | --- | --- |
| S1 | `ConciergeThread.user` is a nullable FK（CASCADE）. `anonymous_id` is a nullable `CharField(64)` with an index. `ConciergeMessage` hangs off the thread | `backend/temples/models.py:1320-1361` |
| S2 | Authenticated chat writes `user=U, anonymous_id=None`. Guest chat writes `user=None, anonymous_id=A` | `backend/temples/api_views_concierge.py:888-912` |
| S3 | **Guest chats always create a thread with an id.** The response carries `thread.id` and `_anon_cookie_value` | `api_views_concierge.py:295-334`, `concierge_history.append_chat` |
| S4 | An authenticated chat that sends an anonymous `thread_id` hits `DoesNotExist` and silently **creates a new user thread**. It does not continue or claim the guest thread | `api_views_concierge.py:904-912` |
| S5 | `append_chat` anonymous branch matches `id=T, anonymous_id=A` **without** `user__isnull=True` | `backend/temples/services/concierge_history.py:371-375` |
| S6 | Detail read: own `user` thread first, else `user IS NULL AND anonymous_id=A`, **also for authenticated requests** | `backend/temples/api/views/concierge.py:121-128` |
| S7 | Guest retention: `purge_expired_guest_data` deletes threads with `user IS NULL`, older than 90 days. It is a manual command; no schedule exists | `backend/temples/services/guest_data_retention.py`, `management/commands/purge_expired_guest_data.py` |
| S8 | `CACHES` is `LocMemCache`（per process）. It is not a shared store | `backend/shrine_project/settings.py:376-381` |
| S9 | No `SIMPLE_JWT` block in settings, so simplejwt defaults apply（no refresh rotation configured）. The backend authenticates Web requests by `Authorization: Bearer`, which the BFF builds from the `access_token` cookie | `settings.py:302-305`, `apps/web/src/lib/server/backend.ts:45-64` |

### 2.2 Save-to-account and login redirect flows（item 2）

| # | fact | source |
| --- | --- | --- |
| R1 | The save CTA `save_concierge_thread` requires auth（`actionGuards.ts`）. For a guest it calls `redirectToAuth("login")` | `apps/web/src/lib/auth/actionGuards.ts`, `app/concierge/ConciergeClientFull.tsx:1034-1039, 1682-1702` |
| R2 | `redirectToAuth` uses a **hard-coded `returnTo = "/concierge"`**. The current `?tid=T` is dropped | `ConciergeClientFull.tsx:461-471` |
| R3 | `LoginForm` → `AuthProvider.login` → `POST /api/auth/login`（BFF → `/api/auth/jwt/create/`）→ `window.location.assign(afterLogin)` | `app/login/LoginForm.tsx:44-46`, `app/api/auth/login/route.ts` |
| R4 | `AuthProvider.login` clears `concierge:eventsByThread`. It keeps the sessionStorage anonymous snapshot. That snapshot is written only for **thread-less** results（`isAnonymousLikeUnified`）, so a normal guest result（S3）has no snapshot | `lib/auth/AuthProvider.tsx:190-192`, `ConciergeClientFull.tsx:236-240, 1356-1370` |
| R5 | For a logged-in user, `useConciergeThreadSave` only checks that the thread appears in `GET /api/concierge-threads/`. It writes nothing | `features/concierge/useConciergeThreadSave.ts` |
| R6 | Signup（`/api/auth/register`）does not set auth cookies. Signup → login goes through R3 | `app/api/auth/register/route.ts` |
| R7 | Session-ending paths: `/api/auth/logout`（clears tokens only）, and `DELETE /api/users/me`（on 204 clears tokens only） | `app/api/auth/logout/route.ts`, `app/api/users/me/route.ts:51-63` |
| R8 | `sanitizeNext` allows `/concierge?...`, so a `returnTo` with `tid` survives login | `lib/nav/login.ts` |

**Inference from R2 + R4 + S3:** today a guest who presses save and logs in lands on the `/concierge` entry
screen, not on their result. They reach it again only if they go back in browser history to `?tid=T`, which
works through the S6 fallback. So the "save" promise is not actually kept today. The handoff must carry `tid`
through login.

### 2.3 Database constraints（item 3）

- `concierge_thread_user_or_anonymous_required`: `CHECK (user IS NOT NULL OR anonymous_id IS NOT NULL)`
  （`models.py:1353-1358`）.
- Both `(user=U, anonymous_id=NULL)` and `(user=U, anonymous_id=A)` satisfy it. There is no uniqueness on
  `anonymous_id` and no constraint that forbids both being set.

---

## 3. Threat model

**Assets:** consultation content（messages, title derived from the query, recommendations）; thread ownership;
the anonymous identity（signed `concierge_anon_id`）.

**Principals:** guest G（holder of anonymous identity A）; account U; a later user V on the same browser
profile; a remote attacker M on another device.

**Root limitation（item 10）:** possession of A proves possession of a browser profile's cookie jar at some
point in time. It **does not prove** that the human who logs in is the human who created the consultation.
No design without a stronger factor can fully close this; the contract below narrows the window and
requires explicit consent from the authenticated principal.

| id | threat | today | contract response |
| --- | --- | --- | --- |
| T1 | V on a shared browser reads G's anonymous thread while logged in | **open**（S6） | detail fallback removed for authenticated requests（I1） |
| T2 | V claims G's thread just by logging in on G's browser | n/a（no claim） | claim needs grant + login binding + explicit confirm by U（§5）; window ≤ TTL |
| T3 | Ownership transfer based only on the inherited anonymous cookie | n/a | forbidden（I3）. A grant needs a pre-login user action |
| T4 | M replays a captured grant | n/a | grant is HttpOnly, never in a JSON body, and bound to A and to the bound user; claim also needs U's session |
| T5 | Double claim / race between tabs | n/a | conditional single-row UPDATE; one winner; idempotent second response |
| T6 | Cross-site request forges start / confirm | n/a | BFF same-origin check（`isAllowedOrigin` already used in `users/me`）+ `SameSite=Strict` grant cookie + POST only |
| T7 | A guest appends to a thread after it became user-owned | latent（S5） | claim sets `anonymous_id=NULL`; anonymous append also filters `user__isnull=True` |
| T8 | Status / confirm used as an oracle for thread existence or content | n/a | status reads only the browser's own grant; returns no title or content; all failures → same 404 shape |
| T9 | Signed anon value readable by page JS（F1） | **open** | X1: strip `_anon_cookie_value` from the browser body; the grant is never put in a body |
| T10 | Grant survives logout / account deletion into the next session | n/a | logout and account deletion delete the grant cookie（R7 paths） |

---

## 4. Contract invariants（proposal）

- **I1.** An authenticated request never reads an ownerless thread implicitly. `ConciergeThreadDetailView`
  serves `user IS NULL` threads only to **unauthenticated** requests with a matching valid anon cookie.
- **I2.** A guest keeps full access to their own anonymous threads while unauthenticated with identity A.
- **I3.** Ownership changes only through §5: a pre-login action creates a grant, one login transition binds it,
  and an explicit post-login confirmation consumes it once. There is no batch or automatic migration, and
  no claim from the cookie alone.
- **I4.** Failed login, token refresh, indeterminate auth and any verification failure never create, bind or
  consume a grant, and never widen read access（fail closed）.
- **I5.** No consultation row is deleted by the handoff. A claim is a one-row `UPDATE` of
  `user` / `anonymous_id`.

---

## 5. Handoff authorization contract（items 4, 6）

### 5.1 Grant format

- A stateless value signed by the backend: `django.core.signing.dumps(payload, salt="concierge-handoff-v1")`.
  Verified with `signing.loads(..., salt=..., max_age=TTL)`.
- Payload（no raw identifiers that are secrets）:

  | field | meaning |
  | --- | --- |
  | `v` | `1` |
  | `tid` | thread pk（one consultation） |
  | `aid` | HMAC-SHA256 of anonymous id A, keyed from `SECRET_KEY` with a dedicated salt. A is not stored raw |
  | `nonce` | 128-bit random |
  | `phase` | `"pending"` or `"bound"` |
  | `uid` | user pk; only when `phase="bound"` |

  The issue time comes from `TimestampSigner`. A re-signed bound grant keeps the original `max_age` window:
  the bound payload carries `iat0`, and the backend rejects it when `now - iat0 > TTL`.

- Storage: **Web-origin cookie only**, `concierge_handoff`, `HttpOnly; Secure`（non-DEBUG）;
  `SameSite=Strict; Path=/api; Max-Age=TTL`. The backend returns it to the BFF; the BFF moves it into
  `Set-Cookie` and **removes it from the JSON body**. It is never logged and never in a URL.
- At most one grant per browser profile. A new start overwrites the previous one.

### 5.2 Lifecycle

```text
guest on /concierge?tid=T ─ save ─► START ─► /auth/login?returnTo=/concierge?tid=T&handoff=1
                                              │
                         login success ───────┴─► BIND（in the login BFF response）
                                              │
             /concierge?tid=T（authenticated）─► STATUS ─► prompt ─► CONFIRM（claim）| DECLINE
```

| step | endpoint（new） | preconditions（all required, else fail closed） | effect |
| --- | --- | --- | --- |
| START | BFF `POST /api/concierge-handoff/start {thread_id}` → backend `POST /api/concierge-threads/handoff/start/` | same-origin; **no `access_token` and no `refresh_token` cookie** at the BFF; backend sees an unauthenticated request; valid signed anon cookie A; thread `id=T, user IS NULL, anonymous_id=A` | issues a pending grant; sets the cookie; the client navigates to login with `tid` |
| BIND | inside `POST /api/auth/login` after `jwt/create` succeeds; BFF → backend `POST .../handoff/bind/` with the new Bearer | grant present, `phase=pending`, inside TTL; anon cookie hashes to `aid`; thread still claimable | re-signs the grant as `phase=bound, uid=U`. **Any failure deletes the grant; the login still succeeds** |
| STATUS | BFF `GET /api/concierge-handoff/status` | authenticated; bound grant; `uid == request.user.id`; inside TTL | returns `{pending: true, thread_id}` only. No title, content or timestamps of other data |
| CONFIRM | BFF `POST /api/concierge-handoff/confirm {thread_id}` → backend `POST .../handoff/confirm/` | same-origin; authenticated; bound grant; `uid == request.user.id`; body `thread_id == tid`; inside TTL; anon cookie hashes to `aid` | atomic claim（§5.3）; deletes the grant cookie on every terminal outcome |
| DECLINE | BFF `POST /api/concierge-handoff/decline` | same-origin | deletes the grant cookie. No backend write |

### 5.3 Claim（consumption）

```text
UPDATE concierge_thread
   SET user_id = U, anonymous_id = NULL
 WHERE id = T AND user_id IS NULL AND anonymous_id = A
```

- `rowcount == 1` → `200 {"saved": true, "thread_id": T}`.
- `rowcount == 0` and the thread now has `user_id == U` → `200`（idempotent; a second tab）.
- Otherwise → `404 {"detail": "not found"}`. Same shape as the detail view; no oracle.
- `anonymous_id = NULL` closes T7: the anonymous identity can no longer address the thread after the claim.
  This drops provenance on the row, so the backend writes one structured log line instead: event name,
  outcome and thread pk. No anon id, user id together with content, or title.
- `ConciergeMessage` rows follow the thread FK unchanged. `ConciergeRecommendationLog.user` stays as it is
  （decision D7）.

### 5.4 Binding to one consultation and one login transition（item 4）

- **One consultation:** `tid` is in the signed payload, and confirm requires the body `thread_id` to match.
- **One identity:** `aid` binds the grant to the anonymous identity that created the thread.
- **One login transition:** START refuses while any auth cookie exists, so a grant can exist only in the guest
  state. BIND runs only inside a successful `/api/auth/login` response and stamps `uid`. Rebinding to another
  user is impossible: BIND accepts `phase=pending` only. A login over an existing bound grant for another
  `uid` deletes it.
- **One use:** the conditional UPDATE（the thread stops being claimable）and cookie deletion on every
  terminal outcome.

---

## 6. Expiration and revocation（item 6）

| rule | mechanism |
| --- | --- |
| TTL | **10 minutes** from START（proposal, D3）. Enforced server-side by `max_age` and `iat0`, and client-side by cookie `Max-Age` |
| consumed | confirm success / idempotent success / 404 → cookie deleted; the thread is no longer claimable |
| declined | decline → cookie deleted |
| bind failure | cookie deleted in the login response |
| logout | `/api/auth/logout` deletes `concierge_handoff`（and rotates A under L1） |
| account deletion | `DELETE /api/users/me` on 204 also deletes `concierge_handoff` |
| new start | overwrites the previous grant（one per profile） |
| anon identity change | expiry, rotation or a different cookie → `aid` mismatch → invalid |
| global | `SECRET_KEY` rotation invalidates all grants |
| **not supported** | server-side revocation of one specific unexpired grant. That needs shared state: `LocMemCache` is per-process（S8）, so it would need a DB table, i.e. a migration. Bounded by TTL plus the bind / uid / aid checks |

---

## 7. Scenario evaluation（items 5, 7）

| scenario | result under the contract |
| --- | --- |
| G creates T, saves, logs in as G, confirms | **claimed**; T appears in history; `?tid=T` returns 200 via `user` |
| G creates T, saves, logs in, declines or ignores | T stays anonymous; not readable while logged in（I1）; readable again as guest only if A still exists（L-option） |
| G creates T, **does not save**, logs in | no grant; T not readable while logged in. No implicit claim |
| G saves, leaves; V logs in within TTL on the same browser | grant binds to V; V sees a prompt without content. **If V confirms, V gets T**（residual R1, §11） |
| G saves, leaves; V logs in after TTL | grant expired → nothing |
| A logged in → logout → V logs in | logout deleted any grant; START was impossible while A was logged in → nothing |
| A → B login without logout | START impossible while auth cookies exist; a bound grant for A is deleted at B's login |
| failed login（wrong password, 4xx/5xx from `jwt/create`） | BIND does not run; grant stays pending until TTL; no transfer |
| token refresh during the flow | refresh does not touch the grant; confirm checks `request.user.id == uid` |
| access token expired, refresh valid, at START | BFF sees `refresh_token` → START refused（treated as logged in; fail closed） |
| replay of a captured grant after confirm | thread no longer claimable → 404 |
| replay by M on another device | needs the grant, a matching anon cookie and U's session → fails |
| two tabs confirm at once | one UPDATE wins; the other gets idempotent 200 |
| tab 1 starts T1, tab 2 starts T2 | last write wins; confirm for T1 fails（`tid` mismatch）→ no transfer. Known UX limit |
| logout in another tab between bind and confirm | grant deleted → confirm 404 |
| anon cookie expired or rotated before confirm | `aid` mismatch → 404 |
| signup instead of login | signup sets no tokens（R6）; the subsequent login runs BIND |
| mobile app | uses Bearer straight to the backend and never holds the Web grant cookie → cannot START or CONFIRM（fail closed）. Mobile anonymous handoff is out of scope |

---

## 8. Legitimate access to existing anonymous consultations（item 8）

- **Guest, same browser, unauthenticated:** unchanged. `?tid=T` returns 200 while A is valid（I2）.
- **Guest who wants it in an account:** open T as guest → save → login → confirm. This also works for
  anonymous threads created **before** deployment, as long as A still exists in that browser.
- **Already logged in:** pre-existing anonymous threads are **not** readable（I1）. To claim one, the person
  logs out, opens it as a guest and saves. Under **L1**, logout rotates A, so threads from before that logout
  become unreachable from that browser. They are not deleted, and they age out under S7 if it is ever run.
- **Retention:** a claimed thread leaves the guest retention set（`user IS NOT NULL`）and is kept for the
  account's lifetime. That is a retention change per claimed row（D6）.

---

## 9. Database impact（item 9）

```text
MIGRATION REQUIRED   = NO
```

- The claim uses the existing columns. Both results satisfy `concierge_thread_user_or_anonymous_required`.
- The grant is stateless（signed cookie）. No table, no cache dependency.
- Write volume: one row per explicit confirm. No batch.
- A migration would be needed only for: per-grant server-side revocation, a persistent claim audit table, or
  a `claimed_at` / `claimed_from_anonymous` column. None is proposed.

---

## 10. Affected source files（for the later implementation; not changed here）

**Backend**

- `backend/temples/api/views/concierge.py`: remove the authenticated fallback（I1）.
- `backend/temples/services/concierge_handoff.py`（new）: grant sign / verify, `aid` HMAC, bind, claim.
- `backend/temples/api/views/`（new handoff views）and `backend/temples/api/urls.py`: start / bind / confirm.
- `backend/temples/services/concierge_history.py`: anonymous `append_chat` adds `user__isnull=True`（T7）.
- `backend/temples/services/anonymous_id.py`: X2 `max_age`; L1 rotation helper.
- Tests: `backend/temples/tests/api/test_concierge_thread_detail_authorization.py`; new
  `backend/temples/tests/api/test_concierge_handoff.py`.

**Web**

- New `apps/web/src/app/api/concierge-handoff/{start,status,confirm,decline}/route.ts`.
- `apps/web/src/app/api/auth/login/route.ts`: BIND after success.
- `apps/web/src/app/api/auth/logout/route.ts`, `apps/web/src/app/api/users/me/route.ts`: delete the grant;
  L1 rotation.
- `apps/web/src/lib/server/authCookies.ts`: grant cookie helpers.
- `apps/web/src/app/api/concierge/chat/route.ts`: X1 strip `_anon_cookie_value`.
- `apps/web/src/features/concierge/useConciergeThreadSave.ts`: guest path calls START.
- `apps/web/src/app/concierge/ConciergeClientFull.tsx`: `returnTo` keeps `tid`（R2）; post-login prompt;
  authenticated 404 on an anonymous `tid` shows the prompt only when STATUS matches.
- Tests next to each file.

**Unchanged:** ranking, shrine data, billing, mobile, migrations.

---

## 11. Residual limitations（item 10）

- **R1 — possession is not identity.** Inside the TTL, a different person who logs in on G's browser after G
  pressed save can confirm and receive G's consultation. The prompt shows no content, and confirmation is
  explicit, but the server cannot tell the humans apart. Narrowed by: pre-login action, TTL, single binding,
  logout clearing. Not eliminated.
- **R2 — no per-grant server revocation**（§6）.
- **R3 — one grant per browser profile;** parallel saves in two tabs keep only the last.
- **R4 — the backend-origin copy of `concierge_anon_id`**（set with `SameSite=None` when the browser talks
  to the backend directly）cannot be cleared or rotated by the Web BFF. Whether browsers hold one in practice
  is NOT_VERIFIED.
- **R5 — after L1, guest threads from before a logout** are unreachable from that browser（not deleted）.
- **R6 — a claim drops the anonymous provenance on the row;** only the log line remains.

---

## 12. Test matrix（for the implementation PR）

### Backend

| case | expected |
| --- | --- |
| guest reads own T | 200 |
| authenticated U with cookie A reads anonymous T（I1） | 404, no content |
| START authenticated / bad cookie / foreign T / user-owned T | 404, no grant |
| START valid | grant issued; not in the response body the browser receives |
| BIND with pending grant, matching A | bound to U |
| BIND with an expired, tampered or already-bound grant, or `aid` mismatch | grant rejected |
| CONFIRM happy path | `user=U, anonymous_id=NULL`; messages intact |
| CONFIRM with `uid != user`, `tid` mismatch, expired, `aid` mismatch, unauthenticated | 404; row unchanged |
| CONFIRM twice / concurrently（`select_for_update` or two transactions） | one write; second idempotent 200 |
| replay after confirm | 404 |
| anonymous append to a claimed T | does not append to the user thread（T7） |
| retention after a claim | claimed T not in `expired_anonymous_threads` |
| no row deleted in any case | count unchanged |

### BFF（vitest）

| case | expected |
| --- | --- |
| START with `access_token` or `refresh_token` present | refused; backend not called |
| START sets `concierge_handoff` HttpOnly, Strict, Max-Age; body has no grant | yes |
| cross-origin START / CONFIRM | 403 |
| login success with a grant → BIND called with the new Bearer; failure → grant deleted, login still 200 | yes |
| login failure → no BIND; grant unchanged | yes |
| logout and account deletion delete the grant（and rotate A under L1） | yes |
| refresh in the chat route / `bffFetch` leaves the grant untouched | yes |
| X1: chat body has no `_anon_cookie_value`; cookie still set | yes |

### Web（vitest）

| case | expected |
| --- | --- |
| guest save → START → navigates to `/auth/login?returnTo=/concierge?tid=T…` | `tid` kept |
| after login on `?tid=T` with STATUS matching → prompt without title or content | yes |
| confirm → saved; history link shown | yes |
| decline / STATUS mismatch / 404 → no prior content shown（PR #3309 tests stay green） | yes |
| A → logout → B on `?tid=T` | no content, no prompt |

### Production QA（after deploy; QA accounts and test data only）

Guest → save → login → confirm; guest → save → wrong password; A → logout → B; and a fresh Incognito window.
No cookie values or content in evidence.

---

## 13. Decisions requiring Mother Ship approval

| id | decision | recommendation |
| --- | --- | --- |
| D1 | Adopt the §5 explicit handoff（H1）, with I1 removing the authenticated fallback | **adopt** |
| D2 | Consumption mode: **C2** pre-login save + post-login confirm, or **C1** claim automatically at BIND（no prompt） | **C2**（C1 makes R1 silent） |
| D3 | Grant TTL | **10 min** |
| D4 | Claim sets `anonymous_id = NULL`（loses provenance） vs keeps it（needs the T7 filter everywhere） | **NULL** + T7 filter |
| D5 | Logout: **L1** rotate A, or **L2** keep A | **L1** |
| D6 | Accept the retention change: a claimed thread is kept for the account lifetime | accept（user-initiated） |
| D7 | Leave `ConciergeRecommendationLog.user` unchanged at claim | leave |
| D8 | X1 strip `_anon_cookie_value`; X2 server `max_age=90d` on the anon cookie | X1 yes; X2 after confirmation |
| D9 | Accept residuals R1–R6 | required for D1 |
| D10 | Mobile anonymous handoff out of scope | out of scope |

---

## 14. Not done

```text
runtime / backend / BFF / frontend / mobile code   UNCHANGED
cookies / tokens / DB / migrations / config        UNCHANGED
consultation records                               UNCHANGED（none deleted or reassigned）
ranking / shrine data / billing                    UNCHANGED
PRODUCTION_SECURITY_E2E                            OPEN
```
