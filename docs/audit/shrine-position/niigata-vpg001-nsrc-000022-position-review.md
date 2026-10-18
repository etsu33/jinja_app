# nsrc-000022 五十嵐神社 G2 Position Review

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000022
position_status          = PASS
new_latitude             = 37.573979
new_longitude            = 139.048758
new_position_source_type = public_reference_dataset_facility_point
new_position_source_url  = https://geoshape.ex.nii.ac.jp/nrct-poi/resource/15/150000311900.html
verified_at              = 2026-10-18
MOTHER_SHIP_G2_DECISION  = PASS（adopted）
CONTRACT_EVIDENCE_NOTE   = PRIMARY_SOURCE_TYPE_PRECEDENT_GAP（see below）
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
environment（network policy denies the host）. Values are recorded exactly as supplied.

## Canonical identity（G1, unchanged）

```text
official_name    = 五十嵐神社
official_address = 新潟県三条市大字飯田2283番地
identity_status  = CONFIRMED
duplicate_status = NEW
```

## Position evidence

```text
source_provider = 『日本歴史地名大系』施設・地点項目データセット / CODH
source_type     = public_reference_dataset_facility_point
source_url      = https://geoshape.ex.nii.ac.jp/nrct-poi/resource/15/150000311900.html
source_address  = 新潟県三条市飯田2283番地
latitude        = 37.573979
longitude       = 139.048758
corroboration   = NONE SUPPLIED
```

Identity match: the source address equals the canonical address except that `大字` is omitted.
That is a notation difference in the same locality and lot.

## Position Contract evaluation

| Requirement（Source Adoption Rule） | Result |
|---|---|
| 1. identity confirmed by current authoritative source | PASS（G1） |
| 2. primary source is the same shrine's POI / navigation target | facility point of a reference dataset（see note） |
| 3. latitude / longitude traceable from the primary source | YES（CODH record URL） |
| 4. primary point consistent with visitor-facing identity | address matches（notation only） |
| 5. independent corroboration where a conflict exists | no conflict observed; no corroboration supplied |

Contract / evidence note（reported, not resolved here）:

- Repository precedent uses CODH `nrct-poi` facility points only as an **independent facility point /
  corroboration**（`docs/audit/niigata-h001-g2-position-gate.md`, nsrc-000003）. No earlier record
  adopts one as the primary Visitor / Navigation Anchor.
- No current map-provider POI or official visitor navigation target is persisted for this candidate.
- The contract lists "public or semi-public position material consistent with current identity" as an
  acceptable primary. Whether this dataset qualifies is Mother Ship's call. This record does not
  decide it.

The Mother Ship PASS stands as recorded.

## Boundary

No change to Candidate Master, Base Seed, Knowledge Seed, Production, Recommendation / Ranking /
Meaning. G2 is not frozen.
