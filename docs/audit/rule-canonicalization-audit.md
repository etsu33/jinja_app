# KAMI MUSUBI Rule Canonicalization Audit — Phase 1

> **Status: `Audit / Historical`（read-only監査記録。Current Source of Truthではない）**
>
> 本書は`develop`時点のCurrent Source of Truthを確定し、Fixed Rules候補抽出の入力となる
> 現行ルール一覧を作るためのPhase 1監査記録である。
>
> 本書はルール変更・文書修正・実装変更・分類変更を一切行っていない。既存正本文書、
> コード、設定、DBのいずれも変更していない。Fixed Rulesは本Phaseでは確定しない。
>
> 本書自身は`docs/audit/`配下の文書であり、`docs/audit/README.md`の定めるとおり
> 現在仕様の正本ではない。現在仕様は本書A章が列挙するActive正本を参照する。

---

## 0. 監査条件

| 項目 | 値 |
| --- | --- |
| 対象branch | `develop` |
| 対象commit | `3d43cd9fed00e640c1ea261c5ddba4b6fc8423ec`（`fix(storage): DB row削除時にStorage実ファイルを孤児化させない (#2829)`） |
| 監査日 | 2026-09-14 |
| 監査種別 | read-only（文書・実装の参照のみ） |
| 対象領域 | `docs/core/` `docs/product/` `docs/knowledge/` `docs/analytics/` `docs/infra/` `docs/ci/` `docs/ops/` `docs/design/`、および`docs/README.md`がCurrent Source of Truthとして参照する領域 |

### Authority判定手順（本書が適用した順序）

1. 各Domain READMEのActive / 正本分類を最優先のAuthority Sourceとする
2. Domain READMEが存在しない領域（`infra` `ci` `ops` `design`）は、`docs/README.md`からの参照と
   文書自身のStatus headerを併用する
3. Reference / Archiveは現行ルール抽出対象外とする
4. `docs/audit/*`は原則として現在仕様の正本として扱わない
5. Domain READMEに掲載がなくStatus headerのみを持つ文書は、**推測でActiveへ昇格させない**。
   H章（UNRESOLVED）へ記録する
6. 文書・実装・テストが矛盾する場合は解決せずG章（CONFLICT）へ記録する

### 母数

| 領域 | `.md`件数 | Domain README |
| --- | ---: | --- |
| `docs/core/` | 16 | あり（`docs/core/README.md`、Status: Active） |
| `docs/product/` | 46 | あり（`docs/product/README.md`、Status: Active） |
| `docs/knowledge/` | 14 | あり（`docs/knowledge/README.md`、Status header無し） |
| `docs/analytics/` | 42 | あり（`docs/analytics/README.md`、Status: Active） |
| `docs/infra/` | 4 | **なし** |
| `docs/ci/` | 1 | **なし** |
| `docs/ops/` | 5 | **なし** |
| `docs/design/` | 2 | **なし** |
| `docs/audit/` | 394 | あり（`docs/audit/README.md`、Status: Active（Navigation Only）） |

---

## A. Current Source of Truth Inventory

Domain READMEがActive / 正本として明示した文書のみを掲載する。

### A-1. Core（Authority Source: `docs/core/README.md` §Active）

| path | domain | status | responsibility | authority source |
| --- | --- | --- | --- | --- |
| `docs/core/README.md` | core | Active | Core文書の入口、Active / Reference分類、責務および委譲関係の管理 | 自己宣言（Status: Active）+ `docs/README.md`が入口として参照 |
| `docs/core/architecture.md` | core | Active | システム全体構造、レイヤー責務、依存関係、詳細正本への委譲 | `docs/core/README.md:52`近傍 §Active/全体構造 |
| `docs/core/desktop-development-contract.md` | core | **Status header無し** | active local Repository、local DB、再生成経路、開発環境の正本契約 | `docs/core/README.md` §Active/全体構造（README分類のみが根拠） |
| `docs/core/roadmap.md` | core | Active | 開発フェーズ、実装順序、ゴールおよび完了条件 | `docs/core/README.md` §Active/全体構造 |
| `docs/core/authentication-flow.md` | core | Active | Web認証アーキテクチャ、Frontend・BFF・Backend責務、JWT・Cookie方針 | `docs/core/README.md` §Active/認証 |
| `docs/core/runtime-security-baseline.md` | core | Active | 現在有効なruntime/security contract、trust boundary、logging / public response / CI security方針 | `docs/core/README.md` §Active/Security |
| `docs/core/concierge-spec.md` | core | Active | Concierge入力、LLM利用、API基本契約、運用上の保護条件 | `docs/core/README.md` §Active/Concierge |
| `docs/core/meaning-layer.md` | core | Active | Meaning Layerの思想、目的、非断定原則 | `docs/core/README.md` §Active/Meaning |
| `docs/core/meaning-layer-connection.md` | core | Active | Meaning LayerとInterpretation / Translation / Composer / Recommendationの接続責務 | `docs/core/README.md` §Active/Meaning |
| `docs/core/narrative-guideline.md` | core | Active | 全Narrative共通の非断定、可能性表現、自律尊重、行動接続原則 | `docs/core/README.md` §Active/Meaning |
| `docs/core/recommendation-architecture.md` | core | Active | Recommendation End-to-Endフロー、各段階の責務・正本データ・引き渡し契約 | `docs/core/README.md` §Active/Recommendation |
| `docs/core/recommendation-readiness.md` | core | Active | 神社Knowledge Coverage / Verification / UsabilityのGovernance観測契約 | `docs/core/README.md` §Active/Recommendation |
| `docs/core/recommendation-reason-contract.md` | core | Active | Recommendation ReasonのInput / Output / 保存 / 表示 / 互換責務 | `docs/core/README.md` §Active/Recommendation |
| `docs/core/openapi-contract-governance.md` | core | Active | API実装上の正本、OpenAPI関連ファイル分類、schema生成経路、CI検証責務 | `docs/core/README.md` §Active/API契約 |

### A-2. Product（Authority Source: `docs/product/README.md` §正本）

| path | domain | status | responsibility | authority source |
| --- | --- | --- | --- | --- |
| `docs/product/README.md` | product | Active | `docs/product`配下の文書構成、分類、読む順番の管理 | 自己宣言（Status: Active） |
| `docs/product/kami-musubi-experience-design.md` | product | Active | 相談・推薦・参拝・振り返りを一本の体験として接続する最上位体験設計 | `docs/product/README.md` §正本/全体体験 |
| `docs/product/mobile-user-flow.md` | product | Active | Mobile／Expo Webの主導線・サブ導線・共通合流地点・地図の段階公開方針 | `docs/product/README.md` §正本/全体体験 |
| `docs/product/concierge-first-final-spec.md` | product | Active | Concierge First全体仕様（HomeHero / ConciergeEntry / Filter / Mode責務） | `docs/product/README.md` §正本/Concierge・Recommendation |
| `docs/product/concierge-modes.md` | product | Active | Need Mode / Compat Mode / Route Mode / Theme Mode / Shrine Search Modeの責務 | 同上 |
| `docs/product/consultation-theme-taxonomy.md` | product | Active | 相談テーマの分類・表示文言・内部キー・各レイヤー対応 | 同上 |
| `docs/product/history-theme-taxonomy.md` | product | Active | `history_theme`のカテゴリ定義 | 同上 |
| `docs/product/meaning-translation-mapping.md` | product | Active | 相談・ご利益・神社・行動を`history_theme`へ接続する変換仕様 | 同上 |
| `docs/product/recommendation-v4-interpreter-contract.md` | product | Active | Consultation InterpreterのInput / Output契約（9Field の意味責務） | 同上 |
| `docs/product/action_suggestion_v4.md` | product | Active | Action Suggestion v4の入出力項目の意味、生成原則、後続体験との接続 | 同上 |
| `docs/product/compass-product-contract.md` | product | Active | Visit CompassのProduct Promise、Authority境界、Signal-to-Explanation Rule | `docs/product/README.md` §正本/Compass |
| `docs/product/compass-mvp-runtime-contract.md` | product | Active | Visit Compass MVPの最小Runtime入出力契約（time / profile / origin / purpose / direction） | 同上 |
| `docs/product/compass-product-logic-evaluation-framework.md` | product | Active（Evaluation Framework only） | Direction Logic選択肢の評価軸・判定方法・用語の固定（採否は決定しない） | 同上 |
| `docs/product/shrine-detail-layer.md` | product | Active | Shrine DetailのPublic / Context / Personal Layer契約 | `docs/product/README.md` §正本/神社詳細・参拝・記録 |
| `docs/product/shrine-detail-v3-design.md` | product | Active | Shrine Detail v3のUX・Analytics・Premium接続設計 | 同上 |
| `docs/product/shrine-submission-flow.md` | product | Active | 神社追加、重複候補、投稿後導線の現行仕様 | 同上 |
| `docs/product/visit-reflection-flow.md` | product | Active | 参拝から振り返りまでの体験・保存・イベント契約 | 同上 |
| `docs/product/journey-timeline-design.md` | product | Active | 相談・提案・参拝・振り返りを時系列で接続する現行体験設計 | 同上（※`docs/README.md`はReference扱い。G-2参照） |
| `docs/product/premium-experience.md` | product | Active | Free / Premiumの体験価値、画面別体験差、Premium対象、価格表現の原則 | `docs/product/README.md` §正本/Premium・Billing |
| `docs/product/billing-paywall.md` | product | Active | Billing状態、Free制限、利用可否、Paywall表示の判定原則 | 同上 |

### A-3. Knowledge（Authority Source: `docs/knowledge/README.md` §正本）

| path | domain | status | responsibility | authority source |
| --- | --- | --- | --- | --- |
| `docs/knowledge/README.md` | knowledge | **Status header無し** | Knowledge Baseの入口、正本 / Reference分類、更新順序の管理 | `docs/README.md`および`docs/core/README.md` §関連ドキュメントからの参照 |
| `docs/knowledge/shrine-profile-spec.md` | knowledge | **Status header無し** | 神社知識モデルと推薦可能品質の定義（7層モデル） | `docs/knowledge/README.md` §正本 |
| `docs/knowledge/shrine-knowledge-contract.md` | knowledge | Active | Knowledge値の意味、出典、確認状態、信頼度、Fact利用条件、AI生成値の制約 | `docs/knowledge/README.md` §正本 |
| `docs/knowledge/shrine-data-guide.md` | knowledge | **Status header無し** | 神社データの入力・出典・品質基準 | `docs/knowledge/README.md` §正本 |
| `docs/knowledge/shrine-position-contract.md` | knowledge | **Status header無し** | `Shrine.latitude` / `longitude`のVisitor / Navigation Anchor採用、Source要件、HOLD / PASS判定 | `docs/knowledge/README.md` §正本 |
| `docs/knowledge/recommendation-copy-guide.md` | knowledge | **Status header無し** | 推薦理由の共通文章構造 | `docs/knowledge/README.md` §正本 |
| `docs/knowledge/action-guide.md` | knowledge | **Status header無し** | 行動提案の生成原則 | `docs/knowledge/README.md` §正本 |
| `docs/knowledge/reflection-guide.md` | knowledge | **Status header無し** | 振り返りの問いと接続方法 | `docs/knowledge/README.md` §正本 |
| `docs/knowledge/glossary.md` | knowledge | **Status header無し** | 共通用語と命名基準 | `docs/knowledge/README.md` §正本 |

> Status header無しの7文書について、`docs/core/recommendation-architecture.md:71`は
> `shrine-profile-spec.md` / `shrine-data-guide.md` / `recommendation-copy-guide.md`を
> 「Active相当として扱うが、Statusヘッダの追加自体は変更範囲外」と明記している。
> 本書もDomain READMEの正本分類のみを根拠として採用し、Status header追加は行わない。

### A-4. Analytics（Authority Source: `docs/analytics/README.md` §Active）

| path | domain | status | responsibility | authority source |
| --- | --- | --- | --- | --- |
| `docs/analytics/README.md` | analytics | Active | `docs/analytics`配下の文書構成、分類、読む順番の管理 | 自己宣言（Status: Active） |
| `docs/analytics/direction-events.md` | analytics | Active / Contract | Web／Mobile共通の方位分析Event名・Payload・禁止属性契約 | `docs/analytics/README.md` §Active |
| `docs/analytics/mobile-search-events.md` | analytics | Active / Contract | Mobile Search導線のEvent名・Payload・禁止属性契約 | 同上 |
| `docs/analytics/mobile-reflection-to-consultation.md` | analytics | Active / Contract | Mobile Reflection保存後の再相談CTAのEvent契約 | 同上 |
| `docs/analytics/consultation-history-events.md` | analytics | Active / Contract | 相談履歴導線のEvent名・Payload・重複防止・禁止属性契約 | 同上 |
| `docs/analytics/direction-analytics-dashboard.md` | analytics | Proposed Dashboard Configuration / Implementation Active | 方位利用ファネル、KPI、PostHog設定案、異常値・日盤検討基準 | 同上（※Status語彙の混在。H-4参照） |
| `docs/analytics/direction-analytics-data-quality.md` | analytics | Active / Quality Contract | 方位Eventの機械可読品質契約、重複・欠損・禁止属性、障害調査手順 | 同上 |
| `docs/analytics/action-suggestion-funnel.md` | analytics | Active | Action Suggestion関連EventのEvent名管理 | 同上 |
| `docs/analytics/monetization-funnel.md` | analytics | Active | Premium / Monetization FunnelのEvent名管理 | 同上 |
| `docs/analytics/save-premium-correlation.md` | analytics | Active | 保存行動とPremium転換のEvent間相関分析の読み方 | 同上 |
| `docs/analytics/recommendation-score-v2-current-design.md` | analytics | Active | Recommendation Score v2の現行スコア式・重み・PostHog計測項目の対応 | 同上 |
| `docs/analytics/user-state-profile.md` | analytics | Active | Score v2が用いるUser State Profileの定義 | 同上 |
| `docs/analytics/shrine-meaning-profile.md` | analytics | Active | Score v2が用いるShrine Meaning Profileの定義 | 同上 |
| `docs/analytics/context-profile.md` | analytics | Active | Score v2が用いるContext Profileの定義 | 同上 |
| `docs/analytics/behavior-profile.md` | analytics | Active | Score v2が用いるBehavior Profileの定義 | 同上 |

