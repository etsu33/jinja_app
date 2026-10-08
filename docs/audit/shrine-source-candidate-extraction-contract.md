# Shrine Source Candidate Extraction Contract

> **Status: CONTRACT FROZEN / IMPLEMENTATION NOT STARTED**
>
> **Scope:** 47都道府県Source管理で `acquisition_scope = 全件取得可能` と確定した
> 15都道府県の公式Sourceを、既存Shrine identity / duplicate detection契約を壊さず
> Existence Candidateへ変換する入口契約。
>
> **Non-goal:** 本文書はProduction Import、Knowledge Fact生成、Coordinate確定、
> Recommendation変更、既存Shrine更新を行わない。

# 1. Objective

47都道府県の神社庁Source管理を正本化した結果、2026-10-08時点で
`全件取得可能` と分類された15都道府県について、公開Sourceから取得した
神社一覧を再現可能なBatchへ切り出し、既存Repositoryのduplicate detectionへ
安全に渡す共通Contractを定義する。

目的は「重複を自動確定すること」ではない。

```text
Official Prefectural Jinjacho Source
        ↓
Raw Candidate Capture
        ↓
Common Minimum Schema
        ↓
Duplicate Normalization
        ↓
Collision Candidate Lookup
        ↓
NEW_CANDIDATE / REVIEW_REQUIRED / INVALID
        ↓
Schema Gate
        ↓
READY_CANDIDATE
        ↓
STOP
```

`READY_CANDIDATE` はProduction write許可を意味しない。
次Gateへ渡せるExistence Candidateという意味だけを持つ。

# 2. Authority hierarchy

本ContractのAuthorityは以下の順で扱う。

```text
1. current Repository implementation
2. current Repository audit contracts
3. current "神社のDB" Source registry
4. historical Sheet audit labels / historical pilot artifacts
```

矛盾時は上位を優先する。

## 2.1 Repository identity authority

```text
SHRINE_IDENTITY_AUTHORITY = Shrine.id
```

name / address / source_id / source_url / place_id /
normalized_name / normalized_address / identity_candidate は
恒久identity authorityではない。

## 2.2 Duplicate/collision authority

現行Repositoryの以下を正本として再利用する。

```text
backend/temples/services/shrine_duplicate_normalize.py
  normalize_shrine_name_for_duplicate()
  normalize_shrine_address_for_duplicate()

backend/temples/services/shrine_submission.py
  find_duplicate_candidates()
```

`find_duplicate_candidates()` は **COLLISION_SIGNAL_ONLY** とする。

```text
candidate 1件
!= identity確定
!= duplicate確定
!= auto-bind許可
!= auto-update許可
```

順位1位もidentity authorityではない。

# 3. Frozen Source Universe

2026-10-08の「神社庁Source」正本で
`acquisition_scope = 全件取得可能` の15都道府県を本ContractのSource Universeとする。

```text
秋田県
山形県
新潟県
山梨県
岐阜県
三重県
滋賀県
京都府
大阪府
奈良県
岡山県
香川県
愛媛県
鹿児島県
沖縄県
```

Source URL、directory URL、verified_at、source_total_count等の
運用メタデータはGoogle Sheets「神社のDB」>「神社庁Source」を正本とする。

本ContractへURLを複製して第二正本を作らない。

## 3.1 Entry gate

Source extractionへ入れるのは、Source registryで最低限以下を満たす県だけ。

```text
acquisition_scope = 全件取得可能
access_status      = 確認済 または同等の公式確認状態
directory_url      = non-empty
verified_at        = non-empty
```

条件が崩れた県はExtractionを開始せずSource registryへ差し戻す。

# 4. Source Candidate boundary

この工程で取得するのは **Existence Candidate** だけ。

## 4.1 Required raw fields

各Candidateで必須:

```text
name
address
source_url
prefecture
source_type
source_verified_at
```

本trackの `source_type` は:

```text
prefectural_jinjacho_official
```

## 4.2 Optional raw fields

Sourceに存在する場合のみ取得:

```text
kana
phone
source_id
detail_url
```

欠損を推測補完しない。

## 4.3 Explicitly excluded from this stage

```text
deity
history
festival
goshintoku / goriyaku
history_theme
Knowledge Fact
latitude
longitude
Recommendation tags
AI-derived meaning
```

