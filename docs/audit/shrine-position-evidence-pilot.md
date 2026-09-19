# Shrine Position Evidence Pilot

## Status

```text
STATUS = ACTIVE
PHASE = PHASE_1_EVIDENCE_COLLECTION
WRITE_PATH = NONE
COORDINATE_REMEDIATION = NOT_IN_SCOPE
```

This document records the 20-Shrine Primary Position Evidence Pilot.

The objective is to collect Position evidence for all Pilot Shrines using one fixed procedure and one fixed schema.

This document does not redefine Position policy.

---

## 1. Authority

Canonical Position meaning and adoption rules remain defined by:

```text
docs/knowledge/shrine-position-contract.md
```

Machine-verifiability triage remains defined by:

```text
docs/audit/shrine-position-ground-truth-v2.md
scripts/audit_shrine_positions_v2.py
```

Evidence-collection procedure remains defined by:

```text
docs/audit/shrine-coordinate-data-flow.md
§8.2 Primary Position Evidence Collection Procedure
```

This Pilot must not weaken, reinterpret, or replace those contracts.

---

## 2. Scope

This Pilot collects evidence for exactly 20 Shrines.

The Pilot evaluates:

* official Shrine identity
* visitor-facing official address
* existing repository Position records
* Primary Position Source candidates
* source entity identity
* coordinate traceability
* Visitor / Navigation Anchor meaning
* required corroboration
* provider role
* observational coordinate deltas

This Pilot does not:

* modify Base Seed
* modify Candidate Master
* modify Production DB
* modify migrations
* change Recommendation logic
* change Compass logic
* change Ranking logic
* automatically adopt coordinates
* introduce fixed meter thresholds
* infer missing evidence
* convert machine audit results directly into canonical Position decisions

Evidence collection is read-only.

---

## 3. Layer Separation

The following layers remain separate.

```text
Human Evidence Collection
↓
Primary Position Evidence Record
↓
Position Audit v2
AUTO_PASS / REVIEW / HOLD
↓
Human Position adjudication
PASS / HOLD_POSITION_REVIEW
```

Evidence collection does not itself produce canonical `PASS`.

Machine `REVIEW` does not mean that a Position is incorrect.

Machine `AUTO_PASS` and canonical `PASS` are not interchangeable.

---

## 4. Pilot Population

The Pilot contains exactly 20 Shrines.

```text
LEGACY_UNTRACED                       14
KNOWN CORRECTION / DRIFT CONTROL       2
WAVE0 POSITION CONTROL                 4
────────────────────────────────────────
TOTAL                                 20
```

### 4.1 LEGACY_UNTRACED

| #  | Shrine     | Stratum         |
| -- | ---------- | --------------- |
| 1  | 神田神社（神田明神） | URBAN_COMPACT   |
| 2  | 生田神社       | URBAN_COMPACT   |
| 3  | 千葉神社       | URBAN_COMPACT   |
| 4  | 住吉神社（博多）   | URBAN_COMPACT   |
| 5  | 伊勢神宮（内宮）   | LARGE_PRECINCT  |
| 6  | 伏見稲荷大社     | LARGE_PRECINCT  |
| 7  | 鹿島神宮       | LARGE_PRECINCT  |
| 8  | 宇佐神宮       | LARGE_PRECINCT  |
| 9  | 三峯神社       | MOUNTAIN_FOREST |
| 10 | 金刀比羅宮      | MOUNTAIN_FOREST |
| 11 | 貴船神社       | MOUNTAIN_FOREST |
| 12 | 厳島神社       | COAST_WATER     |
| 13 | 江島神社       | COAST_WATER     |
| 14 | 彌彦神社       | STANDARD_MIXED  |

### 4.2 Known Correction / Drift Controls

| #  | Shrine  | Pilot role                       |
| -- | ------- | -------------------------------- |
| 15 | 多摩川浅間神社 | KNOWN_CORRECTED                  |
| 16 | 富岡八幡宮   | KNOWN_CORRECTION_WITH_SEED_DRIFT |

### 4.3 Wave0 Position Controls

| #  | Candidate   | Shrine | Pilot role    |
| -- | ----------- | ------ | ------------- |
| 17 | `wave0-003` | 御岩神社   | WAVE0_CONTROL |
| 18 | `wave0-007` | 射水神社   | WAVE0_CONTROL |
| 19 | `wave0-010` | 札幌諏訪神社 | WAVE0_CONTROL |
| 20 | `wave0-002` | 大鳥大社   | WAVE0_CONTROL |

The Pilot population must not be changed during evidence collection without a separate audit decision.

---

## 5. Collection Rules

The same procedure must be applied to all 20 Shrines.

### 5.1 Identity

Record:

```text
official_name
official_address
identity_source_url
candidate_id
```

Do not infer identity from coordinates alone.

Do not use fuzzy name similarity to merge Shrines.

Do not automatically replace visitor-facing addresses with legal or registered-office addresses.

---

### 5.2 Existing Position Record

Check repository-controlled Position evidence before external research.

Possible sources include:

```text
Position Resolution Record
Source Packet Freeze
Candidate Master
previous coordinate correction audit
```

Record the role as:

```text
CURRENT_ADOPTED_RECORD
HISTORICAL_RECORD
NONE
```

Historical records must not automatically override current external evidence.

---

### 5.3 Primary Position Source

Eligible Primary Position Source candidates may include:

* Shrine-official navigation / access map
* map provider directly linked by the Shrine official site
* municipality / prefecture / Shrine-authority visitor-facing map
* current map-provider POI identifying the same Shrine
* other current public or quasi-public position material consistent with Shrine identity

No absolute source ranking is introduced.

Source type alone does not determine adoption.

For every candidate source, verify:

```text
same Shrine entity?
coordinate traceable?
Visitor / Navigation Anchor meaning explainable?
```

---

### 5.4 Human Discovery vs Machine Retrieval

Human research may identify a Primary Position Source URL for legacy Shrines.

Machine audit must not:

* invent replacement URLs
* perform broad search-engine discovery
* infer coordinates from addresses
* substitute another provider silently
* average coordinates
* approximate coordinates visually

Human discovery and machine verification remain separate responsibilities.

---

### 5.5 Entity Match

Use only the existing Position Audit v2 vocabulary.

```text
SAME
DIFFERENT
NON_SHRINE
AMBIGUOUS
```

Definitions:

```text
SAME
= evidence supports the same Shrine identity

DIFFERENT
= source represents another real-world entity

NON_SHRINE
= source represents a parking lot, station, office,
  trailhead, mountain area, unrelated facility, etc.

AMBIGUOUS
= available evidence cannot deterministically establish identity
```

Missing identity evidence is not `SAME`.

---

### 5.6 Coordinate Traceability

Record:

```text
primary_source_type
primary_source_url
primary_source_name
primary_source_address
primary_latitude
primary_longitude
primary_verified_at
```

The coordinate must be deterministically reproducible from the recorded source.

Do not derive it through:

* visual approximation
* address centroid
* interpolation
* coordinate averaging
* nearby landmark substitution

If the coordinate cannot be traced, preserve the uncertainty.

---

### 5.7 Visitor / Navigation Anchor

