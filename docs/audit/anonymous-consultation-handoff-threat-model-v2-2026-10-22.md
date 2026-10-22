# Shared-Device Anonymous Consultation Handoff — Threat Model v2（2026-10-22）

## 1. Status

```text
SCOPE                          = design / audit only
OPTIONS COMPARED               = H1-A, H1-B, H1-C
PRODUCT CONTRACT               = NOT SELECTED（Mother Ship decision, §12）
RUNTIME / DB / AUTH CONFIG     = UNCHANGED
PRODUCTION_SECURITY_E2E        = OPEN
```

- Base: `origin/develop@1b384d9`, plus two earlier docs on this branch:
  - `anonymous-concierge-identity-boundary-b-contract-audit-2026-10-22.md`（Stage 1）
  - `anonymous-consultation-handoff-security-contract-2026-10-22.md`（v1）
- v1 proposed a browser-held grant cookie, a login-time bind and a post-login confirmation. That is
  **H1-A** here. Its main residual was R1: a different person who logs in on the same browser within the
  TTL can confirm. v2 asks whether that residual can be reduced.
- Labels: **Fact** = verified in source. **Inference** = reasoning from facts, not executed.
  **Proposal** = design for approval.
- No cookie value, token, code, consultation content or personal data is recorded here.

---

## 2. Verified facts this analysis depends on

| # | fact | source |
| --- | --- | --- |
| F-1 | The anonymous identity is a signed `concierge_anon_id` cookie. It is a **bearer** value: whoever holds the cookie jar holds the identity | `backend/temples/services/anonymous_id.py` |
| F-2 | Guest chats always create a thread `user=NULL, anonymous_id=A` with an id | `api_views_concierge.py:888-912` |
| F-3 | `CHECK (user IS NOT NULL OR anonymous_id IS NOT NULL)` is the only ownership constraint. No uniqueness on `anonymous_id`; no column for a handoff secret, its hash, an attempt count or a claim time | `models.py:1320-1358` |
| F-4 | Production uses PostgreSQL（PostGIS engine when `DATABASE_URL` is set）. The local fallback is SQLite | `backend/shrine_project/settings.py:165-177` |
| F-5 | `CACHES` is `LocMemCache`, so it is per process. Throttles（`concierge: 8/min`, `anon: 100/min`）are per process too | `settings.py:312-317, 376-381` |
| F-6 | Login is username + password → `/api/auth/jwt/create/`. Signup sets no tokens. No email or phone verification exists for guests | `app/api/auth/login/route.ts`, `app/api/auth/register/route.ts` |
| F-7 | `LoginForm` ends with `window.location.assign(afterLogin)`, a full page load. In-memory UI state does not survive login | `app/login/LoginForm.tsx:44-46` |
| F-8 | The guest save CTA redirects to `/auth/login?returnTo=/concierge` and drops `?tid=` | `ConciergeClientFull.tsx:461-471` |
| F-9 | `sanitizeNext` accepts `/concierge?…` and `/mypage…` as login return targets | `lib/nav/login.ts` |
| F-10 | The anonymous `append_chat` branch matches `id, anonymous_id` without `user__isnull=True` | `services/concierge_history.py:371-375` |
| F-11 | The detail view also serves ownerless threads to authenticated requests that carry a matching anon cookie（the B violation） | `api/views/concierge.py:121-128` |
| F-12 | The 90-day guest retention purge exists only as a manual command; it is not scheduled | `services/guest_data_retention.py`, `docs/ops/guest-data-retention.md` |

---

## 3. Trust boundary（item 1）

```text
 ┌─────────────── anonymous domain ───────────────┐      ┌────────── account domain ──────────┐
 │ proof: possession of a bearer cookie (A)       │      │ proof: knowledge of a password,    │
 │ scope: one browser profile, any person at it   │ ───► │        then JWT for that session    │
 │ strength: weak; no knowledge factor, copyable  │claim │ scope: one person (by assumption)   │
 └─────────────────────────────────────────────────┘      └─────────────────────────────────────┘
```

- A claim moves data **from the weaker domain into the stronger one**. After the claim, the account's
  password protects the consultation, and every later session of that account can read it.
- **Inference:** the claim decision has to rest on proof about the **anonymous side**. Stronger proof about
  the account side does not answer the question that matters: did the person claiming create this
  consultation?
- **Rule:** a proof is valid for the claim only if a different person, sitting at the same browser after
  the creator left, would normally not have it.

---

## 4. Which proof establishes control of the anonymous consultation（item 2）

