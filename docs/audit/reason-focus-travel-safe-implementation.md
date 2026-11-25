# Reason R1a Implementation: focus + travel_safe

## 1. Objective

Add explicit Reason intent copy (`intent_map`) for `focus` and
`travel_safe`, both classified `SEMANTIC_SAFE` in
[semantic-followup-decision-and-pr-split.md](./semantic-followup-decision-and-pr-split.md)
Section 8 — no open product question blocks a generic Reason for either.
Explanation-only; does not alter Recommendation behavior.

## 2. Base SHA

`origin/develop` @ `2226f01e7880adec96fd077fa85c1c9df82ca389`
(`docs: セマンティック follow-up 決定/PR分割設計 (#2598)`), created after
confirming PR #2596 (`fix: complete Japanese need labels`) was already
merged (merge commit `86a5764f9df8e43aea351d52119681f292492057`, all CI
green, exact expected 4-file scope, no unexpected changes). Worktree:
`/Users/morietsu/Developer/jinja_app-reason-focus-travel-safe`, branch
`fix/reason-focus-travel-safe`.

## 3. Baseline Fallback

Fresh-read `intent_map` inside `_build_need_reason_text`
(`concierge_chat_ranking.py`): 9 entries present (study, mental, rest,
love, career, money, courage, protection, marriage); `focus` and
`travel_safe` absent. Live-confirmed baseline:

| Need | Baseline Reason |
|---|---|
| focus | `"学業成就のご利益で知られる集中神社は、今の願いを願う参拝先として適しています。"` |
| travel_safe | `"交通安全のご利益で知られる交通安全神社は、今の願いを願う参拝先として適しています。"` |

The name-less twin `mapping` dict (unreachable dead code, since
`build_recommendation_reason` always passes a real shrine `name`) was
re-checked and confirmed still unreachable and still missing both Needs —
not modified.

## 4. Selected Copy

| Need | Copy | Source |
|---|---|---|
| focus | `"集中や習慣づくり"` | Derived from `KEYWORDS["focus"]` (`集中`, `習慣`, `継続`, `怠け`, `先延ばし`, `やる気`, `ルーティン`) and `NEED_LABELS_JA["focus"]`'s existing `"集中・継続"` wording; matches the established `"AやB"` two-noun-phrase sentence pattern used by every other `intent_map` entry. |
| travel_safe | `"移動や旅の安全"` | Derived from `KEYWORDS["travel_safe"]` (`旅行`, `旅`, `出張`, `移動`, `交通安全`, `安全祈願`) and `NEED_LABELS_JA["travel_safe"]`'s existing `"移動・安全"` wording; same sentence pattern. |

Neither makes an outcome or religious claim, neither narrows the Need
beyond its current GID mapping (`focus`: `{9,10}`, shared with `study`;
`travel_safe`: `{3,13,14}`), and both preserve the existing
`"{lead}のご利益で知られる{name}は、{user_intent}を願う参拝先として適しています。"`
sentence structure unchanged.

## 5. Rationale

`focus`'s meaning (concentration/habit-forming) and `travel_safe`'s meaning
(safety while traveling/moving) are both stable and unambiguous across
every layer already audited — no collision, no taxonomy gap, no axis
conflict blocks writing a generic Reason valid across their currently
supported sub-intents.

## 6. Implementation

Added exactly two entries to `intent_map` (the reachable, with-name branch
of `_build_need_reason_text`):

```python
"focus": "集中や習慣づくり",
"travel_safe": "移動や旅の安全",
```

No other dict, function, or file touched.

## 7. Before / After

| Need | Before | After |
|---|---|---|
| focus | `"...今の願いを願う参拝先として適しています。"` | `"...集中や習慣づくりを願う参拝先として適しています。"` |
| travel_safe | `"...今の願いを願う参拝先として適しています。"` | `"...移動や旅の安全を願う参拝先として適しています。"` |

## 8. Score/Ranking Invariance

Live-verified: `score_need`, `_score_total` (`0.65` in both single-candidate
fixtures), `matched_need_tags`, and `need_evidence_winner_by_tag`
byte-identical before and after — only the `user_intent` clause of the
Reason sentence changed. `focus`/`travel_safe` have no `NEED_TEXT_WEIGHTS`
entry (confirmed, `test_focus_and_travel_safe_have_no_text_evidence_entry`)
— evidence is GID-only by current design, unaffected by this change.
Top3 composition (multi-candidate fixture, `focus` vs. an unrelated
candidate) unchanged: the matched candidate still ranks first with the
same score gap.

## 9. Regression

- Focused: `test_reason_focus_travel_safe.py` (new, 14 tests),
  `test_need_labels_ja_completeness.py`,
  `test_concierge_explanation*.py` (×3), `test_marriage_reason_copy.py`,
  `test_marriage_interpreter_coverage.py`,
  `test_protection_explanation_coverage.py`, `test_compass_*` (×4),
  `test_concierge_primary_reason_unification_contract.py` — **203 passed,
  0 failed**.
- Full backend suite: **1783 passed, 15 skipped (pre-existing categories
  only: GDAL, PostGIS, `GOOGLE_PLACES_API_KEY`, 1 ambiguous-axis-family
  case), 0 failed**.
- Top3 churn: 0. Ranking score churn: 0. Lead churn: 0 (Lead clause
  mechanism untouched; live-verified citing the real matched GID label in
  every case). Only Reason text for `focus`/`travel_safe` changed;
  `relationship` (out of scope, belongs to R1b) reconfirmed still generic.

## 10. Production Safety

Production change is exactly 8 inserted lines (2 dict entries + 6 comment
lines) in `concierge_chat_ranking.py`. No Interpreter, Need normalization,
Mapping, Axis, Text Evidence, C1, Ranking, Lead, label, or candidate-
filtering file touched.

## 11. Out of Scope

`relationship`/`health` (R1b, `SEMANTIC_SAFE_WITH_LIMITATION`, separate
PR). `communication`/`family` (decision-gated, separate PR/packet). Any
Interpreter, Mapping, Axis, Text Evidence, C1, Ranking, or Lead change.

## 12. STOP

Draft PR only. Not merged.
