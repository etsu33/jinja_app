# A-5b Source-backed Collective Backfill Candidate Freeze

## Status

- Status: CANDIDATE_UNIVERSE_CLOSED / NO DATA WRITE
- Recorded at: 2026-09-27
- Base: develop@a5768c97f1e40184b1e3b5c9fc503cb5ff4015c7
- A-5a importer: merged by PR #3014
- Production write: **NONE**
- Runtime activation: **NONE**
- Candidate lifecycle change: **NONE**
- Model Risk release: **NONE**

## 1. Purpose

A-5b begins by freezing the repository-backed candidate universe before any
Knowledge Seed 1.1 data is authored.

This task answers only:

~~~text
Which existing Source-reviewed Knowledge records contain a source-attested
collective / aggregate deity structure that the new Collective model may
represent?
~~~

It does not select the final execution subset, author the backfill seed, or
write any database.

## 2. Authority and boundaries

The following contracts remain authoritative:

~~~text
Named Collective Migration = C
  Model Foundation
  -> Source-backed backfill
  -> Runtime activation
  -> legacy collective cleanup

COLLECTIVE_IDENTITY =
  SHRINE_PLUS_SOURCE_ATTESTED_LABEL

KNOWLEDGE_SEED_SCHEMA =
  VERSION_1_1_WITH_1_0_BACKWARD_COMPATIBILITY

Membership Evidence = B
~~~

Backfill remains additive.

Therefore this task must not:

- delete or rewrite legacy ShrineDeity rows
- parse free-text notes automatically into data
- synthesize unknown members
- create individual ShrineDeity rows only to satisfy Membership
- change Runtime / Recommendation behavior
- write Production
- release any Model Risk HOLD

## 3. Audit method

The candidate universe was derived from all 14 repository Knowledge Seed JSON files under:

~~~text
backend/temples/data/knowledge_seeds/
~~~

The audit searched Source / Deity notes for repository-preserved evidence of
collective structure, including:

~~~text
総称
集合
奉称
御三神
家族神
外８柱
諸神
三社権現
三社明神
~~~

A text hit alone is not admission. Each hit was classified against the current
Shrine block, current Source row, current individual Deity rows, and A-1
migration patterns.

## 4. Classification vocabulary

### BACKFILL_READY

Repository evidence already records:

- a source-attested collective label/expression
- the current Shrine identity
- accepted Source identity
- enough structure to author a 1.1 Collective without inference

Memberships are allowed only where the existing individual ShrineDeity rows
and the same reviewed Source support the relation.

### BACKFILL_READY_COLLECTIVE_ONLY

The Collective itself is source-backed, but A-5b must create no Membership
that would require a new individual ShrineDeity.

This is especially important because new individual ShrineDeity rows would
already be visible to existing Runtime and would violate the A-5 Runtime boundary.

### SOURCE_REVIEW_REQUIRED

Repository evidence identifies a possible Collective, but one or more of these
must be re-reviewed before seed authoring:

- exact source_attested_label
- current-vs-historical meaning
- whether the phrase denotes one Collective Fact
- member relation scope
- member count semantics
- overlapping / nested collective semantics

No backfill row is authorized from this status.

### EXCLUDED_FROM_A5B

The record is outside this backfill track because it is held by another Gate,
is not current Shrine deity structure, or repository evidence explicitly says
not to aggregate it.

## 5. Frozen BACKFILL_READY universe

### 5.1 Pattern B: existing individual members + source-backed collective label

| Shrine | Collective label | Existing members | Source key | Pattern | Freeze status |
|---|---|---:|---|---|---|
| 箱根神社 | 箱根大神 | 3 | batch9-hakone-official | B | BACKFILL_READY |
| 寒川神社 | 寒川大明神 | 2 | batch10-samukawa-deities | B | BACKFILL_READY |
| 二荒山神社 | 二荒山大神 | 3 | batch12-futarasan-official | B | BACKFILL_READY |
| 住吉神社（博多） | 住吉五所大神 | 5 | batch12-sumiyoshi-hakata-official | B | BACKFILL_READY |
| 安房神社 | 忌部五部神 | 5 | batch12-awa-official | B | BACKFILL_READY |
| 王子神社 | 王子大神 | 5 | batch14-oji-official | B | BACKFILL_READY |

For these rows, the repository already preserves both:

~~~text
Collective exists
+
named individual members exist as ShrineDeity rows
~~~

The same reviewed Source also records the member relation.

A future seed may therefore contain:

~~~text
Collective
+
Membership rows to the already-existing individual ShrineDeity rows
~~~

without creating new individual Deity Facts.

### 5.2 Pattern A / D: legacy collective representation, no membership synthesis

