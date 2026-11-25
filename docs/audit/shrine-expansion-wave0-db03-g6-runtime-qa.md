# W0-DB03 G6 Runtime QA

## Status

- Status: `W0_DB03_G6_PASS_4_OF_4`
- Recorded at: `2026-09-25`
- Branch: `audit/w0-db03-g6-runtime-qa`
- Base: `develop@d8211369b4daf5500bcaf07cd0fdfd21a55ad052`
- Gate: `G6 Runtime QA`（`docs/knowledge/shrine-expansion-gate-contract.md` §9）
- Upstream: G4 `W0_DB03_G4_PASS_4_OF_4` / G5 `W0_DB03_G5_PASS_4_OF_4`
- Execution subset: `wave0-012` / `wave0-013` / `wave0-015` / `wave0-016`
- Excluded: `wave0-014 宮城縣護國神社`（G3 `MODEL_CHANGE_REQUIRED`、G4 / G5 / G6 NOT EXECUTED）
- Production access: `NONE`
- G7 Production Import: `NOT EXECUTED`

本書は監査記録のみである。コード・データ・テストは変更していない。

G6 は4つの独立した QA surface を持つ。結果は surface ごと・神社ごとに記録し、1つの PASS へ統合しない。

```text
A. Shrine Detail
B. Concierge shared candidate path
C. Recommendation Reason / Copy
D. Compass distance / direction
```

---

## 1. Isolated runtime state

```text
database : w0db03_g6（本 G6 専用に新規作成）
host     : localhost:5432（サンドボックス内 PostgreSQL 16 + PostGIS）
engine   : django.contrib.gis.db.backends.postgis
lineage  : temples/migrations（標準 GIS lineage）
code     : develop@d821136（working tree clean）
```

| Step | Command | 結果 |
| --- | --- | --- |
| 1 | `migrate --noinput` | EXIT 0 |
| 2 | `bootstrap_production_data` | EXIT 0、3 step すべて SUCCESS、Shrine total 117 |
| 3 | `import_shrine_knowledge wave0_batch_03_seed.json --validate-only` | `validate-only: OK, no errors` |
| 4 | 同 apply | `sources created=4, deities created=18, histories created=5` |

Production への接続・書き込みはない。

### Canonical identity

4社とも `(name_jp, address)` で exactly 1 行へ解決した。同名別住所の行もない。
下表の Shrine id は scratch DB 上のローカル provenance であり、identity としては使用していない。

| candidate_id | name_jp | address | local scratch Shrine id |
| --- | --- | --- | --- |
| wave0-012 | 大神神社 | 奈良県桜井市三輪1422 | 114 |
| wave0-013 | 北野天満宮 | 京都府京都市上京区馬喰町 | 115 |
| wave0-015 | 平安神宮 | 京都府京都市左京区岡崎西天王町97 | 116 |
| wave0-016 | 岡田宮 | 福岡県北九州市八幡西区岡田町1-1 | 117 |

---

## 2. Surface A — Shrine Detail

### Route（repository routing から特定）

```text
GET /api/shrines/<int:pk>/        url name = temples:shrine_detail
  -> temples.api.views.shrine.ShrineViewSet.retrieve   （shrine_project/urls.py -> temples.api.urls）
  -> ShrineViewSet.get_serializer_class()  -> ShrineDetailSerializer
       deities / histories = evidence_gate.decide_detail_display_state() が full / disputed のものだけ
```

`temples/views.py` にも同名の `ShrineViewSet` が存在するが、`/api/shrines/<pk>/` には接続されていない。

Django test `Client` で scratch DB に対して実際に HTTP GET した。

| Shrine | HTTP | deities | histories | 期待 | 自社 Fact のみ | DB 上の全 Fact を返却 | display state | Fact あたり Source | legacy field |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 大神神社 | 200 | 1 | 1 | 1 / 1 | YES | YES | full | 1 | なし |
| 北野天満宮 | 200 | 3 | 1 | 3 / 1 | YES | YES | full | 1 | なし |
| 平安神宮 | 200 | 2 | 2 | 2 / 2 | YES | YES | full | 1 | なし |
| 岡田宮 | 200 | 12 | 1 | 12 / 1 | YES | YES | full | 1 | なし |

- 「自社 Fact のみ」は、返却された各 Fact の id が当該 Shrine の `ShrineDeity` / `ShrineHistory` に属することを DB で照合した結果
- display state は返却された全 Fact を `decide_detail_display_state()` で再判定した結果（全件 `full`）
- `ShrineDetailSerializer` は `sajin` / `description` を出力しない。Knowledge が無い場合は `[]` を返す設計であり、legacy fallback は構造的に発生しない

