

# User State Profile

## 目的

User State Profile は、ユーザーの相談入力から「今どのような目的・状態で神社を探しているか」を構造化するための定義である。

Recommendation Score v2 では、User State Profile を使って以下を判断する。

```text
ユーザーの相談意図
↓
神社の意味・ご利益・文脈との一致
↓
推薦順位
```

このドキュメントでは、現行実装に存在する `query` / `need_tags` / `matched_need_tags` / `primary_need_tag` を中心に User Layer を定義する。

---

## 前提

現時点では、ユーザー状態は独立した `mood` / `concern` / `wish` フィールドとして保存されていない。

既存実装では、主に以下の流れで状態が解釈される。

```text
query / extra_condition
↓
need_tags
↓
matched_need_tags
↓
primary_need_tag
↓
score_v2.components.user_state_match
```

そのため、User State Profile の初期定義では `need_tags` を正本として扱う。

---

## User State と他レイヤーの責務分離

### User State Profile

ユーザーの相談意図を表す。

主な要素:

- raw_query
- extra_condition
- need_tags
- need_hits
- primary_need_tag
- matched_need_tags
- selected_goriyaku_tag_ids

---

### Shrine Meaning Profile

神社側の意味・文脈を表す。

主な要素:

- history_theme
- goriyaku
- goriyaku_tag_ids
- culture_translation
- shrine_type
- origin / history context

---

### Context Profile

その時の利用条件を表す。

主な要素:

- distance
- visit_style_tags
- location / area
- birthdate / astro_profile
- direction_bonus
- public_mode
- flow

---

### Behavior Profile

ユーザーの過去行動を表す。

主な要素:

- detail_view
- route_open
- save / favorite
- visit_done
- reflection_saved
- action_started / action_completed

---

## 現在の User State 抽出

### 入力

`build_chat_recommendations` では、主に以下を受け取る。

```text
query
language
candidates
birthdate
goriyaku_tag_ids
extra_condition
public_mode
flow
need_tags
user
```

User State Profile に直接関係するのは以下。

| 入力 | 用途 |
|---|---|
| query | ユーザー相談文の原文 |
| extra_condition | 追加条件・利用文脈 |
| need_tags | 明示指定された相談テーマ |
| goriyaku_tag_ids | ユーザーが選択したご利益タグ |

---

### need_tags

`resolve_need_payload` によって、`query` から相談テーマを抽出する。

現行の主要タグ:

| need_tag | 意味 |
|---|---|
| study | 学業・試験・資格 |
| career | 仕事・転職・挑戦 |
| mental | 不安・悩み・心の整理 |
| love | 恋愛・縁結び・人間関係 |
| money | 金運・収入・商売 |
| rest | 休息・癒し・静けさ |
| courage | 勇気・挑戦・前進 |

注意:

- `courage` は `NEED_TAG_ALIASES` に存在する
- `NEED_SYNONYMS` の主要カテゴリにはまだ明示されていない
- 初期設計では `career` と近い行動系テーマとして扱う

---

### need_hits

`need_hits` は、どの単語が `need_tags` に反応したかを表す。

例:

```json
{
  "mental": ["不安", "迷い"],
  "career": ["転職"]
}
```

用途:

- ユーザー状態の説明補助
- 抽出根拠の確認
- 将来的なデバッグ・チューニング

Recommendation Score v2 では、現時点では直接スコアに入れない。

---

## matched_need_tags

`matched_need_tags` は、ユーザーの `need_tags` と神社側の情報が一致したタグである。

一致経路:

- shrine astro_tags との一致
- goriyaku / description テキストとの一致
- goriyaku_tag_ids との一致
- ユーザー選択 goriyaku_tag_ids との一致

意味:

```text
ユーザー状態と神社意味の接点
```

注意:

`matched_need_tags` は User State だけではなく、神社側とのマッチ結果である。

そのため、User State Profile の入力要素ではなく、Recommendation Score v2 の中間シグナルとして扱う。

---

## primary_need_tag

`primary_need_tag` は、`matched_need_tags` の先頭から決まる。

```text
primary_need_tag = matched_need_tags[0]
```

用途:

- 相談全体の中心テーマ表示
- explanation payload
- カードや詳細画面での説明

注意:

現状では `need_tags[0]` ではなく、`matched_need_tags[0]` から決まる。

つまり、ユーザーの意図そのものというより、候補神社との一致後に決まる中心テーマである。

---

## consultationSummary の扱い

`consultationSummary` は User State の正本ではない。

現状では、`shrine_meaning_composer.py` の `_build_consultation_summary` によって生成される表示用コピーである。

役割:

- 画面上の「今の状態」表示
- Free / Premium カードの説明
- ユーザーに見せる自然文

注意:

`consultationSummary` は `history_theme` を経由して生成されるため、ユーザー入力だけから作られているわけではない。

そのため、Recommendation Score v2 の User Layer では正本にしない。

---

## history_theme の扱い

`history_theme` は User State ではなく、Shrine Meaning / Action Theme 側の要素として扱う。

理由:

- Shrine model に存在する
- shrine meaning composer で使われる
- action_suggestions の生成にも使われる
- 神社側の歴史的・行動的文脈を表す

ただし、ユーザー状態と対応づけることはできる。

例:

| User State | 対応しやすい history_theme |
|---|---|
| mental | 静寂 / 守り / 再出発 |
| rest | 静寂 / 復興 |
| career | 勝負 / 導き / 再出発 |
| study | 学び |
| love | 縁 |
| money | 勝負 / 商売系文脈 |