The Primary Position candidate must be interpretable as a Visitor / Navigation Anchor.

Do not automatically use:

* parking lot
* shrine office
* trailhead
* precinct centroid
* mountain centroid
* registered office
* arbitrary parcel point

Record:

```text
entry_status
anchor_complexity
multi_site_status
visitor_flow_note
navigation_risk_note
```

Anchor complexity is an audit observation only.

It does not determine `PASS` or `HOLD_POSITION_REVIEW`.

---

### 5.8 Corroboration

Independent corroboration is collected when needed.

Typical triggers:

* existing and current coordinates conflict
* addresses conflict
* multiple plausible POIs exist
* Shrine identity is difficult to distinguish
* Visitor Anchor meaning is not self-evident

Possible corroboration:

```text
other map provider
OSM
Wikidata
public visitor map
other independent current source
```

Corroboration must not silently replace the Primary Position Source.

OSM / Wikidata alone must not be promoted to canonical Primary where stronger evidence is required.

---

### 5.9 Provider Role

A map-provider POI may be:

```text
PRIMARY
CORROBORATION
```

The provider name does not determine its role.

Record:

```text
provider
provider_role
provider_poi_url
provider_latitude
provider_longitude
provider_plus_code
```

Plus Code is supplemental evidence only.

---

### 5.10 Retrieval Status

Use only the existing Position Audit v2 retrieval vocabulary.

```text
OK
NOT_RETRIEVED
FETCH_FAILED
PARSE_FAILED
REDIRECTED
```

Do not create a parallel status taxonomy.

---

### 5.11 Coordinate Delta

Observational delta fields:

```text
stored_vs_primary_delta_m
stored_vs_provider_delta_m
primary_vs_corroboration_delta_m
```

Distance is evidence only.

No fixed meter threshold determines:

```text
AUTO_PASS
REVIEW
HOLD
```

or:

```text
PASS
HOLD_POSITION_REVIEW
```

A small distance does not prove validity.

A large distance does not independently prove invalidity.

---

## 6. Collection Schema

Each Shrine must use exactly the following schema.

```text
pilot_no
pilot_group
candidate_id

official_name
official_address
identity_source_url

stored_latitude
stored_longitude
stored_coordinate_artifact

existing_position_record
existing_position_record_role

primary_source_type
primary_source_url
primary_source_name
primary_source_address
primary_latitude
primary_longitude
primary_verified_at

retrieval_status
entity_match

entry_status
anchor_complexity
multi_site_status
visitor_flow_note
navigation_risk_note

corroboration_required
corroboration_source_type
corroboration_source_url
corroboration_latitude
corroboration_longitude

provider
provider_role
provider_poi_url
provider_latitude
provider_longitude
provider_plus_code

stored_vs_primary_delta_m
stored_vs_provider_delta_m
primary_vs_corroboration_delta_m

evidence_collected_at
notes
```

Unknown evidence must remain:

```text
NOT_RETRIEVED
```

where applicable.

Unknown values must never be converted into inferred evidence.

---

## 7. Initial Stored Coordinate Snapshot

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

This snapshot is the comparison baseline for the Pilot.

It is not a declaration that the stored coordinate is correct.

---

## 8. Evidence Records

All 20 records must follow the same schema.

Do not remove fields from individual Shrine records.

Do not add Shrine-specific fields unless the common schema is formally revised first.

---

### 8.1 Pilot 01 — 神田神社（神田明神）

```text
pilot_no = 01
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 神田神社
official_address = 東京都千代田区外神田2-16-2
identity_source_url = https://www.kandamyoujin.or.jp/access/

stored_latitude = 35.7019
stored_longitude = 139.7674
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = shrine_official_linked_google_place
primary_source_url = NOT_RETRIEVED
primary_source_name = 江戸総鎮守 神田明神（神田神社）
primary_source_address = 東京都千代田区外神田2-16-2
primary_latitude = 35.7019218
primary_longitude = 139.7678456
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = MULTI_CONFIRMED
anchor_complexity = MEDIUM
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式アクセスページは御茶ノ水・秋葉原等からの参拝導線を案内し、Google Maps上の神田明神（神田神社）POIへ直接接続する
navigation_risk_note = 複数の徒歩アプローチは存在するが、Primary POIは神社本体entityを示している

corroboration_required = YES 
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q717682
corroboration_latitude = 35.70193889
corroboration_longitude = 139.76778056

provider = Google Maps
provider_role = PRIMARY
provider_poi_url = NOT_RETRIEVED
provider_latitude = 35.7019218
provider_longitude = 139.7678456
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 40.31
stored_vs_provider_delta_m = 40.31
primary_vs_corroboration_delta_m = 6.17

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master record was found for this legacy Shrine. The legacy stored coordinate is present in repository Seed artifacts but does not provide current adopted Position provenance. The traceable Primary coordinate differs from the legacy stored coordinate by approximately 40.31 m. Wikidata independently identifies the same Kanda Shrine / Kanda-myojin entity and reports a coordinate approximately 6.17 m from the Primary coordinate. Distance values are observational only and are not used as PASS/HOLD thresholds.
```

---

### 8.2 Pilot 02 — 生田神社


```text
pilot_no = 02
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 生田神社
official_address = 兵庫県神戸市中央区下山手通1丁目2-1
identity_source_url = https://ikutajinja.or.jp/access

stored_latitude = 34.694
stored_longitude = 135.1923
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = map_provider_poi
primary_source_url = https://mapfan.com/spots/SC3W3%2CJ%2CU4
primary_source_name = 生田神社
primary_source_address = 兵庫県神戸市中央区下山手通1丁目2-1
primary_latitude = 34.6948193
primary_longitude = 135.1906845
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = LOW
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式アクセスページは三宮各駅から徒歩での参拝導線を案内している
navigation_risk_note = 同名の生田神社が他地域にも存在するため、name-only identity joinは禁止

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q710086
corroboration_latitude = 34.69480556
corroboration_longitude = 135.19069444

provider = MapFan
provider_role = PRIMARY
provider_poi_url = https://mapfan.com/spots/SC3W3%2CJ%2CU4
provider_latitude = 34.6948193
provider_longitude = 135.1906845
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 173.53
stored_vs_provider_delta_m = 173.53
primary_vs_corroboration_delta_m = 1.78

evidence_collected_at = 2026-09-19

notes = No dedicated Position Resolution Record / Source Packet / Candidate Master record was found for this legacy Shrine. Current MapFan POI identifies the same Ikuta Shrine entity and reports 34.6948193, 135.1906845. The legacy stored coordinate differs from this Primary coordinate by approximately 173.53 m. Wikidata independently identifies the same Kobe Ikuta Shrine at 34.69480556, 135.19069444, approximately 1.78 m from the Primary coordinate. Distance values are observational only and are not used as PASS/HOLD thresholds.

```
### 8.3 Pilot 03 — 千葉神社

