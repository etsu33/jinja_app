# Knowledge Seed 1.1 Collective / Membership Field Contract

## Status

- Status: `A-5a FIELD CONTRACT FIXED / DOCUMENTATION ONLY`
- Recorded at: `2026-09-27`
- Base: `develop@ea525a924141aa2bdc959a868f410b9632702219`
- Branch: `docs/collective-deity-knowledge-seed-v1-1-contract`
- Production write: **NONE**
- Backfill execution: **NONE**
- Runtime activation: **NONE**
- Revision 2026-10-01: Mother Ship P1–P5 authoring policy added as §12
- Revision 2026-10-01: Freeze Evidence Artifact linkage added (§12.2, §12.7). The Artifact schema is defined in the A-5b contract §7.1
- Revision 2026-10-01: Direct Verification Timestamp Policy added (§12.8). Referenced from §5.1 and §6.1 `verified_at`

## 1. Purpose

A-5a defines the portable JSON field contract used to import
`ShrineDeityCollective` and `ShrineDeityCollectiveMembership` through the existing
Knowledge importer.

This document freezes the seed shape only. It does not perform the importer implementation,
backfill, Production write, Runtime activation, Model Risk release, or Candidate Master change.

## 2. Mother Ship decisions already fixed

```text
WRITE_PATH_AUTHORITY =
  EXTEND_EXISTING_KNOWLEDGE_IMPORTER

BULK_WRITE_POLICY =
  PROHIBITED_FOR_COLLECTIVE_BACKFILL

INTEGRITY_BOUNDARY =
  DB_ROW_LOCAL_MODEL_SERVICE_CROSS_ROW

COUNT_RELATION_DB_CONSTRAINT =
  ADD_BEFORE_BACKFILL

COLLECTIVE_IDENTITY =
  SHRINE_PLUS_SOURCE_ATTESTED_LABEL

KNOWLEDGE_SEED_SCHEMA =
  VERSION_1_1_WITH_1_0_BACKWARD_COMPATIBILITY
```

A-5a must implement these values as written and must not reopen them.

## 3. Schema version contract

Supported Knowledge Seed versions after A-5a:

```text
1.0
1.1
```

### 3.1 Version 1.0

Version 1.0 keeps the existing contract unchanged:

```text
sources
shrines
  ├ deities
  └ histories
```

Existing 1.0 seed files do not need to be rewritten.

If a 1.0 shrine block contains a `collectives` field, validation must fail instead of
silently ignoring it. Collective / Membership data requires schema version 1.1.

### 3.2 Version 1.1

Version 1.1 is additive:

```text
sources
shrines
  ├ deities
  ├ histories
  └ collectives
       └ memberships
```

A 1.1 seed without `collectives` is valid. Upgrading a file to 1.1 does not require
creating Collective rows.

The existing Source, Deity, History, and Shrine reference field meanings remain unchanged.

## 4. Shrine block extension

A 1.1 shrine block may contain:

```json
{
  "shrine_ref": {
    "name_jp": "神社名",
    "address": "住所"
  },
  "deities": [],
  "histories": [],
  "collectives": []
}
```

`collectives` is optional and defaults to an empty list.

## 5. Collective entry

Each item in `collectives` maps to one `ShrineDeityCollective`.

### 5.1 Fields

| Seed field | Required | Default | Contract |
|---|---:|---|---|
| `source_attested_label` | Yes | none | Non-blank Source-attested aggregate expression. Not an invented canonical group name. Extraction: §12.1 (P1). |
| `role` | No | `unknown` | Reuses `ShrineDeity.ROLE_CHOICES`: `primary`, `enshrined`, `secondary`, `unknown`. Value selection: §12.4 (P4). |
| `sort_order` | No | `0` | Integer, 0 or greater. |
| `member_count` | Conditional | `null` | Integer 0 or greater, or null. Boolean is not accepted as an integer. Value selection: §12.5 (P5). |
| `member_count_relation` | No | `unspecified` | `exact`, `minimum`, `approximate`, `unspecified`. Value selection: §12.5 (P5). |
| `member_list_status` | No | `not_determined` | `complete`, `partial`, `not_enumerated`, `not_determined`. |
| `verification_status` | No | `draft` | Reuses the current Knowledge verification enum. |
| `confidence` | No | empty string | Reuses the current Knowledge confidence enum. |
| `verified_at` | Conditional | `null` | ISO-8601 datetime. Required for statuses already requiring it in the current Knowledge contract. For a new P1–P5-governed Collective: §12.8. |
| `note` | No | empty string | Editorial / audit note only. Must not be parsed into Facts or Memberships. |
| `source_keys` | Yes | none | Non-empty list of Source keys defined in the same seed. Collective owns this Evidence relation. Direct support required: §12.2–§12.3 (P2, P3). |
| `memberships` | No | `[]` | Nested Membership entries. Zero Memberships is valid. |

