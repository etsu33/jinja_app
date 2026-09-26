# Collective Deity Backfill Write / Integrity Gate

## Status

**A-4: READY_FOR_MOTHER_SHIP_DECISION / DOCUMENTATION ONLY**

- Repository: `etsu33/jinja_app`
- Base branch: `develop`
- Base SHA: `aaf66c6bd7ad6c52cbdd6ef473060a1c8a878bcf`
- Branch: `docs/collective-deity-backfill-integrity-gate`
- Production write: **NONE**
- Backfill execution: **NONE**
- Runtime activation: **NONE**
- Model Risk release: **NONE**

本書は、A-2 / A-3 で追加された `ShrineDeityCollective` /
`ShrineDeityCollectiveMembership` へ Source-backed data を投入する前に、
書き込み経路と整合性境界を固定するための Gate である。

A-1 で承認済みの次の決定は変更しない。

```text
Membership Evidence = B
Named Collective Migration = C
```

また、本書だけでは A-5 Source-backed Collective backfill を開始しない。
Mother Ship の明示承認と、本書が定める前提条件の充足が必要である。

---

## 1. Scope

A-4 が扱うのは次の3点である。

1. Write path authority
2. bulk write policy
3. validation / DB constraint boundary

あわせて、A-5 を安全に開始するために必要な以下も記録する。

- dry-run
- idempotency
- Source reuse
- transaction boundary
- conflict / STOP condition
- Production write boundary

A-4 はデータの内容そのものを決めない。

---

## 2. Repository Audit

### 2.1 Current Collective model

`backend/temples/models.py`

`ShrineDeityCollective` は以下を持つ。

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

現在の重要な挙動:

- `member_count_relation` と `member_count` の整合性は `clean()` で検証
- `verification_status` / `verified_at` は既存
  `_validate_verified_at_consistency()` を再利用
- `save()` override はない
- 通常の `objects.create()` は `full_clean()` を自動実行しない
- DB の `CheckConstraint` で member count 整合性は固定されていない
- Runtime / Serializer / Recommendation はこの model をまだ読まない

したがって、Backfill implementation が `full_clean()` を呼ばなければ、
Model Contract を迂回できる。

### 2.2 Current Membership model

`ShrineDeityCollectiveMembership` は以下を持つ。

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

現在の重要な挙動:

- `collective -> CASCADE`
- `deity -> PROTECT`
- `Unique(collective, deity)` は DB constraint
- `collective.shrine_id == deity.shrine_id` は `clean()`
- `save() -> full_clean() -> super().save()`
- Membership Evidence = B により Source は Membership 自身が所有
- Collective Source は Membership へ自動継承されない
- `bulk_create()` / `bulk_update()` / `QuerySet.update()` は
  `save()` / `clean()` を迂回する

same-Shrine invariant は cross-table 条件であり、通常の Django
`CheckConstraint` では表現できない。

### 2.3 Existing Knowledge write path

Current Knowledge import authority:

```text
backend/temples/services/knowledge_seed.py
backend/temples/management/commands/import_shrine_knowledge.py
```

既存 importer は次を既に持つ。

```text
--validate-only
--dry-run
apply
```

`import_shrine_knowledge.py` の current behavior:

- parse / structural validation を先に実施
- Shrine identity を推測せず resolve
- Source identity conflict / ambiguous を plan error として全体停止
- dry-run は CREATE / SKIP plan の計算のみで DB write なし
- apply は単一 `transaction.atomic()`
- Fact create 前に `full_clean()`
- Source create 前にも `full_clean()`
- M2M Source relation を同一 transaction 内で付与
- 途中 failure は全体 rollback
- 同一 seed の再実行で既存 Fact は `SKIP_EXISTS`
- existing Fact を silent overwrite しない

この経路は既に Knowledge Batch で繰り返し利用されており、
新しい parallel importer を作るより再利用する方が既存運用と整合する。

### 2.4 Existing Source identity authority

