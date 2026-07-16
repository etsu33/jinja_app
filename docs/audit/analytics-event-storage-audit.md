

# Analytics Event Storage Audit

> **Status: Archive**
>
> 本ドキュメントは、Analytics保存先とProvider接続状況を確認した時点監査である。
>
> 現行のAnalytics実装は `apps/web/src/lib/analytics/providers.ts` 等を正本とする。

最終更新: 2026-05-18  
対象: analytics / billing funnel / shrine detail card events

---

## 目的

analytics event がどこへ送られ、どのpayloadで保持されているかを確認する。

このPRでは実装追加は行わず、以下を整理する。

```markdown
- track 系関数の責務
- event保存先の現状
- PostHog / GA 接続状況
- payload の必須項目
- 欠損リスク
- 次PR候補
```

---

## ゴール

### ゴール

card analytics と billing funnel analytics の接続状態を整理し、CTR集計へ進める状態にする。

### 現在地

```markdown
- track.ts が analytics 基底になっている
- trackCardEvent が card analytics を担当している
- trackBillingEvent が billing analytics を担当している
- PostHog / GA の実接続は未確認
```

### 次の一手

```markdown
- event payload 欠損を確認する
- analytics provider の責務を固定する
- aggregation helper 実装へ進む
```

---

# track / trackCardEvent / trackBillingEvent の責務

## track

ファイル:

```txt
apps/web/src/lib/analytics/track.ts
```

責務:

```markdown
- analytics event の最下層
- provider に event を渡す
- analytics payload を normalize する
- console / provider 層へ委譲する
```

想定位置:

```txt
UI
 ↓
trackCardEvent / trackBillingEvent
 ↓
track
 ↓
analytics provider
 ↓
PostHog / GA / console
```

---

## trackCardEvent

ファイル:

```txt
apps/web/src/lib/analytics/cardEvents.ts
```

責務:

```markdown
- card analytics schema を固定する
- card_view / card_partial_view / teaser 系eventを送る
- source / cardId / visibility を統一する
- shrine_detail / concierge_result を吸収する
```

現在確認できる送信箇所:

```markdown
- ConciergeClientFull.tsx
- ConciergeSectionsRenderer.tsx
- ShrineDetailArticle.tsx
```

送信event例:

```markdown
- card_view
- card_partial_view
- card_teaser_view
```

---

## trackBillingEvent

ファイル:

```txt
apps/web/src/lib/analytics/billing.ts
```

責務:

```markdown
- billing funnel event を送る
- checkout flow を追跡する
- Premium activation を追跡する
```

現在確認できる送信箇所:

```markdown
- billing/upgrade/page.tsx
- billing/success/page.tsx
```

送信event例:

```markdown
- checkout_started
- checkout_success
- premium_active
```

---

# 保存先の現状

現状確認できる範囲では、analytics event は local analytics layer に集約されている。

```markdown
UI
 ↓
trackCardEvent / trackBillingEvent
 ↓
track
 ↓
analytics provider
```

ただし、以下は未確認。

```markdown
- PostHog 実接続
- GA 実接続
- backend event 保存
- external analytics storage
```

現段階では以下の可能性が高い。

```markdown
- console logging
- local provider abstraction
- 将来 provider 差し替え前提
```

---

# PostHog / GA 接続状況

grep結果では、以下は docs にのみ存在する。

```markdown
- PostHog
- posthog
- gtag
- GA
```

実コード側では、provider abstraction のみ確認できる。

```txt
apps/web/src/lib/analytics/providers.ts
```

docs内記述:

```markdown
- TODO: PostHog / GA に差し替え
- PostHog or GA 接続は別PR
```

そのため、現時点の判断:

```markdown
- analytics provider abstraction は存在する
- PostHog / GA の本番接続は未完了の可能性が高い
- event schema 固定が優先段階
```

---

# 必須payload確認

## card analytics

最低限必要:

```ts
{
  event: string;
  source: string;
  cardId: string;
  visibility: string;
  accessLevel?: string;
}
```

望ましい追加項目:

```ts
{
  sessionId?: string;
  shrineId?: number;
  recommendationRank?: number;
  mode?: string;
}
```

---

## billing analytics

最低限必要:

```ts
{
  event: string;
  source: string;
}
```

望ましい追加項目:

```ts
{
  sessionId?: string;
  plan?: string;
  entryPoint?: string;
  cardId?: string;
}
```

---

# 欠損リスク

## source 欠損

問題:

```markdown
- shrine_detail か concierge_result か判別不能
- card別CTR比較が崩れる
```

影響:

```markdown
- dashboard 集計不能
- source別 funnel が壊れる
```

---

## cardId 欠損

問題:

```markdown
- どの card が表示されたか不明
```

影響:

```markdown
- card CTR 集計不能
- partial / teaser 比較不能
```

---

## visibility 欠損

問題:

```markdown
- visible / partial / teaser の比較不能
```

影響:

```markdown
- paywall 設計改善不能
```

---

## sessionId 欠損

問題:

```markdown
- favorite → premium の相関分析不能
```

影響:

```markdown
- 継続行動分析ができない
- funnel attribution が弱くなる
```

---

# 現時点の整理

## 確定していること

```markdown
- analytics abstraction layer は存在する
- card analytics schema は整理され始めている
- shrine_detail analytics は helper 化された
- premium funnel event は存在する
```

## 未確定

```markdown
- analytics 保存先
- provider の実態
- PostHog / GA 本番運用
- event retention
```

---

# 次PR候補

## 候補A: analytics payload audit

```markdown
- [ ] card event payload を一覧化
- [ ] source / cardId / visibility 欠損確認
- [ ] accessLevel 欠損確認
- [ ] sessionId 設計確認
```

---

## 候補B: analytics aggregation helper

```markdown
- [ ] aggregateCardCtr helper を作る
- [ ] card CTR 集計関数を作る
- [ ] visibility別集計を作る
- [ ] unit test を追加する
```

---

## 候補C: analytics provider 実接続

```markdown
- [ ] PostHog 接続
- [ ] GA 接続
- [ ] provider 切り替え設計
- [ ] production analytics routing
```

---

## TODO

```markdown
- [x] track / trackCardEvent / trackBillingEvent の責務整理
- [x] 保存先の現状整理
- [x] PostHog / GA 接続状況整理
- [x] 必須payload確認
- [x] 欠損リスク整理
- [x] 次PR候補整理
- [ ] 実装追加はまだ行わない
```
