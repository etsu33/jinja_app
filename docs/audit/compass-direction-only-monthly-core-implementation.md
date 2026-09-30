# Compass Monthly Direction-only Core — Implementation Note

## Status

```text
STATUS           = IMPLEMENTED（Core のみ。HTTP / Frontend への接続は未実施）
TYPE             = BACKEND SERVICE + TESTS + DOCS
PUBLIC_API       = UNCHANGED（Monthly / Weekly の request・response schema は変更なし）
OLD_WIRING       = UNCHANGED（get_compass_recommendations(purpose=...) は従来どおり）
CONCIERGE        = UNCHANGED（候補生成・ranking・API の挙動は変更なし）
MIGRATION        = NONE
BASE             = develop @ a5768c97f1e40184b1e3b5c9fc503cb5ff4015c7（PR 作成前に develop @ 9fe25c2b を merge）
RECORDED_AT      = 2026-09-30
```

正本（本 PR はこれらを解釈し直していない）:

- `docs/product/compass-product-contract.md`（Section 0.1 / 3 / 3-A / 10 / 11）
- `docs/product/compass-direction-only-candidate-universe-decision.md`
- `docs/product/compass-direction-only-ranking-weekly-theme-decision.md`
- `docs/knowledge/recommendation-eligibility-contract.md`
- `docs/audit/compass-purpose-runtime-dependency.md`（§12 PR-C に対応）
- `docs/audit/weekly-snapshot-purpose-removal-production-collision.md`（Weekly は本 PR の対象外）

---

## 1. 変更したファイル

| ファイル | 種別 | 内容 |
|---|---|---|
| `backend/temples/services/compass_direction_only_core.py` | 新規 | Direction-only Core 本体（purpose を受け取らない） |
| `backend/temples/services/compass_distance_stage.py` | 新規 | 15 / 30 / 60km distance stage の唯一の実装（旧 orchestrator から移設） |
| `backend/temples/services/compass_recommendation_orchestrator.py` | 変更 | distance stage の定義を削除し、新 module から同じ名前で import（挙動は同一） |
| `backend/temples/services/concierge_chat_candidates.py` | 追加のみ | 共有層に `partition_recommendation_eligible_shrines()` を追加（既存関数は無変更） |
| `backend/temples/tests/services/test_compass_direction_only_core.py` | 新規 | Product Contract test（51件） |
| `docs/audit/compass-direction-only-monthly-core-implementation.md` | 新規 | 本文書 |

変更していないもの:

- `api_views_compass.py`、Monthly / Weekly の HTTP schema、serializer
- Frontend 全体（`CompassClient.tsx` / `CompassPurposeSelector.tsx` / `compassPurposes.ts` を含む）
- Weekly API・Weekly Snapshot model・migration・Weekly Theme
- Analytics / Free・Premium / billing
- kyusei 計算・Monthly Fallback の方位計算
- Concierge の Recommendation weight・semantic ranking・候補生成
- DB schema

### 既存 file の diff の範囲

- `concierge_chat_candidates.py`
  - 74 行の**追加のみ**で、既存行の変更・削除は 0。
  - `build_chat_candidates()` / `build_chat_candidates_with_eligibility()` / `is_recommendation_eligible()` / `filter_recommendation_eligible_candidates()` は1文字も変えていない。
- `compass_recommendation_orchestrator.py`
  - `DISTANCE_STAGE_*` 定数と `_apply_compass_distance_stage` を `compass_distance_stage.py` へ移し、同じ名前で import し直した。
  - 移設した code は byte 単位で同一であることを移設時に機械的に確認した（違いは、コメント内の関数名の参照1箇所だけ）。
  - 定数は `noqa: F401` 付きで re-export しているので、既存 test の `compass_orch.DISTANCE_STAGE_3_KM` などはそのまま動く。
  - 移設で未使用になった `typing.Sequence` の import を削除した。

---

## 2. アーキテクチャ

