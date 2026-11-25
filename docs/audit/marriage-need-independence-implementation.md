# Marriage Need Independence Implementation

> Implements the Mother Ship-approved separation of `marriage` from `love`. Removes the active `marriage → love` alias in both independent copies, corrects the marriage mapping to `{1, 18}`, and updates every test that intentionally pinned the previous alias behavior. Does not add Reason copy. Does not fix the separately-documented interpreter coverage gap for existing-marriage phrasing.

## 1. Scope

Narrow implementation: (1) remove `"marriage": "love"` from every active `NEED_TAG_ALIASES` copy, (2) correct `NEED_TO_GORIYAKU_IDS["marriage"]` from `{1, 27, 29}` to `{1, 18}`, (3) update affected tests, (4) verify expected semantic churn only. `love`/`relationship`/`communication`/`mental`/`courage` mappings and behavior are unchanged. C1, Ranking, Direction, Distance, Lead, Reason templates, `NEED_TEXT_WEIGHTS`, consultation-axis taxonomy, canonical `GoriyakuTag` master, DB, migrations, Seeds, and frontend/UI are all unchanged.

## 2. Base SHA

`origin/develop` at `0edf0d55ba295043539faa76727600b737be5d4d` (`docs: audit marriage and love alias boundary (#2585)`), after that PR was found still open/CI-pending at Phase 0 and merged with explicit Mother Ship authorization. `git log --oneline fd63271f..0edf0d55`: single commit, PR #2585 only. Worktree: `/Users/morietsu/Developer/jinja_app-marriage-need-independence`, branch `fix/marriage-need-independence`.

## 3. Audit Source

`docs/audit/marriage-love-alias-boundary.md` — Section 21 Decision (`PRODUCT_SEMANTIC_DECISION_REQUIRED`), Section 22 Follow-up Scope (the exact implementation plan this PR executes), Section 14 Marriage Mapping Assessment (1 VALID / 0 QUESTIONABLE / 2 INVALID, `{1,18}` corrected set), Section 6 Alias Authority (confirms exactly two active `NEED_TAG_ALIASES` copies).

## 4. Alias Before/After

