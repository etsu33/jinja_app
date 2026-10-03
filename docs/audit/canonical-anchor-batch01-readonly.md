# Canonical Shrine Anchor — PHASE_2 Batch 01 Read-only Audit

## Status

- Status: IN_PROGRESS_RESUMED_AFTER_F7_DECISION
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

## 10. Resume after F-7 Representative Point Decision

Mother Ship decision:

docs/audit/canonical-anchor-f7-representative-point-decision.md

was merged before this continuation.

The prior contract gap is therefore closed:

~~~text
DIRECT_POINT_PACKET_FINAL_POINT_REPRESENTATION
= RESOLVED

ACTIVE_PHASE_2_F7
= representative_point
~~~

Batch 01 resumes read-only under that ACTIVE contract.

---

## 11. PASS D Resume — Coordinate Evidence

### 11.1 春日大社

Semantic state remains unchanged:

~~~text
subject_type = MULTI_PRINCIPAL_UNIT
point_method = UNWEIGHTED_COMPONENT_MEAN
F-4 = COMPLETE
~~~

Authoritative semantic sources continue to identify the four Main Sanctuary halls:

- 春日大社 official Main Sanctuary:
  https://www.kasugataisha.or.jp/guidance/keidai-map3/modal-01/
- 文化庁 第二殿 record:
  https://kunishitei.bunka.go.jp/heritage/detail/102/2534
- 文化遺産データベース 第二殿:
  https://online.bunka.go.jp/db/heritages/detail/147731

Object-level corroboration reproduced in this continuation:

~~~text
第一殿
source = OpenStreetMap-derived Mapcarta object
OSM way = 1134481290
latitude = 34.68158
longitude = 135.84854

第三殿
source = OpenStreetMap-derived Mapcarta object
OSM way = 1134481289
latitude = 34.68157
longitude = 135.84844

第四殿
source = OpenStreetMap-derived Mapcarta object
OSM way = 1134481288
latitude = 34.68157
longitude = 135.84839
~~~

Related source URLs:

- https://mapcarta.com/W1134481290
- https://mapcarta.com/es/W1134481289
- https://mapcarta.com/es/W1134481288

A Wikidata maintenance table exposes a coordinate for 第二殿:

~~~text
Q107020450
34.68157, 135.8484
~~~

but the same rounded coordinate is also exposed for other Main Sanctuary halls.
That precision does not preserve a reliable object-level distinction between the four
INCLUDED components.

Therefore:

~~~text
KASUGA_F5_STATUS
= INCOMPLETE

MISSING_ACCEPTED_INPUT
= 第二殿 subject-distinguishing coordinate provenance
~~~

No F-7 mean is calculated.

The existence of a plausible coordinate is not promoted to a complete F-5 packet
unless the same source can distinguish the intended component reproducibly.

---

### 11.2 宇佐神宮

Semantic state remains unchanged:

~~~text
semantic owner = 上宮
subject_type = MULTI_PRINCIPAL_UNIT
point_method = UNWEIGHTED_COMPONENT_MEAN
F-4 = COMPLETE
~~~

文化庁 explicitly records:

~~~text
本殿は西から第一、第二、第三の順に並立
~~~

for the three Honden.

Source:

https://kunishitei.bunka.go.jp/heritage/detail/102/3599

A Kanagawa University architecture research page exposes three numeric rows for
宇佐神宮本殿:

~~~text
33.52346, 131.3770
33.52348, 131.3772
33.52349, 131.3773
~~~

Source:

https://www.arch.kanagawa-u.ac.jp/lab/shimazaki_kazushi/shimazaki/NationalTreasureBuilding/NationalTreasureBuilding.html

The third coordinate independently matches the 奈良文化財研究所 Cultural Affairs-derived
第三殿 record:

~~~text
第三殿
33.52349, 131.3773
RecNo = 98032356
~~~

Source:

https://heritagemap.nabunken.go.jp/statistic/98032356-%E5%AE%87%E4%BD%90%E7%A5%9E%E5%AE%AE%E6%9C%AC%E6%AE%BF.html

However, the Kanagawa University table does not expose the 棟名 labels beside the three
宇佐神宮 rows in the fetched representation.

Using longitude order plus the Cultural Affairs west-to-east description would allow
a plausible deterministic mapping:

~~~text
west -> 第一殿
middle -> 第二殿
east -> 第三殿
~~~

but this would be a derived attribution rather than a directly subject-labelled
coordinate record for 第一殿 and 第二殿.

Under the current PHASE_2 fail-closed rule this continuation does not silently promote
that attribution into F-5.

Therefore:

~~~text
USA_F5_STATUS
= INCOMPLETE

VERIFIED_COMPONENT_COORDINATE
= 第三殿 33.52349, 131.3773