`knowledge_seed.resolve_source_identity()` が既存 Source の reuse / conflict を扱う。

既存方針:

- reusable identity は reuse
- meaningful metadata conflict は `SOURCE_REUSE_CONFLICT`
- multiple identity matches は `SOURCE_REUSE_AMBIGUOUS`
- conflict / ambiguous は全 import STOP
- Source を推測で作り直して状態合わせしない

Collective / Membership backfill はこの authority を再利用できる。

### 2.5 Existing transaction precedent

Knowledge importer は apply 全体を単一 `transaction.atomic()` で包む。

範囲には既存実装で次が含まれる。

```text
Source create
Shrine resolve
Fact create
Fact-Source M2M
```

Collective / Membership も同じ transaction に含めることで、
partial Collective / partial Membership / orphan Source relation を残さない構造にできる。

### 2.6 Existing cross-row integrity precedent

`docs/audit/canonical-anchor-schema-foundation-implementation-record.md` は、
単一row条件と cross-row 条件の境界を明示している。

Repository precedent:

```text
single-row invariant
-> DB CheckConstraint where practical

cross-row invariant
-> model/service validation

QuerySet.update / bulk_create / raw SQL
-> save()を経由しないため cross-row validation を保証しない
```

この考え方を Collective backfill に適用できる。

---

## 3. Risk Inventory

### R1: Collective validation bypass

次は現在可能である。

```python
ShrineDeityCollective.objects.create(
    shrine=shrine,
    source_attested_label="...",
    member_count_relation="exact",
    member_count=None,
)
```

`objects.create()` は `full_clean()` を呼ばないため、
A-2 で定義した member count contract を通常ORMだけで迂回できる。

### R2: Membership same-Shrine bypass by bulk paths

Membership の通常 `save()` は fail closed だが、

```text
bulk_create
bulk_update
QuerySet.update
raw SQL
```

は `save()` を経由しない。

そのため、cross-Shrine Membership を backfill path が直接作る余地がある。

### R3: Fact exists != Source relation complete

Collective / Membership row を作成しただけでは Evidence-ready ではない。

Membership Evidence = B のため、

```text
Collective.sources
Membership.sources
```

は独立して解決・付与する必要がある。

### R4: Existing row silent mismatch

Existing Knowledge importer は Fact identity が一致すれば
`SKIP_EXISTS` し、silent overwrite しない。

Collective backfill でも単純に「既存rowがあるからSKIP」だけにすると、
同一 identity に対する metadata 差異を見逃す可能性がある。

A-5 では existing Collective / Membership が存在する場合、
expected fields / Source relation が一致しているか確認し、
不一致は `CONFLICT` として STOP する必要がある。

### R5: Production improvisation

Unified Gate の G7 は、Production import 中に unexpected delta が出た場合、
その場で追加 write を行って状態を合わせることを禁止している。

Collective backfill も同じ fail-safe を継承する必要がある。

---

## 4. Write Path Authority

### 4.1 Options

#### Option A: direct ORM from one-off script / shell

```text
script
 -> ShrineDeityCollective.objects.create(...)
 -> Membership.objects.create(...)
```

問題:

- reproducibility が低い
- `full_clean()` 呼び忘れが可能
- dry-run / plan / conflict classification が重複実装になる
- historical Batch 1-7 の local-only gap を再発させる

**Technical recommendation: REJECT**

#### Option B: new dedicated importer

```text
import_collective_deities
 -> new parser
 -> new source resolver
 -> new plan
 -> new transaction
```

利点:

- scope は明確

問題:

- existing `import_shrine_knowledge` と責務重複
- Source identity authority の二重化リスク
- Shrine identity resolution の二重化リスク
- dry-run / idempotency contract の二重化

**Technical recommendation: DO NOT PREFER**

#### Option C: extend existing Knowledge importer

```text
knowledge_seed.py
  -> Collective / Membership seed parsing
  -> existing Shrine identity resolution
  -> existing Source identity resolution

import_shrine_knowledge.py
  -> existing plan
  -> existing dry-run
  -> existing atomic apply
  -> Collective / Membership creation
```

