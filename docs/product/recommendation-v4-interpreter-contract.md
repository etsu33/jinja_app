> **Status: Active**
>
> 本ドキュメントは、KAMI MUSUBIにおけるConsultation Interpreterの解釈フィールドと意味責務を管理する正本文書である。
>
> 正確な生成処理、出力構造、キー、分類ロジックおよび利用条件は、関連するCore文書、Backend実装およびテストを最終的な正本とする。

# Recommendation v4 / Consultation Interpreter Contract

## 目的

ユーザーの相談文を、Meaning Translation、Recommendation、Recommendation ReasonおよびAction Suggestionで再利用できる意味要素へ整理する。

Consultation Interpreterは、ユーザーの性格、心理状態、将来または正解を断定するものではない。

相談文に含まれる状態、目的、感情、制約および行動意図を、後続レイヤーが参照できる文脈として整理する。

---

## 基本原則

- ユーザーの相談原文を解釈結果と混同しない
- 一つの入力から一つの心理状態を断定しない
- 解釈結果は推薦順位を単独で決定しない
- 相談テーマ、ご利益、誕生日、相性および方位は補助情報として扱う
- 医療、心理、宗教または人生上の結果を判定しない
- Frontendで相談解釈ロジックを重複実装しない
- 正確な出力Schemaおよび生成処理はBackend実装とテストを正本とする

---

## 解釈フィールド

Consultation Interpreterは、相談内容を以下の意味要素へ整理する。

| フィールド | 意味責務 | 主な接続先 |
|---|---|---|
| `raw_query` | ユーザーが入力した相談原文 | Meaning Translation、Recommendation Reason |
| `state_profile` | 相談文から読み取れる現在状態の候補 | Meaning Translation、Recommendation Reason |
| `need_profile` | 求めている目的、願いまたは支援テーマ | Recommendation、Meaning Translation |
| `direction_profile` | どの方向の体験へ接続するかという候補 | Meaning Translation、Action Suggestion |
| `emotion_profile` | 相談文に表れている感情トーンと強さ | Recommendation Reason、Action Suggestion |
| `action_intent` | 次に取りたい行動の候補 | Action Suggestion、CTA |
| `decision_context` | ユーザーが整理または判断したい対象 | Meaning Translation、Recommendation Reason |
| `constraint_profile` | 行動や判断に影響する制約 | Recommendation Reason、Action Suggestion |
| `outcome_hint` | ユーザーが望んでいる着地点の候補 | Recommendation Reason、Action Suggestion |

各フィールドの正確なキー、型、必須条件、fallbackおよび生成順序は、関連するBackend実装とテストを正本とする。

---

## raw_query

### 意味責務

`raw_query`は、ユーザーが入力した相談内容の原文を保持する。

後続レイヤーが、構造化された解釈だけでは失われる文脈を確認するために利用できる。

### 原則

- ユーザーの表現を解釈結果へ置き換えない
- 要約結果を原文として扱わない
- 推薦理由へ相談原文をそのまま露出させることを前提にしない
- Debug用途や物理的な正規化処理は本書では管理しない

---

## state_profile

### 意味責務

`state_profile`は、相談文から読み取れる現在状態の候補を整理する。

対象には、疲労、不安、迷い、停滞または変化への準備などが含まれうる。

### 原則

- 心理診断として扱わない
- 一つの状態へ固定しない
- ユーザー本人が明示していない状態を断定しない
- Meaning TranslationやRecommendation Reasonの補助文脈として利用する

---

## need_profile

### 意味責務

`need_profile`は、ユーザーが求めている目的、願い、支援テーマまたは関心を整理する。

相談テーマや明示されたご利益は、自由入力を補助する情報として利用できる。

### 原則

- 自由入力を優先する
- 相談テーマだけで目的を確定しない
- ご利益だけで推薦結果を決定しない
- 正確な`need_tags`の分類、抽出、優先順位および同期手順はBackend実装とテストを正本とする

---

## direction_profile

### 意味責務

`direction_profile`は、相談内容をどの方向の参拝体験や行動文脈へ接続するかを整理する。

例として、休息、安定、見直し、切り替えまたは挑戦などの方向性を扱いうる。

### 原則

- 推薦順位そのものを表さない
- 方角または吉方位と同一視しない
- `history_theme`を単独で確定しない
- Meaning TranslationとAction Suggestionの補助文脈として利用する

---

## emotion_profile

### 意味責務

`emotion_profile`は、相談文に表れている感情トーンおよび強度の候補を整理する。

Recommendation ReasonやAction Suggestionの表現負荷を調整するために利用できる。

### 原則

- 感情を診断しない
- 本人が明示していない感情を断定しない
- 強い不安や疲労を課金または行動促進に利用しない
- 表示文言はKnowledgeのコピー原則に従う

