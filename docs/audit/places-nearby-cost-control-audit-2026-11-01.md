> **Status: Read-only audit（no code / env / API key / Google Cloud change）**
>
> - Audit date: 2026-11-01
> - Base: `develop` @ `419bbdd`（includes #3397 `google-places-cost-audit-2026-11.md`）
> - Scope: `GET /api/places/nearby/`（and its legacy aliases）, the Web callers, the Backend upstream calls, throttling,
>   and a 100-user volume model.
> - No production request and no Google API call were made. No secret, production env value or user coordinate is
>   recorded here.

# Places Nearby GET — Cost & Rate-Limit Audit（2026-11-01）

## 0. Verdict

**Before scaling to 100 test users, the dominant risk is not normal usage; it is rate-limit design.**

**Normal usage:**

- Normal usage is a few thousand Google requests per month at most (§5).
- One Web visit to `/map` normally makes one Google request.

**Rate-limit design:**

1. **The DRF `places-nearby` scope is a no-op on this view (CONFIRMED).** The only effective limit is a hand-written
   cache throttle keyed by `REMOTE_ADDR` for anonymous callers (WS-13, still open).
2. **No Backend response cache:** every allowed request goes to Google (CONFIRMED).
3. **The BFF turns every non-2xx response, including 429 and the kill switch's 503, into `200 {results: []}`
   (CONFIRMED).** Users see "no shrines", and the client cannot back off.
4. **Production values are UNKNOWN:**
   - throttle rate (`THROTTLE_PLACES_NEARBY`)
   - New vs Legacy selection (`PLACES_API_NEW`)
   - kill switch (`GOOGLE_PLACES_ENABLED`)
   - API-key restrictions and Google Cloud quota caps
   - New API SKU prices and the final billed SKU composition (Legacy base prices are documented in §4)

   Cost scenarios remain request-count estimates; the documented Legacy base prices do not establish final billed cost because additional data SKUs may apply.

## 1. Caller and request-flow inventory

### 1.1 Backend routes（runtime URL resolver, local `django.setup()`; CONFIRMED）

| Path | View | `throttle_classes` | Effective `throttle_scope` on the view class |
| --- | --- | --- | --- |
| `/api/places/nearby/` | `temples/api/views/search.py` `nearby_search` | `[ScopedRateThrottle]` | **None** |
| `/api/places/nearby_search/`, `/api/places/nearby-search/` | `nearby_search_legacy`（wraps `nearby_search`） | `[ScopedRateThrottle]` | **None** |
| `/api/shrines/nearby/` | `NearestShrinesAPIView`（`q`-based keyword search, #3385） | defaults | None |

- `temples/urls.py` (`places/nearby_search/`, `shrines/nearby`) is **not mounted**. `shrine_project/urls.py:88-89`
  includes only `users.api.urls` and `temples.api.urls`.

### 1.2 Web callers（CONFIRMED by static search of `apps/web/src`; Mobile has no Nearby caller）

| Caller | Endpoint | Mounted? |
| --- | --- | --- |
| `features/map/components/NearbyShrineCardListClient.tsx` | BFF `GET /api/places/nearby` → Django `/api/places/nearby/` | **Yes**: `MapPageClient.tsx:30,58` renders it while `mode === "nearby"`（`/map`, no place selected） |
| same component via `features/explore/components/NearbySection.tsx` | same | **No**: `showNearbyList` defaults to `false` (`ExploreLayout.tsx:42,72`) and no caller sets it |
| `features/map/components/MapNearbyPicker.tsx` | BFF `/api/places/nearby` | **No importer**（unused） |
| `hooks/useNearbyShrines.ts` → `lib/api/places.ts:28-30` | BFF `/api/shrines/nearby` | **No importer**（unused） |

### 1.3 Request flow（the mounted path）

