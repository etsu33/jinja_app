# NIIGATA-001-VPG001 — G7 Production Closure

## 1. Final classification

```text
EXECUTION_MODE                 = VPG001_4_CANDIDATE_BATCH
AUTHORIZED_CANDIDATES          = nsrc-000021 / nsrc-000022 / nsrc-000024 / nsrc-000025
EXCLUDED                       = nsrc-000023

BACKUP_RESTORE_READINESS       = PASS
PRODUCTION_WRITE_AUTHORIZED    = YES
BASE_IMPORT                    = PASS
BASE_IDEMPOTENCY               = PASS
P1_POST_BASE                   = PASS
P2_POST_000021                 = PASS
P3_POST_000022                 = PASS
P4_POST_000024                 = PASS
P5_POST_000025                 = PASS
P5_FINAL_RECHECK               = PASS
KNOWLEDGE_IDEMPOTENCY          = PASS
PRODUCTION_RUNTIME_QA          = PASS

PROCEDURE_DEVIATION            = NSRC_000022_PRE_WRITE_VALIDATE_ONLY_NOT_OBSERVED_IN_SUPPLIED_LOG

G7_BLOCKERS_REMAINING          = NONE
G7_STATUS                      = CLOSED
G7_RESULT                      = PASS
FORMAL_G7                      = PASS

PRODUCTION_WRITE_AFTER_CLOSURE = PROHIBITED
G8_CORE_READY                  = NOT_EXECUTED
```

Recorded at: 2026-10-20

