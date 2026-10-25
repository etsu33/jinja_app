# Web Production Security Effectiveness Audit（2026-10-25）

## 1. Status

```text
RECORD TYPE              = read-only security effectiveness audit（documentation only）
AUDIT BASELINE           = develop@3dab7121ead9db6c9cd298ac3a3d16ecadf9614b
PRODUCTION WEB COMMIT    = 3dab712（Vercel project jinja-app-web, latest READY production deployment
                           dpl_DKtTqd45GMwHo46Xpgfs99azreZA, ref develop; read-only metadata）
SCOPE                    = apps/web, backend, security CI, configuration, documentation
FINDINGS                 = 22（CONFIRMED ISSUE 9 / POTENTIAL RISK 11 / existing 2）; plus PROTECTED controls（§6）
CRITICAL                 = 1   HIGH = 4   MEDIUM = 7   LOW = 7   INFORMATIONAL = 3
APPLICATION CHANGES      = NONE
PRODUCTION CHANGES       = NONE
FINAL STATUS             = STOP — remediation is proposed as separate PRs（§9）
```

**Status labels.**

| label | meaning |
| --- | --- |
| CONFIRMED ISSUE | the defect is visible in code at the baseline, and reproduced locally where stated |
| POTENTIAL RISK | the code permits the risk; whether it materializes depends on unverified production configuration or exploitability |
| PROTECTED | the control exists and the code path enforces it |
| UNVERIFIED | the production behaviour could not be observed in this audit |

**Severity** follows impact × reachability: Critical = unauthenticated path to a library with a remote-code-execution class
advisory; High = cross-user data exposure, or bypass of a cost / abuse control on a public endpoint; Medium = abuse or
integrity risk that needs an account or specific conditions; Low / Informational = hardening and hygiene.

---

## 2. Method and production-verification limits

### 2.1 What was done

- **Endpoint inventory**: the resolved Django URL conf was introspected locally（`django.setup()` with `USE_GIS=0`, no
  database access）to list every route with its view class, methods, permission, throttle and authentication classes.
  Action-level overrides（`get_permissions`, `@action`, route shadowing）were then read by hand.
- **Code review** of the BFF routes, auth helpers, settings, views, serializers, upload validation, storage, account
  deletion and Stripe webhooks.
- **Local reproduction**: a throwaway pytest file outside the repository, run against a throwaway local PostgreSQL 16
  instance（no network, no production data）. Results are quoted per finding. The file is not committed.
- **Dependency advisories**: `pnpm audit --prod` and `pip-audit -r backend/requirements.txt` against the public
  registries（read-only）.
- **Production metadata**: Vercel project list and production deployment list（read-only; no environment variables,
  logs or settings were read）.

### 2.2 What could not be done

| item | reason | consequence |
| --- | --- | --- |
| HTTP checks against `https://jinja-backend.onrender.com` | this session's egress policy denies the host（proxy 403 on CONNECT; not retried） | every backend production check is **UNVERIFIED** in this audit |
| Render configuration（env presence, workers, proxy behaviour） | no Render access in this session | **UNVERIFIED** |
| GitHub Dependabot / code-scanning alert state | no read-only alerts API in this session | open alert state **UNVERIFIED**; local audit tools used instead（§7） |
| cross-user, brute-force or rate-limit tests in production | prohibited by the audit rules | each needs an approved test plan（§8） |

**Historical evidence reused, not re-verified.** `docs/audit/production-environment-configuration-verification.md`
（commit `dbe686b`, merged 2026-10-18）observed in production: `DEBUG=False`, an explicit CORS allowlist with
credentials, `ALLOWED_HOSTS` satisfied, no client-side secret exposure. Those observations are quoted where relevant and
labelled as historical.

---

## 3. Executive summary

| ID | severity | status | title |
| --- | --- | --- | --- |
| WS-01 | **Critical** | CONFIRMED ISSUE（exploit UNVERIFIED） | Unauthenticated BFF upload passes arbitrary bytes to `sharp@0.35.3`（libheif / librsvg advisories） |
| WS-02 | **High** | CONFIRMED ISSUE（partly mitigated） | `next@16.3.8` in production is inside the range of two Critical RCE advisories and one High DoS advisory |
| WS-03 | **High** | CONFIRMED ISSUE（reproduced locally） | IDOR: `GET /api/concierge/thread/?tid=` returns any user's consultation title and recommendations |
| WS-04 | **High** | CONFIRMED ISSUE（reproduced locally） | Anonymous throttle identity is the client-controlled `X-Forwarded-For` header |
| WS-05 | **High** | CONFIRMED ISSUE（reproduced locally for geocode） | Public endpoints with no effective throttle（geocode search / reverse, routes） |
| WS-06 | Medium | CONFIRMED ISSUE | Login throttle is per-username only: no per-client limit, and targeted lockout |
| WS-07 | Medium | CONFIRMED ISSUE（reproduced locally） | Profile icon upload: no size cap, no format allow-list; storage limit not enforced |
| WS-08 | Medium | POTENTIAL RISK | Private Goshuin images and icons are served from public, unauthenticated URLs |
| WS-09 | Medium | POTENTIAL RISK | Security settings fail open when env vars are missing（`DEBUG=True`, public `SECRET_KEY` fallback） |
| WS-10 | Medium | CONFIRMED ISSUE（reproduced locally） | Any authenticated user can create catalog `Shrine` records |
| WS-11 | Medium | POTENTIAL RISK | Backend dependencies with published advisories（Pillow, Django, DRF） |
| WS-12 | Medium | POTENTIAL RISK | Web dependencies with published advisories（axios, follow-redirects, DOMPurify via posthog-js） |
| WS-13 | Low | POTENTIAL RISK | `places/nearby` manual throttle keys on `REMOTE_ADDR`（shared bucket behind a proxy） |
| WS-14 | Low | POTENTIAL RISK | No HTTPS / cookie hardening settings; the earlier "mitigated" reasoning is incomplete |
| WS-15 | Low | POTENTIAL RISK | Anonymous `shrines/ingest` creates records and calls Google Places |
| WS-16 | Low | POTENTIAL RISK | `LocMemCache` throttle state is per worker and reset on restart |
| WS-17 | Low | POTENTIAL RISK | `DISABLE_THROTTLE` has no production guard |
| WS-18 | Low | CONFIRMED ISSUE | Public profile responses allow username enumeration |
| WS-19 | Low | POTENTIAL RISK | `dangerouslyAllowLocalIP` with loopback `remotePatterns` in the production image config |
| WS-20 | Informational | existing（`SEC-B01`） | Logout does not blacklist the refresh token; JWT lifetimes are library defaults |
| WS-21 | Informational | POTENTIAL RISK | Public debug / schema endpoints and broad `ALLOWED_HOSTS` |
| WS-22 | Informational | existing gap | CI does not gate on existing vulnerable dependencies; no secret scanning in CI |

