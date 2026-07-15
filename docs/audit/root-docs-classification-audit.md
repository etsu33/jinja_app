> 更新注記（2026-07-15）
>
> 本監査時点では`docs/knowledge/meaning-layer-spec.md`をActiveとして評価していた。その後の`docs/audit/recommendation-doc-consolidation-audit.md`における本文再監査で、独自の確定仕様を持たず、責務が以下の正本文書へ分散済みであることを確認した。
>
> - `docs/core/meaning-layer.md`
> - `docs/core/meaning-layer-connection.md`
> - `docs/product/meaning-translation-mapping.md`
> - `docs/core/recommendation-reason-contract.md`
>
> このため、`docs/knowledge/meaning-layer-spec.md`は後続監査の判断を優先し削除した。本文中のActive・必須判定は、当時の監査結果として保持する。

# Root Documents Classification Audit

## 目的

## 監査対象

## 分類基準

## Inventory

## Active確定

- billing-paywall.md
- premium-experience.md
- pricing.md
- recommendation-reason-v4-contract.md
- recommendation-v4-interpreter-contract.md

## Reference確定

- analytics-payload-audit.md
- recommendation-score-v3-design.md
- recommendation-v4-copy-guideline.md
- monetization-flow-design.md
- premium-plan-design.md
- premium-retention-strategy.md

## Archive確定

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
- analytics-payload-audit.mdと現行実装の一致確認
- premium-card-matrix.mdの現行実装反映確認
- analytics-card-events.mdの現行Analytics契約との最終照合

## Delete候補

- なし

## 移動候補

### docs/core候補

### docs/product候補

### docs/analytics候補

analytics-card-events.md analytics-payload-audit.md card-ctr-aggregation.md premium-analytics-dashboard.md
shrine-detail-analytics-route.md

### docs/audit候補

access-tier-copy-audit.md analytics-event-storage-audit.md concierge-ranking-observation.md

### docs/infra・docs/ops候補

## 参照リスク

## PR分割方針

## 本監査で変更しないもの

## 更新ルール

## A1 Analytics・計測系

### 判定

| 文書                               | Status候補    | 移動先候補        | 参照状況                                                      | 判断根拠                                                                                                                                                            |
| ---------------------------------- | ------------- | ----------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `access-tier-copy-audit.md`        | Archive       | `docs/audit/`     | 参照なし                                                      | Access Tier Copy接続時点の判断とTODOを含む                                                                                                                          |
| `analytics-card-events.md`         | Archive       | `docs/analytics/` | `docs/analytics/save-premium-correlation.md`から参照          | Event契約、監査、移行計画、PR履歴が混在する。現行実装済みの`retentionEvents.ts`と`searchEvents.ts`をplannedと記載し、PayloadおよびEvent名にも現行実装との差異がある |
| `analytics-event-storage-audit.md` | Archive       | `docs/audit/`     | 参照なし                                                      | Analytics保存先とProvider接続状況の時点監査                                                                                                                         |
| `analytics-payload-audit.md`       | ActivReferenc | `docs/analytics/` | `docs/audit/cross-platform-event-contract.md`から参照         | Payloadおよび`sessionId`設計背景の補足資料。現行実装との一致確認後に確定する                                                                                        |
| `card-ctr-aggregation.md`          | Archive       | `docs/analytics/` | 参照なし                                                      | 集計設計と未実装Phase、次PR計画を含む                                                                                                                               |
| `concierge-ranking-observation.md` | Archive       | `docs/audit/`     | `docs/audit/recommendation-quality-score-v3-audit.md`から参照 | Ranking WeightとCandidate Poolの観測履歴                                                                                                                            |
| `premium-analytics-dashboard.md`   | Archive       | `docs/analytics/` | 参照なし                                                      | Dashboard・AB Test・後続実装計画の記録                                                                                                                              |
| `shrine-detail-analytics-route.md` | Archive       | `docs/analytics/` | 参照なし                                                      | Shrine Detail Analytics導入時のEvent棚卸しと次PR計画                                                                                                                |

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

また、ProductionでPostHog Keyが未設定の場合のFallback
Provider経路には再帰の可能性があるため、文書整理PRとは分離して確認する。

## A2 Audit・Readiness系

### 判定

A2の7文書は、すべて監査時点の実装状態、判断、TODO、次PR候補またはPhase計画を含む。

現行仕様の正本としては利用せず、監査履歴としてArchiveに分類する。

| 文書                                           | Status候補 | 移動先候補    | 判断根拠                                                             | 現行仕様への移管候補                                      |
| ---------------------------------------------- | ---------- | ------------- | -------------------------------------------------------------------- | --------------------------------------------------------- |
| `history-shift-deep-reflection-audit.md`       | Archive    | `docs/audit/` | Premium Cardの責務分離を検討した時点監査。次PR候補とTODOを含む       | Previous Comparison、History Shift、Deep Reflectionの責務 |
| `mobile-release-readiness-audit.md`            | Archive    | `docs/audit/` | Mobile Release前提のチェックリストと進捗記録                         | EAS、実機、API、認証のRelease条件                         |
| `recommendation-v4-action-suggestion-audit.md` | Archive    | `docs/audit/` | Action Suggestion v4の責務を確認したPhase2監査                       | Recommendation ReasonとAction Suggestionの責務境界        |
| `recommendation-v4-active-readiness-plan.md`   | Archive    | `docs/audit/` | Active化判断、観測条件、Rollback、Implementation Phaseを含む時点計画 | Active化GuardrailとRollback条件                           |
| `recommendation-v4-explanation-audit.md`       | Archive    | `docs/audit/` | Explanationレイヤーの実装状態と境界を確認した監査                    | Reason、Explanation、Action、reason_factsの責務境界       |
| `recommendation-v4-reason-facts-e2e-audit.md`  | Archive    | `docs/audit/` | reason_factsのBackend E2Eと不足Testを確認した監査                    | Field Responsibility、Primary Reason、E2E契約             |
| `shrine-detail-policy-audit.md`                | Archive    | `docs/audit/` | Shrine Detailのカード接続候補と優先順位を整理した監査                | Context Reason、Personal Meaning、Saved Recordの責務      |

### Delete候補

A2にはDelete候補はない。

各文書には、当時の実装判断、責務分離、テスト範囲またはリリース条件に関する固有情報がある。

### 移管方針

Archive化前に、現在も有効な責務定義が現行正本文書へ反映済みかをカテゴリ別PRで確認する。

本監査PRでは、個別文書の移動、本文変更、責務移管は行わない。

## A3 Recommendation系

### 判定

