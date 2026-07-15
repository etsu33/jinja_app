# Recommendation Reason Responsibility Audit

## 目的

本監査は、KAMI MUSUBIにおけるRecommendation Reasonについて、Backend・Frontend・Runtime Snapshot・関連ドキュメントの責務を整理し、以下を明確にすることを目的とする。

- Recommendation Reasonの生成正本
- 通常APIへ返す情報
- Runtime Snapshotへ保存する情報
- Explanation Payloadとの境界
- Action Suggestionとの接続
- Frontend表示モデルとの境界
- 既存互換を維持した今後の修正方針

本書は監査記録であり、Recommendation Reasonの最終契約そのものではない。

Recommendation Reasonの正式なInput / Output Contractは、別途作成する正本文書で固定する。

---

## 監査対象

### Backend

- `backend/temples/services/recommendation_reason_v4.py`
- `backend/temples/services/concierge_chat.py`
- `backend/temples/services/concierge_explanation_payload.py`
- `backend/temples/services/concierge_explanations.py`
- `backend/temples/services/concierge_chat_ranking.py`
- `backend/temples/services/action_suggestion_builder.py`
- `backend/temples/services/concierge_history.py`
- `backend/temples/models.py`

### Frontend

- `apps/web/src/lib/concierge/buildRecommendationReasonViewModel.ts`
- `apps/web/src/lib/concierge/buildRecommendationNarrative.ts`
- `apps/web/src/lib/concierge/buildMeaningNarrative.ts`
- `apps/web/src/lib/shrine/buildShrineDetailModel.ts`
- `apps/web/src/viewmodels/conciergeToShrineList.ts`
- `apps/web/src/app/shrines/[id]/page.tsx`

### Docs

- `docs/knowledge/recommendation-copy-guide.md`
- `docs/core/narrative-guideline.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/action_suggestion_v4.md`
- `docs/audit/recommendation-terminology-contract.md`

---

## 結論

Recommendation Reasonの意味生成正本は、現行実装では以下である。

```text
backend/temples/services/recommendation_reason_v4.py
```

Recommendation Reason v4は、次の3層を生成する。

```text
Fact
↓
Interpretation
↓
Action
↓
reason_text
```

構造化出力には以下が含まれる。

```text
reason_text
fact
interpretation
action
used_fact
used_interpretation
used_action
source
quality
```

ただし、通常のRecommendation itemへ保存されているのは、構造化Payload全体ではない。

通常レスポンスでは次の形式で保存されている。

```text
recommendation_reason_v4: string
recommendation_reason_quality: object
```

完全な構造化Recommendation Reasonは、現状では主にdebug previewへ保持される。

```text
_debug.reason_v4_preview[].preview
```

このため、Recommendation Reason v4には以下の状態が存在する。

```text
生成時
= 構造化dict

通常API・通常Recommendation
= reason_text文字列

debug
= 構造化dict
```

---

## Recommendation Reasonの責務

Recommendation Reasonは、推薦順位そのものを決定するものではない。

Recommendation Reasonの責務は、選定済みの神社について、以下を説明可能な形へ変換することである。

```text
神社固有の根拠
+
相談内容の解釈
+
次に取りやすい行動
```

### Fact

Factは、推薦理由に利用する神社側の根拠を扱う。

主な入力:

- `deity`
- `shrine_history`
- `place_context`
- `goriyaku`
- `history_theme`
- `visit_style_tags`
- `evidence`

Factは以下を行わない。

- ユーザー状態の断定
- 相談内容の解釈
- 次の行動の提案
- 宗教的効果の保証

### Interpretation

Interpretationは、相談内容とMeaning Translationを接続し、今回の相談をどのように受け取ったかを説明する。

主な入力:

- `consultation_axis`
- `need_profile`
- `state_profile`
- `historical_interpretation`
- `history_theme`
- `meaning_translation`

Interpretationは、Knowledge上の以下を内包する。

```text
Meaning
+
User Connection
```

Interpretationは以下を行わない。

- 神社固有事実の新規生成
- 神社の由緒や祭神の断定
- Actionの記述
- 心理診断

### Action

Actionは、ユーザーが次に取りやすい一歩を提示する。

主な入力:

- `action_context`
- `reflection_question_seed`
- `action_intent`
- Recommendation Reasonの`action`
- 制約・判断・望む結果の補助情報

Actionは以下を行わない。

