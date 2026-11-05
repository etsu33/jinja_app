# Anonymous Session Boundary — Residual Risk Verification（2026-10-23）

## 1. Status

```text
SCOPE                          = read-only investigation + documentation
VERIFIES                       = assumptions of PR #3317（logout / recovery contract, open, not merged）
P1 / P2                        = NOT SELECTED（Mother Ship, G4）
runtime / BFF / cookies / auth = UNCHANGED
models / migrations / DB       = UNCHANGED
production                     = NOT MODIFIED; configuration read attempt refused（403, §2.3）
PRODUCTION_SECURITY_E2E        = OPEN
FINAL STATUS                   = STOP — awaiting Mother Ship
```

- Base: `origin/develop@38eca3f`. PR #3317 is open at `5c3be2b`; its file is not on `develop`, so this record
  does not edit it. §11 lists every #3317 statement that this record confirms, narrows or corrects.
- Labels:
  - **Fact（code）** = verified by reading source on this base.
  - **Fact（local run）** = reproduced locally in a throwaway scratch directory; the tool and version are named.
  - **Inference** = reasoned, not executed.
  - **NOT_VERIFIED** = depends on production configuration, a deployed build or a browser / client this record
    could not observe.
- No cookie value, token, code, consultation content, credential or environment value is recorded here.

---

## 2. Web-to-backend paths and the backend-origin cookie（item 1, item 2）

### 2.1 Every path by which a browser could reach the backend origin

| path | reaches backend origin from the browser? | evidence |
| --- | --- | --- |
| BFF route handlers（`app/api/**`）via `djFetch` | **no**: server-to-server. The BFF forwards the browser's **Web-origin** `Cookie` header upstream | Fact（code）: `lib/server/backend.ts:5-8, 40-63` |
| client axios `lib/api/client.ts` | **no**: `baseURL: "/api"`, hard-coded | Fact（code）: `lib/api/client.ts:5-8` |
| client helpers `lib/api/http.ts` | **no**: built on `client.ts`; the `NEXT_PUBLIC_API_BASE` read at line 60 is in `__resolveUrlForTest` only | Fact（code）: `lib/api/http.ts:1-30, 59-60` |
| `lib/api.ts`（axios with `NEXT_PUBLIC_API_BASE`, `withCredentials: true`） | **no importer** in `apps/web/src`, so it is not executed | Fact（code）: repository grep for every import form |
| `lib/conciergeChat.ts` | uses `lib/api/client`（"/api"）; no importer | Fact（code） |
| other `NEXT_PUBLIC_*` URLs | `NEXT_PUBLIC_BASE_URL`, `APP_URL`, `SITE_URL` point at the Web origin; `NEXT_PUBLIC_API_BASE_URL` is read in a `.server.ts` module only | Fact（code）: `app/g/[username]/page.tsx:30`, `lib/url.ts:21`, `lib/api/shrines.server.ts:15` |
| Next.js `rewrites()` / `middleware.ts` | `rewrites()` returns `[]`; middleware only guards `/mypage` | Fact（code）: `apps/web/next.config.ts`, `apps/web/middleware.ts` |
| images from the backend `/media/**` | GET for static files; never sets the anon cookie | Fact（code）: `next.config.ts` `remotePatterns` |
| a person or page navigating to the backend API directly | possible; the backend would set its own `SameSite=None` copy | Inference |
| mobile app | calls the backend origin directly（no BFF） | Fact（code）: `apps/mobile/lib/http.ts:2-3` |

**Conclusion（code level）:** no Web application flow causes the browser to store a backend-origin
`concierge_anon_id`. If such a copy exists, because someone opened the backend API directly, the BFF never
sends it, because the BFF forwards only the Web-origin jar. So it is inert for Web flows（inference）. This
narrows #3317 L-5 / RR-7 / D-7（§11）.

### 2.2 How the Web-origin cookie is actually written

