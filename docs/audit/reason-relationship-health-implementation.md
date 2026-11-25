# Reason R1b Implementation: relationship + health

## 1. Objective

Add explicit Reason intent copy (`intent_map`) for `relationship` and
`health`, both classified `SEMANTIC_SAFE_WITH_LIMITATION` in
[semantic-followup-decision-and-pr-split.md](./semantic-followup-decision-and-pr-split.md)
Section 8. **This distinction from `SEMANTIC_SAFE` is deliberate and
preserved throughout this document and its tests — neither Need is treated
as fully semantically resolved.**

## 2. Base SHA

`origin/develop` @ `2226f01e7880adec96fd077fa85c1c9df82ca389`
(`docs: セマンティック follow-up 決定/PR分割設計 (#2598)`). Same base as
R1a (`fix/reason-focus-travel-safe`, [PR #2599](https://github.com/etsu33/jinja_app/pull/2599)),
**not** branched from R1a — see Section 3 for why. Worktree:
`/Users/morietsu/Developer/jinja_app-reason-relationship-health`, branch
`fix/reason-relationship-health`.

## 3. Dependency Note (Documented, Not Hidden)

R1b does not logically require R1a. Both touch the same `intent_map`
dictionary literal in `concierge_chat_ranking.py`, but at textually
separate lines (R1a appends after `"marriage"`; R1b appends after R1a's
own entries in the working copy this document describes, but was branched
*before* R1a existed on `develop`). Rather than stack this branch on top of
R1a's unmerged branch (a hidden dependency this task's Global Safety Rules
prohibit), this worktree was created directly from `origin/develop` at the
same base SHA as R1a. **Consequence, stated explicitly**: when both R1a
and R1b merge, a small textual merge conflict in the `intent_map` dict body
is expected (both PRs insert new keys near the same location) — trivial to
resolve (keep both sets of entries), non-semantic, and does not indicate
either PR's own correctness is in question.

## 4. Baseline

Fresh-read `intent_map`: `relationship` and `health` both absent (6 Needs
missing total pre-R1a/R1b: relationship, focus, travel_safe, health,
family, communication — R1a addresses focus/travel_safe independently).
Live-confirmed baseline:

| Need | Baseline Reason |
|---|---|
| relationship | `"縁結びのご利益で知られる縁結び神社は、今の願いを願う参拝先として適しています。"` |
| health | `"家内安全のご利益で知られる健康神社は、今の願いを願う参拝先として適しています。"` |

## 5. Semantic Limitation (Preserved, Not Resolved)

### relationship
Core meaning (interpersonal-relationship repair/improvement) is stable and
unambiguous — `SEMANTIC_SAFE` on that basis. **Limitation**: GID evidence
is `{1}` (縁結び), the identical id `love` and `marriage` both also draw
on. The Lead clause (unmodified `_build_need_lead`) will therefore often
cite `"縁結び"` for a relationship-tagged match — the same evidence label
`love`/`marriage` can also produce — so this Reason addition does not, by
itself, give `relationship` any evidence differentiated from those two
Needs. Only the free-text `user_intent` clause differs.

### health
Core meaning (general health/illness) is stable and unambiguous —
`SEMANTIC_SAFE` on that basis. **Limitation**: GID mapping
`{7,8,24,33,38}` includes id=7 (家内安全, household safety — broader than
personal health) and id=8 (福徳, general fortune). A health-tagged match
may cite Lead evidence that reads more "household" or "general fortune"
than "personal health," even though the Reason's `user_intent` clause
itself (`"健康や体調の安定"`) is always accurate to the matched Need.
`health` also has no `NEED_TAG_TO_CONSULTATION_AXIS` entry (fresh-
reconfirmed: `resolve_consultation_axis` returns `"other"` for a
health-only query) — unrelated to and unaddressed by this Reason-only PR.

Neither limitation blocks writing a *generic* Reason valid across health's
and relationship's currently supported sub-intents — both copy candidates
were live-verified across multiple representative sub-intent phrasings
(Section 7).

## 6. Selected Copy

| Need | Copy | Source |
|---|---|---|
| relationship | `"人間関係の改善や修復"` | `KEYWORDS["relationship"]` (`人間関係`, `職場`, `上司`, `同僚`, `家族`, `親子`, `友達`, `対人`) and the `relationship_repair` axis name; deliberately excludes `love`/`marriage`'s own vocabulary (`恋愛`, `夫婦円満`). |
| health | `"健康や体調の安定"` | `KEYWORDS["health"]` (`健康`, `体調`, `病気`, `不調`, `体力`, `治す`). |

Same `"AやB"` sentence-pattern convention as every other `intent_map`
entry; no outcome/religious claim; no narrowing beyond current GID mapping.

## 7. Before / After

| Need | Before | After |
|---|---|---|
| relationship | `"...今の願いを願う参拝先として適しています。"` | `"...人間関係の改善や修復を願う参拝先として適しています。"` |
| health | `"...今の願いを願う参拝先として適しています。"` | `"...健康や体調の安定を願う参拝先として適しています。"` |

Live-verified across sub-intents:
`職場の人間関係を改善したい`→relationship copy;
`健康でいたい`/`病気が治りますように`/`体力をつけたい`→health copy, all
three health sub-intents (general, illness, strength) correctly producing
the same, still-accurate generic copy.

## 8. Score/Ranking Invariance

`score_need`, `_score_total`, `matched_need_tags`,
`need_evidence_winner_by_tag` (GID-only for both, confirmed —
neither has a `NEED_TEXT_WEIGHTS` entry), and Top3 candidate ordering
(multi-candidate fixture) all confirmed byte-identical/unchanged before
and after. `resolve_consultation_axis`/`NEED_TO_GORIYAKU_IDS` re-confirmed
unchanged for both Needs via direct dict-equality assertions.

## 9. Regression

- Focused: `test_reason_relationship_health.py` (new, 21 tests, all
  passing).
- **One pre-existing test required an update**:
  `test_marriage_reason_copy.py::test_relationship_reason_unchanged`
  asserted relationship's Reason stayed on the generic fallback — a
  correct assumption when written (before this PR), now stale because of
  this PR's own intended change. Renamed to
  `test_relationship_reason_not_collapsed_into_marriage_copy` and updated
  to assert the new, correct Reason text, while preserving the test's
  actual protective invariant unchanged: relationship's Reason must never
  contain marriage's copy (`"良縁や夫婦円満"` still asserted absent). This
  is a understood, traced fix to the change this PR itself makes — not an
  assertion weakened to force a pass.
- Full focused set (141 tests: new file + `test_marriage_reason_copy.py` +
  `test_marriage_interpreter_coverage.py` +
  `test_need_labels_ja_completeness.py` + explanation/protection/Compass
  suites): **141 passed, 0 failed**.
- Full backend suite: **1790 passed, 15 skipped (pre-existing categories
  only), 0 failed**.
- Top3 churn: 0. Score churn: 0. Reason-only change (plus the one
  documented, understood test-text update above).

## 10. Production Safety

Production change is exactly 12 inserted lines (2 dict entries + 10
comment lines) in `concierge_chat_ranking.py`. No Interpreter, Need
normalization, Mapping, Axis, Text Evidence, C1, Ranking, or Lead file
touched. `test_marriage_reason_copy.py` was modified (test file only, 8
lines) for the reason documented in Section 9.

## 11. Out of Scope

`focus`/`travel_safe` (R1a, separate PR, `SEMANTIC_SAFE`, no limitation
note required). `communication`/`family` (decision-gated). Any
Interpreter, Mapping, Axis, Text Evidence, C1, Ranking, or Lead change.
`health`'s missing consultation-axis entry (unaddressed, unrelated to
Reason copy).

## 12. STOP

Draft PR only. Not merged.
