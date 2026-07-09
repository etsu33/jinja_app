

# Phase7 UX Monetization Roadmap

## 1. Purpose

Phase7 は、KAMI MUSUBI を「神社を検索するアプリ」から「相談を起点に行動と振り返りが循環する体験」へ引き上げるためのUX・収益化フェーズである。

これまでのフェーズでは、推薦ロジック、Score v3、Recommendation Reason v4、Action Suggestion v4、Visit、Reflection、Behavior Funnel の基盤を整備してきた。

Phase7 では、これらの機能を個別に見せるのではなく、ユーザーが自然に以下の流れを進められるように再設計する。

```text
相談する
↓
神社を提案される
↓
行動する
↓
参拝または記録する
↓
振り返る
↓
変化が蓄積される
↓
また相談する
```

この循環を強化することで、継続率、参拝率、振り返り率、Premium転換率を改善する。

---

## 2. Product Positioning

KAMI MUSUBI は、神社データベースでも観光アプリでもない。

ユーザーの言葉、願い、迷い、疲れ、節目を受け取り、その時点で意味のある神社との出会いを提案するAIコンシェルジュアプリである。

Phase7 で目指す体験は、以下である。

```text
悩みを入力するアプリ
ではなく、
人生の節目で開き、行動し、変化を記録するアプリ
```

推薦の価値は、神社を当てることだけではない。

推薦後に、ユーザーが「行ってみよう」「保存しておこう」「振り返ってみよう」と思えるかが、プロダクト価値を決める。

---

## 3. External App Pattern Reference

他カテゴリの継続型アプリでは、以下のような行動ループが使われている。

### 3.1 Learning and Habit Apps

学習アプリや習慣化アプリでは、ユーザーに大きな成果をすぐ求めず、小さな行動を積み重ねさせる。

代表的な流れは以下である。

```text
今日の課題
↓
短い実行
↓
完了演出
↓
連続記録
↓
次回の理由
```

KAMI MUSUBI では、これを以下に置き換える。

```text
今日の相談
↓
おすすめ神社
↓
今日できる小さな行動
↓
参拝・保存・ルート確認
↓
振り返り
↓
次の相談
```

### 3.2 Meditation and Mental Wellness Apps

瞑想・睡眠・メンタルウェルネス系アプリでは、ユーザーの状態を受け取り、すぐにできる短い行動へ接続する。

代表的な流れは以下である。

```text
今の状態を選ぶ
↓
短いセッションを提案
↓
実行
↓
気分を記録
↓
履歴として蓄積
```

KAMI MUSUBI では、相談内容や補助条件をもとに、神社提案と行動提案へ接続する。

```text
今の相談を入力
↓
相性のよい神社を提案
↓
参拝前にできる行動を提示
↓
参拝後の気持ちを記録
↓
変化の履歴として蓄積
```

### 3.3 Mood Tracking and Journaling Apps

気分記録・日記アプリでは、記録そのものが報酬になる。

ユーザーは過去の記録を見返すことで、自分の状態変化に気づく。

代表的な流れは以下である。

```text
今日の気分を記録
↓
一言メモ
↓
カレンダーやタイムラインで可視化
↓
傾向を知る
```

KAMI MUSUBI では、単なる気分記録ではなく、相談、神社、行動、振り返りをつなげる。

```text
相談内容
↓
提案された神社
↓
実際に取った行動
↓
参拝後の気持ち
↓
自分の変化の流れ
```

### 3.4 Travel and Place Discovery Apps

旅行・場所発見系アプリでは、場所の魅力、保存、ルート、訪問記録が行動導線になる。

代表的な流れは以下である。

```text
場所を見る
↓
保存する
↓
ルートを見る
↓
訪問する
↓
写真やメモを残す
```

KAMI MUSUBI では、場所発見だけでなく、相談理由と訪問理由を結びつける。

```text
なぜ今この神社なのか
↓
どんな気持ちで行くのか
↓
行った後に何が変わったのか
```

---

## 4. Core Experience Loop

