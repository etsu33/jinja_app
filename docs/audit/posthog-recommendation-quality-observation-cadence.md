> **Status: `INSUFFICIENT_SESSION_DIVERSITY`。**
>
> [Production Recommendation Qualityの観測開始をKnowledge分類propertyで
> 確認](posthog-recommendation-quality-production-baseline.md)
> （`KNOWLEDGE_CLASSIFICATION_DATA_AVAILABLE`）を土台に、「次回いつ・
> どの条件で再計測するか」「どの条件が揃えばsegmented funnel分析へ
> 進めるか」を設計・監査した。**現在のデータはMother Ship自身の単一
> thread（threadId基準でdistinct 1件）に由来する3件のみであり、
> segmented funnel分析（CTR/save率等のKnowledge分類別比較）へ進める
> 状態にはまだ達していない。** 併せて、`shrine_decision`(save)/
> `route_open`のjoin key（property名の不一致・rankの欠落）についても
> fresh監査で新たな精緻化を行った。コード変更は行っていない。

---

## 1. Base State（Phase 0）

- PR #2393 merge確認済み（`0a43fbcc`、2026-08-12 09:27:33 UTC）
- develop最新化・origin/developと同期・working tree clean
- **HEAD SHA**: `0a43fbcc43ba8f3a4e3e4b91de0dc745dca9eca5`
- `scripts/analytics_safety/`のdrift確認: PR #2390以降変更なし（PR
  #2391/#2392/#2393はいずれもdocs/audit/のみ）
- 監査docをfresh読み込み: [posthog-recommendation-quality-production-baseline.md](posthog-recommendation-quality-production-baseline.md)
  / [knowledge-recommendation-analytics-contract.md](knowledge-recommendation-analytics-contract.md)
  / [knowledge-recommendation-analytics-observability.md](knowledge-recommendation-analytics-observability.md)

---

## 2. Foundation Gate & Credential Gate（Phase 1-2）

```
$ python3 -m pytest -p no:dotenv scripts/analytics_safety/tests/ -v
============================== 90 passed in 0.10s ==============================

$ bash scripts/analytics_safety/check_posthog_credential_presence.sh ~/.config/kami-musubi/posthog-readonly.env
POSTHOG_PERSONAL_API_KEY_SET=1 / POSTHOG_PROJECT_ID_SET=1 / POSTHOG_HOST_SET=1
```

値・project ID・hostnameはいずれも出力していない。

---

## 3. Current Baseline Recheck（Phase 1）

`2026-08-12T04:12:15Z` 〜 `2026-08-12T09:29:57Z`でfresh再実行（前回監査
[production-baseline.md](posthog-recommendation-quality-production-baseline.md)
のquery windowより約8分延長）。

| 指標 | 値 | 前回比 |
|---|---|---|
| `recommendation_quality`総件数 | 3 | 変化なし |
| `FULLY_KNOWLEDGE_BACKED` | 2 | 変化なし |
| `UNKNOWN` | 1 | 変化なし |
| `PARTIALLY_KNOWLEDGE_BACKED` / `LEGACY_BACKED` | 0 / 0 | 変化なし |
| property completeness | 3/3・3/3・3/3（0%欠損） | 変化なし |
| `concierge_result_impression` | 3 | 変化なし |
| `shrine_detail_transition` | 2 | 変化なし |
| `unique_recommendation_sessions` | 1 | 変化なし |
| `consultation_completed` | 1 | 変化なし |
| `visit_done` | 0 | 変化なし |

前回監査（PR #2393）からの約8分間で新規イベントは到達していない。
raw row取得は行っていない（すべてaggregate count / GROUP BY）。

---

## 4. Independent Session Definition（Phase 2）

バックエンドモデル`backend/temples/models.py`の`ConciergeThread`を
fresh確認した。`user`または`anonymous_id`に紐づき、`created_at`/
`last_message_at`/`recommendations`を持つ永続化されたモデルであり、
フロントエンドの`threadId`はこの`ConciergeThread.id`を指す
（`payload?.thread?.id`経由）。

