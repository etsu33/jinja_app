# NIIGATA-001-H002 — nsrc-000006 赤井神社 G6 Runtime QA

## 1. Status

```text
candidate_id             = nsrc-000006
candidate_name           = 赤井神社
address                  = 新潟県佐渡市加茂歌代2662番地
knowledge_shape          = History-only（Deity 0 / History 3）

UPSTREAM_G4              = PASS / CLOSED
UPSTREAM_G5              = PASS / ELIGIBLE

DETAIL_RUNTIME           = PENDING_CI_MEASUREMENT
CONCIERGE_CANDIDATE_PATH = PENDING_CI_MEASUREMENT
RECOMMENDATION_REASON    = PENDING_CI_MEASUREMENT
COMPASS_DISTANCE         = PENDING_CI_MEASUREMENT
COMPASS_DIRECTION        = PENDING_CI_MEASUREMENT
IDENTITY_FAIL_CLOSED     = PENDING_CI_MEASUREMENT

FORMAL_G6                = PENDING_CI_MEASUREMENT

runtime implementation change = NONE
Ranking / Score change        = NONE
Production access             = NONE
Production write              = NONE
G7 / G8                       = NOT EXECUTED
```

- Recorded at: 2026-10-14
- Base: `develop@66c30edf0034b1aee2048995ef2fbf900dd70db0`
- Branch: `qa/nsrc-000006-g6-runtime-qa`

## 2. Authority / upstream

Authority:

- `docs/knowledge/shrine-expansion-gate-contract.md` §9
- `docs/knowledge/recommendation-eligibility-contract.md`

Upstream:

- `docs/audit/niigata-h002-nsrc-000006-g4-knowledge-materialization.md`
- `docs/audit/niigata-h002-nsrc-000006-g5-recommendation-eligibility.md`
- `docs/audit/shrine-position/niigata-h002-akai-jinja-position-resolution.md`

G6 evaluates four independent surfaces:

```text
A. Shrine Detail
B. Concierge shared candidate path
C. Recommendation Reason / Copy
D. Compass distance / direction
```

A PASS on one surface is not substituted for another.

## 3. Isolated runtime setup

The regression imports current repository data unchanged:

```text
import_shrines_seed
  --source backend/temples/data/shrines_seed_clean.json
  --skip-goriyaku-tags

import_shrine_knowledge
  backend/temples/data/knowledge_seeds/nsrc_000006_seed.json
```

Target identity:

```text
name_jp = 赤井神社
address = 新潟県佐渡市加茂歌代2662番地
lat     = 38.085938
lng     = 138.418312
```

Production is not connected.

## 4. Surface A — Shrine Detail

Expected API:

```text
GET /api/shrines/<target-pk>/
HTTP 200

deities   = 0
histories = 3
```

Expected History / Source relation:

```text
H1 regional_context
4月16日の赤井神社例祭と鬼太鼓奉納
-> https://sado-geinou.com/geinou/kamoutashiro/

H2 tradition
元日午前0時の鬼太鼓奉納
-> https://sado-geinou.com/geinou/kamoutashiro/

H3 regional_context
加茂の五神社としての記録
-> https://dl.ndl.go.jp/pid/971197
```

All Fact / Source verification statuses must remain `source_confirmed`.

Historical S3 names must not appear as current Deity runtime output:

```text
素盞嗚尊
別雷尊
倉稲魂命
菅原道真公
```

## 5. Surface B — Concierge shared candidate path

Runtime authority is the existing shared layer:

```text
build_chat_candidates()
  -> shared Recommendation Eligibility
  -> Concierge / Compass downstream consumers
```

The target's own adopted coordinate is used as QA origin to make candidate membership deterministic:

```text
lat = 38.085938
lng = 138.418312
```

Expected target candidate:

```text
exact target match count = 1

id / shrine_id = target pk
name            = 赤井神社
address         = 新潟県佐渡市加茂歌代2662番地
lat / lng       = 38.085938 / 138.418312
distance_m      = 0

knowledge_deities = []
knowledge_histories =
  regional_context / 4月16日の赤井神社例祭と鬼太鼓奉納
  tradition        / 元日午前0時の鬼太鼓奉納
  regional_context / 加茂の五神社としての記録

goriyaku_tag_ids = []
```

