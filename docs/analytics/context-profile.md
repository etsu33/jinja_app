> **Status: Active**
>
> 本ドキュメントは、Recommendation Score v2が用いるContext Profileの定義を管理する正本文書である。
>
> 正確な実装・重みおよび計測項目は`docs/analytics/recommendation-score-v2-current-design.md`、関連するBackend実装コードおよびテストを最終的な正本とする。

# Context Profile

## 目的

Context Profile は、ユーザーが神社を探す時の利用条件・状況・参拝しやすさ・表示モードを整理するための定義である。

Recommendation Score v2 では、Context Profile を使って以下を判断する。

```text
ユーザーの相談意図
+ 神社側の意味
+ その時の条件
+ 過去行動
↓
推薦順位
```

Context Profile は、ユーザーの悩みや願いそのものではなく、推薦時点の条件を扱う。

---

## 前提

Recommendation Score v2 の4層は以下である。

```text
User State Match
+ Shrine Meaning Match
+ Context Match
+ Behavior Signal
```

Context Profile は、このうち `Context Match` と `distance_score`、および `element_match` / `astro_bonus` / `direction_bonus` などの補助要素を整理する。

---

## Context Profile の4分類

Context Profile は以下の4分類で扱う。

```text
1. Location Context
2. Visit Style Context
3. Compatibility Context
4. Mode Context
```

---

## 1. Location Context

Location Context は、現在地・検索エリア・神社までの距離に関する条件を扱う。

対象:

- distance_m
- area
- lat/lng

---

### distance_m

`distance_m` は、ユーザーの位置情報または検索起点から候補神社までの距離をメートルで表す。

生成元:

```text
backend/temples/services/concierge_chat_candidates.py
```

主な用途:

- 候補一覧の距離表示
- 距離順ソート
- Recommendation Score v2 の `distance_score`

現行計算:

```text
score_distance = exp(-distance_m / 2500.0)
```

意味:

- 近いほど高い
- 距離が遠くなるほど指数的に下がる
- distance_m がない場合は 0.0

---

### area

`area` は、ユーザーが指定した検索地域や地名を表す。

用途:

- 候補検索の起点
- location_text / area query の解釈
- 近隣候補の取得

注意:

- `area` は User State ではない
- 「どこで探すか」を表す Context 条件である

---

### lat/lng

`lat/lng` は、ユーザー起点または神社位置の緯度経度である。

用途:

- distance_m の計算
- direction_bonus の将来計算
- 地図表示

注意:

- 位置情報がない場合、距離スコアは弱くなる
- ただし神社の意味一致や行動履歴とは別軸として扱う

---

## Location Context の初期方針

```text
distance_m
= distance_score の正本

area / lat / lng
= distance_m と候補取得の材料
```

Recommendation Score v2 では、距離は独立した `distance_score` として扱う。

---

## 2. Visit Style Context

Visit Style Context は、ユーザーがどのような参拝環境・行き方・雰囲気を求めているかを扱う。

対象:

- extra_condition
- visit_style_tags
- soft_signal_tags

---

### extra_condition

`extra_condition` は、ユーザーが追加で指定した条件である。

例:

- 静かな場所がいい
- 混んでいない場所
- 徒歩で行きたい
- 近いところがいい
- 落ち着いて過ごしたい

抽出元:

```text
backend/temples/services/concierge_chat_extra_condition.py
```

`extra_condition` は以下に分解される。

```text
sort_tags
hard_filter_tags
soft_signal_tags
visit_style_tags
```

注意:

- extra_condition は User State ではない
- 相談テーマではなく、参拝条件・検索条件として扱う

---

### visit_style_tags

`visit_style_tags` は、参拝スタイルや空間条件を表すタグである。

例:

- quiet
- less_crowded
- walkable
- calm

現行処理:

```text
user_visit_style_tags
∩
shrine_visit_style_tags
=
matched_visit_style_tags
```