```text
pilot_no = 03
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 千葉神社
official_address = 千葉県千葉市中央区院内1-16-1
identity_source_url = https://www.chibajinja.com/

stored_latitude = 35.6114
stored_longitude = 140.1246
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = map_provider_poi
primary_source_url = https://mapfan.com/spots/SAYC%2CJ%2CKUQS0
primary_source_name = 千葉神社
primary_source_address = 千葉県千葉市中央区院内1-16-1
primary_latitude = 35.6118663
primary_longitude = 140.1237354
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = MEDIUM
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式案内はJR千葉駅・京成千葉駅から徒歩約10分の参拝導線を示している
navigation_risk_note = 境内施設は複数存在するため、代表POIと個別施設を混同しない

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q11406700
corroboration_latitude = 35.611806
corroboration_longitude = 140.123833

provider = MapFan
provider_role = PRIMARY
provider_poi_url = https://mapfan.com/spots/SAYC%2CJ%2CKUQS0
provider_latitude = 35.6118663
provider_longitude = 140.1237354
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 93.79
stored_vs_provider_delta_m = 93.79
primary_vs_corroboration_delta_m = 11.08

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master record was found for this legacy Shrine. The current MapFan POI identifies the same Chiba Shrine entity at 35.6118663, 140.1237354. Wikidata independently identifies the same Shrine and official address at 35.611806, 140.123833, approximately 11.08 m from the Primary coordinate. The legacy stored coordinate differs from the Primary coordinate by approximately 93.79 m. Distance values are observational only and are not used as PASS/HOLD thresholds.
```
### 8.4 Pilot 04 — 住吉神社（博多）

```text
pilot_no = 04
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 住吉神社
official_address = 福岡県福岡市博多区住吉3丁目1-51
identity_source_url = https://www.nihondaiichisumiyoshigu.jp/access/

stored_latitude = 33.587
stored_longitude = 130.4086
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = shrine_official_linked_google_place
primary_source_url = https://maps.google.com/maps?cid=1353508457548761201&gl=JP&hl=ja&ll=33.585919%2C130.413737&mapclient=embed&t=m&z=16
primary_source_name = 筑前國一之宮 住吉神社
primary_source_address = 福岡市博多区住吉3丁目1-51
primary_latitude = 33.585919
primary_longitude = 130.413737
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = MEDIUM
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式アクセスページはJR・地下鉄博多駅から徒歩約8分、西鉄バス住吉から徒歩約2分の参拝導線を案内し、Google Mapsへ直接リンクする
navigation_risk_note = 境内には本殿・能楽殿・駐車場等の複数施設があるため、個別施設をShrine代表点と混同しない

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q29682
corroboration_latitude = 33.5857500
corroboration_longitude = 130.4137500

provider = Google Maps
provider_role = PRIMARY
provider_poi_url = https://maps.google.com/maps?cid=1353508457548761201&gl=JP&hl=ja&ll=33.585919%2C130.413737&mapclient=embed&t=m&z=16
provider_latitude = 33.585919
provider_longitude = 130.413737
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 490.79
stored_vs_provider_delta_m = 490.79
primary_vs_corroboration_delta_m = 18.83

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master record was found for this legacy Shrine. The official Sumiyoshi Shrine access page confirms the visitor-facing identity and address and directly links to Google Maps with a traceable coordinate of 33.585919, 130.413737. Wikidata independently identifies the same Fukuoka Sumiyoshi Shrine at 33.5857500, 130.4137500, approximately 18.83 m from the Primary coordinate. The legacy stored coordinate differs from the Primary coordinate by approximately 490.79 m. Distance values are observational only and are not used as PASS/HOLD thresholds.
```
### 8.5 Pilot 05 — 伊勢神宮（内宮）

```text
pilot_no = 05
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 皇大神宮（内宮）
official_address = 三重県伊勢市宇治館町1
identity_source_url = https://www.isejingu.or.jp/access/

stored_latitude = 34.455
stored_longitude = 136.7256
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = map_provider_poi
primary_source_url = https://mapfan.com/spots/SC3W3%2CJ%2CEE
primary_source_name = 伊勢神宮皇大神宮（内宮）
primary_source_address = 三重県伊勢市宇治館町1
primary_latitude = 34.4549588
primary_longitude = 136.7251689
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = SINGLE_CONFIRMED
anchor_complexity = HIGH
multi_site_status = MULTI_SITE
visitor_flow_note = 公式アクセスページは皇大神宮（内宮）を独立した参拝先として案内し、所在地とGoogle Maps導線を提供する
navigation_risk_note = 伊勢神宮全体・内宮・外宮・宇治橋・正宮・駐車場等を同一Positionとして混同しない。大規模境内のため代表点の意味を明示する必要がある

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q687168
corroboration_latitude = 34.4550000
corroboration_longitude = 136.7258330

provider = MapFan
provider_role = PRIMARY
provider_poi_url = https://mapfan.com/spots/SC3W3%2CJ%2CEE
provider_latitude = 34.4549588
provider_longitude = 136.7251689
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 39.79
stored_vs_provider_delta_m = 39.79
primary_vs_corroboration_delta_m = 61.06

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master record was found for this legacy Shrine. The official Ise Jingu access page confirms Kōtai Jingū (Naikū) at Uji-tachi-cho 1. MapFan identifies the same Naikū entity at 34.4549588, 136.7251689. Wikidata identifies the broader Ise Jingū entity at approximately 34.4550000, 136.7258330 and is used only as corroboration because it does not isolate Naikū as precisely as the Primary POI. Distance values are observational only and are not used as PASS/HOLD thresholds.
```
### 8.6 Pilot 06 — 伏見稲荷大社

```text
pilot_no = 06
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 伏見稲荷大社
official_address = 京都府京都市伏見区深草薮之内町68番地
identity_source_url = https://inari.jp/access/

stored_latitude = 34.9671
stored_longitude = 135.7727
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = map_provider_poi
primary_source_url = NOT_RETRIEVED
primary_source_name = 伏見稲荷大社
primary_source_address = 京都府京都市伏見区深草薮之内町68
primary_latitude = 34.9671402
primary_longitude = 135.7726717
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = HIGH
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式アクセスページはJR奈良線稲荷駅から徒歩直ぐ、京阪本線伏見稲荷駅から東へ徒歩5分の参拝導線を案内している
navigation_risk_note = 稲荷山を含む大規模境内であり、伏見稲荷大社本体・千本鳥居・奥社奉拝所・山内社・駐車場等の個別POIをShrine代表Positionと混同しない

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q714828
corroboration_latitude = 34.967202
corroboration_longitude = 135.773386

provider = Google Maps
provider_role = PRIMARY
provider_poi_url = NOT_RETRIEVED
provider_latitude = 34.9671402
provider_longitude = 135.7726717
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 5.16
stored_vs_provider_delta_m = 5.16
primary_vs_corroboration_delta_m = 65.45

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master Position record was found for this legacy Shrine. The official access page confirms Fushimi Inari Taisha at Fukakusa Yabunouchi-cho 68 and provides visitor access from JR Inari and Keihan Fushimi-Inari stations. The current Google Maps POI identifies the same Shrine and reports a coordinate of 34.9671402, 135.7726717. Wikidata independently identifies the same Shrine at 34.967202, 135.773386. The legacy stored coordinate is approximately 5.16 m from the Primary coordinate, while Primary and corroboration differ by approximately 65.45 m. Because this is a large mountainside precinct with many subordinate POIs, coordinate distance alone does not determine Position validity.
```
### 8.7 Pilot 07 — 鹿島神宮

