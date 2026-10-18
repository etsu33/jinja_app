# nsrc-000024 秋葉神社 G2 Position Review

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000024
position_status          = HOLD_POSITION_REVIEW
new_latitude             = NONE
new_longitude            = NONE
new_position_source_type = NONE
new_position_source_url  = NONE
verified_at              = 2026-10-18
TECHNICAL_G2_PROPOSAL    = HOLD_POSITION_REVIEW
MOTHER_SHIP_G2_DECISION  = PENDING
ADOPTED_COORDINATE       = NONE
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
```

- Recorded at: 2026-10-18
- Base: `develop@225352c5`（PR #3266 merge, VPG001 G2 bootstrap）
- Contract: `docs/knowledge/shrine-position-contract.md`
- G2 audit: `docs/audit/niigata-vpg001-g2-position-review.md`

Evidence level: `MOTHER_SHIP_SUPPLIED`. Supplied by Mother Ship on 2026-10-18. Not re-fetched in this
environment（network policy denies the hosts）.

## Canonical identity（G1, unchanged）

```text
official_name    = 秋葉神社
official_address = 新潟県新潟市秋葉区秋葉3丁目8番19号
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

The 10 other frozen 秋葉神社 rows（different addresses）are different shrines and are not position
sources. Name-only matching is not used.

## Evidence supplied

```text
official shrine page（宗教法人 秋葉神社）
  url         = https://www.niitsu.or.jp/~akiha-jinja/
  address     = confirmed（Mother Ship）
  coordinate  = NOT SUPPLIED

新潟県神社庁（official shrine directory）
  url         = https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15105
  address     = 新潟市秋葉区秋葉3丁目8番19号
  coordinate  = NOT SUPPLIED
```

Both corroborate identity. Neither supplies a numeric latitude / longitude.

## Position Contract evaluation

| Requirement（Source Adoption Rule） | Result |
|---|---|
| 1. identity confirmed by current authoritative source | PASS（official page, 神社庁, G1） |
| 2. primary source is the same shrine's POI / navigation target | NOT OBTAINED |
| 3. latitude / longitude traceable from the primary source | NOT OBTAINED |
| 4. primary point consistent with visitor-facing identity | NOT APPLICABLE（no point） |

The contract sets `HOLD_POSITION_REVIEW` when a current primary coordinate cannot be obtained. Address
identity alone does not give PASS.

## Technical G2 proposal

```text
TECHNICAL_G2_PROPOSAL = HOLD_POSITION_REVIEW

reason_codes:
- OFFICIAL_VISITOR_NUMERIC_COORDINATE_NOT_OBTAINED
- PRIMARY_POI_OR_NAVIGATION_TARGET_NOT_ESTABLISHED

ADOPTED_COORDINATE = NONE
```

No coordinate is inferred from the address. Mother Ship has not decided this candidate.

## Required to resolve

A numeric latitude / longitude from an official visitor-facing source for this exact shrine（秋葉区秋葉3丁目8番19号）,
or from structured metadata that source explicitly exposes, such as an official map link to a POI with
a directly traceable coordinate. A map-view centre, address geocoding or a same-name sibling POI is not
acceptable.

## Boundary

No change to Candidate Master, Base Seed, Knowledge Seed, Production, Recommendation / Ranking /
Meaning. G2 is not frozen.
