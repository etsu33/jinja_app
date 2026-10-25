# Anonymous Consultation Logout and Recovery Contract — P1 / P2（2026-10-23）

## 1. Status

```text
SCOPE                           = design / audit only（documentation）
P1 LOGOUT IDENTITY BOUNDARY     = options A / B / C compared — NOT SELECTED（Mother Ship, G4）
P2 RECOVERY CONTRACT            = options R1 / R2 / R3 compared — NOT SELECTED（Mother Ship, G4）
G1（handoff grant schema）       = CONDITIONALLY APPROVED; not reopened by this record
G2 / G3 / G4 / G5               = NOT APPROVED for implementation
runtime / BFF / cookies / auth  = UNCHANGED
models / migrations / DB data   = UNCHANGED
PRODUCTION_SECURITY_E2E         = OPEN
FINAL STATUS                    = STOP — awaiting Mother Ship P1 / P2 decision
```

- Base: `origin/develop@38eca3f`（includes #3313, #3315, #3316）.
- Builds on:
  - `anonymous-concierge-identity-boundary-b-contract-audit-2026-10-22.md`（Stage 1: L1 / L2, X1, X2）;
  - `anonymous-consultation-handoff-threat-model-v2-2026-10-22.md`（proof classes P1–P5, renamed here to
    **K1–K5** so they do not collide with policy ids P1 / P2）;
  - `anonymous-handoff-code-db-lifecycle-audit-2026-10-22.md`（approach A）;
  - `concierge-handoff-grant-schema-proposal.md`（`ConciergeHandoffGrant`, §1.1 gates, §13.1 G4）.
- Approved requirements（G0）this record must keep: approach A; 30-minute code; single use; reissue revokes
  previous open grants; no automatic ownership transfer; no deletion of anonymous consultations by the handoff
  flow; shared-browser cross-account privacy.
- Labels: **Fact** = verified in source on this base, or by a local run stated inline. **Inference** =
  reasoned, not executed. **Proposal** = for Mother Ship, not a decision. **NOT_VERIFIED** = depends on a
  deployment setting or a client runtime that this record could not observe.
- No cookie value, code, consultation content or personal data is recorded here.

Option ids used below:

| id | meaning |
| --- | --- |
| **P1-A** | rotate the anonymous id at logout |
| **P1-B** | rotate at logout **and** provide an independent recovery mechanism（= P1-A + P2-R2 or P2-R3） |
| **P1-C** | keep the anonymous id at logout; prevent cross-account exposure by server rules |
| **P2-R1** | no recovery after anonymous identity loss |
| **P2-R2** | a separately held recovery secret |
| **P2-R3** | a verified external recovery factor established before identity loss |

---

## 2. Verified facts

