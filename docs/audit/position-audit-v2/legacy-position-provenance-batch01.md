# LEGACY_UNTRACED Position Provenance Audit — Batch 01

## Status

- Status: `IN_PROGRESS`
- Recorded at: `2026-09-21`
- Batch: `LEGACY_UNTRACED Batch 01`
- Targets: 10 Shrines
- Complete: `5/10`
- PASS: `5`
- HOLD_POSITION_REVIEW: `0`
- NOT_ADJUDICATED: `5`
- Production write during audit: `NONE`
- Base Seed write during audit: `NONE`
- Post-audit remediation completed: `2/4`

本書は Position Contract の変更ではない。採用ルールの authority は
`docs/knowledge/shrine-position-contract.md` のままである。

## 1. Batch Scope / Production Snapshot

### Target Shrines

1. 明治神宮
2. 伏見稲荷大社
3. 伊勢神宮（内宮）
4. 出雲大社
5. 春日大社
6. 太宰府天満宮
7. 熱田神宮
8. 宇佐神宮
9. 日光東照宮
10. 鶴岡八幡宮

### Production Snapshot

- source: repo-external `~/production-position-snapshot.txt`
- recorded_at: `2026-09-21 12:56:35 JST`
- sha256: `a19b8d3b0868a3b7d2122583140115066258e805c6b0b3b9325a1c5fad8a861f`
- production_total: `113`
- batch_target_count: `10`
- fields: `id / name_jp / address / latitude / longitude / kind / place_ref_id`

Raw Production snapshot は repository に commit しない。

### Current Stored Positions

| # | Shrine | Production ID | Address | Latitude | Longitude | place_ref_id |
| --- | --- | ---: | --- | ---: | ---: | --- |
| 01 | 明治神宮 | 1 | 東京都渋谷区代々木神園町1-1 | 35.6764 | 139.6993 | null |
| 02 | 伏見稲荷大社 | 2 | 京都府京都市伏見区深草薮之内町68 | 34.9671 | 135.7727 | null |
| 03 | 伊勢神宮（内宮） | 3 | 三重県伊勢市宇治館町1 | 34.455 | 136.7256 | null |
| 04 | 出雲大社 | 4 | 島根県出雲市大社町杵築東195 | 35.4016 | 132.6853 | null |
| 05 | 春日大社 | 5 | 奈良県奈良市春日野町160 | 34.6814 | 135.8481 | null |
| 06 | 太宰府天満宮 | 6 | 福岡県太宰府市宰府4-7-1 | 33.5213 | 130.5351 | null |
| 07 | 熱田神宮 | 7 | 愛知県名古屋市熱田区神宮1-1-1 | 35.1279 | 136.9114 | null |
| 08 | 宇佐神宮 | 8 | 大分県宇佐市南宇佐2859 | 33.531 | 131.379 | null |
| 09 | 日光東照宮 | 9 | 栃木県日光市山内2301 | 36.7579 | 139.5986 | null |
| 10 | 鶴岡八幡宮 | 10 | 神奈川県鎌倉市雪ノ下2-1-31 | 35.3256 | 139.5566 | null |

## 2. Audit Rules

Authoritative contract:

`docs/knowledge/shrine-position-contract.md`

Machine-audit reference:

`docs/audit/shrine-position-ground-truth-v2.md`

Canonical meaning:

```text
Shrine.latitude / Shrine.longitude
= Visitor / Navigation Anchor
```

Evaluation layers:

```text
Official Identity
↓
Primary Position Source
↓
Coordinate Traceability
↓
Visitor / Navigation Anchor Semantics
↓
Corroboration when required
↓
Human Position Adjudication
PASS / HOLD_POSITION_REVIEW
```

Rules:

1. Stored Production coordinates are observations, not proof of correctness.
2. Base Seed equality with Production is artifact synchronization only.
3. Shrine identity is established independently from coordinates.
4. Primary Position Source must identify the same real-world Shrine.
5. Adopted coordinates must be reproducible from the recorded Primary Source.
6. Coordinate deltas are observational evidence only; no fixed meter threshold yields PASS or HOLD.
7. Parking, office, trailhead, parcel/precinct centroid, or unrelated auxiliary points are not automatically Visitor / Navigation Anchors.
8. Corroboration is required when stored and current candidates conflict, multiple plausible POIs exist, or Anchor semantics are unclear.
9. Incomplete audit state is `NOT_ADJUDICATED`, not `HOLD_POSITION_REVIEW`.
10. `HOLD_POSITION_REVIEW` is used only after adjudication finds a blocking unresolved conflict.
11. This audit performs no Production DB, Base Seed, Candidate Master, Recommendation, Compass, or Ranking write.