Base:
`develop@6aa0b0f15cd9849452f71324f0bf30f42f4382a8` (#3281 merged)

This closure records Mother Ship execution evidence. This repository change is documentation only
and performs no Production connection or write.

## 2. Scope and invariants

Authorized write cohort:

- nsrc-000021 荒川神社
- nsrc-000022 五十嵐神社
- nsrc-000024 秋葉神社
- nsrc-000025 天津神社

Explicitly excluded:

- nsrc-000023 熱串彦神社

The following remained prohibited throughout execution:

```text
full Base Seed Production apply
nsrc-000023 write
unrelated shrine writes
ranking / recommendation changes
Candidate Master changes
G8 execution
```

## 3. Backup / restore readiness

Authority:
`docs/audit/niigata-vpg001-g7-backup-restore-readiness.md`

```text
PRODUCTION_PREFLIGHT_RECHECK = PASS
BACKUP_CLIENT_COMPATIBILITY  = PASS
FRESH_PRODUCTION_BACKUP      = PASS
ISOLATED_RESTORE             = PASS
RESTORE_FINGERPRINT          = MATCHED
RESTORE_P0_GUARD             = PASS
BACKUP_RESTORE_READINESS     = PASS
```

Frozen Production P0:

```text
Shrine      = 129
Source      = 145
Deity       = 295
History     = 236
Citation    = 2
SourceFact  = 34
Collective  = 6
```

Immediately before the authorized write, the committed Production P0 guard was re-run read-only and
all five statements returned 1.

```text
niigata_vpg001_g7_p0_cohort_checkpoint_pass = 1
niigata_vpg001_g7_p0_nsrc_000021_pass        = 1
niigata_vpg001_g7_p0_nsrc_000022_pass        = 1
niigata_vpg001_g7_p0_nsrc_000024_pass        = 1
niigata_vpg001_g7_p0_nsrc_000025_pass        = 1
```

## 4. Production write authorization

Mother Ship explicitly authorized:

```text
PRODUCTION_WRITE_AUTHORIZED = YES
EXECUTION_MODE              = VPG001_4_CANDIDATE_BATCH
```

Authorized scope:

- deterministic target-only 4-row Base import
- Knowledge import in order 000021 -> 000022 -> 000024 -> 000025
- committed cumulative stage guards
- idempotency verification
- Production Runtime QA

No broader Production write was authorized.

## 5. Deterministic Base subset

The committed cohort extractor produced exactly four rows outside the repository.

```text
SUBSET_ROWS=4
candidate_ids=nsrc-000021,nsrc-000022,nsrc-000024,nsrc-000025
SUBSET_SHA256=7dafa5e1243c50b0c46a5a4f02762e533326b0fac956acc7dfe979b182691c03
```

The independent `shasum -a 256` result matched exactly.

```text
BASE_SUBSET_GENERATED = PASS
BASE_SUBSET_SHA256     = MATCH
```

## 6. Base Shrine Production import

### 6.1 Dry-run

```text
CREATE 荒川神社
CREATE 五十嵐神社
CREATE 秋葉神社
CREATE 天津神社

goriyaku_tags rows=0 updated=0 added_links=0 removed_links=0
done created=4 updated=0 skipped=0 total_seed=4
```

### 6.2 Apply

The same four-row subset was applied with `--skip-goriyaku-tags`.

```text
CREATE 荒川神社
CREATE 五十嵐神社
CREATE 秋葉神社
CREATE 天津神社

goriyaku_tags rows=0 updated=0 added_links=0 removed_links=0
done created=4 updated=0 skipped=0 total_seed=4
```

Dry-run and apply matched.

Observed Shrine ids were 135 / 136 / 137 / 138. These numeric ids are point-in-time provenance only;
canonical identity remains exact `(name_jp, address)`.

### 6.3 P1 post-Base guard

```text
niigata_vpg001_g7_p1_cohort_checkpoint_pass = 1
niigata_vpg001_g7_p1_nsrc_000021_pass        = 1
niigata_vpg001_g7_p1_nsrc_000022_pass        = 1
niigata_vpg001_g7_p1_nsrc_000024_pass        = 1
niigata_vpg001_g7_p1_nsrc_000025_pass        = 1
```

Expected P1 aggregate:

```text
Shrine      = 133
Source      = 145
Deity       = 295
History     = 236
Citation    = 2
SourceFact  = 34
Collective  = 6
```

```text
G7_BASE_IMPORT = PASS
P1             = PASS
```

### 6.4 Base idempotency

A second dry-run returned only SKIP:

```text
SKIP id=135 荒川神社
SKIP id=136 五十嵐神社
SKIP id=137 秋葉神社
SKIP id=138 天津神社
done created=0 updated=0 skipped=4 total_seed=4
```

```text
G7_BASE_IDEMPOTENCY = PASS
```

## 7. Knowledge Production import

### 7.1 nsrc-000021 -> P2

Pre-write validation:

```text
validate-only: OK, no errors
```

Dry-run and apply plan:

```text
source_CREATE  = 1
deity_CREATE   = 1
history_CREATE = 1
```

Apply:

```text
sources created      = 1
deities created      = 1
histories created    = 1
collectives created  = 0
memberships created  = 0
source_facts created = 0
```

P2 guard:

```text
cohort = 1
000021 = 1
000022 = 1
000024 = 1
000025 = 1
```

Expected cumulative aggregate:

```text
Shrine 133 / Source 146 / Deity 296 / History 237 / Citation 2 / SourceFact 34 / Collective 6
```

```text
G7_KNOWLEDGE_000021 = PASS
P2                   = PASS
```

### 7.2 nsrc-000022 -> P3

Observed dry-run and apply plan:

```text
source_CREATE = 1
deity_CREATE  = 1
history_CREATE = 0
```

Apply:

```text
sources created      = 1
deities created      = 1
histories created    = 0
collectives created  = 0
memberships created  = 0
source_facts created = 0
```

P3 guard:

```text
cohort = 1
000021 = 1
000022 = 1
000024 = 1
000025 = 1
```

Expected cumulative aggregate:

```text
Shrine 133 / Source 147 / Deity 297 / History 237 / Citation 2 / SourceFact 34 / Collective 6
```

```text
G7_KNOWLEDGE_000022 = PASS
P3                   = PASS
```

Procedure note: the supplied execution log does not contain a pre-write `--validate-only` result for
nsrc-000022. This is recorded as a procedure deviation, not rewritten as if observed. The subsequent
dry-run, apply, P3 guard, idempotency, final P5 guard, and Production Runtime QA all passed.

### 7.3 nsrc-000024 -> P4

Pre-write validation:

```text
validate-only: OK, no errors
```

Dry-run and apply plan:

```text
source_CREATE  = 1
deity_CREATE   = 3
history_CREATE = 2
```

Apply:

```text
sources created      = 1
deities created      = 3
histories created    = 2
collectives created  = 0
memberships created  = 0
source_facts created = 0
```

P4 guard:

```text
cohort = 1
000021 = 1
000022 = 1
000024 = 1
000025 = 1
```

Expected cumulative aggregate:

```text
Shrine 133 / Source 148 / Deity 300 / History 239 / Citation 2 / SourceFact 34 / Collective 6
```

```text
G7_KNOWLEDGE_000024 = PASS
P4                   = PASS
```

### 7.4 nsrc-000025 -> P5

Pre-write validation:

```text
validate-only: OK, no errors
```

Dry-run and apply plan:

```text
source_CREATE  = 1
deity_CREATE   = 3
history_CREATE = 5
```

Apply:

```text
sources created      = 1
deities created      = 3
histories created    = 5
collectives created  = 0
memberships created  = 0
source_facts created = 0
```

P5 guard:

```text
cohort = 1
000021 = 1
000022 = 1
000024 = 1
000025 = 1
```

Final cumulative Production aggregate:

```text
Shrine      = 133
Source      = 149
Deity       = 303
History     = 244
Citation    = 2
SourceFact  = 34
Collective  = 6
```

The committed P5 guard was re-run after idempotency checks and again returned all five PASS values.

```text
G7_KNOWLEDGE_000025 = PASS
P5                   = PASS
P5_FINAL_RECHECK      = PASS
```

Observed point-in-time provenance ids:

```text
Source  = 147..150
Deity   = 296..303
History = 237..244
```

These ids are not identity contracts.

## 8. Knowledge idempotency

All four Knowledge seeds were re-run with `--dry-run`.

```text
000021:
  source_REUSE_EXISTING = 1
  deity_SKIP_EXISTS     = 1
  history_SKIP_EXISTS   = 1

000022:
  source_REUSE_EXISTING = 1
  deity_SKIP_EXISTS     = 1

000024:
  source_REUSE_EXISTING = 1
  deity_SKIP_EXISTS     = 3
  history_SKIP_EXISTS   = 2

000025:
  source_REUSE_EXISTING = 1
  deity_SKIP_EXISTS     = 3
  history_SKIP_EXISTS   = 5
```

No CREATE was planned.

```text
G7_KNOWLEDGE_IDEMPOTENCY = PASS
```

## 9. Production Runtime QA

The committed runtime QA scripts were executed against Production data for all four candidates.
Each script begins its verification transaction with `SET TRANSACTION READ ONLY`.

Every candidate returned:

```text
TARGET_IDENTITY=PASS
DETAIL_RUNTIME=PASS
SOURCE_RELATION_INTEGRITY=PASS
SHARED_ELIGIBILITY=PASS
CONCIERGE_CANDIDATE_PATH=PASS
RECOMMENDATION_REASON=PASS
COMPASS_DISTANCE=PASS
COMPASS_DIRECTION=PASS
GORIYAKU_ISOLATION=PASS
FACT_OWNERSHIP_ISOLATION=PASS
AGGREGATES_UNCHANGED=PASS
G7_PRODUCTION_RUNTIME_QA=PASS
TRANSACTION_MODE=READ_ONLY
```

Observed shared runtime trace for each candidate:

```text
count=115
eligible=115
ineligible=18
with_place_id=2
miss_latlng=0
dist_none=0
```

Recommendation Top1 and Compass Top1 were not required by the G6/G7 contract.

```text
PRODUCTION_RUNTIME_QA_000021 = PASS
PRODUCTION_RUNTIME_QA_000022 = PASS
PRODUCTION_RUNTIME_QA_000024 = PASS
PRODUCTION_RUNTIME_QA_000025 = PASS
```

## 10. Procedure deviation assessment

```text
PROCEDURE_DEVIATION = NSRC_000022_PRE_WRITE_VALIDATE_ONLY_NOT_OBSERVED_IN_SUPPLIED_LOG
```

This deviation is recorded rather than silently inferred away.

It is classified as non-blocking for Formal G7 because the same committed seed subsequently passed:

- pre-write dry-run with the expected exact CREATE plan;
- Production apply with the same exact plan;
- P3 fail-closed cumulative guard;
- Knowledge idempotency with zero CREATE;
- final P5 cumulative guard after all candidates;
- Production Runtime QA including target identity, source relation integrity, shared eligibility,
  Concierge path, recommendation reason, Compass distance/direction, goriyaku isolation, Fact
  ownership isolation, and aggregate immutability.

No unexpected persisted state was observed.

## 11. Final Production delta

Measured P0 -> verified P5:

```text
Shrine      +4   (129 -> 133)
Source      +4   (145 -> 149)
Deity       +8   (295 -> 303)
History     +8   (236 -> 244)
Citation    +0   (2)
SourceFact  +0   (34)
Collective  +0   (6)
goriyaku系  +0
```

This equals the frozen expected delta from #3280.

## 12. No-scope-change invariants

```text
Full Base Seed                         NOT APPLIED
nsrc-000023                            NOT WRITTEN
unrelated Shrine rows                  NOT AUTHORIZED / no detected delta
goriyaku / goriyaku tags               delta 0
Citation                               delta 0
SourceFact                             delta 0
Collective                             delta 0
Ranking / Score                        UNCHANGED
Recommendation contract                UNCHANGED
Position decisions                     UNCHANGED
models / migrations                    UNCHANGED
Candidate Master                       UNCHANGED
G1-G6 historical results               UNCHANGED
G8                                      NOT EXECUTED
```

## 13. Formal G7 closure

Mother Ship classification:

```text
G7_BLOCKERS_REMAINING          = NONE
G7_STATUS                      = CLOSED
G7_RESULT                      = PASS
FORMAL_G7                      = PASS

PRODUCTION_WRITE_AFTER_CLOSURE = PROHIBITED
G8_CORE_READY                  = NOT_EXECUTED
```

G7 PASS does not imply G8 CORE READY. Candidate Master lifecycle alignment and the G8 Completion
Contract remain a separate gate.
