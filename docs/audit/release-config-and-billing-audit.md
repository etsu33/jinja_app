

# Release Config and Billing Audit

## 目的

リリース前に、Billing 判定・環境変数読み込み・管理者検証導線の責務を確認し、
本番移行前に設定起因の事故を減らす。

## 対象範囲

- `backend/temples/services/billing_state.py`
- `backend/shrine_project/settings.py`
- `backend/.env.local`
- `backend/.env.test`
- `backend/.env.example`
- `backend/README.md`
- Billing 関連テスト

---

## Billing 監査結果

### 判定窓口

Billing 状態の判定窓口は以下に集約する。

- `temples/services/billing_state.py:get_billing_status()`

この関数は、provider ごとの差異を吸収し、利用側には `BillingStatus` として返す。

### provider ごとの責務

| provider | Source of Truth | 用途 |
|---|---|---|
| `stub` | 環境変数 | 開発・テスト・Billing 未導入時の擬似切り替え |
| `stripe` | `UserProfile` | Stripe 導入後の課金状態判定 |
| `revenuecat` | 現時点では `UserProfile` 扱い | 将来のモバイル課金連携候補 |
| `unknown` | fallback | 不正 provider の安全側処理 |

### stub 運用

stub 運用では以下の環境変数を正本とする。

- `BILLING_PROVIDER=stub`
- `BILLING_STUB_PLAN=free|premium`
- `BILLING_STUB_ACTIVE=0|1`
- `BILLING_STUB_CANCEL_AT_PERIOD_END=0|1`

`BILLING_STUB_PLAN=premium` かつ `BILLING_STUB_ACTIVE` が未指定の場合は、
テスト・開発時の利便性のため active 扱いにする。

### stripe 運用

stripe 運用では、認証済みユーザーの `UserProfile` を正本とする。

参照する主な値:

- `UserProfile.subscription_status`
- `UserProfile.current_period_end`

有効判定は以下に委譲する。

- `users.services.billing.is_subscription_active()`

### Premium 判定

Premium 判定は以下に集約する。

- `temples/services/billing_state.py:is_premium_for_user(user)`

`recommend_limit_for_user(user)` は `is_premium_for_user(user)` の結果のみを参照する。

### 管理者検証 bypass

管理者アカウントは、検証用途として Premium 扱いにする。

条件:

- `user.is_authenticated == True`
- `user.is_staff == True`

目的:

- 100 セッション検証
- Score v3 dashboard 確認
- Premium 導線・制限の回避
- 決済を通さない管理者検証

注意:

- 一般ユーザー向けの課金状態とは別扱い。
- 本番で管理者のみが検証できるようにするための bypass であり、一般ユーザーに開放しない。

### 追加した契約テスト

追加対象:

- `backend/temples/tests/api/test_billing_status_contract.py`

確認内容:

- `is_staff=True` の管理者ユーザーは `is_premium_for_user(user) is True` になる。

---

## Environment 監査結果

### 採用する env ファイル

開発環境では以下を使用する。

| ファイル | 用途 | Git 管理 |
|---|---|---|
| `backend/.env.local` | ローカル開発用 | しない |
| `backend/.env.test` | pytest 用 | 必要に応じて管理 |
| `backend/.env.example` | サンプル・初期設定 | する |

### 廃止・非推奨

以下は運用対象外とする。

- `backend/.env`
- `backend/.env.dev`
- `backend/.env.bak`

### 読み込み順

通常起動:

```text
backend/.env.local
```

pytest 実行時:

```text
backend/.env.local
↓
backend/.env.test（上書き）
```

### pytest DB 方針

Backend の pytest は PostgreSQL / PostGIS 前提で実行する。
SQLite は使用しない。

安全策:

- pytest 実行時に `USE_SQLITE=1` が指定されている場合は起動時に明示エラーにする。

### README 反映

`backend/README.md` に以下を追記済み。

- env ファイル構成
- 読み込み順
- `.env.local` を開発用の正本にする方針
- `.env.example` から `.env.local` を作成する手順

---

## 検証結果

### 対象テスト

```bash
pytest temples/tests/api/test_billing_status_contract.py
```

結果:

- passed

### 全体テスト

```bash
pytest
```

結果:

- passed

確認済み結果:

- `698 passed`
- `9 skipped`

---

## 保留事項

### anonymous 時の Billing 扱い

現状では、未認証ユーザーは provider が `stripe` の場合でも stub env fallback を参照する。

現在の扱い:

- 既存テスト上は許容されている
- Billing 未導入・開発環境では便利

将来検討:

- 本番 Stripe 運用時に、anonymous を常に free 固定にするか検討する
- 仕様変更する場合は API 契約テストを先に更新する

### settings.py の責務分離

現時点では、`settings.py` に以下の責務が残っている。

- Database
- Environment
- Security
- Cache
- LLM
- Billing
- Static / Media

将来検討:

- `settings/base.py`
- `settings/database.py`
- `settings/billing.py`
- `settings/llm.py`
- `settings/cache.py`
- `settings/security.py`

などへの分割を検討する。
ただし、現時点では動作安定を優先し、即時分割は行わない。

---

## 結論

Billing と env のリリース前提は、現時点で以下の状態まで整理済み。

- Billing 判定は `get_billing_status()` に集約
- Premium 判定は `is_premium_for_user()` に集約
- 管理者は検証用途として Premium 扱い
- env は `.env.local` / `.env.test` / `.env.example` に整理
- pytest は PostgreSQL / PostGIS 前提
- README に env 運用を反映済み
- 契約テスト・全体テスト通過済み

リリース前の残タスクは、CI / Render / `.gitignore` / `.env.example` の最終整合性確認。
