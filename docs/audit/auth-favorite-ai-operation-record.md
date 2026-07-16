> **Status: Archive**
>
> 本ドキュメントは、Auth・Favoriteの責務分離、およびAI支援時のTerminal Command出力ルールを整理した過去の運用記録である。
>
> 現行の認証仕様、Favorite契約、AI運用ルールの正本としては使用しない。
>
> 現在の参照先は以下とする。
>
> - 認証アーキテクチャ：`docs/core/authentication-flow.md`
> - 認証画面遷移・`returnTo`：`docs/core/auth-flow.md`
> - 全体設計：`docs/core/architecture.md`
> - Favoriteの正確なAPI・状態管理：関連するFrontend・Backend実装およびテスト
> - AI支援時の作業ルール：Projectの現在の運用指示

# Auth・Favorite責務分離とAI運用記録

## 目的

本書は、認証状態とFavorite操作の責務が混在していた時期に、Frontendの状態管理とAPI呼び出しを分離するために作成された記録である。

あわせて、AI支援によるTerminal操作時のCommand崩れを防ぐため、Command出力形式の運用ルールを記録していた。

現在は、認証仕様と作業ルールがそれぞれ別の正本へ分離されたため、本書はArchiveとして保持する。

---

## AuthとFavoriteの責務分離

### 当時の背景

認証状態の取得とFavorite操作が複数のComponentで行われると、以下の問題が起こる可能性があった。

- `/api/users/me/` の重複Request
- 認証状態の不一致
- Providerの多重配置
- Route遷移時の不要な再Fetch
- Favorite表示と保存状態のずれ

このため、認証状態とFavorite操作を分離する方針が採用された。

---

## Authの責務

認証状態は、Frontend全体で一か所に集約する方針とした。

### 当時の原則

- `/api/users/me/` の取得は`AuthProvider`へ集約する
- Componentは`useAuth()`を通じて認証状態を参照する
- Componentごとに認証状態を個別管理しない
- Providerを重複配置しない
- Route遷移ごとに不要な再Fetchを行わない

現在の認証経路・Cookie・BFF・JWTの責務は、`docs/core/authentication-flow.md`を正本とする。

---

## Favoriteの責務

Favoriteは、認証状態とは別の保存操作として扱う方針とした。

### 当時の原則

- 保存済み状態は初期DataとClient Stateから構成する
- 保存・解除をToggle操作として扱う
- 未ログイン時は認証導線へ遷移する
- ログイン済みの場合のみ保存APIを呼び出す
- UIは保存結果を表示し、認証判定や業務ロジックを重複して持たない
- 必要に応じてOptimistic Updateを利用する

当時想定していたAPIは以下だった。

```text
POST /favorites/
DELETE /favorites/by-shrine/{id}/
```

現在のEndpoint・Payload・Permission・State管理は、関連する実装コードとテストを最終的な正本とする。

---

## AuthとFavoriteの関係

当時の画面動作は、以下のように整理されていた。

```text
未ログイン
↓
Favorite操作
↓
LoginまたはSignupへ遷移
↓
認証成功
↓
元の画面へ復帰
↓
保存操作を継続
```

```text
ログイン済み
↓
Favorite APIを呼び出す
↓
保存状態を更新
↓
UIへ反映
```

認証後の復帰導線と`returnTo`の仕様は、`docs/core/auth-flow.md`を参照する。

---

## 当時の設計原則

- 認証状態はFrontend全体で一か所に集約する
- AuthとFavoriteのData操作を分離する
- UI Componentへ業務判定を持たせない
- API呼び出しの責務を重複させない
- Providerの多重配置を避ける
- Stateの正本を複数作らない

現在の全体的な責務境界は、`docs/core/architecture.md`を参照する。

---

## AI支援時のTerminal Commandルール

本書には、AI支援によるTerminal操作でCommandが崩れる事故を防ぐための運用ルールも記録されていた。

### 当時のルール

- Terminalへ貼り付けるCommandは一行で提示する
- Backslashによる改行継続を使用しない
- 複数行Commandを一つのCommandとして提示しない
- そのままCopy & Pasteできる形式にする

このルールは、VS Code TerminalやShellへの貼り付け時に、Commandが意図せず分割・実行される事故を避けるために採用された。

現在のAI支援ルールは、Projectで定義されている最新の運用指示を正本とする。

---

## 本書が保持するもの

- AuthProviderへ認証状態を集約した背景
- AuthとFavoriteの責務を分離した判断
- FavoriteをToggleとして扱う設計意図
- Provider多重配置や過剰Fetchを避ける方針
- AI支援時のTerminal Command事故を防ぐための運用履歴

---

## 本書が扱わないもの

- 現在の認証アーキテクチャ
- 現在のCookie・JWT契約
- 現在のFavorite API契約
- 現在のFrontend State構造
- 現在のLogin・Signup導線
- 現在のAI運用ルール
- TODO
- PR候補
- 実装計画
- 作業進捗

---

## 関連ドキュメント

- `docs/core/authentication-flow.md`
- `docs/core/auth-flow.md`
- `docs/core/architecture.md`
- `docs/README.md`

---

## 更新ルール

- 本書は過去のAuth・Favorite責務整理およびAI運用記録として保持する
- 現行実装や運用ルールの変更に合わせて更新しない
- 当時の判断内容に重大な事実誤認が確認された場合のみ修正する
- TODO、PR候補、実装計画、現在の運用指示は記載しない