| Shrine | Collective label | Current representation | Source key | Pattern | Freeze status |
|---|---|---|---|---|---|
| 八坂神社 | 八柱御子神 | collective label currently stored as one ShrineDeity; individual 8 are not enumerated | src-999044 | A + D | BACKFILL_READY_COLLECTIVE_ONLY |
| 東京大神宮 | 造化の三神 | collective label currently stored as one ShrineDeity; three names are described by Source but not present as individual ShrineDeity rows for this Shrine | src-999050 | A | BACKFILL_READY_COLLECTIVE_ONLY |

A-5b may add the new Collective representation while leaving the legacy
ShrineDeity row untouched.

For 東京大神宮, A-5b must **not** create the three individual ShrineDeity rows
merely to populate Membership. Doing so would change current Runtime before A-6.

Therefore initial A-5b representation is:

~~~text
Collective
Memberships = []
legacy ShrineDeity remains
~~~

Any later individual-member activation requires a separate reviewed data/runtime task.

### 5.3 Pattern C: known named member + unnamed remainder

| Shrine | Source-attested aggregate expression | Known existing member | Unknown remainder | Source key | Freeze status |
|---|---|---|---:|---|---|
| 富岡八幡宮 | 応神天皇（誉田別命）外８柱 | 応神天皇 | 8 | batch13-tomioka-official | BACKFILL_READY |
| 阿蘇神社 | 健磐龍命をはじめ家族神12神 | 健磐龍命 | 11 | src-999035 | BACKFILL_READY |

These are not invented canonical group names. They are repository-preserved
Source-attested aggregate expressions, which is exactly what
source_attested_label is designed to store.

No unknown member is created.

The future seed shape must preserve:

~~~text
member_list_status = partial
known Membership only
unnamed remainder stays unnamed
~~~

The exact member_count_relation, role, and final field values must still be
verified from the frozen Source packet during seed authoring; this candidate
freeze does not invent those values.

## 6. SOURCE_REVIEW_REQUIRED universe

### 6.1 大國魂神社

Repository evidence records two excluded collective expressions:

~~~text
御霊大神
国内諸神
~~~

Source key:

~~~text
batch10-okunitama-official
~~~

Previous seed work intentionally excluded both under the old individual-Deity
model because the individual identities were not determined.

The new model removes that structural blocker, but the current repository note
does not freeze enough exact semantics for immediate seed authoring.

Required re-review:

- exact Source wording
- whether each expression is a separate current enshrinement Collective
- role
- whether a member count is stated
- whether zero Memberships is the correct representation

Status:

~~~text
SOURCE_REVIEW_REQUIRED
~~~

### 6.2 住吉神社（博多） — 住吉三神

The Source note also preserves:

~~~text
住吉三神
= 底筒男神 + 中筒男神 + 表筒男神
~~~

All three member rows exist.

However the same Shrine also has the larger source-backed collective:

~~~text
住吉五所大神
= 住吉三神 + 天照皇大神 + 神功皇后
~~~

The current model can technically hold overlapping Collectives, but A-1 did not
freeze a policy for representing nested/overlapping named collectives.

Status:

~~~text
SOURCE_REVIEW_REQUIRED
reason = OVERLAPPING_COLLECTIVE_SEMANTICS
~~~

No automatic creation of both groups.

### 6.3 浅草神社 — 三社権現 / 三社明神

Repository notes state that the same three individual deities were historically
called:

~~~text
三社権現
三社明神
~~~

All three member rows exist, but the repository evidence also contains historical
shrine-name transitions using the same wording.

A-5b must not assume these are two current Collective deity Facts without a
dedicated temporal/source review.

Status:

~~~text
SOURCE_REVIEW_REQUIRED
reason = CURRENT_VS_HISTORICAL_LABEL
~~~

### 6.4 芝大神宮 — 「5柱の家族神」

Repository Source notes confirm five named family deities, but the repository
does not currently preserve a sufficiently clear exact aggregate label suitable
for deterministic source_attested_label identity.

Status:

~~~text
SOURCE_REVIEW_REQUIRED
reason = EXACT_SOURCE_ATTESTED_LABEL_NOT_FROZEN
~~~

## 7. Explicit exclusions

### 7.1 wave0-014 宮城縣護國神社

Repository Source expression:

~~~text
明治維新以降戦歿者の御霊 56,091柱
~~~

This is structurally compatible with the new Collective model, but it is **not**
an A-5b existing-Knowledge backfill candidate.

Current lifecycle authority remains:

~~~text
candidate_id = wave0-014
owning_gate = G3
model_risk_classification = MODEL_CHANGE_REQUIRED
model_risk_release_status = HOLD
~~~

Therefore:

~~~text
EXCLUDED_FROM_A5B
~~~

Model capability and A-5b must not be used as a side-door G3 release.

