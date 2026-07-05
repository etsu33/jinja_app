

# Mobile Action Suggestion Event Audit

## 目的

Mobileで `action_suggestion_v4_preview` が表示されているだけなのか、行動イベントとして計測できているのかを監査する。

本監査では、以下を明確にする。

- Mobile Conciergeで行動提案が表示されているか
- Mobile Shrine Detailへ行動提案が引き継がれているか
- Backendに `ActionEvent` の正本ログ基盤があるか
- Mobileから `/api/action-events/` に送信しているか
- 次PRで何を実装すべきか

## 前提

以下は完了済み。

- Phase4 Concierge First UI完了
- Phase5 Behavior Measurement Plan作成
- Behavior Funnel Current State Audit完了
- `action_suggestion_v4_preview` Contract固定
- Webで `action_started` / `action_completed` 送信あり
- Mobile Conciergeで `action_suggestion_v4_preview` 表示あり
- Mobile Detailへ `actionSuggestionV4Preview` 引き継ぎあり

## Backendの現在地

BackendにはAction Suggestion計測に必要な基盤が存在する。

### Model

対象:

- `backend/temples/models.py`

状態:

```text
ActionEvent modelあり
```

対応action:

```text
action_started
action_completed
```

### API

対象:

- `backend/temples/api/views/action_event.py`
- `backend/temples/api/serializers/action_event.py`
- `backend/temples/api/urls.py`

状態:

```text
/api/action-events/ あり
```

### Test

対象:

- `backend/temples/tests/api/test_action_event_api.py`
- `backend/temples/tests/services/test_action_completion_observation.py`
- `backend/temples/tests/services/test_concierge_history_action_state.py`

確認できること:

- `action_started` を保存できる
- `action_completed` を保存できる
- action completion observationで集計できる
- behavior signalへ `action_completed_signal` を反映できる

判断:

Backend側はAction Suggestion計測の正本として使える。

## Webの現在地

Webでは、Action Suggestionイベント送信が存在する。

### 対象

- `apps/web/src/features/concierge/components/ConciergeTopRecommendationHero.tsx`
- `apps/web/src/lib/api/actionEvents.ts`
- `apps/web/src/lib/analytics/actionEvents.ts`

状態:

```text
action_started / action_completed 送信あり
```

判断:

WebはAction Suggestionの表示だけでなく、開始・完了イベントも計測できる。

## Mobileの現在地

Mobileでは `action_suggestion_v4_preview` の表示とDetail引き継ぎはできているが、ActionEvent送信は確認できていない。

## Mobile Concierge

対象:

- `apps/mobile/app/concierge/index.tsx`

確認結果:

```text
action_suggestion_v4_preview normalizeあり
推薦カード内に表示あり
DetailへactionSuggestionV4Preview引き継ぎあり
action event送信なし
```

確認箇所:

```ts
const actionSuggestionV4Preview = normalizeActionSuggestionV4Preview(
  item.action_suggestion_v4_preview ?? item.actionSuggestionV4Preview,
);
```

表示箇所:

```text
primaryAction.label
primaryAction.description
secondaryAction.label
secondaryAction.description
reflectionPrompt.question
```

Detail引き継ぎ:

```ts
actionSuggestionV4Preview: card.actionSuggestionV4Preview ? JSON.stringify(card.actionSuggestionV4Preview) : "",
```

判断:

Mobile Conciergeは、行動提案を表示できている。
ただし、表示・タップ・開始・完了イベントはbackendへ送っていない。

## Mobile Shrine Detail

対象:

- `apps/mobile/app/shrines/[id].tsx`

確認結果:

```text
actionSuggestionV4Preview受け取りあり
primary / secondary / reflection表示あり
action event送信なし
```

確認箇所:

```ts
const actionSuggestionV4Preview = contextActionSuggestionV4Preview ?? shrine?.actionSuggestionV4Preview ?? null;
const primaryAction = actionSuggestionV4Preview?.primaryAction ?? actionSuggestionV4Preview?.primary_action ?? null;
const secondaryAction = actionSuggestionV4Preview?.secondaryAction ?? actionSuggestionV4Preview?.secondary_action ?? null;
const reflectionPrompt = actionSuggestionV4Preview?.reflectionPrompt ?? actionSuggestionV4Preview?.reflection_prompt ?? null;
```

判断:

Mobile Detailは、Conciergeから引き継いだ行動提案を表示できている。
ただし、ActionEventとしては未計測。

## 現状まとめ

| 項目 | Backend | Web | Mobile |
|---|---|---|---|
| `action_suggestion_v4_preview`生成 | あり | 受け取り・表示 | 受け取り・表示 |
| Conciergeカード表示 | - | あり | あり |
| Detail表示 | - | あり | あり |
| `action_started`送信 | APIあり | あり | なし |
| `action_completed`送信 | APIあり | あり | なし |
| observation集計 | あり | 利用可能 | Mobile分は欠落 |

