# A-5b Production Reusable Execution Sequence

- Status: **RECORDED**
- Date: 2026-09-27
- Scope: A-5b Pattern B Production backfill execution order
- Parent closure: `docs/audit/collective-deity-a5b-production-backfill-closure.md`
- Execution Gate: `docs/audit/collective-deity-a5b-production-backfill-execution-gate.md`
- Post-import integrity evidence: `docs/audit/collective-deity-a5b-production-post-import-integrity.md`
- Idempotency evidence: `docs/audit/collective-deity-a5b-production-idempotency.md`
- Seed: `backend/temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json`

## 1. Purpose

This record converts the successfully observed A-5b Production execution into a reusable ordered sequence. It is a sequencing record, not blanket authorization to run future Production writes.

The sequence preserves the Gates that prevented schema drift, missing prerequisites, unplanned mutation, duplicate rows, and an unverified recovery path.

## 2. Reusable ordered sequence

The observed safe order is:

```text
1. Freeze repository revision and seed identity
2. Confirm Production connection and migration position
3. Audit physical-schema collisions
4. Review migration plan
5. Create a fresh read-only Production backup
6. Restore the backup into an isolated database and verify parity
7. Apply required schema migrations
8. Verify migration records, physical schema, and required constraint
9. Run seed validate-only
10. Verify all prerequisite Source and ShrineDeity rows
11. Run exact Production dry-run and freeze the planned mutation boundary
12. Execute the Production import
13. Run post-import row-level integrity Gate
14. Run rerun/idempotency dry-run Gate
15. Record evidence and classify closure
```

The order is intentional. A later step must not be used to excuse a failed earlier Gate.

## 3. Gate contract by phase

### Phase A — revision and schema readiness

Required evidence before any Production write:

```text
repository revision = known
seed identity = frozen
Production migration position = known
physical schema collision = 0
migration plan = reviewed
```

For the observed A-5b execution, the frozen seed SHA-256 was:

```text
ae413989731da35d3f9edf3298752262cb98478fa932c92fa25f8ab69fc504dd
```

### Phase B — recovery readiness

Before migration or seed mutation:

```text
fresh read-only backup = PASS
isolated restore = PASS
Production/restored aggregate parity = PASS
pre-migration planned-schema parity = PASS
recovery readiness = PASS
```

A successful dump command alone is not sufficient. The backup must be restored and checked in isolation.

### Phase C — schema migration

Apply only the reviewed migration target and then verify the resulting physical state.

Observed A-5b target:

```text
temples.0118_shrine_deity_collective_count_relation_constraint
```

Observed required sequence:

```text
0115_canonical_anchor_schema_foundation
0116_shrine_deity_collective_foundation
0117_shrine_deity_collective_membership_foundation
0118_shrine_deity_collective_count_relation_constraint
```

Post-migration Gate:

```text
migration records = 4 / 4
physical tables = 5 / 5
missing tables = 0
chk_deity_coll_count_rel = 1
GATE PASS
```

Physical table names must be derived from the actual migrations/models rather than guessed from Django class names.

### Phase D — seed preflight

Before the seed write:

```text
validate-only = PASS
Source prerequisites = 6 / 6
ShrineDeity prerequisites = 23 / 23
```

Then run the exact dry-run and inspect the plan.

Observed authorized A-5b mutation boundary:

```text
source_REUSE_EXISTING = 6
collective_CREATE = 6
membership_CREATE = 23
source CREATE = 0
deity CREATE = 0
history CREATE = 0
dry-run DB writes = 0
```

If the dry-run differs from the reviewed boundary, stop before import.

### Phase E — Production import

Execute the same frozen seed only after the preflight Gate passes.

Observed A-5b write result:

```text
sources created = 0
deities created = 0
histories created = 0
collectives created = 6
memberships created = 23
```

The actual result must remain within the dry-run mutation boundary.

### Phase F — post-import integrity

Importer success is not treated as integrity proof.

Required row-level checks for this A-5b shape:

```text
COLLECTIVE_EXPECTED = 6
COLLECTIVE_FOUND = 6
COLLECTIVE_DUPLICATE = 0
MEMBERSHIP_EXPECTED = 23
MEMBERSHIP_FOUND = 23
MEMBERSHIP_DUPLICATE = 0
SAME_SHRINE_VIOLATION = 0
GATE PASS
```

### Phase G — idempotency

Rerun the same frozen seed with `--dry-run` after successful import.

Expected A-5b rerun shape:

```text
source_REUSE_EXISTING = 6
collective_SKIP_EXISTS = 6
membership_SKIP_EXISTS = 23
CREATE = 0
dry-run DB writes = 0
GATE PASS
```

This verifies the observed seed/importer combination does not plan duplicate creation on the resulting Production state.

## 4. STOP conditions

The sequence must stop before the next mutating step if any applicable Gate fails, including:

```text
repository or seed identity is not frozen
unexpected Production migration position
physical schema collision detected
fresh backup cannot be restored and verified
migration plan differs from the reviewed sequence
post-migration schema or constraint is missing
validate-only fails
Source or ShrineDeity prerequisite is missing
Production dry-run contains an unexpected CREATE or other mutation
actual import exceeds the frozen mutation boundary
post-import duplicate or same-shrine violation is detected
idempotency dry-run plans duplicate creation
```

A later PASS does not retroactively convert an earlier failed Gate into a PASS.

## 5. Reuse boundary

This sequence is reusable as an operational pattern for a future controlled Production backfill only when its own concrete values are re-derived and re-verified.

The A-5b-specific counts, migration numbers, seed hash, source identities, deity identities, table names, and constraints are evidence from this execution. They must not be copied as assumptions into a different backfill.

The reusable invariant is the Gate order:

```text
freeze
→ inspect
→ backup
→ restore-verify
→ migrate
→ schema-verify
→ validate
→ prerequisite-verify
→ dry-run
→ import
→ integrity-verify
→ idempotency-verify
→ closure
```

## 6. Closure progression

```markdown
- [x] backup / restore evidence recorded
- [x] migration 0115-0118 evidence recorded
- [x] pre-import exact plan recorded
- [x] actual import result recorded
- [x] post-import integrity result recorded
- [x] idempotency result recorded
- [x] reusable execution sequence recorded
- [ ] final Production closure classification
```
