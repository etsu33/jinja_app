## 🧩 ConciergeChatView 構成

### モジュール位置

`backend/temples/api/views/concierge.py`

### 役割

- LLM（OpenAI API）を通じて参拝プランを生成するエントリポイント
- 現段階では echo レスポンスでスモーク確認（MVP）
- 将来的には `chat_to_plan()` の呼び出しを有効化し、Shrine DB／経路APIと連携

### 設定との関係

| 設定項目 | 内容 |
| --- | --- |
| `REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"]` | `ScopedRateThrottle` |
| `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["concierge"]` | `8/min` |
| View 内 `throttle_scope` | `concierge` |
| `permission_classes` | `AllowAny` |
| `authentication_classes` | `[]`（CSRF回避） |

### 呼び出しフロー

```
Front（Next） → POST /api/concierge/chat/
        ↓
ConciergeChatView.post()
        ↓
入力検証（message|query, lat, lng）
        ↓
chat_to_plan() もしくは Echo レスポンス
        ↓
HTTP 200 / 400 / 429
```

### 今後の拡張予定

- `chat_to_plan()` の本接続（LLM応答 → Shrine モデル特定 → ルート生成）
- ConciergeHistory 永続化と MyPage 連携
- `/api/concierge/recommendations` との設計統合

---

## 🔐 認証状態・プロフィール状態・利用状態の責務境界

本アプリでは、**認証そのもの**・**保存済みプロフィール**・**コンシェルジュ内一時入力**を分離して扱う。

### 1. AuthState

認証状態を表す層。AuthProvider が管理し、画面へ配布する。

```tsx
type AuthStatus = "unknown" | "authenticated" | "guest";

type AuthUser = {
  id: number;
  email?: string | null;
  username?: string | null;
  nickname?: string | null;
  birthday?: string | null;
};

type AuthState = {
  status: AuthStatus;
  user: AuthUser | null;
  isHydrating: boolean;
};
```

**責務**

- ログイン復元
- 認証状態確認
- user の配布
- login / logout / refreshMe の提供

`/api/users/me/` はこの層のために利用し、画面個別の責務に持ち込まない。

### 2. ProfileState

ログイン済みユーザーに保存されたプロフィール情報。

```tsx
type ProfileState = {
  nickname: string | null;
  birthday: string | null;
};
```

**責務**

- 永続プロフィール値の表現
- session 一時入力との分離

### 3. ConciergeSessionState

コンシェルジュ利用中だけ使う一時入力情報。未ログインでも保持できる。

```tsx
type ConciergeSessionState = {
  sessionNickname: string | null;
  temporaryBirthdate: string | null;
};
```

**責務**

- 相談中の呼び名
- 相性モード用の一時的な生年月日
- プロフィール保存とは別管理

---

## Auth / Favorite 責務の明文化

### Auth（認証）責務

認証状態の取得責務は `AuthProvider` に集約する。

- `/api/users/me/` の呼び出しは **AuthProvider のみ** が行う
- 各画面・各コンポーネントは `useAuth()` を通じて認証状態を参照する
- 認証状態を画面ごとに再取得しない
- ルート遷移時に `users/me` を増やさないことを優先する

#### 禁止事項

- コンポーネントから直接 `/api/users/me/` を呼ぶ
- `getCurrentUser()` のような read API を各所で再利用する
- 認証状態を複数箇所で独自管理する

---

### Favorite（保存）責務

favorite の責務は「初期状態の決定」と「保存/解除の更新」で分離する。

#### 初期状態の決定責務

- shrine detail: server 側が SSR initial を解決する
- ranking 一覧: preload により複数件の初期状態を解決する
- mypage favorites: favorites 本体取得をそのまま使う

#### 更新責務

- `useFavorite` は保存 / 解除の更新責務のみを持つ
- UI コンポーネントは更新結果を描画する
- 保存済み状態では再押下で解除できるトグルUIを前提とする

#### API

- 保存: `POST /favorites/`
- 解除: `DELETE /favorites/by-shrine/{id}/` または `DELETE /favorites/{favorite_id}/`

---

### Auth と Favorite の関係

- 未ログイン時に favorite 操作を行った場合はログイン導線へ遷移する
- ログイン済みの場合はその場で保存 / 解除 API を呼ぶ
- UI は再fetch ではなくローカル state 更新を優先する
- 認証状態の取得責務と favorite 状態の更新責務を混在させない

---

### 設計原則

1. 認証状態は `AuthProvider` に一元化する
2. favorite 初期状態の正本は画面ごとに決める
3. component は状態決定より描画責務を優先する
4. Provider の多重配置を避ける
5. `users/me` の過剰fetchを起こさない

---

## 表示名解決

表示名は `resolveDisplayName()` に統一し、以下の優先順位で決定する。

1. `sessionNickname`
2. `profile.nickname`
3. 未設定時は「あなた」

---

## 認証導線

**正規ルート**

- `/auth/login?returnTo=...`
- `/auth/register?returnTo=...`

**互換ルート**

- `/login`
- `/signup`

互換ルートは残すが、内部では正規ルートへリダイレクトする。

---

## favorite 導線の優先順位

favorite 導線の主導線は以下とする。

`concierge -> shrine detail -> save -> mypage`

- concierge は発見導線
- shrine detail は判断と保存の中心画面
- mypage は保存済み神社の再訪導線

ranking / popular は閲覧導線として残すが、MVP では favorite 導線の主責務を持たせない。
そのため、ranking / popular への preload や保存導線の追加投資は現時点では行わない。

