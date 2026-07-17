> **Status: Active**
>
> 本ドキュメントは、KAMI MUSUBIにおける参拝・訪問の記録から振り返り、履歴および次回相談までを接続する体験責務を管理する正本文書である。
>
> 正確なEvent、Payload、KPI、保存構造、Field、API、画面遷移および送信処理は、関連するAnalytics文書、Core文書、実装コードおよびテストを最終的な正本とする。

# Visit Reflection Flow

## 目的

KAMI MUSUBIにおける参拝・訪問の記録から振り返り、履歴および次回相談までを一つの体験として接続する。

参拝完了を体験の終点にはしない。

ユーザーが行動後に考えたことや感じた変化を無理のない範囲で整理し、後から見返したり、次回相談へつなげたりできる状態を作る。

```text
相談・推薦
↓
神社詳細・経路確認
↓
参拝または訪問
↓
短い振り返り
↓
履歴
↓
次回相談
```

---

## 基本原則

- 参拝・訪問の完了は振り返りの入口として扱う
- 振り返りは短い変化記録として扱う
- 長文日記を前提にしない
- 回答や保存を強制しない
- 行動しなかった場合も振り返りを許容する
- ユーザーの心理状態を診断しない
- 宗教的な効果や達成を判定しない
- 成功・失敗を自動判定しない
- 保存機能と履歴を比較・分析する価値を分離する
- 推薦時点の文脈と行動後の記録を混同しない
- FrontendでVisitやReflectionの業務判定を重複実装しない

---

## 体験フロー

```text
神社を提案される
↓
神社詳細を確認する
↓
保存または経路を確認する
↓
参拝・訪問を記録する
↓
振り返りの入口を提示する
↓
短いReflectionを保存する
↓
履歴として見返す
↓
次回相談へ接続する
```

各段階の体験責務は以下とする。

| 段階 | 体験責務 |
|---|---|
| 神社詳細 | 神社情報と提案理由を確認する |
| 保存 | 後から見返せる状態にする |
| 経路確認 | 現地へ向かう可能性を検討する |
| Visit | 参拝・訪問または関連する行動の完了を記録する |
| Reflection入口 | 行動後の整理を始める選択肢を提示する |
| Reflection保存 | 考えや変化を短い記録として残す |
| 履歴 | 過去の相談、行動および振り返りを見返す |
| 次回相談 | 過去の体験を新しい相談の文脈へ接続する |

各段階を必ず順番どおりに通過する必要はない。

神社へ参拝しなかった場合でも、相談後に行った日常行動や考えたことを振り返る体験を許容する。

---

## Visit

### 意味責務

Visitは、ユーザーが神社へ参拝・訪問したこと、または参拝に関連する行動を完了したことを記録する体験である。

Visitは、行動の事実を扱う。

心理的な改善、願いの達成または宗教的な効果は扱わない。

### Visitの入口

Visitは、以下の体験から接続できる。

- 神社詳細
- 経路確認
- 保存した神社
- マイページまたは履歴
- 推薦後の行動導線

正確な画面、CTA、Routeおよび保存処理は、関連するFrontend・Backend実装とテストを正本とする。

### Visit後の体験

Visitの記録後は、ユーザーへReflectionの入口を提示できる。

ただし、Reflectionの回答や保存は必須としない。

ユーザーは以下を選択できる。

- その場で短く振り返る
- 後から振り返る
- 記録だけ残して終了する
- 次回相談へ進む

### Visitが担当しないもの

- 心理状態の判定
- 行動の良否判定
- Reflection回答の生成
- 推薦理由の再生成
- 神社の効果判定
- 次回行動の強制

---

## Reflection

### 意味責務

Reflectionは、相談や行動の後に考えたこと、感じたことまたは次に持ち帰りたいことを整理する体験である。

Reflectionは、ユーザーの変化を診断するものではない。

ユーザー自身が言葉にした内容を、後から見返せる記録として扱う。