---

## 4. Endpoint and control coverage matrix

Source: local URL-conf introspection at the baseline, plus manual reading of overrides. Default permission is
`AllowAny`（`backend/shrine_project/settings.py:329`）. Default throttles are `ScopedRateThrottle`, `AnonRateThrottle`
（100/min）and `UserRateThrottle`（100/min）（`backend/shrine_project/settings.py:306-328`）. "Scoped" means a `throttle_scope` that actually
reaches DRF. "Owner" means the queryset is filtered by `request.user`（or the signed anonymous id）.

### 4.1 Authentication-required endpoints

| route | methods | auth | owner filter | throttle | assessment |
| --- | --- | --- | --- | --- | --- |
| `api/users/me/` | GET, PATCH, DELETE | `IsAuthenticated`（JWT only） | self | anon / user 100/min | PROTECTED; icon upload → WS-07 |
| `api/users/me/storage/` | GET | `IsAuthenticated` | self | 100/min | PROTECTED; limit only reported（WS-07） |
| `api/my/goshuins/`（+`count/`, `<pk>/`） | GET, POST, PATCH, DELETE | `IsAuthenticated`（JWT） | `filter(user=request.user)`（`temples/api/views/goshuin.py:69-71`） | 100/min | PROTECTED |
| `api/favorites/`（+`<pk>/`） | GET, POST, DELETE | `IsAuthenticated` | `filter(user=...)`（`temples/api_views.py:31-32`） | 100/min | PROTECTED |
| `api/visits/` | GET | `IsAuthenticated` | `filter(user=...)`（`temples/api/views/visit.py:62-64`） | 100/min | PROTECTED |
| `api/shrines/<id>/visit/` | POST | `IsAuthenticated` | writes `user=request.user`; thread lookup scoped by user（`backend/temples/api/views/visit.py:46-53`） | 100/min | PROTECTED |
| `api/reflections/`, `api/shrines/<pk>/reflection/` | GET, POST | `IsAuthenticated` | `filter(user=...)`（`backend/temples/api/views/reflection.py:50-52`） | 100/min | PROTECTED |
| `api/journeys/timeline/` | GET | `IsAuthenticated` | `build_journey_timeline(request.user)`（`backend/temples/api/views/journey.py:13`） | 100/min | PROTECTED |
| `api/concierge-threads/` | GET | `IsAuthenticated` | `filter(user=...)`（`temples/api/views/concierge.py:63-64`） | scope `concierge` | PROTECTED |
| `api/shrine-submissions/` | GET, POST | `IsAuthenticated` | `filter(user=...)`（`backend/temples/api/views/shrine_submission.py:23-24`） | 100/min | PROTECTED |
| `api/shrine-interactions/`, `api/action-events/` | POST | `IsAuthenticated` | write-only | 100/min | PROTECTED |
| `api/billings/checkout/`, `api/billings/portal/` | POST | `IsAuthenticated` | self | 100/min | PROTECTED |
| `api/shrines/`（create） | POST | `IsAuthenticated` | none（global catalog） | scope `shrines` 60/min | **WS-10** |
| `api/debug/behavior-funnel/`, `api/concierge/score-v3/dashboard/` | GET | `IsAdminUser` | — | 100/min | PROTECTED |

### 4.2 Intentionally public（`AllowAny`）endpoints

