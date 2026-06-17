

# Score V2 Behavior CVR SQL

## 目的

score_v2 と save / detail_view / route_open の行動率を実測で確認するための SQL 方針を整理する。

このドキュメントでは、以下を行う。

```markdown
- score_v2 が recommendation_log に保存されているか確認する
- recommendation_log のサンプルを取得する
- recommendations JSON から score_v2 を抽出する
- save率を集計する
- detail_view率を集計する
- route_open率を集計する
- score_v2帯別CVRを集計する
- score_v2 と行動率の相関確認手順を整理する
```

この段階では、Behavior Signal の重み変更は行わない。

---

## 前提

score_v2 の取得元は以下を第一候補とする。

```text
temples_concierge_recommendation_log.recommendations
```

recommendations は JSON 配列として保存されている想定。

各 recommendation に以下が含まれているかを確認する。

```markdown
- shrine_id または id
- name または display_name
- score_v2.total
- score_v2.components.user_state_match
- score_v2.components.shrine_meaning_match
- score_v2.components.context_match
- score_v2.components.behavior_contribution
```

---

## 1. score_v2保存実データ確認SQL

### ゴール

実DB上で recommendations JSON に score_v2 が保存されているか確認する。

### SQL

```sql
SELECT
  id AS recommendation_log_id,
  thread_id,
  user_id,
  created_at,
  jsonb_array_length(recommendations::jsonb) AS recommendation_count,
  EXISTS (
    SELECT 1
    FROM jsonb_array_elements(recommendations::jsonb) AS rec
    WHERE rec ? 'score_v2'
  ) AS has_score_v2
FROM temples_concierge_recommendation_log
WHERE recommendations IS NOT NULL
ORDER BY created_at DESC
LIMIT 20;
```

### 見るポイント

```markdown
- has_score_v2 が true か
- recommendation_count が 0 より大きいか
- thread_id / user_id が入っているか
```

---

## 2. recommendation_logサンプル取得SQL

### ゴール

recommendations JSON の実際のキー構造を確認する。

### SQL

```sql
SELECT
  id AS recommendation_log_id,
  thread_id,
  user_id,
  created_at,
  jsonb_pretty(recommendations::jsonb) AS recommendations_sample
FROM temples_concierge_recommendation_log
WHERE recommendations IS NOT NULL
ORDER BY created_at DESC
LIMIT 3;
```

### 見るポイント

```markdown
- shrine_id があるか
- id が shrine_id として使えるか
- score_v2.total があるか
- score_v2.components があるか
- rank 相当の値があるか
```

---

## 3. score_v2抽出SQL

### ゴール

recommendations JSON を行単位に展開し、score_v2 を集計可能な形にする。

### SQL

```sql
WITH expanded_recommendations AS (
  SELECT
    l.id AS recommendation_log_id,
    l.thread_id,
    l.user_id,
    l.created_at AS recommended_at,
    rec.ordinality AS rank,
    COALESCE(
      NULLIF(rec.item->>'shrine_id', '')::int,
      NULLIF(rec.item->>'id', '')::int
    ) AS shrine_id,
    COALESCE(
      rec.item->>'display_name',
      rec.item->>'name',
      rec.item->>'title'
    ) AS shrine_name,
    NULLIF(rec.item->'score_v2'->>'total', '')::float AS score_v2_total,
    NULLIF(rec.item->'score_v2'->'components'->>'user_state_match', '')::float AS user_state_match,
    NULLIF(rec.item->'score_v2'->'components'->>'shrine_meaning_match', '')::float AS shrine_meaning_match,
    NULLIF(rec.item->'score_v2'->'components'->>'context_match', '')::float AS context_match,
    NULLIF(rec.item->'score_v2'->'components'->>'behavior_contribution', '')::float AS behavior_contribution
  FROM temples_concierge_recommendation_log l
  CROSS JOIN LATERAL jsonb_array_elements(l.recommendations::jsonb) WITH ORDINALITY AS rec(item, ordinality)
  WHERE l.recommendations IS NOT NULL
)
SELECT *
FROM expanded_recommendations
WHERE score_v2_total IS NOT NULL
ORDER BY recommended_at DESC, rank ASC
LIMIT 50;
```

### 注意

`COALESCE(NULLIF(... )::int, ...)` は、キーが空文字の場合に落ちる可能性を下げるための仮置き。

実DBのキー構造によっては、`shrine_id` 抽出式を調整する。

---

## 4. save率集計SQL

