# FU-2-P7: Concierge Thread Ownership & SSR Boundary Audit（2026-10-27）

## 1. Status

```text
RECORD TYPE   = read-only audit（documentation + audit-only tests）
BASELINE      = origin/develop@3174088
SCOPE         = thread detail / list / chat append, concierge_anon_id lifecycle, SSR → BFF → Django path for P7 / P8
CHANGED       = this document; audit tests（backend 1 file, web 2 files）; regenerated call-graph inventory（file counts only）
UNCHANGED     = all application code, authentication, cookies, throttling, routing, recommendation, DB, Premium, UI
PRODUCTION    = NOT ACCESSED（no traffic, no logs, no env values, no data）
FINAL STATUS  = PR for Mother Ship review; routing decision and risk acceptance belong to Mother Ship; STOP
```

Evidence labels: **Code** = read in the current source; **Test** = proven by a local test in this PR or an existing
test; **Inferred** = follows from code but not executed end to end; **Unknown** = needs production facts this audit
must not collect.

## 2. Conclusion

1. **Cross-user isolation holds on every current path（Code + Test）.** No Critical or High finding.
   - The detail view returns one uniform `404 {"detail":"not found"}` for "missing" and "not yours". No content and no
     metadata leak, and no enumeration oracle.
   - The list view is user-only. A foreign `thread_id` on chat never writes into the foreign thread: `append_chat`
     raises `DoesNotExist`, and the view starts a new thread.
   - The other thread references（visit, action_event, shrine_interaction, reflection）require the authenticated owner.
2. **Two Medium findings concern the anonymous identity itself.** Neither is a cross-account IDOR.
   - **F1:** the signed id never expires server-side, and it is also returned in the JSON body, which defeats `HttpOnly`
     against XSS.
   - **F2:** whoever holds the browser's anonymous cookie, including a later-logged-in account on a shared browser,
     reads that cookie's anonymous threads.
3. **One Medium finding is availability.**
   - **F7:** thread reads share the `concierge` 8/min bucket with chat and plan.
4. **Three Low findings:**
   - **F3:** a latent write-path gap that must be closed before any handoff;
   - **F4:** BFF path traversal through the decoded `id`;
   - **F5:** the SSR destination comes from request headers when `WEB_BASE_URL` is unset.
5. **P7 routing recommendation: do NOT apply P2's Option A to P7.**
   - P7 is ownership-sensitive. The anonymous principal *is* a credential（`concierge_anon_id`）, so "no auth context →
     anonymous direct with no cookie" would always return 404.
   - Any direct path would have to carry credentials SSR-side, plus JWT refresh, which SSR cannot persist.
   - Recommendation: keep P7 / P8 on the BFF and address the throttle coupling（F7）separately（§8）.

## 3. Request paths（Code）

```text
Browser ──GET /shrines/{id}?ctx=concierge&tid=T──▶ Next SSR（shrines/[id]/page.tsx:376-424）
          GET /mypage/history/{tid}              ▶ Next SSR（mypage/history/[tid]/page.tsx:20; middleware requires access_token cookie）

Next SSR  getConciergeThreadServer(tid)  concierge.server.ts:5-28
  │  base = resolveServerBaseUrlFromHeaders(h)   resolveServerBaseUrl.ts:10-33（WEB_BASE_URL › x-forwarded-host/host › VERCEL_*）
  │  GET {base}/api/concierge-threads/{encodeURIComponent(tid)}/   Cookie: <entire page Cookie header>
  ▼
Next BFF  app/api/concierge-threads/[id]/route.ts:7-31 → bffFetchWithAuthFromReq（bffFetch.ts:128-238）
  │  pre-refresh if access_token missing/expiring and refresh_token present（:142-151）
  │  Authorization: Bearer <access_token | refreshed>   Cookie: <entire header>   X-KM-* signed from the BFF's own req（:189-196）
  │  retry once on 401 with refresh（:203-206）; relays status/body; sets refreshed access_token cookie（:231-235）
  ▼
Django    GET /api/concierge-threads/<int:pk>/ → ConciergeThreadDetailView（api/views/concierge.py:88-128）
          AllowAny, throttle scope "concierge"; JWTAuthentication + SessionAuthentication（settings.py:304-307）
          1) authenticated → filter(pk, user=request.user)
          2) else / not found → filter(pk, user IS NULL, anonymous_id = unsign(concierge_anon_id))
          3) else → 404 {"detail":"not found"}

P8（list）: getConciergeThreadsServer → /api/concierge-threads → ConciergeThreadListView（:57-77）IsAuthenticated, user only, 50 rows.

Write path: Browser → /api/concierge/chat（BFF chat/route.ts:86-160, djFetch, refresh-retry）→ ConciergeChatView
          append_chat（concierge_history.py:540-599）: thread_id given → select_for_update().get(id, user=U) or (id, anonymous_id=A);
          DoesNotExist → new thread（api_views_concierge.py:892-913）.
```