| writer | what the browser receives | evidence |
| --- | --- | --- |
| BFF `/api/concierge/chat`, anonymous plan | the backend sends **both** `Set-Cookie: concierge_anon_id …; SameSite=None; Secure` and the body value `_anon_cookie_value`. The BFF appends the upstream `Set-Cookie`, then calls `res.cookies.set(…, sameSite: "lax")` | Fact（code）: `api_views_concierge.py:640-669, 1005-1026`; `app/api/concierge/chat/route.ts:61-84, 34-48, 158-163` |
| — result in Next.js 16.3.8 | `res.cookies.set` **replaces every previously appended `Set-Cookie`**. The browser receives only the `SameSite=Lax` copy, and any other upstream cookie in that response is dropped as well | **Fact（local run）**: `next@16.3.8`（the version pinned in `apps/web/package.json`）, `NextResponse` with the route's call order |
| BFF `/api/concierge/chat`, authenticated plans | no body value, so `cookies.set` is not called; the backend sends no anon cookie for these plans | Fact（code + local run） |
| BFF `/api/compass/weekly` | relays the backend `Set-Cookie` unchanged, so the Web-origin cookie is written with `SameSite=None; Secure`. The backend sets it **only when the request had no cookie** | Fact（code）: `app/api/compass/weekly/route.ts:7-22`, `lib/server/bffFetch.ts:22-31, 228-231`; `api_views_compass_weekly.py:145-154` |

- **Inference:** both writers produce one host-only cookie, `concierge_anon_id`, with `Path=/` on the Web
  origin. The `SameSite` attribute is not part of a cookie's identity, so one deletion with the same name and
  path removes it, whichever writer was last.
- **Side finding（Fact, local run）:** the chat route silently drops every other `Set-Cookie` from the backend
  on anonymous responses. The backend sets none today, so there is no impact now. It is a trap for any future
  backend cookie.

### 2.3 Production configuration

| item | status |
| --- | --- |
| Vercel project environment variables（names / targets） | **NOT_VERIFIED**: read-only listing refused with **403 forbidden** for this session's Vercel access. No retry, no workaround |
| whether the deployed Web build equals `develop` code | NOT_VERIFIED |
| backend `DEBUG`（decides `SameSite=None; Secure` vs `Lax`）, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `DJANGO_ORIGIN` | NOT_VERIFIED（environment-driven: `settings.py:433-444`, `lib/server/backend.ts:5-8`） |
| actual `Set-Cookie` attributes in production responses | NOT_VERIFIED（needs production E2E, §9） |

The §2.1 conclusion does **not** depend on `NEXT_PUBLIC_API_BASE`, because no executed client code reads it.
It depends on the deployed build matching `develop`.

---

## 3. Does clearing the Web-origin cookie isolate users on a shared browser?（item 3）

**Answer: it is necessary but not sufficient.** It removes the identity that every Web read and write uses
（§2.1）. These gaps remain:

| # | gap | evidence |
| --- | --- | --- |
| I-1 | **replay**: a copy of the value taken earlier stays valid server-side（§4） | Fact（code + local run） |
| I-2 | **other tabs** keep in-memory state and their own `sessionStorage` snapshot until reload. `AuthProvider.logout` clears only the calling tab | Fact（code）: `lib/auth/AuthProvider.tsx:197-213`; `sessionStorage` is per tab |
| I-3 | **back / forward cache and history** may re-display a page rendered before logout without a new request | Inference; NOT_VERIFIED（browser-level） |
| I-4 | **logout that fails server-side still looks successful**: `AuthProvider.logout` does not check the response status before switching the UI to guest. If the BFF response is lost or 5xx, the cookies may remain while the UI says "logged out" | Fact（code）: `AuthProvider.tsx:197-201`; consequence inference |
| I-5 | **guest → guest with no login**: there is no logout to hook | #3317 RR-1 |
| I-6 | **forced clearing by a third party**（§7）: the same mechanism that isolates can be triggered cross-site | Fact（local run, Chromium mock） |
| I-7 | mobile is untouched by any Web cookie change | §8 |

---

## 4. Signed-cookie replay, expiry and reissuance（item 4）