| 文書                                         | Status候補    | 移動先候補        | 参照状況                      | 判断根拠                                                                                  |
| -------------------------------------------- | ------------- | ----------------- | ----------------------------- | ----------------------------------------------------------------------------------------- |
| `direction-ranking-design.md`                | 判断保留      | `docs/product/`   | 参照なし                      | Direction SignalとRanking Priorityを定義するが、現行Score実装との一致が未確認             |
| `recommendation-reason-v4-contract.md`       | Active        | `docs/product/`   | Copy Guidelineから参照        | Recommendation Reason v4の責務、入力、出力、Layer Boundaryを定義する契約文書              |
| `recommendation-score-v3-design.md`          | ActivReferenc | `docs/analytics/` | Score v3監査から参照          | Score v3のSignalと計算式の設計背景。実装Phaseとドラフトを含むため現行値は実装を正本とする |
| `recommendation-score-v3-roadmap.md`         | Archive       | `docs/audit/`     | Score v3監査から参照          | Roadmap、Active化、Dashboard、観測Snapshot、TODOが混在する時点記録                        |
| `recommendation-v4-consultation-brush-up.md` | Archive       | `docs/audit/`     | 参照なし                      | Consultation改善作業のScope・KPIを整理した短期計画                                        |
| `recommendation-v4-copy-guideline.md`        | ActivReferenc | `docs/knowledge/` | Action Suggestion監査から参照 | v4固有のCopy Ruleを持つが、Knowledge BaseのRecommendation Copy Guideと責務が重複する      |
| `recommendation-v4-interpreter-contract.md`  | Active        | `docs/product/`   | Copy Guidelineから参照        | Consultation InterpreterのField ContractとSource of Truthを定義                           |
| `recommendation-v5-design.md`                | Archive       | `docs/audit/`     | 参照なし                      | 未実装のv5設計と次PR候補を含む将来計画                                                    |

### 現行契約

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

| 文書                            | Status候補    | 移動先候補      | 参照状況                                            | 判断根拠                                                                             |
| ------------------------------- | ------------- | --------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `billing-attribution-design.md` | Archive       | `docs/audit/`   | 参照なし                                            | Card AnalyticsからCheckoutまでのAttribution課題、候補案、次PR、TODOを含む時点設計    |
| `billing-paywall.md`            | Active        | `docs/product/` | `pricing.md`、`premium-experience.md`から参照       | Billing Status、Paywall情報、Premium優先、Free制限、Server最終判定を定義する契約文書 |
| `monetization-flow-design.md`   | ActivReferenc | `docs/product/` | Phase7関連監査・Archive文書から参照                 | Premium提示タイミング、入口、CTA、Subscription Flowを補足する収益導線設計            |
| `premium-card-matrix.md`        | Archive       | `docs/audit/`   | 参照なし                                            | Access Level別Card表示設計を持つが、現在地、次の一手、Payload案、実装TODOを含む      |
| `premium-experience.md`         | Active        | `docs/product/` | Core、Meaning Layer、Pricing、Shrine Detailから参照 | Free / Premiumの体験差、表現、画面別境界を定義する現行正本候補                       |
| `premium-plan-design.md`        | ActivReferenc | `docs/product/` | Phase7関連文書から参照                              | Reflection、Timeline、History、Memory等を含むPremium価値の包括的な構想               |
| `premium-retention-strategy.md` | ActivReferenc | `docs/product/` | 参照なし                                            | 保存、履歴、比較を中心としたPremium継続価値とKPIの戦略補足                           |
| `pricing.md`                    | Active        | `docs/product/` | `shrine-detail-layer.md`から参照                    | 「何に対して支払うか」、Free / Premiumの価値境界、価格表現原則を管理する             |

### 正本の責務分離

Premium・Billing関連の現行文書は、以下の責務に分離する。

| 文書                          | 責務                                               |
| ----------------------------- | -------------------------------------------------- |
| `billing-paywall.md`          | 課金状態、利用可否、Paywall判定、Server責務        |
| `pricing.md`                  | 支払対象、Free / Premiumの価値境界、価格表現       |
| `premium-experience.md`       | Free / Premiumの体験差、画面別境界、利用可能な表現 |
| `monetization-flow-design.md` | Premium導線を提示する時点、文脈、CTA、復帰導線     |

`premium-plan-design.md`は将来構想を含むReference、`premium-retention-strategy.md`は継続価値の戦略補足として扱う。

### Archive

`billing-attribution-design.md`はAttribution実装前の設計・判断履歴としてArchiveにする。

`premium-card-matrix.md`はAccess
Level別UI設計の履歴として保存し、現在も有効な表示境界が`premium-experience.md`または実装へ反映済みかを別PRで確認する。

### Delete候補

A4にはDelete候補はない。

各文書は、課金判定、価値境界、収益導線、継続価値、表示制御またはAttributionに関する固有情報を持つ。

## A5 Journey・Shrine Detail・投稿系

### 判定

| 文書                                 | Status候補    | 移動先候補      | 参照状況                                            | 判断根拠                                                               |
| ------------------------------------ | ------------- | --------------- | --------------------------------------------------- | ---------------------------------------------------------------------- |
| `action_state_behavior_checklist.md` | Archive       | `docs/audit/`   | 参照なし                                            | 動作確認チェックリストであり、仕様契約ではない                         |
| `journey-timeline-api-plan.md`       | Archive       | `docs/audit/`   | 参照なし                                            | Journey Timeline API のPhase計画・Backend/Mobile変更候補を含む時点設計 |
| `journey-timeline-design.md`         | ActivReferenc | `docs/product/` | 参照なし                                            | Journey Timeline の設計思想・情報設計・Migration方針を整理した設計資料 |
| `reflection-timeline-design.md`      | Active        | `docs/product/` | Phase7関連文書から参照                              | Reflection Timeline の役割、UX、KPI、Premium接続を定義する現行設計     |
| `shrine-detail-layer.md`             | Active        | `docs/product/` | Pricing、Premium Experience、Architecture等から参照 | 神社詳細のPublic / Context / Personal Layerと責務境界を定義            |
| `shrine-detail-meaning-layer.md`     | ActivReferenc | `docs/product/` | 参照なし                                            | Shrine Detail のMeaning Layer設計補足ガイド                            |
| `shrine-detail-v3-design.md`         | Active        | `docs/product/` | Phase7 Roadmapから参照                              | Shrine Detail v3 のUX・Analytics・Premium接続を定義する正本候補        |
| `shrine-submission-flow.md`          | Active        | `docs/product/` | Architectureから参照                                | 神社投稿、duplicate_candidate契約、推薦利用方針を定義する現行仕様      |

### Delete候補

A5にはDelete候補はない。

Journey、Shrine Detail、投稿フローそれぞれに固有の責務を持ち、他文書からも参照されている。

### 現行契約

- `reflection-timeline-design.md`
- `shrine-detail-layer.md`
- `shrine-detail-v3-design.md`
- `shrine-submission-flow.md`

### ActivReferenc

- `journey-timeline-design.md`
- `shrine-detail-meaning-layer.md`

### Archive

- `action_state_behavior_checklist.md`
- `journey-timeline-api-plan.md`

## A6 Core / Knowledge

> 更新注記（2026-07-15）
>
> 本節は監査実施時点のInventory・参照状況・分類判断を記録している。
>
> その後の`docs/audit/recommendation-doc-consolidation-audit.md`において、
> `docs/knowledge/meaning-layer-spec.md`の本文を再確認した結果、見出し・論点一覧を除く独自の確定仕様が存在しないことを確認した。
>
> 同文書が扱っていた責務は、現在は以下を正本とする。
>
> - Meaning Layerの思想: `docs/core/meaning-layer.md`
> - Meaning Layerの接続仕様: `docs/core/meaning-layer-connection.md`
> - Meaning Translationの変換仕様: `docs/product/meaning-translation-mapping.md`
> - Recommendation Reasonの契約: `docs/core/recommendation-reason-contract.md`
>
> このため、`docs/knowledge/meaning-layer-spec.md`は後続監査で削除した。以下のInventory・観察記録は当時の監査証跡として保持するが、Active分類および現行契約候補は後続監査の判定を優先する。

