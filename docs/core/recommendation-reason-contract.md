> **Status: Active**
>
> 本ドキュメントは、Recommendation ReasonのInput、Output、Fact / Interpretation / Action、保存、表示および互換責務を管理する正本である。
>
> 意味生成の正確な物理挙動は、関連するBackend実装およびテストを最終的な正本とする。

# Recommendation Reason Contract

## 目的

Recommendation Reasonは、
「なぜこの神社が今回の相談に対する候補なのか」を、
神社固有情報・相談解釈・次の行動へ分離して説明する。

本ドキュメントはRecommendation Reasonの
Input / Output / 保存 / 表示 / 互換責務を定義する正本とする。

## 対象範囲

### 対象

- Recommendation Reasonの入力
- Recommendation Reasonの出力
- Fact / Interpretation / Actionの責務
- reason_textの役割
- used_*の役割
- Runtime Snapshotへの保存
- Frontend表示Adapterとの境界
- Action Suggestionとの接続
- 互換維持方針

### 対象外

- 推薦順位の計算
- Recommendation Score
- Meaning Translationの変換規則
- Action Suggestionの出力契約
- UIレイアウト

## 全体構造

Recommendation Reasonは以下の3層から構成する。

```text
Fact
↓
Interpretation
↓
Action
```

### Fact

神社側の事実と、神社側に付与された意味文脈を説明する。

利用可能な主な入力:

- shrine_name
- deity
- shrine_history
- place_context
- goriyaku
- history_theme
- evidence

`history_theme`は神社の一次事実そのものではなく、
Stored情報を根拠として付与されたMeaning情報である。

現行の物理Schemaでは`fact`内で利用するが、
事実と意味文脈を同一視しない。

Factはユーザー状態の診断や行動提案を行わない。

### Fact表現強度（confidence / history_type）

Recommendation Reasonが`shrine_history`（および`deity`）をどの強度の文体で
表示するかは、Knowledge Fact側の2つの独立した軸から決まる。

- `confidence`（`temples.models.KNOWLEDGE_CONFIDENCE_CHOICES`）: そのFactを
  裏付けるSourceへの信頼度。「情報がどれだけ確からしいSourceに基づくか」を表す。
- `history_type`（`temples.models.ShrineHistory.history_type`）: そのFactが
  何を記述しているかの種別（`official_origin` / `founding` / `historical_event` /
  `tradition` / `regional_context` / `editorial_summary`）。「記述内容が確定した
  史実として書かれているか、伝承として書かれているか」を表す。

**両者は責務が別であり、どちらか一方だけでは他方を代替しない。**
`confidence=high`は「Sourceは信頼できる」ことしか意味せず、
「記述内容が史実として確定している」ことは意味しない。

**Tradition Output Contract（TRADITION_ALWAYS_HEDGED）**:
`history_type="tradition"`のFactは、`confidence`の値に関わらず断定表現
（assertive）を出してはならない。confidenceがどれだけ高くても、伝承として
書かれた内容は伝承としての文体（例:「〜と伝えられています」）で表示する。

この制御はKnowledge Fact`content`本文が手動でhedge表現を含んでいるかには
依存しない。`history_type="tradition"`である事実だけで、Reason生成側
（`backend/temples/services/recommendation_reason_v4.py`の
`_apply_tradition_hedge_floor()`）が表現強度の下限を強制する。
これにより、執筆者が`content`のhedge表現を書き忘れた場合でも
伝承が史実であるかのように出力される事故を構造的に防ぐ。

`history_type="founding"`は既存Pilot（Score v3以前）から現行文体
（confidenceに応じたassertive/weakened/suppressed）のまま維持し、
本契約の対象に含めない。`founding`は「創建の一次的な由緒」という
既存の意味合いで使われており、`tradition`（Source自身が伝承と明記した記述）
とは別カテゴリとして扱う。両者を混同して`history_type`を選択しない。

### Interpretation

相談内容をどのような文脈として受け取ったかを説明する。

利用可能な主な入力:

- consultation_axis
- need_profile
- state_profile
- direction_profile
- emotion_profile
- historical_interpretation
- translated history_theme

Interpretationは神社の事実を新たに断定せず、
Actionを直接指示しない。

### Action

Recommendation Reasonから次の小さな行動へ接続する。

利用可能な主な入力:

- action_context
- reflection_question_seed
- action_intent
- constraint_profile
- outcome_hint

Actionは推薦順位を説明せず、
神社の歴史や相談解釈を繰り返さない。