G6 does not require Top1 or Top3.

## 6. Concierge responsibility boundary

`api_views_concierge._build_chat_candidates_pipeline()` applies the same shared eligibility filter after
merging request-supplied candidates with built candidates.

This G6 does not duplicate or change the eligibility rule.

```text
SHARED_ELIGIBILITY_OWNER
= temples.services.concierge_chat_candidates

CONCIERGE_VIEW
= consumer / request-candidate re-gate

RANKING_CHANGE
= NONE
```

The target-specific QA proves the candidate emitted by the shared layer already has the correct identity,
coordinate, usable Knowledge, and no inferred goriyaku tags.

## 7. Surface C — Recommendation Reason / Copy

Expected unchanged chain:

```text
candidate
-> _build_score_v3_candidate_profile()
-> build_recommendation_input_profile()
-> build_recommendation_reason_v4()
```

The current runtime is expected to select the first target History in Knowledge order:

```text
H1:
赤井神社の4月16日の例祭では、加茂歌代の上組・中組・下組の鬼太鼓が神社で舞を奉納した後、各地区を門付けする。
```

Required safety:

- `deity = None`;
- Source-backed target History only;
- H2/H3 are not silently substituted into H1 reason;
- historical Deity names are not promoted into current Deity text;
- no efficacy / future-result guarantee.

G6 does not change Recommendation templates to force a preferred copy.

## 8. Surface D — Compass responsibility boundary

Compass receives the candidate after shared eligibility.

G6 measures only the existing geographic responsibilities:

```text
adopted coordinate
-> distance
-> bearing
-> direction label
-> direction filter
```

QA origin:

```text
35.681236, 139.767125
```

Required:

- distance is finite integer > 0;
- bearing is in [0, 360);
- direction label is valid;
- matching direction retains target;
- the other seven direction labels exclude target.

```text
COMPASS
!= Recommendation Eligibility owner

COMPASS_TOP1
= NOT_REQUIRED
```

No alternate POI coordinate is used.

## 9. Fail-closed / identity isolation

Canonical runtime identity:

```text
赤井神社 / 新潟県佐渡市加茂歌代2662番地
```

Research-observed noncanonical identities:

```text
赤井神社 / 新潟県佐渡市加茂歌代2622番地
赤井神社 / 新潟県佐渡市加茂歌代1164-7
```

Required result:

```text
canonical candidate = exactly one target
2622                = UNRESOLVED
1164-7              = UNRESOLVED
no eligibility inheritance
no runtime candidate address substitution
```

## 10. Acceptance matrix

| Surface | Pre-CI result |
|---|---|
| Detail: Deity 0 / History 3 | PENDING |
| Detail: exact Fact-Source relations | PENDING |
| Detail: no historical Deity promotion | PENDING |
| Concierge: exact candidate once | PENDING |
| Concierge: adopted coordinate | PENDING |
| Concierge: History 3 / Deity 0 | PENDING |
| Concierge: no inferred goriyaku tags | PENDING |
| Reason: target Source-backed H1 | PENDING |
| Reason: no current Deity inference | PENDING |
| Reason: no efficacy guarantee | PENDING |
| Compass: distance | PENDING |
| Compass: direction | PENDING |
| Compass: matching keeps / other seven exclude | PENDING |
| Identity fail-closed | PENDING |
| Runtime implementation change | NONE |
| Ranking / Score change | NONE |
| Production | NONE |

## 11. Files / data changed

```text
backend/temples/tests/test_nsrc_000006_g6_runtime_qa.py   ADDED
docs/audit/niigata-h002-nsrc-000006-g6-runtime-qa.md      ADDED
```

Not modified:

```text
Base Seed
Knowledge Seed
Candidate Master
Position
Evidence Gate
Shared Eligibility implementation
Recommendation Reason implementation
Ranking / Score
Concierge runtime
Compass runtime
models / migrations
Production
other H002 candidates
```

## 12. Current classification

```text
FORMAL_G6       = PENDING_CI_MEASUREMENT
G7              = NOT_EXECUTED
PRODUCTION_WRITE = NONE
STOP            = TRUE
```

If any surface fails, G6 becomes HOLD. Do not modify unrelated runtime logic to make the target pass.

## 13. STOP

Do not execute G7 in this PR.
Do not connect to or write Production.
