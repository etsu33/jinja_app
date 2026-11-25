# Goriyaku Mapping Master Integrity Correction

> Implements the two safe, explicitly-confirmed correction classes from `docs/audit/goriyaku-mapping-master-integrity.md`: removal of stale `NEED_TO_GORIYAKU_IDS` references to canonical ids absent from the current master (42/43/44/45), and correction of `travel_safe`'s mapping to the canonical master's actual travel-safety labels. Changes `backend/temples/domain/need_to_goriyaku_tag_ids.py` and its test file only. No broader semantic cleanup of the remaining broken Purposes. No new taxonomy, no `GoriyakuTag` master change, no DB write, no migration, no frontend/UI change.

## 1. Base SHA

`origin/develop` at `f75d6304bcff3437564aa385d643d150109026cb` (`docs: Goriyaku mapping master integrity audit (#2577)`), after that PR was found still draft/unmerged at this task's Phase 0 and merged with explicit Mother Ship authorization ("Merge PR #2577 first, then proceed"). Worktree: `/Users/morietsu/Developer/jinja_app-goriyaku-mapping-integrity-fix`, branch `fix/goriyaku-mapping-master-integrity`.

## 2. Audit Source

`docs/audit/goriyaku-mapping-master-integrity.md` Sections 16–21 (`SAFE_CORRECTION_AVAILABLE` for both correction classes; `id 42-45 Decision` = `REMOVE_STALE_REFERENCE` ×4; `航海安全 Decision` = `SAFE_EXISTING_NEED_MAPPING_AVAILABLE`; `Recommendation` = `STRUCTURAL_PLUS_CLEAR_MAPPING`).

## 3. Exact Before/After

| Need Tag | Before | After | Change |
|---|---|---|---|
| love | {1, 20} | {1, 20} | unchanged |
| relationship | {1, 27, 34, **43**} | {1, 27, 34} | removed stale 43 |
| marriage | {1, 27, 29} | {1, 27, 29} | unchanged |
| communication | {30, 33, 37, 39} | {30, 33, 37, 39} | unchanged |
| career | {6, 21, 30, 12, 27} | {6, 21, 30, 12, 27} | unchanged |
| money | {5, 36, 4, 28} | {5, 36, 4, 28} | unchanged |
| study | {9, 10} | {9, 10} | unchanged |
| health | {7, 8, **44, 45**} | {7, 8} | removed stale 44, 45 |
| mental | {11, 16, 26, 28, 38, **43**} | {11, 16, 26, 28, 38} | removed stale 43 |
| protection | {11, 32, 2} | {11, 32, 2} | unchanged |
| courage | {12, 15, 18, 20, 24, 30, 38} | {12, 15, 18, 20, 24, 30, 38} | unchanged |
| focus | {3, 4, 39} | {3, 4, 39} | unchanged (out of scope — Section 21 of the audit doc flags this as a future BROKEN-Purpose finding, not corrected here) |
| rest | {7, 8, **43, 44, 45**} | {7, 8} | removed stale 43, 44, 45 |
| family | {2, 25, 27, 34, **42**} | {2, 25, 27, 34} | removed stale 42 |
| travel_safe | **{10, 22, 23}** | **{3, 13, 14}** | full replacement — all 3 old ids were INVALID/QUESTIONABLE (audit Section 10); all 3 new ids are the canonical master's actual travel-safety labels (交通安全/航海安全/海上安全) |

## 4. Removed Stale References

ids **42, 43, 44, 45** removed from every Need tag that referenced them (relationship, health, mental, rest, family). No replacement id was substituted for any of them — per the audit's Section 7 (`DIFFERENT_MASTER_SCHEME`, no unique replacement provable) and this task's explicit instruction not to fabricate a replacement to avoid an empty mapping. In every case the resulting mapping remained non-empty after removal (no Need tag was reduced to `set()`).

## 5. travel_safe Before/After

- Before: `{10, 22, 23}` = 合格祈願 (exam-passing, study-domain) / 美容 (beauty) / 方除け (directional warding) — 2 INVALID, 1 QUESTIONABLE, 0 VALID (audit Section 10)
- After: `{3, 13, 14}` = 交通安全 (traffic safety) / 航海安全 (voyage safety) / 海上安全 (maritime safety) — all 3 are direct, name-level matches for the `travel_safe` Need tag (audit Section 9, `EXISTING_NEED_CLEAR_MATCH`)