```text
Browser /map（nearby mode）
  requestCurrentPosition()  enableHighAccuracy=false, maximumAge=60000（lib/geo/currentPosition.ts:24-26）
  └─ failure → FALLBACK 東京駅 (35.681236, 139.767125)（NearbyShrineCardListClient.tsx:15, 83-85）
  fetch /api/places/nearby?lat&lng&limit=10   cache: "no-store"（:111-127）
    ▼
BFF app/api/places/nearby/route.ts
  djFetch(/api/places/nearby/?{qs}, cache: "no-store", clientIdentityFrom: req)（:25-29）  — no auth forwarded
  non-2xx / fetch error / bad JSON → 200 {results: []}（:36-57）
    ▼
Django nearby_search（search.py:318-409）
  ① manual throttle（:322-324 → :80-122）
  ② kill switch GOOGLE_PLACES_ENABLED（:326-328）
  ③ PLACES_API_NEW=="1" and keyword=="神社" → Places API (New) searchText（:348-357）
       transient error → Legacy fallback（:242-273）
  ④ otherwise / fallback → Places API (Legacy) nearbysearch（:359-379）
       INVALID_REQUEST → sleep 1.2 s, retry once（google_places.py:375-386）
  ⑤ server-side filter + distance sort; no cache write（:383-409）
```

### 1.4 Triggers per mounted component（CONFIRMED by code reading）

| Trigger | Google requests | Evidence |
| --- | --- | --- |
| Initial load: geolocation resolves, or falls back | 1 | `:70-93`, `:162-166` |
| Same coordinates again in the same mount | 0（`lastKeyRef` dedupe） | `:99-101` |
| Coordinate change | 1 each | geolocation is read once per mount (`:70-93`); there is no watch, so this happens only on remount |
| Map move / pan | **0**: no map-move-driven fetch exists on this path | no handler found |
| Remount: select a search result, then clear it; leave `/map` and return | 1 per remount（the ref is per instance） | `MapPageClient.tsx:30,58`; `lastKeyRef` is a `useRef` |
| Manual refresh button | 1 per click（the dedupe key is cleared）; disabled while loading | `:213-218`, `:174` |
| Client retry | 0（none implemented） | `:128-158` |
| Abort on unmount / supersede | the browser request is aborted; **the BFF → Django → Google chain is not cancelled** (inference from `fetch` semantics) | `:103-105`, `:165` |
| React StrictMode double mount | development only | — |

## 2. Cache and duplicate-request analysis

| Layer | Behaviour | Status |
| --- | --- | --- |
| Browser | `fetch(..., {cache: "no-store"})`; the only dedupe is `lastKeyRef` inside one mount | CONFIRMED |
| Geolocation | `maximumAge: 60000` → a fix up to 60 s old is reused; coordinates are sent at full precision | CONFIRMED |
| BFF | `cache: "no-store"`, no in-memory cache | CONFIRMED |
| Django view | **No response cache.** `text_search` uses `@cache_page(60*5)` (`search.py:229-239`); `nearby_search` has none | CONFIRMED |
| `GP.nearby_search` / `nearby_search_new` | Direct HTTP; no cache | CONFIRMED |
| Upstream multiplicity | Legacy: up to **2** calls per request（INVALID_REQUEST retry）. New: 1 call, plus **1 Legacy** call on a transient error. Whether a failed New call is billed: UNKNOWN | CONFIRMED（code）/ UNKNOWN（billing） |
| Photos | The BFF drops `photo_reference`, so Nearby causes no Place Photo calls | CONFIRMED |

**Duplicate sources that a cache would remove:**

- Remounts at the same spot.
- Repeated manual refresh.
- Users who denied geolocation: all of them query the same fallback coordinates (東京駅).

The cache key would have to be quantized coordinates plus `radius` / `keyword` / `type` / `limit`. Full-precision
coordinates would almost never hit.

**HYPOTHESIS:** Google Maps Platform terms restrict caching of Places content other than `place_id`. Any cache needs a
terms review first. The terms could not be read: see §6.

## 3. Throttle and abuse-risk assessment

### 3.1 What actually limits `GET /api/places/nearby/`

