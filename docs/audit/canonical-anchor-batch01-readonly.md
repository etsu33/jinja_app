# Canonical Shrine Anchor — PHASE_2 Batch 01 Read-only Audit

## Status

- Status: IN_PROGRESS_STOPPED_ON_CONTRACT_GAP
- Recorded at: 2026-09-24
- Parent procedure: docs/knowledge/canonical-anchor-adjudication-procedure.md
- Target batch: 春日大社 / 宇佐神宮 / 日光東照宮
- Canonical DB write: NONE
- Production write: NONE
- Seed write: NONE
- Runtime cutover: NONE
- Compass / Map / distance / route behavior change: NONE

本書はPHASE_2 Batch 01のread-only調査開始記録である。

今回の作業は、STEP 0のrepository-side identity freezeと、PASS A〜Cを中心とする
Evidence取得・semantic owner・component-set判定を実施した。

外部Sourceは2026-09-24時点で公開取得可能な公式・公的資料を再確認した。

Productionへのlive read-only SQLは本作業環境では実行していない。
そのためF-8 displacementに必要な「実行時点のcurrent Navigation Anchor」の最終確認は
後続のlive read-only snapshotまで保留する。

---

## 1. Batch Identity Freeze

repository上のcanonical Shrine identityを次で固定する。

| Shrine | Shrine.id | official / repository address | repository-side Navigation state |
| --- | ---: | --- | --- |
| 春日大社 | 5 | 奈良県奈良市春日野町160 | temples.0111 adopted 34.6812901, 135.8482531 |
| 宇佐神宮 | 8 | 大分県宇佐市南宇佐2859 | temples.0113 adopted 33.52344557, 131.37716659 |
| 日光東照宮 | 9 | 栃木県日光市山内2301 | no dedicated Navigation adoption migration found after prior audit; live Production recheck required before F-8 |

Identity evidence in repository includes:

- 春日大社: backend/temples/migrations/0111_adopt_kasuga_taisha_position.py
- 宇佐神宮: backend/temples/migrations/0113_adopt_usa_jingu_position.py
- 日光東照宮: docs/audit/position-audit-v2/legacy-position-provenance-batch01.md and current Shrine datasets

このidentity freezeはCanonical coordinateの採用ではない。

Navigation coordinate equality / proximityはCanonical adjudicationのEvidenceとして使用しない。

---

## 2. PASS A — Evidence Acquisition

### 2.1 春日大社

#### SEMANTIC Source S-K1

Owner: 春日大社

Title: 御本殿

URL:
https://www.kasugataisha.or.jp/guidance/keidai-map3/modal-01/

Supported claim:

- 御本殿は第一殿・第二殿・第三殿・第四殿を明示する
- 各殿にそれぞれ御祭神を明示する
- 四所神殿の創建を説明する

Evidence strength:
E1_AUTHORITATIVE

#### SEMANTIC Source S-K2

Owner: 文化庁

Title: 春日大社本社 本殿（第一殿〜第四殿）

Example URLs:

https://kunishitei.bunka.go.jp/heritage/detail/102/2533
https://kunishitei.bunka.go.jp/heritage/detail/102/2534
https://kunishitei.bunka.go.jp/heritage/detail/102/2535

Supported claim:

- 本殿は第一殿から第四殿までの四棟で構成される
- 各棟は国宝の本殿として個別登録される
- 文化庁解説は「第一殿より第四殿に至る四棟」と明示する

Evidence strength:
E1_AUTHORITATIVE

#### COORDINATE lead K-C1

Source:
OpenStreetMap-derived object record exposed via Mapcarta

First Hall:
https://mapcarta.com/W1134481290

Observed lead:
34.68158, 135.84854

Third Hall:
https://mapcarta.com/es/W1134481289

Observed lead:
34.68157, 135.84844

Fourth Hall:
https://mapcarta.com/es/W1134481288

Observed lead:
34.68157, 135.84839

Evidence role:
COORDINATE candidate / corroboration

Evidence strength:
E4_CORROBORATION

Important:
Second Hallのobject-level numeric coordinateは今回のread-only passでは再現可能なSourceからまだ取得できていない。

したがってF-5をcompleteとして記録しない。

---

