# Compass Monthly — `shrine_id` Presence Audit (F-2)

## Status

- Status: `AUDITED` + `DECISION_RECORDED`
- Recorded at: `2026-09-23`
- Updated at: `2026-09-23` — `R-2` Mother Ship decision recorded (§10)
- Type: contract-verification audit, now also carrying the `R-2` contract decision.
  The audit body (§1–§9) is **read-only history**; §10 is the later decision.
- Follow-up: `F-2` from `docs/audit/shrine-identity-compass-concierge-contract.md` §8
- Scope: Compass **Monthly** only — `POST /api/compass/recommendations/`
- Weekly Compass: out of scope (no shared implementation affects the Monthly guarantee — §2.7)
- Runtime / schema / serializer / type / projection change: `NONE`
- Compass `id` fallback: **NOT removed** (that is `F-1`)

本書は `#2948` を複製しない。identity contract 本体は
`docs/audit/shrine-identity-compass-concierge-contract.md` が正本であり、本書は
その `F-2` 一問だけを検証する。

## 1. Final Classification

> 以下は **F-2 記録時点**（`2026-09-23`, PR #2950）の状態である。`R-1` 完了後の
> 現在値は §10.4 を参照。本節は歴史的記録として書き換えない。

```text
COMPASS_SHRINE_ID_PRESENCE = PRODUCER_GUARANTEED_CONTRACT_OPTIONAL
```

```text
PRODUCER_SHRINE_ID_PRESENT            = YES
ORCHESTRATOR_PRESERVES_SHRINE_ID      = YES
PUBLIC_PROJECTION_PRESERVES_SHRINE_ID = YES   (preserves — but does not require)
OPENAPI_REQUIRES_SHRINE_ID            = NO
FRONTEND_TYPE_REQUIRES_SHRINE_ID      = NO
HTTP_REGRESSION_TEST_EXISTS           = NO
```

```text
F1_READY = NO
```

Runtime always emits `shrine_id` on the Monthly success path — observed, not assumed
(§4). But three contracts still describe it as optional, and one existing test
*actively asserts* that an item without `shrine_id` is valid projection output. The
fallback cannot be removed against a contract that permits its absence.

## 2. End-to-End Flow and Per-Boundary Guarantee

```text
[1] temples_shrine (Shrine.id = PK)
      │  GUARANTEE: primary key, non-null by definition
      ▼
[2] concierge_chat_candidates.build_chat_candidates_with_eligibility()
      │  L284-285   "id": s.id      "shrine_id": s.id
      │  GUARANTEE: STRONG — single emission site, both keys from one attribute,
      │             enforced by regression test (PR #2949, F-7)
      ▼
[3] concierge_chat.build_chat_recommendations(llm_enabled=False)
      │  L787 resolve_llm_route(...) -> concierge_chat_llm_route.py
      │       effective_llm_enabled=False -> else branch
      │       -> _seed_recs_from_candidates(prefiltered, size=12)
      │          concierge_chat_pool.py: {"recommendations": safe_candidates[:size]}
      │  L798 _ensure_pool_size(recs, candidates=...) -> fills from the SAME list
      │  _normalize_candidate_fields(): row = dict(c); 「既存キーは可能な限り保持する」
      │  GUARANTEE: STRONG — recommendation items ARE candidate dicts.
      │             No item is synthesized; no name-only item exists on this path.
      ▼
[4] compass_recommendation_orchestrator.get_compass_recommendations()
      │  L239 candidate_build = build_chat_candidates_with_eligibility(...)
      │  L328 recs = build_chat_recommendations(..., llm_enabled=False)
      │  L340 recommendations = [r for r in recs["recommendations"] if isinstance(r, dict)]
      │  L103-104 docstring: "untouched ... does not reshape, flatten"
      │  GUARANTEE: STRONG — filter-only (direction + distance rings). No synthesis.
      ▼
[5] compass_public_projection.project_compass_recommendation()
      │  L110-111  {key: source[key] for key in COMPASS_MONTHLY_PUBLIC_ITEM_FIELDS
      │                                if key in source}
      │  GUARANTEE: WEAK — copy-if-present. shrine_id is preserved when the
      │             source has it, and silently absent when it does not.
      ▼
[6] CompassRecommendationsView  (api_views_compass.py L100)
      │  L68 comment: 「serializerはOpenAPI記述専用」
      │  GUARANTEE: NONE — the response is not serializer-validated.
      ▼
[7] CompassRecommendationItemSerializer (serializers/compass.py L121-122)
      │  shrine_id = IntegerField(required=False, allow_null=True)
      │  id        = IntegerField(required=False, allow_null=True)
      │  GUARANTEE: NONE — documents shrine_id as optional AND nullable,
      │             and is documentation-only per [6].
      ▼
[8] apps/web/src/features/compass/types.ts L85-86
      │  shrine_id?: number | string | null;
      │  id?:        number | string | null;
      │  GUARANTEE: NONE — optional and nullable.
      ▼
[9] CompassRecommendationsSection.tsx L58
         const shrineId = rec.shrine_id ?? rec.id;   <- the F-1 fallback
```

