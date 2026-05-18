

# Premium Analytics Dashboard 設計

最終更新: 2026-05-18  
対象: Premium / card analytics / funnel / CTR / favorite correlation

---

## 目的

Premium への関心がどこで発生しているかを確認するため、
card analytics と billing funnel をつなぐ dashboard の設計を固定する。

このPRでは実装を増やさず、以下を定義する。

```markdown
- card別CTR
- Premium funnel
- favorite → premium 相関
- ABテストを始める前の確認条件
```

---

## 前提

すでに以下の card visibility / analytics が整備され始めている。

```markdown
- context_reason
- personal_meaning
- saved_record
- premium_preview
- save_prompt
- consultation_summary
- shrine_meaning
- action_meaning
- previous_comparison
- history_shift
- deep_reflection
```

ShrineDetail 側では以下を source とする。

```markdown
source: shrine_detail
```

ConciergeResult 側では以下を source とする。

```markdown
source: concierge_result
```

---

## dashboard のゴール

### ゴール

Premium 化に効いている表示ブロックを特定する。

### 見たいこと

```markdown
- どの card が見られているか
- どの card の partial / teaser がクリックにつながるか
- どの導線が checkout に進むか
- favorite 行動が premium 化と関係しているか
- ABテストを始める前に十分な計測があるか
```

---

## event分類

### card visibility event

```markdown
- card_view
- card_partial_view
- card_teaser_view
```

### premium click event

```markdown
- premium_preview_click
- save_prompt_click
- shrine_detail_premium_preview_click
- concierge_premium_preview_click
```

### billing funnel event

```markdown
- checkout_started
- checkout_success
- premium_active
```

### behavior event

```markdown
- favorite_click
- shrine_decision
- save_prompt_view
- save_prompt_click
```

---

## card別CTR定義

### 基本式

```txt
card CTR = premium_click_count / card_view_count
```

ただし partial / teaser は別で見る。

```txt
partial CTR = premium_click_count / card_partial_view_count
teaser CTR = premium_click_count / card_teaser_view_count
```

---

## card別に見る指標

| cardId | view event | click event | KPI |
|---|---|---|---|
| context_reason | card_view / card_partial_view | premium preview click | partial → click |
| personal_meaning | card_view / card_partial_view | premium preview click | teaser → click |
| premium_preview | card_teaser_view | premium_preview_click | teaser CTR |
| save_prompt | save_prompt_view | save_prompt_click | save CTR |
| saved_record | card_view | favorite_click | save intent |
| previous_comparison | card_view | premium_preview_click | comparison interest |
| history_shift | card_view | premium_preview_click | retention interest |
| deep_reflection | card_view | premium_preview_click | deep reflection interest |

---

## funnel定義

### Premium funnel

```txt
card_view / card_partial_view / card_teaser_view
↓
premium_preview_click
↓
checkout_started
↓
checkout_success
↓
premium_active
```

### 見るべきCVR

```txt
premium_click_rate = premium_preview_click / card_visibility_event
checkout_start_rate = checkout_started / premium_preview_click
checkout_success_rate = checkout_success / checkout_started
premium_active_rate = premium_active / checkout_success
```

---

## source別 funnel

### ConciergeResult

```markdown
source: concierge_result
```

見るもの:

```markdown
- consultation_summary
- shrine_meaning
- action_meaning
- previous_comparison
- history_shift
- deep_reflection
- premium_preview
- save_prompt
```

### ShrineDetail

```markdown
source: shrine_detail
```

見るもの:

```markdown
- context_reason
- personal_meaning
- saved_record
```

---

## favorite → premium 相関

### 目的

保存行動が Premium 化の前兆になっているかを確認する。

### 仮説

```markdown
favorite_click したユーザーは、premium_preview_click / checkout_started に進みやすい
```

### 確認条件

```markdown
- favorite_click がある session / user
- その後 premium_preview_click があるか
- その後 checkout_started があるか
- その後 premium_active まで到達するか
```

### 見る指標

```txt
favorite_to_premium_click_rate = premium_preview_click_after_favorite / favorite_click
favorite_to_checkout_rate = checkout_started_after_favorite / favorite_click
favorite_to_premium_active_rate = premium_active_after_favorite / favorite_click
```

### 注意

```markdown
- 同一session内だけで見るか、一定期間内で見るかを分ける
- 初期は同一session内で確認する
- userId が使える場合は7日以内の転換も見る
```

---

## ABテスト前の確認条件

teaser copy / partial UI の ABテストは、以下を確認してから行う。

```markdown
- card_view / card_partial_view が一定数ある
- premium_preview_click が計測できている
- checkout_started が計測できている
- source / cardId / accessLevel が欠損していない
- 既存UIの baseline CTR が取れている
```

---

## teaser copy ABテスト方針

### 目的

Premium誘導文言の反応差を見る。

### 対象

```markdown
- premium_preview
- personal_meaning teaser
- action_meaning teaser
```

### まだやらないこと

```markdown
- このPRで copy を変更しない
- このPRで AB variant を実装しない
- このPRで実験割り当てロジックを作らない
```

---

## partial UI ABテスト方針

### 目的

partial の見せ方が Premium click に影響するかを見る。

### 比較候補

```markdown
A: 1 block だけ見せる
B: summary だけ見せる
C: 途中まで表示して teaser を置く
D: 全文は見せず、価値予告だけにする
```

### まだやらないこと

```markdown
- このPRで UI を変更しない
- このPRで blur 表示を追加しない
- このPRで variant を実装しない
```

---

## dashboard 初期ビュー

### View 1: card performance

```markdown
- source
- cardId
- visibility
- card_view count
- card_partial_view count
- card_teaser_view count
- premium_preview_click count
- CTR
```

### View 2: funnel

```markdown
- premium_preview_click
- checkout_started
- checkout_success
- premium_active
- 各step CVR
```

### View 3: favorite correlation

```markdown
- favorite_click count
- favorite後 premium_preview_click count
- favorite後 checkout_started count
- favorite後 premium_active count
```

---

## 実装を増やさない制約

このPRでは以下を行わない。

```markdown
- [ ] dashboard UI を作らない
- [ ] PostHog / GA の設定を変更しない
- [ ] ABテストを実装しない
- [ ] teaser copy を変更しない
- [ ] partial UI を変更しない
- [ ] event schema を変更しない
```

---

## 次PR候補

### 候補A: card別CTR集計の実装

```markdown
- [ ] analytics event を集計する方法を決める
- [ ] cardId / source / visibility ごとに集計する
- [ ] baseline CTR を確認する
```

### 候補B: favorite → premium 相関確認

```markdown
- [ ] favorite_click 後の premium_preview_click を確認
- [ ] checkout_started まで追う
- [ ] premium_active まで追う
```

### 候補C: teaser copy ABテスト設計

```markdown
- [ ] variant A / B の copy を作る
- [ ] 割り当て単位を決める
- [ ] 成功指標を決める
```

### 候補D: partial UI ABテスト設計

```markdown
- [ ] partial 表示パターンを定義
- [ ] 表示差分を最小化する
- [ ] 成功指標を決める
```

---

## TODO

```markdown
- [x] card別CTR定義を作成
- [x] funnel定義を作成
- [x] favorite → premium 相関の確認条件を定義
- [x] teaser copy ABテストは次PRへ分離
- [x] partial UI ABテストは次PRへ分離
- [x] 実装はまだ増やさない
```
