# Knowledge Base Consistency Audit

## 1. 目的

## 2. 監査対象


## 3. 監査上の記載区分

本監査では、事実・推測・設計判断を混在させないため、以下の区分で記録する。

### 3.1 事実（Fact）

リポジトリ内のドキュメント、コード、DB定義から直接確認できる内容。

例：

- `history_theme` は `Shrine` モデルに保持されている
- `goriyaku_tags` が現行DBに存在する
- `Recommendation Readiness` が `shrine-data-guide.md` に定義されている

監査では、確認可能な内容のみを記載する。

---

### 3.2 実装事実（Implementation Fact）

現行実装の挙動から確認できる内容。

ドキュメントと一致しているかは問わず、実際のコードを正本として記録する。

例：

- Recommendation生成時に `history_theme` が利用されている
- `goriyaku_tag_ids` がスコア計算へ渡されている
- `consultationSummary` が表示用コピーとして生成されている

ドキュメントとの差異がある場合は、その差異も併せて記録する。

---

### 3.3 推測（Inference）

事実および実装事実から合理的に推測できる内容。

十分な根拠があるものの、コードや仕様として明文化されていない事項を指す。

例：

- 将来的に `culture_translation` が Meaning Layer に属すると考えられる
- `confidence` は Trust Layer の責務として扱われる可能性が高い

推測は、必ず根拠となる事実または実装事実を併記する。

---

### 3.4 仮説（Hypothesis）

今後検証が必要な設計案や改善案。

現時点では採用を決定していないものを記録する。

例：

- `Trust` を独立モデルとして分離する
- `Reflection` 専用モデルを追加する
- `Recommendation Readiness` を自動算出へ変更する

仮説は実装前提とせず、検証対象として扱う。

---

### 3.5 仕様判断（Design Decision）

本監査において採用する設計方針。

複数案を比較した結果、採用すると決定した内容を記録する。

例：

- Runtime情報は神社固定プロフィールへ保存しない
- Recommendationの責務は Meaning Layer と分離する
- Stored / Derived / Runtime / Governance の4分類を採用する

仕様判断は、以降のドキュメントおよび実装の基準（Single Source of Truth）として扱う。

## 4. 用語差分

### 4.1 目的

Knowledge Base 8文書で使用される用語を比較し、
表記揺れ・責務の重複・意味の不一致を抽出する。

Glossary を用語定義の正本（Single Source of Truth）とし、
他文書との差分を確認する。

### 4.2 監査対象

- README
- shrine-profile-spec
- shrine-data-guide
- meaning-layer-spec
- recommendation-copy-guide
- action-guide
- reflection-guide
- glossary

### 4.3 確認観点

- 表記揺れ
- 同義語
- 未定義用語
- 定義の不一致
- 責務の重複

### 4.4 監査結果

| 用語 | 定義元 | 利用箇所 | 差分 | 優先度 |
|------|--------|----------|------|--------|
| Consultation | glossary.md | glossary / shrine-profile-spec | Glossaryでは「相談内容を解析する処理」。Profileでは「誰に向いているか」を示すマッチング層として使われ、入力解析と一致結果が混在している | P0 |
| Consultation Layer | shrine-profile-spec.md | shrine-profile-spec | `matched_need_tags`、`consultation_axis fit`、`evidence`など、相談解析ではなくUser × Shrineの一致結果を扱っている | P0 |
| Recommendation | glossary.md | 全文書 | Glossaryでは「神社を推薦する文章」だが、他文書では推薦処理・結果・レイヤー全体を指す。Recommendation Reasonとの境界が曖昧 | P0 |
| Recommendation Reason | glossary.md / recommendation-copy-guide.md | recommendation-copy-guide / shrine-profile-spec | 「なぜこの神社か」を説明する表示文章として概ね一貫しているが、Recommendation自体の定義が文章になっているため責務が重複する | P0 |
| Recommendation Readiness | glossary.md / shrine-data-guide.md / shrine-profile-spec.md | 複数文書 | 品質段階として定義されているが、最小条件・Level条件・DB保持有無が未統一 | P0 |
| Recommendation Ready | recommendation-copy-guide.md | recommendation-copy-guide | `Recommendation Readiness`と異なる表記。状態名と判定体系の使い分けルールが存在しない | P0 |
| Reflection Ready | glossary.md | glossary / reflection-guide | `Recommendation Readiness`とは異なりReady表記を採用。命名規則が未統一 | P1 |
| Coverage | glossary.md / shrine-data-guide.md / shrine-profile-spec.md | 複数文書 | Glossaryでは「充足率・利用可能率」。Data GuideではSchema / Populated / Verified / Usableの4種類。Profile内の実測値がどのCoverageか明示されていない | P0 |
| Stored | glossary.md / shrine-profile-spec.md / 各Guide | 複数文書 | 定義自体は概ね一致。ただし物理DB保存済みと、将来保存すべき概念が混在する可能性がある | P0 |
| Derived | glossary.md / shrine-profile-spec.md / 各Guide | 複数文書 | Storedから生成する意味情報として概ね一致。`history_theme`と`culture_translation`はDerivedとして扱われる | P0 |
| Runtime | glossary.md / shrine-profile-spec.md / 各Guide | 複数文書 | 相談ごとに生成する情報として概ね一致。ただし推薦履歴へスナップショット保存することと、Shrineプロフィールへ保存しないことを分けて記述する必要がある | P0 |
| Governance | glossary.md / shrine-profile-spec.md / shrine-data-guide.md | 複数文書 | 品質・出典・運用管理として概ね一致。ReadinessとCoverageはGovernanceに属するが、物理保持方法は未確定 | P0 |
| Trust Layer | shrine-profile-spec.md | shrine-profile-spec / shrine-data-guide | 主要レイヤーとして定義される一方、Glossaryに定義がない | P1 |
| source / source_url | shrine-data-guide.md / ShrineMeaningPayloadV2 / ShrineInteractionLog / ActionEvent | Trust / Meaning / Behavior / Action | 情報出典、Meaning入力ブロック、行動流入元、Action流入元という複数の意味で使われている | P0 |
| verified_at | shrine-data-guide.md | shrine-data-guide / Trust関連 | Glossary未定義。神社単位・項目単位・出典単位のどこへ付与するか未確定 | P1 |
| confidence | shrine-profile-spec.mdの記載候補 / 監査計画 | 現行Knowledge Baseでは定義なし | grep結果0件。事実の信頼度、解釈の確信度、抽出処理の確信度のどれを示すか未定義 | P1 |
| evidence | glossary.md / shrine-profile-spec.md | Recommendation / Action / Reflection | 「推薦理由として採用した根拠」と定義されるが、事実データ・意味情報・Runtimeシグナルを含むため内部構造が未定義 | P1 |
| Reflection Prompt / reflection_prompt | glossary.md / shrine-profile-spec.md | glossary / profile / reflection-guide | 表示用語と内部項目名の差は許容可能だが、概念名と物理名の記載ルールが未定義 | P2 |
| consultation_axis fit / consultation_axis_fit | shrine-profile-spec.md / 監査文書 | profile / audit | 空白区切りとsnake_caseが混在。概念名か物理項目名か不明確 | P2 |

