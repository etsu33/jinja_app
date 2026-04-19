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
/auth/login?returnTo=/shrines/new
↓
必要なら /auth/register?returnTo=/shrines/new
↓
登録成功
↓
ログイン成功
↓
/shrines/new に復帰

### 補足
- 投稿入口は `/shrines/new` を正規とする
- 未ログイン時は以下の認証導線に遷移する
  - `/auth/login?returnTo=/shrines/new`
  - `/auth/register?returnTo=/shrines/new`
- 検索画面から遷移した場合、必要に応じて `returnTo` に元画面（例: `/shrines?q=...`）を保持してよい
- 投稿アクション（`submit_shrine_submission`）はログイン必須
- `returnTo` は Login / Signup の両方で維持すること
