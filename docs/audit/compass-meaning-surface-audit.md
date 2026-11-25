# Compass Meaning Surface Audit

> Status: Active Audit Record
>
> 本書は、KAMI MUSUBI Compassにおける現行Meaning関連surfaceを監査し、
> Calculation / Consultation Interpretation / Shrine Meaning / Recommendation Evidence /
> Presentationの責務境界を明確化するためのdocs-only監査記録である。
>
> 本書はRuntime / API / Model / Migration / Ranking / Recommendation Score /
> Analytics event / DB data / Frontend UIを変更しない。
>
> 本監査では新しい方位意味体系、history_theme taxonomy、goriyaku taxonomy、
> astrology / element mappingを作成しない。

---

## 1. Purpose

Compass Current Contract Alignment完了後の次工程として、
Compass Meaning Contract v1を安全に設計するために、現行実装上のMeaning surfaceを確定する。

特に以下を確認する。

- Compass固有CalculationとMeaningの境界
- Compass地理方位と`direction_profile`の命名衝突
- `purpose` / `need_tags`と既存Recommendation Meaningの接続
- `history_theme`のCanonical Authority
- `goriyaku`と`history_theme`の責務分離
- Weekly ThemeのMeaning Authority有無
- `direction_fingerprint`の意味的責務有無
- non-canonical Meaning vocabularyの残存状況
- Compass Meaning Contract v1へ渡す制約
- 新規Mother Ship Decisionの要否

---

## 2. Audit Scope

対象は現行Compassの以下の経路とする。

```text
User Input
  ↓
Compass Direction Calculation
  ↓
Direction Filtering
  ↓
Recommendation Orchestration
  ↓
Existing Consultation / Shrine Meaning
  ↓
Recommendation Evidence / Reason
  ↓
Monthly / Weekly Presentation
```

主な確認対象:

backend/temples/services/compass_runtime.py
backend/temples/services/compass_recommendation_orchestrator.py
backend/temples/services/weekly_compass_service.py
backend/temples/domain/weekly_presentation.py
backend/temples/domain/weekly_theme_catalog_v1.py

backend/temples/services/consultation_interpreter.py
backend/temples/services/meaning_translation.py
backend/temples/services/shrine_meaning_composer.py

backend/temples/domain/history_theme_taxonomy_v1.py

docs/core/meaning-layer.md
docs/core/meaning-layer-connection.md
docs/product/meaning-translation-mapping.md
docs/product/history-theme-taxonomy.md
docs/product/compass-product-contract.md
docs/product/compass-weekly-presentation-contract.md

## 3. Executive Summary
### FACT 1 — Compass地理方位からMeaningを直接生成する現行mappingは確認されない

Compass Direction Runtimeが生成する主な値は以下である。

referenceDirections
calculationMethod
solarMonthIndex
targetYear
targetDate
note

referenceDirectionsはDirection Filterに利用される。

現行Compass経路では、

referenceDirections
→ history_theme

または

referenceDirections
→ goriyaku

という直接mappingは確認されない。

したがって、現行Compassの地理方位はCalculation / Filtering Authorityであり、
Meaning Authorityではない。

### FACT 2 — direction_profileはCompass地理方位とは別概念である

consultation_interpreter.pyには以下の相談状態由来のdirection_profileが存在する。

tired
→ rest

anxious
→ stabilize

uncertain
→ review

stuck
→ reset

ready_to_change
→ challenge

この値は東西南北等のCompass地理方位ではない。

direction_profile.direction
≠
Compass referenceDirections

meaning_translation.pyのHISTORY_THEME_BY_DIRECTIONも、
この相談解釈上のdirection_profile.directionを対象とする。

rest       → 静寂
stabilize  → 守り
review     → 静寂
reset      → 再出発
challenge  → 勝負

これはCompass方位Meaning mappingではない。

### FACT 3 — Compassではdirection_profile由来Meaningが実質発火しない

Compass Recommendation Orchestratorは、

interpret_consultation(
    query="",
    need_tags=[purpose_slug],
    selected_goriyaku_tag_ids=[],
)

