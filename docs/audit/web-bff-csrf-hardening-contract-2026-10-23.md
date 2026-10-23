# Web BFF CSRF Hardening Contract — V-1（2026-10-23）

## 1. Status

```text
SCOPE                          = implementation contract, documentation only
SOURCE                         = PR #3318 decision V-1（open, not merged）
runtime / BFF / cookies / auth = UNCHANGED
tokens / models / migrations   = UNCHANGED
P1 / P2                        = NOT IMPLEMENTED, NOT SELECTED
production                     = NOT CONTACTED（no requests, no tests against it）
IMPLEMENTATION                 = NOT APPROVED — needs Mother Ship decisions in §11
REVIEW CORRECTIONS（rev 2）     = §4.2 R3 / R12, §4.3, §4.8, §6, §7, §8, §10, §11, §11.1
V-1 COVERAGE                   = 5 core routes only — NOT the whole BFF（§4.8）
FINAL STATUS                   = STOP
```

- Base: `origin/develop@38eca3f`. PRs #3317 and #3318 are open; their files are not on `develop`. This record
  stands alone and cites them by number.
- Evidence labels:
  - **Code** = verified in source on this base.
  - **Mock** = measured in Chromium 141.0.7390.37 against a local Node mock. The mock copies the BFF
    responses' shape; it is **not** the real Next.js app. Two sites were used: `localhost:<port>` and
    `127.0.0.1:<port>`; a second `localhost` port played the same-site attacker.
  - **Inference** = reasoned, not executed.
  - **PROD-UNVERIFIED** = depends on the production domain, the deployed build or the hosting proxy.
- **Correction to PR #3318 §7.1:** the billing checkout and portal routes have **no** origin check. They use
  `req.nextUrl.origin` only to build return URLs. `PATCH /api/users/me` has none either. The only route with an
  origin check is `DELETE /api/users/me`（Code）.

---

## 2. Affected route inventory

### 2.1 Which requests matter for CSRF

A cross-site request matters only if it does one of two things:

- **(W)** it **writes state into the victim's browser**: `Set-Cookie`;
- **(A)** it **uses the victim's ambient credentials**: cookies the browser attaches.

A request that does neither can be sent by the attacker directly, so the victim's browser adds nothing.

- **Mock:** cross-site form POSTs arrive **without** the `SameSite=Lax` cookies, so (A) is blocked cross-site.
- **Mock:** a **same-site** cross-origin form POST（a second port on `localhost`）arrives **with** those
  cookies, so (A) is open from same-site origins.
- **Mock（#3318 §7.2）:** Chromium applies `Set-Cookie` from the response to a cross-site top-level form POST, so
  (W) is open cross-site.

### 2.2 Inventory（all state-changing BFF handlers on this base）

| route | methods | origin check today | (W) writes cookies | (A) relies on cookies | class |
| --- | --- | --- | --- | --- | --- |
| `/api/auth/login` | POST | none | **sets `access_token`, `refresh_token`** | no | **V-1 core** |
| `/api/auth/register` | POST | none | no（signup sets no tokens） | no | **V-1 core** |
| `/api/auth/logout` | POST | none | **clears both tokens** | no | **V-1 core** |
| `/api/concierge/chat` | POST | none | **sets `concierge_anon_id`**; refresh writes tokens | anon cookie; tokens | **V-1 core** |
| `/api/compass/weekly` | POST | none | **relays backend `Set-Cookie`（anon id, `SameSite=None`）** | anon cookie; tokens | **V-1 core** |
| `/api/users/me` | DELETE | **`isAllowedOrigin`** | clears tokens on 204 | tokens | reference implementation |
| `/api/users/me` | PATCH | none | via refresh | tokens | B |
| `/api/favorites`, `/api/favorites/[id]`, `/api/favorites/preload` | POST, DELETE | none | relay + refresh | tokens | B |
| `/api/my/goshuins`, `/api/my/goshuins/[id]` | POST, PATCH, DELETE | none | relay + refresh | tokens | B |
| `/api/shrine-interactions`, `/api/shrine-submissions`, `/api/shrines/[id]/reflection`, `/api/shrines/[id]/visit` | POST | none | relay + refresh | tokens | B |
| `/api/compass/recommendations` | POST | none | relay + refresh | tokens / anon | B |
| `/api/billings/checkout`, `/api/billings/portal` | POST | none（correction above） | relay + refresh | tokens | B |
| `/api/shrines`, `/api/shrines/ingest`, `/api/my/shrines/ingest` | POST | none | **relays backend `Set-Cookie`** | tokens | B |
| `/api/my/shrines`, `/api/deep-dive/ask`, `/api/places/find`, `/api/places/resolve` | POST | none | no | forwarded cookies via `djFetch` | B / C |