存在ImportとKnowledge / Coordinateを分離する。

# 5. Source raw preservation

Source原文は変更しない。

```text
raw_name
raw_address
raw_source_url
raw_source_id
```

をEvidenceとして保持し、比較用値は別fieldへ生成する。

禁止:

```text
raw_nameを書き換えて保存
raw_addressを書き換えて保存
旧字体/異体字を推測変換
通称を正式名へ自動変換
住所を推測補完
Sourceに無い都道府県・番地を推測補完
```

# 6. Deterministic extraction

各Sourceは「何件取るか」だけではなく、
**どのレコードをどういう順序で取ったか**を再現できる必要がある。

各Batchで最低限以下を記録する。

```text
prefecture
batch_id
selection_rule
source_position
source_verified_at
captured_at
source_url
```

## 6.1 selection_rule

selection_ruleはSourceごとに曖昧でない記述を必須とする。

例:

```text
検索条件なし / Source既定表示順 / page 1-10
地域一覧を公式表示順で走査 / region 01-05
全件一覧の表示順 / ordinal 1-100
```

「有名な神社を選ぶ」「代表的な神社を選ぶ」等の恣意的選択は禁止。

## 6.2 source_position

Sourceの形に応じて再取得可能なlocatorを残す。

例:

```text
page001-row001
region03-row018
ordinal000123
source_id:ABC123
```

source_positionはShrine identityではない。

# 7. Batch contract

1県全件を1つの巨大Batchとして扱うことを禁止する。

```text
PREFECTURE
  ├─ Batch N
  ├─ Batch N+1
  └─ ...
```

ただし、**Batch sizeは本Contractでは確定しない。**

```text
BATCH_SIZE = MOTHER_SHIP_DECISION_REQUIRED
```

実装前にMother Shipで固定する。

Batch boundaryを変更した場合は、同じbatch_idを再利用しない。

# 8. Normalization contract

比較用正規化はRepository正本をそのまま使用する。

```python
normalize_shrine_name_for_duplicate(raw_name)
normalize_shrine_address_for_duplicate(raw_address)
```

生成:

```text
normalized_name
normalized_address
```

独自normalizerをCandidate Extraction専用に作らない。

## 8.1 Prohibited normalization

現行正本以上の意味変換を追加しない。

特に禁止:

```text
「神社」「宮」「大社」等の語尾除去
旧字体 -> 新字体の自動変換
通称 -> 正式名変換
地名・都道府県名の削除
同音異字統合
LLMによる名称同一視
```

# 9. Collision lookup contract

各Candidateに対し、read-onlyで:

```python
find_duplicate_candidates(
    name=raw_name,
    address=raw_address,
    limit=100,
)
```

を実行する。

`limit=100` はidentity判定を強くするためではなく、
既定limit=3による監査情報の過度な切り捨てを避けるためのExtraction Contract上の値。

## 9.1 Candidate count interpretation

```text
returned_count = 0
  -> NEW_CANDIDATE

returned_count = 1..99
  -> REVIEW_REQUIRED

returned_count = 100
  -> REVIEW_REQUIRED
  -> POSSIBLY_TRUNCATED = YES
```

100件返却は「100件が全候補」だと断定しない。

## 9.2 Critical boundary

```text
NEW_CANDIDATE
!= definitely new shrine

REVIEW_REQUIRED
!= duplicate shrine
```

両方ともCandidate workflow上の状態であり、identity事実ではない。

# 10. Historical identity-rule labels

Google Sheetsのhistorical auditには:

```text
ID-01
ID-02
...
ID-09
EXACT
CANDIDATE
SOURCE_MATCH
AMBIGUOUS
```

等の詳細分類がある。

これらは監査履歴として保持するが、
現行Repositoryに同じrule engineが存在しないため、
全国Candidate Extraction実装のcanonical code contractにはしない。

```text
IDENTITY_RULE_ID_AUTHORITY = NON_CANONICAL_AUDIT_DERIVED
```

実装がSheetの `ID-02` 等を分岐条件として参照することを禁止する。

# 11. Common Minimum Schema Gate

`NEW_CANDIDATE` のみCommon Minimum Schema Gateへ進める。

必須:

```text
name
address
source_url
prefecture
source_type
source_verified_at
normalized_name
normalized_address
```

## 11.1 Missing field

nameまたはaddressを含む必須field欠損:

```text
classification = INVALID
planned_action = STOP_SOURCE_REVIEW
```

## 11.2 Prefecture mismatch

Source registryの県とaddressから判断される県が不一致:

```text
classification = REVIEW_REQUIRED
planned_action = STOP_PREFECTURE_REVIEW
```

自動で県を修正しない。

## 11.3 Schema PASS

```text
collision lookup returned_count = 0
AND
required fields PASS
AND
prefecture mismatchなし
```

の場合:

```text
classification = READY_CANDIDATE
planned_action = HANDOFF_NEXT_GATE
```

# 12. identity_candidate audit key

Pilotで使用した:

```text
identity_candidate = normalized_name + "|" + normalized_address
```

は監査・比較用keyとして使用してよい。

ただし:

```text
identity_candidate != Shrine.id
identity_candidate != canonical identity
identity_candidate != merge key
```

同値keyの存在だけでauto-mergeしない。

# 13. Canonical output schema

全国Candidate artifactは最低限以下を持つ。

```text
prefecture
batch_id
source_position
selection_rule
captured_at

raw_name
raw_address
kana
phone

source_type
source_url
detail_url
source_id
source_verified_at

normalized_name
normalized_address
identity_candidate

duplicate_lookup_limit
returned_candidate_count
returned_candidate_ids
returned_candidate_names
returned_candidate_addresses
possibly_truncated

classification
planned_action
review_reason

schema_name
schema_address
schema_source_url
schema_prefecture
schema_source_type
schema_source_verified_at
schema_gate_result
```

空欄は空欄として残す。推測値を作らない。

# 14. Canonical classifications

全国Candidate Extractionの実行判断で使用するcanonical classificationは3つに絞る。

```text
READY_CANDIDATE
REVIEW_REQUIRED
INVALID
```

意味:

| classification | 意味 | 次 |
|---|---|---|
| READY_CANDIDATE | current collision lookupで候補0、Common Minimum Schema PASS | 次Gateへhandoff |
| REVIEW_REQUIRED | collision候補あり、県不一致、truncation等 | Human/Mother Ship reviewまでSTOP |
| INVALID | 必須Existence field不足等 | Source再取得までSTOP |

`DUPLICATE` を自動classificationとして生成しない。

# 15. Write policy

Candidate Extraction中のwrite contract:

```text
Production Shrine INSERT = 0
Production Shrine UPDATE = 0
Production Shrine DELETE = 0

AUTO_IMPORT = 0
AUTO_MERGE = 0
AUTO_BIND = 0
AUTO_CREATE = 0

Knowledge write = 0
Coordinate write = 0
Recommendation write = 0
```

Google Sheets等の監査artifactへのEvidence記録は許可するが、
Production DB変更とは分離する。

# 16. Idempotency / reproducibility

同一Source snapshot相当・同一Batch contract・同一DB snapshotに対して
2回実行した場合、最低限以下が一致すること。

```text
selected raw candidate set
source_position
normalized_name
normalized_address
returned candidate payload
classification
planned_action
schema_gate_result
```

差分がある場合:

```text
REPRODUCIBILITY = FAIL
NEXT = STOP
```

Source自体が更新された場合は同一snapshotとは扱わず、
new captureとして `captured_at` / `source_verified_at` を更新する。

# 17. Required test matrix

実装PRでは最低限以下を検証する。

```text
T1  missing name -> INVALID
T2  missing address -> INVALID
T3  prefecture mismatch -> REVIEW_REQUIRED
T4  duplicate lookup 0件 -> NEW_CANDIDATE -> Schema PASS -> READY_CANDIDATE
T5  duplicate lookup 1件 -> REVIEW_REQUIRED
T6  duplicate lookup 複数件 -> REVIEW_REQUIRED
T7  returned_count == limit -> REVIEW_REQUIRED + possibly_truncated
T8  shared listing URLだけではduplicate確定しない
T9  source_id一致だけではidentity確定しない
T10 identity_candidate一致だけではauto-mergeしない
T11 raw values are preserved
T12 same input + same DB snapshot -> deterministic output
T13 extraction run -> Production DB row count unchanged
T14 classification totals sum to total
```

# 18. Relationship to existing pipeline

本Contractは既存Geographic Expansionを置き換えない。

