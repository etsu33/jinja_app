# BFF Backend Call-Graph Audit — WS-04 Client Identity Paths（2026-10-26）

## 1. Status

```text
RECORD TYPE        = read-only static audit（AST）+ audit tooling; no application behaviour changed
BASELINE           = origin/develop@c3c0c9510eb1033a246a416f1b19322f31e3850c（after PR #3354 / #3355）
SCOPE              = every .ts / .tsx under apps/web/src（718 files: 480 production, 232 test, 6 Storybook）
TOOL               = apps/web/scripts/audit/bff-backend-call-graph.mjs（TypeScript Compiler API, typescript 5.9.3）
INVENTORY          = docs/audit/bff-backend-call-graph-inventory-2026-10-26.{md,json}（generated）
RECONCILIATION     = RECONCILED（0 unexplained text hits, 0 AST-only sites, 0 orphan signing calls）
PRODUCTION         = NOT ACCESSED; no traffic; no env values read; no secrets, IPs, tokens or signatures in output
CODE CHANGES       = none to routes, signing, throttling or settings（audit script, its tests, a vitest include entry,
                     two package scripts）
CODEQL             = 3 high alerts（js/incomplete-sanitization）triaged and fixed in the audit script（§11）
FINAL STATUS       = PR for review; STOP before merge
```

---

## 2. Conclusion

1. **Every statically discoverable production Backend request site has the WS-04 signing helper on its path.**
   52 Backend-bound request sites: 51 in Route Handlers, 1 in a Server Component（`getShrineDetailServer`）. All 52 are
   **conditionally signed**; 0 are unsigned; 0 are unresolved. "Conditionally" is deliberate: signing still needs
   `VERCEL=1`, `KM_CLIENT_IDENTITY_SECRET`（≥ 32 chars）and a single-address `x-forwarded-for` at runtime
   （`clientIdentity.ts`）, and none of that is visible to static analysis. No site is classified **signed**.
2. **No client code calls the Backend directly.** All 55 client-only request sites go to the app's own BFF
   （relative `/api/...`）.
3. **The identity is lost on server-side recursive BFF calls — this is the structural gap.** 10 reachable server-side
   sites in 8 modules call the app's own BFF over HTTP, reaching 9 Route Handlers. These routes sign with the identity
   of the request **they** receive. For an internal call, that identity is the Vercel function's egress address, not
   the browser's. The audit marks these hops as identity **absent**（inferred, as in the WS-04 design §13.2; not
   measured）. The over-grouping §13.2 recorded as STOP is real and wider than §13.2 listed（§5.2）.
4. The shrine detail fetch（`getShrineDetailServer`）is **Backend or internal depending on env**: it goes direct and
   signs when a Backend env name is set, otherwise it falls back to the recursive path. Which one production uses is
   still unverified（as in §13.2）.

Blind spot（counter-evidence to conclusion 1）: the audit proves only that the helper is **on the path**. It cannot show
that production sets the secret, that Vercel's `x-forwarded-for` is a single address, or that the Backend accepts the
attestation. The positive evidence for that is the Backend `throttle identity summary`（`bff > 0`,
`attestation_valid > 0`; WS-04 §14.5）, which is a production observation outside this PR.

---

## 3. Method

### 3.1 What the script does