| route | methods | throttle（effective） | assessment |
| --- | --- | --- | --- |
| `api/auth/jwt/create/` | POST | `LoginThrottle` 5/min per username only | **WS-06** |
| `api/auth/jwt/refresh/`, `api/auth/jwt/verify/` | POST | anon / user 100/min（no dedicated scope） | WS-04 applies |
| `api/users/signup/` | POST | anon 100/min | WS-04 applies |
| `api/concierge/chat/`（compat wrapper） | POST | scope `concierge` 8/min, applied by the inner `ConciergeChatView`（`backend/temples/api_views_concierge.py:450-471`） | PROTECTED; identity → WS-04 |
| `api/concierge/plan/` | POST | scope `concierge` 8/min | PROTECTED; identity → WS-04 |
| `api/deep-dive/ask/` | POST | scope `deep_dive` 8/min | PROTECTED; identity → WS-04 |
| `api/concierge-threads/<pk>/` | GET | scope `concierge` | PROTECTED: user or signed anonymous id（`backend/temples/api/views/concierge.py:120-128`） |
| `api/concierge/thread/?tid=` | GET | anon / user 100/min | **WS-03** |
| `api/compass/recommendations/`, `api/compass/weekly/` | POST | scope `compass` 20/min | PROTECTED; identity → WS-04 |
| `api/shrines/`（list）, `api/shrines/<int:pk>/`, `data/`, `meaning/`, `api/populars/` | GET | scope `shrines` 60/min | PROTECTED（public catalog） |
| `api/shrines/<pk>/`（router PATCH / DELETE） | PATCH, DELETE | — | unreachable: the GET-only `shrines/<int:pk>/` route matches first（`temples/api/urls.py:106, 121`）; locally PATCH / DELETE → 405 |
| `api/shrines/ingest/` | POST | scope `shrines_ingest` 1/min | **WS-15** |
| `api/shrines/nearby/`, `api/shrines/<pk>/route/`, `api/route/` | GET / POST | 100/min | public; WS-04 applies |
| `api/routes/` | GET, POST | **none**（`throttle_classes = []`, `temples/api/views/route.py:77`） | **WS-05** |
| `api/geocodes/search/`, `api/geocodes/reverse/` | GET | **none**（scope set on `request`, not on the view） | **WS-05** |
| `api/geocode/search/`, `api/geocode/reverse/`（legacy） | GET | anon / user 100/min | WS-04 applies |
| `api/places/nearby/`, `nearby_search/`, `nearby-search/` | GET | manual 30/min keyed on `REMOTE_ADDR` | **WS-13** |
| `api/places/search/`, `text-search/`, `text_search/`, `photo/`, `detail/…`, `find/`, `resolve/`, `<id>/`, `api/place-caches/` | GET / POST | anon / user 100/min | public; WS-04 applies |
| `api/goshuins/`, `api/goshuins/<pk>/`, `api/goshuins/feed/` | GET | 100/min | PROTECTED: `is_public=True` only（`backend/temples/api/views/goshuin.py:37`, `backend/temples/api/views/goshuin_feed.py:15`）; image URLs → WS-08 |
| `api/profiles/<username>/` | GET | 100/min | public profile only if `is_public`; **WS-18** |
| `api/billing/status/`, `api/billings/status/` | GET | 100/min | public; returns the caller's own state |
| `api/billings/webhook/`, `api/stripe/webhook/` | POST | 100/min | PROTECTED: Stripe signature verified, fail closed（§6） |
| `api/goriyaku-tags/`, `api/`, `healthz/`, `robots.txt` | GET | 100/min | public |
| `api/_debug/whoami/`, `_debug/whoami_jwt/` | GET | 100/min | **WS-21** |
| `api/schemas/`, `swagger/`, `redoc/`, `api/schema/` | GET | 100/min | **WS-21** |
| `media/<path>`（when `STORAGE_BACKEND != r2`） | GET | none | **WS-08** |
| `admin/` | Django admin | session + staff | out of DRF; cookie hardening → WS-14 |

### 4.3 Web BFF（`apps/web/src/app/api`）

- The BFF forwards the browser's cookies and converts them into an `Authorization` header
  （`apps/web/src/lib/server/bffFetch.ts:121-190`）. Authorization is decided by the backend.
- **Frontend route protection is not relied on as authorization.** `apps/web/middleware.ts:5-23` only redirects
  `/mypage` when the `access_token` cookie is absent. Every private record in §4.1 is enforced by the backend
  permission and owner filter. Finding: **PROTECTED**.
- Exceptions where the BFF itself does work before the backend authorizes: `POST /api/my/goshuins`（**WS-01**）. The
  BFF route `GET /api/concierge/thread`（`apps/web/src/app/api/concierge/thread/route.ts`）exposes WS-03; no frontend
  caller was found.
- Cookie-based CSRF on BFF state-changing routes is tracked separately by the CSRF V-1 records（existing; out of scope
  here）.

---

## 5. Findings

### WS-01 — Unauthenticated BFF upload processed by vulnerable `sharp`

