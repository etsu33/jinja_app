# NIIGATA-001-VPG001 — G7 Backup / Restore Readiness

## 1. Final classification

```text
EXECUTION_MODE                 = VPG001_4_CANDIDATE_BATCH
BASELINE_MODE                  = SINGLE_FROZEN_PRESTATE + CUMULATIVE_STAGE_CHECKPOINTS

PRODUCTION_PREFLIGHT_RECHECK   = PASS
BACKUP_CLIENT_COMPATIBILITY    = PASS
FRESH_PRODUCTION_BACKUP        = PASS
ISOLATED_RESTORE               = PASS
RESTORE_FINGERPRINT            = MATCHED
RESTORE_P0_GUARD               = PASS

BACKUP_RESTORE_READINESS       = PASS

PRODUCTION_WRITE_AUTHORIZED    = NO
PRODUCTION_WRITE               = NONE
FORMAL_G7                      = NOT_EXECUTED
G8                             = NOT_EXECUTED
```

Recorded at: 2026-10-20

Base:
`develop@50be6845b4e72e057ea0bb74c63352fe51f960dc` (#3280 merged)

This audit records Mother Ship execution evidence only. This repository change does not perform a
Production connection, backup, restore, import, or write.

## 2. Authorities

- `docs/audit/niigata-vpg001-g7-production-freeze.md`
- `scripts/migration_safety/dump_readonly.sh`
- `scripts/migration_safety/restore_isolated.sh`
- `scripts/migration_safety/readonly_query.sh`
- `scripts/migration_safety/sql/niigata_vpg001_g7_frozen_pre_base_guard.sql`
- candidate-specific G7 preflight SQL for nsrc-000021 / 000022 / 000024 / 000025

The frozen Production P0 remains:

```text
Shrine      = 129
Source      = 145
Deity       = 295
History     = 236
Citation    = 2
SourceFact  = 34
Collective  = 6
```

## 3. Client compatibility

Mother Ship local client:

```text
pg_dump     = 17.10
pg_dumpall  = 17.10
pg_restore  = 17.10
psql        = 17.10
```

Production read-only preflight reported:

```text
PostgreSQL server_version     = 17.6
server_version_num            = 170006
latest temples migration      = 0121_shrine_fact_source_citation
```

Therefore:

```text
BACKUP_CLIENT_COMPATIBILITY = PASS
```

## 4. Production read-only recheck

Immediately before the fresh backup, Mother Ship re-ran the four committed candidate-specific
G7 preflight SQL files through `readonly_query.sh`.

All four runs were read-only and completed successfully.

Observed aggregate state:

```text
Shrine      = 129
Source      = 145
Deity       = 295
History     = 236
Citation    = 2
SourceFact  = 34
Collective  = 6
```

Observed candidate state:

```text
nsrc-000021 = CLEAN_CREATE
nsrc-000022 = CLEAN_CREATE
nsrc-000024 = CLEAN_CREATE
nsrc-000025 = CLEAN_CREATE
```

For each candidate:

```text
target_exact_count               = 0
same_name_other_address_count    = 0
same_address_count               = 0
source_identity_count            = 0
source_metadata_compatible_count = 0
target_deity_count               = 0
target_history_count             = 0
target_fact_source_relation_count= 0
target_citation_count            = 0
```

No P0 drift was observed.

```text
PRODUCTION_PREFLIGHT_RECHECK = PASS
```

## 5. Fresh Production backup

Mother Ship executed the existing guarded `dump_readonly.sh` route.

Backup timestamp:

```text
20261020140453
```

Backup location:

```text
operator home directory outside the repository
~/kami-musubi-backups/20261020140453
```

Artifacts:

| artifact | bytes | SHA256 |
|---|---:|---|
| roles.sql | 5,792 | c5472b47fb7b3bf9f7eaf98c97b7a2a523e05706ee922ac6db47eace35622d31 |
| schema.sql | 138,501 | c126b7bd48691d560c826ccf8531d0c4a2d2225b04fa4e61eea8e9ebf84ddaa0 |
| data.sql | 11,768,055 | 9f56a97ea8c01640c1d8eeb9a693c908e8c0f8c0896d72f68651f8908cd48aa7 |

All three files were non-empty. The dump remained outside the repository and was not committed.

```text
FRESH_PRODUCTION_BACKUP = PASS
```

## 6. Isolated restore

Mother Ship created a disposable local database whose name satisfied the existing
`restore_test` allow-list and restored the backup using `restore_isolated.sh`.

The restore completed through roles, required extension setup, schema restore, and data restore.

```text
ISOLATED_RESTORE = PASS
```

The restore destination was local and disposable only. It was not Production and no Production
application data write occurred.

The restore server was local PostgreSQL 18.0. The restore server version is not treated as the
Production server version. Fingerprint validation is based on the restored schema/data state and
the committed G7 guards.

## 7. Restore fingerprint

Restored migration ledger:

```text
latest temples migration = 0121_shrine_fact_source_citation
```

All four candidate-specific preflight SQL files were run against the restored database.

Restored aggregate state:

```text
Shrine      = 129
Source      = 145
Deity       = 295
History     = 236
Citation    = 2
SourceFact  = 34
Collective  = 6
```

Restored candidate state:

```text
nsrc-000021 = CLEAN_CREATE
nsrc-000022 = CLEAN_CREATE
nsrc-000024 = CLEAN_CREATE
nsrc-000025 = CLEAN_CREATE
```

For all four candidates, target identity, same-name/same-address, Source identity, Knowledge Fact,
relation, Citation, Collective and goriyaku-related preconditions remained at the frozen P0 state.

The restored fingerprint therefore matched the Production read-only P0 measurement.

```text
RESTORE_FINGERPRINT = MATCHED
```

## 8. Frozen P0 guard on restored database

Mother Ship executed the committed file unchanged:

`scripts/migration_safety/sql/niigata_vpg001_g7_frozen_pre_base_guard.sql`

Observed results:

```text
niigata_vpg001_g7_p0_cohort_checkpoint_pass = 1
niigata_vpg001_g7_p0_nsrc_000021_pass        = 1
niigata_vpg001_g7_p0_nsrc_000022_pass        = 1
niigata_vpg001_g7_p0_nsrc_000024_pass        = 1
niigata_vpg001_g7_p0_nsrc_000025_pass        = 1
```

No frozen value was patched or substituted.

```text
RESTORE_P0_GUARD = PASS
```

## 9. Mother Ship readiness decision

The complete backup / restore gate is now satisfied:

```text
PRODUCTION_PREFLIGHT_RECHECK = PASS
BACKUP_CLIENT_COMPATIBILITY  = PASS
FRESH_PRODUCTION_BACKUP      = PASS
ISOLATED_RESTORE             = PASS
RESTORE_FINGERPRINT          = MATCHED
RESTORE_P0_GUARD             = PASS

BACKUP_RESTORE_READINESS     = PASS
```

This decision does **not** authorize a Production import.

The following remain unchanged:

```text
PRODUCTION_WRITE_AUTHORIZED = NO
PRODUCTION_WRITE            = NONE
FORMAL_G7                   = NOT_EXECUTED
G8                          = NOT_EXECUTED
```

## 10. Required next boundary

Before any Production write:

1. Mother Ship must explicitly grant or withhold write authorization for exactly
   `VPG001_4_CANDIDATE_BATCH`.
2. Immediately before the write, the committed P0 guard must be re-run against Production
   read-only.
3. Any Production drift or guard failure means STOP and re-measurement.
4. Only the deterministic four-row Base subset is permitted. Full Base Seed Production apply
   remains prohibited.
5. Formal G7 remains open until P0 → P5 Production guards, idempotency, and Production Runtime QA
   have all passed.

## 11. Repository scope

This audit PR changes documentation only.

```text
Base Seed                    = unchanged
Knowledge Seeds              = unchanged
Candidate Master             = unchanged
Ranking / Recommendation     = unchanged
G1-G6 historical audits      = unchanged
nsrc-000023                  = unchanged / excluded from cohort
Production credential        = not recorded
Production hostname          = not recorded
Production database name     = not recorded
Production write             = NONE
```
