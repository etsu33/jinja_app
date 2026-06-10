

# Recommendation Score v2 現行設計

## 目的

Recommendation Score v2 の現行実装を正本として整理し、推薦ロジック・行動シグナル・PostHog計測項目の対応関係を明確にする。

このドキュメントでは、新しいスコア式を作るのではなく、既存コードにある推薦式を読み解き、今後の改善判断に使える形へ固定する。

---

## 結論

Recommendation Score v2 の骨格はすでに実装済み。

現時点では、コード修正ではなく以下を優先する。

- 現行スコア式の正本化
- 行動シグナルの定義整理
- 重みの現在値確認
- PostHog / DBイベント対応表の整理
- 今後、重みを変更する条件の明文化

---

## 現行スコア式

実装箇所:

- `backend/temples/services/concierge_chat_ranking.py`
- `backend/temples/services/concierge_history.py`

### ranked score

```text
score_total_ranked = score_total_ranked_base + capped_behavior_contribution
```

### base score

```text
score_total_ranked_base =
  score_element * w1
+ score_need_rank_weighted * w2
+ score_popular * w3
+ score_distance * w4
+ score_visit_style * w5
+ astro_bonus
+ direction_bonus
```

### behavior contribution

```text
behavior_contribution = behavior_signal * behavior_weight
behavior_cap = min(score_total_ranked_base * 0.3, 0.5)
capped_behavior_contribution = min(behavior_contribution, behavior_cap)
```

### final ranked score

```text
score_total_ranked = score_total_ranked_base + capped_behavior_contribution
```

---

## 重みの現在値

### 確認済み

| 項目 | 現在値 | 実装箇所 | 備考 |
|---|---:|---|---|
| visit_style weight | 0.35 | `w5 = 0.35` | visit_style の一致に使う |
| behavior_weight | 0.1 | `behavior_weight = 0.1` | 行動履歴の寄与率 |
| behavior_cap_ratio | 0.3 | `score_total_ranked_base * 0.3` | base score の最大30%まで |
| behavior_cap_abs | 0.5 | `min(..., 0.5)` | 絶対上限 |

### 確認済みの `w1〜w5`

`w1〜w4` は `weights` から取得される。デフォルトの生成元では以下の値を返す。

| 変数 | 意味 | 現在値 | 備考 |
|---|---|---:|---|
| w1 | element weight | 0.6 | element match の重み |
| w2 | need weight | 0.3 | need match の重み |
| w3 | popular weight | 0.1 | popular score の重み |
| w4 | distance weight | 0.35 | distance decay の重み |
| w5 | visit_style weight | 0.35 | visit_style match の重み |

確認箇所:

```text
backend/temples/services/concierge_chat_ranking.py
```

確認結果:

```python
return {
    "element": 0.6,
    "need": 0.3,
    "popular": 0.1,
    "distance": 0.35,
}
```

補足: `weights` には分岐があるため、compat / flow 別の値を扱う場合は、対象モードごとの生成元を別途確認する。

---

## Profile定義

### User State Profile

ユーザー側の状態・相談意図を表す。

| 要素 | 既存データ | 用途 |
|---|---|---|
| query | 相談文 | need tag 抽出 |
| need_tags | `_need.tags` / `matched_need_tags` | 相談テーマ判定 |
| birthdate | `birthdate` | compat / element 判定 |
| mode | `need` / `compat` | 推薦モード切替 |
| extra_condition | sort / soft / visit_style | 参拝スタイルや条件指定 |

### Shrine Meaning Profile

神社側の意味・特徴を表す。

| 要素 | 既存データ | 用途 |
|---|---|---|
| goriyaku | `Shrine.goriyaku` | ご利益テキスト一致 |
| astro_tags | candidate data | need tag との一致 |
| astro_elements | `Shrine.astro_elements` | element match |
| popular_score | `Shrine.popular_score` | 人気補正 |
| description | candidate description | text match |
| visit_style_tags | `Shrine.visit_style_tags` | 参拝スタイル一致 |

### Context Profile

状況・移動・参拝しやすさを表す。

