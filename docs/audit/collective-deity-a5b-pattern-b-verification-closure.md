# A-5b Pattern B Isolated Verification Closure

- Status: **CLOSED / PASS**
- Date: 2026-09-27
- Scope: A-5b source-backed collective-deity backfill, Pattern B initial backfill set
- Seed: `backend/temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json`
- Verification environment: isolated local PostgreSQL scratch database `jinja_a5b_scratch`
- Production DB: **not touched**

## 1. Closure purpose

This record closes the isolated verification of the A-5b Pattern B Knowledge Seed 1.1 backfill. The verification proves that the frozen Pattern B input can be reconstructed from repository-canonical prerequisites, planned without unexpected writes, applied to an isolated database, checked against the persisted database state, and re-run idempotently.

This closure does not change the frozen A-5b candidate universe or infer additional candidates.

## 2. Frozen Pattern B scope

The verified backfill contains six source-backed collectives:

1. 箱根神社 — 箱根大神
2. 寒川神社 — 寒川大明神
3. 二荒山神社 — 二荒山大神
4. 住吉神社（博多） — 住吉五所大神
5. 安房神社 — 忌部五部神
6. 王子神社 — 王子大神

Expected relationship cardinality:

- canonical existing Sources: 6
- existing ShrineDeity prerequisites: 23
- new ShrineDeityCollective rows: 6
- new ShrineDeityCollectiveMembership rows: 23

## 3. Scratch database reconstruction

A fresh isolated PostgreSQL database was created and migrated through the repository migration head available for this verification:

- `temples.0118_shrine_deity_collective_count_relation_constraint`

`bootstrap_production_data` then established the Base Shrine state:

- Shrine total: 117

Immediately after base bootstrap, the A-5b Knowledge prerequisites were intentionally absent:

```text
SOURCE_EXPECTED 6
SOURCE_FOUND 0
DEITY_EXPECTED 23
DEITY_FOUND 0
```

This established that Base Shrine bootstrap alone does not reconstruct the Knowledge prerequisite state required by A-5b.

## 4. Canonical prerequisite reconstruction

Repository tracing resolved all required Source and ShrineDeity origins.

The minimal prerequisite Seed set, preserving canonical historical Knowledge Batch order, was frozen as:

```text
batch_1_7_seed.json
batch_9_seed.json
batch_10_seed.json
batch_12_seed.json
batch_14_seed.json
```

All five prerequisite Seeds passed `--validate-only` and isolated `--dry-run` before application.

After applying those prerequisite Seeds, the required A-5b pre-state was measured directly from the scratch database:

```text
SOURCE_EXPECTED 6
SOURCE_FOUND 6
DEITY_EXPECTED 23
DEITY_FOUND 23
```

Result:

```text
A5B_PREREQUISITE_GATE = PASS
```

## 5. Initial A-5b isolated dry-run

Command under verification:

```text
python manage.py import_shrine_knowledge temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json --dry-run
```

Observed plan summary:

```text
source_REUSE_EXISTING = 6
collective_CREATE = 6
membership_CREATE = 23
```

No Source creation was planned. All six Seed Source identities resolved to existing canonical Source rows.

The dry-run completed with no database writes.

Result:

```text
A5B_ISOLATED_DRY_RUN_GATE = PASS
```

## 6. Initial A-5b isolated apply

The same Seed was then applied to the same isolated scratch database.

Observed plan summary:

```text
source_REUSE_EXISTING = 6
collective_CREATE = 6
membership_CREATE = 23
```

Observed import completion:

```text
sources created=0
deities created=0
histories created=0
collectives created=6
memberships created=23
```

The apply therefore added only the intended Collective and Membership rows. Existing Source and ShrineDeity rows were reused rather than recreated.

Result:

```text
A5B_ISOLATED_APPLY_GATE = PASS
```

## 7. Post-import integrity Gate

The persisted database state was checked directly against the identities defined by the A-5b Seed.

Observed result:

```text
COLLECTIVE_EXPECTED 6
COLLECTIVE_FOUND 6
COLLECTIVE_DUPLICATE 0
MEMBERSHIP_EXPECTED 23
MEMBERSHIP_FOUND 23
MEMBERSHIP_DUPLICATE 0
SAME_SHRINE_VIOLATION 0
```

This proves for the verified isolated state that:

- all six expected Collective identities exist exactly once;
- all 23 expected Membership identities exist exactly once;
- no duplicate expected Collective identity was produced;
- no duplicate expected Membership identity was produced;
- every checked Membership references a ShrineDeity belonging to the same Shrine as its Collective.

Result:

```text
A5B_POST_IMPORT_INTEGRITY_GATE = PASS
```

## 8. Second-run idempotency Gate

After the successful apply, the same A-5b Seed was executed again with `--dry-run` against the unchanged scratch database.

Observed plan summary:

```text
source_REUSE_EXISTING = 6
collective_SKIP_EXISTS = 6
membership_SKIP_EXISTS = 23
```

Observed creation counts for the second-run plan:

```text
source_CREATE = 0
collective_CREATE = 0
membership_CREATE = 0
```

The second run completed with no database writes.

Result:

```text
A5B_SECOND_RUN_IDEMPOTENCY_GATE = PASS
```

## 9. Final closure

All isolated verification Gates required for this Pattern B backfill passed:

```text
A5B_PREREQUISITE_GATE = PASS
A5B_ISOLATED_DRY_RUN_GATE = PASS
A5B_ISOLATED_APPLY_GATE = PASS
A5B_POST_IMPORT_INTEGRITY_GATE = PASS
A5B_SECOND_RUN_IDEMPOTENCY_GATE = PASS
```

Final status:

```text
A5B_PATTERN_B_ISOLATED_VERIFICATION = PASS
A5B_PATTERN_B_VERIFICATION_CLOSURE = CLOSED
```

The verified behavior is limited to the frozen Pattern B Seed and the isolated repository-derived prerequisite state described above. This record does not authorize inference of additional collective candidates, modification of the frozen candidate universe, or production application by itself.

## 10. Next Gate

The isolated verification phase is closed. Any subsequent production/backfill execution must be handled as a separate Gate using the repository's applicable production data-change contract and must not reinterpret this isolated verification as evidence that production state is identical to the scratch state.