### ゴール

score_v2帯ごとに、推薦後に保存された割合を見る。

### SQL

```sql
WITH expanded_recommendations AS (
  SELECT
    l.id AS recommendation_log_id,
    l.thread_id,
    l.user_id,
    l.created_at AS recommended_at,
    rec.ordinality AS rank,
    COALESCE(
      NULLIF(rec.item->>'shrine_id', '')::int,
      NULLIF(rec.item->>'id', '')::int
    ) AS shrine_id,
    NULLIF(rec.item->'score_v2'->>'total', '')::float AS score_v2_total
  FROM temples_concierge_recommendation_log l
  CROSS JOIN LATERAL jsonb_array_elements(l.recommendations::jsonb) WITH ORDINALITY AS rec(item, ordinality)
  WHERE l.recommendations IS NOT NULL
), scored AS (
  SELECT
    *,
    CASE
      WHEN score_v2_total < 2 THEN '0-2'
      WHEN score_v2_total < 4 THEN '2-4'
      WHEN score_v2_total < 6 THEN '4-6'
      WHEN score_v2_total < 8 THEN '6-8'
      ELSE '8+'
    END AS score_band
  FROM expanded_recommendations
  WHERE score_v2_total IS NOT NULL
    AND user_id IS NOT NULL
    AND shrine_id IS NOT NULL
), with_save AS (
  SELECT
    s.*,
    EXISTS (
      SELECT 1
      FROM temples_favorite f
      WHERE f.user_id = s.user_id
        AND f.shrine_id = s.shrine_id
        AND f.created_at >= s.recommended_at
        AND f.created_at < s.recommended_at + INTERVAL '7 days'
    ) AS saved_after_recommendation
  FROM scored s
)
SELECT
  score_band,
  COUNT(*) AS recommendation_count,
  COUNT(*) FILTER (WHERE saved_after_recommendation) AS save_count,
  ROUND(
    COUNT(*) FILTER (WHERE saved_after_recommendation)::numeric / NULLIF(COUNT(*), 0),
    4
  ) AS save_rate
FROM with_save
GROUP BY score_band
ORDER BY score_band;
```

### 注意

Favorite は thread_id を持たないため、初期監査では `推薦後7日以内` を仮の紐付け条件にする。

必要に応じて `24 hours` でも比較する。

---

## 5. detail_view率集計SQL

### ゴール

score_v2帯ごとに、推薦後に詳細閲覧された割合を見る。

### SQL

```sql
WITH expanded_recommendations AS (
  SELECT
    l.id AS recommendation_log_id,
    l.thread_id,
    l.user_id,
    l.created_at AS recommended_at,
    rec.ordinality AS rank,
    COALESCE(
      NULLIF(rec.item->>'shrine_id', '')::int,
      NULLIF(rec.item->>'id', '')::int
    ) AS shrine_id,
    NULLIF(rec.item->'score_v2'->>'total', '')::float AS score_v2_total
  FROM temples_concierge_recommendation_log l
  CROSS JOIN LATERAL jsonb_array_elements(l.recommendations::jsonb) WITH ORDINALITY AS rec(item, ordinality)
  WHERE l.recommendations IS NOT NULL
), scored AS (
  SELECT
    *,
    CASE
      WHEN score_v2_total < 2 THEN '0-2'
      WHEN score_v2_total < 4 THEN '2-4'
      WHEN score_v2_total < 6 THEN '4-6'
      WHEN score_v2_total < 8 THEN '6-8'
      ELSE '8+'
    END AS score_band
  FROM expanded_recommendations
  WHERE score_v2_total IS NOT NULL
    AND user_id IS NOT NULL
    AND shrine_id IS NOT NULL
), with_detail_view AS (
  SELECT
    s.*,
    EXISTS (
      SELECT 1
      FROM temples_shrineinteractionlog i
      WHERE i.user_id = s.user_id
        AND i.shrine_id = s.shrine_id
        AND i.action_type = 'detail_view'
        AND i.created_at >= s.recommended_at
        AND i.created_at < s.recommended_at + INTERVAL '7 days'
        AND (s.thread_id IS NULL OR i.thread_id = s.thread_id OR i.thread_id IS NULL)
    ) AS detail_viewed_after_recommendation
  FROM scored s
)
SELECT
  score_band,
  COUNT(*) AS recommendation_count,
  COUNT(*) FILTER (WHERE detail_viewed_after_recommendation) AS detail_view_count,
  ROUND(
    COUNT(*) FILTER (WHERE detail_viewed_after_recommendation)::numeric / NULLIF(COUNT(*), 0),
    4
  ) AS detail_view_rate
FROM with_detail_view
GROUP BY score_band
ORDER BY score_band;
```

