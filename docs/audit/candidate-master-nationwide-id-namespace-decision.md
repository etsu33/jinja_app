# Candidate Master Nationwide candidate_id Namespace Decision

> **Status: N1 MOTHER_SHIP_DECISION = CLOSED**
>
> Recorded at: 2026-10-08
>
> Scope: Nationwide Source Candidate Extraction TrackでCandidate Masterへ新規登録するCandidateの
> `candidate_id` namespaceを確定する。
>
> Candidate Master mutation: 0
> Production write: 0
> Runtime change: 0

## 1. Decision

```text
N1_NATIONWIDE_CANDIDATE_ID_NAMESPACE
= NSRC_GLOBAL_SERIAL

FORMAT
= nsrc-000001

REGEX
= ^nsrc-[0-9]{6}$
```

`nsrc` means Nationwide Source Candidate.

## 2. Namespace boundary

Existing historical Wave0 IDs remain unchanged:

```text
wave0-001 ... wave0-044
```

Nationwide Source Track uses a separate prefix:

```text
nsrc-000001
nsrc-000002
...
```

The two namespaces coexist inside the same Candidate Master authority.

## 3. Why global serial

The candidate ID must be stable even if operational provenance changes.

Therefore `candidate_id` does not encode:

```text
prefecture
source_position
batch_id
handoff_id
source URL
Shrine name
address
classification
lifecycle status
```

Those belong in explicit provenance / factual fields.

This avoids changing an identity key when:

- Source ordering changes;
- handoff boundaries change;
- a candidate is moved to HOLD / REVIEW;
- a later Source snapshot is captured;
- official name/address normalization changes;
- the same Candidate is processed in another downstream batch.

## 4. Allocation rule

Nationwide Source Track IDs are allocated monotonically.

```text
first allocated id = nsrc-000001
next id            = max(existing nsrc serial) + 1
width              = 6 digits
reuse              = prohibited
renumbering        = prohibited
```

If a Candidate is later found to be a duplicate / alias / already-known real-world Shrine,
its allocated `nsrc-*` ID is not reused for another Candidate.

Any later canonicalization / merge disposition is a separate G1 contract decision.

## 5. H001 assignment

Frozen H001 membership:

| candidate_id | source_position | candidate_name | source_address |
|---|---|---|---|
| nsrc-000001 | page001-row001 | 相吉神社 | 中魚沼郡津南町大字谷内4797番地 |
| nsrc-000002 | page001-row002 | 青澤神社 | 糸魚川市大字青海2696番地 |
| nsrc-000003 | page001-row003 | 蒼柴神社 | 長岡市悠久町707番地 |
| nsrc-000004 | page001-row004 | 青海神社 | 加茂市大字加茂字宮山229番地 |
| nsrc-000005 | page001-row005 | 青山稲荷神社 | 柏崎市荒浜4丁目1754番地2 |

Assignment authority:

```text
NIIGATA-001-H001 immutable source_position order
```

This assignment does not yet write the rows into Candidate Master.

## 6. Identity semantics

`candidate_id` identifies the Candidate Registry record.

It does not by itself prove:

```text
real-world Shrine identity
canonical official identity
duplicate status
Production Shrine identity
Position PASS
```

Those remain G1 / G2 responsibilities.

In particular:

```text
nsrc-000001
!= Shrine.id
!= source_position
!= handoff id
```

## 7. Collision / duplicate behavior

Before allocation, the exact `candidate_id` string must not already exist.

After allocation:

- IDs are immutable.
- IDs are never recycled.
- Name-only equality never causes ID reuse.
- Address-only equality never causes ID reuse.
- A later G1 finding that two Candidate records refer to the same real Shrine does not silently renumber either record.

How Candidate Master represents a confirmed duplicate / alias relationship remains governed by G1 and the Candidate Master duplicate contract.

## 8. Scale

Six decimal digits provide:

```text
000001 ... 999999
```

which is sufficient for the planned nationwide shrine expansion without changing namespace width.

No meaning is assigned to the serial number beyond allocation order.

## 9. Historical test preservation

Wave0-specific tests must continue to assert:

```text
historical Wave0 candidate set = exactly 44
historical Wave0 IDs           = unchanged
historical Wave0 batches       = unchanged
```

Global Candidate Master tests must be extended separately to allow additional `nsrc-*` rows.

Do not weaken historical Wave0 assertions merely because the global registry grows.

## 10. Not decided here

N1 does not decide:

```text
N2 nationwide candidate_reason
N3 batch / handoff provenance representation
N4 status_reason_code policy
N5 Candidate Master test-accounting implementation
schema_version bump
H001 Candidate Master payload
```

## 11. Current state

```text
N1 candidate_id namespace = CLOSED

H001 IDs
= nsrc-000001 ... nsrc-000005

G0_DATA_REGISTRATION
= NOT_EXECUTED

G1
= NOT_EXECUTED

G2
= NOT_EXECUTED
```

## 12. STOP

Do not register H001 rows until N2-N5 and the additive Candidate Master contract extension are closed.
