> **Status: Archive**
>
> 本ドキュメントは、Recommendation Reason v4導入時点の責務、入力、出力、実装計画およびActive化条件を記録した過去設計である。
>
> 現行のRecommendation Reasonに関するInput / Output / 保存 / 表示 / 互換責務は、`docs/core/recommendation-reason-contract.md`を正本とする。

# Recommendation Reason v4 Contract


## Goal

Recommendation Reason v4 は、推薦された神社について「なぜ今この神社なのか」を、ユーザーが理解しやすい形で説明するための表示理由生成レイヤーである。

このレイヤーは ranking logic を変更しない。
Score v3 / current ranking の結果を説明するための層として扱う。

## Current Reason Generation

現在の推薦理由生成は主に以下で行われている。

- `backend/temples/services/concierge_chat_ranking.py`
  - `_build_reason_facts`
  - `_resolve_primary_reason`
  - `build_recommendation_reason`
  - `_build_need_reason_text`

呼び出し元:

- `backend/temples/services/concierge_chat.py`
  - `rec["reason"] = build_recommendation_reason(...)`

補助整形:

- `backend/temples/services/concierge_chat_presentation.py`
  - `_attach_reason_source`

## Responsibility

Recommendation Reason v4 は以下を担当する。

- 推薦理由を fact / interpretation / action に分離する
- 相談内容と神社側情報の接続を説明する
- Meaning Translation の結果を表示理由に反映する
- decision_context / constraint_profile / outcome_hint を補助材料として使う
- history_theme / action_context の重複表現を減らす
- need_tags.py を相談分類の正本として扱い、reason_v4 はその分類結果を説明文に変換する
- consultation_interpreter.py の出力を、補助解釈として fact / interpretation / action の接続に使う
- reason_v4 は ranking を変更せず、推薦結果を説明する表示層に限定する

## Non Goals

- ranking logic を変更しない
- Score v3 weight を変更しない
- 神社DB構造を変更しない
- UI layout を変更しない
- Premium導線を変更しない
- need_tags.py の分類ロジックを reason_v4 内で再定義しない
- consultation_interpreter.py の補助解釈だけで推薦順位を変更しない

## Input Contract

Reason v4 は以下の入力を読む。

### need_tags.py as source of truth

`backend/temples/domain/need_tags.py` は、相談文から need_tags を抽出する正本である。

Reason v4 は need_tags の分類結果を再判定しない。
`need_profile.need_tags` / `need_profile.primary_need_tag` を、相談テーマの入力として読む。

使用目的:

- 相談テーマをユーザー向け自然文に変換する
- 神社側の history_theme / goriyaku / goriyaku_tags との接続を説明する
- recommendation_reason_v4 の interpretation layer に反映する

### recommendation_input_profile

候補神社とスコア生成に使われた構造化入力。

使用目的:

- candidate_profile の確認
- score_v2 fields の参照
- score_v3 debug との接続確認

### interpretation_profile

相談文から抽出されたユーザー状態。

使用項目:

- raw_query
- state_profile
- need_profile
- direction_profile
- emotion_profile
- action_intent
- decision_context
- constraint_profile
- outcome_hint

`backend/temples/services/consultation_interpreter.py` は、need_tags の正本ではなく補助解釈レイヤーである。

使用方針:

- need_profile は need_tags.py の結果を優先する
- decision_context / constraint_profile / outcome_hint は説明文の補助材料として使う
- state_profile / direction_profile / emotion_profile は現状の reason_v4 本文では直接使わない
- state_profile / direction_profile / emotion_profile は次フェーズで文体調整・テーマ接続・感情トーン調整の候補とする

### meaning_translation

相談解釈を意味レイヤーへ変換した結果。

使用項目:

- history_theme
- shrine_context_need
- action_context
- reflection_question_seed
- source

### candidate shrine profile

神社側の説明材料。

使用項目:

- name
- history_theme
- goriyaku
- goriyaku_tags
- visit_style_tags
- place_id
- behavior_signals

## Output Contract

Reason v4 は以下の構造を返す。

```json
{
  "reason_text": "string",
  "fact": {
    "label": "string",
    "evidence": []
  },
  "interpretation": {
    "theme": "string",
    "text": "string"
  },
  "action": {
    "text": "string",
    "source": "string"
  },
  "source": {
    "fact": "string",
    "interpretation": "string",
    "action": "string"
  }
}
```

## Fact Layer

Fact Layer は、神社側または推薦計算側に存在する事実だけを扱う。

例:

- ご利益タグが一致している
- history_theme が一致している
- 神社の文脈に `再出発` が含まれる
- 距離・参拝スタイルが条件に合う

禁止:

- ユーザーの心理状態を断定しない
- 神社に行けば変わると言い切らない
- 占術的・宗教的な断定をしない

## Interpretation Layer

Interpretation Layer は、相談内容と神社側事実をつなぐ説明を扱う。

使用材料:

- need_profile
- decision_context
- constraint_profile
- outcome_hint
- history_theme
- shrine_context_need

次フェーズ接続候補:

- state_profile: 現在状態を断定せずに補助説明へ反映する候補
- direction_profile: history_theme との接続理由を強める候補
- emotion_profile: 表現の強さやトーンを調整する候補

方針:

- fact と interpretation を混ぜない
- 「あなたは〜です」と断定しない
- 「今の相談には〜が含まれています」程度に留める
- history_theme を本文内で繰り返しすぎない

## Action Layer

Action Layer は、次に取れる小さな行動を提示する。

使用材料:

- action_intent
- outcome_hint
- action_context
- reflection_question_seed

方針:

- 抽象的な「前に進みましょう」で終わらせない
- 参拝前 / 参拝中 / 参拝後のどこに向けた行動かを明確にする
- action_context と同じ表現を繰り返さない

## Duplication Rules

以下の重複を避ける。

### history_theme duplication

避ける例:

- 再出発の神社です。再出発したいあなたに合います。再出発の一歩になります。

改善方針:

- 1回目は theme
- 2回目以降は具体行動や文脈に変換する

### action_context duplication

避ける例:

- 今の状態を整理しましょう。整理するために、整理できる場所です。

改善方針:

- action_context は1回だけ使う
- 補足では「何を」「どの単位で」整理するかを書く

## Quality Audit Connection

Recommendation Quality Audit の以下指標と接続する。

- reason_depth
- action_specificity
- history_theme_fit
- semantic_duplication
- shrine_specificity
- consultation_fit

## Implementation Plan

```markdown
- [ ] docsでReason v4 contractを固定
- [ ] recommendation_reason_v4.py を新規作成
- [ ] build_recommendation_reason_v4() を定義
- [ ] fact / interpretation / action を返す
- [ ] 既存 build_recommendation_reason はまだ置き換えない
- [ ] debug payload に reason_v4_preview を追加
- [ ] Quality Audit に reason_v4_preview を接続
- [ ] 実測後に表示切替を判断
```

## Activation Policy

Reason v4 は初期段階では preview / debug のみで扱う。

表示切替は以下の改善が確認できた場合に検討する。

- reason_depth の改善
- action_specificity の改善
- semantic_duplication の低下
- detail_open_rate の改善
- save_rate の改善