| field | value |
| --- | --- |
| severity / status | **Critical** / CONFIRMED ISSUE（vulnerable version on a reachable untrusted-input path）; exploitability UNVERIFIED |
| affected | `apps/web/src/app/api/my/goshuins/route.ts:16-41`; `apps/web/package.json:43`（`"sharp": "^0.35.0"`, lockfile resolves `0.35.3` for `apps/web`） |
| expected protection | untrusted uploads are authenticated, size-limited and format-restricted before decoding; image libraries are patched |
| code evidence | `POST` reads `req.formData()`, takes `image`, and runs `sharp(buf).jpeg(...)`（line 37）**before** any authentication: the backend's `IsAuthenticated` is only reached at line 45. There is no size limit, no `limitInputPixels`, and no input-format allow-list, so sharp auto-detects any supported format（including SVG via librsvg and HEIF via libheif）. `pnpm audit` reports for `sharp@0.35.3`: GHSA-rgj7-g3m4-5g8c（libheif, High, fixed ≥0.35.4）and GHSA-wq5f-xc86-pv6w（librsvg CVE-2026-96889, High, fixed ≥0.35.5）. The Next.js advisory GHSA-2464-fhr4-w9xw describes the same upstream component as enabling possible RCE on glibc Linux |
| production evidence | the production deployment is commit `3dab712`, which contains this route and lockfile（Vercel metadata）. No exploit attempt was made. Runtime exploitability on Vercel: **UNVERIFIED** |
| impact | an unauthenticated request can feed attacker-controlled bytes to a native decoder with published memory-safety advisories inside the production BFF function; at minimum memory exhaustion of the function |
| remediation | upgrade `sharp` to ≥0.35.5（or drop the direct dependency）; authenticate before parsing the body; cap the request / file size; allow only the needed input formats（JPEG, PNG, WebP, HEIF/MPO per the product intent in the comment at line 33）via sharp metadata before decode; set `limitInputPixels` |
| regression tests | unauthenticated `POST` → 401 without calling sharp; oversize body → 413; SVG input → 400; JPEG / PNG / WebP / HEIC → converted; existing backend validation unchanged |
| Mother Ship approval | recommended for hotfix priority; the change itself is a normal dependency and input-validation fix |

### WS-02 — `next@16.3.8` inside Critical advisory ranges

| field | value |
| --- | --- |
| severity / status | **High** / CONFIRMED ISSUE（version in range）; partly mitigated |
| affected | `apps/web/package.json:38`（`"next": "16.3.8"`） |
| expected protection | the production framework is outside known Critical advisory ranges |
| code evidence | `pnpm audit`: GHSA-2464-fhr4-w9xw（Critical; Image Optimization RCE "when SVG files are used"; affected 16.0.0–16.4.0, fixed 16.4.1; workaround: the `sharp` used by Next.js ≥0.35.5）; GHSA-673q-mjm6-r5xr（Critical; `use cache` functions returning typed arrays）; GHSA-p3m5-59mp-jv5r（High; Server Actions DoS）. Mitigating facts: the lockfile resolves Next's own `sharp` to `0.35.5`（`pnpm-lock.yaml`, `next@16.3.8` snapshot → `sharp: 0.35.5`）; no `"use cache"` directive exists in `apps/web/src`; `dangerouslyAllowSVG` is not set |
| production evidence | production runs commit `3dab712`（Vercel metadata）. Whether Vercel's managed image optimizer is affected: **UNVERIFIED** |
| impact | depends on the advisories' exact preconditions, which the advisory page does not fully state |
| remediation | upgrade `next` to ≥16.4.1 in its own PR, with the web CI and a Preview smoke test |
| regression tests | full `web-tests` workflow; image-rendering smoke on Preview |
| Mother Ship approval | not required for a patch upgrade; recommended to schedule with WS-01 |

### WS-03 — IDOR on `GET /api/concierge/thread/?tid=`

| field | value |
| --- | --- |
| severity / status | **High** / CONFIRMED ISSUE, reproduced locally |
| affected | `backend/temples/api_views_concierge.py:1117-1130`; route `backend/temples/api/urls.py:139`; serializer `backend/temples/api/serializers/concierge.py:99-108`; BFF `apps/web/src/app/api/concierge/thread/route.ts:8-17` |
| expected protection | a thread is readable only by its owning user or its signed anonymous identity, as `ConciergeThreadDetailView` already enforces（`backend/temples/api/views/concierge.py:120-128`） |
| code evidence | `AllowAny`; `ConciergeThread.objects.get(id=tid)` with no user or anonymous-id filter; returns `id`, `title`, `last_message_at`, `recommendations`, `recommendations_v2`. `title` is the first 40 characters of the user's first consultation text（`backend/temples/services/concierge_history.py:342-346, 380`）. Thread ids are sequential integers |
| local test evidence | thread owned by user A; anonymous `GET /api/concierge/thread/?tid=1` → **200** with the private title; user B → **200**; the owner-scoped `GET /api/concierge-threads/1/` for user B → **404** |
| production evidence | **UNVERIFIED**. Verifying it would read other users' data; it requires an approved test plan with two dedicated test accounts and their own threads |
| impact | anyone can enumerate consultation titles（the user's own words）and recommendation payloads for every user and anonymous thread |
| relation to earlier audit | `docs/audit/concierge-thread-authorization-isolation-audit.md` §3–§4 reviewed only `concierge-threads/` and `concierge-threads/<pk>/` and found no defect there. This endpoint was outside its scope; the earlier conclusion stands for the endpoints it covered |
| remediation | remove the unused route and BFF route, or apply the same user / anonymous scoping as `ConciergeThreadDetailView` |
| regression tests | anonymous, other user and other anonymous id → 404; owner and matching anonymous id → 200; BFF route removed or scoped |
| Mother Ship approval | not required to fix; recommended to decide whether a production exposure review（access-log check）is needed |

### WS-04 — Anonymous throttle identity is client-controlled

