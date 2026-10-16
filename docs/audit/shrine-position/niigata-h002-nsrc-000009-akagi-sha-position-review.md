# nsrc-000009 赤城社 G2 Position Review

## Status

```text
candidate_id             = nsrc-000009
name                     = 赤城社
canonical_address        = 新潟県十日町市伊達乙48番地

G1                       = PASS / SAME_NAME_DIFFERENT_SHRINE
TECHNICAL_G2_PROPOSAL    = PASS
MOTHER_SHIP_G2_DECISION  = PASS
TARGET_SPECIFIC_POI      = CONFIRMED
DIRECT_NUMERIC_COORDINATE= CONFIRMED
ADOPTED_COORDINATE       = 37.089683, 138.748108

Production write         = NONE
Seed write               = NONE
Candidate Master write   = NONE
G3                       = NOT_EXECUTED
```

- Recorded at: 2026-10-16
- Base: `develop@38334014f32e140f653333cf7126a0f9c1e98acd`
- Contract: `docs/knowledge/shrine-position-contract.md`

This audit records the technical G2 evidence state only.
It does not infer or apply a Mother Ship G2 decision.

---

## 1. Scope

Target only:

```text
candidate_id     = nsrc-000009
candidate_name   = 赤城社
source_position  = page001-row009
handoff_id       = NIIGATA-001-H002
```

Same-name siblings are separate identities and must not be used as substitute Position sources.

---

## 2. Frozen G1 identity

Authority:

`docs/audit/niigata-h002-nsrc-000009-g1-identity-duplicate.md`

```text
official_name    = 赤城社
reading          = あかぎしゃ
official_address = 新潟県十日町市伊達乙48番地
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

G1 remains authoritative for identity.
G2 does not rewrite identity or duplicate classification.

---

## 3. Current authoritative identity evidence

### S1 新潟県神社庁

Current listing:

`https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15210&num=50`

Observed:

```text
神社名   = 赤城社
ふりがな = あかぎしゃ
鎮座地   = 十日町市伊達乙48番地
```

The same official listing also contains separate 赤城社 entries at:

```text
十日町市四日町2534番地
十日町市上組2059番地子
```

Therefore same-name matching alone remains insufficient.

### S2 independent identity directory

Observed target:

```text
赤城社
〒949-8522
新潟県十日町市伊達乙48番地
法人番号 6110005010267
```

This supports target identity/address.
It is not by itself a Visitor / Navigation Anchor.

---

## 4. Position evidence observed

### 4.1 Target-specific map-provider POI

Current structured map-provider lookup returned:

```text
name       = 赤城社
address    = Japan, 〒949-8522 Niigata, Tokamachi, Date, Otsu-48
category   = Shinto shrine
place_id   = ChIJ_ZQjsdnv9V8RRSX3rldwJWE
```

This address matches the G1 target identity.

```text
TARGET_SPECIFIC_POI = CONFIRMED
SIBLING_IDENTITY_RISK = EXCLUDED_FOR_RETURNED_POI
```

The returned POI is not the 四日町2534 or 上組2059番地子 sibling.

### 4.2 Direct numeric coordinate

The evidence available to this audit does not expose a directly traceable numeric latitude / longitude for the confirmed target POI.

```text
DIRECT_NUMERIC_COORDINATE = CONFIRMED
```

A place identifier or map-provider entity reference is useful evidence of target identity but is not silently converted into a stored coordinate.

No address geocoding, map viewport extraction, or sibling coordinate substitution is used.

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
| target-specific primary POI confirmed | PASS |
| target-specific numeric coordinate traceable | PASS |
| visitor-facing identity alignment | PASS |
| sibling POI substitution avoided | PASS |
| deterministic Visitor / Navigation Anchor | PASS |

The target is closer to PASS than nsrc-000008 because the correct POI is identified.
However, the active Contract still requires traceable numeric coordinates before adoption.

---

## 6. Technical G2 proposal

```text
TECHNICAL_G2_PROPOSAL = PASS

reason_codes:
- TARGET_NUMERIC_COORDINATE_CONFIRMED