### 記録できる内容

Reflectionでは、以下の内容を任意で扱える。

- 行動後に考えたこと
- 印象に残ったこと
- 行動前後で変わった感覚
- 次に試したいこと
- まだ決めずに置いておきたいこと
- 相談時点から継続しているテーマ

正確な入力項目、型、必須条件および保存Fieldは、関連するBackend・Frontend実装とテストを正本とする。

### 入力原則

- 一度に多くの入力を求めない
- 短い回答でも保存できる体験を優先する
- 長文入力を前提にしない
- 正解のある質問にしない
- 心理状態を断定する質問にしない
- 宗教的な効果を確認する質問にしない
- 回答しない選択を妨げない
- 過去との比較をユーザーへ強制しない

### 質問例

Reflectionの質問は、相談や推薦時点の文脈を参照できる。

| 文脈 | 質問例 |
|---|---|
| 守り | 今日、自分の土台を少し守れたことは何ですか |
| 静寂 | 少し静かになれた瞬間はありましたか |
| 再出発 | 区切りをつけられたことはありましたか |
| 復興 | 自分を立て直すためにできたことはありますか |
| 勝負 | 次に進むために考えたことは何ですか |
| 学び | 今日、積み上げられたことは何ですか |
| 縁 | 大切にしたい関係について考えたことはありますか |

質問表現の正本は、`docs/knowledge/reflection-guide.md`を参照する。

---

## Reflectionプレビューとの境界

Action Suggestionには、次の振り返り観点を示す短い質問が含まれる場合がある。

この質問表示と、実際のReflection入力体験は分離する。

| 体験 | 責務 |
|---|---|
| Action SuggestionのReflectionプレビュー | 次に振り返る観点を提示する |
| Reflection入力UI | ユーザーが回答を入力し、記録として保存する |

Reflectionプレビューは、回答や保存を前提としない。

Reflection入力UIは、ユーザーが実際に回答し、履歴へ記録できる体験である。

Action Suggestionの責務は、`docs/product/action_suggestion_v4.md`を参照する。

正確な表示イベント、保存イベント、Payloadおよび計測語彙は、`docs/analytics/`配下の正本文書を参照する。

---

## 推薦時点の文脈との接続

VisitおよびReflectionは、相談・推薦時点の文脈と接続できる。

```text
相談
↓
Consultation Interpretation
↓
Meaning Translation
↓
Recommendation
↓
Visit
↓
Reflection
```

これにより、ユーザーは以下を一つの体験として見返せる。

- 何について相談したか
- どの神社が提案されたか
- なぜその神社が提案されたか
- どのような行動を選んだか
- 行動後に何を考えたか

Productでは、推薦時点の意味文脈を後続体験へ接続する目的のみを管理する。

正確なSnapshot構造、接続キー、保存先、Field、生成処理および再計算方針は、`docs/core/meaning-layer-connection.md`、`docs/core/architecture.md`および関連するBackend実装・テストを正本とする。

---

## history_themeとの接続

`history_theme`は、推薦時点の神社文脈と行動後の振り返りを接続する補助軸として利用できる。

```text
相談文脈
↓
history_theme
↓
推薦
↓
行動
↓
振り返り
```

Productでは、`history_theme`を以下の目的で使用する。

- 推薦理由とReflectionの文脈を接続する
- 振り返り質問の方向を補助する
- 履歴上で体験を整理する
- 次回相談で過去の文脈を参照する

`history_theme`だけでユーザーの状態を判定しない。

`history_theme`が取得できない場合でも、VisitおよびReflectionの体験は成立させる。

カテゴリ名称と定義は、`docs/product/history-theme-taxonomy.md`を参照する。

変換関係は、`docs/product/meaning-translation-mapping.md`を参照する。

神社への付与基準、Fact / Meaningの分類、出典およびデータ品質は、`docs/knowledge/shrine-profile-spec.md`と`docs/knowledge/shrine-data-guide.md`を正本とする。

