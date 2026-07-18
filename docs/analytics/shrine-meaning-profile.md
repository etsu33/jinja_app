> **Status: Active**
>
> 本ドキュメントは、Recommendation Score v2が用いるShrine Meaning Profileの定義を管理する正本文書である。
>
> 正確な実装・重みおよび計測項目は`docs/analytics/recommendation-score-v2-current-design.md`、関連するBackend実装コードおよびテストを最終的な正本とする。

# Shrine Meaning Profile

## 目的

Shrine Meaning Profile は、神社側が持つ意味・文脈・ご利益・歴史的背景を整理し、Recommendation Score v2 の Shrine Layer と表示用 Meaning Layer を分離するための定義である。

Recommendation Score v2 では、神社側の意味を以下の観点で扱う。

```text
ユーザー状態
↓
神社側の意味・ご利益・歴史文脈との一致
↓
推薦順位
↓
表示コピー
```

このドキュメントでは、現行実装に存在する `history_theme` / `goriyaku` / `goriyaku_tags` / `goriyaku_tag_ids` / `culture_translation` / `origin_summary` を中心に Shrine Layer を定義する。

---

## 前提

現時点では、神社側の意味は複数のレイヤーに分散している。

主な実装箇所:

```text
backend/temples/models.py
backend/temples/services/concierge_chat_candidates.py
backend/temples/services/concierge_chat_ranking.py
backend/temples/services/concierge_explanation_payload.py
backend/temples/services/shrine_meaning_composer.py
backend/temples/services/shrine_culture_translation.py
backend/temples/services/shrine_trust_metadata.py
backend/temples/services/action_suggestions.py
```

そのため、Shrine Meaning Profile では以下を分けて扱う。

```text
Matching Layer
= 推薦順位に使う神社側意味

Presentation Layer
= ユーザーに表示する説明・文脈・コピー
```

---

## Shrine Meaning と他レイヤーの責務分離

### User State Profile

ユーザーの相談意図を表す。

主な要素:

- raw_query
- need_tags
- need_hits
- selected_goriyaku_tag_ids
- primary_need_tag

---

### Shrine Meaning Profile

神社側の意味・文脈を表す。

主な要素:

- goriyaku
- goriyaku_tags
- goriyaku_tag_ids
- history_theme
- description
- sajin
- culture_translation
- origin_summary
- place_tags
- element

---

### Context Profile

その時の利用条件を表す。

主な要素:

- distance
- location / area
- visit_style_tags
- direction_bonus
- birthdate / astro_profile
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

## Shrine Meaning Profile の2層構造

### 1. Matching Layer

推薦順位・スコアに使う神社側意味。

対象:

- goriyaku
- goriyaku_tags
- goriyaku_tag_ids
- history_theme
- description
- astro_tags
- place_tags

目的:

- ユーザーの `need_tags` と神社側情報の一致を判定する
- `score_v2.components.shrine_meaning_match` の根拠にする
- explanation の構造化データに使う

注意:

- 表示用コピーは直接スコアに入れない
- 文章の良し悪しで順位が変わらないようにする

---

### 2. Presentation Layer

ユーザーに見せる意味・説明・行動文脈。

対象:

- culture_translation
- origin_summary
- heroMeaningCopy
- shrineMeaning
- actionMeaning
- historyContext
- benefitActionContext
- todayFlowContext
- afterVisitReflection
- deitySymbolContext

目的:

- 神社固有の文脈を自然文で伝える
- ご利益を結果保証ではなく行動テーマに翻訳する
- 歴史説明をWikipedia化させず、今の状態と接続する

注意:

- Presentation Layer はスコアの正本ではない
- Recommendation Score v2 には直接混ぜない

---

## 現在の神社側入力

`ShrineMeaningInput` では、以下を正規化している。

