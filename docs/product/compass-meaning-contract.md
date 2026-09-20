# Compass Meaning Contract v1

> Status: Active Product Contract
>
> 本書は、KAMI MUSUBI CompassにおけるMeaningの責務、Authority、入力・出力境界、
> provenance、fail-safe、explainabilityを定義するProduct Contractである。
>
> 本書はCompass Meaning Surface Auditで確認されたCurrent Stateを基礎とし、
> 現行Authorityを変更せず、今後の実装が越えてはならないMeaning境界を定義する。
>
> 本Contract自体はRuntime / API / Model / Migration / Ranking /
> Recommendation Score / Analytics / DB data / Frontend UIを変更しない。

---


## 1. Purpose

Compass Meaning Contract v1の目的は、
Compassが扱う「計算結果」「伝統解釈」「KAMI MUSUBI上の意味接続」「ユーザー表示表現」を
明確に分離し、それぞれのAuthorityを固定することである。

Compassには以下の4層を定義する。

```text
Calculation
↓
Traditional Mapping
↓
Synthesis
↓
Expression

```
ただしCurrent v1では以下の状態を正本とする。

Calculation
↓
Traditional Mapping = NOT IMPLEMENTED
↓
Synthesis = existing canonical Meaning Authority boundary
↓
Expression = deterministic / versioned / auditable / NO_LLM

本Contractの目的は、未実装のTraditional Mappingを新設することではない。

Current Stateに存在しないMeaningを推測・補完・発明せず、
既存Canonical Authorityとの責務境界を正式化することを目的とする。

また、以下を防止する。

Calculation結果が自動的にMeaningへ昇格すること
Compass geographic directionとConsultation上のdirection_profileが混同されること
goriyakuとhistory_themeが文字列一致だけで接続されること
Presentation CopyがRecommendation Evidenceへ逆流すること
non-canonical vocabularyが暗黙にCanonical化されること
Stored data coverageが存在すると暗黙に仮定されること
LLMがCompass Meaning Authorityとして利用されること

## 2. Scope

本Contractは、
CompassにおけるMeaningの生成・接続・表現に関する責務境界を定義する。

### 2.1 In Scope

Current v1では、以下のMeaning関連surfaceをContract対象とする。

```text
referenceDirections
calculationMethod
solarMonthIndex
targetYear
targetDate

purpose
need_tags
consultation_axis
history_theme
goriyaku
goriyaku_tags
reason_facts

weekly_theme
direction_fingerprint
directionSupportCopy
```

これらについて、
Calculation / Traditional Mapping / Synthesis / Expressionの
どのAuthorityに属するかを定義する。

### 2.2 Current v1 Meaning Boundary

Current v1では、
Compass geographic directionからTraditional MeaningへのCanonical Mappingは存在しない。

したがって以下はCurrent v1のCanonical connectionではない。

```text
referenceDirections
→ Traditional Meaning

referenceDirections
→ history_theme

referenceDirections
→ goriyaku
```

Current v1は、
既存Canonical Meaning Authorityを再利用し、
Compass専用の新Meaning taxonomyを導入しない。

### 2.3 In-scope Authority Questions

本Contractは少なくとも以下を定義する。

```text
What is Calculation?
What is Meaning?
Who owns each transformation?
Which taxonomy is canonical?
What provenance is required?
What happens when evidence is missing?
What may be shown to the user?
What must not affect Recommendation Ranking?
Which future changes require Mother Ship Decision?
```

### 2.4 Out of Scope

Current v1では以下を変更対象としない。

```text
Kyusei calculation algorithm
Kyusei calculation precision
geographic direction taxonomy
history_theme canonical taxonomy
goriyaku taxonomy
NEED_TO_GORIYAKU_IDS
Recommendation Ranking
Recommendation Score
Weekly Theme catalog
Weekly Snapshot behavior
Astrology
Element
Daily Word
LLM runtime route
Free / Premium policy
Frontend implementation
Analytics taxonomy
Production DB data
```

Out-of-scope項目が既存Runtimeに存在する場合も、
本Contractからそのbehaviorを暗黙に変更しない。

### 2.5 Docs-only Boundary

本Contract作成PRはdocs-onlyとする。

以下を変更しない。

```text
Runtime
API
Model
Migration
DB data
Recommendation Ranking
Recommendation Score
Analytics
Frontend UI
```


## 3. Definitions

本Contractでは、以下の用語を明確に区別する。

| Term                         | Definition                                                                                                                |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Compass geographic direction | Compass Direction Runtimeが算出する地理的方位。`referenceDirections`等で表現される。Meaningそのものではない。             |
| Calculation                  | 入力とCanonical Calculation RuleからCompass direction関連のRuntime outputを決定論的に算出する層。                         |
| Calculation Result           | Calculationによって得られたシステム上の算出結果。宗教的・伝統的意味が客観的事実であることを意味しない。                   |
| Traditional Mapping          | Calculation Resultを、明示されたCanonical Source / Rule / Versionに基づく伝統上の解釈へ変換する層。Current v1では未実装。 |
| Traditional Interpretation   | Traditional Mappingによって得られる伝統上の解釈。Current v1では生成しない。                                               |
| Synthesis                    | Calculation / Traditional Interpretation / existing Meaning Authorityを、Contractで許可されたRuleに従って接続する層。     |
| Expression                   | Synthesis結果をユーザー向け表現へ変換する層。Canonical MeaningやRecommendation Rankingを新規決定するAuthorityを持たない。 |
| Meaning Authority            | MeaningのCanonical定義、変換、接続について正本として扱える責務。                                                          |
| Presentation Authority       | MeaningやRecommendationをユーザーへ表示する表現上の責務。Meaningそのものを新規定義するAuthorityではない。                 |
| Canonical taxonomy           | Product / Domain Contractで正式に定義されたMeaning vocabulary。                                                           |
| Stored data coverage         | Canonical taxonomyに対応する値が実際のStored dataへ保存されている範囲。                                                   |
| Provenance                   | MeaningまたはCalculation Resultの根拠となるSource / Rule / Version / transformation履歴。                                 |
| `direction_profile`          | Consultation Interpretationによって生成される相談状態上の方向性。Compass geographic directionとは別概念。                 |
| `history_theme`              | Shrine-side Meaning vocabulary。Current canonical v1は既存7値を正本とする。                                               |
| `goriyaku`                   | Shrine Benefit / Evidence側の独立したMeaning namespace。`history_theme`とは別Authorityとして扱う。                        |
| `reason_facts`               | Recommendation結果の根拠を構成するRuntime evidence。Presentation Copyそのものではない。                                   |
| `weekly_theme`               | Weekly Presentation用のdeterministic copy。Traditional MeaningまたはRecommendation Signalではない。                       |
| `direction_fingerprint`      | Weekly Presentationのdeterministic identityを構成する内部値。Meaning Authorityを持たない。                                |
| `directionSupportCopy`       | Shrine Meaning Presentationにおける補助表現。Primary Meaning Authorityを持たない。                                        |


### 3.1 Direction Namespace Isolation

以下は別概念として扱う。

```text
Compass geographic direction
≠
Consultation direction_profile
≠
Google routing direction
≠
Concierge direction_reference

```
directionという名称の一致だけから、
Meaning Authority、変換関係、Canonical equivalenceを推定してはならない。

特に、

direction_profile.direction
≠
Compass referenceDirections

をContract上の前提とする。


### 3.2 Canonical Taxonomy vs Stored Data Coverage

以下を明確に区別する。

Canonical taxonomy exists
≠
Stored data is populated

Canonical history_theme taxonomyが存在することは、
Shrine.history_themeにCanonical値が保存済みであることを保証しない。

Meaning Contract v1は、
Stored data coverageの存在を暗黙の前提としてはならない。


### 3.3 Namespace Isolation

