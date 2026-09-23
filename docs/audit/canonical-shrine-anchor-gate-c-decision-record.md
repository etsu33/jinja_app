# Canonical Shrine Anchor — Migration Gate Decision Record (Gate C)

## Status

- Status: `DECIDED`
- Recorded at: `2026-09-23`
- Decision authority: Mother Ship
- Decision type: Migration Gate selection
- Supersedes: `GATE_SELECTED = NONE` as the *current* project state
- Runtime activation: `NONE`
- Implementation started: `NO`

## 1. Decision

```text
GATE_SELECTED = C
GATE_NAME = SPLIT_CANONICAL_AND_NAVIGATION_ANCHORS
```

```text
CURRENT ACTIVE:
Shrine.latitude / Shrine.longitude
= Visitor / Navigation Anchor

CANONICAL CONTRACT:
PROPOSED

RUNTIME CUTOVER:
NOT_PERFORMED

SCHEMA CHANGE:
NOT_PERFORMED

CANONICAL BACKFILL:
NOT_STARTED
```

本記録は Gate の選択のみを確定する。Canonical Shrine Anchor の runtime semantics を
有効化せず、実装も開始しない。

## 2. Established Basis

The Gate was selected against the following resolved state.

```text
A-1  = RESOLVED
A-2  = RESOLVED
A-3  = RESOLVED_PROXIMITY
A-4  = RESOLVED_AT_SEMANTIC_OWNER_LEVEL
A-5  = RESOLVED_ADDITIVE_STAGED_MIGRATION
A-6  = EVIDENCE_SUPPLY_SAMPLE_COMPLETED
A-7  = RESOLVED
A-7b = RESOLVED

MIGRATION_GATE_READY = YES
```

### 2.1 Evidence / audit documents used

| Item | Document |
| --- | --- |
| Gate option set, `A-1`–`A-6` raised, downstream consumer classification | `docs/audit/canonical-shrine-anchor-contract-impact.md` |
| `A-3` distance semantics — producers, consumers, proximity resolution | `docs/audit/canonical-anchor-distance-semantics-current-state.md` |
| `A-4` multiple-ritual-center selection rule | `docs/audit/canonical-shrine-anchor-multi-ritual-center-audit.md` |
| `A-5` migration policy | `docs/audit/canonical-shrine-anchor-unadjudicated-migration-policy.md` |
| `A-6` georeference traceability / single-point reproducibility | `docs/audit/canonical-shrine-anchor-georeference-traceability-audit.md` |
| `A-6` evidence-supply pilot | `docs/audit/shrine-orientation-evidence-pilot.md` |
| `A-7` representative point (`UNWEIGHTED_COMPONENT_MEAN`) | `docs/audit/canonical-shrine-anchor-p2-representation-decision.md` |
| `A-7b` component membership policy | `docs/knowledge/shrine-position-contract.md` §Canonical Shrine Anchor — Component Membership (A-7b) |
| Orientation evidence requirements | `docs/knowledge/shrine-orientation-evidence-contract.md` |
| Currently active position meaning | `docs/knowledge/shrine-position-contract.md` §Canonical Meaning |

### 2.2 Note on label continuity

`A-5` carried two distinct readings during the audit sequence: the **migration
policy** question (resolved in `canonical-shrine-anchor-unadjudicated-migration-policy.md`)
and the **displacement-measurement** question used during A-5B sampling, which was
reported as `INDETERMINATE` at that time.

This record adopts the Mother Ship label `A-5 = RESOLVED_ADDITIVE_STAGED_MIGRATION`.
The A-5B measurement state is unchanged and is not a Gate precondition; it remains an
input to Canonical adjudication batches, not to Gate selection.

## 3. Why This Decision Exists Structurally

The Gate exists because one coordinate field was being asked to carry two
responsibilities that diverge in practice.

```text
ritual / geographic identity        wants the principal enshrinement unit
route destination / arrival         wants a reachable navigation target
```

Three findings made the split the structurally coherent option rather than a
preference:

1. **The proposed Contract states the separation itself.** The Canonical Shrine
   Anchor proposal closes with: *"Navigation destinations are a separate concern and
   must not silently redefine the Canonical Shrine Anchor."* No field existed in
   which that separate concern could live.

   ```text
   NAVIGATION_ANCHOR_FIELD_EXISTS = NO   (at decision time)
   ```

