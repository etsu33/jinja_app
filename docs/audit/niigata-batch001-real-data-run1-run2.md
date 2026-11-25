# NIIGATA Batch 001 Real-Data Run1 / Run2 Audit

> **Status: REAL_DATA_EQUIVALENT_RUN = PASS / CANONICAL_MANAGE_PY_RUN = NOT_EXECUTED**
>
> Recorded at: 2026-10-08
>
> Scope: Frozen `NIIGATA-001` 100-candidate snapshotを、current `develop` の
> Candidate Extraction Runnerと同じnormalization / collision lookup / classification契約で
> Production Shrine dataへSELECT-only適用し、run1 / run2の再現性を確認した記録。
>
> Production write: 0

## 1. Input

Frozen snapshot:

```text
file              = niigata_batch_001_snapshot.json
batch_id          = NIIGATA-001
candidate_count   = 100
captured_at       = 2026-10-08T14:27:00+09:00
source_verified_at = 2026-10-08
sha256            = f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
```

Freeze authority:

```text
docs/audit/niigata-batch001-source-snapshot-freeze.md
```

## 2. Execution authority

Current implementation read from `develop`:

```text
backend/temples/services/shrine_source_candidate_extraction.py
backend/temples/services/shrine_source_candidate_niigata.py
backend/temples/services/shrine_duplicate_normalize.py
backend/temples/services/shrine_submission.py
```

The following current repository behavior was reproduced exactly for the read-only data run:

```text
normalize_shrine_name_for_duplicate()
normalize_shrine_address_for_duplicate()
shrine_name_duplicate_base_key()
find_duplicate_candidates(..., limit=100)

READY_CANDIDATE / REVIEW_REQUIRED / INVALID
M4 READY handoff max 5
```

`find_duplicate_candidates()` remains COLLISION_SIGNAL_ONLY.

## 3. Execution method and limitation

This execution environment did not have:

```text
repository working copy
Django runtime
Production DATABASE_URL
```

Therefore the Django management command itself was **not** invoked.

Instead:

1. the exact frozen JSON input was read;
2. current `develop` Runner / normalizer / duplicate lookup code was read;
3. Production `temples_shrine` rows were queried via authorized SELECT-only Supabase access;
4. the same normalization, name/base-key matching, address score, ordering, `limit=100`,
   classification, and handoff rules were applied;
5. the same query / same frozen input was independently executed twice.

This is recorded as:

```text
REAL_DATA_EQUIVALENT_RUN1 = PASS
REAL_DATA_EQUIVALENT_RUN2 = PASS
CANONICAL_MANAGE_PY_RUN   = NOT_EXECUTED
```

Do not rewrite this record as if
`python manage.py extract_shrine_source_candidates` was executed.

## 4. Production DB snapshot stability

Both executions observed the same Production Shrine state:

```text
Shrine row count = 120
DB fingerprint   = cfac51b6cddc54d62c951545f5fd0f12
```

The fingerprint was calculated from the ordered tuple:

```text
(id, name_jp, address)
```

Run1 and run2 had identical count and fingerprint.

## 5. Run1

```text
total_raw                 = 100
READY_CANDIDATE           = 81
REVIEW_REQUIRED           = 19
INVALID                   = 0
possibly_truncated        = 0
READY handoff count       = 17
Production write          = 0
```

First handoff:

```text
NIIGATA-001-H001
page001-row001
page001-row002
page001-row003
page001-row004
page001-row005
```

Final handoff:

```text
NIIGATA-001-H017
page010-row010
```

## 6. Run2

```text
total_raw                 = 100
READY_CANDIDATE           = 81
REVIEW_REQUIRED           = 19
INVALID                   = 0
possibly_truncated        = 0
READY handoff count       = 17
Production write          = 0
```

Run2 first / final handoff membership matched Run1.

## 7. REVIEW_REQUIRED rows

All 19 rows were collision-signal reviews with `returned_candidate_count = 1`.

### Production candidate id=89 / 赤城神社

Production candidate:

```text
id      = 89
name    = 赤城神社
address = 群馬県前橋市富士見町赤城山4-2
```

Affected NIIGATA source positions:

```text
page002-row001
page002-row002
page002-row003
page002-row004
page002-row005
```

These are five different 新潟県 addresses.
No duplicate identity decision is made.

### Production candidate id=46 / 愛宕神社

Production candidate:

```text
id      = 46
name    = 愛宕神社
address = 東京都港区愛宕1-5-3
```

Affected NIIGATA source positions:

```text
page005-row009
page005-row010
page006-row001
page006-row002
page006-row003
page006-row004
page006-row005
page006-row006
page006-row007
page006-row008
page006-row009
```

These are eleven different 新潟県 addresses.
No duplicate identity decision is made.

### Production candidate id=35 / 賀茂別雷神社（上賀茂神社）

Production candidate:

```text
id      = 35
name    = 賀茂別雷神社（上賀茂神社）
address = 京都府京都市北区上賀茂本山339
```

Affected NIIGATA source positions:

```text
page009-row009
page009-row010
page010-row001
```

The current broad base-name matching returns this candidate because the Production name contains
`雷神社`.

No duplicate identity decision is made.

## 8. Reproducibility

Run1 vs Run2:

```text
DB row count DIFF             = 0
DB fingerprint DIFF           = 0
classification summary DIFF   = 0
collision payload DIFF        = 0
handoff membership DIFF       = 0

REPRODUCIBILITY_DIFF_COUNT    = 0
REPRODUCIBILITY               = PASS
```

## 9. Interpretation

```text
READY_CANDIDATE = 81
```

means only that the current collision lookup returned 0 candidates and the minimum schema /
prefecture gate passed.

It does not authorize:

```text
Production import
Coordinate adoption
Knowledge generation
Recommendation inclusion
```

Likewise:

```text
REVIEW_REQUIRED = 19
```

does not mean 19 duplicates.

All 19 rows must remain stopped until Mother Ship Human Review under M5.

## 10. Next Gate

```text
Mother Ship review of 19 REVIEW_REQUIRED rows
-> READY set freeze
-> max 5 READY candidates per handoff
-> Coordinate / Base Seed Candidate Gate
```

Canonical CLI execution remains a separate execution-method verification if required.

## 11. STOP

This audit does not perform:

- Production INSERT / UPDATE / DELETE
- Candidate Master write
- Coordinate Audit
- Production import
- Batch 002
- Okinawa rollout
- 15-prefecture expansion
