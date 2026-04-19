## 🏛 Shrine Submission Pipeline

神社登録は `shrine` 本体への直接追加ではなく、**`submission` リソースを経由する投稿フロー**として扱う。

目的:

- 神社データ品質の保護
- 投稿責任の追跡
- 承認フローの維持

## Shrine Submission 導線

- 主導線は `shrines search → 0件 → CTA → submission`
- 投稿入口は `/shrines/new`
- `returnTo` により検索画面へ復帰する（詳細は `docs/auth-flow.md` を参照）

## 正本ドキュメント

Shrine Submission に関する詳細仕様は以下を正本とする：

- `docs/shrine-submission-flow.md`（導線 / duplicate_candidate 契約）
- `docs/auth-flow.md`（認証復帰 / returnTo）

本ドキュメントは責務境界の説明に限定する。

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


## duplicate_candidate 契約（正本参照）

duplicate_candidate の詳細契約は以下を正本とする：

- `docs/shrine-submission-flow.md`

本ドキュメントでは責務のみを定義する。

### 責務

- `POST /api/shrine-submissions/` は重複候補がある場合に `duplicate_candidate` を返す
- 判定は serializer ではなく view / service 層で行う
- frontend は response をもとに以下の導線を分岐する
  - 1件: shrine detail へ遷移
  - 複数件: 検索/一覧導線へ遷移

※ JSON構造・フィールド定義は正本ドキュメントを参照すること

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
