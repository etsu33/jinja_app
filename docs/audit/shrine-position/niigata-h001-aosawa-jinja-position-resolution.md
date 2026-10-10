# 青澤神社 Position Resolution

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000002
position_status          = PASS
new_latitude             = 37.00763484
new_longitude            = 137.79024297
new_position_source_type = map_provider_poi
new_position_source_url  = https://www.mapion.co.jp/phonebook/M51020/15216/120399442_ipcbl/
verified_at              = 2026-10-10
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
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

## Primary Position Evidence

Mapion current POI:

- URL: https://www.mapion.co.jp/phonebook/M51020/15216/120399442_ipcbl/
- displayed name: 青沢神社
- reading: あおさわじんじゃ
- locality: 新潟県糸魚川市大字青海
- POI code: `120399442_ipcbl`
- coordinate: `37.00763484, 137.79024297`

The current POI page directly binds the place identity and coordinate in its `data-spotinfo`
payload:

```text
name    = 青沢神社
address = 新潟県糸魚川市大字青海
lat     = 37.00763484
lng     = 137.79024297
```

The same coordinate is used by the page's print-map link and by navigation links whose route
destination is explicitly `青沢神社`:

```text
n_end_name = 青沢神社
n_end_lat  = 37.00763484
n_end_lon  = 137.79024297
```

This establishes the coordinate as the current Mapion POI / navigation target rather than an
address-geocoding result, Mapcode conversion, opaque provider-ID conversion, or unrelated map
viewport.

## Identity / address alignment

Canonical G1 identity:

```text
青澤神社
新潟県糸魚川市大字青海2696番地
```

Mapion uses the orthographic variant `青沢神社`, but provides the same reading
`あおさわじんじゃ` and the same 糸魚川市大字青海 locality.

The existing G2 investigation also observed a provider listing for
`青澤神社 (日連神社)` at `2696 Oumi, Itoigawa`. Its opaque provider Place ID is not converted
into a coordinate; it is retained only as identity / exact-address corroboration.

No same-name result outside the G1-confirmed 糸魚川市大字青海 identity is promoted.

## Corroboration / conflict review

No unexplained competing coordinate for the same G1-confirmed shrine identity is adopted.

The canonical address contains parcel number `2696`, while the Mapion POI page exposes locality
rather than the full parcel. The exact-address provider listing and the Mapion reading / locality
alignment make the identity relationship explainable without deriving a coordinate from the
address.

```text
corroboration_source_type = provider_identity_listing
corroboration_coordinate  = NOT_USED
coordinate_delta_m        = NOT_APPLICABLE
conflicting_address_note  = Mapion omits parcel number; exact-address provider listing corroborates identity
```

## Human QA

The Position Contract Source Adoption Rule was re-checked:

1. current authoritative shrine identity: PASS
2. primary source is the same shrine POI / navigation target: PASS
3. latitude / longitude are directly traceable from the primary source: PASS
4. primary point aligns with the visitor-facing identity: PASS
5. observed identity/address differences are explainable without coordinate inference: PASS
6. deterministic Visitor / Navigation Anchor can be selected without unresolved conflict: PASS

```text
HUMAN_QA = PASS
```

## Gate result

```text
POSITION_GATE          = PASS
ADOPTED_VISITOR_ANCHOR = 37.00763484, 137.79024297
```

The previous `PRIMARY_POI_COORDINATE_NOT_TRACEABLE` HOLD condition is resolved by the
coordinate-bearing Mapion POI / route-target evidence.

## Boundary

This resolution record establishes the G2 adopted Position only.
It does not hydrate Candidate Master, Base Seed, Knowledge Seed, or Production in this PR.
G3 may proceed for this Candidate after this record is merged.
