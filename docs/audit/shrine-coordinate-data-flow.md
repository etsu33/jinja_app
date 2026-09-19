# Shrine Coordinate Data Flow Audit

## 1. Scope

This audit traces how Shrine coordinates enter, persist in, and are consumed by KAMI MUSUBI.

The canonical meaning of:

```text
Shrine.latitude / Shrine.longitude
```

is defined by:

```text
docs/knowledge/shrine-position-contract.md
```

as:

```text
Visitor / Navigation Anchor
```

The coordinate is therefore intended to represent a practical visitor-facing map / distance / direction / route target for the Shrine.

This audit focuses on:

* coordinate provenance
* coordinate ingestion paths
* Base Seed behavior
* Candidate Master / Position Resolution behavior
* historical coordinate corrections
* representative Pilot sampling
* Entry / Anchor complexity
* reproducibility risks
* coordinate drift between repository-controlled artifacts

This audit does not:

* modify Base Seed
* modify Candidate Master
* modify Production DB
* change existing migrations
* change Recommendation / Ranking logic
* change Compass scoring
* introduce a fixed coordinate-distance PASS threshold
* automatically adopt a new coordinate
* resolve Mother Ship decisions

Phase 1 is discovery only.

The objective is to determine:

```text
where coordinate error can originate
↓
which errors are technical
↓
which errors are source / provenance / anchor-definition problems
↓
which cases require human Position review
```

The Position Contract remains authoritative for final position adoption.

---

## 2. Current Coordinate Data Flow

### 2.1 Canonical storage

The Shrine model stores:

```text
latitude
longitude
location
```

with:

```text
latitude  = FloatField
longitude = FloatField
location  = PointField(srid=4326)
```

The GIS representation uses WGS84 / SRID 4326.

Normal ORM save behavior derives:

```text
Point(longitude, latitude, srid=4326)
```

from the stored latitude / longitude pair.

Therefore the internal GIS order is:

```text
longitude, latitude
```

while public Shrine coordinate fields remain:

```text
latitude, longitude
```

No evidence was found in the inspected Base Seed / importer flow of a systematic latitude / longitude swap.

### 2.2 Base Seed path

The repository-controlled Base Seed is:

```text
backend/temples/data/shrines_seed_clean.json
```

The primary import path is:

```text
shrines_seed_clean.json
↓
backend/temples/management/commands/import_shrines_seed.py
↓
Shrine.latitude / Shrine.longitude
↓
Shrine.location
```

The importer reads:

```text
latitude
longitude
```

directly from the Seed.

When GIS is enabled and both values are available, it creates:

```text
Point(longitude, latitude, srid=4326)
```

The importer therefore does not intentionally reinterpret the coordinate meaning.

### 2.3 Base Seed builder

The deterministic Base Seed builder is:

```text
scripts/build_base_shrine_seed.py
```

Its `canonicalize_row()` contract explicitly fixes key ordering only.

The builder states:

```text
値は一切変換しない
```

No coordinate rounding, datum conversion, latitude / longitude swap, geocoding, or coordinate recalculation occurs in the builder.

Therefore:

```text
Base Seed builder
!=
coordinate derivation layer
```

The builder cannot explain a spatial offset already present in an input coordinate.

### 2.4 Google Places / PlaceRef path

A separate coordinate ingress path exists through Places / PlaceRef.

Observed flow:

```text
Places result
↓
PlaceRef
↓
backend/temples/api/views/shrines_nearby.py
↓
Shrine.latitude / Shrine.longitude
```

This path can therefore introduce or update Shrine coordinates independently of the Base Seed flow.

Coordinate provenance cannot be inferred solely from the current stored numeric value.

### 2.5 Address geocoding path

Another possible coordinate path exists through:

```text
Shrine.address
↓
auto_geocode_on_save
↓
GeocodingClient
↓
Shrine.latitude / Shrine.longitude
```

