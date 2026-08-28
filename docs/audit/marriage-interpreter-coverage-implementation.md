# Marriage Interpreter Coverage Implementation

> Closes the two remaining interpreter gaps for existing-marriage phrasing (`docs/audit/marriage-consultation-interpreter-coverage.md`). Adds `夫婦関係`/`夫婦仲` to both active copies of marriage's keyword list. Does not modify Reason copy, marriage mapping, marriage axis, or any other Need's mapping/vocabulary.

## 1. Scope

Add exactly two narrow phrases (`夫婦関係`, `夫婦仲`) — both from the existing `夫婦`-root family already anchored by `夫婦円満` — to `temples/domain/need_tags.py`'s `KEYWORDS["marriage"]` (the real, ranking-affecting extraction path) and `temples/services/consultation_interpreter.py`'s `NEED_KEYWORDS["marriage"]` (kept synchronized per the pre-existing "both identical" invariant). No new priority model, no mental/rest keyword change, no Reason copy, no mapping/axis change.

## 2. Base SHA

`origin/develop` at `42f7fe7dce3ab906dcffb0a6173b3c4b628bac25` (`fix: connect marriage to relationship repair axis (#2590)`). `git log --oneline f6a84478..42f7fe7d`: `f2b38d21` (PR #2589, frontend-only, `apps/web/`, confirmed zero backend overlap via `git diff-tree`) then `42f7fe7d` (PR #2590, this implementation's prerequisite). Worktree: `/Users/morietsu/Developer/jinja_app-marriage-interpreter-coverage`, branch `fix/marriage-interpreter-coverage`.

Fresh-confirmed baseline: `NEED_TAG_ALIASES` has no `"marriage"` entry; `NEED_TO_GORIYAKU_IDS["marriage"] == {1, 18}`; `NEED_TAG_TO_CONSULTATION_AXIS["marriage"] == "relationship_repair"`; `夫婦仲を良くしたい` → `tags=[]`; `夫婦関係を整えたい` → `tags=['mental', 'rest']`.

## 3. Audit Source

`docs/audit/marriage-consultation-interpreter-coverage.md` Section 12 (root cause: `MISSING_MARRIAGE_KEYWORD` for 夫婦仲, `OVERBROAD_MENTAL_KEYWORD + OVERBROAD_REST_KEYWORD` for 夫婦関係), Section 13 (SAFE candidates, exact phrases used here), Section 14 (collision risk LOW for both, checked against love/relationship/mental/rest/family).

## 4. Interpreter Baseline

Fresh-read located **three** relevant structures (not assumed to be only one):

| Location | Role |
|---|---|
| `temples/domain/need_tags.py` `KEYWORDS["marriage"]` | Substring-match vocabulary, consumed by `extract_need_tags()` — the real, production, ranking-affecting path (via `resolve_need_payload`) |
| `temples/domain/need_tags.py` `REGEX["marriage"]` | A supplementary regex layer (`r"(縁結び|良縁|結婚)"`) — partially redundant with `KEYWORDS`, does not cover 婚活/結縁/ご縁/夫婦円満. Not modified — the existing 3-word regex still fires correctly for its own subset; the new phrases are covered by the `KEYWORDS` substring layer alone, consistent with how `family`/`focus`/`money`/`communication`/`health`/`relationship`/`travel_safe` (Needs with no `REGEX` entry at all) already work |
| `temples/services/consultation_interpreter.py` `NEED_KEYWORDS["marriage"]` | The shadow-layer (`interpret_consultation`/`build_need_profile`, confirmed non-ranking-affecting in the prior audit) copy, kept textually identical to `KEYWORDS["marriage"]` by existing convention |

**New, decisive finding from this fresh read**: `need_tags.py` also defines `NEED_PRIORITY` (line 30), a 15-item ranked list used by `extract_need_tags()`'s final "pick by priority" step. `"marriage"` is **priority index 1** (second, right after `"protection"`), while `"mental"` is index 8 and `"rest"` is index 13. This existing, unmodified ordering is what makes Phase 5's multi-Need case resolve safely (Section 7).

## 5. Safe Phrase Candidates

Re-verified via fresh, isolated `patch.object` simulation (not blind trust in the prior audit) before any code edit:

| Candidate | Collision check (love/relationship/mental/rest/family) | Classification |
|---|---|---|
| `夫婦仲` | No overlap with any other Need's `KEYWORDS`/`NEED_KEYWORDS` list (checked directly) | `SAFE_DIRECT_ADD` |
| `夫婦関係` | No overlap with any other Need's own keyword list; the query it targets (`夫婦関係を整えたい`) independently also hits `mental`/`rest` via a different word (`整えたい`) in the same sentence — not a collision *caused* by this candidate, but a pre-existing co-occurrence | `SAFE_WITH_PRIORITY_HANDLING` — resolved by the existing, unmodified `NEED_PRIORITY` ordering (Section 4/6), not a new rule |

Simulation (read-only `unittest.mock.patch.object` on `need_tags.KEYWORDS`, prior to any tracked-file edit) confirmed both classifications empirically before implementation, per the task's "do not implement until classification is recorded" instruction.

## 6. `夫婦仲` Result

```
夫婦仲を良くしたい: tags=[] -> tags=['marriage']
hits: {'marriage': ['夫婦仲']}
```

Clean, isolated fix — no other Need's hits changed.

## 7. `夫婦関係` Result

```
夫婦関係を整えたい: tags=['mental','rest'] -> tags=['marriage','mental','rest']
hits: {'marriage': ['夫婦関係'], 'mental': ['整えたい'], 'rest': ['整えたい']}
```

**Result: B (marriage + mental/rest)**, per the audit's own Phase 5 classification options — not A (marriage only, mental/rest's own `整えたい` match is real and unmodified) and not C (marriage lost — it is not; `NEED_PRIORITY` places it first). `marriage` is listed **first** in the resolved tag list, ahead of `mental`/`rest`, purely as a consequence of the existing, unmodified priority ordering (`NEED_PRIORITY[1] < NEED_PRIORITY[8] < NEED_PRIORITY[13]`).

