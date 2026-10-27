# Concierge B-1: Batch-loaded Recommendation History（2026-10-27）

## 1. Status

```text
RECORD TYPE   = implementation note
DESIGN        = docs/audit/concierge-latency-result-failure-root-cause-2026-10-27.md §7 B-1（PR #3361）
BASELINE      = origin/develop@3384392（PR #3361 not yet merged at branch time; this change does not depend on it）
SCOPE         = concierge_history.py（batch loader + pure helpers）, concierge_chat_ranking.py（optional facts）,
                concierge_chat.py（one load before the enrichment loop）, backend tests
UNCHANGED     = scoring weights, ranking policy, candidate pool（20）, response shape, anonymous path, auth, UI,
                schema（no migration）, dependencies
PRODUCTION    = NOT ACCESSED; no deployment
FINAL STATUS  = PR for Mother Ship review; STOP before merge
```

## 2. Change

- **`load_shrine_history_facts(user, shrine_ids)`** reads, for the ≤ 20 candidate shrines, one aggregate query per table:
  - interaction logs: count + `MAX(created_at)` per shrine and action type（detail_view / route_open）;
  - favorites: `MAX(created_at)`;
  - visits with `status="added"`: `MAX(visited_at)`;
  - `action_completed` events: `MAX(created_at)`;
  - reflections: the latest row per shrine, with `select_related("shrine")`.

  It returns `None` for anonymous users.
- **Pure helpers** reproduce the per-shrine results from those facts: `behavior_signal_breakdown_from_facts`,
  `action_state_from_facts`（precedence reflection > visit(added) > favorite > route_open > detail_view）and
  `reflection_hint_from_facts`.
- **`_attach_breakdown(..., history_facts=…)`** uses the facts when they are given and the candidate has a shrine id.
  Otherwise（anonymous, or an unresolvable id）it calls the original per-shrine functions exactly as before.
- **`_attach_chat_rec_enrichment`** loads the facts once before the loop. `batch_history=False` keeps the old path for
  equivalence testing.
- **The per-shrine functions are unchanged** and remain the oracle. They are also still used elsewhere（thread detail
  `action_state`, `calculate_shrine_behavior_signal_v2`）. The only refactor extracts the hint payload builder
  `_reflection_hint_payload`, without changing any query.

Equivalence basis:

- the filters are identical;
- every "latest" column（`created_at`, `visited_at`）is NOT NULL, so `MAX()` equals `ORDER BY … DESC LIMIT 1`;
- existence is derived from count > 0 or a non-null latest value;
- the recency multiplier is the same function applied to the same timestamps.

## 3. Results

| measurement | before | after |
| --- | --- | --- |
| queries, authenticated, 20 candidates, mixed-history fixture | **266** | **5** |
| queries, authenticated, no history（audit probe） | 280 | ≤ 5 |
| queries, anonymous | 0 | 0 |
| queries vs candidate count（1 / 5 / 20） | linear（≈ 14 per candidate） | constant ≤ 5 |

**Baseline**: the enrichment output for the shared fixture was captured with the unchanged code before any edit. The
same capture after the change is deep-equal for both the authenticated and the anonymous user（local run, Postgres 16,
CI settings）.

Tests:

- `backend/tests/test_concierge_history_batch.py`: **18 passed**.
  - Per-shrine equivalence for every candidate:
    - mixed history;
    - empty history;
    - same-timestamp records;
    - removed versus added visits;
    - favorites;
    - latest reflection;
    - other-user isolation;
    - non-integer ids.
  - Anonymous: 0 queries and unchanged output.
  - End to end: `breakdown`, `breakdown_detail`, `_score_total`, `action_state`, `reflection_hint`, `reason`, final
    order and reasons after `_sort_chat_recommendations` are identical.
  - A candidate without a shrine id keeps the legacy path.
  - Query count ≤ 5 for 1, 5 and 20 candidates.
  - The legacy path is still > 200 queries.
- Existing backend tests matching concierge / compass / recommend / ranking / history / behavior / reflection（115
  files）: **1389 passed, 4 skipped**.
- Full backend suite: see the PR.

## 4. Residual risks

- **Reflection tie order**: when two reflections on one shrine share the same `created_at`, the per-shrine query's row
  order is unspecified. The batch picks the highest id, which is deterministic. Scores and action state are identical;
  only the hint's source row can differ in this exact-tie case（tested）.
- **Reflection row volume**: the reflection query loads all of the user's reflections for the candidate shrines
  （normally a few per shrine）. Aggregates are used for every other table.
- **Production latency is not measured.** The expected gain follows from the query count（≈ 266–280 → 5 round trips）;
  the round-trip time itself is hypothesis H-1 of the audit.
- **Other per-candidate costs**: none found in the audit. `append_chat` and the LLM route are unchanged.
