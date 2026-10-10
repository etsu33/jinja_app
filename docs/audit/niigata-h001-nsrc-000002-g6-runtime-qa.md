# NIIGATA-H001 nsrc-000002 青澤神社 G6 Runtime QA

## 1. Status

~~~text
candidate_id             = nsrc-000002
candidate_name           = 青澤神社
knowledge_shape          = History-only（Deity 0 / History 1）

UPSTREAM_G4              = PASS
UPSTREAM_G5              = PASS / ELIGIBLE

DETAIL_RUNTIME           = PASS
CONCIERGE_CANDIDATE_PATH = PASS
RECOMMENDATION_REASON     = PASS
COMPASS_DISTANCE          = PASS
COMPASS_DIRECTION         = PASS

FORMAL_G6                 = PASS

Production access        = NONE
Production write         = NONE
G7 / G8                  = NOT EXECUTED
~~~

- Recorded at: 2026-10-10
- Base: `develop@585f3625`（PR #3150 merge 後）
- Branch: `audit/nsrc-000002-g6-runtime-qa`
- Upstream G4: `docs/audit/niigata-h001-nsrc-000002-g4-formal-redecision.md`（PR #3149）
- Upstream G5: `docs/audit/niigata-h001-nsrc-000002-g5-recommendation-eligibility.md`（PR #3150）
- Authority: `docs/knowledge/shrine-expansion-gate-contract.md` §9
- Structural pattern: `docs/audit/niigata-h001-g6-runtime-qa.md`（nsrc-000004）。Deity の assertion は流用していない

G6 は次の4 surfaceを独立して扱う。1つのsurfaceのPASSを別surfaceのPASSとして代用しない。

~~~text
A. Shrine Detail
B. Concierge shared candidate path
C. Recommendation Reason / Copy
D. Compass distance / direction
~~~

---

## 2. Execution scope

~~~text
G6_SCOPE = { nsrc-000002 }
~~~

Canonical identity / adopted coordinate:

~~~text
name_jp = 青澤神社
address = 新潟県糸魚川市大字青海2696番地
lat     = 37.00763484
lng     = 137.79024297
~~~

Knowledge Seed: `backend/temples/data/knowledge_seeds/nsrc_000002_seed.json`

~~~text
Deity   = 0
History = 1
  history_type        = regional_context
  title               = 青沢神社の春季祭礼
  content             = 青沢神社では毎年4月第3日曜日に春季祭礼が行われ、前日の宵宮には神楽が奉納される。祭礼当日は神輿・子供みこしの地区巡回、神楽奉納、手踊りが行われる。
  period_text         = 毎年4月第3日曜日
  event_date          = null
  verification_status = source_confirmed
  confidence          = high
~~~

---

## 3. Isolated runtime state

Test file: `backend/temples/tests/test_nsrc_000002_g6_runtime_qa.py`

~~~text
platform = linux (Ubuntu 24.04)
Python   = 3.11.15
Django   = 5.2.16
USE_GIS=0 / DISABLE_GIS_FOR_TESTS=1

pytest isolated PostgreSQL test DB
Production access = NONE
Production write  = NONE
~~~

Fixture:

1. canonical Base Seed（`shrines_seed_clean.json`）を `import_shrines_seed --skip-goriyaku-tags` で import
2. `knowledge_seeds/nsrc_000002_seed.json` を import
3. exact `(name_jp, address)` で青澤神社を解決
4. 現行 Runtime API / function をそのまま使用（実装変更なし）

Result:

~~~text
collected = 4

test_nsrc_000002_g6_detail_runtime                                              = PASS
test_nsrc_000002_g6_concierge_candidate_path                                    = PASS
test_nsrc_000002_g6_recommendation_reason_is_history_backed_and_safe            = PASS
test_nsrc_000002_g6_compass_uses_adopted_coordinate_for_distance_and_direction  = PASS

4 passed
~~~

isolated test DB での target Shrine PK は 123（Production id ではない）。

---

## 4. Surface A — Shrine Detail

~~~text
GET /api/shrines/<target pk>/   (APIClient)
~~~

実測:

~~~text
HTTP status                 = 200
deities                     = []
histories                   = 1
history.title               = 青沢神社の春季祭礼
history.history_type        = regional_context
history.verification_status = source_confirmed
history.sources             = 1
source.url                  = https://matsuri.geo-itoigawa.com/calendar/m04/
source.verification_status  = source_confirmed
~~~

Unrelated Fact 混入なし: response の History id 集合は target Shrine の `ShrineHistory` id 集合（1件）と一致する。

Unsupported deity name absent（response 全体）:

~~~text
沼河比賣命
沼河比売命
~~~

~~~text
DETAIL_RUNTIME = PASS
~~~

| G6 Detail condition | Result |
|---|---|
| expected Deity / History取得可能（Deity 0 / History 1） | PASS |
| Fact display stateがEvidence Contractと整合 | PASS |
| unrelated shrine Factが混入しない | PASS |

---

## 5. Surface B — Concierge shared candidate path

Runtime: `temples.services.concierge_chat_candidates.build_chat_candidates()`

Origin は membership QA を決定的にするため adopted coordinate そのもの（37.00763484, 137.79024297）。

実測:

~~~text
matches (name AND address)  = 1

candidate.id                = target Shrine.pk
candidate.shrine_id         = target Shrine.pk
candidate.name              = 青澤神社
candidate.address           = 新潟県糸魚川市大字青海2696番地
candidate.lat               = 37.00763484
candidate.lng               = 137.79024297
candidate.distance_m        = 0

candidate.knowledge_deities = []
candidate.knowledge_histories = 1  (regional_context / 青沢神社の春季祭礼)
candidate.goriyaku_tag_ids  = []
~~~

~~~text
CONCIERGE_CANDIDATE_PATH = PASS
~~~

Top1 / Top3 は要求していない。Ranking logic は変更していない。

---

## 6. Surface C — Recommendation Reason / Copy

Runtime chain（template 追加・変更なし）:

~~~text
candidate
-> concierge_chat._build_score_v3_candidate_profile()
-> recommendation_input_profile.build_recommendation_input_profile()
-> recommendation_reason_v4.build_recommendation_reason_v4()
~~~

Candidate profile 実測:

~~~text
deity                     = None
shrine_history            = H1 content（凍結値と完全一致）
shrine_history_type       = regional_context
shrine_history_confidence = high
~~~

Reason Fact layer 実測:

~~~text
preview.fact.deity          = None
preview.fact.shrine_history = H1 content（凍結値と完全一致）
preview.fact.goriyaku       = None
~~~

`history_type = regional_context` は `_apply_tradition_hedge_floor()` の対象（`tradition`）ではない。
confidence = high のため reason_strength は assertive のままで、現行 `_build_fact_text()` の assertive 分岐の文になる。

実測 `reason_text`（現行 Runtime の出力そのまま）:

~~~text
青澤神社には、青沢神社では毎年4月第3日曜日に春季祭礼が行われ、前日の宵宮には神楽が奉納される。祭礼当日は神輿・子供みこしの地区巡回、神楽奉納、手踊りが行われるという背景があります。この情報は神社を説明する補助情報であり、今回の順位根拠ではありません。相談内容から、今扱いたいテーマを読み取っています。今回は明確な意味的一致が確認できないため、条件に近い候補として整理しています。参拝前に、次に確認したいことを一つだけ決めておきます。
~~~

Pin した既存契約の挙動:

~~~text
reason_text contains "青澤神社には、{H1 content（末尾「。」除去）}という背景があります。"
reason_text does not contain "と伝えられています"（tradition hedge は出ない）
~~~

Absent（reason_text）:

~~~text
unsupported deity : 沼河比賣命 / 沼河比売命
guarantee phrases : 必ず / 確実 / 保証 / 叶う / 効果があります / ご利益があります / 絶対 / 成就します / 治ります / 合格します
~~~

~~~text
RECOMMENDATION_REASON = PASS
~~~

