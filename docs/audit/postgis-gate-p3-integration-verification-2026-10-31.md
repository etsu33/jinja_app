> **Status: QA record (verification only)**
>
> Gate P3. Verifies the integrated `develop` after Gates P1 and P2: PostGIS and
> GIS-disabled full suites, skip coverage and regressions. No code, test, URL,
> database or migration change.
>
> - Verification date: 2026-10-31
> - Integrated `develop`: `61abfdf11d7ea0cfba77ef035c93b665ca935db4` (#3387 merge)
> - Executed commit: `8c469edf616eb08f7b43632ff363b0063d82e861`. `git diff` between it and
>   `61abfdf` is empty (identical tree), so these runs are evidence for the current HEAD.

# PostGIS / GIS-disabled Integration Verification（Gate P3, 2026-10-31）

## 0. Verdict

**PASS.** Both full suites completed with exit code 0. There are no failures, errors or INTERNALERRORs.
The 19 cases that the `postgis` marker previously skipped by mistake now run on PostGIS without
`FORCE_POSTGIS_TESTS`. The only remaining skips are existing, intended ones.

| Environment | Passed | Failed | Errors | Skipped | Collected | Exit code | Duration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PostGIS (`USE_GIS=1`) | 7416 | 0 | 0 | 5 | 7421 | 0 | 1511.05 s (25:11) |
| GIS-disabled (`USE_GIS=0`) | 7296 | 0 | 0 | 27 | 7323 | 0 | 1009.62 s (16:49) |

## 1. Related PRs (all ancestors of `61abfdf`)

| PR | Gate | Change |
| --- | --- | --- |
| #3383 | P1 | Pre-0108 migration tests (0091 / 0094 / 0099) run on throwaway databases; hardened cleanup |
| #3384 | P2-D | G7 migration preflight assertions follow the active migration lineage |
| #3385 | P2-E1 | Nearby API contract and PostGIS test audit |
| #3386 | P2-E2-A | `test_nearby_api.py` rewritten to the mounted `q`-based `NearestShrinesAPIView` contract |
| #3387 | P2-E2-B | `postgis` marker decided in an autouse fixture after test-database setup |

## 2. Commands and environments

Both suites ran sequentially on the same machine (local PostgreSQL 16.15 + PostGIS 3.4.2, GDAL 3.8,
Python 3.11), using the CI job's environment variables. `--maxfail` was disabled by overriding
`addopts`, and `FORCE_POSTGIS_TESTS` was unset.

| Run | Environment | Command |
| --- | --- | --- |
| PostGIS | `USE_GIS=1`, `IS_PYTEST=1`, `CI=true`, `DATABASE_URL=postgis://…`, no `DISABLE_GIS_FOR_TESTS` | `python -m pytest -o addopts="-p pytest_django -p pytest_env" -q -rfEs -p no:randomly --create-db` |
| GIS-disabled | `USE_GIS=0`, `DISABLE_GIS_FOR_TESTS=1`, `IS_PYTEST=1`, `DATABASE_URL=postgres://…` | same |

The local logs were not modified. After the runs, no temporary `*_mig_*` database remained.

## 3. Skip coverage

### 3.1 PostGIS: before / after

| Skip reason | Before marker fix | After (`8c469ed`) |
| --- | --- | --- |
| `conftest.py:52` "PostGIS is not available in this environment." | 8 in the last full run (`7e7ff37`). On `e0eb429` the same three files gave 19 / 19 skipped in a targeted run | **0** |
| `test_concierge_l1_freetext_readiness.py:268` (existing, data condition) | 4 | 4 |
| `test_gis_smoke.py:11` "GDAL not available locally" (existing, environment) | 1 | 1 |
| **Total** | 13 | **5** |

### 3.2 GIS-disabled: intended skips

| Skip reason | Count |
| --- | --- |
| `postgis` marker, "PostGIS is not available in this environment." (19 Nearby / geographic-query cases and 1 marker lifecycle test) | 20 |
| `test_import_shrines_seed_command.py` location tests ("runs only when USE_GIS is enabled") | 3 |
| `test_concierge_l1_freetext_readiness.py:268` (existing) | 4 |
| **Total** | **27** |

In the GIS-disabled job the `test_gis_*` modules are excluded from collection, as before.

### 3.3 Newly executed on PostGIS (28 cases)

The 19 cases that were previously skipped by mistake:

- `test_nearby_api.py`: 16 cases (7 functions)
  - `test_route_resolves_to_the_keyword_search_view`
  - `test_missing_or_short_q_returns_empty_results_without_calling_places`: `no-params`, `empty-q`, `one-char-q`,
    `one-char-after-strip`, `lat-lng-are-ignored`
  - `test_valid_q_calls_text_search_and_returns_upstream_items_unchanged`
  - `test_empty_upstream_returns_empty_results`: `empty-list`, `no-results-key`, `none`
  - `test_limit_defaults_to_five_and_is_clamped_between_one_and_ten`: `default-5`, `explicit-2`, `capped-at-10`,
    `floored-at-1`
  - `test_full_rerank_when_the_top_result_is_not_a_parent_match`
  - `test_parent_top_result_keeps_google_order_except_the_best_match`
- `test_nearby_query.py::test_knn_order_and_distance_column`, `::test_limit_applied`
- `test_nearest.py::test_nearest_shrines_returns_ordered_results`

New marker regression tests (9 cases, `test_postgis_marker.py`):

- In both environments: backend detection, GIS-disabled skip without database access, extension present / missing,
  **unexpected probe failure propagates** (not converted into a skip), force override, `pg_extension` query, database
  error not swallowed.
- In the PostGIS environment only: `test_marked_test_runs_after_the_test_database_is_set_up`. It shows the probe runs
  against the test database after `django_db_setup`.

### 3.4 Totals reconciliation

- **PostGIS:** the last full run before P2 (`7e7ff37`) was 7380 passed / 1 failed / 13 skipped. Changes since then:
  - +1: the G7 test, failing before, now passes (#3384)
  - +7: the cleanup tests (#3383 hardening)
  - +19: the marker-skipped cases now run (#3386 and #3387)
  - +9: the marker tests (#3387)
  - Result: **7416 passed**. Skips: 13 − 8 = **5**.
- **GIS-disabled:** the previous run was 7288 passed / 15 skipped. Changes since then:
  - `test_nearby_api.py` went from 5 to 16 cases, all skipped here: +11 skipped
  - The marker tests: +8 passed, +1 skipped
  - The cleanup tests are not collected here: 0
  - Result: **7296 passed / 27 skipped**.

## 4. Regression assessment

| Area | PostGIS | GIS-disabled |
| --- | --- | --- |
| Historical migration tests 0091 / 0094 / 0099 (throwaway DB) | passed (0 errors; 26 previously abnormal) | not collected (GIS-only, unchanged) |
| G7 migration preflight (`test_g7_sql_generator_db.py`) | passed (previously 1 failed) | passed |
| Nearby API contract (`test_nearby_api.py`) | 16 passed | 16 skipped (intended) |
| Geographic query (`test_nearby_query.py`, `test_nearest.py`) | 3 passed | 3 skipped (intended) |
| PostGIS marker regression (`test_postgis_marker.py`) | 9 passed | 8 passed, 1 skipped (intended) |
| Whole suite | 0 failed, 0 errors, no INTERNALERROR | 0 failed, 0 errors, no INTERNALERROR |

No new failure, error or unintended skip was found.

## 5. Known limitations

- **Local runs only.** The GitHub backend integration (PostGIS) job runs only on push to `develop` or by
  `workflow_dispatch`, so PRs skip it. This report does not include that job's result for `61abfdf`.
- **Runtime.** The PostGIS full suite took 25:11 locally, against 19:29 for the P1 run. The difference was not
  attributed. It includes the newly executed tests and the throwaway-database migration tests, but local machine
  load was not controlled. The CI job limit is 40 minutes; confirm with the CI run on `develop`.
- `test_gis_smoke.py` is skipped locally (GDAL not found by that smoke check). CI runs it in its own step.
- `test_concierge_l1_freetext_readiness.py:268` (4 skips) is an existing data condition, outside this gate.
- The authoritative contract of `/api/shrines/nearby/` and external consumers remain UNCONFIRMED (#3385). The tests
  pin the current behaviour by Mother Ship decision.

## 6. Core documents

README.md, `docs/core/architecture.md` and `docs/core/roadmap.md` are unchanged: no authoritative contract changed
in Gates P1–P2, which modified tests and test infrastructure only.