- "relay + refresh"（Code）:
  - `bffFetchWithAuthFromReq` appends every upstream `Set-Cookie`（`lib/server/bffFetch.ts:22-31, 228-231`）.
  - When a `refresh_token` cookie is present, it also re-sets `access_token`（`bffFetch.ts:236`）.
  - Cross-site, the refresh cookie is not sent, so no refresh happens（Mock + Inference）.
- **Class B**: protected against **cross-site** CSRF by `SameSite=Lax` alone, but **not** against same-site
  origins. **Class C**: little CSRF value.
- **V-1 core** routes change browser state without needing any cookie. `SameSite` therefore does not protect
  them.

### 2.3 First-party callers（Code）

| route | callers | request shape |
| --- | --- | --- |
| login | `lib/auth/AuthProvider.tsx:181`, `lib/api/auth.ts:18` | `fetch` POST, `Content-Type: application/json` |
| register | `lib/api/auth.ts:72`（`SignupForm`） | `fetch` POST, JSON |
| logout | `AuthProvider.tsx:198`, `lib/api/auth.ts:38` | `fetch` POST, no body |
| chat | `lib/api/conciergeChat.ts:4`; `lib/api/concierge.ts:40`（axios, `baseURL: "/api"`） | POST, JSON |
| compass weekly | `features/compass/CompassClient.tsx:245` | `fetch` POST, JSON |

- No native HTML `<form method=POST>` targets any BFF route; there is no `action="/api…"` in `apps/web/src`
  （Code）.
- No server-side code calls these five routes. Mobile calls the backend directly, not the BFF（Code）.
- The login route also accepts `x-www-form-urlencoded` and `multipart/form-data`
  （`app/api/auth/login/route.ts:11-31`）. **No first-party caller and no test uses those** — the tests are
  `route.test.ts:66-118`（Code）.

---

## 3. CSRF threat model

| id | attack | route | today | evidence |
| --- | --- | --- | --- | --- |
| T1 | **login CSRF**: the attacker's credentials are posted from the attacker's site; the victim's browser now holds the attacker's session | login | open | Mock（#3318）+ Code |
| T2 | **login CSRF → handoff theft**: the victim, holding anonymous id A and a fresh handoff code, submits it while unknowingly logged in as the attacker. The consultation moves to the attacker's account | login + claim（future） | open once approach A ships | Inference（#3318 C-3） |
| T3 | **session replacement**: a logged-in victim is silently switched to the attacker's account; later saves, favourites and uploads land there | login | open | Inference from T1 |
| T4 | **forced logout** | logout | open | Mock |
| T5 | **forced loss of guest identity**, if logout also clears the anon cookie（#3317 P1-A） | logout | latent | Mock |
| T6 | **forced re-identification**: the anon cookie is replaced, guest threads detach, the quota resets | chat; compass only when no cookie exists | open on the mock; real routes not run | Mock + Inference |
| T7 | **write into the victim's anonymous identity**: if the victim's cookie was last written by compass weekly（`SameSite=None`）, it **is** sent cross-site, so a cross-site POST appends a consultation under the victim's A | chat, compass | not measured | Inference（Code: §2.2 compass relay） |
| T8 | **account creation from the victim's browser / IP** | register | open | Code（no check）; low impact |
| T9 | **same-site attacker**（a sibling origin on the same registrable domain）reaches Class B with cookies | Class B | depends on the production domain | Mock（same-site row）; **PROD-UNVERIFIED** |
| T10 | **cross-site JSON `fetch`** | all | blocked: a preflight `OPTIONS` was sent and the `POST` never was | Mock |
| T11 | **sandboxed or opaque origin**: the request arrives with `Origin: null` | all | depends on the check | Mock |

