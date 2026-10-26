# FU-1: SSR Anonymous Client Identity — Trust Boundary Audit and Design Options（2026-10-26）

## 1. Status

```text
RECORD TYPE        = design + audit（documentation only）
BASELINE           = origin/develop@5902aa5（includes PR #3354 / #3355 / #3356）
SOURCE FINDING     = F-2 of docs/audit/bff-anonymous-identity-paths-audit-2026-10-26.md（FU-1 there）
CODE / ENV CHANGES = NONE（no runtime, signing, throttle, auth, CSRF or environment change）
PRODUCTION         = NOT ACCESSED; no traffic; no secret read
ARCHITECTURE       = NOT SELECTED — Options A / B / C are compared for Mother Ship（§11, §12）
FINAL STATUS       = STOP at the PR（§12）
```

Evidence levels used below: **Code** = read in the current repository at the baseline, with file:line;
**Lib** = read in the pinned dependency source（DRF 3.17.2, simplejwt 5.5.1 wheels）; **Inferred** = follows from Code
plus a platform behaviour that was not measured; **Hypothesis** = a runtime claim that needs production evidence.

---

## 2. Executive summary

1. **All ten SSR call sites from PR #3356 are confirmed in the current code**（`pnpm audit:bff-identity:check` = no
   drift）. Not all of them reach the Backend: one is a 501 stub, and four are rejected by the Backend for anonymous
   visitors **before** any throttle runs. For anonymous visitors, **six** paths consume anonymous throttle buckets keyed
   by the BFF's incoming identity（§3）.
2. **The browser's address is available to SSR, but is lost on the internal hop.** SSR can read Vercel's
   `x-forwarded-for` through `headers()`. `getShrineDetailServer` already does this on its direct path. The internal
   HTTP call carries only `cookie`（sometimes `authorization`）. The BFF route then signs whatever address its own request
   came from: the Vercel function egress（Inferred）.
3. **Concrete consequence（Code）**: for an anonymous visitor, a shrine page render spends up to 5 anonymous requests
   （plus 1 in the `ctx=concierge&tid` case）on buckets keyed by the egress identity. If the shrine-data request is
   throttled（HTTP 429）, the page shows "神社の詳細情報が見つかりませんでした" for every visitor who shares that
   identity. The most sensitive bucket is `concierge` at **8/min**（anonymous thread detail）. Whether production traffic
   reaches these limits depends on the Vercel egress distribution, which is unmeasured（Hypothesis）.
4. **Additional findings while verifying**:
   - setting only `NEXT_PUBLIC_API_BASE_URL` sends the shrine-detail fetch **directly to the Backend unsigned**（§4, H-6）;
   - the JWT refresh on an internal hop is anonymous and its new token is discarded by SSR（§3.3）;
   - the `guard:no-backend-direct` script prints a failure but always exits 0（§4, F-9）;
   - `/shrines/resolve` turns a GET page view into a Backend POST that creates shrines（§7, T-9）.
5. **Options**:
   - **A**（SSR → Django direct, sign the page identity）reuses WS-04 unchanged and removes the hop, but duplicates BFF
     logic in Server Components and widens the set of modules that call the Backend.
   - **B**（signed SSR → BFF identity assertion）keeps the API boundary, but adds a new trust hop, a new header contract,
     a replay window without a nonce store, and a dependency on a pinned internal origin.
   - **C**（measure）costs nothing now, but leaves a cross-user failure mode in place and needs new instrumentation to
     produce evidence.
6. **Technical preference（not a decision）**: Option A for the anonymous public reads, with Option C metrics before and
   after. The stated assumptions are in §6.5. Final selection belongs to Mother Ship（§11）.

---

## 3. Current architecture and the verified ten-path inventory

### 3.1 Identity flow today

```text
Browser ──TLS──▶ Vercel edge ──▶ SSR function（page render）
   XFF overwritten by Vercel（platform docs; Inferred for this project）
   SSR can read it: headers().get("x-forwarded-for")（Code: shrines.server.ts:35-38 → clientIdentity.ts:74-80）
                         │
                         │ fetch(`${base}/api/...`), base = WEB_BASE_URL or request host（Code: resolveServerBaseUrl.ts:10-32）
                         │ forwards: cookie（and authorization in one case）; NOT the client address
                         ▼
                  Vercel edge ──▶ BFF route function
                   XFF = the SSR function's egress（Inferred）
                   clientIdentityHeaders(req,…) signs THAT address（Code: clientIdentity.ts:74-107）
                         │ X-KM-Client-IP/Ts/Sig = HMAC(KM_CLIENT_IDENTITY_SECRET, ts\nMETHOD\npath\nip)
                         ▼
                  Render edge（Cloudflare）──▶ Django
                   resolve_client_ident: bff:<ip> → edge:<CF-Connecting-IP> → remote:<REMOTE_ADDR>（Code: throttling.py:270-298）
                   authenticated requests: user.pk（Lib: DRF UserRateThrottle.get_cache_key）
```