利点:

- current Knowledge write authority を維持
- Source reuse policy を再利用
- dry-run / idempotency / atomicity を再利用
- Production operation の入口が増えない
- existing batch workflow と同じ監査線上に置ける

**Technical recommendation: SELECT C**

### 4.2 Proposed decision token

Mother Ship approval candidate:

```text
WRITE_PATH_AUTHORITY = EXTEND_EXISTING_KNOWLEDGE_IMPORTER
```

この値が承認された場合、A-5 では
`import_shrine_knowledge` の extension だけを canonical backfill write path とする。

Management command は orchestration entry point とし、
Source identity / Shrine identity の authority は既存 service を再利用する。

### 4.3 Direct write prohibition for A-5

A-5 implementation / Production execution では以下を canonical write path としない。

```text
Django shell one-off write
standalone Python one-off write
Admin manual creation
raw SQL
migration RunPython
second importer command
```

test fixture / migration test の setup はこの運用制約の対象外だが、
Production backfill authority にはならない。

---

## 5. Bulk Write Policy

### 5.1 Audit result

Membership same-Shrine validation は `save()` に依存する。

Collective member count consistency は `full_clean()` に依存する。

したがって A-5 で bulk API を使うと、現在固定した Model Contract を
書き込み速度と引き換えに迂回する。

今回の backfill は大規模 transactional ETL ではなく、
source-reviewed Named Collective の段階移行である。

bulk optimization を優先する根拠は repository 上にない。

### 5.2 Technical recommendation

A-5 Collective / Membership backfill では次を禁止する。

```text
bulk_create()
bulk_update()
QuerySet.update()
raw SQL write
```

許可する path:

```text
obj = Model(...)
obj.full_clean()
obj.save()
obj.sources.set(...)
```

Membership は `save()` 自身も `full_clean()` を呼ぶが、
write service 側でも intent を明示して validation path を統一してよい。

### 5.3 Proposed decision token

Mother Ship approval candidate:

```text
BULK_WRITE_POLICY = PROHIBITED_FOR_COLLECTIVE_BACKFILL
```

### 5.4 Future exception

将来、件数が bulk write を必要とする規模になった場合は、
A-5 の安全条件を暗黙に外さず、専用の Bulk Integrity Gate を作る。

---

## 6. Validation / DB Constraint Boundary

### 6.1 Classification rule

Technical boundary candidate:

```text
Parser / Plan
  -> input structure / source key / natural-key conflict

Model validation
  -> existing Knowledge lifecycle validation
  -> cross-model semantic validation where DB CHECK cannot express it

DB constraint
  -> row-local structural invariant where practical
  -> uniqueness

Service / Write path
  -> ordering of writes
  -> Source relation completion
  -> idempotency / conflict policy
  -> transaction / expected delta
```

### 6.2 Current invariant matrix

| Invariant | Current layer | DB enforced? | A-5 requirement |
|---|---|---:|---|
| Membership unique `(collective,deity)` | DB UniqueConstraint | Yes | reuse |
| Membership same Shrine | `clean()/save()` | No | validated write path mandatory |
| Collective count relation requires count | `clean()` | No | validated write path mandatory |
| `unspecified => member_count NULL` | `clean()` | No | validated write path mandatory |
| verification status / verified_at | shared model helper | No | reuse existing contract |
| role / status enum | model field choices | No dedicated CHECK | reuse existing convention |
| Source identity conflict | importer plan | N/A | reuse existing authority |
| Source attached to Collective | service/M2M | N/A | verify before transaction commit |
| Source attached to Membership | service/M2M | N/A | verify independently |
| Membership Evidence B independence | model relation + service | N/A | never inherit automatically |

### 6.3 Same-Shrine invariant

```text
collective.shrine_id == deity.shrine_id
```