### A-5. Domain README非設置領域（infra / ci / ops / design）

これらの領域にはDomain READMEが存在しない。Authorityは`docs/README.md`からの参照と
文書自身のStatus headerの二点のみである。**Domain README相当のAuthorityは存在しない**ため、
本表は「Current Source of Truth候補」として扱い、確定はH章へ送る。

| path | domain | status | responsibility | authority source |
| --- | --- | --- | --- | --- |
| `docs/infra/env_policy.md` | infra | Active | 環境変数の運用方針、`.env`取り扱い、APIキー管理 | 自己宣言 + `docs/README.md` §インフラ/環境変数 + `docs/core/runtime-security-baseline.md:115` が正本指定 |
| `docs/ci/testing_policy.md` | ci | **Status header無し** | テスト種別、外部API方針、CI失敗時の判断基準、E2E境界 | `docs/README.md` §開発・検証 + `docs/core/runtime-security-baseline.md:126` が正本指定 |
| `docs/ops/direction-fail-safe.md` | ops | **Status header無し** | 方位機能の縮退契約、障害対応、禁止ログ情報 | `docs/product/compass-product-contract.md:520`・`docs/product/compass-mvp-runtime-contract.md:49,429` が禁止事項・縮退契約の根拠として明示参照 |
| `docs/design/design-token.md` | design | Active | Primitive / Semantic / Platform Themeの3層構造、Semantic Token責務、Governance | 自己宣言 + `docs/README.md` §Design・UI基盤が正本として参照 |
| `docs/infra/render-startup.md` | infra | **Status header無し** | Render Web Service起動運用 | `docs/README.md` §インフラ/Renderからの参照のみ |
| `docs/ops/production-smoke-checklist.md` | ops | **Status header無し** | 本番デプロイ後のsmoke確認手順 | `docs/README.md` §開発・検証/本番確認からの参照のみ |
| `docs/ops/production-smoke-log.md` | ops | **Status header無し** | smoke確認結果の記録（時点ログ） | `docs/README.md`からの参照のみ。**時点記録であり現行ルール抽出対象外** |
| `docs/ops/guest-data-retention.md` | ops | **Status header無し** | 匿名Ownerデータの90日Retention運用 | **どのREADMEからも参照されていない** → H-2 |
| `docs/ops/production-bff-hardening.md` | ops | **Status header無し** | 本番BFFエラーの切り分けチェックリスト | **どのREADMEからも参照されていない** → H-2 |
| `docs/design/premium-meaning-ui-direction.md` | design | **Status header無し**（本文に「design decision + implementation planning」と記載） | Premium Meaning UIの方向づけと実装PR計画 | **どのREADMEからも参照されていない** → H-2 |

---

## B. Excluded Reference Documents

Reference分類の文書は現行ルール抽出対象外とする。**削除は行わない。**

| path | 除外理由 | authority source |
| --- | --- | --- |
| `docs/core/auth-flow.md` | Reference（認証要求時の画面遷移・`returnTo`・復帰導線の補足） | `docs/core/README.md` §Reference + 自己Status: Reference |
| `docs/product/home-hero-final-wireframe.md` | Reference（Home Hero UI設計） | `docs/product/README.md` §Reference + 自己Status |
| `docs/product/concierge-entry-final-wireframe.md` | Reference（Concierge Entry UI設計） | 同上 |
| `docs/product/concierge-filter-area.md` | Reference（Filter UI設計） | 同上 |
| `docs/product/need-mode-ui-flow.md` | Reference（Need Mode UI導線） | 同上 |
| `docs/product/compat-mode-ui-flow.md` | Reference（Compat Mode UI導線） | 同上 |
| `docs/product/visit-style-taxonomy.md` | Reference（参拝スタイル分類） | 同上 |
| `docs/product/explore-integration-design.md` | Reference（Explore体験設計） | 同上 |
| `docs/product/product-document-audit.md` | Reference（Product文書の監査・分類管理）。Status header無し | `docs/product/README.md` §Reference |
| `docs/product/concierge-card-architecture.md` | Reference（Card Tree、Visibility Policy、Renderer責務の設計補足） | `docs/product/README.md` §Reference + `docs/README.md` §Reference + 自己Status |
| `docs/product/direction-ranking-design.md` | Reference（方角を推薦補助軸として扱う設計補足）。**自己Statusは Active**（G-3） | `docs/product/README.md` §Reference + `docs/README.md` §Reference |
| `docs/product/reflection-timeline-design.md` | Reference（長期的な振り返り体験の構想） | `docs/product/README.md` §Reference（`docs/README.md`は現行案内側に掲載。G-2） |
| `docs/product/mobile-bottom-navigation.md` | Reference（Mobile下部ナビゲーション設計補足） | `docs/product/README.md` §Reference + 自己Status |
| `docs/product/monetization-flow-design.md` | Reference（Premium提示、購入復帰、継続計測の設計） | `docs/product/README.md` §Reference + 自己Status（`docs/README.md`は正本案内とReferenceへ二重掲載。G-2） |
| `docs/product/shrine-detail-meaning-layer.md` | Reference（Shrine DetailにおけるMeaning Layerの設計補足） | `docs/product/README.md` §Reference + 自己Status |
| `docs/knowledge/recommendation-v4-copy-guideline.md` | Reference（v4固有コピー規則の補足） | `docs/knowledge/README.md` §Reference + 自己Status |
| `docs/knowledge/evidence-foundation-shared-contract.md` | Reference（Evidence Foundation Shared Contract）。**自己Statusは Active**（G-3） | `docs/knowledge/README.md` §Reference |
| `docs/analytics/analytics-payload-audit.md` | Reference（Payload・Session IDの設計背景） | `docs/analytics/README.md` §Reference + 自己Status |
| `docs/analytics/recommendation-score-v3-design.md` | Reference（Score v3のSignal / Weight / 評価設計）。**`docs/core/architecture.md:190`はScoreの正本として参照**（G-4） | `docs/analytics/README.md` §Reference + 自己Status |
| `docs/analytics/reflection-funnel-dashboard.md` | Reference（Reflection Funnel KPI・Dashboard設計） | 同上 |
| `docs/analytics/recommendation-score-v2.md` | Reference（4 Profile統合設計の背景） | 同上 |
| `docs/analytics/recommendation-score-v2-foundation.md` | Reference（4レイヤー構成の背景） | 同上 |
| `docs/analytics/recommendation-quality-analytics-boundary.md` | Reference（`quality` payloadの責務境界の背景） | 同上 |
| `docs/analytics/history-theme-dashboard.md` | Reference（historyTheme別Dashboardの見方） | 同上 |
| `docs/analytics/history-theme-premium-dashboard.md` | Reference（historyTheme × Premium Dashboardの見方） | 同上 |
| `docs/analytics/reflection-next-recommendation-design.md` | Reference（Reflectionから次回推薦への接続の背景） | 同上 |
| `docs/analytics/consultation-axis-analytics-summary.md` | Reference（consultationAxis別行動差分の集計方針） | 同上 |

---

## C. Excluded Archive Documents

Archive分類の文書は現行ルール抽出対象外とする。**削除は行わない。**

| path | 除外理由 | authority source |
| --- | --- | --- |
| `docs/product/concierge-first.md` | Archive（Concierge First初期設計） | `docs/product/README.md` §Archive + 自己Status |
| `docs/product/concierge-first-wireframe.md` | Archive（初期ワイヤーフレーム） | 同上 |
| `docs/product/pricing.md` | Archive（`premium-experience.md`へ統合済み）。**`docs/README.md` §Premium・課金は正本案内に残置**（G-1、既知の確認ポイント） | `docs/product/README.md` §Archive + 自己Status: Archive |
| `docs/product/card-visibility-renderer-split.md` | Archive（`concierge-card-architecture.md`へ統合済み）。**`docs/README.md`はReferenceとして掲載**（G-1） | `docs/product/README.md` §Archive + 自己Status: Archive |
| `docs/analytics/analytics-card-events.md` | Archive（Card単位Analytics Eventの初期設計・移行計画） | `docs/analytics/README.md` §Archive + 自己Status |
| `docs/analytics/card-ctr-aggregation.md` | Archive（Card CTR集計の初期設計） | 同上 |
| `docs/analytics/premium-analytics-dashboard.md` | Archive（Premium Analytics Dashboardの初期設計） | 同上 |
| `docs/analytics/shrine-detail-analytics-route.md` | Archive（Shrine Detail Analytics Routeの初期設計） | 同上 |
| `docs/analytics/consultation-axis-discovery.md` | Archive（時点監査） | 同上 |
| `docs/analytics/meaning-context-unused-audit.md` | Archive（時点監査） | 同上 |
| `docs/analytics/recommendation-funnel-analysis.md` | Archive（時点監査） | 同上 |
| `docs/analytics/recommendation-output-quality-review.md` | Archive（時点レビュー） | 同上 |
| `docs/analytics/recommendation-output-snapshot.md` | Archive（時点スナップショット） | 同上 |
| `docs/analytics/recommendation-score-v2-output-funnel-audit.md` | Archive（時点監査） | 同上 |
| `docs/analytics/recommendation-score-v2-quality-audit.md` | Archive（時点監査） | 同上 |
| `docs/analytics/score-v2-behavior-correlation-audit.md` | Archive（時点監査） | 同上 |
| `docs/analytics/score-v2-behavior-cvr-sql.md` | Archive（時点監査） | 同上 |
| `docs/analytics/score-v2-measurement-source-audit.md` | Archive（時点監査） | 同上 |
| `docs/analytics/score-v2-production-snapshot.md` | Archive（時点スナップショット） | 同上 |
| `docs/infra/security-alerts-inventory.md` | Archive（自己Status: Archive。Domain README不在のため自己申告のみが根拠） | 自己Status |
| `docs/infra/security-alerts-triage.md` | Archive（同上） | 自己Status |

### C-1. 参照先として案内されているが存在しないパス

| 参照元 | 参照先 | 事実 |
| --- | --- | --- |
| `docs/README.md` §Audit / Archive | `docs/archive/` | **ディレクトリが存在しない**（G-6） |
| `docs/core/openapi-contract-governance.md`（分類表） | `docs/openapi_generated.yaml` | **ファイルが存在しない**。同書は「仕様根拠として一切使用しない」と規定しており、不在は規定と矛盾しない（G-6に記録のみ） |

---

## D. Audit / Decision Record Exceptions

判定基準（Authority判定6に基づく）:
**現行実装コードまたはActive正本文書が、`docs/audit/*`または未分類のDecision Recordを
明示的に参照し、そこにしか存在しない判断・契約に依存している**もののみを例外候補とする。
本書はこれらをCurrent Source of Truthへ昇格させない。Phase 2の判断対象として記録する。

### D-1. `docs/product/`内のMother Ship Decision Record（Domain README未掲載）

| path | status（自己申告） | 実装・正本からの参照 | 例外候補理由 |
| --- | --- | --- | --- |
| `docs/product/compass-product-direction-decision.md` | `DECIDED — MOTHER SHIP PRODUCT DIRECTION` | `backend/temples/services/compass_runtime.py:15`が「#2508 Final Direction Logic」として明示参照。Active正本`docs/product/compass-product-contract.md`が§2.2・§87・§101等で10箇所以上参照。`docs/product/compass-mvp-runtime-contract.md:5`が「Final Direction Logic（Option C）をCONTRACT TARGET」として参照 | Mother Ship Product Decision Recordであり、Compass Direction Logic（Monthly Fallback / Option C）の唯一の決定根拠。`docs/product/README.md`のいずれのカテゴリにも未掲載 |

### D-2. `docs/audit/`配下で自己Status: Activeかつ実装から参照されている文書

| path | status（自己申告） | 実装からの参照 |
| --- | --- | --- |
| `docs/audit/compass-result-experience.md` | Active | 実装コードから`docs/audit/`パス参照あり |
| `docs/audit/compass-route-attribution-contract.md` | Active | 同上 |
| `docs/audit/compass-monthly-fallback-ui-analytics-boundary.md` | Active（§1-22は時点監査） | 同上 |

### D-3. 実装が「契約・判定式・安全規則」としてaudit文書を直接参照している箇所

Active正本側に同等の記述が確認できず、実装が`docs/audit/*`を第一根拠としているもの。

