# Canonical Shrine Anchor — Unadjudicated Production Migration Policy

## Status

- Status: `MOTHER_SHIP_POLICY_READY`
- Recorded at: `2026-09-23`
- Open question: `A-5` from `docs/audit/canonical-shrine-anchor-contract-impact.md`
- Subject: migration handling for the 103 Production rows that are not adjudicated under the current Position Batch 01 audit
- Active Position Contract: `docs/knowledge/shrine-position-contract.md`
- Canonical Shrine Anchor Contract state: `PROPOSED`
- Production write: `NONE`
- Base Seed write: `NONE`
- Schema change: `NONE`
- Migration Gate selection: `NONE`

This document defines how unadjudicated rows must be treated **if** a Migration Gate
other than A is later selected.

It does not select Gate B or Gate C and does not change any runtime behavior.

---

## 1. Problem

The current impact audit records:

```text
PRODUCTION_ROWS_IN_SCOPE = 113

BATCH01_ADJUDICATED
= 10
  - PASS = 8
  - HOLD_POSITION_REVIEW = 2

UNADJUDICATED
= 103
```

The 103-row population includes `pk=70`, whose coordinate was remediated previously
under Visitor / Navigation Anchor semantics but was never adjudicated under either
the current Batch 01 audit or the proposed Canonical Shrine Anchor semantics.

The migration risk is not merely missing data.

The risk is **silent semantic reinterpretation**:

```text
existing latitude / longitude
currently understood as Visitor / Navigation Anchor

must not silently become

Canonical Shrine Anchor
without row-level evidence
```

---

## 2. A-5 Policy

```text
A-5_MIGRATION_POLICY
= ADDITIVE_STAGED_NO_SILENT_REINTERPRETATION
```

The governing rules are:

```text
1. Existing unadjudicated coordinates are not Canonical Shrine Anchors by default.

2. Existing latitude / longitude values are not copied into a Canonical field merely
   because a schema or Contract is introduced.

3. Every Canonical value requires explicit row-level adjudication under the future
   Canonical Shrine Anchor Contract.

4. Until that adjudication occurs, Canonical state remains NOT_ADJUDICATED and the
   Canonical coordinate remains absent.

5. Existing Visitor / Navigation Anchor data remains intact during the Canonical
   backfill process.

6. Runtime consumers do not switch row-by-row between Navigation semantics and
   Canonical semantics under one field meaning.

7. Canonical migration proceeds in deterministic batches with evidence and QA.

8. Missing Canonical evidence is never silently backfilled from a generic POI,
   existing navigation coordinate, address centroid, or map-provider pin.
```

---

## 3. Identity Scope Must Be Frozen Before Canonical Backfill

The `103` count in the impact audit is an **unadjudicated Production-row population**,
not a declaration that every row is automatically a valid unique canonical Shrine
migration target.

Existing repository audits have already shown that raw Production row count and
canonical unique-real-shrine scope can diverge because of:

```text
- QA fixtures
- non-shrine artifacts
- duplicate / shadow rows
- canonical primary rows
```

Historical example:

```text
RAW_PRODUCTION_SHRINE_ROWS = 108

excluded:
- id 102 = QA fixture
- id 105 = NON_SHRINE_ARTIFACT
- ids 101 / 103 / 104 = duplicate shadows

canonical audit units = 103
```

The current model does not automatically discover canonical identity scope.

Therefore A-5 requires:

```text
MIGRATION_TARGET_SCOPE
= EXPLICITLY_FROZEN_CANONICAL_IDENTITY_SET
```

before Canonical position adjudication begins.

No heuristic such as name equality, coordinate proximity, or `place_ref` presence is
allowed to silently define the migration universe.

---

## 4. Status for Unadjudicated Rows

For the future Canonical semantic layer:

```text
UNADJUDICATED ROW
-> CANONICAL_STATUS = NOT_ADJUDICATED
-> CANONICAL_COORDINATE = ABSENT
```

This includes rows that currently have high-quality Visitor / Navigation coordinates.

Example:

```text
pk=70 多摩川浅間神社

current navigation coordinate
= existing / remediated

Canonical Shrine Anchor status
= NOT_ADJUDICATED
```

Navigation quality does not prove ritual-center semantics.

---

## 5. No Bulk Copy Rule

The following operation is prohibited:

```text
canonical_latitude = latitude
canonical_longitude = longitude
for every existing row
```

unless that individual row has already been adjudicated and the exact same coordinate
is independently accepted under Canonical semantics.

Likewise prohibited:

```text
existing POI
-> Canonical automatically

address coordinate
-> Canonical automatically

Navigation Anchor
-> Canonical automatically
```

A numerical equality between old and new coordinates does not remove the need for
semantic adjudication.

---

## 6. Batch Adjudication Policy

Canonical backfill must proceed as explicit review batches.

