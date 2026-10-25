# WS-04 Throttle Client Identity — Audit and Design Gate（2026-10-25）

## 1. Status

```text
RECORD TYPE        = audit + design proposal（documentation only）
SOURCE FINDING     = WS-04, docs/audit/web-production-security-effectiveness-audit-2026-10-25.md（PR #3349）
BASELINE           = develop@c6880f4b67aae22473a40fcc825c74debee7e967
IMPLEMENTATION     = NOT STARTED — blocked on Mother Ship decisions MD-1 and MD-2（§6）
PRODUCTION         = NOT ACCESSED; no rate-limit testing
FINAL STATUS       = STOP at the design gate
```

---

## 2. Root cause

DRF's `SimpleRateThrottle.get_ident()` with `NUM_PROXIES` unset returns the **entire** `X-Forwarded-For` header when it is
present（`rest_framework/throttling.py:23-40`, DRF 3.17.2）. `backend/shrine_project/settings.py:301-330` does not set
`NUM_PROXIES`. Any client that sends its own `X-Forwarded-For` value gets a fresh bucket per distinct value, which
bypasses every anonymous limit that relies on DRF's default identity（`anon`, `concierge`, `deep_dive`, `compass`,
`shrines`, `shrines_ingest`, …）. Reproduced locally in the audit（PR #3349, WS-04）.

A second, opposite effect: the BFF forwards no client address, so every anonymous Web request reaches the backend from a
Vercel function egress address. Unrelated Web users can share a bucket（over-grouping）.

---

## 3. Phase A audit

### 3.1 Throttle identity sources in the backend

| throttle | identity | file:line |
| --- | --- | --- |
| `AnonRateThrottle`（default, 100/min） | DRF `get_ident()` → whole XFF or `REMOTE_ADDR` | `settings.py:306-311` |
| `ScopedRateThrottle`（default; anonymous branch） | DRF `get_ident()` | `settings.py:306-328` |
| `UserRateThrottle` / scoped（authenticated） | `user.pk` | DRF default |
| `LoginThrottle` | SHA-256 of the submitted username | `backend/users/throttles.py:6-14` |
| `PlacesNearbyThrottle` | `user:<pk>` or `REMOTE_ADDR` | `backend/temples/api/throttles.py:8-17` |
| manual `places/nearby` throttle | `user:<pk>` or `REMOTE_ADDR` | `backend/temples/api/views/search.py:47-55, 80-122` |

`LoginThrottle`（WS-06）and the `REMOTE_ADDR` keys（WS-13）are separate findings and are not changed by WS-04.

### 3.2 Header path

```text
 Browser ──HTTPS──▶ Vercel edge ──▶ Next.js BFF function ──HTTPS──▶ Render edge ──▶ gunicorn / Django
   │                  │                   │                            │                 │
   │ may send any     │ overwrites XFF    │ forwards only:             │ adds / appends  │ REMOTE_ADDR = Render
   │ X-Forwarded-For  │ with client IP    │ Authorization, Cookie,     │ XFF（behaviour   │ internal proxy addr
   │                  │（general docs）    │ Content-Type, Origin,      │ UNVERIFIED）     │（UNVERIFIED）
   │                  │                   │ Referer, x-csrftoken       │                 │
   │                  │                   │ — no client address        │                 │
 Mobile app / scripts ──HTTPS──────────────────────────────────────────▶ Render edge（direct, no BFF）
```

Evidence:

| hop | evidence | level |
| --- | --- | --- |
| Vercel edge | Vercel documentation: "Vercel overwrites this header by default to prevent IP spoofing"（`x-forwarded-for`, Request Headers page; also `@vercel/functions` `ipAddress()`） | general platform documentation, read through a documentation index; **not verified for this project** |
| BFF → backend | `apps/web/src/lib/server/bffFetch.ts:154-189`（Authorization, Cookie, init headers）; `apps/web/src/lib/server/backend.ts:44-79`（authorization, cookie, x-csrftoken, origin, referer, content-type）; `apps/web/src/app/api/auth/register/route.ts:58-66`; no client-address header anywhere in `apps/web/src/lib/server` or `apps/web/src/app/api` | repository code |
| Render edge | **no evidence available**: `render.com` is unreachable from this session, the production backend is blocked by the session egress policy, and no repository document records Render's `X-Forwarded-For` behaviour or hop count | **UNVERIFIED** |
| direct callers | the mobile app calls the backend without the BFF（`apps/web/src/lib/server/authCookies.ts:79-81`）; the backend is publicly reachable | repository code / earlier audit |

### 3.3 Can the backend tell BFF requests from direct requests?

**No.** BFF requests carry no secret, signature or token that a direct client could not also send; `Origin` and
`Referer` are client-controllable for non-browser clients. Vercel function egress addresses are not a stable allowlist.

### 3.4 Reusable identity mechanisms

| mechanism | usable as a throttle identity? |
| --- | --- |
| signed `concierge_anon_id` cookie（`backend/temples/services/anonymous_id.py`） | **no** as the sole key: it cannot be forged, but anyone can obtain a new one by sending a request without it, so it does not bound abuse. Could only refine a bucket that is already trustworthy |
| JWT（authenticated users） | yes, already used（`user.pk`）; unchanged |
| `getRequestId`（`apps/web/src/lib/server/logging.ts:13-16`） | **no**: client-controllable |

