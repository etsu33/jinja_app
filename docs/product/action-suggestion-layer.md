

# Action Suggestion Layer

最終更新: 2026-06-06  
対象: KAMI MUSUBI / 行動推薦 / history_theme / reflection / Recommendation Score v3

---

## 目的

本ドキュメントは、KAMI MUSUBI における **行動推薦レイヤ** の設計を定義する。

KAMI MUSUBI は、神社を検索するアプリではなく、
ユーザーの状態を整理し、意味のある場所を提案し、次の小さな行動につなげる体験である。

そのため、推薦対象は神社だけではない。

```txt
状態整理
↓
神社推薦
↓
行動推薦
↓
行動結果
↓
学習
```

この循環を成立させるために、history_theme ごとに action_suggestion を定義し、
行動実行・完了・振り返りを分析できる構造を作る。

---

## ゴール

### ゴール

神社推薦に加えて、ユーザーの現在状態に合う小さな行動を提示できる状態にする。

### 現在地

```markdown
- history_theme は定義済み
- 神社推薦は history_theme / ご利益 / 距離 / 人気 / 相性を使っている
- detail_view / route_open / save / visit / reflection は行動ログとして取得され始めている
- behavior_signal_v2 は推薦スコアへ反映済み
```

### 次の一手

```markdown
- history_theme × action_suggestion を固定する
- 行動テンプレートを定義する
- action_started / action_completed を計測できるようにする
- reflection から行動結果を抽出する
- action_success_signal を Recommendation Score v3 の入力候補にする
```

---

## 基本方針

### やること

```markdown
- 行動提案は history_theme を起点にする
- 行動は小さく、実行可能な単位にする
- 結果保証をしない
- 心理的・宗教的に断定しない
- 行動提案は神社体験の前後どちらにも置けるようにする
- reflection と接続し、行動結果を学習できるようにする
```

### やらないこと

```markdown
- 人生判断を断定する
- ユーザーに行動を強制する
- 「これをすれば成功する」と言う
- 医療・診断・治療のように扱う
- 行動提案を大量に出す
- 目標管理アプリのように重くする
```

---

## 行動推薦の位置づけ

KAMI MUSUBI の推薦は、以下の2層に分かれる。

```txt
1. Shrine Recommendation
   今の状態に合う神社を提案する

2. Action Suggestion
   今の状態から次に取りやすい小さな行動を提案する
```

神社は行動のきっかけであり、行動提案は現実の変化へ接続するための補助線である。

---

## ActionSuggestion 型

```ts
type ActionSuggestion = {
  id: string;
  historyTheme: HistoryTheme;
  title: string;
  description: string;
  category: ActionCategory;
  timing: ActionTiming;
  difficulty: ActionDifficulty;
  timeEstimate: ActionTimeEstimate;
  measurementKey: string;
};
```

### HistoryTheme

```ts
type HistoryTheme =
  | "守り"
  | "静寂"
  | "再出発"
  | "復興"
  | "勝負"
  | "学び"
  | "縁";
```

### ActionCategory

```ts
type ActionCategory =
  | "reflect"
  | "prepare"
  | "connect"
  | "visit"
  | "record";
```

| category | 意味 | 例 |
|---|---|---|
| reflect | 内省する | 書き出す / 振り返る |
| prepare | 準備する | 調べる / 整える / 予約する |
| connect | 人や機会に接続する | 連絡する / 相談する |
| visit | 実際に場所へ行く | 経路を見る / 参拝する |
| record | 記録する | 保存する / 振り返りを書く |

### ActionTiming

```ts
type ActionTiming =
  | "before_visit"
  | "during_visit"
  | "after_visit"
  | "anytime";
```

### ActionDifficulty

```ts
type ActionDifficulty = "easy" | "normal";
```

### ActionTimeEstimate

```ts
type ActionTimeEstimate = "3min" | "10min" | "30min";
```

---

## history_theme × action_suggestion

### 1. 守り

#### 状態

