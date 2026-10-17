# NIIGATA-001-H003 C5 Catalog Runtime QA

> Status: **C5 PASS x4 / NOT_AUTHORIZED x1**
>
> Recorded at: 2026-10-17
>
> Base: `develop@ff5a2fb`（PR #3251 merge, C4 Catalog Evidence）
>
> Production write: 0
> Candidate Master write: 0
> Knowledge write: 0
> Recommendation / Ranking / Eligibility change: 0

## 1. Scope

| candidate_id | canonical name | canonical address | C4 | C5 scope |
|---|---|---|---|---|
| nsrc-000011 | 赤城神社 | 新潟県新潟市江南区二本木1丁目7番16号 | PASS | IN_SCOPE |
| nsrc-000012 | 赤城神社 | 新潟県長岡市四郎丸2丁目5番33号 | PASS | IN_SCOPE |
| nsrc-000013 | 赤城神社 | 新潟県長岡市山屋314番地 | PASS | IN_SCOPE |
| nsrc-000014 | 赤城神社 | 新潟県五泉市上杉川1310番地2 | NOT_AUTHORIZED | EXCLUDED（G2 HOLD_POSITION_REVIEW） |
| nsrc-000015 | 赤城神社 | 新潟県魚沼市湯之谷芋川311番地 | PASS | IN_SCOPE |

Adopted coordinates（`docs/audit/niigata-h003-c4-catalog-evidence.md` / `docs/audit/niigata-h003-position-hold-resolution.md`）:

```text
nsrc-000011 = 37.841794, 139.118507
nsrc-000012 = 37.440743, 138.855238
nsrc-000013 = 37.496407, 139.008620
nsrc-000015 = 37.214543, 139.036468
```

Authority:

- `docs/knowledge/shrine-expansion-gate-contract.md` §11A C5
- `docs/knowledge/recommendation-eligibility-contract.md`
- `docs/audit/niigata-h003-c4-catalog-evidence.md`
- `docs/audit/niigata-h003-position-hold-resolution.md`
- `docs/audit/niigata-h003-g2-g3-routing.md`

C5 acceptance（gate contract §11A）:

```text
Shrine Detail basic identity表示 PASS
Shrine list / API basic presence PASS
map / navigation uses adopted coordinate
Concierge recommendation participation = NO
Compass recommendation participation   = NO
```

## 2. Runtime-path audit

`PRODUCT_SURFACE = CATALOG_ONLY` is an audit-level decision. It is **not** a Candidate Master or
runtime field, and no runtime code reads it. Recommendation non-participation therefore has to come
from the existing Shared Recommendation Eligibility gate, which was traced in code:

### 2.1 Shared Recommendation Eligibility（single authority）

`backend/temples/services/concierge_chat_candidates.py`

```text
is_recommendation_eligible(knowledge_deities, knowledge_histories)
  = bool(knowledge_deities) or bool(knowledge_histories)

partition_recommendation_eligible_shrines(shrines)
  -> shrine_knowledge_selector.fetch_fact_ready_knowledge_deities / histories（batch）
  -> is_recommendation_eligible() per Shrine
  -> ineligible Shrines are dropped（not kept with a low score, not used as fallback）
```

Usable Facts come from `shrine_knowledge_selector` → `evidence_gate.decide_fact_usability()`.
Legacy `goriyaku` / `history_theme` are not read by the gate.

### 2.2 Concierge

| Path | Gate |
|---|---|
| `build_chat_candidates()` → `build_chat_candidates_with_eligibility(apply_popularity_pool_limit=False)` | `partition_recommendation_eligible_shrines()` before any candidate dict is built |
| `api_views_concierge._build_chat_candidates_pipeline()`（request-carried `candidates` + built candidates） | `filter_recommendation_eligible_candidates()` re-applies the same gate to request-carried rows by shrine id |

### 2.3 Compass