The signal is guarded by:

```text
AUTO_GEOCODE_ON_SAVE
```

The repository default is OFF:

```text
AUTO_GEOCODE_ON_SAVE = 0
```

Whether a deployed environment has enabled the setting must not be inferred from repository defaults alone.

Address geocoding is therefore treated as a possible runtime coordinate ingress path, not as the canonical Position source.

### 2.6 Coordinate consumers

Stored Shrine coordinates are directly consumed by location-sensitive product behavior.

Relevant consumers include:

```text
nearest / distance calculation
Compass bearing
direction filtering
map display
route guidance
Shrine detail map flow
```

In particular, Compass direction is calculated from user origin to stored Shrine coordinates.

Therefore coordinate quality affects more than map marker appearance.

A wrong coordinate can affect:

```text
distance
direction
Compass filtering
navigation
visitor experience
```

### 2.7 Current technical conclusion

No current evidence indicates that the primary systematic error source is:

```text
SRID conversion
latitude / longitude order
Base Seed builder transformation
coordinate rounding in builder
runtime bearing mathematics
```

The strongest observed risk currently lies in:

```text
coordinate provenance
source quality
anchor meaning
independent write paths
artifact synchronization
```

---

## 3. Coordinate Provenance Classification

The inspected current Base Seed contains:

```text
113 Shrine rows
```

Mechanical identity comparison found:

```text
Original legacy initial set        = 100
Wave0 Candidate Master overlap     = 10
Batch17 additions outside legacy   = 3
```

The three Batch17 additions are:

```text
北海道神宮
建部大社
波上宮
```

### 3.1 Legacy 100

The original legacy dataset contains 100 Shrine identities.

Per-row Position source metadata is generally not present for this original population.

Two legacy Shrines have later explicit coordinate correction records:

```text
多摩川浅間神社
富岡八幡宮
```

Therefore the legacy population is divided into:

```text
LEGACY_CORRECTED / KNOWN_CORRECTION = 2
LEGACY_UNTRACED                     = 98
```

`LEGACY_UNTRACED` does not mean that the coordinate is wrong.

It means:

```text
current coordinate provenance cannot be reconstructed
to the current Position Contract standard
from the legacy Seed alone
```

### 3.2 Batch17 3 Shrines

Batch17 added:

```text
北海道神宮
建部大社
波上宮
```

Their origins are more traceable than the original 100, but they do not all have the same Position evidence strength.

北海道神宮 and 波上宮 reused repository-tracked coordinate evidence.

建部大社 required additional source research and cross-checking before adoption.

They are therefore kept separate from `LEGACY_UNTRACED`.

### 3.3 Wave0 Position-tracked candidates

The following current Base Seed entries overlap the Wave0 Candidate Master:

```text
wave0-001 三輪神社
wave0-002 大鳥大社
wave0-003 御岩神社
wave0-005 烏森神社
wave0-006 榴岡天満宮
wave0-007 射水神社
wave0-008 別小江神社
wave0-009 戸隠神社 中社
wave0-010 札幌諏訪神社
wave0-011 少彦名神社
```

For these rows the intended Position chain is traceable through:

```text
Source Packet / Position Resolution
↓
Candidate Master
↓
Base Seed
```

The Wave0 Seed tests intentionally compare coordinates without recalculation so that rounding or silent recomputation does not become a new source of truth.

A Wave0 provenance chain being traceable does not automatically mean every Position is currently `PASS`.

Position status remains governed by the Position Contract and applicable Position Resolution Record.

### 3.4 Provenance summary

```text
Current Base Seed                         113
├─ Legacy initial population             100
│  ├─ Known correction cases               2
│  └─ LEGACY_UNTRACED                     98
│
├─ Batch17 additions                       3
│
└─ Wave0 Candidate Master additions       10
```

This classification is a provenance classification only.

It is not a coordinate-quality score.

---

## 4. LEGACY_UNTRACED Population