| proof | what it shows | does V at the same browser have it? |
| --- | --- | --- |
| P1. anon cookie A | the browser profile created the thread | **yes** |
| P2. browser-held grant（v1 cookie）, recent | the browser profile pressed save within the TTL | **yes**, within the TTL |
| P3. account password / reauthentication | the claimant controls **the account** | V has V's own; this proves nothing about the thread |
| P4. secret shown to the creator and **not stored in the browser** | the claimant saw the screen when the secret was issued, or was given the secret | **no**, unless it was exposed（screen left open, clipboard, screenshot） |
| P5. human identity | — | not available. No guest factor exists（F-6） |

**Conclusion（inference）:** among the options, only **P4** separates the creator from a later person on
the same browser. P1 and P2 are browser-scoped. P3 is on the wrong side of the boundary.

---

## 5. Options

### H1-A — post-login confirmation only（= v1）

- Proofs: P1 + P2 + an authenticated session + an explicit click.
- Flow: guest save → grant cookie → login（bind）→ prompt → confirm.

### H1-B — H1-A plus reauthentication at confirm

- Proofs: P1 + P2 + **P3 again**（password re-entered at confirm）.
- **Inference:** the grant exists only in the guest state and has to be confirmed within the TTL of a fresh
  login, so the user typed the password minutes earlier anyway. Reauthentication stops someone who is
  **not** the account holder from confirming inside that account's session. But the threat in scope is V
  claiming G's consultation **into V's own account**, and V can reauthenticate as V. H1-B therefore does
  not reduce the shared-browser transfer risk; it only adds friction.

### H1-C — separately retained, high-entropy, single-use handoff secret

- Proofs: P1 + **P4** + an authenticated session + an explicit submission.
- Flow:
  - The guest presses save. The server issues a code for one thread and shows it once. The guest copies it
    or writes it down. The code is not put in a cookie, `localStorage`, `sessionStorage` or a URL.
  - The guest logs in, then pastes the code into a "save a consultation from before login" form.
  - The server claims the thread if the code is valid and the anon cookie still matches.
- Requiring P1 as well as P4 keeps a leaked code from being enough on its own from another device（§7）.
  That rules out cross-device handoff（decision M4）.

---

## 6. Proposed H1-C contract（issuance, storage, consumption, expiration, revocation）

### 6.1 Code format（stateless; proposal）

```text
payload  = version(1B) || thread_pk(varint) || issued_at(uint32, epoch seconds)
mac      = HMAC-SHA256(key = derive(SECRET_KEY, "concierge-handoff-code-v1"),
                       msg = payload || anonymous_id_A)[:16 bytes]      # 128-bit
code     = Crockford-Base32(payload || mac), shown as groups of 4（≈ 34–38 chars）
```

- A is part of the MAC input, never part of the code. The code reveals the thread pk and the issue time
  to whoever reads it, but no content and no anonymous id.
- A 128-bit MAC rules out online guessing even with per-process throttles（F-5）.
- Being stateless, the code needs no new storage（§8）.

### 6.2 Lifecycle

| step | endpoint（new） | preconditions（all required; else the same 404, no state change） | effect |
| --- | --- | --- | --- |
| ISSUE | BFF `POST /api/concierge-handoff/code {thread_id}` → backend `POST /api/concierge-threads/handoff/code/` | same-origin（`isAllowedOrigin`）; **no `access_token` / `refresh_token` cookie** at the BFF; unauthenticated at the backend; valid anon cookie A; thread `id=T, user IS NULL, anonymous_id=A` | returns the code **once** in the response body of this call only. No cookie is set; nothing is logged |
| DISPLAY | client | — | shows the code with a copy button and a warning（"anyone with this code and this browser can save this consultation"）; hides it when dismissed; does not persist it |
| LOGIN | existing | unchanged | `returnTo` should be `/concierge?tid=T` or the claim form（F-8, F-9） |
| CLAIM | BFF `POST /api/concierge-handoff/claim {code}` → backend `POST /api/concierge-threads/handoff/claim/` | same-origin; authenticated; code parses; MAC verifies with the **current** anon cookie A; `now - issued_at ≤ TTL`; thread `id=T` | conditional UPDATE（§6.3） |

### 6.3 Consumption — exactly once without new persistence（item 4）

```sql
UPDATE temples_conciergethread
   SET user_id = :U, anonymous_id = NULL
 WHERE id = :T AND user_id IS NULL AND anonymous_id = :A;
```