## 5. Stored / Derived / Runtime / Governance対応表

### 5.1 目的

Knowledge Base に登場する概念項目を、
Stored / Derived / Runtime / Governance の4分類へ整理する。

各項目の責務を統一し、
保存対象・計算対象・実行時のみ利用する情報を明確にする。

### 5.2 分類ルール

#### Stored

DBへ永続保存する情報。

対象例：

- Shrine Profile
- goriyaku_tags
- deity
- place_context

---

#### Derived
- history_theme
- culture_translation
- shrine_meaning_profile

Stored情報から計算・生成できる情報。

対象例：

- culture_translation
- completeness_score

---

#### Runtime

相談・推薦ごとに生成される情報。

Shrine固定プロフィールには保存しない。

ただし、過去の推薦結果を再現する必要がある場合は、
ConciergeThreadまたは推薦履歴へ生成時点のスナップショットとして保存できる。

対象例：

- consultation_result
- recommendation_reason
- action_suggestion
- reflection_question
- score_v3

---

#### Governance

データ品質・運用管理のための情報。

対象例：

- source
- verified_at
- confidence
- trust_level
- Coverage
- Recommendation Readiness

### 5.3 監査結果

| 項目 | 現在の分類 | 妥当性 | 修正要否 | 備考 |
|------|------------|--------|----------|------|
| shrine_name | Stored | 妥当 | 不要 | 神社に固定して属する事実 |
| place_context | Stored | 妥当 | 不要 | 所在地・立地情報。Fact Layerでも必須扱い |
| deity | Stored | 妥当 | 不要 | 祭神。現状coverage 0%と記載されるが概念上はStored |
| shrine_history | Stored | 妥当 | 不要 | 由緒・沿革。現状未登録でも分類はStored |
| goriyaku | Stored | 条件付き妥当 | 要整理 | 公式由来の事実と、KAMI MUSUBI側の解釈が混在する可能性 |
| goriyaku_tags | Stored | 妥当 | 不要 | 神社へ固定して付与するタグ |
| history_theme | Derived | 妥当 | 不要 | Storedの由緒・歴史から生成する意味テーマ |
| culture_translation | Derived | 妥当 | 不要 | Stored情報を現代語へ翻訳した解釈 |
| shrine_meaning_profile | Derived | 妥当 | 不要 | Meaning情報の統合値 |
| matched_need_tags | Runtime | 妥当 | 不要 | User × Shrineの一致結果 |
| consultation_axis | Runtime | 妥当 | 不要 | 相談ごとに変化する分類軸 |
| text_score / text_hint | Runtime | 妥当 | 不要 | 相談文と候補神社の一致結果 |
| score_element | Runtime | 妥当 | 不要 | 生年月日等の補助シグナル |
| evidence | Runtime | 条件付き妥当 | 要整理 | 推薦時に採用された根拠。元データ自体はStored / Derivedを含む |
| visit_fit | Runtime | 妥当 | 不要 | 相談・推薦ごとに生成される参拝適合情報 |
| source / source_url | Governance | 妥当 | 要整理 | 名称・URL・種別・対象項目の構造が未確定 |
| verified_at | Governance | 妥当 | 要整理 | 神社単位か項目単位か未確定 |
| Coverage | Governance | 妥当 | 要整理 | Schema / Populated / Verified / Usableの区別が必要 |
| Recommendation Readiness | Governance | 妥当 | 要整理 | 判定条件・保存方法・計算責務が未統一 |

## 6. レイヤー依存関係監査

### 6.1 目的

Knowledge Base に定義される各レイヤーの責務と依存関係を確認し、
責務の重複・逆方向依存・循環依存を抽出する。

### 6.2 対象レイヤー

- Fact
- Meaning
- Consultation
- Recommendation
- Action
- Reflection

### 6.3 監査後の依存関係

Knowledge Baseの実態は、単純な一本道ではなく、
神社側情報とユーザー側情報がRecommendation前に合流する構造である。

```text
Shrine Knowledge
Fact
↓
Meaning

User Context
User Input
↓
Consultation Interpretation

Fact + Meaning + Consultation Interpretation
↓
Recommendation Match
↓
Recommendation Reason
↓
Action
↓
Reflection
```

### 6.4 確認観点

- Factを根拠とせずMeaningを生成していないか
- Consultation InterpretationとRecommendation Matchが混在していないか
- Recommendation候補選定とRecommendation Reason生成が混在していないか
- RecommendationがFactを参照する際、FactとMeaningを同一文で混在させていないか
- ActionがRecommendationだけに依存しているように記述されていないか
- ReflectionがAction以外の入力元を再定義していないか
- Trust / Coverage / Readinessが処理順の下流として扱われていないか
- ReflectionからMeaningへのフィードバックが同一処理内の循環依存になっていないか

### 6.5 監査結果

| レイヤー | 実際の依存先 | 妥当性 | 修正要否 | 備考 |
|----------|--------------|--------|----------|------|
| Fact | なし | 妥当 | 不要 | 神社に固定して属する確認可能な情報を扱う |
| Meaning | Fact | 妥当 | 不要 | Storedの事実を根拠にDerived情報を生成する |
| Consultation Interpretation | User Input | 概念未分離 | 要整理 | Glossary上のConsultation責務。ユーザー入力の解析を扱う |
| Recommendation Match | Meaning + Consultation Interpretation + Fact | 概念未分離 | 要整理 | matched_need_tags、text_score、evidence等のUser × Shrine一致結果を扱う |
| Recommendation | Fact + Meaning + Recommendation Match | 条件付き妥当 | 要整理 | 候補選定・推薦結果・Recommendation Reason文章生成の責務が混在している |
| Recommendation Reason | Fact + Meaning + Recommendation Match | 妥当 | 一部要整理 | Fact・Meaning・User Connectionを分離して表示する |
| Action | Fact + Meaning + Runtime + Recommendation | 妥当 | 一部要整理 | Recommendationを前提とするが、Stored / Derived / Runtimeも直接参照する |
| Reflection | Meaning + Consultation + Recommendation + Action | 妥当 | 一部要整理 | Actionまでの情報を引き継ぐ。Reflection専用入力は未確定 |
| Trust | Fact + Meaning | 直列配置は不適切 | 要整理 | 処理順ではなくデータ品質を横断管理するGovernance |
| Coverage | Stored + Derived + Trust | 直列配置は不適切 | 要整理 | Schema / Populated / Verified / Usableを用途別に評価する |
| Recommendation Readiness | Fact + Meaning + Trust + Coverage | 直列配置は不適切 | 要整理 | Recommendation前の利用可能範囲判定として扱う |
| Reflection Feedback | Reflection → 次回Consultation / History | 未確定 | 要整理 | 同一推薦内でMeaningへ戻さず、次回セッション入力として分離する |

