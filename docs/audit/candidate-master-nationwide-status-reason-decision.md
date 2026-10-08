# Candidate Master Nationwide status_reason_code Decision

> **Status: N4 MOTHER_SHIP_DECISION = CLOSED**
>
> Recorded at: 2026-10-08
>
> Scope: Nationwide Source Candidate TrackでCandidate Masterへ登録するCandidateの
> `status_reason_code` policyを確定する。
>
> Candidate Master mutation: 0
> Production write: 0
> Runtime change: 0

## 1. Decision

```text
N4_STATUS_REASON_POLICY
= LIFECYCLE_STATE_SPECIFIC

POSITIVE_STATUS_REASON_REUSE
= PROHIBITED_FOR_NEW_NATIONWIDE_TRACK
```

Nationwide `nsrc-*` Candidateでは、`status_reason_code` は
**現在の `candidate_status` がなぜその状態なのか**だけを表す。

`candidate_reason` / `admission_provenance` の内容を重複して持たせない。

## 2. Responsibility boundary

```text
candidate_reason
= Registryへ入った admission reason

admission_provenance
= どのSource / snapshot / batch / handoffから入ったか

status_reason_code
= なぜ現在の candidate_status なのか
```

例:

```text
candidate_reason
= official_source_full_enumeration_candidate

candidate_status
= DISCOVERED

status_reason_code
= REGISTRY_ADMISSION_COMPLETE
```

この3つは別責務である。

## 3. Initial H001 lifecycle state

H001の5社は、Candidate ExtractionではREADY済みだが、
Unified GateではまだG1 / G2を通過していない。

したがってG0登録時のcanonical lifecycle stateは:

```text
candidate_status
= DISCOVERED

status_reason_code
= REGISTRY_ADMISSION_COMPLETE
```

This means only:

```text
Candidate has been admitted to the single Candidate Master registry under the
approved nationwide admission contract.
```

It does not mean:

```text
G1 identity PASS
G2 position PASS
BUILD_READY
Production import approved
Recommendation eligible
```

## 4. Positive lifecycle reason policy

New nationwide Candidate rows must not carry one generic positive reason code across multiple lifecycle states.

Use state-specific reasons.

Canonical positive mapping policy:

```text
DISCOVERED
-> REGISTRY_ADMISSION_COMPLETE

BUILD_READY
-> BUILD_READINESS_CONFIRMED

IMPORTED
-> PRODUCTION_IMPORT_COMPLETE

CORE_READY
-> CORE_READY_CONTRACT_PASS
```

Each transition updates `status_reason_code` together with `candidate_status`.

## 5. HOLD / REVIEW policy

HOLD / REVIEW reasons are not admission-track labels.

They must identify the current blocking / review reason owned by the relevant Gate.

Examples of valid semantics:

```text
IDENTITY_REVIEW_REQUIRED
HOLD_POSITION_REVIEW
SOURCE_HOLD
MODEL_CHANGE_REQUIRED
ENTITY_GRANULARITY_REVIEW
```

Exact reason codes for a newly encountered blocker are defined by the owning Gate / dedicated audit,
not inferred from candidate name, source type, or lifecycle history.

Do not create:

```text
NATIONWIDE_HOLD
NIIGATA_REVIEW
SOURCE_TRACK_BLOCKED
```

because those say where the Candidate came from, not why the current lifecycle is blocked.

## 6. Historical Wave0 preservation

Existing Wave0 rows remain unchanged.

In particular, historical use of:

```text
WAVE0_CORE_READY_CANDIDATE
```

across multiple positive lifecycle states is preserved as historical contract behavior.

Do not rewrite Wave0 rows merely to match the new nationwide policy.

The nationwide policy is additive and applies to new `nsrc-*` rows.

## 7. H001 assignment

When H001 is registered:

| candidate_id | candidate_status | status_reason_code |
|---|---|---|
| nsrc-000001 | DISCOVERED | REGISTRY_ADMISSION_COMPLETE |
| nsrc-000002 | DISCOVERED | REGISTRY_ADMISSION_COMPLETE |
| nsrc-000003 | DISCOVERED | REGISTRY_ADMISSION_COMPLETE |
| nsrc-000004 | DISCOVERED | REGISTRY_ADMISSION_COMPLETE |
| nsrc-000005 | DISCOVERED | REGISTRY_ADMISSION_COMPLETE |

All five remain:

```text
G1 = NOT_EXECUTED
G2 = NOT_EXECUTED
```

at the moment of G0 registration.

## 8. Transition invariants

For nationwide `nsrc-*` rows:

1. `candidate_status` and `status_reason_code` must be semantically consistent.
2. Positive lifecycle transitions update both fields together.
3. HOLD / REVIEW transitions replace the positive reason with the current blocker/review reason.
4. HOLD / REVIEW release must pass through the owning Gate before restoring a positive lifecycle state.
5. `candidate_reason` never changes because of lifecycle transition.
6. `admission_provenance` never changes because of lifecycle transition.
7. `build_batch` is independent provenance and is not encoded in `status_reason_code`.

## 9. Test implications

The Candidate Master contract extension must add a nationwide mapping assertion equivalent to:

```text
DISCOVERED  -> REGISTRY_ADMISSION_COMPLETE
BUILD_READY -> BUILD_READINESS_CONFIRMED
IMPORTED    -> PRODUCTION_IMPORT_COMPLETE
CORE_READY  -> CORE_READY_CONTRACT_PASS
```

For HOLD / REVIEW, tests should verify that the reason is one of the explicitly accepted
owning-Gate reason codes for the current row / audit state.

Do not delete or weaken existing Wave0 exact reason-count tests.

N5 will define how historical Wave0 accounting and growing global registry accounting are separated.

## 10. Why not reuse candidate_reason

The following is prohibited:

```text
status_reason_code
= official_source_full_enumeration_candidate
```

because that value explains how the Candidate entered the Registry, not why it is currently
DISCOVERED / BUILD_READY / IMPORTED / CORE_READY / HOLD / REVIEW.

## 11. Why not keep one nationwide positive code

The following pattern is also prohibited for the new track:

```text
DISCOVERED  = NATIONWIDE_SOURCE_CANDIDATE
BUILD_READY = NATIONWIDE_SOURCE_CANDIDATE
IMPORTED    = NATIONWIDE_SOURCE_CANDIDATE
CORE_READY  = NATIONWIDE_SOURCE_CANDIDATE
```

It makes `status_reason_code` stop explaining the current status.

## 12. Not decided here

N4 does not decide:

```text
N5 Candidate Master test-accounting policy
schema_version bump
exact build_batch namespace for later nationwide Data Build
new blocker reason codes not yet encountered
H001 Candidate Master implementation PR
```

## 13. Current state

```text
N1 candidate_id namespace = CLOSED
N2 candidate_reason       = CLOSED
N3 provenance             = CLOSED
N4 status_reason_code     = CLOSED

H001 initial lifecycle
= DISCOVERED / REGISTRY_ADMISSION_COMPLETE

G0_DATA_REGISTRATION
= NOT_EXECUTED

G1
= NOT_EXECUTED

G2
= NOT_EXECUTED
```

## 14. STOP

Do not write H001 Candidate Master rows until N5 and the additive Candidate Master Contract extension are closed.