## 欠落しているもの

Mobileで欠落している可能性が高いもの:

```text
action_started送信
action_completed送信
suggestion_idの設計
source metadataの設計
thread_id / shrine_id / action_type の紐づけ
```

## 計測したいイベント

### 1. action_started

目的:

ユーザーが行動提案に反応したかを測る。

発火候補:

- primary actionを押した時
- secondary actionを押した時
- Detailの行動提案CTAを押した時

### 2. action_completed

目的:

ユーザーが行動を完了したかを測る。

発火候補:

- 「できた」ボタン
- 「記録へ進む」ボタン
- reflection保存後

## metadata候補

```json
{
  "source": "mobile_concierge" | "mobile_shrine_detail",
  "surface": "recommendation_card" | "shrine_detail",
  "action_slot": "primary" | "secondary" | "reflection",
  "action_type": "detail_open" | "route_open" | "save" | "visit" | "reflect" | "pause",
  "recommendation_source": "concierge",
  "has_reflection_prompt": true
}
```

## 実装する場合の最小方針

### 1. Mobile API clientを追加

候補ファイル:

- `apps/mobile/lib/actionEvents.ts`

役割:

- `/action-events/` へPOSTする
- 失敗してもUIを止めない
- backendログが失敗しても体験は継続する

### 2. Conciergeカード側でstarted送信

対象:

- `apps/mobile/app/concierge/index.tsx`

方針:

- primary / secondary actionを押せるUIにする場合のみ送信
- 現在Text表示だけなら、まず実装しない
- UI変更が必要なら別PRに分ける

### 3. Detail側でstarted / completed送信

対象:

- `apps/mobile/app/shrines/[id].tsx`

方針:

- 「参拝前にできること」カードにCTAを追加する場合に送信
- `action_started` はCTA押下時
- `action_completed` は完了ボタン押下時 or 記録保存時

## 推奨判断

Mobile Action Suggestion Eventは、すぐに実装してよいが、UI変更を伴うためPRを分けるべき。

優先順位:

```text
1. Mobile action event API client追加
2. Detail側のaction_started送信
3. Detail側のaction_completed送信
4. Conciergeカード側の送信は後回し
```

理由:

- Detail側はユーザーが行動に移る直前なので計測価値が高い
- Conciergeカードは現在表示中心で、押下UIが弱い
- まずはDetailの「参拝前にできること」から測るのが自然

## 今回のPRでやること

- Mobile Action Suggestion Eventの現状を文書化する
- Backend / Web / Mobileの差分を整理する
- Mobileで欠落しているActionEvent送信を明確にする
- 次PRの実装方針を整理する

## 今回のPRでやらないこと

- Mobile API clientは追加しない
- UIは変更しない
- ActionEvent送信は実装しない
- Backend APIは変更しない
- Dashboardは変更しない

## 次PR候補

### 1. Mobile Action Event API Client

ブランチ候補:

`feature/mobile-action-event-api-client`

目的:

- Mobileからbackend `/api/action-events/` へ送信できるclientを追加する
- UIにはまだつながない

対象候補:

- `apps/mobile/lib/actionEvents.ts`

### 2. Mobile Detail Action Event Tracking

ブランチ候補:

`feature/mobile-detail-action-event-tracking`

目的:

- Mobile Detailの行動提案から `action_started` / `action_completed` を送る

対象候補:

- `apps/mobile/app/shrines/[id].tsx`
- `apps/mobile/lib/actionEvents.ts`

### 3. Mobile Concierge Action Event Tracking

ブランチ候補:

`feature/mobile-concierge-action-event-tracking`

目的:

- Mobile Conciergeカード上の行動提案クリックを計測する

対象候補:

- `apps/mobile/app/concierge/index.tsx`
- `apps/mobile/lib/actionEvents.ts`

## 推奨される次PR

次は **Mobile Action Event API Client** が安全。

理由:

- UI変更なしで進められる
- backend APIが既に存在する
- 後続のDetail / Concierge tracking実装の土台になる
- 小さいPRとして切りやすい

ただし、最終判断は母艦に差し戻す。

## TODO

```markdown
# Mobile Action Suggestion Event Audit

- [x] develop最新版化
- [x] audit/mobile-action-suggestion-event 作成
- [x] Backend ActionEvent確認
- [x] Web action_started / action_completed確認
- [x] Mobile Concierge action_suggestion_v4_preview確認
- [x] Mobile Detail actionSuggestionV4Preview確認
- [x] Mobile ActionEvent送信なしを確認
- [x] 欠落イベント整理
- [x] 次PR候補整理
- [ ] docs/audit/mobile-action-suggestion-event.md をコミット
- [ ] PR作成
```

## 完了条件

- Mobile Action Suggestionの表示と計測の差分が文書化されている
- Backend / Web / Mobile のActionEvent状態が整理されている
- Mobileで次に補うべきPR単位が明確になっている