---

## 4. Proposed origin-validation contract（for approval; not implemented）

### 4.1 One shared helper

`apps/web/src/lib/server/requestOrigin.ts`（new）exports
`rejectCrossOriginRequest(req: NextRequest): NextResponse | null`. Every route in scope calls it **first**,
before reading the body, calling the backend or touching cookies:

```ts
const rejected = rejectCrossOriginRequest(req);
if (rejected) return rejected;
```

### 4.2 Decision table

`expected` is `req.nextUrl.origin`（see §4.4）. The first matching row wins.

| # | `Sec-Fetch-Site` | `Origin` | decision | reason |
| --- | --- | --- | --- | --- |
| R1 | `cross-site` | any | **reject** | browser-asserted cross-site |
| R2 | `same-site` | any | **reject** | sibling origin; blocks T9 |
| R3 | `none` | any | **decision S-9**: (a) evaluate `Origin` by R7–R11, or (b) reject | §4.2.1（rev 2） |
| R4 | `same-origin` | equals `expected` | allow | first-party shape（Mock） |
| R5 | `same-origin` | absent | allow | `Sec-Fetch-Site` is unforgeable by page script（forbidden header） |
| R6 | `same-origin` | present and ≠ `expected`, `null`, or malformed | **reject** | inconsistent; fail closed |
| R7 | absent | equals `expected` | allow | browsers without Fetch Metadata（older Safari / Firefox） |
| R8 | absent | `null` | **reject** | opaque origin（T11） |
| R9 | absent | malformed（`new URL` throws）or not `http(s)` | **reject** | — |
| R10 | absent | present and ≠ `expected` | **reject** | cross-origin |
| R11 | absent | absent | **decision S-1**: allow（as `users/me` today）or reject | see §4.3 |
| R12 | any other value（unknown token, several values） | any | **reject** | fail closed on values the spec does not define（rev 2） |

Header values are compared as the exact lower-case tokens `same-origin`, `same-site`, `cross-site`, `none`.

#### 4.2.1 `Sec-Fetch-Site: none`（rev 2 re-evaluation）

- **What produces it（Mock, Chromium 141.0.7390.37）:** only browser-initiated navigations without an
  initiator page. An address-bar-style `page.goto` GET and a later navigation of the same kind both arrived as
  `none` with no `Origin`.
- **What did not produce it（Mock）:**
  - The first submit of a same-origin form POST arrived as `same-origin`, with `Origin`.
  - **Reloading the POST result page re-sent the POST as `same-origin`, with `Origin`.**
  - Going back in history to the POST result sent no request.
- **First-party callers（Code, §2.3）:** every state-changing call is a `fetch` / axios POST. No page is the
  result of a form POST, so there is nothing to reload or resubmit.
- **Attacker reach（Inference）:** a page or script cannot make the browser label a request `none`; only the
  browser UI can. So `none` is **not a CSRF vector**. Rejecting it adds no protection today, and allowing it
  under R7–R11 removes none.
- **Risk of (b) reject:** a browser other than Chromium might label a reload or resubmission `none`
  （**NOT measured**: WebKit, Firefox）. A future native form post would then fail on reload.
- **Risk of (a) evaluate `Origin`:** none found. A `none` request without `Origin` falls to R11 and so
  follows S-1.
- Recommendation（not a decision）: (a). It keeps one rule — "`Origin` decides whenever Fetch Metadata does
  not say same-origin or cross" — and avoids a browser-specific false reject.