- Factの再説明
- Interpretationの繰り返し
- 効果保証
- 行動の強制

### reason_text

`reason_text`は、Fact・Interpretation・Actionを表示可能な一つの文章として統合した結果である。

```text
reason_text
=
Fact
+
Interpretation
+
Action
```

`reason_text`はRecommendation Reasonの表示用文章であり、構造化入力や生成根拠そのものではない。

---

## Backend責務

### Recommendation Reason生成

正本候補:

```text
backend/temples/services/recommendation_reason_v4.py
```

担当:

- Fact生成
- Interpretation生成
- Action生成
- reason_text生成
- used_*生成
- quality生成
- source生成

### Explanation Payload

対象:

```text
backend/temples/services/concierge_explanation_payload.py
```

`_explanation_payload`はRecommendation Reasonとは別責務である。

主な担当:

- `matched_need_tags`
- `primary_need_tag`
- `primary_reason`
- `secondary_reasons`
- `history_context`
- `action_suggestions`
- Score情報
- `original_reason`

`_explanation_payload`は自然文の最終生成を担当しない。

したがって、Recommendation Reasonへ統合して廃止する対象ではない。

### Ranking Reason

対象:

```text
backend/temples/services/concierge_chat_ranking.py
```

Ranking Reasonは、候補選定時に利用する短い理由・順位根拠を扱う。

Recommendation Reasonとは以下が異なる。

```text
Ranking Reason
= なぜ順位が上がったか

Recommendation Reason
= なぜこの神社を提案するのか
```

Ranking ReasonはRecommendation Reasonへ完全統合しない。

### Chat Explanation

対象:

```text
backend/temples/services/concierge_explanations.py
```

Chat Explanationは既存Chat表示との互換・Presentationを担当している。

Recommendation Reason v4との重複コピーが存在する可能性はあるが、今回の監査では廃止を決定しない。

### Action Suggestion

対象:

```text
backend/temples/services/action_suggestion_builder.py
```

Action Suggestion v4は以下を入力として受け取れる。

```text
recommendation_input_profile
interpretation_profile
meaning_translation
recommendation_reason_v4
```

ただし、`recommendation_reason_v4`引数は構造化dictを想定している。

```python
recommendation_reason_v4: dict[str, Any] | None
```

一方、通常のRecommendation itemへ保存されている値は文字列である。

```text
recommendation_reason_v4: string
```

この型差により、通常経路ではRecommendation Reasonの`action`層をAction Suggestionが構造化データとして利用できない可能性がある。

---

## Frontend責務

### Backend Recommendation Reasonの利用

FrontendではBackendの以下を文字列として扱っている。

```text
recommendation_reason_v4?: string | null
```

主な参照:

```text
apps/web/src/viewmodels/conciergeToShrineList.ts
```

したがって、現行Frontend契約でも`recommendation_reason_v4`は完成済み文章として認識されている。

### Recommendation Reason ViewModel

対象:

```text
apps/web/src/lib/concierge/buildRecommendationReasonViewModel.ts
```

Frontendでは以下の表示用情報を再生成している。

```text
heroMeaningCopy
consultationSummary
shrineMeaning
actionMeaning
```

これらはBackend Recommendation Reasonの構造化出力をそのまま表示しているわけではない。

Frontend側で、以下の情報を組み合わせて詳細表示用ViewModelを生成している。

- Recommendation item
- breakdown
- reason_facts
- need tags
- deepReason
- Shrine Meaning
- fallback copy

したがって、現行Frontendは単なる表示Adapterではなく、一部の意味・コピー生成責務を持つ。

### recommendationReasonDetail

`recommendationReasonDetail`は神社詳細画面での優先表示入力である。

主な構造:

```text
heroMeaningCopy
consultationSummary
shrineMeaning
actionMeaning
```

詳細画面では、原則として`recommendationReasonDetail`が優先される。

ただし、以下のfallbackが存在する。

```text
recommendationReasonDetail
↓
conciergeDeepReason
↓
conciergeReason
↓
shrineMeaningPayloadV2
↓
Frontendローカル生成
```

このfallbackは既存Payload互換を維持する一方、表示正本を分かりにくくしている。

### Frontend再生成の現行理由

Frontend再生成は、Backendの`recommendation_reason_v4`が文字列のみであり、詳細画面で必要な以下の分割済み情報を受け取れないために存在する。

```text
相談内容の要約
神社の意味
次の行動・問い
Hero表示文
```