同じ日本語ラベルを持つ値であっても、
異なるAuthorityまたはtaxonomyに属する場合は別概念として扱う。

例:

goriyaku: 導き
≠
history-theme-like vocabulary: 導き

文字列一致のみを根拠として、
goriyakuとhistory_themeを相互変換してはならない。


## 4. Authority Model

Compass Meaning v1は、以下の4層で責務を分離する。

Layer	Authority	Current v1 Status	Meaning Generation
Calculation	Compass Runtime Authority	ACTIVE	No
Traditional Mapping	Source-backed Traditional Mapping Authority	NOT IMPLEMENTED	No current authority
Synthesis	Existing Canonical Meaning Authority	ACTIVE / CONSTRAINED	Existing authority reuse only
Expression	Versioned Presentation Authority	ACTIVE / CONSTRAINED	Deterministic expression only

Authorityは上位・下位という優先順位ではなく、
異なる責務境界として扱う。

各層は、自身に定義されていないAuthorityを暗黙に取得してはならない。


### 4.1 Calculation Authority

Calculation Authorityは、
Compass geographic directionに関するRuntime Calculation Resultを生成する。

Current v1では主に以下を扱う。

referenceDirections
calculationMethod
solarMonthIndex
targetYear
targetDate

Calculation Authorityは以下を持たない。

Traditional Meaning Authority
history_theme Authority
Goriyaku Authority
Shrine Meaning Authority
psychological interpretation Authority
future prediction Authority
Recommendation Ranking Authority
Presentation Authority

Calculation Resultは、
Meaningそのものとして扱ってはならない。


### 4.2 Traditional Mapping Authority

Current v1では以下を正本とする。

Traditional Mapping Authority
=
NOT IMPLEMENTED

したがってCurrent v1では、
Compass geographic directionからTraditional Meaningを生成するCanonical Authorityは存在しない。

以下のような関係を暗黙に作成してはならない。

referenceDirections
→ traditional symbolism

referenceDirections
→ history_theme

referenceDirections
→ goriyaku

Traditional Mappingを将来導入する場合は、
少なくとも以下を明示する必要がある。

Canonical Source
Rule
Version
Provenance

その導入はCurrent v1の単純なRuntime実装ではなく、
別のMother Ship Decision Gateを通過する。


### 4.3 Synthesis Authority

Synthesisは、
既存Canonical Meaning AuthorityをContractで許可された範囲内で再利用する。

Current v1では少なくとも以下を既存Authorityとして扱う。

need_tags
consultation_axis
canonical history_theme
goriyaku evidence
reason_facts

SynthesisはCompass独自の新Meaning taxonomyを作成しない。

また、異なるnamespace間の関係を
文字列一致、類似語、推測のみから新設してはならない。

Canonical taxonomyの存在はStored data coverageを保証しないため、
SynthesisはShrine.history_themeが保存済みであることを前提としてはならない。


### 4.4 Expression Authority

Expressionは、
許可されたMeaning Resultをユーザー向けPresentationへ変換する責務を持つ。

Current v1では以下を必須条件とする。

deterministic
versioned
auditable
non-predictive
non-assertive
LLM Authority = NONE

Expression Authorityは以下を変更してはならない。

candidate generation
filtering
ranking
recommendation score
recommendation evidence
canonical taxonomy
stored shrine data

Presentation Copyを上流のMeaning AuthorityまたはRecommendation Authorityへ逆流させてはならない。


### 4.5 Authority Escalation Prohibition

ある層のoutputが後続層で利用されることは、
そのoutput自体が後続層のAuthorityを獲得することを意味しない。

例:

Calculation Result used by Synthesis
≠
Calculation becomes Meaning Authority

Meaning Result used by Expression
≠
Expression becomes Meaning Authority

direction_fingerprint used by Weekly Presentation
≠
direction_fingerprint becomes Direction Meaning

Authorityの変更には、
明示的なContract変更またはMother Ship Decisionを必要とする。


## 5. Calculation Contract

### 5.1 Responsibility

Calculation層は、
Compass geographic directionに関するRuntime Calculation Resultを
決定論的に算出する責務のみを持つ。

概念上の基本フローは以下とする。

birthdate
+
effective target date
↓
Compass / Kyusei calculation
↓
Direction Runtime Result

Calculation層はMeaningを生成しない。


### 5.2 Input Boundary

Calculationが利用できる入力は、
Calculation Contractまたは既存Compass Runtime Contractで明示された値に限定する。

Current v1では主に以下を利用する。

birthdate
target_date / effective target date

Current Runtime上でtarget_dateが明示されない経路では、
既存Runtime Contractが定める日付Authorityに従う。

Calculationの意味生成入力として、
以下を使用してはならない。

purpose
need_tags
consultation_axis
goriyaku
history_theme
weekly_theme
reason_facts
Presentation Copy
LLM output

### 5.3 Output Boundary

Current v1のCalculation Resultには、
以下のRuntime値を含みうる。

referenceDirections
calculationMethod
solarMonthIndex
targetYear
targetDate

これらはCalculation metadataまたはDirection Runtime Resultとして扱う。

Calculation層自身が以下の変換を行ってはならない。

referenceDirections
→ psychological meaning

referenceDirections
→ life advice

referenceDirections
→ goriyaku

referenceDirections
→ history_theme

referenceDirections
→ shrine meaning

referenceDirections
→ traditional symbolism

Calculation ResultはMeaning Authorityではない。


### 5.4 Determinism

Calculationは、
同一Input、同一Calculation Rule、同一Calculation Versionに対して
再現可能な結果を生成できなければならない。

基本原則:

same input
+
same calculation rule
+
same calculation version
=
same calculation output

Calculation Resultへ以下を混入させてはならない。

randomness
LLM output
Presentation Copy
user-facing narrative
unversioned interpretation

### 5.5 Calculation Fact Boundary

本ContractでCalculation ResultをFactとして扱う場合、
それは以下の意味に限定する。

Fact
=
the system calculated this value
under the specified rule/version/input

以下を意味しない。

Fact
≠
traditional interpretation is objectively true

Fact
≠
spiritual meaning is objectively true

Fact
≠
future outcome is established

Fact
≠
the recommended shrine has guaranteed benefit

CalculationとInterpretationを同一視してはならない。


### 5.6 Runtime / Persistence Boundary

Direction Calculation Resultは、
Current Compass Contract上、Runtimeで再計算可能な値として扱う。

Direction Runtime
=
ephemeral / recomputable

Calculation Result自体を、
Compass Meaning HistoryまたはUser Meaning Historyとして
自動的にPersistent dataへ昇格させてはならない。

Weekly Presentation等のPersistent Stateは別責務とする。

Direction Runtime
=
Calculation responsibility

Weekly Presentation Snapshot
=
Presentation persistence responsibility

Persistenceの存在はMeaning Authorityを意味しない。


### 5.7 LLM Boundary

Current Mother Ship Decisionは以下である。

Compass LLM Policy = NO_LLM

したがってCalculation層では、
LLMを以下の用途へ使用してはならない。

direction calculation
calculation correction
calculation completion
missing value inference
traditional meaning inference
fallback direction generation

Calculation failureをLLMで補完してはならない。


### 5.8 Failure Boundary

Calculationが有効なResultを生成できない場合、
MeaningまたはDirectionを推測して補完しない。

基本原則:

valid calculation
→ return Calculation Result

invalid / unavailable calculation
→ explicit fail-safe state

以下は禁止する。

invalid calculation
→ invent direction

invalid calculation
→ infer traditional meaning

invalid calculation
→ generate spiritual fallback

invalid calculation
→ LLM completion

具体的なFail-safe behaviorは、
本ContractのFail-safe Contractで定義する。


## 6. Traditional Mapping Contract


### 6.1 Current v1 Status

Current v1では、
Compass geographic directionをTraditional Meaningへ変換するCanonical Mappingは存在しない。

