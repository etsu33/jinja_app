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
  `action_state`, `calculate_shrine_behavior_signal_v2`）. The only refactors extract the hint payload builder
  `_reflection_hint_payload` and the latest-reflection query `_latest_reflection`, without changing any SQL.

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

## 4. Compatibility gate: reflections with the same `created_at`（2026-10-27）

**Legacy behaviour.** `build_recent_reflection_hint` uses `… ORDER BY created_at DESC LIMIT 1`. When several rows share
the latest `created_at`, their order is **not defined**: no tie-breaker exists, and the row is whatever PostgreSQL
returns for that plan.

**First B-1 version（`46a5f53`）.** The batch ordered by `(-created_at, -id)`, which introduced a new rule
（"highest id wins"）.

- A mutation check on PostgreSQL showed a **real** difference. With two tied rows, the legacy query returned a different
  row from the batch.
- Impact, only in this exact-tie case: `reflection_hint.source_reflection_id` and the content derived from the row
  （`state_change_*`, `next_need_hint`, `next_history_theme_hint`, `source_history_theme`）could differ.
- Scores, ranking, `action_state` and `reflection_signal` were never affected, because they depend only on the timestamp.
- `reflection_hint` has no scoring or frontend consumer（repository grep）. It appears in:
  - the API response and the persisted thread recommendations;
  - `score_v2.signals` and the `behavior_profile`（observational only）;
  - observation logs.

**Correction（smallest, no new rule）.** The batch keeps the latest row when it is unique. For each shrine whose latest
`created_at` is shared by several rows, it re-selects with the **same** query the per-shrine function uses
（`_latest_reflection`）. The batch therefore inherits the legacy semantics exactly, including the undefined tie order.

- Cost: +1 query per tied shrine, still bounded by the candidate count. A user with no exact ties stays at 5 queries.
- Making tie order deterministic（for example by id）would be a product decision and is **not** made here.

**Tests**:

- `test_tied_latest_reflection_is_selected_exactly_like_the_per_shrine_query[2|3]`: the full hint must be equal, no
  difference permitted;
- `test_tie_fallback_is_limited_to_tied_shrines`: 5 + one query per tied shrine; an older tie does not trigger the
  fallback;
- `test_ties_in_other_tables_need_no_fallback`;
- `test_enrichment_is_identical_with_tied_reflections`.

The old highest-id rule fails the first test on PostgreSQL（mutation check）.

**Results after the correction**:

- batch tests: 22 passed;
- related backend suites（115 files）: 1393 passed, 4 skipped;
- baseline capture: still 266 → 5 queries, deep-equal outputs.

## 5. Local full-suite failure（not caused by B-1）

`temples/tests/test_nsrc_000002_g7_source_identity_sql.py::test_sql_normalized_url_equals_importer_normalize_source_url`
fails locally and is unrelated to this change.

| check | result |
| --- | --- |
| on the unchanged base `origin/develop@3384392`（local, Python 3.13） | fails identically |
| CI backend unit job on `f17cc74`（the #3360 head, whose code `develop` contains; Python 3.11; plain `python -m pytest`） | **success** |
| cause | `urllib.parse.urlunsplit(("https", "", "example.com/p", "", ""))` returns `https:///example.com/p` on Python 3.11.17 / 3.12.3, but `https:example.com/p` on 3.13.17. The SQL normalisation matches the 3.11 / 3.12 result |

It is pre-existing and depends on the Python version（CI pins 3.11）. If the runtime moves to 3.13, the importer's
`normalize_source_url` and its SQL counterpart need to be reconciled. That is a separate task.

## 6. Residual risks

- **Tie order**: still undefined, exactly as before（inherited, not changed）.
- **Reflection row volume**: the reflection query loads all of the user's reflections for the candidate shrines
  （normally a few per shrine）. Aggregates are used for every other table.
- **Production latency is not measured.** The expected gain follows from the query count（≈ 266–280 → 5 round trips）;
  the round-trip time itself is hypothesis H-1 of the audit.
- **Other per-candidate costs**: none found in the audit. `append_chat` and the LLM route are unchanged.
