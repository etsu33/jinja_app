# nsrc-000023 熱串彦神社 G2 Position Review

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000023
position_status          = PASS
new_latitude             = 38.072529
new_longitude            = 138.407913
new_position_source_type = public_reference_dataset_facility_point
new_position_source_url  = https://geoshape.ex.nii.ac.jp/nrct-poi/resource/15/150000593300.html
verified_at              = 2026-10-18
corroboration_source     = Wikidata（WikiProject Japan shrine dataset）
corroboration_source_url = NOT_SUPPLIED
corroboration_coordinate = 38.072471, 138.407785
coordinate_delta_m       = 12.93
MOTHER_SHIP_G2_DECISION  = PASS（adopted）
CONTRACT_EVIDENCE_NOTE   = PRIMARY_SOURCE_TYPE_PRECEDENT_GAP; CORROBORATION_URL_NOT_SUPPLIED
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
```

- Recorded at: 2026-10-18
- Base: `develop@225352c5`（PR #3266 merge, VPG001 G2 bootstrap）
- Contract: `docs/knowledge/shrine-position-contract.md`
- G2 audit: `docs/audit/niigata-vpg001-g2-position-review.md`

`position_status = PASS` records the existing Mother Ship decision. This record persists the
provenance supplied for it. It does not reinterpret or replace that decision.

Evidence level: `MOTHER_SHIP_SUPPLIED`. Supplied by Mother Ship on 2026-10-18. Not re-fetched in this
environment（network policy denies the hosts）. Values are recorded exactly as supplied.

## Canonical identity（G1, unchanged）

```text
official_name    = 熱串彦神社
official_address = 新潟県佐渡市長江854番地
identity_status  = CONFIRMED
duplicate_status = NEW
```

## Position evidence

Primary:

```text
source_provider = 『日本歴史地名大系』施設・地点項目データセット / CODH
source_type     = public_reference_dataset_facility_point
source_url      = https://geoshape.ex.nii.ac.jp/nrct-poi/resource/15/150000593300.html
source_address  = 新潟県佐渡市長江854番地
latitude        = 38.072529
longitude       = 138.407913
```

Corroboration:

```text
source_provider = Wikidata（WikiProject Japan shrine dataset）
source_url      = NOT_SUPPLIED（no item URL / QID supplied）
identity        = 熱串彦神社 / 佐渡市長江854
latitude        = 38.072471
longitude       = 138.407785
```

```text
coordinate_delta_m（CODH -> Wikidata, haversine） = 12.93
```

The delta is an observation, not a PASS threshold（contract: no fixed distance threshold）. Both sources
name the same shrine at the same address as the canonical identity.

## Position Contract evaluation

| Requirement（Source Adoption Rule） | Result |
|---|---|
| 1. identity confirmed by current authoritative source | PASS（G1） |
| 2. primary source is the same shrine's POI / navigation target | facility point of a reference dataset（see note） |
| 3. latitude / longitude traceable from the primary source | YES（CODH record URL） |
| 4. primary point consistent with visitor-facing identity | address matches exactly |
| 5. independent corroboration | Wikidata point 12.93 m away; item URL not supplied |

Contract / evidence notes（reported, not resolved here）:

- **Primary source type:** repository precedent uses CODH `nrct-poi` points only as corroboration
  （`docs/audit/niigata-h001-g2-position-gate.md`）. No earlier record adopts one as the primary anchor.
- **Corroboration traceability:** the Wikidata corroboration has no item URL or QID, so it is not
  reproducible from this record.
- **Independence:** whether the Wikidata coordinate was derived from the CODH dataset is not verified.

The Mother Ship PASS stands as recorded.

## Boundary

No change to Candidate Master, Base Seed, Knowledge Seed, Production, Recommendation / Ranking /
Meaning. G2 is not frozen.
