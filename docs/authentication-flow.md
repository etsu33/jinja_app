

# Authentication Flow

## 目的

KAMI MUSUBI の認証経路を整理し、frontend / BFF / backend の責務を明確にする。

このドキュメントは、認証入口の乱立を防ぎ、今後の課金判定・マイページ・御朱印・お気に入り・コンシェルジュ保存などの認証付き機能を安全に保守するための正本とする。

---

## 現在の結論

frontend のログイン入口は `/api/auth/login` を正本とする。

frontend から backend の JWT 発行 API を直接呼ぶ入口は持たない。

```text
Frontend
  ↓
/api/auth/login
  ↓
Next.js BFF
  ↓
Django backend /api/auth/jwt/create/
  ↓
access_token / refresh_token を HttpOnly Cookie に保存
```

---

## 認証フロー

### 1. ログイン

```text
Login Form
  ↓
AuthProvider.login(username, password)
  ↓
POST /api/auth/login
  ↓
Next.js API Route
  ↓
Django /api/auth/jwt/create/
  ↓
JWT access / refresh を受け取る
  ↓
HttpOnly Cookie に保存
```

### 正本ファイル

```text
apps/web/src/lib/auth/AuthProvider.tsx
apps/web/src/app/api/auth/login/route.ts
```

### backend 正本

```text
backend 側 /api/auth/jwt/create/
```

frontend 側の `/api/auth/jwt/create` route は未使用だったため削除済み。

---

## Cookie 方針

### 使用する Cookie

```text
access_token
refresh_token
```

### 方針

```text
HttpOnly: true
SameSite: lax
Secure: production では true
Path: /
```

access_token / refresh_token は JavaScript から直接読まない。

---

## BFF の責務

認証付き API route は、原則として `bffFetchWithAuthFromReq` を使う。

### 正本 helper

```text
apps/web/src/lib/server/bffFetch.ts
```

### 主な責務

```text
- request cookie から access_token / refresh_token を読む
- backend へ Authorization: Bearer <token> を付与する
- access_token 期限切れ時に refresh を試す
- refresh 成功時は access_token Cookie を更新する
- backend response を frontend に返す
```

---

## 認証付き route の方針

### 原則

```text
Frontend component
  ↓
Next.js API Route
  ↓
bffFetchWithAuthFromReq
  ↓
Django backend
```

frontend から backend origin を直接組み立てない。

### 禁止方針

```text
- route.ts 内で backend URL を直接組み立てる
- route.ts 内で NEXT_PUBLIC_API_BASE / API_BASE_URL を直接参照する
- route.ts ごとに Authorization 付与ロジックを重複実装する
- frontend 側に JWT 発行 route を複数持つ
```

---

## 現在確認済みの整理

### frontend 認証入口

```text
残す:
- /api/auth/login
- /api/auth/logout
- /api/auth/register

削除済み:
- /api/auth/jwt/create
```

### BFF 統一済み route

```text
apps/web/src/app/api/shrines/[id]/visit/route.ts
apps/web/src/app/api/shrines/[id]/reflection/route.ts
apps/web/src/app/api/visits/route.ts
apps/web/src/app/api/shrine-interactions/route.ts
```

---

## backend 認証方式

backend は主に `JWTAuthentication` を使う。

一部に `SessionAuthentication` が残っているため、削除可否は別途監査する。

### 監査対象

```text
BillingStatusView
UsersMeView
Goshuin 系 API
Favorite 系 API
Concierge 系 API
```

---

## SessionAuthentication の扱い

現時点では即削除しない。

### 理由

```text
- どの API が SessionAuthentication に依存しているか未確定
- Goshuin / Users / Billing に影響する可能性がある
- 管理画面や開発時の互換目的で残っている可能性がある
```

### 判断分類

```text
削除可能:
- JWTAuthentication のみで動作確認できる API

保留:
- 影響範囲が未確認の API

残す:
- 明確に SessionAuthentication が必要な API
```

---

## 検証チェックリスト

