# WS-04 Throttle Client Identity — Audit and Design Gate（2026-10-25）

## 1. Status

```text
RECORD TYPE        = audit + design proposal（documentation only）
SOURCE FINDING     = WS-04, docs/audit/web-production-security-effectiveness-audit-2026-10-25.md（PR #3349）
BASELINE           = develop@c6880f4b67aae22473a40fcc825c74debee7e967
MD-2 / MD-3 / MD-4 = APPROVED by Mother Ship（§8）
MD-1               = NOT VERIFIED — primary sources unreachable（§9）; network separation UNVERIFIED（§10）
IMPLEMENTATION     = NOT STARTED — blocked on MD-1
PRODUCTION         = NOT ACCESSED; no rate-limit testing; no diagnostics
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

Status after the Mother Ship review: MD-2, MD-3 and MD-4 are decided（§8）; MD-1 remains open（§9）.

| id | decision | why it blocks |
| --- | --- | --- |
| **MD-1**（open） | the trusted proxy depth for the Render backend, and how to verify it | Render's `X-Forwarded-For` behaviour is UNVERIFIED. Guessing the depth could trust a forgeable entry or group all clients. Verification options: Render's documentation or support confirmation; or a short-lived diagnostic that reports only the number of XFF entries and whether `REMOTE_ADDR` is private（production change → needs approval） |
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
production                  NOT ACCESSED; no rate-limit tests; no diagnostics
PR                          NONE（created only after the design gate and implementation）
```

---

## 8. Mother Ship decisions recorded

| id | decision | meaning for the implementation |
| --- | --- | --- |
| **MD-2 = C** | HMAC-signed BFF client identity | §4.1 steps 2–4: the BFF sends `X-KM-Client-IP` / `X-KM-Client-Ts` / `X-KM-Client-Sig`; the backend verifies before using it. A new server-only secret on Vercel and Render is approved in principle; its creation and configuration are deployment steps outside this record |
| **MD-3** | backend-first rollout | the backend ships first and accepts a valid attestation, otherwise uses the peer identity; the BFF starts signing only afterwards |
| **MD-4** | WS-13 stays a separate task | the `REMOTE_ADDR`-keyed nearby throttles（§3.1）are not changed by WS-04 |
| MD-1 | **pending** | §9 |

---

## 9. MD-1 verification（Render trusted proxy boundary）

### 9.1 Render service configuration relevant to forwarding

| item | value | source |
| --- | --- | --- |
| Blueprint（`render.yaml`） | **none** in the repository; routing, plan, custom domain and runtime are configured only in the Render dashboard | repository search |
| start command | `gunicorn shrine_project.wsgi:application --bind 0.0.0.0:${PORT} …`, no `--forwarded-allow-ips` / proxy-protocol options | `backend/start.sh:184` |
| Django proxy settings | no `NUM_PROXIES`, `SECURE_PROXY_SSL_HEADER` or `USE_X_FORWARDED_HOST` | `backend/shrine_project/settings.py` |
| public host | `jinja-backend.onrender.com`（Render default domain; whether a custom domain or extra proxy is configured: dashboard only） | `apps/web/next.config.ts`, earlier production record |
| alternative image | `backend/Dockerfile.web` runs `runserver`; the production record found runtime behaviour consistent with `start.sh`, but the dashboard runtime setting is **UNVERIFIED** | `backend/Dockerfile.web:46-47`; `docs/audit/production-environment-configuration-verification.md` |

`gunicorn` sets `REMOTE_ADDR` to the TCP peer, which on Render is a platform proxy, not the client.

### 9.2 Evidence gathered

The Render domains `render.com`, `docs.render.com` and `community.render.com` do not resolve from this environment, so no
Render page could be read directly. The table states each item's level.