Verified via `need_tags_to_goriyaku_ids(["travel_safe"])` → `{3, 13, 14}` (exact match, Section 7 below).

## 6. Master Integrity Before/After

| Metric | Before | After |
|---|---:|---:|
| Total `NEED_TO_GORIYAKU_IDS` references (all 15 Need tags) | 60 | 52 |
| References pointing to nonexistent canonical ids | 8 (unique ids: 42, 43, 44, 45) | **0** |
| Need tags reduced to an empty set | 0 | 0 |
| New Need tags introduced | — | 0 |
| Current mappings removed beyond the 4 stale ids | — | 0 |

Verified programmatically: every remaining `NEED_TO_GORIYAKU_IDS` value is a subset of `range(1, 40)` (the canonical master's exact id range).

## 7. Test Results

New assertions in `backend/temples/tests/test_need_to_goriyaku_tag_ids.py`:
- `test_travel_safe_mapping_matches_master_integrity_correction` — exact-set assertion for `travel_safe == {3, 13, 14}`
- `test_stale_ids_removed_from_previously_referencing_purposes` — exact-set assertions for relationship/health/mental/rest/family post-removal
- `test_purposes_outside_correction_scope_are_unchanged` — narrowed to marriage/communication/courage/focus (the 5 already-corrected Purposes have their own dedicated tests, unchanged; the 5 now-touched Purposes moved to the new stale-ids test above)
- `test_no_reference_points_outside_canonical_master_id_range` — structural invariant, iterates all 15 Need tags against a fixed `range(1, 40)` baseline (no DB coupling, per instruction to prefer fixed canonical expectations)
- `test_ids_42_to_45_referenced_nowhere` — explicit regression guard against the 4 specific stale ids reappearing

```
temples/tests/test_need_to_goriyaku_tag_ids.py: 10 passed
Focused regression (mapping + Compass + Concierge-adjacent + Lead alignment):
  test_need_to_goriyaku_tag_ids.py
  test_compass_recommendation_orchestrator.py
  test_compass_recommendations_api.py
  test_compass_runtime.py
  test_compass_direction_filter.py
  test_backfill_goriyaku_tags_command.py
  test_need_lead_purpose_alignment.py
  => 133 passed, 0 failed

Full temples app suite: 1702 passed, 15 skipped (pre-existing environment
skips: PostGIS/GDAL unavailable locally, GOOGLE_PLACES_API_KEY unset,
one theme-family pin gap unrelated to this change), 0 failed.
```

## 8. 波上宮 Connectivity Before/After

Read-only structural verification only — 波上宮's `goriyaku`/`goriyaku_tags` remain empty in the local DB throughout (confirmed unchanged before and after this correction; Batch 17 Recommendation Evidence is not activated by this PR).

- **Before**: `13 in NEED_TO_GORIYAKU_IDS["travel_safe"]` → `False` → `CANONICAL_BUT_UNMAPPED`
- **After**: `13 in NEED_TO_GORIYAKU_IDS["travel_safe"]` → `True` → `RECOMMENDATION_CONNECTED`

This is a mapping-structure fact only: *if* 波上宮 (or any shrine) is later given the `航海安全` tag through a separately-reviewed and separately-imported Recommendation Evidence write, it would now correctly resolve to the `travel_safe` Purpose. No such write occurred in this PR.

## 9. Ranking Churn

Measured via `unittest.mock.patch.dict` on the live `NEED_TO_GORIYAKU_IDS` dict, running the actual unmodified `get_compass_recommendations()` path (same technique the original correction PR used), fixed origin `(35.662443, 139.5920237)`, `direction_context={"referenceDirections": ["東"], "calculationMethod": "annual_monthly_kyusei_v1"}` (same fixture as the original 5-Purpose correction, for direct comparability):

| Need Tag | Before Top3 | After Top3 | Churn |
|---|---|---|---|
| relationship | 明治神宮/赤坂氷川神社/日枝神社 (score_need=1 each) | **identical** | `NO_CHANGE` |
| health | 乃木神社/靖國神社/長太稲荷神社(fallback) | **identical** | `NO_CHANGE` |
| mental | 明治神宮/赤坂氷川神社/靖國神社 (score_need=1 each) | **identical** | `NO_CHANGE` |
| rest | 乃木神社/靖國神社/長太稲荷神社(fallback) | **identical** | `NO_CHANGE` |
| family | 明治神宮/赤坂氷川神社/日枝神社 (score_need=1 each) | **identical** | `NO_CHANGE` |
| travel_safe | 長太稲荷神社(fallback,dup)/長太稲荷神社(fallback,dup)/明治神宮(fallback) — all score_need=0, matched=[] | **明治神宮 (score_need=1, matched=['travel_safe'], reason: "交通安全のご利益で知られる…")** / 長太稲荷神社(fallback,dup) / 長太稲荷神社(fallback,dup) | `EXPECTED_MAPPING_CORRECTION` |

The 5 `NO_CHANGE` results are mathematically expected, not merely observed: `need_tags_to_goriyaku_ids()` can only ever match an id that exists on some shrine's `goriyaku_tags`, and ids 42–45 do not exist anywhere in the master (Section 6) — removing a reference to a nonexistent id cannot change any computation. `travel_safe`'s single-slot churn (明治神宮 newly matching via `交通安全`) is the audit's predicted, and now measured, real effect: separately confirmed via direct DB query that the `travel_safe`-relevant candidate pool (shrines carrying any of `{3, 13, 14}`) grew from 6 shrines (old `{10, 22, 23}`) to 10 shrines (new `{3, 13, 14}`) nationwide, of which only 1 fell within this particular fixed origin/direction/distance candidate pool.

**Expected churn count: 1** (travel_safe). **Unexpected churn count: 0.** No investigation was required.

## 10. Unchanged Mappings

love, marriage, communication, career, money, study, protection, courage, focus — all 9 verified byte-for-byte identical before/after (Section 3), including the 5 Purposes constraint #23 explicitly required to remain untouched (love/career/money/study/protection) and `focus` (left with its known-broken `{3,4,39}` mapping, per the audit's explicit scoping — see Section 12).

## 11. Remaining Semantic Mapping Gaps

**Not fixed by this PR** (unchanged from `docs/audit/goriyaku-mapping-master-integrity.md` Section 15): 8 of 15 Purposes remain structurally BROKEN at the GID-semantic layer — relationship, marriage, communication, health, mental, courage, focus, family. Of particular note, `focus`'s `{3, 4, 39}` mapping is an exact leftover copy of `study`'s pre-2545 broken mapping and was **not** touched here — it was out of scope for both the original 5-Purpose correction and this stale-ID/travel_safe correction, per this task's constraint #21 ("Do not fix the remaining broken 10 Purposes in this PR"). The audit's Section 21 recommends a second, dedicated Mapping Semantic Audit (mirroring `compass-purpose-goriyaku-mapping.md`'s DB-evidence-plus-simulation methodology) as the next follow-up track — not started by this PR.

## 12. Production Safety

Production Code change: the two files listed in Section 13's diff stat only — `backend/temples/domain/need_to_goriyaku_tag_ids.py` (dict literal edit) and its test file. Django settings, API surface, and DB schema are unaffected.
Production DB change: **NO** — all verification (Sections 7–9) ran against the existing isolated local scratch DB (`shrine_dataset_audit_local`), read-only queries and `patch.dict`-scoped simulation only. No new DB write occurred.
Migration: **none**.
Batch 17 Recommendation Evidence: **not activated** (Section 8).

## 13. Next Follow-up

A second, dedicated Mapping Semantic Audit for the remaining 8 BROKEN Purposes (relationship, marriage, communication, health, mental, courage, family — `focus`'s high-confidence finding flagged as a priority candidate within it, per `goriyaku-mapping-master-integrity.md` Section 22 item 3), pending Mother Ship authorization. Separately, whether to pursue Recommendation Evidence Review / Production activation for the 波上宮 `航海安全` PASS item (now structurally connectable, Section 8) remains a distinct, unstarted decision.
