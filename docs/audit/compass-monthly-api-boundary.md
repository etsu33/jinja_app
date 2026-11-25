# Compass Monthly API Boundary Audit

> Status: CONFIRMED
>
> Scope: `POST /api/compass/recommendations/`
>
> Audit type: read-only contract / boundary audit
>
> Implementation changes: none
>
> Branch: `audit/compass-monthly-api-boundary`

## 1. Purpose

This audit defines the current public HTTP boundary of the Monthly Compass API.

The goals are to:

- distinguish the internal Shared Recommendation object from the Compass public response
- identify the fields actually consumed by the current Compass Web frontend
- define a minimal Compass Monthly Public Contract v1
- prevent internal, debug, ranking, or future experimental fields from leaking automatically
- define regression-test requirements for that boundary
- verify the current generated OpenAPI coverage

This audit does not change Recommendation Authority, ranking, Meaning, Compass direction
calculation, candidate selection, or frontend behavior.

---

## 2. Source of Truth

Current API contract decisions in this audit are based on the repository's active
contract-governance rule:

```text
Django URL routing
+ View implementation
+ Serializer / explicit schema implementation
+ Backend tests
+ observed runtime response
        ↓
current implementation contract
```

Generated or manually maintained OpenAPI files are not treated as stronger authorities
than the runtime implementation.

For Compass Monthly specifically, the primary implementation sources are:

```text
backend/temples/api/urls.py
backend/temples/api_views_compass.py
backend/temples/services/compass_recommendation_orchestrator.py
backend/temples/services/concierge_chat*.py
backend/temples/tests/api/test_compass_recommendations_api.py

apps/web/src/features/compass/types.ts
apps/web/src/features/compass/CompassClient.tsx
apps/web/src/features/compass/components/CompassRecommendationsSection.tsx
apps/web/src/features/compass/resolveCompassSupplementaryFactText.ts
```

---

## 3. Current Request Path

Current Monthly Compass request flow:

```text
CompassClient
    ↓
POST /api/compass/recommendations
    ↓
Next.js BFF
apps/web/src/app/api/compass/recommendations/route.ts
    ↓
raw request body relay
    ↓
POST /api/compass/recommendations/
    ↓
CompassRecommendationsView
    ↓
build_compass_direction_runtime()
    ↓
get_compass_recommendations()
    ↓
Shared Recommendation
    ↓
HTTP response
```

The Web BFF does not independently reshape the Compass request or response.

Therefore the effective public API boundary currently exists in
`CompassRecommendationsView`.

---

## 4. Current Request Input

`CompassRecommendationsView` currently reads the following request keys:

```text
purpose
birthdate
target_date
origin
```

Current normalization behavior:

```text
purpose
→ string
→ stripped
→ empty string when absent

birthdate
→ string
→ stripped
→ None when absent / empty

target_date
→ string
→ stripped
→ None when absent / empty

origin
→ accepted only when it is a mapping/dict
→ otherwise None
```

The current Web client submits:

```text
purpose
birthdate
origin
```

and does not currently submit `target_date`.

This audit does not redefine request validation behavior.
Request serialization / validation hardening may be added as part of the OpenAPI
remediation, but must preserve the existing runtime semantics unless separately approved.

---

## 5. Current Top-Level Response Boundary

Unlike each recommendation item, the current top-level response is already manually
constructed by `CompassRecommendationsView`.

Current structured result keys are:

```text
state
purpose
direction_context
recommendation_instance_id
recommendations
distance_stage_km
direction_candidate_count
distance_candidate_count
```

These fields form the Current Monthly top-level Public Contract v1.

`recommendation_instance_id` is generated once per request and is the canonical
recommendation-generation identity for the response.

### HTTP behavior

Current behavior is:

```text
invalid_purpose
→ HTTP 400

other structured domain result states
→ HTTP 200

unexpected exception
→ HTTP 500
→ {"state": "error"}
```

This audit does not change those HTTP semantics.

---

## 6. Current Direction Context Contract

When `direction_context` is present, the current public fields are:

```text
targetDate
targetYear
solarMonthIndex
referenceDirections
calculationMethod
note
```

Current calculation methods observed in the contract are:

```text
annual_monthly_kyusei_v1
monthly_kyusei_v1
```

`direction_context` is Runtime data.

It is not Recommendation evidence, persisted Meaning, or Weekly Presentation state.

---

## 7. G4 — Monthly recommendation item boundary is not explicit

### Status

**CONFIRMED**

### Current behavior

`CompassRecommendationsView` receives the recommendation dictionaries returned by
`get_compass_recommendations()` and currently exposes each recommendation by spreading
the source dictionary directly into the HTTP response, then appending
`recommendation_instance_id`.

