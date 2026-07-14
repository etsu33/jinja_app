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

## A6 Core / Knowledge

### Inventory

#### docs/core（5ファイル）

| 文書 | 見出し構造 | Source of Truth表記 | 更新ルール表記 |
|---|---|---|---|
| `architecture.md` | 目的 / 全体フロー / レイヤーと責務 / Consultation Interpretation / Meaning Translation / Recommendation / Score v3 / 画面責務 / データ責務 / 認証アーキテクチャ / 正本ドキュメント / 変更ルール | 「正本ドキュメント」節で各詳細仕様の委譲先を明示 | 「変更ルール」節あり。責務境界・全体依存関係が変わる場合のみ更新 |
| `meaning-layer.md` | 概要 / 責務 / 神社とは何か / なぜ推薦するのか / AIは何を解釈しているのか / なぜ断定しないのか / 意味ある移動体験とは何か / 関連ドキュメント | 「関連ドキュメント」で詳細仕様の正本を列挙 | 明示的な更新ルール節なし（思想文書のため） |
| `meaning-layer-connection.md` | 目的 / 全体フロー / 入力 / 出力 / Composerとの接続 / Recommendationとの接続 / Fallback / 責務境界 / 保存方針 / 関連ドキュメント | 「関連ドキュメント」で接続仕様以外は各正本へ委譲と明記 | 「本ドキュメントは接続仕様のみを定義する」と範囲限定あり |
| `narrative-guideline.md` | Purpose / Narrative Principles / Input / Output / Prohibited Expressions / Responsibility / Related Documents | 「Related Documents」で執筆原則のみの範囲限定 | 「本ドキュメントは...執筆原則のみを定義する」と明記 |
| `roadmap.md` | 目的 / 現在地 / 開発原則 / Phase1〜8 / 現在の実装順序 / 文書管理ルール | なし（Roadmap自体が正本） | 「文書管理ルール」節あり。フェーズ・順序・ゴール・完了条件が変わる場合のみ更新 |

#### docs/knowledge（8ファイル、README含む）

| 文書 | 見出し構造 | Source of Truth表記 | 更新ルール表記 |
|---|---|---|---|
| `README.md` | 目的 / ドキュメント構成 / 依存関係 / 更新ルール / 更新順序 | 「LLMや実装担当者が変わってもKAMI MUSUBIらしい提案品質を維持するための正本」と明記 | 「更新ルール」「更新順序」節あり。上流→下流の更新順序（shrine-profile-spec→shrine-data-guide→meaning-layer-spec→recommendation-copy-guide→action-guide→reflection-guide→glossary）を規定 |
| `shrine-profile-spec.md` | 結論(先出し) / 目的 / 知識モデル:7 Layer / 対象範囲 / データの生成・保存区分 / Profile v2項目 / 表示用項目 / 推薦用項目 / 修正優先順位 / 未確定事項 | 事実・実装事実・推測・仮説を区分して記載 | 明示的な更新ルール節なし。P0/P1/P2の修正優先順位あり |
| `shrine-data-guide.md` | 目的 / 入力原則 / 必須項目 / 記述例 / 禁止事項 / 品質確認 / 未確定事項 | 「今後の関連仕様」で前提とするKnowledge Base文書を列挙 | 明示的な更新ルール節なし |
| `meaning-layer-spec.md` | 目的 / Meaning Layer全体像 / 事実から意味への変換 / 人生テーマ / 相談テーマ / 品質基準 / 未確定事項 | なし | なし |
| `recommendation-copy-guide.md` | 目的 / 推薦文の構造 / 事実 / 意味 / ユーザーとの接点 / 禁止表現 / 品質基準 / 未確定事項 | なし | なし |
| `action-guide.md` | 目的 / 行動提案の原則 / 参拝前・参拝中・参拝後 / 禁止事項 / 品質基準 / 未確定事項 | なし | なし |
| `reflection-guide.md` | 目的 / 振り返りの原則 / 参拝前後の比較 / 感情の変化 / 次の一歩 / 禁止事項 / 品質基準 / 未確定事項 | なし | なし |
| `glossary.md` | 目的 / 用語一覧 / 意味レイヤ用語 / 推薦用語 / 行動用語 / 振り返り用語 / 命名規則 | 「各仕様書で利用する用語は、本書の定義を正本とする」と明記 | 「新しい概念を追加する場合は、各仕様書へ追加する前に本書へ定義を追加する」と明記 |