## Input Contract

Recommendation Reasonの正規化済み主入力は、`recommendation_input_profile`とする。

`recommendation_input_profile`は、主に以下の入力を統合する。

- interpretation_profile
- translation_result
- candidate_profile
- score_v2_fields

個別入力は生成元ごとの責務を持つが、
Recommendation Reason生成時には`recommendation_input_profile`を正規化境界として扱う。

## Output Contract

Recommendation Reasonの出力は以下のキーで構成する。

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

### reason_text

Fact → Interpretation → Actionを、
ユーザー向けに一つの文章へ連結した表示候補。

reason_textは意味生成結果であり、
Frontendの最終レイアウトや表示優先順位を決定しない。

### fact

神社側の説明に利用した構造化情報。

### interpretation

相談内容の解釈として生成した構造化情報。

### action

次の小さな行動への接続情報。

### used_fact

Fact生成で実際に採用した入力の監査情報。

### used_interpretation

Interpretation生成で実際に採用した入力の監査情報。

### used_action

Action生成で実際に採用した入力の監査情報。

### source

各層の生成元を示す。

### quality

Recommendation Reasonの入力充足度・固有性を観測する品質情報。

## 意味生成の正本

BackendにおけるRecommendation Reasonの意味生成正本は、

```text
backend/temples/services/recommendation_reason_v4.py
```

とする。

FrontendはRecommendation Reasonの意味を独自に再解釈しない。

## Frontendとの境界

Frontendは表示Adapterとして以下を担当する。

- APIレスポンスの正規化
- 表示領域ごとの分割
- 文字数調整
- legacy fallback
- UI描画

Frontendは以下を担当しない。

- Factの新規生成
- Consultation Interpretationの再生成
- history_themeの再判定
- Recommendation Reasonの意味正本化
- 推薦順位の再計算

### 主理由と補助情報の共通表示契約

Webとモバイルは次の順序で表示する。

1. `相談内容・ご利益との一致`
2. `この神社を選んだ理由`
3. 条件が揃い、Backendが`direction_reference`を返した場合のみ`方位の参考情報`

1と2はRecommendation Reason領域、3は独立した補助情報領域である。`direction_reference`、方位一致状態、方角、方位加点を1または2の文章生成へ入力してはならない。

- 一致: 方位カード内で一致文言を表示する。
- 不一致: 方位カード内で不一致文言を表示する。主理由の順位や強さは変更しない。
- 情報なし: 方位カード全体を表示しない。
- 1と2が同一文言の場合、2を重複表示しない。
- 方位カードとRecommendation Reasonで同じ方位説明を重複表示しない。

表示Adapterは、主理由または通常理由へ混入した`方位`、`方角`、`吉方位`などの方位表現を表示対象から除外する。宗教的効果や結果を保証する断定表現も表示しない。

### 目標とする表示優先順位

Frontendは、利用可能なBackend生成値を優先する。

1. Backend Recommendation Reason構造化出力
2. Backend reason_text
3. Recommendation Snapshot内の既存説明
4. legacy Frontend生成値
5. 安全なfallback

現行Frontendにはlegacy生成経路が残っている。

本優先順位は移行後の責務順序を示すものであり、
現行実装がすべてこの順序へ統一済みであることを意味しない。

legacy fallbackは互換維持のため残すが、
新しい意味生成の正本として扱わない。

## _explanation_payloadとの境界

_explanation_payloadは、
推薦順位根拠・一致タグ・表示補助を保持する構造化Payloadである。

主な責務:

- matched_need_tags
- primary_reason
- secondary_reasons
- score
- history_context
- action_suggestions
- original_reason

Recommendation Reasonは、
Fact / Interpretation / Actionを組み合わせて
「なぜこの神社か」を意味として説明する。

両者は同一のPayloadではない。

## 保存方針

Recommendation生成時に利用した値は、
必要に応じてRuntime Snapshotへ保存する。

### 現行保存

現行実装では、Recommendation itemまたはRuntime Snapshotに、
以下の全部または一部を保持する。

- recommendation_reason_v4
- recommendation_reason_quality
- history_theme
- matched_need_tags
- score components
- action suggestion
- evidence

### 構造化出力の保存

構造化出力のうち、表示に必要な最小集合（`recommendation_reason_v4_detail`、後述）はRuntime Snapshot（`ConciergeThread.recommendations` / `recommendations_v2`）へ恒久保存する。これは実装済みであり未確定ではない。

