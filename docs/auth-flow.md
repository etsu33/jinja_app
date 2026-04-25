# Auth Flow

## 1. concierge の基本方針
- 相談・閲覧は未ログインでも許可
- 保存系操作はログイン必須
- 認証が必要になった瞬間だけ login/register に送る

## 2. concierge 保存導線
未ログインで concierge 利用
↓
保存アクションで認証要求
↓
/auth/login?returnTo=/concierge
↓
必要なら /auth/register?returnTo=/concierge
↓
登録成功
↓
ログイン成功
↓
/concierge に復帰

## 3. mypage 保護導線
未ログインで /mypage?tab=goshuin などへ遷移
↓
login にリダイレクト
↓
/auth/login?returnTo=/mypage?tab=goshuin
↓
ログイン成功
↓
元の tab に復帰

## 4. 責務境界
- ConciergeClientFull:
  未ログイン時の導線分岐、returnTo 指定
- LoginForm:
  login 実行、returnTo 復帰
- SignupForm:
  signup -> login -> returnTo 復帰
- /api/auth/register:
  backend signup endpoint の BFF


## 5. shrine submission 認証導線

未ログインで神社登録CTA押下
↓
/auth/login?returnTo=/shrines/new?returnTo=...
↓
必要なら /auth/register?returnTo=/shrines/new?returnTo=...
↓
登録成功
↓
ログイン成功
↓
/shrines/new?returnTo=... に復帰
↓
投稿成功後は `returnTo` に従って `/shrines` または `/mypage` に戻る

### 具体URL仕様
- 投稿入口は `/shrines/new` を正規とする
- mypage 起点の投稿も `/shrines/new?returnTo=/mypage` を使う
- 未ログイン時は以下へ遷移する
  - `/auth/login?returnTo=/shrines/new`
  - `/auth/register?returnTo=/shrines/new`
  - 必要に応じて `/auth/login?returnTo=/shrines/new?returnTo=/mypage`
- login / signup 完了後は `returnTo` に従い `/shrines/new?returnTo=...` に復帰する
- 投稿成功後は最終的に `returnTo` の指す画面へ戻る

### returnTo ルール
- `returnTo` は相対パスのみ許可する（例: `/shrines/new`, `/shrines?q=...`, `/mypage`）
- auth 入口では nested `returnTo` を維持したまま安全性だけを確認する
- `/shrines/new` ページ側で最終的な `returnTo` 正規化を行う
- 不正な値（外部URLなど）の場合は `/shrines` にフォールバックする
- Login / Signup の両方で `returnTo` を維持する

### 検索画面からの遷移
- `/shrines?q=...` から遷移した場合、必要に応じて以下のように保持してよい
  - `/auth/login?returnTo=/shrines/new?returnTo=/shrines?q=...`
- ただし実装では多段 `returnTo` を正規化すること

### 補足
- 投稿アクション（`submit_shrine_submission`）はログイン必須
