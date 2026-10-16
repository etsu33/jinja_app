# nsrc-000008 赤城社 G2 Position Review

## Status

```text
candidate_id             = nsrc-000008
name                     = 赤城社
canonical_address        = 新潟県十日町市上組2059番地子

G1                       = PASS / SAME_NAME_DIFFERENT_SHRINE
TECHNICAL_G2_PROPOSAL    = HOLD_POSITION_REVIEW
MOTHER_SHIP_G2_DECISION  = PENDING
ADOPTED_COORDINATE       = NONE
Production write         = NONE
Seed write               = NONE
Candidate Master write   = NONE
G3                       = NOT_EXECUTED
```

- Recorded at: 2026-10-16
- Base: `develop@938e436945cefbd350918b53da1833553a352b1e`
- Contract: `docs/knowledge/shrine-position-contract.md`

This audit records only the technical G2 evidence state.
It does not infer or apply a Mother Ship G2 decision.

---

## 1. Scope

Target only:

```text
candidate_id     = nsrc-000008
candidate_name   = 赤城社
source_position  = page001-row008
handoff_id       = NIIGATA-001-H002
```

Sibling same-name shrines are separate identities and are not eligible as substitute Position sources.

---

## 2. Frozen G1 identity

Current G1 authority:

`docs/audit/niigata-h002-nsrc-000008-g1-identity-duplicate.md`

```text
official_name    = 赤城社
official_address = 新潟県十日町市上組2059番地子
reading          = NOT_RECORDED
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

G1 remains authoritative for identity.
G2 does not rewrite identity or duplicate classification.

---

## 3. Current authoritative identity evidence

### S1 新潟県神社庁

Source:

`https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15210&num=50`

Observed current listing:

```text
神社名   = 赤城社
ふりがな = あかぎしゃ
鎮座地   = 十日町市上組2059番地子
```

The same current official listing also contains separate 赤城社 entries at:

```text
十日町市四日町2534番地
十日町市伊達乙48番地
```

Therefore same-name matching alone is not sufficient for Position adoption.

### S2 corporate identity corroboration

Observed corporation identity:

```text
法人名   = 赤城社
法人番号 = 7110005010266
住所     = 新潟県十日町市上組2059番地子
郵便番号 = 949-8602
```

This corroborates the target identity/address.
Per the Position Contract, corporate/legal address evidence is not by itself a Visitor / Navigation Anchor.

---

## 4. Position evidence observed

### 4.1 Official source map affordance

The 新潟県神社庁 listing exposes a `Google Mapを表示する` affordance for the target row.

However, in the evidence available to this audit, the target-specific map-provider destination did not expose a traceable numeric latitude / longitude for the `上組2059番地子` shrine.

```text
OFFICIAL_MAP_AFFORDANCE              = PRESENT
TARGET_POI_NUMERIC_COORDINATE        = NOT_OBTAINED
```

### 4.2 Map-provider business lookup collision

Current map-provider structured lookup for `赤城社` in 十日町市 returned:

```text
name    = 赤城社
address = 新潟県十日町市伊達乙48
```

This is the sibling `nsrc-000009`, not `nsrc-000008`.

```text
SAME_NAME_COLLISION_OBSERVED = YES
TARGET_ENTITY_MATCH          = FAIL_FOR_RETURNED_POI
```

That POI must not be reused for nsrc-000008.

### 4.3 Third-party directory map material

A current directory page identifies the target as:

```text
赤城社
〒949-8602
新潟県十日町市上組2059番地子
法人番号 7110005010266
```

The page includes map / aerial-photo affordances, but the evidence available to this audit does not expose the map's numeric coordinate as a directly traceable target POI coordinate.

```text
IDENTITY_CORROBORATION       = PASS
PRIMARY_NUMERIC_COORDINATE   = NOT_TRACEABLE
```

No iframe/map center, address geocoding result, pixel position, or same-name sibling coordinate is promoted to Visitor / Navigation Anchor.

---

## 5. Position Contract evaluation

`docs/knowledge/shrine-position-contract.md` requires:

1. current authoritative Shrine identity;
2. same-Shrine primary POI / navigation target;
3. traceable latitude / longitude from that primary source;
4. visitor-facing identity alignment;
5. conflict/collision resolution where necessary.

Current result:

| Requirement | Result |
|---|---|
| current authoritative identity | PASS |
| same-name collision understood | PASS |
| target-specific primary POI confirmed | NOT YET |
| target-specific numeric coordinate traceable | NOT YET |
| address-geocoding inference avoided | PASS |
| sibling POI substitution avoided | PASS |
| deterministic Visitor / Navigation Anchor | NOT YET |

The Contract states that when current primary coordinate cannot be obtained, or the source entity is ambiguous, the status is `HOLD_POSITION_REVIEW`.

---

## 6. Technical G2 proposal

```text
TECHNICAL_G2_PROPOSAL = HOLD_POSITION_REVIEW

reason_codes:
- TARGET_PRIMARY_POI_NOT_CONFIRMED
- TARGET_NUMERIC_COORDINATE_NOT_TRACEABLE
- SAME_NAME_SIBLING_POI_COLLISION_OBSERVED

ADOPTED_COORDINATE = NONE
```

This is not a Mother Ship decision.
No coordinate is inferred from the legal address or from sibling 赤城社 records.

---

## 7. Required evidence to resolve HOLD

A PASS candidate requires a target-specific visitor/navigation source such as:

```text
A. Google Maps / other map-provider POI for
   赤城社 / 十日町市上組2059番地子
   with directly traceable numeric latitude / longitude

or

B. authoritative / public visitor-facing page
   that identifies this exact 赤城社 and exposes a traceable map coordinate
```

Required manual QA if using a map-provider POI:

```text
canonical address / target identity match = PASS
returned POI is 上組2059番地子 target       = PASS
伊達乙48 / 四日町2534 sibling risk          = EXCLUDED
direct numeric coordinate                  = OBSERVED
parking / auxiliary point risk             = NONE_OBSERVED
```

Only after that evidence is recorded may Mother Ship select G2 PASS.

---

## 8. Boundary

This audit does not change:

```text
Candidate Master
Base Seed
Knowledge Seed
Production DB
Recommendation / Ranking
Concierge / Compass
GoriyakuTag
other H002 candidates
```

No coordinate write occurs.

---

## 9. Current gate state

```text
NSRC_000008_G1                    = PASS / SAME_NAME_DIFFERENT_SHRINE
TECHNICAL_G2_PROPOSAL             = HOLD_POSITION_REVIEW
MOTHER_SHIP_G2_DECISION           = PENDING
POSITION_STATUS                   = NOT_CLOSED
ADOPTED_VISITOR_ANCHOR            = NONE
NEXT_GATE                         = BLOCKED
G3                                = NOT_EXECUTED
STOP                              = TRUE
```
