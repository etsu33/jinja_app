

# 本番 Smoke Checklist

## 目的

本番デプロイ後に、主要な認証・BFF・backend API が最低限壊れていないことを短時間で確認する。

このチェックリストは「原因調査」ではなく「本番が使える状態か」を確認するためのもの。

詳細調査が必要な場合は以下を参照する。

- `docs/ops/production-bff-hardening.md`
- `docs/triage/production-500-triage.md`

## 前提

- Web は本番ドメインから確認する
- backend 直叩きではなく、原則 `/api/*` のBFF経由を確認する
- Browser DevTools の Network / Application / Console を開いて確認する
- 失敗時は status / response body / Vercel Logs / Render Logs を記録する

## Smoke対象

| 優先 | 項目 | 目的 |
|---:|---|---|
| 1 | login | 認証cookieが発行されること |
| 2 | `/api/users/me/` | 認証状態が復元できること |
| 3 | `/api/concierge/chat/` | コンシェルジュ主導線が動くこと |
| 4 | `/api/my/goshuins/` | 認証付き御朱印取得が動くこと |
| 5 | `/api/shrine-submissions/` | 認証付き投稿一覧が動くこと |
| 6 | `/api/billings/status/` | 課金状態取得が動くこと |
| 7 | `/api/billings/checkout` | checkout開始が動くこと |

## 1. login

### 手順

1. 本番Webでログイン画面を開く
2. テスト用ユーザーでログインする
3. Network で login request を確認する
4. Application > Cookies を確認する

### 期待値

- login API が `200` を返す
- `access_token` が保存される
- `refresh_token` が保存される
- Cookie が `HttpOnly` である
- login後に想定画面へ遷移する

### 失敗時に見るもの

- login response body
- `set-cookie` header
- Vercel Function Logs
- Render backend logs

## 2. `/api/users/me/`

### 手順

1. ログイン後にページをreloadする
2. Network で `/api/users/me/` を確認する

### 期待値

- status が `200`
- 認証済みユーザー情報が返る
- reload後もログイン状態が維持される

### 判断

| status | 判断 |
|---:|---|
| 200 | OK |
| 401 | access / refresh cookie を確認 |
| 500 | Vercel / Render logs を確認 |

## 3. `/api/concierge/chat/`

### 手順

1. `/concierge` を開く
2. `仕事運を上げたい` など短い相談文を送信する
3. Network で `/api/concierge/chat/` を確認する

### 期待値

- status が `200`
- response に `ok: true` が含まれる
- `data.recommendations` が配列で返る
- Console に致命的エラーが出ない
- 匿名利用時は `concierge_anon_id` が必要に応じて保存される

### 確認ログキー

```text
[DJ_FETCH]
[DJ_FETCH_RESPONSE]
[BFF_CHAT_ENTRY]
[BFF_CHAT_PROXY]
[BFF_CHAT_RETURN]
```

### 判断

| status | 判断 |
|---:|---|
| 200 | OK |
| 401 | refresh flow / cookie を確認 |
| 429 | quota / throttle を確認 |
| 500 | Render backend traceback を確認 |

## 4. `/api/my/goshuins/`

### 手順

1. ログイン済み状態で `/mypage` を開く
2. 御朱印タブまたは御朱印一覧を表示する
3. Network で `/api/my/goshuins/` を確認する

### 期待値

- status が `200`
- 空の場合は `[]` または正常な空状態になる
- 画像付きデータがある場合、表示で落ちない

### 判断

| status | 判断 |
|---:|---|
| 200 | OK |
| 401 | 認証cookie / BFF auth forward を確認 |
| 500 | storage / serializer / backend logs を確認 |

## 5. `/api/shrine-submissions/`

### 手順

1. ログイン済み状態で神社投稿画面または投稿履歴に進む
2. Network で `/api/shrine-submissions/` を確認する

### 期待値

- GET が `200`
- 投稿履歴が配列またはpagination形式で返る
- pending / approved / rejected の表示で落ちない

### 追加POST確認（必要時のみ）

1. テスト用の重複しにくい神社名で投稿する
2. response が `201` または `duplicate_candidate` の `400` であることを確認する
3. 本番データを汚すため、不要な大量投稿はしない

### 判断

| status | 判断 |
|---:|---|
| 200 | GET OK |
| 201 | POST OK |
| 400 duplicate_candidate | 重複判定OK |
| 401 | login / auth forward を確認 |
| 500 | serializer / duplicate service / DB logs を確認 |

## 6. `/api/billings/status/`

### 手順

1. `/billing` を開く
2. Network で `/api/billings/status/` を確認する

### 期待値

- status が `200`
- response に以下が含まれる
  - `plan`
  - `is_active`
  - `provider`

### 判断

| status | 判断 |
|---:|---|
| 200 | OK |
| 401 | login状態を確認 |
| 500 | billing provider / backend logs を確認 |

## 7. `/api/billings/checkout`

### 手順

1. `/billing/upgrade` を開く
2. `プレミアムにする` を押す
3. Network で `/api/billings/checkout` を確認する

### 期待値

- status が `200`
- response に `checkout_url` が含まれる
- Stripe checkout URL へ遷移する
- analytics の `upgrade_click` / `checkout_started` が記録される

### 注意

- 実課金が絡む環境では、テストアカウント・テスト決済手段を使う
- 本番決済を不用意に完了させない

### 判断

| status | 判断 |
|---:|---|
| 200 | checkout開始OK |
| 401 | login / auth forward を確認 |
| 500 | billing provider / env / Render logs を確認 |

## 結果記録テンプレート

| 日時 | 環境 | commit / deploy | login | users/me | concierge/chat | my/goshuins | shrine-submissions | billing/status | billing/checkout | メモ |
|---|---|---|---|---|---|---|---|---|---|---|
| YYYY-MM-DD HH:mm | production | `<sha>` | 未確認 | 未確認 | 未確認 | 未確認 | 未確認 | 未確認 | 未確認 |  |

## 失敗時の記録項目

- API path
- method
- status
- request id があれば記録
- response body preview
- Vercel Function Logs の該当ログ
- Render backend logs の該当traceback
- Cookie状態
- 再現手順

## 完了条件

以下がすべて確認できれば、本番 smoke は完了とする。

```markdown
- [ ] login
- [ ] /api/users/me/
- [ ] /api/concierge/chat/
- [ ] /api/my/goshuins/
- [ ] /api/shrine-submissions/
- [ ] /api/billings/status/
- [ ] /api/billings/checkout
```

## 次に分離するPR候補

- smoke結果を記録する `docs/ops/production-smoke-log.md` の追加
- Playwright による最小E2E smoke
- billing checkout の安全なtest mode確認手順追加
- Vercel / Render のログ確認スクリーンショット付き手順追加