**観察**: `meaning-layer-spec.md` / `recommendation-copy-guide.md` / `action-guide.md` / `reflection-guide.md`の4文書は見出しのみで本文が箇条書きレベルに留まり、`shrine-profile-spec.md`や`shrine-data-guide.md`と比べて記述密度が薄い。README更新順序を正本とする前提には支障ないが、内容の厚みは不均衡。

### Reference Audit

#### README・architecture・product・audit文書からの参照

| 対象 | 参照元（抜粋） | 状況 |
|---|---|---|
| `docs/core/architecture.md` | `docs/README.md`、`docs/project-context.md`、`docs/AGENTS.md`、`docs/authentication-flow.md`、`docs/product/*`（7文書）、`docs/meaning-layer/*`（5文書）、`docs/mobile/*`（2文書）、`docs/phase7-ux-monetization-roadmap.md` | 最多参照。Core文書の中心 |
| `docs/core/meaning-layer.md` | 同上系統16文書 | Meaning Layer思想の参照元として広く利用 |
| `docs/core/meaning-layer-connection.md` | `project-context.md`、`meaning-layer/*`、`mobile/*`、`ui/concierge-result-wireframe.md`等9文書 | 接続仕様として実装系文書から参照 |
| `docs/core/narrative-guideline.md` | `project-context.md`、`README.md`、`product/action-suggestion-layer.md`（Archive）、`product/meaning-translation-mapping.md`、`product/visit-reflection-flow.md` | 表示文言原則として参照 |
| `docs/core/roadmap.md` | `project-context.md`、`README.md`、`phase7-ux-monetization-roadmap.md`（Archive）、`phase5-behavior-measurement-plan.md`（Archive） | 現行文書からの参照はREADME・project-contextの2件のみ |
| `docs/knowledge/README.md` | `project-context.md`、`docs/README.md` | Knowledge Base入口として参照 |
| `docs/knowledge/recommendation-copy-guide.md` | `docs/audit/knowledge-base-consistency-audit.md`、本監査文書 | 監査文書からのみ参照 |
| `docs/knowledge/shrine-profile-spec.md`他6文書（shrine-data-guide / meaning-layer-spec / action-guide / reflection-guide / glossary） | `docs/audit/knowledge-base-consistency-audit.md`、およびKnowledge Base内の相互参照（README、各Guideの関連仕様節） | root/product/mobile等の実装系文書からのファイルパス参照は確認できず |

**観察**: `docs/knowledge`配下の個別ファイル（README以外）は、`docs/product/`や`docs/mobile/`等の実装系文書から直接ファイルパスで参照されることがほぼない。参照されているのは`docs/audit/knowledge-base-consistency-audit.md`（責務・用語監査）のみであり、Knowledge Base自体がまだ実装ドキュメントの一次参照先として定着していない可能性がある。

#### 実装からの参照確認

コード内（`*.py` / `*.ts` / `*.tsx`）に`docs/core`・`docs/knowledge`へのパス参照は確認できなかった（grep結果0件）。実装とドキュメントの対応は、`docs/audit/knowledge-base-consistency-audit.md`が現行DB・Service実装を突き合わせる形で個別に監査済み。

#### 古いファイル名への参照確認

- `docs/architecture.md` → `docs/core/architecture.md`、`docs/roadmap.md` → `docs/core/roadmap.md`への移動をgit履歴で確認（rename 100%）。
- `docs/shrine-detail-layer.md:110`が移動前の旧パス`docs/architecture.md`を参照したまま残っている（**参照切れ、要修正**）。
- `meaning-layer.md` / `meaning-layer-connection.md` / `narrative-guideline.md`は`docs/core/`への移動前から現ファイル名のため、旧パス参照は確認されなかった。

### Responsibility Audit

#### docs/core内の責務重複確認

`architecture.md`（全体構造）、`meaning-layer.md`（思想）、`meaning-layer-connection.md`（接続仕様）、`narrative-guideline.md`（文章原則）、`roadmap.md`（開発順序）は扱う抽象度・出力物が明確に異なり、重大な重複は確認されなかった。`architecture.md`と`meaning-layer-connection.md`はともにMeaning Layerの入出力フローを図示するが、`architecture.md`は全体レイヤーの1セクションとして概要を示すに留め、詳細な接続仕様（Composer、Fallback等）は`meaning-layer-connection.md`へ委譲されており、責務分離は維持されている。

#### docs/knowledge内の責務重複確認

既存監査`docs/audit/knowledge-base-consistency-audit.md`の「4. 用語差分」「9. 重複責務」で以下が既に指摘済み。