### 2.2 宇佐神宮

#### SEMANTIC Source S-U1

Owner: 宇佐神宮

Title: 由緒

URL:
https://www.usajinguu.com/lineage/

Supported claim:

- 一之御殿・二之御殿・三之御殿をそれぞれ御祭神と対応させる
- 三殿を宇佐神宮の本殿構造として説明する
- 三殿一徳の神威を説明する

Evidence strength:
E1_AUTHORITATIVE

#### SEMANTIC Source S-U2

Owner: 宇佐市

Title: 上宮

URL:
https://www.city.usa.oita.jp/tourist/touristspot/touristspot2/touristspot3/usachiku/syuyumap/kami/12884.html

Supported claim:

- 上宮は宇佐神宮の主祭神三柱を3つの御殿に祀る
- 一之御殿・二之御殿・三之御殿の成立を個別に説明する
- 上宮「本殿」は一之御殿・二之御殿・三之御殿である
- 各御殿へそれぞれ参拝することを説明する

Evidence strength:
E1_AUTHORITATIVE

#### SEMANTIC Source S-U3

Owner: 文化庁

Title: 宇佐神宮本殿（第一殿・第二殿・第三殿）

URLs:

https://kunishitei.bunka.go.jp/heritage/detail/102/3599
https://kunishitei.bunka.go.jp/bsys/maindetails/102/3600
https://kunishitei.bunka.go.jp/heritage/detail/102/3601

Supported claim:

- 本殿は第一殿より第三殿に至る三社殿で構成される
- 三社殿は東西に並ぶ
- 各殿が国宝として個別の建造物recordを持つ

Evidence strength:
E1_AUTHORITATIVE

#### COORDINATE lead U-C1

Owner:
奈良文化財研究所

Title:
98032356-宇佐神宮本殿

URL:
https://heritagemap.nabunken.go.jp/statistic/98032356-%E5%AE%87%E4%BD%90%E7%A5%9E%E5%AE%AE%E6%9C%AC%E6%AE%BF.html

Subject:
宇佐神宮本殿 第三殿

Observed WGS84 coordinate:
33.52349, 131.3773

Source lineage:
文化庁 国指定文化財等データベース 2021-01-29 snapshot

Evidence strength:
E3_MEASURED / public cultural-property georeference lead

Important:
第一殿・第二殿について同等に再現可能なnumeric subject-matched coordinateは今回passで未取得。

したがってF-5をcompleteとして記録しない。

---

### 2.3 日光東照宮

#### SEMANTIC Source S-N1

Owner: 日光市

Title: 建造物一覧-東照宮1

URL:
https://www.city.nikko.lg.jp/kanko_bunka_sports/bunkazai/3/2/7/6354.html

Supported claim:

- 本殿は東照大権現（徳川家康公の神霊）を祀る神殿
- 石の間は本殿と拝殿を連結する建物
- 拝殿は神霊を礼拝する建物
- 三者の内部役割を区別する

Evidence strength:
E1_AUTHORITATIVE

#### SEMANTIC / STRUCTURAL Source S-N2

Owner: 文化庁

Title: 東照宮 本殿、石の間及び拝殿

URL:
https://kunishitei.bunka.go.jp/heritage/detail/102/269

Supported claim:

- 「本殿、石の間及び拝殿」を員数1棟として登録する
- 本殿・石の間・拝殿からなる権現造形式を明示する
- principal connected unitを一つの文化財objectとして追跡可能

Evidence strength:
E1_AUTHORITATIVE

#### COORDINATE Source N-C1

Owner:
奈良文化財研究所

Title:
98002610-東照宮_本殿、石の間及び拝殿

URL:
https://heritagemap.nabunken.go.jp/statistic/98002610-%E6%9D%B1%E7%85%A7%E5%AE%AE_%E6%9C%AC%E6%AE%BF%E3%80%81%E7%9F%B3%E3%81%AE%E9%96%93%E5%8F%8A%E3%81%B3%E6%8B%9D%E6%AE%BF.html

Observed WGS84 coordinate:
36.75808, 139.5987

Subject:
東照宮 本殿、石の間及び拝殿

Source lineage:
文化庁 国指定文化財等データベース 2021-01-29 snapshot

