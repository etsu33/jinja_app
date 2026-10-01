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
- Revision 2026-10-01: Mother Ship P1–P5 integrated (§5.1, §6.1, §6.2, §13). Canonical text: `collective-deity-knowledge-seed-v1-1-contract.md` §12
- Revision 2026-10-01: Freeze Evidence Artifact defined (§6.1, §6.2, §7.1–§7.3, §9, §12, §14)
- Revision 2026-10-01: Direct Verification Timestamp Policy referenced (§6.1 condition 9, §7, §7.1, §15). Canonical text: Seed 1.1 contract §12.8
- Revision 2026-10-01: Artifact Source reference = semantic Source identity (§7, §7.1, §16)
- Revision 2026-10-01: Pre-FREEZE source-backed replacement (§4, §6.1, §6.3, §6.4, §7, §10, §12, §17)
- Revision 2026-10-01: A-5b unset Collective confidence rule (§6.1 condition 9, §7, §18)
- Revision 2026-10-01: A-5b member_list_status assignment rule (§6.1 condition 5, §7, §19)
- Revision 2026-10-01: Erroneous pre-FREEZE replacement lifecycle (§6.5, §20)

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

- preserve the fixed candidate input set (a §6.4 replacement preserves it: the replacement occupies the failed legacy candidate's position)
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

Collective evidence follows Knowledge Seed 1.1 contract §12 (Mother Ship P1–P5):

- the label is extracted only as permitted by §12.1 (P1)
- the accepted official Source content must directly support the Collective assertion (§12.2, P2)
- notes, legacy ShrineDeity Facts, and prior extraction results are discovery evidence only (§12.2–§12.3, P2–P3)
- `role` follows §12.4 (P4)
- `member_count` / `member_count_relation` follow §12.5 (P5)

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

1. candidate belongs to the fixed A-5b input set, or is a replacement candidate authored under §6.4 that occupies the position of a legacy candidate in that set
2. Shrine identity is deterministically resolvable under existing authority
3. `source_attested_label` is non-blank, Source-attested, and occurs verbatim as one contiguous substring of the accepted official Source, extracted only as permitted by Seed 1.1 contract §12.1 (P1)
4. at least one accepted official Source is traceable for the Collective, and its content has been confirmed to directly support the Collective assertion (§12.2, P2). A note, a legacy Fact, or a prior judgment alone does not satisfy this (§12.2–§12.3, P2–P3)
5. every proposed Collective field is directly supported by the accepted official Source, or is a default that Seed 1.1 contract §12 permits: `role = unknown` under §12.4 (P4); `member_count_relation = unspecified` / `member_count = null` only when no numeric count is established, under §12.5 (P5). `member_list_status` follows the A-5b member_list_status assignment rule (§7)
6. every supplied Membership resolves to an individually attributable same-Shrine Deity under the v1.1 reference contract
7. every supplied Membership has its own non-empty Source evidence
8. member count / count relation values satisfy the existing v1.1 invariant
9. verification / confidence / `verified_at` values satisfy the current Knowledge contract. For a new P1–P5-governed Collective or Membership, `verified_at` also satisfies the Direct Verification Timestamp Policy (Seed 1.1 contract §12.8), and Collective `confidence` follows the A-5b unset confidence rule (§7)
10. no unresolved Source, Shrine, Collective, Membership, or existing-row conflict is present
11. the candidate can be represented without inference beyond upstream contracts
12. a contract-compliant Freeze Evidence Artifact (§7.1) records the direct verification against the accepted official Source, and in it:
    - every required assertion (§7.1) is auditable and has `support_status = SUPPORTED`
    - no required assertion is `UNSUPPORTED` or `AMBIGUOUS`
    - `NOT_APPLICABLE` is used only where the governing contract makes that assertion non-applicable

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
- the Collective assertion is supported only by notes, legacy Facts, or prior judgments, with no direct Source confirmation (P2 / P3)
- the label cannot be extracted under P1
- a numeric expression exists but the Source does not establish its semantics (P5): `unspecified` / `null` must not be used to bypass this HOLD. The Artifact records the count assertion as `AMBIGUOUS`
- no contract-compliant Freeze Evidence Artifact exists, or a required assertion in it is not auditable
- a required assertion is `UNSUPPORTED` or `AMBIGUOUS` in the Freeze Evidence Artifact

HOLD performs zero writes.

### 6.3 EXCLUDE

Use `EXCLUDE` only when the item is not an A-5b Source-backed Collective backfill candidate, for example:

- it is outside the fixed A-5b candidate input set (a §6.4 replacement candidate is not outside it)
- evidence establishes no Collective fact to backfill
- the item is a legacy representation that is not eligible for this staged candidate packet
- the candidate was included accidentally and has no applicable Collective / Membership backfill target

EXCLUDE is not a negative statement about the Shrine or religious content. It is only an A-5b scope classification.

### 6.4 Pre-FREEZE source-backed replacement

```text
PRE_FREEZE_REAUTHORING_POLICY = ALLOW_SOURCE_BACKED_REPLACEMENT_WITH_PROVENANCE
```

**Scope.** This section applies only when all of the following hold:

1. the legacy candidate belongs to the fixed A-5b input set
2. it has not reached `FREEZE` under the current P1–P5 policy
3. no applicable A-5b candidate packet has materialized it into Seed 1.1, the DB,
   or runtime
4. a current direct official Source verification establishes that the legacy
   proposed `source_attested_label` cannot satisfy P1 (Seed 1.1 contract §12.1)

**Legacy candidate.** The legacy candidate is never mutated. It remains recorded
with:

- its original identity (resolved Shrine + legacy `source_attested_label`)
- `a5b_freeze_status = HOLD`
- an explicit P1 failure reason
- provenance pointing to the replacement (§7, "Replacement provenance")

**Replacement candidate.** A replacement candidate may be authored from the
accepted official Source. The replacement:

- uses a `source_attested_label` that independently satisfies current P1
- is evaluated fresh under P1–P5 and §6.1. No prior evidence judgment is inherited
  automatically (P2)
- does not normalize characters or numerals to preserve the legacy identity
- receives its own exact identity: resolved Shrine + `source_attested_label`
  (Seed 1.1 contract §5.3). It is never treated as equal to the legacy identity
- has its own single `a5b_freeze_status`, decided by §6.1 / §6.2

**Universe and count.**

- A replacement is not an unrelated expansion of the fixed input set. It occupies
  the lifecycle position of the failed legacy candidate.
- The `CLOSED_FROZEN` candidate universe and the logical candidate count are
  unchanged. One position holds both identities.
- The legacy identity stays historically auditable and keeps its `HOLD`.
- Only the replacement identity can proceed to `FREEZE` and Seed 1.1 authoring for
  that position.

**Explicit act.** A replacement is a deliberate authoring act recorded in the Freeze
Evidence Artifact for that position. It is never automatic.

**Historical candidate-freeze document.**

- A source-backed replacement does not rewrite
  `docs/audit/collective-deity-backfill-candidate-freeze.md`.
- That document keeps the original `CLOSED_FROZEN` candidate identity as historical
  provenance.
- For an authorized replacement case, two records are authoritative for subsequent
  A-5b processing:
  - the current candidate evaluation
  - the legacy → replacement provenance recorded in the contract-compliant Freeze
    Evidence Artifact
- The historical legacy identity does not override the later P1–P5-governed
  replacement.
- The logical candidate count is unchanged.

**Not authorized by this section:**

- mutation of a candidate already at `FREEZE`
- mutation of an already materialized Collective
- rewriting Pattern B 6 history (§7.3)
- alias matching
- Unicode or numeral normalization
- religious-equivalence inference
- automatic replacement
- Production writes
- Seed writes during evidence classification (§9)

### 6.5 Erroneous pre-FREEZE replacement

```text
ERRONEOUS_PRE_FREEZE_REPLACEMENT_POLICY
= INVALIDATE_REPLACEMENT_AND_RESUME_ORIGINAL_CANDIDATE
```

**Scope.** This section applies only when all of the following hold:

1. a replacement candidate was authorized under §6.4 before `FREEZE`
2. the authorization is later shown to rely on an erroneous Source transcription /
   verification premise
3. the replacement has not been materialized into Seed 1.1, the DB, or runtime
4. the original candidate identity remains historically identifiable

**A. Erroneous replacement**

- All further A-5b progression stops.
- It must not reach `FREEZE`, be authored into Seed 1.1, be written to the DB, or
  enter runtime.
- Its identity and audit history are preserved.
- It is marked invalidated for further A-5b progression by the Freeze Evidence
  Artifact marker:

  ```text
  replacement_progression = INVALIDATED
  ```

  This marker is an Artifact lifecycle note. It is not an `a5b_freeze_status` value
  and adds nothing to the Seed 1.1 schema or any DB model.
- For §12, the replacement identity keeps its last recorded `a5b_freeze_status`. No
  new status value is introduced. The marker bars any progression from that status.

**B. Original candidate**

- It resumes evaluation as the active candidate identity for the position.
- No new candidate identity is created, and the logical candidate count is unchanged.
- It is re-evaluated under the current contracts.
- Earlier `PASS` / `FAIL` judgments are not inherited automatically.

**C. Historical evaluations**

- Historical erroneous evaluations are preserved.
- They are not current authoritative evaluations.
- The corrected evaluation is authoritative for subsequent A-5b processing.

**D. Evidence inheritance**

- Evidence judgments are not copied automatically from the erroneous replacement to
  the resumed original candidate.
- Source-backed facts may be re-established only through a valid current direct
  verification event (Seed 1.1 contract §12.2, §12.8).

**E. Materialization boundary**

If the erroneous replacement has already been materialized into Seed 1.1, the DB, or
runtime, this section does not apply. Such cases require a separate rollback /
correction process.

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

For a new P1–P5-governed candidate, the Collective `verified_at` and each `memberships[].verified_at` follow Seed 1.1 contract §12.8.

A-5b unset confidence rule. For a new P1–P5-governed Collective:

1. If an existing authoritative contract explicitly determines `confidence` =
   `high` / `medium` / `low`, use that value.
2. Otherwise, `confidence = ""`. This is the existing Seed 1.1 unset/default
   representation (Seed 1.1 contract §5.1).
3. Collective `confidence` is never derived from:
   - `source_type`
   - official-source status
   - `verification_status` (including `source_confirmed`)
   - direct Source access
   - Source `confidence`

`confidence = ""` is not a confidence score. It does not mean low confidence. It is
not a new `high` / `medium` / `low` assignment algorithm, and not a Source → Fact
confidence conversion. A project-wide confidence-assignment policy remains a
separate task.

A-5b member_list_status assignment rule. For a new P1–P5-governed Collective,
`member_list_status` is assigned from the accepted Source as follows:

| Value | Use only when the accepted Source |
|---|---|
| `complete` | explicitly establishes the complete individual member list |
| `partial` | explicitly presents an individual member list **and** establishes that the presented list is incomplete / only part of the Collective |
| `not_enumerated` | establishes the Collective but presents no individual member list |
| `not_determined` | presents individual-member information but does not establish whether that list is complete or partial |

A deity name that appears only as part of the aggregate expression or the
`source_attested_label` does not itself count as an individual member-list entry.
For example, 健磐龍命 inside 「健磐龍命をはじめ家族神１２神」 does not by itself
establish `partial`.

`member_list_status` is never derived from:

- Membership row count
- `member_count` or `member_count_relation`
- known deity rows, canonical names, or aliases
- religious relationships
- legacy notes or external knowledge
- the Collective label alone

No rule of the form "N named deities + a stated total = `partial`" exists.

This rule applies A-1 §4.2 semantics to A-5b. It does not change them, the
Seed 1.1 default (`not_determined`), or the model enum.

Replacement provenance (§6.4). When a replacement is authored, the Freeze Evidence
Artifact for that position records both candidate records and this minimum block:

```text
replacement_provenance
  legacy_identity
    shrine_ref.name_jp
    shrine_ref.address
    source_attested_label            (legacy, verbatim)
  legacy_a5b_freeze_status = HOLD
  legacy_hold_reason                 (explicit P1 failure; cites the replacement's label evidence entry)
  replacement_identity
    shrine_ref.name_jp
    shrine_ref.address
    source_attested_label            (replacement, verbatim)
  replacement_basis                  (source_ref + excerpt of the direct verification, §7.1)
  replacement_evaluation             (the replacement's own §7.1 evidence block and §6.1 result)
```

The legacy and replacement labels are recorded verbatim. They are not normalized
for comparison. This block is an Artifact field only. It adds nothing to the Seed 1.1
schema or to any DB model.

In a Freeze Evidence Artifact, `collective_source_keys` and `memberships[].source_keys` are Seed 1.1 file-local values. They are assigned only at Seed 1.1 authoring (§7.1 "Source reference and Seed linkage"). Before then, the Artifact identifies each Source by semantic Source identity (§7.1).

### 7.1 Freeze Evidence Artifact (new P1–P5-governed FREEZE)

```text
FREEZE_EVIDENCE_ARTIFACT = REPOSITORY_LEVEL_CONFIRMING_EVIDENCE
```

A contract-compliant Freeze Evidence Artifact is the §7 frozen candidate artifact,
extended with the evidence block below. It persists the result of direct
verification against an accepted official Source for an A-5b FREEZE decision. It is
not a separate or parallel artifact type.

The official Source remains the underlying authority. The Artifact does not replace it.

```text
Official Source
-> direct verification
-> Freeze Evidence Artifact
-> A-5b FREEZE
-> Seed 1.1
-> importer
-> DB
```

Minimum evidence block, per evaluated candidate:

```text
candidate identity
  shrine_ref.name_jp
  shrine_ref.address
  source_attested_label

sources[]                         (each Source used for verification)
  source_type
  url
  accessed_at
  verification_status

assertions
  source_attested_label           -> evidence entry
  role                            -> evidence entry
  member_count                    -> evidence entry
  member_count_relation           -> evidence entry
  memberships[]
    deity_ref.display_name        -> evidence entry

evidence entry
  value
  source_ref                      (source_type + url of one sources[] entry)
  excerpt
  location
  support_status
```

Field rules:

- **Candidate identity** uses the existing conventions:
  - Shrine: `shrine_ref.name_jp` + `shrine_ref.address`, resolved by the existing
    Shrine authority (§6.1 condition 2)
  - Collective: resolved Shrine + `source_attested_label` (Seed 1.1 contract §5.3)

  No new DB identity scheme is introduced.
- **Source fields** follow the active Source contract
  (`docs/knowledge/shrine-knowledge-contract.md` "Source契約").
- **`source_ref`** identifies a `sources[]` entry by its semantic Source identity
  (`source_type` + normalized URL). See "Source reference and Seed linkage" below.
- **`value`**: the value proposed for the Seed 1.1 field.
- **`excerpt`**: the exact Source text sufficient to audit the assertion. It stores
  only the minimum excerpt needed for auditability, not a copy of the Source.
- **`location`**: the Source location or surrounding context, when available.
- **`support_status`**: one of `SUPPORTED`, `UNSUPPORTED`, `AMBIGUOUS`,
  `NOT_APPLICABLE`.
- **`verified_at` (§7)**: follows Seed 1.1 contract §12.8. One direct verification
  event provides the same `verified_at` only to assertions directly verified during
  that event. A verification recorded without an ISO-8601 datetime cannot supply
  `verified_at`, and a new direct verification event is required.

Required assertions:

- `source_attested_label`
- each supplied Membership
- `role`, when a concrete role other than `unknown` is proposed
- `member_count` / `member_count_relation`, when a value other than
  `null` / `unspecified` is proposed

A contract-valid fallback value is recorded with the `support_status` its Source
evidence has. The fallbacks are `role = unknown` under P4, and
`unspecified` / `null` under P5 when no numeric count is established.

Policy linkage (canonical text: Seed 1.1 contract §12.7):

- **P1:** the label entry's `excerpt` / `location` must show the label as a permitted
  contiguous substring of the Source.
- **P3:** legacy Facts may assist discovery. They cannot cause any entry to receive
  `SUPPORTED`.
- **P4:** a concrete `role` is `SUPPORTED` only when the Source directly supports
  the Collective role and any Source-expression → role-enum mapping is valid under
  an existing contract.
- **P5:** a concrete count / relation is `SUPPORTED` only when the Source
  establishes both the numeric value and its semantics. A numeric expression with
  unresolved semantics is `AMBIGUOUS`, and the candidate is HOLD (§6.2).
- **`NOT_APPLICABLE`** is permitted only where the governing contract makes the
  assertion non-applicable.

Membership evidence (Membership Evidence B, §5.2):

- Each Membership entry is independently auditable and records its own
  `source_ref` and `excerpt`.
- Collective evidence entries do not establish Membership evidence.
- A Membership must not be derived solely from the Collective label, the member
  count, list length, or legacy Membership / Deity Facts.

Source reference and Seed linkage:

```text
FREEZE_ARTIFACT_SOURCE_REFERENCE = SEMANTIC_SOURCE_IDENTITY
```

- **Portable identity.** The Artifact identifies an official Source portably by
  `source_type` + normalized URL. This is the existing Source semantic identity
  (Source contract "Import時のSource semantic identity"; `normalize_source_url` in
  `backend/temples/services/knowledge_seed.py`).
- **`source_key` is not portable.** It is not a Source identity in the Artifact. It
  remains a Seed 1.1 file-local reference only (Seed 1.1 contract §5.1, §6.1).
- **Not yet in a Seed.** The Artifact may record a directly verified official Source
  that has not yet been authored into any Seed 1.1 file.
- **No key ownership.** The Artifact does not reserve, issue, or own a future
  `source_key`.
- **Later Seed 1.1 authoring:**
  1. Define the Source in that seed's `sources[]`.
  2. Assign a non-blank seed-local `key` under the existing Seed 1.1 rules.
  3. Link the Seed Source to the Artifact Source by exact semantic Source
     identity (`source_type` + normalized URL).
- **Keys need not match.** The seed-local key does not need to equal any identifier
  in the Artifact.
- **§5.1 / §5.2.** Their `source_keys` requirements are satisfied in the Seed 1.1
  packet by these linked seed-local keys.
- **No new registry.** No repository-wide Source key or Source registry is
  introduced.

### 7.2 Architecture boundary

```text
Freeze Evidence Artifact = why a candidate / value is supportable
Seed 1.1                 = values selected for import + Source references
Database                 = runtime Facts + Source relations
```

The Freeze Evidence Artifact is not a Source registry, a Seed, Production data,
runtime data, or a copy of the official Source. Its fields are not added to the
Seed 1.1 schema or to any DB model. The importer neither reads nor writes it.

### 7.3 Pattern B 6 compatibility

The six completed Pattern B Collectives are pre-policy / legacy freeze evidence:

- Seed: `backend/temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json`
- Closure: `docs/audit/collective-deity-a5b-production-final-closure-classification.md`

This contract does not require their retroactive migration solely because it now
exists, and it does not change their Seed or DB data. A future material re-authoring
of any of them under the current P1–P5 process must use the current Freeze Evidence
Artifact contract.

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

Not every audit document is confirming evidence:

- ordinary audit notes, analysis notes, and historical audit prose remain
  discovery-only under P2 (Seed 1.1 contract §12.2)
- only a contract-compliant Freeze Evidence Artifact (§7.1) can be the
  repository-level confirming record of direct Source verification for a new
  P1–P5-governed FREEZE

Committing a Freeze Evidence Artifact, or any other audit document, to the
repository is not a Production write and not a DB mutation.

## 10. Determinism / reproducibility

The candidate input set must be fixed before classification. A §6.4 replacement does not change the fixed set: it occupies an existing position, and the reproducibility comparison includes both identities and the replacement provenance (§7).

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
- every candidate identity has exactly one `a5b_freeze_status`. A §6.4 position holds two identities: the legacy identity (`HOLD`) and the replacement identity (its own status). The logical candidate count is unchanged
- every §6.4 replacement records the replacement provenance (§7)
- every `FREEZE` candidate satisfies all applicable Source-backed conditions
- every new P1–P5-governed `FREEZE` candidate has a contract-compliant Freeze Evidence Artifact (§7.1)
- every supplied Membership has independent Source evidence
- every HOLD / EXCLUDE has an explicit reason
- no unresolved conflict is hidden by inference
- no Production or DB mutation occurred during the freeze audit
- the frozen artifact is reproducible under its fixed comparison contract

Only then may A-5b be recorded as closed.

## 13. Revision record — Mother Ship P1–P5 (2026-10-01)

Source of the decisions: Mother Ship resolution of the questions in
`docs/audit/collective-deity-a5b-deferred-ready-4-policy-gap.md` §6.
Canonical policy text: `docs/audit/collective-deity-knowledge-seed-v1-1-contract.md` §12.

Superseded wording:

| Location | Previous wording | Replaced because |
|---|---|---|
| §6.1 condition 3 | "`source_attested_label` is non-blank, Source-attested, and unmodified" | "unmodified" did not define extraction. P1 permits contiguous verbatim extraction and prohibits all other changes |
| §6.1 condition 4 | "at least one valid Source is traceable for the Collective" | P2 requires the Source content to directly support the assertion, not traceability alone |
| §6.1 condition 5 | "every proposed Collective field is supported by the recorded Source or is a contract-defined default" | P5 forbids `unspecified` / `null` when a numeric expression exists with unestablished semantics. P4 fixes `role = unknown` as the only fallback |

Added: §5.1 policy pointer and three HOLD conditions in §6.2.

Unchanged:

- FREEZE / HOLD / EXCLUDE vocabulary
- identity contract
- Membership Evidence B
- mutation prohibition
- downstream write sequence

This revision does not reclassify any candidate or change any recorded closure.

## 14. Revision record — Freeze Evidence Artifact (2026-10-01)

Mother Ship decision:

```text
FREEZE_EVIDENCE_ARTIFACT = REPOSITORY_LEVEL_CONFIRMING_EVIDENCE
```

Origin: the ambiguity between Seed 1.1 contract §12.2 ("audit notes … discovery
evidence only") and the §9 sentence below.

Superseded wording:

| Location | Previous wording | Replaced because |
|---|---|---|
| §9 | "A frozen audit artifact may be committed to the repository. That repository artifact is evidence, not a Production data write." | It did not separate ordinary audit material (discovery-only under P2) from a contract-compliant Freeze Evidence Artifact |

Added:

- §6.1 condition 12
- two §6.2 HOLD conditions, and an Artifact note on the P5 HOLD condition
- §7.1–§7.3
- one §12 closure criterion

Unchanged:

- the P2 direct-Source requirement
- Membership Evidence B
- FREEZE / HOLD / EXCLUDE vocabulary
- the identity contracts
- Seed 1.1 schema, importer, DB models, runtime

This revision does not reclassify any candidate and does not change any recorded
closure, including Pattern B 6.

## 15. Revision record — Direct Verification Timestamp Policy (2026-10-01)

Canonical text: Seed 1.1 contract §12.8.

Changed:

- **§6.1 condition 9.** Previously it required only that `verified_at` satisfy the
  Knowledge contract. For a new P1–P5-governed Collective or Membership,
  `verified_at` must now also be the completion timestamp of the direct verification
  event (Seed 1.1 contract §12.8).
- **§7 and §7.1.** Added references stating which event a `verified_at` value may come
  from, and that a date-only verification cannot supply it.

Consequence under the existing gates (no new gate added):

- A candidate whose direct verification has no recorded ISO-8601 datetime cannot
  satisfy §6.1 condition 9 with `source_confirmed` / `reviewed` metadata.
- The existing §6.2 HOLD condition "verification metadata cannot be established
  under the current contract" applies until a new direct verification event records
  the datetime.

Unchanged:

- `Source.verified_at` semantics
- §7.3 Pattern B 6 compatibility
- Seed 1.1 schema, DB models, importer, runtime, migrations, seed data
- candidate classifications

## 16. Revision record — Artifact Source reference (2026-10-01)

Mother Ship decision:

```text
FREEZE_ARTIFACT_SOURCE_REFERENCE = SEMANTIC_SOURCE_IDENTITY
```

Superseded wording:

| Location | Previous wording | Replaced because |
|---|---|---|
| §7.1 `sources[]` | listed `source_key` as a Source field of the Artifact | `source_key` is file-local to a Seed 1.1 file and is not a portable Source identity |
| §7.1 evidence entry | `source_key` | Replaced by `source_ref` (`source_type` + url of a `sources[]` entry) |
| §7.1 Membership evidence | "records its own `source_key` and `excerpt`" | Membership evidence now records its own `source_ref` |

Added:

- the §7 note on when `collective_source_keys` / `memberships[].source_keys` are
  assigned
- the §7.1 "Source reference and Seed linkage" rules

Unchanged:

- Seed 1.1 `source_key` semantics (file-local; Seed 1.1 contract §5.1, §6.1, §8)
- the Source semantic identity (`source_type` + normalized URL)
- Membership Evidence B
- §12.8 timestamp policy
- Pattern B 6 (§7.3)
- the Seed 1.1 schema, importer, DB models, runtime

No key-generation convention and no Source registry is introduced.

## 17. Revision record — Pre-FREEZE source-backed replacement (2026-10-01)

Mother Ship decision:

```text
PRE_FREEZE_REAUTHORING_POLICY = ALLOW_SOURCE_BACKED_REPLACEMENT_WITH_PROVENANCE
```

Origin: the contract gap on pre-FREEZE label replacement found for a
`DEFERRED_READY` candidate whose legacy label fails P1.

Superseded or extended wording:

| Location | Previous wording | Change |
|---|---|---|
| §4 | "preserve the fixed candidate input set" | Clarified that a §6.4 replacement preserves the set |
| §6.1 condition 1 | "candidate belongs to the fixed A-5b input set" | Also admits a §6.4 replacement occupying a legacy position |
| §6.3 | "it is outside the fixed A-5b candidate input set" | A §6.4 replacement is not outside the set |
| §10 | "The candidate input set must be fixed before classification." | Replacement does not change the set. The comparison includes both identities |
| §12 | "every candidate has exactly one `a5b_freeze_status`" | Applies per candidate identity. The logical count is unchanged. Replacement provenance is required |

Added:

- §6.4, including the precedence rule: the historical candidate-freeze document is
  not rewritten, and the Freeze Evidence Artifact's current evaluation and
  replacement provenance govern subsequent A-5b processing
- §7 replacement provenance block

Unchanged:

- P1–P5 and Seed 1.1 contract §5.3 identity (A-5a not amended)
- §9 mutation prohibition
- Membership Evidence B
- §7.3 Pattern B 6
- the Seed 1.1 schema, DB models, importer, runtime

This revision does not perform any replacement and does not reclassify any candidate.

## 18. Revision record — A-5b unset confidence rule (2026-10-01)

Mother Ship decision for a new P1–P5-governed Collective:

```text
No upstream authoritative high / medium / low assignment rule
-> confidence = ""
```

Changed:

- §6.1 condition 9 references the rule.
- §7 states the rule.

Unchanged:

- Knowledge contract confidence semantics
- the Source confidence prohibitions (PR-C1)
- the Seed 1.1 `confidence` default (`""`)
- importer, models, Recommendation expression-strength behavior

No confidence scoring model is introduced.

## 19. Revision record — A-5b member_list_status assignment rule (2026-10-01)

Mother Ship decision: the four-state assignment semantics in §7, plus the
aggregate-expression rule:

```text
deity name inside aggregate expression != individual member list
```

Changed:

- §6.1 condition 5 references the rule.
- §7 states the rule.

Unchanged:

- A-1 §4.2 vocabulary and semantics
- Seed 1.1 `member_list_status` default and the prohibition on deriving it from
  Membership rows
- model enum, importer, runtime
- candidate classifications

## 20. Revision record — Erroneous pre-FREEZE replacement lifecycle (2026-10-01)

Mother Ship decision:

```text
ERRONEOUS_PRE_FREEZE_REPLACEMENT_POLICY
= INVALIDATE_REPLACEMENT_AND_RESUME_ORIGINAL_CANDIDATE
```

Origin: a §6.4 replacement whose authorization rested on an erroneous Source
transcription, found before `FREEZE` / Seed / DB materialization.

Added:

- §6.5
- the Artifact lifecycle marker `replacement_progression = INVALIDATED`

Unchanged:

- the FREEZE / HOLD / EXCLUDE vocabulary
- §6.4
- Seed 1.1 schema, DB models, importer, runtime
- the historical candidate-freeze document
