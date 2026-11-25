> **Status: `KNOWLEDGE_RECOMMENDATION_ANALYTICS_CONTRACT_READY_WITH_LIMITATIONS`。**
>
> 本監査はAnalytics Contractの**設計のみ**であり、実装ゼロ・Production
> writeゼロ・イベント送信実装ゼロ・Frontend変更ゼロ・Recommendation
> behavior変更ゼロである。既存Analytics実装と
> [knowledge-recommendation-quality-baseline.md](knowledge-recommendation-quality-baseline.md)
> の計測基盤を接続するための最小Contract案を提示する。**次のPR着手判断は
> Mother Shipに委ねる。**

---

## 1. develop SHA

`382f54af9417e743b7ae5b1ccf02a72221a1618b`（2026-08-12 12:32:47 +0900）

PR #2382（[knowledge-recommendation-quality-baseline.md](knowledge-recommendation-quality-baseline.md)）
merge確認済み。develop同期・working tree clean。

---

## 2. Existing Analytics Inventory（Phase 1）

[cross-platform-event-contract.md](cross-platform-event-contract.md)（既存の
詳細監査、本タスクでfresh再確認）から、Recommendation関連の実イベントを
抽出した。

| イベント名 | emitter | 送信元 | 主なproperty | join可能なkey |
|---|---|---|---|---|
| `concierge_result_impression` | `ConciergeSectionsRenderer.tsx:358` | Frontend | source, threadId, resultSetId, shrineId, position, recommendationRank, mode, historyTheme, consultationAxis? | threadId/shrineId/resultSetId/recommendationRank |
| `shrine_detail_transition` | `ConciergeSectionsRenderer.tsx:847,983` | Frontend | source, threadId, resultSetId, position, recommendationRank, shrineId, mode, historyTheme, firstClick | 同上 |
| `recommendation_quality` | `features/concierge/hooks.ts:140` | Frontend（Backend `recommendation_reason_quality`を転送） | source, threadId, shrineId, recommendationRank, accessLevel, shrine_data_rate, evidence_rate, consultation_reflection_rate, fallback_reason_rate, action_grounding_rate, is_ai_inference_only, fallback_source | threadId/shrineId/recommendationRank |
| `shrine_decision` | `ConciergeClientFull.tsx:1522`, `ShrineSaveButton.tsx:65` | Frontend | shrineId, action("route"/"save"/"map_search"), rank?, tid/ctx, consultationAxis? | shrineId/tid(threadId)/rank |
| `shrine_detail_view` | `ShrineDetailViewTracker.tsx:22` | Frontend（+Backend `shrine-interactions/`へ二重POST） | source, shrineId, threadId? | shrineId/threadId |
| `route_open` | `GoogleMapRouteLink.tsx:32` | Frontend（+Backend二重POST） | source, routeTarget, shrineId, threadId, historyTheme, ctx | shrineId/threadId |
| `visit_done` | `ShrineDetailArticle.tsx:724` | Frontend | source, shrineId, threadId, historyTheme, ctx | shrineId/threadId |
| `reflection_saved` | `ShrineReflectionPrompt.tsx:57` | Frontend | source, shrineId, threadId, historyTheme, promptType, answerLength, moodBefore, moodAfter, ctx | shrineId/threadId |
| `consultation_completed` | `ConciergeClientFull.tsx:1198` | Frontend | threadId, mode, flow, hasBirthdate, recommendationCount, historyTheme, consultationAxis?, source | threadId |
| `action_suggestion_preview_view` | `ConciergeTopRecommendationHero.tsx:120` | Frontend | source, threadId, resultSetId, shrineId, recommendationRank, position, historyTheme, actionSuggestionVersion, primaryActionType | threadId/shrineId/resultSetId/recommendationRank |

「retry」「相談再入力」「result再生成」に該当する専用イベントは存在しない
（`filter_result`は絞り込み結果のゼロ件判定であり、相談のやり直しとは別概念）。

推測でイベントを追加せず、存在しないものは「存在しない」と記録する。

---

## 3. Funnel Coverage Matrix（Phase 2）

