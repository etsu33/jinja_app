

# Recommendation Funnel Analysis

## 目的

Recommendation Score v2 の重み調整に入る前に、現在取得できている行動ファネルと不足している集計を整理する。

この監査ではコード変更は行わず、既存実装・計測イベント・不足指標を明文化する。

## 現在実装済みのBackend集計

実装箇所:

```text
backend/temples/services/behavior_funnel.py
```

現在取得できる指標:

```markdown
- detail_view_count
- route_open_count
- save_count
- visit_count
- reflection_count
- save_to_visit_cvr
- visit_to_reflection_cvr
```

## 現在のBehavior Signal

実装箇所:

```text
backend/temples/services/concierge_history.py
```

現在の信号:

```markdown
- detail_view_signal = count * 0.2 * recency
- route_open_signal = count * 0.6 * recency
- save_signal = 1.5 * recency
- visit_signal = 3.0 * recency
- reflection_signal = 4.0 * recency
- action_completed_signal = 2.0 * recency
```

上限:

```text
total = min(sum(signals), 10.0)
```

## ShrineInteractionLog

実装箇所:

```text
backend/temples/models.py
```

現在の action_type:

```markdown
- detail_view
- route_open
- shrine_card_click
```

## Frontend / PostHogイベント

主な送信元:

```text
apps/web/src/components/shrine/ShrineDetailViewTracker.tsx
apps/web/src/components/shrine/GoogleMapRouteLink.tsx
apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx
apps/web/src/components/shrine/detail/ShrineReflectionPrompt.tsx
apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx
```

現在観測できる主なイベント:

```markdown
- shrine_detail_view
- route_open
- visit_done
- reflection_saved
- concierge_result_impression
- shrine_detail_transition
- save_prompt_view
- save_prompt_click
```

## 不足している集計

現在の `behavior_funnel.py` には以下が不足している。

```markdown
- recommendation_view_count
- recommendation_to_detail_cvr
- detail_to_route_cvr
- route_to_save_cvr
```

## 判断

現時点では、詳細閲覧以降の行動ファネルは backend DB で集計できる。

一方で、推薦表示から詳細遷移までの入口ファネルは、DB正本としては弱い。

そのため、Recommendation Score v2 の重み変更前に以下を判断する。

```markdown
- recommendation_view をDB正本にするか
- concierge_result_impression をPostHog観測に留めるか
- shrine_detail_transition を recommendation→detail のCVR計測に使うか
- route_to_save_cvr を backend 集計へ追加するか
```

## 次PR候補

```markdown
- [ ] behavior_funnel.py に detail_to_route_cvr を追加
- [ ] behavior_funnel.py に route_to_save_cvr を追加
- [ ] recommendation_view_count の正本をDB / PostHogどちらに置くか決める
- [ ] recommendation_to_detail_cvr の定義を決める
- [ ] PostHogで concierge_result_impression → shrine_detail_transition を確認する
```