## 3. Batch 1 Adjudication Status

| # | Shrine | Audit Status | Position Status |
| --- | --- | --- | --- |
| 01 | 明治神宮 | COMPLETE | PASS |
| 02 | 伏見稲荷大社 | COMPLETE | PASS |
| 03 | 伊勢神宮（内宮） | COMPLETE | PASS |
| 04 | 出雲大社 | COMPLETE | PASS |
| 05 | 春日大社 | COMPLETE | PASS |
| 06 | 太宰府天満宮 | IN_PROGRESS | NOT_ADJUDICATED |
| 07 | 熱田神宮 | IN_PROGRESS | NOT_ADJUDICATED |
| 08 | 宇佐神宮 | IN_PROGRESS | NOT_ADJUDICATED |
| 09 | 日光東照宮 | IN_PROGRESS | NOT_ADJUDICATED |
| 10 | 鶴岡八幡宮 | IN_PROGRESS | NOT_ADJUDICATED |

```text
BATCH_TARGETS   = 10
COMPLETE        = 5
PASS            = 5
HOLD            = 0
NOT_ADJUDICATED = 5
```

## 4. 出雲大社 — Completed Record

### 4.1 Identity

```text
production_shrine_id = 4
official_name = 出雲大社
official_address = 島根県出雲市大社町杵築東195
identity_status = SUPPORTED
```

### 4.2 Current Production Position

```text
latitude = 35.4016
longitude = 132.6853
place_ref_id = null
provenance = LEGACY_UNTRACED
```

The stored numeric value alone does not provide reconstructable Primary Position provenance under the current Position Contract.

### 4.3 Primary Position Source

```text
primary_source_type = map_provider_poi
primary_source_provider = Mapion
primary_source_url = https://www.mapion.co.jp/phonebook/M06005/32203/ILSP0000082374_ipclm/

primary_latitude = 35.40190463
primary_longitude = 132.68547534

retrieval_status = OK
entity_match = SAME
coordinate_precision_policy = PRESERVE_PRIMARY_SOURCE_PRECISION
```

The adopted coordinate preserves the exact coordinate precision exposed by the Primary Source.

### 4.4 Corroboration

```text
corroboration_source_type = independent_map_provider_poi
corroboration_source_provider = MapFan
corroboration_latitude = 35.4019047
corroboration_longitude = 132.6854754
corroboration_status = SATISFIED
```

Observed deltas:

```text
stored_vs_primary_delta_m ≈ 37.416
primary_vs_corroboration_delta_m ≈ 0.0095
```

The deltas are observational only and are not PASS thresholds.

### 4.5 Anchor Semantics

```text
anchor_type = SHRINE_POI / PRECINCT_CORE
anchor_semantics = CONFIRMED
```

The Primary Position is explainable as the representative Shrine / precinct-core point rather than an identified parking location or unrelated auxiliary facility.

The Shrine has multiple visitor-access elements. A future vehicle-specific navigation destination may therefore be modeled separately from the canonical Shrine Position.

### 4.6 Adjudication

```text
identity_match = SAME
coordinate_traceability = OK
anchor_semantics = CONFIRMED
corroboration_status = SATISFIED
blocking_conflict = NONE

POSITION_STATUS = PASS
ADOPTED_COORDINATE = 35.40190463, 132.68547534
```

### 4.7 Remediation Decision

```text
current_stored_coordinate = 35.4016, 132.6853
adopted_coordinate = 35.40190463, 132.68547534

remediation_decision = UPDATE_TO_ADOPTED_PRIMARY
production_write = NOT_YET_PERFORMED
base_seed_write = NOT_YET_PERFORMED
verified_at = 2026-09-21
```

This decision exists at the audit/adoption layer only. It does not assert that Production or Base Seed has already been modified.

## 5. 明治神宮 — Completed Record

### 5.1 Identity

```text
production_shrine_id = 1
official_name = 明治神宮
official_address = 東京都渋谷区代々木神園町1-1
identity_status = SUPPORTED
```

Official visitor information identifies the same Shrine and distinguishes the
canonical Shrine address from vehicle-specific navigation guidance.

### 5.2 Current Production Position

```text
latitude = 35.6764
longitude = 139.6993
place_ref_id = null
provenance = LEGACY_UNTRACED
```

The stored numeric value is not itself reconstructable from a recorded Primary
Position Source under the current Position Contract.

