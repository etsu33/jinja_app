# FU-2-P2: Shrine Meaning SSR — Identity and Entitlement Boundary Audit（2026-10-27）

## 1. Status

```text
RECORD TYPE      = audit + implementation proposal（documentation only）
BASELINE         = origin/develop@f9a675e（PR #3358 / P3 not yet merged）
DESIGN PARENT    = docs/audit/fu1-ssr-anonymous-identity-design-2026-10-26.md（P2; Option A approved for P3 only）
CODE CHANGES     = NONE（runtime, authorization, Premium, throttle, UI unchanged）
PRODUCTION       = NOT ACCESSED
VERDICT          = a safe Option A boundary EXISTS for requests without any auth context（§6）; protected requests stay on the BFF
FINAL STATUS     = STOP — implementation only after Mother Ship approval（§10）
```

Evidence levels: **Code**（current repository, file:line）, **Test**（existing test that pins the behaviour）, **Inferred**,
**Hypothesis**.

---

## 2. Executive summary

1. **Entitlement is decided entirely in the Backend, and it depends only on the plan that the Backend resolves.**
   `ShrineMeaningView` calls `resolve_plan_context(request)`, and client-supplied plan hints are ignored. Composer and
   shaping produce the response. `anonymous` and `free` are shaped **identically**（same allowed access levels
   `{anonymous, free}`）. Only an authenticated user whom `is_premium_for_user` accepts receives premium fields.
2. **For a request with no auth context, the BFF adds nothing that the Backend uses.** No Authorization header is sent,
   and the forwarded Cookie header cannot contain a Backend session.
   - The Backend `sessionid` lives on the Backend's own domain. No `sessionid` handling exists anywhere in the Web code.
     Its absence on the Web origin is **Inferred** from the two different domains.
   - The meaning view reads the `concierge_anon_id` cookie only to compute an anonymous id. It neither sets that cookie
     nor changes the payload with it.
   - Therefore, for a visitor with no auth context, SSR → Django direct returns **the same payload** as SSR → BFF →
     Django（Code）.
3. **Safe boundary（proposal）**: SSR may call Django directly **only** when the page request carries none of
   `Authorization`, `access_token` and `refresh_token`. That direct request must carry **no** Cookie and no
   Authorization. Every other request keeps the current BFF path: login, JWT refresh, invalid-token 401 and Premium
   behave exactly as today.
   - Routing errors fail **closed**. A premium user who is misrouted to the direct path receives the anonymous/free
     shaping, not more. No protected field can be returned on the direct path, because the request has no principal.
4. **Identity**: the direct request is signed with the page request's Vercel `x-forwarded-for`, the same pattern as P3
   （PR #3358）, for `GET /api/shrines/{id}/meaning/`. Missing or malformed identity → no `X-KM-*` headers → Django
   `edge:` / `remote:`（fail-safe; unchanged WS-04 behaviour）.
5. **Impact of keeping protected requests on the BFF**: small for throttling, because authenticated requests are keyed
   by `user.pk`, not by address. The known cost remains for expired access tokens. The anonymous JWT refresh on the
   internal hop uses the egress identity, and SSR discards the new token（FU-1 §3.3, Q-5）.
6. **Concierge thread SSR（P7 / P8）** is a separate, riskier candidate. P7 is anonymous-readable through
   `concierge_anon_id`, an ownership credential, so a direct path would have to forward that cookie to the Backend.
   P8 rejects anonymous requests before throttling. A dedicated audit is recommended before any change（§9）.

---

## 3. Current request paths

