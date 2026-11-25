# Candidate Master Nationwide Source Track Extension Decision

> **Status: MOTHER_SHIP_DECISION = CLOSED**
>
> Recorded at: 2026-10-08
>
> Scope: Nationwide Source Candidate Extraction handoffs such as `NIIGATA-001-H001`
> を、Shrine Expansion Unified Gate の G0 Registryへどう接続するかを決定する。
>
> Runtime change: 0
> Candidate Master data mutation: 0
> Production write: 0

## 1. Decision

```text
CANDIDATE_MASTER_NATIONWIDE_EXTENSION
= EXTEND_EXISTING_MASTER

PARALLEL_CANDIDATE_REGISTRY
= PROHIBITED
```

Mother Shipは、全国Source TrackのCandidateも既存
`backend/temples/data/shrine_expansion_candidate_master.json`
をG0 Registry authorityとして使用する方針を確定する。

別のCandidate identity registryは作らない。

## 2. Reason

Current Unified Gate Contract already defines Candidate Master as the G0 registry authority.

A second registry would create two authorities for candidate identity / lifecycle and would require
later reconciliation before G1 / G2.

Therefore the extension direction is:

```text
one registry
one candidate authority
multiple admission tracks
```

The historical Wave0 track remains one admission track inside the same Candidate Master.

The Nationwide Source Candidate Extraction track becomes another admission track inside that same authority.

## 3. Historical Wave0 preservation

This decision does not rewrite the existing Wave0 history.

The following remain historical and immutable unless a separate audited decision changes them:

```text
wave0-001 ... wave0-044
W0-DB01 ... W0-DB07
historical Wave0 membership
historical lifecycle transitions
existing Wave0 audit records
```

The nationwide extension must generalize the contract around those records rather than renumbering,
renaming, or migrating them simply to make the new track fit.

## 4. Contract boundary

This decision fixes only the registry-family choice.

It does **not** yet decide:

```text
candidate_id namespace for nationwide Source candidates
candidate_reason value for official full-enumeration admission
build_batch / handoff provenance representation
status_reason_code extension
Candidate Master test-accounting policy
schema_version bump
exact H001 row payload
```

Those are follow-up contract decisions / implementation details.

## 5. Required invariants for the extension

Any implementation must preserve:

1. Candidate Master remains the single G0 registry authority.
2. Candidate identity remains keyed by `candidate_id`, never by name only.
3. Discovery / admission provenance remains distinct from Official Fact Source.
4. Historical Wave0 IDs and batch membership are unchanged.
5. Nationwide Source handoff provenance must remain traceable back to:
   - prefecture
   - source snapshot
   - source_position
   - NIIGATA / future prefecture batch and handoff
6. Candidate Extraction READY does not automatically mean Unified Gate G1 PASS.
7. G1 must still resolve canonical identity / duplicate state before G2 Position adoption.
8. Registry extension alone does not authorize Production import.
9. No Recommendation / Ranking / Concierge / Compass logic changes are introduced by the registry extension.
10. A new parallel candidate registry is not introduced.

## 6. H001 consequence

For:

```text
NIIGATA-001-H001
相吉神社
青澤神社
蒼柴神社
青海神社
青山稲荷神社
```

the previous G0 state:

```text
BLOCKED_CONTRACT_EXTENSION_REQUIRED
```

is resolved only at the **direction decision** level.

H001 is not yet registered because the concrete namespace / provenance / test contract is still undefined.

Therefore current execution state is:

```text
REGISTRY_FAMILY_DECISION = PASS
G0_DATA_REGISTRATION     = NOT_EXECUTED
G1                       = NOT_EXECUTED
G2                       = NOT_EXECUTED
```

## 7. Recommended implementation shape

The implementation should extend the existing Candidate Master contract with the smallest additive change.

Preferred properties:

```text
Wave0 historical rows untouched
new admission-track semantics additive
new nationwide candidate IDs non-colliding
handoff provenance explicit
tests split historical Wave0 invariants from total-registry invariants
```

Do not solve the extension by deleting or weakening existing Wave0 regression tests.
Tests that are truly historical Wave0 invariants should remain exact.
Registry-total assertions that currently encode "44 forever" must be redesigned so historical Wave0
remains exactly 44 while the global registry can grow.

## 8. Next decisions

The next contract decisions are:

```text
N1 candidate_id namespace
N2 nationwide admission candidate_reason
N3 batch / handoff provenance representation
N4 status_reason_code policy
N5 Candidate Master test-accounting policy
```

These should be settled before H001 rows are written into Candidate Master.

## 9. STOP

This decision does not mutate Candidate Master.

Do not proceed to H001 G1 / G2 until the additive Candidate Master contract extension has been defined
and H001 has been registered under it.