```text
STRONG guarantee : [1] [2] [3] [4]
WEAK  guarantee  : [5]
NO    guarantee  : [6] [7] [8]
```

### 2.7 Weekly Compass scope check

`weekly_compass_service.py` L165 also calls `get_compass_recommendations()`, so it
shares boundaries [2]–[4]. It does **not** share [5]–[9]: Weekly has its own
presentation path and does not pass through `compass_public_projection` or
`CompassRecommendationItemSerializer`. The Monthly guarantee is therefore unaffected
by Weekly, and Weekly is not audited here.

## 3. Required Questions

### A. Producer guarantee

```text
Q: Does every eligible registered Shrine candidate contain shrine_id?
A: YES. concierge_chat_candidates.py L284-285 is the single emission site and sets
   "id" and "shrine_id" from the same `s.id`. PR #2949 pins this with a regression
   test asserting equality against the persisted PK.

Q: Can build_chat_recommendations() remove, replace, null, or omit shrine_id?
A: NO on the Compass path. With llm_enabled=False the recommendations ARE the
   candidate dicts (_seed_recs_from_candidates -> safe_candidates[:size]).
   _normalize_candidate_fields() copies the dict and documents that existing keys
   are preserved; it normalizes lat / lng / distance_m / name / place_id / address
   only. _attach_rank_comparison() mutates items in place, adding rank_explanation.
   Nothing rebuilds an item from scratch.

Q: Can any recommendation_success item originate from a source that did not pass
   through the shared Shrine candidate producer?
A: NO on Compass Monthly. get_compass_recommendations() builds its own candidate
   pool (L239) and passes only distance_filtered_candidates to
   build_chat_recommendations (L328). There is no user-supplied candidate merge on
   this path — unlike Concierge, whose api_views_concierge.py merges user
   candidates through _build_chat_candidates_pipeline.

Q: Can any fallback / pool-fill / enrichment path create a recommendation without
   shrine_id?
A: NO on this path. _ensure_pool_size() fills exclusively from the `candidates`
   argument — the same shared-producer list. The LLM branch, which is the only
   source that could return name-only items, is unreachable: Compass passes
   llm_enabled=False (orchestrator L328 region), and resolve_llm_route() additionally
   requires settings.CONCIERGE_USE_LLM. Both gates must be true; Compass fails the
   first unconditionally.
```

```text
PRODUCER_SHRINE_ID_PRESENT = YES
```

### B. Orchestrator guarantee

```text
Q: Does get_compass_recommendations() ever synthesize or reshape recommendation items?
A: NO. Its own docstring (L103-104) states the recommendations are "the untouched
   recommendation dicts returned by build_chat_recommendations() -- this module does
   not reshape, flatten". Compass-specific logic is filtering only:
   filter_candidates_by_direction() and _apply_compass_distance_stage()
   (15 / 30 / 60 km rings) both select from the list; neither constructs an item.

Q: Can recommendation_success contain an item not backed by Shrine.id?
A: NOT ON ANY CURRENTLY REACHABLE PATH. Every item is a shared-producer candidate
   dict whose shrine_id is the persisted Shrine PK.
```

```text
ORCHESTRATOR_PRESERVES_SHRINE_ID = YES
```

### C. Public projection guarantee

```text
compass_public_projection.py L110-111

    projected: dict[str, Any] = {
        key: source[key] for key in COMPASS_MONTHLY_PUBLIC_ITEM_FIELDS if key in source
    }
```