スコア:

```text
score_visit_style = len(matched_visit_style_tags)
context_match = score_visit_style × 0.35
```

用途:

- Recommendation Score v2 の `context_match`
- explanation の補助理由
- 参拝しやすさの説明

---

### soft_signal_tags

`soft_signal_tags` は、候補を除外せずに軽く考慮する追加条件である。

用途:

- explanation / presentation の補助
- 将来的な軽量加点候補

注意:

- 初期段階では強い ranking factor にしない
- hard filter と混ぜない

---

### sort_tags / hard_filter_tags

`sort_tags` は並び替え意図を表す。

例:

- sort_distance

`hard_filter_tags` は候補を絞り込むための強い条件である。

注意:

- hard filter は候補集合を変える
- soft signal は候補集合を変えずに説明や軽い補助に使う
- sort override はスコアではなく並び順制御として扱う

---

## Visit Style Context の初期方針

```text
visit_style_tags
= Context Match の正本

extra_condition
= visit_style_tags / sort_tags / hard_filter_tags / soft_signal_tags の抽出元

soft_signal_tags
= 表示・説明補助
```

---

## 3. Compatibility Context

Compatibility Context は、生年月日・五行・相性・方位など、相談内容とは別の補助的な相性条件を扱う。

対象:

- birthdate
- astro_profile
- element_match
- astro_bonus
- direction_bonus
- direction_reason

---

### birthdate

`birthdate` は、生年月日を使った相性系の入力である。

用途:

- astro_profile の生成
- public_mode = compat の判定材料
- element_match / astro_bonus の補助
- gogyou_context の生成

注意:

- birthdate は User State ではない
- 相談内容ではなく、相性・補助文脈として扱う

---

### astro_profile

`astro_profile` は、生年月日から生成される相性情報である。

生成元:

```text
_resolve_astro_profile
sun_sign_and_element
fortune_profile
```

用途:

- element_match
- astro_bonus
- explanation payload の gogyou_context

注意:

- 相性要素は補助であり、相談意図を上書きしない
- compat mode では相対的に重くなる

---

### element_match

`element_match` は、神社側の element とユーザー側の相性要素の一致を表す。

現行では、Recommendation Score v2 の component として存在する。

```text
score_v2.components.element_match
```

扱い:

- Compatibility Context の主スコア
- User State / Shrine Meaning とは分けて扱う

---

### astro_bonus

`astro_bonus` は、compat mode 時に使われる補助加点である。

用途:

- 生年月日がある場合の相性補正
- compat mode の並び順補助

注意:

- need mode では主軸にしない
- 相談内容を上書きしない

---

### direction_bonus / direction_reason

`direction_bonus` は、将来的な方位スコアのための契約である。

現状:

```text
user_origin がない場合は 0.0
direction calculation はまだ本格実装されていない
```

用途:

- score_v2 contract の将来拡張
- directionSupportCopy の表示補助

注意:

- 現時点ではランキングを逆転させない補助枠
- 方位は主理由にしない

---

## Compatibility Context の初期方針

```text
birthdate
= astro_profile の入力

astro_profile
= element_match / astro_bonus の材料

element_match
= Compatibility Context の主スコア

astro_bonus / direction_bonus
= 補助スコア
```

---

## 4. Mode Context

Mode Context は、推薦ロジックの重みや表示意図を切り替えるための条件を扱う。

対象:

- public_mode
- flow
- weights

---

### public_mode

`public_mode` は、推薦モードを表す。

主な値:

| public_mode | 意味 |
|---|---|
| need | 悩み・相談内容重視 |
| compat | 相性重視 |

現行の重み:

#### need mode

```text
element: 0.6
need: 0.3
popular: 0.1
distance: 0.35
```

#### compat mode

```text
element: 0.8
need: 0.2
popular: 0.0
distance: 0.15
```

意味:

- need mode は相談内容と近さを重視する
- compat mode は生年月日・相性要素を相対的に重視する

---

### flow

`flow` は、推薦体験の入口・UIフローを表す。

現行では、A / B のような flow 値が使われる。

用途:

- mode meta
- UI表示
- 将来的なAB比較

注意:

- flow 自体をスコアに直接入れるのではなく、weights / mode meta の切替に使う

---

### weights

`weights` は、Recommendation Score v2 の各 component の比重である。

主な対象:

- element
- need
- popular
- distance

現行では `_resolve_mode_weights` によって決まる。

注意:

- weights は scoring policy
- ユーザー状態や神社意味そのものではない
- 変更する場合は PostHog の実測とセットで扱う

---

## Mode Context の初期方針

```text
public_mode
= 推薦モード

flow
= 体験入口 / UIフロー

weights
= mode に応じた score policy
```

---

## Recommendation Score v2 の Context Layer

現行の Context 関連 component は以下。

```text
context_match
= score_visit_style × 0.35

distance_score
= score_distance × distance_weight

element_match
= score_element × element_weight

astro_bonus
= compat mode 補助

direction_bonus
= 将来拡張用補助
```

初期整理:

| component | Profile分類 | 意味 |
|---|---|---|
| context_match | Visit Style Context | 参拝スタイル一致 |
| distance_score | Location Context | 距離の近さ |
| element_match | Compatibility Context | 相性要素 |
| astro_bonus | Compatibility Context | 生年月日補助 |
| direction_bonus | Compatibility Context | 方位補助 |
| weights | Mode Context | スコア方針 |

---

## Context Profile と他Profileの境界

### User State Profile ではないもの

- distance_m
- area
- lat/lng
- extra_condition
- visit_style_tags
- birthdate
- astro_profile
- public_mode
- flow

理由:

ユーザーの悩みや願いではなく、推薦時点の条件だから。

---

### Shrine Meaning Profile ではないもの

- distance_m
- user location
- birthdate
- public_mode
- flow

理由:

神社固有の意味ではなく、利用者・利用時点・検索条件に依存するから。

---

### Behavior Profile ではないもの

- extra_condition
- visit_style_tags
- birthdate
- public_mode
- flow

理由:

過去行動ではなく、その場の入力条件だから。

---

## PostHogで見るべき指標

### Location Context

- distance bucket 別 route_open rate
- distance bucket 別 save rate
- distance bucket 別 visit_done rate

例:

```text
0-1km
1-3km
3-5km
5km+
```

---

### Visit Style Context

- visit_style_tags 別 detail_view → route_open CVR
- quiet 指定時の save rate
- less_crowded 指定時の route_open rate

---

### Compatibility Context

- compat mode の save rate
- birthdate 有無別の継続率
- element_match 高低別の route_open rate

---

### Mode Context

- need mode と compat mode のCVR比較
- flow A / B の保存率比較
- mode別 premium_preview_click rate

---

## 未確定事項

- distance_score の decay 係数 2500.0 が妥当か
- context_match の weight 0.35 が妥当か
- compat mode で distance weight 0.15 が低すぎないか
- visit_style_tags のタグ体系を増やすか
- soft_signal_tags をスコアに入れるか
- direction_bonus をいつ本実装するか
- public_mode / flow をPostHog上でどう分析するか

---

## 現時点の判断

Context Profile は、現段階では以下で十分。

```text
Location Context
- distance_m
- area
- lat/lng

Visit Style Context
- extra_condition
- visit_style_tags
- soft_signal_tags

Compatibility Context
- birthdate
- astro_profile
- element_match
- astro_bonus

Mode Context
- public_mode
- flow
- weights
```

Recommendation Score v2 では、Context は以下のように扱う。

```text
context_match
= visit_style_tags の一致

distance_score
= distance_m の距離減衰

element_match / astro_bonus
= compatibility 補助

weights
= public_mode / flow による score policy
```
