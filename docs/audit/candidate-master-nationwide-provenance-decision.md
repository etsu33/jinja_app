# Candidate Master Nationwide Batch / Handoff Provenance Decision

> **Status: N3 MOTHER_SHIP_DECISION = CLOSED**
>
> Recorded at: 2026-10-08
>
> Scope: Nationwide Source Candidate Extraction TrackのCandidateを既存Candidate Masterへ登録する際、
> Source Batch / Handoff / source_position / Frozen Snapshotをどのfieldで追跡するかを確定する。
>
> Candidate Master mutation: 0
> Production write: 0
> Runtime change: 0

## 1. Decision

```text
N3_NATIONWIDE_BATCH_HANDOFF_PROVENANCE
= ADD_ADMISSION_PROVENANCE_OBJECT

BUILD_BATCH_OVERLOAD
= PROHIBITED
```

Nationwide `nsrc-*` Candidateは、上流Source Candidate Extractionの由来を
新しいtop-level object:

```text
admission_provenance
```

で保持する。

Existing `build_batch` は従来どおり downstream Data Build provenance専用とし、
`NIIGATA-001` / `NIIGATA-001-H001` を入れない。

## 2. Responsibility split

```text
admission_provenance
= CandidateがどのSource extraction / handoffからRegistryへ入ったか

build_batch
= Candidateがどのdownstream Data Build batchで処理されたか
```

この2つは別責務であり、相互代替しない。

Example:

```text
source extraction batch = NIIGATA-001
source handoff          = NIIGATA-001-H001

downstream build_batch  = not assigned yet
```

G0登録時点では上流provenanceだけ確定していてよい。

## 3. Canonical object shape

Nationwide `nsrc-*` Candidateは、最低限次のexact keysを持つ。

```json
{
  "admission_provenance": {
    "track": "nationwide_source_candidate",
    "prefecture": "新潟県",
    "source_batch_id": "NIIGATA-001",
    "handoff_id": "NIIGATA-001-H001",
    "source_position": "page001-row001",
    "source_snapshot_sha256": "f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380",
    "source_url": "https://niigata-jinjacho.jp/shrine_niigata/search.php",
    "source_verified_at": "2026-10-08",
    "captured_at": "2026-10-08T14:27:00+09:00"
  }
}
```

Required keys:

```text
track
prefecture
source_batch_id
handoff_id
source_position
source_snapshot_sha256
source_url
source_verified_at
captured_at
```

No optional omission is allowed for the first nationwide implementation.

## 4. Field semantics

### track

```text
nationwide_source_candidate
```

Identifies the admission track.

It is not a lifecycle state.

### prefecture

The prefecture scope under which the official Source extraction was performed.

For H001:

```text
新潟県
```

This must match the Candidate top-level `prefecture` after G0 registration.

### source_batch_id

The frozen Source Extraction batch.

For H001:

```text
NIIGATA-001
```

### handoff_id

The immutable READY handoff that admitted the Candidate downstream.

For H001:

```text
NIIGATA-001-H001
```

### source_position

The immutable position inside the frozen Source snapshot.

Examples:

```text
page001-row001
page001-row002
...
```

It is provenance, not Candidate identity.

### source_snapshot_sha256

The SHA-256 of the exact Frozen Snapshot used for admission.

For NIIGATA-001:

```text
f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
```

This prevents a later Source refresh from being silently treated as the original admission snapshot.

### source_url

The upstream official directory / search Source URL used by the frozen snapshot.

It does not replace later G1 / G3 official fact sources.

### source_verified_at

The date the upstream Source Entry Gate was verified.

### captured_at

The frozen snapshot capture timestamp.

It does not change when downstream lifecycle changes.

## 5. H001 canonical provenance

| candidate_id | source_position | source_batch_id | handoff_id |
|---|---|---|---|
| nsrc-000001 | page001-row001 | NIIGATA-001 | NIIGATA-001-H001 |
| nsrc-000002 | page001-row002 | NIIGATA-001 | NIIGATA-001-H001 |
| nsrc-000003 | page001-row003 | NIIGATA-001 | NIIGATA-001-H001 |
| nsrc-000004 | page001-row004 | NIIGATA-001 | NIIGATA-001-H001 |
| nsrc-000005 | page001-row005 | NIIGATA-001 | NIIGATA-001-H001 |

