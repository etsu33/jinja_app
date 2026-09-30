# A6-01 Collective Runtime Selector / Evidence Gate

- Status: IMPLEMENTED (PR) / not connected to any Runtime surface
- Date: 2026-09-30
- Base: develop `352034e` (A6-00 #3035, A6-00b #3036)
- Selector: `backend/temples/services/collective_runtime_selector.py`
- Tests: `backend/temples/tests/test_collective_runtime_selector.py`

## 1. Selector authority

`fetch_runtime_admitted_collectives(shrine_ids) -> dict[int, list[AdmittedCollective]]`
is the single read-only authority for deciding which `ShrineDeityCollective` rows
may be used at Runtime. It lives in its own module and is not merged into
`shrine_knowledge_selector.py`, which stays Recommendation-specific.

No serializer, view, Recommendation, Compass, Deep Dive, Concierge, Web or Mobile
code calls it in this PR. The external payload contract belongs to A6-02.

## 2. Admission conditions

A Collective is admitted only when **all** of the following hold:

| # | Condition | Where enforced |
|---|---|---|
| 1 | `CollectiveRuntimeActivation` row exists | candidate query (`runtime_activation__isnull=False`) |
| 2 | Collective passes `evidence_gate.decide_fact_usability()` with its own sources | Python |
| 3 | `member_list_status == "complete"` | Python |
| 4 | at least one Membership | Python |
| 5 | every Membership passes `decide_fact_usability()` with **its own** sources | Python |
| 6 | every Membership resolves to an existing `ShrineDeity` | Python |
| 7 | every Membership deity belongs to the Collective's Shrine | Python |

Activation is necessary, not sufficient. No Pattern (A/B/C/D) is inferred, and
`member_count` / `member_count_relation` are metadata, not admission inputs.

## 3. Evidence Gate reuse

- The only evidence authority is `temples.services.evidence_gate.decide_fact_usability()`
  (fact status in `source_confirmed` / `reviewed`, plus at least one fact-ready Source).
- No new status set, threshold or trust policy is defined.
- `confidence` is carried as metadata and never used for admission (a `high`
  Collective without a fact-ready Source is excluded).

## 4. Membership Evidence independence

- A Membership is judged only on `membership.sources`.
- `Collective.sources` are never inherited into, merged with, or used to repair a Membership.
- A Membership may cite the same Source row as its Collective; that is its own relation, and it is accepted.

## 5. Fail-safe behavior

- Any failing condition returns no representation for that Collective. Partial Collectives are never returned.
- One failing Membership excludes the whole Collective.
- Each Collective is evaluated independently, so an invalid Collective does not
  suppress a valid one on the same or another Shrine.
- Unresolved deity: Membership deity is **prefetched** rather than `select_related`.
  On a non-null FK, `select_related` uses an INNER JOIN, which would silently drop a
  dangling Membership row and could make a partial set look complete. With prefetch
  the row stays, and the unresolved deity is detected (`DoesNotExist`) and excluded.
- Shrines with no admitted Collective have no key in the result. Empty input returns `{}`.

## 6. Query strategy

```text
empty shrine_ids                        0 queries
candidates = 0                          1 query  (activated Collectives)
candidates >= 1                         5 queries, constant:
  1. activated Collectives for shrine_ids, ORDER BY sort_order, id
  2. Collective sources (prefetch)
  3. Memberships, ORDER BY sort_order, id (prefetch)
  4. Membership sources (prefetch)
  5. Membership deities (prefetch)
```

The test measures 5 queries for 1 Shrine / 1 Collective / 2 Memberships and
5 queries for 5 Shrines / 13 Collectives / 37 Memberships. All queries are
`SELECT` statements, so the selector is read-only.

## 7. Return structure (internal)

`AdmittedCollective` has: `collective_id`, `shrine_id`, `source_attested_label`, `role`,
`sort_order`, `member_count`, `member_count_relation`, `member_list_status`,
`verification_status`, `confidence`, `memberships`.

`AdmittedCollectiveMembership` has: `membership_id`, `deity_id`, `deity_display_name`,
`sort_order`, `verification_status`, `confidence`.

Collective data is kept separate and never flattened into the ShrineDeity structures.
Ordering is backend-owned `(sort_order, id)` at both levels.

## 8. Non-goals

- ShrineDetailSerializer / View / API payload (A6-02)
- Web / Mobile types and UI
- Recommendation eligibility, candidate filtering, ranking, `recommendation_reason_v4`
- Compass, Weekly Featured, Concierge, Deep Dive retrieval / readiness, DeepDiveFact
- EvidenceLink / Evidence Foundation / normalized transport
- Model, migration, Production data and activation seed changes

## 9. Test results (local, NoGIS CI-equivalent environment)

```text
test_collective_runtime_selector.py                           43 passed
related regression files (evidence_gate / knowledge selector /
  recommendation eligibility / deep dive / detail / compass /
  collective; 48 files)                                        1201 passed
full backend suite (pytest -n 4)                               4398 passed, 12 skipped
makemigrations --check --dry-run                               No changes detected
manage.py check                                                no issues
```

A Production-equivalent test imports the repository A-5b seed and then applies
the A6 activation seed with the existing commands. The selector returns nothing
before activation, and returns 6 Collectives / 23 Memberships after it.
