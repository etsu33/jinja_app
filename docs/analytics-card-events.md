# Analytics Card Events

最終更新: 2026-05-18  
対象: Concierge結果画面 / Shrine詳細画面 / Premium導線 / card単位 analytics

---

## 目的

本ドキュメントは、KAMI MUSUBI の **card 単位** analytics event を固定するための設計メモである。  
analytics は後から適当に足すと、**event名・payload・発火条件**が画面ごとに分裂する。  
人類はなぜ毎回「あとで整理しよう」でevent名を爆発させるのか。未来の自分を敵視しすぎている。

そのため、実装前に以下を固定する。

- event名
- 発火条件
- payload
- accessLevel
- visibility
- source
- CTA種別
- Premium導線の計測単位

## 関連ドキュメント

- `docs/analytics/save-premium-correlation.md`
  - favorite_click / shrine_detail_view / route_click / premium_preview_click / checkout_started / premium_active の相関定義
  - source別 save_rate の定義
  - detail / save / route 比率の定義
  - 「保存されるが課金されない」「詳細は見られるが参拝行動に進まない」「Premium preview は押されるが checkout に行かない」落下判定

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

type CardVisibilityState =
  | "visible"
  | "teaser"
  | "partial"
  | "hidden";

type AnalyticsSource =
  | "concierge_result"
  | "shrine_detail"
  | "billing_upgrade"
  | "mypage";

| 用語 | 意味 |
|---|---|
| cardId | 表示されたカードの識別子 |
| source | event が発生した画面・導線 |
| accessLevel | ユーザーの利用状態 |
| visibility | card の表示状態 |
| ctaType | 押されたCTAの種類 |
| recommendationRank | 推薦順位 |

## Event Naming Rule

### 命名規則

- snake_case
- 英語
- 動詞は末尾に置く
- card単位は card_ prefix を使う
- Premium導線は premium_ prefix を使う
- 保存導線は save_ prefix を使う

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
save_success
next_session
next_thread
thread_resume
```

### 禁止例
```txt
read_more_click
more_detail_click
premium_long_text_open
conciergeClick
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
analytics は増やすほど人類が見なくなる。観測者が観測を放棄する量子力学。

| event | 発火条件 | 目的 |
|---|---|---|
| shrine_detail_transition | Concierge結果から神社詳細へ遷移 | 推薦から詳細への遷移率計測 |
| billing_upgrade_click | Premium導線から upgrade へ遷移 | 課金導線クリック計測 |
| checkout_started | checkout session 開始 | 決済開始計測 |
| checkout_success | checkout success 復帰 | 決済完了計測 |
| premium_active_confirmed | billing status で premium active 確認 | Premium反映確認 |
| next_session | 別日で再訪した | retention計測 |
| next_thread | 新しい相談threadを開始した | 継続相談計測 |
| thread_resume | 既存threadを再開した | 履歴回帰計測 |

---

## Common Payload

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

  // legacy
  sessionId?: string;

  // analytics v2
  analyticsSessionId?: string;
  threadId?: string;
  resultSetId?: string;
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

- visibility が visible
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

## card_teaser_view

### 発火条件

- visibility が teaser
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

## card_partial_view

### 発火条件

- visibility が partial
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

## Save Intent KPI

| KPI | 計算 | 目的 |
|---|---|---|
| save_prompt_view | SavePromptCard 表示 | 保存導線の接触計測 |
| save_prompt_click | SavePromptCard 内CTAクリック | 保存意図の計測 |

### Save Success Event Policy

#### 目的

`save_prompt_click` 後に、実際に保存が完了したかを計測する。

#### event

```txt
save_success
```

#### 発火条件

- 相談結果の保存APIが成功した
- ログイン後に保存処理が完了した
- 保存対象が backend / storage 側で確定した

#### payload

```ts
{
  event: "save_success",
  source: "concierge_result",
  accessLevel: "free",
  threadId: "...",
  resultSetId: "...",
  saveType: "consultation"
}
```

#### 注意

`save_prompt_click` は保存意図を表す。  
`save_success` は保存完了を表す。