Current Contract上の状態は以下とする。

```text
Traditional Mapping
=
NOT IMPLEMENTED
```

これは一時的なfallback状態ではなく、
Current v1における正式なContract状態である。

Traditional Mappingが未実装である場合、
その空白を推測、Presentation Copy、既存goriyaku、history_theme、LLM等で補完してはならない。

### 6.2 Responsibility

Traditional Mappingを将来実装する場合、
Calculation Resultを伝統上の解釈へ変換する責務のみを持つ。

概念上の境界は以下とする。

Calculation Result
↓
Source-backed Traditional Mapping
↓
Traditional Interpretation

Traditional Mappingは、
Shrine Recommendation、Ranking、Goriyaku決定、history_theme決定を直接行うAuthorityではない。


### 6.3 Required Provenance

Traditional Mappingを導入する場合、
各mappingは最低限以下を持たなければならない。

Canonical Source
Rule
Version
Provenance

意味は以下とする。

Field	Requirement
Canonical Source	Mappingの根拠として採用する資料・体系・正本
Rule	Calculation ResultからInterpretationへ変換する明示的な規則
Version	Rule変更を追跡できるversion identifier
Provenance	Sourceから最終Interpretationまでの由来を追跡可能にする情報

Sourceのみ存在してRuleが存在しない状態、
Ruleのみ存在してSourceが存在しない状態を
Canonical Traditional Mappingとして扱ってはならない。


### 6.4 Interpretation Boundary

Traditional Interpretationは、
伝統上の体系に基づくInterpretationとして扱う。

以下と同一視してはならない。

Traditional Interpretation
≠
objective scientific fact

Traditional Interpretation
≠
guaranteed future outcome

Traditional Interpretation
≠
guaranteed shrine benefit

Traditional Interpretation
≠
user personality diagnosis

ユーザー向けExpressionでは、
Traditional Interpretationを客観的事実または断定的予測として表現してはならない。


### 6.5 Prohibited Current v1 Mappings

Current v1では以下を禁止する。

referenceDirections
→ traditional symbolism

referenceDirections
→ history_theme

referenceDirections
→ goriyaku

referenceDirections
→ consultation_axis

referenceDirections
→ user psychological state

また、Compass geographic directionと
Consultation direction_profileを接続してはならない。

Compass referenceDirections
≠
Consultation direction_profile.direction

### 6.6 No Proxy Mapping

Traditional Mappingが未実装であることを理由として、
既存Meaning vocabularyを代理mappingとして利用してはならない。

禁止例:

north
→ 守り

south
→ 勝負

east
→ 再出発

上記のようなmappingがCanonical Source / Rule / Version / Provenanceなしに導入されることを禁止する。

同様に以下も禁止する。

direction
→ goriyaku label by intuition

direction
→ history_theme by semantic similarity

direction
→ Weekly Theme

direction
→ astrology / element meaning

### 6.7 LLM Boundary

Current Mother Ship Decision:

Compass LLM Policy = NO_LLM

したがってLLMはTraditional Mapping Authorityを持たない。

LLMを以下へ使用してはならない。

invent traditional meaning
select traditional source
fill missing mapping
resolve conflicting traditions
generate canonical rule
infer symbolism from direction

### 6.8 Future Introduction Gate

Traditional Mappingの導入は、
Current Contract内の通常実装として扱わない。

導入前に新しいMother Ship Decisionを必要とする。

最低限、以下を確定する。

Which traditional system is authoritative?
Which source is canonical?
Which rule set is canonical?
How are conflicting schools handled?
How is versioning performed?
How is provenance exposed?
How is user-facing wording constrained?

Mother Ship Decisionなしに
Traditional Mapping AuthorityをACTIVEへ変更してはならない。


## 7. Synthesis Contract

### 7.1 Responsibility

Synthesisは、
Contractで許可されたMeaning Authorityを接続し、
Expressionへ渡すMeaning Resultを構成する責務を持つ。

Current v1では、
新しいMeaningを発明する層ではない。

基本原則:

Existing Canonical Meaning Authority
+
Allowed Runtime Evidence
↓
Deterministic Synthesis
↓
Meaning Result

### 7.2 Current v1 Inputs

Current v1のSynthesisは、
既存Recommendation / Knowledge Meaning Authorityを再利用する。

利用対象には少なくとも以下を含みうる。

purpose
need_tags
consultation_axis
canonical history_theme
goriyaku evidence
reason_facts

ただし、
存在するすべての値を常に利用することを意味しない。

各値の利用可否は、
既存Recommendation ContractおよびMeaning Contract上のAuthorityに従う。


### 7.3 No New Taxonomy

Current v1では、
Compass専用の新しいMeaning taxonomyを作成しない。

以下を禁止する。

Compass-specific history_theme
Compass-specific goriyaku taxonomy
direction-specific semantic taxonomy
implicit Common Meaning Vocabulary

新しいCommon Meaning Vocabulary等を導入する場合は、
別のMother Ship Decisionを必要とする。


### 7.4 Canonical history_theme Boundary

Current canonical history_theme v1は、
既存の7値を正本とする。

history_theme:restart
history_theme:stillness
history_theme:restoration
history_theme:challenge
history_theme:connection
history_theme:learning
history_theme:protection

Current v1では、
以下をCanonical history_themeへ昇格させない。

浄化
導き
巡り

これらは現行コード・過去出力・Presentation上に存在しうるが、
Canonical history_theme v1として扱わない。


### 7.5 Namespace Isolation

異なるMeaning namespaceを同一視してはならない。

特に以下をContract上の前提とする。

goriyaku
≠
history_theme

同名ラベルであっても同一Authorityを意味しない。

例:

GoriyakuTag: 導き
≠
history-theme-like vocabulary: 導き

文字列一致、類義語、埋め込み類似度等のみを理由として、
異なるnamespace間のCanonical Mappingを作成してはならない。


### 7.6 Stored Data Boundary

Canonical taxonomyの存在は、
Stored data coverageを保証しない。

Canonical taxonomy exists
≠
Shrine stored data is populated

Current v1のSynthesisは、
Shrine.history_themeにCanonical値が保存済みであることを前提としてはならない。

必要なStored Evidenceが存在しない場合、
存在しないMeaningを推測して補完してはならない。


### 7.7 Geographic Direction Boundary

Current v1ではCompass geographic directionを
Meaning Synthesis Signalとして直接利用しない。

禁止:

referenceDirections
→ history_theme selection

referenceDirections
→ goriyaku selection

referenceDirections
→ consultation_axis selection

referenceDirections
→ Meaning score

DirectionはCurrent v1では、
Calculation / geographic filtering responsibilityに留まる。


### 7.8 Weekly Presentation Boundary

以下はSynthesis Authorityではない。

weekly_theme
direction_fingerprint
directionSupportCopy

weekly_themeをMeaning inputまたはRecommendation Signalとして逆流させてはならない。

direction_fingerprintはdeterministic identityであり、
Meaning Signalではない。

directionSupportCopyはSupplementary Presentationであり、
Canonical Meaningを変更してはならない。


### 7.9 Determinism

Synthesisは、
同一Input、同一Canonical Authority、同一Rule Versionに対して
同一Meaning Resultを再現可能でなければならない。

same allowed inputs
+
same canonical taxonomy
+
same synthesis rule
+
same synthesis version
=
same Meaning Result

Current v1では、
randomnessまたはLLMによってMeaning Resultを変動させてはならない。


### 7.10 No Ranking Authority

SynthesisはRecommendation Ranking Authorityを持たない。

Current v1では以下を禁止する。

new Meaning Result
→ ranking bonus

new Meaning Result
→ score adjustment

Expression wording
→ candidate order

Traditional Interpretation
→ ranking override

Meaning SignalをRankingへ新規導入する場合は、
別のMother Ship DecisionおよびRecommendation Contract変更を必要とする。