返却内容:

| Shrine | deities | histories（history_type / title） |
| --- | --- | --- |
| 大神神社 | 大物主大神 | historical_event / 貞観元年の正一位叙位 |
| 北野天満宮 | 菅原道真公 / 中将殿 / 吉祥女 | founding / 天暦元年の創建 |
| 平安神宮 | 桓武天皇 / 孝明天皇 | founding / 明治28年の平安神宮創建、historical_event / 昭和15年の孝明天皇合祀 |
| 岡田宮 | 神日本磐余彦命（神武天皇）/ 大国主命 / 少彦名命 / 県主熊鰐命 / 高皇産霊神 / 神皇産霊神 / 玉留産霊神 / 生産霊神 / 足産霊神 / 大宮売神 / 事代主神 / 御膳神 | tradition / 神武東征に関する岡田宮伝承 |

岡田宮の History は Detail 出力でも `history_type = tradition` のままで、本文も Seed と同一
（「…滞在したと伝えられている。」）。確定史実への変換は行われていない。

```text
DETAIL_RUNTIME = PASS（4 / 4）
```

---

## 3. Surface B — Concierge shared candidate path

```text
build_chat_candidates_with_eligibility(limit=200)
```

`pool_limit = max(200 * 5, 50) = 1000` で 117 Shrine 全体が pool に入る。pool_limit の実装は変更していない。

```text
source_count     = 117
eligible_count   = 4
ineligible_count = 113
```

| Shrine | CANDIDATE_PATH |
| --- | --- |
| 大神神社 | PASS |
| 北野天満宮 | PASS |
| 平安神宮 | PASS |
| 岡田宮 | PASS |

**全体件数は scratch dataset の artifact である。** この DB には W0-DB03 の Knowledge しか投入していないため、
`eligible 4 / ineligible 113` は Production の coverage でも品質 KPI でもない。本 surface の受け入れ条件は
「4社すべてが共有 eligible candidate path に参加すること」だけである。Top1 / Top3 / 順位 / score は要求しない。

```text
CONCIERGE_CANDIDATE_PATH = PASS（4 / 4）
```

---

## 4. Surface C — Recommendation Reason / Copy

共有 builder が返した各候補 dict に対して、Concierge の実経路と同じ関数列を適用した。新しい説明 helper は作っていない。

```text
candidate（build_chat_candidates_with_eligibility の返り値）
  -> concierge_chat._build_score_v3_candidate_profile()
  -> recommendation_input_profile.build_recommendation_input_profile()
  -> recommendation_reason_v4.build_recommendation_reason_v4(
         authority_context = concierge_chat._build_reason_v4_authority_context(candidate))
```

ranking は実行していない。そのため `authority_context.primary_reason_source = "fallback"` であり、interpretation / translation 入力は空である。

### 結果

| Shrine | profile shrine_id | Reason に入った deity | Reason に入った history（primary） | reason_strength（deity / history） | provenance | 他社 Fact | 断定表現 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 大神神社 | 114 | 大物主大神 | 859年、大神神社の神階は正一位となった。 | assertive / assertive | FULLY_KNOWLEDGE_BACKED | 0 | 0 |
| 北野天満宮 | 115 | 菅原道真公、中将殿、吉祥女 | 947年、北野の地に菅原道真公を祀る社として創建された。 | assertive / assertive | FULLY_KNOWLEDGE_BACKED | 0 | 0 |
| 平安神宮 | 116 | 桓武天皇、孝明天皇 | 1895年3月15日、桓武天皇を御祭神として平安神宮が創建された。 | assertive / assertive | FULLY_KNOWLEDGE_BACKED | 0 | 0 |
| 岡田宮 | 117 | 12柱（Detail と同順） | 『古事記』等に結びつく伝承として、…滞在したと伝えられている。 | assertive / **weakened** | FULLY_KNOWLEDGE_BACKED | 0 | 0 |

- profile の deity は当該 Shrine の `ShrineDeity`（sort_order 順）の連結と完全一致し、history は当該 Shrine の sort_order 最小 History と完全一致した
- 他社 Fact: 他 Shrine の deity 名・history 本文が preview 出力に含まれる件数（0）
- provenance は `build_shrine_reason_provenance()`（既存）による。deity / history とも `KNOWLEDGE_USED`
- 断定表現: `必ず / 確実 / 保証 / 叶う / 効果があります / ご利益があります / 絶対 / 成就します / 治ります / 合格します` 等の検出件数（0）