両者は別eventとして扱う。

---

## Card Engagement KPI

| KPI | 計算 | 目的 |
|---|---|---|
| card_view | card visible 表示 | card単位の接触計測 |
| card_teaser_view | card teaser 表示 | Premium予告の接触計測 |
| card_partial_view | card partial 表示 | Free向け部分表示の接触計測 |
| card_cta_click | card 内CTAクリック | 行動計測 |

---

## Retention KPI

### 目的

継続利用・相談継続・履歴回帰を計測する。

Premium CVRだけではなく、  
「また戻ってきたか」を追う。  
継続率を見ないプロダクトは、だいたい短命になる。

### next_session

別日にアプリへ再訪したとき。

#### event

```txt
next_session
```

#### payload

```ts
{
  analyticsSessionId: "...",
  previousSessionAt: "2026-05-18T12:00:00Z"
}
```

### next_thread

新しい相談threadを開始したとき。

#### event

```txt
next_thread
```

#### payload

```ts
{
  analyticsSessionId: "...",
  threadId: "...",
  source: "concierge_result"
}
```

### thread_resume

既存threadを再開したとき。

#### event

```txt
thread_resume
```

#### payload

```ts
{
  analyticsSessionId: "...",
  threadId: "...",
  resultSetId: "..."
}
```

### KPI

| KPI | 計算 |
|---|---|
| retention rate | next_session / analyticsSessionId |
| thread continuation rate | next_thread / next_session |
| thread resume rate | thread_resume / next_session |

---

## Retention / ID Responsibility

## Analytics Naming Migration Policy

### 目的

`sessionId` に analytics session と concierge thread の2つの意味が混在しているため、  
今後の実装では ID 名を段階的に分離する。

### 現状の問題

| 名前 | 現在の意味 | 問題 |
|---|---|---|
| sessionId | analytics session または threadId | 意味が混在している |
| tid | concierge thread id | analytics payload 上では sessionId として渡される箇所がある |
| resultSetId | 推薦結果セット | 一部eventでのみ送られている |

### 移行方針

| Phase | 内容 | 実装有無 |
|---|---|---|
| Phase 0 | docsで責務と移行方針を固定する | 今回 |
| Phase 1 | card event payload に `threadId` を追加し、`sessionId` は互換維持する | 後続PR |
| Phase 2 | `track.ts` で `analyticsSessionId` を追加し、既存 `sessionId` も当面維持する | 後続PR |
| Phase 3 | 集計関数を `analyticsSessionId ?? sessionId` に対応させる | 後続PR |
| Phase 4 | `sessionId` の意味を段階的に廃止する | 将来 |

### payload 方針

今後のanalytics payloadは以下を優先する。

```ts
{
  analyticsSessionId: "...",
  threadId: "...",
  resultSetId: "..."
}
```

互換期間中は以下も許容する。

```ts
{
  sessionId: "..."
}
```

### このPRでやらないこと

- `track.ts` を変更しない
- `trackCardEvent` を変更しない
- 既存 event payload を変更しない
- 集計関数を変更しない
- PostHog / GA 接続をしない

## Analytics Serialization Responsibility

### AnalyticsPayload

```ts
type AnalyticsPayload =
  Record<string, string | number | boolean>;
```

### AnalyticsPayload Responsibility

- provider 送信可能型
- primitive value のみ許可
- nested object を許可しない
- Date object を許可しない
- undefined は serialize layer で除外する

### serializeCardAnalyticsPayload の責務

serializeCardAnalyticsPayload は
analytics provider へ送信する直前の
payload 正規化レイヤとして扱う。


## providers.ts Responsibility

### 目的

analytics provider を差し替え可能にしつつ、  
application layer と provider SDK を分離する。

PostHog / GA / console provider を
後から切り替えられるようにする。

人類は analytics SDK を直接各画面に書き始めると、
半年後に「このeventどこから飛んでるの？」遺跡探索を始める。

### 責務

- analytics provider abstraction layer
- payload passthrough layer
- provider initialize responsibility

### やらないこと

