# Backend（Django / DRF）

AI参拝ナビのバックエンド実装です。

---

## 技術スタック

- Django 5 + DRF
- PostgreSQL + PostGIS
- JWT（SimpleJWT）
- 画像アップロード（S3予定）

---

## 役割

- 神社 / 御朱印 / お気に入りAPI
- AI参拝ナビ（Concierge）
- ルート計算・位置検索
- 認証・ユーザー管理

---

## 開発・設計ドキュメント

詳細設計・運用ルールは `docs/` 配下に集約しています。

- アーキテクチャ / 認証 → `docs/10_arch_auth_proxy.md`
- API全体概要 → `docs/30_api_overview.md`
- ローカル疎通確認 → `docs/20_smoke_checks.md`
- インフラ / デプロイ → `docs/40_infra_deploy.md`
- ロードマップ → `docs/core/roadmap.md`

---

## ローカル起動

```bash
cd backend
source ../.venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

---

## 環境変数

開発環境では `backend/.env.local` を使用します。

### ファイル構成

| ファイル | 用途 |
|---|---|
| `.env.local` | 開発用。Git管理しない |
| `.env.test` | pytest専用 |
| `.env.example` | サンプル・初期設定 |

### 読み込み順

通常起動:

```text
.env.local
```

pytest実行時:

```text
.env.local
↓
.env.test（上書き）
```

### 運用ルール

- `.env` は使用しない
- `.env.dev` は使用しない
- `.env.local` はGitへコミットしない
- 新しい開発者は `.env.example` をコピーして `.env.local` を作成する

```bash
cp .env.example .env.local
```

---

## BackendテストDB方針

BackendのpytestはPostgreSQL / PostGISを前提に実行します。

SQLiteはBackendテストでは使用しません。

`backend/.env.test` にテスト用の `DATABASE_URL` を定義します。

```bash
DATABASE_URL=postgis://admin:YOUR_LOCAL_DB_PASSWORD@127.0.0.1:5432/jinja_db
USE_SQLITE=0
```

pytest実行時は `backend/.env.local` を読み込み、その後 `backend/.env.test` の設定で上書きします。

pytest実行時に `USE_SQLITE=1` が指定された場合は、誤ってSQLiteへ切り替わらないよう起動時に明示的なエラーとします。

```bash
DATABASE_URL=postgis://admin:YOUR_LOCAL_DB_PASSWORD@127.0.0.1:5432/jinja_db USE_SQLITE=0 pytest temples/tests/api/test_shrine_reflection_api.py temples/tests/services/test_reflection_state_change.py
```

---

## Billing運用契約

### 目的

Frontend、Backend、決済プロバイダ間で、課金状態の正本を一か所に固定する。

### Source of Truth

#### `BILLING_PROVIDER=stub`

環境変数を正本とする。

- `BILLING_STUB_PLAN`: `free` または `premium`
- `BILLING_STUB_ACTIVE`: `0` または `1`

#### `BILLING_PROVIDER=stripe`

`UserProfile`を正本とする。

- `UserProfile.subscription_status`
- `UserProfile.current_period_end`

### API契約

`/api/billings/status/` は以下のキーを返します。

- `plan`
- `is_active`
- `provider`
- `current_period_end`
- `trial_ends_at`
- `cancel_at_period_end`

Frontendが機能判定に使用する値は、次の2項目です。

- `plan`
- `is_active`

`provider` は表示・デバッグ用途とし、UI分岐の根拠には使用しません。

### 実装の入口

- 課金判定: `temples/services/billing_state.py:get_billing_status`
- Premium判定: `is_premium_for_user(user)`
- 推薦上限: `recommend_limit_for_user(user)`
  - Premium: 6件
  - Free: 3件

---

## 神社seedデータ投入

### 対象

- コマンド: `import_shrines_seed`
- 入力ファイル: `temples/data/shrines_seed_clean.json`
- 重複判定キー: `name_jp + address`

### 事前条件

- DBマイグレーションが適用済みである
- 対象環境に `Shrine` テーブルが存在する
- seed JSONが配置済みである

### Dry Run

```bash
python manage.py import_shrines_seed --dry-run
```

期待結果:

- 初回投入前は `created` または `updated` が発生する
- 整合済みの場合は `updated=0`, `skipped=100` になる

### 本実行

```bash
python manage.py import_shrines_seed
```

### 再確認

```bash
python manage.py import_shrines_seed --dry-run
```

期待結果:

- `created=0`
- `updated=0`
- `skipped=100`

### 確認項目

- 神社件数が想定どおりである
- 一覧API、検索、Conciergeで神社を利用できる
- 再実行しても重複作成されない

---

## ステージング環境での投入確認

### 実行順

```bash
python manage.py import_shrines_seed --dry-run
python manage.py import_shrines_seed
python manage.py import_shrines_seed --dry-run
```

### 確認項目

- 1回目のDry Runで差分が検出されるか
- 本実行でエラーが発生しないか
- 2回目のDry Runで `updated=0` になるか

Render無料枠ではShellを利用できないため、環境に応じてMigrationまたはDeploy処理から実行します。

ローカルなどShellを利用できる環境では、次のコマンドで件数を確認できます。

```bash
python manage.py shell -c "from temples.models import Shrine; print(Shrine.objects.count())"
```

### Apple StoreKit backend

The authenticated purchase endpoint is `POST /api/billings/apple/transactions/`
with only `signed_transaction`. Configure App Store Server Notifications V2 to
send `signedPayload` to `POST /api/webhooks/apple/app-store/`.

- `APPLE_STOREKIT_ENVIRONMENTS` defaults to `Production`. Set it to
  `Production,Sandbox` on the backend used by App Review and TestFlight, which
  use Apple Sandbox for in-app purchases. Set it to `Sandbox` for a sandbox-only
  deployment. The existing singular environment variable is a fallback when the
  new variable is unset. See [Apple App Review setup](https://developer.apple.com/help/app-review/before-submitting-for-review/configure-in-app-purchases).
- `APPLE_STOREKIT_ROOT_CERTIFICATES` is a comma-separated list of server-side paths
  to DER-encoded App Store trust roots from [Apple PKI](https://www.apple.com/certificateauthority/).
- `APPLE_STOREKIT_APP_ID` is the numeric App Store ID, required in Production.
  The bundle ID is fixed to `com.morietsu.kamimusubi`. A DB-backed billing provider
  is required to expose real entitlements through the billing resolver.

Apple's [App Store Server Library](https://github.com/apple/app-store-server-library-python)
validates the JWS chain and signature, with online certificate checks enabled.
The API also verifies the inner transaction and any subscription renewal JWS
against the environment verified for the outer notification. Another configured
verifier is tried only when the Apple SDK reports a signed environment mismatch.
Without verification configuration the new endpoints respond with HTTP 503.

The authenticated account that first registers a verified transaction establishes
local ownership. Notifications cannot establish ownership. A notification received
before registration can preserve verified state without associating a user, so
a later claim cannot replay a revoked purchase. Passes use Apple's signed purchase
date as the starting point and retain the existing stacking rules. Refund reversals
do not automatically regrant consumable Passes. Apple subscriptions and Pass
purchases have separate identities per environment. Verified Sandbox purchases
can grant Premium to the claiming account through the usual resolver. Sandbox
Pass time stacks separately from Production and Stripe Pass time.

Migration 0015 identifies existing Apple Pass environments using the verified
receipts. It stops if a Pass has no unique matching environment. Backfill retains
the recorded deadlines. A schema rollback cannot collapse two Apple identities
that differ only by environment.

After the backend records Apple subscriptions, passes or verified state,
rolling back through migration 0014 is unsafe and the reverse migration refuses
the operation. If rolling back application code to a version that handles only
one environment, keep the database schema and Apple billing state, and pause
Apple purchase and notification processing until an environment-aware version
is restored. Reconcile pending events before resuming processing.