| 参照元（実装） | 参照先audit文書 | 実装が依存している内容 |
| --- | --- | --- |
| `backend/temples/services/evidence_gate.py:119` | `docs/audit/deep-dive-readiness-content-sufficiency.md` §3.4 | 機械的判定式 |
| `backend/temples/services/deep_dive_deterministic_answer.py:3,13,140` | `docs/audit/deep-dive-non-llm-runtime-alignment.md` §5 | Non-LLM Answer生成、**Absolute Safety Rules** |
| `backend/temples/services/deep_dive_answer.py:34` | `docs/audit/deep-dive-non-llm-runtime-alignment.md` | LLM未使用・失敗時の挙動 |
| `backend/temples/services/concierge_chat_ranking.py:1155` | `docs/audit/compass-text-evidence-scoring-decision.md` | **Text Evidence Scoring Contract** |
| `backend/temples/services/concierge_chat_ranking.py:381,383` | `docs/audit/marriage-love-alias-boundary.md`（`PRODUCT_SEMANTIC_DECISION_REQUIRED`）、`docs/audit/marriage-need-independence-implementation.md` | need alias境界の意味決定 |
| `backend/temples/services/concierge_chat_ranking.py:1808,1811,1943`、`concierge_chat.py:812` | `docs/audit/compass-need-lead-purpose-alignment.md` | Lead Purpose Alignment / Evidence Chain |
| `backend/temples/services/compass_recommendation_orchestrator.py:84` | `docs/audit/`（authorized sector距離例外） | 距離に依らないsector通過規則 |
| `backend/temples/services/knowledge_coverage_report.py:3,4,22,128` | `docs/audit/knowledge-coverage-canonical-scope-fix.md`ほか | canonical scope定義 |
| `backend/temples/services/knowledge_seed.py:11,65` | `docs/audit/temples-0091-production-remediation.md` | seed実行の制約 |
| `backend/shrine_project/settings.py:88` / `backend/tests/test_settings_migration_modules_nogis_scope.py:11` | `docs/audit/production-migration-modules-nogis-root-cause.md` | migration modules scope |
| `backend/temples/services/concierge_input_contract.py:5,99,201` | `docs/audit/concierge-input-level-signal-inventory.md` | 入力contractのGap定義 |
| `packages/shared/recommendationAnalyticsProvenance.ts:91,102` | `docs/audit/recommendation-instance-identity-propagation.md`（Option C）、`docs/audit/recommendation-strict-funnel-readiness.md` §6,§14 | provenance伝播方式の採択 |

> 実装が`docs/audit/`を参照している文書は全体で **77件**（`docs/audit/*.md`パスのユニーク数）。
> 上表はそのうち「判定式・契約・安全規則」として参照されているものを抜粋した。

### D-4. Active正本が決定内容をaudit文書へ委譲している箇所

| Active正本 | 委譲先audit文書 | 委譲内容 |
| --- | --- | --- |
| `docs/design/design-token.md:101` | `docs/audit/design-token-stage3-neutral-semantic-decision.md` | 中立色統合方針（Option B採用、**決定済み**） |
| `docs/design/design-token.md:107` | `docs/audit/design-token-stage3-dark-surface-decision.md` | Dark Surface Semantic Token新設（**決定済み**） |
| `docs/design/design-token.md:113` | `docs/audit/design-token-stage4-mother-ship-decisions.md` | Stage 4 Mother Ship Decisions 4カテゴリ（**決定済み**） |
| `docs/design/design-token.md:115` | `docs/audit/design-token-stage4-d3-semantic-decisions.md` | Stage 4 D3 Semantic Decisions 4件（**決定済み**） |
| `docs/README.md` §Design・UI基盤 | `docs/audit/design-token-phase6-audit.md` | 監査時点の現行値・重複実装・Web/Mobile比較の根拠 |
| `docs/README.md` §Reference Documents | `docs/audit/concierge-risk-register.md` | Concierge周辺の変更リスク台帳（自己Status: Reference） |
| `docs/analytics/monetization-funnel.md:5,50` | `docs/audit/cross-platform-event-contract.md` | Web / Mobile送信差異の検証結果と解消方針 |
| `docs/core/openapi-contract-governance.md:87,113` | `docs/audit/manual-openapi-contract-drift.md` | `backend/schema.yml`の生成経路、移行案A〜D |
| `docs/product/mobile-user-flow.md`（全編） | `docs/audit/mobile-user-flow-inventory.md` | 「事実(監査根拠)」としての一次情報。同書自身が「正本ではない」と明記 |

---

## E. Current Rule Candidates

各Active正本から、MUST / MUST NOT / responsibility boundary / source of truth / prohibition /
invariant / update rule / conflict rule / fail-safe ruleに該当する記述のみを抽出する。

**除外したもの**（タスク指定4に従い、Fixed候補へ分類しない）:
現在値（coverage %、神社件数、105社等）、Score weight・計算式の数値、
feature-specific implementation detail、file pathだけに依存する操作、未確定事項、
Future案、TODO、Superseded仕様（旧Readiness Level 0〜3を含む）。

### E-1. Conflict Rule（文書 / 実装 / テストの食い違いの扱い）

| # | rule | type | source |
| --- | --- | --- | --- |
| E1-1 | 文書、実装およびテストが食い違う場合、いずれか一つを自動的に正しいものとして扱わず、意図した仕様を確認する | conflict rule | `docs/core/README.md:125` |
| E1-2 | OpenAPI文書と実装が矛盾する場合、現時点では実装側を優先して判断する。ただしこれは「実装が常に仕様として正しい」ことを意味せず、矛盾検知時は監査対象へ差し戻す | conflict rule | `docs/core/openapi-contract-governance.md:49,51` |
| E1-3 | 情報源が矛盾する場合、黙って一方を採用しない | conflict rule | `docs/knowledge/shrine-knowledge-contract.md:253` |
| E1-4 | 矛盾するSourceを削除せず保持する（片方を消して整合性があるように見せない） | conflict rule | `docs/knowledge/shrine-knowledge-contract.md:541` |
| E1-5 | 異なる用途の住所を「新旧」「正誤」と推測で統合しない。説明不能な競合は推測で解消しない | conflict rule | `docs/knowledge/shrine-position-contract.md:107` / `docs/knowledge/README.md` §更新ルール |
| E1-6 | 下流文書だけを更新し、上流仕様または共通用語と矛盾する変更は禁止する | conflict rule / update rule | `docs/knowledge/README.md:128` |
| E1-7 | `compass-mvp-runtime-contract.md`と過去監査群の内容が矛盾する場合は`compass-product-contract.md`を優先する | conflict rule | `docs/product/compass-mvp-runtime-contract.md:5` |
| E1-8 | `mobile-user-flow.md`と監査文書の記載が食い違う場合、より新しい実装・テストの確認結果を優先する | conflict rule | `docs/product/mobile-user-flow.md:7` |

### E-2. Source of Truth（正本の所在）

| # | rule | type | source |
| --- | --- | --- | --- |
| E2-1 | Core文書は目的・責務・境界・入出力の意味・禁止事項・委譲関係・互換方針・更新条件を管理する。実装とテストはEndpoint / Route / Field / Payload / 保存処理 / 判定処理 / Fallback / 実Responseを管理する | source of truth / responsibility boundary | `docs/core/README.md:121` §文書正本と実装正本 |
| E2-2 | Django実装（URL routing / View / Serializer / Permission）をAPI実装上の**唯一の正本**とし、Backendテストを正本の補助とする | source of truth | `docs/core/openapi-contract-governance.md:40,47,84,85` |
| E2-3 | `docs/openapi.yaml`は現行API契約の正本として扱わない（Reference候補） | source of truth / prohibition | `docs/core/openapi-contract-governance.md:88,111` |
| E2-4 | `docs/openapi_generated.yaml`を仕様根拠として一切使用しない。新規docsで根拠として引用しない | prohibition | `docs/core/openapi-contract-governance.md:89,118,131` |
| E2-5 | `api_schema.yaml` / `api_schema.json` / `backend/schema.yml` は現時点で**未確定**であり正本として扱わない | source of truth | `docs/core/openapi-contract-governance.md:86,87` |
| E2-6 | 方位計算と表示契約の正本はBackendとする | source of truth | `docs/core/architecture.md:94` / `docs/core/direction-response-contract.md` §責務 |
| E2-7 | Consultation Interpretation Engineの正本はbackend実装とする | source of truth | `docs/core/architecture.md:58` |
| E2-8 | Recommendation Reasonの意味生成正本はBackendとする | source of truth | `docs/core/recommendation-reason-contract.md:210,212` |
| E2-9 | 各仕様書で利用する用語は`docs/knowledge/glossary.md`の定義を正本とする | source of truth | `docs/knowledge/glossary.md:7` |
| E2-10 | 自由入力（`query`）を相談解釈の正本とし、相談テーマ・ご利益・誕生日・占術情報は補助シグナルとする | source of truth | `docs/product/meaning-translation-mapping.md:24,64,80` / `docs/product/consultation-theme-taxonomy.md:20` |
| E2-11 | 推薦入力の正本は`need_tags`と`consultation_axis`とする。`need_tags`はUser Stateの正本である | source of truth | `docs/product/consultation-theme-taxonomy.md:21` / `docs/analytics/user-state-profile.md:45,479,608` |
| E2-12 | `consultationSummary`はUser Stateの正本ではない | source of truth / prohibition | `docs/analytics/user-state-profile.md:239,253` |
| E2-13 | `Shrine.goriyaku_tags`は検索・推薦に使う正本データとする。MVPでは投稿者選択タグをそのまま検索・推薦の正本にしない | source of truth | `docs/product/shrine-submission-flow.md:167,226` |
| E2-14 | 神社追加のsuggestは入力補助であり正本ではない。正本の重複判定はsubmit後の`duplicate_candidate`とする | source of truth | `docs/product/shrine-submission-flow.md:63,64` |
| E2-15 | Analytics Eventの正本は各helper実装（`packages/shared/directionAnalytics.ts`、`apps/web/src/lib/analytics/consultationHistoryEvents.ts`、`apps/mobile/lib/consultationHistoryAnalytics.ts`等）とする | source of truth | `docs/analytics/direction-events.md:5` / `docs/analytics/consultation-history-events.md:5,145,149` |
| E2-16 | 行動シグナルについて、PostHogは行動観測・CVR確認の一時正本、DBはRecommendation Score v2へ反映する正本とする | source of truth | `docs/analytics/recommendation-score-v2-current-design.md:363,364` |
| E2-17 | 環境変数の実際の値・既定値・実装はコードおよび設定ファイル（`backend/.env.example`）を正本とする | source of truth | `docs/infra/env_policy.md:5,31` |
| E2-18 | 方位条件のE2E正本は`apps/web/e2e/05_direction_flow.spec.ts`とする | source of truth | `docs/ci/testing_policy.md:22` |
| E2-19 | Concierge仕様における最終的な期待動作は実装とテストをsource of truthとする（Tests are the source of truth） | source of truth | `docs/core/concierge-spec.md:110,340` |

### E-3. Responsibility Boundary（責務境界）

| # | rule | type | source |
| --- | --- | --- | --- |
| E3-1 | Frontendは認証状態と認証要求時のUIを担当する。Tokenの保持・更新・Backendへの付与はBFFの責務。認証・権限・所有者・課金状態の最終判定はBackendが担当する | responsibility boundary | `docs/core/architecture.md:297-299` / `docs/core/authentication-flow.md` §責務境界 |
| E3-2 | WebとMobileのToken保存方式を同一視しない | responsibility boundary | `docs/core/architecture.md:300` |
| E3-3 | Meaning Layerは表示コピーを直接生成せず、推薦順位を直接決定せず、永続データを保持しない | responsibility boundary | `docs/core/meaning-layer-connection.md:98,118,164` |
| E3-4 | Meaning Translationは推薦の意味づけを担う補助レイヤーであり、推薦順位・Scoreを単独で決定しない | responsibility boundary | `docs/product/meaning-translation-mapping.md:58,428` |
| E3-5 | Action Suggestionは行動レイヤーであり、神社の選定・推薦順位・推薦理由そのものを決定しない。推薦理由を再生成しない | responsibility boundary | `docs/product/action_suggestion_v4.md:33,231` |
| E3-6 | Consultation Interpreter自体は推薦コピーを生成しない | responsibility boundary | `docs/product/recommendation-v4-interpreter-contract.md:224` |
| E3-7 | Recommendation Readinessの責務はGovernance観測のみ。Candidate generation / Candidate exclusion / Score / Ranking / Fact usability判定 / Reason V4生成 / matching / personalization / user-facing label は明示的に責務外 | responsibility boundary / invariant | `docs/core/recommendation-readiness.md:25-27` §Non-responsibilities |
| E3-8 | Recommendation ReadinessとEvidence Gateは別責務であり混同しない。Readiness側でEvidence Gateのverificationルールを再実装しない | responsibility boundary | `docs/core/recommendation-readiness.md:77,86` |
| E3-9 | Recommendation Eligibilityはcandidate setの**境界**であり、scoreへは一切寄与しない。ineligibleな Shrineを「低スコアで残す」ことはしない | responsibility boundary / invariant | `docs/knowledge/recommendation-eligibility-contract.md` §不変条件 |
| E3-10 | Compass Runtime Authorityは、候補集合の中でどの神社が最も意味的に合うかを決定する権限を持たない。Direction RuntimeとRecommendation結果は別フィールドとして保持し、単一オブジェクトへマージしない | responsibility boundary / invariant | `docs/product/compass-mvp-runtime-contract.md:366` / `docs/product/compass-product-contract.md` §6 |
| E3-11 | Signal Reuse（計算モジュールの再利用）は許可、Authority Reuse（製品責務の継承）は禁止。CompassはCompat ModeのAuthorityを継承しない | responsibility boundary / prohibition | `docs/product/compass-product-contract.md:73,76` §1 |
| E3-12 | Knowledge Baseはデータ品質・文章品質・生成原則を管理し、Core・Productの実装契約を重複定義しない。正本文書とReference文書の責務を混在させない | responsibility boundary | `docs/knowledge/README.md:107,108` |
| E3-13 | Coreはシステム全体構造・横断技術責務・品質基準・接続契約・生成原則を管理し、画面/体験はProduct、神社データ/意味定義/コピーはKnowledge、Event/KPIはAnalytics、監査結果はAuditへ委譲する | responsibility boundary | `docs/core/README.md` §責務境界 |
| E3-14 | Journey Timeline文書はAction Suggestionの生成方法・判定ロジックを保持しない | responsibility boundary | `docs/product/journey-timeline-design.md:357,421` |
| E3-15 | `route_open`（PostHog系）と`trackShrineRouteOpen`（Backend `/shrine-interactions/` POST系）は送信先が異なる別系統として扱う | responsibility boundary | `docs/analytics/mobile-search-events.md:68` |
| E3-16 | WebとMobileでAction Suggestionの計測対象・方式が異なるため、同一指標として比較しない | responsibility boundary | `docs/analytics/action-suggestion-funnel.md:74` |
| E3-17 | 神社詳細は複数の入口を持つ単一の共通合流地点として扱い、独立した主導線としては扱わない | responsibility boundary | `docs/product/mobile-user-flow.md:47,82,114` |
| E3-18 | 地図はKAMI MUSUBIの主導線ではなく探索補助機能として扱う | responsibility boundary | `docs/product/mobile-user-flow.md:48` |
| E3-19 | 検索（Explore）・コンシェルジュ・地図・人気ランキングの責務を混同しない | responsibility boundary | `docs/core/recommendation-architecture.md:218` / `docs/core/architecture.md` §画面責務分離 |
| E3-20 | ComponentはSemantic Tokenを参照し、Primitive Tokenを直接参照しない（例外はコード上に理由を残す） | responsibility boundary | `docs/design/design-token.md:36,52` |

