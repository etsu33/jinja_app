# Knowledge Coverage — Canonical Scope Tooling Fix (P9)

## 1. Metadata

| Field | Value |
|---|---|
| Task | P9 — separate population selection from coverage calculation so Knowledge Coverage can be measured against an explicitly supplied canonical shrine scope, without treating the QA-filtered queryset as canonical truth. |
| Type | **Tooling fix.** No Production data remediation. No duplicate/shadow deletion, no id-105 fix, no coordinate fix, no Recommendation-mapping/scoring change, no Knowledge / `Shrine.goriyaku` / `GoriyakuTag` data change, no model, no migration. |
| Branch | `fix/knowledge-coverage-canonical-denominator` |
| Base | `origin/develop` @ `1ce8c7bf677eeb0bfeb82b15f1d0e5b94767a022` (merge of PR #2614). Fetched this session; `develop` had not advanced beyond the expected merge → **`BASE_DRIFT_REQUIRES_REVIEW` not triggered**. |
| Worktree | `~/Developer/jinja_app-kc-canonical-scope` (isolated; control repo untouched). |
| Date | 2026-08-29 |

## 2. The 107-vs-103 mismatch

`knowledge_coverage_report` derived its audit target from
`exclude_qa_fixture_shrines(Shrine.objects.all())` — a **name-convention**
filter. Against current Production (`RAW_PRODUCTION_SHRINE_ROWS = 108`) that
removes only the QA row **id 102** (`テスト確認神社 …`, `name_jp LIKE 'テスト%'`),
leaving **107**.

The canonical audit denominator established by PR #2614
(`docs/audit/shrine-evidence-integrity-full-audit.md`) is **103** unique real
shrine identities:

```text
108  RAW_PRODUCTION_SHRINE_ROWS
 -1  QA fixture .............................. id 102
 -1  NON_SHRINE_ARTIFACT .................... id 105 (広島市)
 -3  SAME_REAL_SHRINE_DUPLICATE shadows ..... id 101→primary 22, 103→primary 21, 104→primary 49
=103 FULL_AUDIT_DENOMINATOR
```

`knowledge_coverage_report` counted the non-shrine artifact and the three
duplicate shadows in its denominator (they carry no Knowledge, so they inflated
`zero_knowledge` and depressed every percentage). Reporting
`Audit Target Shrines = 107` implied 107 was the canonical real-shrine
denominator. It is not.

## 3. Why QA fixture exclusion is not canonical identity resolution

`shrine_qa_fixture_exclusion.exclude_qa_fixture_shrines()` is shared by
**Knowledge Coverage** and **Concierge / Recommendation candidate
construction** (`concierge_chat_candidates.build_chat_candidates`), plus
`export_shrine_knowledge` and `recommendation_quality_measurement`. Its single
responsibility is *QA/test fixture exclusion by naming convention*
(`テスト%`, `%承認テスト%`, `%検証%`, a small noisy-name list). It intentionally
hard-codes **no** Production row ids.

Expanding it to also drop the non-shrine artifact and the duplicate shadows —
e.g. adding `{101, 103, 104, 105}` — was rejected:

- Production row id is **not** a canonical identity key.
- Spreadsheet ids are already known **not** to be stable across environments
  (`docs/audit/tomioka-hachimangu-identity-resolution.md`: Spreadsheet id 104 ≠
  Production id 104).
- It would silently change the Concierge candidate pool
  (`build_chat_candidates` calls the same helper).
- The current data model has **no persisted canonical / duplicate / artifact
  marker** to base such a rule on.

`AUTOMATIC_CANONICAL_SCOPE_DISCOVERY = NOT_SUPPORTED_BY_CURRENT_MODEL`.

`exclude_qa_fixture_shrines` and `concierge_chat_candidates.py` are **unchanged**
by this PR.

## 4. Selected architecture

**Population selection is separated from coverage calculation** in
`backend/temples/services/knowledge_coverage_report.py`:

- `build_knowledge_coverage_report(shrine_ids=None)` — new optional first
  argument (matches the existing precedent
  `build_recommendation_quality_measurement_report(shrine_ids=None)`):
  - `None` (default) → `_qa_filtered_shrine_ids()` — the **existing**
    QA-filtered-DB scope. Backward compatible.
  - `list[int]` / any iterable / a `Shrine` `QuerySet` → **explicit scope**,
    used exactly as given. De-duplicated order-preservingly; non-existent ids
    are **not** silently dropped (`scope.resolved_in_db` surfaces the gap).
- `_resolve_scope()` is the single place population is chosen; every metric and
  every percentage denominator then uses that one id list.
- The private helper `_audit_target_shrine_ids()` was renamed
  `_qa_filtered_shrine_ids()` (module-private; no external importer) to stop it
  reading as "the audit target".

No new framework, no new model, no new dependency.

### `None` vs empty — not conflated

`shrine_ids is None` selects the default scope. `shrine_ids == []` (or an empty
`QuerySet`) is an **explicit empty scope**: `audit_target_shrines = 0`, a valid
all-zero report, `scope.mode = "explicit"`. It never falls back to "all
shrines". This distinction is covered by a dedicated test
(`test_explicit_empty_scope_audits_zero_and_does_not_fall_back_to_all`,
`test_command_empty_scope_file_audits_zero_not_all`).

## 5. Default compatibility behavior

- `build_knowledge_coverage_report()` with no argument behaves exactly as before
  for every existing metric (`knowledge_coverage`, `zero_knowledge`,
  `deity_coverage`, `history_coverage`, `source_coverage`,
  `both_deity_and_history_coverage`, `fact_ready_coverage`,
  `verified_source_count`, `total_source_count`,
  `verification_status_distribution`, `confidence_distribution`,
  `source_type_distribution`, all `*_count_distribution`).
- Existing JSON keys are preserved: `total_db_shrines`, `audit_target_shrines`,
  `excluded_test_shrines`, and all of the above. The management command still
  prints the `Total DB Shrines:` / `Audit Target Shrines:` /
  `Excluded Test Shrines:` lines.
- **Option A (preserve key, add metadata)** was chosen over a breaking rename:
  `audit_target_shrines` keeps its key but its meaning is now
  scope-dependent, and a new `scope` block makes the semantics explicit
  (`mode`, `count`, `total_db_shrines`, `outside_scope_count`,
  `resolved_in_db`, `note`). The command's text output annotates the line —
  `Audit Target Shrines: N [= Coverage Scope count; mode=… — NOT necessarily
  the canonical unique-real-shrine denominator]` — and adds a
  `Coverage Scope:` line. So `107` is never presented as the canonical
  real-shrine denominator.

## 6. Explicit canonical scope behavior

There is **no built-in "canonical" mode** and no comma-separated Production-id
constant in source. The operator supplies the canonical id set explicitly:

- `--scope-id SHRINE_ID` (repeatable) — ids on the command line.
- `--scope-ids-file PATH` — a file of ids (one per line, `#` comments and blank
  lines ignored; **or** a JSON array). Mutually exclusive with `--scope-id`
  (both → `CommandError`). A missing file → `CommandError` (no silent
  fallback). A file that resolves to zero ids → explicit empty scope (valid
  zero report), **not** a fallback.

To measure the PR #2614 canonical 103 scope, supply the 103 primary ids
(`1`–`100`, `106`, `107`, `108` in current Production — derivable from
`docs/audit/shrine-evidence-integrity-full-audit-matrix.md`) via
`--scope-ids-file`.

This interface is explicit, read-only, deterministic, testable, and cannot
silently fall back to a wrong denominator.

## 7. Report denominator metadata — before / after

| | Before | After |
|---|---|---|
| `total_db_shrines` | all `Shrine` rows | unchanged |
| `audit_target_shrines` | QA-filtered DB row count (**implied canonical**) | scope count; meaning set by `scope.mode` |
| `excluded_test_shrines` | `total − audit_target` | unchanged key; = rows outside the scope |
| `scope` | *(absent)* | `{mode, count, total_db_shrines, outside_scope_count, resolved_in_db, note}` |
| command text | `Audit Target Shrines: 107` | `Coverage Scope: qa_filtered_db (107 …)` + annotated `Audit Target Shrines: 107 [… NOT necessarily the canonical … denominator]` |
| `scope.mode` values | — | `qa_filtered_db` (default) / `explicit` |

All metric calculations and percentage denominators are unchanged in formula —
only which id list feeds them.

## 8. Auto-discovery boundary

**`AUTOMATIC_CANONICAL_SCOPE_DISCOVERY = NOT_SUPPORTED_BY_CURRENT_MODEL`.**
`Shrine` has no persisted canonical-identity / duplicate / artifact field. P9
does **not** invent one and does **not** add heuristic duplicate detection
(no name-only, no coordinate-only inference) to Coverage code. The canonical
scope must be *supplied* to the calculator.

## 9. P8 dependency boundary

A permanent, automatically-discoverable canonical scope depends on **P8
identity remediation** persisting a reliable canonical/duplicate/artifact
marker (or the duplicate shadow rows being resolved). Until then, P9's explicit
scope injection is the supported path. When P8 lands such state, a future
change could add an automatic canonical mode that reads it — out of scope here.

## 10. Production verification

Sanctioned read-only path available this session
(`scripts/migration_safety/readonly_query.sh` + repo-external
`~/.config/kami-musubi/production-db.env`; every SQL passed
`guard.py check-readonly-sql`; credential value never printed / logged / in
argv). A SELECT-only query reproducing the service's core denominators for the
explicit canonical scope `id ∈ {1..100, 106, 107, 108}`:

| Metric | Value [prod] | PR #2614 expectation |
|---|---|---|
| scope resolved in DB (`FULL_AUDIT_DENOMINATOR`) | **103** | 103 ✓ |
| knowledge any (deity or history) | **89** | 89 ✓ |
| zero knowledge | **14** | 14 ✓ |
| source any | **89** | 89 ✓ |

**`PRODUCTION_CANONICAL_SCOPE_VERIFICATION = CONFIRMED`** — the explicit
canonical scope yields denominator 103 and reproduces the PR #2614 high-level
canonical coverage counts. These values are **not** hardcoded into calculation
logic and **not** forced into unit tests (unit tests build their own fixtures);
they are Production verification expectations only.

## 11. No-write confirmation

Nothing was written to Production, DB data, the Google Spreadsheet, Knowledge
rows, `Shrine.goriyaku`, `GoriyakuTag` rows, `PlaceRef`, Recommendation
mappings/scoring, Evidence Gate, `NEED_TO_GORIYAKU_IDS`, or the frontend. No
model, no migration, no fixture, no seed. Production access was read-only via
the sanctioned bridge (credential value never seen). `exclude_qa_fixture_shrines`
and `concierge_chat_candidates.py` are unchanged. Changed files: the Knowledge
Coverage service, its management command, their tests, the QA-exclusion
regression test, and this document.