### 5.3 Primary Position Source

```text
primary_source_type = map_provider_poi
primary_source_provider = Mapion
primary_source_url = https://www.mapion.co.jp/phonebook/M06005/13113/ILSP0000081979_ipclm/

primary_latitude = 35.67623602
primary_longitude = 139.69934113

retrieval_status = OK
entity_match = SAME
coordinate_precision_policy = PRESERVE_PRIMARY_SOURCE_PRECISION
```

### 5.4 Corroboration

```text
corroboration_source_type = independent_map_provider_poi
corroboration_source_provider = MapFan
corroboration_latitude = 35.6762360
corroboration_longitude = 139.6993411
corroboration_status = SATISFIED
```

Observed deltas:

```text
stored_vs_primary_delta_m ≈ 18.608
primary_vs_corroboration_delta_m ≈ 0.004
```

These are observations, not PASS thresholds.

### 5.5 Anchor Semantics

```text
anchor_type = SHRINE_POI / PRECINCT_CORE
anchor_semantics = CONFIRMED

pedestrian_entry_anchor = SEPARATE_CONCEPT
vehicle_entry_anchor = SEPARATE_CONCEPT
parking_anchor = SEPARATE_CONCEPT
```

Official visitor guidance describes three pedestrian entrances and separately
directs vehicle access through the Yoyogi-side entrance. This supports treating
the canonical Shrine Position as a Shrine-level representative point rather
than equating it with a specific gate, parking area, or vehicle destination.

### 5.6 Adjudication

```text
identity_match = SAME
coordinate_traceability = OK
anchor_semantics = CONFIRMED
corroboration_status = SATISFIED
blocking_conflict = NONE_OBSERVED

POSITION_STATUS = PASS
ADOPTED_COORDINATE = 35.67623602, 139.69934113
```

### 5.7 Remediation Decision

```text
current_stored_coordinate = 35.6764, 139.6993
adopted_coordinate = 35.67623602, 139.69934113

remediation_decision = UPDATE_TO_ADOPTED_PRIMARY
production_write = NOT_YET_PERFORMED
base_seed_write = NOT_YET_PERFORMED
verified_at = 2026-09-21
```

The remediation decision is based on replacing a legacy-untraced stored value
with a traceable PASS-adjudicated Primary Position. The approximately 18.6 m
delta is not itself the reason for remediation.

## 6. 伏見稲荷大社 — Completed Record

### 6.1 Identity

```text
production_shrine_id = 2
official_name = 伏見稲荷大社
official_address = 京都市伏見区深草薮之内町68番地
identity_status = SUPPORTED
```

Production address "京都府京都市伏見区深草薮之内町68" is treated as the same
visitor-facing identity with an administrative-prefix / suffix notation difference.

### 6.2 Current Production Position

```text
latitude = 34.9671
longitude = 135.7727
place_ref_id = null
provenance = LEGACY_UNTRACED
```

The stored numeric value alone does not provide reconstructable Primary Position
provenance under the current Position Contract.

### 6.3 Primary Position Source

```text
primary_source_type = map_provider_poi
primary_source_provider = MapFan
primary_source_url = https://mapfan.com/directions/points/34.969276371576%2C135.76926894994%2C%E4%BC%8F%E8%A6%8B%E7%A8%B2%E8%8D%B7%E9%A7%85%EF%BC%88%E4%BA%AC%E9%98%AA%E6%9C%AC%E7%B7%9A%EF%BC%89%2CSCH%2CJ%2CIZ7%2C/34.967133624329%2C135.77318468005%2C%E4%BC%8F%E8%A6%8B%E7%A8%B2%E8%8D%B7%E5%A4%A7%E7%A4%BE%2CSC3W3%2CJ%2C6R%2C/types/walk/settings/now%2C4%2C101

primary_latitude = 34.967133624329
primary_longitude = 135.77318468005

retrieval_status = OK
entity_match = SAME
coordinate_precision_policy = PRESERVE_PRIMARY_SOURCE_PRECISION
```

Mapion was not adopted as Primary for this Shrine because multiple same-name /
auxiliary POIs were observed during evidence collection, making the candidate less
clear than the explicit MapFan Shrine destination.

### 6.4 Corroboration

```text
corroboration_source_type = independent_shrine_reference_database
corroboration_source_provider = 國學院大學デジタル・ミュージアム
corroboration_source_url = https://jmapps.ne.jp/kokugakuin/det.html?data_id=53356

corroboration_latitude = 34.967125
corroboration_longitude = 135.77310833333334
corroboration_status = SATISFIED
entity_match = SAME
```

