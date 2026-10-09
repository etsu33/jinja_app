# 青澤神社 Position Resolution

## Status

```text
record_kind            = position_resolution_record
candidate_id           = nsrc-000002
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
official_name    = 青澤神社
official_address = 新潟県糸魚川市大字青海2696番地
identity_status  = CONFIRMED
```

Identity Source:
- 新潟県神社庁: https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15216

## Position evidence observed

Mapion exposes a current facility page for `青沢神社` / あおさわじんじゃ in
糸魚川市大字青海:

- https://www.mapion.co.jp/phonebook/M51020/15216/120399442_ipcbl/

The page is consistent with the G1 identity at locality / reading level and exposes a Mapcode,
but the captured source does not expose a traceable numeric latitude / longitude.

A map-provider listing also identifies `青澤神社 (日連神社)` at 2696 Oumi, Itoigawa, but
this G2 task does not infer an adopted coordinate from an opaque provider Place ID.

## HOLD reason

```text
hold_reason = PRIMARY_POI_COORDINATE_NOT_TRACEABLE
adopted_anchor = NOT_DETERMINED
```

A Mapcode, station distance, or opaque place identifier is not converted into a coordinate by
inference in this Gate.

## Release condition

Obtain a traceable coordinate-bearing POI for the same G1-confirmed shrine identity and re-run G2.

## Boundary

No coordinate is written to Candidate Master, Base Seed, Knowledge Seed, or Production.
G3 is not executed for this Candidate while G2 is HOLD.
