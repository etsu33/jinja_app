# Knowledge Seed 1.1 Collective / Membership Field Contract

## Status

- Status: `A-5a FIELD CONTRACT FIXED / DOCUMENTATION ONLY`
- Recorded at: `2026-09-27`
- Base: `develop@ea525a924141aa2bdc959a868f410b9632702219`
- Branch: `docs/collective-deity-knowledge-seed-v1-1-contract`
- Production write: **NONE**
- Backfill execution: **NONE**
- Runtime activation: **NONE**

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
| `source_attested_label` | Yes | none | Non-blank Source-attested aggregate expression. Not an invented canonical group name. |
| `role` | No | `unknown` | Reuses `ShrineDeity.ROLE_CHOICES`: `primary`, `enshrined`, `secondary`, `unknown`. |
| `sort_order` | No | `0` | Integer, 0 or greater. |
| `member_count` | Conditional | `null` | Integer 0 or greater, or null. Boolean is not accepted as an integer. |
| `member_count_relation` | No | `unspecified` | `exact`, `minimum`, `approximate`, `unspecified`. |
| `member_list_status` | No | `not_determined` | `complete`, `partial`, `not_enumerated`, `not_determined`. |
| `verification_status` | No | `draft` | Reuses the current Knowledge verification enum. |
| `confidence` | No | empty string | Reuses the current Knowledge confidence enum. |
| `verified_at` | Conditional | `null` | ISO-8601 datetime. Required for statuses already requiring it in the current Knowledge contract. |
| `note` | No | empty string | Editorial / audit note only. Must not be parsed into Facts or Memberships. |
| `source_keys` | Yes | none | Non-empty list of Source keys defined in the same seed. Collective owns this Evidence relation. |
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
| `verified_at` | Conditional | `null` | ISO-8601 datetime; follows current verification-status consistency rules. |
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
