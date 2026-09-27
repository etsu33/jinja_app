# A-5b Production Backfill Closure

- Status: **IN PROGRESS — MIGRATION EVIDENCE RECORDED**
- Date: 2026-09-27
- Scope: A-5b Pattern B production backfill closure
- Upstream execution contract: `docs/audit/collective-deity-a5b-production-backfill-execution-gate.md`
- Seed: `backend/temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json`

## 1. Purpose

This document records measured evidence from the authorized A-5b Pattern B Production execution. It closes the gap between the pre-write execution contract and the state actually observed during backup, recovery verification, migration, import, integrity verification, and idempotency verification.

This closure does not expand the frozen candidate universe and does not authorize unrelated Production changes.

## 2. Backup / restore evidence

Before the Production schema migration and A-5b data write, a fresh read-only backup was created using the repository migration-safety tooling.

### 2.1 Production source and client compatibility

Measured before backup:

```text
PRODUCTION_POSTGRES_VERSION = 17.6
pg_dump default client = PostgreSQL 16.10
PostgreSQL 17 client available = 17.10
```

The PostgreSQL 17 client was selected for the Production dump:

```text
PG_DUMP_BIN=/opt/homebrew/opt/postgresql@17/bin/pg_dump
PG_DUMPALL_BIN=/opt/homebrew/opt/postgresql@17/bin/pg_dumpall
```

### 2.2 Fresh Production backup

Canonical repository script:

```text
scripts/migration_safety/dump_readonly.sh
```

Observed result:

```text
[dump_readonly] source connection configured
SAFE: ok
[dump_readonly] dumping roles (read-only)...
[dump_readonly] dumping schema (read-only, public schema only)...
[dump_readonly] dumping data (read-only, public schema only)...
[dump_readonly] roles.sql: 5426 bytes
[dump_readonly] schema.sql: 106945 bytes
[dump_readonly] data.sql: 11371428 bytes
[dump_readonly] done.
```

Local backup directory used for this execution:

```text
~/kami-musubi-backups/a5b-pre-migration-20260927-180323
```

The backup remained local and was not committed to the repository.

### 2.3 Isolated restore target

A dedicated local database was created for restore verification:

```text
jinja_a5b_migration_safety_restore_test_20260927
```

The local PostgreSQL server was:

```text
PostgreSQL 18.0 (Homebrew)
```

Restore used the canonical repository script:

```text
scripts/migration_safety/restore_isolated.sh
```

with PostgreSQL 18 `psql`:

```text
PSQL_BIN=/opt/homebrew/opt/postgresql@18/bin/psql
```

Observed restore phases all completed:

```text
[restore_isolated] target connection configured
[restore_isolated] applying roles.sql (best-effort; roles may already exist)...
[restore_isolated] ensuring required extensions exist (postgis, pg_trgm)...
[restore_isolated] applying schema.sql...
[restore_isolated] applying data.sql...
[restore_isolated] done.
```

### 2.4 Restored migration state

The restored database reproduced the Production migration position before the A-5b-required schema migration:

```text
[X] 0105_w0b02t02_remove_qa_artifact_id102
[X] 0106_weekly_presentation_snapshot_foundation
[X] 0107_restore_places_seed_schema
[X] 0108_remove_legacy_temples_models
[X] 0109_adopt_izumo_taisha_position
[X] 0110_adopt_fushimi_inari_position
[X] 0111_adopt_kasuga_taisha_position
[X] 0112_adopt_atsuta_jingu_position
[X] 0113_adopt_usa_jingu_position
[X] 0114_f6d_explicit_place_ref_backfill
[ ] 0115_canonical_anchor_schema_foundation
[ ] 0116_shrine_deity_collective_foundation
[ ] 0117_shrine_deity_collective_membership_foundation
[ ] 0118_shrine_deity_collective_count_relation_constraint
```

### 2.5 Production / restored aggregate parity

Read-only aggregate comparison before migration produced exact parity:

```text
                                  Production   Restored
temples_shrine                         117        117
temples_shrinedeity                    287        287
temples_shrineknowledgesource          131        131
django_migrations                      162        162
```

The planned new schema was absent from both states before migration:

```text
Production PLANNED_TABLES_FOUND = 0
Restored   PLANNED_TABLES_FOUND = 0
```

### 2.6 Recovery readiness classification

The fresh backup was therefore not treated as merely a successful dump command. It was restored into an isolated database and checked against the Production pre-migration aggregate and migration state.

