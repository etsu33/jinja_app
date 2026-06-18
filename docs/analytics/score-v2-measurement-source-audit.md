

# Score V2 Measurement Source Audit

## 目的

score_v2 と save / detail_view / route_open の行動相関を確認するために、実測データをどこから取得するかを整理する。

この監査では、重み変更は行わない。

まず、score_v2 が保存されている場所、行動ログとの接続方法、集計SQLの方針を確定する。

---

## 結論

現時点では、score_v2 の実測データ取得元は以下を第一候補とする。

```text
temples_concierge_recommendation_log.recommendations
```

理由は、推薦生成時に各 recommendation に `score_v2` が付与され、その recommendation list が `save_concierge_recommendation_log` 経由で JSONField に保存される構造になっているため。

ただし、これはコード経路上の判断であり、実データで `recommendations[*].score_v2` が保存されているかは次フェーズで確認する。

---

## 現在地

### 確認済み

```markdown
- [x] recommendation_log に thread_id 保存あり
- [x] recommendation_log に recommendations JSON 保存あり
- [x] recommendation_log から shrine_id は recommendations JSON 内で取得可能
- [x] recommendation_log から rank は recommendations 配列順、または recommendation 内の rank 相当から取得可能
- [x] score_v2 はコード経路上 recommendations JSON に保存される見込み
```

### 未確定

```markdown
- [ ] 実DB上の recommendations JSON に score_v2 が存在するか
- [ ] recommendation 内の shrine_id / id / rank の実際のキー名
- [ ] thread_id 経由で ShrineInteractionLog と安定してJOINできるか
- [ ] Favorite は thread_id を持たないため、save率をどう紐付けるか
```

---

## データ保存構造

### ConciergeRecommendationLog

保存テーブル:

```text
temples_concierge_recommendation_log
```

主なカラム:

```markdown
- id
- user_id
- thread_id
- query
- need_tags
- flow
- recommendations
- result_state
- created_at
```

### recommendations JSON

想定される取得対象:

```markdown
- shrine_id / id
- name / display_name
- rank または配列順
- score_v2.total
- score_v2.components.user_state_match
- score_v2.components.shrine_meaning_match
- score_v2.components.context_match
- score_v2.components.behavior_contribution
- score_v2.signals.matched_need_tags
- score_v2.signals.matched_visit_style_tags
```

---

## 行動ログとの接続

### detail_view

保存元:

```text
ShrineInteractionLog(action_type=detail_view)
```

接続候補:

```markdown
- user_id
- shrine_id
- thread_id
- created_at >= recommendation_log.created_at
```

### route_open

保存元:

```text
ShrineInteractionLog(action_type=route_open)
```

接続候補:

```markdown
- user_id
- shrine_id
- thread_id
- created_at >= recommendation_log.created_at
```

### save

保存元:

```text
Favorite
```

接続候補:

```markdown
- user_id
- shrine_id
- created_at >= recommendation_log.created_at
```

注意:

Favorite は thread_id を持たないため、推薦ログとの厳密な紐付けは detail_view / route_open より弱い。

初期監査では、以下のどちらかで扱う。

```markdown
- 推薦後24時間以内の保存
- 推薦後7日以内の保存
```

---

## score_v2実測データ取得方法

### 第一候補

```sql
FROM temples_concierge_recommendation_log
CROSS JOIN LATERAL jsonb_array_elements(recommendations::jsonb) AS rec
```

取得する値:

```sql
rec->'score_v2'->>'total'
rec->'score_v2'->'components'->>'user_state_match'
rec->'score_v2'->'components'->>'shrine_meaning_match'
rec->'score_v2'->'components'->>'context_match'
rec->'score_v2'->'components'->>'behavior_contribution'
```

### rankの扱い

初期監査では、JSON配列順を rank として扱う。

```sql
WITH ORDINALITY
```

を使い、`ordinality` を rank とする。

---

## save率集計SQL方針

### ゴール

score_v2帯ごとに、推薦後に保存された割合を見る。

### 方針

```markdown
- recommendation_log から recommendation を展開
- user_id / shrine_id を取得
- score_v2_total を取得
- Favorite と user_id + shrine_id で接続
- Favorite.created_at が recommendation_log.created_at 以降のものを対象にする
```

### 注意

Favorite は thread_id を持たないため、同一神社を過去に保存済みの場合の扱いを決める必要がある。

初期監査では、以下を分ける。

```markdown
- already_saved: 推薦前に保存済み
- saved_after_recommendation: 推薦後に保存
```

---

## detail_view率集計SQL方針

### ゴール

score_v2帯ごとに、推薦後に詳細閲覧された割合を見る。

### 方針

```markdown
- recommendation_log から recommendation を展開
- thread_id / user_id / shrine_id を取得
- ShrineInteractionLog と接続
- action_type = detail_view
- created_at >= recommendation_log.created_at
```

### 接続優先順位

```text
thread_id + user_id + shrine_id
↓
user_id + shrine_id + created_at window
```

---

## route_open率集計SQL方針

### ゴール

score_v2帯ごとに、推薦後にルート表示された割合を見る。

### 方針

```markdown
- recommendation_log から recommendation を展開
- thread_id / user_id / shrine_id を取得
- ShrineInteractionLog と接続
- action_type = route_open
- created_at >= recommendation_log.created_at
```

### 接続優先順位

```text
thread_id + user_id + shrine_id
↓
user_id + shrine_id + created_at window
```

---

## score_v2帯別CVR監査方針

### score_v2帯

初期監査では以下に分ける。

```markdown
- 0以上 2未満
- 2以上 4未満
- 4以上 6未満
- 6以上 8未満
- 8以上
```

### 見る指標

```markdown
- recommendation_count
- save_count
- detail_view_count
- route_open_count
- save_rate
- detail_view_rate
- route_open_rate
```

### 判断基準

```markdown
- score_v2 が高いほど save_rate が上がるか
- score_v2 が高いほど detail_view_rate が上がるか
- score_v2 が高いほど route_open_rate が上がるか
- behavior_contribution が高い候補ほど行動されているか
```

---

## 保留判断

### 今回やらない

```markdown
- [ ] Behavior Signal重み変更
- [ ] score_v2計算式変更
- [ ] 推薦順位変更
- [ ] DB schema変更
```

### 理由

実データ上で score_v2 と行動率の相関をまだ確認していないため。

先に measurement source を確定し、SQLで現状の相関を確認する。

---

## TODO

```markdown
- [x] develop最新化
- [x] docs/score-v2-measurement-source-audit作成
- [x] recommendation_logにthread_id保存有無を確認
- [x] recommendation_logにshrine_id保存有無を確認
- [x] recommendation_logにrank保存有無を確認
- [x] recommendation_logにscore_v2保存有無を確認（コード経路上は保存見込み。実データ確認は次）
- [x] score_v2実測データ取得方法を決定
- [x] save率集計SQL作成方針を整理
- [x] detail_view率集計SQL作成方針を整理
- [x] route_open率集計SQL作成方針を整理
- [x] score_v2帯別CVR監査方針を整理
```