| Path | Gate |
|---|---|
| `compass_recommendation_orchestrator.get_compass_recommendations()`（legacy purpose path; also used by `weekly_compass_service`） | `build_chat_candidates_with_eligibility()` → `partition_recommendation_eligible_shrines()`; zero eligible → `recommendation_eligibility_zero_candidates` |
| `compass_direction_only_core.get_compass_direction_only_candidates()`（Direction-only） | `partition_recommendation_eligible_shrines()` over the 60 km structural universe; zero eligible → `recommendation_eligibility_zero_candidates` |

Both Compass paths delegate to the shared gate; neither re-implements eligibility.

### 2.4 Detail / List / navigation

| Path | Eligibility dependency |
|---|---|
| `ShrineViewSet.retrieve` → `ShrineDetailSerializer` | none（deities / histories are filtered by `evidence_gate.decide_detail_display_state()`; empty lists are valid） |
| `ShrineViewSet.list` → `ShrineListSerializer` | none（`kind` / name / `q` filters only） |
| web Shrine Detail page directions link | built from Detail API `latitude` / `longitude` via `toValidDestinationCoords()` |

Catalog presence in Detail / List does **not** make a Shrine Recommendation-eligible. No
architectural coupling between Detail/List exposure and Recommendation eligibility was found.

```text
DETAIL_LIST_ELIGIBILITY_COUPLING = NONE
CONCIERGE_GATE                   = SHARED / FAIL_CLOSED
COMPASS_GATE                     = SHARED / FAIL_CLOSED
```

## 3. QA artifacts

| File | Role |
|---|---|
| `scripts/migration_safety/niigata_h003_c5_catalog_runtime_qa.py` | reusable read-only Runtime QA（READ ONLY transaction; exact (name_jp, address) identity）. Same pattern as the G7 Runtime QA scripts |
| `backend/temples/tests/test_niigata_h003_c5_catalog_runtime_qa.py` | disposable-DB regression（9 tests） |

The QA uses real runtime code, not mocked replacements:

- Detail / List: `ShrineViewSet` through `APIClient`（`/api/shrines/<pk>/`, `/api/shrines/?name=赤城神社`）and
  through `APIRequestFactory` in the script.
- Concierge: `build_chat_candidates()`, `build_chat_candidates_with_eligibility()`, and the Concierge
  view pipeline `_build_chat_candidates_pipeline()` with a request-carried target candidate.
- Compass: `get_compass_recommendations(purpose="protection", ...)` and
  `get_compass_direction_only_candidates(...)`. The origin is placed ~2 km south of each target and
  the reference direction is computed from the origin→target bearing, so each target is inside the
  queried direction sector and distance ring（exclusion is not a geometry artefact）.
- Shared verifier: `verify_recommendation_eligibility(shrine_ids=...)` → `INELIGIBLE` for all four.

### 3.1 Materialization（disposable DB only）

The four rows are created only inside the pytest database:

```text
name_jp   = 赤城神社
kind      = shrine
address   = canonical address
latitude  = adopted latitude
longitude = adopted longitude
```

No ShrineDeity / ShrineHistory / goriyaku / goriyaku_tags / history_theme is created for them. The
repository Base Seed is imported as background, so the existing same-name 赤城神社（群馬県）is present
and never resolves as a target. nsrc-000014 is not materialized.

### 3.2 Positive control

To prove the Recommendation paths are live（not trivially empty）, a separate control Shrine
（`C5対照神社`, not an H003 Candidate）with one usable History Fact is placed in the same direction
sector, closer to the origin. The control appears in Concierge candidates and Direction-only Compass
candidates; the H003 target never does. The control exists only in the test database.

### 3.3 Fail-closed sanity

- Attaching a usable History Fact to nsrc-000012 makes the QA script fail（AssertionError）.
- Drifting nsrc-000013's latitude makes the QA script fail.

## 4. Execution results

Disposable pytest database（PostgreSQL 16, nogis migrations）, Python 3.11.

```text
test_niigata_h003_c5_catalog_runtime_qa.py   9 passed
backend full suite（-n auto）                  5952 passed, 8 skipped
ruff check / format                          clean
```

QA script output（`niigata_h003_c5_catalog_runtime_qa.main()`, READ ONLY transaction）:

```text
candidate=nsrc-000011 detail_identity=PASS list_api_presence=PASS adopted_coordinate=PASS (37.841794, 139.118507) concierge_participation=NO compass_participation=NO compass_legacy_state=recommendation_eligibility_zero_candidates compass_direction_only_state=recommendation_eligibility_zero_candidates C5_STATUS=PASS
candidate=nsrc-000012 detail_identity=PASS list_api_presence=PASS adopted_coordinate=PASS (37.440743, 138.855238) concierge_participation=NO compass_participation=NO compass_legacy_state=recommendation_eligibility_zero_candidates compass_direction_only_state=recommendation_eligibility_zero_candidates C5_STATUS=PASS
candidate=nsrc-000013 detail_identity=PASS list_api_presence=PASS adopted_coordinate=PASS (37.496407, 139.008620) concierge_participation=NO compass_participation=NO compass_legacy_state=recommendation_eligibility_zero_candidates compass_direction_only_state=recommendation_eligibility_zero_candidates C5_STATUS=PASS
candidate=nsrc-000015 detail_identity=PASS list_api_presence=PASS adopted_coordinate=PASS (37.214543, 139.036468) concierge_participation=NO compass_participation=NO compass_legacy_state=recommendation_eligibility_zero_candidates compass_direction_only_state=recommendation_eligibility_zero_candidates C5_STATUS=PASS
H003_C5_TARGETS=nsrc-000011,nsrc-000012,nsrc-000013,nsrc-000015
H003_C5_EXCLUDED=nsrc-000014(G2_HOLD_POSITION_REVIEW)
H003_C5_CATALOG_RUNTIME_QA=PASS
TRANSACTION_MODE=READ_ONLY
```

`recommendation_eligibility_zero_candidates` in the script run means the target was in the Compass
candidate source but removed by the shared gate. With the eligible control present（§3.2）, Compass
returns the control and still excludes the target.

## 5. Candidate matrix

| candidate | detail_identity | list_api_presence | adopted_coordinate | concierge_participation | compass_participation | C5_STATUS |
|---|---|---|---|---|---|---|
| nsrc-000011 | PASS | PASS | PASS（37.841794, 139.118507） | NO | NO | PASS |
| nsrc-000012 | PASS | PASS | PASS（37.440743, 138.855238） | NO | NO | PASS |
| nsrc-000013 | PASS | PASS | PASS（37.496407, 139.008620） | NO | NO | PASS |
| nsrc-000014 | — | — | NONE（G2 HOLD） | — | — | NOT_AUTHORIZED |
| nsrc-000015 | PASS | PASS | PASS（37.214543, 139.036468） | NO | NO | PASS |

## 6. Limitations

- C5 is a disposable-DB runtime check. The four rows do not exist in Production yet; Production
  presence is C6 and needs separate Mother Ship authorization.
- The web directions link is verified at the API contract level（Detail returns the adopted
  coordinate; the page passes it to `toValidDestinationCoords()`）. No browser run was performed.
- Top1 / ranking quality is not a C5 criterion and was not evaluated.

## 7. Not changed

```text
Production DB                          NONE
Candidate Master / schema / product_surface field   NONE
Base Seed / Knowledge Seed             NONE
ShrineDeity / ShrineHistory for H003   NONE
goriyaku / history_theme               NONE
Ranking / scoring                      NONE
Recommendation Eligibility rule        NONE
Concierge / Compass runtime            NONE
nsrc-000014                            NONE（G2 HOLD_POSITION_REVIEW preserved）
```

## 8. Closure

```text
nsrc-000011 = C5 PASS
nsrc-000012 = C5 PASS
nsrc-000013 = C5 PASS
nsrc-000014 = C5 NOT_AUTHORIZED（G2 HOLD_POSITION_REVIEW）
nsrc-000015 = C5 PASS

H003_C5_PASS            = 4
H003_C5_NOT_AUTHORIZED  = 1
CATALOG_RECOMMENDATION_BYPASS = NONE
C6 Production Import    = NOT_EXECUTED
C7 CATALOG_READY        = NOT_EXECUTED
STOP                    = TRUE
```