### 7.11 Failure Boundary

必要なMeaning Evidenceが存在しない場合、
SynthesisはMeaningを発明してはならない。

基本原則:

sufficient allowed evidence
→ deterministic Meaning Result

insufficient evidence
→ no Meaning Result / explicit fallback state

禁止:

missing history_theme
→ infer one from shrine name

missing evidence
→ infer from direction

missing evidence
→ infer from goriyaku label similarity

missing evidence
→ LLM-generated meaning

具体的なfallback sequenceはFail-safe Contractで定義する。


## 8. Expression Contract

### 8.1 Responsibility

Expressionは、
Contract上許可されたMeaning Resultを
ユーザーが理解可能なPresentationへ変換する責務を持つ。

概念上の境界:

Meaning Result
↓
Versioned Expression Rule
↓
User-facing Expression

ExpressionはMeaningそのものを新規決定するAuthorityを持たない。


### 8.2 Current v1 Requirements

Current v1のExpressionは以下を満たさなければならない。

deterministic
versioned
auditable
non-predictive
non-assertive
LLM Authority = NONE

同一Meaning Result、同一Expression Rule、同一Versionに対して、
再現可能なPresentationを生成する。


### 8.3 Deterministic Expression

基本原則:

same Meaning Result
+
same expression rule
+
same expression version
=
same user-facing expression

Current v1では、
ランダムコピー生成をCanonical Expressionとして扱わない。

複数のcurated templateを利用する場合も、
選択Ruleは決定論的かつversionedでなければならない。


### 8.4 Non-predictive Boundary

Expressionは未来の結果を断定してはならない。

避ける表現の性質:

必ず成功する
願いが叶う
運命が変わる
この方角へ行けば金運が上がる
この神社へ行けば恋愛が成就する

Current v1では、
MeaningをReflection、Perspective、Action Prompt等として表現できるが、
未来の結果保証として表現してはならない。


### 8.5 Non-assertive Boundary

Traditional InterpretationまたはKAMI MUSUBI Interpretationを、
ユーザー本人についての断定的事実として扱わない。

Interpretation
≠
diagnosis

Interpretation
≠
personality fact

Interpretation
≠
future fact

Interpretation
≠
religious certainty

Expressionは、
Calculation Fact / Traditional Interpretation / KAMI MUSUBI Interpretation /
Presentationを混同しない。


### 8.6 Evidence Fidelity

Expressionは、
上流Meaning Resultに存在しない根拠を追加してはならない。

禁止:

no history_theme evidence
→ expression claims history_theme

no traditional mapping
→ expression claims traditional symbolism

no goriyaku evidence
→ expression claims specific benefit

no direction meaning
→ expression claims direction symbolism

Presentation上の自然な文章化は許可されるが、
Evidenceの意味範囲を拡張してはならない。


### 8.7 LLM Boundary

Current Mother Ship Decision:

Compass LLM Policy = NO_LLM

したがってCurrent v1では、
LLMをuser-facing Expression生成にも使用しない。

禁止:

LLM copy generation
LLM paraphrasing
LLM personalization
LLM explanation generation
LLM fallback copy
LLM tone adaptation

Current v1のExpressionは、
versioned curated copyまたはdeterministic templateを利用する。


### 8.8 Presentation Does Not Become Evidence

以下をContract上の原則とする。

Presentation Copy
≠
Meaning Evidence

Presentation Copy
≠
Recommendation Evidence

Presentation Copy
≠
Canonical taxonomy

Presentation Copy
≠
Ranking Signal

Expression結果を、
後続のRecommendationやMeaning Synthesisへ入力として逆流させてはならない。


### 8.9 Weekly Theme Boundary

weekly_themeはWeekly Presentation Authorityに属する。

以下を禁止する。

weekly_theme
→ history_theme

weekly_theme
→ goriyaku

weekly_theme
→ Recommendation Signal

weekly_theme
→ Ranking weight

Weekly Themeは、
Current v1ではdeterministic Presentation Copyとしてのみ扱う。


### 8.10 directionSupportCopy Boundary

directionSupportCopyはSupplementary Presentationである。

Current v1では、
Primary Meaningを変更してはならない。

directionSupportCopy
does not modify
↓
heroMeaningCopy
shrineMeaning
actionMeaning
canonical Meaning Authority

Supplementary Presentationの存在を、
Direction Meaning Mappingが存在する証拠として扱ってはならない。


### 8.11 Versioning

Expression Ruleまたはcurated copyの変更によって
同一Meaning Resultから異なる表示が生じる場合、
Expression Versionを識別可能にする。

Version変更は、
Meaning AuthorityまたはCanonical taxonomyの変更を暗黙に意味しない。

Expression version change
≠
Meaning taxonomy change

Meaningそのものを変更する場合は、
該当するMeaning ContractまたはMother Ship Decision Gateを通過する。


### 8.12 Failure Boundary

Meaning Resultが存在しない場合、
Expressionは意味を生成して穴埋めしてはならない。

基本原則:

valid Meaning Result
→ render permitted expression

no valid Meaning Result
→ omit Meaning expression
   or render explicitly defined neutral fallback

禁止:

no Meaning Result
→ poetic invention

no Meaning Result
→ traditional claim

no Meaning Result
→ spiritual assertion

no Meaning Result
→ LLM fallback

具体的なneutral fallbackは、
Fail-safe Contractで定義する。

```text
Calculation
   │
   │ Meaningを作らない
   ▼
Traditional Mapping
   │
   │ Current v1 = NOT IMPLEMENTED
   ▼
Synthesis
   │
   │ Existing Canonical Authorityのみ
   ▼
Expression
   │
   │ Meaningを増やさず表示する
   ▼
User

```

## 9. Canonical Taxonomy Boundary


### 9.1 Canonical history_theme v1

Current v1では、
`history_theme`のCanonical Authorityとして既存History Theme Taxonomy v1を利用する。

Canonical machine identityは以下の7値とする。

| Canonical key               | Display label |
| --------------------------- | ------------- |
| `history_theme:restart`     | 再出発        |
| `history_theme:stillness`   | 静寂          |
| `history_theme:restoration` | 復興          |
| `history_theme:challenge`   | 勝負          |
| `history_theme:connection`  | 縁            |
| `history_theme:learning`    | 学び          |
| `history_theme:protection`  | 守り          |

Canonical keyをmachine identityとし、
日本語ラベルはdisplay valueとして扱う。

Compass Meaning Contract v1は、
この7値を変更・拡張しない。


### 9.2 Non-canonical Vocabulary

Current implementation、legacy output、audit、presentation等には、
以下のhistory-theme-like vocabularyが存在しうる。

```text
浄化
導き
巡り
```

Current v1ではこれらをCanonical history_themeとして扱わない。

```text
浄化 / 導き / 巡り
=
non-canonical compatibility / legacy / presentation vocabulary
```

以下を禁止する。

non-canonical vocabulary
→ automatic canonical promotion

non-canonical vocabulary
→ canonical history_theme by semantic similarity

non-canonical vocabulary
→ canonical history_theme by label reuse

これらをCanonical taxonomyへ追加する場合は、
別のMother Ship Decisionを必要とする。

### 9.3 Goriyaku Namespace Boundary

goriyaku / goriyaku_tagsは、
history_themeとは独立したShrine Benefit / Evidence Authorityとして扱う。

goriyaku namespace
≠
history_theme namespace

同じ日本語文字列を持つ場合も、
同一Meaningとして扱ってはならない。

例:

GoriyakuTag: 導き
≠
history-theme-like vocabulary: 導き

文字列一致のみを理由として、
異なるnamespace間のCanonical Mappingを作成してはならない。


### 9.4 Compass-specific Taxonomy Prohibition

Current v1では、
Compass専用のMeaning taxonomyを新設しない。

禁止対象には以下を含む。

