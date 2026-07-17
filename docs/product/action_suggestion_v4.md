> **Status: Active**
>
> 本ドキュメントは、KAMI MUSUBIにおけるAction Suggestion v4の入力・出力項目の意味、生成原則および後続体験との接続を管理する正本文書である。
>
> 正確なSchema、キー、型、Enum、fallback、生成処理および利用条件は、関連するCore文書、Backend実装およびテストを最終的な正本とする。

# Action Suggestion v4 Contract

## 目的

Action Suggestion v4は、Consultation Interpreter、Meaning TranslationおよびRecommendation Reasonで整理された文脈を受け取り、ユーザーが次に取りやすい小さな行動へ接続する。

Action Suggestionは、ユーザーへ行動を命令するものではない。

相談内容、制約および望む着地点を踏まえ、詳細確認、保存、経路確認、参拝、振り返りまたは一度立ち止まる選択肢を提示する。

---

## 全体構造

```text
Consultation Interpreter
↓
Meaning Translation
↓
Recommendation Reason
↓
Action Suggestion
↓
Detail / Save / Route / Visit / Reflection / Pause
```

Action Suggestionは推薦理由を補完する行動レイヤーであり、神社の選定、推薦順位または推薦理由そのものを決定しない。

---

## 基本原則

- 実行可能な小さな行動を提示する
- ユーザーの判断を急がせない
- 行動しない選択を異常として扱わない
- 時間、費用、移動および体力などの制約を尊重する
- 結果、効果または運勢を保証しない
- 心理、医療、宗教または人生上の状態を断定しない
- 一度に提示する行動の負荷を上げすぎない
- FrontendでAction生成ロジックを重複実装しない

---

## 入力項目

Action Suggestionは、以下の意味文脈を参照できる。

| 入力項目 | 意味責務 |
|---|---|
| `decision_context` | ユーザーが整理または判断したい対象 |
| `constraint_profile` | 行動に影響する時間、費用、移動、体力などの制約 |
| `outcome_hint` | ユーザーが望んでいる着地点の候補 |
| `action_context` | Meaning Translationで整理された次に取りやすい行動文脈 |
| `reflection_question_seed` | 振り返り質問を生成するための意味上の手掛かり |

各入力項目の正確なキー、型、必須条件、生成処理およびfallbackは、Consultation Interpreter、Meaning Translationおよび関連するBackend実装・テストを正本とする。

---

## 出力項目

Action Suggestionは、以下の意味要素を返す。

| 出力項目 | 意味責務 |
|---|---|
| `primary_action` | 最初に提示する、最も取りやすい行動 |
| `secondary_action` | primary_actionを補完する別の選択肢 |
| `reflection_prompt` | 行動前後の整理を支援する短い問い |
| `action_source` | 行動提案がどの入力文脈に基づくかを示す根拠 |

正確なSchema、ネスト構造、キー、型、Enumおよびfallback値は、関連するBackend実装とテストを正本とする。

---

## primary_action

### 意味責務

`primary_action`は、ユーザーへ最初に提示する、最も負荷の小さい行動候補である。

### 原則

- 一つの主行動として理解できる内容にする
- 具体的な動詞を使用する
- 命令口調にしない
- 結果を保証しない
- 制約を無視した提案をしない
- 必要に応じて、行動ではなく整理や休止へ接続できる

---

## secondary_action

### 意味責務

`secondary_action`は、主行動とは異なる方向からユーザーの次の一歩を補完する。

### 原則

- primary_actionと同一内容を言い換えない
- primary_actionより著しく負荷を上げない
- 詳細確認、保存、経路確認、参拝、振り返りまたは休止へ接続できる
- secondary_actionを実行しなくても体験が成立する

---

## reflection_prompt

### 意味責務

`reflection_prompt`は、ユーザーが行動前後の考え、感覚または判断材料を整理するための短い問いである。

### 原則

- 一つの問いとして提示する
- 正解を求めない
- 回答を強制しない
- 心理状態を断定しない
- 宗教的な効果または意味を決めつけない
- 行動前または行動後の整理へ接続する

### Reflection入力UIとの境界

Action Suggestionの`reflection_prompt`は、Concierge結果画面などで回答できないプレビューとして表示される場合がある。

このプレビューは、ユーザーが実際に回答を保存できるReflection入力UIとは異なる。

Productでは、以下の体験を分離する。

| 体験 | 責務 |
|---|---|
| Action SuggestionのReflectionプレビュー | 次の振り返り観点を提示する |
| Reflection入力UI | ユーザーが回答し、記録として保存する |

Reflection入力UI、保存およびVisitとの接続は、`docs/product/visit-reflection-flow.md`を参照する。

正確なEvent名、Payload、Propertyおよび計測語彙は、`docs/analytics/`配下の正本文書を参照する。

---

## action_source

### 意味責務

`action_source`は、行動提案がどの相談文脈を主な根拠として生成されたかを示す。

主な根拠には以下が含まれうる。

- 判断対象
- 制約
- 望む着地点
- 行動文脈
- 振り返り質問の手掛かり
- 入力不足時の補完

### 原則