Observed deltas:

```text
stored_vs_primary_delta_m ≈ 44.323
primary_vs_corroboration_delta_m ≈ 7.023
```

These are observations only and are not PASS thresholds.

### 6.5 Anchor Semantics

```text
anchor_type = SHRINE_POI / PRECINCT_CORE
anchor_semantics = CONFIRMED

station_access_point = SEPARATE_CONCEPT
parking_anchor = SEPARATE_CONCEPT
specific_gate_anchor = SEPARATE_CONCEPT
mountain_or_trail_route_point = SEPARATE_CONCEPT
```

The adopted candidate is an explicit Fushimi Inari Taisha Shrine destination and
is independently corroborated near the same precinct-core area. It is therefore
explainable as a Shrine-level Visitor / Navigation Anchor rather than a station,
parking location, specific gate, or mountain/trail route point.

### 6.6 Adjudication

```text
identity_match = SAME
coordinate_traceability = OK
anchor_semantics = CONFIRMED
corroboration_status = SATISFIED
blocking_conflict = NONE_OBSERVED

POSITION_STATUS = PASS
ADOPTED_COORDINATE = 34.967133624329, 135.77318468005
```

### 6.7 Remediation Decision

```text
current_stored_coordinate = 34.9671, 135.7727
adopted_coordinate = 34.967133624329, 135.77318468005

remediation_decision = UPDATE_TO_ADOPTED_PRIMARY
production_write = NOT_YET_PERFORMED
base_seed_write = NOT_YET_PERFORMED
verified_at = 2026-09-21
```

The remediation decision replaces a legacy-untraced stored coordinate with a
traceable PASS-adjudicated Primary Position. The approximately 44.3 m delta is
not itself the reason for remediation.

## 7. 伊勢神宮（内宮） — Completed Record

### 7.1 Identity

```text
production_shrine_id = 3
official_name = 伊勢神宮（内宮）
official_address = 三重県伊勢市宇治館町1
identity_status = SUPPORTED
```

The official access information identifies 皇大神宮（内宮） at the same address
recorded in Production.

### 7.2 Current Production Position

```text
latitude = 34.455
longitude = 136.7256
place_ref_id = null
provenance = LEGACY_UNTRACED
```

The stored numeric value alone does not provide reconstructable Primary Position
provenance under the current Position Contract.

### 7.3 Primary Position Source

```text
primary_source_type = map_provider_poi
primary_source_provider = MapFan

primary_latitude = 34.4549588
primary_longitude = 136.7251689

retrieval_status = OK
entity_match = SAME
coordinate_precision_policy = PRESERVE_PRIMARY_SOURCE_PRECISION
```

The Primary candidate is an explicit 伊勢神宮皇大神宮（内宮） Shrine POI.

### 7.4 Corroboration

```text
corroboration_source_type = independent_shrine_reference_database
corroboration_source_provider = 國學院大學 古典文化学事業

corroboration_latitude = 34.455111111111115
corroboration_longitude = 136.7258888888889
corroboration_status = SATISFIED
entity_match = SAME
```

Observed deltas:

```text
stored_vs_primary_delta_m ≈ 39.79
primary_vs_corroboration_delta_m ≈ 68.15
```

The approximately 68 m Primary/corroboration spread is explicitly recorded as an
observation. It does not itself create a PASS or HOLD threshold.

### 7.5 Anchor Semantics

```text
anchor_type = SHRINE_POI / PRECINCT_CORE
anchor_semantics = CONFIRMED

uji_bridge_entry_anchor = SEPARATE_CONCEPT
parking_anchor = SEPARATE_CONCEPT
shogu_building_anchor = SEPARATE_CONCEPT
```

The Inner Shrine is a large precinct with multiple meaningful visitor points.
The adopted candidate is treated as the Shrine-level representative POI, not as
an assertion that the same coordinate represents Uji Bridge, a parking facility,
or the Shogu building itself.

### 7.6 Adjudication

```text
identity_match = SAME
coordinate_traceability = OK
anchor_semantics = CONFIRMED
corroboration_status = SATISFIED
primary_vs_corroboration_spread = OBSERVED
blocking_conflict = NONE_OBSERVED

POSITION_STATUS = PASS
ADOPTED_COORDINATE = 34.4549588, 136.7251689
```

The corroboration spread does not block adoption because both sources identify the
same real-world Shrine and the differing coordinates are explainable within the
large precinct-level anchor semantics. No evidence collected so far establishes
that the Primary is a parking-only, gate-only, building-only, or unrelated point.

