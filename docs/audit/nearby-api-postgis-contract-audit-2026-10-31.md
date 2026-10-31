> **Status: Audit record (read-only)**
>
> Gate P2-E1. Establishes the current Nearby API contract and the state of the eight
> `postgis`-marked tests before any marker correction. No code, test, URL, marker,
> database or migration change.
>
> - Audit date: 2026-10-31
> - Audited code: `develop` @ `9001a39cff54859554edfa6852c3309c042b6a10` (includes #3383 and #3384)
> - Method: static reading of code and documents; local URL resolution (`django.urls.resolve`,
>   URL-resolver inventory) and import probes in a local process; local forced test run
>   (`FORCE_POSTGIS_TESTS=1`, local PostgreSQL 16 + PostGIS 3.4). No production request.

# Nearby API Contract and PostGIS Test Audit（2026-10-31）

## 0. Conclusion

- **The authoritative contract for a geographic `/api/shrines/nearby` is UNCONFIRMED.** The repository
  carries three mutually inconsistent descriptions of it (§2.3), and the mounted implementation is not a
  geographic search.
- **The mounted `/api/shrines/nearby/` is `NearestShrinesAPIView`, a keyword (`q`) Google Places
  text-search shim.** It ignores `lat` / `lng` and returns `{"results": []}` when `q` is missing.
- **`ShrineNearbyView` does not exist.** `temples/urls.py` imports it, but no class with that name is defined
  in the current tree or found in git history (`git log -S "class ShrineNearbyView"`: no hit).
  `temples/urls.py` is **not included** by the root URLconf and **fails to import**
  (`ImportError: cannot import name 'RouteRequestSerializer' from 'temples.serializers'`).
  Option B is therefore a new implementation, not a restoration.
- **Active geographic search lives elsewhere:** the Map feature uses `/api/places/nearby/`
  (`nearby_search`, Google Places nearby by `lat` / `lng`).
- **No active in-repository consumer of the backend `/api/shrines/nearby/` with `lat` / `lng` was found.**
  The Web BFF route that forwards `lat` / `lng` to it is reachable, but its only in-repo caller chain ends at an
  unreferenced hook (§3). External callers are UNCONFIRMED.
- **The `postgis` marker skips all eight tests because `_has_postgis()` queries the database from
  `pytest_runtest_setup`, where pytest-django blocks database access.** The resulting `RuntimeError` is
  swallowed and returns `False`.
- **Under forced execution, 5 of 8 tests fail and 3 pass.** The 5 failures are the `test_nearby_api.py`
  endpoint tests, which target a contract the mounted view does not implement. The 3 passes test the
  `temples.queries.nearest_shrines` query function directly.

## 1. URL resolution from the project root

- `ROOT_URLCONF = "shrine_project.urls"` (`backend/shrine_project/settings.py:297`).
- The root includes `users.api.urls` (namespace `users_api`) and `temples.api.urls` (namespace `temples`)
  (`backend/shrine_project/urls.py:88-89`).
- `temples.urls` (`backend/temples/urls.py`) is included from nowhere in the codebase (repository-wide
  search for `temples.urls` / `include(` outside tests).
- Resolution probe (local, `USE_GIS=1`):

| Path | Resolves to |
| --- | --- |
| `/api/shrines/nearby/` | `temples:nearby` → `NearestShrinesAPIView` |
| `/api/shrines/nearby` (no slash) | 404 (`APPEND_SLASH = False`) |
| `/api/shrines/nearest/` | `temples:shrine-detail` → `ShrineViewSet.retrieve` with `pk="nearest"` (no `nearest` action exists; a non-integer pk does not match a row) |
| `/api/places/nearby/` | `temples:places-nearby` → `nearby_search` |

## 2. Contract matrix

### 2.1 Mounted endpoints

| Item | `/api/shrines/nearby/` | `/api/places/nearby/` |
| --- | --- | --- |
| Route name | `temples:nearby` | `temples:places-nearby` (+ legacy `places/nearby_search/`, `places/nearby-search/`) |
| View | `NearestShrinesAPIView` (`backend/temples/api/views/shrine.py:116-169`) | `nearby_search` (`backend/temples/api/views/search.py:304-`) |
| Method | GET | GET |
| Query parameters | `q` (used only if ≥ 2 chars), `limit` (default 5, capped 1–10). `lat` / `lng` are ignored | `lat`, `lng` (required floats), `radius` (int, default 1000), `limit` (default 10), `keyword` (default "神社" when no `keyword` / `type`), `type` |
| Response | `{"results": [...]}` with Google Places text-search results, re-ranked | Google Places nearby results (see `places.nearby.types.ts`) |
| Error behaviour | Missing / short `q` → **200 `{"results": []}`**. Non-integer `limit` → unguarded `int()` (not exercised in this audit) | Invalid `lat` / `lng` / `radius` → 400 |
| Authentication | `AllowAny`; JWT / Session optional | `AllowAny`; JWT / Session optional |
| Throttle | Default anon / user throttles (no scope) | `ScopedRateThrottle` + `_apply_places_nearby_throttle` |
| Reachable | Yes | Yes |

### 2.2 Not mounted

| Item | `ShrineNearbyView` |
| --- | --- |
| Referenced at | `backend/temples/urls.py:18` (import) and `:35` (`path("shrines/nearby", ..., name="shrines-nearby")`) |
| Defined | **No** (not in `temples/api_views.py`, not anywhere in the tree, not in git history) |
| Reachable | **No.** `temples.urls` is not included and cannot be imported |

### 2.3 Inconsistent contract descriptions (why the contract is UNCONFIRMED)

| Source | What it says |
| --- | --- |
| `docs/openapi.yaml:39` (manual) | `/api/shrines/nearest/`: "現在地から近い神社（最小情報）", params `lat` / `lng` / `limit`, `distance_m` required |
| `openapi.json:1118` | `/api/shrines/nearest/` (`api_shrines_nearest_retrieve`) |
| `backend/schema.yml:1264` (generated) | `/api/shrines/nearby/` (`operationId: api_shrines_nearest_list`), response `NearestShrinesResponse` (`latitude` / `longitude` / `distance` fields) |
| Implementation | `/api/shrines/nearby/` is a `q` text-search shim; the code comment says "Legacy shim: /api/shrines/nearest/ を JSON 配列で返す", but it returns an object |
| `docs/audit/manual-openapi-contract-drift.md:125` | Already records `/api/shrines/nearest/` as not in urlpatterns and a probable `nearest` → `nearby` rename (inference, not confirmed) |

## 3. Consumer inventory

| Reference | Target | Classification | Evidence |
| --- | --- | --- | --- |
| `apps/web/src/app/api/shrines/nearby/route.ts:14` (BFF route) | backend `/api/shrines/nearby/?lat&lng&limit` | **Reachable but no in-repo caller.** If called, the backend returns `{"results": []}` because `q` is absent (inferred from code) | `docs/audit/bff-backend-call-graph-inventory-2026-10-26.md` R044 |
| `apps/web/src/lib/api/places.ts:28-38` `getNearbyShrines` | BFF `/api/shrines/nearby` | **Unused / unreachable.** Only importer is `src/hooks/useNearbyShrines.ts`, which has no importer | R108 ("module unreferenced") |
| `apps/web/src/lib/api/shrines.ts:27-35` `fetchNearestShrines` | `/shrines/nearest/` | **Test-only** (`src/lib/api/__tests__/shrines.test.ts`, mocked) | R131 ("function unreferenced") |
| `apps/web/e2e/fixtures/mockApi.ts:9`, `e2e/02_nearby_allow.spec.ts:11` | `**/api/shrines/nearby**`, `**/api/shrines/nearest**` route mocks | **Test-only** (Playwright route mocks) | — |
| `apps/web/src/features/map/components/MapNearbyPicker.tsx:65`, `NearbyShrineCardListClient.tsx:124` → BFF `src/app/api/places/nearby/route.ts:25` | backend `/api/places/nearby/` | **Active production consumer** (Map feature) | — |
| `apps/mobile` | — | **No reference** found to `shrines/nearby`, `shrines/nearest` or `places/nearby` | repository search |
| `backend/temples/api/views/shrine.py:56-59` | imports `nearest_queryset`, `nearest_shrines` | **Unused import** (ruff F401) | — |
| `backend/temples/services/geo.py:9` `nearest_shrines` | — | **Uncertain** (separate function; no caller found in non-test backend code) | repository search |
| `ShrineViewSet.PUBLIC_ACTIONS` / serializer branch mention `"nearest"` | — | **Stale reference** (no `nearest` action is defined) | `shrine.py:277, 287` |
| `docs/openapi.yaml`, `openapi.json`, `backend/schema.yml`, the audits above | — | **Documentation reference** (inconsistent, §2.3) | — |
| Concierge / Compass | — | **No reference** to these endpoints or view classes found | repository search |

Runtime usage (production traffic) is not inferred from source code; it is UNCONFIRMED without access logs.

## 4. PostGIS marker root cause

- `backend/temples/tests/conftest.py:24-47`: `_has_postgis()` returns `False` unless `ENGINE` contains
  `postgis` **and** `SELECT 1 FROM pg_extension WHERE extname = 'postgis'` succeeds; any exception returns `False`.
- `conftest.py:50-52`: `pytest_runtest_setup(item)` calls it for every `postgis`-marked item and skips on `False`.
- pytest-django blocks database access outside tests that request the `db` / `transactional_db`
  fixtures or the `django_db` mark, and this hook runs before the test's fixtures. The probe raised
  `RuntimeError: Database access not allowed, use the "django_db" mark, or the "db" or "transactional_db"
  fixtures to enable it.` The `except Exception` turns it into `False`.
- Result: the eight tests are skipped in every environment, including the PostGIS integration job
  (`SKIPPED [8] temples/tests/conftest.py:52: PostGIS is not available in this environment.`).
- `FORCE_POSTGIS_TESTS=1` bypasses the check.

## 5. Eight-test classification

Forced run: `FORCE_POSTGIS_TESTS=1`, PostGIS job environment, on `7b35568`. The test files and the
code under test are unchanged at `9001a39`. Result: **5 failed, 3 passed.**

| Test | Intended behaviour | Current target | Forced result | Matches mounted API? | Meaningful today? |
| --- | --- | --- | --- | --- | --- |
| `test_nearby_api::test_missing_params_returns_400` | No params → 400 | `/api/shrines/nearby/` (shim) | FAILED (`200 == 400`) | No | No as written: the shim answers 200 by design |
| `test_nearby_api::test_basic_within_radius_and_ordered` | lat/lng within radius, distance-ordered | same | FAILED (`[] == ['A_100m', 'B_300m', 'C_600m']`) | No | No as written (shim ignores lat/lng) |
| `test_nearby_api::test_radius_filters_out_far` | radius excludes far rows | same | FAILED (`[] == ['A_100m', 'B_300m']`) | No | No as written |
| `test_nearby_api::test_limit_applied_after_sorting` | limit after sort | same | FAILED (`[] == ['A_100m', 'B_300m']`) | No | No as written |
| `test_nearby_api::test_lon_alias_works` | `lon` alias | same | FAILED (`0 == 3`) | No | No as written |
| `test_nearby_query::test_knn_order_and_distance_column` | KNN order + `distance_m`, 2 km radius | `temples.queries.nearest_shrines` | PASSED | n/a (query function) | Yes, if the query function is kept |
| `test_nearby_query::test_limit_applied` | KNN limit | same | PASSED | n/a | Yes, same condition |
| `test_nearest::test_nearest_shrines_returns_ordered_results` | nearest row first, ~0 m | same | PASSED | n/a | Yes, same condition |

Note: the comment in `test_nearby_api.py:35-36` describes a URLconf (`include("temples.urls")`) that the
repository does not have.

## 6. Options for Mother Ship

| | A. Test the unmounted view directly | B. Mount / restore a geographic Nearby API | C. Align or retire obsolete tests to the current public contract | D. Separate marker correction from endpoint contract changes |
| --- | --- | --- | --- | --- |
| Required changes | Not possible as stated: `ShrineNearbyView` does not exist and `temples.urls` does not import | New view (likely on `nearest_shrines`), URL change, OpenAPI update, tests | Rewrite `test_nearby_api.py` against the shim's actual contract (`q`), or retire the five lat/lng endpoint tests (with a recorded decision) | Fix `_has_postgis()` / marker timing; keep the 3 query-function tests; mark, quarantine or decide the 5 endpoint tests in a separate gate |
| Affected consumers | None | `/api/shrines/nearby/` semantics would change; the only BFF forwarder is reachable with no in-repo caller | None in production; test suite only | None in production |
| Compatibility risk | — | **High:** changes a mounted public endpoint (from `q` text search to lat/lng); external callers UNCONFIRMED | Low (test-only) | Low (test-only), provided the 5 endpoint tests are handled explicitly, not silently skipped |
| Test-coverage impact | — | Restores geographic endpoint coverage, with new code | Removes or replaces coverage of a contract that does not exist today | Restores real coverage of the 3 query-function tests immediately |
| Production behaviour impact | None | **Yes** (new behaviour) | None | None |

## 7. Recommendation (not a selection)

The technically safest sequence is **D, followed by a decision on C**:

1. Correct the marker detection so that the 3 `nearest_shrines` tests actually run in the PostGIS job.
2. In the same or a following gate, Mother Ship decides the fate of the 5 `test_nearby_api.py` endpoint tests,
   since they target a contract with no implementation:
   - retire them, or
   - rewrite them against the current shim contract (C), or
   - keep them as the specification of a future geographic endpoint (B, a product decision).

Option A is not available as stated.

## 8. Documentation discrepancies (reported, not edited)

- `docs/openapi.yaml` and `openapi.json` describe `/api/shrines/nearest/` (lat/lng, `distance_m`), which is not
  mounted. `backend/schema.yml` describes `/api/shrines/nearby/` with lat/lng-style response fields that the
  shim does not return. This is already tracked as open in `docs/audit/manual-openapi-contract-drift.md`.
- `NearestShrinesAPIView`'s comment ("JSON 配列で返す") does not match its object response.
- `README.md:98, 396` describe the Map page's nearby exploration. The Map feature uses `/api/places/nearby/`,
  so the README is not contradicted. `docs/core/architecture.md` and `docs/core/roadmap.md` have no
  Nearby-endpoint contract to correct. **No core document edit is required by this audit.**

## 9. UNCONFIRMED items returned to Mother Ship

1. The intended authoritative contract of `/api/shrines/nearby/` (keyword text search vs. geographic search).
2. Whether any external client (outside this repository) calls `/api/shrines/nearby/` or the BFF
   `/api/shrines/nearby` with `lat` / `lng`. Access logs would be needed: counts and User-Agent only.
3. Whether `temples/urls.py` and the unused Web helpers (`getNearbyShrines`, `useNearbyShrines`,
   `fetchNearestShrines`) should be retired. Out of scope for this audit.