| Mechanism | Identity | Effective? | Evidence |
| --- | --- | --- | --- |
| DRF `ScopedRateThrottle`（WS-04 identity） | `bff:` / `edge:` / `remote:` | **No.** `nearby_search.throttle_scope = "places-nearby"` (`search.py:412, 433`) is set on the function object returned by `@api_view`. The view class (`WrappedAPIView`) has `throttle_scope = None`, so the scoped throttle allows everything | CONFIRMED（runtime introspection: `cls.throttle_scope=None`） |
| Global `AnonRateThrottle` / `UserRateThrottle` | WS-04 / user pk | **No.** `@throttle_classes([ScopedRateThrottle])` replaces the defaults for this view | CONFIRMED |
| Manual throttle `_apply_places_nearby_throttle` | authenticated: `user:<pk>`; anonymous: `REMOTE_ADDR` or `"anon"` (`:47-55`) | **Yes, the only one.** Sliding 60 s window in the Django cache, `N` read from `places-nearby` (`:80-122`) | CONFIRMED |
| `temples/api/throttles.py` `PlacesNearbyThrottle` | `REMOTE_ADDR` | Not referenced anywhere（dead） | CONFIRMED |

**Configuration:**

- Default `places-nearby: 30/min` (`settings.py:324`).
- `THROTTLE_PLACES_NEARBY` overrides it (`:359-360`). **The production value is UNKNOWN.**
- `DISABLE_THROTTLE=1` relaxes it to `1000/min` (`:368-370`). **The production value is UNKNOWN.**
- The cache is `LocMemCache`, so every count is per process (`:390-396`). `WEB_CONCURRENCY` in production is UNKNOWN.

**429 behaviour:**

- Django returns `429 {"detail": "Request was throttled..."}` with no `Retry-After` header (`:112-117`).
- The BFF converts it to `200 {results: []}` (`route.ts:48-57`), and the UI renders an empty list.
- The same happens for the kill switch's `503 PLACES_DISABLED`.
- Rejected requests make no Google call, because the throttle runs before the kill-switch check and the upstream
  call (`:322-328`).

### 3.2 Identity in production

- The BFF forwards no auth. Every Web request therefore reaches Django as anonymous, and the manual throttle keys it
  by `REMOTE_ADDR`.
- The WS-04 design records `REMOTE_ADDR` on Render as the platform proxy address. The consequence is "every client in
  one bucket"（`ws04-throttle-client-identity-design-2026-10-25.md` §3.1, row A）. That production behaviour is
  **HYPOTHESIS**: Render hop behaviour is still open as MD-1.
- WS-04 deliberately left these `REMOTE_ADDR`-keyed Nearby throttles to **WS-13**（MD-4）, which is still open.

### 3.3 Abuse scenarios

| Scenario | Effect | Status |
| --- | --- | --- |
| One client sends `N`/min of anonymous requests directly to Render | Fills the (probably shared) anonymous bucket. **Every Web user then gets empty results**（a DoS on Nearby）. Cost is capped by that bucket | CONFIRMED（mechanism）/ HYPOTHESIS（shared bucket） |
| Many accounts each send `N`/min with JWT directly to Render | One bucket per `user:<pk>`, so cost scales with the number of accounts; signup is open | CONFIRMED（mechanism） |
| `limit` parameter | Not clamped. It is sent as New `maxResultCount` (`:337`, `google_places.py:763-772`); an out-of-range value presumably fails upstream → 502 | CONFIRMED（no clamp）/ UNKNOWN（upstream response） |
| Kill switch | `GOOGLE_PLACES_ENABLED=0` stops all Places upstream calls (`google_places.py:150-162`, `search.py:326-328`) | CONFIRMED（code）; production value UNKNOWN |

**Theoretical cost ceilings (per process, sustained for 30 days):**

- **Anonymous:** one bucket of `N`/min → `N × 43,200` requests/month. At the default `N = 30`: **1,296,000**.
- **Authenticated:** the same ceiling, per account.
- Legacy retries can double each figure.

## 4. Google Cloud quota and key restrictions