| 段階 | event存在 | property充足度 |
|---|---|---|
| Consultation（相談完了） | `consultation_completed`あり | 十分（threadId/mode/flow等） |
| Result（推薦結果生成） | `consultation_completed`の`recommendationCount`で件数のみ把握可 | 個々の推薦内容は別イベントで補完 |
| Result Impression（各神社の表示） | `concierge_result_impression`あり | **ほぼ十分**。shrineId/position/recommendationRank/threadId/resultSetIdを保持。Knowledge分類propertyは**不足**（`QUALITY_PROPERTY_GAP`） |
| Shrine Click（クリック） | `shrine_detail_transition`（推薦発の遷移として`concierge_result_impression`と同じproperty形状で記録） | 十分。ただし同上のKnowledge分類property不足 |
| Detail（詳細閲覧） | `shrine_detail_view`（汎用、推薦経由か`/shrines`一覧経由かは`source`で区別可能） | 十分 |
| Save | `shrine_decision`（action="save"）、`ShrineSaveButton.tsx`経由 | rank/tid/ctxあり。Knowledge分類property不足 |
| Map CTA | `shrine_decision`（action="map_search"）、`route_open`（別イベント、重複気味） | 同上 |
| Visit | `visit_done` | shrineId/threadIdあり。rank/resultSetIdは**含まれない**（部分的property不足） |
| Retry/相談再入力 | **event自体が存在しない** | `UNKNOWN`（2章参照） |

**総評**: Funnelの主要段階（Impression→Click→Detail→Save/Map→Visit）は
event自体は既に揃っている。不足しているのはevent自体ではなく、
Knowledge品質分類をpropertyとして運ぶ経路である。

---

## 4. Impression State（Phase 6）

`concierge_result_impression`が分母として機能する。`shrineId`・
`recommendationRank`・`position`（hero/alternative相当の区別）・
`threadId`・`resultSetId`を既に保持しており、rank付き・hero/alternative
区別付きのimpression計測は**既に可能**。

**分類: impression gapなし**（`RECOMMENDATION_IMPRESSION_GAP`は該当しない）。

---

## 5. Attribution State（Phase 7-9）

### Detail遷移（Phase 7）

`shrine_detail_transition`が推薦発の遷移を専用イベントとして記録しており、
`/shrines`一覧経由の`shrine_card_click`とは名前もfile:lineも別である。
`source`propertyでの二重確認も可能。

**分類: attribution gapなし**（`DETAIL_ATTRIBUTION_GAP`は該当しない）。

### Save/Favorite（Phase 8）

`shrine_decision`（action="save"）が`rank`/`tid`/`consultationAxis`を
伴って発火する。推薦由来のSaveかどうかは`tid`（threadId）の有無で
判定可能（推薦フロー外からのSaveは`ShrineSaveButton.tsx`の呼び出し
コンテキストにより`tid`が空になる設計と推定されるが、本監査では
呼び出し元ごとの`tid`値の実測はしていない）。

**分類: 概ね可能。ただし呼び出しコンテキストごとの`tid`充足率の実測は
`NOT_MEASURED`**。

### Map/Visit（Phase 9）

`shrine_decision`（action="map_search"）と`route_open`が同じ操作を
別イベントとして二重記録している（[cross-platform-event-contract.md](cross-platform-event-contract.md)
で既知の事実）。`visit_done`は`rank`/`resultSetId`を持たず、
「どの推薦順位由来の参拝か」の直接joinはできない
（`shrineId`+`threadId`での間接joinは可能）。

**分類: 部分的attribution gapあり**（`visit_done`のrank/resultSetId
不足、新規イベントではなくproperty追加で解消可能な範囲）。

---

## 6. Quality Property Candidates（Phase 3）

[recommendation_quality_measurement.py](../../backend/temples/services/recommendation_quality_measurement.py)
（PR #2382）が算出可能な値から、analytics property候補を整理する。

