# Canonical Shrine Anchor — P2 Multi-building Representation Decision

## Status

- Status: `MOTHER_SHIP_DECISION_RECORDED`
- Recorded at: `2026-09-23`
- Decision subject: `A-7 P2 multi-building Canonical representation`
- Active Position Contract: `docs/knowledge/shrine-position-contract.md`
- Orientation Evidence Contract: `docs/knowledge/shrine-orientation-evidence-contract.md`
- A-4 audit: `docs/audit/canonical-shrine-anchor-multi-ritual-center-audit.md`
- A-6 audit: `docs/audit/canonical-shrine-anchor-georeference-traceability-audit.md`
- Canonical Shrine Anchor Contract state: `PROPOSED`
- Production write: `NONE`
- Base Seed write: `NONE`
- Schema change: `NONE`
- Migration Gate selection: `NONE`

This document records the Mother Ship decision for A-7.
It does not adopt the proposed Canonical Shrine Anchor Contract and does not change
the current ACTIVE meaning:

```text
Shrine.latitude / Shrine.longitude
= Visitor / Navigation Anchor
```

---

## 1. Decision

```text
A-7_DECISION
= P2_RITUAL_COMPLEX_WITH_DERIVED_REPRESENTATIVE_POINT
```

For a P2 case in which the authoritative semantic owner is a multi-building principal
ritual complex with co-principal sanctuaries:

```text
Canonical semantic owner
= full principal ritual complex

Canonical representative point
= deterministic derived point calculated from all verified co-principal component
  coordinates
```

The representative point exists for numeric / geospatial computation.

It is not itself asserted to be:

```text
- a sacred object
- a ritual structure
- a worship position
- a historically privileged point
- a navigation destination
```

---

## 2. Canonical Meaning Separation

The following concepts are distinct.

```text
SEMANTIC_OWNER
= the authoritative principal ritual complex

COMPONENT_SET
= all co-principal ritual structures that constitute that semantic owner

DERIVED_REPRESENTATIVE_POINT
= one deterministic coordinate representing the component set for computation
```

Therefore:

```text
PRIMARY RITUAL COMPLEX
!=
SINGLE PRIMARY BUILDING
!=
DERIVED REPRESENTATIVE POINT
```

A derived point does not create a new ritual hierarchy.

---

## 3. P2 Representative-point Rule

### P2-R1 — Establish semantic owner first

Before any coordinate derivation, authoritative evidence must identify the
`principal ritual complex`.

If semantic ownership is unresolved, no representative point is calculated.

### P2-R2 — Enumerate all co-principal components

All co-principal ritual components that constitute the selected P2 semantic owner must
be explicitly identified.

Examples:

```text
宇佐神宮 上宮
- 一之御殿
- 二之御殿
- 三之御殿

春日大社 御本殿
- 第一殿
- 第二殿
- 第三殿
- 第四殿
```

A component may not be omitted because it is less convenient to georeference.

### P2-R3 — Require subject-matched verified coordinates

Each co-principal component must have a verified coordinate whose geospatial subject
matches that component.

A generic Shrine POI is not a substitute.

```text
generic Shrine POI
!=
verified component coordinate
```

### P2-R4 — Use all verified co-principal components

The derived point must use the complete verified co-principal component set.

No single component receives priority because it is:

```text
- first in numbering
- geographically central
- historically older
- physically larger
- at higher elevation
- a higher-profile cultural property
- more famous
- more visited
- easier to map
```

### P2-R5 — Derivation method

The selected deterministic method is:

```text
POINT_METHOD
= UNWEIGHTED_COMPONENT_MEAN
```

For `n` verified co-principal component coordinates:

```text
representative_lat
= (lat_1 + lat_2 + ... + lat_n) / n

representative_lng
= (lng_1 + lng_2 + ... + lng_n) / n
```

All included components have equal weight.

No religious, architectural, historical, cultural-property, popularity, or spatial
weight is assigned.

### P2-R6 — No hidden substitution

A source-provided point for the complex may be retained as corroboration or provenance,
but it does not silently replace the deterministic component mean unless a future
Contract explicitly changes this rule.

```text
source point exists
!=
automatic Canonical representative point
```

### P2-R7 — Incomplete component set

If any required co-principal component lacks a verified subject-matched coordinate, or
if component identity / coordinate evidence remains materially unresolved:

```text
semantic owner
= may remain CONFIRMED

representative point
= NOT_DETERMINED
```

For a future Canonical-position adoption workflow, this condition terminates as:

```text
HOLD_POSITION_REVIEW
```

The point is not calculated from a partial component set.

---

## 4. Interpretation Boundary

The arithmetic mean is a representation rule, not a religious claim.

```text
DERIVED REPRESENTATIVE POINT
!=
ritual center as a physical sacred spot
```

