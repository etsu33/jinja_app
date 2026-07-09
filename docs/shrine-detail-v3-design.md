

# Shrine Detail v3 Design

## 1. Purpose

Shrine Detail v3 は、KAMI MUSUBI における神社詳細画面を、単なる情報閲覧ページから「相談後の行動へ進むための体験ページ」へ再設計するためのドキュメントである。

Phase7 UX Monetization Roadmap では、KAMI MUSUBI の中心体験を以下の循環として定義した。

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

Shrine Detail v3 は、この中の「神社を提案される」から「行動する」へ移る接続点である。

ユーザーが詳細画面で知りたいのは、百科事典的な神社情報だけではない。

```text
なぜ今この神社なのか
自分の相談とどう関係するのか
行くなら何をすればよいのか
あとで見返す価値があるのか
```

この疑問に答え、保存、ルート確認、参拝記録、振り返りへ自然につなげることを Shrine Detail v3 の目的とする。

---

## 2. Positioning

Shrine Detail は、以下の3つの責務を持つ。

| Responsibility | Meaning |
| --- | --- |
| Public Shrine Information | 神社の基本情報・由緒・場所情報を伝える |
| Personal Recommendation Context | 相談内容と神社文脈の接点を伝える |
| Action Bridge | 保存・ルート・参拝・振り返りへつなげる |

重要なのは、これらを同じ強さで並べないことである。

Phase7 では、Shrine Detail を次の順で設計する。

```text
相談との接点
↓
神社の意味
↓
今日できる行動
↓
参拝・保存・振り返り
↓
基本情報
```

神社情報は重要だが、最初に長く読ませすぎない。

KAMI MUSUBI の詳細画面は、観光情報ページではなく、相談から行動へ移るための画面である。

---

## 3. Current State

現行の Shrine Detail には、すでに v3 の材料になる表示要素が存在する。

主な既存要素は以下である。

```text
神社名
所在地
画像またはビジュアル領域
説明文
ご利益
推薦理由
recommendationReasonDetail
Action Suggestion
保存導線
ルート表示導線
御朱印表示
御朱印追加導線
公開御朱印
お気に入り状態
```

既存構造は、以下の3層に近い。

```text
ContextReason
PersonalMeaning
SavedRecord
```

ただし、現状ではこれらが画面上で明確に整理されているわけではない。

特に、推薦理由、個人向け意味づけ、保存・御朱印・参拝行動が分散しているため、ユーザーが次に何をすればよいかが弱くなりやすい。

---

## 4. Design Goal

Shrine Detail v3 のゴールは、ユーザーが詳細画面を見たあとに、次のいずれかの行動へ進むことである。

```text
保存する
ルートを見る
参拝したいと思う
参拝しましたを記録する
振り返りを書く
再相談する
```

そのため、v3 では以下を重視する。

```text
情報量より行動導線
神社説明より相談との接点
長文より整理されたブロック
読了より次の一手
```

---

## 5. UX Principles

### 5.1 Start with Personal Context

詳細画面の冒頭では、一般情報よりも「今回の相談との接点」を先に出す。

ユーザーは、推薦結果から詳細へ来ているため、最初に確認したいのは以下である。

```text
なぜこの神社が出てきたのか
今の相談にどう関係するのか
```

そのため、Shrine Detail v3 では、推薦理由を基本情報より上位に置く。

### 5.2 Avoid Fortune-Telling Certainty

神社詳細であっても、宗教的・心理的に断定しない。

避ける表現:

```text
この神社に行けば解決します
あなたにはこの神社が正解です
この神社が運命の場所です
```

採用する表現:

```text
今回の相談とは、この文脈で接点があります
今のテーマに対して、こういう受け取り方ができます
まずは詳細を見て、合いそうか確認できます
```

### 5.3 Keep Action Lightweight

参拝は大きな行動である。

そのため、詳細画面では参拝だけを強く求めない。

軽い行動から並べる。

```text
保存する
ルートを見る
あとで見返す
参拝しました
振り返る
```

### 5.4 Separate Public and Personal Layers

公開情報と個人向け情報を混ぜない。

| Layer | Content |
| --- | --- |
| Public | 住所、由緒、ご利益、基本説明、公開御朱印 |
| Personal | 推薦理由、相談との接点、行動提案、保存状態、振り返り |

公開情報は全ユーザーに見せてよい。

個人向け情報は、相談文脈やログイン状態、Premium状態によって扱いを分ける。

---

## 6. Proposed Page Structure

Shrine Detail v3 の推奨構造は以下である。

```text
Hero Section
↓
Personal Recommendation Summary
↓
Action Bridge
↓
Shrine Meaning Section
↓
Visit and Save Section
↓
Reflection Entry
↓
Public Shrine Information
↓
Goshuin / Record Section
```

---

## 7. Hero Section

### 7.1 Role

Hero Section は、神社の第一印象を作る。

ここでは、神社名、地域、画像、短い意味コピーを表示する。

### 7.2 Content

```text
神社名
所在地またはエリア
画像またはプレースホルダー
短い意味コピー
保存ボタン
```

### 7.3 UX Rule

Hero には情報を詰め込みすぎない。