を呼び出す。

query=""のため、

state_profile.primary_state = None
direction_profile.direction = None
direction_profile.themes = []

となる。

したがってCompassで既存Meaning Translationが利用される場合も、
地理方位ではなく主にpurpose / need_tags側からMeaningへ接続される。

### FACT 4 — Compass Meaningは既存Recommendation / Knowledge資産を再利用する

Compassは独自のShrine Meaning taxonomyを持たない。

既存の以下の資産を共有Recommendation経路から再利用する。

purpose
need_tags
consultation_axis
history_theme
goriyaku / goriyaku_tags
reason_facts

したがってCompass Meaning Contractは、
既存Meaning Authorityを無視して新しいMeaning taxonomyを並列作成してはならない。

### FACT 5 — Canonical history_theme v1は7値である

Canonical Authority:

backend/temples/domain/history_theme_taxonomy_v1.py
docs/product/history-theme-taxonomy.md

Mother Ship FINAL v1は以下の7値である。

| Canonical key | Display label |
| --- | --- |
| history_theme:restart | 再出発 |
| history_theme:stillness | 静寂 |
| history_theme:restoration | 復興 |
| history_theme:challenge | 勝負 |
| history_theme:connection | 縁 |
| history_theme:learning | 学び |
| history_theme:protection | 守り |

Canonical keyがmachine identityであり、日本語ラベルはdisplay valueである。

### FACT 6 — 浄化 / 導き / 巡りはCanonical history_theme v1ではない

shrine_meaning_composer.py等には以下のMeaning-like vocabularyが残存する。

浄化
導き
巡り

これらは、

Shrine Meaning Composer
Recommendation Output Snapshot
過去のAnalytics / Audit
Presentation copy

等で確認される。

しかし、

HISTORY_THEME_V1_CANONICAL_KEYS

には含まれない。

したがって本監査では以下のように分類する。

Canonical history_theme v1
  = 7 values

浄化 / 導き / 巡り
  = non-canonical compatibility / legacy / presentation vocabulary

本監査ではこれら3値をCanonical taxonomyへ昇格させない。

### FACT 7 — 「導き」はnamespace collisionを持つ

導きはMeaning-like vocabularyとして残存するだけでなく、
現行GoriyakuTagにも存在する。

したがって、

goriyaku = 導き

と

history-theme-like vocabulary = 導き

は同一文字列でも別Authorityとして扱う必要がある。

文字列一致だけで、

goriyaku
↔
history_theme

を相互変換してはならない。

### FACT 8 — 現行Local DBではShrine.history_theme実値は0件

本監査時点のローカルjinja_dbをread-onlyで確認した。

Shrine total               = 104
nonempty history_theme     = 0
blank history_theme        = 104
null history_theme         = 0

したがって、

current local Shrine.history_theme
= 104 / 104 blank

である。

Canonical 7値およびnon-canonicalな

浄化
導き
巡り

のいずれも、現在接続しているLocal DBのShrine.history_theme実値としては観測されなかった。

これはLocal DB Observationである。

Production DBのShrine.history_theme状態は本監査では確認していないため、
Productionについて同じ結論を適用しない。

### FACT 9 — Weekly ThemeはMeaning Mappingではない

weekly_theme_catalog_v1.pyは明示的にWeekly Themeを、

Presentation Copy

として定義している。

Weekly Themeは、

Candidate generation
Filtering
Ranking
Recommendation Reason

へ影響しない。

選択には、

purpose
direction_fingerprint
week_start
presentation_version

をdeterministic seedとして利用する。

ただしdirection_fingerprintは方位の象徴意味として利用しない。

direction_fingerprint
→ deterministic selection identity

NOT

direction_fingerprint
→ direction meaning

catalog文言も方位に言及しない。

### FACT 10 — direction_fingerprintはMeaning Authorityではない

direction_fingerprintはWeekly Presentation identityを安定させる内部識別値である。

現行v1では以下から構築する。

referenceDirections
calculationMethod
solarMonthIndex
targetYear

以下には利用しない。

