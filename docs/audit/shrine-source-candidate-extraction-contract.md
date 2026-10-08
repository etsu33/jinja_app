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


# 27. M1 Decision Record — Batch Size

> **Recorded at: 2026-10-08**
>
> 本節は §21 の `M1 BATCH_SIZE` を確定する追記である。
> §1–§26のContract本文は履歴として書き換えない。

```text
M1_BATCH_SIZE = 100 RAW SOURCE CANDIDATES
M1_STATUS = DECIDED
```

## 27.1 Meaning

1 Batchは、同一都道府県・同一Source traversal上の**連続した最大100 raw candidates**で構成する。

```text
BATCH_SIZE_COUNTS
= READY_CANDIDATE
+ REVIEW_REQUIRED
+ INVALID
```

したがって「100 READY_CANDIDATEを集めるまで読み進める」という意味ではない。

## 27.2 Boundaries

```text
CROSS_PREFECTURE_BATCH = PROHIBITED
CROSS_SOURCE_UNIVERSE_BATCH = PROHIBITED
MAX_RAW_CANDIDATES_PER_BATCH = 100
FINAL_PARTIAL_BATCH = ALLOWED
```

県内の最終Batchが100件未満でも、その件数のまま1 Batchとして扱う。

例:

```text
source_total = 1,729

Batch 001 = source positions   1-100
Batch 002 = source positions 101-200
...
Batch 017 = source positions 1601-1700
Batch 018 = source positions 1701-1729
```

## 27.3 Source page boundary

Source側のpagination件数とBatch boundaryは同一である必要はない。

例:

```text
Source page size = 12
Batch size       = 100
```

の場合でも、決定論的なSource traversal順を維持したまま100 raw candidatesまで束ねる。

ただし各rowの `source_position` は元Source上の位置を保持する。

## 27.4 Safety rationale

100件はCandidate Extraction専用の論理Batchであり、Production write単位ではない。

既存新潟Pilotは20件でNormalization / Lookupの独立再実行を検証済み。
全国Contractでは以下が成立しているため、Existence Candidate抽出単位を100件へ拡張する。

```text
Production write = 0
AUTO_IMPORT = 0
AUTO_MERGE = 0
AUTO_BIND = 0
AUTO_CREATE = 0

REVIEW_REQUIRED rows may remain in artifact
INVALID rows may remain in artifact
only READY_CANDIDATE can be handed to the next Gate
```

20件を全国運用単位として維持すると、4,619件規模のSourceでは200を超えるBatchへ細分化され、
監査・再開位置・PR/Artifact管理の運用負荷が過大になる。

一方、200件以上を1 BatchとするとSource drift・adapter defect・reproducibility failure発生時の
再検証範囲が広くなる。

したがってM1では中間値として100件を固定する。

## 27.5 M1 does not decide

M1は以下を確定しない。

```text
M2 FIRST_ROLLOUT_PREFECTURE
M3 PREFECTURE_ROLLOUT_ORDER
M4 READY_CANDIDATE_HANDOFF_SIZE
M5 REVIEW_REQUIRED_HUMAN_REVIEW_OWNER
```

また:

```text
BATCH_SIZE = 100
!= duplicate lookup limitの意味変更
!= Production import size
!= Coordinate Audit size
!= Knowledge Batch size
```

§9の `duplicate_lookup_limit = 100` とM1の `BATCH_SIZE = 100` は
数値が同じでも独立したContractである。

# 28. Updated decision state

```text
M1 BATCH_SIZE                    = DECIDED / 100 RAW CANDIDATES
M2 FIRST_ROLLOUT_PREFECTURE      = PENDING
M3 PREFECTURE_ROLLOUT_ORDER      = PENDING
M4 READY_CANDIDATE_HANDOFF_SIZE  = PENDING
M5 REVIEW_REQUIRED_REVIEW_OWNER  = PENDING

NEXT = M2 FIRST_ROLLOUT_PREFECTURE
```

本追記でもRunner / adapter / Production writeは実装しない。


# 29. M2 Decision Record — First Rollout Prefecture

> **Recorded at: 2026-10-08**
>
> 本節は §21 の `M2 FIRST_ROLLOUT_PREFECTURE` を確定する追記である。
> M1は §27で `100 RAW SOURCE CANDIDATES` と確定済み。