| field | value |
| --- | --- |
| severity / status | **High** / CONFIRMED ISSUE, reproduced locally |
| affected | `backend/shrine_project/settings.py:301-330`（no `NUM_PROXIES`）; DRF `rest_framework/throttling.py:23-40`（3.17.2） |
| expected protection | anonymous rate limits key on a client address the client cannot choose |
| code evidence | with `NUM_PROXIES` unset, DRF's `get_ident` returns the **whole** `X-Forwarded-For` header when present. A client that varies the left-most entry gets a new bucket per request. This applies to every anonymous scope: `concierge` 8/min, `deep_dive` 8/min, `compass` 20/min, `anon` 100/min（signup, refresh, places, …）, `shrines_ingest` 1/min |
| local test evidence | `POST /api/deep-dive/ask/` ×10 with a fixed XFF → 429 from the 9th request; ×10 with a varying left-most XFF entry → **no 429** |
| production evidence | the backend is directly reachable on the public internet（mobile clients call it without the BFF, per `apps/web/src/lib/server/authCookies.ts:79-81`）. Whether Render passes client-supplied XFF through unchanged: **UNVERIFIED**; stress tests are prohibited |
| second effect | the BFF does not forward the browser's address（`apps/web/src/lib/server/bffFetch.ts:181-189`）, so anonymous web traffic arrives from Vercel egress addresses and shares their buckets. This can over-throttle legitimate users（POTENTIAL RISK） |
| impact | LLM-backed and external-API-backed endpoints can be driven past their intended limits; cost and availability |
| remediation | set `NUM_PROXIES` to the verified proxy depth for Render, or a custom `get_ident` that trusts only the platform-appended entry; decide how the BFF conveys a trustworthy client address（for example a server-to-server header protected by a shared secret） |
| regression tests | spoofed XFF prefixes share one bucket; BFF-originated requests are attributed per client as designed |
| Mother Ship approval | **yes**: the trusted-proxy and BFF client-address design |

### WS-05 — Public endpoints with no effective throttle

| field | value |
| --- | --- |
| severity / status | **High** / CONFIRMED ISSUE（geocode reproduced locally; routes from code） |
| affected | `backend/temples/api/views/geocode.py:25-31, 63-67`; `backend/temples/api/views/route.py:74-77` |
| expected protection | each public endpoint that calls an external provider has a scoped limit（`geocode` 30/min, `route` 20/min are defined in `backend/shrine_project/settings.py:311-328`） |
| code evidence | the geocode views set `request.throttle_scope = "geocode"` inside the handler. DRF reads `throttle_scope` from the **view**, and throttles run before the handler, so the scope never applies; `@throttle_classes([ScopedRateThrottle])` also removes the default anon / user throttles. `RouteAPIView` sets `throttle_classes = []` |
| local test evidence | 60 consecutive anonymous `GET /api/geocodes/search/` → all 200, **no 429** |
| production evidence | **UNVERIFIED** |
| impact | unbounded proxying to the public Nominatim service（`backend/temples/services/geocode.py:48, 85`）, whose usage policy is about 1 request/s; risk of the backend's address being blocked（availability）; unbounded route-provider calls |
| remediation | move the scope to the view（`throttle_scope` attribute on a class-based view or a `ScopedRateThrottle` subclass）; give `RouteAPIView` the `route` / `routes` scope |
| regression tests | the 31st geocode request in a minute → 429; routes throttled |
| Mother Ship approval | no |

Note: `nearby_search.throttle_scope = ...`（`backend/temples/api/views/search.py:412, 433`）and
`concierge_chat_compat.throttle_scope = ...`（`backend/temples/api/views/compat.py:94-95`）use the same ineffective
pattern; both are compensated（a manual throttle, and the inner `ConciergeChatView` scope respectively）.

### WS-06 — Login throttle keyed on username only

| field | value |
| --- | --- |
| severity / status | Medium / CONFIRMED ISSUE |
| affected | `backend/users/throttles.py:6-14`; `backend/users/api/auth.py:6-7` |
| expected protection | per-account and per-client limits on password attempts |
| code evidence | the cache key is a hash of the submitted username only; `throttle_classes = [LoginThrottle]` replaces the default anon throttle |
| production evidence | **UNVERIFIED**（brute-force testing prohibited） |
| impact | one client can try one password against many usernames without any limit（credential stuffing）; anyone can block a known username's login for a minute at a time |
| remediation | add a per-client throttle（after WS-04 is fixed）alongside the per-username one; consider a shared cache（WS-16） |
| regression tests | many usernames from one client → 429; per-username limit kept |
| Mother Ship approval | no |

### WS-07 — Profile icon upload: no size cap or format allow-list

| field | value |
| --- | --- |
| severity / status | Medium / CONFIRMED ISSUE, reproduced locally |
| affected | `backend/users/api/views.py:117-121`; `backend/users/api/serializers.py:65-71`; `backend/users/models.py:14`; storage limit `backend/users/api/views.py:51, 62-90` |
| expected protection | the same validation as Goshuin images（JPEG / PNG / WebP, 10 MB, Pillow verify; `backend/temples/api/serializers/validators.py:7-43`） |
| code evidence | `icon` is a plain `ImageField` with no custom validator; no `DATA_UPLOAD_MAX_MEMORY_SIZE` / file size cap; `STORAGE_LIMIT_BYTES` is only reported by `MeStorageView`, never enforced |
| local test evidence | a 48,000,054-byte BMP icon via `PATCH /api/users/me/` → **200** |
| production evidence | **UNVERIFIED** |
| impact | storage and bandwidth abuse; icons are publicly served（WS-08）; Pillow decodes any supported format（WS-11） |
| remediation | reuse `validate_image_file` with the Goshuin allow-list and a size cap; enforce a request-size limit |
| regression tests | BMP / oversize → 400; JPEG / PNG / WebP within limit → 200 |
| Mother Ship approval | no |

### WS-08 — Private images served from public URLs

