> **Status: Active**
>
> 本ドキュメントは、KAMI MUSUBIにおける相談テーマ・相談状態・ご利益・神社文脈・行動・振り返りを`history_theme`へ接続する変換仕様の正本である。
>
> `history_theme`のカテゴリ名称と定義は、`docs/product/history-theme-taxonomy.md`を正本とする。

# Meaning Translation Mapping

## 目的

相談内容から神社推薦、行動提案、振り返りまでを一貫した意味文脈で接続するための変換関係を定義する。

本書の対象範囲は以下とする。

- `theme_key`から相談解釈への接続
- 相談状態から`history_theme`への変換
- ご利益から`history_theme`への補助変換
- 神社への`history_theme`付与方針
- `history_theme`からAction・Reflectionへの接続
- Recommendation・Runtime Snapshot・Analyticsとの接続

本書は、一つの入力から一つの答えを機械的に決定する表ではない。

自由入力を相談解釈の正本とし、相談テーマ・ご利益・誕生日・占術情報は補助シグナルとして扱う。

---

## 全体フロー

```text
相談テーマ / 自由入力
↓
Consultation Interpretation
↓
state_profile
need_profile
consultation_axis
emotion_profile
↓
Meaning Translation
↓
history_theme
action_context
reflection_question_seed
↓
Shrine Fact / Shrine Meaning
↓
Recommendation Match
↓
Recommendation Reason
Action Suggestion
↓
Visit
↓
Reflection
```

Meaning Translationは、推薦の意味づけを担う補助レイヤーであり、推薦順位を単独で決定しない。

---

## 基本原則

- 自由入力を相談内容の正本として扱う
- `need_tags`を推薦入力の主軸とする
- `theme_key`はUI入力の初期ヒントとして扱う
- ご利益は願いの入口として扱う
- `history_theme`は神社側の意味文脈として扱う
- 誕生日・占術・相性・方位は補助シグナルとして扱う
- 同じ入力でも、相談文脈によって異なる`history_theme`への接続を許容する
- 推薦順位・スコア計算はBackendを正本とする
- 心理・医療・宗教・人生について断定しない

---

## 入力の優先順位

| 項目 | 優先度 | 役割 |
|---|---:|---|
| `query` / 自由入力 | 高 | ユーザーの相談内容の正本 |
| `need_tags` | 高 | 推薦入力の主軸 |
| `matched_need_tags` | 高 | ユーザー意図と神社情報の一致結果 |
| `consultation_axis` | 中 | 相談意図の分類 |
| `state_profile` | 中 | 現在状態の構造化 |
| `history_theme` | 中 | 神社側の意味文脈 |
| `goriyaku_tag_ids` | 低〜中 | 明示された願い |
| `theme_key` | 低 | UI選択の入口 |
| 誕生日・相性・占術・方位 | 低 | 補助シグナル |

優先順位は以下とする。

```text
query / 自由入力
↓
need_tags
↓
matched_need_tags
↓
consultation_axis / state_profile
↓
theme_key
↓
補助条件
```

`theme_key`・ご利益・誕生日・占術・方位だけで推薦結果を決定しない。

---

## 相談テーマから推薦入力への接続

相談テーマは、相談解釈の初期ヒントとして利用する。

```text
相談テーマ
↓
theme_key
↓
consultation_axis候補
need_tags候補
history_theme候補
↓
Consultation Interpretation
```

相談テーマの表示文言・内部キーは、`docs/product/consultation-theme-taxonomy.md`を正本とする。

| theme_key | consultation_axis候補 | primary need_tags | secondary need_tags | history_theme候補 |
|---|---|---|---|---|
| `work` | `career_change` | `career` | `courage` / `mental` | 勝負 / 再出発 / 学び |
| `relationship` | `relationship_repair` | `relationship` | `love` / `mental` | 縁 / 静寂 |
| `money` | `money_growth` | `money` | `career` / `courage` | 守り / 勝負 / 再出発 |
| `challenge` | `restart_mindset` | `courage` | `career` / `mental` | 勝負 / 再出発 / 学び |
| `rest` | `nature_reset` | `rest` | `mental` | 静寂 / 復興 |
| `health` | `health` | `health` | `protection` / `rest` | 守り / 復興 |
| `study` | `study_success` | `study` | `focus` / `courage` | 学び / 勝負 |
| `future` | `restart_mindset` | `mental` | `courage` / `career` | 再出発 / 静寂 / 学び |

### ルール

- `theme_key`から`consultation_axis`や`need_tags`を直接確定しない
- 自由入力がある場合は自由入力を優先する
- 相談テーマと自由入力が矛盾する場合は自由入力を優先する
- 相談テーマはユーザー状態の断定に使用しない

---

## 相談状態からhistory_themeへの変換

相談状態は、直接ご利益へ変換せず、一度`history_theme`へ翻訳する。

```text
相談状態
↓
history_theme
↓
神社文脈
↓
推薦理由
```