### 7.7 Remediation Decision

```text
current_stored_coordinate = 34.455, 136.7256
adopted_coordinate = 34.4549588, 136.7251689

remediation_decision = UPDATE_TO_ADOPTED_PRIMARY
production_write = NOT_YET_PERFORMED
base_seed_write = NOT_YET_PERFORMED
verified_at = 2026-09-21
```

The remediation decision replaces a legacy-untraced stored coordinate with the
traceable PASS-adjudicated Primary Position. The approximately 39.8 m stored /
Primary delta is not itself the reason for remediation.

## 8. 春日大社 — Completed Record

### 8.1 Identity

```text
production_shrine_id = 5
official_name = 春日大社
official_address = 奈良県奈良市春日野町160
identity_status = SUPPORTED
```

### 8.2 Current Production Position

```text
latitude = 34.6814
longitude = 135.8481
place_ref_id = null
provenance = LEGACY_UNTRACED
```

The stored numeric value alone does not provide reconstructable Primary Position
provenance under the current Position Contract.

### 8.3 Primary Position Source

```text
primary_source_type = map_provider_poi
primary_source_provider = MapFan
primary_source_url = https://mapfan.com/spots/SC3W3%2CJ%2CE1

primary_latitude = 34.6812901
primary_longitude = 135.8482531

retrieval_status = OK
entity_match = SAME
coordinate_precision_policy = PRESERVE_PRIMARY_SOURCE_PRECISION
```

The previously observed official short-link remained unresolved, so it was not
used as the coordinate-bearing Primary Position Source. The directly
reproducible MapFan Shrine POI was adopted as Primary instead.

### 8.4 Corroboration

```text
corroboration_source_type = independent_shrine_reference_database
corroboration_source_provider = 國學院大學デジタル・ミュージアム
corroboration_source_url = https://jmapps.ne.jp/kokugakuin/det.html?data_id=180677

corroboration_latitude = 34.681336
corroboration_longitude = 135.848348
corroboration_status = SATISFIED
entity_match = SAME
```

Observed deltas:

```text
stored_vs_primary_delta_m ≈ 18.58
primary_vs_corroboration_delta_m ≈ 10.07
```

These are observations only and are not PASS thresholds.

### 8.5 Anchor Semantics

```text
anchor_type = SHRINE_POI / PRECINCT_CORE
anchor_semantics = CONFIRMED

main_sanctuary_anchor = SEPARATE_CONCEPT
parking_anchor = SEPARATE_CONCEPT
bus_stop_anchor = SEPARATE_CONCEPT
museum_anchor = SEPARATE_CONCEPT
botanical_garden_anchor = SEPARATE_CONCEPT
```

The adopted candidate is an explicit Kasuga Taisha Shrine POI rather than an
identified parking area, bus stop, museum, botanical garden, or other auxiliary
facility. It is therefore explainable as a Shrine-level representative
Visitor / Navigation Anchor.

### 8.6 Adjudication

```text
identity_match = SAME
coordinate_traceability = OK
anchor_semantics = CONFIRMED
corroboration_status = SATISFIED
blocking_conflict = NONE_OBSERVED

POSITION_STATUS = PASS
ADOPTED_COORDINATE = 34.6812901, 135.8482531
```

The unresolved official short-link is not a blocking conflict because the
adopted coordinate is independently reproducible from the recorded Primary
Source and corroborated by a separate source for the same Shrine.

### 8.7 Remediation Decision

```text
current_stored_coordinate = 34.6814, 135.8481
adopted_coordinate = 34.6812901, 135.8482531

remediation_decision = NOT_YET_DECIDED
production_write = NOT_YET_PERFORMED
base_seed_write = NOT_YET_PERFORMED
verified_at = 2026-09-21
```

This completed Position adjudication does not itself authorize or perform
Production or Base Seed remediation.

## 9. Remaining Batch 1 Records