### reason_text（逐語）

```text
大神神社では、大物主大神が祀られています。家内安全・商売繁盛・交通安全・縁結び・病気平癒・厄除けの要素も確認材料になります。この情報は神社を説明する補助情報であり、今回の順位根拠ではありません。相談内容から、今扱いたいテーマを読み取っています。今回は明確な意味的一致が確認できないため、条件に近い候補として整理しています。参拝前に、次に確認したいことを一つだけ決めておきます。
```

他3社も同じ文型である（deity 文 + goriyaku の「要素も確認材料」+ 補助情報の注記 + 既定の Interpretation / Action）。

### Knowledge が Ranking signal にならないこと

- 共有 builder が返す候補 dict に score 系の key は無い（`popular_score` 以外 0）
- reason_text は、ranking の primary reason が無い場合に既存の注記「この情報は神社を説明する補助情報であり、今回の順位根拠ではありません。」を付ける
- Knowledge Fact は Fact / Explanation layer にのみ現れる

### 岡田宮 tradition

- candidate profile の `shrine_history_type = tradition`
- 既存の `_apply_tradition_hedge_floor()` により、confidence = high でも `reason_strength.shrine_history = weakened`（TRADITION_ALWAYS_HEDGED）
- 実際の reason_text は deity 文を採用するため、伝承本文は文章化されない。Fact layer（`fact.shrine_history` / evidence）に保持されるだけで、確定史実として断定する文は生成されない

```text
RECOMMENDATION_REASON = PASS（4 / 4）
```

### 観測事項（非ブロッキング、既存挙動）

補足確認として、岡田宮の同じ tradition Fact を既存 `_build_fact_text()` の history-only 分岐（deity が無い場合の分岐）に通すと、次の文になる。

```text
岡田宮には、『古事記』等に結びつく伝承として、神武天皇と五瀬命が東征の途中に岡田宮の地に滞在したと伝えられていると伝えられています。
```

- hedge は保たれており、確定史実化・断定は無い（TRADITION_ALWAYS_HEDGED 契約は満たす）
- ただし、Fact 本文の末尾「伝えられている」にテンプレートの「と伝えられています」が重なり、文が冗長になる
- 岡田宮では deity 文が優先されるため、**現行 runtime ではこの分岐に到達しない**
- W0-DB03 固有ではない。既存の Knowledge Seed にも末尾が「伝えられている / 伝わる / とされる」の tradition Fact が多数ある（例: W0-DB01 三輪神社 / 大鳥大社 / 烏森神社、W0-DB02 別小江神社）
- `test_tradition_output_contract.py` が固定するのは「tradition は hedge され assertive にならない」ことで、重複表現は契約の対象外

本 PR では修正しない（G6 で runtime コードを変更しない）。Mother Ship への返却事項:

| surface | shrine | actual | expected contract | owning module |
| --- | --- | --- | --- | --- |
| Recommendation Reason（history-only 分岐、現行 W0-DB03 では未到達） | 岡田宮（および既存 tradition Fact 多数） | 「…伝えられていると伝えられています。」 | TRADITION_ALWAYS_HEDGED は充足。重複 hedge の扱いは契約未定義 | `temples/services/recommendation_reason_v4.py::_build_fact_text` |

---

## 5. Surface D — Compass distance / direction

既存の runtime authority をそのまま使った。

```text
distance  : concierge_chat_candidates._distance_m
direction : direction_reference._bearing / _direction_label
            （compass_direction_filter.filter_candidates_by_direction が内部で使うものと同一）
filter    : compass_direction_filter.filter_candidates_by_direction
stage     : compass_recommendation_orchestrator._apply_compass_distance_stage
```

QA 固定 origin（W0-DB01 と同一。実ユーザー位置ではない）:

```text
lat = 35.681236
lng = 139.767125
```

| Shrine | 採用 lat / lng | distance_m | direction | 自方位のみ許可した filter | 自方位以外を許可した filter | distance stage |
| --- | --- | ---: | --- | --- | --- | --- |
| 大神神社 | 34.528817 / 135.852894 | 378,392 | 西 | 残る | 除外 | 60km まで到達・範囲外（error なし） |
| 北野天満宮 | 35.03115 / 135.735003 | 372,709 | 西 | 残る | 除外 | 60km まで到達・範囲外（error なし） |
| 平安神宮 | 35.0164902 / 135.7824269 | 368,847 | 西 | 残る | 除外 | 60km まで到達・範囲外（error なし） |
| 岡田宮 | 33.861611 / 130.767333 | 846,219 | 西 | 残る | 除外 | 60km まで到達・範囲外（error なし） |