- Recommendation / Recommendation Reason / Recommendation Readiness / Recommendation Readyの用語が、`glossary.md`・`shrine-profile-spec.md`・`recommendation-copy-guide.md`の間で表記・定義が不統一（P0）
- Consultation（相談解析）とConsultation Layer（User×Shrineの一致結果）が`shrine-profile-spec.md`内で混在（P0）
- `shrine-profile-spec.md`の7 LayerにRecommendation Layerが存在しない一方、`glossary.md` / `recommendation-copy-guide.md` / `action-guide.md` / `reflection-guide.md`はRecommendationをMeaningとActionの間の独立層として扱う（P0）

本監査ではこれらを追加で再検証せず、既存監査結果を正として引き継ぐ。

#### core / knowledge間の責務重複確認

| 観点 | 結果 |
|---|---|
| Meaning Layerの扱い | `core/meaning-layer.md`は「なぜMeaning Layerが必要か」という思想・禁止事項を定義。`knowledge/meaning-layer-spec.md`は「Stored/Derived/Runtimeの区分」「history_theme等の項目定義」という構造仕様を定義。抽象度が異なり重複なし |
| Stored/Derived/Runtime区分 | `core/architecture.md`の「Runtime Snapshot」節と`knowledge/shrine-profile-spec.md`の「データの生成・保存区分」節は同じ4区分（Stored/Derived/Runtime/Governance）を用いるが、`architecture.md`は対象項目の列挙に留め、区分の定義・境界ルールの詳細は`knowledge`側が正本という関係が保たれている |
| 用語定義 | core側に用語集はなく、`knowledge/glossary.md`が唯一の用語正本。重複なし |
| 表示文言原則 | `core/narrative-guideline.md`は表現の原則（可能性表現・断定禁止等）、`knowledge/recommendation-copy-guide.md`は推薦文特有の構造（Fact→Meaning→User Connection→Recommendationの順序、出典必須項目）を定義。両文書とも禁止表現（宗教的断定・心理的断定・効果保証）の記述内容が類似するが、相互参照が設定されていない |

**軽微な指摘**: `narrative-guideline.md`と`recommendation-copy-guide.md`の禁止表現記述は内容が重複気味だが、責務の重複ではなく相互リンク欠落として扱う。

#### product文書との責務重複確認

| knowledge文書 | 対応product文書 | 関係 |
|---|---|---|
| `meaning-layer-spec.md` | `product/meaning-translation-mapping.md` | knowledge側は「Meaning Layerの責務・境界・4区分」という抽象仕様、product側は「history_themeへの変換テーブル・カテゴリ定義」という実装レベルの詳細。`meaning-translation-mapping.md`はStatus:Activeで「history_themeのカテゴリ名称と定義は`product/history-theme-taxonomy.md`を正本とする」とさらに委譲しており、階層的な分離が維持されている |
| `recommendation-copy-guide.md` | root `recommendation-reason-v4-contract.md`（A3で移動候補） | knowledge側は「推薦文の文章構造原則」、root側は「fact/interpretation/actionの実装関数対応（concierge_chat_ranking.py等）」という実装トレース。抽象度は異なるが、扱う分割（3層構造）が類似しており統合または相互参照の余地がある |

#### Recommendation文書との重複確認

A3で現行契約候補とされたroot `recommendation-reason-v4-contract.md`および`recommendation-v4-interpreter-contract.md`は、`knowledge/recommendation-copy-guide.md`と以下の関係にある。

- `knowledge/recommendation-copy-guide.md`: 「何を書いてよいか・書いてはいけないか」という文章生成のガイドライン（Fact→Meaning→User Connection→Recommendationの順序、出典必須項目、禁止表現）
- root `recommendation-reason-v4-contract.md`: 「どの関数がどう実装しているか」という実装対応表（fact/interpretation/actionの分離、呼び出し元ファイル）

両者は正本の重複ではなく上位（生成原則）・下位（実装契約）の関係にあるが、3分割の名称が「Fact/Meaning/User Connection」（knowledge）と「Fact/Interpretation/Action」（root、実装と一致）で異なっており、相互参照もない。knowledge側の「未確定事項」にある「Recommendation Version管理」「LLM Promptとの責務分離」は、root側のcontract文書・実装で一部先行しており、knowledge側の記述更新が必要。

#### Action文書との重複確認

`knowledge/action-guide.md`（行動提案の生成原則・品質基準）と`product/action_suggestion_v4.md`（Status:Active、Input/Output Contract）は責務が分離されている。