### 5.2 Count relation invariant

The seed parser must reject a Collective unless exactly one branch is true:

```text
member_count_relation IN (exact, minimum, approximate)
AND member_count IS NOT NULL

OR

member_count_relation = unspecified
AND member_count IS NULL
```

This is the same invariant now enforced by DB constraint
`chk_deity_coll_count_rel`.

Do not add stronger rules. In particular:

- do not require `member_count > 0`
- do not require `member_count >= 2`
- do not compare `member_count` with Membership row count
- do not derive `member_count` from Membership rows
- do not derive `member_list_status` from Membership rows
- do not force `complete` to equal any Membership count

`exact + member_count=0` remains valid under this contract.

### 5.3 Collective identity

The fixed natural identity is:

```text
resolved Shrine + source_attested_label
```

`source_attested_label` must be a non-blank string with no leading or trailing whitespace.
Identity comparison uses the stored Source-attested label exactly; the importer does not
canonicalize, translate, synonym-match, or infer religious equivalence.

Within one shrine block, duplicate `source_attested_label` values are invalid.

Target DB planning:

```text
0 matching Collective rows
-> CREATE

1 matching row + expected persisted fields and exact Source relation set match
-> SKIP_EXISTS

1 matching row + meaningful field or Source relation mismatch
-> COLLECTIVE_CONFLICT
-> STOP

2+ matching rows
-> COLLECTIVE_AMBIGUOUS
-> STOP
```

No `update_or_create` and no silent overwrite.

## 6. Membership entry

Each item in `memberships` maps to one
`ShrineDeityCollectiveMembership`.

### 6.1 Fields

| Seed field | Required | Default | Contract |
|---|---:|---|---|
| `deity_ref` | Yes | none | Portable reference to an existing or same-seed individually attributable `ShrineDeity` in the same Shrine. |
| `sort_order` | No | `0` | Integer, 0 or greater. |
| `verification_status` | No | `draft` | Reuses the current Knowledge verification enum. |
| `confidence` | No | empty string | Reuses the current Knowledge confidence enum. |
| `verified_at` | Conditional | `null` | ISO-8601 datetime; follows current verification-status consistency rules. For a new P1–P5-governed Membership: §12.8. |
| `note` | No | empty string | Relation-specific note only. |
| `source_keys` | Yes | none | Non-empty list of Source keys proving this member relation. Never inherited from the Collective. |

### 6.2 deity_ref shape

Knowledge Seed 1.1 fixes the portable Membership reference as:

```json
{
  "deity_ref": {
    "display_name": "個別祭神名"
  }
}
```

Only `display_name` participates in the v1.1 Membership deity reference.

Numeric PKs are prohibited.

The resolver scope is always the already-resolved Shrine:

```text
same Shrine + exact display_name
```

The reference may resolve to:

1. an existing `ShrineDeity` row in the target DB, or
2. a Deity entry declared in the same seed/shrine block and planned for creation.

It must never create a missing Deity merely because a Membership refers to it.

Resolution behavior:

```text
exactly 1 same-Shrine deity
-> RESOLVED

0 matches
-> MEMBERSHIP_DEITY_NOT_FOUND
-> STOP

2+ matches
-> MEMBERSHIP_DEITY_AMBIGUOUS
-> STOP

deity belongs to another Shrine
-> MEMBERSHIP_DEITY_WRONG_SHRINE
-> STOP
```

No alias matching, `canonical_name` inference, note parsing, or nearest-name matching is
allowed in v1.1.

### 6.3 Membership identity

DB authority remains:

```text
Unique(collective, deity)
```

Within a single Collective entry, the same `deity_ref.display_name` may appear only once.

Planning behavior:

```text
Membership does not exist
-> CREATE

Membership exists + expected metadata and exact Source relation set match
-> SKIP_EXISTS

Membership exists + meaningful metadata or Source relation mismatch
-> MEMBERSHIP_CONFLICT
-> STOP
```

## 7. Evidence ownership

A-1 fixed Membership Evidence = B.

Therefore 1.1 seed behavior is:

```text
Collective.source_keys
  -> evidence for Collective existence / properties

Membership.source_keys
  -> evidence for that specific member relation
```

