> **Status: Active（Shared Recommendation Eligibility）**
>
> 本書は、Concierge と Compass が共有する Recommendation 候補の**適格性（eligibility）**契約を定義する。Ranking / scoring / Direction / Distance の契約は本書の対象外であり、本契約によって変更されていない。

# Recommendation Eligibility Contract

## 不変条件

```text
Shrine DB presence
!= Recommendation eligibility

Recommendation eligibility
= at least one usable Deity or History Fact
```

Shrine が DB に存在することは、その Shrine が Recommendation 候補になれることを意味しない。Recommendation の候補になれるのは、**usable な Deity Fact または usable な History Fact を最低1件持つ Shrine だけ**である。

```text
Shared eligibility
!= F5 Qualified Evidence gating
!= ranking signal
```

- **F5 Qualified Evidence gating ではない。** 本 gate は Evidence Foundation の 5 次元 qualification（`evidence_qualification.evaluate_evidence_qualification()`）・`EvidenceLink`・`normalized_evidence` transport・G1 canonical taxonomy / alias のいずれも参照しない。判定に使うのは既存の Knowledge / Evidence Gate usability authority のみである。
- **ranking signal ではない。** eligibility は candidate set の**境界**であり、score へは一切寄与しない。eligible な Shrine の順位・スコアは gate の有無で変化しない。ineligible な Shrine を「低スコアで残す」ことはしない。

## 適格条件

```text
usable_deity_fact
OR
usable_history_fact
```

`usable` の判定そのものはここで再定義せず、既存の authority へ委譲する。

```text
temples.services.shrine_knowledge_selector
  .fetch_fact_ready_knowledge_deities() / _histories()
      -> temples.services.evidence_gate.decide_fact_usability()
```

`decide_fact_usability()` の条件（`docs/knowledge/shrine-knowledge-contract.md`「Evidence Gate要件」）:

1. Fact 自身の `verification_status` が `FACT_READY_VERIFICATION_STATUSES` に含まれる
2. Relation 済み Source のうち最低1件の `verification_status` が同集合に含まれる

したがって、**新しい readiness rule は追加していない**。Shrine Detail 側の表示判定と同じ usability 判定を共有する。

## 実装位置（単一責務）

```text
backend/temples/services/concierge_chat_candidates.py
    is_recommendation_eligible()                 # 唯一の判定式
    filter_recommendation_eligible_candidates()  # 候補listへの適用
    build_chat_candidates()                      # 生成時にgateを適用
```

`build_chat_candidates()` は Concierge と Compass が各自の selection logic へ分岐する**手前**の共有層である。

```text
                build_chat_candidates()
                （Shared Eligibility gate）
                          │
            ┌─────────────┴─────────────┐
            │                           │
   Concierge candidate            Compass candidate
   pipeline                       (direction -> distance -> ranking)
```

- **Compass 側に eligibility 判定を複製しない。** `compass_recommendation_orchestrator.py` は `build_chat_candidates()` の返り値をそのまま受け取るだけであり、Knowledge / Evidence を自分では参照しない（`test_shared_recommendation_eligibility.py::test_compass_module_contains_no_eligibility_logic` で固定）。
- Concierge の `_build_chat_candidates_pipeline()`（`api_views_concierge.py`）は、request で持ち込まれた候補（`data["candidates"]`）が共有層を通っていないため、**同じ共有関数** `filter_recommendation_eligible_candidates()` をマージ後に1度だけ適用する。判定式は複製していない。

### pool_limit との関係

`build_chat_candidates()` の `pool_limit = max(limit * 5, 50)` による queryset スライスは、この gate **より前**に効く。したがって gate 適用後の候補数が `pool_limit` を下回ることがある。不足分を ineligible な Shrine で埋め戻すことはしない（silent fallback の禁止）。

## ineligible Shrine の扱い

ineligible な Shrine に対して、以下はいずれも行わない。

- score を下げて残す
- fallback として保持する
- 後段で再投入する
- legacy `Shrine.goriyaku` / `Shrine.history_theme` から eligibility を推定する

shrine id を解決できない候補（request 由来の任意 dict 等）は、eligibility を証明できないため **fail closed** で ineligible として扱う。

## Zero-Candidate Behavior

### Concierge

gate によって候補が 0 件になった場合、**既存の安全な空レスポンス形**をそのまま返す。

- `data.recommendations == []`
- `data.message` は既存の「条件に合いそうな神社が見つかりませんでした。条件を少しゆるめて試してください。」（`concierge_chat_presentation._trim_to_top3_and_fill_message()`）

新しいユーザー向け文言は導入していない。fallback の神社をでっち上げない — 空 pool から神社名を1件生成していた `ConciergeOrchestrator._fallback_from_candidates()` のプレースホルダ（`近隣の神社`）は削除した。候補が1件以上ある場合の挙動は変更していない。