`shrine_id` is the first entry of `COMPASS_MONTHLY_PUBLIC_ITEM_FIELDS` (L32), so it is
copied **whenever the source has it** — and omitted entirely when it does not. There
is no required-field check, no raise, no default.

The module docstring makes the optionality explicit rather than incidental:

```text
「実際のitemはこの部分集合であればよく、全keyを持つ必要はない（Section 9.2）」
「公開対象のsource fieldが存在しない場合、代わりの値をでっち上げない」
```

The second line is a deliberate fail-safe: inventing a `shrine_id` would be worse
than omitting it. The projection is doing the right thing; it simply is not the layer
that guarantees presence.

```text
PROJECTION_SEMANTICS = PRESENT_BY_CURRENT_PRODUCER_ONLY
NOT                  = CONTRACTUALLY_REQUIRED
```

### D. OpenAPI contract

```text
backend/temples/api/serializers/compass.py L121-122
    shrine_id = serializers.IntegerField(required=False, allow_null=True)
    id        = serializers.IntegerField(required=False, allow_null=True)
```

Two independent reasons this is not a guarantee:

1. `required=False, allow_null=True` documents `shrine_id` as both omittable and
   nullable. The class docstring states the allowlist "であって「全件が全fieldを持つ」
   という意味ではない".
2. The serializer never validates the response. `api_views_compass.py` L68 records:
   「serializerはOpenAPI記述専用。ここでの入力解釈は従来どおり手動で行う」. The
   response body is the projection's output, returned directly.

```text
OPENAPI_REQUIRES_SHRINE_ID = NO
```

### E. Frontend contract

```text
apps/web/src/features/compass/types.ts L85-86
    shrine_id?: number | string | null;
    id?:        number | string | null;
```

Optional and nullable. TypeScript will not reject an item lacking `shrine_id`, and
`?? ` in `CompassRecommendationsSection.tsx` L58 is the type-correct response to that
declaration. Removing the fallback while the type stays optional would leave
`shrineId` typed `number | string | null | undefined` and pass `undefined` into
`buildShrineHref`.

```text
FRONTEND_TYPE_REQUIRES_SHRINE_ID = NO
```

### F. Tests

Compass Monthly test files inspected:

```text
backend/temples/tests/api/test_compass_recommendations_api.py
backend/temples/tests/api/test_compass_public_projection.py
backend/temples/tests/services/test_compass_recommendation_orchestrator.py
backend/temples/tests/services/test_compass_direction_filter.py
backend/temples/tests/services/test_compass_runtime.py
apps/web/src/features/compass/components/__tests__/CompassRecommendationsSection.test.tsx
apps/web/src/features/compass/__tests__/CompassClient*.test.tsx
```

What exists:

```text
test_compass_recommendations_api.py L538   assert rec["shrine_id"] == 100
   -> source is a hand-built stub; get_compass_recommendations is PATCHED
      (L531-534). Proves projection preserves a supplied shrine_id, not that
      the real path produces one.

test_compass_public_projection.py L78, L206
   -> sources are literal dicts already containing shrine_id. Same limitation.

test_compass_recommendation_orchestrator.py L782-796
   -> candidates are hand-built dicts with shrine_id. Distance-stage tests.

CompassRecommendationsSection.test.tsx
   -> every fixture sets shrine_id. No case omits it, so the `?? rec.id`
      fallback is never exercised by a test.
```

The DB-backed HTTP test that *could* have carried the assertion:

```text
test_compass_recommendations_api.py L51-79
    @pytest.mark.django_db
    def test_valid_request_returns_recommendation_success(client, shrine_factory)

    asserts: status_code, state, purpose, direction_context.referenceDirections,
             rec["name"], recommendation_instance_id
    does NOT assert: shrine_id presence, non-nullness, or equality to Shrine.id
```

A test actively asserting the **opposite** guarantee:

```text
test_compass_public_projection.py L133-139
    def test_absent_public_fields_are_not_invented():
        projected = project_compass_recommendation(
            {"name": "名前だけの神社"}, recommendation_instance_id=INSTANCE_ID
        )
        assert projected == {"name": "名前だけの神社",
                             "recommendation_instance_id": INSTANCE_ID}
```

