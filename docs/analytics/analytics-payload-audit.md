> **Status: Reference**
>
> 本ドキュメントは、対象機能の設計背景・補足方針を記録した参照資料である。
>
> 現行仕様は関連するActive文書、実装コードおよびテストを最終的な正本とする。
# Analytics Payload Audit

最終更新: 2026-05-18  
対象: analytics payload / card analytics / billing funnel analytics

---

## 目的

analytics payload の現状を確認し、CTR集計・funnel分析に必要な項目が揃っているかを監査する。

このPRでは実装追加は行わず、以下を整理する。

```markdown
- trackCardEvent の payload 型
- trackBillingEvent の payload 型
- 必須項目の欠損リスク
- sessionId の設計状態
- aggregation helper 前提条件
```

---

## ゴール

### ゴール

analytics payload の構造と欠損リスクを固定し、aggregation helper 実装へ進める状態にする。

### 現在地

```markdown
- card analytics schema は概ね整備されている
- shrine_detail analytics は helper 化済み
- billing analytics は source が限定的
- sessionId の扱いに差分がある
```

### 次の一手

```markdown
- payload 欠損箇所を洗い出す
- session attribution 方針を決める
- aggregation helper 実装へ進む
```

---

# trackCardEvent の payload 型

ファイル:

```txt
apps/web/src/lib/analytics/cardEvents.ts
```

確認できた型:

```ts
export type CardAnalyticsPayload = {
  event: CardAnalyticsEventName;
  cardId: CardId;
  source: AnalyticsSource;
  accessLevel: AccessLevel;
  visibility: CardVisibilityState;
  sessionId?: string;
};
```

---

## 確認結果

### cardId

```markdown
- 必須
- 型で固定済み
```

### source

```markdown
- 必須
- AnalyticsSource 型で固定済み
```

### accessLevel

```markdown
- 必須
- anonymous / free / premium
```

### visibility

```markdown
- 必須
- hidden / partial / teaser / visible
```

### sessionId

```markdown
- optional
- 多くの card event で付与されている
```

---

# trackCardEvent の送信状況

## concierge_result

主な送信箇所:

```txt
apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx
apps/web/src/app/concierge/ConciergeClientFull.tsx
```

送信確認済み:

```markdown
- consultation_summary
- shrine_meaning
- action_meaning
- save_prompt
- premium_preview
- shrine_hero
- shrine_compact
- other_shrines
- previous_comparison
- history_shift
- deep_reflection
```

---

## shrine_detail

主な送信箇所:

```txt
apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx
```

送信確認済み:

```markdown
- context_reason
- personal_meaning
- saved_record
```

---

# trackBillingEvent の payload 型

ファイル:

```txt
apps/web/src/lib/analytics/billing.ts
```

確認できた型:

```ts
export type BillingAnalyticsPayload = {
  source?: BillingFunnelSource | null;
};
```

関連event:

```markdown
- upgrade_click
- checkout_started
- checkout_success
- premium_active
```

---

# billing analytics の現状

## source

現状確認できた funnel source:

```markdown
- state_delta_card
```

以下は null の可能性がある。

```markdown
- upgrade page direct access
- source query 欠損
- source parse failure
```

---

## sessionId の扱い

重要:

```markdown
trackBillingEvent は session_id / sessionId を payload から除去している
```

確認箇所:

```txt
apps/web/src/lib/analytics/billing.ts
apps/web/src/lib/analytics/__tests__/billing.test.ts
```

テスト確認済み:

```markdown
- session_id は除去される
- sessionId は除去される
```

---

# track.ts の sessionId 設計

ファイル:

```txt
apps/web/src/lib/analytics/track.ts
```

確認内容:

```ts
const sessionId = getAnalyticsSessionId();
const payloadWithSession = sessionId ? { ...payload, sessionId } : payload;
```

---

## 現状の意味

```markdown
- analytics 基底では sessionId を自動付与している
- card analytics では sessionId が残る
- billing analytics では sanitize で除去される
```

---

# source 欠損リスク

## card analytics

card analytics 側は source が型必須。

そのため、基本的には安全。

ただし以下は注意。

```markdown
- source の種類追加時
- AnalyticsSource 更新漏れ
- temporary event 実装
```

---

## billing analytics

billing 側は source optional。

そのため、以下が発生しうる。

```markdown
- source: null
- attribution不能
- CTR接続不能
```

影響:

```markdown
- premium click → checkout_started の attribution が弱くなる
```

---

# cardId 欠損リスク

## 現状

```markdown
- cardId は型必須
- Concierge / ShrineDetail とも付与済み
```

## リスク

以下で崩れる可能性。

```markdown
- any payload
- temporary analytics
- schema bypass
```

---

# visibility 欠損リスク

## 現状

```markdown
- visibility は型必須
- partial / teaser / visible が整理済み
```

## リスク

以下で崩れる可能性。

```markdown
- 新 card 実装時
- visibility 未設定
- hidden を event 送信してしまう
```

---

# accessLevel 欠損リスク

## 現状

```markdown
- accessLevel は型必須
- resolveAccessLevel 経由で付与されている
```

## リスク

```markdown
- SSR/CSR境界
- 未ログイン状態
- billing status loading中
```

---

# sessionId 設計状態

## card analytics

かなり整備されている。

```markdown
- tid
- activeThreadId
- analytics sessionId
```

が使われている。

---

## billing analytics

session attribution が弱い。

理由:

```markdown
- sanitizeでsessionId除去
- checkout session中心
- billing provider依存を避けている
```

---

## 現時点の判断

```markdown
- card CTR 集計は可能
- session単位 attribution は未完成
- favorite → premium 相関は別設計が必要
```

---

# aggregation helper 前提条件

## 現時点で満たしている

```markdown
- cardId
- source
- visibility
- accessLevel
```

## 未完成

```markdown
- session attribution
- billing attribution
- user-level retention
```

---

# 次PR候補

## 候補A: aggregateCardCtr helper

```markdown
- [ ] aggregateCardCtr を作る
- [ ] visibility別集計を作る
- [ ] card別CTR算出を作る
- [ ] unit test を追加する
```

---

## 候補B: billing attribution 設計

```markdown
- [ ] premium click → checkout_started 接続
- [ ] session attribution 設計
- [ ] checkout session 設計確認
```

---

## 候補C: analytics provider 実接続

```markdown
- [ ] PostHog 接続
- [ ] GA 接続
- [ ] provider routing
```

---

## TODO

```markdown
- [x] trackCardEvent の payload 型を確認
- [x] trackBillingEvent の payload 型を確認
- [x] source 欠損リスクを確認
- [x] cardId 欠損リスクを確認
- [x] visibility 欠損リスクを確認
- [x] accessLevel 欠損リスクを確認
- [x] sessionId の設計状態を確認
- [x] docs/analytics-payload-audit.md を作成
- [x] 実装はまだ増やさない
```
