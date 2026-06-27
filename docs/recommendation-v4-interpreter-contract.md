# Recommendation v4 / Consultation Interpreter Contract

## Goal

相談文を推薦ロジック・意味変換・推薦理由生成で再利用できる構造に分解する。

このcontractは、Recommendation v4で `consultation_interpreter.py` が返すべき出力責務を固定する。

## Current Output

`interpret_consultation()` は以下の構造を返す。

- raw_query
- state_profile
- need_profile
- direction_profile
- emotion_profile
- action_intent
- decision_context
- constraint_profile
- outcome_hint

これらは Recommendation v4 における consultation_axis 相当の入力として利用される。

各フィールドの責務は以下の通り。

| Field | Responsibility | Used By |
|-------|----------------|---------|
| raw_query | 正規化済み相談文 | recommendation reason / debug |
| state_profile | 現在状態 | direction / meaning translation |
| need_profile | 相談テーマ・ご利益 | scoring / shrine matching |
| direction_profile | 推薦方向 | history_theme |
| emotion_profile | 感情トーン | recommendation reason / action suggestion |
| action_intent | 行動意図 | action suggestion / CTA |
| decision_context | 判断したい内容 | meaning translation / recommendation reason |
| constraint_profile | 制約条件 | meaning translation / recommendation reason |
| outcome_hint | 望む着地点 | meaning translation / recommendation reason |

## Field Contract

### raw_query

#### Goal
ユーザーが入力した相談文の正規化済み原文を保持する。

#### Responsibility
- strip済みの文字列を返す
- 推薦理由生成時の原文参照に使う
- 意味変換層で文脈を再確認するために使う

#### Out of Scope
- 要約しない
- 解釈を混ぜない

---

### state_profile

#### Goal
ユーザーの現在状態を表す。

#### Responsibility
- 疲れている
- 不安
- 迷い
- 停滞
- 変化準備

など、現在の心理・行動状態を抽出する。

#### Expected Keys
- primary_state
- secondary_states
- state_hits
- confidence

#### Used By
- direction_profile
- recommendation reason
- action_suggestion

---

### need_profile

#### Goal
ユーザーが求めているテーマ・ご利益・目的を表す。

#### Responsibility
- need_tags を統合する
- query由来の need を抽出する
- selected_goriyaku_tag_ids を保持する

#### Expected Keys
- need_tags
- need_hits
- primary_need_tag
- selected_goriyaku_tag_ids

#### Used By
- recommendation scoring
- shrine matching
- recommendation reason

---

### direction_profile

#### Goal
ユーザーに対して、どの方向の参拝体験を提案するかを表す。

#### Responsibility
- rest
- stabilize
- review
- reset
- challenge

など、推薦の方向性を示す。

#### Expected Keys
- direction
- themes
- source_state

#### Used By
- history_theme selection
- meaning_translation
- recommendation reason

---

### emotion_profile

#### Goal
相談文から読み取れる感情トーンと強度を表す。

#### Responsibility
- tone を返す
- intensity を返す
- 感情シグナルを保持する

#### Expected Keys
- tone
- intensity
- signals

#### Used By
- recommendation reason tone
- action_suggestion tone
- reflection question seed

---

### action_intent

#### Goal
ユーザーが次に取りたい行動意図を表す。

#### Responsibility
- 参拝したい
- 整理したい
- 保存したい

などの行動意図を抽出する。

#### Expected Keys
- intent
- strength
- candidates
- intent_hits

#### Used By
- action_suggestion
- route_open CTA
- reflection flow

## Additional Interpretation Fields

以下のフィールドは Recommendation v4 で利用する追加解釈情報である。

### decision_context

ユーザーが何を決めようとしているか。

例:

- 転職するか
- 関係を続けるか
- 休むか動くか
- お金を使うか守るか

### constraint_profile

ユーザーの制約条件。

例:

- 時間がない
- お金が不安
- 体力が落ちている
- 人間関係の制約がある

### outcome_hint

ユーザーが望む着地点。

例:

- 決めたい
- 落ち着きたい
- 背中を押されたい
- 整理したい

## Non Goals

- ranking logicを変更しない
- Score v3 weightを変更しない
- 神社DB構造を変更しない
- UIを変更しない

## KPI

このcontract改善により、以下の改善を狙う。

- detail_open_rate
- save_rate
- route_open_rate
- reflection_saved_rate