| # | fact | source |
| --- | --- | --- |
| L-1 | The anonymous identity A is a UUID4, signed with `signing.dumps(salt="temples.concierge.anonymous_id")` and stored in the `concierge_anon_id` cookie. There is no server-side table of anonymous identities | `backend/temples/services/anonymous_id.py:15-61` |
| L-2 | The signed value carries a timestamp, but the backend reads it with `max_age=None`, so **a signed A never expires server-side**. The 90-day lifetime exists only as the cookie's `Max-Age` in the browser | `anonymous_id.py:26`; local run, Django 5.2.16: `loads(…, max_age=0)` raises `SignatureExpired` |
| L-3 | The backend sets the cookie on its own origin with `HttpOnly; Max-Age=90d; Path=/; SameSite=None; Secure`（when not `DEBUG`）. Chat and weekly compass responses re-sign and re-set it, so the timestamp refreshes on use | `anonymous_id.py:70-81`; `api_views_concierge.py:652, 669, 1014, 1026`; `api_views_compass_weekly.py:154` |
| L-4 | The chat response body carries the signed value as `_anon_cookie_value`. The BFF copies it into a **Web-origin** cookie of the same name: `HttpOnly; SameSite=Lax; Path=/; Max-Age=90d; Secure` in production | `apps/web/src/app/api/concierge/chat/route.ts:34-48`; `lib/server/authCookies.ts:90-101` |
| L-5 | So two copies can exist: the Web-origin copy（BFF）and a backend-origin copy, which the browser holds only if it ever calls the backend origin directly. Whether production Web does that depends on `NEXT_PUBLIC_API_BASE` | `lib/api.ts:2`, `lib/api/http.ts:60`; env value **NOT_VERIFIED** |
| L-6 | BFF `POST /api/auth/logout` clears `access_token` and `refresh_token` only. It has **no origin check**, unlike `DELETE /api/users/me` | `apps/web/src/app/api/auth/logout/route.ts:6-12`; `app/api/users/me/route.ts`（`isAllowedOrigin`） |
| L-7 | BFF `POST /api/auth/login` sets the two token cookies only; it does not touch `concierge_anon_id` | `app/api/auth/login/route.ts:112-118` |
| L-8 | `AuthProvider.logout` clears the concierge thread cache and the anonymous `sessionStorage` snapshot **of the current tab**. `login` clears the thread cache and keeps the snapshot | `apps/web/src/lib/auth/AuthProvider.tsx:180-213` |
| L-9 | `DELETE /api/users/me` clears the two token cookies on 204 only; it does not touch `concierge_anon_id` | `app/api/users/me/route.ts:39-63` |
| L-10 | The thread detail view is `AllowAny`. For an authenticated request it first looks up the user's thread, then **falls back** to `user IS NULL AND anonymous_id = A` from the cookie | `backend/temples/api/views/concierge.py:88-128` |
| L-11 | The thread list view is `IsAuthenticated`: a guest has no list, only `?tid=` detail reads. Thread ids are sequential `BigAutoField` values | `concierge.py:58-59`; `DEFAULT_AUTO_FIELD` |
| L-12 | The anonymous `append_chat` branch matches `(id, anonymous_id)` without `user__isnull=True` | `backend/temples/services/concierge_history.py:365-375` |
| L-13 | Anonymous quotas（`FeatureUsage`, scope `anonymous`）are keyed on A | `backend/temples/services/quota_service.py:30-54`; `plan_service.py:41-50` |
| L-14 | The handoff grant（proposal, G1 conditional）stores `anon_binding = HMAC(A)` and needs the **current** cookie A at claim. Expired or binding-mismatched grants are not revoked; they become unusable（§5.6 of the schema proposal） | `concierge-handoff-grant-schema-proposal.md` §3, §5.6, §6 |
| L-15 | Guest retention deletes `user IS NULL` threads older than 90 days; it is a manual command, not scheduled | `backend/temples/services/guest_data_retention.py:51-67` |
| L-16 | No email backend, no `send_mail` use, no WebAuthn / FIDO dependency and no guest contact field exist in the backend | `backend/shrine_project/settings.py`; `backend/requirements.txt`; repository grep |
| L-17 | **Mobile:** the concierge chat call uses the unauthenticated `post()`, which sends no `Authorization` header, even for a logged-in user | `apps/mobile/app/concierge/index.tsx:447`; `apps/mobile/lib/http.ts:144-151` |
| L-18 | **Mobile:** tokens live in `AsyncStorage`. `clearTokens()` exists but has **no caller** outside tests, so the app has no logout path | `apps/mobile/lib/authTokens.ts:27-31`; repository grep |
| L-19 | **Mobile:** history uses `getAuth("/concierge-threads/")`（user threads only）. Whether the native HTTP stack keeps the backend anon cookie between requests is **NOT_VERIFIED** | `apps/mobile/lib/consultationHistory.ts:61`; Stage 1 audit |

**Inference from L-17 to L-19:** a logged-in mobile user's consultations are stored as anonymous threads
（cookie-dependent）and do not appear in that user's history. This is a pre-existing gap, outside P1 / P2,
recorded as finding **MF-1**（§12）. It does not change any Web conclusion below.

---

## 3. Cookie rotation is not server-side revocation

| | **cookie rotation** | **server-side revocation** |
| --- | --- | --- |
| what changes | the browser that receives the response gets a new A'（`Set-Cookie`） | the server stops accepting A, or stops mapping A to any thread |
| who is affected | only that browser profile, only on the origin that set it（L-5） | every holder of A: the browser, a copied cookie jar, a backup, a synced profile |
| copied cookie | **still valid**. A signed A verifies forever（L-2）; threads stay `anonymous_id = A` | rejected, or maps to nothing |
| needs state | no | yes: a revocation record, or rewriting `ConciergeThread.anonymous_id` |
| today | not implemented（L-6, L-7, L-9） | impossible without new state（L-1） |

Ways to get server-side effect, with their cost（none is proposed as a decision）:

| id | mechanism | effect on copies | data change | migration |
| --- | --- | --- | --- | --- |
| SR-1 | **bound signature age**: read with `max_age=90d`（X2） | idle copies older than 90 days fail. An attacker who **uses** the copy gets it re-signed（L-3）, so active copies keep living | none | **no** |
| SR-2 | **revocation list**: table of revoked HMAC(A), checked on every anonymous request | all copies of A rejected | new rows only | **yes**（new table） |
| SR-3 | **re-key at logout**: `UPDATE thread SET anonymous_id = A' WHERE user IS NULL AND anonymous_id = A`, then set cookie A' | copies of A see nothing; **the browser keeps access**（so the next person on the browser does too） | rewrites ownership keys of existing consultations | no |
| SR-4 | **orphan at logout**: re-key to a random value nobody holds | nobody can reach the threads; retention later deletes them | rewrites ownership keys; makes the data unreachable | no |
| SR-5 | **revoke open grants at logout**: close open handoff grants of threads with `anonymous_id = A` | a copied cookie **plus** a copied code can no longer claim | grant rows only | changes `0122`: needs a new `revoked_reason` value → **reopens G1** |

- **Inference:** SR-3 and SR-4 change consultation ownership keys outside the handoff. They do not delete
  rows, but they modify consultation data and make the outcome depend on a logout click. They are recorded for
  completeness and are **not** recommended（§8）.
- **Inference:** the realistic holder of a copied cookie jar is malware, a malicious extension or someone who
  copied the browser profile. Such a holder can usually read the screen too. Server-side revocation narrows
  but does not close that case.

---

## 4. Actors and trust boundaries

```text
 G  = guest who created thread T on browser profile W, holding A
 V  = a different person who later uses W（shared browser / shared device）
 M  = remote holder of copied material（cookie jar, code, recovery secret）
 X, Y = accounts

 ┌──────────── anonymous domain（weak）────────────┐        ┌──────── account domain ────────┐
 │ proof K1: bearer cookie A（browser-scoped）      │ claim  │ proof K3: password → JWT        │
 │ proof K4: 30-min code shown once（human-held）   │ ─────► │ proves the ACCOUNT, not T       │
 │ proof K6: recovery secret / factor（P2-R2/R3）    │（K1+K4 │                                 │
 └─────────────────────────────────────────────────┘ +K3）   └─────────────────────────────────┘
```

Rules this record keeps（from G0 and the threat model v2）:

- **B-1** An authenticated session never reads or writes an ownerless thread by cookie alone（removes L-10
  fallback; adds `user__isnull=True` to L-12）. Shared prerequisite for every option.
- **B-2** A transfer needs K1 + K4 + K3 and an explicit submission（approach A claim）. K3 alone, or K1 alone,
  is never enough. **A logged-in account is not proof of an earlier anonymous consultation.**
- **B-3** A recovery proof（K6）may restore the creator's **anonymous** access; it never substitutes for the
  claim, and never transfers ownership by itself（no automatic transfer）.
- **B-4** No operation in P1 or P2 deletes a consultation. Retention（L-15）stays the only deletion path for
  guest threads.

---

## 5. P1 — logout identity boundary

### 5.1 What each option does at logout（and at account deletion）

| | P1-A rotate | P1-B rotate + recovery | P1-C keep A |
| --- | --- | --- | --- |
| logout response | Web-origin `concierge_anon_id` deleted（`Max-Age=0`）; the next guest request gets a fresh A' from the backend（`get_or_create_anonymous_id`, `plan_service.py:41-42`） | same as P1-A | cookie untouched |
| account deletion（204） | same rotation | same | untouched |
| login | **no rotation**（rotating at login would break the claim, which needs A after login, L-14） | same | same |
| server-side revocation of A | none（§3）; SR-1 optional | none; recovery state added（§6） | none |
| prerequisites | B-1, X1 | B-1, X1 | B-1, X1, **plus a guard for guest→guest exposure**（§5.2 row 1） |

### 5.2 Assessment

