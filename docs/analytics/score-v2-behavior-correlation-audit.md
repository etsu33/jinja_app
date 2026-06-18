

# Score V2 Behavior Correlation Audit

## 現状

### 保存元

- save → Favorite
- detail_view → ShrineInteractionLog(action_type=detail_view)
- route_open → ShrineInteractionLog(action_type=route_open)
- visit → Visit(status=added)
- reflection → ShrineReflection

### 集計元

behavior_funnel.py

- detail_view_count
- route_open_count
- save_count
- visit_count
- reflection_count
- save_to_visit_cvr
- visit_to_reflection_cvr

### score_v2

concierge_history.py

behavior_signal は以下から算出される。

- detail_view_signal
- route_open_signal
- save_signal
- visit_signal
- reflection_signal
- action_completed_signal

## 接続

### 行動ログ

Frontend
↓
ShrineInteractionLog / Favorite
↓
behavior_funnel.py
↓
concierge_history.py
↓
behavior_signal
↓
score_v2

### 現在確認できる接続

- detail_view → detail_view_signal
- route_open → route_open_signal
- save → save_signal
- visit → visit_signal
- reflection → reflection_signal

## 集計方針

### Phase1

score_v2 の重み変更は行わない。

まず現状の行動相関を観測する。

確認対象:

- save_rate
- detail_view_rate
- route_open_rate
- visit_rate
- reflection_rate

### Phase2

score_v2帯ごとの行動率を確認する。

例:

- score_v2 0〜2
- score_v2 2〜4
- score_v2 4〜6
- score_v2 6〜8
- score_v2 8〜10

観測対象:

- save率
- detail率
- route_open率
- visit率
- reflection率

### Phase3

行動率と score_v2 の相関を確認する。

- 高scoreほど保存されるか
- 高scoreほどルート表示されるか
- 高scoreほど参拝されるか
- 高scoreほど振り返りされるか

## 保留判断

### 今はやらない

- Behavior Signal重み変更
- Recommendation Score v2 の再設計
- 行動シグナル追加

### 保留理由

現状は観測データ不足。

先に

- score_v2
- save
- detail_view
- route_open
- visit
- reflection

の実測相関を確認する。

重み調整はその後に実施する。

---

## 次フェーズ

### ゴール

score_v2 と行動シグナルの実測相関を確認し、Behavior Signal の重みを変更する根拠を作る。

### 現在地

score_v2 の breakdown 観測は強化済み。

一方で、以下はまだ未確定である。

- score_v2 を実測データとしてどこから取得するか
- recommendation_log に score_v2 が保存されているか
- save / detail_view / route_open を score_v2 帯別に集計できるか

### 次の一手

```markdown
- [ ] score_v2実測データ取得方法を決定
- [ ] recommendation_logにscore_v2保存有無を確認
- [ ] save率集計SQL作成
- [ ] detail_view率集計SQL作成
- [ ] route_open率集計SQL作成
- [ ] score_v2帯別CVR監査
```

### 判断基準

Behavior Signal の重み変更は、以下のいずれかを確認してから行う。

- score_v2 が高い候補ほど save_rate が高い
- score_v2 が高い候補ほど detail_view_rate が高い
- score_v2 が高い候補ほど route_open_rate が高い
- 現在の behavior_contribution が CVR と明確にズレている

### 今回も保留するもの

```markdown
- [ ] Behavior Signal重み変更
- [ ] score_v2計算式の変更
- [ ] 推薦順位の変更
```

理由は、まだ実測相関を確認していないため。