Meaning explanation
Direction symbolism
Recommendation score
Shrine meaning
### FACT 11 — directionSupportCopyはSupplementary Presentationである

Shrine Meaning Composerには、

directionBonus
directionReason
directionSupportCopy

が存在する。

現行テストではdirectionSupportCopyが、

heroMeaningCopy
shrineMeaning
actionMeaning

を変更しないことが固定されている。

したがってこれは、

Meaning Authority

ではなく、

Supplementary Presentation

として分類する。

## 4. Current Meaning Surface Matrix
| Surface                                        | Current Authority                     | Lifecycle                           | Compass Current Role                       | Meaning Authority                   |
| ---------------------------------------------- | ------------------------------------- | ----------------------------------- | ------------------------------------------ | ----------------------------------- |
| `referenceDirections`                          | Compass Runtime                       | Runtime                             | Direction Filter                           | No                                  |
| `calculationMethod`                            | Compass Runtime                       | Runtime                             | Calculation metadata                       | No                                  |
| `solarMonthIndex`                              | Compass Runtime                       | Runtime                             | Calculation metadata                       | No                                  |
| `targetYear`                                   | Compass Runtime                       | Runtime                             | Calculation metadata                       | No                                  |
| `direction_fingerprint`                        | Weekly Presentation                   | Derived / Snapshot identity         | Deterministic seed                         | No                                  |
| `purpose`                                      | `NEED_TAGS`                           | Request                             | Recommendation input                       | Input only                          |
| `need_tags`                                    | Consultation / Recommendation         | Runtime                             | Semantic routing                           | Yes, existing shared authority      |
| `direction_profile`                            | Consultation Interpretation           | Runtime                             | Compassでは`query=""`のため空              | Yes, but NOT geographic direction   |
| `consultation_axis`                            | Consultation Interpretation           | Runtime                             | Shared Recommendation signal               | Yes, existing shared authority      |
| canonical `history_theme`                      | History Theme Taxonomy v1             | Canonical taxonomy                  | Shrine-side meaning vocabulary             | Yes                                 |
| `Shrine.history_theme`                         | Legacy compatibility field            | Stored                              | Local DB 104/104 blank                     | Compatibility path                  |
| `goriyaku` / `goriyaku_tags`                   | Shrine Benefit / Evidence             | Stored                              | Eligibility / Recommendation / Explanation | Separate meaning/evidence authority |
| `reason_facts`                                 | Recommendation                        | Runtime                             | Recommendation evidence / explanation      | Derived evidence                    |
| `weekly_theme`                                 | Weekly Presentation                   | Snapshot                            | Deterministic display copy                 | No                                  |
| `directionSupportCopy`                         | Shrine Meaning Presentation           | Runtime                             | Supplementary copy                         | No                                  |
| 浄化 / 導き / 巡り as history-theme-like words | Legacy / compatibility / presentation | Code / docs                         | Old output / Composer copy                 | Non-canonical                       |
| 導き as `GoriyakuTag`                          | Goriyaku taxonomy                     | Stored / canonical in its namespace | Benefit / evidence                         | Yes, but not `history_theme`        |
| astrology / astro element                      | Concierge compat path                 | Runtime                             | Compass Meaningでは未使用                  | Scope Out                           |
## 5. Current Meaning Architecture

現行CompassをMeaning責務で整理すると以下になる。

```text
Compass Calculation
  │
  ├─ birthdate
  ├─ target_date
  ├─ year/month kyusei calculation
  └─ referenceDirections
        │
        ▼
Direction Filtering
        │
        │  方位自体をMeaningへ変換しない
        ▼
Recommendation Orchestration
        │
        ├─ purpose
        └─ need_tags
              │
              ▼
Existing Consultation / Recommendation Meaning
        │
        ├─ consultation_axis
        ├─ canonical history_theme
        ├─ goriyaku evidence
        └─ reason_facts
              │
              ▼
Expression / Presentation
```

Weekly Presentationは別責務である。

```text
purpose
+
direction_fingerprint
+
week_start
+
presentation_version
        ↓
deterministic catalog selection
        ↓
weekly_theme
```