The shrine page makes up to three `concierge`-scope calls per render for an authenticated user: the detail, the list
and the previous thread's detail（`page.tsx:378, 391, 398`）. An anonymous visitor makes one: the list is 401 before
throttling, so there is no previous thread.

## 4. Ownership / authorization matrix

Legend: ✓ allowed, ✗ denied（the uniform 404 unless noted）. "anon A cookie" = a valid signed `concierge_anon_id` for id A.

| actor ＼ target | own anon thread（A） | other anon thread（B） | own user thread | other user's thread | test |
| --- | --- | --- | --- | --- | --- |
| **detail read** | | | | | |
| no cookie, no auth | ✗ | ✗ | ✗ | ✗ | existing + P7 |
| anon A cookie | ✓ | ✗ | — | ✗（also when the user thread carries `anonymous_id=A`） | existing + P7 |
| forged / unsigned / tampered / other-salt cookie | ✗ | ✗ | — | ✗ | existing + P7 |
| user U, no anon cookie | — | ✗ | ✓ | ✗ | existing |
| user U + anon A cookie | **✓（F2）** | ✗ | ✓ | ✗ | P7 |
| invalid / expired bearer + anon A cookie | **401**（not served on that hop; the BFF refreshes） | 401 | 401 | 401 | P7 |
| forged `X-User-Id` / `X-Anonymous-Id` / `X-KM-*` / XFF | ✗ | ✗ | ✗ | ✗ | P7 |
| **list** | | | | | |
| anonymous | 401 / 403 | | | | existing |
| user U | not listed（even with the anon A cookie） | not listed | listed | not listed | existing + P7 |
| **append（chat）** | | | | | |
| anon A, `thread_id` = own | ✓ | ✗ → new thread | — | ✗ → new thread | P7（service） |
| user U, `thread_id` = own | — | ✗ → new thread | ✓ | ✗ → new thread | P7（service） |
| anon A, user thread carrying `anonymous_id=A` | — | — | — | **✓（F3, latent）** | P7 strict xfail |
| **update / delete / save** | no endpoint exists. "Save" is a client-side ownership check against the list（`useConciergeThreadSave.ts:10-17`） | | | | — |
| **thread_id on visit / action_event / interaction / reflection** | authenticated owner only（`filter(id, user=user).exists()`） | | | | existing（visit, reflection） |

**`?tid=105`**: the value is only forwarded. The SSR helper encodes it, the BFF decodes it（F4）, Django matches
`<int:pk>` and applies the matrix above. A tid the visitor does not own renders the page without concierge sections,
because the helper returns `null` on 401 / 403 / 404. **Test**: the SSR helper test; the uniform 404 test.

## 5. Anonymous identity（P7-2）