これは2つの別テーブルを跨ぐため、通常の `CheckConstraint` では表現しない。

Technical recommendation:

- Membership `save()->full_clean()` を維持
- A-5 importer は Membership を通常 `save()` で作る
- bulk / raw update を禁止
- cross-Shrine を plan stage でも先に検出して STOP
- DB trigger / shrine_id denormalization は A-4 の範囲では導入しない

### 6.4 Collective member count invariant

以下は single-row 条件である。

```text
exact / minimum / approximate -> member_count IS NOT NULL
unspecified                    -> member_count IS NULL
```

現在は `clean()` のみ。

Repository の Canonical Anchor precedent に従うなら、
これは DB `CheckConstraint` へ移せる条件である。

Technical recommendation:

```text
COUNT_RELATION_DB_CONSTRAINT = ADD_BEFORE_BACKFILL
```

候補 constraint semantics:

```text
(
  member_count_relation IN (exact, minimum, approximate)
  AND member_count IS NOT NULL
)
OR
(
  member_count_relation = unspecified
  AND member_count IS NULL
)
```

A-1 / A-2 で承認されていないため、次は追加しない。

- `member_count >= 2`
- `member_count > 0`
- Membership row countとの一致
- `complete` と Membership count の自動一致

DB constraint hardening を採用する場合は、
A-5 data backfill と同じPRへ混ぜず、先行する小さいschema hardening PRへ分離する。

### 6.5 verification_status / verified_at

これは既存 `ShrineKnowledgeSource` / `ShrineDeity` /
`ShrineHistory` と共有される Knowledge lifecycle contract である。

Collectiveだけに新しい DB CheckConstraint を追加すると、
shared Evidence contract に非対称な永続化ルールが生じる。

Technical recommendation:

- A-4ではDB constraintを新設しない
- existing `_validate_verified_at_consistency()` を再利用
- parser + `full_clean()` で fail closed
- shared Knowledge lifecycle 全体のDB hardeningは別track

### 6.6 Proposed boundary token

Mother Ship approval candidate:

```text
INTEGRITY_BOUNDARY = DB_ROW_LOCAL_MODEL_SERVICE_CROSS_ROW
```

補助 decision:

```text
COUNT_RELATION_DB_CONSTRAINT = ADD_BEFORE_BACKFILL
```

---

## 7. A-5 Write Sequence Candidate

Mother Ship が上記 technical recommendation を承認した場合の
A-5 canonical write sequence:

```text
1. parse seed
2. validate all structural fields
3. resolve Shrine identity
4. resolve/reuse Source identity
5. resolve Collective identity
6. resolve Membership deity identity
7. compute CREATE / SKIP / CONFLICT plan
8. if any error or conflict -> STOP, zero writes
9. if --dry-run -> print plan, zero writes, STOP
10. transaction.atomic()
11. create/reuse Sources
12. create Collective
    -> full_clean()
    -> save()
13. attach Collective.sources
14. create Membership one-by-one
    -> full_clean()/save()
15. attach each Membership.sources independently
16. verify expected object/relation counts inside transaction
17. commit
18. second --dry-run
    -> CREATE = 0
    -> CONFLICT = 0
```

No step may derive Membership Source from Collective Source automatically.

---

## 8. Natural Key / Idempotency Direction

A-5 needs deterministic matching before any write.

### 8.1 Collective candidate identity

Technical candidate:

```text
Shrine + source_attested_label
```

Reason:

- `source_attested_label` is source-backed wording defined by A-1
- numeric PK must not appear in seed
- Shrine identity already has current resolver
- role/count/status changes must not silently create duplicate Collectives

However current DB schema has no UniqueConstraint on this pair.

Therefore A-5 should treat an existing same candidate identity as:

```text
all expected structural fields / source relations match
-> SKIP_EXISTS

meaningful field or Source relation differs
-> COLLECTIVE_CONFLICT
-> STOP
```

This identity is a technical candidate, not finalized by A-4 without Mother Ship approval.

