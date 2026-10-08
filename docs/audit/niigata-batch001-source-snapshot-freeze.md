# NIIGATA Batch 001 Source Snapshot Freeze

> **Status: SNAPSHOT_FROZEN / REAL_BATCH_EXECUTION_READY**
>
> Recorded at: 2026-10-08
>
> Scope: 新潟県神社庁 Source の既定レスポンス順から固定した
> NIIGATA-001 first 100 raw candidates の Runner input snapshot freeze。
>
> Production DB write: 0
> Raw snapshot committed to repository: false

## 1. Frozen input

```text
batch_id          = NIIGATA-001
prefecture        = 新潟県
candidate_count   = 100
source_position   = page001-row001 ... page010-row010
unique_positions  = 100 / 100
captured_at       = 2026-10-08T14:27:00+09:00
source_verified_at = 2026-10-08
```

Frozen external input file:

```text
niigata_batch_001_snapshot.json
```

SHA-256:

```text
f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
```

The raw JSON is intentionally kept outside the repository.
The repository records only its immutable metadata and checksum.

## 2. Source authority

Source registry authority:

```text
Google Sheets: 神社のDB
Sheet: 神社庁Source
Prefecture: 新潟県
```

Source directory:

```text
https://niigata-jinjacho.jp/shrine_niigata/search.php
```

Entry Gate was rechecked on 2026-10-08:

```text
acquisition_scope = 全件取得可能
access_status      = 確認済
directory_url      = non-empty
verified_at        = 2026-10-08
source_total_count = 4619
```

## 3. Frozen traversal contract

```text
selection_rule
= 地区未指定 / キーワード未指定 /
  公式Source既定レスポンス順 /
  client-side sortなし
```

The public page does not declare its internal sort key.
Therefore this freeze does not relabel the order as 五十音順 or any other inferred ordering.

```text
ORDER_AUTHORITY = SOURCE_RESPONSE_ORDER
ORDER_SEMANTICS = UNDECLARED
```

## 4. Capture evidence

Canonical audit capture:

```text
Google Sheets: 神社のDB
Sheet: NIIGATA Batch001 Capture
Rows: 100
```

Acquisition evidence split:

```text
DIRECT_GLOBAL_PAGE            = 70
OFFICIAL_AREA_RECONSTRUCTED   = 30
```

The 30 reconstructed rows belong to source pages 3 / 6 / 9, which were unavailable
through the current retrieval path due to cache miss.

Those rows were rechecked on the same official 新潟県神社庁 site using official regional
listings plus adjacent global-page boundaries.

```text
POSITION_EVIDENCE_STATUS = CROSSCHECK_PASS_NOT_DIRECT
count                    = 30 / 30
position conflict         = 0
```

This evidence status remains distinct from DIRECT_GLOBAL_PAGE.
The snapshot freeze does not upgrade indirect cross-checks to direct page retrieval.

## 5. Runner input schema

The frozen JSON conforms to:

```text
backend/temples/services/shrine_source_candidate_niigata.py
```

Snapshot metadata:

```text
prefecture
batch_id
source_type
source_url
source_verified_at
captured_at
selection_rule
```

Candidate fields:

```text
source_position
raw_name
raw_address
kana
phone
source_id
detail_url
```

No audit-only fields such as:

```text
acquisition_evidence
evidence_note
position_evidence_status
position_evidence_note
```

are included in the Runner input, because the adapter is fail-closed on unknown keys.

Those fields remain in the Google Sheets audit capture.

## 6. Validation

Freeze-time validation:

```text
candidate_count              = 100
unique_source_position       = 100
duplicate_source_position    = 0
first_position               = page001-row001
first_name                   = 相吉神社
last_position                = page010-row010
last_name                    = 石井神社
```

The snapshot JSON was serialized with UTF-8, Japanese characters preserved,
sorted JSON keys, and a trailing newline before SHA-256 calculation.

## 7. Authority boundary

```text
Google Sheets Capture
= Source acquisition / Evidence authority

Frozen JSON
= Runner execution input

Repository audit record
= immutable freeze metadata / checksum
```

The frozen JSON is not a Production seed and is not canonical Shrine identity data.

```text
SNAPSHOT != Shrine identity authority
SNAPSHOT != Production import authorization
SNAPSHOT != Coordinate authorization
SNAPSHOT != Knowledge authorization
```

## 8. State transition

Before:

```text
RUNNER_IMPLEMENTATION = COMPLETE
REAL_BATCH_EXECUTION  = BLOCKED_INPUT_SNAPSHOT_REQUIRED
```

After this freeze:

```text
RUNNER_IMPLEMENTATION = COMPLETE
SNAPSHOT_FREEZE       = PASS
REAL_BATCH_EXECUTION  = READY
```

This only clears the input-snapshot blocker.

## 9. Next Gate

```text
real run1
-> real run2
-> reproducibility DIFF 0
-> REVIEW_REQUIRED returned to Mother Ship
-> READY_CANDIDATE handoff max 5
```

## 10. STOP

This freeze does not execute the Runner.

Do not proceed in this PR to:

- Production import
- Coordinate Audit
- Batch 002
- Okinawa rollout
- 15-prefecture expansion