---

## action_intent

### 意味責務

`action_intent`は、ユーザーが次に取りたい行動の候補を整理する。

例として、詳細を知る、保存する、経路を確認する、参拝する、振り返るまたは一度立ち止まるなどを扱いうる。

### 原則

- 行動を強制しない
- 行動しない選択を異常として扱わない
- Action SuggestionやCTAの補助文脈として利用する
- 正確なCTA判定や画面遷移は各Product文書と実装を正本とする

---

## decision_context

### 意味責務

`decision_context`は、ユーザーが何について整理または判断しようとしているかを表す。

例:

- 働き方を変えるか
- 関係を続けるか
- 休むか行動するか
- 支出するか守るか

判断の正解や結論は生成しない。

---

## constraint_profile

### 意味責務

`constraint_profile`は、行動や判断に影響する現実的な制約を整理する。

例:

- 時間
- 費用
- 移動
- 体力
- 人間関係
- 利用可能な選択肢

制約は、ユーザーの行動を否定するためではなく、無理のない提案へ調整するために利用する。

---

## outcome_hint

### 意味責務

`outcome_hint`は、ユーザーが相談を通して望んでいる着地点の候補を整理する。

例:

- 判断材料を得たい
- 気持ちを整理したい
- 少し落ち着きたい
- 次の一歩を考えたい

結果の実現や効果を保証しない。

---

## 後続レイヤーとの接続

### Meaning Translation

Consultation Interpreterで整理した状態、目的、方向、感情、判断対象および制約を、神社文脈、`history_theme`、ActionおよびReflectionへ接続する。

変換関係は`docs/product/meaning-translation-mapping.md`を参照する。

### Recommendation

Consultation Interpreterは、推薦候補の抽出や順位決定に利用できる文脈を提供する。

Score、Weight、Ranking、fallbackおよび一致判定の物理ロジックは、Backend実装とテストを正本とする。

### Recommendation Reason

Recommendation Reasonは、構造化された解釈結果と神社情報を利用し、「なぜこの提案なのか」を説明する。

Consultation Interpreter自体は推薦コピーを生成しない。

### Action Suggestion

Action Suggestionは、行動意図、判断対象、制約および望む着地点を参照し、次に取りやすい小さな行動へ接続する。

出力契約は`docs/product/action_suggestion_v4.md`を参照する。

---

## 責務境界

### Product

Productでは以下を管理する。

- 解釈フィールドの意味
- 各フィールドの体験上の役割
- 後続レイヤーとの接続
- 断定を避ける原則
- 行動負荷を上げない原則

### Core

以下は`docs/core/`配下の正本文書を参照する。

- Consultation InterpretationとMeaning Translationの構造的な接続
- Recommendation全体のデータフロー
- Frontend、BFFおよびBackendの技術責務
- Source of Truth
- 推薦時点の文脈保持

### Backend・実装

以下は関連するBackend実装とテストを正本とする。

- 実装ファイル名
- 関数名
- 正確な出力Schema
- Fieldのキーと型
- 必須・任意条件
- 分類語彙
- keywordおよびregex判定
- fallback
- ScoreおよびRankingへの反映
- 保存処理

### Analytics

以下は`docs/analytics/`配下の正本文書を参照する。

- Event名
- Payload
- Property
- Funnel
- KPI
- 集計方法
- Recommendation品質の評価方法

### Knowledge

以下は`docs/knowledge/`配下の正本文書を参照する。

- 推薦理由の表現原則
- 感情や状態を断定しないコピー
- ActionおよびReflectionの表現ガイド
- 神社FactとMeaningの扱い

---

## 責務外

本書では以下を管理しない。

- 推薦順位
- Score Weight
- 神社DB構造
- API Endpoint
- UIレイアウト
- Component構造
- Analytics KPIの具体値
- 実装手順
- テストケース一覧
- PR計画
- 作業履歴

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/consultation-theme-taxonomy.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/action_suggestion_v4.md`
- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/knowledge/recommendation-copy-guide.md`
- `docs/knowledge/action-guide.md`
- `docs/knowledge/reflection-guide.md`

---

## 更新ルール

- 本書はConsultation Interpreterの解釈フィールドと意味責務を管理する。
- 正確なキー、型、Schema、生成処理およびfallbackは本書で重複管理しない。
- Score、Weight、RankingまたはAPI仕様は本書へ記載しない。
- KPI、Event、PayloadおよびFunnelはAnalytics文書で管理する。
- 解釈フィールドの追加、削除または意味変更がある場合のみ本書を更新する。
- 物理実装のみを変更した場合は、本書の意味契約へ影響があるかを確認する。
- TODO、PR計画、実装進捗、テスト手順および作業履歴は本書へ記載しない。
