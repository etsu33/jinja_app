# Anonymous Handoff Code — DB Compatibility and Secure Lifecycle Audit（2026-10-22）

## 1. Status

```text
SCOPE                       = evidence-based design audit（docs only）
APPROACHES COMPARED         = A（persistent hashed grant）, B（stateless signed token + atomic transfer）
MIGRATION                   = A: REQUIRED（not approved; not created）  B: NOT REQUIRED
PRODUCT CONTRACT            = NOT SELECTED（Mother Ship decisions, §10）
RUNTIME / DB / PRODUCTION   = UNCHANGED
PRODUCTION_SECURITY_E2E     = OPEN
```

- Inspected:
  - `origin/develop@6189ba3`. Since `1b384d9`, the only change is #3311, a favorite-button label in
    `ConciergeSectionsRenderer.tsx` and `ShrineSaveButton.tsx`; none of the files below changed.
  - Open audit branches: `audit/production-concierge-isolation-e2e-20261022`（PR #3310）and
    `audit/concierge-anonymous-handoff-threat-model-v2`（PR #3312, which carries the Stage 1, v1 and v2
    docs）. This branch is stacked on #3312.
- Labels: **Fact** = verified in source on develop. **Inference** = reasoned from facts, not executed.
  **Proposal** = design for approval.
- No cookie value, token, code, consultation content or personal data is recorded.

---

## 2. Exact source evidence

### 2.1 Model and migration

| # | fact | location |
| --- | --- | --- |
| E1 | `ConciergeThread.user` is a FK, `null=True`, `on_delete=CASCADE` | `backend/temples/models.py:1321-1327` |
| E2 | `anonymous_id = CharField(max_length=64, null=True, blank=True, db_index=True)` | `models.py:1328` |
| E3 | Indexes `(user, last_message_at)` and `(anonymous_id, last_message_at)` | `models.py:1349-1352` |
| E4 | The only constraint is `CheckConstraint(Q(user__isnull=False) \| Q(anonymous_id__isnull=False), name="concierge_thread_user_or_anonymous_required")` | `models.py:1353-1358` |
| E5 | E2, E1 nullability, E3 and E4 come from migration `0078_conciergethread_anonymous_id_and_more`; there is no later migration for the thread | `backend/temples/migrations/0078_…py` |
| E6 | The model has no field for a handoff secret, hash, expiry, consumption, revocation, attempt count or claim time | `models.py:1320-1361` |
| E7 | `ConciergeMessage.thread` FK, CASCADE. Messages follow the thread on an owner change | `models.py:1374-1378` |
| E8 | No test asserts E4 for `ConciergeThread`. An equivalent `IntegrityError` test exists for `FeatureUsage` only | `backend/temples/tests/services/test_guest_data_retention.py:310-323` |

### 2.2 Anonymous identity

| # | fact | location |
| --- | --- | --- |
| E9 | `issue_anonymous_id()` is `str(uuid.uuid4())`（122 random bits） | `services/anonymous_id.py` |
| E10 | The cookie is `signing.dumps(raw, salt="temples.concierge.anonymous_id")`; it is verified with `max_age=None`, so there is no server expiry | `anonymous_id.py:_sign_anon_id, _unsign_anon_id` |
| E11 | Cookie attributes: HttpOnly, 90 days, `/`; `SameSite=None; Secure` when not DEBUG | `anonymous_id.py:attach_anonymous_cookie` |
| E12 | An authenticated request resolves `anon_id = None` for writes | `services/plan_service.py::resolve_plan_context` |

### 2.3 Write and read paths