| step | P2 today | evidence |
| --- | --- | --- |
| SSR caller | `fetchShrineMeaningPayloadV2Server(shrineId)` → `${resolveServerBaseUrl()}/api/shrines/{id}/meaning/`, forwarding the **whole** page Cookie header | Code: `apps/web/src/lib/api/shrineMeaning.server.ts:18-50` |
| BFF route | `GET /api/shrines/[id]/meaning` → `bffFetchWithAuthFromReq(req, "/api/shrines/{id}/meaning/")` | Code: `apps/web/src/app/api/shrines/[id]/meaning/route.ts:12-21` |
| BFF auth handling | Authorization header from the incoming request, else Bearer from `access_token` / pre-refreshed access; pre-refresh when access is missing or expiring and a refresh token exists; retry once on 401; forwards the Cookie header; signs the **incoming** request's identity | Code: `bffFetch.ts:128-197`, `:208-211` |
| Django view | `ShrineMeaningView`: `AllowAny`, `throttle_scope = "shrines"`; 404 for an unknown shrine; plan from `resolve_plan_context`; 500 if composition fails | Code: `backend/temples/api/views/shrine_meaning.py:21-44` |
| UI | the page awaits the payload; `null` → existing fallback; `source.historyTheme` used for analytics | Code: `apps/web/src/app/shrines/[id]/page.tsx:302-303, 508`; type guard `apps/web/src/lib/api/shrineMeaning.ts:43-65` |
| other callers of the BFF route | none in production. `lib/api/shrineMeaning.ts`（a client fetch）is unreferenced（PR #3356 inventory） | `docs/audit/bff-backend-call-graph-inventory-2026-10-26.json` |

---

## 4. Public versus protected field matrix

Source: composer `build_generated_fields` / `build_source_fields` / `build_display_fields`
（`backend/temples/services/shrine_meaning_composer.py:773-856`）and shaping
（`backend/temples/services/shrine_meaning_access.py:23-140`）.

| part | field | anonymous | free | premium | rule |
| --- | --- | --- | --- | --- | --- |
| top | `version` | ✓ | ✓ | ✓ | — |
| `source` | `shrineId`, `nameJp`, `address`, `latitude`, `longitude`, `goriyaku`, `goriyakuTags`, `sajin`, `description`, `historyTheme`, `element`, `placeTags`, `directionBonus`, `directionReason` | ✓ | ✓ | ✓ | public shrine data |
| `source` | `interpretationProfile`, `translationResult` | `null` | `null` | ✓ | `PREMIUM_SOURCE_RESTORATION_FIELDS`（premium text could be rebuilt from these） |
| `generated` | `heroMeaningCopy`, `consultationSummary`, `shrineMeaning`, `directionSupportCopy` | ✓ | ✓ | ✓ | not in the premium lists |
| `generated` | `actionMeaning` | `""` | `""` | ✓ | `PREMIUM_GENERATED_REQUIRED_TEXT_FIELDS`（kept as `""` for the frontend type guard） |
| `generated` | `afterVisitReflection`, `historyContext`, `deitySymbolContext`, `benefitActionContext`, `todayFlowContext` | `null` | `null` | ✓ | `PREMIUM_GENERATED_OPTIONAL_TEXT_FIELDS` |
| `display.blocks` | `hero`（access `anonymous`） | ✓ | ✓ | ✓ | `PLAN_ALLOWED_ACCESS_LEVELS` |
| `display.blocks` | `shrine_meaning`, `consultation_summary`（access `free`） | ✓ | ✓ | ✓ | same |
| `display.blocks` | `action_meaning`, `after_visit_reflection`, `history_context`, `deity_symbol`, `benefit_action`（access `premium`） | dropped | dropped | ✓ | same; a block with a missing or unknown access value is dropped（fail closed） |
| `display` | `fallbackMessage` | set if no block is left | same | composer value | `_shape_display` |

Conclusions:

- Nothing that requires authentication alone is returned. The only protected class is **premium**.
- `anonymous` ≡ `free` for this endpoint. An unknown plan falls back to anonymous（`allowed_access_levels_for_plan`）.
- `is_premium_for_user`（`backend/temples/services/billing_state.py:135-149`）returns true for staff users and for an
  active premium billing status.