したがって、Backendから構造化Recommendation Reasonを通常契約として提供するまでは、Frontend ViewModelを即時廃止できない。

---

## Runtime Snapshot

Docsでは、Recommendation生成時点のReason・Action・MeaningをRuntime Snapshotへ保存する方針が記載されている。

現行実装では、以下の保存が確認できる。

```text
recommendation_reason_v4: string
recommendation_reason_quality: object
```

一方、以下の完全な構造は通常Snapshotへ保存されていない可能性が高い。

```text
fact
interpretation
action
used_fact
used_interpretation
used_action
source
```

このため、現行Runtime Snapshotは、Recommendation Reasonの表示文章と品質指標は保持できるが、生成時の全根拠を完全には再現できない。

過去Snapshotは保存後に再計算しない方針であるため、構造化Reasonを保存するかどうかは、Contractで明示的に決定する必要がある。

---

## Docs責務

### Recommendation Copy Guide

対象:

```text
docs/knowledge/recommendation-copy-guide.md
```

担当:

- 推薦コピーの順序
- Fact / Meaning / User Connectionの分離
- 禁止表現
- 神社固有性
- コピー品質

判定:

```text
Active / Reference
```

Recommendation ReasonのInput / Output Schema正本ではない。

### Meaning Layer Connection

対象:

```text
docs/core/meaning-layer-connection.md
```

担当:

- Meaning LayerとRecommendationの接続
- Meaning LayerとComposerの境界
- Runtime Snapshotへの接続方針

判定:

```text
Active / Reference
```

Recommendation Reason自体のSchemaは扱わない。

### Meaning Translation Mapping

対象:

```text
docs/product/meaning-translation-mapping.md
```

担当:

- Consultation InterpretationからMeaning Translationへの変換
- Meaning TranslationからRecommendationへの入力
- history_theme・Action・Reflectionへの接続

判定:

```text
Active / 要修正
```

Runtime Snapshotへ`recommendation_reason`を保存すると記載されているが、構造化Reasonか文字列かが明確ではない。

実装では通常、`recommendation_reason_v4`の文字列が保存される。

### Action Suggestion v4

対象:

```text
docs/product/action_suggestion_v4.md
```

担当:

- Action SuggestionのInput / Output
- Action生成ルール
- ActionとRecommendationの境界

判定:

```text
Active / 正本
```

Recommendation Reason Contractから参照する。

---

## P0

P0は、Recommendation Reason Contract作成時に必ず固定する必要がある不整合である。

### P0-1：同一名称で型が異なる

通常Recommendation item:

```text
recommendation_reason_v4: string
```

Action Suggestion入力:

```text
recommendation_reason_v4: dict
```

同一名称が、呼び出し経路によって文字列と構造化dictの両方を意味している。

この状態では、呼び出し側が名前だけから型と責務を判断できない。

#### 修正候補

既存互換を優先する場合、以下のように分離する案が有力である。

```text
recommendation_reason_v4
= 既存互換の表示用文字列

recommendation_reason_v4_payload
= 構造化Recommendation Reason
```

または、より明示的に以下とする。

```text
recommendation_reason_v4_text
recommendation_reason_v4_payload
```

ただし、既存の`recommendation_reason_v4`を即時renameすると、API・Frontend・Snapshot互換へ影響する。

そのため、既存フィールドを維持し、構造化Payloadを追加する方針が安全と考えられる。

最終名称はRecommendation Reason Contractで決定する。

---

### P0-2：構造化Reasonが通常経路へ保存されない

`build_recommendation_reason_v4()`は完全な構造化Payloadを生成するが、通常Recommendation itemには`reason_text`と`quality`だけが保存される。

このため以下を通常経路で再利用できない。

- `fact`
- `interpretation`
- `action`
- `used_fact`
- `used_interpretation`
- `used_action`
- `source`

Action SuggestionやFrontend表示が構造化Reasonを利用するには、別途同様の情報を再構築する必要がある。

Recommendation Reason Contractでは、通常レスポンスおよびRuntime Snapshotへ保存する最小構造を決定する必要がある。

---

### P0-3：Runtime Snapshotの保存契約が不明確

DocsではRecommendation ReasonをRuntime Snapshotへ保存する方針がある。

ただし、以下のどちらを保存するか明文化されていない。

```text
表示文章のみ
```

または

```text
構造化Reason全体
```