Backend throttle contract（Code: `backend/shrine_project/settings.py:302-333`, `throttling.py`; Lib: DRF 3.17.2）:

- Global classes: `ScopedRateThrottle`, `AnonRateThrottle`, `UserRateThrottle`, all using the WS-04 resolver for
  anonymous requests. Rates: `anon` 100/min, `user` 100/min, `shrines` 60/min, `concierge` 8/min, others in settings.
- For an anonymous request, `UserRateThrottle` also keys by `get_ident()`. Every anonymous request therefore counts
  against both `anon` and `user` with the same identity, plus the view's scope if it has one.
- `APIView.initial()` runs `perform_authentication → check_permissions → check_throttles`（Lib）. An anonymous request
  to an `IsAuthenticated` view gets 401 / 403 **without** consuming a throttle bucket.
- Buckets live in `LocMemCache`, per process（`settings.py:387-394`）; `WEB_CONCURRENCY` defaults to 1（`backend/start.sh:5`）.

### 3.2 Ten paths（P1–P10, verified against the baseline）

| # | SSR source | BFF route → Django | method | Django view / permission / scope（Code） | anonymous visitor | authenticated visitor | reachability / condition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | `lib/api/shrines.server.ts:45` `getShrineDetailServer`（page + `generateMetadata`） | `/api/shrines/[id]/data` → `/api/shrines/{id}/data/`（`djFetch(req, …, forwardAuth:false)`, `route.ts:41`） | GET | `ShrineViewSet.retrieve`, `AllowAny`, scope `shrines`（`views/shrine.py:266-276`） | anonymous; buckets `shrines`, `anon`, `user` by BFF identity | **still anonymous**（`forwardAuth:false` drops Authorization and Cookie, `backend.ts:46-80`） | **conditional**: only when `DJANGO_API_BASE_URL`, `BACKEND_URL` and `NEXT_PUBLIC_API_BASE_URL` are all unset（`shrines.server.ts:17-24, 41`）; 2 calls per page view |
| P2 | `lib/api/shrineMeaning.server.ts:35` | `/api/shrines/[id]/meaning` → `/api/shrines/{id}/meaning/`（`bffFetchWithAuthFromReq`） | GET | `ShrineMeaningView`, `AllowAny`, scope `shrines`（`views/shrine_meaning.py:12-24`） | `shrines`, `anon`, `user` by BFF identity | `user.pk`（cookie → Bearer in `bffFetch.ts:153-159`） | reachable（shrine page, `page.tsx:302`） |
| P3 | `lib/api/publicGoshuins.server.ts:10` | `/api/public/goshuins` → `/api/goshuins/?is_public=true&shrine=…`（direct `fetch` + `clientIdentityHeaders`, `route.ts:51-55`） | GET | `PublicGoshuinViewSet`, `AllowAny`, no scope（`views/goshuin.py:27-33`） | `anon`, `user` by BFF identity | **still anonymous**（SSR sends no cookie; route sends no auth） | reachable（shrine page `page.tsx:335`, `/shrines/[id]/goshuins`） |
| P4 | `lib/api/billing.server.ts:28` | `/api/billings/status` → `/api/billings/status/`（`bffFetchWithAuthFromReq`） | GET | `BillingStatusView`, `AllowAny`, JWT only, no scope（`views/billing.py:66-70`） | `anon`, `user` by BFF identity | `user.pk` | reachable, **unconditional** on every shrine page（`page.tsx:327`）and mypage |
| P5 | `lib/server/favorites.server.ts:53` | `/api/favorites` → `/api/favorites/`（`bffFetchWithAuthFromReq`） | GET | `FavoriteViewSet`, `IsAuthenticated`（`api_views.py:21-32`） | **no request**: skipped without `access_token` / `refresh_token` / Authorization（`favorites.server.ts:12-16, 43-49`） | `user.pk` | reachable（shrine page `page.tsx:331`） |
| P6 | `lib/api/favorites.server.ts:14` | `/api/favorites` → `/api/favorites/` | GET | same | 401 before throttle（no bucket） | `user.pk` | reachable（`/mypage`, `/favorites`）; `/mypage` requires an `access_token` cookie（`middleware.ts`） |
| P7 | `lib/api/concierge.server.ts:10` `getConciergeThreadServer` | `/api/concierge-threads/[id]` → `/api/concierge-threads/{id}/` | GET | `ConciergeThreadDetailView`, `AllowAny`, scope `concierge` **8/min**（`views/concierge.py:88-91`）; anonymous thread found through the `concierge_anon_id` cookie | `concierge`, `anon`, `user` by BFF identity | `user.pk` | reachable: shrine page with `ctx=concierge&tid`（`page.tsx:376-378`）, `/mypage/history/[tid]` |
| P8 | `lib/api/concierge.server.ts:35` `getConciergeThreadsServer` | `/api/concierge-threads` → `/api/concierge-threads/` | GET | `ConciergeThreadListView`, `IsAuthenticated`, scope `concierge`（`views/concierge.py:58-60`） | 401 before throttle（no bucket） | `user.pk` | reachable（shrine page after P7, mypage） |
| P9 | `app/shrines/resolve/page.tsx:23` | `/api/places/resolve`（POST）→ `/api/places/resolve/`（`djFetch(path, {clientIdentityFrom: req})`, `route.ts:83-87`） | POST | `PlacesResolveView`, **`authentication_classes = []`**, `AllowAny`, no scope（`views/places_resolve.py:78-81`）; may create a shrine（`:127-138`） | `anon`, `user` by BFF identity | **still anonymous**（authentication disabled on the view） | reachable（`/shrines/resolve?place_id=…`） |
| P10 | `app/g/[username]/page.tsx:29` | `/api/public/goshuins/[username]` | GET | — | — | — | **stub**: route returns 501 and calls nothing（`route.ts`） |

