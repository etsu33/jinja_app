

# Recommendation v4 Copy Guideline

## Goal

Recommendation v4 Copy Guideline は、Recommendation Reason v4 の推薦理由を、ユーザーが理解しやすく、行動につながりやすい文面に整えるためのコピー品質ルールである。

このガイドラインは以下を目的とする。

- `recommendation_reason_v4` の文面品質を安定させる
- `fact / interpretation / action` の責務を混ぜない
- `consultation_axis` 相当の入力を、ユーザー向けの自然な文に変換する
- 抽象表現・重複表現・断定表現を減らす
- 神社固有情報と相談文脈の接続を強める

## Scope

対象は以下。

- `backend/temples/services/recommendation_reason_v4.py`
- `build_recommendation_reason_v4()`
- `reason_text`
- `fact`
- `interpretation`
- `action`
- `docs/recommendation-reason-v4-contract.md`
- `docs/recommendation-v4-interpreter-contract.md`

## Non Goals

このガイドラインでは以下を行わない。

- ranking logic を変更しない
- Score v3 / Score v4 の weight を変更しない
- 神社DB構造を変更しない
- UI layout を変更しない
- Premium導線を変更しない
- 医療・宗教・占術的な断定をしない

## Current Problem

現在の `recommendation_reason_v4` は、構造としては `fact / interpretation / action` に分離されている。

一方で、文面には以下の問題が残る。

- 内部キーがそのまま表示文に近い形で出る
- `career_decision` や `money` など、ユーザー向けでない語が混ざる
- `history_theme` と `action_context` が重複しやすい
- 「整理する」「確認する」などの抽象表現に寄りやすい
- 神社固有情報よりも、相談テーマの一般論に見えやすい
- 行動提案が、参拝前 / 参拝中 / 参拝後のどこに向けたものか曖昧になりやすい

## Copy Principle

Recommendation v4 のコピーは、以下の順で組み立てる。

```text
神社側の事実
↓
相談文脈との接続
↓
小さな行動
```

推薦理由は、ユーザーを説得する文章ではなく、ユーザーが「なぜこの神社が候補なのか」を理解するための説明である。

## Layer Responsibility

### Fact Layer

Fact Layer は、神社側または推薦計算側に存在する事実だけを扱う。

使用してよい材料:

- shrine name
- history_theme
- goriyaku
- goriyaku_tags
- visit_style_tags
- candidate_profile
- meaning_translation.history_theme

表示方針:

- 神社名または神社側テーマを起点にする
- ご利益を結果保証として書かない
- 神社に行けば状態が変わるとは言い切らない
- 事実と解釈を混ぜない

避ける表現:

```text
この神社に行けば運気が上がります。
この神社があなたに必要です。
この神社が正解です。
```

推奨表現:

```text
この候補には、再出発というテーマが含まれています。
この神社は、仕事運の文脈を持つ候補です。
```

### Interpretation Layer

Interpretation Layer は、相談内容と神社側事実をつなぐ説明を扱う。

使用してよい材料:

- need_profile
- decision_context
- constraint_profile
- outcome_hint
- emotion_profile
- meaning_translation.shrine_context_need
- meaning_translation.history_theme

表示方針:

- 内部キーをそのまま表示しない
- 「あなたは〜です」と断定しない
- 「今の相談には〜が含まれています」程度に留める
- `history_theme` を本文内で繰り返しすぎない
- ご利益だけで理由を完結させない

避ける表現:

```text
相談テーマ:career / 判断文脈:career_decision / 制約:money / 着地点:decide
あなたは転職すべき状態です。
金運が上がる神社です。
```

推奨表現:

```text
仕事や働き方を見直したい相談として受け取れます。
生活や収入への不安を整え、次の判断を落ち着いて考えたい文脈があります。
```

### Action Layer

Action Layer は、次に取れる小さな行動を提示する。

使用してよい材料:

- action_intent
- outcome_hint
- meaning_translation.action_context
- meaning_translation.reflection_question_seed

表示方針:

- 抽象的な応援で終わらせない
- 参拝前 / 参拝中 / 参拝後のどの行動かを明確にする
- 1文に詰め込みすぎない
- 行動を強制しない
- `action_context` と同じ表現を繰り返さない

避ける表現:

```text
前に進みましょう。
今の状態を整理しましょう。
行けばきっと変わります。
```

推奨表現:

```text
参拝前に、今いちばん決めたいことを一つだけ書き出すと、行動につなげやすくなります。
参拝後は、「次に小さく動かすなら何から始めるか」を振り返ると、相談内容を記録に残しやすくなります。
```

## consultation_axis Mapping

`consultation_axis` は実装上の単一フィールドではなく、Recommendation v4 で利用する相談解釈フィールド群の総称として扱う。

| consultation_axis 相当 | 実装名 | 役割 | Copy Rule |
|---|---|---|---|
| 相談テーマ | need_profile | 何に悩んでいるか | ユーザー向けの自然語に変換する |
| 判断文脈 | decision_context | 何を決めようとしているか | 「〜を見直したい相談」として表現する |
| 制約 | constraint_profile | 何が制約になっているか | 「〜が気になっている文脈」と弱く表現する |
| 着地点 | outcome_hint | どうなりたいか | 「〜したい方向」として表現する |
| 行動意図 | action_intent | 次に何をしたいか | 小さな行動に変換する |
| 現在状態 | state_profile | 今の心理・行動状態 | 断定せず「〜が含まれる」と表現する |
| 推薦方向 | direction_profile | 提案する参拝体験の方向 | history_theme に接続する |
| 感情トーン | emotion_profile | 感情の強度・傾向 | 文体の強さを調整する |

## Internal Key Copy Mapping

内部キーは、そのままユーザー表示文に出さない。

### need_profile

| key | User-facing copy |
|---|---|
| mental | 気持ちを落ち着け、今の状態を整理したい |
| rest | 疲れを整え、静かに回復したい |
| career | 仕事や働き方を見直したい |
| money | 生活や収入の土台を整えたい |
| love | 人との縁や関係性を見直したい |
| study | 学びや積み重ねを続けたい |
| courage | 次に進むための一歩を決めたい |

### decision_context

| key | User-facing copy |
|---|---|
| career_decision | 仕事や働き方について判断したい |
| relationship_decision | 人との関係について見直したい |
| money_decision | お金や生活の判断を整えたい |
| rest_or_action | 休むか動くかを見極めたい |

### constraint_profile

| key | User-facing copy |
|---|---|
| time | 時間の余裕が少ない |
| money | お金や収入への不安がある |
| energy | 体力や気力が落ちている |
| relationship | 人間関係の制約がある |

### outcome_hint

| key | User-facing copy |
|---|---|
| decide | 判断材料を持ち帰りたい |
| calm | 気持ちを落ち着けたい |
| move_forward | 小さく前に進みたい |
| clarify | 考えを整理したい |

### action_intent

| key | User-facing copy |
|---|---|
| visit | 実際に足を運んで確認したい |
| reflect | 問いを一つに絞って整理したい |
| save | 今回の相談を残して振り返りたい |

## recommendation_reason_v4 Copy Rule

### reason_text

`reason_text` は以下の構造を基本とする。

```text
{fact_summary}。{interpretation_summary}。{action_summary}
```

1文で無理に連結しない。

避ける構造:

```text
{fact_label}は、{interpretation_text} {action_text}
```

理由:

- 文が長くなりやすい
- fact / interpretation / action の境界が曖昧になる
- 内部キーが混ざったときに読みにくい

推奨構造:

```text
この候補には、再出発というテーマが含まれています。仕事や働き方を見直したい相談として受け取れます。参拝前に、今いちばん決めたいことを一つだけ書き出すと、行動につなげやすくなります。
```