- serialization を担当しない
- normalize を担当しない
- undefined 除去を担当しない
- analytics payload v1/v2 互換吸収を担当しない
- business logic を担当しない
- retention 判定を担当しない

### 境界

```txt
UI / feature layer
  ↓
trackCardEvent
  ↓
serializeCardAnalyticsPayload
  ↓
providers.ts
  ↓
PostHog / GA / console
```

### serialize responsibility の所在


| layer | responsibility |
|---|---|
| feature layer | event発火 |
| trackCardEvent | analytics event統一入口 |
| serializeCardAnalyticsPayload | payload normalize / undefined除去 |
| providers.ts | provider forwarding |
| analytics SDK | 外部送信 |

---

## Analytics Firing Layer Responsibility

### 目的

analytics event を

- どこで
- いつ
- 何回
- 誰が

発火するかを固定する。

schema が正しくても、
発火責務が崩れると analytics は壊れる。

人類は duplicate event に鈍感すぎる。

### firing layer の責務

- analytics event 発火
- event timing 制御
- viewport exposure 判定
- event dedupe
- resultSetId 単位の重複防止
- analytics payload 構築

### firing layer がやらないこと

- provider dispatch
- provider initialize
- analytics SDK 呼び出し詳細
- retention 集計
- dashboard 集計
- recommendation logic
- business decision

### firing responsibility

| layer | responsibility |
|---|---|
| feature component | user interaction / UI state |
| trackCardEvent | analytics schema統一 |
| serializeCardAnalyticsPayload | payload normalize |
| providers.ts | provider forwarding |
| analytics SDK | 外部送信 |

### dedupe responsibility

| ID | responsibility |
|---|---|
| analyticsSessionId | 訪問単位 |
| threadId | 相談単位 |
| resultSetId | 同一推薦結果単位 |

### IntersectionObserver Responsibility

IntersectionObserver は
viewport exposure 判定のみを担当する。

以下は担当しない。

- analytics payload 構築
- retention 判定
- recommendation logic
- provider dispatch

### event firing policy

同一 cardId の card_view は、
同一 resultSetId 内では原則1回のみ発火する。

同一eventの重複送信防止は、
analytics firing layer 側で責務を持つ。

### 実装候補

```txt
ConciergeSectionsRenderer.tsx
PremiumStateDeltaCard.tsx
ThreadList.tsx
ConciergeClientFull.tsx
```

### このPRでやらないこと

- firing layer 共通hook化
- analytics middleware 作成
- track API redesign
- PostHog optimize
- queueing layer 実装
- retry layer 実装


---

## Analytics Event Domain / Namespace Policy

### 目的

analytics event の増殖を防ぐため、event を domain ごとに分離する。

`track()` をどこからでも直接呼び出すと、event名・payload・発火条件が分裂する。  
そのため、原則として domain-specific helper を経由する。

### event domain table

| domain | helper | 主なevent | 責務 |
|---|---|---|---|
| core | `track()` | system / fallback event | low-level pipeline |
| card | `trackCardEvent()` | card_view / card_cta_click / premium_preview_click / save_prompt_click | card exposure / CTA |
| retention | `trackRetentionEvent()` | next_session / next_thread / thread_resume | 継続利用 / 再訪 / 再開 |
| billing | `trackBillingEvent()` | billing_upgrade_click / checkout_started / checkout_success / premium_active_confirmed | 課金funnel |
| search | `trackSearchEvent()` | shrine_search / map_search / route_open | 検索・経路導線 |

### track() responsibility

`track()` は low-level analytics pipeline として扱う。

#### やること

- analyticsSessionId の付与
- timestamp の付与
- provider dispatch
- fail-safe logging
- fallback event の送信

#### やらないこと

- card schema の組み立て
- retention 判定
- billing funnel 判定
- business logic
- UI visibility 判定
- dedupe 判定

### 直track禁止原則

画面・component から `track()` を直接呼ぶことは原則避ける。

以下は domain-specific helper を使う。