- **Fact（PostgreSQL semantics, F-4）:** under READ COMMITTED, a concurrent second UPDATE on the same row
  waits for the first to commit, then re-evaluates its `WHERE`. `user_id IS NULL` is now false, so it
  updates 0 rows. At most one claim per thread can succeed.
- `rowcount = 1` → `200 {"saved": true, "thread_id": T}`.
- `rowcount = 0` and the thread is now owned by U → `200`（idempotent; second tab or double submit）.
- Otherwise → `404 {"detail":"not found"}`.
- `anonymous_id = NULL` makes **every** code for T, and A itself, useless for T afterwards. This also
  closes F-10.

**What "exactly once" means without persistence:**

| property | without migration | needs persistence |
| --- | --- | --- |
| at most one successful claim per thread | **yes**（conditional UPDATE） | — |
| a used code cannot be reused | **yes**（the thread is no longer claimable） | — |
| revoke one unused code before its TTL（e.g. user reports exposure） | **no** | a table or column with the code hash / revocation |
| a reissued code invalidates the previous unused one | **no**（both stay valid until TTL） | the same |
| attempt counter / lockout per code or thread | **no**（per-process throttle only, F-5） | a table, or a shared cache（infrastructure change） |
| short human-typeable codes（e.g. 8 digits） | **unsafe**（guessable without lockout） | the same |

### 6.4 Expiration and lost codes（item 5）

- TTL（proposal **30 min**, decision M2）. This is longer than v1 because the user must handle the code
  themselves; it is still short enough to bound exposure.
- **Lost or expired code, while still a guest with A:** the guest presses save again and gets a new code.
  The old code stays valid until its TTL（§6.3 limitation）.
- **Lost or expired code after login:**
  - Fail closed. The thread stays anonymous and is not deleted.
  - While logged in, a new code cannot be issued. Issuing it from the inherited cookie would be a
    cookie-only path（forbidden）.
  - The user can log out and reissue as a guest **only if A survives logout**. Under L1（rotate A at
    logout, v1 D5）it does not, and the thread becomes unreachable from that browser.
  - This is an explicit interaction to decide（M5）.
- Error copy does not distinguish wrong, expired or foreign codes, so it gives no oracle.

### 6.5 Revocation

| event | effect |
| --- | --- |
| successful claim | all codes for T are dead（the thread is no longer claimable） |
| TTL expiry | that code is dead |
| anon cookie change（expiry, L1 rotation, other browser） | the MAC no longer verifies → every code from A is dead |
| `SECRET_KEY` rotation | every code is dead |
| user-reported exposure of one code | **not revocable** without persistence（R-C3） |

---

## 7. Scenario analysis（item 3）

`G` = guest who created T. `V` = a different person on the same browser. `M` = remote attacker.

| scenario | H1-A | H1-B | H1-C |
| --- | --- | --- | --- |
| G presses save, leaves before login; V logs in within the TTL | **V can claim**（prompt, one click） | **V can claim**（reauthenticates as V） | V **cannot** without the code; only if the code is still on screen or in a shared clipboard |
| G never presses save; V logs in | no transfer | no transfer | no transfer |
| G logs in, leaves before confirming; V uses G's session | V can move T into **G's** account（benign to G's data; T was G's） | blocked by reauthentication | V can submit only with the code; into G's account（benign） |
| account X → logout → account Y（account switch） | logout clears the grant | same | a code issued earlier in the guest state stays valid until TTL **only if anon id A was not rotated**（L2）, and Y still needs the code; under L1 the MAC fails |
| account X → account Y login without logout | the v1 bind rule deletes the grant | same | a code can be issued only in the guest state; Y needs the code |
| cookie jar copied to M（malware, extension, physical copy） | M logs in on their own account with the copied grant → **claims** within the TTL | same | M also needs the code |
| code exposed（screenshot, shoulder-surfing, shared clipboard, chat paste） | n/a | n/a | M also needs anon cookie A（same browser profile）→ fails off-device; V **on the same browser** succeeds within the TTL |
| code put in a URL by mistake | n/a | n/a | forbidden by contract; codes are POST bodies only; never logged |
| multiple tabs | one grant per profile, last write wins | same | one code per issue; codes for different threads coexist |
| token / code replay after a claim | 404 | 404 | 404（the thread is no longer claimable） |
| replay before a claim, within the TTL | grant cookie valid for the bound user | same | the code is valid for any account on the same browser |
| concurrent claims（two tabs, double submit） | one UPDATE wins; idempotent 200 | same | same |
| failed login | no bind; grant pending until TTL | same | nothing changes; the code is still held by the user |
| token refresh mid-flow | no effect | no effect | no effect |
| mobile native app | cannot hold the Web grant → fails closed | same | the app can display and accept a code, but the backend anon cookie on native is NOT_VERIFIED → out of scope |

