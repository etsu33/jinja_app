

# Recommendation v4 Action Suggestion Audit

> **Status: Archive**
>
> 本ドキュメントは、Action Suggestion v4の責務を確認したPhase2時点監査である。
>
> Recommendation ReasonとAction Suggestionの責務境界は `docs/product/action_suggestion_v4.md` を正本とする。

## Goal

Recommendation v4 Phase2 における `action_suggestion_v4` の責務、入力、出力、既存 `recommendation_reason_v4` との境界を整理する。

この監査では、実装追加を主目的にしない。
現在の `action_suggestion_v4` が、Recommendation v4 の相談解釈・意味変換・推薦理由と矛盾なく接続できているかを確認する。

## Current Status

`action_suggestion_v4` はすでに preview payload として実装されている。

正本:

```text
backend/temples/services/action_suggestion_builder.py
```

主な関数:

```text
build_action_suggestion()
attach_action_suggestion_v4_preview()
```

呼び出し元:

```text
backend/temples/services/concierge_chat.py
```

既存テスト:

```text
backend/temples/tests/services/test_action_suggestion_builder.py
backend/temples/tests/api/test_concierge_chat_response_body_contract.py
```

関連docs:

```text
docs/product/action_suggestion_v4.md
docs/product/action-suggestion-layer.md
docs/recommendation-v4-copy-guideline.md
```

## Responsibility

`action_suggestion_v4` は、推薦理由を説明する層ではなく、ユーザーが次に取れる小さな行動を提示する層である。

担当すること:

- 次の小さな行動を提示する
- 保存 / 詳細確認 / 経路確認 / 振り返りへ接続する
- 参拝前または参拝後の問いを提示する
- `consultation_axis` 相当の入力から行動優先度を決める
- `recommendation_reason_v4.action` を fallback として利用する

担当しないこと:

- 推薦順位を説明しない
- 神社のご利益を説明しない
- ユーザーの心理状態を断定しない
- `recommendation_reason_v4.reason_text` と同じ内容を繰り返さない
- `explanation.summary` の代替にならない

## Current Output Contract

