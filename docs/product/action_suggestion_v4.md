

# Action Suggestion v4 Contract

## 目的

Action Suggestion v4 は、Recommendation v4 の相談解釈・意味変換・推薦理由を受け取り、ユーザーが次に取りやすい行動提案を安定した schema で返すための Preview 契約である。

この contract は、推薦順位や ranking logic を変更せず、表示・説明・振り返りに使う action_suggestion の責務だけを固定する。

```txt
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

## ゴール

- 行動提案を抽象文から具体的な実行単位へ寄せる
- recommendation reason と action suggestion の責務を分離する
- reflection flow へ接続できる問いを返す
- schema を安定させ、Preview として観測できる状態にする

---

## 現在地

Recommendation v4 では、相談文を以下の構造に分解する方針がある。

- raw_query
- state_profile
- need_profile
- direction_profile
- emotion_profile
- action_intent

v4 追加候補として以下がある。

- decision_context
- constraint_profile
- outcome_hint

Action Suggestion v4 では、これらを行動提案の input として扱う。

---

## 非ゴール

Action Suggestion v4 では以下を行わない。

- ranking logic を変更しない
- Score v3 weight を変更しない
- 神社DB構造を変更しない
- 推薦候補の順位を入れ替えない
- 課金導線UIを変更しない
- 医療・心理・宗教的な断定をしない
- 参拝を強制しない

---

## 責務分離

### recommendation_reason_v4 の責務

推薦理由は、なぜこの神社が相談文脈と接続するのかを説明する。

扱うもの:

- 相談状態
- 神社の意味
- history_theme
- ご利益との接続
- 推薦理由の根拠

扱わないもの:

- 次に何をするかの具体手順
- 振り返り問い
- 行動完了後の記録文脈

---

### action_suggestion_v4 の責務

行動提案は、推薦理由を受けて、ユーザーが次に取れる小さな行動を提示する。

扱うもの:

- primary_action
- secondary_action
- reflection_prompt
- action_source

扱わないもの:

- 神社推薦順位
- 神社選定ロジック
- スコア計算
- 長文の意味づけ
- 結果保証

---

## Input Contract

Action Suggestion v4 は、以下の input を参照できる。

### decision_context

ユーザーが何を決めようとしているかを表す。

例:

- 転職するか
- 休むか動くか
- 関係を続けるか
- お金を使うか守るか

用途:

- 行動提案の方向性を決める
- 決断を急がせず、整理単位へ分解する

---

### constraint_profile

ユーザーの制約条件を表す。

例:

- 時間がない
- お金が不安
- 体力が落ちている
- 人間関係の制約がある

用途:

- 実行不能な提案を避ける
- 小さく始められる行動に落とす

---

### outcome_hint

ユーザーが望む着地点を表す。

例:

- 決めたい
- 落ち着きたい
- 背中を押されたい
- 整理したい

用途:

- primary_action の表現トーンを決める
- reflection_prompt の問いを調整する

---

### action_context

ユーザーが次に取りやすい行動文脈を表す。

例:

- 参拝する
- 詳細を見る
- 保存する
- 経路を確認する
- 振り返る

用途:

- primary_action / secondary_action の候補生成
- route_open / save / reflection flow との接続

---

### reflection_question_seed

振り返りに使う問いの種を表す。

例:

- 何を整理したいか
- 何を手放したいか
- どの判断を急がず見たいか
- 参拝後に何を確認したいか

用途:

- reflection_prompt の生成
- reflection_saved_rate 改善のための問い設計

---

## Output Contract

Action Suggestion v4 は、必ず以下の schema を返す。

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

### 目的

ユーザーに最初に提示する、もっとも取りやすい行動を表す。

### ルール

- 1つだけ返す
- 具体的な実行単位にする
- 命令形にしすぎない
- 結果保証をしない
- 迷いが強い場合は pause / reflect を優先できる

### 例

```json
{
  "label": "まず詳細を見て、行く理由を確認する",
  "description": "今はすぐ決めるより、この神社が相談内容とどう接続しているかを確認する段階です。",
  "action_type": "detail_open",
  "confidence": 0.82
}
```

---

## secondary_action

### 目的

primary_action の次に取りうる補助行動を表す。

### ルール

- primary_action と同じ action_type にしない
- 行動負荷を上げすぎない
- 保存・経路確認・振り返りのいずれかへ接続する

### 例

```json
{
  "label": "候補として保存して、あとで見返す",
  "description": "今すぐ行けない場合でも、判断材料として残しておけます。",
  "action_type": "save",
  "confidence": 0.74
}
```

---

## reflection_prompt

### 目的

行動前後に、ユーザーが自分の状態を整理するための問いを返す。

### ルール

- 1問だけ返す
- 心理状態を断定しない
- 宗教的な正解を示さない
- 参拝前・参拝後・決断前のいずれかに接続する

### 例

```json
{
  "question": "この神社に行くとしたら、何を決めるためではなく、何を整理する時間にしたいですか？",
  "prompt_type": "before_visit",
  "source_seed": "整理したい"
}
```

---

## action_source

### 目的

行動提案がどの input から作られたかを保持する。

### ルール

- source は enum で返す
- reason は短く返す
- デバッグとテストで確認できるようにする

### 例

```json
{
  "source": "constraint_profile",
  "reason": "体力や時間の制約があるため、すぐ参拝ではなく詳細確認を優先した"
}
```

---

## action_type 定義

| action_type | 意味 | 主な接続先 |
|---|---|---|
| detail_open | 神社詳細を見る | detail_open_rate |
| route_open | 経路を確認する | route_open_rate |
| save | 候補として保存する | save_rate |
| visit | 実際に訪問する | visit_done_rate |
| reflect | 振り返る | reflection_saved_rate |
| pause | すぐ行動せず整理する | reflection flow |

---

## fallback ルール

input が不足している場合でも、schema は壊さない。

fallback 時の方針:

- primary_action は detail_open を優先する
- secondary_action は save を優先する
- reflection_prompt は before_visit を優先する
- action_source.source は fallback にする

---

## 文言ルール

### やる

- 小さな行動にする
- 具体的な動詞を使う
- 判断を急がせない
- ユーザーの制約を尊重する
- 行動と振り返りを接続する

### やらない

- 必ず行きましょう
- この神社が正解です
- 運気が上がります
- 今すぐ決断してください
- あなたはこういう状態です

---

## KPI

Action Suggestion v4 は、以下の改善に寄与することを狙う。

- detail_open_rate
- save_rate
- route_open_rate
- reflection_saved_rate

ただし、この contract PR では計測ロジックや ranking logic は変更しない。

---

## Preview 運用

この contract は Preview として扱う。

Preview 期間では以下のみ許可する。

- schema を返す
- debug / test で確認する
- response payload に含める候補として扱う

Preview 期間では以下を禁止する。

- ranking に反映する
- UI主導線を変更する
- 課金導線に接続する
- Score v3 weight を変更する

---

## Test Plan

- stable schema pytest を追加する
- primary_action / secondary_action / reflection_prompt / action_source が常に存在することを確認する
- action_type が enum 内であることを確認する
- fallback 時にも schema が壊れないことを確認する
- py_compile を通す

---

## TODO

```markdown
- [x] develop最新化
- [x] feature/action-suggestion-v4-contract 作成
- [x] docs/product/action_suggestion_v4.md 作成
- [x] action_suggestion の責務整理
- [x] recommendation_input_profile 接続
- [x] meaning_translation 接続
- [x] recommendation_reason_v4 接続
- [x] decision_context 利用方針
- [x] constraint_profile 利用方針
- [x] outcome_hint 利用方針
- [x] action_context 利用方針
- [x] reflection_question_seed 利用方針
- [x] primary_action 定義
- [x] secondary_action 定義
- [x] reflection_prompt 定義
- [x] action_source 定義
- [ ] stable schema pytest
- [ ] py_compile
- [x] ranking変更禁止
- [x] Score v3 weight変更禁止
- [x] 神社DB構造変更禁止
- [x] Previewのみ
```