### Inventory

#### docs/core（5ファイル）

| 文書                          | 見出し構造                                                                                                                                                                                      | Source of Truth表記                                    | 更新ルール表記                                                                 |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------ |
| `architecture.md`             | 目的 / 全体フロー / レイヤーと責務 / Consultation Interpretation / Meaning Translation / Recommendation / Score v3 / 画面責務 / データ責務 / 認証アーキテクチャ / 正本ドキュメント / 変更ルール | 「正本ドキュメント」節で各詳細仕様の委譲先を明示       | 「変更ルール」節あり。責務境界・全体依存関係が変わる場合のみ更新               |
| `meaning-layer.md`            | 概要 / 責務 / 神社とは何か / なぜ推薦するのか / AIは何を解釈しているのか / なぜ断定しないのか / 意味ある移動体験とは何か / 関連ドキュメント                                                     | 「関連ドキュメント」で詳細仕様の正本を列挙             | 明示的な更新ルール節なし（思想文書のため）                                     |
| `meaning-layer-connection.md` | 目的 / 全体フロー / 入力 / 出力 / Composerとの接続 / Recommendationとの接続 / Fallback / 責務境界 / 保存方針 / 関連ドキュメント                                                                 | 「関連ドキュメント」で接続仕様以外は各正本へ委譲と明記 | 「本ドキュメントは接続仕様のみを定義する」と範囲限定あり                       |
| `narrative-guideline.md`      | Purpose / Narrative Principles / Input / Output / Prohibited Expressions / Responsibility / Related Documents                                                                                   | 「Related Documents」で執筆原則のみの範囲限定          | 「本ドキュメントは...執筆原則のみを定義する」と明記                            |
| `roadmap.md`                  | 目的 / 現在地 / 開発原則 / Phase1〜8 / 現在の実装順序 / 文書管理ルール                                                                                                                          | なし（Roadmap自体が正本）                              | 「文書管理ルール」節あり。フェーズ・順序・ゴール・完了条件が変わる場合のみ更新 |

#### docs/knowledge（監査時点: 8ファイル、README含む）

| 文書                           | 見出し構造                                                                                                                                          | Source of Truth表記                                                                | 更新ルール表記                                                                                                                                                                           |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `README.md`                    | 目的 / ドキュメント構成 / 依存関係 / 更新ルール / 更新順序                                                                                          | 「LLMや実装担当者が変わってもKAMI MUSUBIらしい提案品質を維持するための正本」と明記 | 「更新ルール」「更新順序」節あり。上流→下流の更新順序（shrine-profile-spec→shrine-data-guide→meaning-layer-spec→recommendation-copy-guide→action-guide→reflection-guide→glossary）を規定 |
| `shrine-profile-spec.md`       | 結論(先出し) / 目的 / 知識モデル:7 Layer / 対象範囲 / データの生成・保存区分 / Profile v2項目 / 表示用項目 / 推薦用項目 / 修正優先順位 / 未確定事項 | 事実・実装事実・推測・仮説を区分して記載                                           | 明示的な更新ルール節なし。P0/P1/P2の修正優先順位あり                                                                                                                                     |
| `shrine-data-guide.md`         | 目的 / 入力原則 / 必須項目 / 記述例 / 禁止事項 / 品質確認 / 未確定事項                                                                              | 「今後の関連仕様」で前提とするKnowledge Base文書を列挙                             | 明示的な更新ルール節なし                                                                                                                                                                 |
| `meaning-layer-spec.md`        | 目的 / Meaning Layer全体像 / 事実から意味への変換 / 人生テーマ / 相談テーマ / 品質基準 / 未確定事項                                                 | なし                                                                               | なし                                                                                                                                                                                     |
| `recommendation-copy-guide.md` | 目的 / 推薦文の構造 / 事実 / 意味 / ユーザーとの接点 / 禁止表現 / 品質基準 / 未確定事項                                                             | なし                                                                               | なし                                                                                                                                                                                     |
| `action-guide.md`              | 目的 / 行動提案の原則 / 参拝前・参拝中・参拝後 / 禁止事項 / 品質基準 / 未確定事項                                                                   | なし                                                                               | なし                                                                                                                                                                                     |
| `reflection-guide.md`          | 目的 / 振り返りの原則 / 参拝前後の比較 / 感情の変化 / 次の一歩 / 禁止事項 / 品質基準 / 未確定事項                                                   | なし                                                                               | なし                                                                                                                                                                                     |
| `glossary.md`                  | 目的 / 用語一覧 / 意味レイヤ用語 / 推薦用語 / 行動用語 / 振り返り用語 / 命名規則                                                                    | 「各仕様書で利用する用語は、本書の定義を正本とする」と明記                         | 「新しい概念を追加する場合は、各仕様書へ追加する前に本書へ定義を追加する」と明記                                                                                                         |

**監査時点の観察**: `meaning-layer-spec.md` / `recommendation-copy-guide.md` / `action-guide.md` /
`reflection-guide.md`の4文書は見出しのみ、または本文が箇条書きレベルに留まり、
`shrine-profile-spec.md`や`shrine-data-guide.md`と比べて記述密度が薄かった。

後続の`recommendation-doc-consolidation-audit.md`では、このうち`meaning-layer-spec.md`に独自の確定仕様が存在しないと判断し、削除した。他の3文書は、それぞれコピー・Action・Reflectionの運用原則を持つためActiveを維持する。

### Reference Audit

#### README・architecture・product・audit文書からの参照

| 対象                                                                                                                                  | 参照元（抜粋）                                                                                                                                                                                                               | 状況                                                                |
| ------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `docs/core/architecture.md`                                                                                                           | `docs/README.md`、`docs/project-context.md`、`docs/AGENTS.md`、`docs/authentication-flow.md`、`docs/product/*`（7文書）、`docs/meaning-layer/*`（5文書）、`docs/mobile/*`（2文書）、`docs/phase7-ux-monetization-roadmap.md` | 最多参照。Core文書の中心                                            |
| `docs/core/meaning-layer.md`                                                                                                          | 同上系統16文書                                                                                                                                                                                                               | Meaning Layer思想の参照元として広く利用                             |
| `docs/core/meaning-layer-connection.md`                                                                                               | `project-context.md`、`meaning-layer/*`、`mobile/*`、`ui/concierge-result-wireframe.md`等9文書                                                                                                                               | 接続仕様として実装系文書から参照                                    |
| `docs/core/narrative-guideline.md`                                                                                                    | `project-context.md`、`README.md`、`product/action-suggestion-layer.md`（Archive）、`product/meaning-translation-mapping.md`、`product/visit-reflection-flow.md`                                                             | 表示文言原則として参照                                              |
| `docs/core/roadmap.md`                                                                                                                | `project-context.md`、`README.md`、`phase7-ux-monetization-roadmap.md`（Archive）、`phase5-behavior-measurement-plan.md`（Archive）                                                                                          | 現行文書からの参照はREADME・project-contextの2件のみ                |
| `docs/knowledge/README.md`                                                                                                            | `project-context.md`、`docs/README.md`                                                                                                                                                                                       | Knowledge Base入口として参照                                        |
| `docs/knowledge/recommendation-copy-guide.md`                                                                                         | `docs/audit/knowledge-base-consistency-audit.md`、本監査文書                                                                                                                                                                 | 監査文書からのみ参照                                                |
| `docs/knowledge/shrine-profile-spec.md`他6文書（shrine-data-guide / meaning-layer-spec / action-guide / reflection-guide / glossary） | `docs/audit/knowledge-base-consistency-audit.md`、およびKnowledge Base内の相互参照（README、各Guideの関連仕様節）                                                                                                            | root/product/mobile等の実装系文書からのファイルパス参照は確認できず |