---

## 6. route_open率集計SQL

### ゴール

score_v2帯ごとに、推薦後にルート表示された割合を見る。

### SQL

```sql
WITH expanded_recommendations AS (
  SELECT
    l.id AS recommendation_log_id,
    l.thread_id,
    l.user_id,
    l.created_at AS recommended_at,
    rec.ordinality AS rank,
    COALESCE(
      NULLIF(rec.item->>'shrine_id', '')::int,
      NULLIF(rec.item->>'id', '')::int
    ) AS shrine_id,
    NULLIF(rec.item->'score_v2'->>'total', '')::float AS score_v2_total
  FROM temples_concierge_recommendation_log l
  CROSS JOIN LATERAL jsonb_array_elements(l.recommendations::jsonb) WITH ORDINALITY AS rec(item, ordinality)
  WHERE l.recommendations IS NOT NULL
), scored AS (
  SELECT
    *,
    CASE
      WHEN score_v2_total < 2 THEN '0-2'
      WHEN score_v2_total < 4 THEN '2-4'
      WHEN score_v2_total < 6 THEN '4-6'
      WHEN score_v2_total < 8 THEN '6-8'
      ELSE '8+'
    END AS score_band
  FROM expanded_recommendations
  WHERE score_v2_total IS NOT NULL
    AND user_id IS NOT NULL
    AND shrine_id IS NOT NULL
), with_route_open AS (
  SELECT
    s.*,
    EXISTS (
      SELECT 1
      FROM temples_shrineinteractionlog i
      WHERE i.user_id = s.user_id
        AND i.shrine_id = s.shrine_id
        AND i.action_type = 'route_open'
        AND i.created_at >= s.recommended_at
        AND i.created_at < s.recommended_at + INTERVAL '7 days'
        AND (s.thread_id IS NULL OR i.thread_id = s.thread_id OR i.thread_id IS NULL)
    ) AS route_opened_after_recommendation
  FROM scored s
)
SELECT
  score_band,
  COUNT(*) AS recommendation_count,
  COUNT(*) FILTER (WHERE route_opened_after_recommendation) AS route_open_count,
  ROUND(
    COUNT(*) FILTER (WHERE route_opened_after_recommendation)::numeric / NULLIF(COUNT(*), 0),
    4
  ) AS route_open_rate
FROM with_route_open
GROUP BY score_band
ORDER BY score_band;
```

---

## 7. score_v2帯別CVR集計SQL

### ゴール

save / detail_view / route_open を同時に見て、score_v2帯ごとの行動率を比較する。

### SQL