| # | finding | evidence |
| --- | --- | --- |
| E-1 | `signing.dumps` embeds a timestamp; `loads(…, max_age=None)` ignores it | Fact（local run, Django 5.2.16） |
| E-2 | Two signatures of the same A, made at different times, are **both** accepted with `max_age=None`. Reissuing the cookie does not invalidate older copies | Fact（local run） |
| E-3 | With a `max_age`, the older signature is rejected first（`SignatureExpired`）and the newer one is still accepted | Fact（local run） |
| E-4 | The chat endpoint re-signs and re-sets the cookie on **every** anonymous response. Compass weekly sets it only when absent | Fact（code）: §2.2 |
| E-5 | So with SR-1（`max_age = 90 d`）: a copy that is **used** is re-signed and handed back to its user, so it never ages out. Only idle copies expire | Inference from E-3 + E-4 |
| E-6 | If chat stopped re-signing when a valid cookie is present（as compass does）, SR-1 would become a hard 90-day lifetime from first issuance, including for the legitimate guest | Inference |
| E-7 | `SECRET_KEY` rotation invalidates every anon cookie and every handoff grant binding at once（fail closed）; no `SECRET_KEY_FALLBACKS` is set | Grant schema proposal §12 |

**Consequence:** reissuance is **not** rotation. Rotation means a new A. Reissuance re-signs the same A and
extends its life. Only server-side state（#3317 SR-2 / SR-5）or a hard signature lifetime（E-6）bounds an
actively replayed copy.

---

## 5. Logout-based rotation vs an explicit "End anonymous session"（item 5）

| | logout-based clearing（#3317 P1-A） | explicit "End anonymous session"（EAS） | both（EAS, also run at logout） |
| --- | --- | --- | --- |
| trigger | account logout, account deletion | a guest-visible control, e.g. on `/concierge` | either |
| covers guest → guest（I-5 / RR-1） | **no** | **yes**, if the departing guest uses it | yes |
| covers account switch on a shared browser | yes | only if pressed | yes |
| needs an account | yes | no | — |
| user awareness | implicit | explicit; the copy can say "this browser's guest consultations will no longer be shown" | — |
| server-side effect | none（cookie only）unless SR-5 | same; it could also call a backend operation（e.g. SR-5 for open grants）, which reopens G1 | same |
| CSRF exposure | logout route lacks an origin check（§7） | a new route; must have an origin check from the start | — |
| quota effect | fresh anonymous quota（§6） | fresh quota **on demand**（§6） | — |
| discoverability risk | none（logout exists） | users may never press it | — |
| mobile | no logout exists（§8） | would need a native control and backend support | — |
| migration | none | none for cookie-only | none |

**Inference:** EAS is the only mechanism that reaches I-5. It does not replace logout clearing, because a
person who logs in and then out never sees an EAS prompt. Neither option is selected here（decision V-2）.

---

## 6. Anonymous quota（item 6）

| # | finding | evidence |
| --- | --- | --- |
| Q-1 | The anonymous concierge quota is **3**; `CONCIERGE_DEMO_LIMIT` can override it | Fact（code）: `temples/services/quota_policy.py:7-11, 29-47` |
| Q-2 | `FeatureUsage` rows for scope `anonymous` are keyed on A | Fact（code）: `quota_service.py:30-54` |
| Q-3 | A new A starts with a fresh quota. Clearing cookies or opening a private window already does this today, so rotation adds a one-click path, not a new class of bypass | Inference |
| Q-4 | EAS turns the reset into a visible button. If the anonymous limit is a conversion lever, EAS weakens it more than logout clearing does | Inference |
| Q-5 | On a shared browser **without** rotation, the next guest inherits the previous guest's remaining count and can infer prior use | Inference |
| Q-6 | §7: a cross-site POST that makes the chat endpoint issue a new A also resets the victim's quota and detaches their guest threads | Inference + Fact（local run, mock） |
| Q-7 | MF-1（§8）: if the native app does not keep the cookie, every mobile chat gets a fresh A, so the anonymous quota never applies on mobile | Inference; NOT_VERIFIED |

---

## 7. Logout CSRF and cross-origin cookie changes（item 7）

### 7.1 Origin checks today

