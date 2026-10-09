# 蒼柴神社 Position Resolution

## Status

```text
record_kind            = position_resolution_record
candidate_id           = nsrc-000003
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
official_name    = 蒼柴神社
official_address = 新潟県長岡市悠久町707
identity_status  = CONFIRMED
```

Identity / visitor Sources:
- shrine official access: https://www.aoshijinja.or.jp/アクセス/
- Nagaoka visitor page: https://nagaoka-navi.or.jp/spot/42363

Both identify the same shrine at 悠久町707.

## Position evidence observed

The shrine official access page embeds Google Maps with:

```text
q  = 蒼柴神社
ll = 37.4325553, 138.883193
z  = 15
```

The iframe URL observed from the official page is:

https://www.google.com/maps?ll=37.4325553%2C138.883193&output=embed&q=%E8%92%BC%E6%9F%B4%E7%A5%9E%E7%A4%BE&z=15

However, `ll` is a map viewport-center parameter. This audit does not treat it as proof that the
same numeric point is the shrine POI marker / Visitor Anchor.

Independent public location material:

- GeoShape / 『日本歴史地名大系』 facility record:
  https://geoshape.ex.nii.ac.jp/nrct-poi/resource/15/150000282500.html
- coordinate: `37.433212, 138.882950`
- address: 新潟県長岡市悠久町707番地

Observed distance between the official-map `ll` value and the GeoShape facility point:

```text
coordinate_delta_m = 76.11
```

The distance is an observation, not a PASS threshold.

## HOLD reason

```text
hold_reason = VISITOR_ANCHOR_SEMANTICS_NOT_DETERMINED
adopted_anchor = NOT_DETERMINED
```

The same shrine identity is well supported, but this Gate cannot deterministically establish
whether the official iframe `ll` or the GeoShape facility point is the correct Visitor /
Navigation Anchor. A rough same-precinct position is not promoted into an adopted coordinate.

## Release condition

Obtain a traceable POI-marker / visitor-navigation coordinate for 蒼柴神社 itself, or another
source that resolves the point-semantics difference, then re-run G2.

## Boundary

No coordinate is written to Candidate Master, Base Seed, Knowledge Seed, or Production.
G3 is not executed for this Candidate while G2 is HOLD.