Compass history_theme
Compass goriyaku taxonomy
direction meaning taxonomy
direction symbolism taxonomy
implicit Common Meaning Vocabulary

Meaning vocabularyを新設する場合は、
既存Canonical Authorityとの関係を設計し、
Mother Ship Decision Gateを通過する。


### 9.5 Taxonomy Authority Rule

Presentation、Weekly Theme、LLM output、legacy copy、
Runtime-derived labelsは、
それ自体ではCanonical taxonomyにならない。

frequently used label
≠
canonical vocabulary

existing code string
≠
canonical vocabulary

presentation copy
≠
canonical vocabulary

Canonical Authorityは、
明示されたProduct / Domain Contractによってのみ成立する。


## 10. Stored Data Boundary

### 10.1 Taxonomy and Storage Are Separate

Canonical taxonomyの存在と、
Stored data coverageは別責務として扱う。

Canonical taxonomy exists
≠
Stored data is populated

history_themeのCanonical taxonomyが存在していても、
各ShrineにCanonical history_themeが保存済みであることを意味しない。

Meaning Contract v1は、
Stored data coverageを暗黙に仮定してはならない。


### 10.2 No Stored-value Assumption

Synthesis、Expression、Recommendation Presentationは、
以下を前提としてはならない。

Shrine.history_theme is always populated
goriyaku evidence is always complete
reason_facts are always available
all canonical meaning fields have stored values

Stored Evidenceの有無をRuntimeで確認せず、
Meaningを存在するものとして扱ってはならない。


### 10.3 Missing Stored Data

必要なStored Evidenceが存在しない場合、
不足値を推測して補完してはならない。

禁止:

missing history_theme
→ infer from shrine name

missing history_theme
→ infer from goriyaku label

missing history_theme
→ infer from geographic direction

missing history_theme
→ infer from weekly_theme

missing stored evidence
→ LLM completion

Stored dataが不足している場合は、
利用可能な既存Evidenceのみを利用するか、
該当Meaning表現を生成しない。


### 10.4 Stored vs Derived vs Runtime

Current v1では、
以下のライフサイクルを区別する。

Stored
=
DB / canonical persisted evidence

Derived
=
StoredまたはCanonical Authorityから
決定論的Ruleによって導出された値

Runtime
=
request-level calculation / recommendation result

Presentation
=
user-facing representation

異なるLifecycle間で値を移動させる場合、
その変換RuleとAuthorityを明示する。


### 10.5 Persistence Does Not Create Authority

値がDBまたはSnapshotへ保存されていることは、
その値がCanonical Meaning Authorityを持つことを意味しない。

persistent
≠
canonical

snapshot
≠
meaning authority

例:

WeeklyPresentationSnapshot
=
Presentation persistence

NOT
=
Canonical Meaning persistence

### 10.6 Data Backfill Boundary

Canonical taxonomyが存在することを理由として、
Meaning Contract v1からStored dataのbackfillを要求しない。

Meaning Contract
≠
Data Population Contract

Shrine.history_theme等のcoverage改善を行う場合は、
Data / Knowledge Pipeline側の別工程として扱う。


## 11. Provenance Contract

### 11.1 Purpose

Provenanceは、
Calculation、Meaning変換、Expressionが
どのSource / Rule / Versionから生成されたかを追跡可能にするための契約である。

基本原則:

No opaque Meaning transformation

Meaning ResultまたはInterpretationについて、
由来を説明できない変換をCanonical Authorityとして扱ってはならない。


### 11.2 Provenance Components

Meaning関連のCanonical transformationは、
適用可能な範囲で以下を識別可能にする。

Source
Rule
Version
Input
Output
Transformation path

各要素の責務は以下とする。

Component	Responsibility
Source	根拠となるCanonical資料・taxonomy・evidence
Rule	InputからOutputへ変換する明示的規則
Version	Ruleまたはtaxonomyの変更履歴を識別する
Input	変換に実際に利用された値
Output	変換結果
Transformation path	SourceからOutputまでの責務経路

### 11.3 Calculation Provenance

Calculationでは最低限、
以下を再現可能にする。

input
+
calculation rule
+
calculation version
=
calculation output

Calculation provenanceは、
Traditional Meaningの根拠を意味しない。

Calculation provenance
≠
Traditional Interpretation provenance

### 11.4 Traditional Mapping Provenance

Current v1ではTraditional Mappingは未実装である。

したがってCurrent v1では、
Traditional Interpretation provenanceも生成しない。

将来Traditional Mappingを導入する場合は、
最低限以下を必須とする。

Canonical Source
Rule
Version
Provenance

これらが揃わないmappingは、
Canonical Traditional Mappingとして扱わない。


### 11.5 Synthesis Provenance

Synthesis Resultは、
利用した既存Meaning Authorityを追跡可能でなければならない。

例:

purpose
→ need_tags
→ consultation_axis

Stored Shrine Evidence
→ canonical history_theme

Stored Benefit Evidence
→ goriyaku

Recommendation Evidence
→ reason_facts

Current v1では、
存在しない中間mappingをProvenance上で補完してはならない。


### 11.6 Expression Provenance

Expressionは、
少なくとも以下を識別可能にする。

Meaning Result
+
Expression Rule
+
Expression Version
=
User-facing Expression

Expression Copy自体を、
Meaning Sourceとして逆参照してはならない。

Expression
→ Meaning Source

という逆向きAuthorityを作成してはならない。


### 11.7 Provenance Gap

必要なProvenanceを確認できない場合、
そのMeaning transformationをCanonicalとして扱わない。

基本原則:

unknown provenance
→ do not promote to canonical meaning

禁止:

unknown source
→ assume traditional meaning

unknown rule
→ infer mapping

unknown version
→ silently reuse legacy behavior

unknown provenance
→ LLM explanation

### 11.8 Version Change Boundary

Ruleまたはtaxonomyを変更し、
同一Inputから異なるMeaning Resultが生じうる場合は、
Version変更を識別可能にする。

semantic behavior changes
→ version must change

単なるPresentation wording変更は、
Canonical Meaning taxonomy変更とは区別する。


## 12. Fail-safe Contract

### 12.1 Principle

Compass Meaning v1は、
Meaning不足または失敗時に
推測して「それらしい意味」を作るより、
Meaningを出さないことを優先する。

基本原則:

absence of evidence
≠
permission to invent meaning

Fail-safeは、
上流Authorityを越えないことを最優先とする。


### 12.2 Layer-specific Failure

各層は自身の責務範囲で失敗を処理し、
別Authorityへ勝手に昇格して補完してはならない。

Calculation failure
→ Calculation fail-safe

Traditional Mapping unavailable
→ no Traditional Interpretation

Synthesis evidence insufficient
→ no synthesized Meaning Result

Expression input unavailable
→ omit Meaning expression or use explicit neutral fallback

### 12.3 Traditional Mapping Absence Is Not an Error

Current v1ではTraditional Mappingは
Contract上 NOT IMPLEMENTED である。

したがって、

Traditional Mapping = NOT IMPLEMENTED

はRuntime failureではない。

Current v1でこれを理由として、
代替の方位Meaningを生成してはならない。

no Traditional Mapping
→ continue without Traditional Interpretation

以下は禁止する。

no Traditional Mapping
→ derive meaning from goriyaku

no Traditional Mapping
→ derive meaning from history_theme

no Traditional Mapping
→ derive meaning from direction_profile

no Traditional Mapping
→ LLM-generated symbolism

### 12.4 Calculation Failure

Calculationが有効なDirection Runtime Resultを生成できない場合、
DirectionまたはMeaningを推測して補完しない。

invalid calculation
→ explicit calculation fail-safe state

禁止:

invalid calculation
→ invented direction

invalid calculation
→ default symbolic direction

invalid calculation
→ LLM completion

### 12.5 Synthesis Failure