Phase7 の中心体験は、以下のループで設計する。

```text
Consultation
↓
Recommendation
↓
Action
↓
Visit
↓
Reflection
↓
Timeline
↓
Next Consultation
```

### 4.1 Consultation

ユーザーが今の状態や願いを入力する入口。

重要なのは、入力負荷を下げることと、相談したくなる空気を作ることである。

相談テーマ、自由入力、任意条件はそれぞれ役割を分ける。

| Layer | Role |
| --- | --- |
| 相談テーマ | 入力のきっかけ |
| 自由入力 | 本音や具体的な状況 |
| 任意条件 | 誕生日、参拝スタイル、ご利益などの補助 |

### 4.2 Recommendation

推薦結果では、神社名を並べるだけでは不十分である。

ユーザーが知りたいのは、以下である。

```text
なぜこの神社なのか
今の自分にどう関係するのか
行くとしたら何をすればいいのか
```

Recommendation Reason v4 と Action Suggestion v4 は、この疑問に答えるための中核である。

### 4.3 Action

推薦後に必要なのは、次の小さな行動である。

行動は重くしない。

```text
詳細を見る
保存する
ルートを見る
あとで行く
今日できる一言を書く
```

KAMI MUSUBI では、参拝そのものだけでなく、参拝前の準備行動も価値として扱う。

### 4.4 Visit

Visit は、実際に神社へ行ったことを記録する行動である。

ここでは、行動完了の達成感と、振り返りへの自然な接続が重要になる。

```text
参拝しました
↓
写真または御朱印を残す
↓
一言メモを書く
↓
振り返りへ進む
```

### 4.5 Reflection

Reflection は、KAMI MUSUBI の継続価値の中心である。

参拝後に、ユーザーが自分の変化を言葉にできると、アプリを使う意味が強くなる。

```text
参拝後どう感じたか
行く前と何が違うか
次に何をしたいか
```

### 4.6 Timeline

Timeline は、過去の相談、提案、参拝、振り返りを蓄積する場所である。

単なる履歴ではなく、ユーザーが自分の変化を見返すための画面として扱う。

```text
あの時の相談
↓
提案された神社
↓
実際に取った行動
↓
その後の振り返り
```

---

## 5. Home UX v2

Home は、最初に相談したくなる画面である。

Phase7 の Home では、検索入口ではなく、状態に合わせた相談入口として設計する。

### 5.1 Goal

Home のゴールは、ユーザーが迷わず相談を始められること。

```text
何をすればいいかわからない
↓
今の状態に近い入口がある
↓
相談してみる
```

### 5.2 Key Sections

Home では以下の情報を優先する。

| Section | Role |
| --- | --- |
| Hero Consultation | 今の相談を入力する主導線 |
| Theme Chips | 入力のきっかけ |
| Condition Summary | 任意条件の状態表示 |
| Recent Recommendation | 前回の続き |
| Popular Shrines | 軽い探索導線 |
| Premium Teaser | 履歴・分析への期待づけ |

### 5.3 Design Direction

Home は情報を詰め込みすぎない。

最初の画面では、ユーザーに以下だけ伝える。

```text
今の気持ちを入れれば、神社を提案してもらえる
```

条件入力、ランキング、履歴、Premium は主役ではなく補助として扱う。

---

## 6. Concierge UX v2

Concierge は、KAMI MUSUBI の中心体験である。

Phase7 では、相談入力から推薦結果までの心理的な流れを整える。

### 6.1 Goal

Concierge のゴールは、相談入力と推薦結果の納得感を高めること。

```text
入力する
↓
受け取られた感覚がある
↓
理由つきで提案される
↓
次の行動がわかる
```

### 6.2 Result Structure

推薦結果は、以下の順で表示する。

```text
相談の受け取り
↓
おすすめ神社
↓
なぜこの神社か
↓
今日できる行動
↓
保存・ルート・詳細
```

### 6.3 Psychological Safety

相談内容は、断定的に解釈しない。

避ける表現:

```text
あなたはこういう状態です
この神社が正解です
必ず行くべきです
```