### 6.6 文書間差分

#### Recommendation Layerの欠落

`shrine-profile-spec.md`の7 LayerにはRecommendation Layerが存在しない。

一方、`glossary.md`、`recommendation-copy-guide.md`、`action-guide.md`、
`reflection-guide.md`ではRecommendationがMeaningとActionの間に存在する。

Recommendationを独立Layerとして追加するか、
Profileの7 Layerを「知識・生成・Governanceの分類」として再定義する必要がある。

#### Consultation責務の混在

`glossary.md`ではConsultationを相談解析と定義する。

`shrine-profile-spec.md`ではConsultation Layerに、
User × Shrineの一致結果であるmatched_need_tags、text_score、evidenceを含める。

相談解析と推薦マッチングを別責務へ分離する必要がある。

#### Governanceの直列配置

Trust LayerとRecommendation Readinessは、
Reflection後に処理されるレイヤーではない。

Fact・Meaningの品質確認と、Recommendation前の利用可否判定として
横断的に配置する必要がある。

#### historical_factのレイヤー不一致

`shrine_meaning_composer.py`の`HISTORY_THEME_DEFINITION`には、
`historical_fact`というキーが存在する。

しかし、その内容は特定神社のStored情報ではなく、
history_themeごとに共通利用される汎用文章である。

そのためFact Layerの事実ではなく、
Meaning Layerの歴史的文脈テンプレートとして扱う方が整合する。

`historical_fact`という命名は、
Stored事実とDerived解釈の境界を誤認させる可能性がある。

## 7. 現行DB対応表

### 7.1 目的

Knowledge Base の概念項目と現行DBの物理フィールドを対応付け、
保存済み・未実装・再利用可能な項目を整理する。

### 7.2 対象モデル

- Shrine
- GoriyakuTag
- Favorite
- ConciergeThread
- ConciergeMessage
- Visit
- ShrineReflection
- ShrineInteractionLog
- ActionEvent
- その他関連モデル

重複確認対象：

- `temples.Favorite`
- `favorites.Favorite`

### 7.3 対応区分

- 完全対応
- 部分対応
- 未対応
- Runtimeのみ
- Governanceのみ

### 7.4 対応表

| 概念項目 | 現行DB・実装 | 対応状況 | 保存区分 | 備考 |
|----------|--------------|----------|----------|------|
| shrine_name | `Shrine.name_jp` | 完全対応 | Stored | 神社表示名の正本 |
| place_context | `Shrine.address` / `latitude` / `longitude` / `location` / `place_ref` | 部分対応 | Stored | 単一項目ではなく複数フィールドで構成される |
| deity | `Shrine.sajin` | 部分対応 | Stored | 祭神の自由記述。Knowledge Base上のdeity構造と完全一致するか要整理 |
| shrine_history | `Shrine.description` | 部分対応 | Stored | 一般説明と由緒が同一TextFieldに混在する可能性がある |
| goriyaku | `Shrine.goriyaku` | 完全対応 | Stored | 自由記述TextField。公式情報と編集解釈の混在可能性は残る |
| goriyaku_tags | `Shrine.goriyaku_tags` → `GoriyakuTag` | 完全対応 | Stored | ManyToManyField。検索・分類用途に利用可能 |
| history_theme | `Shrine.history_theme` | 完全対応 | Derived | Derived情報だが事前生成値としてDBへ保存されている |
| consultation_axis | `ConciergeThread.recommendations_v2`内の推薦オブジェクト(`consultation_axis`キー) | 完全対応 | Runtime Snapshot | `concierge_chat.py`で`recs["consultation_axis"]` / `rec["consultation_axis"]`として推薦オブジェクトへ保存されることを確認済み |
| Visit | `Visit` | 完全対応 | Stored Event | user・shrine・visited_at・note・statusを保存 |
| reflection_prompt | `ShrineReflection.prompt` | 完全対応 | Stored Snapshot | 生成時点の問いを保存 |
| reflection_answer | `ShrineReflection.answer` | 完全対応 | Stored User Data | ユーザー回答 |
| mood_before / mood_after | `ShrineReflection.mood_before` / `mood_after` | 完全対応 | Stored User Data | Reflection専用の状態記録 |
| reflection_history_theme | `ShrineReflection.history_theme` | 完全対応 | Stored Snapshot | 保存時点のhistory_themeスナップショット |
| detail_view | `ShrineInteractionLog.action_type=detail_view` | 完全対応 | Stored Event | 軽量行動ログ |
| route_open | `ShrineInteractionLog.action_type=route_open` | 完全対応 | Stored Event | 軽量行動ログ |
| shrine_card_click | `ShrineInteractionLog.action_type=shrine_card_click` | 完全対応 | Stored Event | カードクリックログ |
| action_started / action_completed | `ActionEvent.action_type` | 完全対応 | Stored Event | Action Suggestionに対する開始・完了イベントを保存する |
| action_suggestion_id | `ActionEvent.action_suggestion_id` | 完全対応 | Stored Event | Action Suggestion単位で開始・完了を追跡する識別子 |
| action_history_theme | `ActionEvent.history_theme` | 完全対応 | Stored Snapshot | Action実行時点のhistory_themeを保存する |
| action_category | `ActionEvent.action_category` | 完全対応 | Stored Event | Actionのカテゴリ別分析に利用する |
| action_source | `ActionEvent.source` | 完全対応 | Stored Event | Action導線・流入元を表す。Trust Layerのsourceとは別責務 |
| source / source_url | Shrineモデルには存在しない | 未対応 | Governance | `ShrineInteractionLog.source`は流入元用途でありTrust sourceとは分けて扱う |
| verified_at | Shrineモデル・関連モデルに物理フィールドなし | 未対応 | Governance | 出典確認日時の保存先なし |
| confidence | 物理フィールドなし | 未対応 | Governance | 信頼度の意味も未定義 |
| trust_level | 物理フィールドなし | 未対応 | Governance | Trust Layerの物理実装なし |
| Coverage | 物理フィールドなし | Governanceのみ | Governance | 計算・集計仕様も未確定 |
| Recommendation Readiness | 物理フィールドなし | Governanceのみ | Governance | DB保存かRuntime計算か未確定 |
| culture_translation | `shrine_culture_translation.py`の`SHRINE_CULTURE_TRANSLATIONS` | Service対応 | Derived | 神社IDをキーにしたコード内辞書。DB保存、生成運用、出典管理は未実装 |
| shrine_meaning_profile | `ShrineMeaningPayloadV2` / `shrine_meaning_composer.py` | Runtime対応 | Derived Runtime | 単一物理フィールドではなく、source / generated / displayを統合したpayloadとして生成される |
| matched_need_tags | `ConciergeThread.recommendations_v2`内 | 完全対応 | Runtime Snapshot | ranking結果およびbreakdownから推薦スナップショットへ保存される |
| evidence | `recommendations_v2[].reason_facts[].evidence` | 完全対応 | Runtime Snapshot | Stored・Derived・Runtime由来の採用シグナル名を保存する |
| action_suggestion | `recommendations_v2[].action_suggestion_v4_preview` | 完全対応 | Runtime Snapshot | 推薦生成後にattachされ、Journey Timelineから再取得される |
| recommendation_reason | `recommendations_v2`内の推薦payload | 部分対応 | Runtime Snapshot | reason_factsは確認済み。最終表示文章のキー構造は追加確認対象 |
| Trust display metadata | `shrine_trust_metadata.py` | Service対応 | Derived / Presentation | 格式・文化的地位・系譜・由来要約。Trust provenanceとは別責務 |