Synthesisに必要なCanonical Evidenceが不足する場合、
存在しないMeaning Resultを作成してはならない。

sufficient allowed evidence
→ deterministic Meaning Result

insufficient allowed evidence
→ no Meaning Result

既存Recommendationが有効である場合、
Meaning Synthesis failureのみを理由として
Recommendation全体を破壊してはならない。

valid Recommendation
+
Meaning unavailable
=
Recommendation may remain valid

Meaning layerとRecommendation availabilityを分離する。


### 12.6 Expression Failure

有効なMeaning Resultが存在しない場合、
Expressionは以下のいずれかとする。

omit Meaning-specific expression

OR

render explicitly defined neutral fallback

neutral fallbackは、
新しいMeaning、Traditional claim、future prediction、
Shrine benefit claimを含んではならない。

禁止:

no Meaning Result
→ poetic invention

no Meaning Result
→ spiritual claim

no Meaning Result
→ traditional claim

no Meaning Result
→ specific benefit claim

no Meaning Result
→ LLM fallback

### 12.7 Existing Evidence Fallback

Meaning-specific Evidenceが不足する場合でも、
既存Recommendation Contract上で有効な
reason_facts等のEvidenceが存在する場合は、
そのEvidenceを既存Authorityの範囲内で利用できる。

ただし、

fallback to existing evidence
≠
create new meaning

とする。

FallbackはMeaning Authorityを拡張してはならない。


### 12.8 Presentation Isolation

Weekly ThemeまたはSupplementary Presentationの失敗を、
Calculation、Recommendation Ranking、
Canonical Meaningへ波及させてはならない。

Presentation failure
≠
Calculation failure

Presentation failure
≠
Recommendation failure

Presentation failure
≠
Canonical Meaning mutation

Current Weekly Contract等で定義された
既存fail-safe behaviorを優先する。


### 12.9 No LLM Recovery

Current Mother Ship Decision:

Compass LLM Policy = NO_LLM

したがって、
いずれのfail-safe経路でもLLMをRecovery Authorityとして使用しない。

禁止:

missing calculation
→ LLM

missing mapping
→ LLM

missing evidence
→ LLM

missing expression
→ LLM

### 12.10 Fail-safe Priority

Current v1のFail-safe優先順位は以下とする。

1. Preserve valid upstream facts / evidence
2. Preserve existing valid Recommendation behavior
3. Omit unavailable Meaning-specific output
4. Use only explicitly contracted neutral fallback
5. Never invent unsupported Meaning

Fail-safeによって、
Ranking、Canonical taxonomy、Stored dataを変更してはならない。


## 13. Explainability Contract


### 13.1 Purpose

Explainabilityは、
ユーザーまたは運用者が
「この表示はどのAuthorityから来たのか」を追跡可能にするための責務である。

Explainabilityは新しいMeaningを生成するAuthorityではない。

基本原則:

```text
Explanation
=
describe existing provenance and authority

NOT
=
invent additional meaning
```

### 13.2 Explainable Layers

Current v1では、
少なくとも以下の4種類を区別可能にする。

Calculation Fact
Traditional Interpretation
KAMI MUSUBI Interpretation
Presentation

各層は別Authorityとして説明する。

Calculation Fact

システムがCanonical Calculation Ruleに従って算出したRuntime Result。

例:

referenceDirections
calculationMethod
solarMonthIndex
targetYear
targetDate

Calculation Factは、
伝統上の意味や未来の結果が客観的事実であることを意味しない。

Traditional Interpretation

Canonical Traditional Mappingに基づく解釈。

Current v1ではTraditional Mappingが未実装のため、
Traditional Interpretationは生成しない。

Traditional Interpretation
=
NOT AVAILABLE IN CURRENT v1
KAMI MUSUBI Interpretation

既存Canonical Meaning Authorityと
Contractで許可されたSynthesis Ruleから得られる解釈。

これはTraditional InterpretationまたはCalculation Factと同一視しない。

Presentation

Meaning Resultをユーザーへ伝えるための表示表現。

例:

weekly_theme
directionSupportCopy
versioned curated copy
deterministic template

Presentation自体はMeaning Evidenceではない。


### 13.3 User-facing Explainability Boundary

将来的なUIでは、
以下のような説明導線を持てる構造を許可する。

この言葉の根拠を見る

ただしCurrent v1 Contractは
具体的なUI実装を要求しない。

Explainability UIを実装する場合、
少なくとも以下を区別可能にする。

算出結果
伝統上の解釈
KAMI MUSUBIによる意味接続
表示表現

Traditional Mappingが未実装である場合、
存在しないTraditional Interpretationを表示してはならない。


### 13.4 Provenance Fidelity

Explainabilityは、
実際に利用されたSource / Rule / Version / Evidenceのみを説明する。

禁止:

unused source
→ shown as rationale

missing mapping
→ described as traditional meaning

presentation copy
→ described as source evidence

inferred meaning
→ described as canonical

Explainabilityの説明文が、
実際のProvenanceより広い意味を主張してはならない。


### 13.5 No Reverse Authority

Explainability表示を理由として、
Presentationまたは説明文を上流Authorityへ昇格させてはならない。

Explanation text
≠
Meaning Authority

Explanation label
≠
Canonical taxonomy

Explanation UI
≠
Recommendation Evidence

### 13.6 LLM Boundary

Current Mother Ship Decision:

Compass LLM Policy = NO_LLM

したがってCurrent v1では、
Explainability生成にもLLMを使用しない。

禁止:

LLM-generated rationale
LLM-generated provenance
LLM-generated traditional explanation
LLM-generated confidence explanation

Explainabilityはversioned deterministic copyまたは
明示的なProvenance情報から構成する。


### 13.7 Unknown Explanation

根拠を説明できない場合、
もっともらしい説明を生成してはならない。

基本原則:

unknown rationale
→ disclose unavailable explanation
   or omit explanation

NOT
→ invent rationale

## 14. Weekly Presentation Boundary

### 14.1 Responsibility

Weekly Presentationは、
既存Recommendation Resultをもとに
週単位の継続的なPresentationを提供する責務を持つ。

Weekly Presentationは
Compass Meaning AuthorityまたはRecommendation Authorityではない。


### 14.2 Weekly Theme Authority

weekly_themeは、
Current Weekly Contract上のdeterministic Presentation Copyである。

weekly_theme
=
Presentation Authority

以下ではない。

weekly_theme
≠
Traditional Meaning

weekly_theme
≠
Canonical history_theme

weekly_theme
≠
goriyaku

weekly_theme
≠
Recommendation Signal

weekly_theme
≠
Ranking Signal

### 14.3 Theme Selection Inputs

Current Weekly Presentationでは、
以下の値をdeterministic selection identityとして利用しうる。

purpose
direction_fingerprint
week_start
presentation_version

ただし、
direction_fingerprintをMeaning Signalとして解釈してはならない。

direction_fingerprint
→ deterministic presentation selection

NOT

direction_fingerprint
→ geographic direction meaning

### 14.4 No Direction Symbolism

Weekly Presentationは、
Current v1ではCompass geographic directionへ
象徴的意味を付与しない。

禁止例:

北だから守り
南だから挑戦
東だから再出発

Weekly Themeの選択に
direction fingerprintが利用されていても、
それはdeterministic selectionのためであり、
方向Meaningの存在を意味しない。


### 14.5 Snapshot Boundary

Weekly Presentation Snapshotは、
Presentationの再現性・継続性を保つためのPersistenceである。

Weekly Presentation Snapshot
=
Presentation persistence

以下を意味しない。

snapshot
≠
Canonical Meaning storage

snapshot
≠
Traditional Interpretation storage

snapshot
≠
Recommendation history authority

Persistenceの存在はMeaning Authorityを生成しない。


### 14.6 Hydration Boundary

Weekly PresentationがSnapshotからShrine情報を再取得・hydrateする場合も、
Current Shrine eligibility / serializer / evidence authorityに従う。