| dimension | P1-A rotate | P1-B rotate + recovery | P1-C keep A |
| --- | --- | --- | --- |
| **shared browser / device**: X logs out, V continues as guest | V gets A'. G's / X's earlier guest threads are not readable or claimable by V | as P1-A | **V holds A.** V can open earlier guest threads by `?tid=` from history or by walking sequential ids（L-11）, append to them（L-12 even after B-1, since V is a guest）, and **issue a code and claim them into V's account**. This violates shared-browser privacy unless an extra proof is added to guest reads（none exists） |
| guest → guest, **no login at all** | not addressed: no logout boundary exists | not addressed | not addressed |
| **account switching**: X → logout → Y | Y starts as a fresh guest identity; nothing of X's guest period is reachable | as P1-A | Y（a guest after logout）holds A: same exposure as row 1 |
| X → Y without logout（login over a session） | no rotation（login does not rotate）. B-1 keeps Y from reading guest threads while authenticated. Y cannot claim without the code | same | same |
| **browser cookie reuse**（old cookie copied elsewhere） | rotation does **not** revoke it（§3）. The copy keeps reading G's guest threads and can be used with a copied code | same, plus a recovery secret could restore access after rotation | the copy and the browser keep the same access |
| **existing anonymous consultation access** | lost from W after logout（not deleted; reachable by copies; purged by retention） | lost from W, recoverable with K6 | kept on W for anyone who uses W |
| **previously issued handoff grants** | binding to A no longer matches W's cookie → unusable from W; rows stay open until expiry（L-14）. A copy of A + the code still works until expiry（SR-5 would close it） | as P1-A; recovery that re-binds a thread to A'（§6.2）lets the guest reissue | stay valid on W until expiry: V on W with the code could claim; without the code V can reissue（row 1） |
| **logout and account deletion** | both rotate. Deletion removes owned threads（CASCADE）; guest threads of the old A are untouched | same | neither changes anything for guest threads |
| **cross-origin cookies**（L-5） | the BFF can rotate only the Web-origin copy. A backend-origin copy, if it exists, keeps A. If production Web reads only through the BFF, that copy is inert; **NOT_VERIFIED** | same | n/a |
| forced logout（L-6: no origin check） | a cross-site POST that reaches logout would also rotate A, so a third party could make G lose guest access. Whether browsers apply `Set-Cookie` on that cross-site response is **NOT_VERIFIED**; adding `isAllowedOrigin` to logout closes it | same | only tokens cleared（today's behaviour） |
| anonymous quota（L-13） | rotation gives a fresh anonymous quota. Clearing cookies already does that, so this adds no new bypass（inference） | same | unchanged |
| multiple tabs | logout in tab 1 rotates the cookie for all tabs; tab 2 still shows its own `sessionStorage` snapshot and in-memory state until reload（L-8 clears only tab 1） | same | same, plus tab 2 keeps working on A |
| **Web vs mobile** | Web: BFF logout can rotate. Mobile: no logout exists（L-18）and no BFF; rotation would need a backend endpoint and a native cookie store whose behaviour is NOT_VERIFIED（L-19） | same; recovery UX on mobile §6.4 | Web: nothing to build. Mobile: nothing to build |

**Inference:** only P1-A and P1-B satisfy the approved shared-browser privacy requirement at the logout
boundary. P1-C satisfies it only if guest reads gain a proof that V would not have, and no such proof exists in
the anonymous domain（K1 is all a guest presents）.

**Blind spot shared by all three:** two guests on one browser with no login in between（row 2）. P1 cannot fix
it because there is no logout. Only an explicit "end guest session" control, a shorter cookie lifetime, or user
education reaches it（decision D-8）.

---

## 6. P2 — recovery after anonymous identity loss

"Identity loss" means W no longer presents A: rotation at logout（P1-A / B）, cookie expiry or clearing, another
browser or device, or a private window.

### 6.1 Comparison

| | **P2-R1 no recovery** | **P2-R2 recovery secret** | **P2-R3 verified external factor** |
| --- | --- | --- | --- |
| proof for recovery | none — recovery is impossible | possession of a secret shown once to G while G still held A, and kept by G outside the browser（K6） | control of a factor verified while G held A: email OTP / magic link, or a passkey |
| can the 30-min code be reused? | — | **not as the recovery proof**: the code is bound to A and expires in 30 min. The claim step itself is reused unchanged（§6.2） | same as R2 |
| does recovery reveal contents? | — | **yes**: after recovery the presenter can read the thread as a guest. The secret is therefore read access plus a path to the claim | yes, to whoever controls the factor |
| new anonymous identity or transfer? | — | **re-bind**: the thread's `anonymous_id` moves from A to the presenter's current guest identity A'. No transfer; the 30-min handoff then applies（code + A' + login）. Direct transfer is an alternative that skips the code and is **not** recommended | same re-bind |
| generation | — | selector 80 bit + verifier 256 bit from `secrets`, as M4; shown once; never in a cookie, storage, URL or log | email: address entered by G, OTP 6–8 digits or a 256-bit link token; passkey: WebAuthn registration |
| storage | — | new table: selector, SHA-256 of the verifier, thread FK, timestamps, attempts. No plaintext | email address（PII）or a WebAuthn public key, plus OTP / challenge state |
| lifetime | — | until the thread is claimed, revoked, or purged by retention; optionally a hard cap（D-5） | factor: until purge; OTP: minutes |
| revocation | — | on claim of the thread; on reissue of a new secret; explicit guest cancel; lockout after N failures; thread deletion（CASCADE） | factor removal by G; lockout; thread deletion |
| replay protection | — | single use: conditional UPDATE that sets `consumed_at`, thread row locked first（same order as the grant, §7 of the schema proposal） | OTP single use + expiry; WebAuthn challenge single use |
| every proof lost | thread stays anonymous, unreachable, **not deleted**; retention purges it | same as R1 | same as R1 |
| database / migration | none | **new table and migration（`0123+`）**; `0122` unchanged if re-bind is used（§6.2）; G1 review for the new table | new tables, email delivery or WebAuthn library, privacy policy change |
| mobile UX | nothing | the user must keep a ~40-char secret: copy to notes / password manager / share sheet. iOS / Android tab discarding and app switching make "shown once" fragile | email OTP is familiar; passkey needs associated-domain setup for native apps |
| new attack surface | none | a **portable** bearer secret valid off-device for a long time. A screenshot or synced notes leak = read access from anywhere | email account takeover = consultation access; guest email is new PII; OTP guessing; enumeration of addresses |
| infrastructure today | — | none needed beyond the DB | **none exists**（L-16） |