### E-4. Invariant（不変条件）

| # | rule | type | source |
| --- | --- | --- | --- |
| E4-1 | ConciergeとCompassは別の製品体験である。共有基盤は共有製品責務を意味しない | invariant | `docs/product/compass-product-contract.md:46` §0 Master Principle |
| E4-2 | Compassの価値を作るために、Conciergeの挙動・Ranking・API契約・UX責務を再設計または弱めてはならない。Existing Concierge Impact = ZERO | invariant / MUST NOT | `docs/product/compass-product-contract.md` §0 |
| E4-3 | Concierge内での方位前面化制約はRESTRICTED（不変）。Direction Audit完了はConcierge内での方位前面化を自動的に許可しない（不可逆の境界） | invariant | `docs/product/compass-product-contract.md:530,536,538` §5 |
| E4-4 | `Shrine DB presence != Recommendation eligibility`。Recommendation候補になれるのはusableなDeity FactまたはHistory Factを最低1件持つShrineだけである | invariant | `docs/knowledge/recommendation-eligibility-contract.md` §不変条件 |
| E4-5 | Shared eligibilityはF5 Qualified Evidence gatingでもranking signalでもない | invariant | 同上 |
| E4-6 | 日盤（day-plate）・時盤はMVP対象外であり、`docs/ops/direction-fail-safe.md`が追加を明示的に禁止する。この制約を継承する | invariant / prohibition | `docs/product/compass-product-contract.md:520` / `docs/product/compass-mvp-runtime-contract.md:49,51` / `docs/analytics/direction-events.md:44` |
| E4-7 | Compassは年盤単独結果を出力として採用しない。`target_date`無効時は方向コンテキスト自体を省略し、年盤のみへ縮退させない | invariant / fail-safe rule | `docs/product/compass-mvp-runtime-contract.md:241` |
| E4-8 | Monthly Fallback Directionを年盤・月盤の合意（COMMON DIRECTION）であるかのように表示してはならない | invariant / MUST NOT | `docs/product/compass-product-contract.md:453` / `docs/product/compass-mvp-runtime-contract.md:488` |
| E4-9 | 同一本命星・同一対象月であれば再計算しても結果は決定的に同一である。非決定的な挙動を導入してはならない | invariant / MUST NOT | `docs/product/compass-product-contract.md:439` / `docs/product/compass-mvp-runtime-contract.md:485` |
| E4-10 | 保存済みの推薦結果は、神社情報・評価ロジック・ユーザー行動状態が後から変化しても暗黙に再計算または再ランキングしない | invariant | `docs/core/architecture.md:170` / `docs/core/recommendation-reason-contract.md:325` |
| E4-11 | 現在のFavorite / Visit / Reflectionは現在状態として管理し、過去の推薦結果と同一視しない | invariant | `docs/core/architecture.md:172` |
| E4-12 | local `jinja_db`の現在状態そのものをcanonical source of truthとはしない（Database Is Not the Source of Truth） | invariant | `docs/core/desktop-development-contract.md:152,154` |
| E4-13 | 開発に使用する唯一のlocal Repositoryを固定する。別cloneをactive development sourceとして使用しない | invariant | `docs/core/desktop-development-contract.md:28,47,61` |
| E4-14 | feature / audit / chore / docs branchは作業単位の一時branchであり、merge後の長期的なsource of truthとはしない | invariant | `docs/core/desktop-development-contract.md:95,439` |
| E4-15 | Fact（事実）とInterpretation（意味文脈）は責務が別であり、どちらか一方だけでは他方を代替しない | invariant | `docs/core/recommendation-reason-contract.md:70,86` |
| E4-16 | `history_type="tradition"`であることは「記述内容が史実として確定している」ことを意味しない | invariant | `docs/core/recommendation-reason-contract.md:88,96` |
| E4-17 | `not_collected`と`unknown`を同一視しない。前者は運用上の未着手、後者は確認済みの情報不足である | invariant | `docs/knowledge/shrine-knowledge-contract.md:246` |
| E4-18 | 概念項目と物理フィールドを同一視しない | invariant | `docs/knowledge/shrine-profile-spec.md:494` |
| E4-19 | RecommendationはMeaningを前提とし、ActionはRecommendationを前提とし、ReflectionはActionを前提とする。同じ用語を複数の意味で利用しない | invariant | `docs/knowledge/glossary.md:11,132` |
| E4-20 | Eventが存在しないことを、その行動が発生しなかったことの証拠として扱わない | invariant | `docs/analytics/save-premium-correlation.md:94` |
| E4-21 | 相関は因果を意味しない。あるEventの後に別のEventが多く発生していることは、前者が後者の原因であることを意味しない | invariant | `docs/analytics/save-premium-correlation.md:118,120` |
| E4-22 | 同一の神社であっても、異なる相談文脈または異なるセッションから発生した行動は同一の意思決定として扱わない | invariant | `docs/analytics/save-premium-correlation.md:112` |
| E4-23 | Concierge Input Levelの「Level 3」とReadinessやUI配置上の同名概念を同一概念として扱わない | invariant | `docs/product/concierge-input-architecture.md:57,222`（※Domain README未掲載。H-1） |
| E4-24 | 延期（Deferred）は削除を意味しない | invariant | `docs/product/mobile-user-flow.md:50,223` |

### E-5. Prohibition / MUST NOT（禁止事項）

#### E-5-1 非断定・効果保証の禁止

| # | rule | type | source |
| --- | --- | --- | --- |
| E5-1 | 心理状態、性格、運命を断定しない | prohibition | `docs/core/architecture.md:99` §禁止事項 |
| E5-2 | AIはユーザーの人生を診断せず、運勢・未来・霊的意味を断定しない。AIによる断定・診断・宗教的保証を目的としない | prohibition | `docs/core/meaning-layer.md:23,121,123` |
| E5-3 | 「吉方位なので行くべき」「必ず良い結果になる」「運気が上がる」「願いが叶う」と断定しない | prohibition | `docs/core/recommendation-reason-contract.md:388` |
| E5-4 | Factに心理診断を書く／Interpretationに神社の未確認事実を書く／Actionに宗教的効果保証を書くことを禁止する | prohibition | `docs/core/recommendation-reason-contract.md:380-382` |
| E5-5 | `history_type="tradition"`のFactを、confidenceに関わらず断定表現（assertive）で出してはならない | MUST NOT | `docs/core/recommendation-reason-contract.md:92,390` |
| E5-6 | 決定論的な未来予測・結果保証をしてはならない | MUST NOT | `docs/product/compass-product-contract.md:622` §9 |
| E5-7 | 日次精度を含意してはならない（「今日の吉方位」等） | MUST NOT | `docs/product/compass-product-contract.md:621` §9 |
| E5-8 | 神社の由緒やご利益を、未来の結果やユーザーの心理状態を保証する根拠として利用しない | prohibition | `docs/knowledge/shrine-data-guide.md:103` |
| E5-9 | `history_theme`をユーザーの性格・心理状態・将来を断定するために使用しない。`history_theme`だけでユーザーの状態を判定しない | prohibition | `docs/product/history-theme-taxonomy.md:34` / `docs/product/visit-reflection-flow.md:262` |
| E5-10 | 医療、心理、宗教または人生上の結果を判定しない。心理診断として扱わない | prohibition | `docs/product/recommendation-v4-interpreter-contract.md:25,78` |
| E5-11 | AIは過去のReflectionだけを根拠にユーザーの状態・性格・将来を断定しない | prohibition | `docs/product/visit-reflection-flow.md:311` |
| E5-12 | Reflectionでは感情を評価しない。回答を誘導せず、正解や望ましい感情を設定しない。他人との比較は行わない | prohibition | `docs/knowledge/reflection-guide.md:81,87,99` / `docs/knowledge/action-guide.md:359` |
| E5-13 | 神社詳細であっても宗教的・心理的に断定しない | prohibition | `docs/product/shrine-detail-v3-design.md:156` |
| E5-14 | 参拝作法や宗教的実践を唯一の正解として強制しない。危険または禁止されている行動を提案しない | prohibition | `docs/knowledge/shrine-data-guide.md:448,449` |
| E5-15 | 行動しない選択を異常として扱わない | prohibition | `docs/product/action_suggestion_v4.md:41` / `docs/product/recommendation-v4-interpreter-contract.md:147` |
| E5-16 | Readiness / Coverageを「神社の信頼度」「神社の格」としてユーザーへ直接表示しない。断定的な優劣表現は避ける | prohibition | `docs/core/recommendation-readiness.md:217` |

#### E-5-2 根拠なき主張・捏造の禁止

| # | rule | type | source |
| --- | --- | --- | --- |
| E5-17 | 保存済み根拠がなければFactとして主張しない | prohibition | `docs/core/recommendation-architecture.md:227` |
| E5-18 | 神社の根拠を占術から捏造してはならない。方位の根拠は神社の根拠を代替できない | MUST NOT | `docs/product/compass-product-contract.md:584` §8 |
| E5-19 | Runtime signal（方位・占術）がShrine Knowledgeを新設・上書きしてはならない | MUST NOT | `docs/product/compass-product-contract.md:619` §9 |
| E5-20 | 未使用のsignalをrecommendation evidenceとして提示してはならない。データが存在するというだけの理由で占術・九星気学・方位・ご利益等の用語を表示しない | MUST NOT | `docs/product/compass-product-contract.md:595,596,620` §8,§9 |
| E5-21 | 方位単独で最終的な神社を決定してはならない。神社の決定は常にRecommendation Authority + Shrine Knowledge Authorityの合成結果とする | MUST NOT | `docs/product/compass-product-contract.md:618` §9 |
| E5-22 | 方位一致をRecommendation Reasonの主理由として表示しない。`direction_reference`・方位一致状態・方角・方位加点をReason文章生成へ入力してはならない | MUST NOT | `docs/core/recommendation-reason-contract.md:236,248,387` |
| E5-23 | AI生成だけで事実項目を確定しない。AI生成のみの祭神情報を`verification_status: source_confirmed`以上として保存しない | prohibition | `docs/knowledge/shrine-data-guide.md:148` / `docs/knowledge/shrine-knowledge-contract.md:251` |
| E5-24 | 情報が`disputed`（矛盾未解決）の場合は断定利用しない | prohibition | `docs/knowledge/shrine-knowledge-contract.md:264,465` |
| E5-25 | 公式情報であっても、由緒に含まれる伝承的記述を歴史的確定事実として扱わない | prohibition | `docs/knowledge/shrine-knowledge-contract.md:320` |
| E5-26 | ご利益タグ（`goriyaku_tags`）を歴史的事実の代替として扱わない。`history_theme`を由緒そのものとして扱わない | prohibition | `docs/knowledge/shrine-knowledge-contract.md:381,382` |
| E5-27 | Actionの根拠として、実在しない施設・文化財・由緒書・境内設備を使用しない。存在が確認できない場所を案内しない | prohibition | `docs/knowledge/shrine-data-guide.md:254,341` / `docs/knowledge/action-guide.md:155` |
| E5-28 | 神社固有の理由が存在しないActionは禁止 | prohibition | `docs/knowledge/action-guide.md:121` |
| E5-29 | Wikipediaのみを唯一の根拠としない。OSM / Wikidataを唯一のprimary sourceにしない | prohibition | `docs/knowledge/shrine-data-guide.md:415` / `docs/knowledge/shrine-position-contract.md:249` |
| E5-30 | ご利益タグだけで推薦理由を完結させない。`theme_key`・ご利益・誕生日・占術・方位だけで推薦結果を決定しない | prohibition | `docs/core/architecture.md:101` / `docs/product/meaning-translation-mapping.md:106` |
| E5-31 | 根拠のない文化解釈を保存しない。Derived情報を一次情報として扱わない | prohibition | `docs/knowledge/shrine-profile-spec.md:208,593,596` |
| E5-32 | HOLD状態では座標を推測してSeed / Productionへ投入しない。既存座標を惰性で維持しない。current candidateを距離だけで自動採用しない | prohibition / fail-safe rule | `docs/knowledge/shrine-position-contract.md:115,116,163` |
| E5-33 | 法人登記住所をVisitor / Navigation Anchorの採用根拠として単独では使用しない | prohibition | `docs/knowledge/shrine-position-contract.md:109` |

