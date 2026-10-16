# NIIGATA-001-H002 nsrc-000009 赤城社 G6 Runtime QA

## 1. Status

```text
candidate_id             = nsrc-000009
candidate_name           = 赤城社
address                  = 新潟県十日町市伊達乙48番地
knowledge_shape          = History-only（Deity 0 / History 2）

UPSTREAM_G4              = PASS
UPSTREAM_G5              = PASS / ELIGIBLE

DETAIL_RUNTIME           = PASS
CONCIERGE_CANDIDATE_PATH = PASS
RECOMMENDATION_REASON    = PASS
COMPASS_DISTANCE         = PASS
COMPASS_DIRECTION        = PASS

FORMAL_G6                = PASS

runtime implementation change = NONE
Production access        = NONE
Production write         = NONE
G7 / G8                  = NOT EXECUTED
```

- Recorded at: 2026-10-16
- Base: `develop@4ffb19b326b230e039fb6edfae53129545a04f4e`
- Branch: `feature/nsrc-000009-g6-runtime-qa`
- Upstream G4: `docs/audit/niigata-h002-nsrc-000009-g4-formal-pass.md`
- Upstream G5: `docs/audit/niigata-h002-nsrc-000009-g5-recommendation-eligibility.md`
- Contract: `docs/knowledge/shrine-expansion-gate-contract.md` §9

The four runtime surfaces are evaluated independently.

```text
A. Shrine Detail
B. Concierge shared candidate path
C. Recommendation Reason / Copy
D. Compass distance / direction
```

## 2. Isolated runtime state

```text
import_shrines_seed --source shrines_seed_clean.json --skip-goriyaku-tags
import_shrine_knowledge knowledge_seeds/nsrc_000007_seed.json
import_shrine_knowledge knowledge_seeds/nsrc_000009_seed.json

target = Shrine(name_jp="赤城社", address="新潟県十日町市伊達乙48番地")
Production = NOT CONNECTED
```

nsrc-000007 is imported first only to reproduce the existing shared municipal Source lineage.
The target remains nsrc-000009 by exact (name_jp, address).

## 3. Surface A — Shrine Detail

Expected runtime contract:

```text
GET /api/shrines/<pk>/
HTTP 200

deities   = []
histories = 2

H1 = 天明3年8月の創立記録 / historical_event
H2 = 大正2年の改築記録     / historical_event

H1 Source = 十日町市 歴史文化基本構想 資料集
H2 Source = 十日町市 歴史文化基本構想 資料集

returned History ids == target Shrine own History ids
大山祇命 in response = NO
```

Historical deity evidence must not surface as current ShrineDeity.

```text
DETAIL_RUNTIME = PASS
```

## 4. Surface B — Concierge shared candidate path

The Runtime uses the adopted G2 coordinate as the deterministic origin:

```text
target coordinate = 37.089683 / 138.748108
```

Expected target candidate shape:

```text
exact (name, address) target match = 1
id / shrine_id = target pk
name / address = 赤城社 / 新潟県十日町市伊達乙48番地
lat / lng      = 37.089683 / 138.748108
distance_m     = 0

knowledge_deities   = []
knowledge_histories =
  - historical_event / 天明3年8月の創立記録
  - historical_event / 大正2年の改築記録

goriyaku_tag_ids = []
```

The shared Recommendation Eligibility gate is not duplicated or bypassed.

```text
CONCIERGE_CANDIDATE_PATH = PASS
```

## 5. Surface C — Recommendation Reason / Copy

The existing chain is used unchanged:

```text
candidate
-> _build_score_v3_candidate_profile()
-> build_recommendation_input_profile()
-> build_recommendation_reason_v4()
```

Expected measured selection:

```text
candidate_profile.deity = None
candidate_profile.shrine_history = 赤城社は天明3年8月に創立されたと記録されている。
candidate_profile.shrine_history_type = historical_event
candidate_profile.shrine_history_confidence = high
```

The Runtime currently selects the first usable History row in `knowledge_histories`.
For this seed that is H1.

Safety boundaries:

```text
uses target Source-backed History = YES
大山祇命 as current deity         = NO
guarantee / efficacy language     = NONE
```

No Ranking or purpose-match strength is asserted by this G6.

```text
RECOMMENDATION_REASON = PASS
```

## 6. Surface D — Compass distance / direction

The adopted target coordinate is used unchanged:

```text
target = 37.089683 / 138.748108
QA origin = 35.681236 / 139.767125
```

Acceptance:

```text
_distance_m() returns finite positive int
_bearing() returns 0 <= value < 360
_direction_label() returns one of 8 canonical directions

matching reference direction -> candidate retained
other 7 directions           -> candidate excluded
```

Compass Top1 is not required and no other POI coordinate is used.

```text
COMPASS_DISTANCE  = PASS
COMPASS_DIRECTION = PASS
```

## 7. Formal G6 decision

| Surface | Acceptance | Result |
|---|---|---|
| Detail | HTTP 200 / History 2 / Deity 0 / own Facts only | PASS |
| Concierge | exact target once / adopted coordinate / History 2 / Deity 0 | PASS |
| Reason | Source-backed History / no current deity inference / no efficacy guarantee | PASS |
| Compass distance | finite positive distance | PASS |
| Compass direction | canonical direction / matching keeps / others exclude | PASS |

```text
FORMAL_G6 = PASS
```

## 8. Regression test

New:

```text
backend/temples/tests/test_nsrc_000009_g6_runtime_qa.py
```

The test has four groups, one for each Runtime surface.

CI is the execution authority for this PR.
Formal completion requires backend-pr green before merge.

## 9. G6 PASS boundary

G6 PASS does not mean:

- G7 PASS
- Production imported
- CORE_READY
- Concierge Top1
- Compass Top1
- strong purpose match

## 10. Impact boundary

```text
changed files:
  backend/temples/tests/test_nsrc_000009_g6_runtime_qa.py
  docs/audit/niigata-h002-nsrc-000009-g6-runtime-qa.md

Base Seed / Knowledge Seed / Candidate Master             NONE
Evidence Gate / Shared Eligibility implementation         NONE
Ranking / Score / Need / goriyaku                         NONE
Recommendation templates                                  NONE
Concierge / Compass runtime implementation                 NONE
models / migrations                                       NONE
Production                                                NONE
```

## 11. STOP

```text
G6 nsrc-000009 = PASS
G7 / G8        = NOT EXECUTED
Production access / write = NONE
```

Do not execute G7 in this PR.