2. **Downstream consumers split cleanly, not evenly.** The impact audit classified
   the five declared consumers of the active Contract:

   ```text
   SEMANTICALLY_COMPATIBLE       = 2   map display, compass direction
   NEEDS_NAVIGATION_ANCHOR_SPLIT = 2   route guidance, Shrine detail map link
   INDETERMINATE                 = 1   distance
   ```

   The two `NEEDS_NAVIGATION_ANCHOR_SPLIT` consumers emit the stored coordinate
   verbatim as a routing destination. A ritual-center coordinate inside a precinct
   is precisely the input for which that degrades.

3. **`A-3` removed the ambiguity on the third consumer.** With
   `distance_m` resolved as a geodesic straight-line **proximity indicator** and not
   a navigation promise, distance follows the Canonical side without inheriting a
   travel claim. That converted the one `INDETERMINATE` consumer into an assignable
   one and left the split with no unassigned responsibility.

Gate B (reuse one field) would have required the routing consumers to accept a ritual
coordinate. Gate A (no change) would have left both open HOLDs blocked on a semantic
question the proposal answers. Gate C assigns each responsibility to a field that can
carry it.

## 4. Semantic Responsibility Split

```text
Canonical Shrine Anchor
  - ritual / geographic identity
  - proximity
  - compass direction

Navigation Anchor
  - route destination
  - arrival / walking-navigation semantics
```

Consumer mapping implied by the split (recorded for the future architecture phase,
not applied by this record):

| Consumer | Responsibility | Anchor after cutover |
| --- | --- | --- |
| Map display (Shrine marker) | geographic identity | Canonical |
| `distance_m` / proximity ranking | proximity (`A-3`) | Canonical |
| Compass direction / bearing | direction | Canonical |
| Route guidance (`/map` nearby CTA) | route destination | Navigation |
| Shrine detail map link (walking) | arrival | Navigation |

No consumer is repointed by this record.

## 5. A-5 Migration Constraints (binding on Gate C)

Gate C inherits the migration policy already recorded in
`docs/audit/canonical-shrine-anchor-unadjudicated-migration-policy.md`.

```text
MIGRATION_POLICY = ADDITIVE_STAGED_NO_SILENT_REINTERPRETATION
```

```text
1. Existing Navigation coordinates are preserved.
2. Canonical coordinates start ABSENT / NOT_ADJUDICATED.
3. Canonical coordinates are populated only through evidence-based adjudication.
4. Silent Navigation -> Canonical copy is PROHIBITED.
5. Hidden row-by-row semantic fallback is PROHIBITED.
6. Runtime cutover requires a separate future gate.
```

Constraints 4 and 5 restate the prohibitions that make Gate C additive rather than a
reinterpretation. A numeric equality between an existing Navigation coordinate and a
future Canonical value does not remove the adjudication requirement.

Canonical adjudication additionally remains bound by:

- `A-7` representative point: `UNWEIGHTED_COMPONENT_MEAN`
- `A-7b` component membership: `AUTHORITATIVE_PRINCIPAL_ENSHRINEMENT_UNIT`
- the `COMPONENT_SET_STATUS = COMPLETE` calculation gate
- `PARTIAL_COMPONENT_CANONICAL_POINT = PROHIBITED`

## 6. What Gate C DOES Authorize

```text
1. Recording Gate C as the selected Migration Gate.
2. Treating "split Canonical and Navigation anchors" as the agreed target
   architecture for subsequent design work.
3. Designing a Split Anchor Architecture proposal in a later, separate phase.
4. Planning Canonical adjudication batches under A-5 / A-7 / A-7b rules.
5. Referencing Gate C as settled in future audit and design documents.
```

## 7. What Gate C DOES NOT Authorize

```text
1. Schema change of any kind.
2. Adding Canonical coordinate fields to any model.
3. Modifying the Shrine model, serializers, or any runtime code.
4. Base Seed modification.
5. Production DB modification.
6. Creating or running migrations.
7. Canonical backfill, in whole or in part.
8. Runtime cutover, or any consumer repointing.
9. Changing Recommendation / Ranking / Compass / navigation behavior.
10. Changing distance semantics.
11. Adjudicating any shrine's coordinates or components.
12. Activating the Canonical Shrine Anchor Contract.
13. Altering A-1 through A-7b decisions.
```

The Canonical Shrine Anchor Contract remains `PROPOSED`. Selecting the Gate decides
**which architecture the project is heading toward**; it does not adopt the Contract
and does not change what any field currently means.