| event種別 | 使用helper |
|---|---|
| card表示 / card CTA | `trackCardEvent()` |
| 継続利用 / 再訪 / 再開 | `trackRetentionEvent()` |
| 課金導線 | `trackBillingEvent()` |
| 検索 / map / route | `trackSearchEvent()` |

### escape hatch policy

以下の場合のみ、直 `track()` を許容する。

- まだ domain helper が存在しない experimental event
- system error / debug event
- provider疎通確認
- migration期間中の一時event
- analytics schema確定前の仮event

ただし、直 `track()` を使う場合は以下を守る。

- payload に個人情報を入れない
- nested object を送らない
- Date object を送らない
- event名は snake_case にする
- 後続PRで domain helper へ移行する

### namespace設計

analytics event は以下の namespace 方針で整理する。

| namespace | 例 | 用途 |
|---|---|---|
| `card_*` | card_view / card_cta_click | card単位の表示・行動 |
| `premium_*` | premium_preview_click | Premium導線 |
| `save_*` | save_prompt_click / save_success | 保存導線 |
| `billing_*` | billing_upgrade_click | 課金導線 |
| `checkout_*` | checkout_started / checkout_success | 決済処理 |
| `next_*` | next_session / next_thread | 継続利用 |
| `thread_*` | thread_resume | 相談thread再開 |

### このPRでやらないこと

- `track()` の実装修正
- `trackCardEvent()` の実装修正
- `trackRetentionEvent()` の新規実装
- `trackBillingEvent()` の変更
- `trackSearchEvent()` の新規実装

---

## Retention Event Audit

### 目的

Retention KPI を dashboard で集計できる状態か確認するため、既存実装の event 発火箇所と payload 欠損を監査する。

この監査では、実装追加は行わず、以下を確認する。

```markdown
- premium_history_comparison_view の実装位置
- thread_resume の実装位置
- save_prompt_click / favorite_click の責務
- source の欠損
- cardId の欠損
- dashboard 集計可能状態
- 実装不足event
```

### 監査コマンド

```bash
grep -R "premium_history_comparison_view\|thread_resume\|save_prompt_click\|favorite_click\|premium_preview_click" apps/web/src -n | grep -v "__tests__" | grep -v ".test."
```

```bash
grep -R "trackRetentionEvent(\"thread_resume\"\|thread_resume" apps/web/src -n | grep -v "__tests__" | grep -v ".test."
```

### 実装確認結果

| event | 実装位置 | helper | 状態 | 判断 |
|---|---|---|---|---|
| premium_preview_click | ConciergeSectionsRenderer.tsx | trackCardEvent | 実装あり | 集計可能 |
| premium_preview_click | ShrineDetailArticle.tsx | trackCardEvent | 実装あり | 集計可能 |
| save_prompt_click | ConciergeSectionsRenderer.tsx | trackCardEvent | 実装あり | 集計可能 |
| premium_history_comparison_view | PremiumStateDeltaCard.tsx | trackRetentionEvent | 実装あり | 集計可能。event名整理余地あり |
| favorite_click | ShrineSaveButton.tsx | direct track | 実装あり | source / cardId 欠損あり。save domain整理候補 |
| thread_resume | retentionEvents.ts | trackRetentionEvent 型のみ | 発火箇所なし | 未計測。実装不足候補 |

### payload確認

#### premium_preview_click / concierge_result

```ts
trackCardEvent({
  event: "premium_preview_click",
  cardId: "premium_preview",
  source: "concierge_result",
  accessLevel: props.accessLevel,
  visibility: "teaser",
  ctaType: "continue_with_premium",
  shrineId: props.shrineId ?? undefined,
  threadId: props.tid ?? undefined,
});
```

判断:

```markdown
- source あり
- cardId あり
- accessLevel あり
- visibility あり
- threadId あり
- dashboard集計可能
```

#### save_prompt_click / concierge_result

```ts
trackCardEvent({
  event: "save_prompt_click",
  cardId: "save_prompt",
  source: "concierge_result",
  accessLevel,
  visibility: savePromptVisibility,
  ctaType: isGuestUser ? "login_to_save" : "save",
  threadId: tid ?? undefined,
  resultSetId,
});
```