Evidence strength:
E3_MEASURED / public cultural-property georeference

---

## 3. PASS B — Semantic Owner / Classification

### 3.1 春日大社

Preliminary semantic owner:

御本殿 第一殿・第二殿・第三殿・第四殿のfull principal ritual complex

subject_type:
MULTI_PRINCIPAL_UNIT

point_method:
UNWEIGHTED_COMPONENT_MEAN

Candidate classification:

| component | classification | basis |
| --- | --- | --- |
| 第一殿 | INCLUDED | 春日大社公式 + 文化庁 |
| 第二殿 | INCLUDED | 春日大社公式 + 文化庁 |
| 第三殿 | INCLUDED | 春日大社公式 + 文化庁 |
| 第四殿 | INCLUDED | 春日大社公式 + 文化庁 |

No single hall priority is introduced.

### 3.2 宇佐神宮

Existing A-4 Mother Ship audit already resolved the semantic owner at complex level:

PRIMARY_RITUAL_COMPLEX = 上宮

Current sources S-U1〜S-U3 independently support the three principal Honden structure.

Preliminary subject:

上宮 本殿 一之御殿・二之御殿・三之御殿

subject_type:
MULTI_PRINCIPAL_UNIT

point_method:
UNWEIGHTED_COMPONENT_MEAN

Candidate classification:

| component | classification | basis |
| --- | --- | --- |
| 一之御殿 | INCLUDED | 宇佐神宮公式 + 宇佐市 + 文化庁 |
| 二之御殿 | INCLUDED | 宇佐神宮公式 + 宇佐市 + 文化庁 |
| 三之御殿 | INCLUDED | 宇佐神宮公式 + 宇佐市 + 文化庁 |

下宮をこのcomponent setへ混入しない。

「下宮参らにゃ片参り」は参拝完全性のEvidenceであり、
Canonical ownerのco-principal component equalityへ自動変換しない。

### 3.3 日光東照宮

Existing A-6 audit treated the connected 御本社 object as a reproducibly traceable
principal connected unit.

Current Source S-N1 distinguishes internal roles while Source S-N2 registers the
connected object as one building.

Preliminary subject:

東照宮 御本社 — 本殿、石の間及び拝殿のconnected principal unit

subject_type:
SINGLE_PRINCIPAL_UNIT

point_method:
DIRECT_POINT

Important semantic note:

- 本殿 = enshrinement building
- 石の間 = connector
- 拝殿 = worship building

The connected unit is not interpreted as three co-principal enshrinement components.
Therefore UNWEIGHTED_COMPONENT_MEAN is not used.

This exact scope remains a Human QA item before CONFIRMED.

---

## 4. PASS C — Component Set Completeness

### 春日大社

F-1:
SUPPORTED

F-2:
SUPPORTED for four halls

F-3:
all four = INCLUDED

F-4:
COMPLETE

Reason:
official Shrine material and Cultural Affairs material explicitly identify the four-hall Main Sanctuary set.

Coordinate acquisition state:
INCOMPLETE at F-5 acquisition because 第二殿 numeric subject-matched coordinate is not yet reproduced in this pass.

No mean calculated.

### 宇佐神宮

F-1:
SUPPORTED, carrying forward A-4 semantic-owner decision = 上宮

F-2:
SUPPORTED for 一之御殿 / 二之御殿 / 三之御殿

F-3:
all three = INCLUDED

F-4:
COMPLETE

Reason:
Shrine official / Usa City / Cultural Affairs sources converge on the three-Honden set.

Coordinate acquisition state:
INCOMPLETE at F-5 acquisition because only 第三殿 numeric coordinate has been reproduced in this pass.

No mean calculated.

### 日光東照宮

F-1:
PRELIMINARY_SUPPORTED

F-2/F-3:
connected principal unit can be treated as one SINGLE_PRINCIPAL_UNIT candidate;
internal 本殿 / 石の間 / 拝殿 roles remain documented and are not flattened into
co-principal equality.

F-4:
PRELIMINARY_COMPLETE pending Human QA on subject scope

F-5:
subject-matched coordinate available for the connected unit:
36.75808, 139.5987

F-6:
provenance available from奈良文化財研究所 / 文化庁 lineage

