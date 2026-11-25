# Safe Remaining Need → Goriyaku Mapping Correction

> Implements the 4 SAFE_CORRECTIONS confirmed by `docs/audit/remaining-need-goriyaku-semantic-mapping.md` (Sections 19/22): `relationship`, `health`, `focus`, `family`. `marriage`, `communication`, `mental`, `courage` — the 4 PRODUCT_DECISION_REQUIRED Needs from the same audit — remain untouched. Changes `backend/temples/domain/need_to_goriyaku_tag_ids.py` and its test file only. No new taxonomy, no `GoriyakuTag` master change, no DB write, no migration, no frontend/UI change.

## 1. Scope

Narrow mapping correction: exactly the 4 Need tags the audit classified `SAFE_CORRECTIONS` — no opportunistic fixes of the 4 `PRODUCT_DECISION_REQUIRED` Needs or any other finding from that audit.

## 2. Base SHA

`origin/develop` at `6460bab0a9c45dc3069b1378b43dc4eaa481536b` (`コンシェルジュ推薦理由をEvidenceベースの表示へ整理 (#2581)`), after PR #2580 (this task's own audit source) was found still open/CI-pending at Phase 0 and merged with explicit Mother Ship authorization. `git log --oneline 1fa0dc6c..6460bab0`: PR #2581 (frontend-only, `apps/web/`, confirmed via diff-stat — zero backend overlap) then PR #2580. Worktree: `/Users/morietsu/Developer/jinja_app-safe-remaining-need-mapping`, branch `fix/safe-remaining-need-goriyaku-mapping`.

## 3. Source Audit

`docs/audit/remaining-need-goriyaku-semantic-mapping.md` Section 19 (SAFE_CORRECTIONS) / Section 22 (Recommendation: `SAFE_CORRECTION_PR_READY` for this 4-Need subset) / Section 21 (Option B: bundle all 4 in one PR).

## 4. Exact Before/After

| Need Tag | Before | After |
|---|---|---|
| relationship | `{1, 27, 34}` | `{1}` |
| health | `{7, 8}` | `{7, 8, 24, 33, 38}` |
| focus | `{3, 4, 39}` | `{9, 10}` |
| family | `{2, 25, 27, 34}` | `{2, 26, 34}` |

Fresh-confirmed before editing (Phase 0) that these 4 before-states exactly matched the merged audit's recorded state, with no drift.

## 5. Protected Mappings

Recorded exact values before editing; re-verified unchanged after:

| Need Tag | Value (unchanged before → after) |
|---|---|
| love | `{1, 20}` |
| career | `{6, 21, 30, 12, 27}` |
| money | `{5, 36, 4, 28}` |
| study | `{9, 10}` |
| protection | `{11, 32, 2}` |
| travel_safe | `{3, 13, 14}` |
| marriage | `{1, 27, 29}` |
| communication | `{30, 33, 37, 39}` |
| mental | `{11, 16, 26, 28, 38}` |
| courage | `{12, 15, 18, 20, 24, 30, 38}` |
| rest | `{7, 8}` |

## 6. Unit Test Results

`backend/temples/tests/test_need_to_goriyaku_tag_ids.py`: split the prior combined `test_stale_ids_removed_from_previously_referencing_purposes` / `test_purposes_outside_correction_scope_are_unchanged` tests to separate the 4 Needs now changed (relationship/health/focus/family — new dedicated exact-set tests) from the Needs that remain from those groups unchanged (mental/rest stay in the stale-ids test; marriage/communication/mental/courage stay in the outside-scope test). Structural invariants (`test_no_reference_points_outside_canonical_master_id_range`, `test_ids_42_to_45_referenced_nowhere`) untouched and re-verified.

```
temples/tests/test_need_to_goriyaku_tag_ids.py: 14 passed
```

## 7. Focused Regression Results

```
test_need_to_goriyaku_tag_ids.py
test_compass_recommendation_orchestrator.py
test_compass_recommendations_api.py
test_compass_runtime.py
test_compass_direction_filter.py
test_backfill_goriyaku_tags_command.py
test_need_lead_purpose_alignment.py
=> 137 passed, 0 failed
```

## 8. Full Regression Results

```
temples app full suite: 1706 passed, 15 skipped (pre-existing environment
skips: PostGIS/GDAL unavailable locally, GOOGLE_PLACES_API_KEY unset, one
theme-family pin gap unrelated to this change), 0 failed.
```

## 9. relationship Result

Verified via read-only `patch.dict` simulation (fixed origin/direction, identical to all prior correction PRs in this chain) against the live, unmodified `get_compass_recommendations()`:

- Before Top3: 明治神宮(gid)/赤坂氷川神社(gid)/**日枝神社(gid via 出世運 — false match)**
- After Top3: 明治神宮(gid)/赤坂氷川神社(gid)/**芝大神宮(gid via 縁結び — correct match)**
- The invalid 出世運(27)/火防(34)-driven match is gone; `relationship` still matches independently via its own retained `{1}` — no fallthrough to `love`'s evidence, no alias behavior touched, confirming `relationship` remains `WELL_SEPARATED` as the prior audit found.

## 10. health Result

- Before/After Top3: identical in this fixture (乃木神社/靖國神社 via 家内安全, 長太稲荷神社 fallback) — no shrine within this specific candidate pool carries ids 24/33/38, matching the audit's own `CANDIDATE_POOL_LIMITATION` prediction exactly.
- The new ids (24 健康長寿, 33 病気平癒, 38 足腰健康) are structurally reachable — confirmed via `need_tags_to_goriyaku_ids(["health"])` resolving to `{7, 8, 24, 33, 38}` — but simply not exercised by this particular fixed fixture; DB-wide these 3 tags exist on 1 shrine each (`goriyaku-mapping-master-integrity.md` Section 4 baseline).
- Mapping-only: no `Reason`/`Lead` template text changed for `health`; no medical-efficacy language was introduced (only existing canonical `GoriyakuTag` labels, unmodified, are referenced).

## 11. focus Result

- Before Top3: 明治神宮/花園神社/日枝神社, **all 3 false matches** (交通安全/商売繁盛/商売繁盛 — none semantically related to "focus")
- After Top3: 長太稲荷神社(dup)/長太稲荷神社(dup)/明治神宮, all fallback (`score_need=0`, `matched=[]`)
- This exactly mirrors `study`'s own pre-correction pattern (PR #2545/#2546): false matches disappear, honest fallback returns. `{9, 10}` are DB-wide real (`study`'s own tags, 8 and 3 shrines respectively) but none fell within this specific candidate pool — `CANDIDATE_POOL_LIMITATION`, not a mapping defect.
- Overlap with `study` confirmed as intended: `focus` and `study` now share evidence tags `{9, 10}` exactly as `love`/`relationship`/`marriage` already share id `1` — the same shrine *can* match both `study` and `focus` when it carries 学業成就/合格祈願, which is expected and semantically supported (both Needs share the identical `study_success` `consultation_axis` per the audit's Section 5), not a regression. `study`'s own mapping (`{9, 10}`) is unchanged (Section 5/6).

## 12. family Result

- Before Top3: 明治神宮(gid)/赤坂氷川神社(gid)/**日枝神社(gid via 出世運 — false match)**
- After Top3: 明治神宮(gid)/赤坂氷川神社(gid)/**靖國神社(gid via 厄除け — correct match)**
- id=34 (火防) retained unchanged, contributing identically before/after (both runs draw their top-2 matches through id=2 厄除け, with id=34 present in both mappings without driving any Top3 change).
- id=26 (家庭円満) is structurally reachable — confirmed via `need_tags_to_goriyaku_ids(["family"])` resolving to `{2, 26, 34}` — but did not surface in this fixture's Top3 (family harmony tag has DB-wide shrine_count=1, per Section 4 baseline; not present in this candidate pool).
- The removed ids (25 芸能, 27 出世運) no longer produce any `family` match anywhere — confirmed structurally (neither id is in the post-edit set) and empirically (rank3's false 出世運 match disappeared).

## 13. Ranking Churn

| Need | Cause | Classification |
|---|---|---|
| relationship | INVALID_MAPPING_REMOVAL (27, 34) | Expected — rank3 swap to a different shrine via the same retained VALID tag (SHARED_VALID_TAG-adjacent, same pattern as id=1's existing love/relationship/marriage sharing) |
| health | CLEAR_MISSING_ADDITION (24, 33, 38) | Expected, invisible in this fixture — `NO_CHANGE` observed, attributable to candidate-pool sparsity, not absence of effect |
| focus | INVALID_MAPPING_REMOVAL (3, 4, 39) + CLEAR_MISSING_ADDITION (9, 10, SHARED_VALID_TAG with `study`) | Expected — 3 false matches removed; new true-match potential not visible in this fixture (candidate-pool sparsity) |
| family | INVALID_MAPPING_REMOVAL (25, 27) | Expected — rank3 swap to a different shrine via a different retained VALID tag |

## 14. Unexpected Churn

**0.** Every observed (or fixture-invisible) change traces to a specific, previously-predicted cause from `remaining-need-goriyaku-semantic-mapping.md`. No investigation was required; nothing needed to be changed to suppress any behavior.

## 15. Remaining Product Decision Needs

**Not touched by this PR** (per `remaining-need-goriyaku-semantic-mapping.md` Section 20, unresolved):

- `marriage` — `{1, 27, 29}` unchanged; separately, `NEED_TAG_ALIASES["marriage"] = "love"` (pre-existing, untouched by this PR) makes any future GID-level correction to this entry inert at runtime regardless of content — a distinct architecture question, not decided here
- `communication` — `{30, 33, 37, 39}` unchanged; the audit found no canonical tag in the current master that fits this Need at all (a genuine taxonomy gap, not fixable by mapping alone)
- `mental` — `{11, 16, 26, 28, 38}` unchanged; QUESTIONABLE-retention sign-off pending
- `courage` — `{12, 15, 18, 20, 24, 30, 38}` unchanged; same QUESTIONABLE-retention sign-off pending

## 16. Production Safety

Production Code change: the two files in Section 17's diff stat only — `backend/temples/domain/need_to_goriyaku_tag_ids.py` (dict literal edit, 4 Need tags) and its test file. `NEED_TEXT_WEIGHTS`, `NEED_TAG_ALIASES`, consultation-axis logic, C1 Max, Ranking weights, Lead, Reason, Direction, Distance, canonical `GoriyakuTag` master — all confirmed unchanged (Section 17).
Production DB change: **NO** — all verification ran against the existing isolated local scratch DB, read-only queries and `patch.dict`-scoped simulation only.
Migration: **none**. New taxonomy: **none**.

## 17. Next Follow-up

Resolution of the 4 `PRODUCT_DECISION_REQUIRED` Needs (Section 15), each requiring a distinct Mother Ship decision:
1. `marriage`'s alias-vs-independent architecture question
2. `communication`'s accept-empty-mapping-or-defer-to-new-taxonomy question
3/4. `mental`/`courage`'s QUESTIONABLE-retention sign-off (both have real Text-layer coverage compensating their weak GID layer, per the audit's Section 9/11 — lower urgency than the other two)
