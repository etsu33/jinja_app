

# Analytics Card Events

最終更新: 2026-05-18  
対象: Concierge結果画面 / Shrine詳細画面 / Premium導線 / card単位 analytics

---

## 目的

本ドキュメントは、KAMI MUSUBI の card 単位 analytics event を固定するための設計メモである。

analytics は後から適当に足すと、event名・payload・発火条件が画面ごとに分裂する。
そのため、実装前に以下を固定する。

- event名
- 発火条件
- payload
- accessLevel
- visibility
- source
- CTA種別
- Premium導線の計測単位

---

## 基本方針

### やること

- page単位ではなく card単位で計測する
- Free / Premium / Anonymous の表示差を event に含める
- teaser / partial / visible の違いを計測する
- CTAクリックは cardId と ctaType を必ず持たせる
- PostHog / GA へ差し替え可能な薄い schema にする

### やらないこと

- event名を画面ごとに自由命名しない
- 日本語のevent名を使わない
- payload に本文や相談内容の全文を入れない
- 個人情報や自由入力文をそのまま送らない
- Premium を「長文表示」単位で計測しない

---

## 用語定義

```ts
type AccessLevel = "anonymous" | "free" | "premium";

type CardVisibilityState = "visible" | "teaser" | "partial" | "hidden";

type AnalyticsSource =
  | "concierge_result"
  | "shrine_detail"
  | "billing_upgrade"
  | "mypage";
```

| 用語 | 意味 |
|---|---|
| cardId | 表示されたカードの識別子 |
| source | event が発生した画面・導線 |
| accessLevel | ユーザーの利用状態 |
| visibility | card の表示状態 |
| ctaType | 押されたCTAの種類 |
| recommendationRank | 推薦順位 |

---

## Event Naming Rule

### 命名規則

- snake_case
- 英語
- 動詞は末尾に置く
- card単位は `card_` prefix を使う
- Premium導線は `premium_` prefix を使う
- 保存導線は `save_` prefix を使う

### 採用例

```txt
card_view
card_teaser_view
card_partial_view
card_cta_click
premium_preview_view
premium_preview_click
save_prompt_view
save_prompt_click
```

### 禁止例

```txt
read_more_click
more_detail_click
premium_long_text_open
conciergeClick
カード表示
```

理由:
KAMI MUSUBI の Premium 差分は「続きを読む」ではなく、整理ブロックの増加で表現するため。

---

## Core Events

| event | 発火条件 | 目的 |
|---|---|---|
| card_view | card が visible で表示された | 通常表示カードの接触計測 |
| card_teaser_view | card が teaser で表示された | Premium予告・入口の接触計測 |
| card_partial_view | card が partial で表示された | Free向け部分表示の接触計測 |
| card_cta_click | card 内CTAが押された | card単位の行動計測 |
| premium_preview_view | PremiumPreviewCard が表示された | Premium価値訴求の接触計測 |
| premium_preview_click | PremiumPreviewCard のCTAが押された | Premium導線への興味計測 |
| save_prompt_view | SavePromptCard が表示された | 保存導線の接触計測 |
| save_prompt_click | SavePromptCard のCTAが押された | 保存意図の計測 |

---

## Optional Events

必要になった場合のみ追加する。
最初から増やしすぎない。
人類は計測項目を増やすと、だいたい見なくなる。

| event | 発火条件 | 目的 |
|---|---|---|
| shrine_detail_transition | Concierge結果から神社詳細へ遷移 | 推薦から詳細への遷移率計測 |
| billing_upgrade_click | Premium導線から upgrade へ遷移 | 課金導線クリック計測 |
| checkout_started | checkout session 開始 | 決済開始計測 |
| checkout_success | checkout success 復帰 | 決済完了計測 |
| premium_active_confirmed | billing status で premium active 確認 | Premium反映確認 |

---

## Common Payload

全 event は可能な限り以下の共通 payload を持つ。

```ts
type CardAnalyticsPayload = {
  event: string;
  cardId: CardId;
  source: AnalyticsSource;
  accessLevel: AccessLevel;
  visibility: CardVisibilityState;
  ctaType?: CtaType;
  shrineId?: number | string;
  recommendationRank?: number;
  mode?: "need" | "compat";
  flow?: "A" | "B";
  sessionId?: string;
};
```

---

## CardId

```ts
type CardId =
  | "consultation_summary"
  | "shrine_hero"
  | "shrine_meaning"
  | "action_meaning"
  | "previous_comparison"
  | "history_shift"
  | "other_shrines"
  | "shrine_compact"
  | "save_prompt"
  | "premium_preview"
  | "login_prompt"
  | "state_teaser"
  | "comparison_hint"
  | "deep_reflection"
  | "shrine_public_info"
  | "shrine_access"
  | "shrine_goriyaku"
  | "shrine_goshuin_preview"
  | "context_reason"
  | "personal_meaning"
  | "saved_record";
```

---

## CtaType

```ts
type CtaType =
  | "organize"
  | "save"
  | "login_to_save"
  | "view_shrine_detail"
  | "open_route"
  | "compare_previous"
  | "continue_with_premium"
  | "upgrade"
  | "checkout";
```

### CTA文言との対応

| CTA文言 | ctaType |
|---|---|
| 整理する | organize |
| 今の状態を整理する | organize |
| 保存する | save |
| ログインして保存 | login_to_save |
| 神社の詳細を見る | view_shrine_detail |
| 経路を見る | open_route |
| 前回と比べる | compare_previous |
| Premiumで整理を続ける | continue_with_premium |
| Premiumに進む | upgrade |
| 決済へ進む | checkout |

---

## Event Detail

## card_view

### 発火条件

- visibility が `visible`
- card が viewport に入ったとき
- 同一 cardId は同一画面表示中に原則1回のみ