| step | implementation |
| --- | --- |
| program | `ts.createProgram` with `apps/web/tsconfig.json` options; root files = a directory walk of `src`（includes files that tsconfig excludes, such as stories） |
| sinks | calls whose callee resolves, via `checker.getSymbolAtLocation` + `getAliasedSymbol`, to the global `fetch` declaration（covers `fetch`, `globalThis.fetch`, `window.fetch`, `const f = fetch`, `fetch.bind(...)`, `fetch.call(...)`）; axios request methods on values typed `AxiosStatic` / `AxiosInstance`（instance `baseURL` resolved from `axios.create`） |
| wrappers | a named project function whose URL **path** comes from its own parameter and that has a production caller. Found transitively to a fixed point（wrapper of wrapper）; each call site is then re-evaluated as a request site. Imports and re-exports resolve through the checker |
| URL | the URL expression is split into base and path（template literals, `+`, `new URL(path, base)`, `const` initialisers）. The base is classified by **env names**（never values）, literals and request-host headers: `backend`, `internal-bff`, `relative`, `backend-or-internal`, `parameter`, `external`, `unresolved` |
| signing | `clientIdentityHeaders` reached from the init expression（through `const`s and helper return values）or present in the enclosing function body. For wrappers, the request argument is mapped to the wrapper's parameters / option properties（e.g. `djFetch`: argument 0, or option `clientIdentityFrom` of argument 1 or 2）, and each call site is checked for what it actually passes（a string path or `undefined` → unsigned） |
| context | Next.js entrypoints（`route.ts`, `page` / `layout` / …）propagate labels along static imports; `"use client"` / `"use server"` modules pin their own label. Refined per top-level function by where it is referenced; unreferenced functions are flagged |
| provenance | a Route Handler is "original or internal" when a reachable server-side site targets its path（route patterns match `[id]` / `[...path]`, static segments first） |
| unresolved | callee is a parameter / property / index-signature member with a network-like return type; global `fetch` or a wrapper passed as a value; request sites whose destination is not statically known |
| reconciliation | independent regex scans（§4.2）; every hit is explained as an AST site, comment, string literal, declaration or import, or reported as unexplained |

### 3.2 Classification vocabulary

| field | values |
| --- | --- |
| HMAC | `conditionally signed`（helper on path, request object supplied）, `unsigned`, `unresolved`, `not applicable (non-Backend hop)`. `signed` is never assigned statically |
| identity | `direct`（the incoming Route Handler request or the page request headers）, `forwarded`（a parameter whose production callers pass the incoming request）, `absent`, `unknown` |
| provenance | `original user request`, `original user request (server render / action)`, `original or internal (route also called by server-side fetch)`, `unknown (…)` |

### 3.3 Known limits of the method

- Context is module- and function-granular, not path-sensitive. A shared module imported by client and server code is
  labelled with both（4 sites）.
- An HTTP request that is not a call expression（HTML `<form action>`, `<img src>`, navigation to `/api/...`,
  `XMLHttpRequest`, `EventSource`, `WebSocket`, `sendBeacon`）is not modelled by the AST. A text search for these
  patterns in `src` returned **0** hits.
- `apps/web/middleware.ts`, `next.config.ts` and the Next.js image optimizer are outside `src`. `next.config.ts` has
  no rewrites（`rewrites()` returns `[]`）. Its `images.remotePatterns` allows the production Backend `/media/**`, so
  the image optimizer may fetch Backend media without client identity. That path is not covered here.
- Code in `node_modules` is not traced（only axios is modelled as a sink）.

---

## 4. Coverage and reconciliation

### 4.1 Counts（production scope）

| item | count |
| --- | --- |
| production rows | 142 = 84 direct sinks + 52 wrapper call sites + 6 wrapper-internal final sinks |
| request sites（excluding wrapper-internal） | 136 |
| by destination | relative 71 · backend 51 · internal-bff 11 · backend-or-internal 1 · parameter 1 · unresolved 1 |
| Backend-bound（backend + backend-or-internal） | 52 — conditionally signed 52; identity direct 50, forwarded 2 |
| by context | client 55 · route-handler 51 · ssr 13 · server-action 2 · server 1 · unknown 10 · client+ssr 3 · client+unknown 1 |
| wrappers | 6: `djFetch`, `bffFetchWithAuthFromReq`, `bffPostJsonWithAuthFromReq`（known）; `apiGet`, `apiPost`, `fetchPopularPage`（detected） |
| unresolved（production） | 3（§5.5） |
| test / Storybook rows | 20 rows, 82 unresolved calls（mocks）— excluded from the inventory, kept in the JSON |

### 4.2 Text-search reconciliation