採用する表現:

```text
今の相談には、この文脈が近そうです
この神社は、今のテーマと接点があります
まずは詳細を見て、合いそうか確認できます
```

---

## 7. Shrine Detail v3

Shrine Detail は、推薦から行動へ移る画面である。

Phase7 では、情報ページではなく、行動を促す体験ページとして再設計する。

### 7.1 Goal

Detail のゴールは、ユーザーが「行ってみたい」または「保存しておきたい」と思えること。

### 7.2 Proposed Structure

```text
Hero Image / Visual
↓
あなたへのおすすめ理由
↓
この神社の意味文脈
↓
参拝前にできること
↓
ルートを見る
↓
保存する
↓
参拝しました
↓
振り返りを書く
```

### 7.3 Important UX Rule

神社情報を先に長く読ませすぎない。

最初に必要なのは、百科事典的な情報ではなく、ユーザーの相談との接点である。

```text
この神社の一般情報
より先に、
今の相談とどうつながるか
```

---

## 8. Visit Flow

Visit Flow は、参拝行動を記録する導線である。

### 8.1 Goal

参拝完了を簡単に記録できること。

### 8.2 Flow

```text
参拝しました
↓
日付を記録
↓
写真または御朱印を追加
↓
一言メモ
↓
振り返りへ進む
```

### 8.3 Design Direction

Visit 記録は軽くする。

ユーザーに長い入力を求めない。

最初は以下だけでよい。

```text
参拝日
写真
一言
```

詳細な振り返りは Reflection に分離する。

---

## 9. Reflection Timeline

Reflection Timeline は、KAMI MUSUBI の継続価値を作る画面である。

### 9.1 Goal

ユーザーが過去の相談と変化を見返せること。

### 9.2 Timeline Unit

1つのTimeline item は、以下を持つ。

```text
相談テーマ
提案された神社
取った行動
参拝日
振り返り
次の一手
```

### 9.3 Reflection Prompt

振り返りは、自由記述だけにしない。

入力しやすい選択肢を先に置く。

```text
参拝後の気持ちは？

- 少し軽くなった
- 整理できた
- まだ迷っている
- 行動したくなった
- 変化はまだわからない
```

その後に一言メモを置く。

### 9.4 Premium Connection

Reflection Timeline は Premium と相性がよい。

無料では直近の記録を見せ、Premium では長期的な変化や傾向を見せる。

```text
無料: 直近の相談・参拝・振り返り
Premium: 月別レポート、テーマ傾向、変化の分析、再提案
```

---

## 10. Premium Plan Design

Premium は、単にAI回数を増やすだけでは弱い。

KAMI MUSUBI のPremium価値は、過去の相談、参拝、振り返りをもとに、自分の変化を見られることに置く。

### 10.1 Free Plan

Free は、初回体験と軽い継続に十分な価値を持たせる。

| Feature | Free |
| --- | --- |
| AI相談 | 回数制限あり |
| 神社推薦 | 利用可能 |
| 詳細閲覧 | 利用可能 |
| 保存 | 上限あり |
| 参拝記録 | 基本機能のみ |
| 振り返り | 直近のみ |
| 履歴分析 | なし |

### 10.2 Premium Plan

Premium は、相談と行動の蓄積に価値を置く。

| Feature | Premium |
| --- | --- |
| AI相談 | 実質無制限または大幅増加 |
| 相談履歴 | 無制限 |
| 保存 | 無制限 |
| 参拝記録 | 無制限 |
| 振り返り | 無制限 |
| 月次レポート | 利用可能 |
| 相談テーマ分析 | 利用可能 |
| 参拝傾向分析 | 利用可能 |
| 再提案 | 利用可能 |

### 10.3 Premium Value Message

Premium の訴求は以下に寄せる。

```text
相談を残す
行動を残す
変化を見返す
次の一歩を見つける
```

避ける訴求:

```text
AIをたくさん使える
占い精度が上がる
正解の神社がわかる
```

---

## 11. Monetization Flow