| G6 Recommendation Reason / Copy condition | Result |
|---|---|
| Source-backed Factから生成（History H1） | PASS |
| unresolved Model Riskを文章で断定しない（祭神を出さない） | PASS |
| 別神社のFactを参照しない | PASS |
| 宗教的効果・未来結果を保証しない | PASS |
| 神社固有情報とDerived interpretationを混同しない | PASS |

History-only Reason は有効。Deity を G6 PASS の条件にしていない。
deity / goriyaku / Need mapping / 宗教的効果は推定していない。

観測（判定に影響しない）: interpretation / action は相談文脈が空のため fallback 文
（`quality.fallback_reason_rate = 1.0`）。G6 は Reason の安全性と Fact 由来を確認するもので、
相談適合の品質は対象外。

---

## 7. Surface D — Compass distance / direction

Candidate coordinate entering Compass QA: `lat = 37.00763484 / lng = 137.79024297`（Surface B と同じ canonical candidate）。

Fixed QA origin: `lat = 35.681236 / lng = 139.767125`

Runtime authority:

~~~text
concierge_chat_candidates._distance_m()
direction_reference._bearing()
direction_reference._direction_label()
compass_direction_filter.filter_candidates_by_direction()
~~~

実測:

~~~text
distance_m = 230429   (int, > 0, finite)
bearing    = 310.37671196996786   (0 <= bearing < 360)
direction  = 北西
~~~

Direction filter:

~~~text
reference_directions = [北西]                         -> candidate remains
reference_directions = [北, 北東, 東, 南東, 南, 南西, 西] -> candidate excluded
~~~

別 POI の座標は使っていない。Compass Top1 は要求していない。

~~~text
COMPASS_DISTANCE  = PASS
COMPASS_DIRECTION = PASS
~~~

---

## 8. Formal G6 decision

| Surface | Result | Blocking finding |
|---|---|---|
| A. Shrine Detail | PASS | NONE |
| B. Concierge candidate path | PASS | NONE |
| C. Recommendation Reason / Copy | PASS | NONE |
| D. Compass distance | PASS | NONE |
| D. Compass direction | PASS | NONE |

~~~text
RUNTIME_BLOCKER = NONE
FORMAL_G6       = PASS
~~~

~~~text
G6 PASS
!= G7 Production Import PASS
!= G8 CORE_READY
!= Recommendation Top1
!= Compass Top1
~~~

---

## 9. Tests

| check | 結果 |
|---|---|
| `test_nsrc_000002_g6_runtime_qa.py` | 4 passed |
| nsrc-000002 G4 / G5 / G6（3 file） | 14 passed |
| Recommendation Reason（`test_recommendation_reason_v4.py` / `_authority_alignment.py` / `test_recommendation_reason_quality_knowledge_properties.py`） | 65 passed |
| Shared Eligibility（`test_recommendation_eligibility_verifier.py` / `test_shared_recommendation_eligibility.py` / `test_signal_authority_eligibility_contract.py` / `test_w0_db01_eligibility_reproduction.py`） | 72 passed |
| Compass direction（`test_compass_direction_filter.py` / `test_direction_reference.py` / `test_compass_direction_only_core.py`） | 91 passed |
| Shrine Detail Knowledge API（`api/test_shrine_detail_knowledge_api.py`） | 22 passed |
| `scripts/tests` | 685 passed |
| backend full suite | 4938 passed, 12 skipped |
| `makemigrations --check` | No changes detected |
| ruff / black（新規 test） | PASS |
| `git diff --check` | clean |

---

## 10. Regression boundary

本 audit record を追加する前の branch diff（develop 比）は
`backend/temples/tests/test_nsrc_000002_g6_runtime_qa.py` の1 file だけ。

Runtime 実装は変更していない。次はすべて unchanged:

~~~text
identity / coordinate / Knowledge Fact / Knowledge Seed / Base Seed / Candidate Master
goriyaku / goriyaku_tags / Recommendation mapping / Ranking / Score / weights
Recommendation templates / Evidence Gate / Serializer / Concierge logic / Compass logic
models / migrations / Production configuration
~~~

---

## 11. Not executed

~~~text
G7 Production Import
Production access / write
Candidate Master lifecycle transition
G8 CORE READY
~~~

次の gate は Mother Ship の明示判断を要する。