現行実装では表示文章とqualityのみが中心であり、Docsとの解釈差が生じている。

Recommendation Reason Contractでは以下を固定する必要がある。

- Snapshotへ保存するフィールド
- 表示文章
- 構造化Fact / Interpretation / Action
- used_*の保存要否
- qualityの保存要否
- sourceの保存要否
- 過去Snapshotの互換方針

---

### P0-4：意味生成正本と表示生成正本の境界が未定義

BackendではRecommendation Reasonを生成している。

Frontendでも以下を再生成している。

- `consultationSummary`
- `shrineMeaning`
- `actionMeaning`
- `heroMeaningCopy`

現状はBackendの構造化出力が通常提供されないため、Frontend再生成には合理性がある。

ただし、どちらが意味生成正本で、どちらが表示Adapterなのかが正本文書で固定されていない。

Recommendation Reason Contractでは、以下を原則として固定する必要がある。

```text
Backend
= 意味生成正本

Frontend
= 表示Adapter・fallback
```

ただし、既存Frontend生成ロジックは段階的に移行する。

---

## P1

P1は、P0のContract確定後に段階的に整理できる項目である。

### P1-1：Frontendの詳細表示再生成

`buildRecommendationReasonViewModel.ts`は、詳細表示用のコピーと構造を生成している。

Backend構造化Reasonが通常提供されるようになった場合、Frontendは以下へ縮小できる可能性がある。

```text
Backend構造化Reason
↓
Frontend ViewModel
↓
UI表示
```

Frontendで意味を再生成するのではなく、表示形式への変換のみを担当する。

---

### P1-2：recommendationReasonDetailとBackend Schemaの対応

Frontendの`recommendationReasonDetail`は以下を持つ。

```text
heroMeaningCopy
consultationSummary
shrineMeaning
actionMeaning
```

Backendは以下を持つ。

```text
fact
interpretation
action
reason_text
```

両者の対応は明示的ではない。

Contract確定後に、次の対応を定義する必要がある。

```text
consultationSummary
← interpretation

shrineMeaning
← fact + meaning

actionMeaning
← action

heroMeaningCopy
← reason_textまたは表示用summary
```

---

### P1-3：legacy fallbackの整理

詳細画面には以下のfallbackが残っている。

```text
recommendationReasonDetail
conciergeDeepReason
conciergeReason
shrineMeaningPayloadV2
Frontendローカル生成
```

P0契約と通常Payloadが安定した後、各fallbackの利用状況を計測し、未使用経路を段階的に削除する。

---

### P1-4：actionMeaningの命名

`actionMeaning`は、実態としてActionまたはReflection Questionを表す。

名称上はMeaning Layerの一部に見えるため、責務が分かりにくい。

将来候補:

```text
actionCopy
nextActionCopy
reflectionPromptCopy
```

ただし、Frontendの既存型・テスト・表示契約へ影響するため、今回変更しない。

---

### P1-5：Chat Explanationとのコピー重複

`concierge_explanations.py`とRecommendation Reason v4で、類似する説明文を生成している可能性がある。

ただし、Chat表示・カード表示・詳細表示の用途差があるため、単純統合は行わない。

Contract確定後、以下を分類する。

- Ranking理由
- Card理由
- Chat理由
- 詳細Reason
- Actionへの入力

---

### P1-6：debug previewの通常契約化

完全な構造化Reasonは現状debug previewで確認できる。

この構造を通常API・Snapshotへ追加する場合、debug固有情報を含めず、安定Schemaとして切り出す必要がある。

---

## 正本候補

Recommendation Reason専用の正本文書は現時点で存在しない。

新規正本候補は以下とする。

```text
docs/core/recommendation-reason-contract.md
```

### Coreに配置する理由

Recommendation Reasonは以下を横断する。

- Recommendation
- Meaning Translation
- Knowledge
- Action Suggestion
- Runtime Snapshot
- Frontend表示
- Analytics・品質評価

Product固有の画面仕様やKnowledge固有のコピー規則だけではなく、システム全体の責務境界とデータ契約を定義するため、Coreへ配置する。

### 正本文書で固定する内容

```text
docs/core/recommendation-reason-contract.md
```

では、最低限以下を固定する。