- distance は4社とも有限の正の整数
- direction は4社とも既存8方位（北 / 北東 / 東 / 南東 / 南 / 南西 / 西 / 北西）のいずれか
- 自方位のみを `reference_directions` に与えると候補は残り、それ以外の7方位では除外された（filter が座標を正しく評価している）
- distance stage は候補を error なく消費し、15 → 30 → 60km まで拡張したうえで範囲外として除外した

固定 origin から 60km を超えることは G6 の FAIL ではない。G6 が要求するのは、採用座標で distance / direction 計算が成立することである。

Direction Filter、15 / 30 / 60km 閾値、expansion threshold、Compass scoring、purpose mapping は変更していない。

```text
COMPASS_DISTANCE  = PASS（4 / 4）
COMPASS_DIRECTION = PASS（4 / 4）
```

---

## 6. Per-shrine summary

| Shrine | DETAIL_RUNTIME | CONCIERGE_CANDIDATE_PATH | RECOMMENDATION_REASON | COMPASS_DISTANCE | COMPASS_DIRECTION | blocker |
| --- | --- | --- | --- | --- | --- | --- |
| 大神神社 | PASS | PASS | PASS | PASS | PASS | なし |
| 北野天満宮 | PASS | PASS | PASS | PASS | PASS | なし |
| 平安神宮 | PASS | PASS | PASS | PASS | PASS | なし |
| 岡田宮 | PASS | PASS | PASS | PASS | PASS | なし（§4 観測事項は非ブロッキング） |

STOP 条件の評価:

| STOP 条件 | 結果 |
| --- | --- |
| Detail が他社 Fact を返す / 期待 Fact が欠ける | 該当なし |
| 共有 candidate path に入れない | 該当なし |
| legacy field への eligibility fallback が必要 | 該当なし |
| Reason が他社 Fact を使う | 該当なし |
| tradition が確定史実として表現される | 該当なし |
| 宗教的効果・将来結果の確実性が生成される | 該当なし |
| 採用座標で distance / direction が計算できない | 該当なし |
| Ranking / Compass / Eligibility logic の変更が必要 | 該当なし |
| wave0-014 の再導入 | 該当なし |
| Production access が必要 | 該当なし |

---

## 7. Regression

| 範囲 | test | 結果 |
| --- | --- | --- |
| Shrine Detail Knowledge API / serializer | `api/test_shrine_detail_knowledge_api.py` | PASS |
| Shared Recommendation Eligibility | `services/test_shared_recommendation_eligibility.py` / `services/test_recommendation_eligibility_verifier.py` | PASS |
| Concierge candidate builder | `services/test_concierge_build_chat_candidates_contract.py` / `services/test_concierge_chat_candidates_dedupe.py` | PASS |
| Recommendation Reason v4 / tradition | `services/test_recommendation_reason_v4.py` / `services/test_recommendation_reason_v4_authority_alignment.py` / `services/test_tradition_output_contract.py` | PASS |
| Compass direction filter | `services/test_compass_direction_filter.py` | PASS |
| Compass orchestrator | `services/test_compass_recommendation_orchestrator.py` | PASS |
| Compass API contract | `api/test_compass_recommendations_api.py` / `api/test_compass_weekly_api.py` / `api/test_compass_openapi_identity_contract.py` | PASS |

```text
targeted  : 315 passed
backend full suite（CI unit job と同じ NoGIS 設定）: 3994 passed, 12 skipped, 0 failed
makemigrations --check : No changes detected
```

W0-DB03 を通すために書き換えたテストはない。

---

## 8. Global boundaries

```text
Production access          = NONE
Ranking change             = NONE
Eligibility change         = NONE
Compass logic change       = NONE
Evidence Gate change       = NONE
Serializer change          = NONE
Schema / Migration         = NONE
Candidate Master / Base Seed / Knowledge Seed change = NONE
wave0-014                  = G6 NOT EXECUTED
G7 Production Import       = NOT EXECUTED
```

---

## 9. Final

```text
W0_DB03_G6_PASS_4_OF_4

G6_PASS          = wave0-012 / wave0-013 / wave0-015 / wave0-016
G6_NOT_EXECUTED  = wave0-014（upstream G3 MODEL_CHANGE_REQUIRED）
OBSERVATION      = Reason history-only 分岐の重複 hedge（既存挙動・非ブロッキング・Mother Ship 判断待ち）
NEXT             = G7 Production Import（別 PR / 別指示）
```