Both active copies confirmed and edited (fresh-read, re-verified there is no third copy — `need_to_goriyaku_tag_ids.py`'s own reference to "NEED_TAG_ALIASES" is prose in a comment, not a table):

| File | Before | After |
|---|---|---|
| `backend/temples/services/concierge_chat_ranking.py` | `NEED_TAG_ALIASES["marriage"] = "love"` present | Removed. `"romance": "love"` (and all other non-marriage entries) unchanged |
| `backend/temples/services/concierge_chat_need.py` | `NEED_TAG_ALIASES["marriage"] = "love"` present | Removed. `"romance": "love"` (and all other non-marriage entries) unchanged |

Confirmed after edit: `normalize_need_tag("marriage") == "marriage"` and `_normalize_need_tag("marriage") == "marriage"` (both modules) — marriage survives normalization unchanged. `normalize_need_tag("romance") == "love"` unchanged (verified, `test_love_synonym_alias_is_unchanged`).

## 5. Mapping Before/After

```
"marriage": {1, 27, 29}  ->  "marriage": {1, 18}
```

`27` (出世運) and `29` (芸能運) removed — both fresh-classified INVALID (docs/audit/marriage-love-alias-boundary.md Section 14). `18` (夫婦円満) added — the master's single clearest marriage-specific canonical label, previously unused by any Need's mapping in a semantically-correct way (misassigned to `courage`, still INVALID there, unchanged by this PR per constraint #15 — `courage`'s own cleanup remains a separate, un-authorized-here decision). `1` (縁結び) retained, shared with `love`/`relationship` as before.

## 6. Natural-Language Results

Traced via the real, ranking-affecting path (`extract_need_tags` → `resolve_need_payload`), fixed Compass fixture (`origin=(35.662443, 139.5920237)`, `direction_context={"referenceDirections": ["東"]}`, identical to every prior audit/correction in this chain):

| Query | Raw extracted | Normalized | Consultation axis | Resolved GIDs |
|---|---|---|---|---|
| 新しい出会いがほしい | `['love']` | `['love']` | relationship_repair | `{1,20}` |
| 恋愛を成就させたい | `['love']` | `['love']` | relationship_repair | `{1,20}` |
| 結婚したい | `['marriage']` | `['marriage']` | **`other`** (no dedicated entry, pre-existing absence — Section 11) | `{1,18}` |
| 結婚につながる良縁がほしい | `['marriage']` | `['marriage']` | `other` | `{1,18}` |
| 夫婦関係を整えたい | `['mental','rest']` | `['mental','rest']` | restart_mindset, rest_healing | `{7,8,11,16,26,28,38}` — **unchanged, marriage not reached** (Section 12) |
| 人間関係を見直したい | `['relationship']` | `['relationship']` | relationship_repair | `{1}` |

`love` and `relationship` results are identical to their pre-PR baselines (re-confirmed against `docs/audit/marriage-love-alias-boundary.md` Sections 7/9). `結婚したい`/`結婚につながる良縁がほしい` now correctly resolve as `marriage`, not `love` — the intended fix.

Compass `purpose="marriage"` (fixed fixture, live `get_compass_recommendations`):

```
Top3 (AFTER): 明治神宮 / 赤坂氷川神社 / 芝大神宮
matched=['marriage'] for all three, winner={'marriage': 'gid'}, all via id=1 (縁結び)
reason (unchanged, generic): "縁結びのご利益で知られる〈shrine〉は、今の願いを願う参拝先として適しています。"
```

Matches exactly the corrected-mapping counterfactual predicted in `marriage-love-alias-boundary.md` Section 13-C (no id=18-carrying shrine falls within this particular candidate pool — expected, only 1 shrine nationwide carries it).

## 7. Ranking Churn

| Change | Classification |
|---|---|
| `purpose="marriage"` Top3 changes from love-identical (東京大神宮/明治神宮/赤坂氷川神社, love-flavored reason) to marriage-independent (明治神宮/赤坂氷川神社/芝大神宮, generic reason) | `EXPECTED_ALIAS_REMOVAL` |
| Within the new marriage Top3, evidence is `{1,18}`-driven rather than the old (never-actually-read) `{1,27,29}` | `EXPECTED_MAPPING_CORRECTION` |
| id=18 (夫婦円満)'s real, if sparse (1 shrine nationwide), differentiating effect not visible in this fixture | `DATA_SPARSITY` |
| Consultation axis for marriage-tagged consultations now resolves `other` instead of inheriting `love`'s `relationship_repair` via the alias | `EXPECTED_ALIAS_REMOVAL` side-effect, documented (Section 11), not fixed |
| `夫婦関係を整えたい` still fails to reach `marriage`/`love`/`relationship` at all | `FALLBACK` — pre-existing, confirmed unchanged by this PR (Section 12) |
| 5 pre-existing tests broke and were updated (Section 8) | `EXPECTED_ALIAS_REMOVAL` — each traced to a query containing a domain-level marriage keyword (良縁/ご縁/夫婦円満) previously relying on the alias to resolve as `love` |

**Unexpected churn outside marriage-related fixtures: 0.** Every failure encountered during Phase 12 (Section 8) traced to a query literally containing `結婚`/`婚活`/`夫婦円満`/`良縁`/`ご縁` — no unrelated Need tag, ranking mechanism, or scoring path was affected.

## 8. love Regression

Hard gate, confirmed:

- `NEED_TO_GORIYAKU_IDS["love"] == {1, 20}` — unchanged (pinned test, `test_love_mapping_matches_audited_correction`, passing)
- Compass `purpose="love"` Top3 (fixed fixture): 東京大神宮/明治神宮/赤坂氷川神社, `matched=['love']`, `winner={'love':'text'}`, reason `"...恋愛や良縁を願う参拝先..."` — **byte-identical to the pre-PR baseline**, re-confirmed this session
- `test_love_phrasing_still_resolves_to_love`, `test_love_match_is_unaffected_and_still_produces_love_reason`, `test_love_normalizes_to_love` — all passing, unchanged assertions

3 pre-existing tests needed query-text changes (not assertion weakening) because they used `縁結び`/`良縁`/`ご縁`/`夫婦円満` as a *stand-in* for "a love query" — these words were never actually in `love`'s own keyword list (`恋愛`/`恋`/`復縁`/`片思い`/`両思い`/`出会い`/`告白`); they were always marriage-domain keywords that only *reached* `love` via the now-removed alias. Replaced with genuine love-only phrasing (`出会い`, `復縁`) that exercises the same code path with the same intent, per the instruction not to weaken assertions merely to make tests pass.

## 9. relationship Regression

Hard gate, confirmed:

- `NEED_TO_GORIYAKU_IDS["relationship"] == {1}` — unchanged
- `人間関係を見直したい` → `['relationship']`, unchanged, does not collapse into `marriage` or `love`
- `test_relationship_is_not_in_either_alias_table`, `test_relationship_normalizes_to_relationship_not_love`, and all 4 `test_pr2409_*`/`test_relationship_*` regression tests from `test_concierge_relationship_love_separation.py` — all passing unchanged (these tests were not touched except for the two marriage-specific tests described in Section 4/6, which are separate functions)
- Compass `purpose="relationship"` Top3 (fixed fixture): 明治神宮/赤坂氷川神社/芝大神宮, `matched=['relationship']` — same composition as `marriage`'s new Top3 (both currently draw solely on shared id=1 in this fixture), which is expected and consistent with the pre-existing, accepted precedent of `love`/`relationship`/`marriage` sharing id=1 — not a new collapse between `relationship` and `marriage`

## 10. Consultation-Axis Result

`marriage` has **no** `NEED_TAG_TO_CONSULTATION_AXIS` entry, before or after this PR (fresh-confirmed; this dict was not modified — constraint #13 "do not add new consultation axis" was read to also preclude adding a `marriage` entry to reuse an existing axis, since the task's explicit implementation scope was alias removal + mapping correction only, not touching `consultation_axis.py`). **Consequence, newly exposed by this PR**: before, a marriage-tagged consultation's axis lookup used `"love"` as the key (since the tag was already collapsed by the time the axis lookup ran) and transitively got `relationship_repair`. After, the axis lookup uses `"marriage"` directly, which has no entry, and resolves to the `other` fallback axis instead. This is a real, observed side effect (Section 6's trace), not a defect introduced by editing `consultation_axis.py` (that file is untouched) — it is documented here as a known consequence, not fixed, consistent with the task's explicit scope.

## 11. Known Reason Gap

**`KNOWN_MINOR_COPY_GAP`** — confirmed still present, not fixed in this PR. `purpose="marriage"` now correctly matches via id=1/id=18, but the Reason text remains the generic `"...のご利益で知られる〈shrine〉は、今の願いを願う参拝先として適しています。"` rather than a marriage-flavored equivalent of `love`'s `"...恋愛や良縁を願う参拝先..."`, because no `intent_map`/`_build_need_lead` fallback entry exists for `marriage` (Section 6/18 of the audit doc). Per this task's explicit constraint, no Reason copy was added.

## 12. Known Interpreter Gap

**`MARRIAGE_INTERPRETER_COVERAGE_GAP`** — confirmed still present, not fixed. `夫婦関係を整えたい` ("want to improve our marital relationship") — a real, existing-marriage phrasing — still extracts `['mental', 'rest']`, never `marriage`, `love`, or `relationship` (re-confirmed this session, identical to the audit's finding). This is an upstream interpreter-vocabulary issue (`NEED_KEYWORDS`/`KEYWORDS` overlap with `mental`/`rest` on "整えたい"), independent of and unaffected by the alias/mapping change in this PR. Per this task's explicit constraint, not fixed here.

## 13. Production Safety

Production Code change: the 3 non-test files listed in Section 4/5/15 — `need_to_goriyaku_tag_ids.py`, `concierge_chat_ranking.py`, `concierge_chat_need.py`. C1, Ranking weights, Direction, Distance, Lead, Reason templates, `NEED_TEXT_WEIGHTS`, consultation-axis taxonomy, canonical `GoriyakuTag` master — all confirmed unchanged (Section 15).
Production DB change: **NO** — all verification ran against the existing isolated local scratch DB, read-only queries and live-code (not mocked) execution against the fixed audit fixture only.
Migration: **none**. New taxonomy: **none**. New Need tag: **none** (marriage already existed in `NEED_TAGS`).

## 14. Next Follow-up

- The `KNOWN_MINOR_COPY_GAP` (Section 11) — a small, low-risk `intent_map`/`_build_need_lead` addition for `marriage`, following the same pattern already used for other Needs
- The `MARRIAGE_INTERPRETER_COVERAGE_GAP` (Section 12) — independent interpreter-vocabulary work for existing-marriage phrasing, out of scope for both the audit and this PR
- Whether `marriage` should receive its own `NEED_TAG_TO_CONSULTATION_AXIS["marriage"] = "relationship_repair"` entry (Section 10), reusing the existing axis rather than falling back to `other` — not authorized or performed in this PR, a small candidate follow-up
- `communication`/`mental`/`courage` remain the 3 other `MULTI_LAYER_DESIGN_REQUIRED` Needs from `docs/audit/remaining-product-decision-need-responsibilities.md`, untouched by this PR
- `id=18`'s continued (unchanged) misassignment to `courage` (still INVALID there) remains an open item for that Need's own eventual follow-up