| BFF route | origin check | accepts a form body | evidence |
| --- | --- | --- | --- |
| `POST /api/auth/logout` | **none** | — | Fact（code）: `app/api/auth/logout/route.ts:6-12` |
| `POST /api/auth/login` | **none** | **yes**: JSON, `x-www-form-urlencoded`, `multipart/form-data` | Fact（code）: `app/api/auth/login/route.ts:11-31` |
| `POST /api/auth/register` | none | — | Fact（code） |
| `POST /api/concierge/chat` | none | forwards any content type; DRF's default parsers accept forms | Fact（code）: `chat/route.ts:86-103`; `settings.py:302`（no parser override） |
| `POST /api/compass/weekly` | none | relays the body | Fact（code） |
| `DELETE /api/users/me`, billing checkout / portal | `isAllowedOrigin` | — | Fact（code） |
| global middleware | none for `/api/**` | — | Fact（code）: `apps/web/middleware.ts` |

### 7.2 Browser behaviour, measured on a mock（Chromium 141.0.7390.37）

Setup: a local Node mock that returns the **same `Set-Cookie` shapes** as the BFF routes. It is not the real
Next.js app. The app ran on `http://localhost:4101`; the attacker page on `http://127.0.0.1:4102`, a different
site. The victim's cookies were seeded as `HttpOnly; SameSite=Lax; Path=/`. Two identical runs.

| attack | victim cookies after | Fact（local run） |
| --- | --- | --- |
| cross-site **top-level form POST** to logout | `access_token`, `refresh_token` **deleted**; anon cookie kept | logout CSRF works |
| cross-site `fetch(no-cors)` to logout | unchanged | blocked |
| cross-site form POST to a P1-A logout that also clears the anon cookie | **all three deleted** | forced loss of the guest identity |
| cross-site form POST to login with the attacker's credentials | tokens **replaced by the attacker's** | **login CSRF works** |
| cross-site `fetch(no-cors)` to login | unchanged | blocked |
| cross-site form POST to a chat-shaped endpoint that issues an id when none is sent | the Lax anon cookie is **not sent**, so a new id is issued and **replaces** the victim's | forced re-identification |

- `SameSite=Lax` stops cookies being **sent** on cross-site POSTs. Chromium still **applies** `Set-Cookie` from
  the response to a cross-site top-level navigation. Deletions and new values both take effect.
- Not measured: Safari / WebKit, Firefox, Secure cookies over HTTPS, and the real Next.js routes.

### 7.3 Consequences

| id | consequence | basis |
| --- | --- | --- |
| C-1 | anyone can log a victim out from another site（low severity today） | Fact（local run）+ Fact（code, no origin check） |
| C-2 | under P1-A without an origin check, the same request also destroys the victim's guest access to their consultations | Fact（local run, mock） |
| C-3 | **login CSRF → handoff theft**: the attacker logs the victim's browser into the attacker's account. The victim, still holding A and a freshly shown handoff code, submits it in the claim form. Claim proof K1 + K4 + K3 is satisfied, and the consultation moves into the attacker's account | Inference from C-1 mechanics + approach A claim（grant schema §6）; not executed against real routes |
| C-4 | forced re-identification through chat or compass: the victim's guest threads are detached from the browser and the quota resets | Inference; the real chat path with a form body is NOT_VERIFIED |
| C-5 | nothing today **sets** a chosen A on a victim. The attacker cannot pick the value, which is backend-signed. Fixation of a known A is therefore not shown | Inference |

**Required for any P1 option（proposal）:** same-origin enforcement（`isAllowedOrigin` or `Sec-Fetch-Site`）on
login, register, logout, chat and compass weekly. The claim UI should show the account it will save into.

---

## 8. Separate issue MF-1 — mobile concierge chat is sent unauthenticated（item 8）

Recorded as a **separate security issue**. Mobile code is not changed.

| # | fact | evidence |
| --- | --- | --- |
| M-1 | `fetchConciergeRecommendations` calls `post("/concierge/chat/")`; `post` sends no `Authorization` header | Fact（code）: `apps/mobile/app/concierge/index.tsx:447`; `apps/mobile/lib/http.ts:144-151` |
| M-2 | `postAuth` exists and is not used for chat | Fact（code）: `apps/mobile/lib/http.ts:160` |
| M-3 | there is no mobile logout: `clearTokens` has no non-test caller | Fact（code）: `apps/mobile/lib/authTokens.ts:27-31` |
| M-4 | history reads user-owned threads only（`getAuth("/concierge-threads/")`） | Fact（code）: `apps/mobile/lib/consultationHistory.ts:61` |