| 項目 | 意味 | 主な用途 |
|---|---|---|
| shrine_id | 神社ID | culture_translation / trust_metadata 参照 |
| name_jp | 神社名 | 表示文生成 |
| address | 住所 | 表示・Context補助 |
| latitude / longitude | 緯度経度 | 距離・地図・Context補助 |
| goriyaku | ご利益自由テキスト | Matching / Presentation |
| goriyaku_tags | ご利益タグ名 | Matching / benefitActionContext |
| sajin | 祭神 | deitySymbolContext |
| description | 説明文 | Matching / fallback表示 |
| history_theme | 歴史・行動テーマ | Meaning / action_suggestions |
| element | 五行・属性 | element_match |
| place_tags | 場所タグ | Context / meaning補助 |
| direction_bonus | 方位補助点 | Context補助 |
| direction_reason | 方位理由 | directionSupportCopy |

---

## goriyaku

`goriyaku` は神社のご利益を自由テキストとして表す。

用途:

- `concierge_chat_ranking.py` で `need_tags` とのテキスト一致判定に使う
- `shrine_meaning_composer.py` で primary benefit の fallback に使う
- `benefitActionContext` で、願望成就ではなく行動テーマへ翻訳する

扱い:

```text
goriyaku
↓
benefit labels
↓
benefit state themes
↓
benefitActionContext
```

注意:

- ご利益は結果保証として扱わない
- Matching Layer では一致材料
- Presentation Layer では行動テーマへの翻訳材料

---

## goriyaku_tags / goriyaku_tag_ids

`goriyaku_tags` は神社に紐づくご利益タグ名である。

`goriyaku_tag_ids` は推薦・検索・API payload 上で使うタグIDである。

用途:

- user selected goriyaku tag との一致
- `need_tags_to_goriyaku_ids` による need_tags との接続
- `matched_by_gid` の生成
- 候補検索時の filter

現行の一致経路:

```text
user need_tags
↓
need_tags_to_goriyaku_ids
↓
candidate goriyaku_tag_ids
↓
matched_by_gid
```

また、ユーザーが明示的に選択したご利益タグは以下で扱われる。

```text
requested_goriyaku_tag_ids
↓
matched_user_selected_goriyaku_tag_ids
```

扱い:

- `goriyaku_tag_ids` は Matching Layer の強いシグナル
- ユーザー明示選択との一致は、通常のテキスト一致より強い意図として扱う余地がある

---

## history_theme

`history_theme` は、神社側の歴史文脈・行動意味を表すテーマである。

用途:

- `shrine_meaning_composer.py` の history / action / benefit 文脈生成
- `action_suggestions.py` の行動提案生成
- `ShrineReflection` の snapshot
- `ActionEvent` の action theme

関連定義:

```text
HISTORY_THEME_DEFINITION
HISTORY_THEME_CONTEXT
HISTORY_THEME_DISPLAY_COPY
HISTORY_THEME_ACTION_CONTEXT
HISTORY_THEME_ACTION_RESULT_CONTEXT
```

役割:

| 定義 | 役割 |
|---|---|
| HISTORY_THEME_DEFINITION | 歴史事実・歴史的役割・現代解釈・行動翻訳 |
| HISTORY_THEME_CONTEXT | 短い意味文脈 |
| HISTORY_THEME_DISPLAY_COPY | 画面表示用コピー |
| HISTORY_THEME_ACTION_CONTEXT | 参拝中の行動文脈 |
| HISTORY_THEME_ACTION_RESULT_CONTEXT | ご利益を状態変化へ翻訳する補助 |

注意:

`history_theme` は User State ではない。

ユーザーの状態を直接表すものではなく、神社側の歴史・意味・行動文脈を表す。

---

## history_theme と need_tags の接続

`need_tags` はユーザー側の相談テーマである。

`history_theme` は神社側の意味テーマである。

両者は同じものではないが、意味的な対応関係を持てる。

初期接続案:

| need_tag | 対応しやすい history_theme | 意味 |
|---|---|---|
| mental | 静寂 / 守り / 再出発 | 不安・迷いを整える |
| rest | 静寂 / 復興 | 休息・回復・静けさ |
| career | 勝負 / 導き / 再出発 | 仕事・転職・次の判断 |
| courage | 勝負 / 導き / 再出発 | 前進・挑戦・決断 |
| study | 学び | 学業・試験・継続 |
| love | 縁 | 恋愛・良縁・人間関係 |
| money | 勝負 / 商売系文脈 | 商売・金運・行動の切替 |

扱い:

- 初期段階では直接スコアに強く混ぜない
- explanation / action_suggestions / meaning copy の補助として使う
- 将来的に `need_tag × history_theme` のCVRを見て重み化する

---

## culture_translation

`culture_translation` は curated な神社固有文脈である。

実装:

```text
backend/temples/services/shrine_culture_translation.py
```

主なフィールド:

| 項目 | 意味 |
|---|---|
| landscape_tags | 地形・景観文脈 |
| faith_tags | 信仰文脈 |
| body_feeling_tags | 体感・空気感 |
| historical_background | 歴史的背景 |
| place_meaning | 場所意味 |
| flow_guidance | 今の流れへの接続 |
| action_reason | 行動理由 |
| benefit_translation | ご利益の行動翻訳 |

用途:

- `shrineMeaning`
- `benefitActionContext`
- `todayFlowContext`
- 固有文脈の強化

注意:

- curated data のため品質は高い
- ただし全神社にあるわけではない
- スコア主軸ではなく Presentation Layer の強化として扱う

---

## origin_summary

`origin_summary` は list card の信頼補助情報である。

実装:

```text
backend/temples/services/shrine_trust_metadata.py
```

主なフィールド:

| 項目 | 意味 |
|---|---|
| rank_class | 神社格・分類 |
| cultural_status | 文化的・制度的ステータス |
| lineage | 系譜・総本社など |
| origin_summary | 短い由緒要約 |

用途:

- 候補カード上の信頼補助
- 神社の固有性補強
- originSummary 表示

注意:

- Recommendation Score v2 の主スコアには直接入れない
- 表示信頼・納得感を補強する材料として扱う

---

## description

`description` は神社の説明文である。

用途:

- Ranking で `need_tags` との text hint match に使う
- shrineMeaning の fallback に使う

扱い:

- Matching Layer の補助材料
- Presentation Layer の fallback

注意:

- description があるだけで意味が強いとは限らない
- text match の重みは過剰にしない

---

## sajin

`sajin` は祭神情報である。

用途:

- `deitySymbolContext`
- 表示上の補助情報

扱い:

- 初期段階では Recommendation Score v2 に直接入れない
- 今後、神格・象徴マップを定義する場合に Shrine Meaning Profile の補助軸として使う

---

## place_tags

`place_tags` は場所の特徴を表すタグである。

用途:

- 神社の空間的特徴
- visit_style_tags との接続候補
- Context Profile との橋渡し

扱い:

- Shrine Meaning と Context の中間要素
- 初期段階では Context Match 側で扱う

---

## element

`element` は五行・属性のような相性要素を表す。

用途:

- `score_v2.components.element_match`

扱い:

- Shrine Meaning Profile ではなく、Compatibility / Context 寄りの補助軸
- 初期段階では Shrine Layer とは分けて扱う

---

## Recommendation Score v2 の Shrine Layer

現行コードでは、以下が存在する。

```text
score_v2.components.shrine_meaning_match
```

現状の計算:

```text
shrine_meaning_match = score_need × need_weight
```

この `score_need` は、以下の一致数から作られる。

```text
matched_need_tags
= matched_by_tag + matched_by_text + matched_by_gid
```

ただし、現状では User State Match と Shrine Meaning Match の境界がやや曖昧である。

現行の役割整理:

| component | 意味 |
|---|---|
| user_state_match | ユーザーの相談意図がどれだけ強く候補に反映されたか |
| shrine_meaning_match | 神社側の意味情報が相談テーマとどれだけ接点を持つか |

初期方針:

```text
User State Match
= need_tags の強一致・重み付き一致

Shrine Meaning Match
= 神社側の goriyaku / goriyaku_tags / description / history_theme による意味接点
```