The mechanically identified `LEGACY_UNTRACED` population contains 98 Shrines.

```text
01 明治神宮
02 伏見稲荷大社
03 伊勢神宮（内宮）
04 出雲大社
05 春日大社
06 太宰府天満宮
07 熱田神宮
08 宇佐神宮
09 日光東照宮
10 鶴岡八幡宮
11 住吉大社
12 石清水八幡宮
13 金刀比羅宮
14 鹿島神宮
15 香取神宮
16 氷川神社（大宮）
17 三峯神社
18 箱根神社
19 富士山本宮浅間大社
20 諏訪大社（上社本宮）
21 長太稲荷神社
22 給田六所神社
23 神田神社（神田明神）
24 浅草神社
25 大國魂神社
26 寒川神社
27 榛名神社
28 筑波山神社
29 阿佐ヶ谷神明宮
30 彌彦神社
31 氣多大社
32 越中一宮 高瀬神社
33 椿大神社
34 賀茂御祖神社（下鴨神社）
35 賀茂別雷神社（上賀茂神社）
36 生田神社
37 吉備津神社
38 厳島神社
39 宮地嶽神社
40 川越氷川神社
41 白山比咩神社
42 高千穂神社
43 日枝神社
44 東京大神宮
45 芝大神宮
46 愛宕神社
47 亀戸天神社
48 根津神社
49 品川神社
50 大宮八幡宮
51 江島神社
52 水戸東照宮
53 二荒山神社
54 貴船神社
55 八坂神社
56 住吉神社（博多）
57 靖國神社
58 乃木神社
59 赤坂氷川神社
60 花園神社
61 小網神社
62 鳥越神社
63 湯島天満宮
64 白山神社
65 王子神社
66 千住神社
67 葛西神社
68 穴守稲荷神社
69 武蔵御嶽神社
70 武蔵一宮 氷川女體神社
71 調神社
72 秩父神社
73 鷲宮神社
74 箭弓稲荷神社
75 安房神社
76 千葉神社
77 玉前神社
78 櫻木神社
79 大洗磯前神社
80 笠間稲荷神社
81 酒列磯前神社
82 宇都宮二荒山神社
83 足利織姫神社
84 古峯神社
85 冠稲荷神社
86 妙義神社
87 赤城神社
88 鶴嶺八幡宮
89 森戸大明神
90 報徳二宮神社
91 九頭龍神社 新宮
92 平塚八幡宮
93 忌宮神社
94 高良大社
95 寳登山神社
96 枚岡神社
97 護王神社
98 阿蘇神社
```

The purpose of this list is to freeze the Phase 1 audit population.

It must not be interpreted as:

```text
98 incorrect coordinates
```

The correct interpretation is:

```text
98 coordinates requiring provenance validation
before current Position Contract confidence can be claimed
```

### 4.1 Pilot stratification

For Pilot selection, the population was stratified by location / navigation characteristics.

The categories are audit-selection aids rather than permanent Shrine taxonomy.

```text
URBAN_COMPACT
LARGE_PRECINCT
MOUNTAIN_FOREST
COAST_WATER
STANDARD_MIXED
```

A Shrine may exhibit characteristics of more than one group.

The Pilot uses a dominant audit characteristic only to avoid sample bias.

`MULTI_ENTRY` is not inferred automatically from these categories.

Entry structure requires separate evidence.

---

## 5. 20-Shrine Pilot Selection

The Phase 1 Pilot contains exactly 20 Shrines.

```text
LEGACY_UNTRACED                       14
KNOWN CORRECTION / DRIFT CONTROL       2
WAVE0 POSITION CONTROL                 4
────────────────────────────────────────
TOTAL                                 20
```

The Pilot is designed to test the audit method itself.

It is not a popularity ranking and is not intended to estimate a population-wide error rate.

### 5.1 LEGACY_UNTRACED — 14