Conceptually:

```text
Shared Recommendation dict
        ↓
{**recommendation, recommendation_instance_id}
        ↓
Compass Monthly HTTP response
```

The top-level Compass response itself is manually bounded, but each item in
`recommendations[]` is not.

A runtime success-path inspection observed **49 top-level fields** on a single
recommendation item.

This observed 49-field shape is a success-path observation, not an exhaustive union
of every possible field under all data conditions.

### Confirmed leakage

The observed response includes fields that are clearly internal, ranking-related,
debug-oriented, or otherwise not consumed by the current Compass frontend, including:

```text
_explanation_payload
_prefilter_debug
_primary_reason_label
_primary_reason_source
_reason_facts
_score_total
breakdown_detail
score_v2
popular_score
rank_comparison
rank_explanation
recommendation_reason_quality
```

The current Compass frontend only depends on a substantially smaller subset of the
recommendation object.

### Current Compass frontend dependencies

The current Compass UI directly consumes the following recommendation-level data:

```text
shrine_id
id
name
address
distance_m
reason
breakdown.matched_need_tags
reason_facts[].type
reason_facts[].label
```

`recommendations[].recommendation_instance_id` is not used as the frontend source of
truth, but is retained as a compatibility alias. The canonical value is the
top-level `response.recommendation_instance_id`.

### Public Contract v1 decision

The Compass Monthly recommendation item public allowlist is fixed to these
top-level fields:

```text
shrine_id
id
name
address
distance_m
reason
recommendation_instance_id
breakdown
reason_facts
```

Nested public subsets are limited to:

```text
breakdown.matched_need_tags

reason_facts[].type
reason_facts[].label
```

All other fields are outside the Compass Monthly Public Contract v1.

### Boundary rule

The remediation must use an **explicit allowlist / projection**, not a denylist.

Adding a new field to Shared Recommendation must not automatically expose that field
through the Compass Monthly API.

The Compass projection must not:

- recalculate ranking
- recalculate score
- regenerate recommendation reasons
- create new Meaning
- mutate the source recommendation dictionary
- change recommendation order or count

This is an HTTP / Presentation boundary hardening task only.

---

## 8. Frontend Consumer Audit

The current Compass Web frontend does not consume the complete raw recommendation
dictionary.

The currently required recommendation data is:

```text
shrine_id
id
name
address
distance_m
reason
breakdown.matched_need_tags
reason_facts[].type
reason_facts[].label
```

These fields support:

- identity / navigation
- card title
- address display
- distance display
- recommendation reason
- purpose-match supplementary presentation
- history-theme supplementary presentation

The frontend does not currently require ranking scores, debug state, Recommendation V4
detail objects, Knowledge payloads, astrology internals, or other Shared Recommendation
fields in order to render the Monthly Compass result.

### recommendation_instance_id

The canonical identity is:

```text
response.recommendation_instance_id
```

The current item-level copy:

```text
recommendations[].recommendation_instance_id
```

is retained in Public Contract v1 as a compatibility alias.

It must equal the top-level canonical value.

New Compass frontend code must not use the item-level alias as a new source of truth.

---

## 9. Compass Monthly Public Contract v1

### 9.1 Top-level response

The allowed top-level structured response fields are:

```text
state
purpose
direction_context
recommendation_instance_id
recommendations
distance_stage_km
direction_candidate_count
distance_candidate_count
```

### 9.2 Recommendation item

A recommendation item may expose only these top-level keys:

```text
shrine_id
id
name
address
distance_m
reason
recommendation_instance_id
breakdown
reason_facts
```

This is an allowlist.

It does not mean that every recommendation must always contain all nine fields.

The invariant is:

```text
actual recommendation keys
⊆
Compass Monthly Public Allowlist v1
```

### 9.3 breakdown

The only public nested field is:

```text
breakdown.matched_need_tags
```

No other ranking, score, signal, debug, or derived breakdown field is part of the
Compass Monthly Public Contract v1.

### 9.4 reason_facts

The only public fields for each item are:

```text
type
label
```

Other existing properties such as score, evidence, `label_ja`, `is_primary`, or future
internal metadata are outside this contract.

---

## 10. Public Projection / Allowlist Specification

The Monthly HTTP boundary must explicitly project the Shared Recommendation object into
the Compass public shape.

Required flow:

```text
Shared Recommendation
        ↓
Compass Monthly Public Projection
        ↓
explicit top-level allowlist
        ↓
explicit nested allowlists
        ↓
recommendation_instance_id compatibility alias
        ↓
HTTP response
```

A denylist implementation is not acceptable.

For example, the implementation must not work by removing known keys such as:

```text
_score_total
_prefilter_debug
breakdown_detail
```

because a future internal field would then be exposed automatically.

Instead, only Public Contract v1 fields may be selected.

### Projection properties

The projection must be deterministic and must not perform domain decisions.

It must not:

- recalculate Recommendation
- recalculate ranking
- recalculate score
- change candidate order
- change candidate count
- generate new reason copy
- generate Meaning
- invoke LLM
- query the database
- mutate the Shared Recommendation source object

---

## 11. Fail-Safe Projection Rules

Missing internal data must not be replaced with newly inferred domain data.

Expected behavior:

```text
public source field exists
→ copy it without semantic reinterpretation

public source field absent
→ do not invent a replacement solely for the projection

breakdown is not a mapping
→ do not expose raw breakdown content

matched_need_tags is not the expected collection shape
→ do not expose raw nested content

reason_facts is not a list
→ do not expose raw reason_facts content

reason_facts contains a non-object item
→ do not expose that raw item
```

`recommendation_instance_id` is the exception because it is already generated by the
HTTP View as request-level transport / analytics metadata.

---

## 12. Response Shape Regression Test Contract

The implementation PR must protect the public boundary at two levels:

```text
Public Projection unit tests
+
Compass Monthly HTTP API tests
```

### Required-field preservation

When the source recommendation contains all Public Contract v1 data, projection must
preserve:

```text
shrine_id
id
name
address
distance_m
reason
recommendation_instance_id
breakdown.matched_need_tags
reason_facts[].type
reason_facts[].label
```

### Internal-field non-leak

Tests must inject known internal fields such as:

```text
_prefilter_debug
_score_total
_reason_facts
_explanation_payload
breakdown_detail
score_v2
recommendation_reason_quality
recommendation_reason_v4_detail
```

and verify that they are absent from the Compass HTTP response.

### Unknown-field non-leak

Tests must also inject fields unknown to the production implementation, for example:

```text
future_internal_field
new_experiment_score
future_debug_payload
```

and verify that they are not exposed.

This test is required to prove that the implementation is a true allowlist rather than
a denylist.

### Nested boundary

`breakdown` must expose only:

```text
matched_need_tags
```

`reason_facts[]` must expose only:

```text
type
label
```

### recommendation_instance_id consistency

For every returned recommendation:

```text
recommendations[n].recommendation_instance_id
==
response.recommendation_instance_id
```

The top-level value remains canonical.

---

## 13. G5 — OpenAPI path exists but request/response contract is missing

### Status

**CONFIRMED — PATH PRESENT / CONTRACT MISSING**

### Generated OpenAPI result

The repository uses `drf-spectacular` as the machine-generatable OpenAPI path.

Running:

```text
make spectacular
```

generates `api_schema.yaml`.

The generated schema contains both Compass paths:

```text
/api/compass/recommendations/
/api/compass/weekly/
```

Therefore this is **not** a path-missing issue.

### Monthly generated shape

For:

```text
POST /api/compass/recommendations/
```

the generated OpenAPI currently contains endpoint metadata such as:

- `operationId`
- description
- tags
- security

but does not contain an explicit request body schema.

Its generated success response is:

```yaml
responses:
  '200':
    description: No response body
```

The generated schema also does not describe the actual Monthly `400` and `500`
response contracts.

### drf-spectacular diagnostic

Schema generation reports:

```text
Error [CompassRecommendationsView]: unable to guess serializer.
This is graceful fallback handling for APIViews.
...
Ignoring view for now.
```

The same serializer inference problem is also present on `CompassWeeklyView`.

### Root cause

`CompassRecommendationsView` currently uses:

```text
APIView
+ direct request.data parsing
+ manually constructed Response(dict)
+ no serializer_class
+ no explicit @extend_schema request/response contract
```

As a result, drf-spectacular can register the routed path, but cannot derive the real
request / response schema.

### Classification

```text
PATH
→ PRESENT

REQUEST CONTRACT
→ MISSING

200 RESPONSE BODY SCHEMA
→ MISSING

400 RESPONSE CONTRACT
→ MISSING

500 RESPONSE CONTRACT
→ MISSING
```

This is classified as:

**PATH PRESENT / CONTRACT MISSING**

rather than `PATH MISSING` or `SCHEMA DRIFT`.

### Relationship to G4

G4 and G5 describe the same missing public boundary from two sides:

```text
G4
Shared Recommendation raw dictionary is exposed too broadly at runtime

G5
Generated OpenAPI cannot describe a stable Compass request/response contract
```

The intended remediation is therefore:

```text
Compass Public Contract v1
        ↓
explicit recommendation projection / allowlist
        ↓
response-shape regression tests
        ↓
explicit OpenAPI request/response schema
```