#### E-5-3 責務越境・重複実装の禁止

| # | rule | type | source |
| --- | --- | --- | --- |
| E5-34 | frontend / mobileに判定ロジックを重複実装しない | prohibition | `docs/core/architecture.md:103` / `docs/core/recommendation-architecture.md:165` |
| E5-35 | FrontendおよびMobileは、Backendが返す観測用Scoreを独自に順位へ反映しない | prohibition | `docs/core/architecture.md:188` / `docs/core/recommendation-architecture.md:207` |
| E5-36 | Web / mobileは`direction_reference`を再計算しない。クライアントは方位を再計算・補完しない | prohibition | `docs/core/architecture.md:94` / `docs/core/direction-response-contract.md` / `docs/ops/direction-fail-safe.md` §原則 |
| E5-37 | raw_queryを直接スコア加点しない。LLM出力でユーザーの原文を上書きしない | prohibition | `docs/core/architecture.md:100,102` |
| E5-38 | Frontendを意味生成の正本にしない。FrontendはRecommendation Reasonの意味を独自に再解釈しない | prohibition | `docs/core/recommendation-reason-contract.md:220,384` |
| E5-39 | `_explanation_payload`とRecommendation Reasonを同一視しない。Snapshotを後から暗黙に再計算しない | prohibition | `docs/core/recommendation-reason-contract.md:385,386` |
| E5-40 | 内部タグをそのまま表示しない。内部変数名やフォールバック文言を表示しない | prohibition | `docs/core/recommendation-reason-contract.md:383` / `docs/knowledge/recommendation-copy-guide.md:144` / `docs/knowledge/shrine-profile-spec.md:175` / `docs/product/kami-musubi-experience-design.md:88` |
| E5-41 | FrontendでVisit / Reflection / Action生成 / 相談解釈の業務判定を重複実装しない | prohibition | `docs/product/visit-reflection-flow.md:45` / `docs/product/action_suggestion_v4.md:46` / `docs/product/recommendation-v4-interpreter-contract.md:26` / `docs/product/consultation-theme-taxonomy.md:228` |
| E5-42 | Home HeroやConcierge Entryで相談テーマ一覧や内部キー対応を独自に重複管理しない。Frontend / Backend / Analyticsで独自のカテゴリ名を追加しない | prohibition | `docs/product/consultation-theme-taxonomy.md:200,247` / `docs/product/meaning-translation-mapping.md:276` |
| E5-43 | Premium優先・Free制限・未確定時の判定ロジックを画面ごとに重複実装しない。共通実装へ集約する | prohibition | `docs/product/billing-paywall.md:54,56` |
| E5-44 | 画面からPostHog SDK等を直接呼ばず、必ずhelper経由でEventを送信する。Event名と固定`source`/`platform`を画面コードへ分散させない | MUST / prohibition | `docs/analytics/consultation-history-events.md:7` |
| E5-45 | Recommendation ScoreへLLMへ全候補を無条件に渡す設計を正本にしない | prohibition | `docs/core/recommendation-architecture.md:187` |
| E5-46 | Candidate生成段階で最終順位を決定しない（広め取得と最終順位付けを分離する）。入力保持段階でスコア加点や推薦順位への影響を発生させない | prohibition | `docs/core/recommendation-architecture.md:156,176` |
| E5-47 | Compass由来の個人化された派生値（本命星、吉方位等）を`Shrine`モデルまたは関連テーブルへ書き込んではならない | MUST NOT | `docs/product/compass-mvp-runtime-contract.md:126` |
| E5-48 | `purpose`はCompass Runtime Authority（`kyusei.py`・`direction_reference.py`）の計算に一切入力してはならない | MUST NOT | `docs/product/compass-mvp-runtime-contract.md:207` |
| E5-49 | `honmei.num`（本命星番号）は内部のみとし、Presentation Authorityへ公開しない | prohibition | `docs/product/compass-mvp-runtime-contract.md:112` |
| E5-50 | 投稿者入力は直接推薦ロジックに入れず、必ずadmin確認を経由する | MUST | `docs/product/shrine-submission-flow.md:220` |
| E5-51 | Runtime情報を神社プロフィールへ固定情報として保存しない。Runtime情報を神社固定情報として扱わない | prohibition | `docs/knowledge/shrine-profile-spec.md:174,203,206` / `docs/knowledge/shrine-data-guide.md:134` / `docs/knowledge/recommendation-copy-guide.md:56` |

#### E-5-4 認証・セキュリティの禁止

| # | rule | type | source |
| --- | --- | --- | --- |
| E5-52 | Access Token・Refresh TokenはHttpOnly Cookieで管理し、`localStorage`等のJS到達可能な領域へ保存しない。JWTをClient JavaScriptから直接読み取らない | MUST NOT | `docs/core/authentication-flow.md:103` §禁止事項 / `docs/core/runtime-security-baseline.md:55` |
| E5-53 | FrontendからBackendへ認証付き通信を直接行わない。Frontend Route内でBackend URLを直接組み立てない。Frontend ComponentからBackend Originを直接呼び出さない | MUST NOT | `docs/core/architecture.md:301` / `docs/core/authentication-flow.md` §禁止事項 |
| E5-54 | 認証付きRouteで`NEXT_PUBLIC_API_BASE`や`API_BASE_URL`を直接参照しない。FrontendにJWT発行Routeを複数持たない。RouteごとにAuthorization付与処理を重複実装しない | MUST NOT | `docs/core/authentication-flow.md` §禁止事項 |
| E5-55 | 課金状態や権限をFrontendだけで確定しない。Frontend側の未確定状態を理由にBackendの利用制限を回避できる設計にはしない | MUST NOT | `docs/core/authentication-flow.md` §禁止事項 / `docs/product/billing-paywall.md:50` |
| E5-56 | staff/admin操作（Django Admin、superuser作成等）を認証・権限チェックを経ない匿名HTTPエンドポイントとして公開しない。Bootstrap/superuser作成など権限昇格操作をHTTP経由で無条件公開しない | MUST NOT | `docs/core/runtime-security-baseline.md:45,106` |
| E5-57 | DB接続情報・ファイルシステムpath・migration状態・生exceptionなど内部stateを返すdebug endpointを、認証・権限チェックなしに公開しない | MUST NOT | `docs/core/runtime-security-baseline.md:105` |
| E5-58 | 指定情報はDebug/Info/Error/Warningいずれのlevelであってもproduction runtimeのログへ出力してはならない | MUST NOT | `docs/core/runtime-security-baseline.md:60,62` §禁止 |
| E5-59 | `.env`はGitへコミットしない。APIキーは環境変数で管理し、ソースコードへ直接記述しない | MUST NOT | `docs/infra/env_policy.md:27,37` |
| E5-60 | private / authentication stateを含むbackupをRepositoryへcommitしない | MUST NOT | `docs/core/desktop-development-contract.md:314` |
| E5-61 | Production databaseをlocal development databaseとして使用しない。Production `DATABASE_URL`をlocal development操作へ流用しない | MUST NOT | `docs/core/desktop-development-contract.md:144,146` |
| E5-62 | Production DBへ直接DELETEを行わない。必ず専用commandを経由する | MUST NOT | `docs/ops/guest-data-retention.md:114`（※Domain README未参照。H-2） |
| E5-63 | 認証済み`user`を持つrowは削除しない。`anonymous_id`が無い/空の異常rowは推測で削除しない | MUST NOT / fail-safe rule | `docs/ops/guest-data-retention.md:44,46`（※同上） |
| E5-64 | 外部API（LLM等）の実コールはテストで禁止（コスト事故防止）。E2Eは実Backend、外部ジオコードAPI、本番データへ接続しない | MUST NOT | `docs/ci/testing_policy.md:10,20` |

#### E-5-5 Analytics Payloadの禁止属性

| # | rule | type | source |
| --- | --- | --- | --- |
| E5-65 | 禁止属性はEvent名を問わず送信しない（緯度経度、住所、駅名、都道府県名、神社名・住所、Place ID、経路URL、生年月日、予定日、相談文、推薦理由、検索語、方位文言）。表記揺れも正規化して検出する | MUST NOT | `docs/analytics/direction-events.md:20,22` / `docs/analytics/direction-analytics-data-quality.md:49` |
| E5-66 | 同種の禁止Payload規定をMobile Search / Mobile Reflection / Consultation History各契約でも適用する | MUST NOT | `docs/analytics/mobile-search-events.md:43,45` / `docs/analytics/mobile-reflection-to-consultation.md:23,25` / `docs/analytics/consultation-history-events.md:112,114` |
| E5-67 | 禁止属性が1件でも見つかれば即時停止・調査とする | fail-safe rule | `docs/analytics/direction-analytics-dashboard.md:74` / `docs/analytics/direction-analytics-data-quality.md:75` |
| E5-68 | 品質検証用キーを本番イベントへ追加しない。品質判定のために本番payload・イベント名・ユーザー識別子を増やさない | MUST NOT | `docs/analytics/direction-analytics-data-quality.md:5,40` |
| E5-69 | 少数データから個人を推測しない。少数セルは非表示または期間を延長する。Person property・住所系プロパティ・個別ユーザーcohortを作成しない | MUST NOT | `docs/analytics/direction-analytics-dashboard.md:13,61` |
| E5-70 | WebのsessionIdを相談threadIdの代用として使用しない | MUST NOT | `docs/analytics/consultation-history-events.md:124` |
| E5-71 | ConciergeのURLクエリ（`theme`/`q`）へReflection由来の本文を渡さない（自由入力本文がURLへ含まれるため） | MUST NOT | `docs/analytics/mobile-reflection-to-consultation.md:21` |
| E5-72 | Analyticsは体験改善の観測に利用し、個別ユーザーの心理状態・宗教的効果・信仰の程度・人生上の成果を判定するためには利用しない | prohibition | `docs/product/meaning-translation-mapping.md:466` / `docs/product/visit-reflection-flow.md:345` |
| E5-73 | 方位ログ境界で座標・住所・駅名・都道府県名・神社情報・生年月日・参拝日・相談文・推薦理由・例外メッセージ・イベントpayloadを記録しない（例外本文も記録しない） | MUST NOT | `docs/ops/direction-fail-safe.md:30` |

#### E-5-6 Premium境界の禁止

| # | rule | type | source |
| --- | --- | --- | --- |
| E5-74 | Map / SearchをPremiumの主価値にしない。Premium訴求の主語にしない | prohibition | `docs/product/premium-experience.md:72,148` / `docs/product/shrine-detail-layer.md:98` / `docs/product/mobile-user-flow.md:191` |
| E5-75 | 保存機能自体をPremium専用にしない。保存そのものをPremium限定にしない | prohibition | `docs/product/shrine-detail-v3-design.md:390` / `docs/product/visit-reflection-flow.md:360` |
| E5-76 | Web地図の再有効化を、Premium契約条件として自動的に扱わない | prohibition | `docs/product/mobile-user-flow.md:194` |
| E5-77 | Billingが有効なPremiumユーザーには、いかなる場合もPaywallを表示しない | MUST NOT | `docs/product/billing-paywall.md:34` |
| E5-78 | Concierge結果一覧ではfavorite操作を提供しない | prohibition | `docs/core/concierge-spec.md:259` |

### E-6. Fail-safe Rule（縮退・失敗時の扱い）