**観察**:
`docs/knowledge`配下の個別ファイル（README以外）は、`docs/product/`や`docs/mobile/`等の実装系文書から直接ファイルパスで参照されることがほぼない。参照されているのは`docs/audit/knowledge-base-consistency-audit.md`（責務・用語監査）のみであり、Knowledge
Base自体がまだ実装ドキュメントの一次参照先として定着していない可能性がある。

#### 実装からの参照確認

コード内（`*.py` / `*.ts` /
`*.tsx`）に`docs/core`・`docs/knowledge`へのパス参照は確認できなかった（grep結果0件）。実装とドキュメントの対応は、`docs/audit/knowledge-base-consistency-audit.md`が現行DB・Service実装を突き合わせる形で個別に監査済み。

#### 古いファイル名への参照確認

- `docs/architecture.md` → `docs/core/architecture.md`、`docs/roadmap.md` →
  `docs/core/roadmap.md`への移動をgit履歴で確認（rename 100%）。
- `docs/shrine-detail-layer.md:110`が移動前の旧パス`docs/architecture.md`を参照したまま残っている（**参照切れ、要修正**）。
- `meaning-layer.md` / `meaning-layer-connection.md` /
  `narrative-guideline.md`は`docs/core/`への移動前から現ファイル名のため、旧パス参照は確認されなかった。

### Responsibility Audit

#### docs/core内の責務重複確認

`architecture.md`（全体構造）、`meaning-layer.md`（思想）、`meaning-layer-connection.md`（接続仕様）、`narrative-guideline.md`（文章原則）、`roadmap.md`（開発順序）は扱う抽象度・出力物が明確に異なり、重大な重複は確認されなかった。`architecture.md`と`meaning-layer-connection.md`はともにMeaning
Layerの入出力フローを図示するが、`architecture.md`は全体レイヤーの1セクションとして概要を示すに留め、詳細な接続仕様（Composer、Fallback等）は`meaning-layer-connection.md`へ委譲されており、責務分離は維持されている。

#### docs/knowledge内の責務重複確認

既存監査`docs/audit/knowledge-base-consistency-audit.md`の「4. 用語差分」「9. 重複責務」で以下が既に指摘済み。

- Recommendation / Recommendation Reason / Recommendation Readiness / Recommendation
  Readyの用語が、`glossary.md`・`shrine-profile-spec.md`・`recommendation-copy-guide.md`の間で表記・定義が不統一（P0）
- Consultation（相談解析）とConsultation Layer（User×Shrineの一致結果）が`shrine-profile-spec.md`内で混在（P0）
- `shrine-profile-spec.md`の7 LayerにRecommendation Layerが存在しない一方、`glossary.md` /
  `recommendation-copy-guide.md` / `action-guide.md` /
  `reflection-guide.md`はRecommendationをMeaningとActionの間の独立層として扱う（P0）

本監査ではこれらを追加で再検証せず、既存監査結果を正として引き継ぐ。

#### core / knowledge間の責務重複確認

| 観点                       | 結果                                                                                                                                                                                                                                                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Meaning Layerの扱い        | `core/meaning-layer.md`は思想・禁止事項、`core/meaning-layer-connection.md`はConsultation Interpretation・Composer・Recommendationとの接続仕様、`product/meaning-translation-mapping.md`は`history_theme`等の変換仕様を定義する。旧`knowledge/meaning-layer-spec.md`は独自仕様が存在しないため後続監査で削除した   |
| Stored/Derived/Runtime区分 | `core/architecture.md`の「Runtime Snapshot」節と`knowledge/shrine-profile-spec.md`の「データの生成・保存区分」節は同じ4区分（Stored/Derived/Runtime/Governance）を用いるが、`architecture.md`は対象項目の列挙に留め、区分の定義・境界ルールの詳細は`knowledge`側が正本という関係が保たれている                     |
| 用語定義                   | core側に用語集はなく、`knowledge/glossary.md`が唯一の用語正本。重複なし                                                                                                                                                                                                                                            |
| 表示文言原則               | `core/narrative-guideline.md`は表現の原則（可能性表現・断定禁止等）、`knowledge/recommendation-copy-guide.md`は推薦文特有の構造（Fact→Meaning→User Connection→Recommendationの順序、出典必須項目）を定義。両文書とも禁止表現（宗教的断定・心理的断定・効果保証）の記述内容が類似するが、相互参照が設定されていない |

**軽微な指摘**:
`narrative-guideline.md`と`recommendation-copy-guide.md`の禁止表現記述は内容が重複気味だが、責務の重複ではなく相互リンク欠落として扱う。

#### product文書との責務重複確認

| knowledge文書                  | 対応product文書                                                               | 関係                                                                                                                                                                                                                                            |
| ------------------------------ | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 旧`meaning-layer-spec.md`      | `product/meaning-translation-mapping.md` / `core/meaning-layer-connection.md` | 監査時点では抽象仕様と実装詳細の分離と評価したが、後続の本文再監査で旧文書に独自の確定仕様が存在しないことを確認した。Meaning Layerの接続責務は`core/meaning-layer-connection.md`、変換仕様は`product/meaning-translation-mapping.md`へ集約済み |
| `recommendation-copy-guide.md` | root `recommendation-reason-v4-contract.md`（A3で移動候補）                   | knowledge側は「推薦文の文章構造原則」、root側は「fact/interpretation/actionの実装関数対応（concierge_chat_ranking.py等）」という実装トレース。抽象度は異なるが、扱う分割（3層構造）が類似しており統合または相互参照の余地がある                 |

#### Recommendation文書との重複確認

`docs/core/recommendation-reason-contract.md`はRecommendation Reason生成の実装契約を定義し、
`docs/knowledge/recommendation-copy-guide.md`は文章生成原則を定義する。

両者は役割が異なる。

- `recommendation-copy-guide.md`
  - Fact → Meaning → User Connection → Recommendation の文章構造
  - 禁止表現
  - コピー品質

- `recommendation-reason-contract.md`
  - fact / interpretation / action
  - Runtime Contract
  - 保存・表示・互換性

両文書は上位（生成原則）と下位（実装契約）の関係であり、責務重複は確認されなかった。

