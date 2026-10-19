# nsrc-000021 荒川神社 G2 Position Review

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000021
position_status          = HOLD_POSITION_REVIEW
new_latitude             = NONE
new_longitude            = NONE
new_position_source_type = NONE
new_position_source_url  = NONE
verified_at              = 2026-10-18
TECHNICAL_G2_PROPOSAL    = HOLD_POSITION_REVIEW
MOTHER_SHIP_G2_DECISION  = PENDING
ADOPTED_COORDINATE       = NONE
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
```

- Recorded at: 2026-10-18
- Base: `develop@225352c5`（PR #3266 merge, VPG001 G2 bootstrap）
- Contract: `docs/knowledge/shrine-position-contract.md`
- G2 audit: `docs/audit/niigata-vpg001-g2-position-review.md`

Evidence level: `MOTHER_SHIP_SUPPLIED`. The sources below were supplied by Mother Ship on 2026-10-18.
They were not re-fetched in this environment（its network policy denies the hosts）. Values are recorded
exactly as supplied.

## Canonical identity（G1, unchanged）

```text
official_name    = 荒川神社
official_address = 新潟県胎内市桃崎浜187番地
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

Same-name rows in the frozen Ready Set（新発田市荒川5431番地, 村上市小岩内463番地, 村上市荒川542番地）are
different shrines and are not used as position sources.

## Evidence supplied

### Numeric coordinate（one source）

```text
source_provider = 國學院大學デジタル・ミュージアム / 式内社データベース
source_type     = independent_shrine_reference_database
record          = 荒川神社（胎内市）
source_url      = https://jmapps.ne.jp/kokugakuin/det.html?data_id=182468
latitude        = 38.140916
longitude       = 139.407516
```

The supplied record identifies the shrine by name and municipality（胎内市）. The locality 桃崎浜 is not
stated in the supplied record text.

### Identity corroboration（no coordinate）

```text
新潟県観光協会（official tourism site）
  address = 新潟県胎内市桃崎浜187
  url     = https://niigata-kankou.or.jp/spot/7288

文化庁 国指定文化財等データベース
  record  = 荒川神社本殿
  address = 新潟県胎内市桃崎浜187
  url     = https://kunishitei.bunka.go.jp/bsys/maindetails/101/00013085
```

Both confirm the visitor-facing identity at 桃崎浜187. Neither supplies a numeric coordinate. The 文化庁
record names a building（本殿）, not the shrine as a navigation target.

## Position Contract evaluation

| Requirement（Source Adoption Rule） | Result |
|---|---|
| 1. identity confirmed by current authoritative source | PASS（観光協会, 文化庁, G1） |
| 2. primary source is the same shrine's POI / navigation target | NOT ESTABLISHED |
| 3. latitude / longitude traceable from the primary source | 國學院 record only |
| 4. primary point consistent with visitor-facing identity | NOT ESTABLISHED（locality not in the supplied record） |
| 5. independent corroboration where needed | ABSENT（only one numeric source） |

Independence assessment:

```text
numeric sources supplied               = 1（國學院）
independent numeric corroboration      = NONE
identity sources（観光協会, 文化庁）    = independent of 國學院, but carry no coordinate
```

Two numeric sources are needed before independence can be assessed. Only one exists, so the
independence requirement is **not met**. Identity-only sources cannot corroborate a coordinate.

Repository precedent（`docs/audit/niigata-h001-g2-position-gate.md`,
`docs/audit/position-audit-v2/legacy-position-provenance-batch01.md`）uses 國學院 records only as
`independent_shrine_reference_database` **corroboration** of a map-provider POI primary. No
repository record adopts a 國學院 point as the primary Visitor / Navigation Anchor.

## Technical G2 proposal

```text
TECHNICAL_G2_PROPOSAL = HOLD_POSITION_REVIEW

reason_codes:
- INDEPENDENT_NUMERIC_CORROBORATION_ABSENT
- PRIMARY_POI_OR_NAVIGATION_TARGET_NOT_ESTABLISHED
- REFERENCE_DATABASE_ONLY

candidate_coordinate（not adopted） = 38.140916, 139.407516（國學院）
ADOPTED_COORDINATE                = NONE
```

No coordinate is inferred from the address. Mother Ship has not decided this candidate.

## Required to resolve

One of:

- a current map-provider POI or official visitor navigation target for 荒川神社 / 胎内市桃崎浜187 with a
  directly traceable numeric coordinate, with the 國學院 point as independent corroboration; or
- a second numeric source that is independent of 國學院, with a Mother Ship decision on which source is
  primary.

## Boundary

No change to Candidate Master, Base Seed, Knowledge Seed, Production, Recommendation / Ranking /
Meaning. G2 is not frozen.