```sql
WITH expanded_recommendations AS (
  SELECT
    l.id AS recommendation_log_id,
    l.thread_id,
    l.user_id,
    l.created_at AS recommended_at,
    rec.ordinality AS rank,
    COALESCE(
      NULLIF(rec.item->>'shrine_id', '')::int,
      NULLIF(rec.item->>'id', '')::int
    ) AS shrine_id,
    NULLIF(rec.item->'score_v2'->>'total', '')::float AS score_v2_total,
    NULLIF(rec.item->'score_v2'->'components'->>'user_state_match', '')::float AS user_state_match,
    NULLIF(rec.item->'score_v2'->'components'->>'shrine_meaning_match', '')::float AS shrine_meaning_match,
    NULLIF(rec.item->'score_v2'->'components'->>'context_match', '')::float AS context_match,
    NULLIF(rec.item->'score_v2'->'components'->>'behavior_contribution', '')::float AS behavior_contribution
  FROM temples_concierge_recommendation_log l
  CROSS JOIN LATERAL jsonb_array_elements(l.recommendations::jsonb) WITH ORDINALITY AS rec(item, ordinality)
  WHERE l.recommendations IS NOT NULL
), scored AS (
  SELECT
    *,
    CASE
      WHEN score_v2_total < 2 THEN '0-2'
      WHEN score_v2_total < 4 THEN '2-4'
      WHEN score_v2_total < 6 THEN '4-6'
      WHEN score_v2_total < 8 THEN '6-8'
      ELSE '8+'
    END AS score_band
  FROM expanded_recommendations
  WHERE score_v2_total IS NOT NULL
    AND user_id IS NOT NULL
    AND shrine_id IS NOT NULL
), with_actions AS (
  SELECT
    s.*,
    EXISTS (
      SELECT 1
      FROM temples_favorite f
      WHERE f.user_id = s.user_id
        AND f.shrine_id = s.shrine_id
        AND f.created_at >= s.recommended_at
        AND f.created_at < s.recommended_at + INTERVAL '7 days'
    ) AS saved_after_recommendation,
    EXISTS (
      SELECT 1
      FROM temples_shrineinteractionlog i
      WHERE i.user_id = s.user_id
        AND i.shrine_id = s.shrine_id
        AND i.action_type = 'detail_view'
        AND i.created_at >= s.recommended_at
        AND i.created_at < s.recommended_at + INTERVAL '7 days'
        AND (s.thread_id IS NULL OR i.thread_id = s.thread_id OR i.thread_id IS NULL)
    ) AS detail_viewed_after_recommendation,
    EXISTS (
      SELECT 1
      FROM temples_shrineinteractionlog i
      WHERE i.user_id = s.user_id
        AND i.shrine_id = s.shrine_id
        AND i.action_type = 'route_open'
        AND i.created_at >= s.recommended_at
        AND i.created_at < s.recommended_at + INTERVAL '7 days'
        AND (s.thread_id IS NULL OR i.thread_id = s.thread_id OR i.thread_id IS NULL)
    ) AS route_opened_after_recommendation
  FROM scored s
)
SELECT
  score_band,
  COUNT(*) AS recommendation_count,
  ROUND(AVG(score_v2_total)::numeric, 4) AS avg_score_v2_total,
  ROUND(AVG(user_state_match)::numeric, 4) AS avg_user_state_match,
  ROUND(AVG(shrine_meaning_match)::numeric, 4) AS avg_shrine_meaning_match,
  ROUND(AVG(context_match)::numeric, 4) AS avg_context_match,
  ROUND(AVG(behavior_contribution)::numeric, 4) AS avg_behavior_contribution,
  COUNT(*) FILTER (WHERE saved_after_recommendation) AS save_count,
  COUNT(*) FILTER (WHERE detail_viewed_after_recommendation) AS detail_view_count,
  COUNT(*) FILTER (WHERE route_opened_after_recommendation) AS route_open_count,
  ROUND(COUNT(*) FILTER (WHERE saved_after_recommendation)::numeric / NULLIF(COUNT(*), 0), 4) AS save_rate,
  ROUND(COUNT(*) FILTER (WHERE detail_viewed_after_recommendation)::numeric / NULLIF(COUNT(*), 0), 4) AS detail_view_rate,
  ROUND(COUNT(*) FILTER (WHERE route_opened_after_recommendation)::numeric / NULLIF(COUNT(*), 0), 4) AS route_open_rate
FROM with_actions
GROUP BY score_band
ORDER BY score_band;
```

---

## 8. score_v2と行動率の相関確認手順

### 手順

```markdown
1. score_v2保存実データ確認SQLを実行
2. recommendations JSONのキー構造を確認
3. score_v2抽出SQLを実行
4. save / detail_view / route_open の個別SQLを実行
5. score_v2帯別CVR集計SQLを実行
6. score_v2帯が高いほど行動率が上がるか確認
7. behavior_contribution が行動率に対して強すぎるか弱すぎるか確認
```

### 判断基準

```markdown
- score_v2帯が高いほど save_rate が上がる → score_v2は保存意欲と整合
- score_v2帯が高いほど detail_view_rate が上がる → score_v2は興味喚起と整合
- score_v2帯が高いほど route_open_rate が上がる → score_v2は行動意欲と整合
- behavior_contribution が高いのに行動率が低い → behavior重み過大の可能性
- behavior_contribution が低いのに行動率が高い → behavior重み過小の可能性
```

### 保留

以下は実測結果を見るまで変更しない。

```markdown
- Behavior Signal重み
- score_v2計算式
- 推薦順位
```

---

## TODO

```markdown
- [x] develop最新化
- [x] docs/score-v2-behavior-cvr-sql作成
- [x] score_v2保存実データ確認SQL作成
- [x] recommendation_logサンプル取得SQL作成
- [x] score_v2抽出SQL作成
- [x] save率集計SQL作成
- [x] detail_view率集計SQL作成
- [x] route_open率集計SQL作成
- [x] score_v2帯別CVR集計SQL作成
- [x] score_v2と行動率の相関確認手順を整理
```
