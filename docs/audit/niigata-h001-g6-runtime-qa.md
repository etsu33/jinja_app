# NIIGATA-001-H001 — nsrc-000004 G6 Runtime QA

## 1. Status

~~~text
candidate_id             = nsrc-000004
candidate_name           = 青海神社
fact_owner               = 青海神社（加茂市）

UPSTREAM_G4              = PASS
UPSTREAM_G5              = PASS / ELIGIBLE

DETAIL_RUNTIME           = PASS
CONCIERGE_CANDIDATE_PATH = PASS
RECOMMENDATION_REASON     = PASS
COMPASS_DISTANCE          = PASS
COMPASS_DIRECTION         = PASS

FORMAL_G6                = PASS

Production access        = NONE
Production write         = NONE
G7 / G8                  = NOT EXECUTED
~~~

- Recorded at: 2026-10-10
- Base: `develop@dd45424266152e8b6262f2576d2d67fcb7d097a4`
- Branch: `audit/nsrc-000004-g6-runtime-qa`
- G6 test commit before this audit record: `69442757edc54c8553f8a04de02c220d78b48b40`
- Upstream G5 audit: `docs/audit/niigata-h001-g5-recommendation-eligibility.md`
- Authority: `docs/knowledge/shrine-expansion-gate-contract.md` §9

本書は `nsrc-000004 / 青海神社（加茂市）` について、
G5 Shared Recommendation Eligibility通過後の現行Runtime責務が壊れていないことを、
pytest isolated PostgreSQL DB上で4 surfaceに分けて確認した記録である。

G6は次の4 surfaceを独立して扱う。

~~~text
A. Shrine Detail
B. Concierge shared candidate path
C. Recommendation Reason / Copy
D. Compass distance / direction
~~~

1つのsurfaceのPASSを別surfaceのPASSとして代用しない。

---

## 2. Governing contract

Gate Contract §9:

### Detail

- expected Deity / Historyが取得可能
- Fact display stateがEvidence Contractと整合
- unrelated shrine Factが混入しない

### Concierge

- shared eligibilityを通過
- candidate pathへ参加可能
- safe Recommendation Evidence pathが存在
- 追加Shrineを必ずTop1にすることをAcceptance Criteriaにしない
- 新規Shrine追加だけを理由にRanking logicを変更しない

### Recommendation Reason / Copy

- Source-backed Factから生成される
- unresolved Model Riskを文章で断定しない
- 別神社のFactを参照しない
- 宗教的効果・未来結果を保証しない
- 神社固有情報とDerived interpretationを混同しない

### Compass

- adopted coordinateでdistance計算成功
- adopted coordinateでdirection計算成功
- 別POIへroutingしない
- 必ずCompass Top1になることをAcceptance Criteriaにしない

Regression Boundary:

~~~text
identity
coordinate
Knowledge Fact
goriyaku / tags
Recommendation mapping
Ranking weights
~~~

---

## 3. Execution scope

~~~text
G6_SCOPE = { nsrc-000004 }
~~~

Canonical identity:

~~~text
name_jp = 青海神社
address = 新潟県加茂市大字加茂字宮山229番地
lat     = 37.65657387
lng     = 139.0536436
~~~

対象外:

| candidate_id | Shrine | State |
|---|---|---|
| nsrc-000001 | 相吉神社 | G2 HOLD_POSITION_REVIEW |
| nsrc-000002 | 青澤神社 | G2 HOLD_POSITION_REVIEW |
| nsrc-000003 | 蒼柴神社 | G2 HOLD_POSITION_REVIEW |
| nsrc-000005 | 青山稲荷神社 | G2 HOLD_POSITION_REVIEW |

上記4社についてG6は実行していない。

---

## 4. Isolated runtime state

Test file:

`backend/temples/tests/test_nsrc_000004_g6_runtime_qa.py`

Execution environment:

~~~text
platform = darwin
Python   = 3.11.13
Django   = 5.2.16

DB_HOST=127.0.0.1
USE_GIS=0
DISABLE_GIS_FOR_TESTS=1

pytest isolated PostgreSQL test DB
Production access = NONE
Production write  = NONE
~~~

Fixture setup:

1. `shrines_seed_clean.json` を isolated DB へ import
2. `--skip-goriyaku-tags` を使用
3. `knowledge_seeds/nsrc_000004_seed.json` を isolated DB へ import
4. canonical `(name_jp, address)` で青海神社を取得
5. 現行Runtime function / APIをそのまま使用

No production DB connection was required.

---

## 5. PostgreSQL isolated pytest result

Executed:

`backend/temples/tests/test_nsrc_000004_g6_runtime_qa.py`

Observed result:

~~~text
collected = 4

test_nsrc_000004_g6_compass_uses_adopted_coordinate_for_distance_and_direction
= PASS

test_nsrc_000004_g6_detail_runtime
= PASS