- Pinned by tests:
  - `backend/temples/tests/test_shrine_meaning_endpoint.py`;
  - `backend/tests/test_ws04_auth_regression_meaning_billing.py`, including:
    - `test_meaning_plan_comes_from_the_backend_user`;
    - `test_valid_attestation_does_not_grant_a_plan`;
    - `test_missing_jwt_is_anonymous_for_meaning`;
    - `test_bad_jwt_is_rejected_with_401_before_throttling`.

---

## 5. Identity, cookie, refresh and CSRF trace

| request class | BFF path today | Django result | identity bucket |
| --- | --- | --- | --- |
| no auth context（no Authorization, no `access_token`, no `refresh_token`） | no Authorization; whole Cookie forwarded; no refresh | plan `anonymous`（Code: `plan_service.py:23-50`） | `shrines` / `anon` / `user` keyed by the **BFF's incoming identity** = SSR egress（Inferred, FU-1） |
| valid access token | Bearer | `free` or `premium` | `user.pk` |
| expired access + valid refresh | pre-refresh on the internal hop（`TokenRefreshView` is anonymous → egress bucket）, then Bearer; the new cookie is set on the response to SSR and discarded | `free` / `premium` | refresh: egress; meaning: `user.pk` |
| expired access, no or invalid refresh | Bearer with the expired token → **401**（Test: `test_bad_jwt_is_rejected_with_401_before_throttling`）; `retryOn401` without refresh does nothing | 401 → SSR `null` → UI fallback | none（401 is returned before throttling） |
| `Authorization` header on the page request | passed through as is | per token | per token |

- **Cookies**: on the direct path only the anonymous class is moved, and it carries no Cookie. `concierge_anon_id`
  does not affect the meaning output: `get_or_create_anonymous_id` reads it or mints a UUID in memory, and the view does
  not attach a cookie（Code: `anonymous_id.py:41-61`, `shrine_meaning.py:29-44`）. Dropping all cookies therefore cannot
  change the payload.
- **JWT refresh**: unchanged. Any request with `access_token` or `refresh_token` stays on the BFF.
- **CSRF**: `GET` only. DRF `SessionAuthentication` enforces CSRF only for unsafe methods, and there is no BFF CSRF check
  on this route（V-1 not implemented; FU-1 F-10）. Nothing is bypassed.
- **HMAC signing conditions**（unchanged helper, `clientIdentity.ts`）:
  - `VERCEL=1` and `KM_CLIENT_IDENTITY_SECRET` ≥ 32 chars;
  - the target origin is a configured Backend origin（`isBackendUrl`）;
  - the page `x-forwarded-for` is one valid address;
  - the signed message is `ts\nGET\n/api/shrines/{id}/meaning/\nip`, which matches Django's `request.path` for the
    `<int:pk>` route.

---

## 6. Option A feasibility for P2

### 6.1 Proposed boundary

```text
fetchShrineMeaningPayloadV2Server(shrineId):
  page has Authorization OR access_token OR refresh_token  →  current BFF path, byte-for-byte unchanged
  otherwise（anonymous）                                   →  GET {getDjangoOrigin()}/api/shrines/{id}/meaning/
                                                             headers: Accept + WS-04 identity（if signable）
                                                             no Cookie, no Authorization
                                                             same response handling: !ok → null, type guard, catch → null
```

- **Auth-context predicate**: reuse the rule that `lib/server/favorites.server.ts:12-16` already uses（Authorization, or
  an `access_token` / `refresh_token` cookie）. Keep it conservative: if cookie parsing fails, use the BFF path.
- **Origin**: `getDjangoOrigin()`（server-only `DJANGO_ORIGIN` → `BACKEND_ORIGIN`）, the origin the BFF route already
  uses. Never `resolveServerBaseUrl` or request host headers.
- **Exact request**: `GET /api/shrines/{positive integer}/meaning/`. The existing `shrineId > 0 && finite` guard stays.

### 6.2 Why no protected field can leak

- The direct request carries no credential. Django can resolve only `anonymous`, which by the matrix receives
  public/free fields only.
- A routing bug can only move an authenticated user to the anonymous shaping（less data）, never move an anonymous
  request to more data.
