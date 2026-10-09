# 相吉神社 Position Resolution

## Status

```text
record_kind            = position_resolution_record
candidate_id           = nsrc-000001
position_status        = HOLD_POSITION_REVIEW
new_latitude           = PENDING_HUMAN_QA_INPUT
new_longitude          = PENDING_HUMAN_QA_INPUT
new_position_source_type = PENDING_HUMAN_QA_INPUT
new_position_source_url  = PENDING_HUMAN_QA_INPUT
verified_at            = 2026-10-09
production_write       = NONE
seed_write             = NONE
candidate_master_write = NONE
```

Authority: `docs/knowledge/shrine-position-contract.md`.

## Canonical identity

```text
official_name    = 相吉神社
official_address = 新潟県中魚沼郡津南町大字谷内4797番地
identity_status  = CONFIRMED
```

Identity Source:
- 新潟県神社庁: https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15482

The official directory identifies 相吉神社 / あいよしじんじゃ at the address above.

## Position evidence observed

The Shrine Association entry exposes an address-based Google Map link, but the link is an
address query rather than a coordinate-bearing shrine POI record.

No independently traceable current primary POI coordinate for the same shrine was obtained in
this G2 execution.

## HOLD reason

Position Contract §Source Adoption Rule requires latitude / longitude to be traceable from the
primary position source. Address geocoding is not silently promoted into an adopted Visitor /
Navigation Anchor.

```text
hold_reason = CURRENT_PRIMARY_COORDINATE_UNAVAILABLE
adopted_anchor = NOT_DETERMINED
```

## Release condition

Obtain a traceable coordinate-bearing current shrine POI / visitor map for the same G1-confirmed
identity, plus appropriate corroboration if needed, then re-run G2.

## Boundary

No coordinate is written to Candidate Master, Base Seed, Knowledge Seed, or Production.
G3 is not executed for this Candidate while G2 is HOLD.