### 3.3 Signing on the final Backend request

| path | final request signed? | identity that would be signed |
| --- | --- | --- |
| P1, P2, P3, P4, P7, P9 | **conditionally**: the route passes its incoming `req` to the helper（direct identity per PR #3356） | the address in the BFF route's own `x-forwarded-for` when it is one address and `VERCEL=1` with the secret set; that address is the SSR function egress（**Inferred**）. Otherwise no attestation, and Django uses `edge:<CF-Connecting-IP>` = the BFF function's egress（Inferred） |
| P5, P6, P8 | same mechanism, but anonymous requests stop at the permission check | — |
| P10 | no Backend request | — |

JWT refresh on the internal hop（Code）: when the forwarded `access_token` has expired, `bffFetchWithAuthFromReq`
pre-refreshes（`bffFetch.ts:146-151`）. It sets the new cookie on its response to SSR（`:241-245`）. None of the SSR modules
forwards `Set-Cookie` to the browser（grep: no `set-cookie` handling in the eight SSR modules）. The refresh endpoint is
anonymous（Lib: simplejwt `TokenViewBase.authentication_classes = ()`）, so each such render spends an anonymous
request on the egress identity. It repeats on every render until the browser refreshes its own token.

### 3.4 Budget per anonymous shrine page view（Code-derived upper bound）

| bucket | fallback path（P1 via BFF） | direct path（P1 signed with the page identity） |
| --- | --- | --- |
| `anon` / `user`（100/min each） | P1×2 + P2 + P3 + P4 = 5（+1 P7 with `tid`） | P2 + P3 + P4 = 3（+1） |
| `shrines`（60/min） | 3 | 1 |
| `concierge`（8/min） | 1 with `ctx=concierge&tid` | 1 with `ctx=concierge&tid` |

Per egress identity and per Django process: about 20 anonymous shrine views/min（fallback）or 33（direct） before `anon`
returns 429, and 8 concierge-context views/min before `concierge` does. How many egress identities Vercel uses is
**unmeasured**（Hypothesis H-1）.

---

## 4. Facts versus unverified hypotheses

### 4.1 Verified facts

