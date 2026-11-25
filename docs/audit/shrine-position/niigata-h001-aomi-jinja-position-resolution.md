# 青海神社（加茂市） Position Resolution

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000004
position_status          = PASS
new_latitude             = 37.65657387
new_longitude            = 139.0536436
new_position_source_type = map_provider_poi
new_position_source_url  = https://www.mapion.co.jp/phonebook/M06005/15209/ILSP0061134757_ipclm/
verified_at              = 2026-10-09
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
```

Authority: `docs/knowledge/shrine-position-contract.md`.

## Canonical identity

```text
official_name = 青海神社
identity_status = CONFIRMED
G1 duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

Visitor-facing official Source:
- https://aomi-jinjya.or.jp/acsess.html
- address: 新潟県加茂市大字加茂229番地

NIIGATA-001 Source snapshot records:
- 加茂市大字加茂字宮山229番地

The shrine official page omits the `字宮山` component but preserves the municipality,
district and parcel number. This record does not rewrite the frozen Source address.

The official access page also gives explicit visitor routing from the first torii / Kamo-yama
Park side to the worship hall.

## Primary Position Evidence

Mapion current shrine POI:

- name: 青海神社
- reading: あおみじんじゃ
- locality: 新潟県加茂市大字加茂
- URL: https://www.mapion.co.jp/phonebook/M06005/15209/ILSP0061134757_ipclm/
- map center / single POI coordinate:
  `37.65657387, 139.0536436`

The page explicitly exposes these latitude / longitude values and centers the single POI marker
on them.

This is the 加茂市 / あおみ identity fixed by G1, not the 糸魚川市 same-name shrine.

## Independent corroboration

國學院大學デジタル・ミュージアム 延喜式内社DB:

- https://jmapps.ne.jp/kokugakuin/det.html?data_id=182448
- 青海神社（論社）
- coordinate link: `37.656662, 139.053621`

Observed haversine difference using earth mean radius 6371008.8m:

```text
coordinate_delta_m = 10.00
```

This distance is an audit observation, not an automatic threshold.

## Gate result

```text
POSITION_GATE         = PASS
ADOPTED_VISITOR_ANCHOR = 37.65657387, 139.0536436
conflicting_address_note = official visitor page omits 字宮山; frozen Jinjacho address retains it
```

Identity, current map-provider POI, visitor route, and independent coordinate corroboration are
explainably aligned.

## Boundary

This resolution record establishes the G2 adopted Position only.
It does not hydrate Candidate Master, Base Seed, Knowledge Seed, or Production in this PR.
G3 may proceed for this Candidate after this record is merged.
