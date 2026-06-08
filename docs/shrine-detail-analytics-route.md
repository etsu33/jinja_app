# Shrine Detail Analytics Route

最終更新: 2026-05-18

---

## 目的

ShrineDetail 側の analytics event を整理し、

```markdown
- card view
- partial view
- click event
- page view
```

の責務を分離する。

特に、

```markdown
track()
trackCardEvent()
```

が混在し始めているため、
「どの event をどこで送るか」を固定する。

---

## 現在の event 棚卸し

### 1. page view

対象:

```txt
apps/web/src/components/shrine/ShrineDetailViewTracker.tsx
```

現在:

```ts
track("shrine_detail_view", {
  ...
})
```

責務:

```markdown
- 神社詳細ページ表示
- card 単位ではない
- page analytics
```

---

### 2. premium preview click

対象:

```txt
apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx
```

現在:

```ts
track("shrine_detail_premium_preview_click", {
  ...
})
```

責務:

```markdown
- upgrade CTA click
- paywall click
- card view ではない
```

note:

```markdown
card analytics と混ぜない
```

---

### 3. save / decision event

対象:

```txt
apps/web/src/components/shrine/ShrineSaveButton.tsx
```

現在:

```ts
track("favorite_click", {
  ...
})

track("shrine_decision", {
  ...
})
```

責務:

```markdown
- 保存
- 行動決定
- conversion 寄り
```

---

## card analytics 方針

### card_view

用途:

```markdown
- card が visible
- 実際に描画された
```

候補:

```markdown
- context_reason
- personal_meaning
- saved_record
```

送信:

```ts
trackCardEvent({
  event: "card_view",
  ...
})
```

---

### card_partial_view

用途:

```markdown
- partial
- teaser
- preview
```

候補:

```markdown
- context_reason
- personal_meaning
```

note:

```markdown
saved_record は hidden / visible のみ
```

---

## source 方針

ShrineDetail 側は固定。

```markdown
source: "shrine_detail"
```

ConciergeResult と混ぜない。

---

## track と trackCardEvent の責務

### track

使うもの:

```markdown
- page view
- click
- conversion
- save
- billing
```

例:

```markdown
- shrine_detail_view
- favorite_click
- shrine_decision
- shrine_detail_premium_preview_click
```

---

### trackCardEvent

使うもの:

```markdown
- card visibility
- partial visibility
- teaser visibility
```

例:

```markdown
- card_view
- card_partial_view
```

---

## helper 候補

候補:

```txt
apps/web/src/lib/analytics/cardRenderAnalytics.ts
```

責務:

```markdown
- visibility 判定
- event routing
- source 固定
- accessLevel payload 統一
```

---

## 今回やらない

```markdown
- analytics provider 差し替え
- PostHog 実接続
- GA event migration
- helper 抽象化の本実装
- 全card自動tracking
```

---

## 次PR候補

### 候補A

```markdown
- context_reason card_view 接続
- context_reason card_partial_view 接続
```

### 候補B

```markdown
- personal_meaning card_view 接続
- personal_meaning card_partial_view 接続
```

### 候補C

```markdown
- analytics route helper 作成
- ShrineDetail analytics 共通化
```