- The Backend stays the single authority. The Web code still never decides entitlement.

### 6.3 Behaviour differences to accept or reject（Mother Ship）

| case | today（BFF） | direct（proposal） | assessment |
| --- | --- | --- | --- |
| anonymous visitor | anonymous payload | same payload | identical |
| anonymous visitor's throttle identity | shared SSR egress | the visitor's own address | intended fix |
| stale cookie only（e.g. an expired `access_token` without a refresh token） | stays on the BFF → 401 → `null` | unchanged（still BFF） | identical |
| BFF returns 404 / 429 / 500 | `null` | Django 404 / 429 / 500 → `null` | identical outcome |
| Django unreachable | route error → `null` | fetch error → `null` | identical outcome |

### 6.4 Fail-safe identity

Missing or malformed identity means one of: `VERCEL` unset, a short or missing secret, an unconfigured origin, a
missing / list / port / non-IP `x-forwarded-for`, or `headers()` unavailable. In every case: no `X-KM-*` headers, the
request still goes out, and Django uses `edge:<SSR egress>` or `remote:`. Browser-supplied `X-KM-*` headers are never
read or forwarded.

### 6.5 Impact of keeping protected requests on the BFF

- Throttling: authenticated requests use `user.pk`, so the lost address does not affect fairness.
- JWT refresh on the internal hop remains anonymous on the egress identity, and the token is discarded（FU-1 Q-5; not in
  scope here）.
- The BFF route remains in use by SSR for authenticated visitors, so it cannot be removed.

---

## 7. Regression and security test plan（for the implementation PR）

| # | test | layer |
| --- | --- | --- |
| T-1 | no auth context → one fetch to `${DJANGO_ORIGIN}/api/shrines/7/meaning/`; never `resolveServerBaseUrl` / host headers | web unit（mock `next/headers`, `fetch`） |
| T-2 | `access_token` only, `refresh_token` only, both, or an `Authorization` header → the BFF URL with the Cookie forwarded exactly as today | web unit |
| T-3 | the direct request has **no** `cookie` and **no** `authorization` header, even when the page has unrelated cookies（e.g. `concierge_anon_id`, analytics） | web unit |
| T-4 | exact HMAC headers for `GET /api/shrines/7/meaning/` from the page `x-forwarded-for` | web unit |
| T-5 | fail-safe identity cases（§6.4）→ no `X-KM-*`, the fetch still happens | web unit |
| T-6 | spoofed `x-km-client-*` on the page request → not forwarded | web unit |
| T-7 | 200 + valid payload → returned; invalid shape / 401 / 404 / 429 / 500 / non-JSON / network → `null` | web unit |
| T-8 | logs contain no IP, secret, signature, token or URL | web unit |
| T-9 | invalid `shrineId`（0, negative, NaN）→ no fetch | web unit（existing behaviour） |
| T-10 | Backend: an anonymous request with a valid attestation returns no premium field（block `access`, `generated` premium keys, `source` restoration fields） | backend（extends `test_valid_attestation_does_not_grant_a_plan`） |
| T-11 | Backend: an anonymous request's shaping is identical to a free user's shaping for the same shrine | backend |
| T-12 | shrine page tests（`page.test.tsx` and others）still pass with mocked `fetchShrineMeaningPayloadV2Server` | existing |
| T-13 | `pnpm audit:bff-identity`: P2 becomes a Backend site with direct identity for the anonymous branch; the BFF branch remains an internal site; 0 unsigned Backend sites | tooling |

Baseline run for this audit:

- `ws04.authRegression.meaningBilling.test.ts` + `src/app/shrines/[id]` tests: 6 files / 43 tests passed;
- `audit:bff-identity:check` = 0.

The backend tests were not run locally（no Django environment in this session）; they run in CI.

---

## 8. Implementation PR proposal（not started）