| Item | Evidence available here | Status |
| --- | --- | --- |
| Project / API in use | `google-places-cost-audit-2026-11.md`: project `strong-imagery-467113-s5`, Places API (Legacy), 3 requests in the 7 days to 2026-11-01 | CONFIRMED（#3397） |
| New API in production | That record shows Legacy only. Whether `PLACES_API_NEW=1` is set: UNKNOWN | UNKNOWN |
| Which key is used | Keys 2 / 3 attribution is UNKNOWN（#3397）. The Backend reads the first non-empty of six env names (`google_places.py:53-62`) | UNKNOWN |
| API restriction (key limited to the Places APIs) | Not visible | UNKNOWN |
| Application restriction (server IPs) | Not visible; whether Render egress IPs are static is also UNKNOWN | UNKNOWN |
| Daily per-API quota cap (hard stop) | Not visible | UNKNOWN |
| Budget | JPY 1,000/month alert. It notifies only and does not cap spending（#3397） | CONFIRMED |
| Legacy Nearby Search and Places Details base SKU prices / free monthly caps | Google Maps Platform official global pricing list (checked 2026-11-01): Nearby Search **5,000 free uses/month, USD 32/1,000** in the first paid tier (through 100,000); Places Details **5,000 free uses/month, USD 17/1,000** in that tier. These are **SKU-level**, not project-wide, free usage caps. | VERIFIED (published prices, not actual invoice) |
| Legacy additional data SKUs | Nearby Search (Legacy) cannot restrict returned fields and can trigger Basic Data, Contact Data and Atmosphere Data SKU billing alongside the Nearby Search base SKU. Actual SKU mix and billed amount are not verified. | VERIFIED (billing rule) / UNKNOWN (actual charge) |
| Places API (New) Text Search pricing / free usage | New API prices and the billing tier triggered by the present FieldMask are outside this Legacy pricing verification. | UNKNOWN |


**Official sources (reviewed 2026-11-01):**

- Global pricing: https://developers.google.com/maps/billing-and-pricing/pricing (Places API Legacy; prices in USD, quoted tier through 100,000 uses).
- Legacy SKU details: https://developers.google.com/maps/billing-and-pricing/sku-details/legacy (Nearby Search base SKU plus possible additional Places Data SKUs).
- Nearby Search (Legacy) documentation: https://developers.google.com/maps/documentation/places/web-service/legacy/search-nearby (returned fields are not field-mask-selectable).

**FieldMask on the New path:** `places.id`, `displayName`, `formattedAddress`, `location`, `types`
(`google_places.py:755-761`). This deliberately excludes rating, photos and opening hours. The SKU tier it lands in is
UNKNOWN until the pricing documentation is checked.

## 5. Monthly volume model for 100 users（explicit assumptions）

**Assumptions:**

- Only `/map` in nearby mode calls Google (§1.2).
- Calls per visit = 1 initial + remounts + manual refreshes.
- Legacy retry rate is treated as an upper-bound multiplier.
- Fallback-coordinate users are counted like everyone else (no cache exists).

| Scenario | Visits / user / month | Google calls per visit | Calls / user / month | **100 users / month** | With worst-case ×2 retry |
| --- | --- | --- | --- | --- | --- |
| Light | 4 | 1.2 | 4.8 | **480** | 960 |
| Moderate | 13（about 3 a week） | 1.5 | 19.5 | **1,950** | 3,900 |
| Heavy test use | 30（daily） | 2.0 | 60 | **6,000** | 12,000 |
| Abuse ceiling（§3.3, default N, 1 process） | — | — | — | **1,296,000** | 2,592,000 |

**Monthly cost:** `max(0, calls − F) × P / 1,000`, where:

- `F` is the free monthly cap of the billed SKU;
- `P` is the price per 1,000 requests for that SKU.

For **Legacy Nearby Search base SKU only**, the official global price list reports `F = 5,000` free uses/month and `P = USD 32` per 1,000 in the first paid tier (through 100,000 uses). However, the full billed cost can include other data SKUs, SKU-specific free caps, taxes/exchange rates, and New API or error/retry calls; those remain **UNKNOWN**. The formula is illustrative, not an invoice estimate.

**Reading the table:**

- Under the **Legacy Nearby Search base SKU only**, light and moderate scenarios (480 and 1,950) are below its published 5,000-use monthly free cap; heavy testing (6,000) exceeds it by 1,000 uses, before any retries. **Do not interpret this as zero total cost**, because additional data SKUs and other requests can be billed.
- The abuse ceiling exceeds normal volume by two to three orders of magnitude. **That gap is the real cost exposure,
  and only the rate limit and a Google-side quota cap bound it.**

## 6. Findings