```text
pilot_no = 07
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 鹿島神宮
official_address = 茨城県鹿嶋市宮中2306-1
identity_source_url = https://kashimajingu.jp/info/アクセス・駐車場/

stored_latitude = 35.9658
stored_longitude = 140.6285
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = map_provider_poi
primary_source_url = https://mapfan.com/spots/SC3W3%2CJ%2CE
primary_source_name = 鹿島神宮
primary_source_address = 茨城県鹿嶋市宮中2306-1
primary_latitude = 35.9691243
primary_longitude = 140.6310373
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = HIGH
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式アクセス情報は表参道・大鳥居側の参拝導線と複数の駐車場を区別して案内している。旧entry_status = MULTI_CANDIDATE
navigation_risk_note = 鹿島神宮本体・社務所・駐車場・楼門・御手洗池等の個別POIを代表Positionと混同しない。大規模境内のため代表点の意味を明示する必要がある

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q706499
corroboration_latitude = 35.96880556
corroboration_longitude = 140.63150000

provider = MapFan
provider_role = PRIMARY
provider_poi_url = https://mapfan.com/spots/SC3W3%2CJ%2CE
provider_latitude = 35.9691243
provider_longitude = 140.6310373
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 434.49
stored_vs_provider_delta_m = 434.49
primary_vs_corroboration_delta_m = 54.68

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master Position record was found for this legacy Shrine. The official Kashima Jingu access page confirms the Shrine identity and address and separately identifies visitor parking, reducing the risk of treating parking as the Shrine Position. MapFan identifies Kashima Jingu itself at 35.9691243, 140.6310373. Wikidata independently identifies the same Shrine at 35.96880556, 140.63150000. The legacy stored coordinate differs from the Primary coordinate by approximately 434.49 m, while Primary and corroboration differ by approximately 54.68 m. Distance values are observational only and are not used as PASS/HOLD thresholds.
```
### 8.8 Pilot 08 — 宇佐神宮

```text
pilot_no = 08
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 宇佐神宮
official_address = 大分県宇佐市南宇佐2859
identity_source_url = https://www.usajinguu.com/

stored_latitude = 33.531
stored_longitude = 131.379
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = public_shrine_database
primary_source_url = https://kojiki.kokugakuin.ac.jp/jinjya/usajingu/
primary_source_name = 宇佐神宮
primary_source_address = 大分県宇佐市南宇佐2859
primary_latitude = 33.52602778
primary_longitude = 131.37469444
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = HIGH
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 宇佐神宮は大規模境内を持ち、上宮・下宮・表参道等を含む複数の参拝動線が存在する
navigation_risk_note = 宇佐神宮本体・上宮・下宮・宝物館・表参道駐車場等の個別POIを代表Positionと混同しない

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q715632
corroboration_latitude = 33.52600000
corroboration_longitude = 131.37461111

provider = Kokugakuin University Shrine Database
provider_role = PRIMARY
provider_poi_url = https://kojiki.kokugakuin.ac.jp/jinjya/usajingu/
provider_latitude = 33.52602778
provider_longitude = 131.37469444
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 681.88
stored_vs_provider_delta_m = 681.88
primary_vs_corroboration_delta_m = 8.32

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master Position record was found for this legacy Shrine. The current Kokugakuin University Shrine Database identifies Usa Jingu at Minamiusa 2859 and reports 33.52602778, 131.37469444. Wikidata independently identifies the same Shrine at 33.52600000, 131.37461111, approximately 8.32 m from the Primary coordinate. The legacy stored coordinate differs from the Primary coordinate by approximately 681.88 m. Because Usa Jingu has a large precinct with multiple visitor POIs, coordinate distance alone does not determine Position validity.
```
### 8.9 Pilot 09 — 三峯神社

```text
pilot_no = 09
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 三峯神社
official_address = 埼玉県秩父市三峰298-1
identity_source_url = https://www.mitsuminejinja.or.jp/

stored_latitude = 35.9221
stored_longitude = 138.9336
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = map_provider_poi
primary_source_url = https://mapfan.com/spots/SC3W3%2CJ%2C8
primary_source_name = 三峯神社
primary_source_address = 埼玉県秩父市三峰298-1
primary_latitude = 35.9253985
primary_longitude = 138.9304005
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = HIGH
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 山岳境内への主要参拝導線は三峯神社本体へ集約されるが、周辺に複数の施設・山岳POIが存在する
navigation_risk_note = 三峯神社本体・奥宮・駐車場・興雲閣・登山口等を代表Positionと混同しない。同名の三峯神社も他地域に存在するためname-only joinは禁止

corroboration_required = YES
corroboration_source_type = kokugakuin_university_shrine_database
corroboration_source_url = https://jmapps.ne.jp/kokugakuin/det.html?data_id=53762
corroboration_latitude = 35.92534611
corroboration_longitude = 138.93045806

provider = MapFan
provider_role = PRIMARY
provider_poi_url = https://mapfan.com/spots/SC3W3%2CJ%2C8
provider_latitude = 35.9253985
provider_longitude = 138.9304005
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 466.40
stored_vs_provider_delta_m = 466.40
primary_vs_corroboration_delta_m = 7.80

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master Position record was found for this legacy Shrine. The official Shrine site confirms the Chichibu Mitsumine Shrine identity and address. MapFan identifies the same Shrine at 35.9253985, 138.9304005. Kokugakuin University independently identifies the same Shrine and links the official site, reporting 35.92534611, 138.93045806, approximately 7.80 m from the Primary coordinate. The legacy stored coordinate differs from the Primary coordinate by approximately 466.40 m. Because this is a mountain Shrine with multiple nearby visitor and mountain-related POIs, coordinate distance alone does not determine Position validity.
```

### 8.10 Pilot 10 — 金刀比羅宮

```text
pilot_no = 10
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 金刀比羅宮
official_address = 香川県仲多度郡琴平町892-1
identity_source_url = https://www.konpira.or.jp/

stored_latitude = 34.1811
stored_longitude = 133.8216
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = map_provider_poi
primary_source_url = https://mapfan.com/spots/SC3W3%2CJ%2CQ2
primary_source_name = 金刀比羅宮
primary_source_address = 香川県仲多度郡琴平町892-1
primary_latitude = 34.183994
primary_longitude = 133.809418
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = HIGH
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式案内では門前町から御本宮まで785段の石段を徒歩で参拝し、奥社は1,368段目に位置する。境内に一般参拝者向け駐車場はなく、町内駐車場から徒歩参拝する
navigation_risk_note = 金刀比羅宮本体・御本宮・奥社・社務所・神椿駐車場・参道入口等を代表Positionと混同しない。公式サイト自身が、自動車ナビで「金刀比羅宮」を指定すると一般車両通行禁止道路へ案内される可能性を警告している

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q94760
corroboration_latitude = 34.184258
corroboration_longitude = 133.809614

provider = MapFan
provider_role = PRIMARY
provider_poi_url = https://mapfan.com/spots/SC3W3%2CJ%2CQ2
provider_latitude = 34.183994
provider_longitude = 133.809418
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 1165.87
stored_vs_provider_delta_m = 1165.87
primary_vs_corroboration_delta_m = 34.45

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master Position record was found for this legacy Shrine. The official site confirms Kotohira-gu at Kagawa-ken Nakatado-gun Kotohira-cho 892-1 and describes a long pedestrian approach to the Main Sanctuary and Inner Shrine. MapFan identifies the same Kotohira-gu entity at 34.183994, 133.809418. Wikidata independently identifies the same Shrine at 34.184258, 133.809614, approximately 34.45 m from the Primary coordinate. The legacy stored coordinate differs from the Primary coordinate by approximately 1165.87 m. Because the precinct and approach span a large mountainside area and the official site explicitly warns against using the Shrine itself as an automobile navigation destination, coordinate distance alone does not determine Position validity.
```