| id | fact | evidence |
| --- | --- | --- |
| F-1 | The ten call sites exist exactly as listed in §3.2 | `pnpm audit:bff-identity:check` → 0; file:line in §3.2 |
| F-2 | Incoming `X-KM-*` headers are never forwarded by the BFF; no route copies incoming request headers wholesale | grep over `src/app` and `src/lib` for `new Headers(req.headers)`, spreads or `forEach` of request headers: none; `djFetch` copies only named headers（`backend.ts:46-80`）; `bffFetch` builds headers from `init`（`bffFetch.ts:188-197`） |
| F-3 | Django ignores `X-Forwarded-For`; an attestation is accepted only with all three headers, a valid IP, ±60 s and a constant-time HMAC match. Any failure falls back silently（no error response） | `throttling.py:210-249, 270-298` |
| F-4 | The attestation covers method + decoded path + IP + timestamp; it does **not** cover the query string, a nonce or the host | `clientIdentity.ts:89-107`, `throttling.py:234` |
| F-5 | Permission checks run before throttles | Lib: DRF 3.17.2 `APIView.initial` |
| F-6 | Anonymous requests count against `anon` and `user` with the same key | Lib: DRF `UserRateThrottle.get_cache_key`; `settings.py:308-312` |
| F-7 | A 429 on P1 renders the "not found" shell; P2, P3 and P4 degrade to null / [] / free; P7 is caught and the concierge sections are dropped | `page.tsx:268-296`; `shrineMeaning.server.ts`; `publicGoshuins.server.ts:12-19`; `billing.server.ts:36-39`; `page.tsx:410-424` |
| F-8 | `resolveServerBaseUrlFromHeaders` trusts `x-forwarded-host` / `host` when `WEB_BASE_URL` is unset | `resolveServerBaseUrl.ts:10-19`（the CSRF V-1 contract §4.2 already forbids reusing it for origin checks） |
| F-9 | `guard:no-backend-direct` cannot fail: `rg … && (echo …; exit 1) \|\| exit 0`. It currently matches `src/lib/api/shrines.server.ts:20` and still exits 0 | `apps/web/package.json`; local run: prints "❌ Direct backend access found", exit 0 |
| F-10 | BFF CSRF V-1 is not implemented. Its planned decision table rejects requests with neither `Origin` nor `Sec-Fetch-Site`（D13）; `/api/places/resolve` is not in the V-1 route list | `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md` §1, §2（D13）, §4.1 |

### 4.2 Hypotheses（need production evidence）

| id | hypothesis | why it matters | how to test（§9） |
| --- | --- | --- | --- |
| H-1 | SSR → own-domain requests reach the BFF route with `x-forwarded-for` = one Vercel egress address | defines the shared bucket | Option C metric: attestation path counts + 429 on internal hops |
| H-2 | Vercel egress addresses are few enough that unrelated visitors collide | size of the cross-user effect | anonymised distinct-identity counts（§6.4） |
| H-3 | Vercel overwrites `x-forwarded-for` on page requests with the single client address | needed by Options A and B | already assumed by WS-04 for routes; confirm with `attestation_valid` > 0 |
| H-4 | Vercel overwrites `x-forwarded-host` | F-8 safety; Option B assertion destination | platform documentation / owner |
| H-5 | Production P1 takes the fallback path | P1 cost doubles on the fallback | FU-3 of PR #3356: owner reads Vercel env **names** |
| H-6 | `NEXT_PUBLIC_API_BASE_URL` is unset in production. If it is the only one set, P1 goes **direct and unsigned**: `isBackendUrl` deliberately ignores that name（`clientIdentity.ts:34-40`, `shrines.server.ts:37`）, and Django then sees `edge:<SSR egress>` | P1 identity | same owner check as H-5 |

---

## 5. Security invariants（apply to every option）

| id | invariant | how today's code meets it | what a change must keep |
| --- | --- | --- | --- |
| I-1 | Browser-controlled headers cannot impersonate trusted server assertions | F-2, F-3 | any new header must be stripped or ignored unless verified; never forwarded from the browser |
| I-2 | Django remains the authority for throttle identity | resolver in `throttling.py` | the BFF may assert, but Django verifies and decides |
| I-3 | Authentication and authorization unchanged unless approved | — | no change to `forwardAuth`, JWT handling or permissions |
| I-4 | A failed assertion cannot grant a stronger identity | F-3（fallback to edge / remote） | failure → the pre-existing identity, never a different client's |
| I-5 | No user identity inferred from unverified headers | `user.pk` only from JWT / session | an assertion carries an address, never a user |
| I-6 | No raw IPs, tokens, signatures or secrets in logs | WS-04 logging rules | new counters only, no values |
| I-7 | Anonymous and authenticated users stay logically separated | `user.pk` vs `bff:/edge:/remote:` keys | do not move authenticated requests onto address keys |
| I-8 | CSRF protections are not bypassed | F-10 | an assertion is not a CSRF exemption; no new state-changing path |
| I-9 | Existing legitimate requests continue to work | — | fallback behaviour identical to today when anything is missing |
| I-10 | Changes independently testable and reversible | — | one path or flag at a time; old path kept until verified |

