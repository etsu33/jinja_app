

# Card CTR Aggregation 設計

最終更新: 2026-05-18  
対象: card analytics / premium funnel / CTR aggregation

---

## 目的

card analytics から、Premium 化に寄与している表示ブロックを判定できるようにする。

このPRでは dashboard UI は作らず、以下を固定する。

```markdown
- 集計対象event
- group by条件
- CTR計算式
- 除外条件
- dashboard実装前の確認項目
```

---

## ゴール

### ゴール

どの card が Premium click に効いているかを比較できる状態にする。

### 現在地

card visibility event は整備され始めている。

```markdown
- card_view
- card_partial_view
- card_teaser_view
```

Premium click / billing funnel event も存在する。

```markdown
- premium_preview_click
- checkout_started
- checkout_success
- premium_active
```

### 次の一手

```markdown
- event を source / cardId / visibility ごとに集計する
- card visibility event と premium click event を接続する
- CTRを出すための分母と分子を固定する
```

---

## 集計対象event

### 分母event

card が表示されたことを表す event。

```markdown
- card_view
- card_partial_view
- card_teaser_view
```

### 分子event

Premium への関心を表す click event。

```markdown
- premium_preview_click
- concierge_premium_preview_click
- shrine_detail_premium_preview_click
- save_prompt_click
```

### funnel event

Premium 購入導線の後続step。

```markdown
- checkout_started
- checkout_success
- premium_active
```

---

## 除外event

以下は CTR の直接分子にはしない。

```markdown
- shrine_detail_view
- concierge_result_impression
- favorite_click
- shrine_decision
- save_prompt_view
```

理由:

```markdown
- page view は card 単位ではない
- impression は card visibility と粒度が違う
- favorite_click は保存意図であり、Premium click ではない
- shrine_decision は行動決定であり、課金関心とは別軸
- save_prompt_view は表示eventなので分母側
```

---

## group by条件

最低限、以下で group by する。

```markdown
- source
- cardId
- visibility
- accessLevel
```

可能であれば追加する。

```markdown
- sessionId
- shrineId
- recommendationRank
- mode
- ctaType
```

---

## source定義

### ConciergeResult

```markdown
source: concierge_result
```

対象card:

```markdown
- consultation_summary
- shrine_meaning
- action_meaning
- previous_comparison
- history_shift
- deep_reflection
- premium_preview
- save_prompt
- shrine_hero
- shrine_compact
- other_shrines
```

### ShrineDetail

```markdown
source: shrine_detail
```

対象card:

```markdown
- context_reason
- personal_meaning
- saved_record
```

---

## CTR計算式

### card CTR

```txt
card_ctr = premium_click_count / card_view_count
```

### partial CTR

```txt
partial_ctr = premium_click_count / card_partial_view_count
```

### teaser CTR

```txt
teaser_ctr = premium_click_count / card_teaser_view_count
```

### combined visibility CTR

表示種別をまとめて見る場合。

```txt
combined_ctr = premium_click_count / (card_view_count + card_partial_view_count + card_teaser_view_count)
```

---

## funnel計算式

### click → checkout

```txt
checkout_start_rate = checkout_started / premium_click_count
```

### checkout → success

```txt
checkout_success_rate = checkout_success / checkout_started
```

### success → active

```txt
premium_active_rate = premium_active / checkout_success
```

### visibility → active

```txt
card_to_premium_active_rate = premium_active / card_visibility_count
```

---

## card別CTR table設計

| source | cardId | visibility | card visibility count | premium click count | CTR |
|---|---|---|---:|---:|---:|
| concierge_result | premium_preview | teaser | 0 | 0 | 0% |
| concierge_result | save_prompt | visible | 0 | 0 | 0% |
| shrine_detail | context_reason | partial | 0 | 0 | 0% |
| shrine_detail | personal_meaning | teaser | 0 | 0 | 0% |
| shrine_detail | saved_record | visible | 0 | 0 | 0% |

---

## 集計ロジック案

### 入力

analytics event の配列。

```ts
type AnalyticsEvent = {
  event: string;
  source?: string | null;
  cardId?: string | null;
  visibility?: string | null;
  accessLevel?: string | null;
  sessionId?: string | null;
  shrineId?: number | null;
  createdAt?: string | null;
};
```

### 出力

```ts
type CardCtrRow = {
  source: string;
  cardId: string;
  visibility: string;
  accessLevel: string;
  cardVisibilityCount: number;
  premiumClickCount: number;
  ctr: number;
};
```

---

## 集計単位

初期は session 単位ではなく event count で見る。

理由:

```markdown
- 実装が簡単
- event 欠損確認に向いている
- baseline CTR を取りやすい
```

ただし、次段階では session 単位でも見る。

```markdown
- 同一sessionで card を見たか
- 同一sessionで premium click したか
- 同一sessionで checkout_started したか
```

---

## 初期実装方針

### Phase 1

```markdown
- docsで定義を固定する
- dashboard UIは作らない
- favorite相関は次PRへ分離する
```

### Phase 2

```markdown
- analytics event の保存先を確認する
- ローカル集計関数を作るか判断する
- PostHog / GA で見るか判断する
```

### Phase 3

```markdown
- dashboard UI を作る
- card別CTRを表示する
- funnelを表示する
```

---

## dashboard UIをまだ作らない理由

```markdown
- event保存先が未確定の可能性がある
- まず event 定義と group by を固定する必要がある
- UIを先に作ると、後で集計式変更に巻き込まれる
```

---

## favorite相関を次PRへ分離する理由

favorite は Premium click とは別の行動意図である。

```markdown
favorite_click
↓
premium_preview_click
↓
checkout_started
↓
premium_active
```

この流れを見るには sessionId / userId / 時間窓が必要になる。

そのため、card別CTRとは別PRで扱う。

---

## 検証KPI

### 最初に見るKPI

```markdown
- card_partial_view → premium click CTR
- card_teaser_view → premium click CTR
- premium_preview_click → checkout_started rate
```

### 判断基準

```markdown
- partial CTR が低い場合: 見せ方が弱い可能性
- teaser CTR が低い場合: 文言が弱い可能性
- checkout_start_rate が低い場合: click 後の価格 / 価値説明が弱い可能性
```

---

## 次PR候補

### 候補A: analytics event 保存先確認

```markdown
- [ ] PostHog / GA / local console のどこで見るか確認
- [ ] event payload の欠損を確認
- [ ] source / cardId / visibility / accessLevel が揃っているか確認
```

### 候補B: card CTR aggregation helper

```markdown
- [ ] CardCtrRow 型を定義
- [ ] aggregateCardCtr 関数を作る
- [ ] event配列から card別CTRを算出する
- [ ] unit test を追加する
```

### 候補C: favorite → premium 相関確認

```markdown
- [ ] favorite_click 後の premium_preview_click を確認
- [ ] checkout_started まで確認
- [ ] premium_active まで確認
```

---

## TODO

```markdown
- [x] 集計対象eventを固定
- [x] group by条件を固定
- [x] CTR計算式を実装前提で整理
- [x] dashboard UIはまだ作らない
- [x] favorite相関は次PRへ分離
```
