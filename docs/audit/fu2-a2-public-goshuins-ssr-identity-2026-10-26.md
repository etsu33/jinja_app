# FU-2-A2: Public Goshuin SSR — Direct Backend Fetch（P3）（2026-10-26）

## 1. Status

```text
RECORD TYPE   = implementation note for one approved path（Option A, P3）
DESIGN        = docs/audit/fu1-ssr-anonymous-identity-design-2026-10-26.md（§3.2 P3, §6.1）
BASELINE      = origin/develop@f9a675e
SCOPE         = apps/web/src/lib/api/publicGoshuins.server.ts + tests + regenerated call-graph inventory
UNCHANGED     = BFF route /api/public/goshuins, auth / JWT refresh, billing, Concierge, Compass, Backend throttling,
                HMAC algorithm, environment variables
PRODUCTION    = NOT ACCESSED; no deployment
FINAL STATUS  = PR for Mother Ship review; STOP before merge
```

## 2. Change

| | before | after |
| --- | --- | --- |
| request path | SSR → `${resolveServerBaseUrl()}/api/public/goshuins?limit=12&offset=0&shrine=…`（own BFF; host from `WEB_BASE_URL` or request headers）→ Django `/api/goshuins/?is_public=true&shrine=…` | SSR → `${getDjangoOrigin()}/api/goshuins/?is_public=true&shrine=…`（server-only `DJANGO_ORIGIN` → `BACKEND_ORIGIN`, the same origin the BFF route uses） |
| identity at Django | the BFF route signed **its own** incoming request: the SSR function egress（Inferred, FU-1 §3.3） | `clientIdentityHeaders({ headers: await headers() }, "GET", upstream)` signs the **page request's** Vercel `x-forwarded-for` → `bff:<visitor ip>` |
| signed method / path | `GET` + `/api/goshuins/`（by the route） | `GET` + `new URL(upstream).pathname` = `/api/goshuins/`, which is Django's `request.path` |
| when signing is skipped | — | off Vercel, secret missing / short, origin not a configured Backend origin, `x-forwarded-for` missing / list / malformed, or `headers()` unavailable → no `X-KM-*` headers; Django falls back to `edge:` / `remote:`（WS-04 fail-safe） |
| result | route: Backend array → `slice(offset, offset+limit)`（0..12）→ image normalisation → SSR item mapping | identical steps in SSR: first 12 items in Backend order → the route's image normalisation rules → the same item mapping |
| failures | route 400 / 502 / 500 → SSR `[]` | 401 / 429 / 5xx / non-JSON / invalid JSON / network → `[]` |
| logging | SSR logged the BFF URL | `shrineId`, status and count only; no URL, headers, IP or signature |

Browser-supplied `X-KM-*` headers are never read or forwarded: the helper builds the headers from Vercel's
`x-forwarded-for` only（tested）.

## 3. Call-graph effect（`pnpm audit:bff-identity`）

| item | before | after |
| --- | --- | --- |
| `src/lib/api/publicGoshuins.server.ts` | internal-bff site, identity **absent**（recursive hop） | Backend site, **conditionally signed**, identity **direct**（page request headers） |
| Backend-bound sites | 52（all conditionally signed） | 53（all conditionally signed; no unsigned site） |
| `/api/public/goshuins` server-side internal callers | `publicGoshuins.server.ts` | none |
| reconciliation | RECONCILED | RECONCILED |

The P3 recursive SSR hop is removed. The FU-1 paths P1, P2, P4, P7 and P9 are unchanged（out of scope）.

## 4. Tests

- `src/lib/api/__tests__/publicGoshuins.server.test.ts`（27 tests）. It covers:
  - the destination: the configured origin; never the request host or the BFF;
  - exact HMAC headers for `GET /api/goshuins/`;
  - fail-safe cases: missing, list, port, non-IP, off Vercel, no secret, short secret, unconfigured origin, `headers()`
    unavailable;
  - spoofed `X-KM-*` headers not forwarded;
  - order and the 12-item limit; image normalisation; the `{ results }` body; id filtering;
  - 401, 429, 500, non-JSON, invalid JSON and network failures → `[]`;
  - no secret, IP, signature or Backend URL in logs.
- `src/app/api/public/goshuins/__tests__/route.contract.test.ts`（4 tests）pins the unchanged BFF route contract. The
  sibling `route.test.ts` is outside the vitest `include` and is not run（pre-existing）.

## 5. Residual risks

- Production signing still depends on `VERCEL=1`, `KM_CLIENT_IDENTITY_SECRET` and a single-address page
  `x-forwarded-for`（FU-1 H-3）. Positive evidence is the Backend `throttle identity summary`（`bff` / `attestation_valid`）.
- If neither `DJANGO_ORIGIN` nor `BACKEND_ORIGIN` is set on Vercel, the fetch targets the local default
  `http://127.0.0.1:8000` and returns `[]`. The previous path depended on the same origin inside the BFF route, so the
  configuration dependency is unchanged.
- NAT / CGNAT grouping is inherent to address-based throttling.
- Anonymous requests now spend the **visitor's** `anon` / `user` buckets instead of the shared egress bucket. A visitor
  rendering many shrine pages is throttled on their own identity.
