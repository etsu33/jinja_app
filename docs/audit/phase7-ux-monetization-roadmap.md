> **Status: Archive**
>
> 本ドキュメントは、旧Phase 7においてKAMI
> MUSUBIのUX、継続利用、Visit・Reflection、Premium価値および収益化導線を統合して整理した設計記録である。
>
> 記載されたPhase番号、画面Version、UI構成、KPI、Release順序およびPremium機能は当時のスナップショットであり、現行仕様判断には使用しない。
>
> 現在の参照先は以下とする。
>
> - 全体開発方針：`docs/core/roadmap.md`
> - 全体Architecture：`docs/core/architecture.md`
> - Concierge仕様：`docs/product/concierge-first-final-spec.md`
> - Recommendation Mode：`docs/product/concierge-modes.md`
> - Visit / Reflection契約：`docs/product/visit-reflection-flow.md`
> - Reflection Funnel：`docs/product/reflection-funnel-dashboard.md`
> - Shrine Detail設計：`docs/product/shrine-detail-v3-design.md`
> - Reflection Timeline設計：`docs/product/reflection-timeline-design.md`
> - Premium価値境界：`docs/product/pricing.md`
> - Premium体験境界：`docs/product/premium-experience.md`
> - 収益導線・継続計測：`docs/monetization-flow-design.md`
> - Premium長期構想の履歴：`docs/audit/premium-plan-design.md`


# Phase7 UX Monetization Roadmap

## 目的

本書は、KAMI
MUSUBIを神社の検索・一覧表示を中心とする体験から、相談を起点として行動・参拝・振り返り・再相談が循環する体験へ移行するために作成された設計記録である。

旧Phase 7では、Recommendation、Recommendation Reason、Action
Suggestion、Visit、Reflection、Timeline、Premiumを個別機能として扱わず、ユーザー体験として一つにつなげることを目指していた。

当時想定していた中心体験は以下である。

```text
相談
↓
推薦
↓
行動
↓
参拝または記録
↓
振り返り
↓
変化の蓄積
↓
再相談
```

この循環を成立させることで、単発利用ではなく、参拝・記録・振り返りを通じた継続利用へ接続する方針としていた。

---

## 当時のProduct Positioning

旧Phase 7では、KAMI MUSUBIを神社Databaseや観光案内Appとして扱わない方針を明確にした。

中心に置いた価値は、ユーザーの言葉、願い、迷い、疲れ、節目を受け取り、その時点で意味を置きやすい神社と行動を提案することである。

```text
神社を探す
ことだけではなく、
今の状態を整理する
↓
意味のある場所を知る
↓
小さく行動する
↓
自分の変化を記録する
```

ことをProduct価値として捉えた。

Recommendationの価値は神社を提示することだけでなく、ユーザーが次の行動を理解できることにあると整理した。

---

## 当時のCore Experience Loop

旧Phase 7では、以下を一つのExperience Loopとして設計した。

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

### Consultation

ユーザーの現在の状態や相談を受け取る入口として扱う。

相談Theme、自由入力、補助条件は役割を分ける方針とした。

| 入力      | 当時想定した役割                        |
| --------- | --------------------------------------- |
| 相談Theme | 入力を始めるきっかけ                    |
| 自由入力  | 本音や具体的状況                        |
| 任意条件  | 誕生日、参拝Style、ご利益などの補助情報 |

相談入力は診断や分類を目的とせず、Recommendationへ必要な文脈をBackendへ渡すための入口として扱った。

### Recommendation

推薦結果では神社名の一覧だけを表示せず、以下の問いへ答える方針とした。

- なぜこの神社なのか
- 今の自分とどうつながるのか
- 次に何をすればよいか

Recommendation ReasonとAction Suggestionは、推薦結果を説明と行動へ接続する責務として整理した。

### Action

Recommendation後の行動は、参拝だけに限定しない方針とした。

当時想定していた小さな行動には以下があった。

- 神社詳細を見る
- 保存する
- Routeを確認する
- 後で行く候補として残す
- 参拝前の問いや一言を記録する

ユーザーへ大きな決断を要求せず、次の一歩を小さくすることを重視した。

### Visit

Visitは、神社へ行った事実を記録し、Reflectionへ接続する行動として扱った。

