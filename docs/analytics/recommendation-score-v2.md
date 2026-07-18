> **Status: Reference**
>
> 本ドキュメントは、Recommendation Score v2の4 Profile統合設計の背景を記録した参照資料である。
>
> 現行のスコア式・重みは`docs/analytics/recommendation-score-v2-current-design.md`、各Profileの定義は`docs/analytics/user-state-profile.md`等を正本とする。

# Recommendation Score v2

## 目的

Recommendation Score v2 は、神社推薦に使う複数の判断材料を分離し、どの要素が推薦順位に影響したかを説明可能にするためのスコア設計である。

この設計では、以下の4 Profileを統合する。

```text
User State Profile
+ Shrine Meaning Profile
+ Context Profile
+ Behavior Profile
↓
Recommendation Score v2
```

目的は、単にスコアを高くすることではない。

ユーザーの相談意図、神社側の意味、その時の条件、過去行動を分けたまま、推薦順位へ接続することで、後から改善・検証できる状態を作る。

---

## 前提

Recommendation Score v2 は、以下の責務分離を前提にする。

```text
User State
= 相談意図

Shrine Meaning
= 神社側の意味・ご利益・歴史文脈

Context
= その時の条件・距離・相性・参拝スタイル

Behavior
= 過去行動・保存・参拝・振り返り
```

これらを混ぜずに、`score_v2.components` へ写像する。

---

## 4 Profile と score_v2 components の対応

| Profile | score_v2 component | 意味 |
|---|---|---|
| User State Profile | user_state_match | 相談意図との強い一致 |
| Shrine Meaning Profile | shrine_meaning_match | 神社側意味との接点 |
| Context Profile | context_match | 参拝スタイル条件との一致 |
| Context Profile | distance_score | 距離の近さ |
| Context Profile | element_match | 相性・五行要素 |
| Context Profile | astro_bonus | 生年月日による補助 |
| Context Profile | direction_bonus | 方位補助 |
| Behavior Profile | behavior_signal | 過去行動の強さ |
| Behavior Profile | behavior_contribution | 行動履歴の加点 |
| Behavior Profile | capped_behavior_contribution | cap後の行動加点 |
| Behavior Profile | behavior_ratio | 行動加点比率 |
| Popularity | popularity_score | 人気・既存指標 |

---

## 入力一覧

### User State Profile

主な入力:

- query
- need_tags
- matched_need_tags
- matched_by_tag
- matched_by_text
- matched_by_gid
- requested_goriyaku_tag_ids

主な生成値:

```text
score_need
score_need_rank
score_need_rank_weighted
```

---

### Shrine Meaning Profile

主な入力:

- goriyaku
- goriyaku_tags
- goriyaku_tag_ids
- description
- history_theme
- sajin
- culture_translation
- origin_summary

主な生成値:

```text
score_need
matched_all
reason_facts
primary_reason
```

注意:

- `culture_translation` と `origin_summary` は初期段階では主に表示補助
- generated copy は ranking score に直接混ぜない

---

### Context Profile

主な入力:

- distance_m
- area
- lat/lng
- extra_condition
- visit_style_tags
- birthdate
- astro_profile
- public_mode
- flow
- weights

主な生成値:

```text
score_distance
score_visit_style
matched_visit_style_tags
score_element
astro_bonus
direction_bonus
```

---

### Behavior Profile

主な入力:

- ShrineInteractionLog.detail_view
- ShrineInteractionLog.route_open
- Favorite
- Visit(status="added")
- ShrineReflection

主な生成値:

```text
behavior_signal
behavior_contribution
capped_behavior_contribution
behavior_ratio
action_state
```

注意:

- ActionEvent は現時点では Recommendation Score v2 に直接混ぜない
- ActionEvent は Action Profile として別軸で扱う

---

## 現行の score_v2.components

現行実装では、`score_v2.components` に以下が入る。

```text
user_state_match
shrine_meaning_match
context_match
element_match
distance_score
popularity_score
astro_bonus
behavior_signal
behavior_contribution
capped_behavior_contribution
behavior_ratio
direction_bonus
direction_reason
```

---

## 基本式

現行の順位用ベーススコアは以下。

```text
score_total_ranked_base
= score_element × element_weight
+ score_need_rank_weighted × need_weight
+ score_popular × popular_weight
+ score_distance × distance_weight
+ score_visit_style × visit_style_weight
+ astro_bonus
+ direction_bonus
```

現行変数では以下に対応する。

```text
score_total_ranked_base
= element_match
+ user_state_match
+ popularity_score
+ distance_score
+ context_match
+ astro_bonus
+ direction_bonus
```

最終順位用スコアは以下。

```text
score_total_ranked
= score_total_ranked_base
+ capped_behavior_contribution
```

`score_v2.total` は `score_total_ranked` を表す。

---

## user_state_match

```text
user_state_match
= score_need_rank_weighted × need_weight
```

意味:

- 相談内容との強い一致
- matched_by_tag / matched_by_gid / matched_by_text を重み付きで扱う