判断:

```markdown
- source あり
- cardId あり
- accessLevel あり
- visibility あり
- threadId あり
- resultSetId あり
- dashboard集計可能
```

#### premium_history_comparison_view

```ts
trackRetentionEvent("premium_history_comparison_view", {
  source: "state_delta_card",
  hasSummary: Boolean(stateDelta.summary),
  hasCombinationChange: Boolean(stateDelta.combinationChange?.summary),
  combinationChanged: Boolean(stateDelta.combinationChange?.changed),
  hasTransitionNarrative: Boolean(stateDelta.transitionNarrative?.summary),
  transitionType: stateDelta.transitionNarrative?.type ?? "unknown",
  changedNeedTagCount: changedNeedTags.length,
  continuedNeedTagCount: continuedNeedTags.length,
  daysSincePrevious: stateDelta.daysSincePrevious,
  within7DaysSincePrevious: stateDelta.within7DaysSincePrevious,
});
```

判断:

```markdown
- source あり
- comparison表示の集計は可能
- cardId はないが retention event としては許容
- 将来的には previous_comparison_view へ名称整理余地あり
```

#### favorite_click

```ts
track("favorite_click", {
  shrineId,
  ctx,
  tid,
  nextFav,
});
```

判断:

```markdown
- direct track のまま
- source がない
- cardId がない
- accessLevel がない
- visibility がない
- save_rate の補助指標としては使えるが、card別dashboard集計には弱い
- save domain helper 定義候補
```

#### thread_resume

```txt
apps/web/src/lib/analytics/retentionEvents.ts
```

判断:

```markdown
- RetentionAnalyticsEventName には存在する
- trackRetentionEvent("thread_resume") の発火箇所は未確認
- 現状では thread_resume rate は dashboard で実測できない
- ThreadListItem の既存thread選択時に発火候補
```

### KPI集計可能状態

| KPI | 必要event | 現状 | 判断 |
|---|---|---|---|
| comparison_view rate | premium_history_comparison_view | 実装あり | 集計可能 |
| premium_preview_to_checkout_rate | premium_preview_click → checkout_started | preview側は実装あり | billing側との接続確認が必要 |
| save_rate | save_prompt_click / favorite_click | 実装あり | favorite_click はpayload弱い |
| thread_resume rate | thread_resume / next_session | thread_resume 発火なし | 未計測 |

### 欠損・不足

| 項目 | 状態 | 対応候補 |
|---|---|---|
| thread_resume 発火 | なし | ThreadListItem クリック時に trackRetentionEvent を追加 |
| favorite_click source | なし | source: shrine_detail などを追加 |
| favorite_click cardId | なし | saved_record / shrine_save などを定義 |
| favorite_click helper | direct track | saveEvents.ts の必要性を判断 |
| premium_history_comparison_view 名称 | 実装済みだが長い | previous_comparison_view への整理を検討 |

### 現時点の判断

```markdown
- comparison_view rate は集計可能
- premium_preview_click は ConciergeResult / ShrineDetail の両方で集計可能
- save_prompt_click は集計可能
- favorite_click は保存行動としては使えるが、card analytics としては弱い
- thread_resume は型だけ存在し、未発火のため実測できない
```

### 次PR候補

```markdown
- [ ] thread_resume 発火箇所を ThreadListItem / thread選択導線に追加
- [ ] favorite_click を save domain helper に移行するか判断
- [ ] favorite_click に source / cardId / accessLevel を追加するか判断
- [ ] premium_history_comparison_view を previous_comparison_view に寄せるか判断
- [ ] dashboard集計前に source / cardId の必須条件を再確認する
```

### このPRでやらないこと

```markdown
- [ ] thread_resume の実装追加
- [ ] favorite_click の実装修正
- [ ] event名変更
- [ ] dashboard実装
- [ ] PostHog / GA 接続変更
```
- event 発火箇所の変更


## Direct Track Domain Audit