| # | fact | location |
| --- | --- | --- |
| E13 | `append_chat` is `@transaction.atomic` and uses `select_for_update().get(id, user=U)` or `(id, anonymous_id=A)`; the anonymous branch has **no** `user__isnull=True` | `services/concierge_history.py:349-375` |
| E14 | On `DoesNotExist`, the chat view creates a new thread instead | `api_views_concierge.py:893-912` |
| E15 | The chat response includes `thread.id` and `_anon_cookie_value`（the signed anon value） | `api_views_concierge.py:295-334` |
| E16 | The detail view serves `user IS NULL AND anonymous_id=A` threads to authenticated requests too | `api/views/concierge.py:121-128` |
| E17 | The list view is `IsAuthenticated` and `filter(user=request.user)` | `api/views/concierge.py`（`ConciergeThreadListView`） |

### 2.4 Web, BFF and auth

| # | fact | location |
| --- | --- | --- |
| E18 | The guest save CTA redirects to `/auth/login?returnTo=/concierge`; the `tid` is dropped | `apps/web/src/app/concierge/ConciergeClientFull.tsx:461-471, 1034-1039` |
| E19 | Logged-in "save" only checks that the thread is in the user list; it writes nothing | `apps/web/src/features/concierge/useConciergeThreadSave.ts` |
| E20 | Login: BFF → `/api/auth/jwt/create/`; sets the `access_token` / `refresh_token` cookies; the form then does a full page load | `app/api/auth/login/route.ts`, `app/login/LoginForm.tsx:44-46` |
| E21 | Logout clears the two token cookies only | `app/api/auth/logout/route.ts` |
| E22 | `DELETE /api/users/me` has an origin check（`isAllowedOrigin`）and clears tokens on 204 | `app/api/users/me/route.ts:40-63` |
| E23 | Account deletion ends in `user.delete()` → threads are deleted by E1 CASCADE | `backend/users/services/account_deletion.py:372` |
| E24 | `AuthProvider.login` clears `concierge:eventsByThread`; `logout` also clears the anonymous snapshot | `apps/web/src/lib/auth/AuthProvider.tsx:190-206` |

### 2.5 Platform

| # | fact | location |
| --- | --- | --- |
| E25 | Production DB engine is PostgreSQL / PostGIS via `DATABASE_URL`; the local fallback is SQLite | `backend/shrine_project/settings.py:165-177` |
| E26 | No `ATOMIC_REQUESTS`; transactions are per call（`@transaction.atomic` where used） | `settings.py`（no match） |
| E27 | `CACHES` is `LocMemCache`（per process）; throttles `concierge: 8/min`, `anon: 100/min` are per process | `settings.py:312-317, 376-381` |
| E28 | No `SIMPLE_JWT` block; library defaults apply（no refresh rotation configured） | `settings.py`（no match） |

---

## 3. Database compatibility（item 1）

### 3.1 Does `ConciergeThread` support atomic ownership transfer?

**Yes, for the transfer itself.**

```sql
UPDATE temples_conciergethread
   SET user_id = :U, anonymous_id = NULL
 WHERE id = :T AND user_id IS NULL AND anonymous_id = :A;
```

- **E4:** `(user=U, anonymous_id=NULL)` satisfies the check constraint.
- **Inference（PostgreSQL READ COMMITTED, E25）:**
  - A second concurrent UPDATE waits on the row lock, re-evaluates `WHERE` against the committed row,
    and matches 0 rows. At most one transfer succeeds.
  - It also serializes with `append_chat`'s `select_for_update`（E13）:
    - If the claim commits first, a guest append re-checks `anonymous_id = A`, finds no row and takes
      the E14 path, creating a new anonymous thread. Nothing is written into the user's thread.
    - If the append commits first, the claim waits, then transfers the thread including that message.
- **To verify in the implementation PR:** this is reasoned, not executed. The test matrix（§9）includes a
  two-transaction test on PostgreSQL. SQLite would serialize at the database level and cannot prove it.
- `anonymous_id = NULL` also neutralizes the E13 gap for the transferred row. The `user__isnull=True`
  filter is still proposed as defense in depth.

**No, for a secret's own lifecycle.** E6: no column can hold a secret hash, expiry, consumption or
revocation.