---

## 履歴との接続

保存されたVisitおよびReflectionは、相談から行動後の記録までを時系列で見返すために利用できる。

履歴では、以下の情報を体験単位で接続できる。

- 相談
- 推薦された神社
- 推薦理由
- Visit
- Reflection
- 次回相談

履歴は、ユーザーを評価するための記録ではない。

過去の選択を成功・失敗に分類せず、当時の文脈とその後の考えを見返すために利用する。

Timelineの情報設計は、関連するProduct文書と実装を参照する。

---

## 次回相談との接続

Reflectionは、保存して終了するだけの体験にしない。

必要に応じて、過去の相談や行動を次回相談の文脈として参照できる。

次回相談では、過去の記録を結論として使用しない。

以下のような補助文脈として扱う。

- 前回考えていたこと
- 前回選択した行動
- 行動後に記録した内容
- 継続しているテーマ
- 新しく変化した相談内容

AIは、過去のReflectionだけを根拠にユーザーの状態、性格または将来を断定しない。

---

## Analyticsとの境界

Productでは、VisitおよびReflection体験について、以下を観測する必要性のみを管理する。

- 神社詳細から行動へ進んだか
- Visitが記録されたか
- Reflectionの入口が表示されたか
- Reflectionが保存されたか
- 履歴が見返されたか
- 次回相談へ接続したか
- 各段階で体験が中断していないか

正確な以下の内容は、`docs/analytics/`配下の正本文書を参照する。

- Event名
- Payload
- Property
- 必須・任意項目
- Funnel
- KPI
- 欠損値の扱い
- PostHogの設定
- Web / Mobileの送信差
- 集計方法
- Dashboard構成

参拝から振り返りまでのFunnel、KPIおよびPostHog Dashboard構成は、`docs/analytics/reflection-funnel-dashboard.md`を参照する。

Analyticsは体験改善の観測に使用する。

個別ユーザーの心理状態、宗教的効果、信仰の程度または人生上の成果を判定するためには使用しない。

---

## Free / Premium境界

### Free

Freeでは、相談後の行動と短い振り返りを記録できる基本体験を提供する。

- Visitの記録
- 短いReflectionの保存
- 直近の記録の表示
- 自分の記録を見返すための基本導線

保存そのものをPremium限定にはしない。

### Premium

Premiumでは、蓄積した記録を比較・整理し、継続的に振り返る価値を提供できる。

- 過去のReflectionとの比較
- 一定期間の記録の整理
- 繰り返し現れるテーマの表示
- 過去記録を参照した振り返り支援
- 相談・行動・Reflectionの長期的な接続

Premium価値は、Reflectionを保存できることではなく、蓄積した体験を比較・整理しやすくすることに置く。

具体的なPremium提供範囲は、`docs/product/premium-experience.md`を参照する。

BillingおよびAccess Levelの物理判定は、`docs/product/billing-paywall.md`と関連する実装・テストを正本とする。

---

## 責務境界

### Product

Productでは以下を管理する。

- VisitからReflectionへの体験接続
- VisitとReflectionの意味責務
- Reflectionプレビューと入力UIの境界
- 推薦時点の文脈との接続
- 履歴および次回相談への接続
- Free / Premiumの体験境界
- 断定、強制および結果保証を避ける原則

### Visit

Visitでは以下を扱う。

- 参拝・訪問または関連行動の完了事実
- 対象となる神社
- 行動した時点
- Reflectionへの入口

Visitでは以下を扱わない。

- Reflection回答
- 心理状態の判定
- 推薦理由の再生成
- 宗教的効果の判定
- 行動の成功・失敗判定

### Reflection

Reflectionでは以下を扱う。

- 振り返りの問い
- ユーザーが入力した回答
- 行動前後の任意の記録
- 推薦時点の文脈との接続
- 履歴および次回相談への接続

