> **Status: Reference**
>
> 本ドキュメントは、KAMI MUSUBI Web版における認証画面遷移、`returnTo`、および認証後の復帰導線を管理する Reference 文書である。
>
> 認証アーキテクチャ、JWT、Cookie、Frontend・BFF・Backend の責務は `docs/authentication-flow.md` を正本とする。
>
> 正確な画面遷移、Route、Query Parameter、`returnTo` の実装は関連する Frontend 実装およびテストを最終的な正本とする。

# Auth Flow

## 目的

認証が必要になったタイミングでの画面遷移と、認証後に元の画面へ安全に復帰する導線を定義する。

本書では認証方式ではなく、画面遷移と `returnTo` の利用方針を扱う。

---

## Concierge 利用方針

- 相談・閲覧は未ログインでも利用できる
- 保存操作から認証を要求する
- 必要になるまでは認証画面へ遷移しない

---

## Concierge 保存導線

```text
未ログイン
↓
Concierge利用
↓
保存操作
↓
/auth/login?returnTo=/concierge
↓
必要なら
/auth/register?returnTo=/concierge
↓
認証成功
↓
/concierge に復帰
```

---

## My Page 保護導線

```text
未ログイン
↓
/mypage?tab=...
↓
/auth/login?returnTo=/mypage?tab=...
↓
認証成功
↓
元のタブへ復帰
```

---

## 神社投稿導線

```text
未ログイン
↓
/shrines/new
↓
/auth/login?returnTo=/shrines/new?returnTo=...
↓
必要なら登録
↓
認証成功
↓
/shrines/new に復帰
↓
投稿成功
↓
returnTo に従って遷移
```

---

## `returnTo` 方針

### 基本ルール

- `returnTo` は相対パスのみ許可する
- Login・Signup の両方で保持する
- 多段 `returnTo` を許可する
- 外部URLは許可しない

### 正規化

- 認証入口では安全性のみ確認する
- 最終的な正規化は遷移先ページで行う
- 不正な値は既定画面へフォールバックする

---

## 責務境界

| 項目 | 担当 |
|------|------|
| 認証要求タイミング | Frontend |
| `returnTo` 保持 | Frontend |
| `returnTo` 正規化 | 遷移先ページ |
| JWT・Cookie管理 | BFF |
| 認証・権限判定 | Backend |

---

## 関連ドキュメント

- `docs/authentication-flow.md`
- `docs/README.md`

---

## 更新ルール

- 本書は認証画面遷移と `returnTo` の仕様のみ管理する
- JWT・Cookie・BFF・認証方式は `authentication-flow.md` を更新する
- Endpoint・Route・画面遷移の最終仕様は実装コードとテストを正本とする