### 3.2 A vs B

| property | **A. Persistent hashed grant** | **B. Stateless signed token + atomic transfer** |
| --- | --- | --- |
| new table / columns | `ConciergeHandoffGrant`（§4.2） | none |
| **migration** | **required**（CreateModel） | **not required** |
| at most one transfer per thread | yes（thread UPDATE） | yes（thread UPDATE） |
| a used secret cannot be reused | yes（`consumed_at`） | yes, indirectly: the thread is no longer claimable |
| explicit revocation of one unused secret | **yes**（`revoked_at`） | **no**（only TTL, anon-id change or `SECRET_KEY` rotation） |
| reissue invalidates the previous secret | **yes**（revoke older rows in the same transaction） | **no**（older tokens valid until TTL） |
| attempt counting / lockout | possible（per grant, in DB） | no（per-process throttle only, E27） |
| short typeable code | possible with lockout | **unsafe**; must stay ≥ 128 bits |
| audit record without content | yes（row with times, no secret） | log line only |
| server state to clean up | yes（expired rows; can CASCADE with the thread） | none |
| secret leak from a DB dump | hash only（SHA-256 of a 256-bit secret） | nothing stored; a `SECRET_KEY` leak forges tokens |
| compatibility with E4 / existing rows | no change to existing rows | no change to existing rows |

---

## 4. Recommended token lifecycle（item 2; proposal）

The common rule for both approaches: a transfer needs **(1)** the secret, **(2)** the current anon cookie
whose id matches the thread, **(3)** an authenticated session, and **(4)** an explicit user submission.
(2) alone, or (2)+(3), never authorizes a transfer.

### 4.1 Shared steps

| step | rule |
| --- | --- |
| issuance | Only for an **unauthenticated** request: the BFF sees no `access_token` / `refresh_token`, and the backend sees no user. It needs a valid signed anon cookie A and a thread `id=T, user IS NULL, anonymous_id=A`. Same-origin is enforced（`isAllowedOrigin`, as in E22）and only POST is accepted. Otherwise a uniform `404` |
| generation | `secrets.token_bytes(32)`（256-bit CSPRNG）. Never derived from A, T or time |
| presentation | Returned once in that POST response body. The UI shows it with a copy button and a warning, and hides it when dismissed. Never put in a cookie, `localStorage`, `sessionStorage`, a URL, analytics or logs. The BFF does not log bodies of these routes |
| encoding | Crockford Base32 in groups of 4. With A: `selector(8 chars).verifier(52 chars)`. With B: the signed compact form（≈ 40–60 chars） |
| expiration | TTL proposal **30 min**（M3）. Checked server-side at claim |
| claim | The user is authenticated and the request is same-origin POST `{code}`. The server verifies the code, the current anon cookie A and the thread conditions, then runs the §3.1 UPDATE in one transaction |
| response | `200 {saved:true, thread_id}`, or `200` idempotent when already owned by this user, or a uniform `404`. No reason is revealed |
| failed login | nothing is issued or consumed. The code stays with the user until its TTL |
| logout / abandon | nothing to clear in the browser（the code is not stored there）. An abandoned code expires at TTL. Under A it can also be revoked |

### 4.2 A — persistent grant

```text
ConciergeHandoffGrant
  id                 bigserial
  thread_id          FK ConciergeThread  ON DELETE CASCADE
  selector           char(16) unique         -- random, public lookup key
  verifier_hash      bytea(32)               -- SHA-256(verifier); compared in constant time
  anon_binding       bytea(32)               -- HMAC(SECRET_KEY-derived, A); A not stored raw
  created_at, expires_at
  consumed_at        null                    -- set once
  consumed_by_id     FK user null, SET_NULL
  revoked_at         null
  failed_attempts    smallint default 0
  CHECK (consumed_at IS NULL OR revoked_at IS NULL)
  partial index: (thread_id) WHERE consumed_at IS NULL AND revoked_at IS NULL
```

