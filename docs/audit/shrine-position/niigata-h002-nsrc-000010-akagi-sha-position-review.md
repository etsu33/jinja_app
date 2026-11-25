# nsrc-000010 赤城社 G2 Position Review

## Status

```text
candidate_id             = nsrc-000010
name                     = 赤城社
canonical_address        = 新潟県南魚沼市芹田79番地

G1                       = PASS / SAME_NAME_DIFFERENT_SHRINE
TECHNICAL_G2_PROPOSAL    = HOLD_POSITION_REVIEW
MOTHER_SHIP_G2_DECISION  = HOLD_POSITION_REVIEW

TARGET_SPECIFIC_POI      = CONFIRMED_WITH_DISCREPANCY
DIRECT_NUMERIC_COORDINATE= CONFIRMED
OBSERVED_COORDINATE      = 37.154010, 138.918580
ADOPTED_COORDINATE       = NONE

POSITION_STATUS          = HOLD_POSITION_REVIEW
Production write         = NONE
Seed write               = NONE
Candidate Master write   = NONE
G3                       = NOT_EXECUTED
NEXT_GATE                = BLOCKED
STOP                     = TRUE
```

- Recorded at: 2026-10-17
- Base: `develop@de658fdd30377446c37814861d8dd9bc34ebf21f`
- Contract: `docs/knowledge/shrine-position-contract.md`

This audit records the G2 Position / Navigation Anchor decision for `nsrc-000010`.
The observed map-provider coordinate is preserved as evidence only and is not adopted as `Shrine.latitude / Shrine.longitude`.

---

## 1. Scope

Target only:

```text
candidate_id     = nsrc-000010
candidate_name   = 赤城社
source_position  = page001-row010
handoff_id       = NIIGATA-001-H002
```

Same-name siblings are separate identities and are not eligible as substitute Position sources.

Known H002 same-name siblings:

```text
nsrc-000007 = 赤城社 / 十日町市四日町2534番地
nsrc-000008 = 赤城社 / 十日町市上組2059番地子
nsrc-000009 = 赤城社 / 十日町市伊達乙48番地
nsrc-000010 = 赤城社 / 南魚沼市芹田79番地
```

---

## 2. Frozen G1 identity

Authority:

`docs/audit/niigata-h002-nsrc-000010-g1-identity-duplicate.md`

```text
official_name    = 赤城社
official_address = 新潟県南魚沼市芹田79番地
reading          = NOT_RECORDED
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

Frozen G0 Source:

```text
page001-row010 | 赤城社 | 南魚沼市芹田79番地 | RUNNER_READY
```

G1 remains authoritative for identity.
G2 does not rewrite the canonical name, address, identity classification, or duplicate classification.

---

## 3. Position Contract boundary

Authority:

`docs/knowledge/shrine-position-contract.md`

The active contract defines:

```text
Shrine.latitude / Shrine.longitude
= Visitor / Navigation Anchor
```

Position adoption requires a same-Shrine visitor/navigation target whose latitude and longitude are traceable and whose relation to the visitor-facing identity is explainable.

When the visitor address and position source cannot be explained consistently, the contract requires:

```text
HOLD_POSITION_REVIEW
```

No address geocoding result, viewport center, same-name sibling coordinate, or unverified POI coordinate may be promoted to the adopted Visitor / Navigation Anchor.

---

## 4. Current authoritative identity evidence

### 4.1 新潟県神社庁 / frozen source lineage

The accepted G1 identity is:

```text
神社名 = 赤城社
鎮座地 = 南魚沼市芹田79番地
```

### 4.2 Corporate / independent identity corroboration

Independent records observed during G2 review also identify:

```text
法人名   = 赤城社
所在地   = 新潟県南魚沼市芹田79番地
法人番号 = 8110005013458
```

These records corroborate the canonical identity.
Per the Position Contract, legal/corporate address evidence is not by itself a Visitor / Navigation Anchor.

---

## 5. Map-provider evidence observed

### 5.1 Target-region confirmation

Mother Ship manual QA confirmed the `芹田` area in 南魚沼市.

```text
TARGET_REGION = CONFIRMED
```

The other H002 same-name 赤城社 candidates are in 十日町市 and are therefore geographically distinct from this target.

```text
SIBLING_COLLISION = EXCLUDED
```

### 5.2 Target-specific shrine POI candidate

A map-provider shrine POI was observed in 芹田:

```text
map_provider_name    = 赤城神社
map_provider_address = 〒949-7311 新潟県南魚沼市芹田877
category             = 神社
```

The POI is in the correct municipality and locality and is not any of the known 十日町市 sibling 赤城社 entries.

However, it does not exactly match the G1 canonical identity:

```text
canonical_name       = 赤城社
map_provider_name    = 赤城神社