**Comparison rule:** compare the serialized origin exactly: scheme, host and port（`new URL(origin).origin`）.
There is no suffix, wildcard or case folding beyond what `URL` does. `Referer` is **not** used.

### 4.3 The "both headers absent" case（R11, decision S-1; rev 2: no recommendation）

**Who sends neither header:**

| sender | sends neither? | evidence |
| --- | --- | --- |
| first-party Web（Chromium 141） | no: every POST carried `Origin` and `same-origin` | Mock |
| a cross-site page in Chromium 141 | no: forms, `no-cors` fetch and sandboxed iframes all carried `Origin`（`null` for the sandbox）and `cross-site` | Mock |
| WebKit / Firefox / older browsers | not measured | NOT_VERIFIED |
| a browser with an extension or proxy that strips headers | possible | Inference |
| non-browser clients（curl, scripts, monitors, server-to-server） | yes | Inference |
| the repository's route unit tests | **yes**: they build requests without either header（list below） | Code |

**Allow vs reject:**

| aspect | allow | reject |
| --- | --- | --- |
| browser CSRF from another site | not opened, provided browsers always send one of the two headers on a cross-site POST（true in Chromium 141; other browsers NOT_VERIFIED） | closed even if some browser omits both |
| header-stripping extension or proxy | requests still work; the CSRF check is **silently off** for that user | that user's login, logout and chat fail with 403 |
| non-browser clients | work, but they hold no victim cookie, so there is no CSRF gain in blocking them（Inference） | blocked: curl-based smoke checks or monitors against these routes break（none found in the repository; manual practice NOT_VERIFIED, see below） |
| existing unit tests | unchanged | **16 cases need explicit headers added**（login 4, register 3, chat 6, compass weekly 3）, and one `users/me` case flips from allow to 403 |
| consistency | same as `DELETE /api/users/me` today | changes `users/me` behaviour too（R11 moves into the shared helper） |
| monitoring | the log line records "both absent"; the rate can be measured in report-only mode（S-4） | the same log line, now as rejections |

**Non-browser clients and test utilities（Code）:**

- Unit tests that construct requests without `Origin` or `Sec-Fetch-Site`:
  - `app/api/auth/login/route.test.ts`（4 cases）;
  - `app/api/auth/register/__tests__/route.test.ts`（3）;
  - `app/api/concierge/chat/__tests__/route.test.ts`（6）;
  - `app/api/compass/weekly/__tests__/route.test.ts`（3）;
  - `app/api/users/me/__tests__/route.test.ts`, whose case "Originが無い場合はBackend DELETEを呼ぶ" asserts
    R11 = allow.
- Playwright e2e: browser pages send the headers; chat is intercepted by `page.route` before the BFF
  （`e2e/fixtures/directionScenario.ts:109`）. No `APIRequestContext` POST to these routes exists.
- Scripts and CI: no script, Makefile target or workflow posts to these routes.
- Runbooks: `docs/ops/production-smoke-checklist.md:242` and `docs/ops/production-bff-hardening.md` list
  `/api/concierge/chat/` as a check, but do not say whether it is done in a browser or with curl
  （NOT_VERIFIED）.
- Mobile does not use the BFF.
- **Required either way:** the implementation PR adds a shared test helper that sets same-origin headers, so
  the route tests state their assumption explicitly instead of relying on R11.

This record does **not** choose S-1.

### 4.4 Determining `expected`

- `req.nextUrl.origin` is what `DELETE /api/users/me` uses today（Code）.
- **PROD-UNVERIFIED:** on Vercel, `req.nextUrl.origin` must equal the public origin the browser sees,
  including `https`, for every domain that serves the app（production domain, `www` / apex, preview URLs）.
- If it does not, every legitimate POST would be rejected. The options for S-3, which this record does
  **not** choose（rev 2）:
  - `req.nextUrl.origin` only;
  - `req.nextUrl.origin` plus an explicit allowlist from an env var.

  Report-only mode（S-4）can show which one is needed before enforcement.