最初の役割は、ユーザーに「この神社についてもう少し見たい」と思わせることである。

---

## 8. Personal Recommendation Summary

### 8.1 Role

Personal Recommendation Summary は、今回の相談と神社の接点を説明する最重要ブロックである。

### 8.2 Content

```text
今回の相談との接点
推薦理由の短い要約
primary reason
reason facts
consultation_axis
history_theme
```

表示文言では、内部キーをそのまま出さない。

例えば `career_change` や `history_theme: 勝負` をそのまま見せるのではなく、ユーザー向けの自然文へ変換する。

### 8.3 Example Direction

```text
今回の相談には、決断や前進に関するテーマが含まれています。
この神社は、勝負や再出発の文脈と接点があるため、今の状況を整理する候補として提案されています。
```

### 8.4 Priority

このブロックは、基本情報より上に置く。

理由は、ユーザーが推薦結果から詳細へ遷移しているためである。

---

## 9. Action Bridge

### 9.1 Role

Action Bridge は、推薦を行動へ変えるためのブロックである。

ここでは、神社に行くことだけでなく、今すぐできる小さな行動も提示する。

### 9.2 Content

```text
今日できること
参拝前に意識すること
ルートを見る
保存する
あとで見返す
```

### 9.3 Action Priority

詳細画面での行動優先順位は以下とする。

| Priority | Action | Reason |
| --- | --- | --- |
| 1 | ルートを見る | 参拝意欲に最も近い |
| 2 | 保存する | 再訪・継続利用につながる |
| 3 | 参拝しました | 実行動の記録になる |
| 4 | 振り返りを書く | 継続価値の中心になる |
| 5 | 再相談する | 次回利用につながる |

ただし、UI上ではユーザーの状態に応じて優先表示を調整する。

未訪問の場合は「ルートを見る」「保存する」を優先する。

訪問済みの場合は「参拝しました」「振り返りを書く」を優先する。

---

## 10. Shrine Meaning Section

### 10.1 Role

Shrine Meaning Section は、神社の歴史・ご利益・意味文脈を説明するブロックである。

ただし、単なる神社情報ではなく、相談との接点を補強するために使う。

### 10.2 Content

```text
history_theme
由緒
ご利益
祀られている神様
場所性
文化的文脈
```

### 10.3 UX Rule

ご利益だけで説明を終わらせない。

```text
金運だからおすすめ
縁結びだからおすすめ
```

ではなく、以下のように意味づける。

```text
お金そのものの結果保証ではなく、生活の土台や判断を整える文脈として接点があります
```

---

## 11. Visit and Save Section

### 11.1 Role

Visit and Save Section は、ユーザーがこの神社を自分の記録に残すためのブロックである。

### 11.2 Content

```text
保存する
保存済み状態
お気に入り一覧への導線
参拝しました
御朱印を追加
写真を追加
```

### 11.3 Anonymous / Free / Premium

| Access | Display Direction |
| --- | --- |
| Anonymous | 保存にはログインが必要であることを軽く伝える |
| Free | 保存・参拝記録の基本導線を表示する |
| Premium | 保存・参拝・振り返り・履歴分析への導線を強化する |

保存機能自体は Premium 専用にしない。

Premium 価値は、保存した後の履歴整理、比較、変化分析に置く。

---

## 12. Reflection Entry

### 12.1 Role

Reflection Entry は、参拝後の振り返りへ進む導線である。

KAMI MUSUBI の継続価値は、参拝したことよりも、参拝後に何を感じ、どう変化したかを残せることにある。

### 12.2 Content

```text
参拝後どう感じたか
気持ちは少し変わったか
次に何をしたいか
一言メモ
```

### 12.3 UX Rule

振り返り導線は、参拝前から強く出しすぎない。

未訪問状態では、軽い予告に留める。

```text
参拝後に、感じたことを記録できます
```

訪問済み状態では、振り返り入力を主導線に上げる。

---

## 13. Public Shrine Information

### 13.1 Role

Public Shrine Information は、神社の基本情報を提供するブロックである。

### 13.2 Content

```text
住所
アクセス
由緒
ご利益
公式情報
地図
周辺情報
```

### 13.3 UX Rule

基本情報は必要だが、画面上の主役にはしない。

KAMI MUSUBI の詳細画面では、公開情報は「納得と行動を支える情報」として扱う。

---

## 14. Goshuin / Record Section

### 14.1 Role

Goshuin / Record Section は、参拝体験の記録性を高めるためのブロックである。

### 14.2 Content

```text
公開御朱印
自分の御朱印追加
写真記録
参拝記録
```

### 14.3 UX Rule

公開御朱印は、神社の魅力を伝える補助情報として扱う。

一方で、自分の御朱印や写真は、個人の記録として扱う。

公開情報と個人記録を混ぜない。

---

## 15. Card Responsibility

Shrine Detail v3 では、画面内の情報を以下の card responsibility に整理する。