| #  | Shrine     | Stratum         | Selection reason                                  |
| -- | ---------- | --------------- | ------------------------------------------------- |
| 1  | 神田神社（神田明神） | URBAN_COMPACT   | Dense urban POI environment                       |
| 2  | 生田神社       | URBAN_COMPACT   | Non-Tokyo major urban case                        |
| 3  | 千葉神社       | URBAN_COMPACT   | Regional city urban case                          |
| 4  | 住吉神社（博多）   | URBAN_COMPACT   | Kyushu urban case                                 |
| 5  | 伊勢神宮（内宮）   | LARGE_PRECINCT  | Large precinct and visitor-anchor separation      |
| 6  | 伏見稲荷大社     | LARGE_PRECINCT  | Long route / broad worship area                   |
| 7  | 鹿島神宮       | LARGE_PRECINCT  | Large eastern Japan precinct                      |
| 8  | 宇佐神宮       | LARGE_PRECINCT  | Large western Japan precinct                      |
| 9  | 三峯神社       | MOUNTAIN_FOREST | Mountain navigation / shrine-anchor separation    |
| 10 | 金刀比羅宮      | MOUNTAIN_FOREST | Large elevation and long approach route           |
| 11 | 貴船神社       | MOUNTAIN_FOREST | Mountain valley / multi-site complexity           |
| 12 | 厳島神社       | COAST_WATER     | Island / waterfront navigation                    |
| 13 | 江島神社       | COAST_WATER     | Island and multiple worship sites                 |
| 14 | 彌彦神社       | STANDARD_MIXED  | Comparison case without deliberate high-risk bias |

### 5.2 Known correction controls — 2

#### 多摩川浅間神社

Historical coordinate:

```text
35.5898, 139.6688
```

Current Base Seed:

```text
35.5875263, 139.6687549
```

Current Google Maps POI evidence supplied during this audit:

```text
35.5875263, 139.6687549
Plus Code: HMQ9+2G 大田区、東京都
```

Role:

```text
KNOWN_CORRECTED
```

This functions as a positive control showing a historical stored-coordinate error that was propagated back into the current Base Seed.

#### 富岡八幡宮

Current Base Seed:

```text
35.6733, 139.7967
```

Migration `0099_fix_shrine_49_coordinates.py`:

```text
35.6717809, 139.799519
```

Current Google Maps POI evidence supplied during this audit:

```text
35.6717809, 139.799519
Plus Code: MQCX+PR 江東区、東京都
```

Role:

```text
KNOWN_CORRECTION_WITH_SEED_DRIFT
```

Unlike 多摩川浅間神社, the known correction has not propagated back to the current Base Seed.

This case therefore tests both coordinate detection and artifact synchronization.

### 5.3 Wave0 Position controls — 4

| Candidate   | Shrine | Control role                                           |
| ----------- | ------ | ------------------------------------------------------ |
| `wave0-003` | 御岩神社   | Position Contract PASS / explicit Visitor Anchor case  |
| `wave0-007` | 射水神社   | Position Resolution / review-sensitive case            |
| `wave0-010` | 札幌諏訪神社 | Position Resolution PASS / corrected access-map anchor |
| `wave0-002` | 大鳥大社   | Standard Wave0 tracked Position case                   |

These four are not selected for full manual re-research.

Their purpose is to compare legacy provenance behavior with newer Position-managed data.

---

## 6. Entry / Anchor Complexity

Entry structure and Anchor complexity are intentionally separated.

The audit does not assume:

```text
multiple entrances
=
multiple valid Shrine coordinates
```

Nor does it assume:

```text
single entrance
=
simple Visitor Anchor
```

A Shrine can have one obvious entrance while still having a high-complexity navigation target.

### 6.1 Audit fields

Entry observations use:

```text
MULTI_CONFIRMED
SINGLE_CONFIRMED
MULTI_SITE
NOT_CONFIRMED
```