### 4.5 Rejection response

- `403`, body `{"detail":"forbidden"}`, `Cache-Control: no-store`.
- **No `Set-Cookie` of any kind**, no backend call, no token refresh, no body read.
- One log line with route, the `Sec-Fetch-Site` value and whether `Origin` was absent, `null` or mismatched.
  The `Origin` value itself is **not** logged.
- **Logout rejected:** the cookies stay. The client must surface the failure（§9, S-5）.

### 4.6 Content type（defense in depth; decision S-2）

| route | proposal | why |
| --- | --- | --- |
| login | accept `application/json` only; `415` otherwise, with no cookie written | HTML forms cannot send JSON without a CORS preflight（T10）; no first-party caller uses forms（§2.3） |
| register | JSON only | same |
| chat, compass weekly | JSON only（body present） | the backend's DRF default parsers accept forms（#3318 §7.1） |
| logout | no body; origin check only | — |

A `text/plain` body that looks like JSON is rejected by the header check, not by parsing（Mock: cross-site
forms can send `text/plain`）.

### 4.7 Login and session replacement（T1–T3）

- The origin check closes T1 to T3 from other sites and from same-site origins（R1, R2）.
- A **same-origin** login while already logged in still replaces the session. That is legitimate and stays.
- The claim UI should name the account that will receive the consultation（#3318 C-3）. That is a G3 / UI item
  and not part of this PR.

### 4.8 What V-1 does **not** close（rev 2）

**Completing V-1 does not complete CSRF protection for the BFF.** V-1 covers the five core routes only.

**Class B residual-risk statement:**

> After V-1, the 16 Class B route files（§2.2, `PATCH /api/users/me` included）and the 4 B / C files still accept state-changing requests from any **same-site**
> origin that carries the victim's `SameSite=Lax` cookies. Measured on a Chromium mock: a same-site
> cross-origin form POST arrived with `Sec-Fetch-Site: same-site` and with the Lax cookies. Such an origin can
> add or delete favourites and goshuins, post shrine interactions, submissions, visits and reflections, call
> `PATCH /api/users/me`, and start billing checkout or portal sessions, all as the victim. Cross-site origins
> remain blocked by `SameSite=Lax`.
>
> Whether any same-site origin exists that an attacker can control depends on the production domain and its
> subdomains, which are **PROD-UNVERIFIED**（T9）. Until S-7 extends the helper to Class B, this exposure
> stays open.

Other things V-1 does not address:

| item | why it stays open |
| --- | --- |
| Class C routes（`/api/my/shrines`, `/api/deep-dive/ask`, `/api/places/*`） | not in scope; little CSRF value, but no check either |
| any new state-changing route | there is no global guard; each route must call the helper（S-10） |
| direct backend endpoints | S-6 |
| XSS or a compromised first-party origin | same-origin requests pass the check by design |
| subdomain takeover on the production domain | turns T9 into a reachable attack; depends on DNS hygiene（PROD-UNVERIFIED） |
| the chat BFF dropping other upstream `Set-Cookie` headers（#3318 RR-15） | not a CSRF issue; out of scope |

---

## 5. Direct backend routes（item 8）

| backend surface | CSRF exposure | needs its own protection? |
| --- | --- | --- |
| `/api/auth/jwt/create/`, `/refresh/` | return tokens in the **body**, set no cookie; a cross-site page cannot read the response | **no**（Inference） |
| JWT-authenticated views | `JWTAuthentication` reads the `Authorization` header, which a cross-site form cannot set | **no**（Code: `settings.py:302-305`） |
| `SessionAuthentication` views（Django admin session on the backend origin） | DRF enforces CSRF for session-authenticated requests; admin uses `CsrfViewMiddleware`. `CsrfExemptSessionAuthentication` exists but is **unused** | **no change**; keep it unused（Code: `temples/api/authentication.py`, repository grep） |
| `AllowAny` chat / compass weekly called **directly** | a cross-site form can make the victim's browser get or use a **backend-origin** anon cookie（`SameSite=None`）. #3318 found no Web flow that uses that jar, so it is inert for Web | **optional**: a backend `Sec-Fetch-Site` / JSON-only check as defense in depth（decision S-6） |
| Stripe webhook | `csrf_exempt`; relies on Stripe signature verification | out of scope |