| pattern | text hits | explained as |
| --- | --- | --- |
| `fetch(` | 63 | AST request site 63 |
| `djFetch(` | 24 | AST request site 20 · comment 2 · declaration 1 · string literal 1 |
| `bffFetchWithAuthFromReq(` | 44 | AST request site 42 · comment 1 · declaration 1 |
| `bffPostJsonWithAuthFromReq(` | 3 | AST request site 2 · declaration 1 |
| `clientIdentityHeaders(` | 12 | AST call 11 · declaration 1 |
| `axios.* / api.*(` request methods | 26 | AST request site 26 |
| Backend origin names（`getDjangoOrigin`, `DJANGO_ORIGIN`, …） | 74 | URL/env construction 24 · string literal 31 · comment 6 · declaration 6 · AST call 4 · import 3 |
| detected wrappers（`apiGet(`, `apiPost(`, `fetchPopularPage(`, generics allowed） | 12 | AST request site 9 · declaration 3 |

- Unexplained text hits: **0**. AST request sites without a text hit on the same line: **0**.
- Production `clientIdentityHeaders` calls not attributed to any request site or wrapper: **0**.
- Counts include test files（the patterns run over all 718 files）.

The reconciliation is evidence that the regex patterns and the AST agree. It is not proof of completeness beyond
those patterns（§3.3）.

---

## 5. Findings

### 5.1 F-1 — Backend sites: helper on path everywhere（conditional）

| path | sites | identity source |
| --- | --- | --- |
| `bffFetchWithAuthFromReq`（28）/ `bffPostJsonWithAuthFromReq`（2） | 30 | argument 0 = the Route Handler `req`（direct） |
| `djFetch(req, path, …)` | 12 | argument 0 = `req`（direct） |
| `djFetch(path, { clientIdentityFrom: req })` | 5 | option = `req`（direct; `places/find` passes it through `forwardToUpstream(body, req?)` → forwarded, both callers pass `req`） |
| direct `fetch` + `clientIdentityHeaders(req, …)` in init | 3 | `auth/register`, `public/goshuins`, `public/goshuins/feed` |
| token refresh inside `bffFetch.ts` | 1 | `req` forwarded from `bffFetchWithAuthFromReq` |
| `getShrineDetailServer`（SSR） | 1 | page request headers via `headers()`, only when the target is a configured Backend origin |

13 of the 52 never forward user credentials（anonymous to the Backend: login, register, deep-dive, places
find/nearby/resolve×2, public goshuins×2, shrine data, shrines list, shrines suggest, shrine detail SSR）. These are
the sites where the anonymous throttle identity matters most.

`djFetch`'s path form signs **only** when `clientIdentityFrom` is passed. All 5 current path-form call sites pass it.
A future call without it would be classified `unsigned`. The fixture tests pin that rule.

### 5.2 F-2 — Server-side recursive BFF calls lose the client identity

Reachable server-side sites that call the app's own BFF（identity `absent` on that hop）:

| site | target route | user credentials on the internal hop | note |
| --- | --- | --- | --- |
| `lib/api/shrines.server.ts:45` `getShrineDetailServer` | `/api/shrines/[id]/data` | none（route uses `forwardAuth: false`） | only on the fallback path（no Backend env）; called twice per shrine page（page + `generateMetadata`） |
| `lib/api/shrineMeaning.server.ts:35` | `/api/shrines/[id]/meaning` | Cookie（guests: none） | shrine page |
| `lib/api/publicGoshuins.server.ts:10` | `/api/public/goshuins` | none | shrine page, `/shrines/[id]/goshuins` |
| `lib/api/billing.server.ts:28` | `/api/billings/status` | Cookie | shrine page, mypage |
| `lib/server/favorites.server.ts:53` | `/api/favorites` | Cookie / Authorization（only with an auth context） | shrine page |
| `lib/api/favorites.server.ts:14` | `/api/favorites` | Cookie | mypage, favorites |
| `lib/api/concierge.server.ts:10` / `:35` | `/api/concierge-threads[/id]` | Cookie | shrine page（with `tid`）, mypage history |
| `app/shrines/resolve/page.tsx:23` | `/api/places/resolve`（POST） | none（route uses `djFetch` path form） | **not in WS-04 §13.2** |
| `app/g/[username]/page.tsx:29` | `/api/public/goshuins/[username]` | none | route is a 501 stub with no Backend call — no throttle effect |

Differences from WS-04 §13.2:

- New: `shrines/resolve/page.tsx`（anonymous POST resolve via the BFF）, `g/[username]/page.tsx`（no Backend effect）, and
  `lib/server/favorites.server.ts`. §13.2 named `favorites.server` without a path; this audit found **two** modules.
