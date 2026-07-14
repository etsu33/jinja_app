# Root Documents Classification Audit

## 目的

## 監査対象

## 分類基準

## Inventory

## Active候補

- billing-paywall.md
- premium-experience.md
- pricing.md
- recommendation-reason-v4-contract.md
- recommendation-v4-interpreter-contract.md

## Reference候補

- analytics-payload-audit.md
- recommendation-score-v3-design.md
- recommendation-v4-copy-guideline.md
- monetization-flow-design.md
- premium-plan-design.md
- premium-retention-strategy.md

## Archive候補

- access-tier-copy-audit.md
- analytics-card-events.md
- analytics-event-storage-audit.md
- billing-attribution-design.md
- card-ctr-aggregation.md
- concierge-ranking-observation.md
- history-shift-deep-reflection-audit.md
- mobile-release-readiness-audit.md
- premium-analytics-dashboard.md
- premium-card-matrix.md
- recommendation-score-v3-roadmap.md
- recommendation-v4-action-suggestion-audit.md
- recommendation-v4-active-readiness-plan.md
- recommendation-v4-consultation-brush-up.md
- recommendation-v4-explanation-audit.md
- recommendation-v4-reason-facts-e2e-audit.md
- recommendation-v5-design.md
- shrine-detail-analytics-route.md
- shrine-detail-policy-audit.md

## 判断保留

- direction-ranking-design.md
- analytics-payload-audit.mdの現行実装との一致
- premium-card-matrix.mdの現行実装への反映状況

## Delete候補

- なし

## 移動候補

### docs/core候補

### docs/product候補

### docs/analytics候補
analytics-card-events.md
analytics-payload-audit.md
card-ctr-aggregation.md
premium-analytics-dashboard.md
shrine-detail-analytics-route.md

### docs/audit候補
access-tier-copy-audit.md
analytics-event-storage-audit.md
concierge-ranking-observation.md

### docs/infra・docs/ops候補

## 判断保留

- analytics-card-events.md

## 参照リスク

## PR分割方針

## 本監査で変更しないもの

## 更新ルール


## A1 Analytics・計測系

### 判定

| 文書 | Status候補 | 移動先候補 | 参照状況 | 判断根拠 |
|---|---|---|---|---|
| `access-tier-copy-audit.md` | Archive | `docs/audit/` | 参照なし | Access Tier Copy接続時点の判断とTODOを含む |
| `analytics-card-events.md` | Archive | `docs/analytics/` | `docs/analytics/save-premium-correlation.md`から参照 | Event契約、監査、移行計画、PR履歴が混在する。現行実装済みの`retentionEvents.ts`と`searchEvents.ts`をplannedと記載し、PayloadおよびEvent名にも現行実装との差異がある |
| `analytics-event-storage-audit.md` | Archive | `docs/audit/` | 参照なし | Analytics保存先とProvider接続状況の時点監査 |
| `analytics-payload-audit.md` | Reference候補 | `docs/analytics/` | `docs/audit/cross-platform-event-contract.md`から参照 | Payloadおよび`sessionId`設計背景の補足資料。現行実装との一致確認後に確定する |
| `card-ctr-aggregation.md` | Archive | `docs/analytics/` | 参照なし | 集計設計と未実装Phase、次PR計画を含む |
| `concierge-ranking-observation.md` | Archive | `docs/audit/` | `docs/audit/recommendation-quality-score-v3-audit.md`から参照 | Ranking WeightとCandidate Poolの観測履歴 |
| `premium-analytics-dashboard.md` | Archive | `docs/analytics/` | 参照なし | Dashboard・AB Test・後続実装計画の記録 |
| `shrine-detail-analytics-route.md` | Archive | `docs/analytics/` | 参照なし | Shrine Detail Analytics導入時のEvent棚卸しと次PR計画 |

### 現行契約の分離

`analytics-card-events.md`は現行契約として継続利用しない。

現行Analytics契約は、以下の実装を正本として別文書へ再構成する。

- `apps/web/src/lib/analytics/cardEvents.ts`
- `apps/web/src/lib/analytics/retentionEvents.ts`
- `apps/web/src/lib/analytics/searchEvents.ts`
- `apps/web/src/lib/analytics/billing.ts`
- `apps/web/src/lib/analytics/track.ts`
- `apps/web/src/lib/analytics/providers.ts`

契約文書候補は`docs/analytics/analytics-event-contract.md`とする。

### 実装上の判断保留

現在の実装では、Domain Helperが`track.ts`を経由せずProviderを直接呼び出している。

そのため、`analyticsSessionId`、`sessionId`、timestamp、開発ログ保存の共通付与範囲は別途実装監査が必要である。

また、ProductionでPostHog Keyが未設定の場合のFallback Provider経路には再帰の可能性があるため、文書整理PRとは分離して確認する。

## A2 Audit・Readiness系

### 判定