不安やリスクから距離を取り、生活や心の土台を整えたい状態。

#### 行動方針

```markdown
- 不安を増やす行動ではなく、安心材料を増やす
- 大きな決断を急がせない
- 生活・お金・健康・予定を見える化する
```

#### 行動テンプレート

```markdown
- 今不安なことを3つだけ書く
- 今日守りたい予定を1つ決める
- 今月の固定費を1つ確認する
- 体調を崩しやすい時間帯をメモする
- 経路を確認して、無理なく行ける日を1つ候補にする
```

---

### 2. 静寂

#### 状態

立ち止まり、自分の内側を見つめ直したい状態。

#### 行動方針

```markdown
- 情報を増やしすぎない
- 結論を急がせない
- 静かな時間を作る
```

#### 行動テンプレート

```markdown
- 3分だけ通知を切る
- 今考えすぎていることを1行で書く
- 今日やらないことを1つ決める
- 静かに歩ける場所を1つ選ぶ
- 参拝後に、気持ちの変化を一言だけ残す
```

---

### 3. 再出発

#### 状態

区切りをつけ、新しい方向へ進もうとしている状態。

#### 行動方針

```markdown
- 過去を否定せず、次の一歩を作る
- 大きな転換ではなく、小さな切り替えを促す
- 未来の選択肢を1つ増やす
```

#### 行動テンプレート

```markdown
- やめたいことを1つ書く
- 始めたいことを1つ書く
- 今週変える行動を1つ決める
- 相談したい相手を1人だけ候補にする
- 参拝後に「次に動くこと」を1つ保存する
```

---

### 4. 復興

#### 状態

失ったエネルギーや自信を取り戻していく状態。

#### 行動方針

```markdown
- 回復を急がせない
- できたことを小さく確認する
- 自己否定ではなく再構築を支える
```

#### 行動テンプレート

```markdown
- 今日できたことを1つ書く
- 最近少し楽だった時間を思い出す
- 無理を減らす予定を1つ決める
- 回復の邪魔になっていることを1つ外す
- 参拝後に、少し軽くなった点を記録する
```

---

### 5. 勝負

#### 状態

決断し、挑戦し、前へ進もうとしている状態。

#### 行動方針

```markdown
- 気合いではなく、次の具体行動へ落とす
- 勝ち負けを断定しない
- 行動準備を支える
```

#### 行動テンプレート

```markdown
- 今週勝負したいことを1つ決める
- そのために必要な準備を1つ書く
- 先延ばししている連絡を1つ送る
- 締切を1つカレンダーに入れる
- 参拝後に、最初に動く一手を保存する
```

---

### 6. 学び

#### 状態

知識や経験を積み上げ、成長しようとしている状態。

#### 行動方針

```markdown
- 継続できる最小単位にする
- 完璧な計画より、今日の学習行動を作る
- 成長実感を記録できるようにする
```

#### 行動テンプレート

```markdown
- 今日学ぶ範囲を1つに絞る
- 10分だけ復習する
- 分からないことを1つメモする
- 次に調べるキーワードを1つ保存する
- 参拝後に、積み上げたいことを一言で残す
```

---

### 7. 縁

#### 状態

人・機会・場所とのつながりを見直し、育てたい状態。

#### 行動方針

```markdown
- 相手を動かそうとしない
- 自分ができる接続行動にする
- 関係性の整理と再接続を支える
```

#### 行動テンプレート

```markdown
- 今大切にしたい関係を1つ書く
- 連絡したい人を1人だけ選ぶ
- 感謝を伝えたい相手を1人思い出す
- 距離を置きたい関係を1つ整理する
- 参拝後に、次に育てたい縁を記録する
```

---

## Action Event 設計

行動推薦を学習対象にするため、以下の event を定義する。

| event | 発火条件 | 目的 |
|---|---|---|
| action_suggestion_view | 行動提案が表示された | 表示母数 |
| action_suggestion_click | 行動提案が押された | 関心 |
| action_started | ユーザーが行動開始を明示した | 実行開始 |
| action_completed | ユーザーが完了を明示した | 完了 |
| action_reflection_saved | 行動後の振り返りが保存された | 結果 |

