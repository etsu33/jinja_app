

# historyTheme × Premium Dashboard

## 目的

historyTheme ごとに、保存・Premium導線・課金完了までの流れを確認する。

このドキュメントでは、PostHog上で確認する指標とイベントの見方を定義する。
コード上では、`historyTheme` が analytics payload に含まれ、PostHog に送信される構造になっている。

## 前提

対象イベントは以下。

| イベント | 意味 | 主な確認軸 |
| --- | --- | --- |
| `save_prompt_click` | 相談結果をあとで見返すための保存クリック | `historyTheme`, `source`, `threadId`, `resultSetId` |
| `premium_preview_click` | Premium導線クリック | `historyTheme`, `source`, `cardId`, `threadId`, `resultSetId` |
| `checkout_started` | 決済開始 | `historyTheme`, `source`, `cardId`, `funnelStep` |
| `checkout_success` | 決済成功 | `historyTheme`, `source`, `cardId`, `funnelStep` |
| `premium_active` | Premium有効化確認 | `historyTheme`, `source`, `cardId`, `funnelStep` |

## Dashboard 1: historyTheme別 Premium転換

### ゴール

どの historyTheme が Premium転換に強いかを確認する。

### PostHogで見る指標

- `premium_preview_click` count by `historyTheme`
- `checkout_started` count by `historyTheme`
- `checkout_success` count by `historyTheme`
- `premium_active` count by `historyTheme`

### 見たいCVR

```text
premium_preview_click → checkout_started
checkout_started → checkout_success
checkout_success → premium_active
premium_preview_click → premium_active
```

### 判断基準

- `premium_preview_click` が多く `checkout_started` が少ない
  - Premium訴求は押されているが、決済開始前で落ちている
- `checkout_started` が多く `checkout_success` が少ない
  - 決済画面または価格で落ちている可能性
- `premium_active` が特定 historyTheme に偏る
  - そのテーマは有料価値と接続しやすい可能性

## Dashboard 2: save → premium 相関

### ゴール

保存行動がPremium転換に結びついているかを確認する。

### PostHogで見る指標

- `save_prompt_click` count by `historyTheme`
- `premium_preview_click` count by `historyTheme`
- `premium_active` count by `historyTheme`

### 見たいCVR

```text
save_prompt_click → premium_preview_click
save_prompt_click → premium_active
```

### 確認軸

- `historyTheme`
- `source`
- `threadId`
- `resultSetId`

### 判断基準

- 保存は多いがPremiumに進まない
  - 保存価値はあるが有料価値の説明が弱い
- 保存は少ないがPremiumに進む
  - 保存より深掘り訴求が強い
- 保存もPremiumも低い
  - historyTheme自体の訴求、またはカード文言の再設計対象

## Dashboard 3: premium card別CTR

### ゴール

どのカードがPremiumクリックを生んでいるかを確認する。

### PostHogで見る指標

- `card_view` count by `cardId`, `historyTheme`
- `card_partial_view` count by `cardId`, `historyTheme`
- `card_teaser_view` count by `cardId`, `historyTheme`
- `premium_preview_click` count by `cardId`, `historyTheme`

### 見たいCTR

```text
premium_preview_click / card_view
premium_preview_click / card_partial_view
premium_preview_click / card_teaser_view
```

### 確認軸

- `cardId`
- `historyTheme`
- `source`
- `accessLevel`
- `visibility`

### 判断基準

- viewは多いがclickが少ない
  - カード文言またはCTAが弱い
- click率が高いカードがある
  - Premium訴求の勝ちパターン候補
- historyThemeごとに強いカードが違う
  - テーマ別にPremium訴求文言を変える余地がある

## Dashboard 4: 行動相関

### ゴール

Premium転換だけでなく、実際の行動につながっているかを確認する。

### 対象イベント

現時点で確認対象にしたいイベント。

```text
route_open
visit_done
```

### 見たい相関

```text
historyTheme → route_open
historyTheme → visit_done
premium_active → route_open
premium_active → visit_done
save_prompt_click → route_open
```

### 判断基準

- Premium転換は高いが route_open が低い
  - 内省価値はあるが行動接続が弱い
- route_open は高いが Premium転換が低い
  - 行動価値はあるが有料化ポイントが弱い
- visit_done が取れていない
  - 記録導線またはイベント設計の追加検討

## historyThemeランキング

### 集計候補

| ランク種別 | 計算式 |
| --- | --- |
| 保存率ランキング | `save_prompt_click / card_view` |
| Premium興味ランキング | `premium_preview_click / card_view` |
| 決済開始ランキング | `checkout_started / premium_preview_click` |
| Premium有効化ランキング | `premium_active / premium_preview_click` |
| 行動接続ランキング | `route_open / premium_preview_click` |

## 注意点

- `historyTheme` が `null` のイベントは、未分類として分けて見る
- `source` が違うイベントを混ぜすぎない
- `threadId` / `resultSetId` は相関確認用であり、個人特定目的では使わない
- イベント数が少ない段階ではCVRを断定しない
- まずは傾向を見る。改善判断は最低でも一定数のイベント蓄積後に行う

## 次の改善候補

- PostHog dashboard URLをこのドキュメントに追記する
- historyTheme別の勝ちカードを記録する
- `route_open` / `visit_done` の送信状況を確認する
- 保存後にPremiumへ進んだユーザーの行動パターンを確認する