### Compass

zero-candidate は**原因ごとに別 state** として表現する。互いに統合しない。

```text
recommendation_eligibility_zero_candidates
= no shrine passed shared Recommendation Eligibility

direction_zero_candidates
= eligible shrines existed, but none survived geographic direction filtering

evidence_zero_candidates
= eligible directional candidates existed, but Recommendation returned none
```

| 状況 | state |
|---|---|
| purpose が不正 | `invalid_purpose` |
| origin / direction 入力が不正・不足（Group A: runtime 不成立） | `direction_filter_unavailable` |
| 年盤・月盤の共通方位が空 | `no_common_direction` |
| **共有 Eligibility 契約を満たす Shrine が0件** | **`recommendation_eligibility_zero_candidates`** |
| 方位内に候補0 / 方位内にはあるが60km圏内に0 | `direction_zero_candidates`（メタデータで区別） |
| direction / distance は候補を残したが Recommendation が0件 | `evidence_zero_candidates` |
| 推薦が1件以上 | `recommendation_success` |

#### state 判定順

```text
build_chat_candidates_with_eligibility()
    │
    ├─ Direction Filter が実行不能（origin / referenceDirections 不正）
    │      -> direction_filter_unavailable   ← Group A は常に先
    │
    ├─ eligible 候補 0 件
    │      -> recommendation_eligibility_zero_candidates
    │
    ├─ Direction Filter 後 0 件 / 60km 圏内 0 件
    │      -> direction_zero_candidates
    │
    ├─ Ranking が 0 件
    │      -> evidence_zero_candidates
    │
    └─ 1 件以上 -> recommendation_success
```

`direction_filter_unavailable` を eligibility 判定より先に置くのは、`filter_candidates_by_direction()` の `None` 契約が **origin / referenceDirections だけ**で決まり候補件数に依存しないためである（`compass-mvp-runtime-contract.md` Section 8 の Group A / Group B 分離）。この順序でも「候補が0件だから unavailable になる」ことは起きない。

`recommendation_eligibility_zero_candidates` は**正常な product result** であり technical error ではない。候補生成は正常に完了しており、共有 Eligibility 契約を満たす Shrine が存在しなかったという事実だけを表す。ineligible な Shrine をここで復活させない。

#### Compass が eligibility を判定しないための metadata

Compass は Knowledge / Evidence を一切参照せず、共有層が返す `CandidateBuildResult` の内訳だけで state を決める。

```python
# temples/services/concierge_chat_candidates.py
@dataclass(frozen=True)
class CandidateBuildResult:
    candidates: list[dict]
    source_count: int       # gate 適用前の候補 source 数
    eligible_count: int     # gate 通過数（= len(candidates)）
    ineligible_count: int   # gate 除外数
```

`build_chat_candidates()` は従来どおり候補 list のみを返す薄い adapter として残る（Concierge 側の呼び出し形は不変）。`build_chat_candidates_with_eligibility()` が内訳付きの正本である。

`CompassRecommendationResult` は `source_candidate_count` / `eligible_candidate_count` としてこの値をそのまま保持する。これにより「候補 source は存在したが Eligibility で全滅した」と「そもそも候補 source が0件だった」も観測できる（state はどちらも `recommendation_eligibility_zero_candidates`）。

#### API / frontend / analytics

- API は `recommendation_eligibility_zero_candidates` を **HTTP 200** でそのまま返す（`invalid_purpose` のみ 400）。
- frontend の state union（`CompassUiState` / `CompassRecommendationsResponse["state"]`）に追加済み。backend error / direction failure / `direction_zero_candidates` / `evidence_zero_candidates` のいずれとしても扱わない。表示は既存の空結果表示（`DetailSection variant="tertiary"` + `no_common_direction` と同じ `/concierge` 導線）を再利用する。
- analytics は既存の `compass_result` イベントの `result_state` として独立した値で送出する。他の zero カテゴリへ統合しない。

## 変更していないもの

- Ranking / scoring（`score_need`・`score_need_rank_weighted`・`RECOMMEND_C1_MAX`）
- Direction Filter（`compass_direction_filter`・`direction_reference`）
- Distance Boundary（15 / 30 / 60 km、expansion threshold 5）
- `NEED_TO_GORIYAKU_IDS` / `NEED_TEXT_WEIGHTS` / `GoriyakuTag` master
- G1 canonical taxonomy / alias registry
- Knowledge データ（backfill なし）
- Shrine 一覧・詳細の可視性（`/api/shrines/` 系は ineligible な Shrine も従来どおり返す。本 gate は Recommendation 候補にのみ効く）
