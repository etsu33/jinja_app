# docs/（設計・運用ドキュメント）

このディレクトリは **AI参拝ナビの設計・運用・実装判断の根拠**を集約します。  
「どこに何が書いてあるか」を最短で辿れることを目的にしています。

## 🧭 Core Documents（正本）

まず読むべき正本ドキュメントです。

- `core/architecture.md`
  - システム構成・責務分離・BFF/API方針

- `core/roadmap.md`
  - 開発優先順位・MVP進捗・今後の実装順

- `core/narrative-guideline.md`
  - AIが断定しないための文言・意味づけ方針

- `core/meaning-layer.md`
  - 神社を「意味ある場所」として扱うための意味構造

- `core/recommendation-readiness.md`
  - Recommendation品質・Coverage・Readiness判定の正本

---

## 🧭 全体設計（まずここ）

- **Architecture・システム境界**

  - `core/architecture.md`

- **Recommendation品質**

  - `core/recommendation-readiness.md`

- **認証・通信**

  - `auth-flow.md`

  - `authentication-flow.md`

- **API契約**

  - `openapi.yaml`

  - Backendの実装・起動・運用は `../backend/README.md`

---

## 🔐 認証・通信

Webは、FrontendからBackend APIを直接呼び出さず、Next.jsの`/api` Route Handlerを経由する。

認証の現行責務は以下を参照する。

- `auth-flow.md`

- `authentication-flow.md`

---

## 🤖 AI / LLM

- 実装は `backend/temples/llm/` 配下  
- 方針：自由会話はしない。1回解析して構造化し、推薦・距離計算・フォールバックはサーバ側で決める。

- Concierge chat 仕様（LLM ON/OFF定義、contract fields、ログの見方）
  - `concierge_spec.md`

（必要になったら追加予定）
- `llm/overview.md`（予定）

---

## 🧪 開発・検証

- **Test方針**

  - `ci/testing_policy.md`

- **本番Smoke Check**

  - `ops/production-smoke-checklist.md`

検証結果の時点記録は`ops/production-smoke-log.md`で管理する。

---

## 🚀 インフラ / デプロイ

- **環境変数・Infra方針**

  - `infra/env_policy.md`

- **Render起動契約**

  - `infra/render-startup.md`

---

## 🎨 UI / UX メモ


---

## 🗺 ロードマップ / TODO

- 開発 TODO / 優先度  
  - `core/roadmap.md`

## 🧭 Concierge（仕様）

- Concierge仕様（LLMモード / Contract / 運用）
  - `concierge_spec.md`