---

## 6. Options

### 6.1 Option A — SSR calls Django directly and signs the page identity

What changes: for selected paths, the Server Component calls the Backend origin. It attaches the WS-04 headers built
from `headers()`, the same pattern as `getShrineDetailServer`（`shrines.server.ts:35-48`）.

| aspect | assessment |
| --- | --- |
| WS-04 compatibility | **full**: same headers, same secret, same Backend verification; the signed address is the page request's `x-forwarded-for`（H-3） |
| refactoring | per path. P3: replicate the route's normalisation（`public/goshuins/route.ts`）. P2 / P4 / P7: Bearer from the `access_token` cookie, which is the `bffFetch` logic; reusing it needs a variant that takes `headers()` / `cookies()` instead of `NextRequest`. P1: no code — setting a Backend env name switches it（owner, H-5）. P9: the POST moves into SSR |
| cookies / authentication | P1, P3 and P9 stay anonymous as today. P2, P4 and P7 must convert the cookie to Bearer. Refresh in SSR still cannot set cookies（§3.3）, so expired tokens fall back to anonymous unless refresh is skipped. P7 needs `concierge_anon_id` sent to the Backend origin; how the BFF passes the Web-origin copy must be mirrored（`authCookies.ts:74-82`） |
| CSRF / access control | GETs unaffected. P9 is a POST to a view with no authentication, so no CSRF applies today, and none would be bypassed. Moving it avoids a future D13 rejection of an Origin-less internal POST（F-10） |
| cache | all paths are `no-store` today; unchanged |
| errors | the Backend status reaches SSR directly. Route-level fallbacks（e.g. the billing stub in `billings/status/route.ts`）must be reproduced |
| latency | one fewer function invocation and network hop per call（Hypothesis: lower latency and cost） |
| API boundary | Backend calls spread from Route Handlers / `lib/server` to Server Component modules. This is allowed by `architecture.md` for non-browser code, but the boundary becomes "server code" rather than "BFF routes". F-9 means the guard does not enforce it today |
| migration / rollback | per path, behind a flag or env; rollback = revert or unset. The route stays for browser callers |

### 6.2 Option B — Signed SSR → BFF identity assertion

What changes: SSR adds a new assertion to its internal request. The BFF route verifies it and, if it is valid, signs the
Backend request with the asserted address instead of its own `x-forwarded-for`.

| aspect | requirement / assessment |
| --- | --- |
| trust boundary | new hop: "SSR function → BFF function over the public edge". The BFF must treat the assertion as untrusted input until verified（I-1） |
| spoofing resistance | requires a key the browser cannot obtain. Without the key, a forged assertion must fall back to today's behaviour（I-4）. With a leaked key, an attacker can choose any address: the original WS-04 bucket-splitting bug returns for the BFF path（the same impact as a leak of `KM_CLIENT_IDENTITY_SECRET` today） |
| domain separation | **do not reuse the WS-04 headers or MAC input.** The BFF route path often equals the Backend path（`/api/shrines/{id}/data/` on both）, so an SSR-made `X-KM-*` set for that path would also verify at Django if anything forwarded it. Use distinct header names（e.g. `X-KM-SSR-*`）and a distinct MAC context（a version label in the message）; preferably a distinct key, or a key derived from the secret with a fixed label |
| replay / expiry | short window（≤ 60 s like WS-04）. No nonce store exists on serverless, so replay inside the window remains possible. Impact: requests placed in one known address's bucket. Bind to method + path **+ query** + target origin to narrow it |
| stripping / overwrite | the BFF must ignore any incoming assertion it cannot verify, must never forward it upstream, and must take its decision before calling `clientIdentityHeaders`. Duplicated headers（comma-joined values）must fail verification |
| verifier | the BFF route（the only component that both receives the hop and signs for Django）. Django keeps verifying only WS-04（I-2） |
| sharing the secret | SSR and BFF run from the same deployment and env, so sharing is mechanically simple. The risk is the destination: the SSR base URL comes from request headers when `WEB_BASE_URL` is unset（F-8, H-4）. The assertion must be sent **only** to a pinned, configured origin, or it can leak to whatever host the headers name |
| failure behaviour | missing / invalid / expired → behave exactly as today（egress identity）; count the reason |
| rotation / operations | a second secret, or a derivation, to manage on Vercel; rotation must be atomic within one deployment（it is, if both sides read the same env） |
| extra internal authentication | not needed for identity. The assertion must **not** be used as an authentication or CSRF signal（I-3, I-8） |
| CSRF interaction | an internal POST（P9）has no `Origin` / `Sec-Fetch-Site`. If V-1 is extended to that route, D13 rejects it regardless of B（F-10） |