### 8.11 Pilot 11 — 貴船神社

```text
pilot_no = 11
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 貴船神社
official_address = 京都府京都市左京区鞍馬貴船町180
identity_source_url = https://kifunejinja.jp/

stored_latitude = 35.1217
stored_longitude = 135.762
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = map_provider_poi
primary_source_url = https://mapfan.com/spots/SCAQC%2CJ%2C3TWPH0
primary_source_name = 貴船神社
primary_source_address = 京都府京都市左京区鞍馬貴船町180
primary_latitude = 35.1216434
primary_longitude = 135.7628869
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = MULTI_SITE
anchor_complexity = HIGH
multi_site_status = MULTI_SITE
visitor_flow_note = 公式サイトは本宮・結社・奥宮を三社詣として案内し、最寄りの京都バス「貴船」停留所から本宮まで徒歩約5分としている
navigation_risk_note = 貴船神社本宮・結社・奥宮・本宮駐車場・奥宮駐車場を同一POIとして扱わない。同名の貴船神社が全国に存在するためname-only identity joinは禁止

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q276779
corroboration_latitude = 35.121733
corroboration_longitude = 135.762988

provider = MapFan
provider_role = PRIMARY
provider_poi_url = https://mapfan.com/spots/SCAQC%2CJ%2C3TWPH0
provider_latitude = 35.1216434
provider_longitude = 135.7628869
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 80.91
stored_vs_provider_delta_m = 80.91
primary_vs_corroboration_delta_m = 13.56

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master Position record was found for this legacy Shrine. The official Kifune Shrine site confirms the Kyoto identity and address and explicitly defines the Shrine as a three-site pilgrimage consisting of Hongu, Yui-no-Yashiro, and Okumiya. MapFan identifies the Kyoto Kifune Shrine at 35.1216434, 135.7628869. Wikidata independently identifies the same Kyoto Shrine at 35.121733, 135.762988, approximately 13.56 m from the Primary coordinate. The legacy stored coordinate differs from the Primary coordinate by approximately 80.91 m. Because Kifune Shrine is a multi-site Shrine, coordinate distance alone does not determine Position validity.
```

### 8.12 Pilot 12 — 厳島神社

```text
pilot_no = 12
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 嚴島神社
official_address = 広島県廿日市市宮島町1-1
identity_source_url = https://www.itsukushimajinja.jp/jp/access.html

stored_latitude = 34.2959
stored_longitude = 132.3199
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = map_provider_poi
primary_source_url = https://mapfan.com/spots/SCAHW%2CJ%2C0
primary_source_name = 厳島神社
primary_source_address = 広島県廿日市市宮島町1-1
primary_latitude = 34.2959214
primary_longitude = 132.3198133
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = MEDIUM
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式アクセスでは宮島口からフェリーで宮島桟橋へ渡り、徒歩で神社入口へ向かう単一の主要参拝導線を案内している。公式参拝順路では入口から御本社を経て出口へ進む。旧entry_status = SINGLE_ROUTE
navigation_risk_note = 厳島神社本体・大鳥居・宮島桟橋・宝物館・境外摂末社を代表Positionとして混同しない。神社専用駐車場はなく、自動車で神社本体へ直接到達する前提ではない

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q191763
corroboration_latitude = 34.29580556
corroboration_longitude = 132.32011111

provider = MapFan
provider_role = PRIMARY
provider_poi_url = https://mapfan.com/spots/SCAHW%2CJ%2C0
provider_latitude = 34.2959214
provider_longitude = 132.3198133
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 8.31
stored_vs_provider_delta_m = 8.31
primary_vs_corroboration_delta_m = 30.24

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master Position record was found for this legacy Shrine. The official Itsukushima Shrine site confirms the Shrine identity and address at Miyajima-cho 1-1 and defines a visitor route from Miyajima Pier to the Shrine entrance. MapFan identifies the same Shrine at 34.2959214, 132.3198133. Wikidata independently identifies the same Itsukushima Shrine at 34.29580556, 132.32011111, approximately 30.24 m from the Primary coordinate. The legacy stored coordinate differs from the Primary coordinate by approximately 8.31 m. The Great Torii, ferry pier, parking context, and other island POIs must not be substituted for the Shrine representative Position. Distance values are observational only and are not used as PASS/HOLD thresholds.
```

### 8.13 Pilot 13 — 江島神社

```text
pilot_no = 13
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 江島神社
official_address = 神奈川県藤沢市江の島2丁目3番8号
identity_source_url = https://enoshimajinja.or.jp/

stored_latitude = 35.3013
stored_longitude = 139.4805
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = map_provider_poi
primary_source_url = https://mapfan.com/spots/SC543%2CJ%2C2R
primary_source_name = 江島神社
primary_source_address = 神奈川県藤沢市江の島2丁目3番8号
primary_latitude = 35.3003555
primary_longitude = 139.4795689
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = MULTI_SITE
anchor_complexity = HIGH
multi_site_status = MULTI_SITE
visitor_flow_note = 江島神社は辺津宮・中津宮・奥津宮など島内の複数の宮から構成され、参拝者は江の島入口から徒歩で各宮を巡る
navigation_risk_note = 江島神社全体・辺津宮・中津宮・奥津宮・龍宮・江の島入口・駐車場等を単一の代表Positionとして混同しない。同名神社も他地域に存在するためname-only joinは禁止

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q11259219
corroboration_latitude = 35.300361
corroboration_longitude = 139.479611

provider = MapFan
provider_role = PRIMARY
provider_poi_url = https://mapfan.com/spots/SC543%2CJ%2C2R
provider_latitude = 35.3003555
provider_longitude = 139.4795689
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 134.79
stored_vs_provider_delta_m = 134.79
primary_vs_corroboration_delta_m = 3.87

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master Position record was found for this legacy Shrine. The official Enoshima Shrine identity and Fujisawa address are consistent with the current MapFan POI at 35.3003555, 139.4795689. Wikidata independently identifies the same Fujisawa Enoshima Shrine at 35.300361, 139.479611, approximately 3.87 m from the Primary coordinate. The legacy stored coordinate differs from the Primary coordinate by approximately 134.79 m. Because Enoshima Shrine is a multi-site Shrine distributed across the island, coordinate distance alone does not determine Position validity.
```

### 8.14 Pilot 14 — 彌彦神社