### 7.5 DB対応上の主要差分
#### Culture Translationの実装状態

`culture_translation`は完全未実装ではない。

`shrine_culture_translation.py`において、
神社IDをキーとしたコード内辞書として実装されている。

現行実装は以下の項目を保持する。

- landscape_tags
- faith_tags
- body_feeling_tags
- historical_background
- place_meaning
- flow_guidance
- action_reason
- benefit_translation

ただし、DB保存、出典情報、verified_at、生成担当、更新運用、
Coverage集計は存在しない。

したがって「Service実装済み・Governance未実装」と分類する。

#### Shrine Meaning Profileの実装状態

`shrine_meaning_profile`という単一の物理フィールドは存在しない。

一方、`shrine_meaning_composer.py`には、
`ShrineMeaningPayloadV2`として以下を統合する構造が存在する。

- source
- generated
- display

このpayloadが現行実装におけるMeaning Profile相当と考えられる。

ただし、DBへ永続保存されるプロフィールではなく、
表示時またはAPI応答時に生成されるRuntime構造である。

#### Trust Metadataの責務差分

`shrine_trust_metadata.py`は存在するが、
Knowledge BaseのTrust Layerとは責務が異なる。

現行Serviceが保持するのは以下である。

- rank_class
- cultural_status
- lineage
- origin_summary

一方、Trust Layerが必要とする以下は保持していない。

- source
- source_url
- verified_at
- confidence
- trust_level

したがって、現行Serviceは「文化的・格式的な表示メタデータ」であり、
出典・検証状態を管理するTrust provenance実装とは扱わない。

#### Runtime Snapshotの保存確認

`matched_need_tags`、`reason_facts`、`evidence`、
`action_suggestion_v4_preview`は推薦オブジェクトへ格納される。

`journey_timeline.py`は、
`ConciergeThread.recommendations_v2`または`recommendations`から
これらを再取得する。

したがって、これらはShrine固定プロフィールではなく、
推薦生成時点のRuntime Snapshotとして永続化される。

#### deityとsajin

Knowledge Base上の`deity`に対応する現行フィールドは`Shrine.sajin`である。

ただし、`sajin`は自由記述TextFieldであり、
祭神名・祭神分類・複数祭神・根拠出典を構造化して保持できない。

そのため完全対応ではなく部分対応とする。

#### shrine_historyとdescription

Knowledge Base上の`shrine_history`に対応する候補は`Shrine.description`である。

ただし、`description`は由緒専用であることが型・help_text上で保証されていない。

一般説明と由緒情報が混在する可能性があるため、部分対応とする。

#### Derived情報の保存

`history_theme`はDerived情報であるが、
現行DBでは`Shrine.history_theme`として事前生成値を保存している。

Derivedは非保存という意味ではなく、
Storedを根拠に再生成可能な情報として扱う。

#### Runtimeスナップショット

`ConciergeThread.recommendations`および`recommendations_v2`はJSONFieldである。

現行実装では、以下が推薦オブジェクトへ保存される。

- matched_need_tags
- reason_facts
- reason_facts[].evidence
- action_suggestion_v4_preview

`journey_timeline.py`は、
`ConciergeThread.recommendations_v2`または`recommendations`から
これらを再取得する。

したがって、これらはShrine固定プロフィールではなく、
推薦生成時点のRuntime Snapshotとして永続化される。

#### Reflection専用項目

現行DBには`ShrineReflection`が存在し、
prompt、answer、mood_before、mood_after、history_themeを保存している。

したがってReflection専用項目は完全未実装ではない。

Knowledge Base側の「Reflection専用項目の有無は未確定」という記述は、
既存DB実装との整合を取り直す必要がある。

#### Trust sourceとの同名衝突

現行実装には複数の`source`が存在する。

- `ShrineMeaningPayloadV2.source`: Meaning生成へ渡す神社入力情報
- `ShrineInteractionLog.source`: 行動が発生した画面・導線・流入元
- `ActionEvent.source`: Action導線・流入元
- Knowledge Baseの`source / source_url`: 情報出典

これらは同名だが責務が異なる。

特に`ShrineInteractionLog.source`と`ActionEvent.source`は行動分析用であり、
Trust Layerにおける出典情報として扱わない。

#### Favoriteモデル重複

以下の2モデルが存在する。

- `temples.Favorite`
- `favorites.Favorite`

現行API、Serializer、集計処理、テストは`temples.Favorite`を参照している。

確認できた主な参照元：

- behavior funnel
- concierge history action state
- popular shrine再計算
- Favorite API / Serializer
- Favorite関連テスト

