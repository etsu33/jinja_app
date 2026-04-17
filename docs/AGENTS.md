## Auth / Favorite 責務の分離

### 目的
認証状態の取得とお気に入り操作の責務を明確に分離し、
無駄なAPI呼び出しや状態不整合を防ぐ。

---

### Auth（認証）責務

- `/api/users/me/` の呼び出しは **AuthProvider のみで実行する**
- 各コンポーネントは `useAuth()` を通じて状態を参照する
- ルート遷移時に再fetchしない（初回マウント時のみ）

#### 禁止事項

- コンポーネントから直接 `/users/me` を叩く
- 複数箇所で認証状態を管理する

---

### Favorite（保存）責務

- 保存状態は以下で管理する
  - preload（SSR or API）
  - クライアントのトグル状態（useFavorite）

- API
  - 追加: `POST /favorites/`
  - 削除: `DELETE /favorites/by-shrine/{id}/`

- UIは**トグル前提**（保存 / 解除）で設計する

---

### 認証と保存の関係

- 未ログイン時
  - 保存操作 → ログイン導線へ遷移

- ログイン済み
  - 即API呼び出し
  - UI状態を即時反映（optimistic update許容）

---

### 設計原則

1. 認証状態はグローバルに1箇所で管理（AuthProvider）
2. データ操作は責務ごとに分離（Auth / Favorite）
3. UIは状態の結果のみを描画（ロジックを持たない）

---

### 補足

- `users/me` の過剰fetchはパフォーマンス劣化の主要因になる
- Providerの多重配置は禁止（再マウントの原因）
