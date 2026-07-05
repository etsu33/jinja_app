

# Behavior Funnel Current State Audit

## 目的

Phase5 Behavior Measurement Plan に基づき、現時点で行動ファネルに必要なログがどこまで取得できているかを監査する。

本監査では、特に Web / Mobile の差分を確認し、次の実装PRで何を補うべきかを明確にする。

## 前提

以下は完了済み。

- Phase4 Concierge First UI完了
- Phase5 Behavior Measurement Plan作成
- `recommendation_reason_v4` 表示
- `reason_facts` 表示
- `action_suggestion_v4_preview` 表示
- Web / Mobile Detailで `detail_view` / `route_open` の基礎計測確認

## Backendの現在地

Backendには、行動ファネルに必要な主要モデル・API・集計サービスが存在する。

### 主なモデル

- `ShrineInteractionLog`
  - `detail_view`
  - `route_open`
- `Favorite`
- `Visit`
- `ShrineReflection`
- `ActionEvent`
  - `action_started`
  - `action_completed`
- `ConciergeRecommendationLog`
- `ConciergeRecommendationClickLog`

### 主なAPI / Service候補

- `/api/shrine-interactions/`
- `/api/action-events/`
- `/api/favorites/`
- `/api/visits/`
- `/api/shrines/{id}/reflection/`
- `get_behavior_funnel_metrics`
- `score_v3_dashboard_api`
- `behavior_funnel_debug_api`

## Webの現在地

Web側は、Behavior Funnelの正本ログに比較的乗っている。

### detail_view

状態:

```text
送信あり
```

確認箇所:

- `apps/web/src/components/shrine/ShrineDetailViewTracker.tsx`
- `apps/web/src/lib/api/shrineInteractions.ts`
- `/api/shrine-interactions/`

判断:

Web Detail閲覧は `ShrineInteractionLog.detail_view` に送られる。

### route_open

状態:

```text
送信あり
```

確認箇所:

- `apps/web/src/components/shrine/GoogleMapRouteLink.tsx`
- `apps/web/src/lib/api/shrineInteractions.ts`
- `/api/shrine-interactions/`

判断:

Web 経路表示は `ShrineInteractionLog.route_open` に送られる。

### favorite / save

状態:

```text
送信あり
```

確認箇所:

- `apps/web/src/lib/api/favorites.ts`
- `apps/web/src/app/api/favorites/route.ts`
- `apps/web/src/hooks/useFavorite.ts`
- `apps/web/src/components/PlaceCardClientActions.tsx`

判断:

Web保存はbackend `Favorite` に送られる。

### visit_done

状態:

```text
送信あり候補あり
```

確認箇所:

- `apps/web/src/lib/api/visits.ts`
- `apps/web/src/app/api/visits/route.ts`
- `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx`

判断:

Web参拝記録はbackend `Visit` に送られている可能性が高い。
ただし、UI上の発火条件は別途確認対象。

### reflection_saved

状態:

```text
送信あり
```

確認箇所:

- `apps/web/src/lib/api/reflections.ts`
- `apps/web/src/app/api/shrines/[id]/reflection/route.ts`
- `apps/web/src/components/shrine/detail/ShrineReflectionPrompt.tsx`

判断:

Web振り返り保存はbackend `ShrineReflection` に送られる。

### action_started / action_completed

状態:

```text
送信あり
```

確認箇所:

- `apps/web/src/features/concierge/components/ConciergeTopRecommendationHero.tsx`
- `apps/web/src/lib/api/actionEvents.ts`
- `apps/web/src/lib/analytics/actionEvents.ts`

判断:

Webの行動提案イベントはbackend `ActionEvent` とanalyticsに送られる。

## Mobileの現在地

Mobile側は、`detail_view` / `route_open` はbackendに送られているが、保存・参拝・振り返り・行動提案イベントはlocal中心または未確認である。

### detail_view

状態:

```text
送信あり
```

確認箇所:

- `apps/mobile/app/shrines/[id].tsx`
- `apps/mobile/lib/shrineInteractions.ts`

判断:

Mobile Detail閲覧は `trackShrineDetailView` 経由でbackend `ShrineInteractionLog.detail_view` に送られる。

### route_open

状態:

```text
送信あり
```

確認箇所:

- `apps/mobile/app/shrines/[id].tsx`
- `apps/mobile/lib/shrineInteractions.ts`

判断:

Mobile 経路表示は `trackShrineRouteOpen` 経由でbackend `ShrineInteractionLog.route_open` に送られる。

### Mobile favorite

状態:

```text
AsyncStorageのみ
backend Favoriteには送っていない可能性が高い
```

確認箇所:

- `apps/mobile/lib/storage.ts`
- `apps/mobile/app/shrines/[id].tsx`
- `apps/mobile/app/favorites/index.tsx`
- `apps/mobile/app/ranking/index.tsx`

現状:

```ts
export async function toggleFavorite(id: string) {
  const favs = await getFavorites();
  const next = favs.includes(id) ? favs.filter(x => x !== id) : [id, ...favs];
  await setJSON(keys.favorites, next);
  return next.includes(id);
}
```

判断:

Mobileのお気に入りは `AsyncStorage` の `sanpai:favs` に保存されている。
backend `/api/favorites/` へ送っている実装は確認できていない。

影響:

- Mobileの保存行動はbackend `Favorite` の `save_count` に反映されない可能性が高い
- Behavior Funnel上、Mobileのsave_rateが過小評価される可能性がある

### Mobile visit

状態:

```text
AsyncStorageの `sanpai:visits` を加算
backend Visitには送っていない可能性が高い
```

確認箇所:

- `apps/mobile/lib/storage.ts`
- `apps/mobile/app/shrines/[id].tsx`
- `apps/mobile/app/visit-history/index.tsx`

現状:

```ts
export async function incVisits(delta = 1) {
  const current = await getJSON<number>(keys.visits, 0);
  const next = current + delta;
  await setJSON(keys.visits, next);
  return next;
}
```

判断:

Mobileの参拝回数は `AsyncStorage` の `sanpai:visits` に保存されている。
backend `/api/visits/` へ送っている実装は確認できていない。

影響:

- Mobileの参拝完了はbackend `Visit` の `visit_done_count` に反映されない可能性が高い
- Visit Done RateがMobile分だけ過小評価される可能性がある

### Mobile reflection

状態:

```text
records画面には導線あり
backend ShrineReflection送信は未確認
```

確認箇所:

- `apps/mobile/app/records/index.tsx`
- `apps/mobile/app/shrines/[id].tsx`
- `apps/mobile/app/visit-history/index.tsx`

現状:

- `/records` 画面は存在する
- Detailから `/records` への導線は存在する
- backend `/api/shrines/{id}/reflection/` への送信実装は確認できていない

判断:

Mobileには振り返り導線はあるが、backend `ShrineReflection` への保存は未確認。

影響:

- Mobileの振り返り行動は `reflection_saved_count` に反映されない可能性が高い
- `action_suggestion_v4_preview` が振り返りに効いているかを測りにくい

### Mobile action event

状態:

```text
Action suggestion表示はある
backend ActionEvent送信は未確認
```

確認箇所:

- `apps/mobile/app/concierge/index.tsx`
- `apps/mobile/app/shrines/[id].tsx`

現状:

- Mobile Conciergeで `action_suggestion_v4_preview` を表示している
- Mobile Detailへ `actionSuggestionV4Preview` を引き継いでいる
- backend `/api/action-events/` へ `action_started` / `action_completed` を送っている実装は確認できていない

判断:

Mobileでは行動提案の表示はあるが、表示後の開始・完了イベントはbackendに送られていない可能性が高い。

影響:

- MobileのAction Suggestion効果を測れない
- `action_suggestion_v4_preview` と `reflection_saved_rate` の相関を見づらい

## Behavior Funnel現状まとめ

| 行動 | Backend正本 | Web | Mobile | 判断 |
|---|---|---|---|---|
| detail_view | `ShrineInteractionLog` | 送信あり | 送信あり | OK |
| route_open | `ShrineInteractionLog` | 送信あり | 送信あり | OK |
| save | `Favorite` | 送信あり | local中心 | Mobile欠落候補 |
| visit_done | `Visit` | 送信あり候補 | local中心 | Mobile欠落候補 |
| reflection_saved | `ShrineReflection` | 送信あり | 未確認 | Mobile欠落候補 |
| action_started | `ActionEvent` | 送信あり | 未確認 | Mobile欠落候補 |
| action_completed | `ActionEvent` | 送信あり | 未確認 | Mobile欠落候補 |
| recommendation_log | `ConciergeRecommendationLog` | backend側で記録候補 | backend側で記録候補 | 要確認 |
| recommendation_click | `ConciergeRecommendationClickLog` | 実装候補あり | 未確認 | 要確認 |

## 現時点の判断

Behavior Funnelの基礎KPIは、Webではかなり計測可能。

Mobileは以下の基礎行動のみbackend正本ログに乗っている。

```text
detail_view
route_open
```

