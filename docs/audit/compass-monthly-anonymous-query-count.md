# Compass Monthly Anonymous Query Count Audit

## 1. Purpose

Measure the actual SQL query count for one successful anonymous Monthly Compass request and record the observed baseline without changing production behavior.

Target endpoint:

```text
POST /api/compass/recommendations/
```

This audit is measurement-only. It does not change Recommendation, Ranking, Compass direction logic, quota, billing, schema, frontend behavior, or production data.

## 2. Measurement Environment

- Tested commit: `aaf66c6bd7ad6c52cbdd6ef473060a1c8a878bcf`
- Database: PostgreSQL 16.13
- Request type: anonymous
- LLM: disabled
- Fixture setup: outside `CaptureQueriesContext`
- Measured scope: one anonymous POST only
- Result state: `recommendation_success`
- HTTP status: `200`
- Repeated runs: 3
- Observed query count: 6 on all 3 runs

Existing fixture inputs:

```text
purpose = career
origin = {"lat": 35.0, "lng": 135.0}
birthdate = 1984-05-15
target_date = 2026-09-15
```

The Shrine fixture contains usable Deity knowledge and no ShrineHistory row.

## 3. Result

```text
MONTHLY_ANONYMOUS_QUERY_COUNT=6

HTTP_STATUS=200
STATE=recommendation_success

SELECT=6
INSERT=0
UPDATE=0
DELETE=0

AUTH_DB_QUERY_COUNT=0
BILLING_DB_QUERY_COUNT=0

STATIC_ESTIMATE=7
ACTUAL=6
DELTA=-1
```

## 4. Query Breakdown

| # | Operation | Primary table / responsibility |
|---|---|---|
| 1 | SELECT | `temples_shrine` + `place_ref` LEFT JOIN: candidate retrieval via `build_chat_candidates_with_eligibility`; ordered by `popular_score`; `LIMIT 300` |
| 2 | SELECT | `temples_goriyakutag` + `temples_shrine_goriyaku_tags`: candidate `prefetch_related("goriyaku_tags")` |
| 3 | SELECT | `temples_shrinedeity`: fact-ready Deity knowledge retrieval |
| 4 | SELECT | `temples_shrineknowledgesource` + `temples_shrinedeity_sources`: Deity Source prefetch |
| 5 | SELECT | `temples_shrinehistory`: fact-ready History knowledge retrieval; returns zero rows for this fixture |
| 6 | SELECT | `temples_goriyakutag`: Purpose GID label lookup used by Recommendation reason construction |

No SQL statement in the captured request references `auth_user`, `UserProfile`, billing/subscription tables, quota tables, session tables, or token blacklist tables.

## 5. ROOT_CAUSE_OF_DELTA

```text
STATIC_ESTIMATE=7
ACTUAL=6
DELTA=-1

ROOT_CAUSE_OF_DELTA:
The static estimate assumed that ShrineHistory source prefetch would execute.

In the measured fixture, the Shrine has usable Deity knowledge but no ShrineHistory rows.
The ShrineHistory candidate SELECT is still executed, but it returns zero rows.
Because there are no parent ShrineHistory objects to prefetch from, Django does not issue
the additional ShrineHistory.sources prefetch query.

Therefore:

- Shrine candidate SELECT: 1
- GoriyakuTag prefetch: 1
- ShrineDeity SELECT: 1
- ShrineDeity.sources prefetch: 1
- ShrineHistory SELECT: 1
- Purpose GoriyakuTag label lookup: 1
- ShrineHistory.sources prefetch: 0

Total: 6 SQL

The missing seventh query is therefore the History Sources prefetch query, not an authentication query.

Authentication is a separate delta:
an authenticated Monthly request may add an auth_user lookup, while the anonymous request
does not. That difference must not be used to explain the anonymous 7 -> 6 static-estimate delta.
```

## 6. N+1 Observation

The single-Shrine measurement by itself is not sufficient to establish absence of N+1 behavior.

A separate scale measurement on the same tested commit increased Shrine data from 1 row to 310 rows, exceeding the effective candidate pool cap of 300, while Monthly query count remained 6.

The Knowledge retrieval path uses batched `IN (...)` queries for Deity and History data instead of issuing one query per Shrine.

Classification:

```text
N_PLUS_ONE_OBSERVED=NO
```

This classification is supported by the separate scale measurement, not by the one-Shrine request alone.

## 7. Current Baseline

For the measured fixture and anonymous successful Monthly Compass path:

```text
MONTHLY_ANONYMOUS_BASELINE=6 SQL
```

This is an observed baseline, not yet a hard query-budget assertion.

No exact `assertNumQueries(6)` or equivalent regression gate is introduced by this audit. A stable query budget should only be pinned after Weekly MISS/HIT and authenticated paths are measured and fixture-sensitive query behavior is understood.

## 8. Next Measurement Gate

Next target:

```text
Weekly Anonymous Snapshot MISS
```

After that:

```text
Weekly Anonymous Snapshot HIT
```

These measurements are required before calculating the observed SQL cost of one complete successful Compass UI action:

```text
Monthly + Weekly MISS/HIT
```