Security implications（inference; each depends on native cookie handling, which is NOT_VERIFIED）:

- A logged-in user's mobile consultations are stored as anonymous threads, outside their account, under
  guest retention, and absent from their history.
- Premium or free entitlements are not applied; the anonymous plan and quota are.
- If the native stack **keeps** the backend cookie: on a shared phone, every account in the app shares one
  anonymous identity, and its threads are reachable to all of them through the anonymous path.
- If it does **not** keep it: each chat creates a new A, the anonymous quota never binds（Q-7）, and orphan
  threads accumulate until retention.
- Any Web P1 / P2 choice leaves mobile unchanged.

Decision V-7: track MF-1 as its own issue and PR, outside G1–G4.

---

## 9. Assumptions that need browser-level or production E2E verification（item 9）

| # | assumption | why it is open | how to verify（QA accounts, test data only） |
| --- | --- | --- | --- |
| E2E-1 | the deployed Web build matches `develop`（§2.1） | Vercel access 403 | deployment metadata by the owner |
| E2E-2 | production `Set-Cookie` attributes for chat and compass weekly | env-driven `DEBUG`; relay path | DevTools on production, guest session; record attributes only, never values |
| E2E-3 | no backend-origin `concierge_anon_id` appears during normal Web use | §2.1 is code-level | production guest flow; inspect the backend-origin jar |
| E2E-4 | logout CSRF and login CSRF on the real HTTPS routes（§7.2） | mock only, Chromium only | attacker page on another site; Chromium, WebKit, Firefox |
| E2E-5 | forced re-identification through the real chat / compass routes with a form body | real parser path not run | same harness, guest victim |
| E2E-6 | bfcache / back button after logout（I-3） | browser-level | Playwright: logout, then `goBack()` |
| E2E-7 | failed logout UX（I-4） | network failure path | Playwright route interception returning 5xx |
| E2E-8 | native cookie persistence（MF-1, Q-7） | iOS / Android runtime | device test of two consecutive chats |
| E2E-9 | Safari ITP and Firefox Total Cookie Protection effects on the Lax and None writers | browser policy | cross-browser run |

---

## 10. Residual risks（after this verification）

| id | risk | change vs #3317 |
| --- | --- | --- |
| RR-1 | guest → guest exposure without login | unchanged; EAS is the only mitigation（§5） |
| RR-2 | replayed copies of A stay valid; reissuance extends them（E-2, E-5） | sharpened |
| RR-3 | copied cookie + copied code claims within 30 min | unchanged |
| RR-7 | backend-origin cookie copy | **downgraded**: no Web flow creates or sends it（code level）; E2E-3 open |
| RR-8 | forced logout / forced identity loss cross-site | **confirmed** on a Chromium mock（§7.2） |
| RR-11 | **login CSRF → handoff theft**（C-3） | **new** |
| RR-12 | forced re-identification via chat / compass（C-4） | **new**; real route NOT_VERIFIED |
| RR-13 | logout UI reports success on a failed logout（I-4） | **new** |
| RR-14 | other tabs / bfcache show prior content after logout（I-2, I-3） | extended |
| RR-15 | chat BFF drops unrelated upstream `Set-Cookie` headers | **new**, no current impact |
| MF-1 | mobile chat unauthenticated（§8） | now a separate issue |

---

## 11. Threat-model update for PR #3317

