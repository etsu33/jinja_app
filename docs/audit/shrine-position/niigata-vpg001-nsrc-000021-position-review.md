# nsrc-000021 荒川神社 G2 Position Review

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000021
position_status          = PASS
new_latitude             = 38.140945
new_longitude            = 139.407348
new_position_source_type = map_provider_poi
new_position_source_url  = NOT_SUPPLIED（Google Maps 荒川神社 POI; no URL / place_id supplied）
verified_at              = 2026-10-19
corroboration_source_1   = Yahoo!/Zenrin
corroboration_coordinate_1 = 38.1409423, 139.4072801
corroboration_source_2   = 國學院大學 式内社データベース
corroboration_url_2      = https://jmapps.ne.jp/kokugakuin/det.html?data_id=182468
corroboration_coordinate_2 = 38.140916, 139.407516
MOTHER_SHIP_G2_DECISION  = PASS（2026-10-19）
ADOPTED_COORDINATE       = 38.140945, 139.407348
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
```

- First recorded: 2026-10-18（PR #3267, HOLD_POSITION_REVIEW）
- Resolved: 2026-10-19（base `develop@da06449f`, Mother Ship decision）
- Contract: `docs/knowledge/shrine-position-contract.md`
- G2 audit: `docs/audit/niigata-vpg001-g2-position-review.md`

Evidence level: `MOTHER_SHIP_SUPPLIED`. The Google Maps and Yahoo!/Zenrin coordinates were supplied by
Mother Ship on 2026-10-19 and were not re-fetched in this environment（its network policy denies the
hosts）. Values are recorded exactly as supplied. `verified_at` is the Mother Ship supply / decision
date.

## Canonical identity（G1, unchanged）

```text
official_name    = 荒川神社
official_address = 新潟県胎内市桃崎浜187番地
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

Same-name rows in the frozen Ready Set（新発田市荒川5431番地, 村上市小岩内463番地, 村上市荒川542番地）are
different shrines and are not used as position sources.

Identity corroboration（no coordinate; recorded 2026-10-18）:

```text
新潟県観光協会            新潟県胎内市桃崎浜187   https://niigata-kankou.or.jp/spot/7288
文化庁 国指定文化財等DB    荒川神社本殿 / 新潟県胎内市桃崎浜187
                          https://kunishitei.bunka.go.jp/bsys/maindetails/101/00013085
```

## Adopted Visitor / Navigation Anchor（Mother Ship decision, 2026-10-19）

```text
latitude  = 38.140945
longitude = 139.407348

primary source:
  type     = map_provider_poi
  provider = Google Maps
  entity   = 荒川神社
  url      = NOT_SUPPLIED（no URL / place_id supplied）
```

## Corroboration

```text
1. Yahoo!/Zenrin
   latitude  = 38.1409423
   longitude = 139.4072801
   url       = NOT_SUPPLIED

2. 國學院大學デジタル・ミュージアム / 式内社データベース
   source_type = independent_shrine_reference_database
   record      = 荒川神社（胎内市）
   latitude    = 38.140916
   longitude   = 139.407516
   url         = https://jmapps.ne.jp/kokugakuin/det.html?data_id=182468
```

Coordinate deltas（haversine; audit observations only, **not** a PASS threshold）:

```text
Google Maps -> Yahoo!/Zenrin   5.95 m
Google Maps -> 國學院          15.04 m
Yahoo!/Zenrin -> 國學院        20.84 m
```

The contract defines no fixed distance threshold. These deltas record that the three independent
publishers point to the same precinct area. They are not the basis of the decision.

## Position Contract evaluation

| Requirement（Source Adoption Rule） | Result |
|---|---|
| 1. identity confirmed by current authoritative source | PASS（観光協会, 文化庁, G1） |
| 2. primary source is the same shrine's POI / navigation target | PASS（Google Maps 荒川神社 POI, Mother Ship） |
| 3. latitude / longitude traceable from the primary source | coordinate recorded; source URL / place_id NOT SUPPLIED（see note） |
| 4. primary point consistent with visitor-facing identity | PASS（Mother Ship） |
| 5. independent corroboration | PASS（Yahoo!/Zenrin and 國學院, independent publishers） |

Traceability note: the Audit Record lists `position_source_url`. No Google Maps URL or place_id, and no
Yahoo!/Zenrin URL, was supplied, so neither point can be reproduced from this record alone. This does
not change the Mother Ship decision. It is recorded so the URL can be added.

## Previous HOLD（2026-10-18）— resolved

The 2026-10-18 technical proposal was `HOLD_POSITION_REVIEW`, with reason codes:

```text
INDEPENDENT_NUMERIC_CORROBORATION_ABSENT          -> RESOLVED（Yahoo!/Zenrin + 國學院 numeric points）
PRIMARY_POI_OR_NAVIGATION_TARGET_NOT_ESTABLISHED  -> RESOLVED（Google Maps 荒川神社 POI）
REFERENCE_DATABASE_ONLY                           -> RESOLVED（國學院 is now corroboration, not primary）
```

`INDEPENDENT_NUMERIC_CORROBORATION_ABSENT` is the code this record used for the gap that the 2026-10-19
decision calls `INDEPENDENT_NUMERIC_COORDINATE_NOT_OBTAINED`.

Previous candidate coordinate（國學院 `38.140916, 139.407516`）was not adopted. It is kept as
corroboration only.

## Boundary

No change to Candidate Master, Base Seed, Knowledge Seed, Production, Recommendation / Ranking /
Meaning. G2 is not frozen.