```text
A5B_FRESH_BACKUP = PASS
A5B_ISOLATED_RESTORE = PASS
A5B_PRODUCTION_RESTORED_AGGREGATE_PARITY = PASS
A5B_PRE_MIGRATION_PLANNED_SCHEMA_PARITY = PASS
A5B_RECOVERY_READINESS = PASS
```

No backup artifact is stored in Git.

## 3. Production migration 0115-0118 evidence

### 3.1 Pre-migration Production position

Production was observed at `temples.0114_f6d_explicit_place_ref_backfill`, with the four required migrations unapplied:

```text
[X] 0114_f6d_explicit_place_ref_backfill
[ ] 0115_canonical_anchor_schema_foundation
[ ] 0116_shrine_deity_collective_foundation
[ ] 0117_shrine_deity_collective_membership_foundation
[ ] 0118_shrine_deity_collective_count_relation_constraint
```

A physical-schema collision audit was performed before migration. Seven expected relation names were checked and no pre-existing collision was found:

```text
EXPECTED_TABLES 7
COLLISION_FOUND 0
COLLISION_TABLES []
GATE PASS
```

### 3.2 Migration plan

The Production migration plan targeted `temples.0118_shrine_deity_collective_count_relation_constraint` and resolved exactly the required sequence:

```text
0115_canonical_anchor_schema_foundation
  Create ShrineCanonicalAnchor
  Create ShrineCanonicalAnchorComponent
  Create ShrineCanonicalAnchorEvidence
  Add canonical-anchor constraints

0116_shrine_deity_collective_foundation
  Create ShrineDeityCollective

0117_shrine_deity_collective_membership_foundation
  Create ShrineDeityCollectiveMembership

0118_shrine_deity_collective_count_relation_constraint
  Create constraint chk_deity_coll_count_rel
```

### 3.3 Production migration execution

The authorized Production migration was executed through Django migrations with target `temples 0118`.

Observed result:

```text
Applying temples.0115_canonical_anchor_schema_foundation... OK
Applying temples.0116_shrine_deity_collective_foundation... OK
Applying temples.0117_shrine_deity_collective_membership_foundation... OK
Applying temples.0118_shrine_deity_collective_count_relation_constraint... OK
```

No migration in this sequence reported an execution failure.

### 3.4 Migration record verification

The Production `django_migrations` state was checked after execution.

```text
MIGRATIONS_FOUND 4
MIGRATIONS [
  '0115_canonical_anchor_schema_foundation',
  '0116_shrine_deity_collective_foundation',
  '0117_shrine_deity_collective_membership_foundation',
  '0118_shrine_deity_collective_count_relation_constraint'
]
```

Therefore the expected migration records were present exactly `4 / 4`.

### 3.5 Physical schema verification

An initial post-migration check used incorrect canonical-anchor table-name assumptions and therefore reported only the two collective tables. That result was not accepted as the integrity result.

The physical-schema check was corrected to the actual database table names and rerun. The verified result was:

```text
TABLES_EXPECTED 5
TABLES_FOUND 5
TABLES [
  'temples_shrine_canonical_anchor',
  'temples_shrine_canonical_anchor_component',
  'temples_shrine_canonical_anchor_evidence',
  'temples_shrinedeitycollective',
  'temples_shrinedeitycollectivemembership'
]
MISSING_TABLES []
```

Thus the required post-migration physical schema was present `5 / 5`, with zero missing tables.

### 3.6 Count-relation constraint verification

The 0118 database constraint was queried independently after migration:

```text
COUNT_REL_CONSTRAINT_FOUND 1
CONSTRAINTS ['chk_deity_coll_count_rel']
```

The required constraint therefore existed exactly once.

### 3.7 Migration integrity classification

The accepted post-migration gate was:

```text
MIGRATION_RECORDS = 4 / 4
PHYSICAL_TABLES = 5 / 5
MISSING_TABLES = 0
chk_deity_coll_count_rel = 1
GATE PASS
```

Classification:

```text
A5B_PRODUCTION_MIGRATION_0115_0118_EXECUTION = PASS
A5B_PRODUCTION_POST_MIGRATION_INTEGRITY = PASS
```

## 4. Remaining closure evidence

- [x] Production execution evidence organized
- [x] backup / restore evidence recorded
- [x] migration 0115-0118 evidence recorded
- [ ] pre-import exact plan recorded
- [ ] actual import result recorded
- [ ] post-import integrity result recorded
- [ ] idempotency result recorded
- [ ] reusable execution sequence recorded
- [ ] final Production closure classification