Weekly ThemeはDirection Meaningではない。

## 6. Meaning Contract v1 Constraints

Compass Meaning Contract v1は以下を前提とする。

### 6-1. Calculation

CalculationはMeaningを生成しない。

birthdate
target_date
↓
kyusei calculation
↓
referenceDirections

Calculation resultは事実上のRuntime calculation outputとして扱い、
心理・人生・ご利益・神社Meaningを付与しない。

### 6-2. Traditional Mapping

Current implementation:

NOT IMPLEMENTED

Compass地理方位から伝統上の象徴意味へ変換するCanonical Mappingは、
現行Runtimeには存在しない。

したがってMeaning Contract v1は、
存在しないmappingを実装済みのように扱わない。

特に以下を禁止する。

referenceDirection
→ arbitrary meaning

referenceDirection
→ goriyaku

referenceDirection
→ history_theme

Traditional Mappingを将来導入する場合は、

canonical source
rules
version
provenance

を明示し、別工程として設計する。

### 6-3. Synthesis

v1ではCompass独自の新Meaning taxonomyを追加しない。

既存Canonical Meaning Authorityを優先する。
Canonical taxonomyの存在は、Stored data coverageの存在を保証しない。
Meaning Contract v1は、`Shrine.history_theme`にCanonical値が保存済みであることを前提としない。

history_theme v1
goriyaku taxonomy
need_tags
consultation_axis

ただし異なるnamespaceを同一視しない。

例:

goriyaku: 導き
≠
history_theme: 導き

Canonical history_themeに存在しない文字列を、
文字列類似だけで自動変換または昇格してはならない。

### 6-4. Expression

Compass Expressionは以下を満たす。

deterministic
versioned
auditable
non-predictive
non-assertive
LLM Authority = NONE

Current Mother Ship Decision:

Compass LLM Policy = NO_LLM

したがってLLMは、

Traditional Mapping
Synthesis
Weekly Theme
Compass user-facing expression

のAuthorityを持たない。

## 7. Prohibited v1 Connections

Compass Meaning Contract v1では以下を行わない。

Compass direction → goriyaku direct mapping
Compass direction → history_theme direct mapping

planet / astrology → goriyaku
planet / astrology → history_theme

element → Meaning

non-canonical vocabulary → canonical history_theme automatic promotion

weekly_theme → Recommendation Signal

direction_fingerprint → user-facing meaning

LLM → Meaning generation

Meaning copy → Ranking weight
## 8. Fact / Interpretation / Presentation Boundary

Meaning Contract v1では最低限以下を区別する。

### Calculation Fact
referenceDirections
calculationMethod
solarMonthIndex
targetYear

システム計算結果。

### Traditional Interpretation

現行Compassでは未実装。

将来導入する場合、Source / Rule / Version必須。

### KAMI MUSUBI Interpretation

既存Meaning taxonomyやConsultation Meaningとの接続結果。

Factまたは伝統解釈と同一視しない。

### Presentation
weekly_theme
directionSupportCopy
user-facing templates

ユーザー表示用表現。

Presentation CopyをRecommendation Evidenceとして逆流させない。

## 9. Local DB Observation

Audit environment:

DB host = 127.0.0.1
DB name = jinja_db
Shrine rows = 104

read-only確認結果:

nonempty Shrine.history_theme = 0
blank Shrine.history_theme    = 104
null Shrine.history_theme     = 0

Interpretation:

Local DBではShrine.history_theme実値を確認できない。

これはtaxonomy自体が存在しないことを意味しない。

Canonical taxonomyはコード上に存在する。

またProduction dataを代表する証拠として扱わない。

## 10. Known Drift / Naming Risks
### D1. direction semantic collision

少なくとも以下は別概念である。

Compass geographic direction
Consultation direction_profile
Google routing direction
Concierge direction_reference

Meaning Contractではdirectionという名前だけからAuthorityを推定しない。

### D2. Canonical 7 vs Composer vocabulary

Canonical history_theme v1:

7 values

Shrine Meaning Composer:

7 canonical values
+
浄化
導き
巡り

後者3値をCanonicalとみなさない。

### D3. 導き namespace collision
GoriyakuTag: 導き

は存在する。

同名のMeaning-like vocabularyと混同しない。

### D4. Local Stored Meaning coverage

Local DBではShrine.history_themeが104/104 blankである。

Meaning ContractからStored data coverage改善を暗黙に仮定しない。

## 11. Mother Ship Decision Assessment
### Current Meaning Contract v1 Gate

新規blocking Mother Ship Decisionは不要。

理由:

Compass LLM PolicyはすでにNO_LLMで確定している
Canonical history_theme v1はMother Ship FINAL 7値として確定している
Compass地理方位からMeaningへのmappingは現行実装に存在しない
v1では新taxonomyを追加しない
v1ではTraditional Mappingを未実装のまま明示できる

したがってCompass Meaning Contract v1は、
既存Authorityを変更せず責務境界を定義できる。

### Future Mother Ship Decision Required

以下を行う場合は新しいMother Ship Decisionを必要とする。

A. Compass geographic direction → Traditional Meaning mappingを導入する

B. history_theme v1を7値から拡張する

C. 浄化 / 導き / 巡りをCanonical history_themeへ昇格する

D. 新しいCommon Meaning Vocabularyを作る

E. Compass Meaningへastrology / elementを追加する

F. LLMをCompass Meaning Authorityへ追加する

G. Meaning signalをRankingへ新規反映する

本監査ではこれらを決定しない。

## 12. Meaning Contract v1 Target Architecture

Current-state evidenceから、
Meaning Contract v1は以下の境界を採用できる。

```text
1. Calculation
   ↓
   deterministic Compass calculation

2. Traditional Mapping
   ↓
   CURRENTLY NOT IMPLEMENTED

3. Synthesis
   ↓
   existing canonical Meaning Authorityを尊重
   direct geographic-direction mappingなし

4. Expression
   ↓
   deterministic
   versioned
   auditable
   NO_LLM
```

重要:

Meaning Contractを作ること
≠
Traditional Mappingを新設すること

未実装責務を「未実装」と明示することもContractの一部である。

## 13. Out of Scope

本監査では以下を変更しない。

Direction calculation
Kyusei calculation precision
target_date
Recommendation ranking
Recommendation score
NEED_TO_GORIYAKU_IDS
consultation_axis
history_theme canonical taxonomy
Shrine.history_theme DB data
Goriyaku taxonomy
Weekly Theme catalog
Weekly Snapshot
Frontend UI
Analytics
Free / Premium gate
Astrology
Element
LLM runtime route
Production DB
## 14. Audit Conclusion

現行Compassは、

deterministic geographic Direction Calculation
+
existing Recommendation Meaning reuse
+
deterministic Presentation

という構造である。

現行Runtimeには、

Compass geographic direction
→ symbolic / traditional meaning

という正式なMeaning Mapping層は存在しない。

したがってCompass Meaning Contract v1では、

Calculation
↓
Traditional Mapping = NOT IMPLEMENTED
↓
Synthesis = existing Meaning Authority boundary
↓
Expression = deterministic / versioned / NO_LLM

を基本境界とする。

Canonical history_theme v1は既存7値を正本とし、
浄化 / 導き / 巡り等のnon-canonical vocabularyを自動昇格しない。

新規taxonomy、方位Meaning mapping、astrology / element、LLM導入は行わない。

この条件では新規blocking Mother Ship Decisionは不要であり、
Compass Meaning Contract v1の設計へ進行可能である。

## 15. Next Gate

本監査完了後の次工程:

Compass Meaning Contract v1

Contractでは最低限以下を正式化する。

Calculation Authority
Traditional Mapping boundary
Synthesis Authority
Expression Authority
Source / Rule / Version provenance
Canonical taxonomy reuse
namespace isolation
LLM Authority = NONE
Fail-safe behavior
Explainability boundary

Runtime implementationはMeaning Contract確定後の別PRとする。
