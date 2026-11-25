# Production temples 0121 Migration Gate

## 0. Current status（migration completed）

```text
target migration              = temples 0121_shrine_fact_source_citation
production latest temples     = 0121_shrine_fact_source_citation
0121 applied                  = YES
citation table exists         = YES（temples_shrinefactsourcecitation）
citation row count            = 0
Production PostgreSQL         = 17.6 / server_version_num 170006

FRESH_PRODUCTION_BACKUP       = COMPLETED
ISOLATED_RESTORE              = COMPLETED
RESTORE_FINGERPRINT           = MATCHED

PRODUCTION_MIGRATION_AUTHORIZED = YES（Mother Ship, explicit; temples 0121 ONLY）
MIGRATION_EXECUTION           = PASS
showmigrations temples        = [X] 0121_shrine_fact_source_citation
manage.py check               = PASS
migrate temples 0121 --plan   = No planned migration operations

TEMPLES_0121_MIGRATION_GATE   = CLOSED / PASS
```

Scope of the authorization:

```text
authorized       = temples 0121_shrine_fact_source_citation migration only
not authorized   = nsrc-000009 Base import / Knowledge import / any other Production write
nsrc-000009 G7   = PRODUCTION_WRITE_AUTHORIZED = NO（see
                   docs/audit/niigata-h002-nsrc-000009-g7-production-import-preflight.md）
```

0121 PASS does not imply nsrc-000009 G7 PASS（§13）.

Chronology:

1. PR #3238 created this gate in HOLD（§1–§14, kept as written as the pre-execution record）.
2. Mother Ship took a fresh Production backup, completed the isolated restore, and matched the restore
   fingerprint（§8 / §9）.
3. Mother Ship explicitly authorized the temples 0121 Production migration and executed it.
4. Post-migration verification passed（§15）. The records in §0 / §15 are Mother Ship's observations;
   this repository change made no Production connection or write.

## 1. Status at PR #3238（pre-execution; historical record）

```text
target migration              = temples 0121_shrine_fact_source_citation
production latest temples     = 0120_shrine_source_fact_foundation
0121 applied                  = NO
citation table exists         = NO

MIGRATION_FILE_REVIEW         = PASS
PRODUCTION_PRESTATE           = PASS / EXPECTED_0120
BACKUP_TOOLING_READY          = YES
ISOLATED_RESTORE_ROUTE        = YES

FRESH_0120_BACKUP_TAKEN       = NO
ISOLATED_RESTORE_EXECUTED     = NO
RESTORE_FINGERPRINT_MATCHED   = NO

PRODUCTION_MIGRATION_READY    = HOLD
PRODUCTION_WRITE_AUTHORIZED   = NO
PRODUCTION_WRITE              = NONE
```

- Recorded at: 2026-10-16
- Base: latest `develop`
- Branch: `audit/production-temples-0121-migration-gate`

This document is the dedicated Production Migration Gate for `temples 0121`.
It is intentionally separate from the nsrc-000009 G7 Production Import Gate.

The migration is not executed by this PR.

## 2. Why this gate exists

The nsrc-000009 Production read-only preflight stopped as designed because:

```text
relation "temples_shrinefactsourcecitation" does not exist
```

Production was then measured read-only:

```text
latest temples migration
= 0120_shrine_source_fact_foundation

0121_shrine_fact_source_citation applied
= false

temples_shrinefactsourcecitation exists
= false
```

Therefore nsrc-000009 G7 cannot continue until the schema prerequisite exists.

## 3. Target migration re-read

Authority:

`backend/temples/migrations/0121_shrine_fact_source_citation.py`

Dependency:

```text
temples 0120_shrine_source_fact_foundation
```

Operations:

```text
CreateModel ShrineFactSourceCitation x1
```

No:

- RunPython
- RunSQL
- AlterField
- RemoveField
- DeleteModel
- existing row backfill
- existing Knowledge Source rewrite

The model adds:

- `source` FK -> ShrineKnowledgeSource
- nullable `shrine_history` FK
- nullable `shrine_deity` FK
- `locator_text`
- `created_at`
- exactly-one-Fact check constraint
- nonblank locator check constraint
- conditional History citation uniqueness
- conditional Deity citation uniqueness

The migration is additive at schema level.

## 4. Expected Production delta from migration only

Expected migration-only delta:

```text
new table:
  temples_shrinefactsourcecitation

new existing application rows:
  0

Shrine count:
  unchanged

ShrineKnowledgeSource count:
  unchanged

ShrineHistory count:
  unchanged

ShrineDeity count:
  unchanged
```

The migration must not materialize nsrc-000009 citation rows.
Those belong to the later scoped Knowledge import.

## 5. Production pre-state

Read-only Production measurement already established:

```text
PostgreSQL major         = 17
latest temples migration = 0120_shrine_source_fact_foundation
0121 applied             = NO
citation table           = absent
```

This matches the migration's declared dependency.

No claim is made that the full historical migration lineage is simple.
The gate relies on the measured current Production schema plus the exact 0121 operation.

## 6. Migration safety classification

The migration is structurally low-risk because it is a single new table with FKs to existing Knowledge tables.

However:

```text
ADDITIVE_SCHEMA_CHANGE
!=
PRODUCTION_MIGRATION_READY
```

A fresh recoverable backup is still required immediately before Production migration.

Current classification:

```text
MIGRATION_STRUCTURE = ADDITIVE / NO_DATA_BACKFILL
MIGRATION_READY     = HOLD / FRESH_BACKUP_NOT_YET_VERIFIED
```

## 7. Backup tooling readiness

Repository tooling exists and was previously exercised for Production migrations:

- `scripts/migration_safety/check_credential_presence.sh`
- `scripts/migration_safety/readonly_query.sh`
- `scripts/migration_safety/dump_readonly.sh`
- `scripts/migration_safety/restore_isolated.sh`
- `scripts/migration_safety/guard.py`

Safety properties:

- credential file must remain outside repository
- mode must be 600
- credential value must never be printed or committed
- dump output must remain outside repository
- restore destination must be localhost
- restore database name must satisfy disposable allow-list
- Production read-only SQL is allow-listed before connection

Therefore:

```text
BACKUP_TOOLING_READY = YES
```

## 8. Fresh backup / restore requirement

A prior verified Production backup does not automatically authorize this migration.

Before 0121:

1. Re-measure Production immediately before backup.
2. Confirm latest `temples` migration is still 0120.
3. Confirm citation table is still absent.
4. Take a fresh Production backup using PostgreSQL 17-compatible client tooling.
5. Store backup outside the repository.
6. Confirm roles / schema / data artifacts are non-empty as applicable.
7. Restore to an isolated localhost database accepted by `restore_isolated.sh`.
8. Re-run the 0121 pre-state checks on the restored DB.
9. Confirm the restored fingerprint matches the live read-only Production pre-state.
10. Only then can Mother Ship consider migration execution approval.

Current state:

```text
FRESH_0120_BACKUP_TAKEN     = NO
ISOLATED_RESTORE_EXECUTED   = NO
RESTORE_FINGERPRINT_MATCHED = NO
```

Therefore:

```text
BACKUP_RESTORE_READINESS = PROCEDURE_READY / EXECUTION_PENDING
PRODUCTION_MIGRATION_READY = HOLD
```

## 9. Required restore fingerprint

At minimum the restored copy must match Production for:

```text
latest temples migration = 0120_shrine_source_fact_foundation
0121 migration row       = absent
citation table           = absent
```

Also compare the Production aggregates already used by the active migration-safety runbook for existing application data.

The restored copy must not be mutated to make the fingerprint match.

## 10. Execution boundary

No Production migration command is authorized by this document.

If later authorized, execution must be app-scoped and target-scoped:

```text
python manage.py migrate temples 0121 --noinput
```

Do not use bare:

```text
python manage.py migrate
```

because unrelated pending migrations across apps could be applied.

The exact environment/runtime invocation must use the existing Production migration runbook and must not expose credentials.

## 11. Post-migration verification requirements

Immediately after 0121, before returning to nsrc-000009 G7:

```text
latest temples migration = 0121_shrine_fact_source_citation
citation table exists     = true
citation row count        = 0
```

Verify the table has the expected:

- FKs
- check constraints
- conditional unique constraints

Existing aggregate counts for Shrine / Source / History / Deity must remain unchanged.

No nsrc-000009 Knowledge import is allowed inside the migration step.

## 12. Failure routing

If fresh Production pre-state differs from the state recorded above:

```text
STOP / PRODUCTION_STATE_CHANGED
```

If backup fails:

```text
STOP / BACKUP_FAILED
```

If isolated restore fails:

```text
STOP / RESTORE_FAILED
```

If restore fingerprint differs from Production:

```text
STOP / RESTORE_FINGERPRINT_MISMATCH
```

If migration applies unexpected DDL or data change:

```text
STOP / MIGRATION_POSTCHECK_FAILED
```

Do not compensate with ad-hoc writes.

## 13. Relationship to nsrc-000009 G7

Current routing:

```text
nsrc-000009 G7
  -> HOLD / PRODUCTION_SCHEMA_PREREQUISITE_MISSING

temples 0121 migration gate
  -> fresh backup / isolated restore
  -> Mother Ship explicit migration approval
  -> 0121 apply
  -> post-migration verification

then
  -> nsrc-000009 Production read-only preflight rerun
```

0121 PASS does not imply nsrc-000009 G7 PASS.

## 14. Final state

```text
TEMPLES_0121_MIGRATION_GATE_CREATED = YES
BACKUP_TOOLING_READY                = YES
ISOLATED_RESTORE_ROUTE              = YES

FRESH_BACKUP                        = NOT EXECUTED
ISOLATED_RESTORE                    = NOT EXECUTED
FINGERPRINT_MATCH                   = NOT EXECUTED

PRODUCTION_MIGRATION_READY          = HOLD
PRODUCTION_WRITE                    = NONE
```

## 15. Execution record（Mother Ship; after PR #3238）

Pre-execution（§8 / §9）:

```text
FRESH_PRODUCTION_BACKUP     = COMPLETED
ISOLATED_RESTORE            = COMPLETED
RESTORE_FINGERPRINT         = MATCHED
```

Authorization:

```text
PRODUCTION_MIGRATION_AUTHORIZED = YES（Mother Ship, explicit）
scope                           = temples 0121_shrine_fact_source_citation only
```

Post-migration verification（§11）:

```text
Production PostgreSQL       = 17.6 / 170006
latest temples migration    = 0121_shrine_fact_source_citation
showmigrations temples      = [X] 0121_shrine_fact_source_citation
citation table exists       = YES
citation row count          = 0
manage.py check             = PASS
migrate temples 0121 --plan = No planned migration operations

MIGRATION_EXECUTION         = PASS
```

Routing after closure:

```text
temples 0121 migration gate = CLOSED / PASS
nsrc-000009 G7              -> Production read-only preflight rerun（done; nsrc-000009 audit §18）
                            -> PRODUCTION_WRITE_AUTHORIZED = NO
```

No nsrc-000009 Knowledge or Base data was imported as part of this migration.
