> **Status: Active**
>
> 本ドキュメントは、KAMI MUSUBI Web版における認証アーキテクチャ、Frontend・BFF・Backendの責務、およびJWT・Cookieの利用方針を管理する正本である。
>
> 認証が必要になった際の画面遷移、`returnTo`、Concierge保存・My Page・神社投稿からの復帰導線は、`docs/core/auth-flow.md`を参照する。
>
> 正確なEndpoint・Cookie処理・認証方式は、関連する実装コードとテストを最終的な正本とする。

# Authentication Flow

## 目的

KAMI MUSUBIの認証経路を一本化し、Frontend・Next.js BFF・Django Backendの責務を明確にする。

認証入口の乱立、JWT処理の重複、Backendへの直接通信を防ぎ、課金・My Page・御朱印・お気に入り・Concierge保存・参拝記録などの認証付き機能を安全に保守する。

---

## 基本方針

Web版の認証経路は、以下を正本とする。

```text
Frontend
↓
Next.js BFF
↓
Django Backend
↓
JWTAuthentication
↓
request.user
```

Frontendのログイン入口は、Next.js BFFの`/api/auth/login`とする。

FrontendからDjango BackendのJWT発行Endpointを直接呼び出さない。

---

## ログインフロー

```text
Login Form
↓
AuthProvider.login
↓
POST /api/auth/login
↓
Next.js API Route
↓
Django /api/auth/jwt/create/
↓
access_token / refresh_tokenを取得
↓
HttpOnly Cookieへ保存
↓
認証状態をFrontendへ反映
```

### Frontendの正本実装

- `apps/web/src/lib/auth/AuthProvider.tsx`
- `apps/web/src/lib/api/auth.ts`

### BFFの正本実装

- `apps/web/src/app/api/auth/login/route.ts`
- `apps/web/src/app/api/auth/logout/route.ts`
- `apps/web/src/app/api/auth/register/route.ts`

### Backendの認証Endpoint

```text
/api/auth/jwt/create/
```

Frontend側にJWT発行用の`/api/auth/jwt/create` Routeは持たない。

---

## Cookie方針

Web版では、以下のCookieを使用する。

```text
access_token
refresh_token
```

### Cookie属性

```text
HttpOnly: true
SameSite: lax
Secure: productionではtrue
Path: /
```

### ルール

- JWTをFrontend JavaScriptから直接読み取らない
- JWTを`localStorage`へ保存しない
- Access TokenとRefresh TokenはHttpOnly Cookieで管理する
- Cookieの生成・更新・削除はBFF側で行う

---

## Frontendの責務

Frontendは、認証画面・認証状態・認証要求時のUIを担当する。

### 担当すること

- Login Formから`/api/auth/login`を呼び出す
- Signup Formから`/api/auth/register`を呼び出す
- Logout時に`/api/auth/logout`を呼び出す
- `AuthProvider`で認証状態を管理する
- 未ログイン時に認証画面へ遷移する
- 認証後の復帰先を保持する

### 担当しないこと

- JWTの直接保存
- JWTの直接解析
- Backend Originの組み立て
- Authorization Headerの生成
- Refresh Tokenによる再発行処理
- Backendの課金状態・権限判定

画面遷移と`returnTo`の詳細は`docs/core/auth-flow.md`で管理する。

---

## BFFの責務

認証付きAPI Routeは、原則として`bffFetchWithAuthFromReq`を利用する。

### 正本Helper

```text
apps/web/src/lib/server/bffFetch.ts
```

### 担当すること

- Request CookieからAccess Token・Refresh Tokenを取得する
- Backendへ`Authorization: Bearer <token>`を付与する
- Access Token期限切れ時にRefreshを試行する
- Refresh成功時にAccess Token Cookieを更新する
- Backend ResponseをFrontendへ返す
- 認証失敗時のResponseを統一する

### 担当しないこと

- UI表示
- Login画面への遷移
- 課金状態の最終判定
- Backendの業務ロジック

---

## 認証付きAPIの通信経路

認証付き機能は、次の経路を利用する。

```text
Frontend Component
↓
Next.js API Route
↓
bffFetchWithAuthFromReq
↓
Django Backend
```

Frontend ComponentからBackend APIを直接呼び出さない。

---

## Backendの責務

Backendは認証情報から`request.user`を解決し、権限・課金状態・保存対象の判定を行う。