| property候補 | 型 | 必須/optional/不要 | 根拠 |
|---|---|---|---|
| `knowledge_backing_class` | string（FULLY/PARTIALLY/LEGACY/UNKNOWN） | **必須** | Phase 4の問い1-4に直接必要な唯一の分類値 |
| `deity_knowledge_used` | boolean | **必須** | 問い5（deity利用有無での行動差） |
| `history_knowledge_used` | boolean | **必須** | 問い5（history利用有無での行動差） |
| `reason_fact_count` | int | optional | 既存`shrine_data_rate`（`recommendation_quality`イベント）と重複度が高く、優先度は低い |
| `source_confirmed_fact_count` | int | 不要 | 既存Baseline計測でBatch 9〜16のFactはほぼ全件`source_confirmed`であり、現時点では変動が乏しく行動指標との相関検証に使える分散がない |
| `knowledge_fact_count` | int | 不要 | `knowledge_backing_class`で代替可能、propertyを増やす必要性が薄い |
| `legacy_fallback_used` | boolean | optional | `knowledge_backing_class == LEGACY_BACKED`から導出可能（冗長だが集計クエリの単純化に資する） |
| `knowledge_coverage_status` | string | 不要 | Recommendation単位ではなくShrine単位の静的属性であり、Baseline監査（[knowledge-recommendation-quality-audit.md](knowledge-recommendation-quality-audit.md)）で別途集計可能。Analyticsイベントへ載せる必然性が薄い |

Fact本文（deity表示名・shrine_history本文）・Source URL・publisher名は
**一切property候補に含めない**（Phase 13参照）。

---

## 7. Join Strategy（Phase 5）

既存property（`threadId`/`shrineId`/`recommendationRank`/`resultSetId`）で
**join可能**。新規ID導入は不要。

ただし重要な前提条件がある: `recommendation_quality_measurement.py`の
現在の実装は「今この瞬間のDB状態に対する分類」を計算する設計であり、
過去のある推薦レスポンス時点での分類を再現するものではない。Knowledgeは
Batchごとに増減するため、**同じshrineIdでも計測タイミングによって
`knowledge_backing_class`が変わりうる**。

したがって、行動指標との正確な相関分析には「そのイベント発火時点の
分類」をイベント自体に埋め込む方式（6章のproperty案をBackendの
推薦レスポンス生成時に計算し、その場でイベントpayloadへ含める）が
必須であり、後からのバッチ的なjoin（イベント発火後にshrineIdだけで
現在の分類と突き合わせる）は時点のズレにより不正確になる。

**分類: `NEW_JOIN_IDENTIFIER_REQUIRED`ではない。既存keyで十分だが、
property自体を「発火時点で計算してpayloadへ含める」設計が前提条件**。

---

## 8. CTR定義（Phase 11）

```
Recommendation CTR =
  count(shrine_detail_transition) / count(concierge_result_impression)
```

`knowledge_backing_class`でsegment化して比較する
（`WHERE knowledge_backing_class = 'FULLY_KNOWLEDGE_BACKED'`等）。

## 9. Detail Transition Rate定義

CTRと同一定義（本Product文脈では両者は同義）。

## 10. Save Rate定義

```
Save Rate =
  count(shrine_decision WHERE action='save') / count(concierge_result_impression)
```

分母をimpressionに固定する（Detail到達後のSave率にすると、Detail
遷移率自体の効果と二重に評価してしまうため、Baseline指標としては
impression起点で統一する）。

## 11. Visit Intent Rate定義

```
Visit Intent Rate =
  count(shrine_decision WHERE action='map_search' OR route_open)
  / count(concierge_result_impression)
```

`shrine_decision(map_search)`と`route_open`の二重記録問題（5章）が
未解消のため、実装時にはどちらか一方を正本と決める必要がある
（本監査では決定しない）。

## 12. Retry Rate定義

専用イベントが存在しないため定義不能。

```
Retry Rate = UNKNOWN
```

計測するには新規イベント追加が必要（本監査のPR候補には含めない、
[knowledge-recommendation-quality-audit.md](knowledge-recommendation-quality-audit.md)
のTrack C領域として別途検討）。

---

## 13. Segmentation Design（Phase 12）

必要最小限のsegment軸:

- `knowledge_backing_class`（4値）
- `recommendation_rank`（上位vs下位、例: rank<=3 vs rank>3の2群に粗く括る）
- `deity_knowledge_used` / `history_knowledge_used`（それぞれ2値、必要時のみ）

`consultation_axis`・hero/alternative区別・knowledge coverage等は
**segment軸へ含めない**。理由: 4分類×axis×rank×hero/alternativeを
掛け合わせると、[knowledge-recommendation-quality-baseline.md](knowledge-recommendation-quality-baseline.md)
のローカル実測（sample 100件中LEGACY_BACKED/PARTIALLY_KNOWLEDGE_BACKEDが
共に0件）が示す通り、現状の分布は`FULLY_KNOWLEDGE_BACKED`と`UNKNOWN`に
偏っている可能性が高く、過度な細分化はサンプル数不足によるノイズだらけの
比較を生む。

---

## 14. Privacy / Payload Audit（Phase 13）

6章の property候補を再確認した結果:

- 相談本文（consultation raw text）: 含まれない
- Fact本文（deity表示名・shrine_history本文）: 含まれない
- Source URL・publisher: 含まれない
- ユーザー入力の自由記述: 含まれない

6章の候補はすべて分類値（string enum）・boolean・count（int）のみで
構成されており、既存の`recommendation_quality`イベントが送信している
`shrine_data_rate`等の数値指標と同じ粒度である。

**唯一の既存の機微データ**は本監査の対象外（[cross-platform-event-contract.md](cross-platform-event-contract.md)
102行目で指摘済みの`reflection_saved`の`moodBefore`/`moodAfter`自由記述）
であり、本Contract提案はこれに一切触れない。

**分類: privacy上の問題なし**。

---

## 15. Existing Analytics Test Coverage（Phase 14）

| 対象 | test file | 状態 |
|---|---|---|
| `searchEvents.ts`（`concierge_result_impression`/`shrine_detail_transition`等） | `apps/web/src/lib/analytics/__tests__/searchEvents.test.ts` | 存在 |
| `cardEvents.ts` | `apps/web/src/lib/analytics/__tests__/cardCtr.test.ts` | 存在 |
| `billing.ts` | `apps/web/src/lib/analytics/__tests__/billing.test.ts` | 存在 |
| `trackRecommendationQualityFromRecommendations`（`features/concierge/hooks.ts`） | **なし** | `TEST_GAP` |
| Backend `_attach_recommendation_reason_quality` | `test_recommendation_reason_v4.py`にquality算出自体のテストはあるが、event送信までの結線テストはBackend側の責務外（Frontend側で行うべき） | 部分的 |

**分類: 追加実装時は`hooks.ts`のtrackRecommendationQuality呼び出しに
対する新規テストが必須**（`TEST_GAP`、既存に倣うテストパターンは
`searchEvents.test.ts`を参照すればよい）。

---

## 16. Proposed Contract（Phase 15）

**既存イベントへのproperty追加のみを提案し、新規イベントは追加しない。**
`recommendation_quality`イベントは既にshrineId/threadId/recommendationRank
というjoin keyと、Backend `recommendation_reason_quality`という結線経路を
持っており、6章の3必須propertyを追加するだけで7章の前提条件（発火時点での
計算）を自然に満たせる。

### 既存: `recommendation_quality`（変更なし部分）

```
source, threadId, shrineId, recommendationRank, accessLevel,
shrine_data_rate, consultation_reflection_rate, fallback_reason_rate,
evidence_rate, action_grounding_rate, is_ai_inference_only, fallback_source
```

### 提案: 追加3 property（必須のみ）

```
knowledge_backing_class: "FULLY_KNOWLEDGE_BACKED" | "PARTIALLY_KNOWLEDGE_BACKED"
                          | "LEGACY_BACKED" | "UNKNOWN"
deity_knowledge_used: boolean
history_knowledge_used: boolean
```

Backend側の変更範囲（設計のみ、実装しない）: `concierge_chat.py`の
`_attach_recommendation_reason_quality()`内で、既に呼び出し済みの
`_build_score_v3_candidate_profile(rec)`の結果を
`recommendation_quality_measurement.build_shrine_reason_provenance()`
（PR #2382で追加済み）へそのまま渡し、`rec["recommendation_reason_quality"]`
dictへ3 propertyを追加する。**新しい計算ロジックの実装は不要**
（既存の分類関数を呼ぶだけ）。

