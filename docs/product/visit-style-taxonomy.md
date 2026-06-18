

# Visit Style Taxonomy

## 目的

Concierge First の補助条件として使う参拝スタイルを整理する。

このドキュメントでは、現行の `QUICK_PRESETS`、`extraCondition`、`visit_style_tags`、Recommendation Score v2 との接続を整理し、UIで扱う参拝スタイルを3レイヤーに分けて定義する。

参拝スタイルは相談テーマを上書きするものではなく、候補神社の並び替えや説明補強に使う補助条件として扱う。

---

## 結論

MVPでは、参拝スタイルを以下の3レイヤーで扱う。

```markdown
# 体験スタイル
- 静かな時間を過ごしたい
- 気分を切り替えたい
- 自然を感じたい
- 歴史や文化に触れたい
- 特別な体験をしたい
- 写真を楽しみたい

# 実用条件
- 近場がいい
- アクセスしやすい場所がいい
- 有名な神社が安心
- 人混みを避けたい

# 神社好き向け
- 由緒を知りたい
- 御朱印を楽しみたい
- 神話に触れたい
- 境内をゆっくり歩きたい
```

初期実装では、既存 `visit_style_tags` にあるタグへ寄せて扱う。

存在しないタグは、すぐにDBタグ追加せず、まずは `extraCondition` の自然文として保持する。

---

## 現在のQUICK_PRESETS

現在の `ConciergeFilterPanel.tsx` では、以下の `QUICK_PRESETS` が存在する。

```markdown
- 静かに整えたい
- 人混みが苦手
- 近場優先
- 自然を感じたい
- 気持ちを切り替えたい
- 有名な神社が安心
```

### 現在の扱い

`QUICK_PRESETS` は専用 state を持たず、`extraCondition` に文章として追加される。

```text
QUICK_PRESETS
↓
extraCondition
↓
extra_condition_tags.py
↓
visit_style_tags
↓
score_visit_style
```

### 判断

現行構造は維持する。

ただし、UI表示は3レイヤーに整理する。

---

## 現在のvisit_style_tags

現行コード上で確認できる主な `visit_style_tags` は以下。

```markdown
- quiet
- less_crowded
- nearby
- nature
- reset
- classic
- business
- study
- urban
```

### 主な定義元

```text
backend/temples/domain/extra_condition_tags.py
backend/temples/models.py
backend/temples/services/concierge_chat_ranking.py
backend/temples/data/shrines_seed_clean.json
```

### 現在の役割

`visit_style_tags` は、ユーザーの補助条件と神社側の空間・体験特徴の一致を見るために使われる。

---

## 体験スタイル

体験スタイルは、ユーザーが「その神社でどう過ごしたいか」を表す。

| 表示文言 | visit_style_tag候補 | extraCondition文言 | 初期実装方針 |
|---|---|---|---|
| 静かな時間を過ごしたい | quiet | 静かな雰囲気で、気持ちを落ち着けて整理できる場所がいい | 既存タグへ接続 |
| 気分を切り替えたい | reset | 気持ちを切り替えて、前向きになれる場所がいい | 既存タグへ接続 |
| 自然を感じたい | nature | 自然を感じながら、ゆっくり参拝できる場所がいい | 既存タグへ接続 |
| 歴史や文化に触れたい | classic | 歴史や文化を感じながら参拝できる場所がいい | 既存タグへ寄せる |
| 特別な体験をしたい | classic | 日常から少し離れて、特別感のある参拝がしたい | 自然文として保持 |
| 写真を楽しみたい | urban | 写真を撮りながら楽しめる雰囲気の場所がいい | 既存タグへ寄せるか保留 |

### 判断

- `quiet` / `reset` / `nature` は既存タグとして採用する
- `classic` は「有名・定番」だけでなく、歴史文化寄りにも使えるが、意味が広がりすぎるため注意する
- `special` / `photo` のような新タグは初期MVPでは追加しない

---

## 実用条件

実用条件は、参拝しやすさ・移動しやすさ・混雑回避などの現実条件を表す。

| 表示文言 | visit_style_tag候補 | extraCondition文言 | 初期実装方針 |
|---|---|---|---|
| 近場がいい | nearby | できるだけ近い場所を優先して | 既存タグへ接続 |
| アクセスしやすい場所がいい | nearby | 駅から行きやすい、アクセスしやすい場所がいい | `duration_max_min` と併用検討 |
| 有名な神社が安心 | classic | 有名で定番感があり、安心して参拝しやすい場所がいい | 既存タグへ接続 |
| 人混みを避けたい | less_crowded | 混雑しにくい、落ち着いた場所がいい | 既存タグへ接続 |

### 注意

`nearby` は現在地や距離計算と混同しない。

現状では、あくまでユーザーの希望タグとして扱う。

本当に距離・現在地を使う場合は、Location / Route Mode 側で扱う。

---

## 神社好き向け

神社好き向けは、神社そのものへの関心が強いユーザー向けの補助条件である。