- ユーザーへ心理的な断定理由として表示しない
- 推薦順位の根拠として扱わない
- Debugやテストの物理仕様は本書では管理しない
- 正確なEnum、生成優先順位およびfallbackはBackend実装とテストを正本とする

---

## 行動の接続先

Action Suggestionは、以下の体験へ接続できる。

| 接続先 | 体験上の意味 |
|---|---|
| 詳細確認 | 神社情報と推薦理由を確認する |
| 経路確認 | 現地へ向かう可能性を検討する |
| 保存 | 後から見返せる状態にする |
| 参拝 | 訪問または参拝行動へ進む |
| 振り返り | 考えや行動後の変化を整理する |
| 休止 | 判断を急がず、一度立ち止まる |

正確な`action_type`のEnum、画面遷移、CTA判定および送信処理は、関連するFrontend・Backend実装とテストを正本とする。

---

## 入力不足時の原則

入力が不足している場合でも、ユーザー体験を破綻させない。

### 原則

- 強い行動を推測で提示しない
- 詳細確認や保存など、負荷の低い選択肢を優先する
- ユーザー状態を推測して補完しない
- Schemaを維持する物理処理はBackend実装とテストを正本とする

---

## 文言原則

### 使用する方向

- 詳細を確認してみる
- 後から見返せるように保存する
- 無理のない範囲で経路を確認する
- 今考えていることを一つ整理する
- 今日は一度立ち止まる

### 使用しない方向

- 必ず参拝しましょう
- この神社が正解です
- ここへ行けば運気が上がります
- 今すぐ決断してください
- あなたはこのような心理状態です

具体的なコピー原則は、`docs/knowledge/action-guide.md`および`docs/knowledge/recommendation-copy-guide.md`を参照する。

---

## 後続体験との接続

### Recommendation Reason

Recommendation Reasonは「なぜこの神社を提案するのか」を説明する。

Action Suggestionは、その説明を受けて「次に何を選べるか」へ接続する。

Action Suggestion自体は推薦理由を再生成しない。

### Shrine Detail

詳細確認を選択した場合は、神社の公開情報、相談文脈および個人向け補足を確認できる画面へ接続する。

神社詳細の責務は、`docs/product/shrine-detail-layer.md`を参照する。

### Visit・Reflection

参拝および振り返りへ進む場合は、VisitとReflectionの意味責務に従う。

詳細は`docs/product/visit-reflection-flow.md`を参照する。

---

## 責務境界

### Product

Productでは以下を管理する。

- 入力項目と出力項目の意味
- primary_actionとsecondary_actionの役割
- Reflectionプレビューと入力UIの体験境界
- 行動の接続先
- 行動負荷を上げない原則
- 断定、強制および結果保証を避ける原則

### Core

以下は`docs/core/`配下の正本文書を参照する。

- Consultation InterpreterからAction Suggestionまでの構造的な接続
- Recommendation全体のデータフロー
- Frontend、BFFおよびBackendの技術責務
- 推薦時点の文脈保持

### Backend・実装

以下は関連するBackend実装とテストを正本とする。

- 正確なInput / Output Schema
- キーと型
- Enum
- 必須・任意条件
- 生成順序
- action_typeの選択処理
- confidenceの算出
- fallback
- Debug情報
- 保存処理

### Frontend・実装

以下は関連するFrontend実装とテストを正本とする。

- CTAの表示
- Actionごとの画面遷移
- Reflectionプレビューの表示
- Access Levelによる表示差
- イベント送信処理

### Analytics

以下は`docs/analytics/`配下の正本文書を参照する。

- Event名
- Payload
- Property
- Funnel
- KPI
- Reflectionプレビューの計測
- Action別の利用状況
- Web / Mobileの送信差

### Knowledge

以下は`docs/knowledge/`配下の正本文書を参照する。

- Action文言の表現原則
- 命令、断定および結果保証を避けるコピー
- Reflection質問の表現ガイド
- 神社FactとMeaningの扱い

---

## 責務外

本書では以下を管理しない。

- 神社候補の選定
- Recommendation Ranking
- Recommendation Score
- Score Weight
- 推薦理由の生成処理
- API Endpoint
- UIレイアウト
- Component構造
- Event名とPayload
- KPIの具体値
- 実装手順
- テストケース一覧
- PR計画
- 作業履歴

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/recommendation-v4-interpreter-contract.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/shrine-detail-layer.md`
- `docs/product/visit-reflection-flow.md`
- `docs/core/architecture.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/knowledge/action-guide.md`
- `docs/knowledge/recommendation-copy-guide.md`
- `docs/knowledge/reflection-guide.md`
- `docs/analytics/action-suggestion-funnel.md`

---

## 更新ルール

- 本書はAction Suggestionの入力・出力項目の意味と生成原則を管理する。
- 正確なSchema、キー、型、Enum、fallbackおよび生成処理は本書で重複管理しない。
- Event、Payload、Property、FunnelおよびKPIはAnalytics文書で管理する。
- action_typeの追加、削除または意味変更がある場合は、本書への影響を確認する。
- 入力項目または出力項目の意味責務が変更された場合のみ本書を更新する。
- 物理実装のみを変更した場合は、本書の意味契約への影響を確認する。
- TODO、PR計画、実装進捗、テスト手順および作業履歴は本書へ記載しない。