```text
M2_FIRST_ROLLOUT_PREFECTURE = NIIGATA
M2_FIRST_ROLLOUT_PREFECTURE_JA = 新潟県
M2_STATUS = DECIDED
```

## 29.1 Selection rationale

新潟県を初回Rolloutに採用する理由は、全国版Candidate Extraction Contractを
最小の新規不確定要因で実証しながら、十分な失敗ケースも観測できるため。

### A. Full-enumeration Source is already established

神社庁Source正本では新潟県は:

```text
acquisition_scope = 全件取得可能
source_total_count = 4,619
registered_count = 11
directory_status = 全件一覧・検索あり
```

で管理されている。

### B. Source traversal has prior operational evidence

既存Pilotは新潟県をMother Shipが選定し、Source既定表示順から固定20件を取得している。

```text
PILOT_PREFECTURE = NIIGATA
pilot_input_count = 20
Production write = 0
```

この20件についてInput fixednessは20/20一致でPASSしている。

### C. Normalization is already reproducible on the same Source shape

現行Repositoryの:

```text
normalize_shrine_name_for_duplicate()
normalize_shrine_address_for_duplicate()
```

を独立再実行した結果、20 records × 2 fields = 40/40一致、DIFF 0が記録されている。

### D. Duplicate lookup already produced both zero-hit and collision-signal cases

同じ20件で `find_duplicate_candidates(..., limit=100)` を独立実行した結果:

```text
candidate_count = 0 : 15 records
candidate_count = 1 : 5 records
candidate_count > 1 : 0 records
DIFF = 0
```

よって初回100件Batchで:

```text
READY_CANDIDATE path
REVIEW_REQUIRED path
```

の両方が発生する可能性を既存実績から期待できる。

これは「全件がNEWで簡単にPASSするだけ」の県より、Contract検証に適している。

### E. Existing registered Shrine rows exist in the same prefecture

新潟県はKAMI MUSUBI側に11社登録済み。

```text
registered_count = 11
```

したがって、Source Candidateと既存Shrine DBの衝突検知を
実データ上で確認できる条件がすでにある。

## 29.2 Why not use the smallest Source first

沖縄県はSource total 10件で全件列挙可能だが、
M1で固定した100 raw candidate Batchの実証には小さすぎる。

```text
Okinawa source_total = 10
M1 batch_size = 100
```

最終partial Batchの動作確認には利用できるが、
初回Rolloutで必要な:

```text
pagination / traversal
100-record batch boundary
collision lookup volume
mixed classification
reproducibility at M1 scale
```

を十分に検証しにくい。

M2は「最も簡単な県」ではなく、
**既存Evidenceが最も多く、全国RunnerのContractを100件規模で検証できる県**
として新潟県を選定する。

## 29.3 First rollout boundary

M2は県だけを固定する。

```text
FIRST_ROLLOUT_PREFECTURE = 新潟県
FIRST_BATCH_MAX_RAW_CANDIDATES = 100
```

実行時はSource registry Entry Gateを再確認する。

```text
acquisition_scope = 全件取得可能
access_status = valid
directory_url = non-empty
verified_at = non-empty
```

Source unreadable / structure driftを検出した場合:

```text
M2 decision remains NIIGATA
execution = STOP_SOURCE / STOP_SOURCE_DRIFT
```

別県へ自動fallbackしない。

## 29.4 M2 does not decide

M2は以下を確定しない。

```text
M3 PREFECTURE_ROLLOUT_ORDER
M4 READY_CANDIDATE_HANDOFF_SIZE
M5 REVIEW_REQUIRED_HUMAN_REVIEW_OWNER
```

またM2は:

```text
新潟県全4,619件の一括実行
Production Import
Coordinate write
Knowledge generation
Recommendation change
```

を許可しない。

初回実証範囲はM1に従い最大100 raw Source Candidates。

# 30. Updated decision state

```text
M1 BATCH_SIZE                    = DECIDED / 100 RAW CANDIDATES
M2 FIRST_ROLLOUT_PREFECTURE      = DECIDED / NIIGATA
M3 PREFECTURE_ROLLOUT_ORDER      = PENDING
M4 READY_CANDIDATE_HANDOFF_SIZE  = PENDING
M5 REVIEW_REQUIRED_REVIEW_OWNER  = PENDING

FIRST_IMPLEMENTATION_GATE
= NIIGATA / MAX 100 RAW SOURCE CANDIDATES

NEXT = M3 PREFECTURE_ROLLOUT_ORDER
```