| # | rule | type | source |
| --- | --- | --- | --- |
| E6-1 | 方位関連処理の失敗を、相談API・通常推薦・通常理由・候補閲覧の失敗へ昇格させない | fail-safe rule | `docs/ops/direction-fail-safe.md` §原則 |
| E6-2 | 不正な`direction_reference`の場合は方位カードを表示しない。分析送信失敗は操作を遅延・中断しない | fail-safe rule | `docs/ops/direction-fail-safe.md:14,15` |
| E6-3 | 方位を無効化した通常相談が成功しない場合は、方位以外の障害として別途エスカレーションする | fail-safe rule | `docs/ops/direction-fail-safe.md:40` |
| E6-4 | Concierge入力の不正値は破棄する（エラーにはしない）。不正入力は無視し、全体をエラーにしない | MUST / fail-safe rule | `docs/core/concierge-spec.md:50,120,121` |
| E6-5 | `birthdate`は内部で必ず`YYYY-MM-DD`へ正規化し、backendが必ず再正規化する | MUST | `docs/core/concierge-spec.md:48,55` |
| E6-6 | `target_date`が不正/パース不能の場合、「未指定」として扱わず方向コンテキストを省略する。クライアントの不正値を黙って「today」へ差し替えない | fail-safe rule | `docs/product/compass-mvp-runtime-contract.md:96` |
| E6-7 | 生年月日欠落時は`CompassDirectionRuntime`を生成しない。デフォルトの生年月日・本命星を代入しない | fail-safe rule | `docs/product/compass-mvp-runtime-contract.md:427` |
| E6-8 | 方位計算が例外で失敗した場合、固定イベントコードでログし、生年月日・座標・例外メッセージは記録しない。当該リクエストの方向コンテキストのみを省略し、Compass全体のレスポンスを失敗させない | fail-safe rule | `docs/product/compass-mvp-runtime-contract.md:429` |
| E6-9 | `NO_COMMON_DIRECTION`はエラーではなく正当なCompass結果として扱う。デフォルト方位を代入せず、「入力を確認してください」という誘導も行わない | fail-safe rule | `docs/product/compass-mvp-runtime-contract.md:437,443` |
| E6-10 | いかなるフォールバックも、裏付けのない占術/方位の主張を生成してはならない | fail-safe rule / MUST NOT | `docs/product/compass-mvp-runtime-contract.md:445` |
| E6-11 | 再試行を主要な解決策として提示してはならない。生年月日・originの訂正を促してはならない（実際に無効である場合を除く） | MUST NOT | `docs/product/compass-mvp-runtime-contract.md:485,486` / `docs/product/compass-product-contract.md:219,220` |
| E6-12 | 真に入力が無効なケース（Aグループ）と`NO_COMMON_DIRECTION` / Monthly Fallback（B・B'グループ）を、ユーザーへの案内文言レベルでも混同してはならない | MUST NOT | `docs/product/compass-mvp-runtime-contract.md:487` |
| E6-13 | Billing状態が未取得またはエラーの場合、FrontendはPremiumユーザーを誤ってPaywall表示で遮断しない | fail-safe rule | `docs/product/billing-paywall.md:46` |
| E6-14 | 地図が利用できない状態でも主要フローを完遂できることを必須条件とする | fail-safe rule / MUST | `docs/product/mobile-user-flow.md:48,139` |
| E6-15 | 一般的な離脱をerrorにしない。Mobileの`candidate_position`欠落を異常とせず、unknownで補完しない。属性欠落を0やunknownへ置換しない | fail-safe rule | `docs/analytics/direction-analytics-data-quality.md:53,55` / `docs/analytics/direction-events.md:39` |
| E6-16 | 0件をエラーと断定しない。閾値超過は調査開始条件であり、機能の良否や因果を断定しない | fail-safe rule | `docs/analytics/direction-events.md:40` / `docs/analytics/direction-analytics-data-quality.md:57` / `docs/analytics/direction-analytics-dashboard.md:65` |
| E6-17 | 品質レポート用のsequence keyがない場合、表示順序を推測しない | fail-safe rule | `docs/analytics/direction-analytics-data-quality.md:56` |

### E-7. LLM関連のMUST / MUST NOT

| # | rule | type | source |
| --- | --- | --- | --- |
| E7-1 | `birthdate`は構造化入力であり、free textとは分離する（MUST）。backendが最終的な正規化責務を持つ（MUST） | MUST | `docs/core/concierge-spec.md:37,38` |
| E7-2 | LLM Disabled（`CONCIERGE_USE_LLM = false`）のとき、推論目的の外部API呼び出しは原則禁止（分類器/要約API等、LLM相当のものを含む） | prohibition | `docs/core/concierge-spec.md:157,159,164` |
| E7-3 | LLM Disabledのとき、Orchestratorは外部通信を行ってはならない（MUST NOT）。Disabled時のOrchestratorはルールベース/ローカル完結であることが必須 | MUST NOT | `docs/core/concierge-spec.md:168,171,172` |
| E7-4 | LLM Disabled（`enabled=false`）の場合、`used=true`は禁止（仕様違反） | prohibition | `docs/core/concierge-spec.md:179` |
| E7-5 | API Contractには破壊禁止項目が存在する | prohibition | `docs/core/concierge-spec.md:187` §2 |

### E-8. Update Rule（更新ルール）

| # | rule | type | source |
| --- | --- | --- | --- |
| E8-1 | Core文書を追加・削除または分類変更した場合は`docs/core/README.md`を同じPRで更新する。Active / Reference分類は監査結果と一致させる | update rule | `docs/core/README.md` §更新ルール |
| E8-2 | 正本を追加・削除した場合は`docs/product/README.md`の「読む順番」と「正本」を同じPRで更新する。分類変更時は`product-document-audit.md`と内容を一致させる。同一文書を複数カテゴリへ重複掲載しない | update rule | `docs/product/README.md` §更新ルール |
| E8-3 | Event名またはPayloadを変更する場合は、実装と契約文書を同じPRで更新する。分類変更時は対象文書のStatusヘッダと`docs/analytics/README.md`を同じPRで更新する | update rule | `docs/analytics/README.md` §更新ルール |
| E8-4 | Database、Prompt、UIへ反映する前にKnowledge Baseを更新する。Knowledge正本は定められた順序（shrine-profile-spec → shrine-knowledge-contract → shrine-data-guide → shrine-position-contract → recommendation-copy-guide → action-guide → reflection-guide → glossary）で更新する | update rule | `docs/knowledge/README.md` §更新ルール・§更新順序 |
| E8-5 | 共通コピー原則を変更する場合は、先に`recommendation-copy-guide.md`へ反映し、その後にv4固有規則との整合を確認する | update rule | `docs/knowledge/README.md` §更新順序 |
| E8-6 | Reference文書の未実装案を、実装済み仕様として扱わない | update rule / prohibition | `docs/analytics/README.md:90` |
| E8-7 | Audit文書に記載された時点判断やTODOを現行契約として扱わない | update rule / prohibition | `docs/analytics/README.md:81` |
| E8-8 | Archive文書は履歴保存を目的とし、現行の仕様・計測契約判断には使用しない | update rule / prohibition | `docs/product/README.md:160` / `docs/analytics/README.md:79` |
| E8-9 | 詳細仕様、TODO、実装履歴、監査結果およびPR情報を各READMEへ記載しない | update rule | `docs/core/README.md` / `docs/product/README.md` §更新ルール |
| E8-10 | Recommendation Readinessは実装の進捗やデータ件数だけでは更新しない。Governance責務・Non-responsibilitiesの変更時に更新する | update rule | `docs/core/recommendation-readiness.md:286,292` |
| E8-11 | 新しいScoreは既存順位へ直ちに反映せず、差分・寄与・行動データとの関係を観測した上で適用可否を判断する | update rule | `docs/core/architecture.md` §Recommendation Score |
| E8-12 | Analytics Eventの追加より既存属性による集計を優先する。追加が必要な場合は目的・発火箇所・重複単位・保持期間・禁止属性検査・Web／モバイル差を先に契約文書へ追記する | update rule | `docs/analytics/direction-events.md:44` |
| E8-13 | `docs/audit/README.md`は audit文書の内容・Status・削除・移動を管理しない。新しいaudit chainを索引化する場合はCurrent Source of Truthとの対応関係を確認した上で追加する | update rule | `docs/audit/README.md` §更新ルール |
| E8-14 | 古い数値（Coverage件数、shrine件数等）はHistorical Snapshotとしてそのまま残りうる。現在値へ無断更新しない | update rule | `docs/audit/README.md` §`docs/audit/`の性質 |
| E8-15 | Statusなしは「未分類」を意味するに留まり、Statusなし＝古い/Superseded/Archiveと断定しない | update rule / conflict rule | `docs/audit/README.md` §Statusが付与されていない文書について |

### E-9. 優先順位ルール（Precedence）

| # | rule | type | source |
| --- | --- | --- | --- |
| E9-1 | 自由入力がある場合は自由入力を優先する。相談テーマと自由入力が矛盾する場合は自由入力由来の解釈を優先する | update rule / conflict rule | `docs/product/consultation-theme-taxonomy.md:20,75,138,140` / `docs/product/meaning-translation-mapping.md:142,143` / `docs/product/recommendation-v4-interpreter-contract.md:95` |
| E9-2 | 現在仕様を知る際は Current Source of Truth → Final/latest audit → Intermediate audit → Historical snapshot の順で参照する | update rule | `docs/audit/README.md` §読み方 |
| E9-3 | Compassの月次方向解釈は COMMON DIRECTION（最優先） → MONTHLY FALLBACK → NO_COMMON_DIRECTION の優先順位で解決される | invariant | `docs/product/compass-product-contract.md:369,371,374` §2.2-1 |
| E9-4 | element / birthdate / directionはprimary_reasonを上書きしない | invariant | `docs/analytics/recommendation-score-v2-current-design.md:217` |
| E9-5 | Billing状態の確認だけで送信可否を判断せず、相談APIを通じた判定を優先する | update rule | `docs/product/billing-paywall.md:66` |
| E9-6 | Backend生成値が利用可能な場合、Frontendはそれを優先する | update rule | `docs/core/recommendation-reason-contract.md:260` |
| E9-7 | Level 1（相談）はRecommendationの意味的主軸であり、Level 2 / Level 3はLevel 1を補助し原則としてLevel 1の意味を上書きしない | invariant | `docs/product/concierge-input-architecture.md:53,54,429,434,445`（※Domain README未掲載。H-1） |

---

## F. Duplicate Rule Candidates

同一趣旨のルールが複数のActive正本に存在するもの。**本Phaseでは統合・削除・書き換えを行わない。**

| # | 重複ルール | 出現箇所 | 備考 |
| --- | --- | --- | --- |
| F-1 | 非断定原則（診断・断定・効果保証をしない） | `docs/core/meaning-layer.md:23,121,123`、`docs/core/narrative-guideline.md`、`docs/core/recommendation-reason-contract.md:388`、`docs/product/compass-product-contract.md:622`、`docs/product/history-theme-taxonomy.md:34`、`docs/product/shrine-detail-v3-design.md:156`、`docs/product/visit-reflection-flow.md:311`、`docs/product/recommendation-v4-interpreter-contract.md:25,78`、`docs/knowledge/recommendation-copy-guide.md:97-137`、`docs/knowledge/action-guide.md:111-147`、`docs/knowledge/reflection-guide.md:119-147`、`docs/knowledge/shrine-data-guide.md:91-103` | 最多重複。`narrative-guideline.md`が共通原則の正本と宣言されているが、各文書が個別に再掲している |
| F-2 | 方位一致をRecommendation Reasonの主理由にしない | `docs/core/recommendation-reason-contract.md:236,248,387`、`docs/product/compass-product-contract.md:584`（同契約を明示的に継承と記載） | Compass側は「そのまま適用する」と参照しており、意図的な継承 |
| F-3 | frontend / mobileへ判定ロジックを重複実装しない | `docs/core/architecture.md:103`、`docs/core/recommendation-architecture.md:165`、`docs/product/consultation-theme-taxonomy.md:228`、`docs/product/visit-reflection-flow.md:45`、`docs/product/action_suggestion_v4.md:46`、`docs/product/recommendation-v4-interpreter-contract.md:26` | `recommendation-architecture.md:165`は`architecture.md`からの継承と明記 |
| F-4 | Frontend / MobileがBackendの観測用Scoreを独自に順位へ反映しない | `docs/core/architecture.md:188`、`docs/core/recommendation-architecture.md:207` | 後者は前者の継承と明記 |
| F-5 | `direction_reference`を再計算しない | `docs/core/architecture.md:94`、`docs/core/direction-response-contract.md` §責務、`docs/ops/direction-fail-safe.md` §原則 | `direction-response-contract.md`はDomain README未掲載（H-1） |
| F-6 | 自由入力を相談解釈の正本とし、矛盾時は自由入力を優先する | `docs/product/consultation-theme-taxonomy.md:20,75,138,140`、`docs/product/meaning-translation-mapping.md:24,64,142,143`、`docs/product/recommendation-v4-interpreter-contract.md:95`、`docs/product/concierge-first-final-spec.md:44` | 4文書で同一ルールを再掲 |
| F-7 | JWT / Tokenを`localStorage`へ保存しない | `docs/core/authentication-flow.md:103` §禁止事項、`docs/core/runtime-security-baseline.md:55` | 後者は前者を正本と明記した上で原則のみ再掲 |
| F-8 | 課金状態・権限をFrontendだけで確定しない | `docs/core/architecture.md:299`、`docs/core/authentication-flow.md` §禁止事項、`docs/product/billing-paywall.md:50` | |
| F-9 | Map / SearchをPremiumの主価値にしない | `docs/product/premium-experience.md:72,148`、`docs/product/shrine-detail-layer.md:98`、`docs/product/mobile-user-flow.md:191` | `mobile-user-flow.md:197`は「既存文書の方針と実装は一致（MATCHES）」として重複を自認 |
| F-10 | Snapshotを後から暗黙に再計算しない | `docs/core/architecture.md:170`、`docs/core/recommendation-reason-contract.md:325,386` | |
| F-11 | 日盤・時盤をMVP対象外／追加禁止とする | `docs/ops/direction-fail-safe.md`（原典）、`docs/product/compass-product-contract.md:520`、`docs/product/compass-mvp-runtime-contract.md:49`、`docs/analytics/direction-events.md:44`、`docs/analytics/direction-analytics-dashboard.md:90` | 原典がDomain README不在領域にある（H-2） |
| F-12 | Analytics禁止属性（PII等）をEvent名を問わず送信しない | `docs/analytics/direction-events.md:20,22`、`docs/analytics/mobile-search-events.md:43,45`、`docs/analytics/mobile-reflection-to-consultation.md:23,25`、`docs/analytics/consultation-history-events.md:112,114`、`docs/analytics/direction-analytics-data-quality.md:49`、`docs/ops/direction-fail-safe.md:30` | 6文書で同種の禁止リストを個別管理。`direction-analytics-data-quality.md`は`DIRECTION_ANALYTICS_FORBIDDEN_KEYS`で一元管理と記載 |
| F-13 | 内部タグ・内部変数名を表示しない | `docs/core/recommendation-reason-contract.md:383`、`docs/knowledge/recommendation-copy-guide.md:144`、`docs/knowledge/shrine-profile-spec.md:175`、`docs/product/kami-musubi-experience-design.md:88` | |
| F-14 | Runtime情報を神社プロフィールへ保存しない | `docs/knowledge/shrine-profile-spec.md:174,203,206,519`、`docs/knowledge/shrine-data-guide.md:134`、`docs/knowledge/recommendation-copy-guide.md:56` | `shrine-profile-spec.md`内でも4箇所で再掲 |
| F-15 | 出典必須・AI生成のみで事実を確定しない | `docs/knowledge/shrine-data-guide.md:148`、`docs/knowledge/shrine-knowledge-contract.md:248-252`、`docs/knowledge/recommendation-copy-guide.md:58`、`docs/knowledge/shrine-profile-spec.md:344,345` | |
| F-16 | 「正確な物理挙動は実装コードとテストを最終的な正本とする」 | Active正本ほぼ全文書のblockquote冒頭（core 12件、product 15件、analytics 12件ほか） | 定型句。Fixed Rules化の際は1件へ集約可能な候補 |
| F-17 | 「TODO、PR計画、実装進捗、テスト手順、作業履歴は本書へ記載しない」 | `docs/product/`のActive正本ほぼ全件（`consultation-theme-taxonomy.md:250`、`history-theme-taxonomy.md:379`、`meaning-translation-mapping.md:532`、`recommendation-v4-interpreter-contract.md:337`、`action_suggestion_v4.md:364`、`visit-reflection-flow.md:576`、`journey-timeline-design.md:598`、`premium-experience.md:229`、`billing-paywall.md:157`、`mobile-user-flow.md:284`ほか）、`docs/analytics/`のActive正本複数 | 定型句。同上 |
| F-18 | Recommendation可能条件／Readinessの正本を`docs/core/recommendation-readiness.md`とする委譲 | `docs/knowledge/shrine-profile-spec.md:28,102,196,219,366,552,691`、`docs/knowledge/shrine-data-guide.md:506,526,609`、`docs/knowledge/shrine-knowledge-contract.md:102`、`docs/core/recommendation-reason-contract.md:423` | 同一文書内での多重再掲を含む。参照先の責務が変更済みである点はG-5参照 |
| F-19 | Recommendation順位を単独で決定しない（補助レイヤー宣言） | `docs/core/meaning-layer-connection.md:118`、`docs/product/meaning-translation-mapping.md:58,428`、`docs/product/action_suggestion_v4.md:33`、`docs/product/recommendation-v4-interpreter-contract.md:224` | |
| F-20 | 相談テーマ一覧・カテゴリ名をFrontend/Backend/Analyticsで独自に重複管理しない | `docs/product/consultation-theme-taxonomy.md:200,247`、`docs/product/meaning-translation-mapping.md:276`、`docs/product/history-theme-taxonomy.md:376` | |