| aspect | fact | evidence |
| --- | --- | --- |
| creation | Server-side `uuid4` in `get_or_create_anonymous_id`, reached from the plan context of chat / plan（`plan_service.py:42`）. The client cannot choose the value; it can only drop its cookie to get a new one | Code（`anonymous_id.py:53-61`） |
| format | `signing.dumps(id, salt="temples.concierge.anonymous_id")`（SECRET_KEY HMAC） | Code（`:16-21`） |
| validation | `signing.loads(..., max_age=None)`: **no server-side expiry**（F1） | Code（`:24-26`）; Test |
| Backend-origin cookie | `HttpOnly`, `Max-Age` 90 days, `SameSite=None; Secure` when not DEBUG, `Lax` in DEBUG | Code（`:70-79`） |
| Web-origin cookie | The BFF copies `_anon_cookie_value` from the chat body into a `Lax`, `HttpOnly`, 90-day cookie（`authCookies.ts:73-100`）. When Django also sends `Set-Cookie`, the response carries a **single** `concierge_anon_id`, the `Lax` one | Code; local probe of `chat/route.ts`（not committed）; existing route test |
| body exposure | `_anon_cookie_value` stays in the JSON body the browser receives（`api_views_concierge.py:332-333, 1012-1016`; `chat/route.ts:61-84` relays the body verbatim）（F1） | Code |
| transmission to Django | Only inside the forwarded Cookie header（BFF）; never as a header of its own | Code; Test（web） |
| usage | Detail read（`user IS NULL` required）, append（anonymous branch）, anonymous quota, Compass weekly owner | Code |
| logging | Booleans only（`anon_cookie_present`, `hasAnonCookie`）; existing privacy tests | Code; Test（existing + P7 web） |
| anonymous → authenticated | **No handoff exists.** Login and logout do not clear `concierge_anon_id`（only `access_token` / `refresh_token`, `auth/logout/route.ts`）. The anonymous thread stays `user=NULL`, and the logged-in session can still read it by direct id（F2） | Code; Test |
| cross-account / replay | Replaying a captured cookie value reads that browser's anonymous threads indefinitely（F1）. It never reaches a user-owned thread on the read path; on the write path it does not today, but would after a handoff that keeps `anonymous_id`（F3） | Test |

## 6. Findings

| id | severity | finding | evidence | impact | precondition |
| --- | --- | --- | --- | --- | --- |
| F1 | **Medium** | The anonymous credential has no server-side lifetime and is readable by page JS through the chat JSON body | `anonymous_id.py:24-26`; `api_views_concierge.py:332-333, 1012-1016`; `chat/route.ts:61-84, 159-162` | Anyone who obtains the value once（XSS on the Web origin, a copied response, a shared device）reads all anonymous consultations of that browser indefinitely; the 90-day `Max-Age` is client-side only | XSS or device / response access |
| F2 | **Medium**（privacy, shared device） | Any principal holding the browser's anonymous cookie reads its anonymous threads, including an account that logs in later on the same browser; logout does not clear the cookie | `api/views/concierge.py:121-125`; `auth/logout/route.ts:6-11`; the authentication libraries do not reference the cookie | User B on a shared browser can open user A's earlier anonymous consultation by direct id（e.g. history or a `?tid=` link）; it is never listed | Shared browser + knowledge of the thread id |
| F7 | **Medium**（availability） | Thread detail / list share the `concierge` 8/min bucket with chat and plan | `views/concierge.py:60, 90`; `api_views_concierge.py:470, 1086`; `settings.py:320`; Test | An authenticated user browsing ≥ 3 shrine pages from a consultation（3 calls each）can exhaust their chat quota for the minute; an anonymous SSR read is keyed by the SSR hop identity（FU-1 F-7）, so unrelated visitors share it. A 429 makes the helper throw, and the page silently drops the concierge sections | Code default 8/min; production override env is **Unknown** |
| F3 | **Low**（latent） | `append_chat`'s anonymous branch has no `user__isnull=True`, and the check constraint is OR, not XOR | `concierge_history.py:561-565`; `models.py:1353-1357`; Test（strict xfail: DID NOT RAISE） | If any row has both `user` and `anonymous_id`, the old anonymous cookie can append messages to the user's thread（integrity; the read path is safe） | Such a row exists. No current write path creates one; production data is **Unknown**. A future handoff that keeps `anonymous_id` creates it |
| F4 | **Low** | The BFF interpolates the decoded `id` param into the upstream path unvalidated; the URL parser resolves `..` | `concierge-threads/[id]/route.ts:8-9`; Next param decoding（`next/dist/shared/lib/router/utils/route-matcher.js:17-31`）; Test（`it.fails`） | A crafted link（`/mypage/history/..%2F..%2F…`）makes the victim's SSR / BFF issue an authenticated **GET** to another Django path with the victim's credentials; the result is rendered only to the victim as a thread object | Victim follows a link; Django GET endpoints keep their own authorization. End-to-end Next decoding of an encoded slash is **Inferred** |
| F5 | **Low**（configuration-dependent） | Without `WEB_BASE_URL`, the SSR helper picks its destination from `x-forwarded-host` / `host` and sends the whole Cookie header there | `resolveServerBaseUrl.ts:10-19`; `concierge.server.ts:7-17`; Test | A request whose host headers are not platform-controlled turns SSR into a fetch to an arbitrary host（with the requester's own cookies, so no victim credential） | `WEB_BASE_URL` unset（**Unknown**）and host headers not overwritten by the platform |
| I1 | Info | Thread ids are sequential integers, but there is no oracle | Test（uniform-404 test） | — | — |

