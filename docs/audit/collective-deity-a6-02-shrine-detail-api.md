# A6-02 Step 2 — Shrine Detail API `deity_collectives`

- Status: IMPLEMENTED (branch `feature/a6-02-collective-detail-api`) / Shrine Detail API connected
- Date: 2026-10-02
- Base: develop `2f0c0b5` (includes PR #3063)
- Admission authority (unchanged): `backend/temples/services/collective_runtime_selector.py`
  (`fetch_runtime_admitted_collectives`, A6-01)
- Representation (Step 1, unchanged): `ShrineDeityCollectiveSerializer`,
  `ShrineDeityCollectiveMembershipSerializer` in `backend/temples/api/serializers/shrine.py`
- Production write / activation: **NONE**

## 1. Step 2 scope

Expose A6-01 runtime-admitted deity Collectives in the Shrine Detail API as the
top-level field `deity_collectives`.

| In scope | Out of scope |
|---|---|
| `ShrineDetailSerializer.deity_collectives` | Source payloads for Collectives / Memberships |
| `ShrineViewSet.retrieve` calls the selector once | Web / Mobile UI |
| tests, query-count observation, this document | Recommendation / Compass / Concierge / Deep Dive |
| | Production activation (`activate_collective_runtime` apply) |
| | models, migrations, activation seed |

## 2. Responsibility boundary

```text
A6-01 selector  = the only admission authority (Evidence Gate, activation, member list,
                  Membership evidence, same-Shrine, ordering)
ShrineViewSet   = calls the selector once per detail request, passes the result
ShrineDetailSerializer.deity_collectives = representation only
```

The serializer:

- does not re-evaluate Evidence Gate or any admission condition
- does not read `Shrine.deity_collectives` (the model relation)
- does not sort Collectives or Memberships; A6-01 owns `(sort_order, id)` ordering
- infers no Pattern (A/B/C/D)

## 3. Data flow

```text
GET /api/shrines/{id}/
  -> ShrineViewSet.retrieve
       instance = self.get_object()
       admitted = fetch_runtime_admitted_collectives([instance.pk])   # once per request
       context[ADMITTED_DEITY_COLLECTIVES_CONTEXT_KEY] = admitted     # {shrine_id: [AdmittedCollective]}
  -> ShrineDetailSerializer(instance, context=context)
       get_deity_collectives(obj) = ShrineDeityCollectiveSerializer(
           context[KEY].get(obj.pk, []), many=True)
```

- Context key: `ADMITTED_DEITY_COLLECTIVES_CONTEXT_KEY = "admitted_deity_collectives"`
  (exported from `temples.api.serializers.shrine`).
- The value is keyed by `shrine_id`, so a serializer for one Shrine never renders
  another Shrine's admitted Collectives.
- No admitted Collective → `"deity_collectives": []`.
- No context: the serializer is called without the key (for example by the ingest
  action). It returns `[]` (fail closed) and never falls back to the model relation.

## 4. Payload contract

`deity_collectives` is an array of `ShrineDeityCollectiveSerializer`:

```text
{
  "deity_collectives": [
    {
      "id": int,
      "source_attested_label": str,
      "role": str,
      "sort_order": int,
      "member_count": int | null,
      "member_count_relation": str,
      "member_list_status": str,
      "verification_status": str,
      "confidence": str,
      "memberships": [
        {
          "deity": {"id": int, "display_name": str},
          "sort_order": int,
          "verification_status": str,
          "confidence": str
        }
      ]
    }
  ]
}
```

- No `sources` key at either level.
- Existing Shrine Detail fields are unchanged: `id`, `kind`, `name_jp`, `name_romaji`,
  `address`, `latitude`, `longitude`, `goriyaku`, `goriyaku_tags`, `is_favorite`,
  `distance`, `distance_text`, `location`, `kyusei`, `deities`, `histories`.

## 5. Surfaces

| Surface | `deity_collectives` |
|---|---|
| `GET /api/shrines/{id}/` (retrieve; router `shrine-detail` and `shrine_detail_view`, both `ShrineViewSet.retrieve`) | **yes**: A6-01 admitted only |
| `GET /api/shrines/` (list) | no (`ShrineListSerializer`) |
| nearest: `/api/shrines/nearby/` (`NearestShrinesAPIView`, Places results, no Shrine serializer); `ShrineViewSet` maps a `nearest` action to `ShrineListSerializer` in `get_serializer_class` but defines no such action | no |
| popular / ranking (`ShrineListSerializer`) | no |
| `POST /api/shrines/ingest/` | field present (documented 200 = `ShrineDetailSerializer`), value always `[]` (no selector call; fail closed) |
| Web / Mobile UI | not connected |
| Recommendation / Compass / Concierge / Deep Dive | unchanged |

**Ingest boundary.** `POST /api/shrines/ingest/` also instantiates
`ShrineDetailSerializer`, but A6-02 Step 2 does not treat ingest as a Collective
runtime exposure surface. Because ingest does not provide admitted Collective
context, `deity_collectives` is intentionally `[]`. Any future Collective exposure
from ingest requires a separate surface decision.

`temples.serializers.ShrineSerializer` (used by legacy `temples/views.py`) is not this
serializer. `temples/serializers/routes.py` does not export `ShrineSerializer`, so it
resolves to `None`.

## 6. Activation remains necessary but not sufficient

The following rows exist in `ShrineDeityCollective` but never appear in the detail
payload. Each case is covered by a test:

- no `CollectiveRuntimeActivation`
- Collective evidence not usable (`draft` / `unverified` / `disputed`, or no
  fact-ready Source)
- `member_list_status` other than `complete`
- zero Memberships
- a Membership without its own fact-ready Source, or without any Source
- a Membership resolving to another Shrine's deity
- another Shrine's admitted Collective

## 7. Query-count observation

Measured on `GET /api/shrines/{id}/` with a local PostgreSQL 16, NoGIS
(CI unit-job equivalent), using `CaptureQueriesContext`:

| Case | Before (develop `2f0c0b5`) | After | Delta |
|---|---:|---:|---:|
| no Knowledge, no Collective | 4 | 5 | +1 |
| 5 deities + 5 histories | 6 | 7 | +1 |
| + 1 activated Collective × 2 Memberships | 6 | 11 | +5 |
| + 3 activated Collectives × 4 Memberships | 6 | 11 | +5 |

- The added cost is exactly the A6-01 selector contract:
  - 1 query when the Shrine has no activated Collective
  - 5 queries when candidates exist
- The cost does not grow with the number of Collectives or Memberships:
  1×2 and 3×4 both cost 11. So there is no per-Collective or per-Membership N+1.
- The test `test_detail_query_count_does_not_grow_with_collectives_or_memberships`
  pins this.
- The selector is not bypassed for optimization. It is called exactly once per
  request, which `test_detail_calls_selector_exactly_once_with_the_shrine_id` pins.

## 8. OpenAPI / schema

- `docs/core/openapi-contract-governance.md` classifies `backend/schema.yml` as
  未確定 (generation command not identified).
- `api_schema.yaml` (`make spectacular`) is gitignored.
- So no committed schema file is regenerated or edited in this change.
- Verification: `manage.py spectacular` was run before and after into a scratch file.
  - The diff contains only the expected additions: `ShrineDetail.deity_collectives`
    (array of `ShrineDeityCollective`, readOnly, required), the
    `ShrineDeityCollective`, `ShrineDeityCollectiveMembership` and
    `_CollectiveMembershipDeity` components, and the serializer docstring.
  - Generator warnings are unchanged.

## 9. Tests

New: `backend/temples/tests/api/test_shrine_detail_deity_collectives_api.py`.

Updated: `backend/temples/tests/serializers/test_shrine_deity_collective_serializers.py`.
The Step 1 assertion `test_shrine_detail_serializer_is_not_connected_to_collectives`
is replaced by three tests:

- the field exists
- only context-admitted Collectives render, with no Collective query in the serializer
- no context → `[]`

| Requirement | Test |
|---|---|
| A field present | `test_detail_includes_deity_collectives_field` |
| B none admitted → `[]` | `test_no_admitted_collective_returns_empty_list` |
| C admitted appears once | `test_admitted_collective_appears_exactly_once_with_serializer_payload` |
| D no activation | `test_collective_without_activation_does_not_appear` |
| E invalid Collective evidence | `test_activated_collective_with_invalid_evidence_does_not_appear[draft/unverified/disputed]`, `test_activated_collective_without_fact_ready_source_does_not_appear` |
| F incomplete member list | `test_activated_collective_with_incomplete_member_list_does_not_appear[partial/not_enumerated/not_determined]` |
| G no Membership | `test_activated_collective_without_membership_does_not_appear` |
| H Membership without own fact-ready Source | `test_membership_without_own_fact_ready_source_hides_collective`, `test_membership_without_any_source_hides_collective_even_if_collective_source_ready` |
| I cross-Shrine Membership | `test_membership_resolving_to_other_shrine_deity_hides_collective` |
| J selector-owned ordering | `test_collective_and_membership_ordering_follow_selector` |
| K deities / histories unchanged | `test_existing_deities_and_histories_are_unchanged_by_collectives` |
| L list / nearest not exposed | `test_shrine_list_api_does_not_expose_deity_collectives`, `test_list_and_nearest_serializer_have_no_deity_collectives_field` |
| M no Knowledge → 200 + `[]` | `test_detail_without_knowledge_or_collective_is_safe_and_empty` |
| single admission source | `test_detail_calls_selector_exactly_once_with_the_shrine_id`, `test_detail_output_is_exactly_what_selector_returns` |
| query count | `test_detail_query_count_does_not_grow_with_collectives_or_memberships` |

Results (local PostgreSQL 16, NoGIS, CI unit-job settings):

```text
focused (new API test + Collective serializers + A6-01 selector)   81 passed
regressions (shrine detail knowledge, list created_at, public search,
  evidence-gate recommendation/detail contract, knowledge serializers,
  evidence-gate pilot, reason strength, shared recommendation eligibility,
  urls, root views)                                               116 passed, 1 skipped
nearest / nearby                                                    1 passed, 3 skipped (GIS-only)
full backend suite (pytest, all testpaths)                       4436 passed, 8 skipped, 0 failed
  skips: GDAL / PostGIS unavailable (GIS-only) and a pre-existing concierge
  ambiguous-theme skip; none relate to this change
manage.py check                                                  no issues
makemigrations --check --dry-run                                 No changes detected
```

## 10. Not changed

- models, migrations (`makemigrations --check --dry-run`: No changes detected)
- A6-01 selector, Evidence Gate, activation seed, `activate_collective_runtime`
- Recommendation eligibility, Compass, Concierge, Deep Dive
- Web / Mobile UI
- Production data (no write, no activation apply)