Frontend側の変更範囲（設計のみ）: `hooks.ts`の
`trackRecommendationQualityFromRecommendations()`で、既存の
`quality.shrine_data_rate`等と同じパターンで3つのkeyを追加するだけ。

---

## 17. Backward Compatibility（Phase 16）

- 既存の7 property（`shrine_data_rate`等）は変更しない。
- 新規3 propertyはoptional（`quality.knowledge_backing_class ?? null`の
  ようなfallbackを踏襲すれば、Backend未対応時でもFrontend側は壊れない）。
- PostHog上の既存dashboard・aggregationは、propertyが追加されるだけで
  既存クエリの結果は変わらない（既存propertyのrename・削除を伴わない）。
- 既存consumer（`recommendation-quality-analytics-boundary.md`が定義する
  Backend/Web/PostHog/Mobileの責務境界）とも矛盾しない: 「qualityの正本は
  Backend」という既存契約をそのまま踏襲し、Web側は新propertyを再計算せず
  受け取って転送するのみ。

**分類: backward compatibility上の問題なし**。

---

## 18. Rollout Design（Phase 17）

```
PR1: Backend側でrecommendation_reason_qualityへ3 property追加
     （build_shrine_reason_provenance()の呼び出しのみ、新規ロジックなし）
     + Backend側テスト追加

PR2: Frontend側でtrackRecommendationQualityFromRecommendations()へ
     3 property追加 + hooks.tsのテスト新規追加（15章のTEST_GAP解消）

PR3（optional）: visit_doneへrank/resultSetIdを追加
     （5章「部分的attribution gap」解消、独立して実施可能）

PR4（別トラック）: PostHog dashboard設計・実装
     （本Contractのスコープ外、[knowledge-recommendation-quality-audit.md](knowledge-recommendation-quality-audit.md)
     Next PR候補Aと同一）
```

PR1とPR2は独立した安全な単位に分割できる（PR1のみでもBackend response
に新フィールドが増えるだけで実害はなく、PR2が未着手でも既存Frontendは
単に新フィールドを無視するだけで壊れない）。

---

## 19. Baseline / Sample-size Limitation（Phase 18）

具体的なイベント数・セッション数・期間の目標値は、本監査の範囲では
根拠を持たない。

**`SAMPLE_SIZE_NOT_YET_DEFINED`**。

[knowledge-recommendation-quality-baseline.md](knowledge-recommendation-quality-baseline.md)
のローカルDB実測（sample 100件中`FULLY_KNOWLEDGE_BACKED`85件・`UNKNOWN`
15件、`PARTIALLY`/`LEGACY`ともに0件）は、Production側でも近い分布に
なる可能性を示唆するが、これは「1推薦あたりの分類」の分布であり、
「行動指標比較に必要なイベント数」の算出根拠にはならない。実装後、
実際のイベント発生率を観測してから統計的に十分なサンプルサイズを
決定すべきである。

---

## 20. Decision Criteria（Phase 19）

Analytics実装後、以下が判断可能になる:

- `FULLY_KNOWLEDGE_BACKED`群が`UNKNOWN`群と比べてCTR/Save Rate/Visit
  Intent Rateが高いか
- `deity_knowledge_used`/`history_knowledge_used`の有無で行動差があるか

**因果関係と相関の区別**: 上記はいずれも観察的な相関であり、
Knowledge有無がランダムに割り当てられているわけではない（Knowledgeを
持つ神社は`popular_score`や地域等の点で元々偏りがある可能性がある、
[post-batch16-knowledge-next-track-comparison.md](post-batch16-knowledge-next-track-comparison.md)
参照）。相関が確認できても「Knowledgeを追加すれば行動が改善する」という
因果主張はできない。A/Bテストや準実験的な設計が必要になる場合がある点を、
実装判断時の前提として明記する。

---

## 21. Gap Classification（Phase 20）