| 表示文言 | visit_style_tag候補 | extraCondition文言 | 初期実装方針 |
|---|---|---|---|
| 由緒を知りたい | classic | 由緒や歴史を知りながら参拝したい | `classic` へ寄せる |
| 御朱印を楽しみたい | なし | 御朱印も楽しめる神社がいい | 自然文として保持 |
| 神話に触れたい | classic | 神話や由緒に触れられる神社がいい | `classic` へ寄せる |
| 境内をゆっくり歩きたい | quiet / nature | 境内をゆっくり歩きながら参拝したい | 既存タグの組み合わせで対応 |

### 判断

神社好き向けはMVPでは弱めに扱う。

理由は、Kamimusubiの主導線が「神社好きの検索」ではなく「相談テーマから神社と出会う体験」だから。

ただし、Premiumやリピート体験では価値が出る可能性があるため、設計上は残す。

---

## extraConditionとの対応

現状、参拝スタイルは `extraCondition` に自然文として保存される。

### 現在の流れ

```text
ConciergeFilterPanel
↓
onExtraConditionChange
↓
extraCondition
↓
baseFilters.extra_condition
↓
compatPayload.filters.extra_condition
↓
backend extra_condition_tags.py
↓
visit_style_tags
```

### 既存判定

`extra_condition_tags.py` では、自然文のキーワードから以下のようなタグへ変換している。

| キーワード例 | tag |
|---|---|
| 静か / 落ち着いた | quiet |
| 人混み / 混雑 / 空いて | less_crowded |
| 近い / 近場 / 駅近 | nearby |
| 自然 | nature |
| 切り替え / 前向き | reset |
| 有名 / 定番 / 安心 | classic |
| 仕事 / 商売 | business |
| 学び / 勉強 / 資格 | study |

### 判断

MVPでは `extraCondition` を維持する。

`visitStyle` 専用 state はまだ作らない。

理由は、既存の推薦ロジックが `extraCondition` から `visit_style_tags` を抽出する前提で動いているため。

---

## Recommendation Score v2での扱い

Recommendation Score v2 では、参拝スタイルは補助スコアとして扱われている。

現行設計では、以下の重みがある。

```text
score_visit_style × 0.35
```

### 現在の構造

```text
user_visit_style_tags
↓
shrine_visit_style_tags
↓
matched_visit_style_tags
↓
score_visit_style
↓
context_match
```

### 判断

参拝スタイルは、need一致を上書きしない。

つまり、相談テーマとの一致が弱い神社を、参拝スタイルだけで上位にしすぎない。

現行テストでも、visit_style は補助軸として、同程度のneed一致候補の順位調整に使う方針になっている。

---

## UIでの表示方針

### 表示場所

参拝スタイルは `ConciergeFilterPanel` 内に置く。

HomeHeroには置かない。

### 表示ルール

```markdown
- 相談テーマより目立たせない
- Accordion内の補助条件として扱う
- 3レイヤーに分けて表示する
- 一度に全部見せすぎない
- 初期表示は体験スタイル + 実用条件を優先する
- 神社好き向けは折りたたみ、または後段表示にする
```

### 初期表示案

```text
どんな参拝にしたいですか？

体験スタイル
[静かな時間] [気分を切り替える] [自然を感じる]

実用条件
[近場] [アクセスしやすい] [有名で安心] [人混みを避ける]

神社好き向け
[由緒] [御朱印] [神話] [境内を歩く]
```

---

## 初期MVPで採用する項目

### 採用

```markdown
- 静かな時間を過ごしたい
- 気分を切り替えたい
- 自然を感じたい
- 近場がいい
- アクセスしやすい場所がいい
- 有名な神社が安心
- 人混みを避けたい
```

### 表示は残すが弱める

```markdown
- 歴史や文化に触れたい
- 由緒を知りたい
- 境内をゆっくり歩きたい
```

### 初期MVPでは保留

```markdown
- 特別な体験をしたい
- 写真を楽しみたい
- 御朱印を楽しみたい
- 神話に触れたい
```

---

## 次PR候補

### PR1: Visit Style Taxonomy UI反映

```markdown
- [ ] ConciergeFilterPanel の QUICK_PRESETS を3レイヤー表示へ整理
- [ ] 既存 extraCondition への反映方式は維持
- [ ] quiet / reset / nature / nearby / classic / less_crowded を優先表示
- [ ] 神社好き向けは控えめに表示
- [ ] typecheck
```

### PR2: visit_style_tags表示説明の改善

```markdown
- [ ] 推薦理由で「参拝スタイルとの一致」を補助理由として表示
- [ ] matched_visit_style_tags をユーザー向け文言へ変換
- [ ] 吉方位・相性とは混ぜない
- [ ] Meaning Cardとの表示順を確認
```

### PR3: visit_style_tags拡張検討

```markdown
- [ ] photo / goshuin / mythology / special のタグ追加要否を検討
- [ ] 追加する場合はShrine.visit_style_tagsの既存データ補完を設計
- [ ] CVRを見てから追加判断する
```

---

## TODO

```markdown
- [x] develop最新化
- [x] audit/visit-style-taxonomy作成
- [x] 現在のQUICK_PRESETSを棚卸し
- [x] 体験スタイルを確定
- [x] 実用条件を確定
- [x] 神社好き向けを確定
- [x] extraCondition / visit_style_tags との対応を整理
- [x] docsへ参拝スタイルTaxonomyを追記
```
