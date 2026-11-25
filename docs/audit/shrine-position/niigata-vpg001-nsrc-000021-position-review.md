# nsrc-000021 荒川神社 G2 Position Review

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000021
position_status          = PASS
new_latitude             = 38.1409456
new_longitude            = 139.4073314
new_position_source_type = map_provider_poi
new_position_source_url  = https://www.google.com/maps/place/%E8%8D%92%E5%B7%9D%E7%A5%9E%E7%A4%BE/@38.1409298,139.4074058,58m/data=!3m1!1e3!4m12!1m5!3m4!2zMzjCsDA4JzI3LjUiTiAxMznCsDI0JzI2LjQiRQ!8m2!3d38.140958!4d139.407324!3m5!1s0x5f8b6bd0cbf5ba91:0xa762ad68fe889819!8m2!3d38.1409456!4d139.4073314!16s%2Fg%2F11v4bqq35k?authuser=0&entry=ttu&g_ep=EgoyMDI2MTAxMy4wIKXMDSoASAFQAw%3D%3D
verified_at              = 2026-10-19
google_maps_feature_id   = 0x5f8b6bd0cbf5ba91:0xa762ad68fe889819
google_maps_entity_token = /g/11v4bqq35k
corroboration_source_1   = Yahoo!/Zenrin
corroboration_coordinate_1 = 38.1409423, 139.4072801
corroboration_source_2   = 國學院大學 式内社データベース
corroboration_url_2      = https://jmapps.ne.jp/kokugakuin/det.html?data_id=182468
corroboration_coordinate_2 = 38.140916, 139.407516
MOTHER_SHIP_G2_DECISION  = PASS（2026-10-19）
ADOPTED_COORDINATE       = 38.1409456, 139.4073314
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
```

- First recorded: 2026-10-18（PR #3267, HOLD_POSITION_REVIEW）
- Resolved: 2026-10-19（base `develop@da06449f`, Mother Ship decision）
- Primary provenance finalized: 2026-10-19（Mother Ship-supplied Google Maps POI URL）
- Contract: `docs/knowledge/shrine-position-contract.md`
- G2 audit: `docs/audit/niigata-vpg001-g2-position-review.md`

Evidence level: `MOTHER_SHIP_SUPPLIED`. The URL and coordinates were supplied by Mother Ship on
2026-10-19. They were not re-fetched in this environment（its network policy denies the hosts）. The URL
is recorded verbatim. `verified_at` is the Mother Ship supply / decision date.

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

## Adopted Visitor / Navigation Anchor

```text
latitude  = 38.1409456
longitude = 139.4073314

primary source:
  type        = map_provider_poi
  provider    = Google Maps
  entity      = 荒川神社
  feature_id  = 0x5f8b6bd0cbf5ba91:0xa762ad68fe889819
  entity      = /g/11v4bqq35k
  url         = new_position_source_url（Status block, verbatim）
```

The adopted coordinate is the place-entity coordinate embedded in the URL:

```text
place name（URL path, decoded）  = 荒川神社
entity block                    = !3m5!1s0x5f8b6bd0cbf5ba91:0xa762ad68fe889819!8m2!3d38.1409456!4d139.4073314
entity token                    = !16s%2Fg%2F11v4bqq35k（/g/11v4bqq35k）
```

Other points in or around the same URL that are **not** adopted:

```text
viewport centre   @38.1409298,139.4074058            map view only
dropped pin       !3d38.140958!4d139.407324          pin block（2z… decodes to 38°08'27.5"N 139°24'26.4"E）
right-click point 38.141030, 139.407468              separately observed by Mother Ship; not the POI entity
earlier value     38.140945, 139.407348              rounded / manual-click value, replaced（see below）
```

### Provenance precision correction（2026-10-19）

The first 2026-10-19 PASS recorded `38.140945, 139.407348`. Mother Ship has since supplied the canonical
POI URL. The adopted coordinate is now the POI entity coordinate from that URL, `38.1409456,
139.4073314`. This corrects the precision of the provenance. It is not a new position decision, and
`position_status` stays `PASS`.

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
Google Maps POI -> Yahoo!/Zenrin   4.50 m
Google Maps POI -> 國學院          16.48 m
Yahoo!/Zenrin   -> 國學院          20.84 m
```

The contract defines no fixed distance threshold. These deltas record that three independent
publishers point to the same precinct area. They are not the basis of the decision.

## Position Contract evaluation

| Requirement（Source Adoption Rule） | Result |
|---|---|
| 1. identity confirmed by current authoritative source | PASS（観光協会, 文化庁, G1） |
| 2. primary source is the same shrine's POI / navigation target | PASS（Google Maps 荒川神社 POI entity） |
| 3. latitude / longitude traceable from the primary source | PASS（entity coordinate embedded in the recorded URL） |
| 4. primary point consistent with visitor-facing identity | PASS（Mother Ship） |
| 5. independent corroboration | PASS（Yahoo!/Zenrin and 國學院, independent publishers） |

Open provenance item（does not affect the PASS）: no Yahoo!/Zenrin URL was supplied, so that
corroboration point is not reproducible from this record.

## Previous HOLD（2026-10-18）— resolved

The 2026-10-18 technical proposal was `HOLD_POSITION_REVIEW`, with reason codes:

```text
INDEPENDENT_NUMERIC_CORROBORATION_ABSENT          -> RESOLVED（Yahoo!/Zenrin + 國學院 numeric points）
PRIMARY_POI_OR_NAVIGATION_TARGET_NOT_ESTABLISHED  -> RESOLVED（Google Maps 荒川神社 POI entity）
REFERENCE_DATABASE_ONLY                           -> RESOLVED（國學院 is now corroboration, not primary）
```

`INDEPENDENT_NUMERIC_CORROBORATION_ABSENT` is the code this record used for the gap that the 2026-10-19
decision calls `INDEPENDENT_NUMERIC_COORDINATE_NOT_OBTAINED`.

The 國學院 point（`38.140916, 139.407516`）was never adopted. It is kept as corroboration only.

## Boundary

No change to Candidate Master, Base Seed, Knowledge Seed, Production, Recommendation / Ranking /
Meaning. G2 is not frozen.
