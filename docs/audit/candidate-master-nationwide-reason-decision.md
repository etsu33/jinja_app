# Candidate Master Nationwide candidate_reason Decision

> **Status: N2 MOTHER_SHIP_DECISION = CLOSED**
>
> Recorded at: 2026-10-08
>
> Scope: Nationwide Source Candidate Extraction TrackでCandidate Masterへ新規登録するCandidateの
> `candidate_reason` を確定する。
>
> Candidate Master mutation: 0
> Production write: 0
> Runtime change: 0

## 1. Decision

```text
N2_NATIONWIDE_CANDIDATE_REASON
= official_source_full_enumeration_candidate
```

Meaning:

```text
The Candidate was admitted to the Registry because it was discovered through
deterministic full-enumeration of an accepted official source.
```

## 2. Contract semantics

Current Candidate Master Contract defines:

```text
candidate_reason
= Registry admission reason
```

It is not:

```text
candidate_status reason
duplicate result
source_type
official identity proof
Recommendation reason
priority
ranking signal
```

The current status reason remains owned by `status_reason_code`.

## 3. Wave0 preservation

Existing Wave0 default remains unchanged:

```text
candidate_defaults.candidate_reason
= historical_recovered_popularity_candidate
```

Do not replace the global default with the nationwide value.

Historical Wave0 rows continue to inherit that default exactly as before.

Nationwide `nsrc-*` rows must explicitly override `candidate_reason` per Candidate:

```text
candidate_reason
= official_source_full_enumeration_candidate
```

This preserves historical meaning while allowing multiple admission tracks in one Candidate Master.

## 4. Why this value

The reason value describes the **admission mechanism**, not the provider.

Therefore it does not encode:

```text
prefecture
Jinjacho organization name
source URL
batch id
handoff id
source_position
candidate classification
```

Those belong to explicit provenance fields.

The value is intentionally broader than:

```text
prefectural_jinjacho_full_enumeration_candidate
```

because admission semantics are "accepted official source + full enumeration".

The exact source type remains independently recorded as Source provenance.

## 5. Required admission conditions

An `nsrc-*` Candidate may use:

```text
candidate_reason
= official_source_full_enumeration_candidate
```

only when its upstream extraction record establishes:

1. accepted official source;
2. full-enumeration acquisition scope;
3. deterministic source traversal / source_position;
4. frozen source snapshot or equivalent reproducible capture;
5. Candidate Extraction contract passage to the handoff stage.

This reason must not be used for:

- popularity / ranking discovery;
- manually curated one-off candidates;
- partial source acquisition;
- inferred candidates;
- model-generated candidates;
- search-engine snippets without accepted Source provenance.

## 6. H001 assignment

The following five H001 Candidate Registry rows will explicitly carry this reason when G0 registration is implemented:

| candidate_id | candidate_name | candidate_reason |
|---|---|---|
| nsrc-000001 | 相吉神社 | official_source_full_enumeration_candidate |
| nsrc-000002 | 青澤神社 | official_source_full_enumeration_candidate |
| nsrc-000003 | 蒼柴神社 | official_source_full_enumeration_candidate |
| nsrc-000004 | 青海神社 | official_source_full_enumeration_candidate |
| nsrc-000005 | 青山稲荷神社 | official_source_full_enumeration_candidate |

No Candidate Master write is performed by this decision.

## 7. Immutability

Once assigned, `candidate_reason` is admission provenance.

It does not change when lifecycle changes:

```text
DISCOVERED
-> BUILD_READY
-> IMPORTED
-> CORE_READY
```

Nor does it change if the Candidate moves to:

```text
HOLD
REVIEW
```

A later duplicate / alias finding also does not rewrite the admission reason.

## 8. Test implication

Current Wave0 test:

```text
candidate_defaults.candidate_reason
== historical_recovered_popularity_candidate
```

must remain.

The nationwide extension must add a separate assertion for `nsrc-*` rows:

```text
candidate_reason
== official_source_full_enumeration_candidate
```

Do not weaken the Wave0 historical default assertion.

## 9. Not decided here

N2 does not decide:

```text
N3 batch / handoff provenance representation
N4 status_reason_code policy
N5 Candidate Master test-accounting policy
schema_version bump
exact G0 registration payload beyond candidate_reason
```

## 10. Current state

```text
N1 candidate_id namespace = CLOSED
N2 candidate_reason       = CLOSED

H001 candidate_reason
= official_source_full_enumeration_candidate

G0_DATA_REGISTRATION
= NOT_EXECUTED

G1
= NOT_EXECUTED

G2
= NOT_EXECUTED
```

## 11. STOP

Do not register H001 rows until N3-N5 and the additive Candidate Master contract extension are closed.