`favorites.Favorite`を参照する現行コードは、
今回の検索範囲では確認できなかった。

したがって、今回確認した範囲では、現行正本は`temples.Favorite`である可能性が高い。

`favorites.Favorite`は未使用または旧実装候補として扱い、
削除前にmigration、admin、INSTALLED_APPS、既存DBテーブルを追加確認する。

## 8. 未実装概念

### 8.1 目的

Knowledge Base に定義されているが、
現行実装では未対応となっている概念を整理する。

### 8.2 分類

- P0（実装優先）
- P1（次フェーズ）
- P2（将来検討）

### 8.3 確認観点

- DB未実装
- Runtimeのみ存在
- ドキュメントのみ存在
- Governance未実装
- Trust Layer未実装

### 8.4 一覧

| 概念 | 現状 | 優先度 | 対応方針 | 備考 |
|------|------|--------|----------|------|
| Trust provenance metadata | 未実装 | P1 | source・verified_at・対象項目を持つ構造を設計 | 現行ShrineTrustMetadataとは別責務 |
| verified_at | 未実装 | P1 | source単位または項目単位の保持方法を決定 | Shrine単位では更新粒度が粗い |
| confidence | 未実装・未定義 | P1 | Fact検証・Derived生成・抽出処理のどれを評価するか定義 | 一つのconfidenceへ混在させない |
| Recommendation Readiness | 文書定義のみ | P0 | 判定関数とLevel条件を統一 | DB保存かRuntime計算かは後続判断 |
| Coverage集計 | 文書定義のみ | P0 | Schema / Populated / Verified / Usableの集計処理を設計 | 現状の93%等の種別が不明 |
| culture_translation DB管理 | Service辞書のみ | P2 | コード辞書維持かDB移行か決定 | 生成運用・出典・更新責務がない |
| culture_translation Coverage | 未実装 | P1 | 対応神社数・欠損率を集計 | 現状はID 14・17のみ確認 |
| shrine_meaning_profile保存 | Runtime Composerのみ | P2 | 保存の必要性を先に検証 | 再生成可能ならDB保存不要 |
| generic history context provenance | 未実装 | P1 | 汎用歴史説明をFactではなくMeaningとして明示 | `historical_fact`の命名修正候補 |
| legacy Favorite model cleanup | `favorites.Favorite`が未使用候補 | P1 | migration・admin・DBテーブル確認後に整理 | 現行正本は`temples.Favorite` |

## 9. 重複責務

### 9.1 目的

Knowledge Base内で複数文書が同一責務を持っていないかを確認し、
責務境界を明確化する。

### 9.2 確認観点

- 同じ概念が複数文書で管理されていないか
- 正本（Single Source of Truth）が一意になっているか
- 派生文書が正本を書き換えていないか

### 9.3 監査結果

| 責務 | 重複文書・実装 | 正本候補 | 修正要否 | 備考 |
|------|----------------|----------|----------|------|
| Favoriteモデル | `favorites.Favorite` / `temples.Favorite` | `temples.Favorite` | 要整理 | 現行API・Serializer・集計・テストは`temples.Favorite`を参照。`favorites.Favorite`は未使用または旧実装候補 |

## 10. 矛盾する必須条件

### 10.1 目的

Knowledge Base 8文書間で、必須条件・前提条件・責務定義が矛盾していないかを確認する。

### 10.2 確認観点

- MUST / SHOULD / Optional の不一致
- 同一項目の必須条件の違い
- レイヤー責務の矛盾
- Runtime / Stored の扱いの矛盾
- Recommendation条件の不一致

### 10.3 監査結果

| 対象 | 文書・実装 | 矛盾内容 | 優先度 | 対応方針 |
|------|------------|----------|--------|----------|
| Trust Layer | shrine-profile-spec / shrine_trust_metadata.py | 文書では出典・検証品質を扱うが、実装は文化的格式・系譜・由来要約を扱う | P1 | Service名または責務を分離 |
| Fact利用条件 | recommendation-copy-guide / shrine_meaning_composer.py | 文書ではFactはStoredのみ利用可能だが、Composerでは汎用テンプレートを`historical_fact`として扱う | P0 | Meaning用名称へ変更し、Factとして表示しない |
| culture_translation | shrine-profile-spec / Service | 文書では生成ルール未確定だが、実装には神社別翻訳が存在する | P1 | 実装事実を文書へ反映し、暫定ルールとして明示 |
| source / source_url | shrine-data-guide / `ShrineMeaningPayloadV2` / `ShrineInteractionLog` / `ActionEvent` | 文書ではsourceを「情報出典」として定義するが、`ShrineMeaningPayloadV2.source`はMeaning入力ブロック、`ShrineInteractionLog.source`・`ActionEvent.source`は行動・Action流入元を指し、同名で責務が異なる | P0 | Trust出典・Meaning入力・行動流入元・Action流入元それぞれへ命名を分離する |

## 11. Recommendation Readiness監査

### 11.1 目的

Recommendation Readiness の定義・計算条件・利用箇所を整理し、
Knowledge Base全体で単一の定義へ統一する。

### 11.2 確認観点

- Readiness定義
- Coverageとの関係
- sourceとの関係
- verified_atとの関係
- confidenceとの関係
- Ready判定条件
- 利用箇所

### 11.3 監査結果

| 項目 | 現状 | 問題点 | 修正方針 | 優先度 |
|------|------|--------|----------|--------|
| Recommendation Readiness | glossary・shrine-data-guide・profileで定義が異なる | 判定条件が統一されていない | Glossaryを正本とし、判定条件を一元化する | P0 |
| Recommendation Ready | Ready / Readiness が混在 | 状態名と判定体系が混同される | 「Recommendation Readiness」を正式な判定体系名とし、Readyは判定結果の状態表現に限定する | P0 |
| Coverage | Schema / Populated / Verified / Usable が存在 | Readinessとの関係が未定義 | CoverageはReadiness算出の入力指標として位置付ける | P0 |
| verified_at | 文書定義のみ | Readiness判定への利用条件が未定義 | Verified Coverageの算出に利用し、その結果を上位Readiness Level判定へ反映する | P1 |
| confidence | 未定義 | 判定対象が曖昧 | Readiness条件から切り離し、Trust評価へ限定する | P1 |
| source / source_url | 同名で複数責務 | 出典管理とRuntime sourceが混在 | Trust provenanceのみReadiness対象とする | P1 |
| Trust Layer | Governanceとして定義 | Readinessとの境界が曖昧 | Trustは品質管理、Readinessは推薦可否判定として責務を分離する | P0 |
| Runtime Snapshot | recommendations_v2へ保存 | Readinessとの関係が曖昧 | Readiness判定後の生成物として扱い、判定条件には含めない | P1 |
| Level0〜3 | shrine-data-guideでは段階定義済み、profileでは基準値が未確定 | Level条件の正本が一意でない | Level0〜3の条件はshrine-data-guideを暫定正本とし、Glossaryには概念定義のみ置く | P0 |

