# A-5b Source-backed Collective Backfill Candidate Freeze Contract

## Status

- Status: `A-5b CANDIDATE FREEZE CONTRACT / FROZEN`
- Recorded at: `2026-09-27`
- Base branch: `develop`
- Branch: `audit/a5b-source-backed-candidate-freeze`
- Production write: **NONE**
- Backfill execution: **NONE**
- Runtime activation: **NONE**
- Candidate Master change: **NONE**

## 1. Purpose

A-5b freezes the candidate set that may proceed to the Source-backed Collective / Membership backfill defined by the existing Collective Deity contracts.

This is a read-only audit gate. It does not execute the backfill and does not authorize Production writes.

A-5b exists after A-5a fixed Knowledge Seed schema 1.1. It must not redefine the model, importer, Source identity, Collective identity, Membership identity, verification lifecycle, or write path already fixed by A-1 through A-5a.

## 2. Canonical authority

A-5b inherits, without reinterpretation, the existing contracts:

- `docs/audit/collective-deity-model-change-design.md`
- `docs/audit/collective-deity-backfill-integrity-gate.md`
- `docs/audit/collective-deity-knowledge-seed-v1-1-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- current `backend/temples/models.py`
- current Knowledge importer authority in `backend/temples/services/knowledge_seed.py` and `backend/temples/management/commands/import_shrine_knowledge.py`

If this document conflicts with those authorities, the upstream canonical contract wins and the candidate must not be frozen under the conflicting interpretation.

## 3. Fixed upstream decisions

A-5b must preserve these decisions:

```text
Membership Evidence = B
Named Collective Migration = C
WRITE_PATH_AUTHORITY = EXTEND_EXISTING_KNOWLEDGE_IMPORTER
BULK_WRITE_POLICY = PROHIBITED_FOR_COLLECTIVE_BACKFILL
INTEGRITY_BOUNDARY = DB_ROW_LOCAL_MODEL_SERVICE_CROSS_ROW
COUNT_RELATION_DB_CONSTRAINT = ADD_BEFORE_BACKFILL
COLLECTIVE_IDENTITY = SHRINE_PLUS_SOURCE_ATTESTED_LABEL
KNOWLEDGE_SEED_SCHEMA = VERSION_1_1_WITH_1_0_BACKWARD_COMPATIBILITY
```

## 4. A-5b scope

A-5b may only determine whether a candidate has sufficient repository-traceable evidence to be frozen for a later Source-backed backfill packet.

A-5b may:

- preserve the fixed candidate input set
- resolve Shrine identity using the existing authority
- identify a Source-attested Collective label
- identify Source-backed Collective properties
- identify individually attributable Membership relations only when independently supported
- record Source provenance required by Knowledge Seed 1.1
- classify each candidate as `FREEZE`, `HOLD`, or `EXCLUDE`
- freeze a deterministic candidate artifact for the later backfill implementation/execution stage

A-5b must not:

- write Production data
- mutate the DB
- execute the backfill
- use Django shell or a one-off script as a canonical write path
- create a parallel importer
- use `bulk_create`, `bulk_update`, `QuerySet.update`, or raw SQL as a backfill authority
- infer or invent a canonical Collective name
- infer religious equivalence
- synthesize unknown members
- inherit Collective Sources into Membership Sources
- create a missing Deity merely because a Membership refers to it
- rewrite existing Deity / History identity behavior
- activate Collective data in Runtime
- change Serializer / selector / Recommendation Eligibility
- change Concierge / Compass / Deep Dive / Evidence Transport
- release Model Risk holds
- change Candidate Master status

## 5. Source-backed evidence boundary

### 5.1 Collective evidence

Every candidate Collective requires its own non-empty `source_keys`.

The Source must directly support the Source-attested aggregate expression and the Collective properties proposed for the later seed packet.

The Collective identity remains exactly:

```text
resolved Shrine + source_attested_label
```

`source_attested_label` is Source-attested text. A-5b must not canonicalize, translate, synonym-match, or infer an equivalent religious label.

### 5.2 Membership evidence

Membership Evidence remains policy B.

Every supplied Membership requires its own non-empty `source_keys` proving that specific member relation.

```text
Collective Source evidence
!=
automatic Membership evidence
```

There is no Source inheritance from Collective to Membership.

If a Source establishes only the Collective and does not establish a named member relation:

```text
Collective may remain a candidate
Membership must not be supplied
```

A Collective with zero Memberships remains valid.

## 6. Candidate freeze states

A-5b audit states are namespaced as `a5b_freeze_status` and do not replace Knowledge verification statuses or other repository lifecycle statuses.

### 6.1 FREEZE

A candidate may be `FREEZE` only when all applicable conditions are satisfied:

1. candidate belongs to the fixed A-5b input set
2. Shrine identity is deterministically resolvable under existing authority
3. `source_attested_label` is non-blank, Source-attested, and unmodified
4. at least one valid Source is traceable for the Collective
5. every proposed Collective field is supported by the recorded Source or is a contract-defined default
6. every supplied Membership resolves to an individually attributable same-Shrine Deity under the v1.1 reference contract
7. every supplied Membership has its own non-empty Source evidence
8. member count / count relation values satisfy the existing v1.1 invariant
9. verification / confidence / `verified_at` values satisfy the current Knowledge contract
10. no unresolved Source, Shrine, Collective, Membership, or existing-row conflict is present
11. the candidate can be represented without inference beyond upstream contracts

`FREEZE` means only that the candidate packet is frozen for the next backfill stage.

```text
FREEZE != BACKFILL_EXECUTED
FREEZE != PRODUCTION_WRITE_AUTHORIZED
FREEZE != FACT_READY
FREEZE != RUNTIME_ACTIVE
```

### 6.2 HOLD

Use `HOLD` when the candidate remains in scope but cannot satisfy `FREEZE` without additional evidence or adjudication.

HOLD conditions include:

- Shrine identity unresolved or ambiguous
- Source identity conflict or ambiguity
- Source-attested label absent or ambiguous
- Source does not directly support a proposed field
- conflicting Source evidence
- member relation is not independently Source-backed
- Membership Deity is not found, ambiguous, or belongs to another Shrine
- existing Collective / Membership meaningful-field mismatch
- existing Source relation mismatch
- verification metadata cannot be established under the current contract
- any interpretation would require alias matching, note parsing, canonical-name inference, or religious-equivalence inference

HOLD performs zero writes.

### 6.3 EXCLUDE

Use `EXCLUDE` only when the item is not an A-5b Source-backed Collective backfill candidate, for example:

- it is outside the fixed A-5b candidate input set
- evidence establishes no Collective fact to backfill
- the item is a legacy representation that is not eligible for this staged candidate packet
- the candidate was included accidentally and has no applicable Collective / Membership backfill target

EXCLUDE is not a negative statement about the Shrine or religious content. It is only an A-5b scope classification.

## 7. Frozen candidate artifact schema

Each evaluated candidate record must preserve at minimum:

```text
candidate_order
candidate_name
candidate_address

