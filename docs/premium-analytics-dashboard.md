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

## Retention KPI 固定

### 目的

Premium の継続価値を、感覚ではなく dashboard 指標で確認できるようにする。

このdashboardでは、PVや単純なクリック数ではなく、以下を中心に見る。

```markdown
- 前回比較が見られているか
- 相談履歴が再開されているか
- 保存行動が起きているか
- Premium preview から checkout に進んでいるか
```

### Dashboard KPI

| KPI | 定義 | 分子 | 分母 | 主event | source |
|---|---|---|---|---|---|
| comparison_view rate | 前回比較が表示された割合 | `premium_history_comparison_view` | premium active session | `premium_history_comparison_view` | `state_delta_card` |
| thread_resume rate | 既存相談が再開された割合 | `thread_resume` | `next_session` | `thread_resume` | `thread_history` |
| save_rate | 保存導線が押された割合 | `save_prompt_click` / `favorite_click` | eligible view | `save_prompt_click` / `favorite_click` | `concierge_result` / `shrine_detail` |
| premium_preview_to_checkout_rate | Premium preview から checkout に進んだ割合 | `checkout_started` | `premium_preview_click` | `premium_preview_click` → `checkout_started` | `concierge_result` / `shrine_detail` |
| checkout_success_rate | checkout 開始後に成功した割合 | `checkout_success` | `checkout_started` | `checkout_started` → `checkout_success` | billing |
| premium_active_rate | checkout 成功後にPremium有効化した割合 | `premium_active` | `checkout_success` | `checkout_success` → `premium_active` | billing |

### KPIごとの判断用途

#### comparison_view rate

前回比較が Premium 価値として見られているかを確認する。

判断用途:

```markdown
- Premiumユーザーが「前回との違い」を見ているか
- Premiumの中心価値が comparison に寄っているか
- comparison card copy / 表示位置の改善余地があるか
```

#### thread_resume rate

相談履歴が、単なる過去ログではなく再開導線として機能しているかを確認する。

判断用途:

```markdown
- ユーザーが過去の相談に戻っているか
- 履歴が retention に寄与しているか
- thread list copy / resume導線を強化すべきか
```

#### save_rate

保存が「あとで見返す」行動につながっているかを確認する。

判断用途:

```markdown
- 相談結果や神社が記録対象として認識されているか
- 保存導線copyが機能しているか
- saved_record / save_prompt の改善余地があるか
```

#### premium_preview_to_checkout_rate

Premium preview への関心が checkout に進んでいるかを確認する。

判断用途:

```markdown
- Premium preview copy が課金意欲につながっているか
- ConciergeResult と ShrineDetail のどちらが課金導線として強いか
- source別に checkout_start_rate を比較する
```

### source / event 対応

| 領域 | source | 主event | 見るKPI |
|---|---|---|---|
| ConciergeResult | `concierge_result` | `premium_preview_click` / `save_prompt_click` | premium_preview_to_checkout_rate / save_rate |
| ShrineDetail | `shrine_detail` | `premium_preview_click` / `favorite_click` | premium_preview_to_checkout_rate / save_rate |
| Thread history | `thread_history` | `thread_resume` | thread_resume rate |
| State delta card | `state_delta_card` | `premium_history_comparison_view` | comparison_view rate |
| Billing | billing | `checkout_started` / `checkout_success` / `premium_active` | checkout_success_rate / premium_active_rate |

### 初期dashboardで見ないもの

初期dashboardでは、以下を中心指標にしない。

```markdown
- PV
- 単純な page view
- 神社詳細の閲覧数だけ
- Map / Search の利用数だけ
- 長文閲覧量
```

理由:

```markdown
Premium の価値は、神社情報の閲覧量ではなく、状態変化・保存・比較・再開にあるため。
```

### 実装前の確認条件

実装に進む前に以下を確認する。

```markdown
- premium_preview_click の source が concierge_result / shrine_detail で分かれている
- save_prompt_click と favorite_click の責務が分かれている
- thread_resume が既存thread再開時に発火する
- premium_history_comparison_view が comparison表示時に発火する
- checkout_started / checkout_success / premium_active が billing funnel として追える
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

### save_rate の正式定義

save_rate は「保存意図」または「保存実行」が発生した割合として扱う。

| source | 分子 | 分母 |
|---|---|---|
| concierge_result | save_prompt_click | save_prompt eligible view |
| shrine_detail | favorite_click | saved_record card_view |

### anonymous → free save conversion

anonymous の save_prompt_click 後に login / signup を経由し、同一 user または session で favorite_click が発生した割合を見る。

### shrine_decision taxonomy

| action | 意味 |
|---|---|
| save | 神社をあとで見返す対象として保存した |
| detail | 神社詳細へ進んだ |
| route | 経路確認へ進んだ |

### saveEvents.ts 判断

現時点では作らない。  
理由は save系eventがまだ少なく、direct track + schema補強で足りるため。


## Save → Premium Correlation

### 目的

保存行動が Premium 化の前兆になっているかを確認する。

### session内相関

初期dashboardでは、同一session内で以下の順序が発生したかを見る。

```txt
favorite_click
↓
premium_preview_click
↓
checkout_started
↓
premium_active
```

### KPI

| KPI | 分子 | 分母 | 条件 |
|---|---|---|---|
| favorite_to_premium_click_rate | favorite_click 後に premium_preview_click が発生した session | favorite_click が発生した session | same session |
| favorite_to_checkout_rate | favorite_click 後に checkout_started が発生した session | favorite_click が発生した session | same session |
| favorite_to_premium_active_rate | favorite_click 後に premium_active が発生した session | favorite_click が発生した session | same session |

### 注意

- 初期は同一session内だけを見る
- userId が安定して取得できる段階で 7日以内転換を見る
- event順序は favorite_click → premium_preview_click → checkout_started → premium_active を基本とする
- checkout_started が favorite_click より前にある session は、この相関指標から除外する