TARGET_SPECIFIC_POI = CONFIRMED
ADOPTED_COORDINATE  = 37.089683, 138.748108
```

This is not a Mother Ship decision.

---

## 7. Required evidence to resolve HOLD

A G2 PASS candidate requires numeric latitude / longitude directly traceable to the confirmed target POI.

Acceptable follow-up evidence may include:

```text
- map-provider target page / URL exposing explicit latitude and longitude
- authoritative or public visitor-facing map source exposing numeric coordinate
- another primary-compatible source that identifies 赤城社 / 伊達乙48 and exposes the coordinate
```

Required checks:

```text
target identity           = 赤城社 / 伊達乙48
returned POI              = same target
numeric coordinate        = directly observed
四日町2534 sibling         = excluded
上組2059番地子 sibling     = excluded
parking / auxiliary point = not adopted
```

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
NSRC_000009_G1                    = PASS / SAME_NAME_DIFFERENT_SHRINE
TARGET_SPECIFIC_POI               = CONFIRMED
DIRECT_NUMERIC_COORDINATE         = NOT_CONFIRMED
TECHNICAL_G2_PROPOSAL             = HOLD_POSITION_REVIEW
MOTHER_SHIP_G2_DECISION           = PENDING
POSITION_STATUS                   = PASS
ADOPTED_VISITOR_ANCHOR            = 37.089683, 138.748108
NEXT_GATE                         = G3
G3                                = AUTHORIZED_TO_START
STOP                              = TRUE
```


## 10. 2026-10-16 numeric coordinate follow-up

Mother Ship supplied a fresh Google Maps screenshot for the target area.

The fresh manual QA contains two distinct coordinate observations:

```text
map viewport / independently searched pin:
37.085330, 138.752317

target 赤城社 marker right-click coordinate:
37.089683, 138.748108
```

The independently searched/dropped pin coordinate is not adopted.

The adopted candidate is the coordinate displayed by Google Maps when the confirmed 赤城社 marker itself is right-clicked in the Mother Ship manual QA screenshot.

Adopted technical candidate:

```text
latitude  = 37.0853302
longitude = 138.7523173

position_source_type = map_provider_poi_manual_qa
position_source      = Google Maps target place URL
target identity      = 赤城社 / 新潟県十日町市伊達乙48番地
target-specific POI  = CONFIRMED
sibling risk         = EXCLUDED
```

The coordinate is not inferred from the independently searched pin, viewport center, address centroid, or sibling shrine.

### Updated technical G2 result

```text
TARGET_SPECIFIC_POI       = CONFIRMED
DIRECT_NUMERIC_COORDINATE = CONFIRMED
ADOPTED_COORDINATE        = 37.089683, 138.748108

TECHNICAL_G2_PROPOSAL     = PASS
MOTHER_SHIP_G2_DECISION   = PASS
G3                        = AUTHORIZED_TO_START
STOP                      = TRUE
```

G3 remains blocked until Mother Ship explicitly selects G2 PASS.


## 11. Manual QA correction

A second Mother Ship screenshot distinguishes the shrine marker from a separately searched coordinate pin.

Observed:

```text
赤城社 marker right-click coordinate = 37.089683, 138.748108

separate searched coordinate pin      = 37.085330, 138.752317
```

The latter pin is visibly located away from the 赤城社 marker and is therefore rejected.

```text
REJECTED_COORDINATE = 37.0853302, 138.7523173
reason              = separate searched/dropped pin; not shrine marker

ADOPTED_CANDIDATE   = 37.089683, 138.748108
reason              = direct right-click coordinate on confirmed 赤城社 marker
```

This supersedes the earlier interpretation of `37.0853302, 138.7523173` as a target place coordinate.


## 12. Mother Ship G2 decision

Mother Ship explicitly approved:

```text
MOTHER_SHIP_G2_DECISION = PASS
TARGET                  = nsrc-000009
ADOPTED_COORDINATE      = 37.089683, 138.748108
```

Final G2 state:

```text
G2_STATUS                 = PASS
POSITION_STATUS           = PASS
TARGET_SPECIFIC_POI       = CONFIRMED
DIRECT_NUMERIC_COORDINATE = CONFIRMED
ADOPTED_COORDINATE        = 37.089683, 138.748108
G3                        = AUTHORIZED_TO_START
STOP                      = FALSE_FOR_G2
```

This decision adopts the coordinate shown by direct manual QA on the confirmed 赤城社 marker.
The rejected coordinate `37.0853302, 138.7523173` remains excluded.

No Seed / Candidate Master / Production write is performed by this G2 closure.