The same Source key may appear in both lists when the same Source supports both facts.

The following is prohibited:

```text
membership.source_keys missing
-> inherit collective.source_keys
```

There is no inheritance.

For A-5 Source-backed backfill, both Collective and every supplied Membership require
their own non-empty `source_keys`.

If a Source establishes only the Collective but does not establish a named member relation:

```text
Collective may be seeded
Membership must not be created
```

A Collective with zero Memberships is valid.

## 8. Structural validation

Before any DB write, `--validate-only` / parser validation must detect at minimum:

- unsupported schema version
- `collectives` used with schema 1.0
- non-list `collectives` / `memberships`
- blank or malformed `source_attested_label`
- duplicate Collective identity inside the same shrine block
- invalid role
- negative / non-integer sort order
- invalid member count type or negative count
- invalid count relation
- invalid member list status
- invalid verification status / confidence
- missing required `verified_at`
- missing / empty / unknown `source_keys`
- malformed `deity_ref`
- duplicate Membership reference within one Collective

DB-dependent identity resolution belongs to the planning stage and must additionally detect:

- Shrine NOT_FOUND / AMBIGUOUS
- Source CONFLICT / AMBIGUOUS
- Collective existing-row conflict / ambiguity
- Membership Deity NOT_FOUND / AMBIGUOUS / wrong Shrine
- Membership existing-row conflict

Any error or conflict means zero writes.

## 9. Canonical 1.1 examples

### 9.1 Collective whose members are not enumerated

```json
{
  "schema_version": "1.1",
  "sources": [
    {
      "key": "src-collective-example",
      "source_type": "shrine_official",
      "title": "御祭神",
      "publisher": "神社名",
      "url": "https://example.invalid/saijin",
      "verification_status": "source_confirmed",
      "confidence": "high",
      "verified_at": "2026-09-27T00:00:00+09:00"
    }
  ],
  "shrines": [
    {
      "shrine_ref": {
        "name_jp": "神社名",
        "address": "住所"
      },
      "deities": [],
      "histories": [],
      "collectives": [
        {
          "source_attested_label": "Sourceに記載された集合表現",
          "role": "primary",
          "sort_order": 0,
          "member_count": 56091,
          "member_count_relation": "exact",
          "member_list_status": "not_enumerated",
          "verification_status": "source_confirmed",
          "confidence": "high",
          "verified_at": "2026-09-27T00:00:00+09:00",
          "note": "",
          "source_keys": ["src-collective-example"],
          "memberships": []
        }
      ]
    }
  ]
}
```

### 9.2 Named Collective with source-backed known members

```json
{
  "source_attested_label": "Sourceに記載された集合名",
  "role": "enshrined",
  "sort_order": 2,
  "member_count": 2,
  "member_count_relation": "exact",
  "member_list_status": "complete",
  "verification_status": "source_confirmed",
  "confidence": "high",
  "verified_at": "2026-09-27T00:00:00+09:00",
  "note": "",
  "source_keys": ["src-group"],
  "memberships": [
    {
      "deity_ref": {
        "display_name": "祭神A"
      },
      "sort_order": 0,
      "verification_status": "source_confirmed",
      "confidence": "high",
      "verified_at": "2026-09-27T00:00:00+09:00",
      "note": "",
      "source_keys": ["src-membership-a"]
    },
    {
      "deity_ref": {
        "display_name": "祭神B"
      },
      "sort_order": 1,
      "verification_status": "source_confirmed",
      "confidence": "high",
      "verified_at": "2026-09-27T00:00:00+09:00",
      "note": "",
      "source_keys": ["src-membership-b"]
    }
  ]
}
```

The example does not imply that Membership count must equal `member_count`; it only
illustrates one case where the Source happens to establish both.

## 10. Explicit non-goals

A-5a field contract does not:

- migrate existing named Collective rows automatically
- parse existing Deity `note` values
- delete or rewrite legacy `ShrineDeity` rows
- synthesize unknown members
- add numeric DB IDs to seed files
- change Source identity rules
- change current Deity / History identity behavior
- perform the A-5b backfill
- write Production data
- activate Collective data in Runtime
- change Serializer / selector / Recommendation Eligibility
- change Concierge / Compass / Deep Dive / Evidence Transport
- release `wave0-014`
- change Candidate Master status

## 11. A-5a implementation handoff

After this documentation PR is merged, the implementation task is:

```text
existing import_shrine_knowledge
  +
Knowledge Seed 1.1 parser
  +
Collective plan/apply
  +
Membership plan/apply
  +
1.0 backward compatibility
  +
1.1 idempotency / conflict / source-independence tests
```