一方で、

- Meaning
- Interpretation

など一部用語は完全一致していないため、今後は`docs/core/recommendation-reason-contract.md`を実装正本、
`docs/knowledge/recommendation-copy-guide.md`を文章正本として整合を維持する。

#### Action文書との重複確認

`knowledge/action-guide.md`（行動提案の生成原則・品質基準）と`product/action_suggestion_v4.md`（Status:Active、Input/Output
Contract）は責務が分離されている。

- `action-guide.md`:
  Stored/Derived/Runtimeで利用できる情報の分類、参拝前後のAction例、禁止事項（一般論のみ禁止・効果保証禁止等）
- `action_suggestion_v4.md`:
  primary_action/secondary_action/reflection_prompt/action_sourceのContract定義、Recommendation
  Ranking等を扱わない旨の責務境界

重大な重複は確認されなかった。`product/action-suggestion-layer.md`（Status:Archive）は初期設計であり、現行責務は`action_suggestion_v4.md`へ移行済みと明記されている。

#### Reflection文書との重複確認

`knowledge/reflection-guide.md`（振り返りの生成原則・品質基準）と`product/visit-reflection-flow.md`（Status:Active、Visit→Reflection体験・イベント・保存責務）も同様に分離されている。

- `reflection-guide.md`: 参拝前後比較・感情の変化・次の一歩という問いの構成原則、禁止事項（心理診断禁止・正解誘導禁止等）
- `visit-reflection-flow.md`:
  route_open→visit_done→reflection_prompt_view→reflection_saved→history_theme履歴→next_consultationという画面遷移・Analyticsイベント・保存責務

重大な重複は確認されなかった。

### Implementation Alignment

| 確認項目                         | 実装箇所                                                                                                                                                                                                                 | 整合状況                                                                                                                                                                                                                                                                                                                          |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| history_theme                    | `Shrine.history_theme`（`backend/temples/models.py`、CharField max_length=32、db_index）。Derivedとして事前生成値をDB保存                                                                                                | `knowledge/glossary.md`の定義（「神社の歴史や由緒から抽出した意味テーマ」）と一致。Derivedが「非保存」を意味しない点は本文からは読み取りにくく、`knowledge-base-consistency-audit.md`が既に指摘済み                                                                                                                               |
| reason_facts                     | `backend/temples/services/concierge_chat_ranking.py`の`_build_reason_facts`、`backend/temples/services/journey_timeline.py`                                                                                              | `shrine-profile-spec.md`が「reason_factsはhistory_theme, culture_translation, user_selected_tag, need_tag, goriyaku_tag, text_hint, elementのいずれか1つでも存在すれば非空になる」と実装事実として明記。実装ファイルの存在と一致確認済み                                                                                          |
| recommendation_reason_v4         | `backend/temples/services/recommendation_reason_v4.py`の`build_recommendation_reason_v4()`。fact/interpretation/action/used_fact/used_interpretation/used_action/qualityを生成                                           | root `recommendation-reason-v4-contract.md`の記述（fact/interpretation/actionへの分離）と実装が一致。`knowledge/recommendation-copy-guide.md`のFact→Meaning→User Connection→Recommendationという4分割とは命名が異なる（Meaningがinterpretationの一部に相当、User Connectionに明示的に対応する層がない）。**用語の不一致は要整理** |
| action_suggestion_v4             | `backend/temples/services/action_suggestion_builder.py`                                                                                                                                                                  | `product/action_suggestion_v4.md`のContract定義と実装ファイルが対応                                                                                                                                                                                                                                                               |
| consultation_axis                | `backend/temples/domain/consultation_axis.py`。`ConciergeThread.recommendations_v2`内へRuntime Snapshotとして保存（`concierge_chat.py`）                                                                                 | `knowledge-base-consistency-audit.md` 7.4節で「完全対応」と確認済み。本監査でも実装ファイルの存在を確認                                                                                                                                                                                                                           |
| matched_need_tags                | `backend/temples/services/concierge_chat_ranking.py`。`ConciergeThread.recommendations_v2`内へ保存                                                                                                                       | 同上。Runtime Snapshotとして実装済み                                                                                                                                                                                                                                                                                              |
| Stored/Derived/Runtime境界       | `Shrine`モデル（Stored: sajin, description, goriyaku, goriyaku_tags / Derived: history_theme）、`ConciergeThread.recommendations_v2`JSONField（Runtime: matched_need_tags, consultation_axis, reason_facts, evidence等） | `knowledge/shrine-profile-spec.md`の区分定義と概ね一致。ただし`deity`→`Shrine.sajin`、`shrine_history`→`Shrine.description`はいずれも自由記述TextFieldへの部分対応であり、概念項目と物理フィールドが完全一致していない（`knowledge-base-consistency-audit.md` 7.5節と同じ結論を本監査でも再確認）                                 |
| Recommendation Readiness実装状況 | 実装コード内に`recommendation_readiness` / `RecommendationReadiness` / `readiness_level`等の実装は確認できず（grep結果0件）。Coverage算出処理も未実装                                                                    | `knowledge/shrine-data-guide.md`および`shrine-profile-spec.md`は「Level0〜3」の段階定義を持つが、判定関数・DB保持は未実装。`knowledge-base-consistency-audit.md`が「文書定義のみ、P0」と分類した結論を本監査でも再確認。**文書は仕様として先行しているが実装が追いついていない**                                                  |

### Classification

#### Active確定

| 文書                                          | 理由                                                                                                      |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `docs/core/architecture.md`                   | 全体レイヤー構造・責務境界の正本として広範囲から参照され、変更ルールも明記                                |
| `docs/core/meaning-layer.md`                  | Meaning Layerの思想的正本として広範囲から参照                                                             |
| `docs/core/meaning-layer-connection.md`       | Meaning Layerの接続仕様の正本                                                                             |
| `docs/core/narrative-guideline.md`            | 表示文言の執筆原則の正本                                                                                  |
| `docs/core/roadmap.md`                        | 開発フェーズ・順序の正本                                                                                  |
| `docs/knowledge/README.md`                    | Knowledge Base全体の入口・更新順序の正本                                                                  |
| `docs/knowledge/shrine-profile-spec.md`       | 神社知識モデルの正本。事実/推測/仮説の区分が明示され監査可能性が高い                                      |
| `docs/knowledge/shrine-data-guide.md`         | 神社データ入力基準の正本                                                                                  |
| `docs/knowledge/recommendation-copy-guide.md` | 推薦文構造の正本                                                                                          |
| `docs/knowledge/action-guide.md`              | 行動提案生成原則の正本                                                                                    |
| `docs/knowledge/reflection-guide.md`          | 振り返り生成原則の正本                                                                                    |
| `docs/knowledge/glossary.md`                  | 用語定義の正本。他文書からの参照は少ないが、README更新順序・shrine-data-guideの関連仕様節で位置付けが明確 |

本監査時点では全12文書をActiveと判定した。

ただし、後続の`recommendation-doc-consolidation-audit.md`により、
`docs/knowledge/meaning-layer-spec.md`は削除へ更新された。現在のActive対象は12文書であり、本節の当初判定より1文書少ない。