本追記でもRunner / adapter / Production writeは実装しない。


# 31. M3 Decision Record — Prefecture Rollout Order

> **Recorded at: 2026-10-08**
>
> M3は商品優先順位ではなく、Source adapter / batch / reproducibilityを
> 安全に広げるための**技術Rollout順**として固定する。

```text
M3_PREFECTURE_ROLLOUT_ORDER =

01 新潟県
02 沖縄県
03 大阪府
04 香川県
05 岐阜県
06 鹿児島県
07 秋田県
08 愛媛県
09 山梨県
10 滋賀県
11 岡山県
12 山形県
13 三重県
14 奈良県
15 京都府

M3_STATUS = DECIDED
```

## 31.1 Ordering policy

Rollout順は以下の優先軸で決める。

```text
1. 既存実証量
2. Source構造差の早期検証
3. 小さいSourceでpartial Batchを検証
4. exact source_total_countがあるSourceを先行
5. 地域分割・概数・外部詳細導線など構造が複雑なSourceを後段
```

順番は神社の重要度・人気・地域優先度を意味しない。

## 31.2 First three prefectures are deliberate contract tests

### 01 新潟県

M2で確定済み。
既存20件Pilot + 4,619件Source + 既存DB11社により、
100 raw candidate Batch / collision signal / reproducibilityを検証する。

### 02 沖縄県

```text
source_total_count = 10
directory_status = 全件一覧あり
```

新潟とは異なる小規模static-list型Sourceで、
M1の `FINAL_PARTIAL_BATCH = ALLOWED` を実データで検証する。

### 03 大阪府

行政区別一覧型。
新潟のpagination/search型、沖縄のsmall static list型に続き、
region-partition型Source adapterを早期に検証する。

## 31.3 Middle rollout group

以下は全件取得可能かつ、比較的明確な一覧/検索Sourceを持つため、
共通Runner / adapter contractが3県で成立した後に順次展開する。

```text
04 香川県
05 岐阜県
06 鹿児島県
07 秋田県
08 愛媛県
09 山梨県
10 滋賀県
11 岡山県
12 山形県
```

この順番はSource品質ランキングではない。
同一Contractで段階的に規模を上げるための運用順である。

## 31.4 Structure-heavy group

以下は地域別列挙・別導線・概数等を含み、
Source traversalのadapter差が比較的大きいため後段に置く。

```text
13 三重県
14 奈良県
15 京都府
```

京都府は21支部・約1,570社という公開構造を持つが、
source_total_countをexactとして固定していないため最後とする。

## 31.5 Rollout gate

次県へ進むには、その県のfirst Batchで最低限:

```text
Source Entry Gate PASS
Canonical output schema PASS
Production write = 0
classification漏れ = 0
reproducibility DIFF = 0
```

を満たす。

失敗した場合:

```text
AUTO_SKIP_TO_NEXT_PREFECTURE = PROHIBITED
```

Source修正 / adapter修正 / Contract再確認を行い、
Mother Ship判断なしに順番を飛ばさない。

# 32. M4 Decision Record — READY_CANDIDATE Handoff Size

```text
M4_READY_CANDIDATE_HANDOFF_SIZE = MAX 5
M4_STATUS = DECIDED
```

## 32.1 Meaning

Candidate Extractionで `READY_CANDIDATE` になった行だけを、
同一Extraction snapshot内の `source_position` 順で最大5件ずつ
Coordinate / Base Seed Candidate Gateへhandoffする。

```text
HANDOFF_SIZE = 1..5 READY_CANDIDATES
MAX = 5
FINAL_PARTIAL_HANDOFF = ALLOWED
```

`REVIEW_REQUIRED` / `INVALID` を5件に含めない。

## 32.2 Why 5

既存Wave0 Data Build Contractは:

```text
Data Build standard unit = 5 shrines / Batch
MAX = 5
```

として実運用されている。

この単位は:

- Source / Position Human Review量を制限
- 1社のidentity/position conflictを局所化
- Production差分を小さく保つ
- rollback / incident isolationを容易にする