Canonical write sequence remains the A-4 contract:

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

Do not begin A-5b in the same PR.

## 12. Collective authoring evidence policy (Mother Ship P1–P5)

Revision added 2026-10-01. Origin: the policy questions recorded in
`docs/audit/collective-deity-a5b-deferred-ready-4-policy-gap.md` §6, decided by Mother Ship.

This section is the canonical authoring rule for every new Collective Fact authored
under Knowledge Seed 1.1. It governs what a seed author may write. It does not add
parser or DB invariants. §5.2 and §8 remain the complete structural validation
contract.

```text
P1 LABEL_POLICY    = ALLOW_SYNTACTIC_EXTRACTION
P2 EVIDENCE_POLICY = REQUIRE_DIRECT_SOURCE_SUPPORT
P3 LEGACY_POLICY   = LEGACY_FACT_AS_DISCOVERY_EVIDENCE_ONLY
P4 ROLE_POLICY     = DIRECT_SOURCE_ROLE_ONLY
P5 COUNT_POLICY    = SOURCE_EXPLICIT_COUNT_SEMANTICS_ONLY
```

### 12.1 P1 — `source_attested_label` extraction

A `source_attested_label` may be extracted as a contiguous substring that appears
verbatim in the accepted official Source.

Allowed:

- selecting the contiguous substring that represents the Collective expression
- excluding surrounding heading / category text
- excluding surrounding grammatical predicate text
- trimming leading / trailing whitespace required by schema validity (§5.3)

Required:

- the extracted label occurs verbatim as one contiguous substring in the Source
- extraction does not alter the religious or semantic content
- Source evidence retains enough context to audit the extraction

Prohibited:

- paraphrasing
- synonym replacement
- translation
- character or numeral normalization
- word reordering
- concatenating text from separate Source locations
- generating a canonical name not present in the Source
- semantic inference

### 12.2 P2 — Direct Source support

A new Collective Fact must be directly supported by the accepted official Source.

P2 separates two things:

- **Direct authority.** The accepted official Source content itself directly
  supports the assertion. The Source is the confirming authority.
- **Persisted verification record.** A contract-compliant Freeze Evidence Artifact
  (A-5b contract §7.1) may serve as the canonical repository record of two facts:
  that direct verification occurred, and which Source content supported the
  assertion. The Artifact records the verification result. It is not the
  underlying authority and does not replace the Source.

```text
FREEZE_EVIDENCE_ARTIFACT = REPOSITORY_LEVEL_CONFIRMING_EVIDENCE
```

- `Source.note`, `Deity.note`, ordinary audit notes, analysis notes, historical
  audit prose, legacy Facts, and previous extraction results are
  `DISCOVERY_EVIDENCE_ONLY`. They cannot independently satisfy P2.
- The Source content itself must directly support the new Collective assertion.
- An existing `source_key` may be reused only after confirming that the same Source
  directly supports the new assertion.
- Source identity may be reused. A prior evidence judgment may not be reused
  automatically.

### 12.3 P3 — Legacy ShrineDeity Facts

Legacy ShrineDeity Facts may be used for:

- candidate discovery
- identity matching
- locating candidate Sources / `source_keys`
- migration auditing
- regression comparison

Legacy ShrineDeity Facts must not by themselves establish:

- Collective existence
- Collective semantics
- Collective `role`
- `member_count`
- `member_count_relation`
- Memberships

A legacy `source_key` is not inherited automatically. It may be reused only under
P2 (§12.2), after direct Source verification.

### 12.4 P4 — Collective `role`

Set a concrete Collective `role` only when:

- the accepted official Source directly supports the role of the Collective itself, and
- the Source expression maps to an existing role enum under an existing contract.

Otherwise:

```text
role = unknown
```

If Source wording exists but no authoritative Source-expression → role-enum mapping
exists, use `unknown`.

Prohibited:

- inheriting a legacy ShrineDeity role
- deriving the Collective role from member roles
- deriving the role from the label alone
- deriving the role from page position alone
- deriving the role from general religious knowledge

### 12.5 P5 — `member_count` / `member_count_relation`

Set `member_count` and a non-`unspecified` `member_count_relation` only when the
accepted official Source directly establishes both:

1. the numeric count
2. the semantics of that count

| Source establishes | `member_count` | `member_count_relation` |
|---|---|---|
| explicit total N | N | `exact` |
| explicit at-least N | N | `minimum` |
| explicit approximate N | N | `approximate` |

