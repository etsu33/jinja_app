# Score V2 Production Snapshot

## 目的

Recommendation Score v2 が本番データ上で保存されているか、また save / detail_view / route_open と接続して実測できるかを確認する。

この監査では、重み変更は行わない。

まず、以下を確認する。

```markdown
- recommendation_log 実データ確認
- score_v2 存在率確認
- score_v2 サンプル取得
- shrine_id / rank / thread_id 抽出確認
- score_v2 帯別 CVR 集計
- score_v2 と行動率の相関確認
```

---

## 結論

現時点では未実行。

まず Supabase SQL Editor で production snapshot 用 SQL を実行し、結果をこのドキュメントに貼る。

---

# Production Snapshot

## 1. recommendation_log実データ確認

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

### 結果

```markdown
- recommendation_log件数:
- recommendation_count平均:
- has_score_v2 true件数:
- has_score_v2 false件数:
- thread_idあり:
- user_idあり:
```

### 判断

```markdown
- [ ] recommendation_log に実データあり
- [ ] recommendations JSON が空ではない
- [ ] score_v2 が保存されている
```

---

## 2. score_v2存在率確認

### SQL

```sql
WITH logs AS (
  SELECT
    id,
    recommendations::jsonb AS recommendations
  FROM temples_concierge_recommendation_log
  WHERE recommendations IS NOT NULL
), expanded AS (
  SELECT
    l.id AS recommendation_log_id,
    rec.item
  FROM logs l
  CROSS JOIN LATERAL jsonb_array_elements(l.recommendations) AS rec(item)
)
SELECT
  COUNT(*) AS recommendation_count,
  COUNT(*) FILTER (WHERE item ? 'score_v2') AS score_v2_count,
  ROUND(
    COUNT(*) FILTER (WHERE item ? 'score_v2')::numeric / NULLIF(COUNT(*), 0),
    4
  ) AS score_v2_presence_rate
FROM expanded;
```

### 結果

```markdown
- recommendation_count:
- score_v2_count:
- score_v2_presence_rate:
```

### 判断

```markdown
- [ ] score_v2存在率が確認できた
- [ ] score_v2未保存データの有無を確認した
```

---

## 3. score_v2サンプル10件取得

### SQL

```sql
SELECT
  l.id AS recommendation_log_id,
  l.thread_id,
  l.user_id,
  l.created_at AS recommended_at,
  rec.ordinality AS rank,
  rec.item->>'id' AS raw_id,
  rec.item->>'shrine_id' AS raw_shrine_id,
  COALESCE(
    rec.item->>'display_name',
    rec.item->>'name',
    rec.item->>'title'
  ) AS shrine_name,
  rec.item->'score_v2' AS score_v2
FROM temples_concierge_recommendation_log l
CROSS JOIN LATERAL jsonb_array_elements(l.recommendations::jsonb) WITH ORDINALITY AS rec(item, ordinality)
WHERE l.recommendations IS NOT NULL
  AND rec.item ? 'score_v2'
ORDER BY l.created_at DESC, rec.ordinality ASC
LIMIT 10;
```

### 結果

```markdown
- score_v2.totalあり:
- score_v2.componentsあり:
- score_v2.signalsあり:
- raw_id確認:
- raw_shrine_id確認:
- rank確認:
```

---

## 4. shrine_id抽出確認

### SQL

```sql
WITH expanded AS (
  SELECT
    l.id AS recommendation_log_id,
    rec.ordinality AS rank,
    rec.item,
    rec.item->>'id' AS raw_id,
    rec.item->>'shrine_id' AS raw_shrine_id
  FROM temples_concierge_recommendation_log l
  CROSS JOIN LATERAL jsonb_array_elements(l.recommendations::jsonb) WITH ORDINALITY AS rec(item, ordinality)
  WHERE l.recommendations IS NOT NULL
)
SELECT
  COUNT(*) AS recommendation_count,
  COUNT(*) FILTER (WHERE raw_shrine_id IS NOT NULL AND raw_shrine_id <> '') AS has_shrine_id,
  COUNT(*) FILTER (WHERE raw_id IS NOT NULL AND raw_id <> '') AS has_id,
  COUNT(*) FILTER (
    WHERE (raw_shrine_id IS NULL OR raw_shrine_id = '')
      AND (raw_id IS NULL OR raw_id = '')
  ) AS missing_both
FROM expanded;
```

### 結果

```markdown
- recommendation_count:
- has_shrine_id:
- has_id:
- missing_both:
```

### 判断

```markdown
- [ ] shrine_id を抽出できる
- [ ] id を fallback として使える
- [ ] missing_both の扱いを決める
```

---

## 5. rank抽出確認

### SQL