- **Hashing:** the verifier carries 256 bits of entropy, so a fast hash（SHA-256）is enough; a slow KDF is
  not needed. The selector allows an indexed lookup without timing leaks on the verifier.
- **Consumption（single transaction）:**
  1. `SELECT … FROM grant WHERE selector=:s FOR UPDATE`. Then check, in constant time, the verifier hash
     and the A binding, plus `consumed_at IS NULL AND revoked_at IS NULL AND expires_at > now()`.
     - On a hash or binding mismatch: increment `failed_attempts` in its own committed transaction,
       then return 404.
     - On any other failed check: 404.
  2. `UPDATE grant SET consumed_at=now(), consumed_by=U WHERE id=:g AND consumed_at IS NULL`.
  3. The §3.1 thread UPDATE. If either UPDATE touches 0 rows, roll back the whole transaction → 404.
- **Reissue:** in the same transaction as the new insert, set `revoked_at` on the thread's other open
  grants.
- **Explicit revocation:** a guest-state "cancel" with the anon cookie, and an internal admin path.
- **Lockout:** with `failed_attempts ≥ N` the grant is revoked.
- **Retention:** grant rows are deleted with their thread（CASCADE）. Consumed or expired rows are purged
  after N days by the existing manual retention command（decision M6）.

### 4.3 B — stateless token

```text
payload = v || thread_pk || issued_at || nonce(16B)
token   = payload || HMAC-SHA256(key=derive(SECRET_KEY,"concierge-handoff-v1"), payload || A)[:16]
```

- Verification: recompute the MAC with the current A, check the TTL, then run the §3.1 UPDATE.
- **One-time:** after a transfer the thread no longer matches `user_id IS NULL AND anonymous_id = A`, so
  every token for T is dead.
- **Replay before use:** valid until TTL. There is no revocation（§3.2）.
- **Concurrent claims:** decided by the thread UPDATE.

---

## 5. Shared-device threat model（item 3）

Two different protections, kept apart:

- **Inherited-cookie protection:** someone holding the browser's cookies without having seen the code.
  Achieved by both A and B, because the secret is required and not stored in the browser.
- **Stolen-secret protection:** someone who obtained the code. Both approaches **bind the code to A**, so
  a code alone works only from the original browser profile. Only A can **revoke** a code known to be
  exposed, or lock it after guesses.

| scenario | A | B |
| --- | --- | --- |
| another user opens the same browser（guest） | can read G's anonymous thread as a guest while A exists（existing I2 behavior; L-decision M5）; **cannot transfer** without the code | same |
| another user logs into their own account on the same browser | cannot read（the fallback is removed）; cannot transfer without the code | same |
| copied browser cookie（anon + tokens） | no code → no transfer | same |
| copied code, different device | the A binding fails → 404 | same |
| copied code **and** the same browser（e.g. code left on screen） | transfer possible until consumed, revoked or expired; G can revoke | transfer possible until consumed or expired; **no revoke** |
| two simultaneous claims（same or different accounts） | grant UPDATE + thread UPDATE: one winner; the other gets 404, or 200 idempotent for the same user | thread UPDATE: one winner |
| expired code | `expires_at` → 404 | TTL check → 404 |
| revoked code | `revoked_at` → 404 | n/a（not supported） |
| reissue after a suspected exposure | the older code is revoked | the older code stays valid until TTL |
| guessing | the 256-bit verifier plus lockout | the 128-bit MAC; per-process throttle only |
| browser refresh while the code is shown | the code is gone from the screen; the user must have copied it, or reissue（A revokes the old one） | reissue; the old one stays valid |
| multiple tabs | an independent grant per issue（or revoke-older per thread） | independent tokens |
| failed login | no effect | no effect |
| account switch X → Y | Y can transfer only with the code + A | same |
| logout, then the next guest | the code was never stored; a next guest without the code cannot transfer | same |