`unspecified` / `null` is permitted only when the Source-backed Collective has no
established numeric count.

If a numeric expression exists but its semantics cannot be established:

- do not discard it by using `unspecified` / `null`
- the candidate remains unresolved / HOLD until the count semantics are established

Prohibited:

- inferring exactness from a numeral alone
- deriving the count from Membership row count
- inheriting the count from a legacy Fact
- converting an ambiguous numeric expression to `unspecified` / `null`
- inferring total vs. remainder

### 12.6 Relation to earlier sections

- §5.1 `source_attested_label`, `role`, `member_count`, `member_count_relation`:
  the allowed values are unchanged. §12 governs which value the author may choose.
- §5.2: the parser / DB invariant is unchanged. P5 is an authoring evidence rule. It
  is enforced at review / A-5b freeze, not by the parser.
- §5.3: exact identity matching is unchanged. The P1-extracted label is the stored
  label and is compared exactly.
- §6.2 / §7 / §10: the prohibitions on note parsing, Membership from note-only names,
  and automatic Source inheritance are unchanged. P2 and P3 do not relax them.

### 12.7 Freeze Evidence Artifact linkage

The minimum Artifact schema and the FREEZE / HOLD gates are defined in
`docs/audit/collective-deity-source-backed-backfill-candidate-freeze-contract.md`
§6 and §7.1. This section links each policy to the Artifact's assertion
`support_status` (`SUPPORTED` / `UNSUPPORTED` / `AMBIGUOUS` / `NOT_APPLICABLE`).

- **P1:** the `source_attested_label` assertion preserves enough exact Source
  context to verify that the label is a permitted contiguous substring of the
  Source (§12.1).
- **P2:** the official Source is the confirming authority. The Artifact is the
  canonical repository persistence of the direct-verification result. Ordinary
  audit notes remain discovery-only (§12.2).
- **P3:** legacy Facts may assist discovery and history. They cannot cause an
  assertion to receive `SUPPORTED` (§12.3).
- **P4:** a concrete `role` may receive `SUPPORTED` only when both hold:
  1. the accepted Source directly supports the Collective role, and
  2. any required Source-expression → role-enum mapping is valid under an
     existing contract.

  Otherwise the contract-valid fallback `role = unknown` applies (§12.4).
- **P5:** a concrete `member_count` / `member_count_relation` may receive
  `SUPPORTED` only when the Source establishes both the numeric value and the
  semantics of the count. If a numeric expression exists but its semantics are
  unresolved, `support_status = AMBIGUOUS` and the candidate remains HOLD. The
  ambiguity must not be converted to `unspecified` / `null` to pass FREEZE (§12.5).

The Artifact contract adds no field to the Seed 1.1 schema (§5–§6). It adds no
parser rule (§8) and no DB schema.

`verified_at` for a new P1–P5-governed Collective or Membership follows §12.8.

### 12.8 Direct Verification Timestamp Policy

Scope: a new P1–P5-governed Collective (§5.1 `verified_at`) or Membership (§6.1
`verified_at`).

`verified_at` records the timestamp at which the direct verification against the
accepted official Source supporting that Fact or relation was completed (P2, §12.2).

Rules:

- Record it as an ISO-8601 datetime at verification time.
- It must satisfy the current Knowledge verification-status consistency rules:
  `source_confirmed` / `reviewed` require `verified_at`
  (`docs/knowledge/shrine-knowledge-contract.md`; model
  `_validate_verified_at_consistency`).
- Do not reconstruct it from a date-only audit record.
- Do not inherit it from `Source.accessed_at`.
- Do not inherit it from a Source's prior `verified_at`.
- Do not inherit it from a legacy Fact's or Membership's `verified_at`.
- Do not infer it from file timestamps, commit timestamps, screenshots, notes, or
  incidental metadata.
- One direct verification event may provide the same `verified_at` to multiple
  assertions only when those assertions were directly verified during that same
  event.
- If a direct verification was completed without recording an ISO-8601 datetime,
  do not reconstruct the datetime later. A new direct verification event is
  required before `source_confirmed` / `reviewed` metadata may be authored for the
  new Fact or relation.

Unchanged by this policy:

- `Source.verified_at` remains Source metadata. It is not redefined as a Collective
  or Membership verification time.
- No Seed 1.1 field, parser rule (§8), DB field, model, importer, runtime, migration,
  or seed data is added or changed.
- Pattern B 6 legacy compatibility (A-5b contract §7.3) is unchanged.