---

## Shrine Meaning Match の初期材料

### 強い材料

- goriyaku_tag_ids
- goriyaku_tags
- history_theme

### 中程度の材料

- goriyaku text
- description text
- culture_translation tags

### 表示補助材料

- origin_summary
- sajin
- trust metadata

---

## スコアに入れないもの

初期段階では、以下は直接スコアに入れない。

- heroMeaningCopy
- consultationSummary
- shrineMeaning
- actionMeaning
- historyContext
- benefitActionContext
- todayFlowContext
- afterVisitReflection
- origin_summary

理由:

- 生成コピーで順位が変わると評価不能になる
- 文章品質と意味一致が混ざる
- 後からABテストしづらくなる

---

## 初期ルール

Shrine Meaning Profile の初期ルールは以下。

```text
Shrine Meaning の正本
= goriyaku / goriyaku_tags / goriyaku_tag_ids / history_theme

Shrine Meaning の補助材料
= description / sajin / place_tags / culture_translation tags

Shrine Meaning の表示コピー
= heroMeaningCopy / shrineMeaning / actionMeaning / historyContext / benefitActionContext

スコアに直接入れないもの
= origin_summary / generated copy
```

---

## Recommendation Score v2 接続TODO

- [ ] `goriyaku_tag_ids` を Shrine Meaning Match の強シグナルとして扱う
- [ ] `goriyaku` text match は補助シグナルとして扱う
- [ ] `description` text match は補助シグナルとして扱う
- [ ] `history_theme` と `need_tags` の接続表を定義する
- [ ] `culture_translation` は初期段階では表示強化に留める
- [ ] `origin_summary` は trust / presentation 用に留める
- [ ] generated copy を ranking score に混ぜない
- [ ] `score_v2.components.shrine_meaning_match` の定義を docs に固定する

---

## 次PR候補

### PR1: Shrine Meaning Profile のドキュメント整理

目的:

- 現行実装の Shrine Layer を明文化する

TODO:

- [ ] `docs/analytics/shrine-meaning-profile.md` を追加
- [ ] Matching Layer / Presentation Layer を整理
- [ ] history_theme / goriyaku / culture_translation / origin_summary の責務を整理

---

### PR2: history_theme × need_tags 対応表の実装検討

目的:

- User State と Shrine Meaning の接続を明示する

TODO:

- [ ] `need_tag × history_theme` matrix を定義
- [ ] 初期重みを低めに設定
- [ ] PostHogで route_open / save / visit_done との相関を見る

---

### PR3: Shrine Meaning Match の breakdown 改善

目的:

- `score_v2.signals` に Shrine Meaning の一致経路をより明確に出す

候補:

```json
{
  "shrine_meaning_signals": {
    "matched_by_goriyaku_tag_ids": [1, 2],
    "matched_by_goriyaku_text": ["仕事運"],
    "matched_by_history_theme": ["勝負"],
    "matched_by_description": ["挑戦"]
  }
}
```

---

### PR4: culture_translation coverage 拡張

目的:

- 固有文脈のある神社を増やす

TODO:

- [ ] 上位表示神社の culture_translation 追加候補を洗い出す
- [ ] 三峯神社 / 鹿島神宮以外の重要神社を追加
- [ ] 表示品質と行動率の相関を見る

---

## 現時点の判断

Shrine Meaning Profile は、現段階では以下で十分。

```text
goriyaku
goriyaku_tags
goriyaku_tag_ids
history_theme
description
culture_translation
origin_summary
```

ただし、Recommendation Score v2 に直接入れるのは以下に限定する。

```text
goriyaku
goriyaku_tags
goriyaku_tag_ids
history_theme
description
```

`culture_translation` と `origin_summary` は、初期段階では表示・納得感・固有性補強として扱う。

これにより、Recommendation Score v2 は以下の構造を維持できる。

```text
User State Match
+ Shrine Meaning Match
+ Context Match
+ Behavior Signal
```