| 相談状態 | primary history_theme | secondary history_theme | 解釈 |
|---|---|---|---|
| 不安が強い | 守り | 静寂 | 土台を整え、刺激から距離を置く |
| 将来が見えない | 再出発 | 静寂 | 立ち止まり、方向を見直す |
| 疲れている | 静寂 | 復興 | 休息と回復を優先する |
| 落ち込んでいる | 復興 | 静寂 | エネルギーを取り戻す |
| やり直したい | 再出発 | 復興 | 区切りを作り、立て直す |
| 転職を考えている | 再出発 | 勝負 | 環境変化と決断 |
| 独立したい | 勝負 | 再出発 | 挑戦と新しい段階への移行 |
| 挑戦したい | 勝負 | 学び | 行動と準備 |
| 決断したい | 勝負 | 守り | 選択とリスク整理 |
| 自信がない | 復興 | 学び | 自己効力感と積み上げ |
| 勉強したい | 学び | 勝負 | 継続と成果への行動 |
| 人間関係で悩んでいる | 縁 | 静寂 | 関係性と距離感の整理 |
| 健康が不安 | 守り | 復興 | 生活基盤と回復 |
| お金が不安 | 守り | 再出発 | 不安を減らし、生活を整える |
| 商売を伸ばしたい | 勝負 | 再出発 | 成長と変化 |
| 自分を見つめ直したい | 静寂 | 学び | 内省と理解 |

---

## ご利益からhistory_themeへの変換

ご利益は、ユーザーが願いを入力しやすくするための入口として扱う。

```text
ご利益
↓
history_theme
↓
Shrine Meaning
↓
Recommendation Reason
```

| ご利益 | primary history_theme | secondary history_theme | 解釈 |
|---|---|---|---|
| 金運 | 守り | 勝負 / 再出発 | 生活基盤・収入・働き方 |
| 商売繁盛 | 勝負 | 再出発 | 商い・挑戦・成長 |
| 仕事運 | 勝負 | 学び | 決断・努力・成果 |
| 開運 | 再出発 | 勝負 | 区切り・流れの変化 |
| 厄除け | 守り | 復興 | 不安やリスクから距離を置く |
| 縁結び | 縁 | 守り | 人・機会とのつながり |
| 学業成就 | 学び | 勝負 | 積み上げ・継続 |
| 病気平癒 | 復興 | 守り | 回復・生活基盤 |
| 家内安全 | 守り | 縁 | 暮らしと家族 |
| 交通安全 | 守り | 再出発 | 安全な移動と新しい行動 |

### ルール

- ご利益だけで`history_theme`を確定しない
- 相談内容とご利益を組み合わせて意味を決定する
- 効果・運勢・宗教的結果を保証しない
- UIへ「この神社で願いが叶う」と表示しない

### 表現例

使用しない表現：

```text
この神社へ行けば金運が上がります。
```

使用する表現：

```text
金運という願いを、今は生活基盤を整えるテーマとして受け止めています。
```

---

## history_theme

`history_theme`は、ユーザーではなく神社が持つ意味文脈を表す。

カテゴリ名称と定義は、`docs/product/history-theme-taxonomy.md`を正本とする。

MVPでは以下の7カテゴリを使用する。

- 守り
- 静寂
- 再出発
- 復興
- 勝負
- 学び
- 縁

### 利用範囲

- Recommendation Reason
- Meaning Card
- Action Suggestion
- Visit
- Reflection
- Runtime Snapshot
- Analytics

Frontend・Backend・Analyticsで独自のカテゴリ名を追加しない。

---

## 神社へのhistory_theme付与

神社の`history_theme`は、以下を総合して決定する。

- 御祭神
- 神社の由緒
- 歴史的背景
- ご利益
- 土地性
- コンシェルジュで伝える意味

ご利益だけで分類しない。

| 神社の特徴 | 主なhistory_theme |
|---|---|
| 商売繁盛・勝運 | 勝負 |
| 縁結び・良縁 | 縁 |
| 厄除け・家内安全 | 守り |
| 学業・知恵 | 学び |
| 病気平癒・回復 | 復興 |
| 静かな山・自然・内省 | 静寂 |
| 再建・再生・転機 | 再出発 |

### 管理方針

- 本番推薦対象の神社は原則として`history_theme`を持つ
- 情報不足の場合のみ一時的な未設定を許容する
- テスト用神社は本番分析対象から除外する
- 新規神社はAdmin Reviewで`history_theme`を確定する

```text
Shrine Submission
↓
Admin Review
↓
history_theme決定
↓
公開
```

---

## Actionとの接続

`history_theme`は、推薦理由だけでなく次の行動文脈へ接続する。

```text
history_theme
↓
action_context
↓
Action Suggestion
```