test_nsrc_000004_g6_concierge_candidate_path
= PASS

test_nsrc_000004_g6_recommendation_reason_is_source_backed_and_safe
= PASS

4 passed
0 failed
total = 6.49s
~~~

Therefore:

~~~text
G6_RUNTIME_TESTS = PASS_4_OF_4
~~~

---

## 6. Surface A — Shrine Detail

Runtime route:

~~~text
GET /api/shrines/<pk>/
~~~

The test used `APIClient` against the isolated DB.

Expected Deity:

~~~text
椎根津彦命
大国魂命
~~~

Expected History:

~~~text
神亀3年の創建
明治5年の三社本殿合殿
~~~

Observed / asserted:

~~~text
HTTP status              = 200
deities                  = 2
histories                = 2
Fact verification_status = source_confirmed
Source relation per Fact = 1
Source verification      = source_confirmed
~~~

Explicit non-membership check:

~~~text
賀茂別雷命
多多須玉依媛命
賀茂建角身命
~~~

The response does not contain the above excluded deity names.

Result:

~~~text
DETAIL_RUNTIME = PASS
~~~

Contract mapping:

| G6 Detail condition | Result |
|---|---|
| expected Deity / History取得可能 | PASS |
| Fact display stateがEvidence Contractと整合 | PASS |
| unrelated shrine Factが混入しない | PASS |

---

## 7. Surface B — Concierge shared candidate path

Runtime path used:

`temples.services.concierge_chat_candidates.build_chat_candidates()`

The QA call used the adopted Shrine coordinate itself as the origin:

~~~text
origin lat = 37.65657387
origin lng = 139.0536436
~~~

This intentionally makes candidate distance deterministic for membership QA.

Observed / asserted:

~~~text
canonical candidate matches = 1

candidate.id        = target Shrine.pk
candidate.shrine_id = target Shrine.pk
candidate.name      = 青海神社
candidate.address   = 新潟県加茂市大字加茂字宮山229番地

candidate.lat       = 37.65657387
candidate.lng       = 139.0536436
candidate.distance_m = 0
~~~

Knowledge carried by the candidate:

~~~text
knowledge_deities  = 2
knowledge_histories = 2
goriyaku_tag_ids    = []
~~~

Expected Knowledge membership:

~~~text
Deity:
- 椎根津彦命
- 大国魂命

History:
- 神亀3年の創建
- 明治5年の三社本殿合殿
~~~

The candidate reaches the current Concierge shared candidate path without
creating or inferring `goriyaku_tags`.

Result:

~~~text
CONCIERGE_CANDIDATE_PATH = PASS
~~~

G6 does not require this Shrine to become Top1 / Top3.
No Ranking logic is changed by this QA.

---

## 8. Surface C — Recommendation Reason / Copy

Existing runtime functions used:

~~~text
candidate
-> concierge_chat._build_score_v3_candidate_profile()
-> recommendation_input_profile.build_recommendation_input_profile()
-> recommendation_reason_v4.build_recommendation_reason_v4()
~~~

No new Recommendation rule or copy template was added.

Candidate profile assertions:

~~~text
deity contains:
- 椎根津彦命
- 大国魂命

primary shrine_history:
神亀3年（726）、青海首一族が加茂山山麓に青海神社を創建した。

goriyaku = None
~~~

Excluded Deity:

~~~text
賀茂別雷命
多多須玉依媛命
賀茂建角身命
~~~

None of the excluded Deity names appear in the candidate deity text or generated reason text.

The Recommendation Reason Fact layer preserves the same Shrine-side values:

~~~text
preview.fact.deity          = current candidate deity text
preview.fact.shrine_history = H1 source-backed content
preview.fact.goriyaku       = None
~~~

The current Reason v4 structure separates:

~~~text
fact
interpretation
action
used_fact
used_interpretation
used_action
~~~

For this G6 execution, no derived translation payload is injected into the Fact assertions.
The tested Shrine Fact values remain those read from the candidate's usable Knowledge.

Forbidden guarantee wording asserted absent from `reason_text`:

~~~text
必ず
確実
保証
叶う
効果があります
ご利益があります
絶対
成就します
治ります
合格します
~~~

Result:

~~~text
RECOMMENDATION_REASON = PASS
~~~

Contract mapping:

| G6 Recommendation Reason / Copy condition | Result |
|---|---|
| Source-backed Factから生成 | PASS |
| unresolved Model Riskを文章で断定しない | PASS |
| 別神社Factを参照しない | PASS |
| 宗教的効果・未来結果を保証しない | PASS |
| Shrine Fact / Derived interpretation責務分離 | PASS |

No claim is made that `goriyaku_tags=[]` provides a Need score.
G6 Reason safety and downstream Need scoring are separate responsibilities.

---

## 9. Surface D — Compass distance / direction

Candidate coordinate entering Compass QA:

~~~text
lat = 37.65657387
lng = 139.0536436
~~~

Fixed QA origin:

~~~text
lat = 35.681236
lng = 139.767125
~~~

Existing runtime authority used:

~~~text
distance:
concierge_chat_candidates._distance_m()

bearing:
direction_reference._bearing()

direction:
direction_reference._direction_label()

filter:
compass_direction_filter.filter_candidates_by_direction()
~~~

Observed / asserted:

~~~text
distance_m is not None
distance_m is int
distance_m > 0
distance_m is finite

0 <= bearing < 360

direction is one of:
北 / 北東 / 東 / 南東 / 南 / 南西 / 西 / 北西
~~~

Direction filter behavior:

~~~text
reference_directions = [calculated own direction]
-> candidate remains

reference_directions = all seven other directions
-> candidate excluded
~~~

The candidate object used by distance and direction calculation is the canonical
青海神社 candidate created from the adopted Base Seed coordinate.
No alternate POI coordinate is substituted by this QA path.

Result:

~~~text
COMPASS_DISTANCE  = PASS
COMPASS_DIRECTION = PASS
~~~

G6 does not require the Shrine to become Compass Top1.

---

## 10. Per-surface summary

| Surface | Result | Blocking finding |
|---|---|---|
| A. Shrine Detail | PASS | NONE |
| B. Concierge candidate path | PASS | NONE |
| C. Recommendation Reason / Copy | PASS | NONE |
| D. Compass distance | PASS | NONE |
| D. Compass direction | PASS | NONE |

~~~text
RUNTIME_BLOCKER = NONE
~~~

---

## 11. Formal G6 decision

Gate Contract §9 conditions were compared against the four isolated runtime tests.

~~~text
DETAIL_RUNTIME             = PASS
CONCIERGE_CANDIDATE_PATH   = PASS
RECOMMENDATION_REASON      = PASS
COMPASS_DISTANCE           = PASS
COMPASS_DIRECTION          = PASS

G6 blocking condition      = NONE
~~~

Formal decision:

~~~text
FORMAL_G6 = PASS
~~~

Meaning:

~~~text
G6 PASS
= G5を通過した青海神社について、
  Detail / Concierge / Recommendation Reason / Compassの
  現行Runtime責務がisolated QAで成立した
~~~

It does not mean:

~~~text
Production Import approved
Production write completed
Recommendation Top1
Compass Top1
Need score quality guaranteed
G7 PASS
G8 CORE_READY
~~~

---

## 12. Regression Boundary

Before this audit document, branch diff against its develop base contains only:

~~~text
backend/temples/tests/test_nsrc_000004_g6_runtime_qa.py
~~~

No runtime implementation was changed to make nsrc-000004 pass.

Boundary:

~~~text
identity               = unchanged
coordinate             = unchanged
Knowledge Fact         = unchanged
goriyaku / tags        = unchanged
Recommendation mapping = unchanged
Ranking weights        = unchanged

Base Seed               = unchanged
Knowledge Seed          = unchanged
Candidate Master        = unchanged
Evidence Gate           = unchanged
Serializer              = unchanged
Schema / Migration      = unchanged
Production config       = unchanged
~~~

G6 is verified against the existing runtime, not achieved by rewriting runtime behavior.

---

## 13. Downstream boundary

~~~text
G6 PASS
!= G7 Production Import PASS
!= G8 CORE_READY
~~~

Not executed here:

~~~text
G7 Production Import Gate
Production import
Production write
G8 CORE READY Closure
~~~

The next gate requires its own scope and explicit Mother Ship decision.

---

## 14. Completion checklist

- [x] PR #3130 merge後の最新developをbaseとして固定
- [x] G6 authorityをGate Contract §9へ固定
- [x] nsrc-000004のみをexecution scopeへ固定
- [x] G2 HOLD 4社をscope外へ固定
- [x] Surface A Shrine Detailをisolated runtimeで検証
- [x] Surface B Concierge candidate pathをisolated runtimeで検証
- [x] Surface C Recommendation Reason / Copyをisolated runtimeで検証
- [x] Surface D Compass distance / directionをisolated runtimeで検証
- [x] PostgreSQL isolated pytest 4 / 4 PASS
- [x] unrelated Shrine Fact混入なし
- [x] unsupported guarantee wordingなし
- [x] adopted coordinateでdistance / direction成立
- [x] Ranking / Score変更なし
- [x] Seed / Candidate Master変更なし
- [x] Production access / writeなし
- [x] Formal G6 = PASS
- [x] G6監査文書を作成
- [ ] PR作成
- [ ] STOP

---

## STOP BOUNDARY

~~~text
FORMAL_G6 = PASS

Do not execute G7 in this G6 audit.
Do not write Production.
Do not modify Ranking / Score.
Do not infer goriyaku_tags.
Do not modify the four G2 HOLD candidates.
~~~