```text
get_compass_direction_only_candidates(origin, direction_context)   ← purpose 引数なし
  │
  ├─ NoCommonDirectionResult                    -> no_common_direction（DB を読まない）
  ├─ direction_context が Mapping でない          -> direction_filter_unavailable（DB を読まない）
  ├─ origin 不正 / referenceDirections 不正        -> direction_filter_unavailable（DB を読まない）
  │      方位の妥当性は filter_candidates_by_direction([], ...) の None 契約に判定させる
  │
  ├─ STRUCTURAL_BASE（exclude_qa_fixture_shrines + 座標 NOT NULL + address <> ''）
  ├─ lossless bounding box（DB 側。人気順・LIMIT なし）
  ├─ exact distance_m <= 60000（Python 側。共有候補層の _distance_m）   = U60
  ├─ partition_recommendation_eligible_shrines(U60)（共有層）
  │      source_count > 0 かつ eligible_count == 0   -> recommendation_eligibility_zero_candidates
  ├─ filter_candidates_by_direction（既存の Direction authority）
  │      0件（U60 自体が0件の場合を含む）              -> direction_zero_candidates
  ├─ apply_compass_distance_stage（15 / 30 / 60km）       = ACTIVE_SET
  └─ rank_active_set: distance_m ASC、完全一致時のみ shrine_id ASC
                                                          -> recommendation_success
```

### 内部結果 `CompassDirectionOnlyResult`

| field | 内容 |
|---|---|
| `state` | 下表の state |
| `candidates` | ranking 済み候補（成功時のみ） |
| `direction_context` | runtime の direction context（`no_common_direction` では None） |
| `source_candidate_count` | U60 の件数（STRUCTURAL_BASE ∩ 60km 以内） |
| `eligible_candidate_count` | U60 のうち Shared Eligibility を通過した件数 |
| `direction_candidate_count` | そのうち方位 sector に入る件数 |
| `distance_candidate_count` | ACTIVE_SET の件数 |
| `distance_stage_km` | ACTIVE_SET を決めた ring（15 / 30 / 60） |

候補 1 件の field（Public Projection が使う事実・位置の field だけ）:

```text
shrine_id, id, name, address, latitude, longitude, distance_m,
knowledge_deities, knowledge_histories
```

- 推薦理由（semantic reason / breakdown / score）は生成しない。
- Knowledge Fact は事実表示のために運ぶだけで、ranking には使わない。

### State

state の文字列は旧 Monthly と同じ値を使い、cutover で公開 state が変わらないようにした（test で文字列の一致を固定）。

| 状況 | state |
|---|---|
| 年盤・月盤の共通方位が空（Group B） | `no_common_direction` |
| origin / direction 入力が不正・不足（Group A） | `direction_filter_unavailable` |
| U60 に Shrine はあるが Eligibility を満たすものが0件 | `recommendation_eligibility_zero_candidates` |
| Eligibility 通過はあるが方位内に0件 / U60 が0件（60km 以内に Shrine なし） | `direction_zero_candidates` |
| 1件以上 | `recommendation_success` |

- purpose が存在しないため `invalid_purpose` は発生しない。
- semantic Recommendation を実行しないため `evidence_zero_candidates` も発生しない。
- Group A（unavailable）は DB を読む前に判定する。候補の件数によって unavailable かどうかが変わることはない（test で query 0 を固定）。

---

## 3. 候補母集団（STRUCTURAL_BASE → U60）

```text
STRUCTURAL_BASE = exclude_qa_fixture_shrines(Shrine.objects.all())
                  .filter(latitude IS NOT NULL, longitude IS NOT NULL)
                  .exclude(address = '')
```

- QA fixture の除外は既存 authority（`shrine_qa_fixture_exclusion.exclude_qa_fixture_shrines`）をそのまま使う。除外規約を Compass 側に書き直していない（test で固定）。
- `popular_score` / purpose / need / goriyaku / Recommendation score / Knowledge 件数 / LIMIT は membership 条件に入らない。
- 候補 SQL の `FROM` 以降に `popular_score` / `LIMIT` / `OFFSET` が無く、`ORDER BY` は `id` だけであることを、実際の SQL で test している。

---