| ID | Finding | Class |
| --- | --- | --- |
| N-1 | DRF `places-nearby` scope is a no-op on the Nearby views; the global anon/user throttles are also bypassed | CONFIRMED |
| N-2 | The only limit is the manual throttle keyed by `REMOTE_ADDR` (anonymous) or `user:<pk>`; WS-13 is open | CONFIRMED |
| N-3 | Anonymous Web users probably share one bucket in production (Render `REMOTE_ADDR` = proxy) → Nearby DoS by one client | HYPOTHESIS（MD-1 unverified） |
| N-4 | No Backend or Web response cache; every allowed request reaches Google | CONFIRMED |
| N-5 | The BFF maps 429 / 503 / errors to `200 {results: []}`; no `Retry-After`, no client back-off | CONFIRMED |
| N-6 | Remounts and manual refresh each cost one Google request; aborting does not stop the upstream call | CONFIRMED（code）/ HYPOTHESIS（no upstream cancel） |
| N-7 | Legacy INVALID_REQUEST retry and New→Legacy fallback can double calls per request | CONFIRMED（code）/ UNKNOWN（billing of failed New calls） |
| N-8 | `limit` is not clamped before `maxResultCount` | CONFIRMED |
| N-9 | `google_places.req_history` is an unbounded module-level list holding request params, including location, for every call (`google_places.py:16, 33-38, 201`). It is not exposed, but grows for the process lifetime | CONFIRMED |
| N-10 | Production `THROTTLE_PLACES_NEARBY`, `DISABLE_THROTTLE`, `PLACES_API_NEW`, `GOOGLE_PLACES_ENABLED`, `WEB_CONCURRENCY` | UNKNOWN |
| N-11 | Key restrictions, quota caps, actual SKU mix and New API prices | UNKNOWN; Legacy base SKU prices VERIFIED (§4) |
| N-12 | Dead code: `PlacesNearbyThrottle`, `MapNearbyPicker`, `useNearbyShrines` (no runtime effect) | CONFIRMED |
| N-13 | Nearby triggers no photo calls; there is no map-move-driven fetching | CONFIRMED（no issue） |

## 7. Minimal remediation proposals（separate PRs; none implemented here）

| PR | Change | Addresses | Notes |
| --- | --- | --- | --- |
| **R-1**（WS-13） | Make the Nearby throttle effective with WS-04 identity: set the scope on the view class (e.g. a small `APIView`, or a scoped throttle subclass with a fixed scope), drop the manual `REMOTE_ADDR` throttle, and keep the global anon throttle | N-1, N-2, N-3 | Same pattern as `places-resolve`（#3394）. Tests: scope active, per-identity buckets, 429 before upstream |
| **R-2** | BFF propagates 429 / 503 (or an explicit `throttled` / `disabled` flag) instead of `200 []`; the UI shows a retry-later state, and manual refresh gets a short cooldown | N-5, N-6 | UI copy only; no product-behaviour change |
| **R-3** | Short-TTL Backend cache for Nearby, keyed by quantized coordinates (e.g. ~100 m) + `radius` / `keyword` / `type` / `limit` | N-4, N-6 | **Blocked on a Google Maps Platform terms review**（caching limits）. Quantization also reduces precise-coordinate retention |
| **R-4** | Clamp `limit` to the documented range before calling New; bound or remove `req_history` outside tests | N-8, N-9 | Small, independent |
| **R-5**（ops, owner） | In Google Cloud: restrict the server key to the Places APIs, set a per-API daily request quota (a hard stop, unlike the budget alert), and record which key / API is live. Confirm `GOOGLE_PLACES_ENABLED=0` as the emergency stop | N-10, N-11 | No code. The evidence-gathering steps follow #3397 |
| R-6 | Remove the dead Nearby code | N-12 | Hygiene; optional |

**Suggested order before 100 users:** R-5 (quota cap) → R-1 → R-2. R-3 waits for the terms review.

## 8. Limitations

- Static analysis plus local runtime introspection only. No production logs or Google metrics beyond #3397.
- The original coding session could not access `developers.google.com`; a subsequent independent review verified **Legacy base SKU** prices and free caps using the official published pricing documentation (see §4). **New API prices, the actual invoice and caching terms remain unverified here.**
- The volume model is assumption-driven. Replace it with the `nearby_fetch` analytics event counts
  (`apps/web/src/lib/analytics/searchEvents.ts:26, 202`) once they are available.

## 9. Core documents

README.md, `docs/core/architecture.md` and `docs/core/roadmap.md` are unchanged: no canonical behaviour or priority
changes. The remediation PRs above should update them when they land.