```text
pilot_no = 14
pilot_group = LEGACY_UNTRACED
candidate_id = NOT_RETRIEVED

official_name = 彌彦神社
official_address = 新潟県西蒲原郡弥彦村弥彦2887-2
identity_source_url = https://www.yahiko-jinjya.or.jp/

stored_latitude = 37.7047
stored_longitude = 138.8287
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = NONE
existing_position_record_role = NONE

primary_source_type = map_provider_poi
primary_source_url = https://mapfan.com/spots/SC3W3%2CJ%2C00
primary_source_name = 彌彦神社
primary_source_address = 新潟県西蒲原郡弥彦村弥彦2887-2
primary_latitude = 37.7067028
primary_longitude = 138.8259704
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = MEDIUM
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式サイトは弥彦山麓の彌彦神社本体への交通アクセスと参拝案内を提供している
navigation_risk_note = 彌彦神社本体・宝物殿・社叢・弥彦山ロープウェイ・駐車場等の個別POIを代表Positionとして混同しない。同名神社が他地域にも存在するためname-only joinは禁止

corroboration_required = YES
corroboration_source_type = kokugakuin_university_shrine_database
corroboration_source_url = https://jmapps.ne.jp/kokugakuin/det.html?data_id=53403
corroboration_latitude = 37.70651389
corroboration_longitude = 138.82630833

provider = MapFan
provider_role = PRIMARY
provider_poi_url = https://mapfan.com/spots/SC3W3%2CJ%2C00
provider_latitude = 37.7067028
provider_longitude = 138.8259704
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 327.50
stored_vs_provider_delta_m = 327.50
primary_vs_corroboration_delta_m = 36.40

evidence_collected_at = 2026-09-19
notes = No dedicated Position Resolution Record / Source Packet / Candidate Master Position record was found for this legacy Shrine. The official Yahiko Shrine site confirms the current Shrine identity and address at Yahiko 2887-2. MapFan identifies the same Shrine at 37.7067028, 138.8259704. Kokugakuin University independently identifies the same Shrine at 37.70651389, 138.82630833, approximately 36.40 m from the Primary coordinate. The legacy stored coordinate differs from the Primary coordinate by approximately 327.50 m. Nearby POIs such as the treasure hall, shrine grove, ropeway facilities, and parking must not be substituted for the Shrine representative Position. Distance values are observational only and are not used as PASS/HOLD thresholds.
```

### 8.15 Pilot 15 — 多摩川浅間神社

```text
pilot_no = 15
pilot_group = KNOWN_CORRECTED
candidate_id = NOT_RETRIEVED

official_name = 多摩川浅間神社
official_address = 東京都大田区田園調布1-55-12
identity_source_url = https://sengenjinja.info/

stored_latitude = 35.5875263
stored_longitude = 139.6687549
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = docs/audit/shrine-70-coordinate-correction.md
existing_position_record_role = HISTORICAL_RECORD

primary_source_type = map_provider_poi
primary_source_url = NOT_RETRIEVED
primary_source_name = 多摩川浅間神社
primary_source_address = 東京都大田区田園調布1-55-12
primary_latitude = 35.5875263
primary_longitude = 139.6687549
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = LOW
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 多摩川駅側から神社境内へ向かう通常の参拝導線を持ち、神社本体の代表POIを特定可能。旧entry_status = SINGLE_CANDIDATE
navigation_risk_note = 過去のlegacy座標は多摩川駅周辺の近隣地点へずれていたため、駅・周辺店舗等を神社代表Positionとして混同しない

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q11430753
corroboration_latitude = 35.58721944
corroboration_longitude = 139.66861111

provider = Google Maps
provider_role = PRIMARY
provider_poi_url = NOT_RETRIEVED
provider_latitude = 35.5875263
provider_longitude = 139.6687549
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 0.00
stored_vs_provider_delta_m = 0.00
primary_vs_corroboration_delta_m = 36.51

evidence_collected_at = 2026-09-19
notes = This Pilot is a KNOWN_CORRECTED control. Repository audit history records that the previous coordinate 35.5898, 139.6688 resolved near a nearby non-Shrine location and was corrected to 35.5875263, 139.6687549 through the shrine-70 coordinate correction and migration 0094. The current Base Seed contains the corrected coordinate. The current Primary evidence reproduces the same corrected coordinate exactly, producing a 0.00 m stored-vs-Primary delta. Wikidata independently identifies the same Tamagawa Sengen Shrine and official website at 35.58721944, 139.66861111, approximately 36.51 m from the Primary coordinate. This control therefore reproduces the known correction under the current Evidence Collection procedure. Distance values remain observational and are not PASS/HOLD thresholds.
```

### 8.16 Pilot 16 — 富岡八幡宮

```text
pilot_no = 16
pilot_group = KNOWN_CORRECTION_WITH_SEED_DRIFT
candidate_id = NOT_RETRIEVED

official_name = 富岡八幡宮
official_address = 東京都江東区富岡1-20-3
identity_source_url = https://www.tomiokahachimangu.or.jp/

stored_latitude = 35.6733
stored_longitude = 139.7967
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = docs/audit/p8-identity-coordinate-remediation.md
existing_position_record_role = HISTORICAL_RECORD

primary_source_type = google_place_of_worship
primary_source_url = NOT_RETRIEVED
primary_source_name = 富岡八幡宮
primary_source_address = 東京都江東区富岡1-20-3
primary_latitude = 35.6717809
primary_longitude = 139.799519
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = MEDIUM
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 富岡八幡宮本体は門前仲町駅から徒歩圏にあり、同一住所のplace_of_worship POIとして現在位置を追跡可能
navigation_risk_note = 同名の富岡八幡宮が横浜市金沢区にも存在するためname-only joinは禁止。江東区富岡1-20-3のidentityで固定する

corroboration_required = YES
corroboration_source_type = map_provider_poi
corroboration_source_url = https://mapfan.com/spots/SC3W3%2CJ%2C09
corroboration_latitude = 35.6718782
corroboration_longitude = 139.7995823

provider = Google Places
provider_role = PRIMARY
provider_poi_url = NOT_RETRIEVED
provider_latitude = 35.6717809
provider_longitude = 139.799519
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 305.57
stored_vs_provider_delta_m = 305.57
primary_vs_corroboration_delta_m = 12.24

evidence_collected_at = 2026-09-19
notes = Google Place ID = ChIJK11I4BGJGGAR5mZswigcu58. This Pilot is a KNOWN_CORRECTION_WITH_SEED_DRIFT control. Repository audit history and migration 0099 identify 35.6717809, 139.799519 as the corrected position for the Koto-ku Tomioka Hachimangu entity at Tomioka 1-20-3. The current Base Seed still contains the legacy coordinate 35.6733, 139.7967, approximately 305.57 m from the corrected Primary coordinate. Current MapFan independently identifies the same Shrine at 35.6718782, 139.7995823, approximately 12.24 m from the Primary coordinate. This control reproduces the known artifact synchronization defect: remediation exists, but the Base Seed remains stale. Distance values are observational only and are not used as PASS/HOLD thresholds.
```
### 8.17 Pilot 17 — 御岩神社