| field | value |
| --- | --- |
| severity / status | Medium / POTENTIAL RISK |
| affected | `backend/shrine_project/settings.py:471-497`（`AWS_QUERYSTRING_AUTH = False` line 487, public `MEDIA_URL` line 493）; `backend/shrine_project/urls.py:123-128`（unauthenticated `media_serve` when not on R2）; `backend/temples/models.py:1600`（`upload_to="goshuin/"`） |
| expected protection | images of non-public Goshuin records are not retrievable without authorization |
| code evidence | `is_public` only filters API listings. Every stored object has a permanent public URL; the BFF uploads under the fixed name `upload.jpg`（`apps/web/src/app/api/my/goshuins/route.ts:43`）, so storage adds only a short random suffix on collision |
| production evidence | which storage backend production uses, and whether bucket listing is disabled: **UNVERIFIED** |
| impact | a leaked or guessed URL exposes a private image indefinitely; the image survives an `is_public` change |
| remediation | private prefix with signed, short-lived URLs（or BFF-proxied access）for non-public images; random object names |
| regression tests | non-public image URL requires a signature; public images unchanged |
| Mother Ship approval | **yes**（storage and cost design） |

### WS-09 — Security settings fail open

| field | value |
| --- | --- |
| severity / status | Medium / POTENTIAL RISK |
| affected | `backend/shrine_project/settings.py:101-109` |
| expected protection | production refuses to start without a secret key and runs with `DEBUG=False` unless explicitly enabled |
| code evidence | `DEBUG = env.bool("DEBUG", default=True)`; when `DJANGO_SECRET_KEY` is unset outside CI / pytest, `SECRET_KEY` becomes the public string `django-insecure-dev-only-secret`. SimpleJWT has no `SIMPLE_JWT` block, so tokens are signed with `SECRET_KEY`; the anonymous-id cookie is signed with it too |
| production evidence | historical（2026-10-18, `dbe686b`）: `DEBUG=False` observed and a secret key inferred as set. Not re-verified: **UNVERIFIED** |
| impact | a missing env var on a redeploy would silently enable debug pages and make JWTs forgeable by anyone |
| remediation | when not running under CI or pytest, raise if `DJANGO_SECRET_KEY` is missing; default `DEBUG` to `False` |
| regression tests | settings import fails without the secret in a production-like environment; `DEBUG` false by default |
| Mother Ship approval | no（deployment checklist update recommended） |

### WS-10 — Any authenticated user can create catalog shrines

| field | value |
| --- | --- |
| severity / status | Medium / CONFIRMED ISSUE, reproduced locally |
| affected | `backend/temples/api/views/shrine.py:273-276`; `backend/temples/api/urls.py:105, 120`; `ShrineWriteSerializer`（`backend/temples/api/serializers/shrine.py:318-345`） |
| expected protection | the public shrine catalog is curated（staff or a review flow such as `shrine-submissions`） |
| code evidence | `get_permissions` returns `IsAuthenticated` for `create`; no staff check; no existing test covers `POST /api/shrines/` |
| local test evidence | anonymous → 401; ordinary user → **201**, one `Shrine` row created; `PATCH` / `DELETE` on the new pk → 405（shadowed route） |
| production evidence | **UNVERIFIED** |
| impact | sign-up is open, so anyone can add catalog entries that appear in public search and possibly recommendations; update / delete are protected only by an accidental route order |
| remediation | restrict `create` / `update` / `destroy` to staff; add explicit tests so the route order is not the protection |
| regression tests | ordinary user create → 403; staff → 201; update / delete → 403 for non-staff |
| Mother Ship approval | **yes**: confirm whether user creation is intended |

### WS-11 — Backend dependency advisories

| field | value |
| --- | --- |
| severity / status | Medium / POTENTIAL RISK（advisory details not reviewed one by one） |
| affected | `backend/requirements.txt`（Django 5.2.16, djangorestframework 3.17.2, Pillow 12.3.0 resolved） |
| evidence | `pip-audit`: Django 5.2.16 → PYSEC-2026-3717, PYSEC-2026-4035（fixed 5.2.17）; DRF 3.17.2 → 3 CVEs（fixed 3.18.2）; Pillow 12.3.0 → about 40 advisories（fixed 13.0.0）. Pillow decodes user uploads（Goshuin validation, icons） |
| production evidence | the deployed backend version: **UNVERIFIED**（no Render access）; GitHub Dependabot state: **UNVERIFIED** |
| remediation | upgrade in a dedicated PR; Pillow 13 is a major version and needs the image-validation tests |
| Mother Ship approval | no |

### WS-12 — Web dependency advisories

| field | value |
| --- | --- |
| severity / status | Medium / POTENTIAL RISK |
| evidence | `pnpm audit --prod`（whole workspace）: 3 Critical, 46 High, 13 Moderate, 3 Low. For `apps/web` runtime: `next`（WS-02）, `sharp`（WS-01）, `axios`（several High: prototype-pollution gadgets, ReDoS, redirect handling）, `follow-redirects`（High）, `dompurify` via `posthog-js`（Critical GHSA-cg2g-xh64-v4q7, client-side, conditional on `SAFE_FOR_TEMPLATES`）, `browserslist`. Most `apps/mobile` entries are build-time Expo CLI dependencies, not the production web runtime |
| remediation | upgrade `axios` / `follow-redirects` / `posthog-js` in a dependency PR; triage the rest against actual use |
| Mother Ship approval | no |

### WS-13 — `places/nearby` throttle keyed on `REMOTE_ADDR`