```text
Authorization Header
↓
JWTAuthentication
↓
request.user
↓
Permission・Billing・Ownership判定
```

### 担当すること

- JWTの検証
- `request.user`の解決
- Permission Classによるアクセス制御
- User単位の保存・取得
- 課金状態の判定
- 所有者判定
- 認証失敗Responseの返却

### 担当しないこと

- HttpOnly Cookieの直接管理
- Frontend画面遷移
- `returnTo`の保持
- Frontend Auth Stateの管理

---

## 認証入口

Frontendで使用する認証入口は次の3つとする。

```text
/api/auth/login
/api/auth/logout
/api/auth/register
```

Django BackendのJWT Endpointは、BFFから呼び出す内部経路として扱う。

Frontend Componentから直接利用しない。

---

## 認証付き機能

次の機能は、認証済みユーザーを前提とする。

- お気に入り保存
- 参拝記録
- 振り返り保存
- My Page
- 自分の御朱印管理
- 神社情報の投稿
- 課金状態の取得
- User固有情報の取得
- Concierge結果の保存

相談・閲覧など、認証不要と定義された機能は未ログインでも利用できる。

認証が必要になるタイミングと画面復帰は`docs/core/auth-flow.md`で管理する。

---

## SessionAuthenticationの扱い

Web版の認証主経路はJWTとする。

ただし、Backend内に残る`SessionAuthentication`は、この文書だけを根拠として削除しない。

### ルール

- Django Adminなど、Sessionを必要とする経路と分離して判断する
- APIごとのAuthentication Classは実装コードを正本とする
- JWTのみで動作確認できたAPIでも、影響範囲を確認してから変更する
- Session依存の有無はテストと実装監査で確認する

`SessionAuthentication`の削除可否は、本書の現行仕様ではなく、個別の監査・実装PRで扱う。

---

## 禁止事項

- Frontend Route内でBackend URLを直接組み立てる
- Frontend ComponentからBackend Originを直接呼び出す
- RouteごとにAuthorization付与処理を重複実装する
- 認証付きRouteで`NEXT_PUBLIC_API_BASE`や`API_BASE_URL`を直接参照する
- FrontendにJWT発行Routeを複数持つ
- Access Token・Refresh Tokenを`localStorage`へ保存する
- JWTをClient JavaScriptから直接読み取る
- 課金状態や権限をFrontendだけで確定する

---

## 責務境界

| 項目 | Frontend | BFF | Backend |
|---|:---:|:---:|:---:|
| Login Form | 担当 | 受理 | 認証 |
| Cookie保存 | 担当しない | 担当 | 担当しない |
| Authorization Header | 担当しない | 担当 | 検証 |
| Token Refresh | 担当しない | 担当 | 発行 |
| 認証状態UI | 担当 | 補助 | 担当しない |
| `request.user` | 担当しない | 転送 | 担当 |
| Permission判定 | 担当しない | 担当しない | 担当 |
| 課金状態判定 | 表示のみ | 転送 | 担当 |
| `returnTo` | 担当 | 保持・転送 | 担当しない |

---

## 正本実装

### Frontend

- `apps/web/src/lib/auth/AuthProvider.tsx`
- `apps/web/src/lib/api/auth.ts`

### BFF

- `apps/web/src/app/api/auth/login/route.ts`
- `apps/web/src/app/api/auth/logout/route.ts`
- `apps/web/src/app/api/auth/register/route.ts`
- `apps/web/src/lib/server/bffFetch.ts`

### Backend

- JWT発行Endpoint
- Authentication Class設定
- Permission Class設定
- 認証対象となる各API View

Endpoint、Cookie名、Response、Authentication Classの正確な契約は実装コードとテストを正本とする。

---

## 関連ドキュメント

- `docs/core/auth-flow.md`
- `docs/README.md`
- `docs/core/architecture.md`
- `backend/README.md`

---

## 更新ルール

- 本書はWeb版の認証アーキテクチャと責務境界を管理する
- 認証経路、Cookie、BFF、JWT方針が変更された場合のみ更新する
- 画面遷移・`returnTo`・認証後の復帰導線は`docs/core/auth-flow.md`で管理する
- Mobile固有のToken保存・認証経路はMobile側文書と実装で管理する
- 検証チェックリスト、TODO、監査計画、PR候補、実装進捗は記載しない