---

## 6. Existing user experience（item 4）

- **Legitimate anonymous consultations are preserved:**
  - No row changes at deployment.
  - There is no batch migration; each transfer is one explicit claim.
  - A guest keeps reading their thread while unauthenticated with A.
- **Pre-existing anonymous threads:** these can be claimed by the same flow, as long as A still exists in
  that browser.
- **A user who loses the code:**
  1. **Still a guest:** continue the consultation normally（read and append）. Issue a new code from the
     same thread whenever ready. Under A the lost code is revoked.
  2. **Already logged in:**
     - The thread is not shown while logged in. Showing it would expose it through the inherited cookie.
     - No code can be issued while authenticated, because that would be a cookie-only path.
     - The consultation stays anonymous and undeleted.
     - To continue, the user logs out and returns as a guest. That works only if A survives logout
       （**L2**）. Under **L1**（rotate A at logout）it becomes unreachable from that browser.
  3. **What protects other accounts in all cases:** no transfer happens without the code, and no account
     reads an ownerless thread.
- **Save flow change（E18, E19）:**
  - The guest save shows the code dialog, then goes to login with `returnTo` that keeps `tid`, or with a
    claim form on `/mypage`（allowed by `sanitizeNext`）.
  - The logged-in save path（E19）is unchanged.
- **Retention:** a claimed thread leaves the guest retention set. It is then deleted with the account
  （E23, CASCADE）, like every other account thread.

---

## 7. Minimum changes after approval（not implemented）

| layer | A | B |
| --- | --- | --- |
| backend | migration + model; issue / claim / revoke service and views; detail-view fallback removal（E16）; `append_chat` filter（E13） | issue / claim service and views; E16; E13 |
| BFF | `concierge-handoff/{code,claim,revoke}` with `isAllowedOrigin`, no body logging | `concierge-handoff/{code,claim}` |
| frontend | code dialog; claim form; guest "cancel code"; `returnTo` keeps `tid` | code dialog; claim form; `returnTo` keeps `tid` |
| auth routes | unchanged | unchanged |
| ranking / shrine data / billing / mobile | unchanged | unchanged |

---

## 8. Residual risks（item 5 of the deliverables）

| id | risk | A | B |
| --- | --- | --- | --- |
| RR1 | code exposed on the **same** browser（screen left open, shared clipboard, screenshot） | until consumed, revoked or expired | until consumed or expired |
| RR2 | no revocation of a known-exposed code | mitigated | **open** |
| RR3 | old code still valid after a reissue | mitigated | **open** until TTL |
| RR4 | brute force | lockout + 256-bit | 128-bit, per-process throttle |
| RR5 | `SECRET_KEY` compromise | the A binding can be forged; hashes stay safe | tokens can be forged |
| RR6 | lost code after login with L1 | unrecoverable（no deletion） | same |
| RR7 | possession of the browser plus the code is not proof of the same human | open | open |
| RR8 | friction on mobile browsers（copy across a full-page login, tab discarding） | same | same |
| RR9 | a DB migration and grant-row cleanup to operate | yes | none |
| RR10 | the backend-origin anon cookie copy | NOT_VERIFIED（Stage 1 R4） | same |
| RR11 | the transfer drops `anonymous_id` provenance on the row | the grant row keeps an audit trail | log line only |

---

## 9. Test matrix

### Backend（pytest, PostgreSQL）

