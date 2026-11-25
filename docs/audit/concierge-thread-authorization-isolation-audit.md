# Concierge Thread Authorization Isolation Audit（2026-10-22）

## 1. Status

```text
BACKEND_THREAD_AUTHORIZATION          = NO DEFECT FOUND（source + regression tests）
FRONTEND_FALLBACK_AFTER_API_DENIAL    = CONFIRMED DEFECT（reproduced in test, fixed）
FRONTEND_STALE_THREAD_ON_TID_SWITCH   = CONFIRMED DEFECT（reproduced in test, fixed）
BROWSER_STORAGE_ACROSS_ACCOUNTS       = CONFIRMED DEFECT（no clearing on login / logout; fixed）
PRODUCTION_ROOT_CAUSE_OF_2026_10_22   = NOT ESTABLISHED（identity per HTTP response unknown）
PRODUCTION_SECURITY_E2E               = NOT CLOSED（manual QA in §9）
```

- Base: `origin/develop@09aaed3`
- Related record: [`production-concierge-thread-followup-2026-10-22.md`](production-concierge-thread-followup-2026-10-22.md)
- No private user data, consultation content, account identifier, cookie or token is recorded here.

---

## 2. Reported scenario（Production, 2026-10-22）

- A user opened `/concierge?tid=88` after switching accounts and saw consultation-specific
  recommendation content.
- Similar content was reported in a Chrome Incognito window.
- Render logs showed `GET /api/concierge-threads/88/` returning both `404` and `200` under different
  authentication conditions.
- **Not established:** which identity made each request, and whether the displayed content came from the
  API, from browser storage or from in-memory state. No cross-account leak has been proven from the
  Production evidence alone.

---

## 3. Relevant source files

| area | file |
| --- | --- |
| thread detail / list API | `backend/temples/api/views/concierge.py`（`ConciergeThreadDetailView`, `ConciergeThreadListView`） |
| routing | `backend/temples/api/urls.py`（`concierge-threads/`, `concierge-threads/<int:pk>/`） |
| anonymous identity | `backend/temples/services/anonymous_id.py`（signed `concierge_anon_id` cookie, httpOnly） |
| thread write path | `backend/temples/services/concierge_history.py::append_chat`, `backend/temples/api_views_concierge.py` |
| frontend thread page | `apps/web/src/app/concierge/ConciergeClientFull.tsx` |
| thread detail client | `apps/web/src/lib/api/concierge.ts::getConciergeThread`（401 / 403 / 404 → `null`） |
| auth state | `apps/web/src/lib/auth/AuthProvider.tsx` |

---

## 4. Backend authorization（no defect found）

`ConciergeThreadDetailView.get`（`AllowAny`）:

1. If the request is authenticated, it looks up `ConciergeThread(pk, user=request.user)`.
2. If not found, it looks up `ConciergeThread(pk, user IS NULL, anonymous_id=<signed cookie value>)`.
3. Otherwise it returns `404 {"detail": "not found"}`. The body contains no thread data.

Assessment:

| invariant | result | basis |
| --- | --- | --- |
| account B cannot read account A's thread | holds | step 1 filters by `user`; step 2 requires `user IS NULL` |
| an anonymous visitor cannot read a user-owned thread | holds | step 2 requires `user IS NULL`, even when `anonymous_id` matches |
| unrelated anonymous identities are isolated | holds | the cookie is signed（`django.core.signing`）; an unsigned or forged value resolves to `None` |
| a new Incognito session cannot read any existing thread | holds | no session and no anonymous cookie → 404 |
| the thread list exposes only own threads | holds | `IsAuthenticated` + `filter(user=request.user)` |
| the write path cannot append to another account's thread | holds | `append_chat` uses `get(id, user=user)`; a miss raises `DoesNotExist` and a new thread is created |

Authenticated chat threads are saved with `anonymous_id = None`（`api_views_concierge.py`）, so the
anonymous fallback can never reach them.

**Design observation（not changed; Mother Ship decision）:** step 2 also runs for authenticated
requests. An ownerless thread created anonymously in a browser therefore stays readable by whoever
holds that browser's `concierge_anon_id` cookie. That includes any account later signed in on the same
browser, and a guest after logout, because logout does not clear the httpOnly cookie and login does not
claim anonymous threads. This is the anonymous-identity design（the cookie *is* the identity）, not a
bypass of account ownership. Changing it would change the anonymous-consultation product contract.