**Conclusion:** V-1 is a BFF change. The backend needs no change for the Web threat. S-6 covers the
backend-origin jar and future clients.

---

## 6. Request / response test matrix（implementation PR）

Shared helper（`lib/server/__tests__/requestOrigin.test.ts`）: one case per row R1–R12, with R3 and R11 written
for both outcomes of S-9 and S-1 and only the chosen one kept, plus:

- upper-case scheme or host;
- default port（`:443`）;
- trailing slash;
- `Origin` with a path;
- non-`http(s)` scheme;
- two `Origin` values.

Per route（vitest, next to the existing tests）:

| case | login | register | logout | chat | compass weekly |
| --- | --- | --- | --- | --- | --- |
| same-origin `Origin` + `Sec-Fetch-Site: same-origin`, JSON | 200 path unchanged; existing tests green | same | cookies cleared as today | upstream called; existing cookie tests green | same |
| `Sec-Fetch-Site: cross-site`（any `Origin`） | **403**, no `Set-Cookie`, `djFetch` not called | 403, no upstream | **403, tokens not cleared** | 403, no upstream, **no anon cookie** | 403, no upstream, no relay |
| `Sec-Fetch-Site: same-site` | 403 | 403 | 403 | 403 | 403 |
| `Origin` mismatched, no `Sec-Fetch-Site` | 403 | 403 | 403 | 403 | 403 |
| `Origin: null` | 403 | 403 | 403 | 403 | 403 |
| malformed `Origin` | 403 | 403 | 403 | 403 | 403 |
| both headers absent | per S-1 | per S-1 | per S-1 | per S-1 | per S-1 |
| `Sec-Fetch-Site: none` + matching `Origin` | per S-9（a: allowed; b: 403） | same | same | same | same |
| `Sec-Fetch-Site: none`, no `Origin` | per S-9 then S-1 | same | same | same | same |
| unknown `Sec-Fetch-Site` value（R12） | 403 | 403 | 403 | 403 | 403 |
| form-encoded body, same-origin（S-2） | 415, no cookie | 415 | n/a | 415, no upstream | 415 |
| `text/plain` body shaped like JSON | 415 | 415 | n/a | 415 | 415 |
| rejection response | `Cache-Control: no-store`; body has no upstream detail | same | same | same | same |

Assertions on every rejection: `res.headers.getSetCookie()` is empty, the mocked `djFetch` /
`bffFetchWithAuthFromReq` was called 0 times, and the request body was not consumed.

**Regression set（rev 2）:**

- **Existing tests:** all 16 cases in the four route test files listed in §4.3, plus the 5 `users/me` cases,
  stay green after a shared `sameOriginHeaders()` test helper is added to their requests. Under S-1 = reject,
  the `users/me` "Origin absent" case is rewritten to expect 403.
- **Class B guard test:** one test per Class B handler（`PATCH /api/users/me` included）asserts that it does
  **not** call the helper yet. It is deleted when S-7 lands, so coverage cannot be assumed by accident.
- **Inventory guard（S-10）:** a test lists every exported POST / PUT / PATCH / DELETE handler under
  `app/api/**` and fails when a new one is neither in the V-1 list nor in the documented Class B / C lists.

Frontend（vitest）:

- `AuthProvider.logout` and `lib/api/auth.ts` `logout`: on a non-2xx response, the UI does **not** switch to
  guest silently（S-5）.
- `SignupForm` / login page: a 403 / 415 shows the existing generic error.

E2E（Playwright, **non-production** deployment only）:

- First-party login, logout, register, chat and compass weekly still work in Chromium, WebKit and Firefox.
- The #3318 §7.2 attack page against the real routes now gets 403 and the jar is unchanged.