A2の7文書は、すべて監査時点の実装状態、判断、TODO、次PR候補またはPhase計画を含む。

現行仕様の正本としては利用せず、監査履歴としてArchive候補に分類する。

| 文書 | Status候補 | 移動先候補 | 判断根拠 | 現行仕様への移管候補 |
|---|---|---|---|---|
| `history-shift-deep-reflection-audit.md` | Archive | `docs/audit/` | Premium Cardの責務分離を検討した時点監査。次PR候補とTODOを含む | Previous Comparison、History Shift、Deep Reflectionの責務 |
| `mobile-release-readiness-audit.md` | Archive | `docs/audit/` | Mobile Release前提のチェックリストと進捗記録 | EAS、実機、API、認証のRelease条件 |
| `recommendation-v4-action-suggestion-audit.md` | Archive | `docs/audit/` | Action Suggestion v4の責務を確認したPhase2監査 | Recommendation ReasonとAction Suggestionの責務境界 |
| `recommendation-v4-active-readiness-plan.md` | Archive | `docs/audit/` | Active化判断、観測条件、Rollback、Implementation Phaseを含む時点計画 | Active化GuardrailとRollback条件 |
| `recommendation-v4-explanation-audit.md` | Archive | `docs/audit/` | Explanationレイヤーの実装状態と境界を確認した監査 | Reason、Explanation、Action、reason_factsの責務境界 |
| `recommendation-v4-reason-facts-e2e-audit.md` | Archive | `docs/audit/` | reason_factsのBackend E2Eと不足Testを確認した監査 | Field Responsibility、Primary Reason、E2E契約 |
| `shrine-detail-policy-audit.md` | Archive | `docs/audit/` | Shrine Detailのカード接続候補と優先順位を整理した監査 | Context Reason、Personal Meaning、Saved Recordの責務 |

### Delete候補

A2にはDelete候補はない。

各文書には、当時の実装判断、責務分離、テスト範囲またはリリース条件に関する固有情報がある。

### 移管方針

Archive化前に、現在も有効な責務定義が現行正本文書へ反映済みかをカテゴリ別PRで確認する。

本監査PRでは、個別文書の移動、本文変更、責務移管は行わない。


## A3 Recommendation系

### 判定

| 文書 | Status候補 | 移動先候補 | 参照状況 | 判断根拠 |
|---|---|---|---|---|
| `direction-ranking-design.md` | 判断保留 | `docs/product/` | 参照なし | Direction SignalとRanking Priorityを定義するが、現行Score実装との一致が未確認 |
| `recommendation-reason-v4-contract.md` | Active候補 | `docs/product/` | Copy Guidelineから参照 | Recommendation Reason v4の責務、入力、出力、Layer Boundaryを定義する契約文書 |
| `recommendation-score-v3-design.md` | Reference候補 | `docs/analytics/` | Score v3監査から参照 | Score v3のSignalと計算式の設計背景。実装Phaseとドラフトを含むため現行値は実装を正本とする |
| `recommendation-score-v3-roadmap.md` | Archive | `docs/audit/` | Score v3監査から参照 | Roadmap、Active化、Dashboard、観測Snapshot、TODOが混在する時点記録 |
| `recommendation-v4-consultation-brush-up.md` | Archive候補 | `docs/audit/` | 参照なし | Consultation改善作業のScope・KPIを整理した短期計画 |
| `recommendation-v4-copy-guideline.md` | Reference候補 | `docs/knowledge/` | Action Suggestion監査から参照 | v4固有のCopy Ruleを持つが、Knowledge BaseのRecommendation Copy Guideと責務が重複する |
| `recommendation-v4-interpreter-contract.md` | Active候補 | `docs/product/` | Copy Guidelineから参照 | Consultation InterpreterのField ContractとSource of Truthを定義 |
| `recommendation-v5-design.md` | Archive | `docs/audit/` | 参照なし | 未実装のv5設計と次PR候補を含む将来計画 |

### 現行契約候補

以下は現行実装との一致確認後、Active文書として整理する候補とする。

- `recommendation-reason-v4-contract.md`
- `recommendation-v4-interpreter-contract.md`

### Copy Guide統合候補

`recommendation-v4-copy-guideline.md`と`docs/knowledge/recommendation-copy-guide.md`を並列の正本にはしない。

v4固有規則のうち現在も有効な内容をKnowledge Baseへ統合し、root文書はReferenceまたはArchiveへ整理する。

### Delete候補

現時点ではDelete候補を確定しない。

`recommendation-v4-consultation-brush-up.md`は、固有内容が現行文書へ完全に吸収済みであることを確認できた場合のみDelete候補とする。


## A4 Premium・Billing系

### 判定