| history_theme | 行動テーマ | 参拝時の例 | 日常行動例 |
|---|---|---|---|
| 守り | 土台を整える | 今守りたいものを一つ思い浮かべる | 生活基盤を一つ整える |
| 静寂 | 情報から距離を置く | 静かな時間を過ごす | 通知を切る・休む |
| 再出発 | 区切りを作る | 手放したいことを言葉にする | 次の一歩を一つ決める |
| 復興 | 回復を優先する | 疲れを認める | 睡眠・食事・休息を整える |
| 勝負 | 次の一歩を決める | 決めたいことを書き出す | 応募・相談・予約を行う |
| 学び | 積み上げる | 学びたいことを確認する | 短時間の学習を行う |
| 縁 | 関係を育てる | 大切な人を思い浮かべる | 感謝・連絡・距離調整を行う |

Action Suggestionの契約は、`docs/product/action_suggestion_v4.md`を参照する。

---

## Visitとの接続

Visitは、参拝または推薦後の行動完了を記録するレイヤーとして扱う。

```text
Route
↓
Visit
↓
Reflection
```

Visitでは以下を保持する。

- `shrineId`
- `threadId`
- `history_theme`
- `actionTheme`
- `visitedAt`

Visitの保存・イベント責務は、`docs/product/visit-reflection-flow.md`を参照する。

---

## Reflectionとの接続

Reflectionは、結果の正解を評価するものではなく、参拝・行動後の状態変化を記録する。

```text
history_theme
↓
reflection_question_seed
↓
Reflection
```

| history_theme | Reflection例 |
|---|---|
| 守り | 今日、守れたことは何か |
| 静寂 | 静かになれた瞬間はあったか |
| 再出発 | 区切りをつけられたことは何か |
| 復興 | 回復のためにできたことは何か |
| 勝負 | 今日、決めたことは何か |
| 学び | 今日、積み上げたことは何か |
| 縁 | 今日、大切にした縁は何か |

保存対象：

- `history_theme`
- `actionTheme`
- `prompt`
- `answer`
- `moodBefore`
- `moodAfter`
- `createdAt`

保存しないもの：

- 心理診断
- 医療判断
- 宗教的達成判定
- AIによる人生評価

---

## Recommendationとの接続

Meaning Translationは、Recommendationに以下の情報を提供する。

- `need_tags`
- `consultation_axis`
- `state_profile`
- `history_theme`
- `action_context`
- `reflection_question_seed`
- Shrine Fact
- Shrine Meaning

```text
Consultation Interpretation
↓
Meaning Translation
↓
history_theme
↓
Recommendation Match
↓
Recommendation Reason
```

Meaning Translationは推薦理由を補助するが、推薦順位やScoreを単独で決定しない。

---

## Runtime Snapshot

Recommendation生成時には、意味変換結果をRuntime Snapshotへ保存する。

保持対象：

- `history_theme`
- `matched_need_tags`
- `recommendation_reason`
- `action_context`
- `reflection_question_seed`
- `action_suggestion`
- Score Components

Runtime Snapshotは推薦生成時点の状態を保持し、保存後に再計算しない。

Favorite・Visit・ユーザー属性が後から変化しても、生成時点の推薦内容を維持する。

---

## Analyticsとの接続

Meaning Translationは、Behavior Funnelの分析軸として利用する。

```text
Consultation
↓
Recommendation
↓
Detail
↓
Route
↓
Visit
↓
Reflection
```

主な分析対象：

- Recommendation CTR
- Detail View Rate
- Route Open Rate
- Visit Rate
- Reflection Rate
- 継続利用率
- `history_theme`別CVR
- `history_theme`別継続率

Analyticsでは、`docs/product/history-theme-taxonomy.md`で定義されたカテゴリ名を使用する。

---

## 責務境界

### Meaning Translation

- 相談内容の意味整理
- `history_theme`候補の生成
- 神社文脈との接続
- `action_context`の生成
- `reflection_question_seed`の生成
- Recommendation Reasonへの情報提供
- Runtime Snapshotへの情報提供
- Analytics軸の提供

### Recommendation

- 神社候補の抽出
- Score計算
- 推薦順位の決定
- 一致結果の生成

### Frontend

- 推薦理由を表示する
- Action・Reflectionへの導線を表示する
- Backendが返した意味変換結果を保持する

### 責務外

- UIレイアウトの決定
- 神社マスターの直接更新
- 行動の強制
- 効果保証
- 心理診断
- 医療判断
- 宗教的判断

---

## 関連ドキュメント

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/narrative-guideline.md`
- `docs/product/README.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/consultation-theme-taxonomy.md`
- `docs/product/history-theme-taxonomy.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/visit-reflection-flow.md`

---

## 更新ルール

- 本書はMeaning Translationの変換関係と接続方針を管理する。
- `history_theme`のカテゴリ名称・定義は本書で重複管理しない。
- 相談テーマの表示文言・内部キーは本書で重複管理しない。
- 推薦順位・Score計算・UI実装・API契約は各責務の正本で管理する。
- 相談状態・ご利益・神社文脈・Action・Reflectionとの対応関係が変更された場合のみ更新する。
- TODO、PR計画、実装進捗、テスト手順、作業履歴は本書へ記載しない。
