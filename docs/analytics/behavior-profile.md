

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

## 責務分離

### ShrineInteractionLog

神社そのものに対する行動を保存する。

対象:

- detail_view
- route_open
- shrine_card_click

用途:

- 神社への興味・行動意図を見る
- Recommendation Score v2 の軽量な行動シグナルに使う

---

### Favorite

神社を保存した状態を表す。

対象:

- save

用途:

- 後で見返したい意思を表す
- detail_view より強い興味シグナルとして扱う

---

### Visit

神社へ行った自己申告を表す。

対象:

- visit_done

用途:

- 実際の行動に近い強いシグナルとして扱う

---

### ShrineReflection

参拝後・行動後の振り返りを表す。

対象:

- reflection_saved

用途:

- 行動後の変化・内省を表す最も強いシグナルとして扱う

---

### ActionEvent

神社そのものではなく、提案された小さな行動に対する反応を保存する。

対象:

- action_started
- action_completed

frontend 側の対応候補:

- action_suggestion_click → action_started
- action_done → action_completed

用途:

- 行動提案がユーザーの実行につながったかを見る
- ShrineInteractionLog とは混ぜず、Action Profile として別軸で扱う

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

| 状態 | 意味 |
|---|---|
| none | 行動なし |
| detail_viewed | 詳細を見た |
| route_opened | 経路を開いた |
| saved | 保存した |
| visited | 参拝・訪問を記録した |
| reflected | 振り返りを保存した |

---

## 現在の重み

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
|---|---:|
| 30日以内 | 1.0 |
| 90日以内 | 0.5 |
| 90日超 | 0.2 |

目的:

- 最近の行動を強く評価する
- 古い行動も完全には捨てない
- 一時的なクリックより、継続的な行動傾向を見やすくする

---

## Behavior Profile 定義

### Interest

ユーザーが神社に興味を持った状態。

対象:

- detail_view

評価:

- 弱いシグナル
- 回数と新しさで補正する

---

### Interest+

ユーザーが後で見返す意思を示した状態。

対象:

- save / favorite

評価:

- detail_view より強い興味
- ただし実際に行ったとは限らない

---

### Intent

ユーザーが神社へ行く可能性を示した状態。

対象:

- route_open

評価:

- 行動意図のシグナル
- save より弱い場合もあるが、実地行動に近い

---

### Action

ユーザーが提案された小さな行動を試そうとした、または完了した状態。

対象:

- action_started
- action_completed

評価:

- 神社そのものへの行動ではない
- Recommendation Score v2 へ直接混ぜる前に、Action Profile として別集計する

---

### Strong Action

ユーザーが神社へ行ったと記録した状態。

対象:

- visit_done

評価:

- 強い行動シグナル
- 自己申告だが、route_open より実行に近い

---

### Transformation

ユーザーが行動後の変化や振り返りを保存した状態。

対象:

- reflection_saved

評価:

- 最も強いシグナル
- 神社提案が意味ある体験につながった可能性が高い

---

## ActionEvent の接続方針

現状:

- backend に ActionEvent model / migration / API / test は存在する
- frontend から `/api/action-events/` を叩く wrapper は未実装
- PostHog の `action_suggestion_click` / `action_done` は送信済み

接続候補:

| frontend event | backend ActionEvent |
|---|---|
| action_suggestion_click | action_started |
| action_done | action_completed |

注意:

- ActionEvent API は認証必須
- 未ログインユーザーは backend 保存できない
- PostHog は未ログインも含めた分析用として残す
- ActionEvent は永続化用として使う

---

## Recommendation Score v2 への接続方針

現時点では、Recommendation Score v2 の主軸は以下に限定する。

- ShrineInteractionLog
- Favorite
- Visit
- ShrineReflection

ActionEvent はすぐに混ぜない。

理由:

- ShrineInteractionLog は神社への行動
- ActionEvent は提案行動への行動
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