All five share:

```text
track                  = nationwide_source_candidate
prefecture             = 新潟県
source_snapshot_sha256 = f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
source_url             = https://niigata-jinjacho.jp/shrine_niigata/search.php
source_verified_at     = 2026-10-08
captured_at            = 2026-10-08T14:27:00+09:00
```

## 6. Immutability

Once the Candidate enters G0:

```text
admission_provenance
= IMMUTABLE
```

Do not rewrite it when:

- Candidate moves to BUILD_READY / IMPORTED / CORE_READY;
- Candidate moves to HOLD / REVIEW;
- a later Source snapshot is captured;
- the official Source changes order;
- a later batch sees the same shrine again;
- G1 resolves duplicate / alias / same-name-different-shrine;
- downstream Data Build assigns `build_batch`.

A later observation is new evidence, not a replacement for the original admission record.

## 7. Do not overload existing fields

### build_batch

Do not use:

```text
build_batch = NIIGATA-001
build_batch = NIIGATA-001-H001
```

`build_batch` remains downstream Data Build provenance.

### candidate_id

Do not encode:

```text
source_batch_id
handoff_id
source_position
```

N1 already fixed `nsrc-000001` style stable IDs.

### candidate_reason

Do not encode the batch / handoff in `candidate_reason`.

N2 already fixed:

```text
official_source_full_enumeration_candidate
```

### discovery_sources

Do not force Source batch / handoff provenance into the existing Wave0-shaped
`discovery_sources[]` contract.

Current `discovery_sources[]` includes ranking-oriented fields such as `discovery_rank`.
Nationwide Source handoff provenance has different semantics and must not fake a ranking value.

N5 may redesign global test/accounting boundaries, but N3 keeps these responsibilities distinct.

## 8. G0 / downstream relationship

At G0 registration:

```text
candidate_id          = assigned
candidate_reason      = assigned
admission_provenance  = assigned
build_batch           = not yet assigned unless downstream Data Build has separately decided it
```

Later:

```text
admission_provenance = unchanged
build_batch          = downstream Data Build decision
```

The downstream batch value must never be inferred from `handoff_id`.

## 9. Validation requirements

The Candidate Master extension must later test at minimum:

1. every `nsrc-*` row has `admission_provenance`;
2. `track == nationwide_source_candidate`;
3. top-level `prefecture == admission_provenance.prefecture`;
4. `source_batch_id` is non-empty;
5. `handoff_id` is non-empty;
6. `source_position` is non-empty;
7. `source_snapshot_sha256` matches exactly 64 lowercase hex chars;
8. H001 five rows all share one snapshot hash and one handoff id;
9. H001 source_positions are unique;
10. Wave0 historical rows are not required to gain `admission_provenance` retroactively;
11. `build_batch` does not contain Source Extraction batch/handoff IDs.

## 10. Historical Wave0 preservation

Wave0 rows remain unchanged.

Do not backfill artificial `admission_provenance` objects onto `wave0-*` rows merely for shape symmetry.

Their historical admission provenance remains represented by the existing Wave0 Candidate Master /
audit records.

The new object is additive for the nationwide Source track.

## 11. Not decided here

N3 does not decide:

```text
N4 status_reason_code policy
N5 Candidate Master test-accounting policy
schema_version bump
downstream Data Build batch namespace for nsrc candidates
exact H001 candidate_status
```

## 12. Current state

```text
N1 candidate_id namespace = CLOSED
N2 candidate_reason       = CLOSED
N3 provenance             = CLOSED

G0_DATA_REGISTRATION
= NOT_EXECUTED

G1
= NOT_EXECUTED

G2
= NOT_EXECUTED
```

## 13. STOP

Do not write H001 Candidate Master rows until N4 / N5 and the additive Candidate Master Contract extension are closed.
