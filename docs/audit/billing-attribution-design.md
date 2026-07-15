

# Billing Attribution Design

> **Status: Archive**
>
> 本ドキュメントは、Card AnalyticsからCheckoutまでのAttribution課題・候補案を整理した時点設計である。
>
> 現行の課金判定は `docs/product/billing-paywall.md` を正本とする。

最終更新: 2026-05-19  
対象: billing funnel / premium click attribution / card analytics

---

## 目的

Premium導線の click event と billing funnel event を接続し、
どの表示ブロックが checkout / premium active に寄与したかを追える状態にする。

このPRでは実装追加は行わず、以下を整理する。

```markdown
- premium click → checkout_started の接続方針
- shrine_detail / concierge_result source の扱い
- billing source null 発生条件
- checkout session の責務
- sessionId を billing に持たせるか
- attribution window
```

---

## ゴール

### ゴール

Premium導線の成果を以下の流れで説明できる状態にする。

```txt
card_view / card_partial_view / card_teaser_view
↓
premium click
↓
checkout_started
↓
checkout_success
↓
premium_active
```

### 現在地

```markdown
- card analytics は source / cardId / visibility / accessLevel を持つ
- aggregateCardCtr helper は実装済み
- billing analytics は checkout_started / checkout_success / premium_active を持つ
- billing 側の attribution はまだ弱い
```

### 次の一手

```markdown
- billing event にどの文脈を引き継ぐか決める
- source null の発生条件を整理する
- sessionId / checkoutSessionId の責務を分ける
```

---

## attribution の対象

### card analytics 側

対象event:

```markdown
- card_view
- card_partial_view
- card_teaser_view
- premium_preview_click
- concierge_premium_preview_click
- shrine_detail_premium_preview_click
- save_prompt_click
```

主なpayload:

```ts
{
  event: string;
  source: "concierge_result" | "shrine_detail";
  cardId: string;
  visibility: "visible" | "partial" | "teaser";
  accessLevel: "anonymous" | "free" | "premium";
  sessionId?: string;
}
```

---

### billing analytics 側

対象event:

```markdown
- upgrade_click
- checkout_started
- checkout_success
- premium_active
```

現在の主なpayload:

```ts
{
  source?: BillingFunnelSource | null;
  funnelStep?: string;
  checkoutSessionId?: string;
}
```

---

## 現在の課題

### 1. card source と billing source が一致していない

card analytics の source:

```markdown
- concierge_result
- shrine_detail
```

billing funnel source:

```markdown
- state_delta_card
- null
```

このままだと、以下の接続が弱い。

```txt
personal_meaning teaser
↓
shrine_detail_premium_preview_click
↓
checkout_started
```

---

### 2. billing source が null になりやすい

発生条件:

```markdown
- /billing/upgrade に直接アクセスした
- source query が付与されていない
- source が parseBillingFunnelSource の許可値にない
- CTA側の source と billing 側の許可値がずれている
```

影響:

```markdown
- checkout_started の流入元が不明になる
- card別CTRからcheckout率へ接続できない
- dashboardで source別 funnel が崩れる
```

---

### 3. sessionId の扱いが非対称

card analytics:

```markdown
- sessionId を持てる
- track.ts 側でも analytics sessionId を自動付与する
```

billing analytics:

```markdown
- session_id / sessionId を sanitize で除去している
- checkoutSessionId は持つ
```

判断:

```markdown
- card CTR は event count で集計できる
- checkout attribution には追加設計が必要
```

---

## source 設計方針

billing 側にも、card 起点の source を扱えるようにする。

### 候補

```ts
type BillingFunnelSource =
  | "state_delta_card"
  | "concierge_result"
  | "shrine_detail"
  | "premium_preview"
  | "save_prompt";
```

ただし、source を広げすぎると意味が曖昧になる。

---

## 推奨方針

source は画面単位、cardId はカード単位に分ける。

```ts
{
  source: "concierge_result" | "shrine_detail";
  cardId: "premium_preview" | "save_prompt" | "personal_meaning" | "context_reason";
  funnelStep: string;
}
```