Anchor complexity uses:

```text
LOW
MEDIUM
HIGH
```

These are audit observations only.

They are not Position Contract PASS / HOLD states.

### 6.2 Pilot observations

| Shrine     | Entry observation | Anchor complexity | Audit note                                                                  |
| ---------- | ----------------- | ----------------- | --------------------------------------------------------------------------- |
| 神田神社（神田明神） | MULTI_CONFIRMED   | MEDIUM            | Multiple visitor approaches increase navigation-anchor ambiguity            |
| 生田神社       | NOT_CONFIRMED     | LOW               | Urban primary-site comparison                                               |
| 千葉神社       | NOT_CONFIRMED     | MEDIUM            | Multiple structures, but entry count not assumed                            |
| 住吉神社（博多）   | NOT_CONFIRMED     | MEDIUM            | Visitor entrance and service access must not be conflated                   |
| 伊勢神宮（内宮）   | SINGLE_CONFIRMED  | HIGH              | Entrance and principal worship destination are spatially distinct concepts  |
| 伏見稲荷大社     | NOT_CONFIRMED     | HIGH              | Shrine identity spans a long worship route / mountain context               |
| 鹿島神宮       | MULTI_CANDIDATE   | HIGH              | Large precinct with more than one meaningful access context                 |
| 宇佐神宮       | NOT_CONFIRMED     | HIGH              | Upper / lower worship areas make a single representative point non-trivial  |
| 三峯神社       | NOT_CONFIRMED     | HIGH              | Parking / approach / shrine / mountain-area points must remain distinct     |
| 金刀比羅宮      | NOT_CONFIRMED     | HIGH              | Long elevation-based approach makes route anchor significant                |
| 貴船神社       | MULTI_SITE        | HIGH              | 本宮 / 結社 / 奥宮 must not be collapsed without policy                           |
| 厳島神社       | SINGLE_ROUTE      | MEDIUM            | Visitor flow has a strong route component                                   |
| 江島神社       | MULTI_SITE        | HIGH              | Multiple worship sites exist within the broader Shrine experience           |
| 彌彦神社       | NOT_CONFIRMED     | MEDIUM            | Used as a lower-risk comparison case                                        |
| 多摩川浅間神社    | SINGLE_CANDIDATE  | LOW               | Known corrected POI provides a relatively simple positive control           |
| 富岡八幡宮      | NOT_CONFIRMED     | MEDIUM            | Coordinate drift is confirmed independently of entry structure              |
| 御岩神社       | NOT_CONFIRMED     | HIGH              | Shrine / mountain / related worship-site context requires anchor discipline |
| 射水神社       | MULTI_CANDIDATE   | HIGH              | Park context and navigation access make visitor targeting non-trivial       |
| 札幌諏訪神社     | NOT_CONFIRMED     | LOW               | Relatively compact Wave0 control                                            |
| 大鳥大社       | NOT_CONFIRMED     | MEDIUM            | Vehicle access and ordinary visitor approach can represent different points |

`MULTI_CANDIDATE`, `SINGLE_CANDIDATE`, and `SINGLE_ROUTE` are descriptive Pilot observations, not permanent controlled vocabulary.

They must not be promoted into production taxonomy without a separate specification decision.

### 6.3 Phase 1 conclusion

The Pilot demonstrates that coordinate quality requires at least three concepts to remain separate:

```text
ENTRY_COMPLEXITY
ANCHOR_COMPLEXITY
MULTI_SITE_COMPLEXITY
```

A coordinate can be numerically accurate for a Shrine POI while still being a poor Visitor / Navigation Anchor.

Therefore Phase 2 automation must not reduce Position quality to:

```text
distance between two coordinates
```

alone.

---

## 7. Pilot Evidence Collection Schema

The 20-Shrine Pilot uses one common evidence schema.

The purpose is to prevent each Shrine from being investigated using a different ad-hoc method.