```markdown
- [ ] /api/auth/login でログインできる
- [ ] access_token / refresh_token が HttpOnly Cookie に保存される
- [ ] /api/users/me/ が認証済みユーザーを返す
- [ ] /api/billings/status/ が premium 状態を返す
- [ ] コンシェルジュ送信ができる
- [ ] お気に入り保存ができる
- [ ] 参拝完了 visit API が動く
- [ ] 振り返り reflection API が動く
- [ ] 御朱印 my/goshuins API が動く
```

---

## 次の監査 TODO

```markdown
- [ ] SessionAuthentication利用箇所を一覧化
- [ ] JWTAuthentication利用箇所を一覧化
- [ ] BillingView の認証方式を確認
- [ ] UsersView の認証方式を確認
- [ ] Goshuin系APIの認証方式を確認
- [ ] SessionAuthentication削除可否を分類
- [ ] 削除可能 / 保留 / 残す を分ける
- [ ] 次PR用の実装指示書を作成
```


---

## 認証アーキテクチャ

### 目的

KAMI MUSUBI の認証経路は、frontend / BFF / backend の責務を分離し、認証入口の乱立を防ぐ構成とする。

認証付き機能は、課金状態・マイページ・御朱印・お気に入り・コンシェルジュ保存・参拝記録など、ユーザー状態に依存するため、認証経路を一本化して保守する。

---

### 現在の正本フロー

```text
Frontend
  ↓
/api/auth/login
  ↓
Next.js BFF
  ↓
Django backend /api/auth/jwt/create/
  ↓
access_token / refresh_token を HttpOnly Cookie に保存
  ↓
認証付き API は BFF 経由で backend へ転送
```

frontend のログイン入口は `/api/auth/login` を正本とする。

frontend 側に JWT 発行用の `/api/auth/jwt/create` route は持たない。

---

### Frontend の責務

```text
- ログインフォームから /api/auth/login を呼ぶ
- JWT を JavaScript で直接保持しない
- 認証状態は AuthProvider で扱う
- access_token / refresh_token は HttpOnly Cookie として扱う
```

正本ファイル:

```text
apps/web/src/lib/auth/AuthProvider.tsx
apps/web/src/app/api/auth/login/route.ts
apps/web/src/lib/api/auth.ts
```

---

### BFF の責務

認証付き API route は、原則として `bffFetchWithAuthFromReq` を経由する。

```text
apps/web/src/lib/server/bffFetch.ts
```

BFF は以下を担当する。

```text
- request cookie から access_token / refresh_token を読む
- backend へ Authorization: Bearer <token> を付与する
- access_token 期限切れ時に refresh を試す
- refresh 成功時は access_token Cookie を更新する
- backend response を frontend に返す
```

frontend component から backend origin を直接組み立てない。

---

### Backend の責務

backend は JWTAuthentication を認証の正本とする。

```text
Django backend
  ↓
JWTAuthentication
  ↓
request.user を解決
  ↓
課金状態・ユーザー情報・保存情報などを判定
```

課金判定は backend 側で `request.user` をもとに行う。

```text
/api/billings/status/
```

---

### 禁止方針

```text
- frontend route 内で backend URL を直接組み立てる
- route.ts ごとに Authorization 付与ロジックを重複実装する
- NEXT_PUBLIC_API_BASE / API_BASE_URL を認証付き route で直接参照する
- frontend に JWT 発行 route を複数持つ
- access_token / refresh_token を localStorage に保存する
```

---

### SessionAuthentication の扱い

現時点では SessionAuthentication を即削除しない。

理由:

```text
- 依存箇所がまだ完全には確定していない
- Goshuin / Users / Billing などに影響する可能性がある
- 開発初期や互換目的で残っている可能性がある
```

今後の監査で以下に分類する。

```text
削除可能:
- JWTAuthentication のみで動作確認できる API

保留:
- 影響範囲が未確認の API

残す:
- 明確に SessionAuthentication が必要な API
```

---

### 関連ドキュメント

```text
docs/authentication-flow.md
```
