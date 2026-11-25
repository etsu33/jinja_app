# WS-04 Throttle Client Identity — Audit and Design Gate（2026-10-25）

## 1. Status

```text
RECORD TYPE        = audit + design proposal（documentation only）
SOURCE FINDING     = WS-04, docs/audit/web-production-security-effectiveness-audit-2026-10-25.md（PR #3349）
BASELINE           = develop@c6880f4b67aae22473a40fcc825c74debee7e967
MD-2 / MD-3 / MD-4 = APPROVED by Mother Ship（§8）
MD-1               = APPROVED: CF_CONNECTING_IP_WITH_VERIFIED_EDGE_BOUNDARY（evidence §11, implementation §12）
IMPLEMENTATION     = Phase C backend + BFF implemented（§12）; production configuration NOT performed
PRODUCTION         = NOT ACCESSED; no rate-limit testing; no diagnostics
FINAL STATUS       = PR review; deployment gated on §13.4; recursive SSR identity = STOP（§13.2）
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

---

## 11. Render isolated-service observations and MD-1 review（2026-10-25）

This section **supersedes §10.1 and §10.5's previous UNVERIFIED / not-deployed status**. It records operator-supplied test results and read-only Render service metadata verified in the same project conversation. It does **not** approve MD-1 or assert production runtime behavior.

### 11.1 Isolated service and production comparison

- Temporary diagnostic service: `ws04-md1-header-probe-20261025` (`srv-dbespffb9u1s73ar5sn0`), Render workspace `tea-d18eq9qdbo4c739j9sdg`.
- Isolated service: Python / Singapore / Free, public default `onrender.com` domain, `0.0.0.0/0` IP allow list, one instance, auto-deploy off.
- Production `jinja-backend` (`srv-d4sk1uscjiac739ko5r0`): Python / Singapore / Starter-class (`0.5c-512mb`), public default `onrender.com` URL, `0.0.0.0/0` allow list, one instance, auto-deploy on `develop`.
- **Difference / residual uncertainty:** Free versus paid plan, distinct application servers, and unverified internal edge routing / any separately configured production routing. No claim is made that the two services' internal edge behavior is necessarily identical.
- HMAC diagnostic deployed to the isolated service at commit `9ad19ff987f55c261d75d31d81e4a2368d2a12d1` and reported **LIVE** by Render. Production `jinja-backend` and its data were not modified.

### 11.2 Initial header-spoof observations (pre-HMAC diagnostic)

| Probe | Observed result | Interpretation |
| --- | --- | --- |
| ordinary request | `XFF` length 3; `CF-Connecting-IP` and `True-Client-IP` present and equal; same as XFF first entry | header presence/shape observed, not alone proof of trust |
| forged `X-Forwarded-For` | XFF length 4; supplied marker survived in XFF; CF/True markers absent; CF matched XFF second entry | entire XFF is attacker-influenced and must not be used as throttle identity |
| forged `CF-Connecting-IP` | client observed `error code: 1000` | consistent with edge rejection; HTTP status and edge provenance not independently recorded |
| forged `True-Client-IP` | marker absent; CF and True present and equal | supports an overwritten-header hypothesis for that request |

These were a handful of non-load requests to the isolated service only; do not extrapolate an unconditional platform guarantee.

### 11.3 Ephemeral-HMAC two-network comparison

The operator supplied one iPhone 4G measurement and two Mac-network measurements. **All three had the same `key_id = 4a1ac7c3`.** Only shortened token prefixes are retained here, to avoid retaining full temporary network identifiers.

| Measurement | `tokens.cf_connecting_ip` prefix | CF = True | XFF entries | Result |
| --- | --- | --- | --- | --- |
| iPhone 4G, once | `6442ae0b…` | true | 3 | usable measurement |
| Mac network, first | `dcad2f63…` | true | 3 | usable measurement |
| Mac network, second | `dcad2f63…` | true | 3 | stable across both Mac samples |

- **PASS (sampled network separation):** the Mac token was stable across two requests and differed from the iPhone 4G token under one key generation; header presence and equality were consistent.
- **UNVERIFIED:** repeat stability for the iPhone under the same key, and whether this difference is reproducible across further samples.
- A notable detail: the intermediate XFF token differed across the two Mac requests while the CF token remained stable. The rightmost XFF-derived token in the diagnostic corresponds to the CF value in the supplied samples. Position-based logic remains unsupported.
- The tokens prove a difference in *observed candidate-address values for these two network samples*, not unique users. NAT / shared-address limitations remain.

### 11.4 MD-1 status and proposed contract

```text
MD-1 DECISION                = PENDING MOTHER SHIP APPROVAL
TECHNICAL REVIEW             = CONDITIONAL APPROVAL RECOMMENDED
CANDIDATE PEER IDENTITY      = CF-Connecting-IP, only across a verified edge trust boundary
ENTIRE X-FORWARDED-FOR       = NEVER TRUST
HARDCODED NUM_PROXIES        = DO NOT SET BASED ON THESE SAMPLES
INVALID/MISSING EDGE HEADER = FAIL-SAFE NON-SPOOFABLE FALLBACK; verify its availability impact
BACKEND IMPLEMENTATION      = NOT STARTED
BFF HMAC IMPLEMENTATION     = NOT STARTED
PRODUCTION DEPLOYMENT       = NOT PERFORMED
```

Implementation must never accept caller-supplied `CF-Connecting-IP` from a bypass path as trusted. Tests must cover spoof attempts, missing/malformed edge identity, BFF attestation verification, and stable authenticated identity; rollout remains Backend first per MD-3. Existing MD-2=C (BFF HMAC) and MD-4=WS-13 separate remain approved. Do not assume this evidence proves edge consistency across all requests or that `REMOTE_ADDR` fallback achieves per-client fairness.

**Next gate:** explicit Mother Ship MD-1 approval, or further production-edge/source-authenticity verification if the Mother Ship does not accept the residual assumptions. The temporary Render diagnostic service must be deleted after evidence collection under explicit authorization; no deletion is claimed here.

---

## 12. Phase C implementation（2026-10-25）

Mother Ship decisions applied: **MD-1 = `CF_CONNECTING_IP_WITH_VERIFIED_EDGE_BOUNDARY`**, MD-2 = C, MD-3 = backend-first,
MD-4 = WS-13 separate. This section supersedes the "NOT STARTED" lines of §1 and §11.4 for the code; production
configuration and deployment are still **not performed**.

### 12.1 Trust boundary as implemented

| layer | rule | where |
| --- | --- | --- |
| edge boundary | `CF-Connecting-IP` is read **only** when the deployment sets `THROTTLE_TRUSTED_EDGE=render-cloudflare`. Unset or any other value → not trusted. The setting is the operator's assertion that the service is reached only through Render's Cloudflare edge, which overwrites the header（§9.2, §11.2）. | `backend/shrine_project/throttling.py`, `settings.py` |
| header validation | exactly one IPv4 / IPv6 address（no list, whitespace, port, zone id; ≤ 45 chars）; IPv4-mapped IPv6 normalised | `parse_client_ip` |
| X-Forwarded-For | never read | — |
| BFF attestation | `X-KM-Client-IP` / `X-KM-Client-Ts` / `X-KM-Client-Sig` = lowercase hex `HMAC-SHA256(secret, ts\nMETHOD\npath\nip)`; `hmac.compare_digest`; clock skew ≤ 60 s; secret ≥ 32 chars; any failure → attestation ignored（never an error response） | `verified_bff_client_ip` |
| fail-safe | no valid attestation and no trusted edge value → `remote:<REMOTE_ADDR>`（Render platform proxy: groups clients, cannot be split by a caller） | `resolve_client_ident` |
| authenticated users | unchanged: DRF uses `user.pk` and never calls `get_ident()` | DRF |
| logging | no per-request logs; one-time warnings for configuration problems only, without values | `_warn_once` |

Precedence for anonymous requests: `bff:<ip>` → `edge:<ip>` → `remote:<addr>`. Scopes and rate values are unchanged; the
project classes subclass DRF's `AnonRateThrottle` / `UserRateThrottle` / `ScopedRateThrottle` and override only
`get_ident()`. `LoginThrottle`（WS-06）and the `REMOTE_ADDR`-keyed nearby throttles（WS-13: `PlacesNearbyThrottle`,
`_nearby_ident`）are untouched.

BFF side（`apps/web/src/lib/server/clientIdentity.ts`）: signs only when `VERCEL=1`, `KM_CLIENT_IDENTITY_SECRET` is at least
32 characters and Vercel's `x-forwarded-for` is a single valid address; otherwise sends nothing. Applied in `djFetch`,
`bffFetchWithAuthFromReq`（including the token refresh）, and the routes that call the backend directly or by path
（`auth/login`, `auth/register`, `places/find`, `places/nearby`, `places/resolve`, `public/goshuins`, `public/goshuins/feed`）.
Server components that fetch the backend（`src/lib/api/shrines.server.ts`）are not signed and keep the peer identity.

### 12.2 Before / after（anonymous）

| request | before | after（edge configured, secret on both sides） |
| --- | --- | --- |
| direct client, forged `X-Forwarded-For` | new bucket per value | `edge:<CF-Connecting-IP>` |
| direct client, forged `CF-Connecting-IP` | n/a（edge rejects, §11.2） | edge rejects; if it reached the app it is the edge-written value |
| direct client, forged `X-KM-Client-*` | n/a | signature invalid → `edge:<CF-Connecting-IP>` |
| Web user via BFF | whole Render XFF chain（Vercel egress + proxy hops） | `bff:<Vercel-provided client ip>` |
| Web user via BFF, secret missing on either side | — | `edge:<Vercel egress>`（shared） |
| `THROTTLE_TRUSTED_EDGE` unset | — | `remote:<platform proxy>`（**all anonymous clients share one bucket**） |
| authenticated | `user.pk` | `user.pk` |

### 12.3 Required configuration and order（owner action; not performed）

1. Render `jinja-backend`: add `THROTTLE_TRUSTED_EDGE=render-cloudflare` and `KM_CLIENT_IDENTITY_SECRET`（random, ≥ 32
   chars）**before** the backend change is deployed. Without the first, every anonymous client shares one bucket.
2. Deploy the backend; confirm anonymous Concierge / Compass still work.
3. Vercel（Production; Preview only if it talks to a non-production backend）: add the same `KM_CLIENT_IDENTITY_SECRET` as a
   server-only variable and redeploy. Until then the BFF sends nothing and Web users share the Vercel egress bucket.
4. Rotation: change both sides together; during the gap attestation is ignored（fail-safe, shared bucket）.

### 12.4 Residual risks

- Production edge equality with the isolated Free service is inferred, not proven（§11.1）.
- Other services in the same Render workspace can reach `jinja-backend` over the private network and set
  `CF-Connecting-IP` themselves. Only owner-controlled services exist there; the diagnostic service should be deleted.
- Between steps 2 and 3, all Web users share the Vercel egress buckets（e.g. `concierge` 8/min）; keep the gap short.
- IPv6 clients are keyed by full address（not /64）; NAT groups users behind one address.
- A captured attestation can be replayed for ≤ 60 s, but only into the same client's bucket.
- Paths are signed in their encoded form; Django compares the decoded `request.path`, so non-ASCII paths fall back to the
  peer identity.

---

## 13. Pre-merge blockers B-1 / B-2 / R-1（2026-10-25）

Resolves the PR #3354 pre-merge review findings within the same PR. No production setting, deployment or merge was
performed. §12.3 is superseded by §13.4.

### 13.1 B-1: startup configuration guard

`backend/shrine_project/throttle_config.py` is called from `settings.py` at import time, so it runs on the real
production path（gunicorn → `shrine_project.wsgi` → settings）and on every `manage.py` command. It needs no database.

| condition | result |
| --- | --- |
| `THROTTLE_TRUSTED_EDGE` not empty and not `render-cloudflare`（any environment; case-sensitive） | `ImproperlyConfigured` |
| `RENDER_EXTERNAL_HOSTNAME` set（Render web service）and `THROTTLE_TRUSTED_EDGE` missing / blank | `ImproperlyConfigured` |
| `KM_CLIENT_IDENTITY_SECRET` set but shorter than 32 characters or with surrounding whitespace | `ImproperlyConfigured` |
| `KM_CLIENT_IDENTITY_SECRET` unset | allowed（attestation unused; Web users share the Vercel egress bucket） |
| local / CI（no `RENDER_EXTERNAL_HOSTNAME`）with nothing set | allowed（`remote:` fallback, as before this PR） |

Messages name the variable but never its value. Local evidence: with `RENDER_EXTERNAL_HOSTNAME` set and the edge
missing, `gunicorn shrine_project.wsgi:application` logs the `ImproperlyConfigured` line, then
`Reason: Worker failed to boot.` and exits with status 3; with a valid configuration it keeps serving.

**Operational consequence of a failed startup（Render）.** The new instance never becomes healthy and the deploy fails.
Whether the previous instance keeps serving depends on Render's zero-downtime deploy, which applies only to services
without a persistent disk. **The production disk status is unverified**, so a failed startup must be treated as a
possible outage. The guard therefore does not replace the ordering in §13.4: the variables are set before the code that
checks them is deployed, and the env-triggered redeploy of the old code（which ignores them）is the safe moment to
confirm the values were saved. The guard also applies to any other Render web service built from this code（e.g. a
preview environment）: each needs `THROTTLE_TRUSTED_EDGE`.

`RENDER_EXTERNAL_HOSTNAME` is the platform signal already used by `settings.py`（`ALLOWED_HOSTS`, CSRF origins）and printed
by `start.sh`; its presence in production is inferred from those code paths, not observed in this session.

### 13.2 B-2: Server Component identity

Audit of Server Component fetches that can reach Django anonymously:

| function | path to Django | rendering |
| --- | --- | --- |
| `getShrineDetailServer`（`lib/api/shrines.server.ts`; Shrine page + `generateMetadata`, i.e. **two calls per view**） | **direct** when `DJANGO_API_BASE_URL` / `BACKEND_URL` / `NEXT_PUBLIC_API_BASE_URL` is set; otherwise **recursive** through the app's own `/api/shrines/{id}/data/` BFF route | dynamic（`cache: "no-store"`, request-time `searchParams`; no `generateStaticParams`, no `revalidate`） |
| `fetchShrineMeaningPayloadV2Server`, `fetchPublicGoshuinsForShrineServer`, `shrines.list.server`, `concierge.server`, `favorites.server`, `billing.server` | **recursive** through the app's own BFF routes（`resolveServerBaseUrl*` / request host） | dynamic（`no-store`, `cookies()` / `headers()`） |

Implemented（direct path only）: `getShrineDetailServer` signs with the existing HMAC contract when all of these hold:

- `VERCEL=1` and the secret is set;
- the target origin equals a configured backend origin（`DJANGO_ORIGIN`, `BACKEND_ORIGIN`, `DJANGO_API_BASE_URL`,
  `BACKEND_BASE_URL`, `BACKEND_URL`; `NEXT_PUBLIC_API_BASE_URL` alone is not trusted as a backend origin）;
- the page request's Vercel-overwritten `x-forwarded-for` is a single valid address.

`headers()` is read only in that case, so the rendering mode and the `no-store` fetch are unchanged; otherwise the
fetch call is byte-for-byte the previous one. No client IP is invented and no new request is added.

**STOP — recursive Server Component requests.** On the recursive path the BFF route receives a request whose
`x-forwarded-for` is the Vercel function's own egress address, not the browser's. Propagating the browser identity
would need either a new trust hop（the BFF accepting an identity asserted by another function）or moving these
Server Components to call Django directly. Both change the rendering architecture, which is outside the approved
scope. These requests therefore stay keyed by the Vercel egress address（`bff:` or `edge:`）. This over-grouping existed
before this PR（§2）; what changes is that the accidental spread from varying Render proxy hops in the old
XFF-chain key（§11.3）disappears. Its size is unmeasured. Which path production uses for `getShrineDetailServer` is
**unverified**（the Vercel environment list returned 403 to this session）.

### 13.3 R-1: rejected attestation diagnostics

`verified_bff_client_ip` now separates outcomes:

- `absent`: no `X-KM-*` header（mobile and direct callers）, which is normal and not recorded;
- `valid`;
- rejections: `incomplete`, `secret_unconfigured`, `malformed`, `expired`, `bad_signature`.

Each rejection increments a per-process counter（`attestation_rejection_counts()`）. A warning
`BFF client identity attestation rejected: reason=<reason> count=<n> window_seconds=300` is emitted at most once per
reason per 300 s per process, with the number of rejections since the previous warning. No IP, timestamp value,
signature, secret or signed payload is logged.

### 13.4 Configuration and rollout（owner action; not performed）

Pre-checks（owner, read-only）:

1. Render `jinja-backend`: whether a persistent disk is attached（decides whether a failed startup is an outage）.
2. Render logs: `RENDER_EXTERNAL_HOSTNAME=` is printed with a value by `start.sh`.
3. Vercel: system environment variables are exposed（`VERCEL=1` at runtime）, and which of `DJANGO_ORIGIN`,
   `BACKEND_ORIGIN`, `DJANGO_API_BASE_URL`, `BACKEND_URL` are set（B-2 direct versus recursive path）.

Rollout（Backend first）:

1. Generate a secret locally（≥ 32 characters, no whitespace）; never paste it into chat, tickets or logs.
2. Render `jinja-backend`: set `THROTTLE_TRUSTED_EDGE=render-cloudflare` and `KM_CLIENT_IDENTITY_SECRET`. The automatic
   redeploy runs the current code, which ignores both; confirm it is healthy.
3. Merge PR #3354; the backend deploys from `develop`. If startup fails, the deploy log shows the variable name in
   `ImproperlyConfigured`; fix the variable or roll back（below）.
4. Verify without load testing:
   - startup logs contain no `ImproperlyConfigured`;
   - no `trusted edge identity missing` warning appears while serving traffic;
   - anonymous Concierge / Compass work from Web and mobile;
   - no rise in HTTP 429.
   Before step 5, `reason=secret_unconfigured` must not appear（it would mean the BFF already signs while the backend has
   no secret）.
5. Vercel Production: set the same `KM_CLIENT_IDENTITY_SECRET`（server-only, Sensitive）and redeploy. Keep the gap
   between steps 3 and 5 short.
6. Verify: Web flows work; no `attestation rejected` warning with `reason=bad_signature`（secret mismatch）,
   `expired`（clock）, or `secret_unconfigured`.
7. Delete the temporary diagnostic service（separate authorization）.

Rollback:

- Backend misbehaves（429 surge, failed startup）: Render → previous deploy. The variables can stay; the old code
  ignores them. Do not remove `THROTTLE_TRUSTED_EDGE` while the new code runs: the guard would stop the next start.
- Web identity problems only: compare the secret on both sides; removing it on Vercel returns Web users to the shared
  egress bucket（behaviour before this PR）.
- BFF errors: Vercel Instant Rollback. Old and new backend both accept requests with or without `X-KM-*`, so the two
  rollbacks are independent.
- Secret rotation or leak: replace on both sides together; during the gap attestations are rejected
  （`bad_signature`）and Web users share the egress bucket.

---

## 14. Follow-up: health check and identity observability（2026-10-26）

PR #3354 is merged into `develop`（`b97a5e4e`）. This follow-up is a separate branch and PR
（`fix/ws04-healthcheck-identity-observability`）. No production setting, deployment or traffic generation was performed.

### 14.1 Edge warning: evidence versus hypotheses

| statement | level |
| --- | --- |
| `/healthz/` was a DRF `@api_view` without a throttle override, so the default Anon / User throttles ran and called the anonymous identity resolver | **confirmed**（code） |
| A request without `CF-Connecting-IP`（edge trusted）to `/healthz/` returns 200, logs the edge warning once and consumes `throttle_anon_remote:<addr>` / `throttle_user_remote:<addr>` | **confirmed**（isolated reproduction） |
| Those buckets are not shared with edge-identified users（`edge:<ip>`）; when full, `/healthz/` returned 429 | **confirmed**（isolated reproduction） |
| The previous warning was once per process, so a later real missing-edge event was not reported | **confirmed**（isolated reproduction） |
| `/healthz/` was throttled the same way before PR #3354（DRF default identity = `REMOTE_ADDR` without XFF） | **confirmed**（code） |
| Render's internal health check reaches the instance without `CF-Connecting-IP`, and caused the production warning | **hypothesis**（production logs not examined in this session） |
| Render's health-check frequency stays below 100 per minute per source address | **unverified** |

### 14.2 Implementation

- **P-1** `backend/shrine_project/urls.py`: `@throttle_classes([])` on `healthz`. The endpoint stays public
  （`AllowAny`）with the same response（`{"ok": true, "release": …}`）. It no longer runs throttles or the identity
  resolver. Other endpoints keep the default throttle classes and rates.
- **P-2** `throttling.py`: the one-time `edge_missing` warning becomes a counted, bounded warning: the first event is
  logged immediately, then at most one warning per process per 300 s with the number of events since the previous one:
  `trusted edge identity missing or malformed; using fail-safe throttle identity: event=edge_missing count=<n> window_seconds=300`.
  The fail-safe `remote:` fallback is unchanged. An unconfigured edge（local / CI）is not an `edge_missing` event.
- **P-3** `throttling.py`: each anonymous identity resolution increments exactly one path counter（`bff` / `edge` /
  `remote`）and one attestation counter（`absent` / `valid` / `rejected`）. The resolved identity is cached per request,
  so several throttle classes do not double-count. When at least 300 s have passed since the window started, the next
  resolution emits one INFO line and starts a new window:
  `throttle identity summary: window_seconds=300 bff=<n> edge=<n> remote=<n> attestation_absent=<n> attestation_valid=<n> attestation_rejected=<n>`.
  No event means no line. Counters live behind one lock with a fixed key set（bounded memory）. Nothing is added to HTTP
  responses. Authentication and throttle decisions are unchanged.

### 14.3 Interpretation limits

- Counts are **per process**: each gunicorn worker and each restart has its own counters; they are not summed or
  deduplicated across workers or instances. Add the lines of all workers for a time range to get a total.
- A window is closed by the first resolution after 300 s; the last partial window of a quiet period is reported only
  when traffic resumes（or never, if the process stops）.
- Authenticated requests are not counted（DRF uses `user.pk` and never calls the resolver）; `/healthz/` is not counted.
- `bff` counts requests with a valid attestation; it says nothing about how many distinct clients there are.
- R-1 rejection warnings（§13.3）stay in place and give the reason for `attestation_rejected`.

### 14.4 Tests

`backend/tests/test_ws04_healthcheck_identity_observability.py`（18 tests）covers:

- `/healthz/` returns the contract with no throttle key, resolver call or counter, and stays 200 with full buckets;
- other endpoints still return 429 at the original limit; rates and classes are unchanged（read in a fresh process,
  independent of tests that mutate the rate dict）;
- `edge_missing` counting and the 300 s window; repeated events stay observable; fail-safe fallback;
- every path and outcome counter; one count per request across throttle classes and through a real API request;
  authenticated requests not counted; summary content and window; no events, no summary; 8-thread counter consistency;
- no identity category in responses; logs without IPs, JWT, signatures or secret.

Mutation checks: removing the `healthz` exemption fails 3 tests; restoring warn-once behaviour fails 2.
Full backend run: 7124 passed; the only failures are the 4 known pre-existing ones（§13）plus the order-dependent rates
test, which was then fixed as described above and re-run（168 focused WS-04 / throttle tests passed）.

### 14.5 Production verification procedure（owner, read-only, after an approved deploy）

1. Render logs after the deploy: the `event=edge_missing` warning should stop appearing at worker boot. If it still
   appears, real traffic reaches the backend without `CF-Connecting-IP`; investigate before anything else.
2. After normal traffic, find `throttle identity summary` lines（one per worker per ≥ 300 s of traffic）:
   - before the Vercel secret is set: `bff=0`, `attestation_absent` ≈ all anonymous requests;
   - after it is set: `bff > 0` and `attestation_valid > 0` = **positive evidence** that HMAC attestations are accepted;
     `attestation_rejected` should stay near 0（R-1 warnings give the reason otherwise）;
   - `remote` should stay near 0 now that health checks are excluded.
3. Record only the numbers; do not copy surrounding log lines that may contain access-log addresses.
4. No load test and no synthetic traffic are needed: the summary counts normal requests.

### 14.6 Rollback

Render → previous deploy. No setting or data migration is involved; the change is code-only and every counter is
in memory. Rolling back restores throttling on `/healthz/` and the warn-once behaviour.

### 14.7 Mother Ship gate

Deployment of this PR is **not approved by this record**. Merge and deploy require explicit Mother Ship approval.