### 7.2 玉前神社 — 「その一族の神々」

The phrase appears in a festival-description context and is not established by
the current seed as the Shrine's current enshrined Collective.

Status:

~~~text
EXCLUDED_FROM_A5B
reason = NOT_CURRENT_DEITY_STRUCTURE
~~~

### 7.3 wave0 Batch 03 packet boundary

A current seed note explicitly records:

~~~text
殿ごとの祭神を集合ラベルへまとめない
~~~

That boundary remains intact.

No grouping is introduced merely because the new model exists.

## 8. Frozen candidate-universe count

The current repository audit freezes:

~~~text
BACKFILL_READY
  Pattern B                  6
  Pattern C                  2
  subtotal                   8

BACKFILL_READY_COLLECTIVE_ONLY
  Pattern A / D              2
  subtotal                   2

SOURCE_REVIEW_REQUIRED
  大國魂神社                 2 expressions
  住吉三神                   1
  浅草神社                   2
  芝大神宮                   1
  subtotal                   6 expressions

EXCLUDED_FROM_A5B
  wave0-014                  1
  玉前神社 related phrase    1
  explicit no-group packet   1 boundary
~~~

Therefore the **frozen technically expressible ready universe is 10 Collective candidates**.

This is not an execution order and is not a Production authorization.

## 9. Candidate-universe closure verification

The frozen 10-candidate ready universe was revalidated after freeze against the
repository-preserved Source identities and the canonical Collective identity
contract.

### 9.1 Source identity revalidation

For every ready candidate, the Source key named by this freeze document was
independently located in the existing Knowledge Seed corpus.

~~~text
ready candidates                  10
source keys resolved              10
source_type = shrine_official     10
unresolved source keys             0
~~~

Result:

~~~text
SOURCE_IDENTITY_REVALIDATION = PASS
~~~

This proves only that the frozen candidate points to the expected accepted
repository Source identity. It does not authorize Production or replace the
Source-backed field review required during seed authoring.

### 9.2 Candidate identity uniqueness

Canonical Collective identity remains:

~~~text
Shrine identity + source_attested_label
~~~

The 10 ready candidates were compared using that compound identity.

~~~text
candidate_count                  10
unique_candidate_identity_count 10
duplicate_candidate_count        0
~~~

Result:

~~~text
CANDIDATE_IDENTITY_DUPLICATE_GATE = PASS
~~~

A label alone is not a cross-Shrine identity key. Nested or overlapping
Collectives inside one Shrine remain governed by their explicit review state;
for example, 住吉三神 remains SOURCE_REVIEW_REQUIRED and is not silently merged
with 住吉五所大神.

### 9.3 Closure result

All candidate-universe closure checks required before Mother Ship execution-set
selection are now satisfied:

~~~text
CANDIDATE_UNIVERSE_FREEZE          PASS
SOURCE_IDENTITY_REVALIDATION       PASS (10/10)
CANDIDATE_IDENTITY_DUPLICATE_GATE  PASS (duplicate = 0)
~~~

Therefore:

~~~text
A5B_CANDIDATE_UNIVERSE_CLOSURE = CLOSED_FROZEN
~~~

Closure scope is limited to candidate discovery, Source identity traceability,
and candidate identity uniqueness. It does not select an execution subset,
author Knowledge Seed 1.1 data, mutate the database, activate Runtime behavior,
or release any Model Risk HOLD.

## 10. Mother Ship execution-set boundary

The candidate universe is now separable from the execution set.

This document does **not** choose which ready candidates are included in the
first A-5b Data PR.

The next Mother Ship decision is:

~~~text
A5B_INITIAL_BACKFILL_SET =
  UNRESOLVED
~~~

Valid selections must be a subset of the 10 ready candidates above.

SOURCE_REVIEW_REQUIRED candidates cannot enter the initial Data PR until
their own review closes.

EXCLUDED_FROM_A5B items cannot enter through this track.

## 11. Next implementation boundary

After Mother Ship fixes A5B_INITIAL_BACKFILL_SET, the next task is a
separate data PR that:

1. starts from current develop
2. authors an isolated Knowledge Seed 1.1 backfill file
3. reuses existing Source identities
4. changes no Runtime code
5. deletes no legacy ShrineDeity
6. runs --validate-only
7. runs isolated --dry-run
8. freezes expected delta
9. applies only to isolated / production-equivalent DB during QA
10. proves second dry-run has zero CREATE / CONFLICT
11. stops before Production

Production remains governed by G7 and explicit Mother Ship approval.

## 12. STOP

This candidate-freeze task stops before:

- seed authoring
- database write
- Runtime activation
- legacy cleanup
- Production operation
- wave0-014 re-entry
- Candidate Master mutation