### 6.2 Proposed shape of P2-R2 if Mother Ship chooses it（proposal, not a decision）

```text
RECOVERY_SECRET_ISSUE   guest with A, thread T (user IS NULL, anonymous_id = A), explicit action
                        → returns secret once; stores selector + sha256(verifier)
RECOVERY_REBIND         unauthenticated guest with current A' (any browser) submits the secret
                        lock T FOR UPDATE → lock secret row
                        verify selector / verifier（constant time）; T.user IS NULL; secret open
                        UPDATE T SET anonymous_id = A' WHERE id = T AND user IS NULL
                        UPDATE secret SET consumed_at = now()
                        → 200; the guest now sees T under A'
HANDOFF（unchanged）     issue the 30-min code under A' → login → claim（approach A, B-2）
```

- Authenticated sessions cannot re-bind（the same rule as issuance: a cookie-holding logged-in session must
  not open a second path）.
- Re-binding leaves any open grant bound to the old A unusable. The next issuance on T revokes it as
  `reissued` through the existing partial unique index. **No new `revoked_reason` and no `0122` change.**
- Per-thread secrets keep the blast radius to one consultation. A per-identity secret（all threads of A）is
  simpler for the user but leaks everything at once（D-4）.

---

## 7. Combined options and G1 / `0122` impact

| combination | privacy at logout | recovery | reopens G1? | changes `0122`? | new migration |
| --- | --- | --- | --- | --- | --- |
| P1-A + P2-R1 | ✓ | none | no | no | no |
| P1-A + SR-5（revoke grants at logout） | ✓, also closes copy + code | none | **yes**（new reason value） | **yes** | in `0122` |
| P1-B = P1-A + P2-R2（re-bind） | ✓ | secret | **new G1 item for the new table**; the grant schema unchanged | no | yes（`0123+`） |
| P1-B = P1-A + P2-R2（direct transfer） | ✓ | secret | yes; a second transfer path needs its own contract | possibly | yes |
| P1-B = P1-A + P2-R3 | ✓ | email / passkey | new G1 items; privacy policy | no | yes |
| P1-C + P2-R1 | **✗**（§5.2 row 1） | n/a（A survives logout） | no | no | no |
| any + SR-1（signature max-age） | — | — | no | no | no |
| any + SR-2（revocation list） | — | — | new G1 item | no | yes |

---

## 8. Recommended security contract（for evaluation; not a selection）

Recommendation for Mother Ship to evaluate: **P1-A + P2-R1**, with SR-1 and the shared prerequisites. P2-R2
（re-bind form）is the only recovery candidate worth a later decision.

1. **Shared prerequisites（all options）:** B-1（remove the L-10 fallback; `user__isnull=True` in L-12）; X1
   （strip `_anon_cookie_value` from the browser body, L-4）; `isAllowedOrigin` on `/api/auth/logout`（L-6）.
2. **Logout and account deletion（P1-A）:** the BFF deletes the Web-origin `concierge_anon_id`（`Max-Age=0`）.
   The next guest request has no cookie, so the backend issues a fresh A'（`plan_service.py:41-42`）. No new
   endpoint and no signing in the BFF. Login never rotates. The UI says that the guest consultations of this
   browser end at logout.
