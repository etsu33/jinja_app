# nsrc-000025 天津神社 G2 Position Review

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000025
position_status          = PASS
new_latitude             = NOT_DETERMINED
new_longitude            = NOT_DETERMINED
new_position_source_type = NOT_SUPPLIED
new_position_source_url  = NOT_SUPPLIED
verified_at              = 2026-10-18
MOTHER_SHIP_G2_DECISION  = PASS（adopted）
CONTRACT_EVIDENCE_NOTE   = ADOPTED_COORDINATE_NOT_DETERMINED; COORDINATE_SOURCE_NOT_SUPPLIED; TWO_HONDEN_POINT_SEMANTICS_UNRESOLVED
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
```

- Recorded at: 2026-10-18
- Base: `develop@225352c5`（PR #3266 merge, VPG001 G2 bootstrap）
- Contract: `docs/knowledge/shrine-position-contract.md`
- G2 audit: `docs/audit/niigata-vpg001-g2-position-review.md`

`position_status = PASS` records the existing Mother Ship decision. It is not reinterpreted. The
coordinate that decision adopted is **not determined** from the evidence supplied（see below）, so
`new_latitude` / `new_longitude` are not filled in. No coordinate is chosen by this record.

Evidence level: `MOTHER_SHIP_SUPPLIED`. Supplied by Mother Ship on 2026-10-18. Not re-fetched in this
environment（network policy denies the hosts）. Values are recorded exactly as supplied.

## Canonical identity（G1, unchanged）

```text
official_name    = 天津神社
official_address = 新潟県糸魚川市一の宮1丁目3番34号
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

The official shrine site identifies 天津神社御本殿 and 奴奈川神社御本殿 separately. nsrc-000025 is
天津神社 only. The other frozen 天津神社 row（上越市大字東京田）is a different shrine.

## Evidence supplied

Numeric coordinate candidates（no source attributed to either）:

```text
candidate A = 37.0401500, 137.8642250   source = NOT SUPPLIED
candidate B = 37.0399114, 137.864377    source = NOT SUPPLIED
A -> B      = 29.76 m（haversine）
```

Official identity sources（no coordinate）:

```text
糸魚川観光ガイド
  url     = https://www.itoigawa-kanko.net/trad/amatsu_shrine/
  address = 新潟県糸魚川市一の宮1-3-34

天津神社・奴奈川神社 official site
  url     = https://amatsujinja.com/contact/
  address = 新潟県糸魚川市一の宮1-3-34
```

## Contract / evidence mismatch（reported, not resolved here）

1. **Adopted coordinate not determined.** Two candidates were supplied, and the evidence doesn't say
   which one the Mother Ship PASS adopted. This record does not choose.
2. **Coordinate source not supplied.** Neither A nor B has a source or URL. The Audit Record requires
   `position_source_type` / `position_source_url` to be traceable. The two official sources confirm
   identity only.
3. **Point semantics in a two-honden precinct.** A and B are 29.76 m apart in a precinct that has two
   honden. The evidence doesn't show whether either point is 天津神社御本殿, 奴奈川神社御本殿, the
   precinct, or another point. The contract's gate lists "large precinct anchor semantics unresolved"
   as a HOLD case. This is recorded as an open question. The Mother Ship decision is not changed.

| Requirement（Source Adoption Rule） | Result |
|---|---|
| 1. identity confirmed by current authoritative source | PASS（official site, 糸魚川観光ガイド, G1） |
| 2. primary source is the same shrine's POI / navigation target | NOT ESTABLISHED（no source supplied） |
| 3. latitude / longitude traceable from the primary source | NOT TRACEABLE |
| 4. primary point consistent with visitor-facing identity | NOT DETERMINED（two points, no attribution） |
| 5. conflict explained | A / B difference not explained |

The Mother Ship PASS stands as recorded. Persisting an adopted coordinate requires Mother Ship to name
the adopted point and its source.

## Boundary

No change to Candidate Master, Base Seed, Knowledge Seed, Production, Recommendation / Ranking /
Meaning. G3 model-risk（天津神社・奴奈川神社）stays open. G2 is not frozen.
