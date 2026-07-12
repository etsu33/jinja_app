# Action Suggestion v4 Contract

## 目的

Action Suggestion v4 は、Recommendation v4 の相談解釈・意味変換・推薦理由を受け取り、ユーザーが次に取りやすい行動提案を安定した Contract として返す仕様を定義する。

本ドキュメントは Action Suggestion の責務、入力、出力、生成ルールを定義する。推薦順位やスコア計算は扱わない。

---

## 全体構造

```text
consultation_interpreter
↓
recommendation_input_profile
↓
meaning_translation
↓
recommendation_reason_v4
↓
action_suggestion_v4
```

---

## 責務

Action Suggestion v4 は、推薦理由を受けて次に取りやすい小さな行動を返す。

### 扱うもの

- primary_action
- secondary_action
- reflection_prompt
- action_source

### 扱わないもの

- Recommendation Ranking
- Recommendation Score
- 神社選定ロジック
- 長文の意味付け
- 結果保証
- 医療・心理・宗教的断定

---

## Input Contract

Action Suggestion v4 は以下の入力を参照できる。

| Input | 役割 |
|-------|------|
| decision_context | 判断対象の整理 |
| constraint_profile | 制約条件の把握 |
| outcome_hint | 望む着地点 |
| action_context | 次に取りやすい行動文脈 |
| reflection_question_seed | 振り返り質問の生成 |

---

## Output Contract

Action Suggestion v4 は以下の Schema を返す。

```json
{
  "primary_action": {
    "label": "string",
    "description": "string",
    "action_type": "detail_open | route_open | save | visit | reflect | pause",
    "confidence": 0.0
  },
  "secondary_action": {
    "label": "string",
    "description": "string",
    "action_type": "detail_open | route_open | save | visit | reflect | pause",
    "confidence": 0.0
  },
  "reflection_prompt": {
    "question": "string",
    "prompt_type": "before_visit | after_visit | decision | emotion | constraint",
    "source_seed": "string"
  },
  "action_source": {
    "source": "decision_context | constraint_profile | outcome_hint | action_context | reflection_question_seed | fallback",
    "reason": "string"
  }
}
```

---

## primary_action

最初に提示する行動。

### ルール

- 1件のみ返す
- 実行可能な行動にする
- 命令口調にしない
- 結果保証をしない
- 必要に応じて pause・reflect を選択できる

---

## secondary_action

primary_action を補完する行動。

### ルール

- primary_action と異なる action_type を返す
- 行動負荷を上げすぎない
- 保存・経路確認・振り返りへ接続する

---

## reflection_prompt

振り返りや意思整理のための問いを返す。

### ルール

- 1問のみ返す
- 心理状態を断定しない
- 宗教的な正解を示さない
- 行動前後の整理を支援する

---

## action_source

生成根拠を保持する。

### ルール

- source は Enum
- reason は短文
- Debug・Test で確認可能とする

---

## action_type

| action_type | 接続先 |
|--------------|--------|
| detail_open | 詳細画面 |
| route_open | 経路表示 |
| save | 保存 |
| visit | 参拝 |
| reflect | 振り返り |
| pause | 整理時間 |

---

## fallback

入力不足でも Schema は維持する。

| 項目 | fallback |
|------|----------|
| primary_action | detail_open |
| secondary_action | save |
| reflection_prompt | before_visit |
| action_source | fallback |

---

## 文言ルール

### 行うこと

- 小さな行動を提案する
- 具体的な動詞を使う
- 判断を急がせない
- 制約を尊重する
- 行動と振り返りを接続する

### 行わないこと

- 必ず行きましょう
- この神社が正解です
- 運気が上がります
- 今すぐ決断してください
- あなたはこういう状態です

---

## 関連ドキュメント

- `docs/product/meaning-translation-mapping.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/visit-reflection-flow.md`

---

## 更新ルール

本ドキュメントは以下の場合のみ更新する。

- Input Contract が変更された場合
- Output Schema が変更された場合
- Action Contract の責務が変更された場合
- action_type が追加・削除された場合

実装状況、テスト、進捗、作業履歴、チェックリストは本書へ記載しない。