The `404` and `200` responses for the same tid in Production are consistent with this design: the same
thread was requested by different identities. That alone does not show a defect.

---

## 5. Frontend: confirmed root cause

### 5.1 Local cache rendered after API denial

- `ConciergeClientFull.tsx` keeps `eventsByThread` in `localStorage` under `concierge:eventsByThread`.
  The key is **per tid only**, with no identity in it. The cache holds `assistant_state`（full
  recommendation payloads）and user / assistant message text.
- For `?tid=N`:
  - `getConciergeThread(N)` maps 401 / 403 / 404 to `null`, so `threadDetail` becomes `null`.
  - `displayUnified = liveUnified ?? backendUnified ?? lastUnified`, where `lastUnified` is the newest
    local `assistant_state` for N.
  - `messages = deriveMessages(events)`, where `events` are the local events for N.
- **Effect:** after the API denies N, the locally cached recommendations and messages for N are still
  rendered. They are whatever any earlier identity on the same browser profile left for that tid.
- Reproduced: `ConciergeClientFull.threadIsolation.test.tsx` renders the cached foreign shrine name
  after a `null`（denied）response on unmodified `develop`.

### 5.2 Stale thread while switching tid

- The detail-fetch effect did not reset `threadDetail` when `tidNum` changed. `liveUnified` / `liveRecs`
  were not tied to a tid.
- **Effect:** while tid B's request is pending, tid A's content is shown under tid B. A live chat result
  from tid A also stays primary under tid B. Reproduced in the same test file.
- Out-of-order responses were already handled correctly by the effect's `cancelled` flag.

### 5.3 No storage clearing at identity boundaries

`AuthProvider.login` / `logout` did not touch `concierge:eventsByThread`（localStorage）or
`concierge:anonymousSnapshot:v1`（sessionStorage）, so the local cache carried across accounts on the
same browser.

### 5.4 What this explains, and what it does not

- **Explained:** "account switched, then `?tid=88` showed consultation content". If the earlier identity
  had viewed tid 88 in that browser, its cached state for tid 88 is rendered even when the API returns
  404 for the new identity.
- **Not explained:** the Incognito report. A new Incognito window starts with empty storage and no
  cookies, so neither path above can supply tid 88 content. The detail API returns 404 there.
  Missing evidence:
  - whether the window was newly opened;
  - whether a consultation was submitted in that window first, which creates a *new* tid;
  - the response status of the Incognito request;
  - whether the content was really tid-88-specific or generic sections.

```text
INCOGNITO_OBSERVATION = UNEXPLAINED / EVIDENCE MISSING（not addressed by speculation）
```

---

## 6. Change scope（frontend only; no backend runtime change）

| file | change |
| --- | --- |
| `apps/web/src/lib/concierge/conciergeLocalState.ts`（new） | shared storage keys, `clearConciergeThreadCache()`, `clearConciergeAnonymousSnapshot()` |
| `apps/web/src/lib/auth/AuthProvider.tsx` | `login`: clear the thread cache（keep the same tab's anonymous snapshot）; `logout`: clear the thread cache and the anonymous snapshot |
| `apps/web/src/app/concierge/ConciergeClientFull.tsx` | see below |

`ConciergeClientFull.tsx` changes:

1. `threadAccess = { tid, status: pending | granted | denied | unavailable }`. On a tid change,
   `threadDetail` is reset and the status becomes pending.
2. A response is `granted` only if it is non-null **and** `data.id === tidNum`.
   - `null`（401 / 403 / 404）→ `denied`, and that tid's entry is removed from `eventsByThread`.
   - network / 5xx → `unavailable`. The cache is kept but not displayed（fail closed）.
3. On `?tid=` routes:
   - `backendUnified` is used only when granted;
   - local `events`（`lastUnified` and the message list）are used only when granted;
   - the entry route（no tid）is unchanged.
4. `liveTid` records which thread `liveUnified` / `liveRecs` belong to. On `?tid=N`, live state is used
   only if `liveTid === N`.
5. Identity change on the same screen. This applies only after auth has resolved, and only when the
   previous identity was an authenticated user（`user:A → user:B` or `user:A → guest`）:
   - clear live / detail / thread-access state, `eventsByThread`, and both storage keys;
   - re-check access for the current tid（the fetch effect depends on `identityKey`）.

   `guest → login` does not clear, so a guest's own anonymous result survives login. The `?tid=`
   display is still guarded by item 3.

