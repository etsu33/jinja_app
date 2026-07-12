# KAMI MUSUBI Architecture

## 目的

本ドキュメントは、KAMI MUSUBI の主要レイヤーと責務境界を1ページで確認するための概要を定義する。

詳細仕様、API契約、実装履歴、テスト方針は各正本ドキュメントへ分離し、本書には全体構造と依存関係のみを残す。

---

## 全体フロー

```text
User Input
↓
Consultation Interpretation
↓
Meaning Translation
↓
Recommendation
↓
Explore / Detail
↓
Route / Save / Visit
↓
Reflection
```

KAMI MUSUBI は Concierge First を採用する。

主導線は神社検索ではなく、相談テーマから神社と出会い、参拝と振り返りへ進む体験とする。

---

## レイヤーと責務

| レイヤー | 責務 | 主な出力 | 責務外 |
|----------|------|----------|--------|
| Consultation Interpretation | ユーザー入力を構造化する | state_profile / need_profile / direction_profile / emotion_profile / action_intent | 推薦順位の決定、心理診断 |
| Meaning Translation | 相談状態と神社文脈を意味情報へ変換する | history_theme / action_context / reflection_question_seed | 表示文言の最終決定、順位変更 |
| Recommendation | 神社候補の選定と推薦理由生成を行う | 候補、理由、Runtime Snapshot | UI表示責務、神社マスター更新 |
| Explore | 候補の発見・比較・位置確認を行う | 一覧、地図、検索結果 | 長文推薦理由、ユーザー状態の解釈 |
| Detail | 神社固有情報を正確に表示する | 由緒、祭神、ご利益、御朱印、位置情報 | 過度な推薦ロジック |
| Action | 参拝前後の具体的な一歩へ接続する | route / save / visit 導線 | 効果保証、行動強制 |
| Reflection | 参拝後の気づきを整理する | prompt / answer / mood / next action | 診断、正解提示 |

---

## Consultation Interpretation

Consultation Interpretation Engine の正本は backend 実装とする。

frontend / mobile は入力、補助条件、表示のみを担当し、相談解釈の判定ロジックを持たない。

```text
raw_query
↓
state_profile
need_profile
direction_profile
emotion_profile
action_intent
```

### 入力の扱い

**主入力**

- 相談テーマ

**条件追加**

- 参拝スタイル
- 誕生日
- ご利益タグ

**補助シグナル**

- 占星術
- 九星気学
- 風水
- 吉方位
- 相性

need_profile を推薦の主要入力とし、誕生日、占術、方位、相性は補助シグナルに限定する。

### 禁止事項

- 心理状態、性格、運命を断定しない
- raw_query を直接スコア加点しない
- ご利益タグだけで推薦理由を完結させない
- frontend / mobile に判定ロジックを重複実装しない
- LLM出力でユーザーの原文を上書きしない

---

## Meaning Translation

Meaning Translation Layer は interpretation_profile を受け取り、translation_result を生成する。

```text
interpretation_profile
↓
translate_meaning()
↓
translation_result
↓
ShrineMeaningComposer
```

主な接続は以下とする。

```text
translation_result.history_theme
→ generated.historyContext

translation_result.action_context
→ generated.actionMeaning

translation_result.reflection_question_seed
→ generated.afterVisitReflection
```

現時点では推薦順位を変更せず、以下に限定する。

- 意味入力の構造化
- 表示文言の補助
- debug / payload上の観測
- Action / Reflection生成の材料

表示文言の最終決定は Composer が担当する。

---

## Recommendation

Recommendation は、神社側の事実・意味情報と、ユーザー側の相談解釈を結合して生成する。

```text
Shrine Fact / Meaning
+
Consultation Interpretation
↓
Recommendation Match
↓
Recommendation Reason
```

Recommendation は以下を分離して扱う。

- 候補選定
- マッチング結果
- 推薦理由
- 表示用コピー
- 行動提案

推薦生成時点の評価値、理由、Actionは、`ConciergeThread.recommendations_v2` へ Runtime Snapshot として保存する。

### Snapshot Policy