```text
pilot_no = 17
pilot_group = WAVE0_CONTROL
candidate_id = wave0-003

official_name = 御岩神社
official_address = 茨城県日立市入四間町752
identity_source_url = https://www.oiwajinja.jp/

stored_latitude = 36.63604985
stored_longitude = 140.58558306
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = docs/audit/shrine-expansion-wave0-db01-g1-visitor-position-anchor.md
existing_position_record_role = CURRENT_ADOPTED_RECORD

primary_source_type = mapion_poi
primary_source_url = https://www.mapion.co.jp/phonebook/M06005/08202/ILSP0061135259_ipclm/
primary_source_name = 御岩神社
primary_source_address = 茨城県日立市入四間町
primary_latitude = 36.63604985
primary_longitude = 140.58558306
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = HIGH
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式交通案内は日立駅から御岩神社前までの公共交通導線と、社務所前P1・入口付近P2〜P4を区別して案内する。境内案内では御岩神社本体に加えて複数の境内・山内拠点が存在する
navigation_risk_note = 御岩神社本体・社務所・駐車場・登山口・御岩山・かびれ神宮・薩都神社中宮等を代表Positionとして混同しない。同名の御岩神社が他地域にも存在するためname-only joinは禁止

corroboration_required = YES
corroboration_source_type = prefectural_tourism_official
corroboration_source_url = https://www.ibarakiguide.jp/spot.php?code=470&mode=detail
corroboration_latitude = NOT_RETRIEVED
corroboration_longitude = NOT_RETRIEVED

provider = Mapion
provider_role = PRIMARY
provider_poi_url = https://www.mapion.co.jp/phonebook/M06005/08202/ILSP0061135259_ipclm/
provider_latitude = 36.63604985
provider_longitude = 140.58558306
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 0.00
stored_vs_provider_delta_m = 0.00
primary_vs_corroboration_delta_m = NOT_RETRIEVED

evidence_collected_at = 2026-09-19
notes = This Pilot is a WAVE0_CONTROL. The existing Position Resolution Record adopts 36.63604985, 140.58558306 as the Visitor / Navigation Anchor for Oiwa Shrine, and the same coordinate is frozen in the Position Contract, Candidate Master, Base Seed, and Production import records. Current official Shrine information confirms the Hitachi identity and address. Mapion continues to identify the same Hitachi Oiwa Shrine entity. Ibaraki Prefecture tourism information independently confirms the same Shrine identity, address, visitor access, and a Google Maps route, but an independent coordinate value was not deterministically retrieved in this collection pass. The stored and Primary coordinates therefore reproduce the adopted Position exactly at 0.00 m delta. No inferred corroboration coordinate is recorded.
```
### 8.18 Pilot 18 — 射水神社

```text
pilot_no = 18
pilot_group = WAVE0_CONTROL
candidate_id = wave0-007

official_name = 射水神社
official_address = 富山県高岡市古城1番1号
identity_source_url = https://www.imizujinjya.or.jp/access

stored_latitude = 36.7484968
stored_longitude = 137.0215428
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = docs/audit/shrine-position/imizu-jinja-position-resolution.md
existing_position_record_role = HISTORICAL_RECORD

primary_source_type = map_provider_poi
primary_source_url = https://www.google.com/maps/place/%E8%B6%8A%E4%B8%AD%E7%B7%8F%E9%8E%AE%E5%AE%88%E4%B8%80%E5%AE%AE+%E5%B0%84%E6%B0%B4%E7%A5%9E%E7%A4%BE/@36.7487628,137.0187706,17z/data=!4m14!1m7!3m6!1s0x5ff782b4e4d6b057:0x35f602686ce24412!2z6LaK5Lit57eP6Y6u5a6I5LiA5a6uIOWwhOawtOelnuekvg!8m2!3d36.7487585!4d137.0213509!16s%2Fg%2F120yf1fd!3m5!1s0x5ff782b4e4d6b057:0x35f602686ce24412!8m2!3d36.7487585!4d137.0213509!16s%2Fg%2F120yf1fd
primary_source_name = 越中総鎮守一宮 射水神社
primary_source_address = 富山県高岡市古城1-1
primary_latitude = 36.7487585
primary_longitude = 137.0213509
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = HIGH
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式アクセスでは射水神社が高岡古城公園中央に位置し、参拝者駐車場への進入経路を別途案内している。高岡駅から徒歩約10分の参拝導線も提示されている
navigation_risk_note = 神社本体・高岡古城公園・公園入口・参拝者駐車場・周辺道路を代表Positionとして混同しない。公式サイト自身がナビやGoogle Mapでは公園周辺または進入禁止箇所で案内が終了する場合があると警告している。二上射水神社は別entityであるためname-only joinは禁止

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q11458557
corroboration_latitude = 36.748529
corroboration_longitude = 137.021163

provider = Google Maps
provider_role = PRIMARY
provider_poi_url = https://www.google.com/maps/place/%E8%B6%8A%E4%B8%AD%E7%B7%8F%E9%8E%AE%E5%AE%88%E4%B8%80%E5%AE%AE+%E5%B0%84%E6%B0%B4%E7%A5%9E%E7%A4%BE/@36.7487628,137.0187706,17z/data=!4m14!1m7!3m6!1s0x5ff782b4e4d6b057:0x35f602686ce24412!2z6LaK5Lit57eP6Y6u5a6I5LiA5a6uIOWwhOawtOelnuekvg!8m2!3d36.7487585!4d137.0213509!16s%2Fg%2F120yf1fd!3m5!1s0x5ff782b4e4d6b057:0x35f602686ce24412!8m2!3d36.7487585!4d137.0213509!16s%2Fg%2F120yf1fd
provider_latitude = 36.7487585
provider_longitude = 137.0213509
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 33.75
stored_vs_provider_delta_m = 33.75
primary_vs_corroboration_delta_m = 30.52

evidence_collected_at = 2026-09-19
notes = This Pilot is a WAVE0_CONTROL and review-sensitive Position case. A current Position Resolution Record exists with position_status = HOLD_POSITION_REVIEW. The stored coordinate 36.7484968, 137.0215428 originates from the earlier frozen Source Packet, but the original source URL was not preserved; the Resolution Record explicitly records old_position_source_url_status = NOT_RECORDED_IN_SOURCE_PACKET. Current Google Maps Primary Evidence identifies the same Imizu Shrine entity at 36.7487585, 137.0213509. Wikidata independently identifies the same Takaoka Kojo Park Imizu Shrine at 36.748529, 137.021163. The stored coordinate differs from the current Primary by approximately 33.75 m, while Primary and corroboration differ by approximately 30.52 m. The HOLD is therefore not justified by a distance threshold; it remains because the provenance of the currently stored coordinate cannot be deterministically reproduced from its original source.
```

### 8.19 Pilot 19 — 札幌諏訪神社