| case | A | B |
| --- | --- | --- |
| E4 holds: thread with `user=NULL, anonymous_id=NULL` → `IntegrityError`（closes the E8 gap） | ✓ | ✓ |
| issue: authenticated / missing, forged or expired cookie / foreign T / user-owned T → 404, nothing stored | ✓ | ✓ |
| issue: the code is not in logs or `Set-Cookie`; only `verifier_hash` is stored | ✓ | ✓（nothing stored） |
| claim happy path: `user=U, anonymous_id=NULL`, messages intact, no row deleted | ✓ | ✓ |
| claim without the code（cookie + session only） → 404 | ✓ | ✓ |
| claim with the code + another browser's A → 404 | ✓ | ✓ |
| claim unauthenticated / tampered / expired → 404 | ✓ | ✓ |
| revoked grant → 404; reissue revokes the older one | ✓ | n/a |
| lockout after N failures | ✓ | n/a |
| replay after a success → 404; same user again → idempotent 200 | ✓ | ✓ |
| two transactions claim concurrently（threads or `select_for_update` ordering） → one winner | ✓ | ✓ |
| claim racing a guest `append_chat` → no anonymous write into the user thread | ✓ | ✓ |
| authenticated detail read of an ownerless thread with a matching cookie → 404 | ✓ | ✓ |
| guest retention: claimed T not in `expired_anonymous_threads`; grant rows CASCADE with the thread | ✓ | ✓ |
| migration: `makemigrations --check` clean, and forward / backward on a copy | ✓ | n/a（must show no migration） |

### BFF（vitest）

| case | expected |
| --- | --- |
| code route with `access_token` or `refresh_token` → refused, backend not called | ✓ |
| cross-origin POST → 403; GET → 405 | ✓ |
| no `Set-Cookie` for the code; bodies not logged | ✓ |
| claim forwards Bearer and the anon cookie; status passed through | ✓ |
| token refresh in other routes does not affect handoff | ✓ |
| login / logout routes unchanged; existing tests green | ✓ |

### Frontend（vitest）

| case | expected |
| --- | --- |
| guest save → code dialog; the code is absent from storage, URL and analytics calls | ✓ |
| dismiss and reload → the code is not shown again | ✓ |
| `returnTo` keeps `tid`, or points to the claim form | ✓ |
| claim form: success → history link; any failure → one generic message, no prior content | ✓ |
| multiple tabs: claim in one tab; the other tab shows the idempotent result | ✓ |
| PR #3309 isolation tests green | ✓ |

### Production QA（after deploy; QA accounts and test data only; no codes or content in the evidence）

- Guest → code → login → claim.
- A second account on the same browser without the code → no transfer.
- Code used from another browser → no transfer.
- Expired code; reissued code（A: the old code fails）.

---

## 10. Mother Ship decisions

| id | decision | notes |
| --- | --- | --- |
| M1 | **A**（persistent grant, migration）or **B**（stateless, no migration） | A adds revocation, reissue invalidation, lockout and an audit trail at the cost of a migration and cleanup; B is the smaller change with RR2 / RR3 open |
| M2 | If A: approve the `ConciergeHandoffGrant` migration as a separate, reviewed change | required before any implementation |
| M3 | TTL | proposal 30 min |
| M4 | Bind the code to the anon cookie（same browser only） | proposal yes; no cross-device claim |
| M5 | Logout: L1（rotate A）vs L2（keep A） | L1 makes a lost code after login unrecoverable; L2 lets the next guest read earlier guest threads |
| M6 | Grant-row retention（A） | e.g. purge consumed or expired rows after 30 days with the manual retention command |
| M7 | Accept residual risks RR1–RR11 for the chosen approach | required |
| M8 | Claim sets `anonymous_id = NULL` | proposal yes |
| M9 | Ship the shared prerequisites（E16 fallback removal, E13 filter, X1）with the handoff or separately | open |

---

## 11. Not done

```text
runtime / backend / BFF / frontend / mobile code    UNCHANGED
migrations / DB / auth configuration / production   UNCHANGED（no migration created）
consultation records                                UNCHANGED（none deleted or reassigned）
ranking / shrine data / billing                     UNCHANGED
repository hooks                                    NOT BYPASSED
PRODUCTION_SECURITY_E2E                             OPEN
```