3. **No recovery（P2-R1）:** a lost code before login → reissue as the guest（reissue revokes the old grant,
   G0）. A lost code after login, or after logout → the thread stays anonymous, is not deleted, and becomes
   unreachable; retention purges it. The UI tells the guest, at issuance and at logout, to finish the claim
   before logging out.
4. **SR-1:** read the anon signature with `max_age = 90 days`, so idle copies stop working. This changes no
   schema.
5. **No SR-5 for now:** closing "copied cookie + copied code" would reopen G1 for an attacker who already holds
   the browser profile and the screen. Recorded as residual RR-3.

Why this and not the others（inference）:

- It is the only combination that meets shared-browser privacy without new persistent secrets, new PII or new
  migrations.
- Loss under P2-R1 hurts availability（the user cannot save the consultation）, not confidentiality. P2-R2 and
  P2-R3 buy availability by adding a proof that works off the browser. That is exactly the property an
  attacker wants.
- P2-R3 has no infrastructure（L-16）and would make guests identifiable.

**Counter-argument:** P2-R1 means a user who logs in, loses the code and logs out loses the consultation from
that browser. How often this happens is **not measured**. If it is frequent, P2-R2 becomes the better trade,
and §6.2 keeps that door open without touching `0122`.

---

## 9. Data flow and authorization boundaries（under the §8 contract）

| operation | caller state | proof required | reads content? | writes |
| --- | --- | --- | --- | --- |
| guest chat / read `?tid=T` | guest | K1 = A, thread `user IS NULL, anonymous_id = A` | yes | messages（guest） |
| authenticated read of a guest thread | logged in | — | **never**（B-1） | — |
| issue handoff code | guest only | K1, thread anonymous with A | no（the code only） | grant row |
| claim | logged in | K1 + K4 + K3, explicit submit | after success | grant consumed; thread `user = U, anonymous_id = NULL` |
| logout | logged in | same-origin（new） | — | tokens and Web-origin anon cookie cleared; A' on the next guest request |
| account deletion | logged in | same-origin（existing） | — | user and owned threads deleted; anon cookie cleared on 204 |
| recovery re-bind（only if P2-R2） | guest | K6 | after success | thread `anonymous_id = A'`; secret consumed |
| retention purge | operator | — | — | deletes guest threads > 90 days（skips live grants, schema §10.1） |
| mobile chat | any（sent unauthenticated, L-17） | K1 if the native jar keeps it（NOT_VERIFIED） | — | anonymous threads |

---

## 10. Security test matrix（scenarios required by this task）

Expected outcome under each P1 option, with P2-R1 unless stated. ✓ = safe outcome, ✗ = exposure, — = n/a.

| # | scenario | P1-A | P1-B（+R2 re-bind） | P1-C |
| --- | --- | --- | --- | --- |
| S1 | G consults anonymously; V logs into the same browser | ✓ V cannot read（B-1）or claim（no code） | ✓ same | ✓ same while V is logged in; **✗ after V logs out**: V as guest holds A（S4 / §5.2 row 1） |
| S2 | G loses the code **before** login | ✓ G reissues as the guest; the old grant is revoked | ✓ same | ✓ same |
| S3 | G loses the code **after** login | thread unreachable from W after logout; not deleted | ✓ G re-binds with the secret, reissues, claims | G logs out, reissues as the guest（A survives）, claims — **and so can V**（S4） |
| S4 | G logs out before completing the handoff | G's own claim later fails（binding）; grant unusable from W; copy + code still valid to expiry（RR-3） | as P1-A, recoverable with the secret | grant still usable on W; V with the code can claim; V without the code can reissue |
| S5 | B（attacker）holds only A's old cookie | reads G's guest threads（rotation does not revoke, §3）; cannot claim without a code; SR-1 bounds idle copies | same; cannot re-bind without the secret | same |
| S6 | B holds only a copied code | ✓ claim fails: binding needs A（L-14） | ✓ same | ✓ same off-device; ✗ on W after logout |
| S7 | B holds a copied cookie **and** code | ✗ claims within 30 min（RR-3）; SR-5 would close it at the cost of G1 | ✗ same | ✗ same |
| S8 | G changes browsers | no access from the new browser（K1 missing）; nothing deleted | ✓ re-bind with the secret on the new browser | no access from the new browser |
| S9 | multiple tabs, concurrent recovery or claim | claim: one winner（thread lock, schema §8）; logout in one tab rotates for all | recovery: one consumes the secret（conditional UPDATE）; the other 404 | claim as P1-A |
| S10 | recovery racing retention | — | purge locks threads first with `SKIP LOCKED`; a re-bind holding T wins and the purge skips T; a purge holding T wins and the re-bind returns 404; never a partial state（same lock order） | — |
| S11 | account deletion and logout | both rotate A; guest threads of the old A untouched; owned threads deleted by CASCADE | same; open recovery secrets of the old A stay valid until claim / expiry | nothing rotates; next guest holds A |
| S12 | expired, replayed, revoked or stolen recovery secret | — | expired / replayed / revoked → uniform 404, counted toward lockout; **stolen → works**（RR-5）, mitigated only by single use, per-thread scope and the hard cap | — |