Presentation Snapshotに保存されていることだけを理由として、
現在無効なShrineを強制的にMeaning対象へ復活させてはならない。


### 14.7 Failure Isolation

Weekly Presentation failureは、
Monthly Compass ResultまたはRecommendation Resultを破壊してはならない。

Weekly Presentation failure
≠
Monthly Recommendation failure

Weekly Theme生成やSnapshot取得に失敗した場合、
既存Recommendationが有効であればその結果を維持する。


### 14.8 Meaning Reverse-flow Prohibition

Weekly Presentation outputを
Meaning SynthesisまたはRecommendationへ逆流させてはならない。

禁止:

weekly_theme
→ history_theme

weekly_theme
→ goriyaku

weekly_theme
→ reason_facts

weekly_theme
→ ranking bonus

featured shrine selection
→ new recommendation evidence

### 14.9 Versioning Boundary

Weekly Presentationのcopyまたはselection ruleを変更する場合、
presentation_version等により変更を識別可能にする。

ただし、

presentation version change
≠
Meaning taxonomy change

とする。


## 15. Recommendation / Ranking Boundary

### 15.1 Responsibility Separation

Compass MeaningとRecommendationは、
連携するが同一Authorityではない。

Meaning Authority
≠
Recommendation Authority

Current v1では、
Meaning ContractがRecommendation Rankingを変更しない。


### 15.2 Existing Recommendation Authority

Current Compassは、
既存Recommendation経路を再利用する。

Meaning Contract v1は、
以下の既存責務を変更しない。

candidate generation
eligibility
direction filtering
distance stage
ranking
recommendation score
reason generation contract

これらの変更は、
Recommendation ContractまたはRuntime Contractの別工程とする。


### 15.3 No New Ranking Signal

Current v1では、
Meaning Contractで新たに定義されたMeaning Resultを
Ranking Signalへ追加してはならない。

禁止:

Traditional Interpretation
→ ranking bonus

Synthesis Meaning Result
→ score weight

Expression wording
→ ranking

weekly_theme
→ ranking

directionSupportCopy
→ ranking

non-canonical vocabulary
→ ranking

### 15.4 Geographic Direction Boundary

Compass geographic directionは、
既存Contract上のDirection Filteringに利用できる。

ただし、

direction used for geographic filtering
≠
direction meaning used for ranking

とする。

Current v1では、
方向の象徴意味をRankingへ利用してはならない。


### 15.5 Existing Evidence Boundary

Recommendation Reasonは、
既存Recommendation Evidence Authorityに従う。

Meaning Contractは、
存在しないEvidenceをReasonへ追加してはならない。

no traditional mapping
→ no traditional direction reason

no stored history_theme
→ no fabricated history_theme reason

no goriyaku evidence
→ no fabricated benefit reason

### 15.6 Synthesis Does Not Override Recommendation

Synthesis Resultが生成されても、
それだけを理由として既存Recommendationを上書きしてはならない。

Meaning Result
≠
Recommendation override

Current v1では以下を禁止する。

Meaning Result
→ candidate exclusion

Meaning Result
→ candidate insertion

Meaning Result
→ rank reorder

Meaning Result
→ eligibility override

### 15.7 Expression Does Not Alter Recommendation

ユーザー向けcopyはRecommendation Resultへ影響しない。

Presentation
→ display only

NOT

Presentation
→ recommendation logic

copy変更によって候補順、score、eligibilityが変化してはならない。


### 15.8 Missing Meaning Does Not Invalidate Recommendation

有効なRecommendation Evidenceが存在する場合、
Meaning-specific Evidenceが不足していることだけを理由として
Recommendation自体を無効化してはならない。

valid Recommendation
+
Meaning unavailable
=
Recommendation may remain valid

この場合、
Meaning-specific Expressionのみをfail-safeする。


### 15.9 Future Ranking Integration Gate

将来Meaning SignalをRankingへ導入する場合、
Current v1の単純な実装拡張として扱わない。

以下を最低限必要とする。

Mother Ship Decision
Recommendation Contract change
explicit signal definition
weight definition
evidence requirement
determinism requirement
regression testing
analytics impact review

Current v1では、
Meaning → Ranking connectionは存在しないものとして扱う。


## 16. Prohibited Connections


### 16.1 Principle

Current Compass Meaning Contract v1では、
明示的に許可されていないMeaning connectionを追加してはならない。

基本原則:

```text
absence of an allowed mapping
≠
permission to infer a mapping

```
既存コード、文字列類似、Presentation Copy、
legacy behavior、LLM output等を根拠として
新しいCanonical connectionを暗黙に作成してはならない。


### 16.2 Geographic Direction → Meaning

Current v1では以下を禁止する。

Compass geographic direction
→ traditional symbolism

Compass geographic direction
→ history_theme

Compass geographic direction
→ goriyaku

Compass geographic direction
→ consultation_axis

Compass geographic direction
→ psychological state

Compass geographic direction
→ personality interpretation

Current v1におけるgeographic directionは、
Calculation / geographic filtering responsibilityに留まる。


### 16.3 Direction Namespace Mixing

以下を同一視してはならない。

Compass referenceDirections
≠
Consultation direction_profile.direction
≠
Google routing direction
≠
Concierge direction_reference

directionという名称が共通していることは、
Meaning connectionの根拠にならない。


### 16.4 Goriyaku ↔ history_theme

以下の直接変換を禁止する。

goriyaku
→ history_theme

history_theme
→ goriyaku

同一または類似する日本語ラベルを持つ場合も、
文字列一致のみを根拠としてMappingしてはならない。

例:

GoriyakuTag: 導き
≠
history-theme-like vocabulary: 導き

### 16.5 Non-canonical Vocabulary → Canonical Taxonomy

以下を禁止する。

浄化
導き
巡り
→ automatic canonical history_theme promotion

non-canonical / legacy / presentation vocabularyは、
Mother Ship DecisionなしにCanonical taxonomyへ昇格させてはならない。


### 16.6 Astrology / Element → Compass Meaning

Current v1では以下を禁止する。

astrology
→ Compass Meaning

planet
→ history_theme

planet
→ goriyaku

element
→ Compass Meaning

element
→ ranking

Astrology / ElementをCompass Meaningへ導入する場合は、
別のMother Ship Decisionを必要とする。


### 16.7 Weekly Presentation → Meaning / Recommendation

以下を禁止する。

weekly_theme
→ history_theme

weekly_theme
→ goriyaku

weekly_theme
→ reason_facts

weekly_theme
→ Recommendation Signal

weekly_theme
→ Ranking Signal

また、

direction_fingerprint
→ user-facing direction meaning

も禁止する。

direction_fingerprintはdeterministic identityであり、
Meaning Signalではない。


### 16.8 Expression → Upstream Authority

PresentationまたはExpressionを上流へ逆流させてはならない。

禁止:

Expression Copy
→ Meaning Evidence

Expression Copy
→ Canonical taxonomy

Expression Copy
→ Recommendation Evidence

Expression Copy
→ Ranking Signal

Explainability Copy
→ Provenance Source

Expressionはdisplay responsibilityに留まる。


### 16.9 Meaning → Ranking

Current v1では以下を禁止する。

Traditional Interpretation
→ ranking bonus

Synthesis Meaning Result
→ ranking weight

Meaning label
→ candidate reorder

Meaning Result
→ eligibility override

Meaning Result
→ candidate insertion / exclusion

MeaningをRankingへ接続する場合は、
Recommendation Contract変更とMother Ship Decisionを必要とする。


### 16.10 Missing Evidence → Inferred Meaning

Evidence不足を推測で補完してはならない。

禁止:

missing history_theme
→ infer from shrine name

missing history_theme
→ infer from goriyaku similarity

missing Meaning Evidence
→ infer from geographic direction