- score_v2：推薦生成時点の評価スナップショット
- action_state：現在DBに基づく状態
- ranking_applied：推薦順位へ反映済みかを示すフラグ

保存済み推薦は再計算・再ランキングしない。

現在の Favorite、Visit、Reflection 状態が変化しても、過去の推薦結果は生成時点の値を維持する。

---

## Score v3

Score v3 は shadow mode とし、既存順位を変更しない。

### 観測する component

- state_match_score
- meaning_match_score
- shrine_profile_score
- behavior_score
- history_score
- final_score

### 用途

- 既存ランキングとの差分確認
- componentごとの寄与分析
- Behavior Funnelとの相関確認
- active化判断のための実測

frontend / mobile は `debug.score_v3` を順位決定に利用しない。

---

## 画面責務

```text
Top
↓
Concierge
↓
Explore
↓
Detail
↓
Route
↓
Visit
↓
Reflection
```

| 画面 | 役割 |
|------|------|
| Top | 相談開始 |
| Concierge | 「なぜこの神社か」の生成 |
| Explore | 「どこへ行くか」の探索 |
| Detail | 「どんな神社か」の理解 |
| Route | 「どう行くか」の支援 |
| Visit | 「行った事実」の保存 |
| Reflection | 行動後の意味整理 |

### 設計原則

- 検索は浅く広く
- 詳細は正確に
- コンシェルジュは深く

Explore は Recommendation Logic、Meaning Layer、Recommendation Score を持たない。

Detail は神社理解を担当し、過度なパーソナライズを行わない。

---

## データ責務

### Shrine

公開検索、ランキング、コンシェルジュ推薦で参照される神社マスター。

### ShrineSubmission

ユーザー投稿の受付・審査用データ。

pending、rejected の状態では、公開検索・ランキング・推薦対象に含めない。

```text
User
↓
ShrineSubmission（pending）
↓
Admin Review
↓
approved
↓
Shrine
```

重複判定、承認、却下、API契約は投稿フローの正本ドキュメントへ委譲する。

### Runtime Snapshot

以下は Shrine 固定プロフィールへ保存せず、推薦生成時点のスナップショットとして保持する。

- matched_need_tags
- consultation_axis
- text_score
- text_hint
- score_element
- evidence
- recommendation_reason
- action_suggestion
- score_components

### Behavior Data

行動の意味を混在させない。

- Favorite：保存・候補化
- Visit：参拝実行
- ShrineReflection：参拝後の内省
- ShrineInteractionLog：detail view、route open、card click
- ActionEvent：Action Suggestion の開始・完了

---

## 認証アーキテクチャ

```text
Frontend
↓
Next.js BFF
↓
Django API
↓
JWTAuthentication
```

### 基本方針

- frontend のログイン入口は `/api/auth/login`
- access token / refresh token は HttpOnly Cookie に保存する
- 認証付きAPIは `bffFetchWithAuthFromReq` を経由する
- frontend から backend origin を直接組み立てない
- JWT を localStorage へ保存しない
- 課金、保存、ユーザー状態の判定は backend の `request.user` を正本とする

SessionAuthentication は依存監査が完了するまで即削除しない。

---

## 正本ドキュメント

詳細仕様は以下へ分離する。

- Concierge First：`docs/product/concierge-first.md`
- Concierge Modes：`docs/product/concierge-modes.md`
- Explore：`docs/product/explore-integration-design.md`
- Meaning Layer：`docs/core/meaning-layer.md`
- 神社詳細：`docs/shrine-detail-layer.md`
- Premium：`docs/premium-experience.md`
- 投稿フロー：`docs/shrine-submission-flow.md`
- 認証：`docs/authentication-flow.md`
- Recommendation / Knowledge：`docs/knowledge/`
- 監査：`docs/audit/`

---

## 変更ルール

- 詳細仕様を本書へ再掲しない
- 実装履歴や完了チェックリストを本書へ置かない
- API schema、migration、テストケースは専用ドキュメントへ分離する
- 責務境界または全体依存関係が変わる場合のみ本書を更新する
- 実装状態の細かな変更だけでは本書を更新しない
