
## 🎯 体験設計の責務分離

本プロダクトは「検索・詳細・コンシェルジュ」の役割を明確に分離することで、
UXの肥大化と責務の混在を防ぐ。

## Concierge First

KAMI MUSUBI は Concierge First を採用する。

本プロダクトの主導線は神社検索ではなく、相談テーマから神社と出会う体験とする。

```text
相談テーマ
↓
状態整理
↓
need_tags
↓
history_theme
↓
神社提案
↓
詳細確認
↓
経路案内 / 保存 / 振り返り
```

### 入力責務

主入力:

- 相談テーマ

条件追加:

- 参拝スタイル
- 誕生日
- ご利益タグ

補助シグナル:

- 占星術
- 九星気学
- 風水
- 吉方位
- 相性

### 責務境界

相談テーマは推薦理由の中心とする。

誕生日・占術・吉方位は推薦理由の主軸にしない。

神社一覧や地図は補助導線として扱い、意思決定の中心はコンシェルジュが担う。

### concierge-first.md との関係

- `docs/product/concierge-first.md`
  - 画面導線
  - 入力責務
  - UX方針

### concierge-modes.md との関係

- `docs/product/concierge-modes.md`
  - need mode
  - compat mode
  - mode resolver
  - 推薦ロジック

### Meaning Layer との関係

コンシェルジュは以下の流れで意味生成を行う。

```text
相談テーマ
↓
need_tags
↓
history_theme
↓
神社固有文脈
↓
Meaning Layer
↓
行動提案
```

Meaning Layer の責務は「正解を提示すること」ではなく、「なぜこの神社が今の相談テーマと接続するのか」を説明することである。

---

### 検索（/shrines）

- 目的：候補の発見と比較
- 提供価値：**軽い判断補助**（主価値ではなく補助導線）
- 表現：
  - ご利益タグ
  - 簡易的な「選ぶ理由」
  - 距離・基本情報

制約：

- 長文の推薦理由は出さない
- ユーザーの状態解釈は行わない
- 意味づけは行わない（コンシェルジュに委譲）

---

### 神社詳細（/shrines/[id]）

- 目的：神社の理解
- 提供価値：**情報理解**
- 表現：
  - ご利益
  - 由緒・説明
  - 御朱印
  - 位置情報

制約：

- 過度な推薦ロジックは持たない
- パーソナライズは最小限
- 情報レイヤの詳細は `docs/shrine-detail-layer.md` を正本とする

---

### コンシェルジュ（/concierge）

- 目的：意思決定支援
- 提供価値：**今の自分との意味づけ**
- 表現：
  - なぜこの神社なのか
  - どの状態に対して合っているか
  - 言語化された推薦理由

責務：

- ユーザーの入力（悩み・願い）を解釈する
- ご利益・神社特性と接続する
- 意味のある文脈を生成する

Premium 体験では、この文脈生成をパーソナル理由・相性・継続分析・保存/記録拡張へ深める。詳細は `docs/premium-experience.md` を参照する。

---

## Recommendation Snapshot Policy

コンシェルジュ推薦結果の `score_v2` は、**推薦生成時点のスナップショット**として扱う。

目的:

- 過去の相談結果の再現性を保つ
- 保存済み thread の推薦理由が後から変わることを防ぐ
- 行動状態の現在値と、推薦生成時点の評価値を分離する

### score_v2

`score_v2` は推薦生成時点の評価値であり、`ConciergeThread.recommendations` / `recommendations_v2` に保存された後は再計算しない。

含まれる主な要素:

- user_state_match
- shrine_meaning_match
- context_match
- element_match
- distance_score
- popularity_score
- astro_bonus
- behavior_signal
- ranking_applied

`behavior_signal` は Favorite / Visit / ShrineReflection など、推薦生成時点で確認できたユーザー行動を数値化したものとする。

### action_state

`action_state` は保存済み thread 表示時点の現在DBから判定する。

想定状態:

- none
- saved
- visited
- reflected

そのため、保存済み `score_v2.components.behavior_signal` と現在の `action_state` は一致しない場合がある。

例:

- 推薦生成時点では saved + visited により `behavior_signal = 6.0`
- その後 favorite が削除され、現在DBでは visited のみ
- thread詳細では `score_v2` は 6.0 のまま保持し、`action_state` は visited として表示する

### ranking_applied

`ranking_applied` は、`score_v2` を実際の推薦順位に反映したかを示す。

- `false`: score_v2 は観測・説明用であり、既存ランキングには未反映
- `true`: 新規 recommendation 生成時に score_v2 をランキングへ反映済み

保存済み thread の `score_v2` は再ランキングしない。`ranking_applied=true` の適用対象は、新規 recommendation 生成時のみとする。

### 責務分離

- `score_v2`: 推薦生成時点の評価スナップショット
- `action_state`: 現在DBにもとづくユーザー行動状態
- `ranking_applied`: score_v2 が推薦順位へ反映されたかのフラグ

この分離により、履歴の再現性と現在状態の表示を両立する。

---

### 設計原則

- 検索は「浅く広く」
- 詳細は「正確に」
- コンシェルジュは「深く」

この分離を崩さないことで、UXの一貫性と拡張性を維持する。

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

## 体験境界の正本ドキュメント

体験境界に関する詳細仕様は以下を正本とする：

- `docs/pricing.md`（free / premium の価値境界）
- `docs/premium-experience.md`（Premium 体験境界）
- `docs/shrine-detail-layer.md`（神社詳細の情報レイヤ）

---

## Shrine Submission の正本ドキュメント

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

---

## Shrine / ShrineSubmission の責務分離

`Shrine` は公開検索・ランキング・concierge 推薦で参照される公開マスターとする。

`ShrineSubmission` はユーザー投稿の受付・審査用データであり、pending / rejected の状態では公開検索・推薦対象に含めない。

`ShrineSubmission.goriyaku_tags` は投稿者の意図を示す参考情報であり、`Shrine.goriyaku_tags` とは別物として扱う。検索・推薦に使う正本タグは、管理者が `Shrine.goriyaku_tags` として確定する。

承認時に自動反映するのは `name / address / lat / lng / owner` のみとし、タグ・note は自動反映しない。
