> **Status: Reference**
>
> 本ドキュメントは、consultationAxis別の保存・参拝・課金導線の行動差分を確認するための集計方針を記録した参照資料である。
>
> 本書のPostHog集計は策定時点で未実施(次フェーズTODOとして未着手)であり、実施状況はPostHog側の実際の設定を最終的な正本とする。

# Consultation Axis Analytics Summary

## 目的

`consultationAxis` ごとに、保存・参拝導線・課金導線の行動差分を確認する。

このドキュメントでは、`consultationAxis` を recommendation score に反映する前に、実測でどの相談軸が保存・ルート閲覧・課金に結びつきやすいかを確認するための集計仕様を定義する。

---

## 対象axis

- `money_growth`
- `career_change`
- `independence`
- `rest_healing`
- `restart_mindset`
- `nature_reset`
- `study_success`
- `other`

---

## 保存先

`consultationAxis` は frontend analytics payload として送信され、PostHog event property として保存される。

現時点ではDB migrationは追加しない。

---

## consultationAxis付きevent

- `consultation_completed`
- `concierge_result_impression`
- `shrine_detail_transition`
- `card_view`
- `card_teaser_view`
- `premium_preview_click`
- `save_prompt_view`
- `save_prompt_click`
- `card_cta_click`
- `shrine_decision`

---

## axis別 save_rate

### ゴール

相談軸ごとに「あとで見返す」意図がどれくらい発生しているかを見る。

### 分母

`consultation_completed` のうち `consultationAxis` が存在するevent数。

### 分子

`save_prompt_click` のうち同一 `consultationAxis` を持つevent数。

### 指標

```text
axis_save_rate = save_prompt_click / consultation_completed
```

### 注意

現時点では「実際にDBへ保存完了したか」ではなく、「保存CTAを押したか」を見る。

保存完了eventが追加された場合は、分子を保存完了eventへ切り替える。

---

## axis別 route_open率

### ゴール

相談軸ごとに「実際に行ってみる」導線へ進んだ割合を見る。

### 分母

`consultation_completed` のうち `consultationAxis` が存在するevent数。

### 分子

現時点では `shrine_decision` のうち `action = route` かつ同一 `consultationAxis` を持つevent数。

### 指標

```text
axis_route_rate = shrine_decision(action=route) / consultation_completed
```

### 注意

`route_open` eventは `GoogleMapRouteLink.tsx` 側で発火しているが、現時点ではpropsから `consultationAxis` を受け取れない。

そのため暫定的に concierge 内の `shrine_decision action=route` を代替指標にする。

---

## axis別 premium率

### ゴール

相談軸ごとに課金導線へ進む強さを見る。

### 分母

`consultation_completed` のうち `consultationAxis` が存在するevent数。

### 分子候補

段階別に見る。

1. `premium_preview_click`
2. `checkout_started`
3. `premium_active`

### 指標

```text
axis_premium_preview_click_rate = premium_preview_click / consultation_completed

axis_checkout_started_rate = checkout_started / consultation_completed

axis_premium_active_rate = premium_active / consultation_completed
```

### 注意

`checkout_started` / `premium_active` に `consultationAxis` が常に残るかは、billing upgrade entry context の保持状況に依存する。

不足する場合は、billing導線へ `consultationAxis` を引き継ぐ設計が必要。

---

## PostHog集計方針

### 保存率

- event: `consultation_completed`
- breakdown: `consultationAxis`
- compare event: `save_prompt_click`

### 参拝導線率

- event: `consultation_completed`
- breakdown: `consultationAxis`
- compare event: `shrine_decision`
- filter: `action = route`

### 課金導線率

- event: `consultation_completed`
- breakdown: `consultationAxis`
- compare events:
  - `premium_preview_click`
  - `checkout_started`
  - `premium_active`

---

## 次フェーズTODO

- [ ] PostHogでaxis別save_rateを作成
- [ ] PostHogでaxis別route_rateを作成
- [ ] PostHogでaxis別premium_preview_click_rateを作成
- [ ] checkout_started / premium_active に consultationAxis が残るか確認
- [ ] route_openへconsultationAxisを渡す設計を検討
- [ ] 実測後に recommendation score へ反映するか判断