これはスコアの正本ではなく、意味づけ・説明・行動提案の補助として扱う。

---

## Recommendation Score v2 の User Layer

現行コードでは `score_v2.components.user_state_match` が存在する。

現状の計算:

```text
user_state_match = score_need_rank_weighted × need_weight
```

関連するシグナル:

```text
matched_by_tag
matched_by_text
matched_by_gid
matched_user_selected_goriyaku_tag_ids
```

User Layer の役割:

- ユーザー相談と候補神社がどれだけ一致しているかを見る
- 神社の人気や距離よりも、相談意図との接点を優先する
- 行動履歴に引っ張られすぎないようにする

---

## User State Profile 初期定義

### raw_query

ユーザーが入力した相談文の原文。

用途:

- need_tags 抽出
- LLM fallback
- デバッグ
- 将来的な再解析

スコア利用:

- 直接加点しない
- need_tags / extra_tags の抽出元として使う

---

### extra_condition

ユーザーが追加で指定した条件。

例:

- 静かな場所がいい
- 徒歩で行ける場所
- 夜に行きたい
- 混んでいない場所

用途:

- visit_style_tags
- sort_tags
- hard_filter_tags
- soft_signal_tags

スコア利用:

- Context Profile 側で扱う

---

### need_tags

ユーザー相談から抽出されたテーマ。

用途:

- User State の正本
- candidate ranking
- explanation
- User Layer score

スコア利用:

- matched_need_tags の母体
- score_need_rank_weighted の材料

---

### need_hits

need_tags 抽出の根拠。

用途:

- デバッグ
- 説明改善
- 将来的な抽出精度検証

スコア利用:

- 初期段階では直接使わない

---

### selected_goriyaku_tag_ids

ユーザーが明示選択したご利益タグ。

用途:

- ユーザー意図の強いシグナル
- matched_user_selected_goriyaku_tag_ids の材料

スコア利用:

- need_tags より強い明示意図として扱う余地がある

---

### primary_need_tag

候補との一致後に決まる中心テーマ。

用途:

- 表示
- explanation
- 状態要約

スコア利用:

- 初期段階では直接加点しない
- matched_need_tags の代表として扱う

---

## 未定義・今後追加候補

### mood

現在は独立保存されていない。

対応候補:

- mental
- rest
- ShrineReflection.mood_before / mood_after

今後の方針:

- 相談時点の mood を保存する場合は、User State Profile に追加する
- ただし初期実装では query → need_tags で代替する

---

### concern

現在は独立保存されていない。

対応候補:

- query
- need_hits
- need_tags

今後の方針:

- concern を LLM で抽出する場合は、構造化フィールドとして追加する
- ただし、過剰に心理断定しない

---

### wish

現在は独立保存されていない。

対応候補:

- need_tags
- goriyaku_tag_ids

今後の方針:

- ユーザーが明示選択する願いは `selected_goriyaku_tag_ids` として扱う
- 自然文からの願い抽出は `need_tags` に集約する

---

## 初期ルール

User State Profile の初期ルールは以下。

```text
User State の正本 = query から抽出した need_tags
User State の説明 = matched_need_tags / primary_need_tag
User State の表示コピー = consultationSummary
User State と混ぜないもの = history_theme
```

---

## Recommendation Score v2 接続TODO

- [ ] `need_tags` を User State Profile の正本として明文化する
- [ ] `matched_need_tags` を User × Shrine の一致結果として扱う
- [ ] `primary_need_tag` を表示用代表テーマとして扱う
- [ ] `consultationSummary` を表示用コピーとして扱う
- [ ] `history_theme` を Shrine Meaning Profile 側に分離する
- [ ] `score_v2.components.user_state_match` の定義を docs に固定する
- [ ] `selected_goriyaku_tag_ids` を明示意図として別重み化するか検討する
- [ ] `mood / concern / wish` を保存フィールドにするか検討する

---

## 次PR候補

### PR1: User State Profile のドキュメント整理

目的:

- 現行実装の User Layer を明文化する

TODO:

- [ ] `docs/analytics/user-state-profile.md` を追加
- [ ] need_tags / matched_need_tags / primary_need_tag の責務を整理
- [ ] consultationSummary / history_theme を User State から分離

---

### PR2: score_v2 components の表示・確認

目的:

- User State Match がどの程度順位に影響しているか確認する

TODO:

- [ ] score_v2.components.user_state_match をログで確認
- [ ] matched_need_tags の有無別に順位を比較
- [ ] selected_goriyaku_tag_ids の影響を確認

---

### PR3: User State Profile payload 化

目的:

- query解析結果を明示的な payload として保持する

候補フィールド:

```json
{
  "raw_query": "最近不安で、落ち着ける神社に行きたい",
  "need_tags": ["mental", "rest"],
  "need_hits": {
    "mental": ["不安"],
    "rest": ["落ち着ける"]
  },
  "selected_goriyaku_tag_ids": [],
  "primary_need_tag": "mental"
}
```

注意:

- 初期段階ではDB追加しない
- まず response / debug / analytics payload として検証する

---

## 現時点の判断

User State Profile は、現段階では以下で十分。

```text
raw_query
need_tags
need_hits
selected_goriyaku_tag_ids
matched_need_tags
primary_need_tag
```

`mood / concern / wish` は重要だが、今すぐ独立フィールドにすると心理的断定が強くなりすぎる。

そのため初期設計では、自然文からの推測は `need_tags` に留める。

これにより、Recommendation Score v2 は以下の構造を維持できる。

```text
User State Match
+ Shrine Meaning Match
+ Context Match
+ Behavior Signal
```
