# 青山稲荷神社（柏崎市） Position Resolution

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000005
position_status          = PASS
new_latitude             = 37.4172812
new_longitude            = 138.5910754
new_position_source_type = map_provider_poi
new_position_source_url  = https://map.yahoo.co.jp/v3/place/PBYAFpYs7-Q
verified_at              = 2026-10-10
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
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

The current prefectural shrine directory fixes the target as the 柏崎市荒浜 identity.
Same-name shrine results outside 柏崎市 are not used for this Candidate.

## Primary Position Evidence

Yahoo! Map current shrine POI:

- URL: https://map.yahoo.co.jp/v3/place/PBYAFpYs7-Q
- name: 青山稲荷神社
- address: 新潟県柏崎市荒浜4丁目1754-2
- selected POI pin coordinate: `37.4172812, 138.5910754`

Human QA on 2026-10-10 verified the returned POI page HTML contains the selected static-map marker:

```text
mappin_selected_48.png(138.5910754,37.4172812)
alt="青山稲荷神社の地図"
```

The same POI context identifies the place as `青山稲荷神社` / category `神社`.
The coordinate pair is therefore traceable to the selected shrine POI rather than adopted from
an address geocoder, opaque provider ID, or unrelated map viewport.

## Identity / address alignment

```text
canonical address = 新潟県柏崎市荒浜4丁目1754番地2
Yahoo POI address = 新潟県柏崎市荒浜4丁目1754-2
```

The difference is address notation only (`番地` vs hyphenated parcel notation).
Municipality, district, chome, parcel number, and shrine name align.

A separately observed same-name / similar-name shrine outside 柏崎市 is excluded by this exact
address constraint.

## Corroboration / conflict review

No unexplained competing coordinate for the same 柏崎市荒浜 shrine identity remains in this
G2 re-entry.

The previously investigated municipal ArcGIS FeatureServer was directly queried and did not
return a text-identity match for 青山稲荷神社 in its 807-feature dataset. That dataset is
therefore not promoted into the primary coordinate source and does not create a competing
coordinate.

```text
corroboration_source_url = NONE_REQUIRED
corroboration_coordinate = NOT_APPLICABLE
coordinate_delta_m       = NOT_APPLICABLE
conflicting_address_note = notation-only difference; exact parcel identity aligns
```

## Human QA

The Position Contract Source Adoption Rule was re-checked against the evidence above:

1. current authoritative shrine identity: PASS
2. primary source is the same shrine POI / navigation target: PASS
3. latitude / longitude are traceable from the primary source: PASS
4. primary point aligns with the visitor-facing identity: PASS
5. unexplained source / coordinate conflict requiring corroboration: NONE
6. deterministic Visitor / Navigation Anchor can be selected without inference: PASS

```text
HUMAN_QA = PASS
```

## Gate result

```text
POSITION_GATE          = PASS
ADOPTED_VISITOR_ANCHOR = 37.4172812, 138.5910754
```

The previous `PRIMARY_POI_COORDINATE_NOT_TRACEABLE` HOLD condition is resolved by the
coordinate-bearing Yahoo! Map selected POI evidence.

## Boundary

This resolution record establishes the G2 adopted Position only.
It does not hydrate Candidate Master, Base Seed, Knowledge Seed, or Production in this PR.
G3 may proceed for this Candidate after this record is merged.