`used_fact` / `used_interpretation` / `used_action` / `source` / `quality`は、Backend内部の監査・品質計測専用として扱い、Runtime Snapshotへは保存しない。理由・詳細はAnalytics用途の確認が済んでいないため。

保存対象を追加する場合は、
Payload容量、過去互換、Analytics用途を確認した上で
別Contract変更として扱う。

過去Snapshotは、神社情報や生成ロジックが更新されても再計算しない。

## recommendation_reason_v4_detail（Frontend表示Adapter契約）

`recommendation_reason_v4_detail`は、`build_recommendation_reason_v4()`の出力から表示に必要な項目のみを抜き出した、Web/Mobile共通のFrontend向け表示契約である。

生成元: `backend/temples/services/concierge_chat.py`の`_attach_recommendation_reason_quality()`。

### Output

```json
{
  "version": "v4",
  "reason_text": "string",
  "fact": { "...": "build_recommendation_reason_v4()のfactと同一" },
  "interpretation": { "...": "同上のinterpretationと同一" },
  "action": { "...": "同上のactionと同一" }
}
```

- `reason_text`は、常に同一itemの`recommendation_reason_v4`（フラットな文字列field）と一致する。
- `used_fact` / `used_interpretation` / `used_action` / `source` / `quality`は含まない（Backend内部専用）。

### 付与対象

`recommendations`および`recommendations_v2`の両方の各itemへ、shrine_id/id/nameで対応付けて付与する。

### 保存

`recommendation_reason_v4_detail`は、Chat API応答生成時に他のitem fieldと同様に`ConciergeThread.recommendations` / `recommendations_v2`（JSONField）へ保存される。History取得時（`ConciergeThreadDetailSerializer`）は、保存済みのJSONをそのまま返す（再計算しない）。

このPR以前に作成されたThreadには`recommendation_reason_v4_detail`が含まれない。Frontend側はfield欠落時に旧表示へfallbackする前提で実装する（`docs/product/recommendation-v4-frontend-adapter-contract.md`参照）。

### Frontend表示Adapterとの境界

`recommendation_reason_v4_detail`の各fieldをどの文型・見出しで表示するか（例: deity/shrine_history/goriyaku/history_themeの優先順位、place_contextを表示に使わない等）はFrontend側Adapterの責務であり、本ドキュメントでは定義しない。Web/Mobileそれぞれの実装契約は`docs/product/recommendation-v4-frontend-adapter-contract.md`を参照する。

## Action Suggestionとの接続

Recommendation ReasonはAction Suggestionへ入力を提供できる。

ただし、Action Suggestionの最終出力契約は、

```text
docs/product/action_suggestion_v4.md
```

を正本とする。

Recommendation Reason内のactionは、
Recommendation Reason文章を構成する一層であり、
Action Suggestion全体と同一ではない。

## 禁止事項

- Factに心理診断を書く
- Interpretationに神社の未確認事実を書く
- Actionに宗教的効果保証を書く
- 内部タグをそのまま表示する
- Frontendを意味生成の正本にする
- _explanation_payloadとRecommendation Reasonを同一視する
- Snapshotを後から暗黙に再計算する
- 方位一致をRecommendation Reasonの主理由として表示する
- 「吉方位なので行くべき」「必ず良い結果になる」「運気が上がる」「願いが叶う」と断定する
- `history_type="tradition"`のFactを、confidenceに関わらず断定表現(assertive)で出す

## 互換維持方針

以下の既存物理名は直ちに変更しない。

- recommendation_reason_v4
- reason_text
- fact
- interpretation
- action
- used_fact
- used_interpretation
- used_action
- _explanation_payload
- recommendationReasonDetail
- consultationSummary
- shrineMeaning
- actionMeaning

概念上の責務を先に固定し、
物理名変更はAPI Version更新時に別途判断する。

## 品質基準

Recommendation Reasonは最低限以下を満たす。

- 神社固有情報が存在する
- 相談解釈との接続が説明できる
- 事実・解釈・行動が分離されている
- 内部キーが表示されない
- 宗教的・心理的効果を断定しない
- Action Suggestionと矛盾しない

Recommendation可能条件は、`docs/core/recommendation-readiness.md`を正本とする。

## 関連ドキュメント

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/recommendation-readiness.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/action_suggestion_v4.md`
- `docs/knowledge/shrine-profile-spec.md`
- `docs/knowledge/recommendation-copy-guide.md`