| #3317 statement | status after this record |
| --- | --- |
| L-3: chat and compass weekly re-sign the cookie on use | **corrected**: chat re-signs every anonymous response; compass sets it only when absent（E-4） |
| L-4: the BFF copies the body value into a Lax cookie | **confirmed and extended**: that write also discards the upstream `SameSite=None` `Set-Cookie`（Next 16.3.8）. Compass writes the Web-origin cookie as `SameSite=None`（§2.2） |
| L-5 / D-7: a backend-origin copy may exist, depending on `NEXT_PUBLIC_API_BASE` | **narrowed**: no executed client code reads `NEXT_PUBLIC_API_BASE`; no Web flow stores or forwards a backend-origin copy. The deployed build is still unverified（E2E-1, E2E-3） |
| L-6 / RR-8: logout has no origin check; effect NOT_VERIFIED | **confirmed（Chromium mock）**, and the same gap exists on login, register, chat and compass（§7） |
| SR-1: bounds only idle copies | **confirmed**（E-3, E-5）; E-6 adds the "stop re-signing" variant |
| §8 contract: "UI says logout ends guest consultations" | **needs** I-4 handling and the origin check before it is safe |
| §12 RR list | add RR-11 to RR-15 |
| §16 decisions | add V-1 to V-9（§13）; D-7 can close after E2E-1 / E2E-3 |

---

## 12. Test requirements（for a later implementation PR; nothing implemented）

**BFF（vitest）**

- Every state-changing auth or concierge route rejects a cross-origin `Origin` / `Sec-Fetch-Site: cross-site`
  with 403 and **sets no cookie**: login, register, logout, chat, compass weekly.
- Chat anonymous response: exactly one `concierge_anon_id` `Set-Cookie`, with the intended attributes. Any
  other upstream `Set-Cookie` is preserved, or is dropped by an explicit rule（RR-15）.
- Logout（if P1-A）: tokens and anon cookie cleared in one response.

**Web（vitest / Playwright）**

- Logout with a 5xx or lost response leaves the UI in a state that does not claim success（I-4）.
- After logout: `goBack()` shows no prior consultation content（I-3）; a second tab after reload shows none（I-2）.
- The claim form shows the logged-in account before submission（C-3）.

**Backend（pytest, PostgreSQL）**

- With SR-1: a signature older than the limit → guest reads 404; a fresh re-signature of the same A → 200
  （documents E-2 / E-5）.
- An anonymous request without a cookie gets a new A and a fresh quota（Q-3 baseline）.

**Cross-browser E2E** — E2E-4 to E2E-6 and E2E-9 on Chromium, WebKit and Firefox, against a non-production
deployment first.

**Mobile** — E2E-8 when MF-1 is scheduled.

---

## 13. Mother Ship decision table

New decisions from this record（V-*）, plus the #3317 decisions they affect. None is decided here.

| id | decision | options | note |
| --- | --- | --- | --- |
| V-1 | same-origin enforcement on login, register, logout, chat, compass weekly | required before any P1 option / separate hardening PR now | RR-8, RR-11, RR-12 exist **today**, independent of P1 |
| V-2 | "End anonymous session" | none / standalone / standalone and at logout | only mitigation of RR-1 |
| V-3 | quota stance when A is cleared | accept the reset / key the anonymous quota on something else | Q-3, Q-4 |
| V-4 | chat cookie re-signing | keep re-signing every response（SR-1 bounds idle copies only）/ re-sign only when absent（hard lifetime, E-6） | interacts with D-6 |
| V-5 | logout failure behaviour（I-4） | show an error and keep the session / always clear the client state | — |
| V-6 | post-logout caching（I-3） | `no-store` on concierge pages / accept | after E2E-6 |
| V-7 | MF-1 mobile unauthenticated chat | separate issue and PR / bundle with mobile handoff | outside G1–G4 |
| V-8 | production and cross-browser E2E（§9） | who runs it, with which QA accounts, on which deployment | required to close E2E-1 to E2E-9 |
| V-9 | production configuration access | owner confirms the deployed commit and the env-driven settings（§2.3） | Vercel listing returned 403 |
| D-1 / D-2 | P1 / P2（#3317） | unchanged | V-1, V-2 inform them |
| D-6 | SR-1 | unchanged | see V-4 |
| D-7 | backend-origin cookie | narrowed（§11） | close after E2E-1 / E2E-3 |

---

## 14. Not done

```text
runtime / backend / BFF / frontend / mobile code   UNCHANGED
cookies / auth configuration                       UNCHANGED
models / migrations / database                     UNCHANGED
production                                         NOT MODIFIED（config read refused 403; no requests sent）
P1 / P2                                            NOT SELECTED
scratch tooling                                    outside the repository; not committed
PRODUCTION_SECURITY_E2E                            OPEN
```