| claim | source | level |
| --- | --- | --- |
| Render's edge **appends** to a client-supplied `X-Forwarded-For` and does not strip it; the leftmost entry is caller-controlled | Render article "Host PocketBase on Render"（`https://render.com/articles/host-pocketbase-on-render`）and a Render community thread, as summarised by a web search engine; third-party test repository `https://github.com/johnbeynon/header-test` | secondary（search summary）+ third-party; **not read verbatim** |
| an observed chain had **four** entries: the spoofed value, the real client IP, and **two proxy-hop addresses** | `johnbeynon/header-test` README（undated; author's affiliation not stated） | third-party, anecdotal |
| Cloudflare sits in front of Render web services and writes `CF-Connecting-IP` on every request, overwriting any caller value; a spoofed `CF-Connecting-IP` is rejected at the edge（`403 error code: 1000`） | the same Render article（search summary）; `johnbeynon/header-test` README | secondary + third-party |
| Render overwrites a spoofed `True-Client-IP` with the real client IP | `johnbeynon/header-test` README | third-party |
| an app on Render sees a proxy address by default and must read a forwarded header | Render article "How Render handles DDoS attacks"（`https://render.com/articles/how-render-handles-ddos-attacks`）, search summary | secondary |

### 9.3 Trusted proxy boundary assessment

- **The leftmost `X-Forwarded-For` entry must never be trusted**（consistent across all sources）.
- **`NUM_PROXIES = 1` would likely be wrong.** If the observed chain（client entry followed by two platform hops）is
  representative, DRF would take the last entry, which is a Render proxy address. Every client would then share one bucket.
  A fixed depth of 3 would depend on a hop count that no primary source states and that may change.
- **The more robust candidate source is a header the edge overwrites**（`CF-Connecting-IP`, or `True-Client-IP`）rather
  than a position in `X-Forwarded-For`. This changes §4.1 step 1: the peer identity would come from an edge-overwritten
  header, with `REMOTE_ADDR` as the fail-safe fallback, and no `NUM_PROXIES`.
- None of this is verified for **this** service（plan, custom domain, current edge configuration）, and none of it was
  read from a primary Render page. The boundary therefore remains **UNVERIFIED**, and no value is set.

### 9.4 Isolated diagnostic（designed, not run）

Purpose: confirm the header behaviour on a Render web service without touching production and without recording any
address.

1. **Environment**: a separate, throwaway Render web service in the same account and region type as production, on the
   default `onrender.com` domain, deployed from a scratch branch. Not the production service, database or secrets.
2. **Endpoint**: one `GET` route that returns only derived, non-sensitive facts:
   - the number of `X-Forwarded-For` entries;
   - whether `CF-Connecting-IP` and `True-Client-IP` are present;
   - booleans: "`CF-Connecting-IP` equals XFF entry *k*" for each *k*, "`True-Client-IP` equals `CF-Connecting-IP`",
     "`REMOTE_ADDR` is a private address";
   - whether each header value equals a **probe token** sent by the tester（detects pass-through of a spoofed value）.
   It never returns or logs a header value or an address; access logs disabled for the route.
3. **Probes**（run by the owner, a handful of requests, no load）: no extra headers; a spoofed `X-Forwarded-For` token;
   a spoofed `True-Client-IP` token; a spoofed `CF-Connecting-IP` token; from two different networks to confirm that the
   chosen source distinguishes clients.
4. **Acceptance for MD-1**: the chosen source is present on every request, is never equal to a spoofed token, and differs
   between the two networks. Delete the service afterwards.

### 9.5 Remaining unknowns and blocker

| unknown | needed for |
| --- | --- |
| primary Render documentation text on forwarded headers | citing an authoritative source |
| whether production `jinja-backend` is behind the same Cloudflare edge（plan, region, custom domain, any extra proxy） | choosing the trusted source |
| whether `CF-Connecting-IP` / `True-Client-IP` are always present and always overwritten for this service | the fail-safe design |
| the current XFF hop count, and whether it is stable | ruling out `NUM_PROXIES` permanently |
| whether the service can be reached without passing the edge | trusting any edge header |

**Blocker**: MD-1 cannot be verified from this environment. All Render domains are unresolvable here, the production
backend is blocked by the session egress policy, and no dashboard access is available. To proceed, one of the following
is needed: (a) the owner reads Render's documentation or obtains Render support confirmation and records it; or (b)
Mother Ship approves running the isolated diagnostic in §9.4（a new, non-production Render service）. Implementation stays
stopped until then.

---

## 10. Network identity separation check（2026-10-25）

### 10.1 Result