---

## 11. Privacy and usability trade-offs

| aspect | P1-A + R1 | P1-B（+R2） | P1-B（+R3） | P1-C |
| --- | --- | --- | --- | --- |
| next person on a shared browser | protected after logout | protected | protected | **exposed** |
| guest identifiability | none | none | **email collected**（new PII, policy change） | none |
| cost of a mistake（lost code after login） | consultation lost from this browser | user must have kept the secret | user must remember the address | recoverable, but so is V's attack |
| extra steps | none beyond the code | save one more secret | enter and verify email | none |
| mobile | no change; mobile already has no logout（L-18） | storing a long secret on a phone is fragile | familiar OTP; passkey setup is heavy | no change |
| implementation size | small（two BFF routes; no backend endpoint） | new table, 2 endpoints, UI | email infra or WebAuthn, tables, UI, policy | none（but needs a guest-read proof that does not exist） |

---

## 12. Residual risks

| id | risk | applies to |
| --- | --- | --- |
| RR-1 | guest → guest on one browser with no login: the second guest reads the first guest's threads | all options |
| RR-2 | a copied anon cookie keeps reading guest threads; rotation does not revoke it; SR-1 bounds only idle copies | all |
| RR-3 | copied cookie + copied code claims within 30 min | all, unless SR-5 |
| RR-4 | a lost code after login makes the consultation unreachable from that browser（not deleted） | P1-A + R1 |
| RR-5 | a stolen recovery secret gives read access and a claim path from any device until it is used or capped | P2-R2 |
| RR-6 | email takeover gives consultation access; guest email becomes stored PII | P2-R3 |
| RR-7 | the backend-origin cookie copy is not rotated by the BFF（NOT_VERIFIED whether it exists in production） | P1-A / B |
| RR-8 | forced logout through the origin-less logout route rotates A（NOT_VERIFIED; closed by `isAllowedOrigin`） | P1-A / B |
| RR-9 | other tabs keep `sessionStorage` / in-memory content until reload after a logout elsewhere | all |
| MF-1 | mobile sends concierge chat unauthenticated, so logged-in mobile consultations are anonymous and absent from history（L-17 to L-19） | existing; outside P1 / P2 |
| RR-10 | possession of a browser, code or secret is never proof of the same human（K5 not available） | all |

---

## 13. Migration impact

| change | migration | G1 |
| --- | --- | --- |
| P1-A / P1-B rotation | none（BFF cookie deletion only） | not reopened |
| SR-1 signature max-age | none | not reopened |
| B-1, X1, logout origin check | none | not reopened |
| SR-5 revoke grants at logout | **edit `0122`**: new `revoked_reason` value + the two value checks | **reopened**（D1 of #3316） |
| P2-R2 re-bind | **new migration** `0123+`: `ConciergeRecoverySecret`（own constraints, own reasons） | new G1 item; `ConciergeHandoffGrant` unchanged |
| P2-R2 direct transfer | new migration; possibly grant changes | reopened |
| P2-R3 | new tables（factor, OTP / WebAuthn state）, new dependency, privacy policy | new G1 items |
| SR-2 revocation list | new table | new G1 item |
| SR-3 / SR-4 re-key / orphan | data UPDATE on existing threads（no schema） | not schema, but changes consultation data: **not recommended** |

---

## 14. Architecture impact（exact places; nothing changed）