理由:

```markdown
- source は流入画面を表す
- cardId は押された導線の発生元を表す
- source に card 名を混ぜると group by が崩れる
```

---

## checkout session の責務

checkoutSessionId は Stripe / checkout flow の識別子として扱う。

```markdown
- checkout_started
- checkout_success
- premium_active
```

を同じ checkoutSessionId で接続する。

ただし、checkoutSessionId は card_view とは直接つながらない。

そのため、card 起点の attribution には以下が必要。

```markdown
- source
- cardId
- funnelStep
- analytics sessionId または attribution token
```

---

## sessionId を billing に持たせるか

### 選択肢A: billing payload に sessionId を残す

メリット:

```markdown
- card event と billing event を同一sessionで接続しやすい
- favorite → premium 相関にも使いやすい
```

デメリット:

```markdown
- 既存 sanitize 方針の変更が必要
- テスト更新が必要
- 外部providerに渡すpayload方針を再確認する必要がある
```

---

### 選択肢B: attribution token を別名で持つ

例:

```ts
{
  attributionId: string;
}
```

メリット:

```markdown
- sessionId sanitize 方針を崩さずに済む
- billing funnel 専用の接続IDにできる
```

デメリット:

```markdown
- 発行・保存・引き継ぎの設計が必要
- localStorage / query param / checkout metadata の扱いが増える
```

---

### 現時点の判断

このPRでは決めきらない。

ただし、次の実装候補としては以下が安全。

```markdown
- まず source / cardId / funnelStep を billing payload に追加する
- sessionId / attributionId は別PRで設計する
```

理由:

```markdown
- source / cardId はpayload拡張として小さい
- session attribution は checkout / provider / privacy 方針に関わるため重い
```

---

## attribution window

### 初期方針

同一session内を初期の attribution window とする。

```txt
premium click
↓ 30分以内
checkout_started
↓ 同一checkoutSessionId
checkout_success
↓ billing status確認
premium_active
```

### 将来方針

userId が安定して使える場合は、7日以内の転換も見る。

```markdown
- same session: 初期分析
- 24h window: 短期検討
- 7d window: 後日課金
```

---

## 最小実装案

次PRで実装するなら、まず以下に絞る。

```markdown
- BillingAnalyticsPayload に source / cardId / funnelStep を明示する
- parseBillingFunnelSource の許可値を source単位に見直す
- /billing/upgrade の query から source / cardId / funnelStep を読む
- checkout_started に source / cardId / funnelStep を渡す
- checkout_success / premium_active にも entryContext を引き継ぐ
- 既存テストを更新する
```

---

## まだやらないこと

```markdown
- [ ] PostHog / GA 接続
- [ ] dashboard UI 作成
- [ ] attributionId 実装
- [ ] checkout metadata 追加
- [ ] userIdベースの7日 attribution
```

---

## 次PR候補

### 候補A: billing payload 拡張

```markdown
- [ ] BillingAnalyticsPayload に cardId / funnelStep を追加
- [ ] source の許可値を整理
- [ ] upgrade / success の entryContext を整理
- [ ] billing.test.ts を更新
```

---

### 候補B: attribution token 設計

```markdown
- [ ] attributionId の発行方法を決める
- [ ] query / storage / checkout metadata のどれで持つか決める
- [ ] privacy / retention 方針を確認する
```

---

### 候補C: checkout session mapping

```markdown
- [ ] checkout_started / checkout_success / premium_active を checkoutSessionId で接続
- [ ] checkoutSessionId 欠損時の扱いを決める
- [ ] stale session の扱いを決める
```

---

## TODO

```markdown
- [x] docs/billing-attribution-design.md を作成
- [x] premium_preview_click → checkout_started 接続を整理
- [x] shrine_detail / concierge_result source を整理
- [x] billing source null 発生条件を整理
- [x] checkout session の責務を整理
- [x] sessionId を billing に持たせるか検討
- [x] attribution window を定義
- [x] 実装はまだ増やさない
```