Not changed:

- backend views, models, migrations, cookies, ranking or scoring;
- API contracts;
- the anonymous-consultation flow;
- the backend shared-browser anonymous fallback（§4 observation）.

---

## 7. Before / after

| scenario | before | after |
| --- | --- | --- |
| `?tid=N`, API 404, local cache has N from another identity | cached recommendations and messages shown | nothing private shown（neutral sections only）; cache entry for N removed |
| `?tid=N`, API 200（own thread） | backend thread shown | unchanged |
| own thread, backend has no recommendations, local cache has them | local cache fills in | unchanged（allowed after granted） |
| switching tid A → B, B pending | A shown under B | nothing from A shown; B shown when granted |
| late response for the previous tid | ignored（`cancelled`） | unchanged（still ignored） |
| A → logout → B on the same browser | A's local cache persists for B | cleared at logout |
| A → login as B（no logout） | persists | cleared at login |
| A → B on the same screen without remount | A's live / detail state stays | cleared; access re-checked as B |
| anonymous consultation（entry → `?tid=`） | works | unchanged（live result has `liveTid = tid`） |
| anonymous owner reopening `?tid=`（cookie valid） | works | unchanged（API 200 → granted） |
| network / 5xx on `?tid=` | local cache shown | not shown（fail closed） |

---

## 8. Regression tests

Frontend `apps/web/src/app/concierge/__tests__/ConciergeClientFull.threadIsolation.test.tsx`（9 tests;
5 fail on unmodified `develop`）:

- API denial with a populated foreign cache → not rendered; the cache entry is removed;
- direct `?tid=` after logout with a leftover cache → not rendered;
- own thread（200）→ rendered; the local cache fills in only after granted;
- tid switch while pending → the previous thread is not shown; a late response for the previous tid is ignored;
- in-page account switch → state and storage cleared; access re-checked as the new identity.

Frontend `apps/web/src/lib/auth/__tests__/AuthProvider.conciergeStorage.test.tsx`（2 tests）:

- logout clears both keys;
- login clears the thread cache and keeps the anonymous snapshot.

Backend `backend/temples/tests/api/test_concierge_thread_detail_authorization.py`（10 tests; lock in
current behavior）:

- account A reads its own thread;
- account B → 404 with no content;
- an anonymous visitor（no cookie, or another cookie）→ 404;
- an anonymous cookie matching a user-owned thread's `anonymous_id` → 404;
- the anonymous owner → 200;
- another anonymous identity → 404;
- an unsigned cookie → 404;
- an authenticated user with another anonymous cookie → 404;
- the list returns only own threads; the list requires authentication.

Existing tests kept: `ConciergeClientFull.autoSubmitPending.test.tsx`（entry → `?tid=` flow, recommendations
rendering）and `test_concierge_thread_log_privacy.py`.

---

## 9. Known limitations and remaining Production QA

Limitations:

- **Shared-browser anonymous cookie（§4）.** Not changed. If Mother Ship wants signed-in requests to stop
  falling back to the browser's anonymous identity, or logout to rotate the anonymous cookie, that is a
  product-contract change for a separate PR.
- **Entry-route anonymous snapshot / `eventsByThread[0]`.** These are still restored on `/concierge`
  for the same browser identity. They are cleared on logout, and the thread cache is cleared on login.
- **Pre-fix caches.** Caches left by a pre-fix build stay in a user's browser until the next
  login / logout or until the API denies that tid. They are no longer displayed on `?tid=` without a
  `granted` response.
- **Incognito.** The Incognito observation remains unexplained（§5.4）.

Manual Production QA（authorized QA accounts and test consultations only; record statuses, not content）:

1. QA account A creates a test consultation and opens `?tid=<A's test tid>`. Expected: shown.
2. In the same browser, log out, log in as QA account B and open the same URL. Expected: API 404 and
   no A content. `concierge:eventsByThread` in DevTools has no entry for that tid.
3. In a new Incognito window, open the same URL directly. Expected: API 404 and no content.
   If content appears, capture the network status and whether any request returned 200, without
   recording the content itself.
4. As a guest, create an anonymous consultation and reopen its `?tid=`. Expected: shown（anonymous flow
   intact）.
5. Switch quickly between two of B's own threads. Expected: each tid shows only its own result.

```text
PRODUCTION_SECURITY_E2E = OPEN（steps 1–5 not executed）
```
