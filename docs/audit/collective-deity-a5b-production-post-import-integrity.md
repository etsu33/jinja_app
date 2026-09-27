# A-5b Production Post-import Integrity Evidence

- Status: **PASS**
- Date: 2026-09-27
- Scope: A-5b Pattern B Production backfill post-import integrity
- Parent closure: `docs/audit/collective-deity-a5b-production-backfill-closure.md`
- Seed: `backend/temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json`

## 1. Purpose

This record preserves the measured Production integrity result obtained immediately after the authorized A-5b Pattern B import. It is intentionally separate from importer success: creation counts alone do not establish uniqueness or shrine-local referential integrity.

## 2. Gate definition

The post-import verification reconstructed the expected collective and membership identities from the frozen A-5b seed and queried the resulting Production rows.

The Gate checked:

1. all six expected `ShrineDeityCollective` identities exist exactly once;
2. no expected collective identity is duplicated;
3. all 23 expected `ShrineDeityCollectiveMembership` identities exist exactly once;
4. no expected membership identity is duplicated;
5. every inspected membership references a deity belonging to the same shrine as its collective.

## 3. Measured Production result

Observed output:

```text
COLLECTIVE_EXPECTED 6
COLLECTIVE_FOUND 6
COLLECTIVE_DUPLICATE 0
MEMBERSHIP_EXPECTED 23
MEMBERSHIP_FOUND 23
MEMBERSHIP_DUPLICATE 0
SAME_SHRINE_VIOLATION 0
GATE PASS
```

## 4. Integrity interpretation

### Collective identity

```text
expected = 6
found exactly once = 6
duplicate identities = 0
```

All six frozen A-5b collective identities were present exactly once after import.

### Membership identity

```text
expected = 23
found exactly once = 23
duplicate identities = 0
```

All 23 frozen A-5b membership identities were present exactly once after import.

### Same-shrine invariant

The verification compared `collective.shrine_id` with `deity.shrine_id` for the relevant membership rows.

```text
SAME_SHRINE_VIOLATION = 0
```

No inspected A-5b membership crossed shrine boundaries.

## 5. Gate classification

```text
A5B_PRODUCTION_COLLECTIVE_INTEGRITY = 6 / 6 PASS
A5B_PRODUCTION_COLLECTIVE_DUPLICATE = 0 PASS
A5B_PRODUCTION_MEMBERSHIP_INTEGRITY = 23 / 23 PASS
A5B_PRODUCTION_MEMBERSHIP_DUPLICATE = 0 PASS
A5B_PRODUCTION_SAME_SHRINE_VIOLATION = 0 PASS
A5B_PRODUCTION_POST_IMPORT_INTEGRITY = PASS
```

This Gate establishes the measured post-import row-level integrity for the frozen A-5b candidate set. It does not substitute for the independent rerun/idempotency Gate.

## 6. Closure progression

```markdown
- [x] backup / restore evidence recorded
- [x] migration 0115-0118 evidence recorded
- [x] pre-import exact plan recorded
- [x] actual import result recorded
- [x] post-import integrity result recorded
- [ ] idempotency result recorded
- [ ] reusable execution sequence recorded
- [ ] final Production closure classification
```