候補比較:

- **`threadId`（= `ConciergeThread.id`）**: バックエンドで永続化された
  安定識別子。1つの相談・会話セッションに対応。**採用**。
- `resultSetId`: `ConciergeSectionsRenderer.tsx`内でのみ生成される
  フロントエンド一時的な複合キー（`${threadId}:${rank}:${position}:
  ${shrineId}の署名`）で、impression重複防止用のクライアント側de-dup
  keyに過ぎず、バックエンドに永続化されない。session識別には不適。
- consultation session単位: 独立した概念として別途存在せず、実質
  `threadId`と1対1に近い。

新しいidentifierは作成していない。既存`unique_recommendation_sessions`
query（`count(DISTINCT properties.threadId)`、`concierge_result_
impression`基準）は、この定義と整合している。

---

## 5. Session Diversity Check（Phase 3）

| 指標 | 値 |
|---|---|
| `recommendation_quality`内のdistinct `threadId`数 | **1** |
| `concierge_result_impression`内のdistinct `threadId`数 | **1**（既存query再実行、一致確認） |
| `recommendation_quality`イベント数 | **3** |

個別ID値は出力していない（count/count(DISTINCT)のみ）。

---

## 6. Observation Readiness Criteria（Phase 4）

質的条件（固定sample thresholdは設定しない）に対する現状評価:

| 条件 | 判定 | 根拠 |
|---|---|---|
| A. 複数独立sessionが存在 | ❌ 未達 | distinct threadId = 1（5章） |
| B. classificationが1種類だけでない | 🔶 部分的 | `FULLY_KNOWLEDGE_BACKED`/`UNKNOWN`の2値は観測（3章）だが、単一threadの3推薦内での分散であり、セッション横断的な多様性ではない |
| C. impression/detail eventが継続して到達 | ❌ 未達 | 単一時点の1バーストのみ確認（2026-08-12 17:39 JST前後）。複数の異なる時間帯での到達は未確認 |
| D. property completenessが維持 | ✅ 達成 | 2回のfresh queryで一貫して0%欠損（3章） |
| E. event schema driftなし | ✅ 達成 | `QUERY_CONTRACT`・`guard.py`のallow-list・join key出力コード、いずれも前回監査以降変更なし（1章） |

**5条件中2つ（D・E）のみ完全達成、Aは未達、Cは未達、Bは部分的達成に
留まる。** 次フェーズ（segmented funnel分析）へ進む条件は現時点では
揃っていないと判定する。

---

## 7. Segmented CTR Readiness（Phase 5）

Join key契約をfresh再確認した（コード変更なし、[production-baseline.md](posthog-recommendation-quality-production-baseline.md)
10章からのdriftなしを`git diff`で確認済み・1章）。

| event | join key | 状態 |
|---|---|---|
| `concierge_result_impression` | `threadId`/`shrineId`/`recommendationRank` | ✅ full rank-level join可能 |
| `shrine_detail_transition` | `threadId`/`shrineId`/`recommendationRank` | ✅ full rank-level join可能 |
| `recommendation_quality` | `threadId`/`shrineId`/`recommendationRank` | ✅ full rank-level join可能 |

impression側・detail_transition側とも`knowledge_backing_class`との
join key（`threadId`+`shrineId`+`recommendationRank`）を保持しており、
raw eventなしでaggregate segmentationが可能な設計であることを確認
した。ただし6章の判定によりsample不足のため、
`ctr_by_classification`（`UNVERIFIED_SEGMENTED_QUERY_CONTRACT`）は
**本監査でも実行していない**。

---

## 8. Save Funnel Readiness（Phase 6）

`shrine_decision`の実装コードをfresh再確認した結果、**action種別に
よってjoin key構成が異なる**ことが判明した（前回のContract監査§32の
要約「rank/tid/ctxあり」は`action="route"`のケースのみを正確に反映
しており、`action="save"`には当てはまらないことを、実装コードの
直接確認で精緻化した）:

| action | 発生箇所 | payload keys | join可能性 |
|---|---|---|---|
| `route`（open_map） | `ConciergeClientFull.tsx:1550` | `shrineId`/`action`/`rank`/`tid`/`consultationAxis?` | `shrineId`+`tid`(≒threadId)+`rank`(≒recommendationRank)で理論上rank-level join可能。ただし**property名が`tid`/`rank`であり、他イベントの`threadId`/`recommendationRank`とは別名**（HogQL側でaliasを意識したjoinが必要） |
| `save` | `ShrineSaveButton.tsx:65` | `shrineId`/`action`/`ctx`/`tid` | **`rank`/`recommendationRank`が一切存在しない**。`shrineId`+`tid`（thread単位）でのみjoin可能、rank単位のattributionは不可能 |

**分類: `JOIN_READY_WITH_LIMITATIONS`**（save actionはthread+shrine
レベルのみ、property名の不一致もあり）。Knowledge分類との結合は
`shrineId`+`tid`(=`threadId`)単位でaggregate-onlyに可能だが、
同一thread内で同一shrineへの推薦が複数rankに出現するケースがあれば
attributionが曖昧になる制約がある。イベント変更は行っていない。

---

## 9. Visit Intent Readiness（Phase 7）

`route_open`・`visit_done`の実装コードをfresh再確認した。

| event | 発生箇所 | payload keys | join可能性 |
|---|---|---|---|
| `route_open` | `GoogleMapRouteLink.tsx:57` | `shrineId`/`threadId`/`historyTheme`/`ctx` | `threadId`は正しい key名だが**`rank`/`recommendationRank`が存在しない**。thread+shrineレベルのみ |
| `visit_done` | `ShrineDetailArticle.tsx:732` | `shrineId`/`threadId`/`historyTheme`/`accessLevel`/`mode` | 同上、`rank`/`resultSetId`とも欠落 |

- `route_open` = **`JOIN_READY_WITH_LIMITATIONS`**（新規確認: 従来
  「join可能性」とのみ記載されていたが、rank欠落という同種の制約が
  `visit_done`と同様に存在することを本監査でfresh確認した）
- `visit_done` = 引き続き**`JOIN_READY_WITH_LIMITATIONS`**（既知、
  [Analytics Contract](knowledge-recommendation-analytics-contract.md)
  §5/§21、[Analytics Observability](knowledge-recommendation-analytics-observability.md)
  §143と一致）

event schema変更は行っていない。

---

## 10. UNKNOWN Investigation Readiness（Phase 8）

個別event rowは取得せず、`backend/temples/services/
recommendation_quality_measurement.py`の`classify_provenance()`
コードのみをfresh確認した。

```python
def classify_provenance(deity_status, history_status):
    ...
    if knowledge_used and legacy_used:
        return "PARTIALLY_KNOWLEDGE_BACKED"
    if knowledge_used:
        return "FULLY_KNOWLEDGE_BACKED"
    if legacy_used:
        return "LEGACY_BACKED"
    return "UNKNOWN"  # 両方EMPTY（由来を判定する材料がない）
```

`FieldStatus = Literal["KNOWLEDGE_USED", "LEGACY_USED", "EMPTY"]`。
`EMPTY`は「suppressされた、またはそもそも値がない」場合に付与される
（`_field_status()`docstring）。

**UNKNOWNが起こりうる条件（コード上の整理、個別データの追跡はしていない）**:

1. **expected behavior**: 対象shrineにdeity fact・history factの
   いずれも存在しない場合の正常な分類（バグではない）。
2. **missing Knowledge**: 該当shrineがまだKnowledge（`ShrineDeity`/
   `ShrineHistory`）でカバーされていないバッチ未取り込みのケース。
3. **empty deity/history**: 両fieldとも値そのものが空。
4. **fallback behavior**: confidence-basedのreason強度判定
   （`_reason_strength_from_confidence`、low/mixed→suppressed）に
   より、データが存在してもsuppressされて`EMPTY`扱いになるケース。

上記1〜4のいずれが今回のUNKNOWN 1件の実際の原因かは、個別event row/
consultation内容を見ない限り特定できない。実ユーザー個別データの
追跡は指示通り行っていない。