### 6.3 Option C — Keep the flow and measure

| aspect | assessment |
| --- | --- |
| measurement available today | Django `throttle identity summary`（`bff` / `edge` / `remote`, attestation outcomes）per 300 s window（WS-04 §14）. It does **not** separate SSR-internal from browser-originated requests, and it does not count 429s |
| collision measurement（new, FU） | per window: (a) the number of distinct anonymous identities seen, from an in-memory set of truncated keyed hashes cleared every window — counts only; (b) the 429 count per scope and per identity path（`bff` / `edge` / `remote`）; (c) on the Web side, the count of internal SSR fetches by path and status, without addresses |
| fairness / cross-user 429 | real by construction for P1, P2, P3, P4, P7 and P9 whenever H-1 / H-2 hold; most likely on `concierge` 8/min（P7） |
| alert thresholds（proposal） | any 429 on P1 or P7 internal hops; a 429 rate > 0.5 % of anonymous Backend requests in a window; a distinct-identity ratio（identities / requests）that falls sharply relative to the browser-originated baseline |
| privacy | counts and truncated keyed hashes only, with an in-memory key per process; no addresses, tokens or signatures（I-6） |
| operational risk | accepts a latent availability bug on the shrine page; detection depends on new instrumentation |
| revisit criteria | any confirmed internal-hop 429; H-2 confirmed（collisions observed）; traffic growth; or a change that adds new SSR internal calls |

### 6.4 Evaluation matrix

Scores are relative（++ better … −− worse）, with the evidence in §6.1–§6.3.

| criterion | A: SSR → Django | B: SSR → BFF assertion | C: measure |
| --- | --- | --- | --- |
| 1 security / spoofing resistance | ++ no new trust hop; WS-04 unchanged | − new hop, new header and key, replay window, destination pinning required | + nothing new; existing exposure unchanged |
| 2 compatibility | − moves logic out of routes; guard / boundary wording | + routes and API boundary unchanged | ++ |
| 3 correctness of anonymous identity | ++ page identity reaches Django | + correct when the assertion verifies; falls back otherwise | −− egress identity stays |
| 4 implementation complexity | − per-path rework（auth conversion for P2 / P4 / P7） | −− new crypto contract on both SSR and BFF, plus stripping | ++ / − only the metrics |
| 5 testability | + unit tests per path; identical to the existing WS-04 tests | − needs spoofing, replay, duplication and destination tests on top | + metrics are testable offline |
| 6 operational burden | + none new（same secret） | − extra secret or derivation; rotation discipline | − dashboards / alerts to read |
| 7 performance / latency | ++ one hop fewer（Hypothesis） | − adds MAC work to the same number of hops | 0 |
| 8 maintainability | − two places that call the Backend | − subtle invariants future routes must keep | + |
| 9 rollback | ++ per path | + flag off → today | ++ |
| 10 residual risk | NAT grouping（inherent）; P1 env dependency（H-5 / H-6）; refresh-in-SSR limits | key leak = mintable identities; replay ≤ window; misconfigured destination leaks assertions | cross-user 429 on the shrine page stays possible |

### 6.5 Technical preference（explicit assumptions; not a selection）

Preference: **Option A for the anonymous public reads first（P1 via env, P3, P2 for guests）, with Option C metrics
added first so the change can be shown to help.** P4 / P7 / P9 would follow per path, or remain under C if the metrics
show no collisions.

Assumptions:

- H-3 holds（page requests carry a single client address）;
- the extra Backend surface in Server Components is acceptable to Mother Ship（an API boundary decision, Q-2）;
- duplicating the small route normalisations is cheaper than maintaining a second cryptographic contract.

If Mother Ship wants the "only Route Handlers call Django" boundary kept, B is the option that does it, and §6.2 lists
its mandatory controls.

---

## 7. Threat model

| id | threat | today | A | B | C |
| --- | --- | --- | --- | --- | --- |
| T-1 | Browser sends `X-KM-Client-*` to the BFF | dropped（F-2） | same | same, plus assertion headers dropped / verified | same |
| T-2 | Browser sends `X-KM-Client-*` directly to Django | HMAC rejects; fallback edge（F-3） | same | same | same |
| T-3 | Browser forges an SSR assertion to the BFF | n/a | n/a | rejected without the key; fallback（must be tested） | n/a |
| T-4 | Replay of a captured attestation / assertion | ≤ 60 s, same address bucket only（WS-04 §12.4） | same | adds a second ≤ window replay surface | same |
| T-5 | Bucket exhaustion of the shared egress identity by heavy anonymous traffic（or deliberately, by repeatedly rendering shrine pages） | **possible**（§3.4） | removed for migrated paths | removed when the assertion verifies | possible; detected |
| T-6 | Assertion or cookies sent to an attacker-chosen host via `x-forwarded-host`（F-8） | cookies today if H-4 fails | not applicable（Backend origin pinned by `isBackendUrl`） | **must pin the destination** | unchanged |
| T-7 | Secret leak | identities mintable at Django | same | additionally at the BFF | same |
| T-8 | NAT / CGNAT grouping | inherent | inherent | inherent | inherent |
| T-9 | Cross-site GET to `/shrines/resolve?place_id=…` triggers a Backend POST that may create a shrine | exists（Code: `page.tsx:13-33`, `places_resolve.py:127-138`）; outside identity scope | unchanged unless redesigned | unchanged | unchanged |

---

## 8. Failure-mode analysis

| condition | today | Option A | Option B |
| --- | --- | --- | --- |
| secret unset on Vercel | no attestation; Django `edge:<egress>` | same as today for the migrated paths（edge:<SSR egress>） | no assertion; today's behaviour |
| page `x-forwarded-for` missing / multi-valued | n/a for the internal hop | no attestation → `edge:<SSR egress>`（no worse than today） | no assertion → today's behaviour |
| assertion malformed / duplicated / expired / bad MAC | n/a | n/a | ignored + counted; today's behaviour（I-4） |
| Django secret mismatch | `bad_signature` → `edge:` | same | same at the final hop |
| Django throttles（429） | P1 → "not found" shell; others degrade（F-7） | per-visitor bucket; same rendering on 429 | same as A when verified |
| upstream timeout / 5xx | as today per module | must reproduce the route fallbacks（billing stub, goshuin normalisation） | unchanged |
| expired access token in SSR | anonymous refresh on egress, token discarded（§3.3） | refresh moves to SSR, still cannot set cookies; recommend no refresh in SSR（treat as anonymous） | unchanged（refresh at BFF, signed with the asserted address） |

---

## 9. Verification and rollout strategy（design only — nothing implemented）

| # | test | CI（unit / integration） | needs controlled production verification |
| --- | --- | --- | --- |
| V-1 | two anonymous users, different client IPs → different Backend keys | ✓ BFF / SSR helpers with mocked headers; Django resolver tests with signed headers | ✓ confirm `bff` counts and no shared 429 |
| V-2 | two anonymous users behind one NAT → same key（expected） | ✓ | — |
| V-3 | authenticated user → `user.pk`, never an address key | ✓（existing `ws04.authRegression` tests extended） | — |
| V-4 | missing / malformed / multi-valued `x-forwarded-for` → no attestation, fallback | ✓（`clientIdentity.test.ts` style） | — |
| V-5 | spoofed `X-KM-Client-*`（and `X-KM-SSR-*` for B）from the browser → ignored, never forwarded | ✓ route tests asserting upstream headers | — |
| V-6 | SSR recursive request（each of P1–P9）→ expected identity source | ✓ module tests with mocked `headers()` / `fetch` | ✓ internal-hop 429 = 0 |
| V-7 | B only: expired, replayed outside the window, wrong method / path / query, wrong origin, duplicated header | ✓ | — |
| V-8 | Django with no trusted identity → `remote:` fallback, no error | ✓（existing backend WS-04 tests） | — |
| V-9 | partial upstream failure（P2 / P3 / P4 / P7 fail, P1 succeeds）→ page renders with degraded sections | ✓ page-level tests with mocked modules | — |
| V-10 | regression: Concierge chat / threads, Compass recommendations / weekly | ✓ existing suites（`web-contract`, direction E2E, backend tests） | ✓ normal-traffic observation only |

