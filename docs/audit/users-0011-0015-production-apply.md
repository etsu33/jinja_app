> **Status: 適用完了。DB の形と件数、判定の動き、Web での表示、適用後のログを確認済み。
> バックアップの CSV ファイルの保存確認だけが未完了。**
>
> 本ドキュメントは、`users` 0011〜0015 を本番 DB（Supabase）へ適用した記録である。
> 操作する人の Mac には本番 DB の接続情報が無い前提で、事前確認とバックアップは
> Supabase ダッシュボード、適用は Render Shell だけで行った。
> 手順の正本は `scripts/migration_safety/README.md` の
> 「Runbook: `users` 0011-0015 via Dashboard + Render Shell」。
>
> このリポジトリは公開されているため、ユーザー ID・ニックネーム・決済 ID・
> 接続先・サービス ID など、個人や環境を特定できる値は書かない。

# users 0011〜0015 本番適用の記録（2026-11-21）

## 対象

| マイグレーション | 内容 | 止まる条件があるか |
|---|---|---|
| 0011 | Premium の期限を「月額」「Pass」「旧来の期限」に分ける | あり（データ次第で `RuntimeError`） |
| 0012 | `PremiumSubscription` テーブルを作る | なし |
| 0013 | Stripe の月額契約を `PremiumSubscription` に移す | あり |
| 0014 | `AppleStoreKitReceipt` テーブルを作る | なし |
| 0015 | Pass の購入に Apple の環境を持たせ、制約を張り替える | あり |

## 使ったもの

- `scripts/migration_safety/sql/users_0011_0015_preflight.sql`（事前確認）
- `scripts/migration_safety/sql/users_0011_0015_postcheck.sql`（事後確認）
- どちらも SELECT 文1本だけ。`guard.py check-readonly-sql` で SAFE を確認し、
  `tests/test_guard.py::TestUsers0011_0015SqlIsReadonlySingleStatement` で固定した。

### 事前確認 SQL のローカル検証（本番には接続していない）

0010 の状態の使い捨て DB（PostgreSQL 16）に、0011・0013・0015 が止まる条件を
1つずつ入れたデータを作り、事前確認 SQL の結果と、実際のマイグレーション
（`migrate users 0015`）の結果を突き合わせた。

- 21 通りすべてで「SQL に FAIL が出る」と「migrate が `RuntimeError` で止まる」が
  一致し、FAIL になった行と止まった理由も対応していた。
- 止まらないはずの境界（期限切れの past_due、canceled、前後に空白のある status）は
  PASS かつ migrate 成功で一致した。
- 正常データで適用した後、事後確認 SQL は全項目 PASS、
  「5 compare」は事前確認の「5 expect」と一致した。
- この検証用のスクリプトはリポジトリに入れていない（下の「残っていること」参照）。

## 本番での記録

時刻は UTC。

### Step 0：本番の状態（Render Shell、読み取りのみ）

| 確認 | 結果 |
|---|---|
| `django_migrations` の users | 0010 まで記録、0011〜0015 は記録なし |
| デプロイ済みのファイル | 0011〜0015 あり（新しいコードが DB より先にデプロイされていた） |
| `RUN_MIGRATIONS_ON_START` | `0` |
| `migrate users 0015 --plan` | users の 0011〜0015 の5本だけ。中身はリポジトリのファイルと一致 |

### Step 1：事前確認（02:52:46）

21 項目すべて PASS。

| 5 expect | 件数 |
|---|---|
| profiles total | 17 |
| Pass purchases total | 3 |
| Pass purchases by source | stripe=3 |
| Pass users | 1 |
| profiles without Stripe ids | 17 |
| non-Pass with deadline（→ `legacy_premium_until`） | 2 |
| non-Pass with future deadline（今も旧来の Premium） | 1 |
| Stripe subscriptions 0013 will create | 0 |

### Step 2：バックアップ

- `users_userprofile`（17 行）と `users_premiumpasspurchase`（3 行）を SQL Editor で
  `SELECT * … ORDER BY id` し、行数が事前確認と一致することを確認した。