将来的に ranking の利用実績や回遊価値が確認できた場合に限り、favorite 初期状態取得の最適化を再検討する。

---

## アクション単位の認証ガード

ログイン必須判定は `isAuthRequiredForAction()` に集約する。

例:

- `save_concierge_thread` → required
- `save_profile` → required
- `toggle_favorite` → required
- `concierge_consult` → not required

判定関数は「必要判定」のみを責務とし、遷移処理は UI 側で扱う。

---

## 画面要件


### `/concierge`

- guest 利用可能
- ConciergeSessionState を使用
- 保存系のみログイン要求

### `/concierge` の favorite 方針

Concierge結果一覧では favorite 操作を提供しない。

理由:

- 本画面は discovery / comparison の導線に特化する
- 保存操作は shrine詳細に集約する
- Hero / Compact に保存UIを載せると責務が肥大化する
- favorite 状態管理の複雑化を避ける

運用方針:

- shrine詳細では SSR initial により保存状態を正として扱う
- 一覧系で favorite を出す場合は preload を使う
- Concierge に favorite を導入する場合は、Hero / Compact 両方のUI責務を再設計してから行う

#### preload の適用対象画面

preload は「複数カードの favorite 初期状態だけを軽く解決する仕組み」として扱う。

適用対象:

- shrine detail: preload ではなく SSR initial を使う
- ranking 一覧: preload を使う
- mypage favorites 一覧: preload ではなく favorites 本体取得を使う

非適用対象:

- concierge 一覧: favorite UI を提供しないため preload を使わない
- popular 一覧: 現時点では preload を使わない

#### concierge → shrine detail の favorite 状態

concierge から shrine detail へ遷移した後の favorite 状態は、detail 側の SSR initial を正本として扱う。

- concierge 一覧では preload を使わない
- shrine detail で server が favorite 済み判定を行う
- `ShrineSaveButton` へ `initial` を渡して表示を決定する

#### favorite UI の単一責務

- shrine detail: server が favorite 初期状態の正本を決める
- ranking 一覧: preload が favorite 初期状態を解決する
- useFavorite: 保存 / 解除の更新責務のみを持つ
- component は初期状態の決定責務を持たない

### `/mypage`

- ログイン必須
- AuthProvider の状態を見て描画分岐する

### `/popular` の favorite 方針

popular 一覧では現時点で preload を適用しない。

理由:

- 本画面は探索導線としての役割が強い
- favorite 初期状態の即時表示より、一覧表示の軽さと単純さを優先する
- preload は ranking のような比較導線に限定して使う

将来的に popular 一覧へ favorite UI を強化する場合は、ranking と同じ preload パターンを再利用する。

---

# 🏛 Shrine Submission Pipeline

神社登録は `shrine` 本体への直接追加ではなく、**`submission` リソースを経由する投稿フロー**として扱う。

目的:

- 神社データ品質の保護
- 投稿責任の追跡
- 承認フローの維持

---

## 投稿主体

投稿は **ログインユーザーのみ** とする。

理由:

- 投稿責任の所在を持てる
- 重複投稿の追跡が可能
- 荒らし対策

anonymous 投稿は採用しない。

---

## Submission 状態

投稿データは `shrine_submission` として保存され、以下の状態を持つ。

- pending
- approved
- rejected

### pending

- 投稿直後の状態
- 公開されない
- 管理レビュー待ち

### approved

- 管理承認済み
- shrine 本体へ反映

### rejected

- 不正・重複・不完全投稿

---

## データモデル（実装済み）

```sql
shrine_submissions
-------------------
id
user_id
name
address
lat
lng
goriyaku_tags
note
status
created_at
reviewed_at
reviewed_by
-------------------
```

---

## Shrine 反映フロー

```
User
 ↓
POST /api/shrine-submissions
 ↓
shrine_submission (pending)
 ↓
admin review
 ↓
approved
 ↓
shrine table insert
```

---

## Duplicate Detection

投稿時に既存神社との重複をチェックする。

基本キー:

- name + address

一致する shrine が存在する場合:

- submission を reject
- または既存 shrine への関連付けを提示する

---

## MVP スコープ外

以下は今回の投稿機能には含めない。

- 画像アップロード
- 御朱印登録の同時実装
- 出典必須化
- 即公開

投稿データは最小構成のみ扱う。

## Shrine Submission Review Flow（実装済み）
- `POST /api/shrine-submissions/` を実装済み
- ログインユーザーのみ投稿可能
- 成功時は `ShrineSubmission(status=pending)` を作成して返す
- 投稿時に以下の重複を検査する
  - 既存 `Shrine(name + address)`
  - 既存 `pending ShrineSubmission(name + address)`
- 投稿時点では `Shrine` 本体は作成しない

`ShrineSubmission` は Django model として実装済み。

### approve
- `approve_shrine_submission()` を経由して承認する
- `pending` のみ承認可能
- 既存 `Shrine(name + address)` と重複する場合は承認しない
- 承認成功時は `Shrine` を新規作成する
- `reviewed_at` / `reviewed_by` を保存する

### reject
- `reject_shrine_submission()` を経由して却下する
- `status=rejected`
- `reviewed_at` / `reviewed_by` / `review_comment` を保存する

### admin
- Django admin の action から approve / reject を実行できる
- approve は service 経由で Shrine 本体へ反映する
- reject は review 情報を保存し、Shrine 本体は作成しない
