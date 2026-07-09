

# Monetization Flow Design

## 1. Purpose

Monetization Flow は、KAMI MUSUBI における収益導線を、ユーザー体験を壊さずに設計するためのドキュメントである。

KAMI MUSUBI の収益化は、相談体験の途中で課金を強く要求するものではない。

ユーザーが相談し、神社を知り、行動し、振り返り、記録を積み重ねる中で「この体験をもっと深く残したい」と感じたタイミングで Premium を提示する。

本設計では、課金導線を以下の体験拡張として扱う。

```text
相談
↓
推薦
↓
神社詳細
↓
参拝
↓
振り返り
↓
履歴
↓
Premium
```

Premium は体験を遮る壁ではなく、積み上げた体験を未来へ残すための拡張レイヤーである。

---

## 2. Monetization Philosophy

KAMI MUSUBI は、神社情報そのものを売るサービスではない。

収益化の対象は、以下である。

```text
相談の継続性
参拝記録の蓄積
振り返りの深さ
過去との比較
AIとの文脈継続
人生テーマの可視化
```

課金理由は「AIをたくさん使えるから」ではなく、「自分の相談・行動・振り返りが積み重なり、未来の自分にとって意味を持つから」である。

### 2.1 Not Selling

KAMI MUSUBI では、以下を主な課金理由にしない。

```text
神社情報の閲覧制限
地図やルートの制限
参拝記録そのものの制限
基本的な振り返りの制限
不安を煽る占い的な課金
```

基本体験は無料でも成立させる。

Premium は、その体験を深く・長く・比較可能にするためのものとする。

---

## 3. Free Journey

無料ユーザーは、KAMI MUSUBI の中核体験を最後まで試せる。

無料版の目的は、ユーザーに以下を体験してもらうことである。

```text
相談できる
神社を提案される
理由がわかる
詳細を見られる
ルートを開ける
保存できる
参拝を記録できる
短い振り返りを残せる
```

無料版では、体験の入口を閉じない。

無料ユーザーが「これは自分に関係がある」と感じることが、Premium 転換の前提になる。

---

## 4. Premium Journey

Premium ユーザーは、無料体験の延長として、より深い記録と継続性を得る。

Premium で拡張する対象は、以下である。

```text
相談履歴
参拝履歴
Reflection Timeline
AIとの継続文脈
過去相談との比較
月次レビュー
テーマ傾向
保存・検索・整理
```

Premium は「新しい別体験」ではなく、既存体験の深度を上げる。

```text
無料: 今回の相談を支える
Premium: これまでの相談とこれからの行動をつなぐ
```

---

## 5. Monetization Timing

Premium を提示するタイミングは、ユーザーが価値を感じた後に限定する。

### 5.1 Good Timing

| Timing | User State | Premium Message Direction |
| --- | --- | --- |
| Reflection保存後 | 記録を残した直後 | この記録を未来にも残せます |
| Timeline閲覧時 | 過去を見返している | 過去の相談と参拝をまとめて振り返れます |
| 保存上限到達時 | 残したい神社が増えた | 保存した神社を整理して見返せます |
| 月次レビュー表示時 | 自分の変化に関心がある | 今月の相談と行動をまとめて確認できます |
| 再相談時 | 継続性を求めている | 前回の振り返りを踏まえて相談できます |
| 御朱印・写真追加後 | 記録価値を感じている | 写真や御朱印を長く整理できます |

### 5.2 Bad Timing

以下のタイミングでは Premium を強く出さない。

```text
初回起動直後
相談入力前
不安が強い相談直後
推薦結果を見る前
ルート表示前
参拝中
```

Premium は、ユーザーの迷いや不安につけ込むものではない。

価値を感じた後に、自然な選択肢として提示する。

---

## 6. Premium Entry Points

Premium 導線は、以下の画面に配置する。

| Screen | Entry Point | Direction |
| --- | --- | --- |
| Home | 前回の続き / Timeline teaser | 継続価値を見せる |
| Concierge Result | 再相談 / 履歴保存 teaser | 文脈継続を見せる |
| Shrine Detail | 保存・参拝後の履歴 teaser | 記録価値を見せる |
| Visit Flow | 参拝記録後 | 体験の保存価値を見せる |
| Reflection | 保存後 | 深い振り返りを見せる |
| Timeline | 過去履歴の制限地点 | 長期保存と検索価値を見せる |
| My Page | Plan status | 管理導線として置く |

Premium CTA は、画面の主目的を邪魔しない位置に置く。

---

## 7. CTA Design

Premium CTA は、機能名ではなく体験価値を伝える。

### 7.1 Preferred Copy Direction

```text
過去の相談と参拝をまとめて振り返る
```

```text
この記録を未来の自分にも残す
```

```text
前回の振り返りを踏まえて、次の相談をする
```

```text
今月の相談と行動の流れを見る
```

```text
あなたの参拝と振り返りをTimelineで整理する
```

### 7.2 Avoided Copy Direction

避けるコピーは以下である。

```text
今すぐ課金してください
Premiumで全部解放
あなたに必要な答えを見る
運命の神社を確認する
この先は有料です
```

Premium は不安を煽るものではなく、記録と継続を深める選択肢である。

---

## 8. Free and Premium Boundary

Free と Premium の境界は、体験を分断しないように設計する。

### 8.1 Free