For each migration target:

```text
1. Confirm canonical Shrine identity.
2. Identify ritual semantic owner.
3. Apply P1 / P2 / P3 / P4 / P5 rule.
4. For P2, apply the A-7 complete-component representative-point rule.
5. Trace the geographic point or component coordinates.
6. Record source / provenance.
7. Decide:
   - PASS
   - HOLD_POSITION_REVIEW
8. Write only PASS Canonical values.
```

An incomplete audit remains:

```text
NOT_ADJUDICATED
```

not `HOLD_POSITION_REVIEW`.

A completed audit with unresolved accepted-source conflict becomes:

```text
HOLD_POSITION_REVIEW
```

---

## 7. Runtime Cutover Rule

A-5 prohibits mixed hidden semantics in one runtime field.

During backfill:

```text
current runtime coordinate semantics
= existing Visitor / Navigation Anchor
```

remain active.

The application must not do this under a field documented as Canonical:

```text
if Canonical exists:
    use Canonical
else:
    silently fall back to Navigation Anchor
```

because that makes one output field represent two meanings depending on row coverage.

A future Canonical runtime cutover requires an explicit release gate.

At minimum, that gate must establish:

```text
- migration target identity scope is frozen
- every runtime-eligible target has an explicit Canonical adjudication state
- PASS rows have complete Canonical provenance
- HOLD / NOT_ADJUDICATED behavior is explicit
- consumer fallback semantics are explicit
- Navigation consumers are not silently pointed at Canonical ritual coordinates
```

A-5 does not set a percentage threshold.

---

## 8. Gate-specific Migration Consequence

### If Gate A is selected

```text
A-5 migration action
= NONE
```

The current Visitor / Navigation Anchor Contract stays active.

### If Gate B is selected

Because Gate B reuses the existing coordinate meaning:

```text
existing single coordinate field
Visitor / Navigation Anchor
->
Canonical Shrine Anchor
```

A-5 requires all migration-target rows to be Canonical-adjudicated before semantic
cutover.

A mixed row-by-row reinterpretation is prohibited.

In addition, the known route / walking-destination semantic collision remains a
separate blocker identified by the impact audit.

### If Gate C is selected

Gate C permits an additive staged migration:

```text
existing Navigation Anchor
= preserved

new Canonical Anchor
= absent until adjudicated
```

Canonical values can be populated in batches without changing live route semantics.

However, adding a new field does not itself authorize runtime use. Runtime cutover
still requires an explicit consumer gate.

---

## 9. Base Seed / Portable Data Rule

If Canonical Anchor data is added to portable Seed or another repository-owned data
source later:

```text
existing seed latitude / longitude
must retain their documented current semantics
until an explicit Seed Contract migration
```

Canonical data must be added through a separately defined field / structure or an
explicit all-row semantic migration.

No seed-wide semantic relabeling is implied by this A-5 decision.

---

## 10. A-5 Resolution

```text
A-5
= RESOLVED

MIGRATION_POLICY
= ADDITIVE_STAGED_NO_SILENT_REINTERPRETATION

UNADJUDICATED_CANONICAL_STATUS
= NOT_ADJUDICATED

UNADJUDICATED_CANONICAL_COORDINATE
= ABSENT

EXISTING_NAVIGATION_COORDINATE
= PRESERVED

BULK_COPY_NAVIGATION_TO_CANONICAL
= PROHIBITED

MIGRATION_SCOPE
= EXPLICITLY_FROZEN_CANONICAL_IDENTITY_SET

BACKFILL
= EVIDENCE-BASED BATCHES

PARTIAL_COMPONENT_CANONICAL_POINT
= PROHIBITED

ROW-BY-ROW_HIDDEN_RUNTIME_FALLBACK
= PROHIBITED

RUNTIME_CUTOVER
= EXPLICIT FUTURE GATE
```

---

## 11. Consequence for Migration Gate Readiness

With A-5 resolved:

```text
A-1 = RESOLVED
A-2 = RESOLVED
A-3 = RESOLVED
A-4 = RESOLVED
A-5 = RESOLVED
A-6 = EVIDENCE-SUPPLY AUDIT COMPLETED / A-7 closes the point-policy gap
A-7 = RESOLVED
```

Therefore:

```text
MIGRATION_GATE_READY_FOR_SELECTION
= YES
```

This document does not select A / B / C / D.

---

## 12. Required Statements

```text
1. No Production data was changed.
2. No Base Seed data was changed.
3. No schema was changed.
4. No existing Visitor / Navigation coordinate was reinterpreted.
5. pk=70 does not automatically become a Canonical Shrine Anchor.
6. No unadjudicated row receives a Canonical coordinate.
7. No raw Production row count is treated as automatic canonical identity scope.
8. No Migration Gate option was selected by this A-5 policy record.
```