Low / POTENTIAL RISK. `backend/temples/api/views/search.py:47-55, 80-122` keys anonymous requests on `REMOTE_ADDR`.
Behind Render's proxy that is likely the proxy's address, so all anonymous callers would share one 30/min bucket, and
one client can exhaust it for everyone. Render behaviour: **UNVERIFIED**. Remediation: use the corrected identity from
WS-04. Tests: two clients get independent buckets. Mother Ship: no.

### WS-14 — No HTTPS / cookie hardening settings

Low / POTENTIAL RISK. `settings.py` sets none of `SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT`,
`SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`. The earlier production verification called this
"mitigated" because "the browser only ever reaches the backend via the Vercel BFF"
（`docs/audit/production-environment-configuration-verification.md:212`）. That reasoning is incomplete: browsers do
reach `admin/` on the backend origin, and mobile clients call the backend directly. Remediation: set the proxy header and
secure-cookie settings for production; add HSTS after confirming the TLS setup. Tests: settings check under a
production-like environment. Mother Ship: no.

### WS-15 — Anonymous `shrines/ingest`

Low / POTENTIAL RISK. `backend/temples/api/views/shrine.py:375-409`: `AllowAny`, creates or returns a `Shrine` from a
Google Place ID and calls Google Places; limited by scope `shrines_ingest` 1/min, whose identity is spoofable（WS-04）.
Impact: catalog growth and Places API cost. Remediation: after WS-04, decide whether authentication is required.
Mother Ship: yes（product intent）.

### WS-16 — `LocMemCache` throttle state

Low / POTENTIAL RISK. `backend/shrine_project/settings.py:374-381` uses `LocMemCache`; the comment requires `WEB_CONCURRENCY=1`
（`backend/start.sh:5, 184` defaults to 1）. Production worker count: **UNVERIFIED**. With more than one worker or
instance, every limit multiplies, and a restart resets all counters. Remediation: a shared cache（`django-redis` is
already in `requirements.txt`）before scaling. Mother Ship: yes if it adds infrastructure.

### WS-17 — `DISABLE_THROTTLE` without a production guard

Low / POTENTIAL RISK. `backend/shrine_project/settings.py:351-354` raises every scope except `shrines_ingest` to 1000/min when the env var is
`1`. It does not disable throttling entirely, but nothing prevents it in production. Earlier guidance says it is not
set in production（`docs/audit/beta-stability-80-readiness-audit.md:124`）; **UNVERIFIED** now. Remediation: ignore it
when `DEBUG` is false. Mother Ship: no.

### WS-18 — Username enumeration via public profile

Low / CONFIRMED ISSUE. `backend/temples/api/views/public_profile.py:29-39` returns 404 with `"User not found"` or
`"Profile is not public"`, which tells the caller whether an account exists. Remediation: one identical 404 body.
Tests: both cases return the same body. Mother Ship: no.

### WS-19 — `dangerouslyAllowLocalIP` in the production image config

Low / POTENTIAL RISK. `apps/web/next.config.ts:16-35` enables `dangerouslyAllowLocalIP` and allows
`http://127.0.0.1:8000/media/**` and `http://localhost:8000/media/**`. In production this lets the image optimizer be
pointed at loopback port 8000 paths under `/media/`. It is a narrow surface, but it is a development setting in the
production config. Remediation: enable local patterns only in development builds. Mother Ship: no.

### WS-20 — Logout and JWT lifetimes（existing `SEC-B01`）

Informational / existing. Logout only clears cookies（`apps/web/src/app/api/auth/logout/route.ts:6-12`）and does not
blacklist the refresh token; already tracked as `SEC-B01`（`docs/audit/security-follow-up-backlog.md`）. Additional
observation: there is no `SIMPLE_JWT` setting, so library defaults apply（in SimpleJWT 5.5.1, short access and
refresh lifetimes, no rotation）, while the cookie `Max-Age` values are 1 h and 7 days
（`apps/web/src/lib/server/authCookies.ts:21-23`）. The cookie outlives the token; this is a consistency issue, not an
exposure. Account deletion blacklists every outstanding token（`backend/users/services/account_deletion.py:312-327`）.

### WS-21 — Public debug / schema endpoints and broad `ALLOWED_HOSTS`

Informational / POTENTIAL RISK. `backend/shrine_project/urls.py:47-72, 88-89` exposes `whoami` endpoints that report
only the caller's own state（consistent with `docs/core/runtime-security-baseline.md` §9）; `backend/shrine_project/urls.py:93-117` publishes
the full OpenAPI schema and UIs. `backend/shrine_project/settings.py:414-422` always adds `localhost`, `127.0.0.1`, `0.0.0.0`, `web` and
`.onrender.com` to `ALLOWED_HOSTS`. Remediation: remove the debug routes in production; consider restricting the schema
UI; drop the development hosts when `DEBUG` is false.

### WS-22 — CI coverage gaps（existing）

Informational. CodeQL runs for Python and JavaScript on pull requests to `main` / `develop` and weekly
（`.github/workflows/codeql.yml:7-12, 25`）; dependency review fails on newly introduced High advisories
（`.github/workflows/dependency-review.yml:5, 16`）; Dependabot covers npm, pip and GitHub Actions
（`.github/dependabot.yml`）. Gaps: already-present vulnerable dependencies are not gated（WS-01, WS-02, WS-11, WS-12
reached production）; `gitleaks.json` exists but no workflow or hook runs a secret scanner; repository-level GitHub
secret scanning is **UNVERIFIED**. CodeQL success is not evidence of authorization or throttling correctness.