#### Reference確定

> 後続監査では`meaning-layer-spec.md`をReferenceへ移さず削除した。独自情報が存在しないため、Referenceとして保持する必要もないと判断した。

#### 判断保留確定

該当なし。A1〜A5と異なり、docs/core・docs/knowledgeは全文書が現行の思想・責務・知識正本として機能しており、実装との対応も個別に監査済み（`knowledge-base-consistency-audit.md`）であるため判断を保留する文書はない。

#### 現行契約

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/narrative-guideline.md`
- `docs/core/roadmap.md`
- `docs/knowledge/README.md`
- `docs/knowledge/shrine-profile-spec.md`
- `docs/knowledge/shrine-data-guide.md`
- `docs/knowledge/recommendation-copy-guide.md`
- `docs/knowledge/action-guide.md`
- `docs/knowledge/reflection-guide.md`
- `docs/knowledge/glossary.md`

### A7への引き継ぎ事項

- `docs/shrine-detail-layer.md:110`の`docs/architecture.md`参照切れの修正
- `docs/knowledge/recommendation-copy-guide.md`と`docs/core/recommendation-reason-contract.md`の用語対応を維持する（Fact/Meaning/User
  Connection vs Fact/Interpretation/Action）の整理
- `narrative-guideline.md`と`recommendation-copy-guide.md`の禁止表現記述の相互参照欠落
- Recommendation
  Readiness/Coverageの未実装状態（`knowledge-base-consistency-audit.md`のP0/P1事項）は実装フェーズへ引き継ぎ、文書分類には影響しない

### 結論

Coreは「思想・責務・依存関係」の正本、Knowledgeは「知識・コピー・データ仕様」の正本として責務分離されている。

重大な責務重複は確認されなかったが、以下の軽微な課題を確認した。

1. `docs/shrine-detail-layer.md`に移動前の旧パス`docs/architecture.md`への参照切れが残っている
2. `knowledge/recommendation-copy-guide.md`とroot
   `recommendation-reason-v4-contract.md`の間で概念の3分割名称（Meaning/User Connection vs
   Interpretation/Action）が不一致
3. `docs/knowledge`配下の個別文書（README以外）は、`docs/product/`等の実装系文書からファイルパスで直接参照されることがほぼなく、参照されているのは`docs/audit/knowledge-base-consistency-audit.md`のみ
4. Recommendation Readiness/Coverageは文書定義のみで実装が未着手（既存監査で確認済みの結論を本監査でも再確認）

これらは文書分類（Active/Reference/Archive）には影響しないため、A6の分類結果は「全12文書をActiveとする」で確定する。個別の整理は上記4点をA7以降または実装監査へ引き継ぐ。

## A7 Product

### Inventory

`docs/product`配下は21ファイル（README.md、product-document-audit.md含む）。

| 文書                                                                                                                                                                                                                                                    | Status表記       | 見出し構造（抜粋）                                                                                                                                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `README.md`                                                                                                                                                                                                                                             | なし（入口文書） | 目的 / 読む順番 / 正本 / Reference / Archive / 役割境界 / 更新ルール                                                                                                                                                |
| `concierge-first-final-spec.md`                                                                                                                                                                                                                         | Active           | 目的 / MVP結論 / HomeHero責務 / ConciergeEntry責務 / Filter責務 / Need Mode / Compat Mode境界 / Recommendation Score v2入力一覧                                                                                     |
| `concierge-modes.md`                                                                                                                                                                                                                                    | Active           | 目的 / Mode一覧 / 基本原則 / Mode責務(5Mode) / 責務境界 / 関連ドキュメント / 更新ルール                                                                                                                             |
| `consultation-theme-taxonomy.md`                                                                                                                                                                                                                        | Active           | 目的 / 基本原則 / 相談テーマ(8種) / レイヤー構成 / consultation_axis対応 / need_tags対応 / history_theme対応 / 自由入力との関係 / Home Hero・Concierge Entryでの利用                                                |
| `history-theme-taxonomy.md`                                                                                                                                                                                                                             | Active           | 目的 / 基本原則 / カテゴリ一覧(7種：守り/静寂/再出発/復興/勝負/学び/縁、各定義・相談例・行動テーマ・関連ご利益)                                                                                                     |
| `meaning-translation-mapping.md`                                                                                                                                                                                                                        | Active           | 目的 / 全体フロー / 基本原則 / 入力の優先順位 / 相談テーマ→推薦入力 / 相談状態→history_theme / ご利益→history_theme / 神社へのhistory_theme付与 / Action/Visit/Reflection/Recommendationとの接続 / Runtime Snapshot |
| `visit-reflection-flow.md`                                                                                                                                                                                                                              | Active           | 目的 / 基本原則 / 体験フロー / visit_done / reflection_prompt_view / reflection_saved（各Event名・Payload定義）                                                                                                     |
| `action_suggestion_v4.md`                                                                                                                                                                                                                               | Active           | 目的 / 全体構造 / 責務(扱うもの/扱わないもの) / Input・Output Contract / primary_action / secondary_action / reflection_prompt / action_source / action_type / fallback / 文言ルール                                |
| `home-hero-final-wireframe.md` / `concierge-entry-final-wireframe.md` / `concierge-filter-area.md` / `need-mode-ui-flow.md` / `compat-mode-ui-flow.md` / `visit-style-taxonomy.md` / `reflection-funnel-dashboard.md` / `explore-integration-design.md` | Reference        | 各UI・補助条件・分析設計を扱う。全8文書とも冒頭に「現行仕様の判断には正本を参照」の範囲限定あり                                                                                                                     |
| `concierge-first.md` / `concierge-first-wireframe.md` / `action-suggestion-layer.md` / `product-doc-consolidation.md`                                                                                                                                   | Archive          | 全4文書とも冒頭に「Status: Archive」「現行の判断には使用しない」「現在の正本」の明記あり                                                                                                                            |
| `product-document-audit.md`                                                                                                                                                                                                                             | なし（監査文書） | 目的 / 監査サマリー / 推奨する正本構成 / ファイル別分類 / 統合済み文書 / 整理時の注意 / 更新ルール                                                                                                                  |

**観察**:
`docs/product`は`docs/core`・`docs/knowledge`と異なり、Archive文書自身に「Archive理由」「現在の正本」を明記する自己参照構造が徹底されている。個別ファイルの`Status`表記と`README.md`の正本/Reference/Archive分類、および既存`product-document-audit.md`の4分類はすべて一致しており、内部矛盾は確認されなかった。

### Reference Audit

#### READMEからの参照確認

`docs/product/README.md`は21ファイル中20ファイル（自身を除く全ファイル）を「正本」「Reference」「Archive」いずれかの表に列挙しており、抜け漏れは確認されなかった。

#### docs/coreからの参照確認

`docs/core/architecture.md`の「正本ドキュメント」節（314-325行目）は、以下のように`docs/product`へ責務を委譲している。

```text
- Concierge First：docs/product/concierge-first.md
- Concierge Modes：docs/product/concierge-modes.md
- Explore：docs/product/explore-integration-design.md
```

`docs/core/narrative-guideline.md`（132-133行目）・`docs/core/meaning-layer.md`（225-226行目）・`docs/core/meaning-layer-connection.md`（180-181行目）の関連ドキュメント節も同様に、`concierge-first.md`と`concierge-modes.md`の2ファイルのみを参照している。

**重大な指摘（現行正本と不一致な旧正本参照）**:
`concierge-first.md`は本監査でArchive確定（現行正本は`concierge-first-final-spec.md`）だが、`docs/core`配下の4文書すべてが現行正本ではなくArchive文書を「Concierge
First」の委譲先として参照している。`docs/audit/knowledge-base-refactoring.md:210`は「`docs/product/`配下を`concierge-first.md`でgrepし、残存する言及はREADME.md・product-document-audit.mdのArchive分類表内の正当な記載のみ」と結論しているが、この確認は`docs/product/`配下限定であり、`docs/core`配下と後述のroot
`README.md`は対象外だった。

なお、`consultation-theme-taxonomy.md` / `history-theme-taxonomy.md` / `meaning-translation-mapping.md` /
`visit-reflection-flow.md` /
`action_suggestion_v4.md`という現行Active5文書は、`docs/core`配下のどの文書からも直接参照されていない（`docs/core/architecture.md`は個別文書ではなく`docs/product/`ディレクトリ単位の委譲に留まる）。

#### docs/knowledgeからの参照確認

`docs/knowledge`配下から`docs/product/`へのファイルパス参照は確認できなかった（grep結果0件）。`docs/knowledge/shrine-profile-spec.md`の7行目・77行目に`action_suggestion_v4`という語の言及はあるが、ファイルパス参照ではない。

#### docs/product相互参照確認

正本7文書・Reference8文書間の相互参照は概ね一貫しており、Referenceの「関連ドキュメント」節は対応する正本を指す構成になっている（例：`need-mode-ui-flow.md`→`concierge-modes.md`、`reflection-funnel-dashboard.md`→`visit-reflection-flow.md`）。Archive4文書も、全文書が現行正本への「現在の正本」節を持つ。

#### 古い文書参照確認

過去に`meaning-translation-mapping.md`へ統合されて削除された5文書（`theme-to-recommendation-input-mapping.md`等）および`shrine-classification-policy.md`、`home-to-concierge-flow.md`への参照は、`product-document-audit.md`内の履歴記録を除き確認されなかった（参照切れなし）。

**重大な指摘（root
README.mdの旧正本参照）**: リポジトリルートの`README.md`は以下3箇所でArchive文書`concierge-first.md`をプロダクト導線の説明として直接参照している。

- `README.md:5`「詳細は docs/product/concierge-first.md を参照してください」
- `README.md:26`「詳細仕様は `docs/product/concierge-first.md` を参照してください」
- `README.md:364`「**Concierge First**: docs/product/concierge-first.md」

いずれも現行正本`concierge-first-final-spec.md`ではなくArchive文書を指しており、リポジトリの入口文書として参照先の修正が必要である。

### Responsibility Audit

#### Product内の責務重複確認

正本7文書は`README.md`の読む順番どおり抽象度が積み上がる構成（Concierge
First全体仕様→Mode責務→相談テーマ分類→history_theme分類→変換仕様→参拝後導線→Action契約）になっており、重大な責務重複は確認されなかった。`concierge-first-final-spec.md`と`concierge-modes.md`はいずれもNeed
Mode/Compat
Modeの境界に触れるが、`concierge-first-final-spec.md`は「MVPとしてどう配置するか」、`concierge-modes.md`は「Modeの責務定義そのもの」という関係で、後者が正本という位置付けが明記されている（`concierge-modes.md`68-75行目の責務境界表）。

#### Coreとの責務境界確認

`docs/core/architecture.md`は全体レイヤー構造、`docs/product/*`は画面・Mode・分類体系・変換仕様という実装レベルの詳細を担い、階層関係自体は維持されている。ただし前述のとおり、`docs/core`側の委譲先ファイルパスが現行正本ではなくArchive文書（`concierge-first.md`）を指しており、責務境界の記述と実際の正本構成が一致していない。

#### Knowledgeとの責務境界確認

Meaning Layer関連の現行責務は、以下へ分離されている。

- `docs/core/meaning-layer.md`
  - Meaning Layerの思想・非断定方針
- `docs/core/meaning-layer-connection.md`
  - Consultation Interpretation、Meaning Translation、Composer、Recommendation間の接続仕様
- `docs/product/meaning-translation-mapping.md`
  - `history_theme`、Action、Reflectionへの変換・接続仕様
- `docs/core/recommendation-reason-contract.md`
  - Fact / Interpretation / Action、保存、表示、互換責務

旧`docs/knowledge/meaning-layer-spec.md`は、後続監査で独自の確定仕様が存在しないと判断し削除した。したがって、KnowledgeからProductへ委譲する旧階層ではなく、Coreが思想・接続・Recommendation
Reason契約を持ち、Productが具体的な変換仕様を持つ構成を現行正本とする。
`meaning-translation-mapping.md`側が「`history_theme`のカテゴリ名称と定義は`history-theme-taxonomy.md`を正本とする」とさらに委譲しており、knowledge→product→productという階層的な分離が維持されている。

`action-guide.md`（knowledge、行動提案の生成原則）と`action_suggestion_v4.md`（product、Input/Output
Contract）、`reflection-guide.md`（knowledge、振り返りの生成原則）と`visit-reflection-flow.md`（product、画面遷移・Event・保存責務）もA6と同様、原則と実装契約という関係で重複は確認されなかった。

#### 実装契約との責務境界確認

`action_suggestion_v4.md`・`meaning-translation-mapping.md`・`visit-reflection-flow.md`はいずれもInput/Output・Event名・Payloadを明示するContract文書であり、`docs/audit/visit-reflection-implementation-consistency.md`が実装との一致・不一致を既に個別監査済み。本監査ではこの既存監査結果を正として引き継ぎ、再検証はしない。

### Implementation Alignment

| 文書                             | 実装箇所                                                                                                                           | 整合状況                                                                                                                                                                                                                                    |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `action_suggestion_v4.md`        | `backend/temples/services/action_suggestion_builder.py`                                                                            | `primary_action` / `secondary_action` / `reflection_prompt` / `action_source` / `action_type`のフィールド構成が実装と一致                                                                                                                   |
| `history-theme-taxonomy.md`      | `backend/temples/services/action_suggestions.py`の`HISTORY_THEME_ACTION_SUGGESTIONS`                                               | 7カテゴリ（守り/静寂/再出発/復興/勝負/学び/縁）が完全一致                                                                                                                                                                                   |
| `consultation-theme-taxonomy.md` | `backend/temples/domain/consultation_axis.py`（`theme_key`定義）、`apps/web/src/app/concierge/ConciergeClientFull.tsx`（表示文言） | `work`等の`theme_key`と表示文言が実装と一致                                                                                                                                                                                                 |
| `visit-reflection-flow.md`       | `apps/web/src/lib/analytics/searchEvents.ts`                                                                                       | `visit_done` / `reflection_prompt_view` / `reflection_saved`のEvent名は一致するが、Payloadフィールド構成・`promptType`の値体系は`docs/audit/visit-reflection-implementation-consistency.md`が既に不一致を確認済み（本監査では再検証しない） |
| `concierge-modes.md`             | `apps/web/src/lib/concierge/pickModeFromThread.ts`                                                                                 | Need Mode / Compat Modeの2Modeのみ実装されている。Route Mode / Theme Mode / Shrine Search Modeの3Modeは実装コード内に該当ロジックが確認できなかった（grep結果0件）                                                                          |

**観察**:
`concierge-modes.md`は5Modeを責務として定義するが、実装（`pickModeFromThread.ts`）が扱うのはNeed/Compatの2Modeのみ。`explore-integration-design.md`（Reference）が`/shrines`・`/map`という別導線としてRoute/Theme/Shrine
Search相当の探索機能に触れているが、Mode名としての実装対応はない。`concierge-modes.md`自身が「Mode は推薦アルゴリズムではなく入力文脈を決定する」という責務定義文書であるため、この差分は文書分類（Active/Reference/Archive）には影響しない。ただし実装が追いついていない3Modeの扱いはA8への引き継ぎ事項とする。

### Classification

#### Active確定

| 文書                                          | 理由                                                                       |
| --------------------------------------------- | -------------------------------------------------------------------------- |
| `docs/product/concierge-first-final-spec.md`  | Concierge First全体仕様の正本。Status表記・README分類・相互参照が一致      |
| `docs/product/concierge-modes.md`             | Mode責務の正本。`docs/core`からも参照される                                |
| `docs/product/consultation-theme-taxonomy.md` | 相談テーマ分類の正本。実装の`theme_key`と一致確認済み                      |
| `docs/product/history-theme-taxonomy.md`      | `history_theme`カテゴリ定義の正本。実装と完全一致確認済み                  |
| `docs/product/meaning-translation-mapping.md` | 相談・ご利益・神社・行動をhistory_themeへ接続する変換正本                  |
| `docs/product/visit-reflection-flow.md`       | 参拝後導線の正本。Event名は実装一致、Payload不一致は既存監査へ引き継ぎ済み |
| `docs/product/action_suggestion_v4.md`        | Action Suggestion Contractの正本。実装と一致確認済み                       |

全7文書をActiveと確定する。

#### 後続監査による分類更新

`docs/knowledge/meaning-layer-spec.md`は、本監査時点ではActiveとしたが、
`docs/audit/recommendation-doc-consolidation-audit.md`で本文を再確認した結果、独自の確定仕様が存在しないため削除した。

現在のMeaning Layer関連正本は以下とする。

- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/core/recommendation-reason-contract.md`

#### Reference確定

| 文書                                              | 理由                                   |
| ------------------------------------------------- | -------------------------------------- |
| `docs/product/home-hero-final-wireframe.md`       | Home Hero UI詳細。体験判断は正本へ従属 |
| `docs/product/concierge-entry-final-wireframe.md` | Concierge Entry UI詳細                 |
| `docs/product/concierge-filter-area.md`           | Filter UI詳細                          |
| `docs/product/need-mode-ui-flow.md`               | Need Mode UI導線の補足                 |
| `docs/product/compat-mode-ui-flow.md`             | Compat Mode UI導線の補足               |
| `docs/product/visit-style-taxonomy.md`            | 参拝スタイル補助条件の分類             |
| `docs/product/reflection-funnel-dashboard.md`     | Reflection KPI・分析設計               |
| `docs/product/explore-integration-design.md`      | Explore体験の補足設計                  |

全8文書をReferenceと確定する。

#### Archive確定

| 文書                                        | 理由                                                                                                                                                       |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/product/concierge-first.md`           | 初期設計。現行正本は`concierge-first-final-spec.md`。ただし`docs/core`4文書とroot `README.md`3箇所が誤ってこれを現行正本として参照しており、参照修正が必要 |
| `docs/product/concierge-first-wireframe.md` | 初期ワイヤーフレーム検討記録。参照元はREADME・product-document-audit.mdのみ                                                                                |
| `docs/product/action-suggestion-layer.md`   | 初期設計。責務は`action_suggestion_v4.md`等へ完全移行済みと自己申告                                                                                        |
| `docs/product/product-doc-consolidation.md` | Google Docs統合作業の履歴記録                                                                                                                              |

全4文書をArchiveと確定する。

#### Delete候補

現時点でのDelete確定はなし。

`action-suggestion-layer.md`は「Archive理由」節で旧責務の移行先をすべて明示しており、内容面での独自情報は薄い。`product-doc-consolidation.md`も統合作業完了後の履歴メモであり、実務上の再参照価値は低い。この2文書は他のArchive2文書（`concierge-first.md`・`concierge-first-wireframe.md`が持つ「初期コンセプト・責務整理の設計思想」ほどの独自性を持たないため、**Delete検討対象（A8で最終判断）**として提示する。ただし最終的な削除可否はユーザー確認後に確定する。

#### 判断保留確定

該当なし。全21文書（README.md・product-document-audit.mdの2管理文書を含む）の分類はA7で確定する。

### A8への引き継ぎ事項

- root `README.md`（3箇所）および`docs/core`4文書（`architecture.md` / `narrative-guideline.md` / `meaning-layer.md` /
  `meaning-layer-connection.md`）が、Archive文書`docs/product/concierge-first.md`を現行正本として参照している旧正本参照の修正
- `concierge-modes.md`が定義する5Modeのうち、Route Mode / Theme Mode / Shrine Search
  Modeの3Modeが実装未着手（Need/Compatの2Modeのみ実装）。実装フェーズへ引き継ぐか、文書側に実装状況の注記を追加するかの判断
- Delete候補として提示した`action-suggestion-layer.md`・`product-doc-consolidation.md`の削除可否のユーザー判断
- `visit-reflection-flow.md`のPayload・`promptType`不一致（`docs/audit/visit-reflection-implementation-consistency.md`で既確認）は実装または文書のどちらに寄せるかの設計判断が未決のまま

### 結論

`docs/product`は21文書中、既存の`README.md`・`product-document-audit.md`による4分類（正本7・Reference8・Archive4・管理2）と、本監査の独立した参照・責務・実装整合確認の結果が完全に一致した。ファイル単位の自己申告（Status表記）と一覧文書の分類に矛盾はない。

一方で、`docs/product`外部から現行正本と不一致な旧正本参照が2系統見つかった。

1. root `README.md`（3箇所）がArchive文書`concierge-first.md`を現行正本として参照している
2. `docs/core`4文書の「正本ドキュメント」委譲先も同様にArchive文書を指している

これらは`docs/product`内部の分類には影響しないが、リポジトリ入口としての参照整合性に関わるため、A8以降での修正を推奨する。Delete候補として`action-suggestion-layer.md`・`product-doc-consolidation.md`の2文書を提示するが、最終判断はユーザー確認後に確定する。

### A8以降の進捗

参照切れ2件（root
`README.md`の3箇所、`docs/core`4文書）は`docs/audit/archive-final-classification.md`（A8）で修正済み。root直下Archive21ファイルの物理移動・Delete候補3件の最終確認・実行計画は同文書を参照する。