## 4. Lossless 60km 地理 pre-filter

### 方式

DB 側では緯度経度の bounding box で粗く絞り、Python 側で正確な距離を判定する。

```text
d      = (60000 m + 1 m) / 6371000 m × 1.001        （角距離 [rad]）
Δlat   = d
Δlng   = asin( sin(d) / cos(φ0) )                   （球冠が極を含まない場合）

latitude  BETWEEN φ0 - Δlat AND φ0 + Δlat
longitude BETWEEN λ0 - Δlng AND λ0 + Δlng
```

- 半径 6371000m は、正確な距離判定に使う `_distance_m()` と同じ球の半径である。
- `Δlng` は、球冠の経度方向の最大幅に対する厳密な上界である。最大幅は origin の緯度ではなく、やや極側の緯度で生じるが、この式はそれを含めた上界になっている。
- 経度で絞らないケース（常に lossless）:
  - 球冠が極を含む（`|φ0| + d >= π/2`）
  - 範囲が日付変更線をまたぐ
- 余裕は範囲を**広げる方向**にしか働かない:
  - `+1 m`: `_distance_m()` は距離を int へ切り捨てるため、真の距離が 60000〜60001m 未満の点も `<= 60000` と判定される。その点を box に含める。
  - `× 1.001`: 浮動小数点誤差に対する余裕。
- 余分に拾った Shrine（box の四隅付近など）は、Python 側の exact distance で除外する。
- 起点 (35.0, 135.0) での box の半幅は、緯度 約 0.540°、経度 約 0.660°。

### 性能上の前提

- `latitude` / `longitude` には既存の index がある（`idx_shrine_lat` / `idx_shrine_lng` / `idx_shrine_lat_lng`、`models.py`）。schema 変更は不要だった。
- 本番データでの実行計画（EXPLAIN）は未検証（§9）。

### Lossless の検証（test）

- **性質 test** `test_bounding_box_is_lossless_for_every_point_within_60km`
  - 49 の origin: 日本の代表地点、赤道、南半球、ランダム 40 点、極付近、日付変更線付近。
  - 各 origin から、ランダムな方位・距離（0〜60000m と、境界 59990〜60001m）に点を生成する。
  - `_distance_m() <= 60000` となる点がすべて box 内に入ることを assert する（1万点以上）。
- **四隅 test**: box 内だが実距離 60km 超の点が、exact distance で除外される。
- **境界 test**: 59.99km は残り、60.01km は除外される。60km 超からの補充はない。

### 正確な距離の authority

`concierge_chat_candidates._distance_m()`（球面 Haversine、m 単位 int 切り捨て）を再利用した。

- 旧 Monthly の distance stage が読む `distance_m` と同じ関数なので、新 Core と旧経路で距離の値は一致する。
- 距離計算は複製していない。Concierge の距離挙動も変えていない（関数は無変更で、import しているだけ）。
- membership の条件は `_distance_m() <= 60000` である。int 切り捨てのため、真の距離が 60001m 未満の Shrine が含まれる。これは現行 distance stage と同じ判定である。

---

## 5. Shared Recommendation Eligibility の再利用

- 共有層（`concierge_chat_candidates.py`）に `partition_recommendation_eligible_shrines(shrines)` を追加した。
  - 呼び出し側が決めた Shrine 集合に、既存の authority をそのまま適用する:
    `fetch_fact_ready_knowledge_deities/_histories`（batch）+ `is_recommendation_eligible()`
  - 候補 source の決め方（人気順・件数・地理条件）には関与しない。
- 判定式・readiness rule は新設していない:
  - legacy goriyaku / history_theme からの推定なし
  - Evidence Gate ロジックの複製なし
- Compass Core は Knowledge / Evidence の authority を直接参照しない。AST test で次の名前が Core に無いことを固定した:
  `is_recommendation_eligible` / `decide_fact_usability` / `fetch_fact_ready_knowledge_*` / `FACT_READY_VERIFICATION_STATUSES` / `verification_status`