## 12. Trust / source / verified_at監査

### 12.1 目的

Trust Layer の責務を整理し、
保存対象・運用対象・Runtime対象を明確化する。

### 12.2 確認観点

- source
- verified_at
- confidence
- trust_level
- 更新責務
- 保存責務

### 12.3 監査結果


| 項目 | 現状 | 保存区分 | 修正要否 | 備考 |
|------|------|----------|----------|------|
| Trust Layer | 出典要否の文書ルールのみ存在 | Governance | 要 | 物理実装・更新責務なし |
| ShrineTrustMetadata | コード内辞書として存在 | Derived / Presentation | 要整理 | Trust provenanceではなく文化・格式情報 |
| source / source_url | 複数責務で同名利用 | Governance / Runtime / Stored Event | 要 | Trust出典、Meaning入力ブロック、行動流入元、Action流入元を命名上分離する |
| ShrineInteractionLog.source | 実装済み | Stored Event | 分離済み | 行動の流入元でありTrust sourceではない |
| ActionEvent.source | 実装済み | Stored Event | 分離済み | Action導線の流入元でありTrust sourceではない |
| verified_at | 未実装 | Governance | 要 | 検証対象の粒度が未確定 |
| confidence | 未実装・未定義 | Governance | 要 | 信頼度の対象が不明 |
| trust_level | 未実装 | Governance | 要 | Readinessとの責務境界も未確定 |
| culture_translation provenance | 未実装 | Governance | 要 | Derived解釈の根拠Stored情報を追跡できない |
| origin_summary | ShrineTrustMetadataに存在 | Derived / Presentation | 要整理 | 出典のない要約であり、Fact表示時は注意が必要 |

## 13. P0 / P1 / P2分類

### 13.1 目的

監査結果を優先順位ごとに整理し、
実装フェーズへ引き継ぐ。

### 13.2 分類基準

#### P0

リリース前に必須。

#### P1

実装優先度は高いが、P0完了後でも問題ない。

#### P2

将来対応・運用改善。

### 13.3 分類結果

| 項目 | 優先度 | 理由 | 次PR |
|------|--------|------|------|
| Glossary用語統一 | P0 | Consultation、Recommendation、Ready / Readinessなどの意味が文書間で異なり、後続実装の責務境界に影響する | Knowledge Base用語統一 |
| Consultation Interpretation / Recommendation Match分離 | P0 | 相談解析とUser × Shrineの一致結果が同一レイヤーへ混在している | Knowledge Base用語統一 |
| Recommendation / Recommendation Reason分離 | P0 | 候補選定・推薦結果・表示文章の責務が混在している | Knowledge Base用語統一 |
| Recommendation Layer追加または7 Layer再定義 | P0 | shrine-profile-specの7 LayerにRecommendationが存在せず、他文書と依存関係が一致しない | Knowledge Base用語統一 |
| Recommendation Readiness統一 | P0 | Level条件、最小条件、保存責務が文書間で統一されていない | Recommendation Readiness統一 |
| Level0〜3の正本確定 | P0 | shrine-data-guideとshrine-profile-specで確定度が異なる | Recommendation Readiness統一 |
| Coverage定義統一 | P0 | Schema / Populated / Verified / Usableと、既存のcoverage数値の意味が一致していない | Recommendation Readiness統一 |
| ReadinessとCoverageの関係確定 | P0 | CoverageがReadiness算出へどう影響するか未定義 | Recommendation Readiness統一 |
| Fact / Meaning境界修正 | P0 | `historical_fact`がStored事実ではなくDerivedテンプレートを指している | Knowledge Base用語統一 |
| source命名分離 | P0 | 情報出典、Meaning入力、Behavior流入元、Action流入元が同名で混在している | Knowledge Base用語統一 |
| Shrine DB物理設計 | P0 | deity / sajin、shrine_history / descriptionなど概念と物理フィールドが部分対応のまま | Shrine DB物理設計 |
| Runtime Snapshot責務の明文化 | P0 | Shrineプロフィールへ保存しないことと、ConciergeThreadへ保存することの区別が必要 | Shrine DB物理設計 |
| Trust provenance最小設計 | P1 | source_url、verified_at、対象項目の保持構造が存在しない | Trust Layer最小実装 |
| verified_at保持粒度 | P1 | Shrine単位・項目単位・出典単位のどこへ保持するか未定義 | Trust Layer最小実装 |
| confidence定義 | P1 | Fact検証、Derived生成、抽出処理の信頼度が混同される可能性がある | Trust Layer最小実装 |
| culture_translation運用定義 | P1 | Service実装は存在するが、生成担当・更新・Coverage・出典管理がない | culture_translation設計 |
| culture_translation Coverage計測 | P1 | 現在の対応神社数と欠損率が可視化されていない | Readiness Shadow監査 |
| Recommendation Readiness Shadow監査 | P1 | 現行データへLevel条件を適用した際の影響が未計測 | Readiness Shadow監査 |
| deity / shrine_history入力運用 | P1 | DB項目が部分対応であり、入力担当・出典確認・更新手順が未定義 | Shrine Fact Backfill |
| Legacy Favorite整理 | P1 | `favorites.Favorite`が未使用候補だが、migration・DBテーブル確認前に削除できない | Legacy Favorite整理 |
| Reflection既存実装との文書整合 | P1 | 文書では専用項目が未確定だが、DBにはprompt・answer・moodが存在する | Reflection Layer設計 |
| culture_translation DB管理 | P2 | 現行Service辞書でも動作するため、DB移行は運用上の必要性を検証してからでよい | culture_translation設計 |
| shrine_meaning_profile保存 | P2 | Runtimeで再生成可能であり、DB保存の必要性が未検証 | Shrine DB物理設計 |
| Reflection Feedback設計 | P2 | 次回推薦へ利用する履歴入力の設計が未確定 | Reflection Layer設計 |
| Meaning / Action / Reflection Version管理 | P2 | 現行MVPの前提条件ではなく、将来の再現性・監査性向上項目 | 各LayerのVersion管理PR |

