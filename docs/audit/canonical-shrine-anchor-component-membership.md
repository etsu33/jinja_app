# Canonical Shrine Anchor — Component Membership Policy (A-7b) and A-5B Evidence Packet Contract

## Status

- Status: `MOTHER_SHIP_DECISION_RECORDED`
- Recorded at: `2026-09-23`
- Closes: `A-7b` (component-membership half of `A-7`)
- Defines: the `A-5B` Evidence Packet field contract
- Active Position Contract: `docs/knowledge/shrine-position-contract.md` (unchanged)
- Canonical Shrine Anchor Contract state: `PROPOSED` (unchanged)
- Production write: `NONE`
- Base Seed write: `NONE`
- Schema change: `NONE`
- Coordinate acquisition or inference: `NONE`
- `A-5_DECISION`: not selected by this document (already recorded in `canonical-shrine-anchor-unadjudicated-migration-policy.md` §10)
- `GATE_SELECTED`: `NONE`

本書は Contract の変更ではない。`docs/knowledge/shrine-position-contract.md` の
authority は変更されない。

## 1. Scope and Relation to Existing Records

| Document | Holds |
| --- | --- |
| `docs/knowledge/shrine-position-contract.md` | ACTIVE contract. `Shrine.latitude / longitude = Visitor / Navigation Anchor` |
| `docs/audit/canonical-shrine-anchor-contract-impact.md` | Impact of the PROPOSED Canonical Shrine Anchor Contract; raised `A-1`–`A-6` |
| `docs/audit/canonical-shrine-anchor-unadjudicated-migration-policy.md` | `A-5 = RESOLVED`; `MIGRATION_POLICY = ADDITIVE_STAGED_NO_SILENT_REINTERPRETATION` |
| `docs/audit/shrine-orientation-evidence-pilot.md` | Evidence-supply pilot; recorded the egress-blocked source state |
| **this document** | `A-7b` component-membership policy + `A-5B` Evidence Packet field contract |

`A-7` established the representative point (`UNWEIGHTED_COMPONENT_MEAN`) and the
semantic owner (full principal ritual complex). `A-7b` closes the remaining half:
**which components constitute that complex, and how membership is established.**

This document does not re-decide `A-5`, does not select a Migration Gate, and does
not acquire, infer, or record any coordinate.

## 2. A-7b Decision

```text
A-7b_COMPONENT_MEMBERSHIP_POLICY
= AUTHORITATIVE_PRINCIPAL_ENSHRINEMENT_UNIT
```

### 2.1 Rules (as decided)

```text
1. All INCLUDED classifications require authoritative evidence.

2. The authoritative-source requirement applies equally to:
   - single principal sanctuary components
   - multiple co-equal honden
   - multiple primary sanctuary components

3. A component must be classified as exactly one of:
   - INCLUDED
   - EXCLUDED
   - UNCLASSIFIED

4. Absence of INCLUDE evidence does NOT imply EXCLUDED.

5. UNCLASSIFIED is used when available evidence is insufficient
   to establish INCLUDE or EXCLUDE.

6. UNWEIGHTED_COMPONENT_MEAN must not be calculated unless:
   COMPONENT_SET_STATUS = COMPLETE.

7. COMPONENT_SET_STATUS may be COMPLETE when authoritative evidence
   establishes the complete constituent set of the principal
   enshrinement unit and no unresolved component affecting that set
   remains UNCLASSIFIED.

8. Do not require classification of every structure on shrine grounds.
   The completeness requirement applies only to the principal
   enshrinement unit.
```

### 2.2 Classification state set

```text
INCLUDED      authoritative evidence identifies the component as a constituent
              of the principal enshrinement unit (Rule 1, Rule 2)

EXCLUDED      a positive determination that the component is not a constituent
              — by category under PRINCIPAL_RITUAL_COMPONENT_RULE, or by an
              authoritative source

UNCLASSIFIED  available evidence is insufficient to establish either (Rule 5)
```

The three values are exhaustive and mutually exclusive (Rule 3).

### 2.3 Completeness gate

```text
COMPONENT_SET_STATUS = COMPLETE
  requires BOTH:
    (a) authoritative evidence establishes the COMPLETE constituent set of the
        principal enshrinement unit; AND
    (b) no component that would affect that set remains UNCLASSIFIED

COMPONENT_SET_STATUS = INCOMPLETE
  otherwise

UNWEIGHTED_COMPONENT_MEAN
  computable ONLY when COMPONENT_SET_STATUS = COMPLETE   (Rule 6)
```