| layer | P1-A（and B） | P2-R2 additions | P1-C |
| --- | --- | --- | --- |
| Django models | none | `ConciergeRecoverySecret` after `ConciergeHandoffGrant` | none |
| Django services | `anonymous_id.py`: SR-1 `max_age`（rotation itself needs no backend change）; `concierge_history.py`: B-1 filter | `services/concierge_recovery.py`: issue / re-bind with thread → secret lock order | B-1 only |
| Django views / URLs | `api/views/concierge.py`: remove L-10 fallback; no new endpoint | issue and re-bind views | fallback removal |
| BFF | `app/api/auth/logout/route.ts`: `isAllowedOrigin`, delete `concierge_anon_id`; `app/api/users/me/route.ts`: delete it on 204; `app/api/concierge/chat/route.ts`: X1 | 2 routes with `isAllowedOrigin`; no cookie for the secret | X1 only |
| anonymous cookie handling | Web-origin rotation; backend-origin copy decision（D-7） | none | none |
| concierge frontend | logout copy; post-logout state reset already done for one tab（L-8）; claim-before-logout prompt | "save a recovery key" dialog; re-bind form for guests | none |
| handoff grant schema | none（unusable grants stay open to expiry） | none（re-bind + reissue） | none |
| guest retention | none | purge must lock threads first and cascade secrets（as schema §10.1） | none |
| PostgreSQL tests | rotation, B-1, SR-1 | re-bind races, purge race, lockout | B-1 |
| Web | as above | as above | — |
| native mobile | no logout exists（L-18）; rotation needs a backend endpoint + a logout UI + native cookie verification（L-19）; mobile handoff stays out of scope | out of scope until MF-1 is resolved | — |

---

## 15. Test plan for a later implementation PR（after approval）

**Backend（pytest, PostgreSQL）**

- rotation: a request without the cookie gets a new A'; the old signed A still verifies（documents §3）; with SR-1, an A signed more than 90 days ago returns 404 on guest reads.
- B-1: authenticated request + matching anon cookie → 404 on detail; append to a claimed thread does not write.
- S2–S4, S6, S7 with real grants: binding mismatch after rotation → 404 and `failed_attempts` unchanged for
  expired grants（schema I9）.
- No consultation row deleted by logout, rotation, account deletion of another user, or recovery（row counts）.
- P2-R2 only: issue / re-bind / replay / revoke / lockout; concurrent re-bind; re-bind vs purge both orders.

**BFF（vitest）**

- logout: cross-origin → 403; same-origin → token cookies and `concierge_anon_id` cleared in one response.
- account deletion 204 → rotation; non-204 → nothing changed.
- chat: X1, no `_anon_cookie_value` in the browser body.

**Web（vitest / Playwright）**

- S1, S4, S11 end to end with QA accounts; tab 2 after logout in tab 1 shows no prior content after reload.

**Mobile** — none until MF-1 and D-7 are decided.

---

## 16. Outstanding Mother Ship decisions

| id | decision | options | note |
| --- | --- | --- | --- |
| D-1 | P1 logout identity boundary | P1-A / P1-B / P1-C | recommendation for evaluation: P1-A; P1-C fails shared-browser privacy（§5.2） |
| D-2 | P2 recovery | R1 / R2 / R3 | recommendation for evaluation: R1 now; R2（re-bind）as the only follow-up candidate |
| D-3 | SR-5 revoke open grants at logout | yes（reopens G1, edits `0122`）/ no（accept RR-3） | recommendation: no |
| D-4 | if R2: scope per thread or per identity; re-bind or direct transfer | — | recommendation: per thread, re-bind |
| D-5 | if R2: hard lifetime cap for a secret | e.g. 30 / 90 days / until purge | open |
| D-6 | SR-1 signature max-age 90 days（X2） | yes / no | recommendation: yes; no schema change |
| D-7 | backend-origin anon cookie: confirm whether production Web calls the backend origin directly; rotate or retire that copy | — | NOT_VERIFIED（L-5） |
| D-8 | guest → guest exposure without login（RR-1）: accept, add "end guest session", or shorten the cookie lifetime | — | open |
| D-9 | whether logout UI must warn when this browser has issued a handoff code in the last 30 min（the server can tell from open grants bound to A） | — | open |
| D-10 | MF-1 mobile chat sent unauthenticated: separate fix | — | outside P1 / P2 |
| D-11 | whether final G1 waits for D-1 to D-3（Q7 of #3316） | — | open |

---

## 17. Not done

```text
runtime / backend / BFF / frontend / mobile code   UNCHANGED
cookies / auth configuration                       UNCHANGED
models / migrations（0122 not created）             UNCHANGED
database contents / consultation records           UNCHANGED（none deleted or reassigned）
production configuration                           NOT CONTACTED
P1 / P2                                            NOT SELECTED
PRODUCTION_SECURITY_E2E                            OPEN
```
