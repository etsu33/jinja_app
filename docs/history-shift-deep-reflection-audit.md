

# HistoryShift / DeepReflection 分離監査

最終更新: 2026-05-18  
対象: `PremiumStateDeltaCard` / `previous_comparison` / `history_shift` / `deep_reflection`

---

## 目的

`PremiumStateDeltaCard` に含まれている state delta 系の表示ブロックを棚卸しし、
`previous_comparison` / `history_shift` / `deep_reflection` の責務に分離できるかを確認する。

このPRでは UI 実装を増やさず、表示責務・analytics責務・policy接続単位を整理する。

---

## 前提

以下はすでに policy 接続済みである。

```markdown
- [x] ConsultationSummaryCard
- [x] ShrineMeaningCard
- [x] ActionMeaningCard
- [x] PreviousComparisonCard
```

未分離の対象は以下である。

```markdown
- [ ] HistoryShiftCard
- [ ] DeepReflectionCard
```

`PreviousComparisonCard` は現時点では `PremiumStateDeltaCard` として接続済みである。

---

## 現在の構造

現在、`PremiumStateDeltaCard` は以下の情報を1つのカード内で扱っている。

```txt
PremiumStateDeltaCard
├─ stateDelta.summary
├─ stateDelta.combinationChange.summary
├─ stateDelta.transitionNarrative.title
├─ stateDelta.transitionNarrative.summary
├─ stateDelta.changedNeedTags
├─ stateDelta.continuedNeedTags
├─ stateDelta.daysSincePrevious
└─ stateDelta.within7DaysSincePrevious
```

このため、現在の1カードは以下の3責務をまとめて持っている可能性がある。

```markdown
- previous_comparison: 前回相談との比較
- history_shift: 状態や流れの変化
- deep_reflection: 変化の意味づけ・継続テーマの深掘り
```

---

## block分類

| block | 現在の意味 | 分類候補 | 判断 |
|---|---|---|---|
| `stateDelta.summary` | 前回との全体差分 | `previous_comparison` | 主責務として扱う |
| `stateDelta.combinationChange.summary` | 相談テーマの組み合わせ変化 | `previous_comparison` / `deep_reflection` | 保留。比較にも深掘りにも使える |
| `stateDelta.transitionNarrative.title` | 状態遷移の見出し | `history_shift` | 分離候補 |
| `stateDelta.transitionNarrative.summary` | 状態遷移の説明 | `history_shift` | 分離候補 |
| `stateDelta.changedNeedTags` | 今回強く出たテーマ | `deep_reflection` | 分離候補 |
| `stateDelta.continuedNeedTags` | 継続しているテーマ | `deep_reflection` | 分離候補 |
| `stateDelta.daysSincePrevious` | 前回からの日数 | `previous_comparison` | 補助情報 |
| `stateDelta.within7DaysSincePrevious` | 直近比較かどうか | `previous_comparison` | 補助情報 |

---

## previous_comparison の責務

### ゴール

前回相談と今回相談の差分を、Premiumユーザーに見せる。

### 表示対象

```markdown
- stateDelta.summary
- stateDelta.daysSincePrevious
- stateDelta.within7DaysSincePrevious
```

### 表示しないもの

```markdown
- 状態遷移の詳細説明
- 深い解釈
- 継続テーマの意味づけ
```

### analytics

```markdown
- cardId: previous_comparison
- event: card_view
- visibility: visible
```

---

## history_shift の責務

### ゴール

前回から今回にかけて、ユーザーの状態や相談テーマの流れがどう変化したかを示す。

### 表示候補

```markdown
- stateDelta.transitionNarrative.title
- stateDelta.transitionNarrative.summary
```

### 表示しないもの

```markdown
- 前回比較の要約だけ
- 継続テーマの深掘り
- 決めつけ調の心理分析
```

### analytics候補

```markdown
- cardId: history_shift
- event: card_view
- visibility: visible
```

### 判断

`transitionNarrative` が存在する場合のみ表示候補とする。

UIを分ける前に、まず analytics 分離だけで十分か確認する。

---

## deep_reflection の責務

### ゴール

今回強く出ているテーマと、継続しているテーマを整理し、ユーザーが次の行動を考えやすくする。

### 表示候補

```markdown
- stateDelta.changedNeedTags
- stateDelta.continuedNeedTags
- stateDelta.combinationChange.summary
```

### 表示しないもの

```markdown
- 神社推薦そのもの
- 行動指示
- 心理的・宗教的な断定
```

### analytics候補

```markdown
- cardId: deep_reflection
- event: card_view
- visibility: visible
```

### 判断

`changedNeedTags` または `continuedNeedTags` がある場合に表示候補とする。

`combinationChange.summary` は deep_reflection に含めるか、previous_comparison に残すか保留する。

---

## analytics分離だけで済むか

### analytics分離のみで済む条件

```markdown
- UI上は1カードのままで問題ない
- PremiumStateDeltaCard の中に複数blockが自然に並ぶ
- card_view を block 単位で取りたいだけ
- ユーザー体験上、見た目を分ける必要がない
```

### UI分離が必要な条件

```markdown
- previous_comparison / history_shift / deep_reflection の表示位置を変えたい
- Free / Premium の見せ方を block ごとに変えたい
- 各blockに別CTAを置きたい
- stateDelta 内の一部だけを hidden / teaser / partial にしたい
```

---

## 現時点の判断

現時点では、UI分離を急がない。

まずは `PremiumStateDeltaCard` 内部blockを以下のように整理する。

```markdown
- previous_comparison: 既存 card として維持
- history_shift: transitionNarrative がある場合の内部block候補
- deep_reflection: changedNeedTags / continuedNeedTags / combinationChange の内部block候補
```

次PRでは、表示分離ではなく **analytics分離だけで足りるか** を確認する。

---

## 実装を増やさない制約

この監査PRでは以下を行わない。

```markdown
- [ ] 新規コンポーネントを作らない
- [ ] PremiumStateDeltaCard の JSX を変更しない
- [ ] analytics event を追加しない
- [ ] visibility policy を変更しない
- [ ] Free / Premium の表示差分を変更しない
```

---

## 次PR候補

### 候補A: state delta analytics 分離

```markdown
- [ ] history_shift の view 条件を定義
- [ ] deep_reflection の view 条件を定義
- [ ] UIは分けずに analytics のみ分離
- [ ] typecheck
```

### 候補B: PremiumStateDeltaCard 内部block分割

```markdown
- [ ] PreviousComparisonBlock を切り出す
- [ ] HistoryShiftBlock を切り出す
- [ ] DeepReflectionBlock を切り出す
- [ ] 表示順を固定する
- [ ] typecheck
```

### 候補C: ShrineDetail 側 policy 接続へ進む

```markdown
- [ ] ContextReasonCard を確認
- [ ] PersonalMeaningCard を確認
- [ ] SavedRecordCard を確認
- [ ] ConciergeResult 側とは別PRにする
```

---

## TODO

```markdown
- [x] PremiumStateDeltaCard の内部blockを棚卸し
- [x] summary / combinationChange / transitionNarrative を分類
- [x] previous_comparison の責務を固定
- [x] history_shift 候補を抽出
- [x] deep_reflection 候補を抽出
- [x] analytics分離だけで済むか確認
- [x] UI分離が必要か判断
- [x] 実装はまだ増やさない
```