UNRESOLVED_COMPONENT_COORDINATE_ATTRIBUTION
= 第一殿
= 第二殿
~~~

No official F-7 mean is calculated.

For audit only, the three candidate numeric rows have an arithmetic mean of:

~~~text
33.52347666666667
131.37716666666665
~~~

This diagnostic value is NOT F-7 and is NOT a Canonical candidate because the
per-component F-5 attribution is not complete.

---

### 11.3 日光東照宮

The F-7 contract gap is closed.

Semantic state:

~~~text
subject = 東照宮 本殿、石の間及び拝殿 connected principal unit
subject_type = SINGLE_PRINCIPAL_UNIT
point_method = DIRECT_POINT
~~~

The same named subject is georeferenced by 奈良文化財研究所:

~~~text
subject = 東照宮 本殿、石の間及び拝殿
latitude = 36.75808
longitude = 139.5987
~~~

Source:

https://heritagemap.nabunken.go.jp/statistic/98002610-%E6%9D%B1%E7%85%A7%E5%AE%AE_%E6%9C%AC%E6%AE%BF%E3%80%81%E7%9F%B3%E3%81%AE%E9%96%93%E5%8F%8A%E3%81%B3%E6%8B%9D%E6%AE%BF.html

A separate architecture research table corroborates the same subject at approximately
the same coordinate.

Under the ACTIVE F-7 decision:

~~~text
F-7 representative_point

latitude = 36.75808
longitude = 139.5987
point_method = DIRECT_POINT
input_count = 1
derivation_note =
  copied exactly from the verified subject-matched F-5 coordinate
~~~

No mean is asserted.

Current state:

~~~text
NIKKO_F5 = COMPLETE
NIKKO_F6 = COMPLETE
NIKKO_F7 = COMPLETE
NIKKO_F8 = PENDING_LIVE_PRODUCTION_NAVIGATION_READ
~~~

The repository contains historical / candidate Navigation values, but F-8 requires the
current Visitor / Navigation Anchor meaning and value at execution time.

This audit does not substitute a stale repository value for the live read-only check.

---

## 12. Production Read-only Gate

The final F-8 step requires a live read-only query of the current Production Shrine rows.

Target:

~~~text
Shrine.id IN (5, 8, 9)

fields:
id
name_jp
address
latitude
longitude
place_ref_id
~~~

No write is required.

The connected Render account currently exposes one workspace candidate, but the Render
connector requires explicit user confirmation of the workspace before any database
query.

Therefore the audit remains fail-closed until that authorization is supplied.

~~~text
PRODUCTION_READ
= NOT_YET_EXECUTED

PRODUCTION_WRITE
= NONE
~~~

---

## 13. Current Batch State after Resume

| Shrine | F-4 | F-5 | F-6 | F-7 | F-8 | Current adjudication |
| --- | --- | --- | --- | --- | --- | --- |
| 春日大社 | COMPLETE | INCOMPLETE | PARTIAL | NOT_COMPUTED | NOT_ALLOWED | NOT_ADJUDICATED |
| 宇佐神宮 | COMPLETE | INCOMPLETE | PARTIAL | NOT_COMPUTED | NOT_ALLOWED | NOT_ADJUDICATED |
| 日光東照宮 | PRELIMINARY_COMPLETE | COMPLETE | COMPLETE | COMPLETE (DIRECT_POINT) | PENDING_PRODUCTION_READ | NOT_ADJUDICATED |

No shrine is moved to HOLD_POSITION_REVIEW.

The remaining blockers are missing / insufficiently attributable coordinate evidence
and a live read-only Navigation snapshot, not accepted-source conflicts.

---

## 14. Updated Required Statements

~~~text
PHASE_2_BATCH_01_STARTED = YES
PHASE_2_BATCH_01_RESUMED = YES

F7_CONTRACT_GAP = RESOLVED

KASUGA_F5 = INCOMPLETE
USA_F5 = INCOMPLETE
NIKKO_F7 = COMPLETE

PRODUCTION_READ = NOT_YET_EXECUTED
PRODUCTION_WRITE = NONE

CANONICAL_DB_WRITE = NONE
SEED_WRITE = NONE
CANONICAL_BACKFILL = NOT_STARTED
RUNTIME_CUTOVER = NOT_PERFORMED

BATCH_01_CONFIRMED_COUNT = 0
BATCH_01_HOLD_COUNT = 0
BATCH_01_NOT_ADJUDICATED_COUNT = 3
~~~

## 15. STOP Boundary after Resume

Do not:

- infer 春日大社 第二殿 from rounded shared coordinates
- infer 宇佐神宮 第一殿 / 第二殿 attribution from longitude ordering as final F-5
- compute a MULTI F-7 from incomplete F-5
- use stale repository Navigation coordinates as final F-8 input
- create Canonical Anchor rows
- perform Production writes
- begin PHASE_3