- `shrines.list.server`（listed in §13.2）is **not referenced** from any production code; it is dormant.

Impact（**hypothesis**, not measured）: for anonymous visitors, the Backend keys these requests by `bff:<Vercel egress>`
or `edge:<Vercel egress>`. One anonymous shrine page view can produce several such requests（shrine data ×2 on the
fallback path, meaning, public goshuins, billing status）. They share a bucket with every other visitor served from the
same egress address. Authenticated internal hops carry the user's JWT, and DRF then keys them by `user.pk`. The egress
address distribution on Vercel is unmeasured.

### 5.3 F-3 — Env-dependent destination of the shrine detail fetch

`getShrineDetailServer` resolves `DJANGO_API_BASE_URL || BACKEND_URL || NEXT_PUBLIC_API_BASE_URL`, otherwise
`resolveServerBaseUrl()`. Classified `backend-or-internal`: signed with the page identity on the direct path; identity
absent on the fallback path（F-2）. Which path production takes depends on Vercel env, which was not readable here.

### 5.4 F-4 — Dormant and unreferenced request code

These sites are statically present but not reachable from any Next.js entrypoint, or their function has no production
reference. They are not live paths today. They are latent: reviving one could reintroduce an unsigned or recursive
path.

| site | what it would do |
| --- | --- |
| `lib/bff/refreshMutex.ts:27` `refreshJwtWithMutex` | POST to `${origin}/api/auth/jwt/refresh/`, origin from a parameter, **no signing helper**; module-scope single in-flight promise（the cross-user pattern fixed in `bffFetch.ts`, E2E-001） |
| `app/shrines/actions.ts:9, :32`（`"use server"`） | relative `fetch("/api/...")` on the server — would throw at runtime（Node `fetch` rejects relative URLs） |
| `lib/api/shrines.list.server.ts:13`, `lib/api/favorites.server.ts:44`, `lib/api/shrineMeaning.ts:19` | server-side internal BFF calls（F-2 pattern） |
| `lib/api/publicGoshuins.ts`, `publicGoshuins.client.ts`, `shrines.list.client.ts`, `shrines.ts:35/46`, `places.ts`, `conciergeChat.ts`, `lib/conciergeChat.ts`, `actionEvents.ts`, `http.ts` `apiPatch` / `apiDelete` / `apiPatchForm` | client → BFF calls only |

### 5.5 F-5 — Unresolved production call sites（3）

| site | why unresolved | assessment |
| --- | --- | --- |
| `hooks/usePopularShrines.ts:58` → `fetchPopularPage(next)` | URL is the `next` field of a previous response | client-only; the wrapper rejects anything not starting with `/api/populars/`, so it stays a same-origin BFF call. Not a Backend path |
| `lib/bff/refreshMutex.ts:27` | origin is a parameter | dormant（F-4） |
| `lib/favoritesCache.ts:20` `fetcher()` | callee is a parameter | `getFavoritesCached` has no production caller |

### 5.6 Incidental（outside WS-04; not investigated further）

Calls to BFF paths that have no Route Handler in `src/app`（a 404 unless something outside `src` serves them）:
`/api/concierge/plan/`（`src/api/conciergePlan.ts:69`, client）, `/api/favorites/by-shrine/{id}/`（`lib/api/favorites.ts:71`,
client）, `/api/goshuins/`（`lib/api/goshuin.ts:18`, client）, `/api/public/profile/{username}/`（`lib/api/publicProfile.ts:15`,
SSR via axios with relative `baseURL` "/api", which also fails on the server）. `/api/public/goshuins/[username]` is a 501
stub, but `/g/[username]` server-renders against it. These are functional findings for separate triage.

---

## 6. Inventory

The per-call-site inventory（all 142 production rows with file:line, calling function, method, destination,
context, provenance, identity, HMAC, authentication and evidence）, the wrapper models, the Route Handler table and
the reconciliation detail are generated into:

- `docs/audit/bff-backend-call-graph-inventory-2026-10-26.md`（readable tables）
- `docs/audit/bff-backend-call-graph-inventory-2026-10-26.json`（machine-readable, includes test-scope rows）