## 8. Current Runtime State

```text
Shrine.latitude / Shrine.longitude   = Visitor / Navigation Anchor  (ACTIVE, unchanged)
Canonical coordinate field            = DOES_NOT_EXIST
Canonical adjudicated rows            = 0
Production rows in scope              = unchanged by this record
Schema                                = unchanged
Serializers                           = unchanged
Ranking / distance / compass          = unchanged
Route guidance / detail map link      = unchanged
Base Seed                             = unchanged
Migrations                            = none added
```

Every runtime consumer continues to read `Shrine.latitude` / `Shrine.longitude` under
Visitor / Navigation Anchor semantics, exactly as before this record.

## 9. Next Architectural Phase

Recorded as the expected sequence. None of it is authorized to begin by this record.

```text
PHASE_1  Split Anchor Architecture design proposal
         - field / storage shape for the Canonical anchor
         - NOT_ADJUDICATED representation
         - consumer routing per §4
         - explicit no-fallback rule surface

PHASE_2  Canonical adjudication batch procedure
         - A-7b component membership packets
         - COMPONENT_SET_STATUS gating
         - frozen migration target identity scope (A-5 §3)

PHASE_3  Canonical backfill in evidence-based batches

PHASE_4  Runtime cutover — SEPARATE FUTURE GATE, not granted here
```

`PHASE_1` requires its own Mother Ship instruction before any work begins.

## 10. Explicit Stop Boundary

```text
THIS RECORD ENDS AT GATE SELECTION.
```

```text
DONE      : Gate C recorded; A-7b applicability metadata updated to GATE_SELECTED = C
NOT DONE  : schema, model, serializer, Seed, migration, Production,
            Recommendation, Ranking, Compass, navigation, distance semantics,
            Canonical backfill, runtime cutover, coordinate adjudication
NOT DONE  : Split Anchor Architecture implementation (PHASE_1 onward)
```

Any subsequent change touching runtime, schema, or data requires a new Mother Ship
instruction naming the phase.

## 11. Historical Audit Handling

Earlier audit documents record `GATE_SELECTED = NONE`. That was the true state when
each was written and is **not** corrected by this record.

Left unchanged intentionally:

```text
docs/audit/canonical-shrine-anchor-contract-impact.md
docs/audit/canonical-shrine-anchor-unadjudicated-migration-policy.md
docs/audit/canonical-shrine-anchor-georeference-traceability-audit.md
docs/audit/canonical-shrine-anchor-multi-ritual-center-audit.md
docs/audit/canonical-shrine-anchor-p2-representation-decision.md
docs/audit/canonical-anchor-distance-semantics-current-state.md
docs/audit/shrine-orientation-evidence-pilot.md
```

This Decision Record is the later decision. Where an earlier document's
`GATE_SELECTED = NONE` conflicts with it, **this record governs the current state**
and the earlier document governs the historical state at its own recorded date.

The one exception is `docs/knowledge/shrine-position-contract.md` §A-7b, whose
`GATE_SELECTED` line is *applicability metadata for an active contract clause* rather
than a historical audit observation. It is updated to `C` by the same change that adds
this record.

## 12. Required Statements

```text
1. No schema was changed.
2. No Canonical coordinate field was added.
3. The Shrine model, serializers, and all runtime code are unchanged.
4. No Base Seed change.
5. No Production DB change.
6. No migration was created.
7. Recommendation / Ranking / Compass / navigation are unchanged.
8. Distance semantics are unchanged.
9. No Canonical backfill was performed.
10. No runtime cutover was performed.
11. No shrine coordinate or component was adjudicated.
12. A-1 through A-7b decisions are unchanged.
13. The Canonical Shrine Anchor Contract remains PROPOSED.
14. Split Anchor Architecture implementation has not begun.
```

## 13. STOP

```text
GATE_SELECTED     = C
GATE_NAME         = SPLIT_CANONICAL_AND_NAVIGATION_ANCHORS
CONTRACT_TIER     = PROPOSED
RUNTIME_CUTOVER   = NOT_PERFORMED
SCHEMA_CHANGE     = NOT_PERFORMED
CANONICAL_BACKFILL = NOT_STARTED
IMPLEMENTATION    = NOT_STARTED
```

Next action requires a Mother Ship instruction opening `PHASE_1`.