| event | file | domain | migration candidate | note |
|---|---|---|---|---|
| empty_state_view | apps/web/src/app/shrines/page.tsx | search | trackSearchEvent | 神社検索の空結果 |
| add_shrine_click | apps/web/src/app/shrines/page.tsx | search | trackSearchEvent | 未登録神社追加導線 |
| premium_history_click | ThreadList.tsx | retention | trackRetentionEvent | 履歴クリック |
| concierge_premium_preview_click | ConciergeSectionsRenderer.tsx | card | trackCardEvent | premium_preview_click へ統合候補 |
| concierge_result_impression | ConciergeSectionsRenderer.tsx | card | trackCardEvent | resultSetId を持つ表示event |
| concierge_result_click | ConciergeSectionsRenderer.tsx | card / search | trackCardEvent / trackSearchEvent | action別に分離候補 |
| premium_history_comparison_view | PremiumStateDeltaCard.tsx | retention | trackRetentionEvent | previous_comparison_view へ統合候補 |
| premium_history_comparison_click | PremiumStateDeltaCard.tsx | retention | trackRetentionEvent | comparison CTA |
| shrine_decision | ConciergeClientFull.tsx | search / action | trackSearchEvent | detail後の意思決定 |
| latest_event | track.test.ts | escape hatch | none | test用 |


## Analytics Helper File Structure

| file | responsibility | status |
|---|---|---|
| track.ts | low-level analytics pipeline / analyticsSessionId付与 | existing |
| providers.ts | provider abstraction / payload passthrough | existing |
| cardEvents.ts | card analytics schema / card payload serialize | existing |
| billing.ts | billing funnel analytics / billing payload serialize | existing |
| retentionEvents.ts | retention analytics schema / retention payload serialize | planned |
| searchEvents.ts | search analytics schema / search payload serialize | planned |
| cardCtr.ts | card CTR aggregation | existing |
| conciergeDecisionSummary.ts | concierge decision / session summary aggregation | existing |

## Concierge Result Click Domain Policy

### 目的

`concierge_result_click` の責務を整理し、  
card CTA / search transition / route action を混在させない。

推薦結果クリックは単なる card CTA ではなく、  
「推薦結果から神社詳細へ進んだ」遷移eventとして扱う。

### 現状

```ts
track("concierge_result_click", {
  action: "detail",
  position: "hero_primary" | "compact",
  rank: 1,
  shrineId: 123,
  firstClick: true
});
```

---

### 問題

- `card_cta_click` と責務が近い
- ただし推薦結果の詳細遷移という意味を持つ
- `resultSetId` は dedupe 判定には使われているが payload には含まれていない
- `threadId` が payload に含まれていない
- hero / compact の position 意味が event 名からは分からない

### 方針

| 現event | domain | 方針 |
|---|---|---|
| concierge_result_click | result / search | `shrine_detail_transition` へ移行候補 |
| card_cta_click | card | Premium / Save / UI CTA 用に維持 |
| route_open | map / search | 経路を見る導線用に別event候補 |

### 将来payload案

```ts
{
  event: "shrine_detail_transition",
  source: "concierge_result",
  threadId: "...",
  resultSetId: "...",
  shrineId: 123,
  recommendationRank: 1,
  position: "hero_primary" | "compact",
  firstClick: true
}
```



### 実装方針

- `cardEvents.ts` は継続利用する
- `billing.ts` は既存方針を維持する
- `retentionEvents.ts` を後続PRで追加する
- `searchEvents.ts` を後続PRで追加する
- helper file は domain 単位で分離する
- `track.ts` は低レベルpipelineとして残す


### このPRでやらないこと

- helper file の新規作成
- 既存 event の移行
- payload v2 の実装
- PostHog / GA 接続変更

---

## Direct Track Final Audit

### 目的

画面・component から直接呼ばれている `track()` を棚卸しし、  
domain helper へ移行する対象と、escape hatch として残す対象を分離する。

analytics は event を追加するより、  
野良 event を増やさないことの方が重要である。  
人類は「一旦 track だけ入れる」を覚えると、だいたい半年後に考古学を始める。

### 監査対象