### payload

```ts
{
  event: "card_view",
  cardId: "shrine_hero",
  source: "concierge_result",
  accessLevel: "free",
  visibility: "visible",
  shrineId: 123,
  recommendationRank: 1,
  mode: "need",
  flow: "A"
}
```

---

## card_teaser_view

### 発火条件

- visibility が `teaser`
- Premium価値の予告として表示されたとき

### payload

```ts
{
  event: "card_teaser_view",
  cardId: "action_meaning",
  source: "concierge_result",
  accessLevel: "free",
  visibility: "teaser",
  mode: "need"
}
```

---

## card_partial_view

### 発火条件

- visibility が `partial`
- Free向けに冒頭または hint のみ表示されたとき

### payload

```ts
{
  event: "card_partial_view",
  cardId: "shrine_meaning",
  source: "concierge_result",
  accessLevel: "free",
  visibility: "partial",
  shrineId: 123,
  recommendationRank: 1
}
```

---

## card_cta_click

### 発火条件

- card 内のCTAが押されたとき

### payload

```ts
{
  event: "card_cta_click",
  cardId: "premium_preview",
  source: "concierge_result",
  accessLevel: "free",
  visibility: "visible",
  ctaType: "continue_with_premium"
}
```

---

## premium_preview_view

### 発火条件

- PremiumPreviewCard が表示されたとき

### payload

```ts
{
  event: "premium_preview_view",
  cardId: "premium_preview",
  source: "concierge_result",
  accessLevel: "free",
  visibility: "visible"
}
```

---

## premium_preview_click

### 発火条件

- PremiumPreviewCard のCTAが押されたとき

### payload

```ts
{
  event: "premium_preview_click",
  cardId: "premium_preview",
  source: "concierge_result",
  accessLevel: "free",
  visibility: "visible",
  ctaType: "continue_with_premium"
}
```

---

## save_prompt_view

### 発火条件

- SavePromptCard が visible または teaser で表示されたとき

### payload

```ts
{
  event: "save_prompt_view",
  cardId: "save_prompt",
  source: "concierge_result",
  accessLevel: "anonymous",
  visibility: "teaser"
}
```

---

## save_prompt_click

### 発火条件

- 保存CTAが押されたとき

### payload

```ts
{
  event: "save_prompt_click",
  cardId: "save_prompt",
  source: "concierge_result",
  accessLevel: "anonymous",
  visibility: "teaser",
  ctaType: "login_to_save"
}
```

---

## Funnel KPI

## Premium CVR

### 目的

Premium preview から checkout / premium active までの転換を見る。

### funnel

```txt
premium_preview_view
↓
premium_preview_click
↓
billing_upgrade_click
↓
checkout_started
↓
checkout_success
↓
premium_active_confirmed
```

### KPI

| KPI | 計算 |
|---|---|
| preview CTR | premium_preview_click / premium_preview_view |
| upgrade CTR | billing_upgrade_click / premium_preview_view |
| checkout start rate | checkout_started / billing_upgrade_click |
| checkout success rate | checkout_success / checkout_started |
| premium activation rate | premium_active_confirmed / checkout_started |

---

## Save Intent KPI

### funnel

```txt
save_prompt_view
↓
save_prompt_click
↓
login_success または save_success
```

### KPI

| KPI | 計算 |
|---|---|
| save CTR | save_prompt_click / save_prompt_view |
| anonymous login intent | login_to_save click / anonymous save_prompt_view |
| save completion | save_success / save_prompt_click |

---

## Card Engagement KPI

| KPI | 計算 | 見ること |
|---|---|---|
| card exposure | card_view count | どの整理ブロックが見られたか |
| teaser CTR | card_cta_click / card_teaser_view | teaser が行動につながったか |
| partial CTR | card_cta_click / card_partial_view | partial が行動につながったか |
| detail transition | shrine_detail_transition / shrine_hero card_view | 神社詳細へ進んだか |

---

## Privacy Policy

### 送ってよいもの

- cardId
- source
- accessLevel
- visibility
- ctaType
- shrineId
- recommendationRank
- mode
- flow
- sessionId

### 送らないもの

- ユーザーの相談文全文
- 自由入力の原文
- 生年月日
- 住所の詳細
- 個人を直接識別できる情報
- 御朱印画像URL
- 決済情報

---

## 実装方針

### 推奨構造

```txt
apps/web/src/lib/analytics/
├─ events.ts
├─ cardEvents.ts
└─ types.ts
```

### events.ts

```ts
export function trackEvent(event: string, payload: Record<string, unknown>) {
  if (process.env.NODE_ENV !== "production") {
    console.log("ANALYTICS_EVENT", event, payload);
  }

  // TODO: PostHog / GA に差し替え
}
```

### cardEvents.ts

```ts
export function trackCardEvent(payload: CardAnalyticsPayload) {
  trackEvent(payload.event, payload);
}
```

---

## 実装TODO

```markdown
- [ ] analytics-card-events.md で event schema を固定
- [ ] CardId を union type として定義
- [ ] CtaType を union type として定義
- [ ] CardAnalyticsPayload を定義
- [ ] trackEvent の console log 仮実装を作る
- [ ] trackCardEvent を作る
- [ ] card_view / card_teaser_view / card_partial_view を発火する
- [ ] card_cta_click を共通化する
- [ ] premium_preview_view / premium_preview_click を追加する
- [ ] save_prompt_view / save_prompt_click を追加する
- [ ] PostHog or GA 接続は別PRに分離する
```

---

## 完了条件

- event名が固定されている
- cardId が固定されている
- ctaType が固定されている
- payload に個人情報を含めない方針が明記されている
- Premium funnel が追える
- Save intent funnel が追える
- PostHog / GA に依存しない薄い analytics 層として実装できる