F-7/F-8:
NOT WRITTEN because a contract gap was detected before finalization.

---

## 5. Contract Gap Found During Batch Execution

### 5.1 The gap

The ACTIVE PHASE_2 procedure states:

DIRECT_POINT:
subject-matched coordinate is the representative point.

However the inherited A-5B Evidence Packet contract defines:

F-7 calculated_mean

as:

- required when F-4 = COMPLETE
- shape = latitude / longitude / component_count / calculation_note
- definition = unweighted arithmetic mean of INCLUDED components

F-8 displacement is permitted only when F-7 is present.

This works naturally for:

MULTI_PRINCIPAL_UNIT
+ UNWEIGHTED_COMPONENT_MEAN

but it does not explicitly define where a:

SINGLE_PRINCIPAL_UNIT
+ DIRECT_POINT

final representative coordinate is recorded in the packet.

### 5.2 Why this cannot be silently solved

The following silent reinterpretations would each change the packet contract:

Option A:
store DIRECT_POINT inside F-7 even though F-7 is defined as calculated_mean.

Option B:
treat one DIRECT_POINT as a one-component arithmetic mean.

Option C:
skip F-7 and allow F-8 to use F-5 directly.

Option D:
rename/generalize F-7 to representative_point.

No current authoritative document selects one of these.

Therefore Batch 01 does not invent a mapping.

### 5.3 Gate result

CONTRACT_GAP:
DIRECT_POINT_PACKET_FINAL_POINT_REPRESENTATION

MOTHER_SHIP_DECISION_REQUIRED = YES

No Canonical coordinate is adopted.

No F-7/F-8 is finalized for 日光東照宮.

---

## 6. Batch State at STOP

| Shrine | subject_type | point_method | F-4 | Current stop | Current adjudication |
| --- | --- | --- | --- | --- | --- |
| 春日大社 | MULTI_PRINCIPAL_UNIT | UNWEIGHTED_COMPONENT_MEAN | COMPLETE | F-5 coordinate acquisition incomplete | NOT_ADJUDICATED |
| 宇佐神宮 | MULTI_PRINCIPAL_UNIT | UNWEIGHTED_COMPONENT_MEAN | COMPLETE | F-5 coordinate acquisition incomplete | NOT_ADJUDICATED |
| 日光東照宮 | SINGLE_PRINCIPAL_UNIT | DIRECT_POINT | PRELIMINARY_COMPLETE | F-7 packet representation contract gap | NOT_ADJUDICATED |

No shrine is classified HOLD_POSITION_REVIEW in this pass.

Reasons:

- 春日大社 / 宇佐神宮: coordinate acquisition work remains incomplete.
- 日光東照宮: packet contract requires Mother Ship clarification before finalization.

These are not accepted-source conflicts.

---

## 7. Required Next Decision

Before Batch 01 can finalize a DIRECT_POINT shrine packet, Mother Ship must define how
the A-5B packet represents the final DIRECT_POINT coordinate.

The decision must preserve:

- subject_type / point_method distinction
- no hidden mean semantics
- F-8 displacement traceability
- backward readability of existing A-5B packet fields
- no DB schema implication unless separately approved

This audit does not select the solution.

---

## 8. Required Statements

PHASE_2_BATCH_01_STARTED = YES

READ_ONLY = YES

IDENTITY_TARGETS =
  春日大社 Shrine.id=5
  宇佐神宮 Shrine.id=8
  日光東照宮 Shrine.id=9

CANONICAL_DB_WRITE = NONE

PRODUCTION_WRITE = NONE

SEED_WRITE = NONE

CANONICAL_BACKFILL = NOT_STARTED

RUNTIME_CUTOVER = NOT_PERFORMED

COMPASS_CHANGE = NONE

BATCH_01_CONFIRMED_COUNT = 0

BATCH_01_HOLD_COUNT = 0

BATCH_01_NOT_ADJUDICATED_COUNT = 3

CONTRACT_GAP =
DIRECT_POINT_PACKET_FINAL_POINT_REPRESENTATION

## 9. STOP

Batch 01 remains read-only and stops here.

Do not:

- invent F-7 semantics for DIRECT_POINT
- calculate partial MULTI means
- copy Navigation coordinates
- create Canonical Anchor rows
- perform Production writes
- begin PHASE_3


---

## 10. Follow-up — Batch 01 Resumed After F-7 Decision

### Status

- Resumed at: 2026-09-24
- Resume base: develop `644675a8478c2607a211fa5803bb3f4cc461a992`
- F-7 Mother Ship decision: MERGED via PR #2980
- Active F-7: `representative_point`
- Canonical DB write: NONE
- Production write: NONE
- Seed write: NONE
- Runtime cutover: NONE

PR #2980 resolved the previous
`DIRECT_POINT_PACKET_FINAL_POINT_REPRESENTATION` contract gap.

Active rule:

```text
DIRECT_POINT
-> F-7 representative_point is the exact verified subject-matched F-5 coordinate

UNWEIGHTED_COMPONENT_MEAN
-> F-7 representative_point is the deterministic mean of exactly all INCLUDED F-5 coordinates

F-8.to_coordinate
-> F-7 representative_point
```

Batch 01 was resumed under that rule.

---

## 11. Production Navigation Read-only Access Gate

### 11.1 Render workspace confirmation

The explicitly authorized Production workspace was confirmed:

```text
workspace_name = エツ's workspace
workspace_id   = tea-d18eq9qdbo4c739j9sdg
```

Production backend:

```text
service_name = jinja-backend
service_id   = srv-d4sk1uscjiac739ko5r0
branch       = develop
region       = singapore
```

### 11.2 Database provider

The user confirmed that the Production database is hosted in Supabase.

Render reports no Render-managed Postgres instance in the authorized workspace,
which is consistent with Render hosting the backend while `DATABASE_URL` points to
an external Supabase Postgres database.

### 11.3 Live SELECT result

Supabase is connected in the ChatGPT product for this request, but the current
execution surface did not expose a callable Supabase SQL action.

The sanctioned local credential bridge also is not available in this container, and
the public Production API could not be resolved from this execution environment.

Therefore the requested point-in-time live SELECT was **not fabricated from historical values**.

```text
PRODUCTION_NAVIGATION_LIVE_SELECT
= NOT_EXECUTED

REASON
= SUPABASE_SQL_ACTION_NOT_EXPOSED_IN_CURRENT_EXECUTION_SURFACE

PRODUCTION_WRITE
= NONE
```

### 11.4 Previously audited / migration-backed expectations

These are retained only as expected state, not as the requested live snapshot.

```text
春日大社 Shrine.id=5
expected after temples.0111
= 34.6812901, 135.8482531

宇佐神宮 Shrine.id=8
expected after temples.0113
= 33.52344557, 131.37716659

日光東照宮 Shrine.id=9
last audited stored Production coordinate
= 36.7579, 139.5986
```

Production was later verified through `temples.0114`, proving the linear migration
lineage through 0111 and 0113 was applied. This does not replace a fresh live SELECT.

---

## 12. 春日大社 — Coordinate Follow-up

### 12.1 Semantic set

The authoritative four-Honden set remains:

```text
第一殿 INCLUDED
第二殿 INCLUDED
第三殿 INCLUDED
第四殿 INCLUDED

subject_type = MULTI_PRINCIPAL_UNIT
point_method = UNWEIGHTED_COMPONENT_MEAN
F-4 = COMPLETE
```

Semantic authority remains the Shrine official material and Cultural Affairs records.

### 12.2 Subject-labelled georeference leads

Current directly labelled coordinate records include:

```text
第一殿
Mapcarta / OSM-derived object record
34.68158, 135.84854

第二殿
Wikidata cultural-property record Q107020450
34.68157, 135.8484

第三殿
Mapcarta / OSM-derived object record
34.68157, 135.84844
(Wikidata project page also exposes 34.681576, 135.848419)

第四殿
Mapcarta / OSM-derived object record
34.68157, 135.84839
```

### 12.3 Precision gate

The second-hall coordinate is directly subject-labelled, but the displayed longitude
precision is only four decimal places.

The four Honden are adjacent structures. Promoting that rounded value into a
high-precision four-component mean would create false precision.

Therefore:

```text
KASUGA_SECOND_HALL_SUBJECT_MATCH
= YES

KASUGA_SECOND_HALL_HIGH_PRECISION
= NO

KASUGA_F5_HIGH_PRECISION_SET
= INCOMPLETE

KASUGA_F7
= NOT_COMPUTED

KASUGA_ADJUDICATION
= NOT_ADJUDICATED
```

No interpolation, visual-center inference, ordinal-position inference, or neighboring
hall substitution is permitted.

---

## 13. 宇佐神宮 — Coordinate Follow-up

### 13.1 Semantic set

Authoritative material continues to establish:

```text
上宮 本殿
一之御殿 INCLUDED
二之御殿 INCLUDED
三之御殿 INCLUDED

subject_type = MULTI_PRINCIPAL_UNIT
point_method = UNWEIGHTED_COMPONENT_MEAN
F-4 = COMPLETE
```

Cultural Affairs states that the three Honden are aligned east-west, and Usa City
states that worship is performed at all three Honden.

### 13.2 Directly labelled coordinate evidence

#### 一之御殿

Yahoo! Map exposes a directly labelled object:

```text
subject = 宇佐神宮 一之御殿
coordinate = 33.52343924838255, 131.37705676706398
```

The coordinate is present in the static-map marker request for that named object.

This is map-provider coordinate evidence, not semantic authority.

#### 三之御殿

奈良文化財研究所 Heritage Map exposes:

```text
subject = 宇佐神宮本殿
棟名 = 第三殿
coordinate = 33.52349, 131.3773
source lineage = 文化庁 国指定文化財等データベース
```

#### 二之御殿

Cultural Affairs / 文化遺産オンライン directly identify the 第二殿 as a distinct
National Treasure building.

A secondary National Treasure coordinate index exposes a three-row coordinate sequence
for 宇佐神宮本殿:

```text
33.52346, 131.3770
33.52348, 131.3772
33.52349, 131.3773
```

However that coordinate table does **not** directly attach 第一殿 / 第二殿 / 第三殿
labels to the individual rows in the retrieved evidence.

The current contract prohibits assigning rows by ordinal or spatial inference merely
because Cultural Affairs separately states that the buildings run west-to-east.

Therefore the middle coordinate is **not** promoted to a subject-labelled F-5 entry.

### 13.3 Gate

```text
USA_FIRST_HALL_DIRECT_SUBJECT_LABEL
= YES

USA_SECOND_HALL_DIRECT_SUBJECT_LABEL
= NO

USA_THIRD_HALL_DIRECT_SUBJECT_LABEL
= YES

USA_F5_COMPLETE
= NO

USA_F7
= NOT_COMPUTED

USA_ADJUDICATION
= NOT_ADJUDICATED
```

No partial mean is calculated.

---

## 14. 日光東照宮 — F-7 Representative Point

### 14.1 Semantic QA

Cultural Affairs records:

```text
東照宮 本殿、石の間及び拝殿
員数 = 1棟
```

and describes the connected Gongen-zukuri unit as consisting of 本殿・石の間・拝殿.

Nikko City separately records the internal functions:

- 本殿 = enshrinement building
- 石の間 = connector
- 拝殿 = worship building

The connected cultural-property object is therefore not reinterpreted as three
co-principal enshrinement components.

Batch 01 retains:

```text
subject_type = SINGLE_PRINCIPAL_UNIT
point_method = DIRECT_POINT
```

### 14.2 F-5 / F-6

奈良文化財研究所 Heritage Map / Cultural Affairs lineage provides the
subject-matched coordinate for:

```text
東照宮 本殿、石の間及び拝殿
= 36.75808, 139.5987
```

### 14.3 F-7

Under PR #2980:

```text
F-7 representative_point

latitude = 36.75808
longitude = 139.5987
point_method = DIRECT_POINT
input_count = 1
derivation_note =
  copied exactly from the verified subject-matched F-5 coordinate
```

No mean, rounding correction, centroid, or Navigation adjustment is applied.

### 14.4 F-8

The final F-8 requires the **fresh Production Navigation coordinate**.

Because live Production SELECT was not executable in the current tool surface:

```text
NIKKO_F8_FINAL
= NOT_COMPUTED
```