テストコードを除外した direct `track()` / provider direct call を対象とする。

```bash
grep -R "track(\"\\|track('" apps/web/src -n | grep -v "__tests__" | grep -v ".test."
```

### 残存 direct track 一覧

| event | file | domain | 方針 | note |
|---|---|---|---|---|
| shrine_decision | apps/web/src/app/concierge/ConciergeClientFull.tsx | search / action | 後続整理 | 相談後の意思決定event。保存導線・詳細遷移と混在しないよう後続で確認する |
| empty_state_view | apps/web/src/app/shrines/page.tsx | search | `trackSearchEvent` 移行候補 | 神社検索の空結果 |
| add_shrine_click | apps/web/src/app/shrines/page.tsx | search | `trackSearchEvent` 移行候補 | 未登録神社追加導線 |
| posthog_health_check | apps/web/src/app/providers/ClientBootstrap.tsx | escape hatch | 残す | provider疎通確認のため direct provider call を許容 |
| premium_history_click | apps/web/src/features/concierge/components/ThreadList.tsx | retention | `trackRetentionEvent` 移行候補 | 履歴クリック / thread再開候補 |
| premium_history_comparison_view | apps/web/src/features/concierge/components/PremiumStateDeltaCard.tsx | retention | `trackRetentionEvent` 移行候補 | 前回比較表示 |
| premium_history_comparison_click | apps/web/src/features/concierge/components/PremiumStateDeltaCard.tsx | retention | `trackRetentionEvent` 移行候補 | 前回比較CTA |
| shrine_submission_complete | apps/web/src/features/shrine-submission/components/ShrineSubmissionForm.tsx | submission | 今回保留 | submission domain helper 未定義のため保留 |
| shrine_card_click | apps/web/src/components/shrines/ShrineCard.tsx | search / card | `trackSearchEvent` 移行候補 | 神社カードクリック |
| shrine_detail_view | apps/web/src/components/shrine/ShrineDetailViewTracker.tsx | search | `trackSearchEvent` 移行候補 | 神社詳細表示 |
| shrine_detail_premium_preview_click | apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx | card / premium | `trackCardEvent` 移行候補 | 神社詳細内Premium導線 |
| favorite_click | apps/web/src/components/shrine/ShrineSaveButton.tsx | save / action | 今回保留 | save domain helper 未定義のため保留 |
| shrine_decision | apps/web/src/components/shrine/ShrineSaveButton.tsx | search / action | 後続整理 | 保存操作後の意思決定event。`ConciergeClientFull.tsx` 側と重複確認が必要 |

### 分類方針

| 分類 | 方針 |
|---|---|
| search | `trackSearchEvent` へ移行する |
| retention | `trackRetentionEvent` へ移行する |
| card / premium | `trackCardEvent` へ移行する |
| billing | `trackBillingEvent` を使う |
| submission | helper 未定義のため今回は保留 |
| save / action | save domain の必要性を後続で判断する |
| escape hatch | provider疎通・debug・migration用途のみ残す |

### escape hatch として残すevent

| event | 理由 |
|---|---|
| posthog_health_check | provider疎通確認であり、domain event ではないため |

### 後続PR候補

```markdown
- [ ] search系 direct track を `trackSearchEvent` へ移行
- [ ] retention系 direct track を `trackRetentionEvent` へ移行
- [ ] shrine_detail_premium_preview_click を `trackCardEvent` へ移行
- [ ] save / favorite 系eventのdomainを定義
- [ ] submission domain helper の必要性を判断
- [ ] shrine_decision の責務を整理
```

### このPRでやらないこと

- direct `track()` の実装修正
- event名の変更
- provider実装の変更
- dashboard / aggregation の変更
- PostHog / GA 接続変更


---


## Retention / Save Schema Boundary

### 目的

dashboard aggregation 前提となる analytics schema の境界を固定する。

analytics event は送れているだけでは不十分であり、
「source別」「card別」「導線別」に集計できる状態である必要がある。

そのため、source / cardId / domain boundary の責務をここで固定する。

### thread_resume の発火タイミング