課金導線は、初回起動直後に強く出さない。

ユーザーが価値を感じた後に提示する。

### 11.1 Best Timing

Premium 導線を出すタイミングは以下。

| Timing | Reason |
| --- | --- |
| 相談回数上限に近づいた時 | 継続利用の意思がある |
| 保存上限に達した時 | 神社を残す価値を感じている |
| 振り返り後 | 変化記録の価値を感じやすい |
| Timeline閲覧時 | 履歴分析の価値が伝わりやすい |
| 月次レポート表示時 | Premium価値が最も自然 |

### 11.2 Upgrade Copy Direction

課金コピーは、機能羅列ではなく、ユーザーの変化に寄せる。

```text
過去の相談と参拝を残して、自分の変化を見返せます
```

```text
相談履歴から、今のテーマの傾向を確認できます
```

```text
前回の振り返りをもとに、次の一歩を提案します
```

---

## 12. KPI Design

Phase7 では、機能完成ではなく行動指標で評価する。

### 12.1 Core Funnel

| Step | KPI |
| --- | --- |
| Home | consultation_start_rate |
| Concierge | recommendation_view_rate |
| Result | detail_open_rate |
| Detail | route_open_rate |
| Detail | save_rate |
| Visit | visit_done_rate |
| Reflection | reflection_saved_rate |
| Premium | upgrade_click_rate |
| Premium | purchase_conversion_rate |

### 12.2 Target Direction

初期目標は以下。

| KPI | Target |
| --- | ---: |
| consultation_start_rate | 60% |
| recommendation_view_rate | 90% |
| detail_open_rate | 80% |
| save_rate | 25% |
| route_open_rate | 20% |
| visit_done_rate | 10% |
| reflection_saved_rate | 50% of visits |
| upgrade_click_rate | 5% |
| purchase_conversion_rate | 3% |

### 12.3 Measurement Principle

すべての改善は、以下のループで見る。

```text
仮説
↓
実装
↓
計測
↓
改善
```

---

## 13. Funnel Improvement Plan

Phase7 の改善対象は、以下の順で進める。

### 13.1 Detail Open Improvement

推薦結果から詳細閲覧への遷移を改善する。

理由:

Detail を見ないと、保存、ルート、参拝、振り返りへ進まないため。

### 13.2 Route Open and Save Improvement

Detail からルート表示・保存への導線を強化する。

理由:

保存とルート表示は、実際の参拝意欲に近い行動であるため。

### 13.3 Visit Done Improvement

参拝記録を軽くする。

理由:

参拝記録が重いと、Reflection へ進まないため。

### 13.4 Reflection Saved Improvement

振り返りを選択式＋一言入力にする。

理由:

自由記述だけだと入力負荷が高い。

### 13.5 Premium Conversion Improvement

Premium は、履歴・分析・再提案と接続する。

理由:

KAMI MUSUBI の月額価値は、単発の推薦ではなく、相談と行動の蓄積にあるため。

---

## 14. Release Strategy

Phase7 は、以下の順で小さくリリースする。

### 14.1 Design First

まず UX と収益導線を docs に固定する。

実装前に、各画面の目的、KPI、導線を明確にする。

### 14.2 Small PRs

画面単位でPRを分ける。

```text
Home UX v2
Concierge UX v2
Shrine Detail v3
Visit Flow v1
Reflection Timeline v1
Premium Teaser v1
```

### 14.3 No Payment First

決済実装は最後にする。

先に、Premium 価値の見せ方、導線、コピー、制限ポイントを検証する。

### 14.4 Payment Last

Stripe / App Store / Google Play の決済導入は、Premium 導線が固まってから行う。

---

## 15. Phase7 Decision

Phase7 では、以下を優先する。

```text
機能追加より、行動導線
画面追加より、循環設計
課金実装より、課金したくなる理由
```

当面の中心は、以下である。

```text
相談
↓
提案
↓
行動
↓
振り返り
↓
変化の可視化
```

この循環が回る状態を作ってから、Premium を本格実装する。