Reflectionでは以下を扱わない。

- Visit完了の物理判定
- 神社推薦順位
- 心理・医療診断
- 宗教的効果の判定
- AIによる成功・失敗評価

### Core

以下は`docs/core/`配下の正本文書を参照する。

- ConsultationからReflectionまでの全体構造
- Recommendation、VisitおよびReflectionのデータフロー
- Frontend、BFFおよびBackendの技術責務
- Source of Truth
- 推薦時点の文脈保持
- 各記録の構造的な接続

### Backend・実装

以下は関連するBackend実装とテストを正本とする。

- Model
- Field
- 型
- Index
- Foreign Key
- 接続キー
- Serializer
- API Endpoint
- 必須・任意条件
- 保存処理
- 更新処理
- 削除処理
- Snapshotの保存先
- fallback
- Validation

### Frontend・実装

以下は関連するFrontend実装とテストを正本とする。

- Visit CTA
- Reflection入力UI
- 保存可否
- 画面遷移
- Timeline表示
- Access Levelによる表示差
- Event送信処理
- Web / Mobileの画面差

### Analytics

以下は`docs/analytics/`配下の正本文書を参照する。

- Event名
- Payload
- Property
- Funnel
- KPI
- 欠損値の扱い
- Dashboard
- PostHog送信
- Web / Mobileの計測差
- 集計方法

### Knowledge

以下は`docs/knowledge/`配下の正本文書を参照する。

- Reflection質問の表現原則
- Action文言の表現原則
- ユーザー状態を断定しないコピー
- 神社FactとMeaningの扱い
- `history_theme`と神社情報の接続基準

### Audit

以下は`docs/audit/`配下の監査文書で管理する。

- 現行実装状況
- Web / Mobileの未接続事項
- 過去に検討して採用しなかったField
- Migration判断
- 検証結果
- 未確認事項
- 実装差分
- 移行手順

---

## 責務外

本書では以下を管理しない。

- Event名
- Payload
- Property
- Funnel
- KPI
- Model全文
- Field一覧
- Index
- Serializer
- API Endpoint
- URL Query
- Component構造
- Web / Mobileの送信状況
- Analytics欠損値の物理処理
- Recommendation Ranking
- Recommendation Score
- 神社DB構造
- Migration手順
- テストケース一覧
- 実装進捗
- PR計画
- 作業履歴

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/history-theme-taxonomy.md`
- `docs/product/shrine-detail-layer.md`
- `docs/product/premium-experience.md`
- `docs/product/billing-paywall.md`
- `docs/product/reflection-timeline-design.md`
- `docs/product/journey-timeline-design.md`
- `docs/analytics/reflection-next-recommendation-design.md`
- `docs/analytics/history-theme-dashboard.md`
- `docs/analytics/reflection-funnel-dashboard.md`
- `docs/core/architecture.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/recommendation-readiness.md`
- `docs/knowledge/reflection-guide.md`
- `docs/knowledge/action-guide.md`
- `docs/knowledge/shrine-profile-spec.md`
- `docs/knowledge/shrine-data-guide.md`

---

## 更新ルール

- 本書はVisitからReflection、履歴および次回相談までの体験責務を管理する。
- VisitまたはReflectionの意味責務が変更された場合は、本書を更新する。
- Reflectionプレビューと入力UIの体験境界が変更された場合は、本書を更新する。
- Free / Premiumの体験境界が変更された場合は、本書を更新する。
- 推薦時点の文脈とVisit / Reflectionの接続目的が変更された場合は、本書を更新する。
- Event、Payload、Property、FunnelおよびKPIは本書で重複管理しない。
- Model、Field、Index、API、型および保存処理は本書で重複管理しない。
- 物理実装のみを変更した場合は、本書の体験責務への影響を確認する。
- TODO、PR計画、実装進捗、テスト手順、検証結果および作業履歴は本書へ記載しない。