| 要素 | 既存データ | 用途 |
|---|---|---|
| distance_m | candidate distance | 距離減衰 |
| lat / lng | recommendation log | 位置文脈 |
| radius_m | recommendation log | 検索範囲 |
| flow | recommendation log | 推薦フロー |
| result_state | recommendation log | fallback / result state |
| visit_style_tags | extra_condition / shrine | 参拝スタイル文脈 |

### Behavior Profile

ユーザーが神社に対して行った行動を表す。

| 行動 | 既存データ | v2上の意味 | 初期信号 |
|---|---|---|---:|
| recommendation_click | `ConciergeRecommendationClickLog` | 推薦候補への反応 | 未反映 |
| shrine_card_click | `ShrineInteractionLog.shrine_card_click` | カードクリック | 未反映 |
| detail_view | `ShrineInteractionLog.detail_view` | 詳細確認 | count * 0.2 * recency |
| route_open | `ShrineInteractionLog.route_open` | 行く意図 | count * 0.6 * recency |
| save | `Favorite` | 後で行きたい | 1.5 * recency |
| visit_done | `Visit.status="added"` | 実際に行った | 3.0 * recency |
| reflection_saved | `ShrineReflection` | 行動後の意味づけ | 4.0 * recency |

---

## 行動シグナル式

実装箇所:

- `backend/temples/services/concierge_history.py`

```text
behavior_signal = min(
  detail_view_signal
+ route_open_signal
+ save_signal
+ visit_signal
+ reflection_signal,
  10.0
)
```

### recency multiplier

| 経過日数 | multiplier |
|---|---:|
| 30日以内 | 1.0 |
| 90日以内 | 0.5 |
| 90日超 | 0.2 |

---

## PostHog / DBイベント対応表

| KPI / 行動 | DB | PostHog event候補 | v2反映 |
|---|---|---|---|
| 推薦表示 | `ConciergeRecommendationLog` | `recommendation_view` | 間接 |
| 推薦クリック | `ConciergeRecommendationClickLog` | `recommendation_click` | 未反映 |
| カードクリック | `ShrineInteractionLog.shrine_card_click` | `shrine_card_click` | 未反映 |
| 詳細閲覧 | `ShrineInteractionLog.detail_view` | `detail_view` | 反映済み |
| 経路表示 | `ShrineInteractionLog.route_open` | `route_open` | 反映済み |
| 保存 | `Favorite` | `save` / `favorite_create` | 反映済み |
| 参拝完了 | `Visit.status="added"` | `visit_done` | 反映済み |
| 振り返り保存 | `ShrineReflection` | `reflection_saved` | 反映済み |
| Premium Preview | 未確認 | `premium_preview_view` / `premium_preview_click` | 未反映 |
| Checkout | 未確認 | `checkout_started` | 未反映 |
| Premium Active | 未確認 | `premium_active` | 未反映 |

---

## 現時点で修正しない理由

現行式はすでに以下を満たしている。

- 相談テーマとの一致
- 神社側の意味一致
- 距離減衰
- 参拝スタイル一致
- 人気補正
- 行動履歴
- 行動履歴の過剰反映防止cap

そのため、現時点で重みを変更するより、実データを見てから調整する方が安全。

特に `behavior_cap` は、過去行動だけで同じ神社が出続ける問題を防ぐために重要。

---

## 今後の改善条件

重みを変更する場合は、以下のKPIを見てから判断する。

| KPI | 見る理由 |
|---|---|
| save_rate | 推薦が保存につながるか |
| detail_view_rate | 候補が興味を持たれているか |
| route_open_rate | 行動意図につながるか |
| visit_rate | 実際の参拝につながるか |
| reflection_saved_rate | 継続・意味づけにつながるか |
| save_to_route_cvr | 保存後に行動へ進むか |
| route_to_reflection_cvr | 参拝意図から振り返りへ進むか |
| premium_preview_click_rate | Premium訴求と推薦体験の接点 |

---

## 次アクション

1. compat / flow 別の `weights` 分岐を確認する
2. PostHog event 名の実装状況を確認する
3. `recommendation_click` / `shrine_card_click` を behavior_signal に入れるか判断する
4. 実データが溜まった段階で重みを再調整する

---

## 結論

Recommendation Score v2 は、すでに実装骨格がある。

このPRではコードを変更せず、現行式・行動シグナル・計測対応を正本化する。

重み変更は、PostHogとDB集計で実データを確認してから行う。