None of the findings allows reading another account's thread, or another anonymous identity's thread without its
cookie value.

## 7. Existing coverage and missing cases（P7-4）

| case | before this PR | this PR |
| --- | --- | --- |
| cross-user IDOR, detail（A/B accounts, A/B anonymous, anonymous → user thread） | ✓ `temples/tests/api/test_concierge_thread_detail_authorization.py` | — |
| list isolation, list requires auth | ✓ same file | + an anonymous thread is not listed with the anon cookie |
| foreign `thread_id` on append（4 actor combinations） | ✗ | ✓ backend |
| append to a user thread carrying `anonymous_id`（F3） | ✗ | ✓ strict xfail |
| missing vs foreign 404 indistinguishable（anonymous, anon cookie, authenticated） | partial（body only） | ✓ |
| no identity metadata in the owner payload | ✗ | ✓ |
| tampered signature, other-salt cookie | unsigned only | ✓ |
| very old signed value still valid（F1） | ✗ | ✓（pins current behaviour） |
| forged identity headers | ✗ | ✓ 5 variants |
| invalid / expired bearer + valid anon cookie → 401, no content | ✗ | ✓ |
| user + matching anon cookie（F2）; login does not transfer | ✗ | ✓（pins current contract） |
| `concierge` scope shared; authenticated read spends the user bucket | ✗ | ✓ |
| BFF forwards the cookie / bearer, relays the 404, no secrets in logs | ✗ | ✓ web |
| BFF id traversal（F4） | ✗ | ✓ `it.fails` |
| SSR destination, header-derived host（F5）, encoding, null / throw mapping | partial | ✓ web |
| thread_id ownership on visit / reflection | ✓ existing | — |
| action_event / shrine_interaction thread_id | not found by name | not added（same `validate_thread_id` pattern; Code only） |
| logout clears anon cookie | ✗（it does not） | documented（F2）, not tested as desired behaviour |

## 8. FU-2-P7 routing recommendation（for Mother Ship）

**Recommendation: keep P7（detail）and P8（list）on the existing SSR → BFF → Django path. Do not implement Option A
for P7 now.**

Why P2's rule does not transfer:

1. P2 sends no Cookie and no Authorization because its anonymous response is public. P7's anonymous response is
   **private**: ownership requires `concierge_anon_id`. Under P2's rule every anonymous P7 read would return 404.
2. A credential-carrying direct path would need, in SSR:
   - the anon cookie forwarded to Django;
   - Bearer from `access_token`;
   - **JWT refresh**, whose new cookie SSR cannot set.

   Without refresh, an expired token gives 401 and the thread disappears（Test: invalid bearer → 401）. Re-implementing
   this outside `bffFetchWithAuthFromReq` duplicates the security-sensitive code and adds the F2 / F5 surfaces to a
   second place.
3. "No `access_token` / `refresh_token`" is **not** a safe signal that a P7 request is public. The request may still
   carry the anonymous ownership credential. Misclassifying it as public either breaks access（cookie dropped）or
   forwards a private credential on a path designed for public data.

If Mother Ship still wants a direct P7 path later, these are the minimum security constraints:

- **Credentials:** forward only `concierge_anon_id`（never the whole Cookie header）, plus Bearer from `access_token`.
  Keep any request with `refresh_token` on the BFF.
