# docs/（設計・運用ドキュメント）

このディレクトリは **AI参拝ナビの設計・運用・実装判断の根拠**を集約します。
「どこに何が書いてあるか」を最短で辿れることを目的にしています。

---

## 🧭 Core Documents（正本）

Core文書の読む順番、Active / Reference分類、責務および委譲関係は以下を参照する。

- `core/README.md`
  - Core文書全体の入口

主要な正本は以下である。

- `core/architecture.md`
  - システム全体構造、責務分離および依存関係

- `core/roadmap.md`
  - 開発フェーズ、実装順序、ゴールおよび完了条件

- `core/authentication-flow.md`
  - Web認証アーキテクチャとFrontend・BFF・Backendの責務

- `core/concierge-spec.md`
  - Concierge入力、LLM利用、API基本契約および運用上の保護条件

- `core/meaning-layer.md`
  - Meaning Layerの思想、目的および非断定原則

- `core/recommendation-readiness.md`
  - Recommendation品質、CoverageおよびReadiness判定

- `core/recommendation-reason-contract.md`
  - Recommendation ReasonのInput / Output / 保存 / 表示 / 互換責務

まず読むべき正本文書です。

- `core/architecture.md`
  - システム構成・責務分離・BFF/API方針

- `core/roadmap.md`
  - 開発優先順位・MVP進捗・今後の実装順

- `core/narrative-guideline.md`
  - AIが断定しないための文言・意味づけ方針

- `core/meaning-layer.md`
  - 神社を「意味ある場所」として扱うための意味構造

- `core/meaning-layer-connection.md`
  - Meaning LayerとConsultation Interpretation / Composer / Recommendationの接続責務

- `core/recommendation-readiness.md`
  - Recommendation品質・Coverage・Readiness判定の正本

- `core/recommendation-reason-contract.md`
  - Recommendation ReasonのInput / Output / 保存 / 表示 / 互換責務

---

## 🧭 全体設計（まずここ）

### Architecture・システム境界

- `core/architecture.md`

### Recommendation品質

- `core/recommendation-readiness.md`

### 認証・通信

- `core/auth-flow.md`
- `core/authentication-flow.md`

### API契約

- `openapi.yaml`

Backendの実装・起動・運用は `../backend/README.md` を参照する。

---

## 🔐 認証・通信

WebはFrontendからBackend APIを直接呼び出さず、Next.js の `/api` Route Handler を経由する。

認証の現行責務は以下を参照する。

- `core/auth-flow.md`
- `core/authentication-flow.md`

---

## 🤖 AI / LLM

- 実装は `backend/temples/llm/` 配下
- 方針：自由会話は行わず、一度構造化した上で推薦・距離計算・フォールバックをサーバ側で決定する。

### Concierge

- `core/concierge-spec.md`
  - LLM ON/OFF、Contract Fields、ログ仕様

（将来追加予定）

- `llm/overview.md`

---

## 🧪 開発・検証

### Test方針

- `ci/testing_policy.md`

### 本番確認

- `ops/production-smoke-checklist.md`

検証結果は `ops/production-smoke-log.md` で管理する。

---

## 🚀 インフラ / デプロイ

### 環境変数

- `infra/env_policy.md`

### Render

- `infra/render-startup.md`

---

## 🧭 プロダクト・体験設計

現行のユーザー体験、画面責務および機能契約は以下を参照する。

- `product/kami-musubi-experience-design.md`
  - 相談・推薦・参拝・振り返りを一本の体験として接続する最上位体験設計

- `product/README.md`
  - Concierge First、Mode、相談テーマ、Meaning Translation、Visit / Reflection、Action Suggestionの入口

- `core/concierge-spec.md`
  - Conciergeの入力、LLMモード、API契約および運用ログ

- `product/recommendation-v4-interpreter-contract.md`
  - Consultation InterpreterのInput / Output契約

## 🎨 Design・UI基盤

Web / Mobile共通のDesign Token、UI基盤および視覚言語に関する正本文書は以下を参照する。

- `design/design-token.md`
  - Primitive / Semantic / Platform Themeの3層構造
  - Semantic Tokenの責務と参照原則
  - Web / MobileのPlatform Theme差分方針
  - Component Tokenの優先順位
  - 段階的な移行順序とGovernance

監査時点の現行値、重複実装およびWeb / Mobile比較の根拠は以下を参照する。

- `audit/design-token-phase6-audit.md`
  - Design Token Phase 6の棚卸し・比較・不整合記録

---

## 💳 Premium・課金

Premiumの価値、体験差、課金判定および収益導線は以下を参照する。

- `product/billing-paywall.md`
  - 課金状態、利用可否、Paywall判定およびServer責務

- `product/pricing.md`
  - Free / Premiumの価値境界と価格表現

- `product/premium-experience.md`
  - Free / Premiumの体験境界、保存・履歴・比較の原則

- `product/monetization-flow-design.md`
  - Premium提示タイミング、CTA、購入後復帰、解約方針および継続計測

---

## 🏮 神社詳細・参拝・記録

神社詳細、参拝後導線および記録体験は以下を参照する。

- `product/shrine-detail-layer.md`
  - 神社詳細の Public / Context / Personal Layer

- `product/shrine-detail-v3-design.md`
  - 神社詳細 v3 のUX、AnalyticsおよびPremium接続

- `product/shrine-submission-flow.md`
  - 神社追加、重複候補および投稿後導線

- `product/reflection-timeline-design.md`
  - 相談・参拝・振り返りを時系列で蓄積する体験設計

---

## 📚 Reference Documents

以下は現行仕様の補足、設計背景または運用上の参照資料である。

現行判断では、各文書が指定するActive文書、実装コードおよびテストを優先する。

### Recommendation・Analytics

- `analytics/analytics-payload-audit.md`
- `analytics/recommendation-score-v3-design.md`
- `knowledge/recommendation-v4-copy-guideline.md`
- `product/direction-ranking-design.md`

### Premium・Journey

- `product/monetization-flow-design.md`
- `product/journey-timeline-design.md`

### Concierge UI

- `product/card-visibility-renderer-split.md`
- `product/concierge-card-architecture.md`
- `audit/concierge-risk-register.md`

### Shrine Detail・Mobile

- `product/shrine-detail-meaning-layer.md`
- `product/mobile-bottom-navigation.md`

---

## 🗂 Audit / Archive

過去の設計判断、監査結果および長期構想は `docs/audit/` および `docs/archive/` に保存する。

例：

- `audit/premium-reference-consolidation-audit.md`
- `audit/premium-plan-design.md`
- `audit/premium-retention-strategy.md`

これらは設計履歴・判断経緯を保持するための文書であり、現行仕様の判断には使用しない。

---

## 🗺 ロードマップ / TODO

開発TODOおよび優先順位は以下を参照する。

- `core/roadmap.md`
