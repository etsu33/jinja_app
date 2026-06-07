# Behavior Profile

## 目的

Behavior Profile は、ユーザーが神社提案に対してどの程度行動したかを整理するための行動シグナル定義である。

この設計では、単なる閲覧数ではなく、以下の流れを評価する。

```text
興味
↓
意思
↓
行動
↓
変化
```

Recommendation Score v2 では、この行動シグナルを使って、ユーザーにとって再提案価値のある神社を判断しやすくする。

---

## 前提

Behavior Profile は、神社そのものへの行動と、行動提案への反応を分けて扱う。

```text
Shrine Behavior
= 神社候補に対する行動

Action Profile
= 提案された小さな行動に対する反応
```

現時点で Recommendation Score v2 に直接入るのは Shrine Behavior のみである。

ActionEvent は、backend に model / API / test は存在するが、frontend からの永続化接続は未実装である。

---

## 責務分離

### ShrineInteractionLog

神社そのものに対する軽量な行動を保存する。

対象:

- detail_view
- route_open
- shrine_card_click

保存先:

```text
POST /api/shrine-interactions/
```

frontend wrapper:

```text
apps/web/src/lib/api/shrineInteractions.ts
```

用途:

- 神社への興味・行動意図を見る
- Recommendation Score v2 の軽量な行動シグナルに使う

注意:

- `detail_view` と `route_open` は `calculate_shrine_behavior_signal_v2` に入る
- `shrine_card_click` は現時点では action_state 判定・behavior_signal には入らない

---

### Favorite

神社を保存した状態を表す。

対象:

- save / favorite

保存先:

```text
Favorite model
```

用途:

- 後で見返したい意思を表す
- detail_view より強い興味シグナルとして扱う
- `classify_shrine_action_state` では `saved` として扱う

注意:

- 保存は実地行動ではない
- ただし再訪・比較・課金導線につながる強い興味として扱う

---

### Visit

神社へ行った自己申告を表す。

対象:

- visit_done

保存先:

```text
POST /api/shrines/{shrineId}/visit
```

frontend wrapper:

```text
apps/web/src/lib/api/visits.ts
```

frontend PostHog event:

```text
visit_done
```

用途:

- 実際の行動に近い強いシグナルとして扱う
- `classify_shrine_action_state` では `visited` として扱う

注意:

- 自己申告であり、実際の参拝を保証するものではない
- それでも `route_open` より行動に近いシグナルとして扱う

---

### ShrineReflection

参拝後・行動後の振り返りを表す。

対象:

- reflection_saved

保存先:

```text
POST /api/shrines/{shrineId}/reflection
```

frontend wrapper:

```text
apps/web/src/lib/api/reflections.ts
```

frontend PostHog event:

```text
reflection_prompt_view
reflection_saved
```

保存される主な項目:

- history_theme
- prompt
- answer
- mood_before
- mood_after

用途:

- 行動後の変化・内省を表す最も強いシグナルとして扱う
- `classify_shrine_action_state` では `reflected` として扱う

注意:

- 振り返りは体験の深さを示す
- Recommendation Score v2 では最も強い行動シグナルとして扱う

---

### ActionEvent

神社そのものではなく、提案された小さな行動に対する反応を保存する。

対象:

- action_started
- action_completed

backend endpoint:

```text
POST /api/action-events/
```

frontend 側の対応候補:

| frontend event | backend ActionEvent |
|---|---|
| action_suggestion_click | action_started |
| action_done | action_completed |

用途:

- 行動提案がユーザーの実行につながったかを見る
- ShrineInteractionLog とは混ぜず、Action Profile として別軸で扱う

注意:

- ActionEvent API は認証必須
- 未ログインユーザーは backend 保存できない
- 現時点では frontend wrapper が未実装
- PostHog の `action_suggestion_click` / `action_done` は送信済み
- Recommendation Score v2 にはまだ直接混ぜない

---

## DB保存とPostHog送信の整理

| 行動 | DB保存 | PostHog | 主な用途 |
|---|---|---|---|
| detail_view | ShrineInteractionLog | shrine_detail_view | 興味 |
| route_open | ShrineInteractionLog | route_open | 行動意図 |
| save | Favorite | save系イベント | 後で見返す意思 |
| visit_done | Visit | visit_done | 実地行動に近い自己申告 |
| reflection_saved | ShrineReflection | reflection_saved | 行動後の変化 |
| action_suggestion_click | 未接続 | action_suggestion_click | 行動提案への興味 |
| action_done | 未接続 | action_done | 行動提案の完了自己申告 |

方針:

```text
DB保存
= Recommendation Score v2 / 再提案 / 個別ユーザー履歴に使う

PostHog
= ファネル分析 / 未ログイン含む行動傾向分析に使う
```

---

## 現在の行動状態分類