一方で、以下はbackend正本ログに乗っていない可能性が高い。

```text
favorite / save
visit_done
reflection_saved
action_started
action_completed
```

したがって、現状のファネル分析では **Mobileの後段行動が過小評価されるリスク** がある。

## 優先課題

### Priority A: Mobile saveをbackend Favoriteに接続

目的:

Mobileの保存行動をbackend `Favorite` に反映する。

理由:

- save_rateが重要KPI
- 収益化前の再訪候補把握に効く
- localだけだとユーザー端末をまたいだ保存ができない

候補ブランチ:

`feature/mobile-favorite-api-sync`

### Priority B: Mobile visit_doneをbackend Visitに接続

目的:

Mobileの参拝記録をbackend `Visit` に反映する。

理由:

- visit_done_rateが参拝行動の主要KPI
- Score v3 / v4のbehavior signalに使える

候補ブランチ:

`feature/mobile-visit-api-sync`

### Priority C: Mobile action eventをbackend ActionEventに接続

目的:

Mobileの行動提案開始・完了をbackend `ActionEvent` に反映する。

理由:

- `action_suggestion_v4_preview` の効果検証に必要
- reflectionとの相関を見たい

候補ブランチ:

`feature/mobile-action-event-tracking`

### Priority D: Mobile reflection_savedをbackend ShrineReflectionに接続

目的:

Mobileの振り返り保存をbackend `ShrineReflection` に反映する。

理由:

- reflection_saved_rateが測れる
- 参拝後体験の改善に必要

候補ブランチ:

`feature/mobile-reflection-api-sync`

## 今回のPRでやること

- Behavior Funnelの現状を文書化する
- Backend / Web / Mobileのログ取得状況を整理する
- Mobileの欠落候補を明確にする
- 次に実装すべきPR候補を整理する

## 今回のPRでやらないこと

- Mobile API接続は実装しない
- backend APIは変更しない
- UIは変更しない
- Dashboardは変更しない
- Score v3 / v4 active化はしない

## 次PR候補

### 1. Mobile Favorite API Sync

ブランチ候補:

`feature/mobile-favorite-api-sync`

対象:

- `apps/mobile/lib/storage.ts`
- `apps/mobile/app/shrines/[id].tsx`
- 必要に応じてAPI client

目的:

- Mobileのfavoriteをbackend `Favorite` に送る
- local fallbackは残す

### 2. Mobile Visit API Sync

ブランチ候補:

`feature/mobile-visit-api-sync`

対象:

- `apps/mobile/lib/storage.ts`
- `apps/mobile/app/shrines/[id].tsx`
- 必要に応じてAPI client

目的:

- Mobileのvisit_doneをbackend `Visit` に送る
- local fallbackは残す

### 3. Mobile Action Event Tracking

ブランチ候補:

`feature/mobile-action-event-tracking`

対象:

- `apps/mobile/app/concierge/index.tsx`
- `apps/mobile/app/shrines/[id].tsx`
- `apps/mobile/lib` 配下のAPI client

目的:

- Mobileの `action_started` / `action_completed` をbackend `ActionEvent` に送る

### 4. Mobile Reflection API Sync

ブランチ候補:

`feature/mobile-reflection-api-sync`

対象:

- Mobile records / reflection入力導線
- backend `ShrineReflection` API client

目的:

- Mobileの振り返り保存をbackend `ShrineReflection` に送る

## 推奨判断

次は **Mobile Favorite API Sync** から進めるのが安全。

理由:

- save_rateは重要KPI
- UI変更が少ない
- local fallbackを残しやすい
- backend `/api/favorites/` は既に存在する
- Web実装も既にあるため参照しやすい

ただし、最終判断は母艦に差し戻す。

## TODO

```markdown
# Behavior Funnel Current State Audit

- [x] develop最新版化
- [x] audit/behavior-funnel-current-state 作成
- [x] Backendログ基盤確認
- [x] Web detail_view / route_open確認
- [x] Web favorite / visit / reflection確認
- [x] Web action event確認
- [x] Mobile detail_view / route_open確認
- [x] Mobile favorite確認
- [x] Mobile visit確認
- [x] Mobile reflection確認
- [x] Mobile action event確認
- [x] 欠落ログ候補整理
- [x] 次PR候補整理
- [ ] docs/audit/behavior-funnel-current-state.md をコミット
- [ ] PR作成
```

## 完了条件

- Backend / Web / Mobile の行動ログ取得状況が整理されている
- Mobileの欠落ログ候補が明確になっている
- Behavior Funnel分析前に補うべきPR候補が明確になっている
