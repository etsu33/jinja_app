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
MOTHER_SHIP_PRIMARY_SOURCE_DECISION = CODH_FACILITY_POINT_ACCEPTED_AS_PRIMARY（candidate-specific, 2026-10-19）
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

Contract / evidence note（first recorded 2026-10-18）:

- Repository precedent had used CODH `nrct-poi` facility points only as an **independent facility
  point / corroboration**（`docs/audit/niigata-h001-g2-position-gate.md`, nsrc-000003）.
- No current map-provider POI or official visitor navigation target is persisted for this candidate.
- The contract lists "public or semi-public position material consistent with current identity" as an
  acceptable primary, and leaves that call to Mother Ship.

## Mother Ship primary-source decision（2026-10-19）

```text
decision       = CODH 日本歴史地名大系 facility point accepted as the primary position source
scope          = nsrc-000022 only（candidate-specific）
global rule    = NONE. CODH does not automatically qualify as primary for any other candidate.
status_after     = PASS（kept）
```

The precedent note above is resolved for this candidate by that decision. No corroboration was
supplied. The contract requires corroboration only where a conflict exists, and none is observed.

## Boundary

No change to Candidate Master, Base Seed, Knowledge Seed, Production, Recommendation / Ranking /
Meaning. G2 is not frozen.