End-to-end (`build_chat_recommendations`) confirms this is a **real** match, not merely a cosmetic list-ordering artifact: a candidate carrying marriage's own GID evidence (`goriyaku_tag_ids=[1]`) for this exact query correctly produces `matched_need_tags=['marriage']` in its breakdown.

## 8. Multi-Need Handling

**No new priority model was invented.** `NEED_PRIORITY` (`need_tags.py`) is unmodified — this PR relies entirely on the pre-existing ordering, exactly per the task's Phase 6 instruction ("If the existing contract already specifies how a more specific marriage phrase should interact with broad mental/rest matches, implement that existing rule"). `PRODUCT_SEMANTIC_PRIORITY_DECISION_REQUIRED` was **not** triggered — the existing contract was sufficient and was used as-is.

## 9. Coverage Before/After

| | Before | After |
|---|---:|---:|
| Marriage-seeking (4 cases) | 4/4 = 100% | 4/4 = 100% (unchanged, hard requirement met) |
| Existing-marriage (5 cases) | 3/5 = 60% | **5/5 = 100%** |

Existing-marriage per-case: 夫婦円満を願いたい / 結婚生活を良くしたい / パートナーとの結婚生活に悩んでいる (already correct, unaffected) + 夫婦仲を良くしたい (newly correct) + 夫婦関係を整えたい (newly includes `marriage`, per Section 7's B classification — counted correct per the task's own Phase 4 framing, "includes/resolves to marriage").

**Exact improvement: +2 cases, +40 percentage points (60% → 100%) on existing-marriage coverage.**

## 10. love Regression

Hard gate, confirmed:

- `恋愛を成就させたい` → `['love']`, unchanged
- `復縁したい` → `['love']`, unchanged
- `love` never appears in any marriage-related query's resolved tags
- Compass `purpose="love"` Top3/matched/winner/reason: byte-identical to the pre-PR baseline (Compass uses `need_tags=[purpose_slug]` directly, not the free-text interpreter path, so it is structurally unaffected by this PR regardless)
- **Unexpected love churn: 0**