| Feature | Free Direction |
| --- | --- |
| AI相談 | 制限付きで利用可能 |
| 神社推薦 | 利用可能 |
| 推薦理由 | 基本表示 |
| 神社詳細 | 利用可能 |
| ルート表示 | 利用可能 |
| 保存 | 上限あり |
| 参拝記録 | 基本機能あり |
| Reflection | 短い記録が可能 |
| Timeline | 直近履歴を表示 |

### 8.2 Premium

| Feature | Premium Direction |
| --- | --- |
| AI相談 | 継続文脈つきで拡張 |
| 相談履歴 | 長期保存 |
| 推薦理由 | 過去文脈との接続を強化 |
| 保存 | 無制限または大幅拡張 |
| 参拝記録 | 写真・御朱印・詳細メモを拡張 |
| Reflection | 深い振り返り・追記・比較 |
| Timeline | 長期履歴・検索・フィルタ |
| Review | 月次・年次振り返り |
| Analysis | 相談テーマ・行動傾向の可視化 |

境界は「基本体験」と「長期価値」で分ける。

---

## 9. Subscription Flow

決済導線は、以下の流れを前提とする。

```text
Premium teaser
↓
Premium plan page
↓
Checkout
↓
Payment success
↓
Premium activated
↓
元の体験へ戻る
```

### 9.1 Return Context

購入後は、必ず元の文脈に戻す。

例えば、Reflection保存後にPremiumへ進んだ場合は、購入後にTimelineまたはReflection詳細へ戻す。

```text
Reflection
↓
Premium CTA
↓
Checkout
↓
Success
↓
Reflection Timeline
```

課金後にユーザーをHomeへ戻すだけでは、体験の流れが切れる。

---

## 10. Pricing Direction

MVP時点では、価格設計は変更しやすく保つ。

Premium は、まず月額プランを基本とする。

価格の妥当性は、以下の価値に対して検証する。

```text
相談継続
履歴保存
Reflection拡張
Timeline検索
月次レビュー
AI文脈継続
```

価格は、機能数ではなく、継続して記録を残したくなる体験に対して設定する。

---

## 11. Retention Design

Premium の継続率は、決済直後ではなく、利用継続によって決まる。

継続を支える体験は以下である。

```text
月次レビュー
過去の相談の再表示
参拝記録の振り返り
季節ごとの提案
前回Reflectionからの再相談
保存神社の再提案
```

通知だけで継続率を上げようとしない。

ユーザーが戻る理由を、記録と変化の中に作る。

---

## 12. Cancellation Philosophy

解約導線は分かりやすくする。

解約しにくい設計は短期的な売上には見えても、信頼を損なう。

KAMI MUSUBI では、Premiumをユーザーの意思で選び、必要がなくなれば自然に解約できる設計にする。

解約前には、以下を提示してもよい。

```text
保存済みの記録がどう扱われるか
Premium機能が停止する範囲
再開時に戻れるか
```

ただし、不安を煽る表現は使わない。

---

## 13. Analytics Design

Monetization Flow では、以下のイベントを計測する。

| Event | Meaning |
| --- | --- |
| premium_teaser_view | Premium導線を見た |
| premium_cta_click | Premium CTAを押した |
| premium_plan_view | Premiumプランページを見た |
| checkout_start | 決済を開始した |
| checkout_success | 決済が成功した |
| checkout_cancel | 決済を中断した |
| premium_activated | Premiumが有効化された |
| premium_feature_used | Premium機能を利用した |
| subscription_cancel_click | 解約導線を押した |
| subscription_cancel_complete | 解約完了 |

### 13.1 Funnel

基本ファネルは以下とする。

```text
premium_teaser_view
↓
premium_cta_click
↓
premium_plan_view
↓
checkout_start
↓
checkout_success
↓
premium_feature_used
```

### 13.2 Context Tracking

Premium導線では、どの画面から発生したかを必ず記録する。

```text
source_screen
source_action
source_feature
thread_id
shrine_id
visit_id
reflection_id
```

これにより、どの体験が課金意欲につながっているかを確認できる。

---

## 14. Revenue KPI

Monetization Flow では、以下を主要KPIとする。

| KPI | Meaning |
| --- | --- |
| premium_teaser_view_rate | Premium導線が表示された割合 |
| premium_cta_click_rate | CTAを押した割合 |
| checkout_start_rate | 決済開始率 |
| checkout_success_rate | 決済成功率 |
| purchase_conversion_rate | 購入転換率 |
| premium_feature_activation_rate | Premium化後に機能を使った割合 |
| month_1_retention | 1か月継続率 |
| cancel_rate | 解約率 |

売上だけを見ない。

Premium化したユーザーが、実際にReflection、Timeline、月次レビューを使っているかを確認する。

---

## 15. Future Monetization Expansion

MVP後は、以下の収益拡張を検討できる。

```text
年間プラン
季節の振り返りレポート
御朱印帳拡張
巡礼ルート作成
地域別Journey
家族・パートナー共有
記録のPDFエクスポート
```

ただし、MVP時点では拡張しすぎない。

まずは、相談・参拝・振り返り・Timeline・Premium の基本導線で検証する。

---

## 16. Decision

KAMI MUSUBI の Monetization Flow は、体験の途中に置く壁ではなく、体験の蓄積を深める導線として設計する。

```text
課金して使える
ではなく、
使ったから残したくなる
```

Premium は、神社情報を閉じるためのものではない。

ユーザーが積み上げた相談、参拝、振り返りを未来へつなぐための器である。

この方針により、KAMI MUSUBI は短期的な課金圧ではなく、長期的な信頼と継続利用を前提とした収益化を目指す。
