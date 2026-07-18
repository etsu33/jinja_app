> **Status: Archive**
>
> 本ドキュメントは、Recommendation Score v2の重み調整前における行動ファネルの実装状況を確認した時点監査である。
>
> 現行の集計実装は`backend/temples/services/behavior_funnel.py`等の実装コードを最終的な正本とする。

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

## Recommendation Funnel Definition

### recommendation_view の正本

暫定正本: PostHog `concierge_result_impression`

理由:

- 現時点で backend `behavior_funnel.py` には `recommendation_view_count` がない
- frontend の `ConciergeSectionsRenderer.tsx` から `concierge_result_impression` が送信されている
- 推薦表示はユーザー行動ではなく表示イベントなので、まずはPostHog観測で十分

将来:

- DB正本化する場合は `ConciergeRecommendationLog` を `recommendation_view_count` として扱うか検討する

### recommendation_click の正本

暫定正本: PostHog `shrine_detail_transition`

理由:

- ユーザーが推薦結果から詳細に進んだ行動を表す
- backend の `ConciergeRecommendationClickLog` は存在するが、現行ファネルでは未反映
- 初期分析では `concierge_result_impression → shrine_detail_transition` を見る

将来:

- DB正本化する場合は `ConciergeRecommendationClickLog` と `ShrineInteractionLog.detail_view` の関係を整理する

### recommendation_to_detail_cvr

```text
recommendation_to_detail_cvr =
  shrine_detail_transition / concierge_result_impression
```

暫定正本: PostHog

理由:

- 推薦表示から詳細遷移までの入口ファネルは、現時点ではDB正本が弱い
- `concierge_result_impression` と `shrine_detail_transition` はPostHog上で同一文脈として観測しやすい
- Recommendation Score v2 の重み変更前に、まず入口CVRとして確認する

### detail_to_route_cvr

```text
detail_to_route_cvr =
  route_open_count / detail_view_count
```

正本: backend DB

理由:

- `detail_view_count` と `route_open_count` は `behavior_funnel.py` で集計済み
- 詳細閲覧から経路表示への遷移は、神社提案が行動意図につながったかを見る指標として扱える

### route_to_save_cvr

```text
route_to_save_cvr =
  save_count / route_open_count
```

正本: backend DB

理由:

- `route_open_count` と `save_count` は `behavior_funnel.py` で集計済み
- 経路表示後に保存する流れは、参拝検討の継続意図として扱える
- ただし保存は route_open より前に発生する場合もあるため、初期分析では補助指標として扱う

## Recommendation Score v2への反映方針

- `recommendation_view` は重みに使わない
- `recommendation_click` は当面重みに使わない
- `shrine_card_click` は当面重みに使わない
- Recommendation Score v2 は実行シグナル優先を維持する
- 重み調整は `detail_view` / `route_open` / `save` / `visit_done` / `reflection_saved` を中心に行う

理由:

- `recommendation_view` は表示イベントであり、ユーザーの意思決定とは限らない
- `recommendation_click` / `shrine_card_click` は興味シグナルだが、実行意図としては弱い
- 神社_APP の価値は、クリックよりも「実際に向かう・保存する・振り返る」行動にある
- 初期の重み調整では、実行シグナルを優先した方がRecommendation Score v2の目的と一致する

## 次PR候補

```markdown
- [ ] behavior_funnel.py に detail_to_route_cvr を追加
- [ ] behavior_funnel.py に route_to_save_cvr を追加
- [ ] recommendation_view_count の正本をDB / PostHogどちらに置くか決める
- [ ] recommendation_to_detail_cvr の定義を決める
- [ ] PostHogで concierge_result_impression → shrine_detail_transition を確認する
```

## 次フェーズTODO

### Recommendation Funnel

```markdown
- [x] recommendation_view の正本を決める
- [x] recommendation_click の正本を決める
- [x] recommendation_to_detail_cvr の定義を決める
- [x] detail_to_route_cvr の定義を決める
- [x] route_to_save_cvr の定義を決める
```

### PostHog監査

```markdown
- [ ] concierge_result_impression 件数確認
- [ ] shrine_detail_transition 件数確認
- [ ] route_open 件数確認
- [ ] visit_done 件数確認
- [ ] reflection_saved 件数確認
```

### Recommendation Score v2

```markdown
- [x] recommendation_view を重みに使うか判断
- [x] recommendation_click を重みに使うか判断
- [x] shrine_card_click を重みに使うか判断
- [x] 実行シグナル優先方針を維持するか確認
```