### fact.text

Fact は短くする。

推奨:

```text
この候補には、再出発というテーマが含まれています。
```

避ける:

```text
再出発の神社です。
```

理由:

「神社そのものが再出発である」と断定するより、「候補に含まれるテーマ」として扱う方が安全。

### interpretation.text

Interpretation は、相談文脈を自然語で説明する。

推奨:

```text
仕事や働き方を見直したい相談として受け取れます。
```

避ける:

```text
相談テーマ:career / 判断文脈:career_decision
```

### action.text

Action は、小さく、実行単位で書く。

推奨:

```text
参拝前に、今いちばん決めたいことを一つだけ書き出すと、行動につなげやすくなります。
```

避ける:

```text
前に進みましょう。
```

## Duplication Rules

### history_theme duplication

`history_theme` は1つの推薦理由内で原則1回までに留める。

避ける:

```text
再出発の神社です。再出発したいあなたに合います。再出発の一歩になります。
```

改善:

```text
この候補には、再出発というテーマが含まれています。今の相談は、働き方や次の方向を見直したい文脈として受け取れます。
```

### action_context duplication

`action_context` と同じ意味の文を繰り返さない。

避ける:

```text
今の状態を整理します。整理するために、整理できる場所です。
```

改善:

```text
参拝前に、今いちばん決めたいことを一つだけ書き出すと、行動につなげやすくなります。
```

### generic phrase duplication

以下の表現は使いすぎない。

- 整える
- 整理する
- 見直す
- 一歩
- 寄り添う
- 後押しする
- つながる

使う場合は、何を整えるのか、何を見直すのかを明確にする。

## Prohibited Expressions

以下の表現は禁止する。

```text
必ず変わります。
運気が上がります。
恋愛が成就します。
金運が上がります。
この神社が正解です。
あなたはこういう人です。
この方角しかありません。
神様が導いています。
病気が治ります。
```

## Review Checklist

`recommendation_reason` をレビューするときは、以下を確認する。

```markdown
- [ ] fact / interpretation / action が混ざっていない
- [ ] 内部キーがユーザー表示文に出ていない
- [ ] 抽象表現だけで終わっていない
- [ ] history_theme が重複していない
- [ ] action_context が重複していない
- [ ] 神社固有情報が1つ以上含まれている
- [ ] 相談文脈が1つ以上含まれている
- [ ] 行動提案が小さな実行単位になっている
- [ ] 医療・宗教・占術的な断定をしていない
- [ ] 結果保証をしていない
```

## Quality Metrics

Recommendation Quality Audit では、以下の観点で評価する。

| Metric | Meaning | Target |
|---|---|---|
| reason_depth | 推薦理由の深さ | 神社事実 + 相談文脈 + 行動が入っている |
| action_specificity | 行動提案の具体性 | 参拝前 / 中 / 後のどれかが明確 |
| history_theme_fit | history_theme との整合 | 相談軸とテーマが矛盾しない |
| semantic_duplication | 意味重複 | 同じ単語・同じ意味を繰り返さない |
| shrine_specificity | 神社固有性 | 神社名 / ご利益 / history_theme のいずれかが入る |
| consultation_fit | 相談文脈との整合 | need / decision / constraint / outcome のいずれかが反映される |

## Implementation Order

```markdown
- [x] docs/recommendation-v4-copy-guideline.md 作成
- [x] Recommendation Copy Guideline 作成
- [ ] recommendation_reason を全件レビュー
- [x] recommendation_reason_v4 Copy Rule 作成
- [ ] 必要最小限の copy rule 修正
- [ ] backend pytest
- [ ] py_compile
```

## Next Review Target

次は `recommendation_reason_v4.py` の以下をレビューする。

- `_build_fact`
- `_build_interpretation`
- `_build_action`
- `_build_reason_text`

レビュー後、必要最小限のコード修正を行う。