- **未確認**：2 つを CSV ファイルとしてリポジトリの外に保存できたかは、
  ファイル名と行数での確認がとれていない。

### Step 3：直前の事前確認

実施したかどうかの記録が無い。ただし、Step 5 の「5 compare」が Step 1 の
「5 expect」と完全に一致したため、その間にデータは変わっていない。

### Step 4：適用（Render Shell）

`python manage.py migrate users 0011 --noinput` から 0015 まで、1 本ずつ実行し、
5 本とも `OK`。出力に接続先の情報は出ていない。

- 0011 の `OK` と次の入力待ちが表示された後に `^C` が押されている。
  止めたのは貼り付けが崩れた入力行だけで、マイグレーションには影響していない。

### Step 5：事後確認（03:54:54）

13 項目すべて PASS。「5 compare」は Step 1 の「5 expect」と全件一致
（17 / 3 / stripe=3 / 1 / 17 / 2 / 1 / 0）。

### Step 6：適用後の動作確認

| 確認 | 結果 |
|---|---|
| `BILLING_PROVIDER`（Render Shell） | `stripe`。判定は環境変数ではなく DB の中身で行われる |
| `get_billing_status` を Render Shell で直接実行（読み取りのみ） | 旧来の期限が有効なアカウント：`premium`、期限は `legacy_premium_until` の値。Pass の期限が切れたアカウント：`free` |
| Web 本番のマイページ | 旧来の期限が有効なアカウントで `Premium` のバッジが表示された |
| Render の Logs（直近1時間、03:05〜04:05 UTC ごろ（日本時間 12:05〜13:05）） | `legacy_premium_until`・`does not exist` ともに該当なし。`/api/users/me/` と `/api/billings/status/` は 200 |

- Pass の期限が切れたアカウントは、パスワードが分からず Web でのログインはしていない。
  判定は上の Render Shell の結果で確認済みのため、本番 DB に書き込むパスワード再設定は行わなかった。
- `free` と判定されるアカウントがあることで、全員を premium にする設定が働いていないことも確かめられた。

## 途中で起きたこと

- 本番への適用の前に、Mac のターミナルで `migrate users 0011`〜`0015` が 3 回
  実行された。Mac がつないでいたのはローカル DB（最初の実行時に users が 0009 で、
  本番の 0010 と異なる）で、Render Shell で見た本番の記録は適用まで 0010 のまま
  だったため、本番には影響していない。
  - 教訓：Mac のターミナルと Render Shell は見た目が似ている。コマンドを打つ前に、
    行の先頭が `render@srv-` かどうかを確かめる。
- バックアップ確認の過程で、プロフィールと Pass の購入の中身がチャットに貼られた。
  すべてテスト用のアカウントと Stripe のテスト決済だったが、今後は行数だけを伝える。

## 分かったこと

- 本番のアカウントは名前からするとすべてテスト・QA 用（推測）。
- Stripe の月額契約者は 0 人。0013 の移し替えは本番では 1 件も処理していない。
- 本番 DB の Pass の購入 3 件は、すべて Stripe のテストモードの決済
  （決済 ID が `cs_test_` で始まる）。本番の Stripe がテストモードのキーで動いている
  可能性がある（推測、今回の作業の範囲外）。

## 残っていること

1. バックアップの CSV が保存されているかの確認と、いつ消すかの決定
2. 適用前に、新しいコードが存在しない列を読んでエラーになっていたか（障害があったか）は
   確かめていない。確かめた Logs は直近1時間（03:05 UTC 以降）だけで、適用の時刻（02:52〜03:54 UTC の間）より前を十分に含んでいない
3. `/billing` ページの有効期限の表示は確かめていない（判定の期限は Render Shell で確認済み）
4. 本番に、期限が残っている Pass の購入も、Stripe の月額契約も無い。そのため
   「Pass の期限で Premium になる」「月額契約が `PremiumSubscription` に記録される」
   動きは本番のデータでは確かめていない
5. 事前確認 SQL のローカル検証（21 通り）をスクリプトとしてリポジトリに入れるか
