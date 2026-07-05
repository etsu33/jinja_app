

# Mobile Concierge explanation.summary Audit

## 目的

Mobile Concierge の推薦カードで `explanation.summary` を表示すべきかを検討する。

本監査では、すぐにUIへ表示追加するのではなく、以下を整理する。

- `RecommendationApiCard` が `explanation` を受け取っているか
- `RecommendationCard` が `explanationSummary` を持っているか
- `toRecommendationCard` で `explanation.summary` をnormalizeしているか
- 現在の表示が `recommendation_reason_v4` / `reason_facts` / legacy reason のどれを使っているか
- `explanation.summary` を追加した場合の表示重複リスク

## 前提

以下は完了済み。

- 主要Contract固定
  - `reason_facts`
  - `recommendation_reason_v4`
  - `action_suggestion_v4_preview`
  - `consultation_axis`
  - `explanation`
- Normalize Cleanup
  - Web `_reason_facts` fallback削減
  - Web `_explanation_payload.original_reason` 依存削減
  - Mobile `_reason_facts` fallback削減
- Mobile Shrine Detail で `action_suggestion_v4_preview` を表示
- Concierge → Detail へ `action_suggestion_v4_preview` を引き継ぎ

## 現在地

### RecommendationApiCard

対象ファイル:

- `apps/mobile/app/concierge/index.tsx`

現状:

```markdown
- RecommendationApiCard
  - explanation未定義
```

つまり、Mobile Concierge のAPI受け取り型にはまだ `explanation` が入っていない。

## RecommendationCard

現状:

```markdown
- RecommendationCard
  - explanationSummary未定義
```

Mobile内部の表示用カード型にも `explanationSummary` は存在しない。

## toRecommendationCard

現状:

```markdown
- toRecommendationCard
  - explanation normalizeなし
```

`toRecommendationCard` では現在、以下を中心に整形している。

- `recommendation_reason_v4`
- `reason_facts`
- `recommendation_reason_detail`
- `action_suggestion_v4_preview`

`explanation.summary` はまだnormalizeされていない。

## 表示

現状:

```markdown
- 表示
  - card.reason = recommendation_reason_v4 / reason_facts / legacy reason
  - explanation.summary は未使用
```

Mobile Concierge の推薦カードでは、主な説明文として `card.reason` を表示している。

`card.reason` は以下の優先順で作られる。

1. `recommendation_reason_v4`
2. `reason_facts` 由来の補助文
3. legacy `reason`

そのため、`explanation.summary` をそのまま追加すると、推薦理由と意味が重複する可能性がある。

## 判断

現時点では、Mobile Concierge に `explanation.summary` をすぐ表示追加しない。

理由:

- `RecommendationApiCard` に `explanation` が未定義
- `RecommendationCard` に `explanationSummary` が未定義
- `toRecommendationCard` にnormalizeがない
- 既存の `card.reason` が推薦理由として機能している
- `recommendation_reason_v4` と `explanation.summary` の表示内容が重複しやすい
- Mobileカード上で情報量が増えすぎる可能性がある

したがって、現時点では以下の方針とする。

```text
Mobile Conciergeカードの主説明: recommendation_reason_v4
補助根拠: reason_facts
詳細説明: Shrine Detail側の explanation
```

## 今回のPRでやること

- Mobile Conciergeで `explanation.summary` が未使用であることを文書化する
- 表示追加しない判断を記録する
- 追加する場合の条件を整理する
- 次PR候補を明確にする

## 今回のPRでやらないこと

- `RecommendationApiCard` に `explanation` を追加しない
- `RecommendationCard` に `explanationSummary` を追加しない
- `toRecommendationCard` にnormalizeを追加しない
- Mobile Conciergeカードに `explanation.summary` を表示しない
- API Contractは変更しない

## 将来追加する場合の条件

`explanation.summary` をMobile Conciergeに表示する場合は、以下の条件を満たすときに限定する。

- `recommendation_reason_v4` と意味が重複しない
- 1カードあたりの情報量が増えすぎない
- 表示目的が明確である
- Webとの差分を縮める必要がある
- Detailへ遷移せずとも、候補の意味を把握しやすくする必要がある

## 追加する場合の最小実装案

### 型追加候補

```ts
explanation?: {
  summary?: string | null;
} | null;
```

### ViewModel追加候補

```ts
explanationSummary?: string | null;
```

### normalize候補

```ts
const explanationSummary = asTrimmedString(item.explanation?.summary);
```

### 表示候補

既存の `card.reason` の下に出すのではなく、以下のどちらかに限定する。

```text
A. card.reason が空の場合のfallback
B. 折りたたみ/詳細補助として表示
```

## 次PR候補

### 1. Mobile consultation axis analytics

ブランチ候補:

`refactor/mobile-consultation-axis-analytics`

目的:

- Mobileで `consultation_axis` を表示ではなくanalytics / contextとして保持するか検討する

対象候補:

- `apps/mobile/app/concierge/index.tsx`

### 2. Mobile Concierge explanation summary fallback

ブランチ候補:

`feature/mobile-concierge-explanation-summary-fallback`

目的:

- `card.reason` が空の場合だけ `explanation.summary` をfallbackとして使う
- 情報量を増やさず、欠落時の安全性だけ上げる

対象候補:

- `apps/mobile/app/concierge/index.tsx`

### 3. Concierge First UI全体レビュー

ブランチ候補:

`audit/concierge-first-ui-overall-review`

目的:

- Web / Mobile のConcierge First UIを横断レビューする
- 次の実装優先順位を整理する

対象候補:

- docsのみ
- 実装なし

## 推奨判断

次PRは **Mobile consultation axis analytics** または **Concierge First UI全体レビュー** が安全。

`explanation.summary` 表示追加は、現時点では優先度を下げる。

理由:

- Mobile Conciergeの主説明は `recommendation_reason_v4` で成立している
- Detail側で `explanation` は扱えている
- 追加表示より、analytics / context整理の方が次の改善判断に効きやすい

## TODO

```markdown
# Mobile Concierge explanation.summary Audit

- [x] develop最新版化
- [x] audit/mobile-concierge-explanation-summary 作成
- [x] RecommendationApiCard確認
- [x] RecommendationCard確認
- [x] toRecommendationCard確認
- [x] 現在の表示確認
- [x] explanation.summary未使用を確認
- [x] 表示追加しない判断を記録
- [x] 次PR候補整理
- [ ] docs/audit/mobile-concierge-explanation-summary.md をコミット
- [ ] PR作成
```

## 完了条件

- Mobile Conciergeで `explanation.summary` が未使用であることが文書化されている
- すぐに表示追加しない判断が記録されている
- 将来追加する場合の条件と最小実装案が整理されている
