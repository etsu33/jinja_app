# docs/（設計・運用ドキュメント）

このディレクトリは **AI参拝ナビの設計・運用・実装判断の根拠**を集約します。  
「どこに何が書いてあるか」を最短で辿れることを目的にしています。

---

## 🧭 Core Documents（正本）

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

- `auth-flow.md`
- `authentication-flow.md`

### API契約

- `openapi.yaml`

Backendの実装・起動・運用は `../backend/README.md` を参照する。

---

## 🔐 認証・通信

WebはFrontendからBackend APIを直接呼び出さず、Next.js の `/api` Route Handler を経由する。

認証の現行責務は以下を参照する。

- `auth-flow.md`
- `authentication-flow.md`

---

## 🤖 AI / LLM

- 実装は `backend/temples/llm/` 配下
- 方針：自由会話は行わず、一度構造化した上で推薦・距離計算・フォールバックをサーバ側で決定する。

### Concierge

- `concierge_spec.md`
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

- `kami-musubi-experience-design.md`
  - 相談・推薦・参拝・振り返りを一本の体験として接続する最上位体験設計

- `product/README.md`
  - Concierge First、Mode、相談テーマ、Meaning Translation、Visit / Reflection、Action Suggestionの入口

- `concierge_spec.md`
  - Conciergeの入力、LLMモード、API契約および運用ログ

- `recommendation-v4-interpreter-contract.md`
  - Consultation InterpreterのInput / Output契約

---

## 💳 Premium・課金

Premiumの価値、体験差、課金判定および収益導線は以下を参照する。

- `billing-paywall.md`
  - 課金状態、利用可否、Paywall判定およびServer責務

- `pricing.md`
  - Free / Premiumの価値境界と価格表現

- `premium-experience.md`
  - Free / Premiumの体験境界、保存・履歴・比較の原則

- `monetization-flow-design.md`
  - Premium提示タイミング、CTA、購入後復帰、解約方針および継続計測

---

## 🏮 神社詳細・参拝・記録

神社詳細、参拝後導線および記録体験は以下を参照する。

- `shrine-detail-layer.md`
  - 神社詳細の Public / Context / Personal Layer

- `shrine-detail-v3-design.md`
  - 神社詳細 v3 のUX、AnalyticsおよびPremium接続

- `shrine-submission-flow.md`
  - 神社追加、重複候補および投稿後導線

- `reflection-timeline-design.md`
  - 相談・参拝・振り返りを時系列で蓄積する体験設計

---

## 📚 Reference Documents

以下は現行仕様の補足、設計背景または運用上の参照資料である。

現行判断では、各文書が指定するActive文書、実装コードおよびテストを優先する。

### Recommendation・Analytics

- `analytics-payload-audit.md`
- `recommendation-score-v3-design.md`
- `recommendation-v4-copy-guideline.md`
- `direction-ranking-design.md`

### Premium・Journey

- `monetization-flow-design.md`
- `journey-timeline-design.md`

### Concierge UI

- `card-visibility-renderer-split.md`
- `concierge-card-architecture.md`
- `concierge_risk_register.md`

### Shrine Detail・Mobile

- `shrine-detail-meaning-layer.md`
- `mobile-bottom-navigation.md`

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