canonical_address    = 新潟県南魚沼市芹田79番地
map_provider_address = 新潟県南魚沼市芹田877
```

Therefore:

```text
TARGET_SPECIFIC_POI = CONFIRMED_WITH_DISCREPANCY
```

This record does not infer that `877` is a typo for `79`, nor does it rewrite the canonical address.

---

## 6. Mother Ship manual QA coordinate

Mother Ship opened the 芹田 map-provider POI and right-clicked the shrine marker itself.

Observed numeric coordinate:

```text
latitude  = 37.154010
longitude = 138.918580
```

The coordinate was obtained from the shrine marker, not from:

- map viewport center;
- dropped/searched pin;
- address centroid;
- nearby road point;
- sibling 赤城社 marker.

Therefore:

```text
DIRECT_NUMERIC_COORDINATE = CONFIRMED
OBSERVED_COORDINATE       = 37.154010, 138.918580
```

This observation proves the map-provider POI has a traceable numeric coordinate.

It does not by itself prove that the POI is the exact G1 canonical `赤城社 / 芹田79番地` identity.

---

## 7. Address / name discrepancy

Observed discrepancy:

```text
canonical:
  name    = 赤城社
  address = 新潟県南魚沼市芹田79番地

map provider:
  name    = 赤城神社
  address = 新潟県南魚沼市芹田877
```

Current evidence supports:

```text
CANONICAL_ADDRESS_SIDE = 芹田79番地
MAP_PROVIDER_SIDE      = 芹田877
```

The `79番地` side remains authoritative for canonical identity because it is the accepted G1 identity and is independently corroborated.

The `877` address is preserved only as the map-provider POI address.

The available evidence does not prove:

```text
877 = typo of 79
79  = old address
877 = visitor address
79  = legal-only address
```

Those explanations are not inferred.

---

## 8. Position Contract evaluation

| Requirement | Result |
|---|---|
| current authoritative Shrine identity | PASS |
| same-name sibling collision understood | PASS |
| target-region shrine POI observed | PASS |
| numeric coordinate directly traceable | PASS |
| visitor-facing identity alignment | HOLD |
| canonical address vs POI address explained | HOLD |
| deterministic Visitor / Navigation Anchor | HOLD |

The remaining issue is not lack of a coordinate.
The remaining issue is whether the observed POI can be deterministically identified as the exact canonical `赤城社 / 芹田79番地` Visitor / Navigation Anchor.

Under the active Position Contract, that unresolved identity/address relationship requires `HOLD_POSITION_REVIEW`.

---

## 9. Technical G2 proposal

```text
TECHNICAL_G2_PROPOSAL = HOLD_POSITION_REVIEW

reason_codes:
- CANONICAL_ADDRESS_AND_MAP_POI_ADDRESS_MISMATCH
- CANONICAL_NAME_AND_MAP_POI_NAME_VARIANT_UNRESOLVED
- TARGET_COORDINATE_OBSERVED_BUT_NOT_SAFE_TO_ADOPT

TARGET_SPECIFIC_POI       = CONFIRMED_WITH_DISCREPANCY
DIRECT_NUMERIC_COORDINATE = CONFIRMED
OBSERVED_COORDINATE       = 37.154010, 138.918580
ADOPTED_COORDINATE        = NONE
```

Important:

```text
OBSERVED_COORDINATE != ADOPTED_COORDINATE
```

No coordinate is promoted to Shrine latitude/longitude in this G2 result.

---

## 10. Mother Ship G2 decision

Mother Ship explicitly selected:

```text
MOTHER_SHIP_G2_DECISION = HOLD_POSITION_REVIEW
TARGET                  = nsrc-000010
```

This matches the technical proposal.

Final G2 state:

```text
NSRC_000010_G1                  = PASS / SAME_NAME_DIFFERENT_SHRINE

G2_STATUS                       = HOLD_POSITION_REVIEW
POSITION_STATUS                 = HOLD_POSITION_REVIEW

CANONICAL_NAME                  = 赤城社
CANONICAL_ADDRESS               = 新潟県南魚沼市芹田79番地

MAP_PROVIDER_NAME               = 赤城神社
MAP_PROVIDER_ADDRESS            = 新潟県南魚沼市芹田877

TARGET_SPECIFIC_POI             = CONFIRMED_WITH_DISCREPANCY
DIRECT_NUMERIC_COORDINATE       = CONFIRMED
OBSERVED_COORDINATE             = 37.154010, 138.918580
ADOPTED_COORDINATE              = NONE

SIBLING_COLLISION               = EXCLUDED

G3                              = NOT_EXECUTED
NEXT_GATE                       = BLOCKED
STOP                            = TRUE
```

This HOLD is a controlled Position Gate result, not a failed G1 identity review.

---

## 11. HOLD release condition

The target may be re-opened for G2 only if new Position evidence resolves the canonical-to-POI relationship.

Examples of acceptable follow-up evidence:

```text
- authoritative visitor-facing source linking 赤城社 / 芹田79番地 to the observed shrine POI;
- public map/navigation source that identifies the same physical shrine while explaining the address discrepancy;
- other source-backed evidence that deterministically reconciles the canonical identity with the observed POI.
```

A future re-open must not assume that `79` and `877` are equivalent without evidence.

---

## 12. Boundary

This G2 decision does not change:

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

No Production query or write is required by this audit.
No Seed / Candidate Master / Production coordinate write is authorized.

```text
NSRC_000010_G2 = HOLD_POSITION_REVIEW
ADOPTED_COORDINATE = NONE
G3 = BLOCKED
STOP = TRUE
```
