# Collective Deity Model Change Design

## Status

**DESIGN COMPLETE / IMPLEMENTATION NOT STARTED**

- Repository: `etsu33/jinja_app`
- Base branch: `develop`
- Base SHA: `b4eeaaba7d79052d5a5e677f325e5da38d78a061`
- Design branch: `design/collective-deity-model-change`
- Scope: A-1 Collective Deity Model Change Design
- Change type: docs-only design record

This document defines the minimum model change required to represent source-backed collective deity structures without changing current Runtime, Recommendation, Serializer, Production data, Candidate lifecycle, or Model Risk release state.

---

## 1. Problem

Current `ShrineDeity` assumes that one row represents one individually attributable named deity.

That model can represent multiple named deities as multiple rows, but it cannot represent the following structures without meaning loss:

- unnamed or incompletely named collective deity groups
- open-ended groups such as `ほか8柱` or `ほか15柱以上`
- source-backed member counts
- whether a member list is complete, partial, not enumerated, or not determined
- the parent relationship between a named collective and known individual members

The model gap must not be bypassed by inventing placeholder deity rows or synthesizing unknown individual identities.

---

## 2. Existing Boundaries Confirmed by Audit

### 2.1 Individually named deities

Existing `ShrineDeity` remains the authority for individually attributable named deities.

Current behavior supports:

- one Shrine to many `ShrineDeity` rows
- `primary / enshrined / secondary / unknown` role
- deterministic `sort_order`
- Source relation
- verification status
- confidence
- Evidence Gate evaluation

The meaning of `ShrineDeity` is not widened by A-1.

### 2.2 Named collectives already exist in heterogeneous forms

Repository data currently contains more than one representation pattern.

Examples include:

- a collective label stored as one `ShrineDeity` Fact
- individual deity rows with the collective label preserved only in `note` or Source material
- individually known members with an unnamed remainder
- collective structures that are held outside Runtime because the current model cannot preserve their meaning

A-1 does not normalize these records in-place.

### 2.3 Sub-shrine boundary

A deity of a subordinate shrine, precinct shrine, sessha, massha, or associated worship target must not be silently mixed into the parent Shrine's main deity facts.

A-1 does not introduce a shrine-unit hierarchy model.

### 2.4 Alias and identity relations

Alias handling and semantic identity relations are separate model concerns.

A-1 does not solve:

- aliases
- `same_as`
- deity identity relations
- shinbutsu-shugo semantic relations
- historical equivalence or identification relations

---

## 3. Design Boundary

A-1 introduces a separate collective concept while preserving current `ShrineDeity` semantics.

Conceptual structure:

```text
Shrine
├── ShrineDeity
│   └── individually attributable named deity
│
└── ShrineDeityCollective
    └── source-backed collective deity fact
        └── ShrineDeityCollectiveMembership
            └── relation to known ShrineDeity rows
```

A `ShrineDeityCollective` is valid even when it has zero Membership rows.

This is required for source-backed collectives whose members are not individually enumerated.

---

## 4. ShrineDeityCollective

### 4.1 Candidate fields

```text
shrine
source_attested_label
role
sort_order
member_count
member_count_relation
member_list_status
sources
verification_status
confidence
verified_at
note
created_at
updated_at
```

### 4.2 Field responsibilities

#### `shrine`

Identifies the Shrine to which the collective Fact belongs.

#### `source_attested_label`

Stores the collective expression actually attested by the accepted Source.

It is not an AI-generated canonical name.

A-1 does not add `canonical_name` or `aliases` to the collective model.

#### `role`

Uses the current deity-role vocabulary:

```text
primary
enshrined
secondary
unknown
```

The role must not be inferred when the accepted Source does not establish one.

#### `sort_order`

Provides deterministic display and processing order.

#### `member_count`

Stores a source-backed numeric collective count when one is available.

When populated, the value represents the collective count and must not be treated as the count of known Membership rows.

A value must not be invented from Membership row count.

#### `member_count_relation`

Candidate closed vocabulary:

```text
exact
minimum
approximate
unspecified
```

Semantics:

- `exact`: the Source states an exact count
- `minimum`: the Source states a lower bound such as "15柱以上"
- `approximate`: the Source states an approximate count
- `unspecified`: no numeric count is established

Validation direction:

- `exact / minimum / approximate` require `member_count`
- `unspecified` requires `member_count = null`