- `action-guide.md`: Stored/Derived/Runtimeで利用できる情報の分類、参拝前後のAction例、禁止事項（一般論のみ禁止・効果保証禁止等）
- `action_suggestion_v4.md`: primary_action/secondary_action/reflection_prompt/action_sourceのContract定義、Recommendation Ranking等を扱わない旨の責務境界

重大な重複は確認されなかった。`product/action-suggestion-layer.md`（Status:Archive）は初期設計であり、現行責務は`action_suggestion_v4.md`へ移行済みと明記されている。

#### Reflection文書との重複確認

`knowledge/reflection-guide.md`（振り返りの生成原則・品質基準）と`product/visit-reflection-flow.md`（Status:Active、Visit→Reflection体験・イベント・保存責務）も同様に分離されている。

- `reflection-guide.md`: 参拝前後比較・感情の変化・次の一歩という問いの構成原則、禁止事項（心理診断禁止・正解誘導禁止等）
- `visit-reflection-flow.md`: route_open→visit_done→reflection_prompt_view→reflection_saved→history_theme履歴→next_consultationという画面遷移・Analyticsイベント・保存責務

重大な重複は確認されなかった。

### Implementation Alignment

| 確認項目 | 実装箇所 | 整合状況 |
|---|---|---|
| history_theme | `Shrine.history_theme`（`backend/temples/models.py`、CharField max_length=32、db_index）。Derivedとして事前生成値をDB保存 | `knowledge/glossary.md`の定義（「神社の歴史や由緒から抽出した意味テーマ」）と一致。Derivedが「非保存」を意味しない点は本文からは読み取りにくく、`knowledge-base-consistency-audit.md`が既に指摘済み |
| reason_facts | `backend/temples/services/concierge_chat_ranking.py`の`_build_reason_facts`、`backend/temples/services/journey_timeline.py` | `shrine-profile-spec.md`が「reason_factsはhistory_theme, culture_translation, user_selected_tag, need_tag, goriyaku_tag, text_hint, elementのいずれか1つでも存在すれば非空になる」と実装事実として明記。実装ファイルの存在と一致確認済み |
| recommendation_reason_v4 | `backend/temples/services/recommendation_reason_v4.py`の`build_recommendation_reason_v4()`。fact/interpretation/action/used_fact/used_interpretation/used_action/qualityを生成 | root `recommendation-reason-v4-contract.md`の記述（fact/interpretation/actionへの分離）と実装が一致。`knowledge/recommendation-copy-guide.md`のFact→Meaning→User Connection→Recommendationという4分割とは命名が異なる（Meaningがinterpretationの一部に相当、User Connectionに明示的に対応する層がない）。**用語の不一致は要整理** |
| action_suggestion_v4 | `backend/temples/services/action_suggestion_builder.py` | `product/action_suggestion_v4.md`のContract定義と実装ファイルが対応 |
| consultation_axis | `backend/temples/domain/consultation_axis.py`。`ConciergeThread.recommendations_v2`内へRuntime Snapshotとして保存（`concierge_chat.py`） | `knowledge-base-consistency-audit.md` 7.4節で「完全対応」と確認済み。本監査でも実装ファイルの存在を確認 |
| matched_need_tags | `backend/temples/services/concierge_chat_ranking.py`。`ConciergeThread.recommendations_v2`内へ保存 | 同上。Runtime Snapshotとして実装済み |
| Stored/Derived/Runtime境界 | `Shrine`モデル（Stored: sajin, description, goriyaku, goriyaku_tags / Derived: history_theme）、`ConciergeThread.recommendations_v2`JSONField（Runtime: matched_need_tags, consultation_axis, reason_facts, evidence等） | `knowledge/shrine-profile-spec.md`の区分定義と概ね一致。ただし`deity`→`Shrine.sajin`、`shrine_history`→`Shrine.description`はいずれも自由記述TextFieldへの部分対応であり、概念項目と物理フィールドが完全一致していない（`knowledge-base-consistency-audit.md` 7.5節と同じ結論を本監査でも再確認） |
| Recommendation Readiness実装状況 | 実装コード内に`recommendation_readiness` / `RecommendationReadiness` / `readiness_level`等の実装は確認できず（grep結果0件）。Coverage算出処理も未実装 | `knowledge/shrine-data-guide.md`および`shrine-profile-spec.md`は「Level0〜3」の段階定義を持つが、判定関数・DB保持は未実装。`knowledge-base-consistency-audit.md`が「文書定義のみ、P0」と分類した結論を本監査でも再確認。**文書は仕様として先行しているが実装が追いついていない** |