```text
参拝を記録
↓
写真・御朱印・Memoを残す
↓
Reflectionへ進む
```

Visitの保存自体を目的にせず、相談・推薦・行動・振り返りをつなぐ接続点とした。

### Reflection

Reflectionは、参拝後にユーザー自身が変化を言葉にするための機能として位置付けた。

当時想定していた問いは以下である。

- 参拝後にどう感じたか
- 行く前と何が違うか
- 次に何をしたいか

Reflectionは診断、評価、正解提示を行わず、ユーザー自身の言語化を補助する方針とした。

### Timeline

Timelineは単なる操作履歴ではなく、相談・推薦・参拝・振り返りを一つの体験単位として見返す場所として設計した。

```text
当時の相談
↓
提案された神社
↓
取った行動
↓
参拝後の振り返り
```

Timelineを通じて、自分の状態や行動の変化に気づけることを継続利用の中心価値とした。

## 当時の画面別UX方針

### Home

Homeは検索画面ではなく、相談を始めるための入口として設計する方針だった。

ユーザーが何を入力すべきか迷う状態から、現在の状態に近いThemeを選び、必要に応じて自由入力へ進める構造を想定した。

当時重視した役割は以下である。

- 相談開始の主導線を一つにする
- Themeを自由入力の補助として使う
- 人気・Ranking・Mapを主役にしない
- 未ログインでも相談を始められる
- 保存など必要な場面でのみ認証を要求する

現在のHome・Concierge入口仕様は、`docs/product/concierge-first-final-spec.md`および関連する現行UI文書を正本とする。

---

### Concierge

Conciergeは、入力からRecommendationまでの心理的な流れを整える責務として扱った。

当時想定していた流れは以下である。

```text
相談を入力
↓
相談内容を整理
↓
最も関連する神社を提示
↓
理由を説明
↓
小さな行動を提示
```

Recommendation画面では、候補数を増やすより、最上位候補と理由を理解しやすくすることを優先した。

心理的安全性の観点から、以下を原則とした。

- 宗教的な断定を行わない
- 心理状態を診断しない
- 「必ず変わる」「運命」などの断定表現を避ける
- ユーザーの選択余地を残す
- 神社を唯一の解決策として扱わない
- Recommendationは提案であり決定ではない

現在のConcierge契約は、以下を正本とする。

- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/consultation-theme-taxonomy.md`

---

### Shrine Detail

Shrine Detailは、神社情報を並べるだけのInformation
Pageではなく、Recommendation理由を理解し、次の行動を選ぶためのExperience Pageとして設計する方針だった。

当時の基本順序は以下である。

```text
今の相談とのつながり
↓
この神社をすすめる理由
↓
神社の意味
↓
参拝・保存・Route確認
↓
Visit・Reflection
↓
事実情報
```

神社の由緒・祭神・ご利益・場所情報は重要だが、ユーザーの状態との接続より前面に出しすぎない方針とした。

Shrine Detailで重視した行動は以下である。

- 保存
- Route確認
- 参拝記録
- Reflection
- Timelineへの接続

現在のShrine Detail仕様は、`docs/product/shrine-detail-v3-design.md`および関連実装を正本とする。

---

### Visit Flow

Visit Flowでは、参拝完了の記録を重くしないことを重視した。

当時想定していた流れは以下である。

```text
神社詳細
↓
Route確認
↓
参拝
↓
参拝済みとして記録
↓
Reflection Prompt
↓
Timelineへ保存
```

Visit登録時に長い入力を要求せず、参拝後の振り返りへ自然につなげる方針とした。

Visitは以下の文脈と接続する構想だった。

- Recommendation Thread
- 推薦された神社
- Recommendation Reason
- Action Suggestion
- Visit日時
- Reflection

現在の保存Model・Event・Payload契約は、以下を正本とする。

- `docs/product/visit-reflection-flow.md`
- `docs/audit/visit-reflection-implementation-consistency.md`
- 関連するBackend・Frontend実装とTest

---

### Reflection Timeline

Reflection Timelineは、KAMI MUSUBIの継続価値を可視化する場所として設計した。

Timeline上の一単位は、単なるReflection本文ではなく、相談から振り返りまでのまとまりとして扱う方針だった。

Reflection Promptは回答を誘導しすぎず、短く答えられる形を想定した。

当時重視した原則は以下である。

- 記録を義務化しない
- 長文を要求しない
- Moodの良し悪しを評価しない
- 変化がなくても保存できる
- 過去の相談と参拝を接続する
- ユーザー自身の言葉を中心にする

現在のReflection・Timeline仕様は、以下を参照する。

- `docs/product/visit-reflection-flow.md`
- `docs/product/reflection-funnel-dashboard.md`
- `docs/product/reflection-timeline-design.md`

---

### 当時のPremium価値

旧Phase 7では、Premiumを検索回数や地図機能の制限として設計しない方針を採用した。

Premiumの中心価値は、継続利用によって蓄積された相談・参拝・Reflectionを、より深く見返せることに置いた。

当時想定していたPremium価値は以下である。

- より深いRecommendation Reason
- Action Meaningの詳細
- 過去の相談履歴
- Visit・Reflection履歴の拡張
- 過去との比較
- 継続的な変化の整理
- Timelineの拡張
- Reflectionの補助
- 月次または期間単位の振り返り

Premiumの中心にしないものは以下である。

- 基本的な神社検索
- 地図表示
- Route確認
- 基本Recommendation
- 占術結果だけの表示
- 単純な利用回数増加

無料ユーザーも相談・推薦・詳細・基本行動を完了でき、Premiumは履歴と継続価値を拡張する位置付けとした。

現在のPremium価値境界は`docs/product/pricing.md`、体験境界は`docs/product/premium-experience.md`、課金状態とPaywall判定は`docs/product/billing-paywall.md`を正本とする。長期構想の履歴は`docs/audit/premium-plan-design.md`を参照する。

---

### 当時のMonetization方針

Upgrade導線は、機能利用前に強く出すのではなく、ユーザーが記録価値や継続価値を理解したタイミングで提示する方針だった。

当時想定した自然な表示タイミングは以下である。

- 深いRecommendation Reasonを確認するとき
- 過去のReflectionを比較するとき
- Timelineの拡張機能を利用するとき
- 継続的な変化を見返すとき
- 期間単位のReportを見るとき

Upgrade Copyは不安や損失を過度に刺激せず、追加される価値を具体的に説明する方針とした。

「続きを見るために支払う」ではなく、「これまでの相談や参拝を、より深く見返す」という価値で表現することを重視した。

現在のMonetization Flowは、`docs/monetization-flow-design.md`およびBilling関連の現行契約を正本とする。

## 当時のKPI設計

旧Phase 7では、機能が実装されたかではなく、相談からReflectionまでの行動がつながったかを評価する方針だった。

### Core Funnel

当時想定していた主要Funnelは以下である。

```text
Consultation Started
↓
Recommendation Viewed
↓
Shrine Detail Viewed
↓
Save / Route Open
↓
Visit Done
↓
Reflection Saved
↓
Return Visit
↓
Premium Conversion
```

### 当時の評価指標

- 相談開始率
- 相談完了率
- Recommendation表示率
- RecommendationからDetailへの遷移率
- Save率
- Route Open率
- Visit Done率
- Reflection保存率
- Timeline再訪率
- 再相談率
- Premium導線表示率
- Premium導線Click率
- 課金転換率
- 継続率

### 計測原則

当時は以下を計測原則とした。

- Event名とPayload契約を先に固定する
- WebとMobileで意味をそろえる
- 表示Eventと実行Eventを分ける
- Recommendation文脈を可能な範囲で保持する
- 少数Dataから結論を出さない
- 改善前後で同じ指標を比較する
- Premium転換だけでなくVisit・Reflectionも評価する

現在のEvent・Payload・Funnel契約は、現行Analytics文書と実装を正本とする。

---

## 当時のFunnel改善順序

旧Phase 7では、下流だけを改善するのではなく、上流から順にFunnelを確認する方針だった。

```text
RecommendationからDetailへ進むか
↓
DetailからSave・Routeへ進むか
↓
RouteからVisit記録へ進むか
↓
VisitからReflectionへ進むか
↓
継続価値を理解した後にPremiumへ進むか
```

### Detail遷移が弱い場合

当時想定していた確認観点は以下である。

- Recommendation Reasonが理解しにくくないか
- 神社名・場所・距離などの判断材料が不足していないか
- Top Recommendationが主役になっているか
- CTAが見つけやすいか

### Save・Routeが弱い場合

当時想定していた確認観点は以下である。

- 保存する理由が伝わっているか
- Route CTAが適切な位置にあるか
- Access情報が不足していないか
- Action Suggestionが次の行動を明確にしているか

### Visit Doneが弱い場合

当時想定していた確認観点は以下である。

- 参拝記録の入力負荷が高くないか
- Route後にAppへ戻る理由があるか
- Visit登録の意味が説明されているか
- Reflectionへの接続が自然か

### Reflection Savedが弱い場合

当時想定していた確認観点は以下である。

- Promptが重すぎないか
- 記録価値が伝わっているか
- Visitとの関係が見えるか
- 過去の相談やAction Suggestionが引き継がれているか

### Premium Conversionが弱い場合

当時想定していた確認観点は以下である。

- 無料体験だけで中核価値を理解できているか
- Upgradeを表示する時点が早すぎないか
- 継続利用による追加価値が明確か
- 制限の説明だけになっていないか
- 課金後に利用できる内容が具体的か

これらは当時の改善仮説であり、現在のUI変更やKPI判断を直接決定するものではない。

---

## 当時のRelease方針

旧Phase 7では、一度に全画面を変更せず、体験単位で小さくReleaseする方針を採用した。

当時想定していた原則は以下である。

- Designと契約を先に固定する
- 画面・機能単位で変更を分ける
- 既存導線を壊さない
- Visit・Reflectionの基盤を先に整える
- Payment接続は最後に行う
- 課金前に無料・Premium境界を確認する
- Analyticsで変更前後を比較できる状態にする

Paymentを先に接続すると、価値検証前に課金状態だけが複雑になるため、UXと継続価値を先に確認する方針だった。

現在のRelease順序は、`docs/core/roadmap.md`、GitHub Issue、Pull Requestおよび現行のRelease計画を参照する。

---

## 旧Phase 7で確定した設計思想

旧Phase 7では、以下を優先する判断を行った。

- 神社検索ではなく相談を体験の入口にする
- Recommendation Reasonを理解と納得へつなげる
- Action Suggestionを小さな行動へつなげる
- VisitをReflectionへの接続点として扱う
- ReflectionとTimelineを継続価値の中心にする
- Premiumを履歴・比較・振り返りの拡張として設計する
- Paymentを価値検証後に接続する
- UX改善を行動Funnelで評価する
- WebとMobileでBackendの業務契約を共有する
- 宗教的・心理的な断定を行わない
- ユーザー自身の選択と変化を主役にする

---

## 本書が保持するもの

- 相談から再相談までを循環として捉えた背景
- Recommendationを説明と行動へ接続する考え方
- Visit・Reflection・Timelineを継続価値とした判断
- Premiumを履歴・比較・内省支援として設計した背景
- Paymentを最後に接続する方針
- Funnelを用いてUXを改善する考え方
- 小さなRelease単位を重視した判断

---

## 本書が扱わないもの

- 現在の開発Phase
- 現在の画面構造
- 現在のHome・Concierge・Shrine Detail仕様
- 現在のVisit・Reflection契約
- 現在のPremium機能
- 現在の料金
- 現在のPayment Provider
- 現在のEvent・Payload契約
- 現在のKPI目標値
- 現在のRelease順序
- TODO
- PR候補
- 実装計画
- 作業進捗

---

## 関連ドキュメント

- `docs/core/roadmap.md`
- `docs/core/architecture.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/visit-reflection-flow.md`
- `docs/product/reflection-funnel-dashboard.md`
- `docs/product/shrine-detail-v3-design.md`
- `docs/product/reflection-timeline-design.md`
- `docs/product/pricing.md`
- `docs/product/premium-experience.md`
- `docs/product/billing-paywall.md`
- `docs/monetization-flow-design.md`
- `docs/audit/premium-plan-design.md`

---

## 更新ルール

- 本書は旧Phase 7におけるUX・継続利用・Premium・収益化設計の記録を保持するArchive文書である
- 現行仕様、実装状態、料金、KPI、Release順序に合わせて更新しない
- 現在の仕様判断には、関連するActive・Reference文書と実装コードを使用する
- 当時の判断内容に重大な事実誤認が確認された場合のみ修正する
- TODO、PR候補、実装Phase、作業進捗、新しい仕様は追記しない