現行の raw 値:

```text
score_need_rank_weighted
= matched_by_tag_count × 2.0
+ matched_by_gid_count × 2.0
+ text_score_sum × 1.2
+ study_bonus
```

扱い:

- User State Profile の主スコア
- 推薦順位に強く影響する

---

## shrine_meaning_match

```text
shrine_meaning_match
= score_need × need_weight
```

意味:

- 神社側の意味情報が相談テーマとどれだけ接点を持つか
- `matched_all` の件数ベース

現行の raw 値:

```text
score_need = len(matched_all)
```

扱い:

- Shrine Meaning Profile のスコア
- `user_state_match` より単純な一致数として扱う

注意:

- 現行では `user_state_match` と同じ need_weight を使っている
- 将来的に Shrine Meaning 独立weightを切り出す余地がある

---

## context_match

```text
context_match
= score_visit_style × 0.35
```

意味:

- ユーザーが求める参拝スタイルと神社側タグの一致

現行の raw 値:

```text
score_visit_style = len(matched_visit_style_tags)
```

対象:

- quiet
- less_crowded
- walkable
- calm

扱い:

- Context Profile の Visit Style Context
- 初期 weight は固定値 0.35

---

## distance_score

```text
distance_score
= score_distance × distance_weight
```

現行の距離減衰:

```text
score_distance = exp(-distance_m / 2500.0)
```

意味:

- 近いほど高い
- 遠いほど指数的に下がる

扱い:

- Context Profile の Location Context
- need mode では距離weightが高め
- compat mode では距離weightが低め

---

## element_match

```text
element_match
= score_element × element_weight
```

意味:

- 五行・相性要素の一致
- Compatibility Context の主スコア

扱い:

- compat mode では重くなる
- need mode でも一定の補助として残る

---

## popularity_score

```text
popularity_score
= score_popular × popular_weight
```

現行の正規化:

```text
score_popular = clamp01(popular_score / 10.0)
```

意味:

- 人気・既存評価の補助

扱い:

- need mode では 0.1
- compat mode では 0.0
- 主理由にはしすぎない

---

## astro_bonus

```text
astro_bonus
= compat mode の補助加点
```

現行値:

```text
pri == 2 → 0.6
pri == 1 → 0.3
otherwise → 0.0
```

条件:

```text
astro_bonus_enabled = public_mode == "compat"
```

扱い:

- Compatibility Context の補助
- need mode では原則無効

---

## direction_bonus

```text
direction_bonus
= min(direction_result.bonus, DIRECTION_BONUS_MAX)
```

意味:

- 方位補助
- 将来拡張用の契約

現状:

- user_origin がない場合は 0.0
- direction_reason は None
- 現時点ではランキングを逆転させない補助枠

注意:

- 方位を主理由にしない
- 表示では `directionSupportCopy` の補助に留める

---

## behavior_signal

```text
behavior_signal
= calculate_shrine_behavior_signal_v2(user, shrine_id)
```

対象:

- detail_view
- route_open
- save / favorite
- visit_done
- reflection_saved

現行重み:

| イベント | 重み |
|---|---:|
| detail_view | 0.2 × 回数 × recency |
| route_open | 0.6 × 回数 × recency |
| save / favorite | 1.5 × recency |
| visit_done | 3.0 × recency |
| reflection_saved | 4.0 × recency |

上限:

```text
behavior_signal <= 10.0
```

---

## behavior_contribution と cap

Behavior はそのまま最終スコアに足さない。

現行式:

```text
behavior_contribution
= behavior_signal × 0.1
```

行動履歴が強くなりすぎないように cap をかける。

```text
behavior_cap
= score_total_ranked_base × 0.3
```

```text
capped_behavior_contribution
= min(behavior_contribution, behavior_cap)
```

```text
behavior_ratio
= capped_behavior_contribution / score_total_ranked_base
```

最終式:

```text
score_total_ranked
= score_total_ranked_base
+ capped_behavior_contribution
```

方針:

- 行動履歴は推薦を補助する
- 相談内容や神社意味を上書きしない
- 行動だけで順位が暴走しないようにする

---

## mode別 weights

### need mode

```text
element: 0.6
need: 0.3
popular: 0.1
distance: 0.35
```

意味:

- 相談内容と距離を重視
- 人気は補助

---

### compat mode

```text
element: 0.8
need: 0.2
popular: 0.0
distance: 0.15
```

意味:

- 相性を重視
- 距離は弱め
- 人気は順位に入れない

---

## 公開スコアと内部順位スコア

現行では、2種類のスコアがある。

### score_total

```text
score_total
= score_element × element_weight
+ score_need × need_weight
+ score_popular × popular_weight
+ astro_bonus
+ direction_bonus
```

用途:

- API契約用の公開スコア
- 画面表示や explanation の基本値

注意:

- distance_score / context_match / behavior は含まれない

---

### score_total_ranked