#### `member_list_status`

Candidate closed vocabulary:

```text
complete
partial
not_enumerated
not_determined
```

Semantics:

- `complete`: the accepted Source establishes the complete member list
- `partial`: only part of the member list is established
- `not_enumerated`: the collective is established but members are not individually listed
- `not_determined`: the available accepted Source does not establish whether the list is complete

Membership row count must never be used as an implicit completeness signal.

#### `sources`

Direct relation to `ShrineKnowledgeSource`.

The Collective Fact follows the existing Knowledge Evidence principle: a Fact is not Runtime-usable merely because a DB row exists.

#### `verification_status / confidence / verified_at / note`

Reuse the existing Knowledge verification vocabulary and validation direction.

No new parallel evidence-status system is introduced by A-1.

#### `created_at / updated_at`

Audit timestamps consistent with existing Knowledge models.

---

## 5. ShrineDeityCollectiveMembership

### 5.1 Candidate fields

```text
collective
deity
sort_order
sources
verification_status
confidence
verified_at
note
created_at
updated_at
```

### 5.2 Structural constraints

The following constraints are required by the design:

```text
collective.shrine_id == deity.shrine_id
```

and:

```text
Unique(collective, deity)
```

A Membership row may reference only an existing, individually attributable `ShrineDeity`.

Unknown members must never be synthesized to satisfy an expected count.

### 5.3 Membership Evidence decision

Mother Ship decision:

```text
Membership Evidence = B
```

Meaning:

- Membership is an independent source-backed relation
- Membership owns its own `sources`
- Collective Source is never inherited automatically
- the same `ShrineKnowledgeSource` may be referenced by both Collective and Membership
- a fact-ready Collective does not automatically make its Membership rows fact-ready

This preserves fail-safe Evidence behavior when the Source proves that a collective exists but does not prove a particular member relation.

---

## 6. Existing Named Collective Migration

Mother Ship decision:

```text
Named Collective Migration = C
```

Meaning:

**Additive staged migration.**

The migration sequence is:

1. Model Foundation
2. Source-backed backfill
3. Runtime activation
4. Legacy collective cleanup

### 6.1 Model Foundation

The first implementation stage adds the new model capability only.

It must not:

- delete existing `ShrineDeity` rows
- reinterpret existing `note` text automatically
- alter Recommendation behavior
- alter Shared Recommendation Eligibility
- modify Production Knowledge data
- release any Model Risk HOLD

### 6.2 Source-backed backfill

Existing named collectives may be migrated only after reviewed Source evidence establishes the structure.

No automatic migration may be derived only from free-text `note` values.

Expected existing patterns include:

```text
A. collective label currently stored as ShrineDeity

B. individual ShrineDeity rows exist and the collective label is
   preserved only in note / Source

C. some individual members are known and an unnamed remainder exists

D. the collective is established but individual members are not enumerated
```

Each pattern must be handled explicitly and source-backed.

### 6.3 Runtime activation

Runtime support is a separate stage after backfill and QA.

### 6.4 Legacy cleanup

Legacy collective representations may be removed only after Runtime activation and QA establish that the new representation is complete and behaviorally safe.

---

## 7. Evidence Gate Compatibility

Current `evidence_gate.decide_fact_usability()` evaluates:

```text
verification_status
confidence
source_verification_statuses
```

Current `decide_detail_display_state()` similarly evaluates Fact status and Source status without requiring a ShrineDeity-specific payload.

Therefore the existing Evidence decision logic is expected to be reusable for Collective and Membership Facts.

A-1 does not modify those functions.

Any implementation PR must prove reuse through tests rather than introducing a second Evidence authority.

---

## 8. Runtime / Serializer Blast Radius

A-1 is a design-only task.

The following Runtime surfaces were inspected and are explicitly outside A-1 implementation.

### 8.1 Shrine Detail API

Current Detail Runtime exposes:

```text
deities
histories
```

through `ShrineDetailSerializer`.

Future Collective activation will require a separately defined payload.

The Collective must not be silently flattened into the existing `deities` array.

Potential future work:

- Collective serializer
- Membership serializer or nested membership representation
- Detail View prefetch
- Detail Evidence display filtering
- Web and Mobile type support
- UI representation

None of these changes belong to A-1.

### 8.2 Recommendation selector

Current Runtime reads usable:

- `ShrineDeity`
- `ShrineHistory`

through `shrine_knowledge_selector`.

Future Collective activation requires an explicit Collective selector.

A-1 does not modify `fetch_fact_ready_knowledge_deities()`.

### 8.3 Shared Recommendation Eligibility

Current authority is:

```text
usable ShrineDeity >= 1
OR
usable ShrineHistory >= 1
```

The existence of a `ShrineDeityCollective` row must not silently change that contract.

Whether a usable Collective becomes a third eligibility path requires a separate Mother Ship decision and a separate Runtime change.

Until then:

```text
is_recommendation_eligible()
```

remains unchanged.

### 8.4 Concierge and Compass

Shared Recommendation Eligibility is applied before Concierge / Compass divergence.

Therefore any future eligibility change affects both paths and must be implemented at the shared authority, not independently in Compass.

A-1 changes neither path.

### 8.5 Recommendation Reason

Current Recommendation reason generation consumes simplified `knowledge_deities` payloads and joins individual deity `display_name` values.

A collective must not be expanded into thousands of synthetic individual names or flattened as if it were one ordinary `ShrineDeity`.

Future Runtime activation requires an explicit Collective presentation contract.

A-1 does not change Recommendation reason generation.

### 8.6 Deep Dive

Current Deep Dive deity retrieval is based on `ShrineDeity`.

Collective-aware questions require a separate Runtime contract.

A-1 does not modify Deep Dive retrieval or answer generation.

### 8.7 Evidence Transport

Current normalized Evidence Transport supports `ShrineDeity` and `ShrineHistory` Fact types.

Collective / Membership transport is outside A-1.

If activated later, it requires an explicit versioned transport decision rather than silently overloading the existing deity payload.

### 8.8 Knowledge Seed pipeline

Current Knowledge Seed schema uses the existing `deities` and `histories` structures.

Collective backfill requires a later schema extension and corresponding:

- parser validation
- import behavior
- dry-run / validate-only coverage
- idempotency tests
- Source resolution tests

The exact future schema version is not decided in A-1.

### 8.9 Web

Current Web Detail presentation consumes:

```text
ShrineDeity[]
ShrineHistory[]
```

A-1 does not change API types, ViewModels, or UI.

### 8.10 Mobile

Current Mobile Detail presentation also consumes existing deity/history arrays.

A-1 does not change Mobile types, ViewModels, or UI.

---

## 9. Explicit Non-Goals

A-1 does not solve or change:

- deity aliases
- deity `same_as` relation
- religious identity relation
- shinbutsu-shugo semantic relation
- main-shrine / sessha / massha / precinct-shrine hierarchy
- associated worship target modeling
- goriyaku modeling
- legacy `Deity` master integration
- Recommendation scoring
- Recommendation ranking
- Runtime eligibility
- Deep Dive behavior
- Production data
- Candidate lifecycle
- Product-policy HOLD

These concerns must not be smuggled into the Collective implementation PR.

---

## 10. Model Risk Boundary

Model capability, Runtime eligibility, and Model Risk release are separate gates.

The following implications are prohibited:

```text
Collective model exists
=> Runtime usable
```

```text
Runtime usable
=> Model Risk released
```

```text
Model Risk released
=> Candidate automatically promoted
```

A Model Risk candidate must be explicitly re-evaluated at its owning Gate after the required model capability, Source-backed data, Evidence, and Runtime behavior exist.

No automatic HOLD release is permitted.

The creation of this design record does not change the lifecycle status of any candidate.

---

## 11. A-1 Exit Condition

A-1 is complete when all of the following are documented:

- individual deity boundary confirmed
- collective model gap confirmed
- named collective behavior confirmed
- Collective-to-Membership relation defined
- sub-shrine boundary confirmed
- alias / identity concerns separated from Collective scope
- Collective fields defined
- Membership Evidence decision fixed to `B`
- Named Collective Migration decision fixed to `C`
- Runtime / Serializer blast radius documented

All A-1 design conditions are satisfied by this record.

---

## 12. STOP

A-1 stops at design.

This task does **not** include:

- Django model implementation
- migration generation or execution
- Seed schema change
- Seed backfill
- Serializer change
- Runtime activation
- Recommendation change
- Web or Mobile change
- Production write
- Candidate lifecycle change
- Model Risk RELEASE

The next implementation task must be opened independently from this design record.