### 8.2 Membership identity

DB authority already exists:

```text
Unique(collective, deity)
```

A-5 plan behavior:

```text
not found
-> CREATE

found + expected Membership metadata / sources match
-> SKIP_EXISTS

found + meaningful mismatch
-> MEMBERSHIP_CONFLICT
-> STOP
```

### 8.3 No silent update

Named Collective Migration = C is additive staged migration.

Therefore initial Source-backed backfill must not use:

```text
update_or_create
silent overwrite
note-derived repair
automatic role/count rewrite
```

Existing mismatch means review, not mutation.

---

## 9. Source-backed Rules

A-5 must preserve Membership Evidence = B.

### Collective

A Collective marked usable by Evidence Gate must have its own accepted Source relation.

### Membership

A Membership marked usable by Evidence Gate must have its own accepted Source relation.

### Shared Source row

The same `ShrineKnowledgeSource` row may be referenced by both.

### Prohibited

```text
membership.source_keys omitted
-> automatically inherit collective.source_keys
```

は禁止。

If Source only proves Collective existence and not member relation:

```text
Collective Fact may exist
Membership must not be created as confirmed relation
```

---

## 10. Dry-run Contract

A-5 must retain the existing 3-mode Knowledge importer shape.

```text
--validate-only
--dry-run
apply
```

### validate-only

Must validate at minimum:

- schema version
- required fields
- enum values
- source key existence
- Shrine identity resolvable
- Collective structural rules
- referenced Deity identity resolvable within same Shrine
- no inferred unknown members

DB writes: **0**

### dry-run

Must additionally resolve current DB state and report:

```text
source_CREATE / REUSE_EXISTING / CONFLICT
collective_CREATE / SKIP_EXISTS / CONFLICT
membership_CREATE / SKIP_EXISTS / CONFLICT
```

DB writes: **0**

### apply

Allowed only if the same plan has zero errors/conflicts.

---

## 11. Transaction / Rollback Contract

Apply mode must use one `transaction.atomic()` boundary for the entire
Collective backfill seed.

The transaction includes:

```text
new Source rows
Collective rows
Collective-Source M2M
Membership rows
Membership-Source M2M
post-write expected-delta verification
```

Any error before commit must rollback all changes from that seed.

Partial success is not an accepted state.

---

## 12. Production Gate

A-4 does not authorize Production write.

Existing Unified Gate G7 remains authority.

Production execution requires at minimum:

- A-4 decisions approved
- required schema hardening merged
- A-5 Data PR merged
- isolated / production-equivalent preflight PASS
- expected delta frozen
- dry-run on target DB produces expected plan
- Mother Ship explicit Production write approval
- credentials remain outside repo/chat/AI

Unexpected delta:

```text
STOP
DO NOT improvise repair write
RETURN observed delta to Mother Ship
```

---

## 13. Runtime Boundary

A-5 backfill does not activate Runtime.

Even after data exists:

```text
ShrineDetailSerializer
shrine_knowledge_selector
Shared Recommendation Eligibility
Concierge
Compass
Recommendation Reason
Deep Dive
Evidence Transport
Web
Mobile
```

remain unchanged until A-6 Runtime Activation Gate.

```text
DB presence != Runtime eligibility
Runtime eligibility != Model Risk release
```

---

## 14. Model Risk Boundary

A successful Source-backed backfill does not automatically RELEASE
`wave0-014` or any other Model Risk candidate.

Required sequence remains:

```text
Model capability
-> Source-backed data
-> Evidence validation
-> Runtime activation where required
-> owning Gate re-evaluation
-> explicit release decision
```

No automatic lifecycle promotion.

---

## 15. STOP Conditions

A-5 must not write if any of the following occurs.

```text
Shrine identity NOT_FOUND
Shrine identity AMBIGUOUS
Source identity CONFLICT
Source identity AMBIGUOUS
Collective identity ambiguous
Collective existing-row mismatch
Membership deity not found
Membership deity belongs to another Shrine
Membership existing-row mismatch
unknown member would need to be synthesized
member_count contract invalid
verification/verified_at invalid
Source key unresolved
dry-run delta differs from expected
Production delta differs from frozen preflight
```