- 共有層の判定式を monkeypatch で差し替えると Core の結果も追従することを test で確認した（Core が自分で判定していない証拠）。
- Concierge の `build_chat_candidates_with_eligibility()` はこの helper を経由しない。既存関数は無変更である。

---

## 6. Direction / Distance stage / Ranking

- **Direction**: `filter_candidates_by_direction()` をそのまま使う。
  - bearing / 8方位ラベル / sector 境界を Core に複製していない（`_bearing` / `_direction_label` / `_DIRECTION_LABELS` / `atan2` が Core に無いことを test で固定）。
  - 方位は membership にだけ使い、角度差による重み付けはしない。
- **Distance stage**: `compass_distance_stage.apply_compass_distance_stage()`（旧 orchestrator と同じ関数 object）。
  - 5 は ring を広げる閾値であり、成功に必要な最低件数ではない。
  - 60km で 1〜4 件は成功、0 件は空結果。60km 超・人気・意味による補充はしない。
- **Ranking**: `rank_active_set()` は `sorted(key=(distance_m, shrine_id))` だけ。ACTIVE_SET 確定後にだけ呼び、membership は変えない。
  - `popular_score` の逆転、Knowledge Fact 件数の増減、goriyaku（text と tag）の付与のいずれでも順序が変わらないことを test で固定した。

---

## 7. 人気順・件数上限が membership に影響しないことの証明

`test_low_popularity_shrine_is_not_lost_to_the_old_popular_top_n_pool`:

- データ:
  - origin の南 20km（60km 圏内）に、`popular_score=1000` の Shrine を **310 件**置く。方位が合わず、Knowledge も無い。
  - origin の北 10km に、`popular_score=0` の eligible Shrine（target）を1件置く。
- 旧設計: 共有 builder に Compass の設定（`candidate_pool_limit=60` → `LIMIT 300`）を渡すと、`source_count == 300` になり、target は pool に入らない（test で assert）。
- 新 Core:
  - `source_candidate_count == 311`（件数上限なし）
  - `eligible_candidate_count == 1`
  - 結果は `[target]`
- **変異確認**（test に含めず、手動で実施）:
  - 新 Core の source query を一時的に旧設計（`ORDER BY -popular_score, id LIMIT 300`）へ書き換えて同 test を実行した。
  - `recommendation_eligibility_zero_candidates` となり **FAIL**（target が消えた）。
  - 元に戻すと PASS。

---

## 8. Test 結果

| 対象 | 結果 |
|---|---|
| 新 Core（`test_compass_direction_only_core.py`） | **51 passed** |
| Compass / Shared Eligibility / Concierge 候補の関連 15 files（新 Core を含む） | **404 passed** |
| backend 全体（base `a5768c97` 上、PostgreSQL 16、CI unit job と同じ env） | **4293 passed, 8 skipped, 0 failed**（skipped は PostGIS 専用 test） |
| backend 全体（最新 develop `9fe25c2b` を merge した後） | **4292 passed, 1 failed, 8 skipped**。1 failed は develop 側の既存失敗（下記） |
| `ruff check`（新規 file） | pass |
| `black --check`（新規 file） | pass |
| `git diff --check` | pass |

関連 15 files の内訳:

- **Compass**: api（recommendations / weekly / public projection / openapi identity / db query budget）、services（direction filter / orchestrator / runtime）、新 Core
- **Eligibility**: `test_shared_recommendation_eligibility.py` / `test_shrine_knowledge_selector.py`
- **Concierge 候補**: `test_concierge_build_chat_candidates_contract.py` / `test_concierge_candidate_utils.py` / `test_concierge_chat_candidates_dedupe.py` / `test_concierge_chat_score_v3_candidate_profile.py`

### develop 側の既存失敗（本 PR と無関係）

`temples/tests/test_knowledge_seed_collective_import.py::test_all_repository_seeds_are_1_0_and_still_parse_without_collectives`