---

## 6. Controls verified as PROTECTED

| control | evidence |
| --- | --- |
| owner filtering on private records | §4.1 rows（favorites, Goshuin, visits, reflections, journey, threads, submissions, me） |
| public Goshuin listing limited to `is_public` | `backend/temples/api/views/goshuin.py:32-38`; `backend/temples/api/views/goshuin_feed.py:12-16` |
| thread detail isolation | `backend/temples/api/views/concierge.py:120-128`（and the earlier isolation audit） |
| Goshuin image validation | `backend/temples/api/serializers/validators.py:7-43`; allow-list JPEG / PNG / WebP, 10 MB, Pillow `verify()`（`backend/temples/api/serializers/my_goshuin.py:11-15, 25-31`） |
| Stripe webhooks | signature verified, fail closed when the secret is missing（`backend/users/services/stripe_webhook.py:59-81`; `backend/temples/api/views/billing.py:186-211`） |
| account deletion | billing first, fail closed; outstanding tokens blacklisted; storage removal on commit（`backend/users/services/account_deletion.py:312-368`） |
| frontend guard not used as authorization | `apps/web/middleware.ts:5-23` is UX only; backend enforces（§4.3） |
| CORS | explicit allowlist with credentials（code `backend/shrine_project/settings.py:442-454`; production observed 2026-10-18, historical） |
| catalog update / delete | unreachable through the router（405 locally）; see WS-10 for why this is not a designed protection |

---

## 7. Existing versus newly discovered

| item | status |
| --- | --- |
| WS-20（refresh token not blacklisted on logout） | **existing**: `SEC-B01` |
| BFF cookie CSRF（Class A / Class B） | **existing**: CSRF V-1 records（#3319 onward）; not re-assessed |
| Supabase RLS advisory | **existing**: `docs/audit/supabase-security-advisor-rls.md`; not re-assessed |
| WS-14 reasoning | **corrects** the "mitigated" statement in `docs/audit/production-environment-configuration-verification.md:212` |
| WS-01 to WS-13, WS-15 to WS-19, WS-21 | **new in this audit** |
| WS-22 | known context; the gating gap is newly stated |

Dependency findings come from local `pnpm audit` / `pip-audit` runs on 2026-10-25, not from GitHub's alert pages.

---

## 8. Production checks requiring an approved test plan

| check | needs |
| --- | --- |
| WS-03 exposure in production | two dedicated test accounts, their own threads, and a log review plan |
| WS-04 / WS-05 / WS-06 / WS-13 effectiveness | a bounded, pre-agreed request budget against a non-production backend, or Render configuration evidence |
| WS-01 exploitability | not to be tested in production; patch instead |
| WS-08 bucket listing and URL behaviour | owner inspection of the storage configuration |
| WS-09 / WS-14 / WS-16 / WS-17 env and worker values | owner confirmation of presence and values on Render, without copying secrets |

---

## 9. Proposed remediation PRs（separate; none performed here）

| PR | findings | scope | Mother Ship |
| --- | --- | --- | --- |
| R-1 | WS-01 | `sharp` ≥0.35.5; auth, size and format checks in `POST /api/my/goshuins`; tests | recommended（hotfix priority） |
| R-2 | WS-02 | `next` ≥16.4.1 | no |
| R-3 | WS-03 | remove or owner-scope `concierge/thread/?tid=` and its BFF route; tests | no（exposure review: yes） |
| R-4 | WS-04, WS-13, WS-06 | trusted proxy depth, client identity, BFF client address, per-client login limit | **yes**（design） |
| R-5 | WS-05 | scoped throttles for geocode and routes; tests | no |
| R-6 | WS-07 | icon validation and request size limit | no |
| R-7 | WS-09, WS-14, WS-17, WS-21 | settings fail closed; HTTPS / cookie hardening; production guards; debug routes | no |
| R-8 | WS-10, WS-15 | catalog write permissions | **yes**（product intent） |
| R-9 | WS-11 | Django, DRF, Pillow upgrades | no |
| R-10 | WS-12 | axios, follow-redirects, posthog-js upgrades | no |
| R-11 | WS-08 | private image delivery | **yes**（storage design） |
| R-12 | WS-16 | shared throttle cache | yes if infrastructure is added |
| R-13 | WS-18, WS-19, WS-22 | profile 404 body; dev-only image patterns; CI audit / secret scanning | no |

### 9.1 Documentation synchronization（not done here）

- `docs/core/roadmap.md:65, 431` states that Critical / High runtime remediation is complete. WS-01 to WS-05 show new
  Critical / High items; the roadmap and `docs/core/runtime-security-baseline.md` should be updated after Mother Ship
  triage.
- `docs/audit/security-follow-up-backlog.md` could track these items once they are triaged.
- `README.md`'s rate-limit section（lines 476-493）describes scopes but not their identity weakness（WS-04）.

---

## 10. STOP

```text
application / backend code       UNCHANGED
API routes / auth / cookies      UNCHANGED
environment variables            NOT READ; NOT MODIFIED
Vercel                           read-only project and deployment metadata only
Render / database / storage      NOT ACCESSED
production HTTP requests         attempted to documented public endpoints only; blocked by session egress policy
destructive or bulk requests     NONE
test users / production data     NONE created or modified
local verification               throwaway tests and database outside the repository; not committed
PR merge                         NONE
```
