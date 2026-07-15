# Recommendation v5 Design

> **Status: Archive**
>
> 本ドキュメントは、未実装のv5設計と次PR候補を含む将来計画である。
>
> 現行の推薦契約は `docs/product/recommendation-reason-v4-contract.md` を正本とする。

## 目的

Recommendation v5 は、推薦順位を急に変更する実装ではなく、相談解釈・意味変換・行動シグナル・振り返りシグナルを整理し、次の推薦改善に向けた設計方針を固定する。

現時点では Score v3 が shadow mode で評価中のため、v5では active score の変更は行わない。

## 現在地

Recommendation v4 までで以下は整備済み。

- Recommendation Reason v4
- Recommendation Reason Quality
- Action Suggestion v4
- Explanation 品質監査
- reason_facts coverage
- Score v3 shadow mode
- Score v3 dashboard
- Score v3 shadow evaluation

次に必要なのは、推薦の「脳みそ」にあたる解釈レイヤの整理である。

## v5の対象範囲

### 対象

- consultation interpreter
- meaning translation
- behavior signal
- reflection signal
- recommendation input profile
- backend API contract の整理方針

### 対象外

- Score v3 active 化
- weight変更
- Web / Mobile UI実装
- 課金導線
- DB schema変更

## 1. Consultation Interpreter

### 現状

`consultation_interpreter.py` はキーワードベースで以下を抽出している。

- state_profile
- need_profile
- direction_profile
- emotion_profile
- action_intent
- decision_context
- constraint_profile
- outcome_hint

### 課題

- キーワード一致の優先順位が粗い
- 相談の「願望」と「状態」と「制約」が混ざりやすい
- `primary_need_tag` が先頭優先になりやすい
- money / career / courage などが相談文脈によって意味が変わる
- 恋愛・人間関係・縁の境界が曖昧になりやすい

### v5方針

相談文を以下の5層に分けて扱う。

1. state
   - 今の心理・身体・状況
2. need
   - 求めているご利益・願望カテゴリ
3. constraint
   - 邪魔している条件
4. outcome
   - どうなりたいか
5. action_intent
   - 次に何をしたいか

### 追加検討

- `primary_need_tag` の決定ルールを明示する
- `consultation_axis` と `primary_need_tag` の責務を分ける
- `emotion_intensity` を action suggestion / reflection question に反映する
- selected_goriyaku_tag_ids はユーザー明示条件として優先扱いする

## 2. Meaning Translation

### 現状

`meaning_translation.py` は interpretation profile を以下に変換する。

- history_theme
- shrine_context_need
- action_context
- reflection_question_seed

### 課題

- `history_theme` が強い
- `reflection_question_seed` が history_theme のみに依存している
- 同じ history_theme だと問いが単調になりやすい
- money が守りに寄りやすく、商売繁盛・拡大・挑戦の文脈が薄い
- constraint と outcome の組み合わせがまだ弱い

### v5方針

meaning translation は以下の順に整理する。

1. consultation_axis
2. state_profile
3. need_profile
4. constraint_profile
5. outcome_hint
6. action_intent
7. history_theme

### 改善候補

- `reflection_question_seed` を history_theme だけでなく、state / outcome / constraint から生成する
- `action_context` を intent だけでなく、outcome と constraint から補正する
- `money` を以下に分岐する
  - 守り: 生活費・不安・安定
  - 商売繁盛: 売上・事業・利益
  - 勝負: 独立・挑戦・拡大
- `career` を以下に分岐する
  - 再出発: 転職・働き方変更
  - 勝負: 独立・挑戦
  - 学び: スキル・資格・準備

## 3. Behavior Signal

### 現状

`concierge_history.py` では以下を扱う。

- detail_view
- route_open
- save
- visit_signal
- reflection_signal

### 課題

- behavior は現在スコア加点として扱われている
- save は「良い」だけでなく「迷っている」「保留」の可能性がある
- route_open は強い関心だが訪問完了ではない
- visit_done と reflection_saved は体験後シグナルとして別扱いした方がよい

### v5方針

behavior を関心段階として整理する。

| action | 意味 |
| --- | --- |
| detail_view | 興味あり |
| route_open | 行く可能性あり |
| save | 保留・比較・再検討 |
| visit_done | 実行済み |
| reflection_saved | 体験後の意味化 |

### 改善候補

- save は単純加点ではなく「比較候補」として扱う
- route_open は短期行動意図の強いシグナルにする
- visit_done は同じ神社の再推薦より、関連テーマ推薦に活かす
- reflection_saved は次回推薦の方向補正に使う

## 4. Reflection Signal

### 現状

`reflection_state_change.py` では振り返り内容から以下を推定する。

- improved
- unchanged
- worsened
- unknown

また、以下を返す。

- next_need_hint
- next_history_theme_hint

### 課題

- キーワードベースで簡易判定
- reflection 内容の意味解析は限定的
- reflection signal は現在、量的シグナルとしての扱いが中心
- 次回推薦への反映ルールがまだ弱い

### v5方針

reflection は「参拝後の状態変化」として扱う。

| state_change | 次回推薦方針 |
| --- | --- |
| improved | 少し前進するテーマを提案 |
| unchanged | 同系統または守り・静寂を維持 |
| worsened | 負荷を下げ、静寂・守りへ戻す |
| unknown | 通常推薦に補助情報として扱う |

### 改善候補

- `next_history_theme_hint` を Score v3 / v5 の補助シグナルへ接続する
- reflection question を state_change に応じて変える
- improved 時は action suggestion を少し前向きにする
- worsened 時は route_open より pause / reflect を優先する

## 5. Recommendation Input Profile

### 現状

`recommendation_input_profile` は Score v3 / Reason v4 / Action Suggestion v4 の橋渡しになっている。

### v5方針

v5では recommendation_input_profile を正本に寄せる。

保持すべき情報:

- raw_query
- interpretation_profile
- meaning_translation
- candidate_profile
- score_v2_fields
- behavior_profile
- reflection_profile
- action_profile
- quality/debug fields

## 6. Web / Mobile 表示との関係

v5は Web / Mobile UI の表示統一フェーズではない。

ただし、v5で backend の返却意味を整理することで、後続の Web / Mobile 表示差分監査がやりやすくなる。

後続フェーズで確認するもの:

- recommendation_reason_v4
- recommendation_reason_quality
- reason_facts
- explanation
- action_suggestion_v4_preview
- score_v3_debug
- consultation_axis

## 7. 実装方針

このPRでは設計のみ行う。

やらないこと:

- ranking変更
- Score v3 weight変更
- active化
- API response変更
- DB migration
- UI変更

次PR以降で小さく分ける。

## 8. 次PR候補

### PR1: consultation interpreter v5 design contract

- primary_need_tag の決定ルール明文化
- consultation_axis と need_profile の責務整理
- state / need / constraint / outcome / action_intent の優先順位整理

### PR2: meaning translation v5 design contract

- history_theme決定順序の見直し
- reflection_question_seed の生成条件追加
- money / career / courage の分岐整理

### PR3: behavior / reflection signal contract

- behaviorを関心段階として定義
- reflection state change と次回推薦方針を接続
- Score v3 / v5 の補助シグナルとして整理

### PR4: Web / Mobile API contract audit

- backend返却値を正本化
- Web / Mobile 表示差分を監査
- 共通contractへ寄せる

## 結論

Recommendation v5 は、今すぐ推薦順位を変える実装ではなく、推薦判断の解釈レイヤを整理する設計フェーズである。

Score v3 が shadow評価中のため、v5では安全に設計を固定し、実装はPR単位で小さく進める。