The point may fall:

```text
- between buildings
- in a courtyard
- on a non-ritual surface
```

without invalidating the representation.

Its meaning is:

```text
a deterministic geospatial representative of an authoritative multi-building
principal ritual complex
```

It must not be described to users as:

```text
- the exact sacred center
- the place where the deity resides
- the worship point
- the correct route destination
```

unless independent evidence separately supports such a claim.

---

## 5. Relationship to Existing Layers

### Orientation Evidence

The ACTIVE Orientation Evidence Contract remains unchanged.

```text
PHYSICAL_ORIENTATION
RITUAL_AXIS
SYMBOLIC_ORIENTATION
```

do not automatically determine the P2 representative point.

### Navigation Anchor

The ACTIVE Position Contract remains unchanged.

```text
Visitor / Navigation Anchor
!=
P2 derived representative point
```

The P2 representative point must not silently become a Google Maps route destination.

### Distance / Compass

This decision does not decide whether product-facing distance uses:

```text
- Navigation Anchor
- Canonical representative point
- another semantics
```

That remains under A-3 / the eventual Migration Gate.

---

## 6. Application to Audited Cases

### 宇佐神宮

A-4 established:

```text
SEMANTIC_OWNER
= 上宮
```

Co-principal set:

```text
一之御殿
二之御殿
三之御殿
```

Under A-7:

```text
CANONICAL_REPRESENTATION
= mean coordinate of all three verified component coordinates

SINGLE_HONDEN_PRIORITY
= PROHIBITED
```

No coordinate is calculated or adopted by this decision record.

### 春日大社

Co-principal set:

```text
第一殿
第二殿
第三殿
第四殿
```

Under A-7:

```text
CANONICAL_REPRESENTATION
= mean coordinate of all four verified component coordinates

SINGLE_HONDEN_PRIORITY
= PROHIBITED
```

No coordinate is calculated or adopted by this decision record.

---

## 7. Determinism Test

Given the same:

```text
- semantic owner
- complete co-principal component set
- verified component coordinates
```

all implementations must produce the same representative point using the same
unweighted arithmetic-mean formula.

Human preference is not part of the calculation.

Therefore the P2 representation rule is reproducible.

---

## 8. Prohibited Rules

The following are explicitly not adopted:

```text
- first-Honden coordinate
- center-Honden coordinate
- oldest-Honden coordinate
- most-important-deity weighting
- cultural-property-rank weighting
- visitor-popularity weighting
- nearest-navigation-node weighting
- generic map-provider POI
- precinct centroid
- arbitrary polygon centroid
- partial-component mean
```

A precinct centroid and the adopted component mean may numerically resemble each
other in some cases, but they are semantically different and must not be conflated.

---

## 9. A-7 Resolution

```text
A-7_P2_MULTI_BUILDING_REPRESENTATION
= RESOLVED

SEMANTIC_OWNER
= FULL_PRINCIPAL_RITUAL_COMPLEX

POINT_METHOD
= UNWEIGHTED_COMPONENT_MEAN

INPUT_REQUIREMENT
= ALL_VERIFIED_CO_PRINCIPAL_COMPONENT_COORDINATES

SINGLE_COMPONENT_PRIORITY
= PROHIBITED

GENERIC_POI_AUTO_ADOPTION
= PROHIBITED

INCOMPLETE_COMPONENT_SET
= HOLD_POSITION_REVIEW

REPRESENTATIVE_POINT_IS_SACRED_SITE
= NO

REPRESENTATIVE_POINT_IS_NAVIGATION_DESTINATION
= NO
```

---

## 10. Migration Gate Effect

This decision removes the P2 representative-point ambiguity identified by A-6.

```text
A-4 = RESOLVED_AT_SEMANTIC_OWNER_LEVEL
A-6 = PARTIALLY_RESOLVED / geospatial supply observed
A-7 = RESOLVED

P2_POINT_POLICY
= RESOLVED
```

The Migration Gate is still not selected.

Remaining open questions include:

```text
A-3 = distanceM semantics
A-5 = migration policy for 103 unadjudicated Production rows
```

---

## 11. Required Statements

```text
1. No Production data was changed.
2. No Base Seed data was changed.
3. No existing PASS / HOLD_POSITION_REVIEW status was changed.
4. The ACTIVE Position Contract remains unchanged.
5. The proposed Canonical Shrine Anchor Contract remains PROPOSED.
6. No Canonical coordinate was calculated or adopted.
7. UNWEIGHTED_COMPONENT_MEAN is a representation rule, not a ritual hierarchy.
8. All co-principal components are required before derivation.
9. A partial component mean is prohibited.
10. The derived point is not a navigation destination.
11. No Migration Gate option was selected.
```