---

## 7. Compatibility assessment

| area | effect | evidence |
| --- | --- | --- |
| first-party Web requests | unchanged: they send the own `Origin` and `Sec-Fetch-Site: same-origin` | Mock + Code（§2.3） |
| `Referrer-Policy` | the repo sets none. In Chromium 141 a same-origin POST kept its real `Origin` even under `Referrer-Policy: no-referrer` | Code + Mock; **other browsers not measured** |
| login via form-encoded body | stops working if S-2 is adopted; no first-party caller or test uses it | Code |
| non-browser tools（curl, scripts, monitors） | unaffected if S-1 = allow; blocked if S-1 = reject. None found in the repository; manual runbook practice NOT_VERIFIED | Code + Inference |
| existing route unit tests | 16 cases build requests without either header; they need explicit headers under S-1 = reject, and are cleaner with them either way | Code（§4.3） |
| reload / resubmission | Chromium 141 re-sends a reloaded form POST as `same-origin`; no first-party page is a POST result | Mock + Code（§4.2.1） |
| mobile app | unaffected（talks to the backend, not the BFF） | Code |
| preview deployments | unaffected if `req.nextUrl.origin` equals the preview URL | **PROD-UNVERIFIED**（§4.4） |
| browser extensions that strip `Origin` | possible false 403 if they also strip Fetch Metadata and S-1 = reject | Inference |
| e2e fixtures | `page.route` intercepts chat before the BFF; unaffected | Code: `e2e/fixtures/directionScenario.ts:109` |
| `DELETE /api/users/me` | moves to the shared helper. That **adds** R1, R2, R12 and the S-9 outcome to it; same-origin behaviour unchanged | Code |

---

## 8. Implementation PR scope（after approval）

**In scope**

1. `lib/server/requestOrigin.ts`: the helper and its tests（§4.1, §4.2, §6）.
2. Apply it first in: `app/api/auth/login/route.ts`, `auth/register/route.ts`, `auth/logout/route.ts`,
   `concierge/chat/route.ts`, `compass/weekly/route.ts`.
3. Replace the local `isAllowedOrigin` in `app/api/users/me/route.ts`（DELETE）with the helper.
4. S-2 content-type checks, if approved.
5. S-5 logout failure handling in `AuthProvider.tsx` and `lib/api/auth.ts`, if approved.
6. Optional rollout switch for report-only mode（S-4）.
7. The `sameOriginHeaders()` test helper, the existing-test updates, and the Class B and inventory guard tests
   （§6 regression set）.

**Out of scope — so V-1 does not close BFF-wide CSRF（§4.8）**

- Class B routes（decision S-7）: the same-site exposure stays open.
- Any backend change（S-6）.
- Cookie attributes, the token lifetime, the RR-15 drop of relayed `Set-Cookie`, P1 / P2, the handoff grant,
  mobile（MF-1）, migrations.

**Size estimate（inference）:** about 1 new module, 6 route edits, 1–2 client edits, and about 60 test cases.

---

## 9. User-facing behaviour changes that need Mother Ship approval

| id | change | who notices |
| --- | --- | --- |
| U-1 | a logout that is rejected or fails shows an error, and the user stays logged in, instead of the UI silently showing "guest" while the cookies remain（S-5） | a user whose logout fails |
| U-2 | login and register accept JSON only（S-2） | only non-browser callers; no first-party caller |
| U-3 | requests from sibling same-site origins are refused（R2） | any future first-party subdomain that posts to the BFF |
| U-4 | requests with neither header refused, if S-1 = reject | scripts / tools |
| U-5 | report-only period: no blocking for a set time, logging only（S-4） | nobody; delays protection |

---

## 10. Facts, mock results and unverified conditions

