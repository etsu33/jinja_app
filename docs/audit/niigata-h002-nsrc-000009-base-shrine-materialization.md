# NIIGATA-001-H002 — nsrc-000009 Base Shrine Materialization

## 1. Status

```text
candidate_id                  = nsrc-000009
name_jp                       = 赤城社
address                       = 新潟県十日町市伊達乙48番地

BASE_SHRINE_PREREQUISITE      = REQUIRED_FOR_G4
BASE_SHRINE_MATERIALIZATION   = IMPLEMENTED / CI_PENDING

Base Seed row count           = 124 -> 125
target exact identity count   = 1
duplicate identity            = 0
required fields missing       = 0

Knowledge Seed                = NOT CREATED
FORMAL_G4                     = NOT EXECUTED
G5 / G6 / G7 / G8             = NOT EXECUTED
Production write              = NONE
```

- Recorded at: 2026-10-16
- Base: `develop@68a1d61cfafafcd5725a71078e249462404dc1ec`
- Branch: `feature/nsrc-000009-base-shrine`

## 2. Authority

Identity:

```text
official_name    = 赤城社
official_address = 新潟県十日町市伊達乙48番地
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

Position authority:

```text
position_status = PASS
latitude        = 37.089683
longitude       = 138.748108
```

Sources:
- `docs/audit/niigata-h002-nsrc-000009-g1-identity-duplicate.md`
- `docs/audit/shrine-position/niigata-h002-nsrc-000009-akagi-sha-position-review.md`
- `docs/audit/niigata-h002-nsrc-000009-g3-source-knowledge-fit.md`

## 3. Materialized Base row

```json
{
  "name_jp": "赤城社",
  "address": "新潟県十日町市伊達乙48番地",
  "latitude": 37.089683,
  "longitude": 138.748108,
  "goriyaku": "",
  "kyusei": null,
  "astro_elements": [],
  "location": {
    "lat": 37.089683,
    "lng": 138.748108
  }
}
```

Neutral fields are intentionally preserved.

Not added:
- goriyaku_tags
- visit_style_tags
- history_theme
- Deity / History / Source
- Recommendation fields
- derived Knowledge

## 4. Scope boundary

This PR changes only:
1. Base Seed target row +1;
2. target exact-identity regression;
3. H002 G6 unresolved/ineligible expectation after Base materialization;
4. this audit.

This PR does not create the G4 Knowledge Seed.

```text
Shrine DB presence
!= Recommendation eligibility
```

Until Knowledge is materialized, the target resolves by exact identity but remains `INELIGIBLE`
in the H002 helper that imports Base data without target Knowledge.

## 5. Same-name isolation

H002 contains distinct 赤城社 identities.

```text
四日町2534番地       != nsrc-000009
上組2059番地子       != nsrc-000009
伊達乙48番地         =  nsrc-000009
南魚沼市芹田79番地   != nsrc-000009
```

The materialization and tests use exact `(name_jp, address)` identity only.

## 6. Acceptance target

CI must prove:

```text
Base Seed count                 = 125
exact target rows               = 1
target coordinate               = 37.089683 / 138.748108
resolve_shrine exact target     = OK
other same-name addresses       != target
duplicate (name,address)        = 0
G6 H002 state:
  nsrc-000006 = INELIGIBLE
  nsrc-000007 = INELIGIBLE
  nsrc-000008 = UNRESOLVED
  nsrc-000009 = INELIGIBLE
  nsrc-000010 = UNRESOLVED
Production write                = NONE
```

## 7. STOP

Do not create Knowledge Seed or execute Formal G4 in this PR.

Next after merge:

```text
nsrc-000009 G4 Source Packet Freeze / Knowledge Fact + Evidence
```