### 13.4 実装順序

```text
P0-1 Knowledge Base用語統一
↓
P0-2 Recommendation Readiness統一
↓
P0-3 Shrine DB物理設計
↓
P1-1 Readiness Shadow監査
↓
P1-2 Trust Layer最小実装
↓
P1-3 Shrine Fact Backfill
↓
P1-4 Legacy Favorite整理
↓
P2 拡張設計
```

## 14. DB適用設計

### 14.1 目的

Knowledge Baseで定義した概念項目を、現行DBへどのように適用するかを整理する。

既存フィールドの再利用、新規フィールド追加、別モデル化、Runtimeの非保存を分離し、
実装前に物理設計の責務を明確にする。

### 14.2 設計区分

- 既存フィールドを再利用
- 既存フィールドを拡張
- 新規フィールドを追加
- 別モデルとして分離
- Runtimeのため保存しない
- Governanceとして保持方法を別途決定

### 14.3 フィールド型の判断基準

#### TextField

単一の説明文、由緒、解釈文など、順序を持つ文章を保存する場合に使用する。

#### JSONField

構造がまだ変化する可能性があり、複数の属性を一括で保持する必要がある場合に使用する。

ただし、検索・集計・参照整合性が必要な項目を恒久的にJSONFieldへ閉じ込めない。

#### ManyToManyField

複数の神社で共有され、検索・絞り込み・集計に利用するタグや分類に使用する。

#### 別モデル

出典、確認履歴、更新者、複数レコード、監査履歴など、
独立したライフサイクルを持つ情報に使用する。

### 14.4 監査結果とDB適用候補

本節は、現行実装と監査結果から考えられるDB適用候補を整理する。

ここに記載する内容は仕様判断ではなく、
次PR「Shrine DB物理設計」で比較・決定するための仮説および候補である。

- 既存フィールドを再利用できる可能性がある
- Runtime情報はShrine本体へ追加しない方針が有力
- Coverage / ReadinessはRuntime計算が候補だが、保存要否は未確定
- Trust provenanceは別モデル化が有力候補だが、物理構造は未確定
- culture_translationのDB化はP2候補
- Legacy Favoriteの整理は別PR候補

| 概念項目 | 現行DB | 監査結果 | DB適用候補 | 優先度 | 次PRでの決定事項 |
|----------|--------|----------|------------|--------|------------------|
| shrine_name | `Shrine.name_jp` | 1:1対応を確認済み | 既存フィールド再利用候補 | P0 | 再利用方針の最終確定 |
| place_context | `Shrine.address` / `latitude` / `longitude` / `location` / `place_ref` | 複数フィールドで構成されることを確認済み | 既存フィールド再利用候補（複数フィールド構成の維持を想定） | P0 | 複数フィールドをplace_contextとして集約するロジック |
| deity | `Shrine.sajin` | 自由記述TextFieldとして存在することを確認済み | 既存フィールド再利用候補 | P1 | 祭神名・複数祭神・出典の構造化要否 |
| shrine_history | `Shrine.description` | 一般説明と由緒が同一フィールドに混在する可能性を確認 | 既存フィールド再利用候補 | P1 | 一般説明と由緒情報の分離要否 |
| goriyaku | `Shrine.goriyaku` | 自由記述TextFieldとして存在することを確認済み | 既存フィールド再利用候補 | P1 | 事実（社伝由来）と解釈の混在整理 |
| goriyaku_tags | `Shrine.goriyaku_tags`（M2M） | 1:1対応を確認済み | 既存フィールド再利用候補 | P0 | 再利用方針の最終確定 |
| history_theme | `Shrine.history_theme` | Derivedだが事前生成値として保存されていることを確認済み | 既存フィールド再利用候補 | P0 | 再利用方針の最終確定 |
| culture_translation | `shrine_culture_translation.py`のコード内辞書 | コード内辞書として実装済みであることを確認済み | 現状のService辞書を維持する候補（DB化はP2候補） | P2 | DB化するか辞書実装を維持するか |
| shrine_meaning_profile | `ShrineMeaningPayloadV2`（Runtime生成） | Runtime Composerで都度生成されることを確認済み | Shrine本体へは追加しない方針が有力（Runtime計算候補） | P2 | 保存の必要性自体の検証 |
| Runtime系項目（matched_need_tags / consultation_axis / text_score・text_hint / score_element / evidence / visit_fit / recommendation_reason / action_suggestion / reflection_question） | `ConciergeThread.recommendations_v2`（JSONField） | JSONFieldへ格納されることを確認済み | Shrine本体へは追加しない方針が有力 | P0 | 14.5節と対応。個別スキーマの検討 |
| Coverage | 物理フィールドなし | 物理フィールドが存在しないことを確認済み | Runtime計算が候補だが、保存要否は未確定 | P0 | 集計処理の実装場所・キャッシュ要否 |
| Recommendation Readiness | 物理フィールドなし | 物理フィールドが存在しないことを確認済み | Runtime計算が候補だが、保存要否は未確定 | P0 | 判定関数の実装場所・キャッシュ要否 |
| source / source_url | Shrineモデルには存在しない | Shrineモデルに存在しないことを確認済み | 別モデル化が有力候補だが、物理構造は未確定 | P1 | モデル設計（対象項目・URL・種別・複数出典への対応） |
| verified_at | 物理フィールドなし | 物理フィールドが存在しないことを確認済み | 別モデル化が有力候補だが、物理構造は未確定 | P1 | 神社単位・項目単位・出典単位のどこへ付与するか |
| confidence | 物理フィールドなし・未定義 | 定義・物理フィールドともに存在しないことを確認済み | 別モデル化が有力候補だが、物理構造は未確定 | P1 | 定義自体（Fact検証／Derived生成／抽出処理のどれを評価するか） |
| trust_level | 物理フィールドなし | 物理フィールドが存在しないことを確認済み | 別モデル化が有力候補だが、物理構造は未確定 | P1 | Recommendation Readinessとの責務境界 |
| Legacy Favorite（`favorites.Favorite`） | `favorites.Favorite`（未使用候補、現行正本は`temples.Favorite`） | 現行コードからの参照が確認できなかった | 別PR候補（削除または休眠化） | P1 | migration・admin・INSTALLED_APPS・既存DBテーブルの追加確認 |

### 14.5 非保存対象

以下は相談・推薦ごとに変化するRuntime情報であり、
「Runtime情報はShrine本体へ追加しない方針が有力」という14.4の候補整理に基づき、
Shrine固定プロフィールへは保存しない想定である。