Reproduce from `apps/web`:

```bash
pnpm audit:bff-identity          # regenerate both files
pnpm audit:bff-identity:check    # exit 1 if the committed JSON differs from the current code
node scripts/audit/bff-backend-call-graph.mjs   # summary only
```

Exit status: `0` reconciled, `1` drift（with `--check`）, `2` not reconciled.

Tests: `apps/web/scripts/audit/__tests__/bff-backend-call-graph.test.ts`（23 tests; in-memory fixtures for aliases,
`globalThis.fetch`, `bind`, re-exports, `djFetch` path / request / option forms, `forwardAuth: false`, wrapper of wrapper,
unsigned wrapper, direct Route Handler fetch, SSR internal and direct fetches, client fetch, axios instances, dynamic
callees, escaped `fetch`, reconciliation failure, no env values in output, plus a smoke test over the real `src`）.

---

## 7. Residual risks

| risk | why it remains |
| --- | --- |
| Signing not proven at runtime | static analysis cannot see env values, Vercel headers or Backend verification; production evidence is the WS-04 §14.5 summary counts |
| Recursive SSR over-grouping（F-2） | architectural; WS-04 §13.2 STOP still applies; size unmeasured |
| Shrine detail path unknown（F-3） | Vercel env not readable from this session |
| Image optimizer → Backend `/media/**` | outside `src`; unsigned by construction; whether the Backend throttles media is not checked here |
| Approximate context labels | module / function granularity; 4 sites carry mixed labels |
| New request patterns | anything outside §3.1（non-call requests, new HTTP clients）needs the script to be extended; the reconciliation patterns are the tripwire |

---

## 8. Proposed follow-up PR boundaries

Each item is a separate PR, and none is started by this record.

| id | scope | type | gate |
| --- | --- | --- | --- |
| FU-1 | Decide the SSR identity design for F-2: (a) anonymous server-side fetches call the Backend directly and sign with the page identity（the `getShrineDetailServer` pattern）, (b) a new trusted internal hop（SSR → BFF assertion）, or (c) accept and measure | design record only | Mother Ship; changes rendering / trust architecture |
| FU-2 | Implement the chosen FU-1 option for the anonymous hops first（public goshuins, meaning, shrine data fallback, resolve page） | runtime | after FU-1 approval |
| FU-3 | Owner read-only check of which `getShrineDetailServer` path production uses（Vercel env names only） | verification | owner |
| FU-4 | Remove dormant request code（F-4: `refreshMutex.ts`, `shrines/actions.ts`, unreferenced `lib/api` modules）after confirming no external import | cleanup | review; no behaviour change |
| FU-5 | Documentation: add the throttle identity contract and the SSR hop to `docs/core/runtime-security-baseline.md` / `architecture.md`; add `THROTTLE_TRUSTED_EDGE` / `KM_CLIENT_IDENTITY_SECRET` to the README rate-limit section | docs | review |
| FU-6 | Optional: run `pnpm audit:bff-identity:check` in `web-tests.yml` as a drift guard | CI | policy decision（it makes every request-site change regenerate the inventory） |
| FU-7 | Triage the incidental no-route calls（§5.6） | bug triage | separate |

---

## 9. README / architecture / roadmap consistency

| document | statement | audit result | assessment |
| --- | --- | --- | --- |
| `docs/core/architecture.md` §認証アーキテクチャ | Frontend → Next.js BFF → Backend; the Frontend never calls the Backend directly with credentials | 0 client sites reach the Backend | **consistent** |
| `docs/core/architecture.md` | describes only the browser → BFF → Backend path | 10 reachable server-side sites use server → own BFF → Backend（F-2）; one SSR site may call the Backend directly（F-3） | **gap**: the recursive SSR hop and its identity consequence are not documented（FU-5） |
| `docs/core/runtime-security-baseline.md` | Security contract source of truth | no mention of throttle identity, `THROTTLE_TRUSTED_EDGE` or BFF attestation | **gap**（FU-5） |
| `README.md` § Rate limit（DRF throttle） | Concierge scope 8/min; `THROTTLE_CONCIERGE`, `DISABLE_THROTTLE` | does not mention that a Render web service now fails to start without `THROTTLE_TRUSTED_EDGE`（WS-04 §13.1）; `backend/.env.example` does list both variables | **incomplete**（FU-5） |
| `docs/core/roadmap.md` | the 2026-10-25 audit findings are not resolved; fixes and production verification are handled by separate PRs | WS-04 code is merged（#3354, #3355）; production configuration and verification are still outstanding; F-2 is an open STOP | **consistent**（no update needed for this audit） |