### Classification

#### Active確定

| 文書 | 理由 |
|---|---|
| `docs/core/architecture.md` | 全体レイヤー構造・責務境界の正本として広範囲から参照され、変更ルールも明記 |
| `docs/core/meaning-layer.md` | Meaning Layerの思想的正本として広範囲から参照 |
| `docs/core/meaning-layer-connection.md` | Meaning Layerの接続仕様の正本 |
| `docs/core/narrative-guideline.md` | 表示文言の執筆原則の正本 |
| `docs/core/roadmap.md` | 開発フェーズ・順序の正本 |
| `docs/knowledge/README.md` | Knowledge Base全体の入口・更新順序の正本 |
| `docs/knowledge/shrine-profile-spec.md` | 神社知識モデルの正本。事実/推測/仮説の区分が明示され監査可能性が高い |
| `docs/knowledge/shrine-data-guide.md` | 神社データ入力基準の正本 |
| `docs/knowledge/meaning-layer-spec.md` | Meaning Layer責務境界の正本（本文は薄いがREADME更新順序上必須） |
| `docs/knowledge/recommendation-copy-guide.md` | 推薦文構造の正本 |
| `docs/knowledge/action-guide.md` | 行動提案生成原則の正本 |
| `docs/knowledge/reflection-guide.md` | 振り返り生成原則の正本 |
| `docs/knowledge/glossary.md` | 用語定義の正本。他文書からの参照は少ないが、README更新順序・shrine-data-guideの関連仕様節で位置付けが明確 |

全13文書をActiveと確定する。Archive/Delete候補は確認されなかった。

#### Reference確定

該当なし。docs/core・docs/knowledgeはいずれも正本（Active）またはKnowledge Base内の必須構成文書であり、補足資料（Reference）に区分される文書はない。

#### 判断保留確定

該当なし。A1〜A5と異なり、docs/core・docs/knowledgeは全文書が現行の思想・責務・知識正本として機能しており、実装との対応も個別に監査済み（`knowledge-base-consistency-audit.md`）であるため判断を保留する文書はない。

#### 現行契約候補確定

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/narrative-guideline.md`
- `docs/core/roadmap.md`
- `docs/knowledge/README.md`
- `docs/knowledge/shrine-profile-spec.md`
- `docs/knowledge/shrine-data-guide.md`
- `docs/knowledge/meaning-layer-spec.md`
- `docs/knowledge/recommendation-copy-guide.md`
- `docs/knowledge/action-guide.md`
- `docs/knowledge/reflection-guide.md`
- `docs/knowledge/glossary.md`

### A7への引き継ぎ事項

- `docs/shrine-detail-layer.md:110`の`docs/architecture.md`参照切れの修正
- `knowledge/recommendation-copy-guide.md`とroot `recommendation-reason-v4-contract.md`の用語不一致（Fact/Meaning/User Connection vs Fact/Interpretation/Action）の整理
- `narrative-guideline.md`と`recommendation-copy-guide.md`の禁止表現記述の相互参照欠落
- Recommendation Readiness/Coverageの未実装状態（`knowledge-base-consistency-audit.md`のP0/P1事項）は実装フェーズへ引き継ぎ、文書分類には影響しない

### 結論

Coreは「思想・責務・依存関係」の正本、Knowledgeは「知識・コピー・データ仕様」の正本として責務分離されている。

重大な責務重複は確認されなかったが、以下の軽微な課題を確認した。

1. `docs/shrine-detail-layer.md`に移動前の旧パス`docs/architecture.md`への参照切れが残っている
2. `knowledge/recommendation-copy-guide.md`とroot `recommendation-reason-v4-contract.md`の間で概念の3分割名称（Meaning/User Connection vs Interpretation/Action）が不一致
3. `docs/knowledge`配下の個別文書（README以外）は、`docs/product/`等の実装系文書からファイルパスで直接参照されることがほぼなく、参照されているのは`docs/audit/knowledge-base-consistency-audit.md`のみ
4. Recommendation Readiness/Coverageは文書定義のみで実装が未着手（既存監査で確認済みの結論を本監査でも再確認）

これらは文書分類（Active/Reference/Archive）には影響しないため、A6の分類結果は「全13文書をActiveとする」で確定する。個別の整理は上記4点をA7以降または実装監査へ引き継ぐ。