| 文書 | Status候補 | 移動先候補 | 参照状況 | 判断根拠 |
|---|---|---|---|---|
| `billing-attribution-design.md` | Archive | `docs/audit/` | 参照なし | Card AnalyticsからCheckoutまでのAttribution課題、候補案、次PR、TODOを含む時点設計 |
| `billing-paywall.md` | Active候補 | `docs/product/` | `pricing.md`、`premium-experience.md`から参照 | Billing Status、Paywall情報、Premium優先、Free制限、Server最終判定を定義する契約文書 |
| `monetization-flow-design.md` | Reference候補 | `docs/product/` | Phase7関連監査・Archive文書から参照 | Premium提示タイミング、入口、CTA、Subscription Flowを補足する収益導線設計 |
| `premium-card-matrix.md` | Archive候補 | `docs/audit/` | 参照なし | Access Level別Card表示設計を持つが、現在地、次の一手、Payload案、実装TODOを含む |
| `premium-experience.md` | Active候補 | `docs/product/` | Core、Meaning Layer、Pricing、Shrine Detailから参照 | Free / Premiumの体験差、表現、画面別境界を定義する現行正本候補 |
| `premium-plan-design.md` | Reference候補 | `docs/product/` | Phase7関連文書から参照 | Reflection、Timeline、History、Memory等を含むPremium価値の包括的な構想 |
| `premium-retention-strategy.md` | Reference候補 | `docs/product/` | 参照なし | 保存、履歴、比較を中心としたPremium継続価値とKPIの戦略補足 |
| `pricing.md` | Active候補 | `docs/product/` | `shrine-detail-layer.md`から参照 | 「何に対して支払うか」、Free / Premiumの価値境界、価格表現原則を管理する |

### 正本の責務分離

Premium・Billing関連の現行文書は、以下の責務に分離する。

| 文書 | 責務 |
|---|---|
| `billing-paywall.md` | 課金状態、利用可否、Paywall判定、Server責務 |
| `pricing.md` | 支払対象、Free / Premiumの価値境界、価格表現 |
| `premium-experience.md` | Free / Premiumの体験差、画面別境界、利用可能な表現 |
| `monetization-flow-design.md` | Premium導線を提示する時点、文脈、CTA、復帰導線 |

`premium-plan-design.md`は将来構想を含むReference、`premium-retention-strategy.md`は継続価値の戦略補足として扱う。

### Archive候補

`billing-attribution-design.md`はAttribution実装前の設計・判断履歴としてArchive候補にする。

`premium-card-matrix.md`はAccess Level別UI設計の履歴として保存し、現在も有効な表示境界が`premium-experience.md`または実装へ反映済みかを別PRで確認する。

### Delete候補

A4にはDelete候補はない。

各文書は、課金判定、価値境界、収益導線、継続価値、表示制御またはAttributionに関する固有情報を持つ。

## A5 Journey・Shrine Detail・投稿系

### 判定

| 文書 | Status候補 | 移動先候補 | 参照状況 | 判断根拠 |
|---|---|---|---|---|
| `action_state_behavior_checklist.md` | Archive候補 | `docs/audit/` | 参照なし | 動作確認チェックリストであり、仕様契約ではない |
| `journey-timeline-api-plan.md` | Archive候補 | `docs/audit/` | 参照なし | Journey Timeline API のPhase計画・Backend/Mobile変更候補を含む時点設計 |
| `journey-timeline-design.md` | Reference候補 | `docs/product/` | 参照なし | Journey Timeline の設計思想・情報設計・Migration方針を整理した設計資料 |
| `reflection-timeline-design.md` | Active候補 | `docs/product/` | Phase7関連文書から参照 | Reflection Timeline の役割、UX、KPI、Premium接続を定義する現行設計 |
| `shrine-detail-layer.md` | Active候補 | `docs/product/` | Pricing、Premium Experience、Architecture等から参照 | 神社詳細のPublic / Context / Personal Layerと責務境界を定義 |
| `shrine-detail-meaning-layer.md` | Reference候補 | `docs/product/` | 参照なし | Shrine Detail のMeaning Layer設計補足ガイド |
| `shrine-detail-v3-design.md` | Active候補 | `docs/product/` | Phase7 Roadmapから参照 | Shrine Detail v3 のUX・Analytics・Premium接続を定義する正本候補 |
| `shrine-submission-flow.md` | Active候補 | `docs/product/` | Architectureから参照 | 神社投稿、duplicate_candidate契約、推薦利用方針を定義する現行仕様 |

### Delete候補

A5にはDelete候補はない。

Journey、Shrine Detail、投稿フローそれぞれに固有の責務を持ち、他文書からも参照されている。

### 現行契約候補

- `reflection-timeline-design.md`
- `shrine-detail-layer.md`
- `shrine-detail-v3-design.md`
- `shrine-submission-flow.md`

### Reference候補

- `journey-timeline-design.md`
- `shrine-detail-meaning-layer.md`

### Archive候補

- `action_state_behavior_checklist.md`
- `journey-timeline-api-plan.md`