```text
pilot_no = 19
pilot_group = WAVE0_CONTROL
candidate_id = wave0-010

official_name = 札幌諏訪神社
official_address = 北海道札幌市東区北12条東1丁目1番10号
identity_source_url = https://www.sapporo-suwajinja.com/

stored_latitude = 43.07603505258046
stored_longitude = 141.3540979693115
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md
existing_position_record_role = CURRENT_ADOPTED_RECORD

primary_source_type = shrine_authority_access_map
primary_source_url = https://jinjasapporo.net/find-shrine/%E8%AB%8F%E8%A8%AA%E7%A5%9E%E7%A4%BE/
primary_source_name = 諏訪神社
primary_source_address = 北海道札幌市東区北12条東1丁目1番10号
primary_latitude = 43.07603505258046
primary_longitude = 141.3540979693115
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = LOW
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式サイトは地下鉄東豊線北13条東駅から徒歩3分、南北線北12条駅から徒歩8分の参拝導線を案内する。北海道神社庁札幌支部の同一神社ページにはアクセスマップが掲載されている
navigation_risk_note = 一般地図ProviderのPOI座標を機械的に採用せず、神社authorityのアクセスマップが示すVisitor / Navigation Anchorとの意味差を保持する。同名の諏訪神社が多数存在するためname-only joinは禁止

corroboration_required = YES
corroboration_source_type = map_provider_poi
corroboration_source_url = https://mapfan.com/spots/SC3W3%2CJ%2CY0
corroboration_latitude = 43.0759164
corroboration_longitude = 141.3542148

provider = Hokkaido Jinja-cho Sapporo Branch / embedded Google Maps
provider_role = PRIMARY
provider_poi_url = https://jinjasapporo.net/find-shrine/%E8%AB%8F%E8%A8%AA%E7%A5%9E%E7%A4%BE/
provider_latitude = 43.07603505258046
provider_longitude = 141.3540979693115
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 0.00
stored_vs_provider_delta_m = 0.00
primary_vs_corroboration_delta_m = 16.25

evidence_collected_at = 2026-09-19
notes = This Pilot is a WAVE0_CONTROL and corrected access-map anchor case. The existing CLOSED Position Resolution Record has position_status = PASS and adopts 43.07603505258046, 141.3540979693115 as the Visitor / Navigation Anchor. The coordinate is derived from the Google Maps iframe embedded in the Hokkaido Jinja-cho Sapporo Branch page for the same Suwa Shrine identity and address. The current Base Seed contains the adopted coordinate exactly, producing a 0.00 m stored-vs-Primary delta. MapFan independently identifies the same Shrine at 43.0759164, 141.3542148, approximately 16.25 m from the adopted Primary and effectively identical to the former anchor. The correction therefore reflects source meaning and Visitor / Navigation Anchor semantics rather than a distance threshold.
```

### 8.20 Pilot 20 — 大鳥大社

```text
pilot_no = 20
pilot_group = WAVE0_CONTROL
candidate_id = wave0-002

official_name = 大鳥大社
official_address = 大阪府堺市西区鳳北町1-1-2
identity_source_url = https://www.ootoritaisha.jp/

stored_latitude = 34.5367778
stored_longitude = 135.4608611
stored_coordinate_artifact = backend/temples/data/shrines_seed_clean.json

existing_position_record = docs/audit/shrine-expansion-wave0-db01-source-packet-freeze.md
existing_position_record_role = CURRENT_ADOPTED_RECORD

primary_source_type = public_shrine_database
primary_source_url = https://kojiki.kokugakuin.ac.jp/jinjya/otoritaisha/
primary_source_name = 大鳥大社（大鳥神社）
primary_source_address = 大阪府堺市西区鳳北町1-1-2
primary_latitude = 34.5367778
primary_longitude = 135.4608611
primary_verified_at = 2026-09-19

retrieval_status = OK
entity_match = SAME

entry_status = NOT_CONFIRMED
anchor_complexity = MEDIUM
multi_site_status = NOT_RETRIEVED
visitor_flow_note = 公式アクセスではJR阪和線鳳駅西出口から徒歩約5分の参拝導線を案内し、自動車の場合は西の大鳥居から駐車場へ進入する経路を別途示している
navigation_risk_note = 大鳥大社本体・西の大鳥居・大鳥大社前交差点・駐車場等を代表Positionとして混同しない。同名・類似名の大鳥神社が全国に存在するためname-only joinは禁止

corroboration_required = YES
corroboration_source_type = wikidata
corroboration_source_url = https://www.wikidata.org/wiki/Q705151
corroboration_latitude = 34.536898
corroboration_longitude = 135.460765

provider = Kokugakuin University Shrine Database
provider_role = PRIMARY
provider_poi_url = https://kojiki.kokugakuin.ac.jp/jinjya/otoritaisha/
provider_latitude = 34.5367778
provider_longitude = 135.4608611
provider_plus_code = NOT_RETRIEVED

stored_vs_primary_delta_m = 0.00
stored_vs_provider_delta_m = 0.00
primary_vs_corroboration_delta_m = 16.00

evidence_collected_at = 2026-09-19
notes = This Pilot is a WAVE0_CONTROL and standard tracked Position case. The W0-DB01 Source Packet Freeze records the Kokugakuin University Shrine Database as the Position source and freezes 34.5367778, 135.4608611 with position_status = PASS. Candidate Master, Base Seed, and Production import records preserve the same coordinate. Current Kokugakuin evidence continues to identify Otori Taisha at Sakai-shi Nishi-ku Otorikita-machi 1-1-2 and publishes the same source coordinate. Wikidata independently identifies the same Shrine at 34.536898, 135.460765, approximately 16.00 m from the Primary coordinate. The stored and Primary coordinates therefore reproduce the tracked Position exactly at 0.00 m delta. Nearby entrance, intersection, and parking POIs must not be substituted for the Shrine representative Position.
```

---

## 9. Remaining Pilot Records

The same record structure defined in §8 must be used for:

```text
03 千葉神社
04 住吉神社（博多）
05 伊勢神宮（内宮）
06 伏見稲荷大社
07 鹿島神宮
08 宇佐神宮
09 三峯神社
10 金刀比羅宮
11 貴船神社
12 厳島神社
13 江島神社
14 彌彦神社
15 多摩川浅間神社
16 富岡八幡宮
17 御岩神社
18 射水神社
19 札幌諏訪神社
20 大鳥大社
```

Each record must retain the complete schema.

No Shrine-specific shortcut is permitted.

---

## 10. Completion Gate

This Pilot is complete only when all 20 Shrines have:

```text
official identity evidence
existing Position record classification
Primary Position Source evidence
retrieval_status
entity_match
coordinate traceability result
Visitor / Navigation Anchor observation
corroboration decision
provider role
coordinate delta fields or explicit NOT_RETRIEVED
evidence collection timestamp
```

Completion does not imply remediation.

---

## 11. Open Items

* Collect official identity evidence for all 20 Shrines.
* Inspect repository Position records for all 20 Shrines.
* Collect Primary Position Source evidence using the fixed procedure.
* Record `entity_match`.
* Record coordinate traceability.
* Determine corroboration requirements.
* Collect Provider POI evidence after Primary roles are established.
* Measure observational coordinate deltas.
* Classify discrepancies into the Phase 1 error taxonomy.
* Determine which checks may become deterministic Phase 2 rules.
* Do not remediate coordinate data inside this Pilot.

---

## 12. STOP

This document records Phase 1 evidence collection only.

No coordinate remediation is authorized by this Pilot.

Do not modify:

* Base Seed
* Candidate Master
* Production DB
* migrations
* Recommendation
* Compass
* Ranking

Any remediation requires a separately gated follow-up.