---

## 10. Not done

```text
apps/web/src, backend          UNCHANGED
routes / signing / throttles    UNCHANGED
settings / env / secrets        UNCHANGED / NONE READ
production                      NOT ACCESSED; no traffic generated
merge / deployment              NOT PERFORMED
```

---

## 11. CodeQL alert triage（PR #3356, 2026-10-26）

### 11.1 Alerts

The CodeQL check on head `ce9e556` reported 3 new high-severity alerts. The source is the check run annotations; the
code-scanning alerts API returned 403 to this session, so alert numbers and data-flow paths were not available. All
three are rule **`js/incomplete-sanitization`**（"Incomplete string escaping or encoding — this does not escape
backslash characters in the input"）, and all three are in `apps/web/scripts/audit/bff-backend-call-graph.mjs`, which
this PR adds. None is in application code.

| # | line（at `ce9e556`） | code | input | classification |
| --- | --- | --- | --- | --- |
| A-1 | 2138 | `w.name.replace(/\$/g, "\\$")` when building a RegExp for a detected wrapper name | a function name read from repository source | **false positive in effect; fixed as hygiene.** Names are checked against `/^[A-Za-z_$][\w$]*$/` first, so they cannot contain a backslash or any other RegExp metacharacter except `$`. The escaping was nonetheless ad hoc |
| A-2 | 2191 | same pattern for the alias / multi-line reconciliation RegExp | same | same as A-1 |
| A-3 | 2246–2247 | `mdEscape`: escaped `\|` but not `\` for Markdown table cells | URL expressions, callee text and evidence strings taken from repository source | **real defect, integrity only, latent.** A value containing `\|` would become `\\|`, which GFM reads as a literal backslash followed by a column separator: the generated inventory table would gain a column. It is not a security vulnerability: the output is a committed Markdown file, and GitHub sanitises rendered HTML. The committed inventory at `ce9e556` was **not** affected: its only backslash is a correct `\|` escape |

### 11.2 Does the script process untrusted input unsafely?

- **Input**: only the TypeScript sources under `apps/web/src`（plus `tsconfig.json`）, read from the local checkout.
  These are as trusted as the code CI builds. No network input, no env values, no user data.
- **Dynamic RegExp**: built only from validated identifiers（now with a complete escape）and fixed literals. The patterns
  have no nested quantifiers, so there is no practical ReDoS surface.
- **Output**: files at paths given on the command line, or stdout. Nothing is executed or evaluated.
- **Conclusion**: no unsafe handling of untrusted input. The trust boundary is "a contributor's own code", the same
  boundary as the build itself.

### 11.3 Fix（audit tooling only）

- New `escapeRegExp(s)` escapes every RegExp metacharacter, including the backslash. It replaces the two ad hoc `$`
  escapes（A-1, A-2）.
- `mdEscape(s)` escapes backslashes **before** pipes（A-3）.
- Three tests added（23 in total）:
  - `escapeRegExp` round-trips a string with a backslash and every metacharacter;
  - `mdEscape` keeps `a\|b`, trailing backslashes and newlines inside one cell; this test fails against the old
    implementation;
  - a fixture with a `$`-containing wrapper name still reconciles.
- The regenerated inventory is byte-identical（`pnpm audit:bff-identity:check` → 0）.
- No suppression or dismissal is used. Application routes, HMAC signing, throttling and settings are unchanged.

### 11.4 Residual risks

- A-1 / A-2 depended on the identifier filter staying in place; the complete escape removes that coupling.
- Markdown cells may still contain HTML-like text taken from source code（for example generics such as `Promise<Response>`）.
  GitHub renders it sanitised, so the effect is cosmetic, not executable.
- Whether CodeQL clears these alerts is confirmed only by the CI re-run on the new head; it is recorded in the PR.