### 7.1 Schema

```text
pilot_no
pilot_group
candidate_id

official_name
official_address

stored_latitude
stored_longitude
stored_coordinate_artifact

official_position_status
official_position_type
official_position_latitude
official_position_longitude
official_position_url

map_provider
map_provider_poi_latitude
map_provider_poi_longitude
map_provider_poi_url
map_provider_plus_code

secondary_provider
secondary_provider_latitude
secondary_provider_longitude
secondary_provider_url

candidate_visitor_anchor_type
candidate_visitor_anchor_latitude
candidate_visitor_anchor_longitude

entry_status
anchor_complexity
multi_site_status
visitor_flow_note
navigation_risk_note

stored_vs_official_delta_m
stored_vs_provider_delta_m
provider_vs_provider_delta_m

evidence_collected_at
notes
```

### 7.2 Missing evidence rule

Unknown values are not inferred.

Use:

```text
NOT_RETRIEVED
```

when evidence has not yet been collected.

This prevents an empty value from being misread as:

```text
no conflict
not applicable
zero distance
PASS
```

### 7.3 Initial stored-coordinate snapshot

| #  | Shrine     | Pilot group                      | Stored coordinate                      |
| -- | ---------- | -------------------------------- | -------------------------------------- |
| 1  | 神田神社（神田明神） | LEGACY_UNTRACED                  | `35.7019, 139.7674`                    |
| 2  | 生田神社       | LEGACY_UNTRACED                  | `34.694, 135.1923`                     |
| 3  | 千葉神社       | LEGACY_UNTRACED                  | `35.6114, 140.1246`                    |
| 4  | 住吉神社（博多）   | LEGACY_UNTRACED                  | `33.587, 130.4086`                     |
| 5  | 伊勢神宮（内宮）   | LEGACY_UNTRACED                  | `34.455, 136.7256`                     |
| 6  | 伏見稲荷大社     | LEGACY_UNTRACED                  | `34.9671, 135.7727`                    |
| 7  | 鹿島神宮       | LEGACY_UNTRACED                  | `35.9658, 140.6285`                    |
| 8  | 宇佐神宮       | LEGACY_UNTRACED                  | `33.531, 131.379`                      |
| 9  | 三峯神社       | LEGACY_UNTRACED                  | `35.9221, 138.9336`                    |
| 10 | 金刀比羅宮      | LEGACY_UNTRACED                  | `34.1811, 133.8216`                    |
| 11 | 貴船神社       | LEGACY_UNTRACED                  | `35.1217, 135.762`                     |
| 12 | 厳島神社       | LEGACY_UNTRACED                  | `34.2959, 132.3199`                    |
| 13 | 江島神社       | LEGACY_UNTRACED                  | `35.3013, 139.4805`                    |
| 14 | 彌彦神社       | LEGACY_UNTRACED                  | `37.7047, 138.8287`                    |
| 15 | 多摩川浅間神社    | KNOWN_CORRECTED                  | `35.5875263, 139.6687549`              |
| 16 | 富岡八幡宮      | KNOWN_CORRECTION_WITH_SEED_DRIFT | `35.6733, 139.7967`                    |
| 17 | 御岩神社       | WAVE0_CONTROL                    | `36.63604985, 140.58558306`            |
| 18 | 射水神社       | WAVE0_CONTROL                    | `36.7484968, 137.0215428`              |
| 19 | 札幌諏訪神社     | WAVE0_CONTROL                    | `43.07603505258046, 141.3540979693115` |
| 20 | 大鳥大社       | WAVE0_CONTROL                    | `34.5367778, 135.4608611`              |

### 7.4 Existing high-confidence evidence

The Pilot begins with several already-traceable cases.

#### 多摩川浅間神社

```text
stored_coordinate =
35.5875263, 139.6687549

Google Maps POI =
35.5875263, 139.6687549

known historical coordinate =
35.5898, 139.6688
```

