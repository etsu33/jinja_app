# nsrc-000025 天津神社 G2 Position Review

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000025
position_status          = PASS
new_latitude             = 37.0397729
new_longitude            = 137.8644153
new_position_source_type = official_linked_shared_precinct_map_provider_poi
new_position_source_url  = https://www.google.com/maps/place/%E5%A4%A9%E6%B4%A5%E7%A5%9E%E7%A4%BE%E3%83%BB%E5%A5%B4%E5%A5%88%E5%B7%9D%E7%A5%9E%E7%A4%BE/@37.0399538,137.8617831,946m/data=!3m1!1e3!4m10!1m2!2m1!1z5aSp5rSl56We56S-!3m6!1s0x5ff65db3f4e2982f:0xbf5aa67a0cc9ddc2!8m2!3d37.0397729!4d137.8644153!15sCgzlpKnmtKXnpZ7npL5aDyIN5aSp5rSlIOelnuekvpIBDXNoaW50b19zaHJpbmWaASNDaFpEU1VoTk1HOW5TMFZKUTBGblRVUnZjblJVYWt4QkVBReABAPoBBAhMEB8!16s%2Fm%2F0nb82lf?authuser=0&entry=ttu&g_ep=EgoyMDI2MTAxMy4wIKXMDSoASAFQAw%3D%3D
verified_at              = 2026-10-19
official_visitor_source  = https://amatsujinja.com/（交通案内 section）
google_maps_entity_name  = 天津神社・奴奈川神社
google_maps_feature_id   = 0x5ff65db3f4e2982f:0xbf5aa67a0cc9ddc2
google_maps_entity_token = /m/0nb82lf
anchor_semantics         = SHARED_PRECINCT_VISITOR_NAVIGATION_ANCHOR（not the 天津神社御本殿 coordinate）
MOTHER_SHIP_G2_DECISION  = PASS（final, 2026-10-19）
ADOPTED_COORDINATE       = 37.0397729, 137.8644153
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
```

- First recorded: 2026-10-18（PR #3267）
- Current status set to HOLD: 2026-10-19（PR #3267 amendment）
- Resolved to PASS: 2026-10-19（base `develop@0df81f75`, Mother Ship final decision）
- Contract: `docs/knowledge/shrine-position-contract.md`
- G2 audit: `docs/audit/niigata-vpg001-g2-position-review.md`

Evidence level: `MOTHER_SHIP_SUPPLIED`. The Google Maps URL and the official page were supplied by
Mother Ship on 2026-10-19 and are recorded verbatim, not reconstructed or normalized. They were not
re-fetched in this environment（its network policy denies the hosts）. `verified_at` is the Mother Ship
supply / decision date.

## Canonical identity（G1, unchanged）

```text
official_name    = 天津神社
official_address = 新潟県糸魚川市一の宮1丁目3番34号
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

The official shrine site identifies 天津神社御本殿 and 奴奈川神社御本殿 separately. nsrc-000025 is
天津神社 only. The other frozen 天津神社 row（上越市大字東京田）is a different shrine.

## Visitor-facing authority

```text
天津神社・奴奈川神社 official site
  url     = https://amatsujinja.com/
  section = 交通案内（visitor-facing access / map section; the cited linked / shared-precinct
            navigation context）

Identity-only sources（recorded 2026-10-18, no coordinate）:
  糸魚川観光ガイド   https://www.itoigawa-kanko.net/trad/amatsu_shrine/   新潟県糸魚川市一の宮1-3-34
  official contact   https://amatsujinja.com/contact/                       新潟県糸魚川市一の宮1-3-34
                     （identity only; not the map-link source for this decision）
```

## Adopted Visitor / Navigation Anchor（Mother Ship final decision, 2026-10-19）

```text
latitude  = 37.0397729
longitude = 137.8644153

primary source:
  type        = official_linked_shared_precinct_map_provider_poi
  provider    = Google Maps
  entity name = 天津神社・奴奈川神社
  feature_id  = 0x5ff65db3f4e2982f:0xbf5aa67a0cc9ddc2
  entity      = /m/0nb82lf
  url         = new_position_source_url（Status block, verbatim）
```

The adopted coordinate is the place-entity coordinate embedded in the URL:

```text
place name（URL path, decoded）  = 天津神社・奴奈川神社
entity block                    = !3m6!1s0x5ff65db3f4e2982f:0xbf5aa67a0cc9ddc2!8m2!3d37.0397729!4d137.8644153
entity token                    = !16s%2Fm%2F0nb82lf（/m/0nb82lf）
search query（1z…, decoded）     = 天津神社
viewport centre（not adopted）   = @37.0399538,137.8617831（map view only, 234.49 m from the entity point）
```

### Anchor semantics

```text
this coordinate IS      the Visitor / Navigation Anchor for the shared 天津神社・奴奈川神社 precinct
this coordinate IS NOT  the 天津神社御本殿 coordinate
```

The Google Maps entity is the shared precinct（`天津神社・奴奈川神社`）, not a single honden. Mother Ship
adopted the shared-precinct interpretation, which resolves the previous two-honden anchor-semantics
HOLD. This is consistent with the Canonical Meaning: `Shrine.latitude / longitude` is a Visitor /
Navigation Anchor, not a honden location.

Fact ownership is unchanged. 天津神社 and 奴奈川神社 remain separate shrine / Fact owners（G1）. Sharing
a visitor anchor does not merge their deity or history facts. The G3 model-risk question stays open.

## Historical candidates and corroboration（not adopted）

Distances from the adopted point（haversine; audit observations only, **not** a PASS threshold）:

```text
Candidate A  37.0401500, 137.8642250
  source  = Japanese Wikipedia
  status  = NOT ADOPTED
  note    = upstream provenance unresolved
  delta   = 45.21 m

Candidate B  37.0399114, 137.864377
  source  = Open Data Japan / provider 新潟県糸魚川市
  status  = NOT ADOPTED
  role    = corroboration near the adopted shared-precinct anchor
  delta   = 15.77 m

CODH         37.039941, 137.864358
  record  = 天津神社祭祀遺跡
  status  = NOT ADOPTED as Visitor / Navigation Anchor
  role    = corroboration only
  delta   = 19.37 m
```

Source URLs for A, B and CODH were not supplied. They are kept as historical / corroboration
records. The 2026-10-18 record attributed no source to A or B. The sources above were supplied on
2026-10-19.

## Position Contract evaluation

| Requirement（Source Adoption Rule） | Result |
|---|---|
| 1. identity confirmed by current authoritative source | PASS（official site, 糸魚川観光ガイド, G1） |
| 2. primary source is the same shrine's POI / navigation target | PASS（shared-precinct Google Maps entity; official 交通案内 context） |
| 3. latitude / longitude traceable from the primary source | PASS（entity coordinate embedded in the recorded URL） |
| 4. primary point consistent with visitor-facing identity | PASS（shared-precinct visitor anchor, Mother Ship） |
| 5. conflict explained | PASS（A / B / CODH are not adopted; semantics = shared precinct） |

## Decision history

```text
2026-10-18  MOTHER_SHIP_G2_DECISION = PASS（adopted）recorded; adopted coordinate not determined
2026-10-19  current status set to HOLD_POSITION_REVIEW by Mother Ship; historical PASS preserved
2026-10-19  Mother Ship final decision: PASS at 37.0397729, 137.8644153（shared-precinct anchor）
```

The historical PASS was a decision without a determined coordinate or traceable source. The
2026-10-19 HOLD recorded that gap. The final PASS closes it with a determined coordinate, a traceable
source and explicit anchor semantics. The historical PASS is not rewritten.

HOLD reasons closed:

```text
ADOPTED_COORDINATE_NOT_DETERMINED          -> RESOLVED（37.0397729, 137.8644153）
PRIMARY_COORDINATE_SOURCE_NOT_TRACEABLE    -> RESOLVED（Google Maps entity URL recorded verbatim）
TWO_HONDEN_CANDIDATE_SEMANTICS_UNRESOLVED  -> RESOLVED（shared-precinct Visitor / Navigation Anchor）
```

## Boundary

No change to Candidate Master, Base Seed, Knowledge Seed, Production, Recommendation / Ranking /
Meaning. G3 model-risk（天津神社・奴奈川神社）stays open. G2 is not frozen.