- 原因: develop の #3022（`data(knowledge): author A-5b Pattern B collective seed`）が追加した `backend/temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json` は version `1.1` である。この test は「repository の全 seed が `1.0`」を要求しているため失敗する（`AssertionError: a5b_collective_pattern_b_seed.json / '1.1' == '1.0'`）。
- 証拠: 本 PR の変更を含まない `origin/develop @ 9fe25c2b` を単独で checkout し、同じ test file を実行した。結果は 1 failed / 113 passed で、同じ assertion で失敗する。
- 本 PR の変更（Compass Core / 共有 eligibility helper）とは無関係である。指示どおり、無関係な code を変更して suite を緑にすることはしていない。

### 変更した既存 file の lint / format は develop と同じ状態

`concierge_chat_candidates.py` と `compass_recommendation_orchestrator.py` は、**develop の時点で既に** `black --check` が通らない。`concierge_chat_candidates.py` は ruff の既存指摘も 3 件ある。

- 本 PR ではこの2 file 全体を再 format していない（無関係な差分を混ぜないため）。
- 本 PR の追加行・変更行は black / ruff の新しい指摘を生んでいない:
  - black の差分 hunk 数: develop と本 branch で同じ（concierge 5 / orchestrator 1）で、すべて既存行
  - ruff の指摘: develop と同一の 3 件（concierge）/ 0 件（orchestrator）

### Query の形（N+1 なし、exact budget は置かない）

- `test_query_count_does_not_scale_with_candidate_count`: 候補 2 件 → 42 件で query 数が同じ。
- 構成（Fact の種類が揃っている場合）:
  - 候補 source 1
  - Knowledge: deity 1 + source prefetch 1 + history 1 + source prefetch 1
- 参考値として、本 fixture の形（候補 3 件、各 Shrine に deity と history の両方の Fact）では Core 全体で **5 本**だった。

- 内訳: `temples_shrine` 1、`temples_shrinedeity` 1、`temples_shrineknowledgesource` 1、`temples_shrinehistory` 1、`temples_shrineknowledgesource` 1
- 旧経路（#3010: 匿名 Monthly 6 本）にあった goriyaku_tags の prefetch と tag label 解決は、新 Core には無い
- Fact の種類が欠けると、対応する source prefetch を Django が発行しないため、本数はデータ次第で減る方向にだけ動く

この値は budget ではない。正式な post-implementation baseline は、#3009 と同じ `CaptureQueriesContext` 方式で別 PR（PR-G）で測る。

---

## 9. 既知の follow-up

1. **PR-D（Monthly API + Frontend cutover）**
   - `api_views_compass.py` を新 Core へ接続する。
   - request / response から `purpose`、state から `invalid_purpose` を外す。
   - Public Projection との adapter を作る。候補には `reason` / `breakdown` / `reason_facts` が無いので、Compass 固有の説明（「なぜこの方向か」「なぜ候補に入ったか」）をどこで組み立てるかは、同 PR の Presentation 設計になる。
2. **PR-E（Weekly）**
   - Weekly はまだ旧 `get_compass_recommendations(purpose=...)` を使う。
   - Snapshot identity から purpose を外す作業は、`weekly-snapshot-purpose-removal-production-collision.md` の手順に従う。
3. **PR-F（Active docs）**
   - `docs/knowledge/recommendation-eligibility-contract.md` の「Compass は `build_chat_candidates()` の返り値を受け取る」「state 表の `invalid_purpose`」は、cutover 後に現行と合わなくなる。
   - 本 PR 時点では旧配線が生きているため、書き換えていない。
4. **PR-G（DB query baseline）**: 新 Core を HTTP に接続した後に、POST_DIRECTION_ONLY_BASELINE を測る。
5. **本番規模の検証**
   - bounding box + index の実行計画（EXPLAIN）を本番データ量で確認していない。
   - 60km 圏の Shrine 数が多い地域では、U60 の Knowledge 読み込み行数が増える（本数は一定）。
6. **origin の NaN / 範囲外**
   - 新 Core は、非有限値・緯度 ±90 / 経度 ±180 を超える origin を `direction_filter_unavailable` として扱う（bounding box を安全に作れないため）。
   - 旧経路ではこれらが `direction_zero_candidates` になり得た。cutover 時に公開挙動として確認する。
