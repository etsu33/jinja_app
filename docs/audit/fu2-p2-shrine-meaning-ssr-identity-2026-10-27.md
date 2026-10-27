# FU-2-P2: Shrine Meaning Anonymous SSR — Direct Backend Fetch（2026-10-27）

## 1. Status

```text
RECORD TYPE   = implementation note（Option A for anonymous P2 only）
DESIGN        = docs/audit/fu2-shrine-meaning-ssr-boundary-2026-10-27.md（§6 boundary, §7 test plan）
BASELINE      = origin/develop@6b67de0（includes PR #3359; independent of PR #3358）
SCOPE         = apps/web/src/lib/api/shrineMeaning.server.ts, web + backend tests, regenerated call-graph inventory
UNCHANGED     = BFF route /api/shrines/[id]/meaning, bffFetch, auth / JWT refresh, Free / Premium shaping, Django
                authorization / throttling / signing, billing, Concierge, Compass, Goshuin, UI
PRODUCTION    = NOT ACCESSED; no deployment
FINAL STATUS  = PR for Mother Ship review; STOP before merge
```

## 2. Change

| page request | before | after |
| --- | --- | --- |
| has `Authorization`, `access_token` or `refresh_token` | SSR → own BFF with the whole Cookie header | **unchanged**（same URL, same Cookie forwarding; login, refresh, invalid-token 401 and Premium are handled by the BFF as before） |
| none of them（anonymous） | SSR → own BFF → Django; Django saw the SSR egress identity | SSR → `${getDjangoOrigin()}/api/shrines/{id}/meaning/`, `GET`, **no Cookie, no Authorization**, WS-04 headers signed from the page request's `x-forwarded-for` → `bff:<visitor ip>` |
| auth context cannot be determined（`headers()` / `cookies()` fails） | — | BFF path（conservative） |
| identity unavailable / malformed | — | no `X-KM-*` headers; the request still goes direct; Django uses `edge:` / `remote:`（WS-04 fail-safe） |
| response | `!ok` → `null`; type guard; exception → `null` | identical on both paths |

Browser-supplied `X-KM-*` headers are never read or forwarded. Entitlement stays in the Backend: the direct request has
no principal, so Django resolves `anonymous`, whose shaping equals `free`（no premium fields）.

## 3. Tests

| layer | file | tests | covers |
| --- | --- | --- | --- |
| web | `apps/web/src/lib/api/__tests__/shrineMeaning.server.test.ts` | 31 | §3a below |
| backend | `backend/tests/test_fu2_shrine_meaning_anonymous_direct.py` | 8 | §3b below |

**§3a — web tests**:

- the direct destination: the configured origin; never the request host or the BFF;
- exact HMAC headers for `GET /api/shrines/7/meaning/`;
- no Cookie or Authorization on the direct path, even with `concierge_anon_id`, `csrftoken`, `sessionid` or analytics
  cookies present;
- fail-safe identity cases;
- spoofed `X-KM-*` headers ignored;
- `access_token`, `refresh_token`, both, or an Authorization header → BFF with an unchanged Cookie header;
- undeterminable context → BFF;
- 401, 404, 429, 500, invalid JSON, non-JSON, a failed type guard, network → `null`;
- a premium-shaped Backend payload passed through untouched;
- invalid ids → no fetch.

**§3b — backend tests**:

- an anonymous direct-shaped request（Accept + attestation, no Cookie or Authorization）never receives premium blocks,
  premium generated text or source restoration fields;
- its payload equals the free user's payload;
- the attestation selects only the throttle identity: `throttle_{shrines,anon,user}_bff:<ip>`; an `X-Plan` header is
  ignored;
- an invalid, expired or malformed attestation and a missing attestation fail safe to `edge:` with 200;
- an unknown shrine → 404.

Run results:

- web full suite: 230 files / 2089 tests passed;
- backend（local Postgres 16, CI-equivalent nogis settings）: new 8 + existing meaning / WS-04 27 = 35 passed;
- `tsc` and ESLint: clean.

## 4. Call-graph effect（`pnpm audit:bff-identity`）

| item | before | after |
| --- | --- | --- |
| `shrineMeaning.server.ts` anonymous branch | internal-bff, identity absent | Backend site, **conditionally signed**, identity **direct**（page request headers） |
| `shrineMeaning.server.ts` auth-context branch | — | internal-bff（intentionally unchanged; authenticated throttling uses `user.pk`） |
| Backend-bound sites | 52 | 53, all conditionally signed, 0 unsigned |
| reconciliation | RECONCILED | RECONCILED |

Known inventory artefacts（audit tool, not this change）:

- the auth branch's "authentication" column says "none forwarded", because the tool does not model the Cookie header
  built from `cookies()`;
- one evidence string prints `undefined:` before "page request headers". Both are cosmetic.

## 5. Residual risks

- Production signing depends on `VERCEL=1`, the secret and a single-address page `x-forwarded-for`（FU-1 H-3）. The
  evidence is the Backend `throttle identity summary`.
- If neither `DJANGO_ORIGIN` nor `BACKEND_ORIGIN` is set on Vercel, the anonymous direct fetch targets the local default,
  and the result is `null`（the existing meaning fallback）. The BFF route used the same origin, so the dependency is
  unchanged.
- Anonymous visitors now spend their own `shrines` 60/min, `anon` and `user` buckets; NAT grouping is inherent.
- Authenticated requests keep the internal hop. The anonymous JWT refresh on that hop（FU-1 Q-5）is unchanged.
- P3（PR #3358）duplicates the small page-identity helper. Extract it into `lib/server/` once both are merged.