```text
NETWORK SEPARATION   = UNVERIFIED
REASON               = no isolated diagnostic service exists yet, and the two measurements（Mac network, iPhone
                       cellular）can only be taken by the owner on those devices
DIAGNOSTIC           = implemented and locally tested, not deployed: scripts/ws04_edge_diagnostic/
JINJA-BACKEND        = UNCHANGED; no production endpoint; no production diagnostics
```

Checked before concluding: no diagnostic code or result exists on any branch of `etsu33/jinja_app` or in another
repository of the account; this environment has no Render access（the Render domains and `*.onrender.com` are
unreachable, and there is no Render API tool）.

### 10.2 Diagnostic with an ephemeral HMAC comparison token

`scripts/ws04_edge_diagnostic/app.py`（standard library only, no dependencies, no environment variables）:

- **Ephemeral key**: 32 random bytes generated in memory at process start; never persisted, returned or logged. A short
  random `key_id` is returned so that measurements can confirm they used the **same key**; a restart or free-instance
  spin-down creates a new key and a new `key_id`, so tokens cannot be linked across generations（no long-lived network
  identifier）.
- **Comparison token**: the first 16 hex characters of `HMAC-SHA256(key, candidate)` for `CF-Connecting-IP`,
  `True-Client-IP` and each `X-Forwarded-For` entry counted from the right.
- **Never returned or logged**: raw addresses, header values, the key, full HMACs; the access log is disabled.
- **Spoof detection**: `?probe=<token>` reports booleans for whether each header equals the tester's probe value.
- Local checks（`python3 -m unittest scripts/ws04_edge_diagnostic/test_app.py`）: 8 passed — stable token for the same
  input, different tokens for different inputs, no raw value in the response, spoof detection, missing headers, no log
  output from the HTTP server.

Owner procedure（deploy as a Free instance, measure, delete）: `scripts/ws04_edge_diagnostic/README.md`.

### 10.3 Production versus isolated service configuration

| setting | production `jinja-backend` | isolated diagnostic（as specified） | comparable? |
| --- | --- | --- | --- |
| hosting | Render web service | Render web service, Free instance | yes, if Free is not a different edge path（UNVERIFIED） |
| domain | `jinja-backend.onrender.com`（default domain; custom domain: dashboard only） | default `onrender.com` domain, no custom domain | yes for the default domain; a production custom domain or extra proxy would break comparability |
| region | dashboard only（UNVERIFIED） | choose the production region | must match |
| plan / instance type | dashboard only（UNVERIFIED） | Free | UNVERIFIED whether the edge differs by plan |
| runtime | gunicorn via `backend/start.sh`（dashboard runtime UNVERIFIED） | Python standard-library HTTP server | the edge headers do not depend on the app server; `REMOTE_ADDR` semantics do |
| Blueprint | none（dashboard configuration） | none | yes |

### 10.4 Remaining trust assumptions

Even a PASS from §10.2 would establish only the following for the isolated service: two specific networks produced
different edge identities, the identity was stable within one key generation, and the tested spoofed headers did or did
not pass through. It would **not** establish:

1. that production is behind the same edge configuration（plan, region, domain, any extra proxy — §10.3）;
2. that the chosen header is present on **every** request and always overwritten（only a handful of requests are
   sampled）;
3. that no path reaches the service without passing the edge;
4. per-user separation: carrier-grade NAT on cellular networks and shared office networks group many users under one
   address; this is inherent to address-based throttling;
5. stability across Cloudflare points of presence, IPv4 / IPv6 changes and future Render platform changes.

Matching header structure（same entry count, same presence flags）is **not** treated as evidence of client separation;
only differing tokens for the same candidate source under one `key_id` are.

### 10.5 MD-1 readiness recommendation

**Not ready.** Recommended next step: the owner deploys the diagnostic as a Free Render web service in the production
region, runs the README measurements within one `key_id`, records only the equality results, and deletes the service.
MD-1 can be proposed for approval when all of the following hold:

- Mac token stable, iPhone token stable, Mac ≠ iPhone for the same candidate source;
- that source never equals a spoofed probe value, and a spoofed `CF-Connecting-IP` is rejected or overwritten;
- the source is present on every sampled request;
- the owner confirms the production service uses the default domain with no additional proxy, and the same region.

Until then, WS-04 implementation stays stopped.