| ID | 分類 | 内容 | Severity | 影響ファイル | 依存 | コスト |
|---|---|---|---|---|---|---|
| A | `IMPRESSION_GAP` | 該当なし（4章） | — | — | — | — |
| B | `ATTRIBUTION_GAP` | `visit_done`にrank/resultSetIdがない（5章） | Low | `ShrineDetailArticle.tsx` | INDEPENDENT | S |
| C | `QUALITY_PROPERTY_GAP` | `knowledge_backing_class`等がイベントpayloadに存在しない（6章） | **High** | `concierge_chat.py`, `hooks.ts` | INDEPENDENT | S |
| D | `JOIN_KEY_GAP` | 該当なし（7章、既存keyで十分） | — | — | — | — |
| E | `FUNNEL_EVENT_GAP` | Retry/相談再入力イベントが存在しない（12章） | Medium | 該当Frontendコンポーネント（未特定） | INDEPENDENT | M（新規イベント設計を要する） |
| F | `DASHBOARD_GAP` | PostHog dashboard未整備（[knowledge-recommendation-quality-audit.md](knowledge-recommendation-quality-audit.md)で既出） | Medium | PostHog側 | C（QUALITY_PROPERTY_GAP解消）に依存 | M |

---

## 22. Smallest Valuable PR（Phase 21）

**「既存`recommendation_quality`イベントへ、PR #2382で実装済みの
`build_shrine_reason_provenance()`の分類結果（`knowledge_backing_class`/
`deity_knowledge_used`/`history_knowledge_used`）を追加する」**
（18章PR1+PR2を1つの原則として統合した最小案）。

これが最小である理由:

- 新規イベントを作らない（Backward compatibility章の通り、既存イベントの
  拡張のみ）
- 新規分類ロジックを実装しない（PR #2382の既存関数をそのまま呼ぶ）
- 新規join keyを導入しない（既存threadId/shrineId/recommendationRankで
  十分）
- Backend/Frontendとも数行〜数十行規模の変更で完結する

---

## 23. Cost / Risk（Phase 22）

| 項目 | 値 |
|---|---|
| S/M/L | S |
| Backend | 小（`_attach_recommendation_reason_quality()`内で1関数呼び出し追加、3 dict key追加） |
| Frontend | 小（`trackRecommendationQualityFromRecommendations()`内で3 key追加） |
| Analytics | PostHog側のスキーマ変更は不要（新propertyは自動的に既存eventのpayloadへ追加されるだけ） |
| Migration | なし |
| Production write | なし（Analyticsイベント送信のみ、DB書き込みではない） |
| rollout risk | 低（optional property追加、既存フィールドの変更なし、18章の通り2PRへ分割可能） |

---

## 24. Mother Ship Decision Points

1. 22章の最小PR（`recommendation_quality`イベントへの3 property追加）を
   先に実装する
2. [knowledge-recommendation-quality-audit.md](knowledge-recommendation-quality-audit.md)
   のPR候補（Quality Measurement再計測 / Shadow Ranking / Runtime Evidence UX）
   のいずれかを先に進める
3. Retry/相談再入力イベント（21章E）の新規設計を先に検討する
4. `visit_done`のrank/resultSetId不足（21章B）を先に解消する
5. 何も実装せず、[knowledge-recommendation-quality-baseline.md](knowledge-recommendation-quality-baseline.md)
   の限界（Production実分類breakdown未確認）を先に埋める

Codexはこれらのどれかを選ばない。

---

## Final Classification

**`KNOWLEDGE_RECOMMENDATION_ANALYTICS_CONTRACT_READY_WITH_LIMITATIONS`**

既存Analyticsイベントの棚卸し・Funnel Coverage・Attribution状態・Join
戦略・最小Contract案・Rollout設計・Gap分類・最小価値PR・コスト比較を
完了した。制限事項: Retry Rate計測不能（Funnel Event Gap）、
Sample-sizeの具体的根拠なし（`SAMPLE_SIZE_NOT_YET_DEFINED`）、
`shrine_decision(map_search)`と`route_open`の二重記録の正本未決定。

**本監査では実装の着手判断・優先順位を一切決定しない。**