1. Recommendation Reasonの目的
2. 対象範囲・対象外
3. Fact / Interpretation / Actionの定義
4. `reason_text`の定義
5. 構造化Payload Schema
6. 表示用文字列フィールド
7. 通常APIの契約
8. Runtime Snapshotの保存対象
9. quality / source / used_*の扱い
10. `_explanation_payload`との境界
11. Ranking Reasonとの境界
12. Chat Explanationとの境界
13. Action Suggestionへの接続
14. Frontend ViewModelとの境界
15. 旧Payload互換
16. Version管理
17. fallback方針
18. 完了条件

---

## 関連文書の正本・Reference分類

| 文書 | 分類 | 責務 |
|---|---|---|
| `docs/core/recommendation-reason-contract.md` | 新規正本候補 | Recommendation ReasonのSchema・責務・保存・接続 |
| `docs/knowledge/recommendation-copy-guide.md` | Active / Reference | 推薦コピーの文体・禁止表現・品質原則 |
| `docs/core/narrative-guideline.md` | Active / Reference | KAMI MUSUBI全体の断定回避・表示原則 |
| `docs/core/meaning-layer.md` | Active / Reference | Meaning Layerの概念定義 |
| `docs/core/meaning-layer-connection.md` | Active / Reference | Meaning LayerとRecommendation・Composerの接続 |
| `docs/product/meaning-translation-mapping.md` | Active / 要修正 | Meaning Translationの入力・出力・Runtime接続 |
| `docs/product/action_suggestion_v4.md` | Active / 正本 | Action SuggestionのInput / Output Contract |
| `docs/audit/recommendation-terminology-contract.md` | Audit | 用語判断の履歴 |
| 本書 | Audit | Recommendation Reason責務監査の履歴 |

---

## 正本作成後の修正候補

Recommendation Reason Contract作成後、以下を順番に検討する。

### 実装候補1

通常Recommendation itemへ構造化Recommendation Reasonを追加する。

例:

```text
recommendation_reason_v4
recommendation_reason_v4_payload
recommendation_reason_quality
```

既存文字列フィールドは互換維持する。

### 実装候補2

Action Suggestionへ構造化Recommendation Reasonを渡す。

```text
recommendation_reason_v4_payload.action
```

を参照可能にする。

### 実装候補3

Runtime Snapshotへ構造化Reasonの最小項目を保存する。

### 実装候補4

Frontend ViewModelをBackend構造化Reason優先へ変更する。

### 実装候補5

利用されなくなったlegacy fallbackを削除する。

---

## Codex実装候補

現時点ではCodexへ直接実装を依頼しない。

先にRecommendation Reason Contractで以下を決定する必要がある。

- 構造化Payloadのフィールド名
- 通常APIへ返すSchema
- Snapshot保存対象
- 旧文字列フィールドの互換期間
- Frontendへ渡す最小構造
- Action Suggestionの入力契約

Contract確定後、複数ファイルをまたぐ以下の実装はCodex主担当とする。

```text
構造化Recommendation Reasonを通常RecommendationとRuntime Snapshotへ追加し、
既存のrecommendation_reason_v4文字列を維持したまま、
Action SuggestionとFrontendが段階的に構造化Payloadを利用できるようにする
```

---

## 今回変更しないもの

- `recommendation_reason_v4`既存文字列フィールド
- Backend API物理名
- DB・migration
- Runtime Snapshot Schema
- Frontend ViewModel
- `recommendationReasonDetail`
- `actionMeaning`
- `_explanation_payload`
- Ranking Reason
- Chat Explanation
- Action Suggestion実装

本監査PRは文書追加のみとする。

---

## 監査完了判定

Recommendation Reasonの生成・保存・表示・Snapshot・Action Suggestion・Frontendとの責務差を確認し、P0 / P1および新規正本候補を確定した。

以上により、本監査は完了とする。
---

## 監査結果

Recommendation Reasonの意味生成正本は、現行実装では`recommendation_reason_v4.py`である。

ただし、完全な構造化Reasonは通常API・Runtime Snapshotへ保存されず、通常契約では表示用文字列とqualityのみが中心となっている。

その結果、Action SuggestionとFrontendはRecommendation Reasonの構造化結果を十分に再利用できず、別経路から同様の情報を再構築している。

次の作業では、

```text
docs/core/recommendation-reason-contract.md
```
を作成し、Recommendation ReasonのSchema・保存・互換・表示境界を正本として固定する。

Recommendation Reasonの正式なInput / Output / 保存 / 表示 / 互換責務は、
`docs/core/recommendation-reason-contract.md`を正本とする。