missing Traditional Mapping
→ infer from existing Meaning vocabulary

missing Evidence
→ LLM-generated Meaning

### 16.11 LLM Connections

Current Mother Ship Decision:

Compass LLM Policy = NO_LLM

Current v1ではLLMを以下へ接続してはならない。

LLM
→ Calculation

LLM
→ Traditional Mapping

LLM
→ Synthesis

LLM
→ Expression

LLM
→ Explainability

LLM
→ Fail-safe recovery

LLM
→ Recommendation Reason for Compass Meaning

LLMを単なる言い換え用途として利用する場合も、
Current v1では許可しない。


### 16.12 Persistence → Authority

以下を禁止する。

value persisted
→ assume canonical

snapshot exists
→ assume Meaning Authority

legacy field exists
→ assume active canonical taxonomy

Persistenceの存在は、
Canonical Authorityの証明にならない。


## 17. Mother Ship Decision Gate

### 17.1 Current Gate Status

Compass Meaning Contract v1のCurrent Scopeについては、
新規blocking Mother Ship Decisionを必要としない。

既に以下が確定している。

Compass LLM Policy
=
NO_LLM

またCurrent v1では、

Traditional Mapping
=
NOT IMPLEMENTED

を正式なContract状態として扱う。

既存Canonical history_theme v1は、
現行7値をそのまま利用し、
Current Contractでは変更しない。


### 17.2 Changes Requiring Mother Ship Decision

以下の変更を行う場合、
実装開始前に新しいMother Ship Decisionを必要とする。


#### A. Traditional Mapping Introduction
Compass geographic direction
→ Traditional Meaning

を導入する場合。

決定対象には少なくとも以下を含む。

Canonical traditional system
Canonical source
Rule set
Versioning
Conflicting-school policy
Provenance policy
User-facing interpretation policy

#### B. Canonical history_theme Expansion

Current canonical 7値を追加・削除・統合・変更する場合。


#### C. Non-canonical Vocabulary Promotion

以下をCanonical history_themeへ昇格する場合。

浄化
導き
巡り

#### D. Common Meaning Vocabulary Introduction

Compass / Concierge / Shrine / Traditional Meaning間を接続する
新しいCommon Meaning Vocabularyを導入する場合。


#### E. Astrology / Element Introduction

Astrology、planet、element等を
Compass Meaning Authorityとして導入する場合。


#### F. LLM Authority Introduction

LLMを以下のいずれかへ導入する場合。

Traditional Mapping
Synthesis
Expression
Explainability
Fail-safe

#### G. Meaning → Ranking Integration

Meaning Resultを
Recommendation Ranking / Score / Eligibilityへ反映する場合。


### 17.3 Decision Before Implementation

Mother Ship Decisionが必要な変更については、
Runtime実装、DB変更、taxonomy変更、
copy追加を先行してはならない。

Mother Ship Decision
↓
Contract change
↓
Implementation
↓
Test
↓
Review

の順序を守る。


### 17.4 No Implicit Decision

以下をMother Ship Decisionの代替として扱ってはならない。

existing code
legacy behavior
test fixture
presentation copy
developer interpretation
LLM suggestion
temporary implementation

Mother Ship Decisionが存在しない場合、
Current Contractの境界を維持する。


### 17.5 Contract Versioning

Mother Ship Decisionによって
Meaning Authority、Canonical taxonomy、
Mapping Rule、Ranking integration等が変更される場合、
必要に応じてCompass Meaning ContractのVersionを更新する。

Current v1と互換性のないMeaning behaviorを、
v1のまま暗黙に変更してはならない。


## 18. Acceptance Criteria

Compass Meaning Contract v1は、
以下をすべて満たした場合にContractとして成立する。


### 18.1 Architecture
Calculation
Traditional Mapping
Synthesis
Expression

の4層が明確に分離されていること。

Current v1で以下が明記されていること。

Traditional Mapping
=
NOT IMPLEMENTED

### 18.2 Calculation Boundary

CalculationがMeaning Authorityを持たないこと。

以下が禁止されていること。

referenceDirections
→ history_theme

referenceDirections
→ goriyaku

referenceDirections
→ traditional symbolism

Calculationがdeterministic / recomputableであり、
LLMを使用しないこと。


### 18.3 Canonical Meaning Boundary

Canonical history_theme v1が
既存7値に固定されていること。

浄化 / 導き / 巡りが
non-canonicalとして扱われていること。

goriyakuとhistory_themeが
別namespaceとして定義されていること。


### 18.4 Stored Data Boundary

以下が明示されていること。

Canonical taxonomy exists
≠
Stored data is populated

Shrine.history_theme等のStored coverageを
Contractが暗黙に仮定しないこと。

Persistenceの存在が
Meaning Authorityを意味しないこと。


### 18.5 Provenance

Canonical Meaning transformationについて、
Source / Rule / Version / Input / Output /
Transformation pathを追跡可能にする原則が定義されていること。

Traditional Mappingを将来導入する場合に、

Canonical Source
Rule
Version
Provenance

が必須であること。


### 18.6 Synthesis Boundary

Synthesisが既存Canonical Authorityを再利用し、
新しいCompass-specific taxonomyを作成しないこと。

Stored Evidence不足時に
Meaningを推測して補完しないこと。

Current v1でgeographic directionを
Meaning Synthesis Signalとして利用しないこと。


### 18.7 Expression Boundary

Expressionが以下を満たすこと。

deterministic
versioned
auditable
non-predictive
non-assertive
LLM Authority = NONE

Expressionが新しいMeaning Evidenceを生成しないこと。

Presentation Copyが上流Authorityへ逆流しないこと。


### 18.8 Explainability

以下を区別可能なContractになっていること。

Calculation Fact
Traditional Interpretation
KAMI MUSUBI Interpretation
Presentation

Current v1ではTraditional Interpretationが
存在しないことを正しく表現できること。

ExplainabilityがProvenance以上の主張を追加しないこと。


### 18.9 Weekly Presentation

weekly_themeがPresentation Authorityに限定されていること。

direction_fingerprintが
Meaning Signalではないこと。

Weekly Presentation Snapshotが
Presentation persistenceとして定義されていること。

Weekly failureが既存の有効なRecommendationを
破壊しない境界が存在すること。


### 18.10 Recommendation / Ranking

Meaning Contract v1が
既存Recommendation Ranking / Score / Eligibilityを変更しないこと。

Meaning Result、Weekly Theme、Expression Copy、
Traditional Interpretation等が
新しいRanking Signalにならないこと。

Meaning unavailableのみを理由として、
有効なRecommendationを無効化しないこと。


### 18.11 Fail-safe

各層のfail-safeがAuthority境界を越えないこと。

以下が成立すること。

missing evidence
→ omit unsupported Meaning

NOT

missing evidence
→ invent Meaning

Current v1のいずれのfail-safeでも
LLM Recoveryを利用しないこと。


### 18.12 Mother Ship Gate

以下の変更が
Mother Ship Decision対象として明記されていること。

Traditional Mapping introduction
history_theme taxonomy change
non-canonical vocabulary promotion
Common Meaning Vocabulary introduction
Astrology / Element introduction
LLM Authority introduction
Meaning → Ranking integration

### 18.13 Docs-only Scope

本Contract作成PRでは、
以下を変更しないこと。

Runtime
API
Model
Migration
DB data
Recommendation Ranking
Recommendation Score
Frontend UI
Analytics event
Weekly runtime behavior
Kyusei calculation
LLM runtime route

### 18.14 Final Contract Gate

以下の状態であれば、
Compass Meaning Contract v1をCurrent Product Contractとして扱える。

Authority boundaries are explicit
+
Canonical vocabulary is bounded
+
Unsupported mappings are prohibited
+
Provenance requirements are defined
+
Fail-safe behavior is defined
+
LLM Authority = NONE
+
Mother Ship gates are explicit