| kind | items |
| --- | --- |
| **Code facts** | §1 correction; §2.2 inventory; §2.3 callers and form support; no `Referrer-Policy` set; `CsrfExemptSessionAuthentication` unused; JWT auth by header |
| **Chromium mock results**（141.0.7390.37, local） | rev 2: `Sec-Fetch-Site: none` only on address-bar-style GET navigations; a reloaded form POST re-sent as `same-origin` with `Origin`; history back sent no request. Earlier: first-party POSTs carry `Origin` + `Sec-Fetch-Site: same-origin`; cross-site forms（urlencoded / text/plain / multipart）carry the attacker `Origin` + `cross-site` and no Lax cookies; a cross-site JSON `fetch` stops at preflight; same-site cross-origin carries `same-site` **and** the Lax cookies; a sandboxed iframe sends `Origin: null`; `no-referrer` did not null a same-origin `Origin`; #3318: `Set-Cookie` applies on cross-site top-level POSTs |
| **NOT measured** | WebKit and Firefox for every row above, including `none` on reload / resubmission and the "both headers absent" case |
| **PROD-UNVERIFIED** | the production domain and any sibling subdomains（T9）; `req.nextUrl.origin` on Vercel for every serving domain（§4.4）; production response headers（`Referrer-Policy`）; WebKit / Firefox behaviour; the real routes' behaviour under attack（E2E on non-production only） |

---

## 11. Remaining Mother Ship decisions

| id | decision | options | recommendation（not a decision） |
| --- | --- | --- | --- |
| S-1 | both `Origin` and `Sec-Fetch-Site` absent | allow / reject | **none given**（rev 2）; trade-offs in §4.3 |
| S-2 | JSON-only bodies on login, register, chat, compass weekly | yes / no | yes（U-2） |
| S-3 | how `expected` is derived | `req.nextUrl.origin` only / plus an env allowlist | **none given**（rev 2）; depends on S-8 results（§4.4） |
| S-4 | rollout | enforce at once / report-only first（length?） | report-only for a short period on preview, then enforce |
| S-5 | logout failure UX（U-1） | show an error and keep the session / clear the client state anyway | show the error |
| S-6 | backend defense in depth for direct `AllowAny` anon-cookie endpoints | now / later / never | later, with MF-1 |
| S-7 | extend the helper to Class B routes | in the V-1 PR / follow-up PR / not at all | follow-up PR after the production domain is known（T9）; until then the §4.8 residual risk is accepted **explicitly** or not at all |
| S-8 | who verifies §10 PROD-UNVERIFIED items, and on which non-production deployment | — | required before enforce mode |
| S-9 | `Sec-Fetch-Site: none`（R3） | (a) evaluate `Origin` / (b) reject | (a)（§4.2.1） |
| S-10 | inventory guard test for new state-changing routes | yes / no | yes |
| S-11 | accept the Class B same-site residual risk until S-7（§4.8） | accept with a date / block V-1 until S-7 | open |
| V-1 | approve this contract as the implementation PR scope（§8） | yes / no | — |

### 11.1 Implementation blockers（rev 2）

The implementation PR must not start until all of these are resolved:

1. **S-1** and **S-3** decided by Mother Ship. This record gives no recommendation for either.
2. **S-9** decided（R3）.
3. **S-8**: production-dependent checks are done on a non-production deployment:
   - `req.nextUrl.origin` equals the browser-visible origin on every serving domain;
   - the production domain and its subdomains are known（T9）.
4. **S-11**: the Class B residual risk is accepted, or S-7 is pulled into scope.
5. **V-1** approves §8 as the scope.

These are **not** blockers for starting implementation, but they shape it:

- S-2（JSON only）, S-4（rollout）, S-5（logout UX）: each adds or removes a step in §8.
- S-6（backend）and S-10（inventory guard）.

---

## 12. Not done

```text
runtime / BFF / frontend / backend / mobile code   UNCHANGED
auth tokens / cookies                              UNCHANGED
models / migrations / database                     UNCHANGED
P1 / P2                                            NOT IMPLEMENTED
production                                         NOT CONTACTED; no offensive tests
scratch tooling（Chromium mock）                    outside the repository; not committed
```