For audit orientation only, using the last audited stored Production coordinate
`36.7579, 139.5986` would produce approximately 21.9 m geodesic displacement.

That 21.9 m value is **PROVISIONAL / NON-AUTHORITATIVE** and MUST NOT be written into
the final F-8 packet until the live Production SELECT confirms the from-coordinate.

---

## 15. Human QA — Current Result

### 15.1 春日大社

```text
identity                    PASS
semantic owner              PASS
component membership        PASS
component completeness      PASS
subject_type / point_method PASS
coordinate provenance       PARTIAL
representative point        NOT_AVAILABLE
Navigation fallback         NONE
final status                NOT_ADJUDICATED
```

QA blocker:
第二殿のhigh-precision subject-matched coordinate.

### 15.2 宇佐神宮

```text
identity                    PASS
semantic owner              PASS
component membership        PASS
component completeness      PASS
subject_type / point_method PASS
coordinate provenance       PARTIAL
representative point        NOT_AVAILABLE
Navigation fallback         NONE
final status                NOT_ADJUDICATED
```

QA blocker:
二之御殿のdirect subject-labelled coordinate.

### 15.3 日光東照宮

```text
identity                    PASS
semantic owner              PASS
subject_type / point_method PASS
subject-matched coordinate  PASS
F-7 reproducibility         PASS
Navigation fallback         NONE
F-8                         BLOCKED_ON_LIVE_PRODUCTION_SELECT
final status                NOT_ADJUDICATED
```

No accepted-source conflict was found.

The remaining block is operational evidence for F-8, not a semantic disagreement.

---

## 16. Batch 01 Current Final Gate

```text
BATCH_01_CONFIRMED_COUNT
= 0

BATCH_01_HOLD_COUNT
= 0

BATCH_01_NOT_ADJUDICATED_COUNT
= 3
```

Reasons:

```text
春日大社
-> F-5 high-precision component coordinate set incomplete

宇佐神宮
-> F-5 direct subject-labelled component coordinate set incomplete

日光東照宮
-> F-7 complete
-> F-8 blocked until fresh Production Navigation SELECT
```

None of these conditions are accepted-source conflicts, so
`HOLD_POSITION_REVIEW` is not used.

---

## 17. Next Exact Requirements

Only the following evidence gaps remain for Batch 01:

```text
1. Supabase Production:
   SELECT id, name_jp, latitude, longitude
   FROM temples_shrine
   WHERE id IN (5, 8, 9)
   ORDER BY id;

2. 春日大社:
   第二殿のhigher-precision direct subject-matched coordinate

3. 宇佐神宮:
   二之御殿のdirect subject-labelled coordinate
```

After those are obtained:

- generate remaining F-7 where permitted
- calculate F-8 from the fresh Production snapshot
- rerun Human QA
- produce the Batch 01 final adjudication

No DB write is required for any of these steps.

---

## 18. Required Statements — Resume

```text
PHASE_2_BATCH_01_RESUMED = YES

READ_ONLY = YES

F7_CONTRACT_GAP = RESOLVED

PRODUCTION_DB_PROVIDER = SUPABASE

PRODUCTION_NAVIGATION_LIVE_SELECT = NOT_EXECUTED

KASUGA_F7 = NOT_COMPUTED
USA_F7 = NOT_COMPUTED
NIKKO_F7 = COMPLETE
NIKKO_F8_FINAL = NOT_COMPUTED

HUMAN_QA = PARTIAL_COMPLETE

BATCH_01_CONFIRMED_COUNT = 0
BATCH_01_HOLD_COUNT = 0
BATCH_01_NOT_ADJUDICATED_COUNT = 3

CANONICAL_DB_WRITE = NONE
PRODUCTION_WRITE = NONE
SEED_WRITE = NONE
CANONICAL_BACKFILL = NOT_STARTED
RUNTIME_CUTOVER = NOT_PERFORMED
```

## 19. STOP

Batch 01 stops again only on the three explicit evidence gaps in §17.

Do not:

- infer missing component coordinates from order or adjacency
- promote rounded coordinates to false high precision
- substitute historical Production values for a fresh live SELECT
- calculate partial MULTI means
- create Canonical Anchor rows
- write to Production
- begin PHASE_3