---

## G. Conflicts / Stale References

**本Phaseでは修正しない。記録のみ行う。**

### G-1. `docs/README.md`とDomain READMEの分類差分（既知の確認ポイント）

| # | 対象 | `docs/README.md`の扱い | Domain READMEの扱い | 文書自身のStatus | 判定 |
| --- | --- | --- | --- | --- | --- |
| G1-1 | `docs/product/pricing.md` | §💳 Premium・課金の**現行案内に掲載**（「Free / Premiumの価値境界と価格表現」） | **Archive**（`premium-experience.md`へ統合済み） | Archive | **CONFLICT**。Domain README + 自己Statusを優先し、本書C章でArchiveとして除外した |
| G1-2 | `docs/product/card-visibility-renderer-split.md` | §📚 Reference Documents / Concierge UIに掲載 | **Archive**（`concierge-card-architecture.md`へ統合済み） | Archive | **CONFLICT**。C章でArchiveとして除外 |
| G1-3 | `docs/core/auth-flow.md` | §🧭 全体設計/認証・通信 および §🔐 認証・通信で`authentication-flow.md`と並列に現行参照として掲載 | **Reference** | Reference | **CONFLICT**。B章でReferenceとして除外 |
| G1-4 | `docs/product/journey-timeline-design.md` | §📚 Reference Documents / Premium・Journeyに掲載 | **正本** | Active | **CONFLICT**。Domain READMEを優先しA章へ掲載 |
| G1-5 | `docs/product/reflection-timeline-design.md` | §🏮 神社詳細・参拝・記録の**現行案内に掲載** | **Reference** | Reference | **CONFLICT**。B章でReferenceとして除外 |
| G1-6 | `docs/product/monetization-flow-design.md` | §💳 Premium・課金の現行案内**および**§📚 Reference Documentsの**両方に掲載** | Reference | Reference | **CONFLICT**（`docs/README.md`内部の二重掲載）。`docs/product/README.md` §更新ルール「同一文書を複数カテゴリへ重複掲載しない」にも抵触 |

### G-2. `docs/README.md`のCore正本一覧の網羅漏れ・重複

| # | 事象 |
| --- | --- |
| G2-1 | `docs/README.md` §🧭 Core Documents（正本）は、`docs/core/README.md` §Activeが列挙する13文書のうち `desktop-development-contract.md` / `runtime-security-baseline.md` / `recommendation-architecture.md` / `openapi-contract-governance.md` の4件を掲載していない |
| G2-2 | `docs/core/direction-response-contract.md`（自己Status: Active）は`docs/README.md`・`docs/core/README.md`のいずれにも掲載がない（H-1と重複） |
| G2-3 | `docs/README.md` §Core Documents内で `core/architecture.md` と `core/roadmap.md` が同一セクション内に2回ずつ掲載されている（「主要な正本は以下である」と「まず読むべき正本文書です」） |
| G2-4 | `docs/README.md` §🤖 AI / LLM は `llm/overview.md` を「（将来追加予定）」としているが、**`docs/llm/overview.md`は既に存在する**（Status header無し、Domain README無し） |

### G-3. 文書自身のStatusとDomain README分類の不一致

| # | 対象 | 文書自身のStatus | Domain READMEの分類 | 判定 |
| --- | --- | --- | --- | --- |
| G3-1 | `docs/product/direction-ranking-design.md` | **Active** | Reference（`docs/product/README.md`） | **CONFLICT**。`docs/README.md`もReference扱い。Domain READMEを優先しB章へ |
| G3-2 | `docs/knowledge/evidence-foundation-shared-contract.md` | **Active**（PR-F1〜F5 + G1） | Reference（`docs/knowledge/README.md`） | **CONFLICT**。Domain READMEを優先しB章へ |
| G3-3 | `docs/core/desktop-development-contract.md` | **Status header無し** | Active（`docs/core/README.md`） | 不一致（欠落）。Domain README分類を採用しA章へ |
| G3-4 | `docs/knowledge/`のActive正本7件（`shrine-profile-spec.md` / `shrine-data-guide.md` / `shrine-position-contract.md` / `recommendation-copy-guide.md` / `action-guide.md` / `reflection-guide.md` / `glossary.md`）および`docs/knowledge/README.md`自身 | **Status header無し** | 正本（`docs/knowledge/README.md`） | 不一致（欠落）。`docs/core/recommendation-architecture.md:71`が同事象を既に記録し「Statusヘッダ追加は変更範囲外」としている |

### G-4. Active正本間の正本指定の矛盾

| # | 事象 |
| --- | --- |
| G4-1 | `docs/core/architecture.md:190`は Recommendation ScoreのSignal / Component / Weight / 計算式の正本として `docs/analytics/recommendation-score-v3-design.md` を指定している。しかし同文書の自己Statusは **Reference** であり、`docs/analytics/README.md`も **Reference** に分類している。**CONFLICT**。`docs/core/recommendation-architecture.md:73` が同じ不整合を既に記録し「本書の変更範囲外とし、母艦判断項目へ記録する」としている |
| G4-2 | `docs/core/recommendation-architecture.md:205` も Scoring段階の正本データとして同文書を指定しており、G4-1の不整合を継承している |
| G4-3 | `docs/README.md` §🧭 全体設計/API契約は `openapi.yaml` を参照している。しかし `docs/core/openapi-contract-governance.md:88,111` は `docs/openapi.yaml` を「**正本ではない（Reference候補）**」「現行API契約の正本として扱わない」と規定している。**CONFLICT** |
| G4-4 | `docs/analytics/direction-analytics-dashboard.md` は `docs/analytics/README.md` §Active に掲載されているが、自己Statusは「Proposed Dashboard Configuration / Implementation Active」であり、Dashboard構成部分は提案段階である。Active契約と提案が同一文書に混在している |

### G-5. 文書と実装の矛盾（Eligibility Filter）

| # | 事象 |
| --- | --- |
| G5-1 | `docs/core/recommendation-readiness.md`（Active）§Runtime / Governance Boundaryは「**Candidate Generationは座標・住所の有無とtestフィクスチャ除外のみを条件とし、Knowledge完全性を候補除外に使っていない**」と記載する。`docs/core/recommendation-architecture.md:193`（Active）も Eligibility Filter段階について「**現状は明示的な除外を行わない**」と記載する。<br>一方 `docs/knowledge/recommendation-eligibility-contract.md`（自己Status: Active、**Domain README未掲載**）は「Recommendation候補になれるのはusableなDeity FactまたはHistory Factを最低1件持つShrineだけ」と規定し、`backend/temples/services/concierge_chat_candidates.py`（`is_recommendation_eligible()` / `filter_recommendation_eligible_candidates()`、`build_chat_candidates()`内で適用）に実装されていることを確認した。<br>**CONFLICT**：Knowledge由来の候補除外が実装済みであるのに対し、Core側Active正本2件は「除外していない」と記載している。本書は解決しない |
| G5-2 | G5-1に関連し、`docs/core/recommendation-readiness.md` §Mother Ship Decisions Requiredは「情報不足神社を候補から除外すべきか」をProduct未決事項として残しているが、実装上の除外は既に稼働している |

### G-6. Stale References（参照先の不在・古い記載）

| # | 参照元 | 事象 |
| --- | --- | --- |
| G6-1 | `docs/README.md` §🗂 Audit / Archive | `docs/archive/` を保存先として案内しているが、**`docs/archive/`ディレクトリは存在しない** |
| G6-2 | `docs/audit/README.md`（冒頭・§Major Audit Chain Index・§更新ルール） | 「`docs/audit/`配下**91文書**」と記載しているが、現在の`docs/audit/*.md`は**394件**である |
| G6-3 | `docs/knowledge/shrine-knowledge-contract.md:102` | `docs/core/recommendation-readiness.md` を「**Readiness Level本体**」として参照しているが、同書はLevel 0〜3を`[Superseded]`として明示的に不採用としており、Capability Setへ移行済みである |
| G6-4 | `docs/knowledge/shrine-profile-spec.md:389,711` | 「Readiness Level」を現行概念として参照している（同上の理由でstale） |
| G6-5 | `docs/knowledge/shrine-data-guide.md:578` | 「どのLevelまで利用可能かを明示し」と記載しており、Superseded概念を前提としている |
| G6-6 | `docs/core/openapi-contract-governance.md`（分類表） | `docs/openapi_generated.yaml` を分類対象として列挙しているが、**当該ファイルは存在しない**（規定内容「一切使用しない」とは矛盾しない） |
| G6-7 | `docs/product/mobile-user-flow.md:272` | 監査根拠として `docs/audit/mobile-user-flow-inventory.md`（commit `0610dfd9`時点）を全編で引用しており、現行実装との差分が未検証のまま残る |
| G6-8 | 用語衝突 | `docs/product/concierge-input-architecture.md` の「Level 1 / 2 / 3」（Concierge Input Level）と、Supersededな「Readiness Level 0〜3」、および `docs/product/concierge-filter-area.md:69-72` の「Level 2 / Level 3-A/B/C」が同名概念として混在している。`concierge-input-architecture.md:57,222` は「同一概念として扱わない」と自ら明記しているが、`docs/`全体での用語整理は行われていない |

### G-7. 既知の確認ポイントに対する監査結果

| 確認ポイント | 結果 |
| --- | --- |
| Recommendation Readiness旧Level 0〜3を現行ルールとして扱わないこと | **遵守**。`docs/core/recommendation-readiness.md` §旧設計（Superseded）に該当。E章から除外済み。ただしG6-3〜G6-5のstale参照が3文書に残存 |
| `docs/README.md`と各Domain READMEの分類差分 | **6件のCONFLICTを検出**（G1-1〜G1-6）、加えて網羅漏れ4件（G2-1〜G2-4） |
| `pricing.md`等、上位案内には残るがDomain READMEでArchiveの文書 | **2件検出**（G1-1 `pricing.md`、G1-2 `card-visibility-renderer-split.md`）。いずれもC章でArchiveとして除外し、Current Source of Truthとして扱っていない |