- **Destination:** a configured Backend origin only. Never derive it from request headers（F5）.
- **Input:** validate `tid` as a positive integer before building any URL（F4）.
- **Response handling:**
  - keep the uniform 404 and the `null` on 401 / 403 / 404;
  - never cache（`no-store`）;
  - log no cookie, token or content.
- **Identity:** sign the page identity exactly as P2 does. Never forward browser `X-KM-*` headers.

The real P7 problem is F7（the shared 8/min bucket）, not the hop. Options for a separate decision, none implemented:

- a separate read scope for thread detail / list（a throttle policy change; needs approval）;
- dropping the SSR previous-thread fetch from the shrine page;
- handling 429 explicitly instead of dropping the sections silently.

## 9. Implementation PR proposals（separate PRs; not implemented）

| PR | scope | addresses | risk |
| --- | --- | --- | --- |
| P7-A | `append_chat` anonymous branch adds `user__isnull=True`（behaviour unchanged for all current rows; the strict xfail flips to pass） | F3 | very low; a precondition for any handoff |
| P7-B | `concierge-threads/[id]/route.ts` rejects non-positive-integer ids with 404 before fetching（the `it.fails` flips） | F4 | very low |
| P7-C | SSR thread helpers use a configured origin（or require `WEB_BASE_URL` in production） | F5 | low; needs the production env fact |
| P7-D | Stop returning `_anon_cookie_value` to the browser. The BFF strips it after setting the cookie, or Django sends it through a header only the BFF reads | F1（JS exposure） | medium（Mobile does not use the body: **Unknown**, to verify） |
| P7-E | Server-side lifetime for the anonymous id（a `max_age` on unsign, or a versioned issue date）. **Product decision**: affects anonymous history continuity | F1（lifetime） | product |
| P7-F | Shared-browser policy: clear `concierge_anon_id` on login / logout, and/or skip the anonymous lookup for authenticated principals once a handoff exists. **Product decision** | F2 | product / UX |
| P7-G | Throttle coupling（§8 options） | F7 | policy decision |

## 10. Tests run（local only）

- Backend（PostgreSQL 16, CI-equivalent nogis settings, Python 3.13 locally; CI uses 3.11）:
  - `tests/test_fu2_p7_concierge_thread_ownership_audit.py`: **20 passed, 1 xfailed（strict）**. The xfail fails with
    `DID NOT RAISE DoesNotExist` under `--runxfail`, which proves F3.
  - With the existing thread detail, log-privacy, legacy-endpoint, visit and reflection API tests: **62 passed, 1
    xfailed**.
- Web（vitest）:
  - `concierge-threads/[id]/__tests__/route.p7audit.test.ts` and `lib/api/__tests__/concierge.server.p7audit.test.ts`:
    **12 passed, 1 expected fail**. The `it.fails` was checked to fail on its assertion when turned into a plain `it`.
  - Related suites（`api/concierge*`, `lib/api`, `shrines/[id]`, `mypage`, `features/concierge`）: **75 files, 562
    passed, 1 expected fail**.
- `tsc --noEmit` and ESLint on the new files: clean. `ruff check` on the new backend file: clean.
- `pnpm audit:bff-identity:check`: RECONCILED after regeneration. The only change is the analysed test-file count（719 →
  721）.

## 11. Blind spots / not done

- **Production is not observed.** These are not verified:
  - whether rows with both `user` and `anonymous_id` exist（F3）;
  - whether `WEB_BASE_URL` is set（F5）;
  - the effective `concierge` rate（F7）;
  - whether the platform overwrites `x-forwarded-host`.
- Mobile uses the Backend-origin cookie directly. Its handling of `_anon_cookie_value` and its CSRF exposure on POST with
  a `SameSite=None` cookie（chat uses `JWTAuthentication` only, so no CSRF check）were **not** audited here. The
  integrity impact would be an append to the victim's own anonymous thread; reading it is blocked by CORS（**Inferred**;
  CORS configuration not reviewed）.
- F4 end to end（a real Next server decoding `%2F` in the App Router）is inferred from the matcher source, not run.
- Counter-evidence to the main conclusion: F2 is a deliberate continuity behaviour（an anonymous consultation stays
  readable after login without a handoff）. Removing it without a handoff would break that flow, so the severity
  depends on Mother Ship's shared-device threat model.