| item | content |
| --- | --- |
| branch | `fix/fu2-shrine-meaning-ssr-identity` |
| files | `apps/web/src/lib/api/shrineMeaning.server.ts`; a new web test; optionally the backend tests T-10 / T-11; the regenerated inventory; a short audit note |
| dependency | merge PR #3358 first, then extract the small "signed direct Backend GET from SSR" helper it introduced（`pageIdentityHeaders` in `publicGoshuins.server.ts`）into `lib/server/`, so that P3 and P2 share it instead of duplicating it |
| not touched | BFF route, `bffFetch`, auth / refresh, billing, Concierge, Compass, Backend throttles and shaping, UI |
| rollback | revert; the BFF path is unchanged for all authenticated traffic and is the anonymous fallback |

---

## 9. Concierge thread SSR（P7 / P8）— separate follow-up candidate

| aspect | finding |
| --- | --- |
| P7 detail | `ConciergeThreadDetailView`: `AllowAny`, scope `concierge` **8/min**. Anonymous threads are matched by the signed `concierge_anon_id` cookie, which proves **ownership**（Code: `backend/temples/api/views/concierge.py:88-125`） |
| P8 list | `IsAuthenticated` → anonymous requests are rejected before throttling（no identity issue） |
| why it is riskier than P2 | a direct path must forward `concierge_anon_id` to the Backend. It is a credential. Today only the BFF forwards it, and the Web-origin copy is issued by the BFF（`authCookies.ts:73-100`）. The response is private per owner, not public |
| possible boundary | anonymous requests only: forward exactly one cookie（`concierge_anon_id`）, no others; keep authenticated requests on the BFF. This needs its own threat model（cookie scoping, replay of the signed anon id, error handling of 404 vs 401） |
| recommendation | a separate audit PR before any implementation; P7 matters because 8/min is the smallest shared bucket（FU-1 §3.4） |

---

## 10. STOP gate and open questions

| id | question for Mother Ship |
| --- | --- |
| P2-Q1 | Approve the boundary in §6.1（direct only without any auth context; no cookies on the direct request）? |
| P2-Q2 | Is the auth-context predicate（Authorization / `access_token` / `refresh_token`）sufficient, or should any cookie at all keep a request on the BFF? Both are safe; the stricter one moves fewer requests |
| P2-Q3 | Require PR #3358 to merge first and share its helper（recommended）? |
| P2-Q4 | Schedule the separate Concierge P7 audit? |

```text
RUNTIME CHANGES    = NONE in this PR
IMPLEMENTATION     = NOT STARTED
NEXT STEP          = Mother Ship answers P2-Q1…Q4
```

---

## 11. Documentation consistency

| document | current text | status |
| --- | --- | --- |
| `apps/web/src/lib/api/shrineMeaning.server.ts` header comment | "Server Component から Next.js BFF を経由して取得する" | would become inaccurate for anonymous requests; update it in the implementation PR |
| `docs/core/architecture.md` | "認証、権限、所有者および課金状態の最終判定はBackendが担当する" | consistent: entitlement stays in `ShrineMeaningView` / `shape_shrine_meaning_payload_for_plan` |
| `docs/audit/fu1-ssr-anonymous-identity-design-2026-10-26.md` §3.2 P2 | "Cookie（guests: none）; user.pk for authenticated" | consistent with §5 here; the FU-1 doc stays a historical record |
| `docs/audit/bff-anonymous-identity-paths-audit-2026-10-26.md` | P2 listed as a recursive internal hop | still accurate until the implementation PR regenerates the inventory |
| `docs/core/roadmap.md`, `README.md` | no P2-specific statement | no change needed |

## 12. Unresolved risks

- The absence of a Backend `sessionid` on the Web origin is inferred from the separate domains. If the two ever shared a
  registrable domain, the BFF path could authenticate a session cookie that the direct path drops. That would only
  reduce data（fail closed）.
- Production signing still depends on FU-1 H-3（a single-address page `x-forwarded-for`）and on the Vercel env.
- NAT grouping is inherent. Anonymous visitors now spend their own `shrines` 60/min bucket.
- The backend tests were not executed in this session.