This asserts that a recommendation with **no `shrine_id`** is valid projection output.
It is a correct fail-safe test, and it is also a committed statement that the public
contract tolerates a missing `shrine_id`.

Is F-7 (PR #2949) sufficient? **No.** F-7 asserts the invariant at the *service*
boundary (`build_chat_candidates_with_eligibility` / `build_chat_candidates`). It does
not exercise the projection, the view, or the HTTP response, which is exactly where
the optionality lives.

```text
HTTP_REGRESSION_TEST_EXISTS = NO
```

## 4. Runtime Observation (evidence, not inference)

The real Monthly success path was executed end-to-end against a throwaway
PostgreSQL test database, through the Django test client, with no repository change
and no stubbing of the orchestrator, projection, or view:

```text
POST /api/compass/recommendations/
  purpose=career  origin={35.0,135.0}  birthdate=1984-05-15  target_date=2026-09-15

status: 200   state: recommendation_success
persisted Shrine.id: 1   |   rec count: 1
  [0] keys = ['address', 'breakdown', 'distance_m', 'id', 'name', 'reason',
              'reason_facts', 'recommendation_instance_id', 'shrine_id']
      shrine_id=1   id=1   name='北西の神社'

ALL shrine_id non-null : True
ALL shrine_id == id    : True
shrine_id == Shrine.id : True
```

This confirms boundaries [1]–[6] behave as traced. It is **one observed payload** and
is recorded as corroboration of the code trace, not as the guarantee itself — a
sample payload containing `shrine_id` is explicitly not a basis for `F1_READY = YES`.

## 5. Missing Guarantees

```text
M-1  Public projection does not require shrine_id (copy-if-present, L110-111),
     and test_compass_public_projection.py L133 asserts an item without it is
     valid output.

M-2  CompassRecommendationItemSerializer declares required=False, allow_null=True,
     and is documentation-only — it validates nothing at runtime.

M-3  types.ts declares shrine_id?: number | string | null — optional and nullable.

M-4  No test asserts, on a DB-backed HTTP success response, that every
     recommendation_success item has a non-null shrine_id equal to Shrine.id.
     The DB-backed test exists (L51-79) but omits the assertion.
```

## 6. F-1 Gate

```text
F1_READY = NO

F1_BLOCKER =
  The public Compass Monthly contract does not require shrine_id at any enforced
  layer. Runtime currently always emits it, but projection (M-1), OpenAPI schema
  (M-2) and the frontend type (M-3) all declare it optional, one committed test
  asserts that an item without it is valid output (M-1), and no HTTP-boundary
  regression test pins its presence (M-4). Removing `rec.shrine_id ?? rec.id`
  would make the client depend on a guarantee nothing enforces.
```

## 7. Exact Minimal Remediation Required Before F-1

Recorded only. **None of this is performed by this audit**, per the F-2 scope rules
(do not change serializer, frontend type, or public projection).

```text
R-1  (test, no contract change — safest first step)
     Extend the existing DB-backed HTTP test
     test_compass_recommendations_api.py::test_valid_request_returns_recommendation_success
     with, for every item in body["recommendations"]:
         "shrine_id" in rec
         rec["shrine_id"] is not None
         rec["shrine_id"] == <persisted Shrine.id>
     Converts HTTP_REGRESSION_TEST_EXISTS to YES without touching any contract.
     -> DONE. PR #2951 added
        test_recommendation_success_items_carry_persisted_shrine_id.

R-2  (contract) Decide whether shrine_id becomes REQUIRED in the Compass Monthly
     Public Contract v1. This is a public-contract change and needs its own gate.
     It also governs the fate of `id`, which is in the same allowlist
     (compass_public_projection.py L32-33).
     -> RESOLVED. See §10. shrine_id = REQUIRED; `id` retained as a
        compatibility field and NOT removed by that decision.

R-3  (projection) Only if R-2 says required: decide the behavior when a source
     lacks shrine_id — raise, or drop the item. Note this interacts with
     test_absent_public_fields_are_not_invented (L133), whose current assertion
     would need to be re-scoped rather than deleted: the fail-safe it protects
     (never invent a value) must survive.

R-4  (schema) Only after R-2: serializers/compass.py L121 required=True,
     allow_null=False.

R-5  (frontend) Only after R-2/R-4: types.ts L85 shrine_id: number | string
     (non-optional). F-1 then becomes a type-safe deletion rather than a
     behavioral bet.
```

Ordering constraint:

```text
R-1 may proceed immediately and independently.
R-2 gates R-3, R-4, R-5.
F-1 requires R-1 and R-5 at minimum.
```

Doing `F-1` with only `R-1` complete would still leave the frontend type optional and
the deletion unsound.

## 8. Required Statements

```text
1. The Compass `id` fallback was NOT removed.
2. `id` was NOT removed from the public API.
3. shrine_id was NOT made required.
4. No serializer change.
5. No TypeScript type change.
6. No public projection change.
7. No runtime, Recommendation, Ranking, schema, DB, or migration change.
8. No Canonical / Navigation Anchor change.
9. F-1 / F-3 / F-4 / F-5 / F-6 were not started.
10. The only committed change is this document.
```

## 9. STOP (F-2 audit)

```text
COMPASS_SHRINE_ID_PRESENCE = PRODUCER_GUARANTEED_CONTRACT_OPTIONAL
F1_READY                   = NO
NEXT                       = R-1 (test-only) then R-2 (contract gate)
```

`R-1` and `R-2` have since been completed. The current state is recorded in §10; this
section preserves the F-2 audit's own stopping point.

---

## 10. R-2 Mother Ship Decision Record

### 10.1 Status

```text
R-2_STATUS   = RESOLVED
R-2_DECISION = REQUIRE_SHRINE_ID_FOR_COMPASS_MONTHLY_SUCCESS_ITEMS
```

- Recorded at: `2026-09-23`
- Decision authority: Mother Ship
- Type: **contract decision record only**
- Implementation: `NOT_STARTED` — `R-3` / `R-4` / `R-5` are separate tasks
- Runtime / projection / serializer / TypeScript change by this record: `NONE`

本節は決定の記録であり、契約の実装ではない。§1–§9 の F-2 監査本体は当時の状態を
保持したまま書き換えていない。

### 10.2 Scope

```text
endpoint  = POST /api/compass/recommendations/
surface   = Compass MONTHLY only
condition = state == "recommendation_success"
subject   = recommendations[*]   (every item, not only index 0)
```

Out of scope for this decision:

```text
- Compass Weekly (separate presentation path — §2.7)
- non-success states (direction_zero_candidates / error / 400 responses)
- Concierge (its own identity handling is recorded in
  docs/audit/shrine-identity-compass-concierge-contract.md)
```

### 10.3 The contract

When `state = recommendation_success`, every item in `recommendations[*]` must satisfy:

```text
COMPASS_MONTHLY_SUCCESS_ITEM_IDENTITY_CONTRACT:
  shrine_id = REQUIRED
  shrine_id = NON_NULL
  shrine_id = Shrine.id
  id        = COMPATIBILITY_FIELD
  id        = NOT_IDENTITY_AUTHORITY
```

Identity authority, unchanged from `#2948`:

```text
SHRINE_IDENTITY_AUTHORITY = Shrine.id
PUBLIC_IDENTITY_KEY       = shrine_id
```

`shrine_id = Shrine.id` means the value must be the **persisted primary key of the
Shrine row the item refers to** — not a rank, list index, result-set ordinal, or the
primary key of a different row. A structurally valid integer that resolves to the
wrong Shrine violates this contract.

### 10.4 State after R-1, before R-3 / R-4 / R-5

```text
PRODUCER_SHRINE_ID_PRESENT            = YES
ORCHESTRATOR_PRESERVES_SHRINE_ID      = YES
PUBLIC_PROJECTION_PRESERVES_SHRINE_ID = YES   (preserves — still does not require)
HTTP_REGRESSION_TEST_EXISTS           = YES   <- changed by R-1 (PR #2951)
OPENAPI_REQUIRES_SHRINE_ID            = NO
FRONTEND_TYPE_REQUIRES_SHRINE_ID      = NO

COMPASS_SHRINE_ID_PRESENCE = PRODUCER_GUARANTEED_CONTRACT_OPTIONAL
F1_READY                   = NO
```

`R-2` records **what the contract must become**. It does not change any of the three
`NO` rows above — those are `R-3` / `R-4` / `R-5`. The classification therefore stays
`PRODUCER_GUARANTEED_CONTRACT_OPTIONAL` until those land.

### 10.5 Status of `id`

```text
id = COMPATIBILITY_FIELD
id = NOT_IDENTITY_AUTHORITY
id = NOT_REMOVED_BY_THIS_DECISION
```

`id` remains in `COMPASS_MONTHLY_PUBLIC_ITEM_FIELDS`
(`compass_public_projection.py` L32-33) and in
`CompassRecommendationItemSerializer` (`serializers/compass.py` L122). Removing it is
**not decided here** and is not implied by requiring `shrine_id`.

Consequence for consumers: once the contract is implemented, `shrine_id` is the only
field a client may treat as Shrine identity. `id` may continue to be emitted, but no
consumer may derive identity from it — which is what makes the `F-1` fallback
removable later.

### 10.6 Explicitly deferred to R-3

**Not decided by R-2.** What runtime must do if an impossible/invalid source item
reaches the projection without a usable `shrine_id`:

```text
OPEN (R-3):
  - raise
  - fail closed
  - drop the offending item
  - transform the result state
  - some combination, possibly differing by cause
```

Recording the constraint without choosing the behavior: `R-3` must not resolve this by
inventing a `shrine_id`. The projection's existing fail-safe — 「公開対象のsource
fieldが存在しない場合、代わりの値をでっち上げない」 — and the test that protects it,
`test_compass_public_projection.py::test_absent_public_fields_are_not_invented`
(L133), must survive `R-3` in **re-scoped** form rather than be deleted. Fabricating an
identity is worse than any of the options above.

Per the audited evidence (§3 A / §3 B), no currently reachable Monthly success path
can produce such an item; `R-3` is defining behavior for a state that is unreachable
today but not structurally prevented.

### 10.7 Implementation sequence

```text
R-1  DB-backed HTTP regression                          DONE      (PR #2951)
R-2  Contract decision                                  RESOLVED  (this section)

R-3  Public Projection enforcement                      NOT_STARTED
       + resolve the §10.6 behavior question
R-4  OpenAPI serializer required / non-null             NOT_STARTED
       serializers/compass.py L121
R-5  Frontend type non-optional                         NOT_STARTED
       apps/web/src/features/compass/types.ts L85

F-1  Remove the Compass navigation `id` fallback        BLOCKED
       CompassRecommendationsSection.tsx L58
       only after R-3 / R-4 / R-5 are complete AND validated
```

```text
ORDER      : R-3 -> R-4 -> R-5 -> F-1
F1_READY   = NO   (unchanged by this decision)
```

`F-1` remains blocked. Requiring `shrine_id` by decision does not make the client-side
fallback removable; only the implemented and validated `R-3` / `R-4` / `R-5` do.

### 10.8 Evidence basis

```text
PR #2948  Shrine.id = identity authority; shrine_id = public identity key
          docs/audit/shrine-identity-compass-concierge-contract.md
PR #2949  F-7 — shared candidate emission regression-protected:
          Shrine.id == candidate["shrine_id"] == candidate["id"]
PR #2950  F-2 — runtime preserves shrine_id end-to-end; public / schema /
          frontend contracts still optional -> PRODUCER_GUARANTEED_CONTRACT_OPTIONAL
PR #2951  R-1 — DB-backed HTTP regression: every observed recommendation_success
          item has a non-null shrine_id resolving to the correct persisted row
```

### 10.9 Required statements for R-2

```text
1.  compass_public_projection.py was NOT changed.
2.  CompassRecommendationItemSerializer was NOT changed.
3.  TypeScript types were NOT changed.
4.  `id` was NOT removed.
5.  The Compass navigation fallback was NOT removed.
6.  No runtime or API response behavior was changed.
7.  No Recommendation / Ranking change.
8.  No DB / schema / migration change.
9.  No Canonical / Navigation Anchor change.
10. R-3 / R-4 / R-5 / F-1 were NOT started.
11. The R-3 invalid-item behavior question is explicitly left OPEN (§10.6).
12. The only committed change is this document.
```

### 10.10 STOP

```text
R-2_STATUS = RESOLVED
IMPLEMENTATION = NOT_STARTED
NEXT = R-3 (Public Projection enforcement + §10.6 behavior decision)
```

Next action requires a Mother Ship instruction naming `R-3`.