| # | Shrine | Official Identity | Primary Source Candidate | Primary Coordinate State | Anchor Semantics | Corroboration | Position |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 06 | 太宰府天満宮 | SUPPORTED | FOUND | ROUTE_LINK_FOUND_COORDINATE_NOT_RETRIEVED | NOT_YET_ADJUDICATED | NOT_YET_COMPLETED | NOT_ADJUDICATED |
| 07 | 熱田神宮 | SUPPORTED | FOUND | EMBED_CENTER_RETRIEVED | NOT_YET_ADJUDICATED | NOT_YET_COMPLETED | NOT_ADJUDICATED |
| 08 | 宇佐神宮 | SUPPORTED | FOUND | NOT_RETRIEVED | NOT_YET_ADJUDICATED | NOT_YET_COMPLETED | NOT_ADJUDICATED |
| 09 | 日光東照宮 | SUPPORTED | FOUND | NOT_RETRIEVED | NOT_YET_ADJUDICATED | NOT_YET_COMPLETED | NOT_ADJUDICATED |
| 10 | 鶴岡八幡宮 | SUPPORTED | FOUND | FETCH_INCOMPLETE | NOT_YET_ADJUDICATED | NOT_YET_COMPLETED | NOT_ADJUDICATED |

## 10. Remediation Candidates

| Shrine | Position Status | Remediation Decision | Production Write | Base Seed Write |
| --- | --- | --- | --- | --- |
| 出雲大社 | PASS | UPDATE_TO_ADOPTED_PRIMARY | PERFORMED | PERFORMED |
| 明治神宮 | PASS | UPDATE_TO_ADOPTED_PRIMARY | NOT_YET_PERFORMED | NOT_YET_PERFORMED |
| 伏見稲荷大社 | PASS | UPDATE_TO_ADOPTED_PRIMARY | PERFORMED | PERFORMED |
| 伊勢神宮（内宮） | PASS | UPDATE_TO_ADOPTED_PRIMARY | NOT_YET_PERFORMED | NOT_YET_PERFORMED |

The individual Remediation Decision blocks above preserve the state at the time
of adjudication. Current remediation execution state is recorded in this table
and in Section 11.

## 11. Post-audit Remediation Execution Record

This section records remediation executed after Position adjudication.

The original Production Snapshot and each Shrine's "Current Production Position"
remain unchanged because they represent the observed state at the time of audit.

### 11.1 出雲大社

```text
audit_status = COMPLETE
position_status = PASS
adopted_coordinate = 35.40190463, 132.68547534

production_remediation_pr = #2908
production_remediation_migration = temples.0109_adopt_izumo_taisha_position
production_write = PERFORMED
production_migration_status = APPLIED
production_post_check = PASS

base_seed_sync_pr = #2909
base_seed_write = PERFORMED
base_seed_coordinate = 35.40190463, 132.68547534

verified_at = 2026-09-21
```

Production read-only verification after migration confirmed:

```text
id = 4
name_jp = 出雲大社
address = 島根県出雲市大社町杵築東195
latitude = 35.40190463
longitude = 132.68547534
```

No Shrine identity or address change was performed.

### 11.2 伏見稲荷大社

```text
audit_status = COMPLETE
position_status = PASS
adopted_coordinate = 34.967133624329, 135.77318468005

production_remediation_pr = #2913
production_remediation_migration = temples.0110_adopt_fushimi_inari_position
production_write = PERFORMED
production_migration_status = APPLIED
production_post_check = PASS

base_seed_sync_pr = #2915
base_seed_write = PERFORMED
base_seed_coordinate = 34.967133624329, 135.77318468005

verified_at = 2026-09-21
```

Production read-only verification after migration confirmed:

```text
id = 2
name_jp = 伏見稲荷大社
address = 京都府京都市伏見区深草薮之内町68
latitude = 34.967133624329
longitude = 135.77318468005
```

No Shrine identity or address change was performed.

### 11.3 Remediation State

```text
remediation_candidates = 4
production_remediation_completed = 2
base_seed_sync_completed = 2

completed:
- 出雲大社
- 伏見稲荷大社

not_yet_remediated:
- 明治神宮
- 伊勢神宮（内宮）
```

Remediation completion does not change the Batch adjudication count.

```text
COMPLETE = 5/10
PASS = 5
HOLD_POSITION_REVIEW = 0
NOT_ADJUDICATED = 5
```

## 12. Non-Goals

The Batch adjudication itself does not:

- write Production DB;
- modify Base Seed;
- create or modify migrations;
- alter Recommendation / Ranking / Concierge / Compass logic;
- define a fixed coordinate-distance PASS threshold;
- treat an unfinished audit as HOLD;
- infer missing evidence.

Post-audit remediation is a separate execution phase and is recorded in
Section 11.

## 13. STOP

Current Batch 1 state:

```text
COMPLETE = 4/10
PASS = 4
HOLD_POSITION_REVIEW = 0
NOT_ADJUDICATED = 6
```

Continue remaining Shrines under the same Position Contract and record format.
