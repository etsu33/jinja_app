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

1. candidate belongs to the fixed A-5b input set
2. Shrine identity is deterministically resolvable under existing authority
3. `source_attested_label` is non-blank, Source-attested, and occurs verbatim as one contiguous substring of the accepted official Source, extracted only as permitted by Seed 1.1 contract §12.1 (P1)
4. at least one accepted official Source is traceable for the Collective, and its content has been confirmed to directly support the Collective assertion (§12.2, P2). A note, a legacy Fact, or a prior judgment alone does not satisfy this (§12.2–§12.3, P2–P3)
5. every proposed Collective field is directly supported by the accepted official Source, or is a default that Seed 1.1 contract §12 permits: `role = unknown` under §12.4 (P4); `member_count_relation = unspecified` / `member_count = null` only when no numeric count is established, under §12.5 (P5)
6. every supplied Membership resolves to an individually attributable same-Shrine Deity under the v1.1 reference contract
7. every supplied Membership has its own non-empty Source evidence
8. member count / count relation values satisfy the existing v1.1 invariant
9. verification / confidence / `verified_at` values satisfy the current Knowledge contract. For a new P1–P5-governed Collective or Membership, `verified_at` also satisfies the Direct Verification Timestamp Policy (Seed 1.1 contract §12.8)
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

For a new P1–P5-governed candidate, the Collective `verified_at` and each `memberships[].verified_at` follow Seed 1.1 contract §12.8.

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