---

## 8. Migration and compatibility（item 8）

```text
H1-A  MIGRATION = NO
H1-B  MIGRATION = NO   (reauthentication = second POST to jwt/create; compare user id)
H1-C  MIGRATION = NO   for the stateless 128-bit code (§6.1)
H1-C+ MIGRATION = YES  for per-code revocation, reissue invalidation, attempt lockout or short codes
```

- **Compatibility:**
  - No existing row is changed by deployment.
  - Anonymous threads created before deployment can be claimed through H1-C, as long as the guest still
    holds A in that browser and issues a code as a guest.
  - PR #3309's frontend isolation and its tests are unaffected.
  - The v1 grant cookie and login-time bind are **not needed** under H1-C, so `/api/auth/login` stays
    unchanged.
  - The removal of the F-11 fallback is shared by all options. It changes one behavior: today a guest who
    logs in can still open `?tid=T` through browser history. After the change that shows 404 until a
    claim. This is the intended B outcome.

---

## 9. Usability（item 6）

| aspect | H1-A | H1-B | H1-C |
| --- | --- | --- | --- |
| extra steps for the legitimate guest | 1 click | password + click | copy code → login → paste |
| full-page login reload（F-7） | survives（cookie） | survives | the user must keep the code（clipboard / note）; the screen does not |
| mobile browser | fine | password re-entry on a phone | copy/paste across the login page works; tab discarding on iOS/Android also loses the screen, so the code has to be copied first; typing ~36 chars is poor; password-manager app switches can clear the screen |
| shared-device warning needed | yes | yes | yes, plus "do not leave the code on screen" |
| existing save CTA（F-8） | must keep `tid` in `returnTo` | same | same, or send the user to a claim form（`/mypage` allowed by F-9） |
| expected drop-off | low | medium | **highest**（inference; not measured） |

---

## 10. Minimum changes per option（item 7; not implemented）

**Common to all options**

- Backend `api/views/concierge.py`: remove the authenticated fallback（F-11）.
- Backend `services/concierge_history.py`: anonymous append adds `user__isnull=True`（F-10）.
- Backend: one conditional-UPDATE claim service plus a view and URL in `api/urls.py`.
- Web `ConciergeClientFull.tsx`: `returnTo` keeps `tid`（F-8）.

| layer | H1-A | H1-B | H1-C |
| --- | --- | --- | --- |
| backend | start / bind / confirm endpoints; signed grant | H1-A + reauth check at confirm | issue-code and claim endpoints; HMAC code; **no** bind |
| BFF | start / status / confirm / decline routes; grant cookie helpers; login route bind; logout and account-deletion clear | H1-A + credential forwarding at confirm | 2 routes（code, claim）with `isAllowedOrigin`; no cookie; **login / logout untouched** |
| frontend | save → start; post-login prompt | prompt with a password field | save → code dialog（copy, warning, hide）; claim form（paste）after login |
| migration | no | no | no（stateless code） |

---

## 11. Residual risks（item 9）

**H1-A**

- R-A1: V on the same browser within the TTL can claim G's consultation with one click.
- R-A2: a copied cookie jar plus M's own account can claim within the TTL.
- R-A3: one grant per browser.
- R-A4: no per-grant revocation.

**H1-B**

- All of H1-A. R-A1 and R-A2 are **not** reduced, because V and M reauthenticate to their own accounts.
- R-B1: added friction, and a second password prompt to protect.

**H1-C**

- R-C1: the code is a bearer secret on the same browser. If G leaves it on screen, in a shared clipboard or
  in a screenshot, V at that browser can claim within the TTL.
- R-C2: a lost code after login is unrecoverable through the handoff when A is rotated（L1）. The
  consultation stays anonymous and is not deleted.
- R-C3: no revocation of one unused code without persistence; a reissue leaves earlier codes valid until
  their TTL.
- R-C4: highest friction, worst on mobile; likely lower save completion.
- R-C5: the code reveals the thread pk and issue time to whoever reads it（no content）.
- R-C6: throttles are per process（F-5）. Safety depends on the 128-bit entropy, not on rate limits.

**All options**

- Possession of an anonymous session, or of a code shown on it, is not proof of the same human（P5 is not
  available）.
- The backend-origin anon cookie copy is NOT_VERIFIED（Stage 1 R4）.