STOP means no ad-hoc repair write.

---

## 16. Technical Recommendation Summary

Repository audit leads to the following technical recommendation set.

```text
WRITE_PATH_AUTHORITY =
  EXTEND_EXISTING_KNOWLEDGE_IMPORTER

BULK_WRITE_POLICY =
  PROHIBITED_FOR_COLLECTIVE_BACKFILL

INTEGRITY_BOUNDARY =
  DB_ROW_LOCAL_MODEL_SERVICE_CROSS_ROW

COUNT_RELATION_DB_CONSTRAINT =
  ADD_BEFORE_BACKFILL
```

These are not silently converted into Mother Ship decisions by this audit.

---

## 17. Mother Ship Decision Gate

A-4 closes only after Mother Ship explicitly accepts or replaces the values below.

```text
Decision 1:
WRITE_PATH_AUTHORITY =
  EXTEND_EXISTING_KNOWLEDGE_IMPORTER
  / NEW_DEDICATED_IMPORTER
  / OTHER

Decision 2:
BULK_WRITE_POLICY =
  PROHIBITED_FOR_COLLECTIVE_BACKFILL
  / CONDITIONALLY_ALLOWED
  / ALLOWED

Decision 3:
INTEGRITY_BOUNDARY =
  DB_ROW_LOCAL_MODEL_SERVICE_CROSS_ROW
  / MODEL_SERVICE_ONLY
  / OTHER

Decision 3a:
COUNT_RELATION_DB_CONSTRAINT =
  ADD_BEFORE_BACKFILL
  / KEEP_MODEL_VALIDATION_ONLY
```

No option may be inferred from document order.

---

## 18. Post-Decision Implementation Order

If Mother Ship approves the technical recommendation set:

```text
A-4a  this Gate document merged
  |
  v
A-4b  member_count relation DB CheckConstraint hardening
      - Standard + NoGIS migrations
      - no data backfill
      - no Runtime change
  |
  v
A-5   Source-backed Collective backfill implementation
      - extend existing importer
      - seed/parser/plan/apply/tests
      - isolated backfill
      - still no Runtime activation
  |
  v
A-6   Runtime Activation Gate
```

If `COUNT_RELATION_DB_CONSTRAINT = KEEP_MODEL_VALIDATION_ONLY`,
A-4b is skipped, but A-5 must still call `full_clean()` before every
Collective save and bulk paths remain governed by Decision 2.

---

## 19. A-4 Completion Checklist

```markdown
- [x] current develop reviewed
- [x] Collective model write bypass reviewed
- [x] Membership same-Shrine bypass reviewed
- [x] current Knowledge importer reviewed
- [x] Source identity reuse reviewed
- [x] atomicity / dry-run / idempotency precedent reviewed
- [x] Canonical Anchor single-row vs cross-row precedent reviewed
- [x] Write path options compared
- [x] bulk policy options compared
- [x] validation / DB constraint boundary documented
- [x] Production / Runtime / Model Risk boundaries documented
- [ ] Mother Ship: WRITE_PATH_AUTHORITY selected
- [ ] Mother Ship: BULK_WRITE_POLICY selected
- [ ] Mother Ship: INTEGRITY_BOUNDARY selected
- [ ] Mother Ship: COUNT_RELATION_DB_CONSTRAINT selected
- [ ] A-4 Gate CLOSED
```

---

## 20. Non-goals

A-4 does not:

- add Collective data
- add Membership data
- change existing Collective / Membership rows
- add Runtime exposure
- modify Recommendation eligibility
- modify ranking
- modify Compass
- modify Concierge
- modify Deep Dive
- modify Web / Mobile
- release Model Risk HOLD
- change Candidate Master
- perform Production write
- infer religious / historical facts
