

# Action Suggestion Funnel

## イベント一覧

### action_suggestion_view

行動提案カードが表示された時に送信。

発火箇所:
- ConciergeTopRecommendationHero.tsx
- useEffect 内

目的:
- 行動提案が何回ユーザーに露出したか確認する
- action_suggestion_click / action_done の母数を作る

---

### action_suggestion_click

「試してみる」ボタン押下時に送信。

発火箇所:
- ConciergeTopRecommendationHero.tsx

目的:
- 行動提案に興味を持った割合を確認する

---

### action_done

「完了」ボタン押下時に送信。

発火箇所:
- ConciergeTopRecommendationHero.tsx

目的:
- ユーザー自己申告ベースの行動完了率を確認する

注意:
- 現在はDB保存されない
- PostHogイベントのみ
- 再訪時に状態は保持されない

---

## Payload一覧

全イベント共通で以下を送信。

| 項目 | 内容 |
|--------|--------|
| source | イベント発生元 |
| threadId | 相談セッションID |
| resultSetId | レコメンド結果ID |
| shrineId | 神社ID |
| recommendationRank | 推薦順位 |
| position | 表示位置 |
| historyTheme | 履歴テーマ |
| actionSuggestionId | 行動提案ID |
| actionCategory | 行動カテゴリ |
| actionTheme | 行動テーマ |
| actionPosition | 表示順 |

---

## PostHogで見るファネル

### 基本ファネル

action_suggestion_view
↓
action_suggestion_click
↓
action_done

確認したい指標:

- View → Click CVR
- Click → Done CVR
- View → Done CVR

---

### テーマ別分析

比較対象:

- historyTheme別
- actionCategory別
- actionSuggestionId別

確認したいこと:

- どのテーマが行動されやすいか
- どのカテゴリが完了率高いか

---

### 推薦順位分析

比較対象:

- recommendationRank

確認したいこと:

- 上位推薦ほど行動率が高いか

---

## 現状の制約

### 1. action_done が永続化されない

現在は PostHog のみ。

そのため:

- 行動履歴に残らない
- パーソナライズに利用できない
- 再訪時に状態が消える

---

### 2. 実行日時が存在しない

現在取得しているのは:

- ボタンを押した

のみ。

実際に行動したかは保証できない。

---

### 3. 行動後体験が存在しない

action_done 後に:

- 振り返り
- メモ
- 継続記録

などの導線がない。

---

## 次の設計TODO

- [ ] action_done 後のUI状態設計
- [ ] action_done 永続化要否判断
- [ ] reflection連携設計

---

## 次PR候補

### PR1

action_done UI状態追加

候補:

- 完了済み表示
- チェックマーク表示
- ボタン無効化

---

### PR2

action_done 永続化

候補:

- ActionCompletion モデル
- ユーザー紐付け
- 実行日時保存

---

### PR3

行動履歴分析

追加イベント候補:

- action_reflection_view
- action_reflection_saved
- action_repeat

---

### PR4

Recommendation Score v2連携

行動シグナルとして活用候補:

- action_suggestion_click
- action_done
- reflection_saved

行動実績を推薦ロジックへ反映する。