## 11. relationship Regression

Hard gate, confirmed:

- `職場の人間関係を改善したい` → `['relationship']`, unchanged
- `友人との関係を見直したい` → `[]` (pre-existing, unrelated Interpretation Gap, confirmed unchanged — not touched by this PR)
- `NEED_TO_GORIYAKU_IDS["relationship"] == {1}`, unchanged
- Compass `purpose="relationship"` Top3: byte-identical to baseline
- **Unexpected relationship churn: 0**

## 12. mental Regression

Hard gate, confirmed:

- `気持ちを整えたい` (genuinely mental/rest-only, no `夫婦`-root word present) → `['mental', 'rest']`, `marriage` does **not** appear — confirmed the new keywords do not leak into unrelated mental queries
- Compass `purpose="mental"` Top3: byte-identical to baseline
- **Unexpected mental churn: 0**

## 13. rest Regression

Hard gate, confirmed:

- `少し休みたい` → `['rest']`, unchanged, `marriage` does not appear
- Compass `purpose="rest"` Top3: byte-identical to baseline
- **Unexpected rest churn: 0**

## 14. Recommendation Runtime

For the 2 newly-fixed cases, live `build_chat_recommendations` (candidate with `goriyaku_tag_ids=[1, 18]`):

```
夫婦仲を良くしたい:
  need_tags=['marriage'], consultation_axis=relationship_repair
  matched_need_tags=['marriage'], winner={'marriage':'gid'}
  reason: "縁結びのご利益で知られる〈shrine〉は、今の願いを願う参拝先として適しています。"

夫婦関係を整えたい:
  need_tags=['marriage','mental','rest'], consultation_axis=relationship_repair
  matched_need_tags=['marriage'] (only marriage evidence present on this candidate)
  winner={'marriage':'gid'}
  reason: identical generic text (Section 15)
```

Both confirm: Need = `marriage`, axis = `relationship_repair`, mapping = `{1, 18}` (via the `need_evidence_winner_by_tag` / matched-GID chain) — exactly as required.

## 15. Reason Gap Unchanged

**`KNOWN_REASON_GAP_UNCHANGED`** — re-confirmed this session: `intent_map["marriage"]` still absent from `_build_need_reason_text` (`concierge_chat_ranking.py`, untouched by this PR). Both newly-fixed cases produce the same generic `"今の願い"` fallback phrasing observed in every prior audit/implementation in this chain. Not modified, per explicit constraint.

## 16. Product Decision Required

**None.** `PRODUCT_SEMANTIC_PRIORITY_DECISION_REQUIRED` was not triggered — the existing `NEED_PRIORITY` contract fully and safely resolved the one multi-Need case (Section 7/8) without requiring any new decision.

## 17. Production Safety

Production Code change: `temples/domain/need_tags.py` and `temples/services/consultation_interpreter.py` — two keyword-list entries each, plus documentation comments. `NEED_TO_GORIYAKU_IDS`, `NEED_TAG_ALIASES`, `NEED_TAG_TO_CONSULTATION_AXIS`, `NEED_TEXT_WEIGHTS`, `NEED_PRIORITY`, C1, Ranking weights, Lead logic, Reason templates, Direction, Distance — all confirmed unchanged (Sections 10–13, 15).
Production DB change: **NO**.
Migration: **none**. New taxonomy: **none**.

## 18. Follow-up Boundaries

Per `docs/audit/marriage-consultation-interpreter-coverage.md` Section 21/22, the third and final independent track — Reason (`intent_map["marriage"]`, informed by `concierge_plan.py`'s existing "良縁成就" wording) — remains **not started** by this PR and is a separate, independently-authorizable follow-up. With this PR, both the Axis (#2590) and Interpreter tracks are complete; only Reason remains open in the responsibility matrix first established in `marriage-consultation-interpreter-coverage.md` Section 18.
