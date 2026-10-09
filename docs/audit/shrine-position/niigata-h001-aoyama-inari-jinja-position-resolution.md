# 青山稲荷神社（柏崎市） Position Resolution

## Status

```text
record_kind            = position_resolution_record
candidate_id           = nsrc-000005
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
official_name    = 青山稲荷神社
official_address = 新潟県柏崎市荒浜4丁目1754番地2
identity_status  = CONFIRMED
```

Identity Source:
- 新潟県神社庁: https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15205

## Position evidence observed

Yahoo! Map exposes a current shrine POI with the exact H001 target address:

- https://map.yahoo.co.jp/v3/place/PBYAFpYs7-Q
- name: 青山稲荷神社
- address: 新潟県柏崎市荒浜4丁目1754-2

The captured page does not expose a traceable numeric latitude / longitude for that POI.

Same-name map results exist outside 柏崎市; therefore this G2 record uses the exact G1 address
as an identity constraint and does not select a same-name POI by name alone.

## HOLD reason

```text
hold_reason = PRIMARY_POI_COORDINATE_NOT_TRACEABLE
adopted_anchor = NOT_DETERMINED
```

The exact-address POI is useful identity evidence but cannot satisfy the Position Contract until
its numeric coordinate is traceable.

## Release condition

Obtain a coordinate-bearing current POI / visitor map for the 柏崎市荒浜 identity and re-run G2.

## Boundary

No coordinate is written to Candidate Master, Base Seed, Knowledge Seed, or Production.
G3 is not executed for this Candidate while G2 is HOLD.