---

## 4. Design options（Phase B）

| option | anonymous identity | fixes XFF forgery | Web user separation | needs |
| --- | --- | --- | --- | --- |
| A. `REMOTE_ADDR` only | Render's internal proxy address | yes | **no**: every client in one bucket | nothing — rejected（global DoS） |
| B. trusted proxy depth | the address appended by the verified Render edge（`XFF[-depth]`） | **yes** | no: Web users grouped by Vercel egress address（as today） | **MD-1** verified depth |
| **C. B + signed BFF attestation（recommended）** | for a valid attestation: the client IP that Vercel provided to the BFF; otherwise B | **yes** | **yes** | **MD-1** + **MD-2**（shared secret） |
| C′. B + Vercel OIDC token instead of a shared secret | as C | yes | yes | MD-1 + enabling Vercel OIDC for the project and verifying its JWT on the backend |
| D. signed anonymous cookie as identity | cookie value | no（mintable） | yes | rejected |

### 4.1 Recommended design（option C）

1. **Backend identity resolver** used by project subclasses of `AnonRateThrottle`, `ScopedRateThrottle` and
   `UserRateThrottle`（set in `DEFAULT_THROTTLE_CLASSES`; scopes and rate values unchanged）:
   - authenticated → `user.pk`（unchanged）;
   - valid BFF attestation → `bff:<client ip>`;
   - otherwise → `peer:<address appended by the trusted edge>`, taken as `XFF[-TRUSTED_PROXY_DEPTH]` only when the
     configured depth is a positive integer and the header has at least that many entries;
   - depth unset, malformed header or too few entries → `REMOTE_ADDR`（fails safe: groups rather than splits）.
   Client-supplied entries to the left of the trusted position are never used.
2. **BFF attestation**: the BFF reads the client IP from Vercel's `x-forwarded-for`（or `@vercel/functions`
   `ipAddress()`）and adds three headers to backend requests: `X-KM-Client-IP`, `X-KM-Client-Ts`, and
   `X-KM-Client-Sig = HMAC-SHA256(secret, ts + "\n" + method + "\n" + path + "\n" + ip)`.
3. **Backend verification**: constant-time compare; timestamp within ±60 s; IP must parse as IPv4 / IPv6; any failure
   → ignore the attestation and use the peer identity（never an error response, so behaviour degrades to option B）.
4. **Secrets and logging**: the secret is server-only on Vercel and Render（never `NEXT_PUBLIC_*`; the existing
   `guard:no-next-public-in-server` check applies）. Neither the secret, the signature nor raw IPs are logged; only
   "attestation valid / invalid / absent" may be logged.
5. **Rollout order**: backend first（accepts attestation, otherwise option B）, then the BFF starts sending.

### 4.2 Before / after throttle keys（anonymous requests）

| request | today | option B | option C |
| --- | --- | --- | --- |
| direct client, no XFF | Render-supplied XFF（likely the client IP; UNVERIFIED） | trusted edge entry | trusted edge entry |
| direct client, forged `XFF: random, …` | **new bucket per value** | trusted edge entry（forgery ignored） | trusted edge entry |
| direct client sending forged `X-KM-Client-*` | n/a | n/a | signature invalid → trusted edge entry |
| Web user via BFF | Vercel egress address（shared） | Vercel egress address（shared） | `bff:<that user's client ip>` |
| authenticated user | `user.pk` | `user.pk` | `user.pk` |

---

## 5. Tests planned for Phase C

- forged XFF prefixes from one client share one bucket;
- repeated requests from one client are throttled at the scope rate;
- two distinct attested Web clients get separate buckets;
- direct backend calls without attestation use the trusted edge entry;
- invalid, expired, malformed or missing attestation headers fall back safely; malformed XFF and too-few entries;
- authenticated identity unchanged; Concierge and Compass anonymous flows still pass;
- the secret and signature never appear in logs.

---

## 6. Mother Ship decisions required before implementation

| id | decision | why it blocks |
| --- | --- | --- |
| **MD-1** | the trusted proxy depth for the Render backend, and how to verify it | Render's `X-Forwarded-For` behaviour is UNVERIFIED. Guessing the depth could trust a forgeable entry or group all clients. Verification options: Render's documentation or support confirmation; or a short-lived diagnostic that reports only the number of XFF entries and whether `REMOTE_ADDR` is private（production change → needs approval） |
| **MD-2** | a new server-only shared secret on Vercel and Render（option C）, or enabling Vercel OIDC（option C′） | new secrets and production environment variables |
| MD-3 | rollout order and fallback（§4.1 step 5） | production configuration sequencing |
| MD-4 | whether WS-13（`REMOTE_ADDR`-keyed nearby throttles）should adopt the same resolver in the same change | scope; WS-13 is a separate finding |

Option B alone needs only MD-1. It fixes the forgery but keeps Web users grouped by Vercel egress address.

---

## 7. Not done

```text
backend / web code          UNCHANGED
settings / env variables    UNCHANGED
secrets                     NONE created
production                  NOT ACCESSED; no rate-limit tests
PR                          NONE（created only after the design gate and implementation）
```