- matched_need_tags
- consultation_axis_fit
- recommendation_reason
- action_suggestion
- reflection_question
- text_score
- score_element
- evidence
- visit_fit

必要な場合は、推薦生成時点のスナップショットとして
ConciergeThreadまたは推薦履歴側へ保存する。

Coverage・Recommendation Readinessも同様に、DB固定値としては保存せずRuntime計算とする案が候補にあるが、保存要否は次PRで確定する未確定事項である。

## 15. Migration分割案

> 本章は3.4節の仮説に該当する。
> 14章のDB物理設計が未確定であるため、
> Migration番号・変更内容・Data Migrationの有無は確定していない。
> 以下は、安全に分割する場合の一般的な候補構成である。

### 15.1 目的

DB変更を一度に投入せず、
後戻り可能な単位へ分割する。

スキーマ変更、既存データ補完、制約追加を分離し、
各段階でデータ状態を確認できる構成とする。

### 15.2 分割原則

- nullableなフィールド追加を先行する
- データ補完前に必須制約を付けない
- スキーマ変更とBackfillを同一Migrationへ含めない
- M2M・別モデル追加はShrine更新と分離する
- Index追加はデータ移行後に行う
- Rename・削除は互換期間を設ける

### 15.3 Migration候補

| Migration | 変更内容 | Data Migration | Rollback | 前提 |
|-----------|----------|----------------|----------|------|
| 候補1 | nullable追加 | なし | ○ | 監査完了 |
| 候補2 | Backfill | あり | △ | 候補1 |
| 候補3 | Coverage / Readiness判定処理の追加 | 原則なし | ○ | 判定方式確定 |
| 候補4 | Index・制約追加 | なし | ○ | データ確認 |
| 候補5 | 旧構造整理 | 必要時 | △ | 互換期間終了 |

### 15.4 データ移行方針

- 推測でデータを補完しない
- 出典未確認は未確認として扱う
- Derived情報はStored情報からのみ生成する
- Backfill件数・失敗件数を記録する
- 再実行可能なMigrationまたはManagement Commandとする

## 16. Rollout / Rollback方針

> 本章は3.4節の仮説に該当する。
> 14章の物理設計および15章のMigration構成が確定した後に、
> 対象変更へ合わせてRollout / Rollback手順を確定する。
> 現時点では、段階導入時の確認観点を整理したものである。

### 16.1 目的

Knowledge BaseのDB適用を段階的に有効化し、
問題発生時に安全に戻せる状態を維持する。

### 16.2 Rollout方針

- 新規構造を追加する場合は、旧構造を正本として維持する
- 読み取り先を変更する場合は、段階的に切り替える
- Dual Writeが必要かは、物理設計確定後に判断する

### 16.3 Rollback方針

- 読み取り先のみ旧構造へ戻す
- ReadinessはFeature Flagで停止可能とする
- Backfill前データは変更しない
- 新旧Dual Write期間を設ける
- 破壊的変更は別リリースとする

### 16.4 監視項目

- Backfill成功率
- source未設定率
- verified_at未設定率
- Readiness分布
- reason_facts生成率
- fallback_rate
- recommendation生成エラー率
- detail_open_rate
- save_rate
- route_open_rate

### 16.5 中止条件

以下のいずれかが発生した場合は新構造を有効化しない。

- 推薦生成エラー率が増加
- reason_facts生成率が低下
- Readiness判定で推薦件数が大幅減少
- source・verified_at欠損が増加
- 新旧表示で情報差異が発生

## 17. 次PR候補

### 17.1 目的

本監査で抽出した課題を、
責務が重ならない単位でPRへ分割する。

本PRでは実装を行わず、
各PRの目的と完了条件のみ整理する。

### 17.2 PR候補一覧

| PR候補 | 目的 | 変更範囲 | 完了条件 | 優先度 |
|--------|------|----------|----------|--------|
| Knowledge Base用語統一 | Glossaryを正本へ統一 | docs/knowledge | 用語差分解消 | P0 |
| Recommendation Readiness統一 | 判定条件統一 | docs/knowledge | Readiness定義確定 | P0 |
| Shrine DB物理設計 | 概念項目とDB対応 | docs/knowledge・docs/architecture | DB設計確定 | P0 |
| Trust Layer最小実装 | source・verified_at追加 | backend | Migration・テスト完了 | P1 |
| Shrine Fact Backfill | Fact補完 | backend・scripts | Backfill完了 | P1 |
| Readiness Shadow監査 | Readiness分布確認 | backend・docs/audit | Shadow監査完了 | P1 |
| culture_translation設計 | Meaning Layer整理 | docs/knowledge | 設計確定 | P2 |
| Reflection Layer設計 | Reflection専用項目整理 | docs/knowledge | 設計確定 | P2 |
| Legacy Favorite整理 | 未使用候補の`favorites.Favorite`を安全に整理 | backend/favorites・migrations・admin・settings | 参照・migration・DBテーブル確認後に削除または休眠化方針を確定 | P1 |

### 17.3 次PR選定ルール

- P0をDB実装より先に完了する
- Docs修正とDB実装を同一PRに含めない
- MigrationとBackfillを分離する
- Trust LayerとReflection Layerを同時実装しない
- 破壊的変更は最後に実施する
- `favorites.Favorite`は参照・migration・admin・INSTALLED_APPS・DBテーブル確認後に別PRで整理する

## 18. 最終レビューチェック

### 18.1 目的

14〜16章の内容について、仕様判断・Migration案・Rollout方針の間に矛盾や前提の飛躍がないかを確認する。次PR着手前に解消する。

### 18.2 チェック結果

- [x] 14.5非保存対象との整合確認
  15.3の該当行を「候補3｜Coverage / Readiness判定処理の追加｜原則なし（Data Migration）」へ修正し、14.4/14.5の「Coverage・Recommendation Readinessは保存要否が未確定」という候補整理と矛盾しない表現に変更した。

- [x] 15章Migration案が確定前提になっていないか確認
  15章冒頭に「本章は3.4節の仮説に該当し、14章のDB物理設計が未確定であるため確定していない」旨の注記を追加し、Migration 1〜5を候補1〜5へ改称した。

- [x] 16章Rollout / Rollbackが仮説であることを明示
  16章冒頭に「本章は3.4節の仮説に該当し、14章・15章が確定した後に手順を確定する」旨の注記を追加し、16.2を断定的な手順列挙から条件付きの確認観点（Dual Writeは物理設計確定後に判断、等）へ書き換えた。