```sql
SELECT
  l.id AS recommendation_log_id,
  rec.ordinality AS rank,
  rec.item->>'rank' AS raw_rank,
  COALESCE(
    rec.item->>'display_name',
    rec.item->>'name',
    rec.item->>'title'
  ) AS shrine_name
FROM temples_concierge_recommendation_log l
CROSS JOIN LATERAL jsonb_array_elements(l.recommendations::jsonb) WITH ORDINALITY AS rec(item, ordinality)
WHERE l.recommendations IS NOT NULL
ORDER BY l.created_at DESC, rec.ordinality ASC
LIMIT 20;
```

### 結果

```markdown
- WITH ORDINALITYでrank取得可能:
- recommendation内raw_rankあり:
- 初期監査で使うrank:
```

### 判断

初期監査では `WITH ORDINALITY` の `rank` を正本として扱う。

---

## 6. thread_id抽出確認

### SQL

```sql
SELECT
  COUNT(*) AS log_count,
  COUNT(*) FILTER (WHERE thread_id IS NOT NULL) AS thread_id_count,
  ROUND(
    COUNT(*) FILTER (WHERE thread_id IS NOT NULL)::numeric / NULLIF(COUNT(*), 0),
    4
  ) AS thread_id_rate
FROM temples_concierge_recommendation_log;
```

### 結果

```markdown
- log_count:
- thread_id_count:
- thread_id_rate:
```

### 判断

```markdown
- [ ] thread_idでdetail_view / route_openと接続できる見込みあり
- [ ] thread_id欠損時のfallback条件が必要
```

---

# CVR Measurement

## 7. score_v2抽出SQL実行

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

### 結果

```markdown
- score_v2抽出件数:
- score_v2_total最小:
- score_v2_total最大:
- shrine_id抽出成功:
- rank抽出成功:
```

---

## 8. save率集計

### 結果貼り付け欄

```markdown
| score_band | recommendation_count | save_count | save_rate |
|---|---:|---:|---:|
| 0-2 |  |  |  |
| 2-4 |  |  |  |
| 4-6 |  |  |  |
| 6-8 |  |  |  |
| 8+ |  |  |  |
```

---

## 9. detail_view率集計

### 結果貼り付け欄

```markdown
| score_band | recommendation_count | detail_view_count | detail_view_rate |
|---|---:|---:|---:|
| 0-2 |  |  |  |
| 2-4 |  |  |  |
| 4-6 |  |  |  |
| 6-8 |  |  |  |
| 8+ |  |  |  |
```

---

## 10. route_open率集計

### 結果貼り付け欄

```markdown
| score_band | recommendation_count | route_open_count | route_open_rate |
|---|---:|---:|---:|
| 0-2 |  |  |  |
| 2-4 |  |  |  |
| 4-6 |  |  |  |
| 6-8 |  |  |  |
| 8+ |  |  |  |
```

---

## 11. score_v2帯別CVR取得

### 結果貼り付け欄

```markdown
| score_band | recommendation_count | avg_score_v2_total | save_rate | detail_view_rate | route_open_rate |
|---|---:|---:|---:|---:|---:|
| 0-2 |  |  |  |  |  |
| 2-4 |  |  |  |  |  |
| 4-6 |  |  |  |  |  |
| 6-8 |  |  |  |  |  |
| 8+ |  |  |  |  |  |
```

---

# Analysis

## 12. score_v2帯ごとのsave率比較

```markdown
- 高score帯ほどsave_rateが上がっているか:
- 例外帯:
- 仮説:
```

## 13. score_v2帯ごとのdetail率比較

```markdown
- 高score帯ほどdetail_view_rateが上がっているか:
- 例外帯:
- 仮説:
```

## 14. score_v2帯ごとのroute率比較

```markdown
- 高score帯ほどroute_open_rateが上がっているか:
- 例外帯:
- 仮説:
```

## 15. behavior_contribution寄与分析

```markdown
- behavior_contributionが高い候補ほど行動率が高いか:
- behavior_contributionが過大に見えるケース:
- behavior_contributionが過小に見えるケース:
```

## 16. 重み変更要否判断

```markdown
- User State Match:
- Shrine Meaning Match:
- Context Match:
- Behavior Match:
- 現時点で重み変更するか:
- 理由:
```

---

## TODO

```markdown
# Production Snapshot

- [x] develop最新化
- [x] audit/score-v2-production-snapshot作成
- [ ] recommendation_log実データ確認
- [ ] score_v2存在率確認
- [ ] score_v2サンプル10件取得
- [ ] shrine_id抽出確認
- [ ] rank抽出確認
- [ ] thread_id抽出確認

# CVR Measurement

- [ ] score_v2抽出SQL実行
- [ ] save率集計
- [ ] detail_view率集計
- [ ] route_open率集計
- [ ] score_v2帯別CVR取得

# Analysis

- [ ] score_v2帯ごとのsave率比較
- [ ] score_v2帯ごとのdetail率比較
- [ ] score_v2帯ごとのroute率比較
- [ ] behavior_contribution寄与分析
- [ ] 重み変更要否判断
```
