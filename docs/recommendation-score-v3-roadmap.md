

# Recommendation Score v3 Roadmap

## 目的

Recommendation Score v3 を、いきなり本実装せず、行動・プロフィール・方位・参拝・振り返りの順に段階実装する。

推薦順位を大きく揺らすのではなく、既存の相談内容ベースの推薦を維持しながら、補助シグナルを安全に積み上げる。

---

## Phase1: Behavior Profile

### ゴール

軽い行動シグナルを推薦補助に使える状態にする。

### 対象シグナル

- save
- detail_view
- route_open

### 実装方針

- 行動ログから Behavior Profile を生成する
- visit_done / reflection_saved はここでは扱わない
- breakdown に behavior_signal を追加する
- スコア影響は中程度に留める

### 完了条件

- [ ] Behavior Profile の型を定義
- [ ] save / detail_view / route_open を集計
- [ ] behavior_signal を breakdown に追加
- [ ] concierge 系テストが通る

---

## Phase2: DerivedProfile

### ゴール

UserProfile から生成した派生プロフィールを、推薦補助シグナルとして安定利用する。

### 対象シグナル

- 九星気学
- 五行
- ライフパス

### 実装方針

- 既存の DerivedProfile を利用する
- 占術要素だけで順位を決めない
- profile_signal は最大 +0.03 程度に抑える

### 完了条件

- [ ] DerivedProfile を Recommendation Score v3 の入力に含める
- [ ] profile_signal の重みを明文化
- [ ] breakdown に profile_signal を保持
- [ ] concierge 系テストが通る

---

## Phase3: DirectionProfile

### ゴール

吉方位を補助シグナルとして扱える状態にする。

### 対象シグナル

- luckyDirection

### 実装方針

- DirectionProfile を Recommendation Score v3 の入力に含める
- 方位だけで順位を決めない
- 現時点では placeholder / 簡易計算を許容する
- スコア影響は最大 +0.01〜0.02 に抑える

### 完了条件

- [ ] DirectionProfile を Score v3 入力に含める
- [ ] direction_signal を breakdown に追加
- [ ] 方位情報がない神社では加点しない
- [ ] concierge 系テストが通る

---

## Phase4: visit_done

### ゴール

「実際に参拝した」行動を強い行動シグナルとして扱う。

### 対象シグナル

- visit_done

### 実装方針

- Behavior Profile とは分離する
- 参拝済み神社への過剰な再推薦を避ける
- 同じテーマで再訪に意味がある場合のみ補助する

### 完了条件

- [ ] visit_done を Action Profile として定義
- [ ] visit_signal を breakdown に追加
- [ ] 参拝済み神社の扱いを定義
- [ ] concierge 系テストが通る

---

## Phase5: reflection_saved

### ゴール

参拝後の振り返りを、行動変化の質として推薦に反映する。

### 対象シグナル

- reflection_saved

### 実装方針

- Reflection Profile として Behavior Profile から分離する
- reflection 内容の意味解析は別フェーズにする
- まずは保存有無をシグナル化する

### 完了条件

- [ ] reflection_saved を Reflection Profile として定義
- [ ] reflection_signal を breakdown に追加
- [ ] reflection 内容の解析は未実装として明示
- [ ] concierge 系テストが通る

---

## Phase6: Score v3 完成

### ゴール

User State Profile / Behavior Profile / DerivedProfile / DirectionProfile / Action Profile / Reflection Profile を統合した Recommendation Score v3 を完成させる。

### Score v3 入力

- User State Profile
- Behavior Profile
- DerivedProfile
- DirectionProfile
- Action Profile
- Reflection Profile

### 計算式ドラフト

```text
score_v3 =
  state_signal
  + history_signal
  + distance_signal
  + behavior_signal
  + profile_signal
  + direction_signal
  + action_signal
  + reflection_signal
```

### 実装方針

- User State Profile を主シグナルにする
- Behavior / Action / Reflection を行動学習として扱う
- DerivedProfile / DirectionProfile は補助シグナルに留める
- breakdown を必ず残し、順位変動の説明可能性を担保する

### 完了条件

- [ ] Score v3 の統合関数を実装
- [ ] breakdown に各シグナルを保持
- [ ] 既存推薦より大きく劣化しない
- [ ] concierge 系テストが通る
- [ ] 代表ケースで順位変動を確認

---

## やらないこと

- 占術だけで順位を決める
- 吉方位だけで順位を決める
- 人気ランキング化する
- 状態や人生を断定する
- 特定の神社を絶対視する
- breakdown なしでスコアを変更する

---

## 最終データフロー

```text
UserProfile
↓
DerivedProfile生成
↓
DirectionProfile生成
↓
ConciergeContext
↓
Recommendation Score v3
↓
推薦
↓
save / detail_view / route_open
↓
visit_done
↓
reflection_saved
↓
Behavior Profile 更新
↓
次回推薦
```