### payload案

```ts
type ActionEventPayload = {
  event: string;
  userId?: number;
  anonymousId?: string;
  shrineId?: number;
  threadId?: number;
  historyTheme: HistoryTheme;
  actionSuggestionId: string;
  actionCategory: ActionCategory;
  timing: ActionTiming;
  source: "concierge_result" | "shrine_detail" | "reflection" | "mypage";
  recommendationRank?: number;
};
```

---

## KPI定義

### 行動実行率

```txt
action_started / action_suggestion_view
```

### 行動完了率

```txt
action_completed / action_started
```

### 行動振り返り率

```txt
action_reflection_saved / action_completed
```

### 神社行動接続率

```txt
action_started / route_open
```

### reflection接続率

```txt
reflection_saved / action_completed
```

---

## reflection から抽出する項目

Reflection は自由記述をそのまま使うのではなく、行動結果として構造化する。

```ts
type ReflectionActionResult = {
  actionSuggestionId?: string;
  completed: boolean;
  feltChange: "lighter" | "clearer" | "motivated" | "unchanged" | "unknown";
  nextActionText?: string;
  blockerText?: string;
};
```

### 抽出候補

```markdown
- 行動したか
- 気持ちが軽くなったか
- 次にやることが見えたか
- まだ詰まっていることは何か
- 同じ history_theme が継続しているか
```

---

## action_success_signal

Recommendation Score v3 では、神社に対する行動だけでなく、行動提案の結果を使う。

### 入力候補

```markdown
- action_started
- action_completed
- action_reflection_saved
- feltChange
- nextActionText の有無
- blockerText の有無
- 同じ history_theme での再相談
```

### 初期スコア案

```txt
action_started: +1.0
action_completed: +2.0
action_reflection_saved: +3.0
feltChange lighter / clearer / motivated: +1.0
nextActionText exists: +1.0
blockerText exists: -0.5
```

上限は 10.0 とする。

---

## Recommendation Score v3 入力候補

```txt
Recommendation Score v3
=
base shrine score
+ behavior_signal_v2
+ action_success_signal
+ history_theme affinity
+ recency
```

### 方針

v3では、神社そのものだけでなく、以下を学習する。

```markdown
- どの history_theme が行動につながりやすいか
- どの action category が完了されやすいか
- どの神社が reflection までつながりやすいか
- どの状態の人にどの行動提案が合いやすいか
```

---

## 実装フェーズ

### Phase 1: docs設計

```markdown
- [x] history_theme × action_suggestion を設計
- [x] history_theme別 行動テンプレート作成
- [x] action_suggestion の型を定義
- [x] action event を設計
- [x] action_success_signal を設計
- [x] recommendation score v3 の入力候補を整理
```

### Phase 2: backend contract

```markdown
- [ ] ActionSuggestion 定義を backend に追加
- [ ] history_theme から action_suggestion を返す service を作成
- [ ] action event 保存 model を設計
- [ ] action_started / action_completed API を設計
```

### Phase 3: frontend display

```markdown
- [ ] ConciergeResult に action_suggestion card を追加
- [ ] ShrineDetail に action_suggestion teaser を追加
- [ ] action_started / action_completed のCTAを追加
```

### Phase 4: learning

```markdown
- [ ] action_success_signal を算出
- [ ] Recommendation Score v3 に接続
- [ ] history_theme別 action CVR をdebug APIで確認
```

---

## TODO

```markdown
- [x] docs/product/action-suggestion-layer.md 作成
- [x] history_theme × action_suggestion を設計
- [x] history_theme別 行動テンプレート作成
- [x] action_suggestion の型を定義
- [x] action event を設計
- [x] action_success_signal を設計
- [x] recommendation score v3 の入力候補を整理
- [ ] backend contract へ進むか母艦で判断する
```