Condition (b) is bounded by Rule 8: a structure on the grounds that does not bear on
the principal enshrinement unit may remain unclassified without blocking `COMPLETE`.
Completeness is a property of the unit, not of the precinct.

This gate is the operational form of `PARTIAL_COMPONENT_CANONICAL_POINT = PROHIBITED`
(`canonical-shrine-anchor-unadjudicated-migration-policy.md` §10), and it is what
"the A-7 complete-component representative-point rule" in that document's §6 step 4
refers to.

## 3. What A-7b Resolves

### 3.1 The co-equal-honden ambiguity — CLOSED

The `PRINCIPAL_RITUAL_COMPONENT_RULE` INCLUDE clause has two limbs. The first is
explicitly source-gated ("when an authoritative source identifies it"); the second
("Multiple co-equal honden … when they jointly constitute that principal enshrinement
unit") does not repeat the phrase, leaving open whether it inherits the requirement.

Rule 2 closes this: the authoritative-source requirement applies **equally** to single
components, multiple co-equal honden, and multiple primary sanctuary components.

```text
CO_EQUAL_HONDEN_SOURCE_REQUIREMENT = SAME_AS_SINGLE_COMPONENT
```

No shrine's component set may be established from the self-evidence of its own
architectural form.

### 3.2 The EXCLUDE-list catch-all gap — CLOSED

`PRINCIPAL_RITUAL_COMPONENT_RULE` enumerates ten excluded categories (gates,
corridors, approach structures, parking / visitor facilities, museums, administrative
buildings, detached auxiliary shrines, detached memorial / mausoleum complexes,
secondary worship complexes) with no catch-all. A ritual structure belonging to
neither list — a registered 祝詞舎, or 幣殿 / 透塀 / 玉垣 — had no rule disposition.

Rules 3, 5 and 8 close this jointly:

- Rule 3 supplies the missing third value, so such a component is **`UNCLASSIFIED`**,
  not silently dropped and not silently excluded.
- Rule 8 bounds the consequence: an `UNCLASSIFIED` structure blocks `COMPLETE` only
  when it bears on the principal enshrinement unit.

```text
UNENUMERATED_RITUAL_STRUCTURE -> UNCLASSIFIED
BLOCKS_COMPLETENESS           -> only if it affects the principal enshrinement unit
```

### 3.3 Reconciliation — where `EXCLUDED` comes from

Rule 4 ("absence of INCLUDE evidence does NOT imply EXCLUDED") and the
`PRINCIPAL_RITUAL_COMPONENT_RULE` EXCLUDE list can be misread as conflicting. They are
not, and the distinction must be preserved in every packet:

```text
EXCLUDED      arises from a POSITIVE act:
                category membership under PRINCIPAL_RITUAL_COMPONENT_RULE
                (a gate is excluded because it is a gate), or an
                authoritative-source statement.

UNCLASSIFIED  arises from ABSENCE: no INCLUDE evidence and no applicable
                exclusion category.
```

The category-based EXCLUDE list remains rebuttable by its own `UNLESS` clause: an
authoritative source explicitly identifying an enumerated component as a constituent
of the principal main sanctuary moves it to `INCLUDED`.

### 3.4 Reporting correction

An earlier report in this workstream recorded the component set of each A-5B target
shrine as:

```text
component set = {}          <- INCORRECT NOTATION
```

Under Rule 4 that notation asserts more than the evidence supports: `{}` reads as an
established empty set, which would be an exclusion determination. The correct record
for the current evidence state is:

```text
COMPONENT_SET_STATUS = INCOMPLETE
candidate components = UNCLASSIFIED
UNWEIGHTED_COMPONENT_MEAN = NOT_COMPUTABLE (Rule 6)
```

No classification, displacement, or mean derived from the `{}` notation exists or was
carried forward.

### 3.5 What A-7b does not resolve

```text
A-7b establishes HOW membership is determined.
A-7b does NOT determine membership for any shrine.
```

Determination requires authoritative sources. The evidence-supply state for those
sources is recorded in `docs/audit/shrine-orientation-evidence-pilot.md`; no source
was retrievable in that environment, and this document acquires none.

## 4. A-5B Evidence Packet Contract

An A-5B Evidence Packet is the per-shrine record that carries a component-membership
determination and, when and only when `COMPONENT_SET_STATUS = COMPLETE`, the derived
representative point and its displacement.

### 4.1 Fields

#### F-1 `principal_unit_source`

```text
requirement : REQUIRED
holds       : the authoritative source establishing WHAT the principal
              enshrinement unit is for this shrine
shape       : source_title / source_owner / source_type / source_url /
              publication_or_update_date / exact_claim_supported
```

This field answers "what is the unit", distinctly from F-2, which answers "what belongs
to it". A packet whose F-1 is absent cannot reach `COMPLETE`, because Rule 7 condition
(a) requires evidence of the complete constituent set, which presupposes the unit's
identity.

#### F-2 `component_membership_evidence`

```text
requirement : REQUIRED, one entry per candidate component
holds       : the evidence bearing on THAT component's classification
shape       : component_name / source_title / source_owner / source_type /
              source_url / publication_or_update_date /
              exact_claim_supported / evidence_strength
```

`evidence_strength` uses the scale already established for this workstream:

```text
E1_AUTHORITATIVE  cultural-property authority / government / shrine official
                  direct statement
E2_SCHOLARLY      university / public research institution / specialist
                  architectural research
E3_MEASURED       official or scholarly measured drawing / plan /
                  GIS-quality spatial evidence
E4_CORROBORATION  map / aerial imagery / non-semantic spatial corroboration
```

`E4` alone never supports an `INCLUDED` classification: Rule 1 requires authoritative
evidence, and corroboration-tier material is not authoritative for membership.

A component recorded with no entry is `UNCLASSIFIED`, never omitted.

#### F-3 `component_classification`

```text
requirement : REQUIRED, one value per candidate component
values      : INCLUDED | EXCLUDED | UNCLASSIFIED        (Rule 3, exhaustive)
shape       : component_name / classification / basis
```

`basis` must state which mechanism produced the value:

```text
INCLUDED      -> the F-2 entry that identifies it as a constituent
EXCLUDED      -> the PRINCIPAL_RITUAL_COMPONENT_RULE category invoked,
                 or the authoritative-source statement
UNCLASSIFIED  -> which of INCLUDE / EXCLUDE could not be established, and why
```

A `basis` reading "no evidence found" on an `EXCLUDED` row is invalid — that is Rule 4.

#### F-4 `set_completeness`

```text
requirement : REQUIRED
values      : COMPLETE | INCOMPLETE
shape       : status / rule_7a_justification / rule_7b_justification /
              unclassified_components_not_affecting_the_unit
```

`rule_7a_justification` cites the authoritative evidence establishing the **complete**
constituent set — not merely that the listed components belong, but that no further
component does.

`rule_7b_justification` states that no `UNCLASSIFIED` component affects the set, and,
per Rule 8, lists the unclassified structures judged not to bear on the principal
enshrinement unit together with the ground for that judgement.

#### F-5 `included_component_coordinates`

```text
requirement : REQUIRED when F-4 = COMPLETE; PROHIBITED otherwise
holds       : one coordinate per INCLUDED component, and no others
shape       : component_name / latitude / longitude /
              coordinate_reference (WGS84 unless stated)
```

Coordinates for `EXCLUDED` or `UNCLASSIFIED` components must not appear. A packet that
carries coordinates while `F-4 = INCOMPLETE` is invalid: it is the shape from which a
partial-component point would be computed.

#### F-6 `coordinate_provenance`

```text
requirement : REQUIRED, one entry per F-5 coordinate
shape       : component_name / source_title / source_owner / source_type /
              source_url / retrieval_or_publication_date /
              extraction_method / evidence_strength / stated_precision
```

`extraction_method` records how the number was obtained from the source (stated in the
record text / read from a measured drawing / map-provider record centre / other), so a
later reader can reproduce it.

Per the established rule of this workstream: a coordinate stated only as prose
direction or as an unquantified description is not a coordinate. No degree value is
invented from descriptive text.

#### F-7 `calculated_mean`

```text
requirement : REQUIRED when F-4 = COMPLETE; PROHIBITED otherwise   (Rule 6)
shape       : latitude / longitude / component_count / calculation_note
definition  : unweighted arithmetic mean of the F-5 latitudes and of the
              F-5 longitudes, over exactly the INCLUDED components
```

`component_count` must equal the number of `INCLUDED` rows in F-3 and the number of
F-5 entries. Any mismatch invalidates the packet.

The mean is not required to coincide with any physical component; for a row of
co-equal honden it will generally fall between them.

#### F-8 `displacement`

```text
requirement : REQUIRED when F-7 is present; PROHIBITED otherwise
shape       : from_coordinate / from_coordinate_meaning / to_coordinate /
              displacement_m / method
method      : geodesic, consistent with distance_m semantics
              (A-3: geodesic straight-line proximity indicator)
```

`from_coordinate_meaning` must name what the current value is (Visitor / Navigation
Anchor, `LEGACY_UNTRACED`, or an adopted-but-unwritten value), because the displacement
is meaningless without it.

Recording a displacement is not an adjudication and does not make the mean a Canonical
Shrine Anchor. Adoption remains subject to the batch procedure in
`canonical-shrine-anchor-unadjudicated-migration-policy.md` §6.

### 4.2 Gate order

Fields must be satisfied in order. A packet may stop at any point and remain valid as
a partial record; it may not skip forward.

```text
F-1  principal_unit_source
 |
F-2  component_membership_evidence
 |
F-3  component_classification            (INCLUDED / EXCLUDED / UNCLASSIFIED)
 |
F-4  set_completeness  -- INCOMPLETE --> STOP. Packet valid and closed here.
 |                                       No F-5 / F-6 / F-7 / F-8.
 COMPLETE
 |
F-5  included_component_coordinates
 |
F-6  coordinate_provenance
 |
F-7  calculated_mean
 |
F-8  displacement
```

### 4.3 Packet validation

```text
V-1  every candidate component carries exactly one F-3 value         (Rule 3)
V-2  no F-3 = EXCLUDED row has a basis of mere absence               (Rule 4)
V-3  no F-3 = INCLUDED row rests on E4 alone                         (Rule 1)
V-4  F-4 = COMPLETE requires both 7a and 7b justifications           (Rule 7)
V-5  F-5 / F-7 absent whenever F-4 = INCOMPLETE                      (Rule 6)
V-6  F-7.component_count == count(F-3 = INCLUDED) == count(F-5)
V-7  F-8 present only when F-7 present
V-8  no coordinate anywhere in the packet lacks an F-6 entry
V-9  unclassified structures outside the principal enshrinement unit
     do not block COMPLETE, and are listed under F-4                 (Rule 8)
```

## 5. Current State of the A-5B Target Shrines Under A-7b

Recorded for continuity. No evidence was acquired for this document.

| Shrine | F-1 | F-3 | `COMPONENT_SET_STATUS` | F-7 | Packet stops at |
| --- | --- | --- | --- | --- | --- |
| 春日大社 | absent | all candidates `UNCLASSIFIED` | `INCOMPLETE` | `NOT_COMPUTABLE` | F-4 |
| 宇佐神宮 | absent | all candidates `UNCLASSIFIED` | `INCOMPLETE` | `NOT_COMPUTABLE` | F-4 |
| 日光東照宮 | absent | all candidates `UNCLASSIFIED` | `INCOMPLETE` | `NOT_COMPUTABLE` | F-4 |

```text
A-5B_DISPLACEMENT_MEASURED = 0 / 3
A-5B_CLASSIFICATION        = INSUFFICIENT_EVIDENCE (all three, unchanged)
```

Under Rule 8 this is not a statement that the precincts are unclassified. It is a
statement that the principal enshrinement unit's constituent set is not established
for any of the three, and that Rule 6 therefore forbids computing a mean.

The blocking input remains the authoritative-source supply recorded in
`docs/audit/shrine-orientation-evidence-pilot.md`. `A-7b` changes what a supplied
packet must contain; it does not change whether one is available.

## 6. Required Statements

```text
1. No Production data was changed.
2. No Base Seed data was changed.
3. No schema was changed.
4. No shrine coordinate was acquired, inferred, modified, or recorded.
5. No migration was created.
6. No ranking, distance, or navigation behavior was changed.
7. docs/knowledge/shrine-position-contract.md is unchanged and remains authoritative.
8. The Canonical Shrine Anchor Contract remains PROPOSED.
9. A-5_DECISION is not selected or altered by this document.
10. GATE_SELECTED = NONE.
```

## 7. STOP

```text
A-7b                      = RESOLVED
COMPONENT_MEMBERSHIP_POLICY = AUTHORITATIVE_PRINCIPAL_ENSHRINEMENT_UNIT
A-5B_EVIDENCE_PACKET      = CONTRACT_DEFINED (F-1 .. F-8)
A-5B_PACKETS_SUPPLIED     = 0 / 3
GATE_SELECTED             = NONE
```

Next action requires an A-5B Evidence Packet satisfying §4 for at least one shrine,
or an egress allowance for the source leads recorded in
`docs/audit/shrine-orientation-evidence-pilot.md` §4.