#### 富岡八幡宮

```text
stored Base Seed =
35.6733, 139.7967

migration 0099 =
35.6717809, 139.799519

Google Maps POI =
35.6717809, 139.799519
```

This is a confirmed artifact synchronization discrepancy.

#### 御岩神社

```text
candidate_id = wave0-003

stored =
36.63604985, 140.58558306

POSITION_STATUS = PASS
```

The Position Contract records this value as an adopted Visitor / Navigation Anchor.

#### 札幌諏訪神社

```text
candidate_id = wave0-010

stored =
43.07603505258046, 141.3540979693115

POSITION_STATUS = PASS
```

The Position Resolution Record adopts the access-map coordinate based on source meaning rather than distance alone.

### 7.5 Delta policy

The following fields remain observational:

```text
stored_vs_official_delta_m
stored_vs_provider_delta_m
provider_vs_provider_delta_m
```

No fixed meter threshold is introduced in Phase 1.

Distance does not independently determine:

```text
PASS
HOLD_POSITION_REVIEW
```

Position adoption still requires identity, source type, point purpose, and conflict interpretation under the Position Contract.

---

## 8. Phase 1 Findings

### 8.1 富岡八幡宮 Base Seed Coordinate Drift

#### Status

`CONFIRMED`

#### Affected shrine

```text
official_name = 富岡八幡宮
official_address = 東京都江東区富岡1-20-3
```

#### Current Base Seed

```text
latitude  = 35.6733
longitude = 139.7967
```

#### Known corrected coordinate

Migration `0099_fix_shrine_49_coordinates.py` records the corrected coordinate as:

```text
latitude  = 35.6717809
longitude = 139.799519
```

#### Current provider evidence

Google Maps POI:

```text
latitude  = 35.6717809
longitude = 139.799519
plus_code = MQCX+PR 江東区、東京都
```

The Google Maps POI coordinate exactly matches the coordinate recorded by migration `0099`.

#### Observed drift

```text
Base Seed
35.6733, 139.7967

!=

Migration 0099
35.6717809, 139.799519

=

Current Google Maps POI
35.6717809, 139.799519
```

Therefore the current Base Seed retains the pre-correction coordinate even though a later correction exists and is independently consistent with the current provider POI.

#### Classification

```text
finding_type = SEED_COORDINATE_DRIFT
pilot_group = KNOWN_CORRECTION_WITH_SEED_DRIFT
root_layer = DATA / PROVENANCE
runtime_transformation_error = NOT_OBSERVED
builder_transformation_error = NOT_OBSERVED
```

#### Interpretation

This finding does not indicate a latitude/longitude conversion, SRID, precision, or Base Seed builder error.

The observed issue is a synchronization gap between:

```text
historical Base Seed coordinate
↓
later coordinate correction
↓
current Base Seed
```

The correction was represented in a migration, but the canonical Base Seed did not receive the same corrected value.

#### Risk

If the Base Seed is later used to rebuild or import Shrine data without an additional correction gate, the old coordinate can be reintroduced.

This is therefore a reproducibility and re-import regression risk, not only a historical coordinate-quality issue.

#### Phase 1 handling

Phase 1 records this discrepancy only.

Do not modify:

* Base Seed
* Production DB
* migration history
* Recommendation logic
* Compass logic

Remediation belongs to a separately gated follow-up after the Pilot classification is complete.

## 9. Open Items

* Collect Primary Position Evidence for the 20-Shrine Pilot using one fixed procedure.
* Collect provider POI evidence using one fixed procedure.
* Measure coordinate deltas.
* Classify observed discrepancies into the Phase 1 error taxonomy.
* Determine which checks can become deterministic Phase 2 rules.
* Do not remediate coordinate data inside this Phase 1 audit.

## 10. STOP

This document records Phase 1 discovery state only.

No coordinate remediation is authorized by this audit document.