---

## H. UNRESOLVED

推測でActive扱いしない文書、およびAuthority判定が確定できない事項。

### H-1. Status headerはあるがDomain READMEに掲載がない文書（分類不能）

Domain READMEがAuthority Sourceであるため、**推測でActiveへ昇格させない**。Phase 2の判断対象。

| path | 自己Status | 備考 |
| --- | --- | --- |
| `docs/core/direction-response-contract.md` | Active | `docs/core/architecture.md:95`が委譲先として明示参照。Core READMEの読む順番・Active表のいずれにも不在 |
| `docs/product/compass-product-direction-decision.md` | `DECIDED — MOTHER SHIP PRODUCT DIRECTION` | D-1参照。実装・Active正本から多数参照される決定記録 |
| `docs/product/concierge-input-architecture.md` | Active（Architecture Decision） | 1,961行。Level 1/2/3責務、Signal属性モデル、Level間優先順位を規定 |
| `docs/product/history-recommendation-navigation-design.md` | Active | 自ら「正本文書」と宣言 |
| `docs/product/recommendation-signal-authority.md` | Active | Recommendation Signalの責務と競合時の優先順位を「設計判断として固定する正本」と宣言 |
| `docs/product/recommendation-v4-frontend-adapter-contract.md` | Active | `docs/core/recommendation-reason-contract.md:360`が表示契約の参照先として明示指定 |
| `docs/product/recommendation-result-information-architecture.md` | Draft（設計監査のみ） | Draftのため現行ルール抽出対象外 |
| `docs/product/recommendation-result-observation-policy.md` | Status header無し | 分類不能 |
| `docs/product/deep-dive-answer-generation-contract.md` | Status header無し | 分類不能。関連実装は`docs/audit/deep-dive-non-llm-runtime-alignment.md`を参照している（D-3） |
| `docs/knowledge/recommendation-eligibility-contract.md` | Active（Shared Recommendation Eligibility） | **実装稼働中**。G5-1のCONFLICT当事者 |
| `docs/knowledge/recommendation-evidence-review-contract.md` | 「Contract definition only」 | 分類不能 |
| `docs/knowledge/shrine-expansion-candidate-master-contract.md` | `ACTIVE`（Effective from 2026-09-10、Schema version 1.2） | 独自Status語彙。Domain README未掲載 |
| `docs/analytics/compass-analytics-contract.md` | Active | Domain README未掲載 |
| `docs/analytics/compass-posthog-query-contract.md` | Active（`no_common_direction` runtimeへ整合済み） | Domain README未掲載 |

### H-2. Domain READMEも上位READMEからの参照も存在しない文書

Authority Sourceが皆無。Active / Reference / Archiveのいずれとも判定できない。

| path | 自己Status | 備考 |
| --- | --- | --- |
| `docs/ops/direction-fail-safe.md` | なし | ただし`compass-product-contract.md:520`・`compass-mvp-runtime-contract.md:49,429`（いずれもActive正本）が禁止事項・縮退契約の**根拠**として明示参照している。実質的な契約文書だが分類が存在しない |
| `docs/ops/guest-data-retention.md` | なし | 90日Retentionの運用規定。「Privacy Policy第10項と現状不一致」「定期実行未設定」と自記 |
| `docs/ops/production-bff-hardening.md` | なし | |
| `docs/design/premium-meaning-ui-direction.md` | なし（本文に「design decision + implementation planning」） | |
| `docs/llm/overview.md` | なし | `docs/README.md`は「将来追加予定」と記載（G2-4） |
| `docs/concierge/README.md` `docs/concierge/boundary.md` `docs/concierge/normalization.md` | なし | `docs/concierge/`ディレクトリ自体がどのREADMEからも参照されていない |
| `docs/meaning-layer/*.md`（5件） | 未確認 | 同上。`docs/core/meaning-layer.md`とのディレクトリ名衝突あり |
| `docs/mobile/*.md`（7件） | 未確認 | 同上 |
| `docs/ui/concierge-result-wireframe.md` `docs/triage/production-500-triage.md` `docs/runbooks/render-featureusage-recovery.md` `docs/migration-audit/temples-prod-gap.md` | 未確認 | 同上 |

> `docs/meaning-layer/`(5) `docs/mobile/`(7) `docs/ui/`(1) `docs/triage/`(1) `docs/runbooks/`(1) `docs/migration-audit/`(1) `docs/concierge/`(3) `docs/llm/`(1) の8ディレクトリ（計20文書）は、
> タスクの対象領域指定（core / product / knowledge / analytics / infra / ci / ops / design + docs/README.mdが参照する領域）のいずれにも該当せず、
> `docs/README.md`からの参照も存在しない。**本監査では内容を精査していない。** Phase 2で領域スコープの再確認が必要。

### H-3. Domain README不在領域のAuthority

`docs/infra/` `docs/ci/` `docs/ops/` `docs/design/` の4領域にはDomain READMEが存在しない。
A-5に掲載した文書は「Current Source of Truth候補」に留まり、Authority判定1（Domain READMEのActive分類）を
満たしていない。特に以下が未確定である。

- `docs/ops/direction-fail-safe.md` が Active正本相当か否か（Active正本2件が契約根拠として参照している）
- `docs/ci/testing_policy.md` が Active正本相当か否か（`runtime-security-baseline.md:126`が正本指定している）
- `docs/ops/production-smoke-log.md` は時点記録であり、他のops文書と分類が異なる

### H-4. Status語彙の不統一

`docs/audit/README.md` §Status Vocabulary Contractが定義する語彙（`Active Tracking` / `Reference` /
`Audit / Historical` / `Audit / Superseded` / `Archive` / `Review`）は、同書自身が
「91文書全件への一括適用は本PRの対象外」としている。現時点で確認できる語彙の揺れ:

- `Active` / `Active / Contract` / `Active / Quality Contract` / `Active（Architecture Decision）` /
  `Active（Shared Recommendation Eligibility）` / `Active（Navigation Only）` /
  `Proposed Dashboard Configuration / Implementation Active` / `Active — Evaluation Framework only`
- `DECIDED — MOTHER SHIP PRODUCT DIRECTION` / `ACTIVE`（大文字・Effective from付き）
- `KNOWLEDGE_IMPORT_READY_WITH_LIMITATIONS` 等のSCREAMING_SNAKE_CASE独自Status（`docs/audit/`配下に多数）

Fixed Rules確定前に語彙の正規化方針が必要だが、**本Phaseでは決定しない**。

### H-5. Mother Ship未決事項（Active正本が明示的に母艦判断へ差し戻しているもの）

これらは「未確定事項」としてE章から除外した。Phase 2でFixed候補へ含めないことの根拠として記録する。

| 未決事項 | 記録元 |
| --- | --- |
| 情報不足神社をRecommendation候補から除外すべきか（Product方針） | `docs/core/recommendation-readiness.md` §Mother Ship Decisions Required |
| 105社Rollout時の品質最低条件（どのCapabilityを必須とするか） | 同上 |
| `docs/openapi.yaml`の移行方針（案A〜D） | `docs/core/openapi-contract-governance.md:113` |
| `backend/schema.yml`の生成経路特定と正本採否 | `docs/core/openapi-contract-governance.md:143` |
| Mobile先行実装に伴うPhase順序変更の可否（`MOTHER_SHIP_DECISION_REQUIRED`） | `docs/core/roadmap.md:431` |
| Compass Free/Premium境界の最終決定 | `docs/product/compass-product-contract.md` §12 |
| Shrine Knowledge ModelのModel選択・Pilot対象・enum最終確定 | `docs/knowledge/shrine-knowledge-contract.md:7` |
| `deity` / `shrine_history`の必須化タイミング | `docs/knowledge/shrine-profile-spec.md:570,582` |
| Source confidenceの算出方式・利用方法 | `docs/knowledge/shrine-knowledge-contract.md:482,495` |
| 具体的な料金、請求周期、プラン構成 | `docs/product/premium-experience.md:156,183` |
| Design Tokenの保留事項（Web / Mobile実値統一の可否ほか） | `docs/design/design-token.md` §保留事項 |
| Web地図の未設定運用時の文言変更、Native地図の扱い、人気神社セクションの扱い、returnTo設計要件 | `docs/product/mobile-user-flow.md:143,147,158,204` §20 未確定事項 |

---

## I. Next Phase Input

Phase 2（Fixed Rules候補抽出）への引き渡し内容。

### I-1. 確定した入力

| 項目 | 件数 | 所在 |
| --- | ---: | --- |
| Current Source of Truth（Domain README確定分） | 58文書（core 14 / product 20 / knowledge 9 / analytics 15、うちDomain README自身4件を含む） | A-1〜A-4 |
| Current Source of Truth候補（Domain README不在領域） | 10文書 | A-5 |
| 除外したReference文書 | 27文書 | B |
| 除外したArchive文書 | 21文書 | C |
| Audit / Decision Record例外候補 | Decision Record 1件 + Active audit 3件 + 実装参照 13経路 + 正本委譲 9件 | D |
| 現行ルール候補 | 9カテゴリ・**193件**（E1 8 / E2 19 / E3 20 / E4 24 / E5 78 / E6 17 / E7 5 / E8 15 / E9 7） | E |
| 重複ルール候補 | 20グループ | F |
| CONFLICT | 15件（G1×6、G3×2、G4×4、G5×2、G6-3〜G6-5を1グループとして1件） | G |
| Stale Reference | 8件 | G-6 |
| UNRESOLVED文書 | 14件（H-1）+ Authority不在10件（H-2）+ 領域外20文書（H-2） | H |

### I-2. Phase 2で先に解消が必要な前提（Fixed Rules確定の阻害要因）

優先度順。いずれも本Phaseでは解決していない。

1. **G5-1（Eligibility Filterの文書 / 実装矛盾）**
   Core側Active正本2件（`recommendation-readiness.md` / `recommendation-architecture.md`）が
   「Knowledge由来の候補除外は行っていない」と記載する一方、`recommendation-eligibility-contract.md`と
   実装は除外を行っている。Recommendation領域のFixed Rules（E3-7 / E3-9 / E4-4）は
   この矛盾が解消されるまで確定できない。

2. **H-1（Domain README未掲載のActive宣言文書 14件）**
   特に`recommendation-eligibility-contract.md` `recommendation-signal-authority.md`
   `concierge-input-architecture.md` `recommendation-v4-frontend-adapter-contract.md`
   `compass-product-direction-decision.md` は、他のActive正本または実装から契約として参照されている。
   Domain READMEへの掲載可否（＝Authority付与）を先に決める必要がある。

3. **G4-1（Score正本のReference指定矛盾）**
   `architecture.md`がScore正本として指定する文書がReference分類である。
   Recommendation Score関連のFixed Rules（E5-35など）の根拠が不安定。
   なお本矛盾は`docs/core/recommendation-architecture.md:73`で既に母艦判断項目として記録済み。

4. **H-3（Domain README不在領域4つ）**
   `docs/ops/direction-fail-safe.md`は日盤・時盤禁止（F-11）とfail-safe契約（E6-1〜E6-3）の**原典**でありながら、
   Authority判定1を満たしていない。Compass関連のFixed Rulesが不安定な基盤の上に立っている。

5. **G1-1〜G1-6（`docs/README.md`の分類差分6件）**
   `docs/README.md`が現行案内としてArchive文書（`pricing.md`）を掲載し続けている。
   読み手が誤ってArchiveを現行正本として参照するリスクが残る。

### I-3. Phase 2での作業単位（提案。本Phaseでは確定しない）

| Phase | 作業 | 入力 |
| --- | --- | --- |
| 2-A | H-1の14文書についてDomain README掲載可否を決定（Authority確定） | H-1 |
| 2-B | H-3の4領域についてDomain README設置またはAuthority委譲方針を決定 | A-5、H-3 |
| 2-C | G5-1の文書 / 実装矛盾の意図した仕様を確認（E1-1の手順に従う） | G-5 |
| 2-D | G1 / G2 / G3 / G4の分類差分・正本指定矛盾の解消方針を決定 | G-1〜G-4 |
| 2-E | 2-A〜2-Dの結果を反映したうえで、E章の193件からFixed Rules候補を抽出 | E |
| 2-F | F章の20グループについて統合先正本を決定（特にF-16 / F-17の定型句、F-12の禁止属性リスト） | F |
| 2-G | D章の例外候補について、Active正本への昇格 / audit据え置き / 内容の正本側への移設を判断 | D |
| 2-H | H-2の領域外20文書について監査スコープの要否を判断 | H-2 |

### I-4. 本Phaseで意図的に行わなかったこと

- ルール変更、文書修正、実装変更、設定・DB変更
- 分類（Active / Reference / Archive）の変更
- 矛盾の解決
- 重複ルールの統合・削除・書き換え
- Status headerの追加・修正
- Fixed Rulesの確定
- 分類不能文書の推測によるActive扱い
- `docs/audit/*`のCurrent Source of Truthへの昇格

---

## 関連ドキュメント

- `docs/README.md`
- `docs/core/README.md`
- `docs/product/README.md`
- `docs/knowledge/README.md`
- `docs/analytics/README.md`
- `docs/audit/README.md`