```text
Prefectural Jinjacho Source Registry
        ↓
THIS CONTRACT
Source Candidate Extraction
        ↓
READY_CANDIDATE
        ↓
Coordinate / Base Seed Candidate Gate
        ↓
import_shrines_seed --dry-run
        ↓
separate Production Import Gate
        ↓
Knowledge Source / Knowledge Fact workflow
```

Knowledge Fact生成は本Contract外。

# 19. Source adapter boundary

15SourceはHTML構造・pagination・地域分割・検索UIが異なるため、
Extraction実装がSource別adapterを必要とする可能性がある。

本Contractが固定するのは**adapterの内部実装ではなく出力Contract**。

すべてのadapterは同じCanonical output schemaへ変換しなければならない。

禁止:

```text
県ごとにclassificationルールを変える
県ごとにnormalizerを変える
県ごとにduplicate authorityを変える
Source固有fieldをProduction Shrineへ直接流す
```

# 20. Failure policy

Fail safeを優先する。

```text
Source unreadable
-> STOP_SOURCE

Source structure changed
-> STOP_SOURCE_DRIFT

required fields missing
-> INVALID

prefecture mismatch
-> REVIEW_REQUIRED

collision candidates >= 1
-> REVIEW_REQUIRED

lookup truncated possibility
-> REVIEW_REQUIRED

normalization / lookup nondeterministic
-> STOP_REPRODUCIBILITY

unclassified row
-> STOP_CONTRACT
```

Batch内にREVIEW/INVALIDがあってもCandidate Extraction artifact自体は最後まで生成してよい。
ただし該当行は次Gateへ送らない。

# 21. Mother Ship decisions remaining

本Contractでは以下を決定しない。

```text
M1 BATCH_SIZE
M2 FIRST_ROLLOUT_PREFECTURE
M3 PREFECTURE_ROLLOUT_ORDER
M4 READY_CANDIDATEを何件単位でCoordinate Gateへ送るか
M5 REVIEW_REQUIREDのHuman Review運用責任者
```

これらは実装開始前または各実行GateでMother Shipへ返す。

# 22. Implementation ownership

本Contract確定後のRunner実装は複数ファイル・テストを伴うためCodex主担当候補。

```text
ChatGPT
  Contract / design / review

Codex
  Source adapter / runner / tests / PR

Cursor
  local adjustment only

Mother Ship
  M1-M5 decision
```

# 23. First implementation gate

15県同時実装は禁止。

```text
Step 1  Mother ShipがBatch size / first prefectureを確定
Step 2  1県1Batchで全国版Contractを実証
Step 3  同一snapshot + DB snapshotで2回実行
Step 4  diff 0を確認
Step 5  2県目でSource adapter差異を確認
Step 6  Expansion Gateへ戻す
Step 7  15県横展開の可否を判断
```

# 24. Non-goals

- Production Shrine import
- existing Shrine update
- automatic duplicate merge
- canonical identity resolution
- PlaceRef backfill
- Coordinate決定
- Knowledge Fact生成
- goriyaku / history_theme生成
- Recommendation変更
- Runtime変更
- UI変更
- A-6 Collective Runtime activation

# 25. Final contract

```text
SOURCE_UNIVERSE = 15 PREFECTURES / FULL_ENUMERATION_AVAILABLE

RAW_SOURCE_PRESERVATION = REQUIRED
COMMON_MINIMUM_SCHEMA = REQUIRED

NORMALIZATION_AUTHORITY
= shrine_duplicate_normalize

COLLISION_LOOKUP_AUTHORITY
= shrine_submission.find_duplicate_candidates

COLLISION_LOOKUP
= COLLISION_SIGNAL_ONLY

AUTO_DUPLICATE_DECISION = PROHIBITED
AUTO_MERGE = PROHIBITED
AUTO_IMPORT = PROHIBITED
PRODUCTION_WRITE = 0

CANONICAL_CLASSIFICATIONS
= READY_CANDIDATE | REVIEW_REQUIRED | INVALID

READY_CANDIDATE
= lookup candidate 0
  + required schema PASS
  + prefecture consistency PASS

BATCH_SIZE
= MOTHER_SHIP_DECISION_REQUIRED

NEXT
= Mother Ship M1-M5
  -> single-prefecture implementation gate
```

# 26. STOP

本ContractはここでSTOPする。

Runner / adapter / Production writeはこのPRでは実装しない。
