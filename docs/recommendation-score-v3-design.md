# Recommendation Score v3 Design

## 1. 目的

Kamimusubi の推薦を「人気順」ではなく、

- ユーザーの現在の状態
- 行動履歴
- プロフィール情報
- 振り返り結果

を総合して評価する。

順位の大幅な変動ではなく、
「今のその人に合いやすい順」に補正することを目的とする。

---

## 2. User State Profile

現在の相談内容から生成される状態。

例：

- needPrimary
- needTags
- historyTheme
- mood
- consultationTheme

最も重要なシグナル。

重み：

40〜50%

---

## 3. Behavior Profile

実際の行動から生成するプロフィール。

対象：

- save
- detail_view
- route_open

目的：

「言葉」より「行動」を重視する。

軽い行動シグナルとして利用する。

重み：

20〜30%

---

## 4. DerivedProfile Signal

UserProfileから生成される補助プロフィール。

対象：

- 九星気学
- 五行
- ライフパス

役割：

補助シグナル。

順位を大きく変えない。

重み：

0〜5%

---

## 5. DirectionProfile Signal

吉方位プロフィール。

対象：

- luckyDirection

役割：

補助シグナル。

重み：

0〜2%

---

## 6. visit_done の扱い

参拝完了は強い行動シグナル。

目的：

「興味」ではなく「実際に行った」を学習する。

重み：

10〜15%

状態例：

- 未参拝
- 参拝済み

---

## 7. reflection_saved の扱い

振り返りを保存した場合。

目的：

行動変化の質を学習する。

重み：

10〜15%

状態例：

- reflectionなし
- reflectionあり

---

## 8. Score v3 計算式ドラフト

score_v3

=

need_signal

+

history_signal

+

distance_signal

+

behavior_signal

+

profile_signal

+

direction_signal

+

visit_signal

+

reflection_signal

イメージ：

score_v3 =
0.45 × User State Profile
+ 0.25 × Behavior Profile
+ 0.10 × History Signal
+ 0.10 × Distance Signal
+ 0.05 × DerivedProfile
+ 0.02 × DirectionProfile
+ 0.02 × Visit
+ 0.01 × Reflection

---

## 9. 実装フェーズ分割

### Phase1

Behavior Profile

- save
- detail_view
- route_open

### Phase2

Profile Signal

- 九星気学
- 五行
- ライフパス

### Phase3

Direction Profile

- 吉方位

### Phase4

Action Signal

- visit_done

### Phase5

Reflection Signal

- reflection_saved

### Phase6

Recommendation Score v3 完成

---

## 10. やらないこと

- 占術だけで順位を決める
- 方位だけで順位を決める
- 人気ランキング化する
- 状態を断定する
- 人生を断定する
- 特定の神社を絶対視する

## 11. データフロー

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
visit_done
↓
reflection_saved
↓
Behavior更新
↓
次回推薦