### Scope boundary

The Monthly remediation must not automatically expand into unrelated OpenAPI cleanup.

`CompassWeeklyView` has the same OpenAPI inference problem, but Weekly remediation is
tracked separately from the Monthly boundary implementation.

Other unrelated APIView schema-generation errors reported by `make spectacular` are
also outside this audit's implementation scope.

---

## 14. OpenAPI Remediation Contract

The Monthly implementation PR must make the real API contract representable by
drf-spectacular.

After remediation, generated OpenAPI must describe:

```text
POST /api/compass/recommendations/

request
├─ purpose
├─ birthdate
├─ target_date
└─ origin

responses
├─ 200 structured Compass result
├─ 400 invalid-purpose result
└─ 500 error result
```

The generated success response must describe the Compass Monthly Public Contract v1,
including the bounded recommendation item structure.

The implementation may use explicit DRF serializers, `@extend_schema`, or another
repository-consistent drf-spectacular mechanism.

The implementation choice must not change domain behavior merely to satisfy schema
generation.

---

## 15. Scope Boundaries / Non-Goals

This audit does not authorize changes to:

```text
Recommendation candidate selection
Recommendation ranking
Recommendation scoring
Compass direction calculation
distance-stage behavior
Meaning
history_theme taxonomy
Recommendation Reason generation
Recommendation Reason V4 generation
LLM behavior
Free / Premium gating
Analytics event semantics
Weekly Presentation logic
Weekly snapshot persistence
DB schema
Compass frontend UX
Concierge public response contract
```

The same OpenAPI inference issue exists on `CompassWeeklyView`, but Weekly remediation
is outside the Monthly implementation scope.

Other APIViews reported by `make spectacular` are also unrelated to this audit.

---

## 16. Implementation Gate

Implementation may begin only against the contract fixed by this audit.

The implementation PR must preserve:

```text
same Recommendation Authority
same recommendation order
same recommendation count
same Compass result states
same HTTP status behavior
same canonical recommendation_instance_id semantics
same frontend-visible Monthly behavior
```

The intended code change is limited to:

```text
Compass Monthly public projection
+
response/request schema representation
+
regression tests
```

If implementation requires changing Ranking, Meaning, Recommendation Authority, or
Weekly behavior, the task must stop and return to Mother Ship review.

---

## 17. Acceptance Criteria

The implementation is accepted when all of the following are simultaneously true:

1. Monthly recommendation items cannot expose keys outside Public Contract v1.
2. `breakdown` exposes only `matched_need_tags`.
3. `reason_facts` items expose only `type` and `label`.
4. Known internal/debug fields do not leak.
5. Unknown future fields do not leak.
6. Existing public values are not semantically rewritten by the projection.
7. item-level `recommendation_instance_id` equals the canonical top-level value.
8. Existing Monthly result states and HTTP statuses remain unchanged.
9. Existing Monthly frontend behavior remains unchanged.
10. `make spectacular` generates a real Monthly request schema.
11. `make spectacular` generates a real Monthly response schema.
12. Generated OpenAPI no longer reports `CompassRecommendationsView` as unable to determine its API contract.
13. Weekly Compass behavior is unchanged.
14. Concierge behavior is unchanged.
15. Relevant Backend and Web regression tests pass.

---

## 18. Recommended Implementation Split

This audit is completed as a documentation-only PR.

The subsequent implementation should be a separate feature/fix PR.

Suggested implementation scope:

1. Add Compass Monthly public projection boundary.
2. Add nested allowlists.
3. Add projection unit tests.
4. Add Monthly API response-shape regression tests.
5. Add explicit Monthly OpenAPI request / response schema.
6. Run existing Compass / Concierge regression suites.
7. Run `make spectacular` and verify the Monthly generated contract.

Weekly OpenAPI remediation should remain a separate task.

---

## 19. Audit Conclusion

The Monthly Compass endpoint is operational, but its public recommendation-item
boundary is currently wider than the frontend contract requires.

At runtime, Shared Recommendation dictionaries can cross directly into the Compass
response, allowing internal and debug fields to become externally visible.

At the documentation/schema layer, the endpoint path is present in generated OpenAPI,
but its request and response body contracts are not represented because
drf-spectacular cannot infer the bare `APIView` structure.

The required remediation is therefore a boundary hardening change rather than a
Recommendation redesign:

```text
Shared Recommendation
        ↓
explicit Compass Public Contract v1
        ↓
allowlisted Public Projection
        ↓
regression-protected HTTP response
        ↓
explicit generated OpenAPI contract
```

No Ranking, Meaning, Direction Runtime, or Recommendation Authority change is required
by this audit.