という既存理由を持つ。

新しい20件・10件等の並行単位を作らず、
READY handoffも既存5社単位へ合わせる。

## 32.3 Boundary

```text
M1 Extraction Batch = max 100 RAW candidates
M4 Handoff          = max 5 READY candidates
```

は別Contract。

100 raw candidatesから60 READYが出た場合、例として:

```text
Handoff 01 = READY source_position順 1-5
Handoff 02 = 次の5 READY
...
Handoff 12 = 最後の5 READY
```

途中のREVIEW / INVALIDを飛ばしてREADYだけを順序保持して束ねる。

ただしhandoff membershipはExtraction snapshotごとにfreezeする。
後日REVIEWが解決してREADYへ変わっても、既存handoffへ差し込んで
過去のmember setを変更しない。新しいhandoffとして扱う。

## 32.4 Cross-boundary policy

```text
CROSS_PREFECTURE_HANDOFF = PROHIBITED
CROSS_EXTRACTION_SNAPSHOT_HANDOFF = PROHIBITED
```

同じ県でも別Extraction snapshotのREADYを混ぜない。

# 33. M5 Decision Record — REVIEW_REQUIRED Human Review Owner

```text
M5_REVIEW_REQUIRED_HUMAN_REVIEW_OWNER = MOTHER_SHIP
M5_STATUS = DECIDED
```

## 33.1 Responsibility

`REVIEW_REQUIRED` の最終identity / Source判断はMother Shipが行う。

```text
ChatGPT
= evidence整理 / conflict説明 / review観点提示

Codex
= repo lookup / deterministic artifact生成 / tests / PR

Mother Ship
= final Human Review decision

Cursor
= local adjustment only
```

Codex / Runner / ChatGPTが候補1件を理由に同一神社と自動確定しない。

## 33.2 REVIEW_REQUIRED does not auto-resolve

以下はいずれもMother Ship確認前に自動解除しない。

```text
collision candidate >= 1
prefecture mismatch
possibly_truncated
Source ambiguity
same-name / different-address
same-address / different-name
```

```text
AUTO_RECLASSIFY_TO_READY = PROHIBITED
AUTO_RECLASSIFY_TO_DUPLICATE = PROHIBITED
AUTO_MERGE = PROHIBITED
```

## 33.3 Human Review evidence packet

Mother Shipへ最低限以下を提示する。

```text
raw_name
raw_address
prefecture
source_url
source_position

normalized_name
normalized_address

returned_candidate_count
returned_candidate_ids
returned_candidate_names
returned_candidate_addresses

review_reason
source_verified_at
batch_id
```

必要なEvidenceが欠ける場合は判定せずREVIEWを維持する。

## 33.4 Scope boundary

M5はCandidate Extraction段階のidentity / Source Review ownerを決める。

以下の別GateのHuman Review責任を上書きしない。

```text
Position / Navigation Anchor adjudication
Knowledge Fact review
Model Risk review
Recommendation semantic review
Production Import execution
```

# 34. M1-M5 Final Decision State

```text
M1 BATCH_SIZE
= DECIDED / 100 RAW SOURCE CANDIDATES

M2 FIRST_ROLLOUT_PREFECTURE
= DECIDED / NIIGATA

M3 PREFECTURE_ROLLOUT_ORDER
= DECIDED / 15 PREFECTURES

M4 READY_CANDIDATE_HANDOFF_SIZE
= DECIDED / MAX 5

M5 REVIEW_REQUIRED_HUMAN_REVIEW_OWNER
= DECIDED / MOTHER_SHIP
```

```text
MOTHER_SHIP_DECISIONS_M1_M5 = CLOSED
```

# 35. Next implementation gate

M1-M5がすべて確定したため、次工程は実装Gateへ移る。

```text
FIRST IMPLEMENTATION
= NIIGATA
= Source positions first 100 under deterministic traversal
= Production write 0
= Runner / adapter / tests
= reproducibility run1/run2
= READY handoff max 5
= REVIEW_REQUIRED -> Mother Ship
```

担当:

```text
Codex = primary implementation owner
ChatGPT = contract/review
Mother Ship = REVIEW_REQUIRED adjudication
```

15県同時実装は禁止を維持する。