---

## 11. Re-measurement Trigger Design（Phase 9）

- 「一定日数後」には依存しない。
- 推奨トリガー: 「**複数独立sessionが蓄積したら**」「**classification
  diversityが確認できたら**」「**自然利用（Mother Ship検証以外の
  トラフィック）が増えたら**」の複合条件。
- 具体的な件数threshold: **`NOT_DEFINED`**（根拠なく数値を設定しない、
  指示通り）。
- 再計測時に確認すべき点（[production-baseline.md](posthog-recommendation-quality-production-baseline.md)
  14章から継承・精緻化）:
  1. distinct threadId数が1から複数へ拡大しているか（5章）
  2. 6章の条件A〜Eのうち、特にA（複数session）とC（継続到達）が
     達成されているか
  3. `PARTIALLY_KNOWLEDGE_BACKED`/`LEGACY_BACKED`を含む4分類全てが
     実データで観測できるか
  4. `shrine_decision`/`route_open`/`visit_done`側にもデータが
     生じているか（8〜9章のjoin制約を踏まえたaggregate-only分析が
     可能かも合わせて確認）

---

## 12. No Premature Optimization Boundary（Phase 10）

以下はいずれも本監査で**行っていない**: Recommendation reason変更・
Ranking変更・Score v3 active化・Analytics event変更・Dashboard実装・
Knowledge Model変更・UI変更・sample不足でのA/B優劣判定。

---

## 13. Measurement State Classification（Phase 11）

**`D. INSUFFICIENT_SESSION_DIVERSITY`**

根拠:

- `A. OBSERVATION_COLLECTION_ACTIVE`だけでは実態を過小評価する:
  単なる「収集中」ではなく、既にKnowledge分類が実データで機能して
  いることを2回のfresh queryで確認済み（3章）。
- `B. MULTI_SESSION_DATA_AVAILABLE`ではない: distinct threadId = 1
  （5章）。
- `C. SEGMENTED_FUNNEL_ANALYSIS_READY`ではない: 6章の条件A・Cが
  未達であり、7章の判断によりsegmented queryも未実行。
- `E. EVENT_SCHEMA_GAP`ではない: 8〜9章で発見したjoin key制約
  （`shrine_decision`のproperty名不一致・rank欠落、`route_open`の
  rank欠落）は**新規の破壊的スキーマ問題ではなく、既存の設計上の
  制約**であり、`recommendation_quality`本体の測定は正しく機能して
  いる。
- 6章の評価（5条件中D・Eのみ達成、A・Cが未達、Bが部分的）から、
  **`INSUFFICIENT_SESSION_DIVERSITY`が最も正確な分類**と判断した。

---

## 14. Security（Phase 12）

```
$ gitleaks detect --source docs/audit/posthog-recommendation-quality-observation-cadence.md --no-git -v
no leaks found
```

credential値・project id・hostname・raw response・raw event row・
distinct_id・person data・consultation本文はいずれも出力・取得して
いない。`git status`/`git diff --check`でdoc-only変更を確認。

---

## Final Classification

**`INSUFFICIENT_SESSION_DIVERSITY`**

現在の`recommendation_quality`データ（N=3）はMother Ship自身の単一
thread由来であり、独立した複数セッションへの拡大が観測されるまで、
segmented funnel分析（CTR/save率のKnowledge分類別比較）へは進めない。
併せて、`shrine_decision`(save)/`route_open`のjoin key（property名
不一致・rank欠落）を実装コードから新たにfresh精緻化し、いずれも
`JOIN_READY_WITH_LIMITATIONS`として記録した。再計測トリガーは
「複数独立session蓄積後」を基本条件とし、根拠のない数値thresholdは
設定していない（`NOT_DEFINED`を維持）。Recommendation behavior・
Ranking・Score v3・Analytics event・Knowledge Modelはいずれも変更
していない。

Production DB writes = 0
PostHog mutations = 0
Raw event exports = 0
Recommendation behavior changes = 0
Ranking changes = 0