`build_action_suggestion()` は以下の構造を返す。

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
  },
  "preview": true,
  "version": "v4",
  "source_keys": []
}
```

## Input Sources

`action_suggestion_v4` は以下を入力として読む。

### recommendation_input_profile

使用目的:

- `interpretation_profile` を取得する
- `translation_result` を取得する
- Recommendation v4 の入力構造と接続する

### interpretation_profile

使用項目:

- decision_context
- constraint_profile
- outcome_hint

現時点では `action_intent` は直接読んでいない。
`action_intent` は `meaning_translation.action_context` に変換されたあと、行動文脈として利用される。

### meaning_translation

使用項目:

- action_context
- reflection_question_seed

### recommendation_reason_v4

使用項目:

- action.text

`meaning_translation.action_context` がない場合、`recommendation_reason_v4.action.text` を fallback として使う。

## consultation_axis Usage

| consultation_axis 相当 | 実装名 | action_suggestion_v4 での扱い |
|---|---|---|
| 判断文脈 | decision_context | 詳細確認を優先し、判断材料を増やす提案にする |
| 制約 | constraint_profile | すぐ行くより、負担確認・詳細確認を優先する |
| 着地点 | outcome_hint | 望む着地点を言葉にする行動へ落とす |
| 行動文脈 | action_context | 問いを決める / 状態を整理する行動に使う |
| 振り返り種 | reflection_question_seed | reflection_prompt の質問として使う |
| 行動意図 | action_intent | 直接は読まず、meaning_translation 経由で反映する |

## Priority Rule

現在の優先順位は以下。

```text
constraint_profile
↓
decision_context
↓
action_context
↓
reflection_question_seed
↓
outcome_hint
↓
fallback
```

この順序は妥当。

理由:

- 制約がある場合、まず無理なく行けるか確認する必要がある
- 判断文脈がある場合、即行動より判断材料の追加が自然
- action_context がある場合、具体行動に落としやすい
- reflection_question_seed は問いとして使いやすい
- outcome_hint は抽象度が高いため、後順位でよい
- 入力不足時は detail_open / save が安全

## Recommendation Reason v4との境界

### recommendation_reason_v4

役割:

```text
なぜこの候補なのかを説明する
```

主な出力:

- fact
- interpretation
- action
- reason_text

### action_suggestion_v4

役割:

```text
次に何をするかを提示する
```

主な出力:

- primary_action
- secondary_action
- reflection_prompt
- action_source

### 重複させないこと

避ける表現:

```text
今の状態を整理しましょう。
問いを一つに絞りましょう。
判断材料を増やしましょう。
```

これらは reason と action の両方に出やすい。
`recommendation_reason_v4` 側では文脈説明に留め、`action_suggestion_v4` 側で実行単位に落とす。

## Copy Audit

### 現状で良い点

- `primary_action` と `secondary_action` が分かれている
- `reflection_prompt` が独立している
- `action_source` で根拠が追跡できる
- fallback が `detail_open` と `save` で安全
- 既存 `action_suggestions` を破壊せず preview として追加している

### 注意点

- `action_context` をそのまま description に使う箇所がある
- `recommendation_reason_v4.action.text` を fallback に使うため、reason 側と重複する可能性がある
- `action_intent` を直接読んでいないため、将来的に intent を action_type に反映する余地がある
- `attach_action_suggestion_v4_preview()` は `_explanation_payload.action_suggestions` 起点で meaning_translation を仮組みしているため、true v4 pipeline とはまだ完全一致ではない

## Current Judgment

現時点では、`action_suggestion_v4` の大きな実装修正は不要。

理由:

- schema が安定している
- preview として additive に実装されている
- existing action_suggestions を破壊していない
- consultation_axis の主要要素を利用している
- fallback が安全側に倒れている

ただし、Recommendation v4 全体で active 化する前に以下を確認する。

```markdown
- [ ] recommendation_reason_v4.action と primary_action.description の重複率
- [ ] action_context がそのまま表示されすぎていないか
- [ ] action_intent を直接読む必要があるか
- [ ] attach_action_suggestion_v4_preview が true v4 input を受け取るべきか
```

## explanation_v4との関係

`explanation_v4` という名前の専用実装は現時点では存在しない。

現在の explanation 系は以下。

```text
backend/temples/services/concierge_explanation_payload.py
backend/temples/services/concierge_explanations.py
```

`action_suggestion_v4` は explanation の一部ではなく、行動提案の preview payload として扱う。

ただし現在は `_explanation_payload.action_suggestions` を参照して `action_suggestion_v4_preview` を作っているため、完全には独立していない。

今後の整理方針:

```text
explanation
↓
なぜこの候補かを説明する

action_suggestion_v4
↓
次に何をするかを提案する
```

## reason_factsとの関係

`reason_facts` は以下で生成される。

```text
backend/temples/services/concierge_chat_ranking.py
```

主な箇所:

```text
_build_reason_facts()
rec["_reason_facts"] = reason_facts
```

`_reason_facts` は explanation payload で正規化される。

```text
backend/temples/services/concierge_explanation_payload.py
```

`action_suggestion_v4` は現時点で `reason_facts` を直接読まない。

判断:

- reason_facts は推薦理由・explanation の根拠
- action_suggestion_v4 は相談文脈と行動文脈の接続
- 直接結合しない方が責務はきれい

## Test Scope

この監査後に実行するテスト。

```bash
USE_SQLITE=0 python -m pytest temples/tests/services/test_action_suggestion_builder.py
```

```bash
python -m py_compile temples/services/action_suggestion_builder.py temples/tests/services/test_action_suggestion_builder.py
```

必要に応じて追加するテスト。

```bash
USE_SQLITE=0 python -m pytest temples/tests/api/test_concierge_chat_response_body_contract.py -k action_suggestion_v4
```

## TODO

```markdown
- [x] action_suggestion_v4 の生成箇所を確認
- [x] action_suggestion_v4 の呼び出し元を確認
- [x] action_suggestion_v4 のテストを確認
- [x] consultation_axis 利用状況を確認
- [x] recommendation_reason_v4 との責務境界を整理
- [x] explanation_v4 の有無を確認
- [x] reason_facts との関係を整理
- [x] 大きな実装修正は不要と判断
- [ ] backend pytest
- [ ] py_compile
```

## Next Step

このPRでは、まず `action_suggestion_v4` の監査docsを追加する。

次に `explanation_v4` ではなく、既存 explanation 系の監査へ進む。

```text
backend/temples/services/concierge_explanation_payload.py
backend/temples/services/concierge_explanations.py
```

その後、`consultation_axis整合性監査` と `reason_facts backend E2E` へ進む。