`classify_shrine_action_state` では、以下の優先順位で状態を分類している。

```text
reflected
↓
visited
↓
saved
↓
route_opened
↓
detail_viewed
↓
none
```

意味:

| 状態 | 意味 | 判定元 |
|---|---|---|
| none | 行動なし | 該当レコードなし |
| detail_viewed | 詳細を見た | ShrineInteractionLog.detail_view |
| route_opened | 経路を開いた | ShrineInteractionLog.route_open |
| saved | 保存した | Favorite |
| visited | 参拝・訪問を記録した | Visit(status="added") |
| reflected | 振り返りを保存した | ShrineReflection |

---

## action_state 状態遷移図

代表的な遷移は以下。

```text
none
↓
detail_viewed
↓
route_opened
↓
saved
↓
visited
↓
reflected
```

ただし実際のユーザー行動は必ずこの順番ではない。

例:

```text
none → saved
none → route_opened
saved → reflected
route_opened → visited
visited → reflected
```

`classify_shrine_action_state` は時系列ではなく、存在する行動の中で最も強い状態を返す。

つまり、過去に `detail_view` があっても `ShrineReflection` が存在すれば `reflected` になる。

---

## behavior_signal の現行重み

`calculate_shrine_behavior_signal_v2` の現行重み。

| イベント | レイヤー | 重み |
|---|---|---:|
| detail_view | Interest | 0.2 × 回数 × recency |
| route_open | Intent | 0.6 × 回数 × recency |
| save / favorite | Interest+ | 1.5 × recency |
| visit_done | Strong Action | 3.0 × recency |
| reflection_saved | Transformation | 4.0 × recency |

上限:

```text
10.0
```

---

## Recency multiplier

行動の新しさを以下で補正する。

| 期間 | multiplier |
|---|---|
| 30日以内 | 1.0 |
| 90日以内 | 0.5 |
| 90日超 | 0.2 |

目的:

- 最近の行動を強く評価する
- 古い行動も完全には捨てない
- 一時的なクリックより、継続的な行動傾向を見やすくする

---

## behavior_signal の意味

`behavior_signal` は、その神社に対するユーザー行動の強さを 0.0 から 10.0 で表す。

```text
behavior_signal
= detail_view
+ route_open
+ favorite
+ visit
+ reflection
```

ただし、Recommendation Score v2 に入るときは直接足し込まれない。

`concierge_chat_ranking.py` では以下のように扱う。

```text
behavior_contribution = behavior_signal × 0.1
```

さらに、行動の影響が強くなりすぎないように以下で制限する。

```text
behavior_cap = score_total_ranked_base × 0.3
capped_behavior_contribution = min(behavior_contribution, behavior_cap)
```

方針:

- 行動履歴は推薦を補助する
- 相談内容や神社意味より強くしすぎない
- 行動履歴だけで順位が逆転しすぎないようにする

---

## Behavior Profile 定義

### Interest

ユーザーが神社に興味を持った状態。

対象:

- detail_view

評価:

- 弱いシグナル
- 回数と新しさで補正する
- クリックだけなので過信しない

---

### Interest+

ユーザーが後で見返す意思を示した状態。

対象:

- save / favorite

評価:

- detail_view より強い興味
- ただし実際に行ったとは限らない
- 課金導線・継続利用との相関を確認する価値が高い

---

### Intent

ユーザーが神社へ行く可能性を示した状態。

対象:

- route_open

評価:

- 行動意図のシグナル
- save より弱い場合もあるが、実地行動に近い
- route_open 後の visit_done 率を見ることで質を検証する

---

### Action

ユーザーが提案された小さな行動を試そうとした、または完了した状態。

対象:

- action_started
- action_completed

評価:

- 神社そのものへの行動ではない
- Recommendation Score v2 へ直接混ぜる前に、Action Profile として別集計する
- action_done は自己申告なので、Reflection とは分けて扱う

---

### Strong Action

ユーザーが神社へ行ったと記録した状態。

対象:

- visit_done

評価:

- 強い行動シグナル
- 自己申告だが、route_open より実行に近い
- reflection_saved への導線開始点として扱う

---

### Transformation

ユーザーが行動後の変化や振り返りを保存した状態。

対象:

- reflection_saved

評価:

- 最も強いシグナル
- 神社提案が意味ある体験につながった可能性が高い
- mood_before / mood_after / answerLength を分析すれば質的変化を見られる

---

## Recommendation Score v2 の Behavior Layer

現時点では、Recommendation Score v2 の Behavior Layer は以下に限定する。

- ShrineInteractionLog.detail_view
- ShrineInteractionLog.route_open
- Favorite
- Visit(status="added")
- ShrineReflection

ActionEvent はすぐに混ぜない。

理由:

- ShrineInteractionLog / Favorite / Visit / ShrineReflection は神社そのものへの行動
- ActionEvent は提案行動への反応
- 同じスコアに混ぜると、神社への関心と行動提案への反応が混線する

暫定方針:

```text
Recommendation Score v2
= 神社への行動シグナル

Action Profile
= 提案行動への行動シグナル
```

将来的には、Action Profile を補助スコアとして Recommendation Score v2 に接続する。

---

## Behavior Layer の制約

### 1. 未ログイン行動はDB保存されない場合がある

PostHog には残るが、Recommendation Score v2 に使う個別ユーザー履歴には入らない。

影響:

- 未ログインユーザーの関心は再提案に反映しづらい
- ログイン後の履歴統合は別設計が必要

---

### 2. visit_done は自己申告である

実際に参拝したことを保証するものではない。

ただし、ユーザーが「行った」と記録した行動は、route_open より強い意図として扱う価値がある。

---

### 3. reflection_saved は最強シグナルだが母数が少ない

reflection_saved は深い行動だが、入力負荷があるため母数は少なくなりやすい。

そのため、重みは高くしつつ、PostHog では以下を見る。

- visit_done → reflection_prompt_view
- reflection_prompt_view → reflection_saved
- reflection_saved 後の再相談率

---

### 4. 行動履歴は相談内容を上書きしない

Behavior Layer は補助であり、User State Match / Shrine Meaning Match を上書きしすぎない。

現行では、behavior contribution に 30% cap があるため、この制約はコード上にも反映されている。

---

## PostHogで見るべきファネル

### 神社行動ファネル

```text
shrine_detail_view
↓
route_open
↓
visit_done
↓
reflection_saved
```

見る指標:

- detail_view → route_open CVR
- route_open → visit_done CVR
- visit_done → reflection_saved CVR
- detail_view → reflection_saved CVR

---

### 保存起点ファネル

```text
shrine_detail_view
↓
save
↓
visit_done / reflection_saved
```

見る指標:

- detail_view → save CVR
- save → route_open CVR
- save → visit_done CVR
- save → premium_preview / checkout との相関

---

### 行動提案ファネル

```text
action_suggestion_view
↓
action_suggestion_click
↓
action_done
```

見る指標:

- view → click CVR
- click → done CVR
- action_done → visit_done との相関
- action_done → reflection_saved との相関

注意:

ActionEvent が frontend 接続されるまでは、PostHog が主な分析元になる。

---

## 次PR候補

### PR1: frontend ActionEvent API wrapper追加

目的:

- frontend から `/api/action-events/` を呼べるようにする

TODO:

- [ ] apps/web/src/lib/api/actionEvents.ts を作成
- [ ] action_started 保存APIを実装
- [ ] action_completed 保存APIを実装
- [ ] APIテストを追加

---

### PR2: ConciergeTopRecommendationHero と ActionEvent API 接続

目的:

- action_suggestion_click / action_done を backend に永続化する

TODO:

- [ ] action_suggestion_click 時に action_started を保存
- [ ] action_done 時に action_completed を保存
- [ ] 未ログイン時はPostHogのみ送信
- [ ] 保存失敗時もUIを壊さない
- [ ] frontend test を追加

---

### PR3: Action Profile 集計サービス追加

目的:

- ActionEvent を集計し、行動提案の有効性を見る

TODO:

- [ ] action_started_count
- [ ] action_completed_count
- [ ] action_completion_rate
- [ ] history_theme別 completion rate
- [ ] action_category別 completion rate

---

### PR4: Recommendation Score v2 補助接続

目的:

- Action Profile を推薦改善の補助材料として使う

TODO:

- [ ] ActionEvent を直接スコアに混ぜるか検討
- [ ] Action Profile を別スコアとして保持するか検討
- [ ] save / route_open / visit_done / reflection_saved との相関を見る
- [ ] 過学習を避けるため、初期重みは低めに設定する

---

## 未確定事項

- action_completed を Recommendation Score v2 に直接加算するか
- action_started と action_completed の重みをどうするか
- 未ログインユーザーの ActionEvent を匿名保存するか
- action_done 後に reflection 導線を出すか
- PostHog と DB の集計差分をどう扱うか
- save / route_open / visit_done / reflection_saved の重みをPostHog実データでどう補正するか

---

## 現時点の判断

Behavior Profile は、現段階では以下で十分。

```text
detail_view
route_open
save / favorite
visit_done
reflection_saved
```

ActionEvent は重要だが、Recommendation Score v2 にはまだ直接入れない。

まずは以下の分離を維持する。

```text
Shrine Behavior
= 神社そのものへの行動

Action Profile
= 行動提案への反応
```

これにより、Recommendation Score v2 は以下の構造を維持できる。

```text
User State Match
+ Shrine Meaning Match
+ Context Match
+ Behavior Signal
```