```text
score_total_ranked
= score_total_ranked_base
+ capped_behavior_contribution
```

用途:

- 実際の並び順
- `_score_total`
- `score_v2.total`

注意:

- distance_score / context_match / behavior cap を含む

---

## score_v2.signals

`score_v2.signals` には、スコアの根拠になる一致経路を入れる。

現行:

```text
matched_need_tags
matched_by_tag
matched_by_text
matched_by_gid
matched_visit_style_tags
matched_user_selected_goriyaku_tag_ids
```

用途:

- explanation
- debug
- PostHog / observation
- 将来の重み補正

---

## 未実装・補助扱いの要素

### ActionEvent

現時点では Recommendation Score v2 に直接混ぜない。

理由:

- 神社そのものへの行動ではなく、行動提案への反応だから
- Shrine Behavior と Action Profile を混ぜると分析しづらい

---

### direction_bonus

契約はあるが、本格運用は未実装寄り。

現時点では、user_origin がなければ 0.0。

---

### culture_translation / origin_summary

表示補助として扱う。

現時点では ranking score に直接混ぜない。

---

### soft_signal_tags

表示・説明補助として扱う。

現時点では ranking score への直接加点は限定的。

---

## PostHogで検証するKPI

### User State

- need_tag別 detail_view rate
- need_tag別 save rate
- need_tag別 route_open rate

---

### Shrine Meaning

- history_theme別 save rate
- goriyaku_tag_ids一致有無別 route_open rate
- matched_by_gid 有無別 visit_done rate

---

### Context

- distance bucket別 route_open rate
- visit_style_tags別 save rate
- compat mode / need mode別 CVR

---

### Behavior

- behavior_signal bucket別 再相談率
- saved → visit_done rate
- visit_done → reflection_saved rate
- reflection_saved 後の継続率

---

## 次PR候補

### PR1: score_v2 documentation 固定

目的:

- 現行式を docs に固定する
- 4 Profile と score_v2.components の対応を明確にする

TODO:

- [ ] `docs/analytics/recommendation-score-v2.md` を作成
- [ ] 各 component の式を明記
- [ ] 未実装要素を明記

---

### PR2: score_v2 debug view / dashboard

目的:

- 各推薦候補の `score_v2.components` を見やすくする

TODO:

- [ ] component別 contribution を表示
- [ ] top contributors を表示
- [ ] behavior cap の効き具合を表示

---

### PR3: weights 検証

目的:

- 現行weightがCVRに寄与しているか検証する

TODO:

- [ ] need mode の distance weight を検証
- [ ] compat mode の element weight を検証
- [ ] context_match 0.35 の妥当性を検証
- [ ] behavior cap 30% の妥当性を検証

---

## 現時点の判断

Recommendation Score v2 は、現段階では以下の式で固定する。

```text
score_total_ranked_base
= element_match
+ user_state_match
+ popularity_score
+ distance_score
+ context_match
+ astro_bonus
+ direction_bonus
```

```text
score_total_ranked
= score_total_ranked_base
+ capped_behavior_contribution
```

Behavior は重要だが、相談意図・神社意味・Context を上書きしすぎないよう cap を維持する。

ActionEvent / direction_bonus / culture_translation は、初期段階では補助または未実装扱いとして切り分ける。

## score_v2.signals 現在形

score_v2.signals には、推薦スコアの根拠となる観測用 payload を入れる。

### user_state_profile

配置:
- recs["_debug"]["user_state_profile"]
- ranking_breakdown_observation["_debug"]["user_state_profile"]

責務:
- query / extra_condition / need_tags / need_hits / selected_goriyaku_tag_ids を保持する
- matched_need_tags / primary_need_tag は top recommendation 由来の User × Shrine 一致結果として扱う

### shrine_meaning_profile

配置:
- score_v2.signals.shrine_meaning_profile
- ranking_breakdown_observation.top10[*].shrine_meaning_profile

責務:
- goriyaku / goriyaku_tags / goriyaku_tag_ids / history_theme を保持する
- culture_translation / origin_summary の有無を観測する
- matched_by_tag / matched_by_text / matched_by_gid を Shrine Meaning 側の一致経路として保持する

### context_profile

配置:
- score_v2.signals.context_profile
- ranking_breakdown_observation.top10[*].context_profile

責務:
- distance_m / score_distance を保持する
- requested_visit_style_tags / visit_style_tags / matched_visit_style_tags を保持する
- direction_bonus / direction_reason を方位補助として保持する

### behavior_profile

配置:
- score_v2.signals.behavior_profile
- ranking_breakdown_observation.top10[*].behavior_profile

責務:
- action_state を保持する
- behavior_breakdown / behavior_signal / behavior_contribution / capped_behavior_contribution / behavior_ratio を保持する
- visit_signal / reflection_signal / reflection_hint を保持する

### 注意

これらの Profile は観測契約であり、追加しただけでは新しいランキング加点を発生させない。
score_v2.total を変える場合は、別PRで重み設計と検証を行う。