`thread_resume` は、既存threadをユーザーが選択して再開したときに発火する。

発火候補は `ThreadList.tsx` の `onSelect(idStr)` 直前とする。

### thread_resume の duplicate 条件

`thread_resume` は、現在選択中の thread を再クリックした場合は発火しない。

実装条件:

```ts
if (id === selectedId) return;
```

理由:

```markdown
- 同じthreadの再クリックを再開行動として扱わない
- thread_resume rate の過剰計測を防ぐ
- ユーザーが別の既存threadへ移動した場合のみ resume として扱う
```

### next_thread / thread_resume の境界

| event | 意味 | 発火候補 |
|---|---|---|
| next_thread | 新しい相談threadを開始した | `onCreateNew` 実行時 |
| thread_resume | 既存threadを選択して再開した | `onSelect(idStr)` 実行時 |

### save_prompt_click / favorite_click の境界

| event | 意味 | domain | 状態 |
|---|---|---|---|
| save_prompt_click | 保存したい意図 | card / save intent | `trackCardEvent` 管理済み |
| favorite_click | 神社保存/解除の実行 | save / action | direct track のまま |
| save_success | backend保存完了 | save | 後続候補 |

### source 必須ルール

以下のeventは dashboard aggregation 対象のため、`source` を必須とする。

| domain | event例 | source 必須理由 |
|---|---|---|
| card | premium_preview_click | Concierge / ShrineDetail の比較に必要 |
| card | save_prompt_click | 保存導線の画面別比較に必要 |
| retention | premium_history_comparison_view | comparison 表示元の識別に必要 |
| retention | thread_resume | 履歴再開導線の識別に必要 |
| billing | checkout_started | 課金導線の入口比較に必要 |
| search | shrine_detail_transition | 詳細遷移元の識別に必要 |

### cardId 必須対象

以下のeventは card analytics 対象のため、`cardId` を必須とする。

| event category | cardId |
|---|---|
| card_view | required |
| card_teaser_view | required |
| card_partial_view | required |
| card_cta_click | required |
| premium_preview_click | required |
| save_prompt_click | required |

### cardId を必須にしないevent

| event | 理由 |
|---|---|
| next_session | visit単位のretention event |
| next_thread | thread作成event |
| thread_resume | thread再開event |
| checkout_started | billing funnel event |
| checkout_success | billing funnel event |
| premium_active | billing status event |
| posthog_health_check | provider疎通確認 |

### dashboard aggregation 前提schema

```ts
{
  event: string;
  source: string;
  accessLevel?: string;
  cardId?: string;
  visibility?: string;
  threadId?: string;
  resultSetId?: string;
  shrineId?: number | string;
}
```

### aggregation key

初期dashboardでは、以下の key で集計できる状態を目標とする。

```txt
event
source
cardId
accessLevel
visibility
threadId
resultSetId
```

### dashboard 集計上の扱い

| event | 集計用途 | 注意 |
|---|---|---|
| premium_preview_click | Premium関心 / checkout導線 | source / cardId 必須 |
| save_prompt_click | 保存意図 | source / cardId 必須 |
| favorite_click | 保存操作 | 現状は補助event。source / cardId 欠損 |
| premium_history_comparison_view | comparison view rate | retention event。cardIdなし許容 |
| thread_resume | thread resume rate | 現状未発火。実装候補あり |

### 後続PR候補

```markdown
- [ ] thread_resume を ThreadList の既存thread選択時に発火する
- [ ] next_thread を新規相談開始時に発火するか判断する
- [ ] favorite_click に source を追加するか判断する
- [ ] favorite_click に cardId を追加するか判断する
- [ ] saveEvents.ts の必要性を判断する
- [ ] dashboard aggregation 側で source / cardId 欠損eventの扱いを決める
```

### このPRでやらないこと

```markdown
- [ ] event追加
- [ ] helper実装
- [ ] dashboard UI実装
- [ ] favorite_click 修正
- [ ] thread_resume 実装
- [ ] next_thread 実装
- [ ] PostHog / GA 接続変更
```