---

## 12. Bounded MVP recommendation（item 10; not a product decision）

**Recommended for evaluation: H1-C stateless.**

- Proof: code + the current anon cookie + an authenticated session.
- 128-bit code, TTL 30 min, displayed once and never stored in the browser.
- Atomic conditional UPDATE that sets `anonymous_id = NULL`.
- No migration, and no changes to login or logout.

Reasons:

- It is the only option whose proof（P4）separates the creator from a later person on the same browser
  （§4）.
- It needs fewer server pieces than H1-A: no grant cookie, no bind, no status endpoint.
- Exactly-once claiming holds with the existing columns（§6.3）.

H1-B is **not recommended**: it adds friction without reducing the shared-browser transfer risk（§5）.

H1-A remains the low-friction alternative **if Mother Ship accepts R-A1**.

This recommendation trades usability（R-C4）for transfer safety. Whether that trade is right depends on how
often guest consultations happen on shared devices. That has not been measured.

---

## 13. Test matrix（for the implementation PR after approval）

### Backend（pytest, PostgreSQL）

| case | expected |
| --- | --- |
| authenticated request with a matching anon cookie reads anonymous T | 404, no content（all options） |
| ISSUE: authenticated / no cookie / forged cookie / foreign T / user-owned T | 404; no code |
| ISSUE valid | code returned once; not logged; no cookie set |
| CLAIM valid（code + A + auth） | `user=U, anonymous_id=NULL`; messages intact; row count unchanged |
| CLAIM with a tampered MAC / wrong A / expired / unauthenticated / another thread's code | 404; row unchanged |
| CLAIM twice; two concurrent transactions | exactly one update; second idempotent 200 |
| CLAIM after the claim with an older code | 404 |
| anonymous append to a claimed thread | does not write to the user thread |
| reissue: two codes for T, claim with one, then the other | second 404 |
| no consultation row deleted in any case | counts unchanged |
| guest retention after a claim | claimed T not in `expired_anonymous_threads` |

### BFF（vitest）

| case | expected |
| --- | --- |
| code route with `access_token` or `refresh_token` present | refused; backend not called |
| cross-origin code / claim | 403 |
| code route response: no `Set-Cookie` for the code; no logging of the body | yes |
| claim route forwards Bearer and cookies; propagates 200 / 404 unchanged | yes |
| login / logout routes unchanged（H1-C） | existing tests green |

### Web（vitest）

| case | expected |
| --- | --- |
| guest save → code dialog with copy and warning; code not in storage or URL | yes |
| dismiss hides the code; reload does not show it again | yes |
| after login, the claim form accepts a pasted code → success → history link | yes |
| wrong / expired code → one generic error; no prior content shown | yes |
| A → logout → B on `?tid=T` | no content |
| PR #3309 isolation tests | green |

### Production QA（after deploy; QA accounts, test data only）

- Guest → code → login → claim.
- Guest → code → leave → second QA account logs in without the code → cannot claim.
- Wrong code; expired code.
- No codes, cookies or content in the evidence.

---

## 14. Remaining Mother Ship decisions

| id | decision | options |
| --- | --- | --- |
| M1 | Handoff option | H1-A / H1-B / H1-C（recommendation: H1-C stateless; H1-B not recommended） |
| M2 | TTL | H1-A 10 min; H1-C 30 min（proposal） |
| M3 | Accept the residuals of the chosen option（§11） | required |
| M4 | Require anon cookie A at claim（same browser only）vs allow cross-device claim with the code alone | recommendation: require A |
| M5 | Logout behavior L1（rotate A）vs L2, given R-C2 | L1 makes lost codes after login unrecoverable; L2 leaves guest threads readable to the next guest |
| M6 | Accept no per-code revocation（stateless）, or approve a migration for revocation / lockout / short codes | recommendation: stateless for the MVP |
| M7 | Claim sets `anonymous_id = NULL`（drops provenance; a log line instead） | recommendation: NULL |
| M8 | Accepted save-flow friction / drop-off before measurement, or measure the share of shared-device guest saves first | open |
| M9 | X1（strip `_anon_cookie_value` from the browser body）as a separate change | recommendation: yes |

---

## 15. Not done

```text
runtime / backend / BFF / frontend / mobile code   UNCHANGED
auth configuration / cookies / DB / migrations     UNCHANGED
consultation records                               UNCHANGED（none deleted or reassigned）
recommendation logic / shrine data / billing       UNCHANGED
PRODUCTION_SECURITY_E2E                            OPEN
```