resolved_shrine_id
source_attested_label
role
sort_order
member_count
member_count_relation
member_list_status
verification_status
confidence
verified_at
note
collective_source_keys

memberships[]
  deity_ref.display_name
  sort_order
  verification_status
  confidence
  verified_at
  note
  source_keys

a5b_freeze_status
reason_code
review_note
```

Source records referenced by `source_keys` must remain representable under Knowledge Seed 1.1 and preserve the existing Source identity contract.

No numeric DB primary key may be used as a portable Membership deity reference.

## 8. Conflict and fail-safe contract

A-5b is fail closed.

Any unresolved conflict means the candidate cannot be `FREEZE`.

Existing upstream planning semantics remain authoritative:

```text
0 matching Collective rows
-> CREATE candidate for later plan

1 matching Collective + exact expected fields + exact Source relation set
-> SKIP_EXISTS candidate for later plan

1 matching Collective + meaningful mismatch
-> COLLECTIVE_CONFLICT
-> HOLD / STOP

2+ matching Collective rows
-> COLLECTIVE_AMBIGUOUS
-> HOLD / STOP
```

Membership planning follows the existing v1.1 contract in the same way. A-5b does not silently overwrite an existing row to make evidence fit.

## 9. Mutation prohibition

During A-5b candidate freeze:

```text
Production write = 0
DB mutation = 0
Seed mutation = 0 during evidence classification
AUTO_IMPORT = 0
AUTO_MERGE = 0
AUTO_CREATE = 0
Runtime activation = 0
```

A frozen audit artifact may be committed to the repository. That repository artifact is evidence, not a Production data write.

## 10. Determinism / reproducibility

The candidate input set must be fixed before classification.

A-5b run1 must be frozen before an independent run2 comparison.

The reproducibility comparison must use only fields whose generation authority is canonical or explicitly fixed by this contract. Audit-derived helper fields must not be silently promoted to canonical comparison fields.

If a field is discovered to have no canonical repository authority, its provenance must be recorded and the field must be explicitly included or excluded before the reproducibility Gate is evaluated.

A reproducibility PASS does not prove Source truth or Production import eligibility. It proves only deterministic reproduction of the frozen comparison contract.

## 11. Downstream boundary

After A-5b candidate freeze closes, the next stage may prepare Knowledge Seed 1.1 packets and run the existing importer validation / dry-run path.

The canonical write sequence remains the A-4 / A-5a sequence:

```text
parse
-> validate
-> resolve Shrine
-> resolve Source
-> resolve Collective identity
-> resolve Membership deity identity
-> CREATE / SKIP / CONFLICT plan
-> any error = STOP, zero writes
-> dry-run = zero writes
-> transaction.atomic()
-> normal validated saves only
-> attach Collective sources
-> attach Membership sources independently
-> verify expected delta
-> commit
-> second dry-run CREATE=0 / CONFLICT=0
```

A-5b itself stops before any apply / Production write.

## 12. Closure criteria

A-5b candidate freeze may close only when:

- the candidate input set is frozen
- every candidate has exactly one `a5b_freeze_status`
- every `FREEZE` candidate satisfies all applicable Source-backed conditions
- every supplied Membership has independent Source evidence
- every HOLD / EXCLUDE has an explicit reason
- no unresolved conflict is hidden by inference
- no Production or DB mutation occurred during the freeze audit
- the frozen artifact is reproducible under its fixed comparison contract

Only then may A-5b be recorded as closed.