| Card | Responsibility | Access Direction |
| --- | --- | --- |
| ShrineHeroCard | 神社の第一印象を作る | all |
| ContextReasonCard | 推薦理由を説明する | free partial / premium visible |
| PersonalMeaningCard | 相談との意味接続を説明する | free teaser or partial / premium visible |
| ActionBridgeCard | 次の行動を提示する | all |
| SaveVisitCard | 保存・参拝記録へつなげる | login recommended |
| ReflectionEntryCard | 振り返りへつなげる | free basic / premium enhanced |
| PublicInfoCard | 神社基本情報を表示する | all |
| GoshuinRecordCard | 御朱印・記録を扱う | free basic / premium enhanced |

この整理は、将来的な CardVisibilityPolicy 接続の前提になる。

---

## 16. Access Level Design

### 16.1 Anonymous

Anonymous は、神社詳細の基本価値を体験できる状態にする。

表示するもの:

```text
神社名
所在地
基本説明
公開情報
一部の推薦理由
ルート導線
ログイン誘導つき保存導線
```

表示しない、または弱く出すもの:

```text
個人向けの深い意味整理
過去相談との比較
振り返り履歴
保存済み記録
```

### 16.2 Free

Free は、相談から神社に出会い、保存・参拝記録へ進める状態にする。

表示するもの:

```text
推薦理由の基本表示
神社意味の一部
保存
ルート
参拝しました
基本的な振り返り
```

Premium teaser として表示するもの:

```text
過去相談との比較
参拝後の変化分析
テーマ傾向
月次レポート
```

### 16.3 Premium

Premium は、詳細画面を「自分の相談履歴と行動履歴がつながる場所」として表示する。

表示するもの:

```text
推薦理由の詳細
相談との意味接続
過去相談との比較
参拝履歴との接続
振り返り履歴
次の一手の再提案
```

Premium の価値は、神社情報を増やすことではない。

ユーザー自身の相談、行動、振り返りがつながることである。

---

## 17. Analytics Design

Shrine Detail v3 では、以下の行動を計測対象にする。

| Event | Meaning |
| --- | --- |
| shrine_detail_view | 詳細画面を開いた |
| context_reason_view | 推薦理由ブロックを見た |
| action_bridge_view | 行動提案ブロックを見た |
| route_open | ルートを開いた |
| shrine_save | 保存した |
| visit_done | 参拝済みにした |
| reflection_start | 振り返りを開始した |
| reflection_saved | 振り返りを保存した |
| premium_teaser_view | Premium導線を見た |
| premium_cta_click | Premium CTAを押した |

### 17.1 Funnel

Shrine Detail v3 の基本ファネルは以下である。

```text
recommendation_view
↓
shrine_detail_view
↓
route_open / shrine_save
↓
visit_done
↓
reflection_saved
↓
premium_cta_click
```

### 17.2 KPI

| KPI | Target Direction |
| --- | --- |
| detail_open_rate | 推薦から詳細へ進んだ割合 |
| route_open_rate | 詳細からルートへ進んだ割合 |
| save_rate | 詳細から保存した割合 |
| visit_done_rate | 参拝済み記録まで進んだ割合 |
| reflection_saved_rate | 参拝後に振り返りを保存した割合 |
| premium_cta_click_rate | Premium導線を押した割合 |

---

## 18. Premium Connection

Shrine Detail v3 では、Premium をいきなり決済として出さない。

Premium は、以下の価値を感じる場面で提示する。

```text
保存した神社を後から見返したい
参拝後の変化を残したい
過去の相談と比較したい
自分のテーマ傾向を知りたい
次の一手を再提案してほしい
```

### 18.1 Premium Teaser Timing

| Timing | Message Direction |
| --- | --- |
| 保存後 | 保存した神社を履歴で整理できます |
| 参拝記録後 | 参拝後の変化を残せます |
| 振り返り後 | 過去の相談と変化を比較できます |
| 再訪問時 | 前回の相談と今回の流れを見返せます |

### 18.2 Avoided Monetization Pattern

避ける設計:

```text
詳細情報の続きはPremium
神社の由緒全文はPremium
地図を見るにはPremium
```

採用する設計:

```text
自分の相談と参拝履歴を整理するにはPremium
過去との比較を見るにはPremium
変化の傾向を見るにはPremium
```

---

## 19. Implementation Boundary

この設計では、まだ実装変更を行わない。

実装時は、以下のようにPRを分ける。

```text
Shrine Detail v3 layout audit
↓
ContextReasonCard整理
↓
ActionBridgeCard整理
↓
SaveVisitCard整理
↓
ReflectionEntry導線追加
↓
Analytics計測整理
↓
Premium teaser導線整理
```

一度にすべてを変更しない。

Shrine Detail は、推薦、保存、参拝、振り返り、Premium が交差する画面であり、まとめて触ると責務が崩れやすい。

---

## 20. Decision

Shrine Detail v3 は、以下の方針で進める。

```text
情報ページではなく、行動接続ページとして扱う
公開情報より先に、相談との接点を示す
参拝を強制せず、保存・ルート・記録の軽い行動を置く
振り返り導線を継続価値の中心にする
Premium は神社情報ではなく、履歴整理・比較・変化分析に接続する
```

この方針により、Shrine Detail は Phase7 の中心である「相談 → 行動 → 振り返り」の中継点になる。