Rollout principle: **Option C metrics first**（a baseline）, then one path per PR behind a flag or env. Each step is
verified by counts only（no load tests）. Rollback is the flag / env, or a revert. The Backend needs no change for
Option A. For Option B, nothing on the Backend changes either（the BFF still signs WS-04）.

---

## 10. Recommended follow-up PR boundaries（none started）

| id | scope | type | gate |
| --- | --- | --- | --- |
| FU-1a | Mother Ship decision on Q-1…Q-6（§11） | decision record | Mother Ship |
| FU-2-C | Option C instrumentation: internal SSR fetch counts / statuses（Web）; 429 per scope + identity path and distinct-identity counts（Django） | runtime, metrics only | FU-1a |
| FU-2-A1 | P1: owner sets a Backend env **name**（`DJANGO_API_BASE_URL` or `BACKEND_URL`; **not** `NEXT_PUBLIC_API_BASE_URL` alone, H-6） | env（owner） | FU-1a + owner |
| FU-2-A2 / B | per-path migration（P3 → P2 → P4 → P7 → P9）or the B assertion contract | runtime | FU-1a choice |
| FU-G | fix `guard:no-backend-direct` so it can fail, and decide its allowlist in line with Q-2 | CI | review（independent of A / B / C） |
| FU-R | `/shrines/resolve` GET-triggered POST（T-9） | security triage | separate |
| FU-D | documentation updates in §13 | docs | review |

---

## 11. Open questions for Mother Ship

| id | question |
| --- | --- |
| Q-1 | Which option（A, B, C, or A + C）, and for which paths? |
| Q-2 | Is it acceptable for Server Component modules（outside Route Handlers / `lib/server`）to call Django directly? This decides Option A and the guard allowlist（FU-G） |
| Q-3 | Approve the owner check of Vercel env **names**（H-5 / H-6）and, if needed, setting a Backend env name for P1? |
| Q-4 | For Option B: a separate secret or a derived key? Accept a ≤ 60 s replay window without a nonce store? |
| Q-5 | Should SSR stop refreshing JWTs on internal hops（treat expired access as anonymous）? |
| Q-6 | Accept the current risk until FU-2-C data exists, and with which alert threshold? |

---

## 12. STOP gate

```text
THIS RECORD           = analysis and options only
ARCHITECTURE          = NOT SELECTED（Q-1）
FU-2                  = NOT STARTED
RUNTIME / ENV / AUTH  = UNCHANGED
NEXT STEP             = Mother Ship answers §11; then one FU-2 PR per approved item
```

---

## 13. README / architecture / roadmap consistency（proposals only; not applied）

| document | current text | proposal |
| --- | --- | --- |
| `docs/core/architecture.md` §認証アーキテクチャ | Frontend → BFF → Backend | add the server-side path（SSR → own BFF → Backend）and its identity consequence; after Q-2, state whether Server Components may call Django directly |
| `docs/core/runtime-security-baseline.md` | no throttle-identity contract | add the WS-04 resolver order, the BFF attestation and the invariants I-1…I-10 |
| `README.md` § Rate limit | scopes and overrides only | add `THROTTLE_TRUSTED_EDGE`（required on Render）and `KM_CLIENT_IDENTITY_SECRET`; note that anonymous requests count against `anon`, `user` and the scope |
| `docs/core/roadmap.md` | 2026-10-25 findings unresolved, handled by separate PRs | consistent; optionally reference FU-1 as an open security design item. No policy change proposed |
| `apps/web/package.json` `guard:no-backend-direct` | intended to fail on direct Backend access | currently ineffective（F-9）; FU-G |

---

## 14. Unresolved assumptions

- H-1…H-6（§4.2） — all require production observation or owner-read configuration.
- The Next.js / Vercel behaviour that Server Components cannot set cookies is taken from framework behaviour, not
  re-verified here. The code fact used is narrower: none of the SSR modules forwards `Set-Cookie`.
- Line numbers refer to `origin/develop@5902aa5`.
