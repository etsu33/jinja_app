# Marriage Consultation Axis Implementation

> Connects the independent `marriage` Need to the existing `relationship_repair` consultation axis. Does not modify Interpreter or Reason. `marriage` mapping (`{1, 18}`), alias state (absent), `love`, and `relationship` are unchanged.

## 1. Scope

Single-line implementation: add `"marriage": "relationship_repair"` to `NEED_TAG_TO_CONSULTATION_AXIS` (the sole active copy). No other consultation axis, Need tag, mapping, alias, interpreter keyword, C1, Ranking weight, Lead, Reason template, Direction, Distance, DB, Model, migration, Seed, or frontend/UI change.

## 2. Base SHA

`origin/develop` at `f6a84478dcc8001b3a85786750739aeeafcd6a1d` (`docs: audit marriage consultation and interpreter coverage (#2588)`). `git log --oneline b7556455..f6a84478`: single commit, PR #2588 only. Worktree: `/Users/morietsu/Developer/jinja_app-marriage-consultation-axis`, branch `fix/marriage-consultation-axis`.

Fresh-confirmed baseline: `NEED_TAG_ALIASES` has no `"marriage"` entry (both copies); `NEED_TO_GORIYAKU_IDS["marriage"] == {1, 18}`; `love`/`relationship` mappings unchanged; `resolve_consultation_axis(query="結婚したい", need_tags=["marriage"])` returned `axis="other", source="fallback"` before this change.

## 3. Audit Source

`docs/audit/marriage-consultation-interpreter-coverage.md` Section 8 (`SAFE_TO_REUSE`), Section 21 (`THREE_SEPARATE_PRS`, this PR implements the first — Axis only), Section 22 (Future Regression Gates, directly used to construct Section 7/8's verification below).

## 4. Axis Before

`NEED_TAG_TO_CONSULTATION_AXIS` had no `"marriage"` key. `resolve_consultation_axis` for a `marriage`-tagged consultation fell through all 3 tiers (no LLM axis, no query-keyword match, no need_tags-fallback entry) to `axis="other", source="fallback"`.

## 5. Axis After

```python
NEED_TAG_TO_CONSULTATION_AXIS: Dict[str, ConsultationAxis] = {
    ...
    "love": "relationship_repair",
    "marriage": "relationship_repair",
}
```

Confirmed: only one active copy of this dict exists (`backend/temples/domain/consultation_axis.py`) — fresh-verified via repo-wide grep, no second copy (unlike `NEED_TAG_ALIASES`, which had two). `resolve_consultation_axis(query="結婚したい", need_tags=["marriage"])` now returns `axis="relationship_repair", source="need_tags"`.

## 6. Runtime Results

5 required queries, real production path:

| Query | Normalized Need | Axis (before → after) | GIDs |
|---|---|---|---|
| 結婚したい | `['marriage']` | `other` → `relationship_repair` | `{1,18}` |
| 結婚につながる良縁がほしい | `['marriage']` | `other` → `relationship_repair` | `{1,18}` |
| 夫婦円満を願いたい | `['marriage']` | `other` → `relationship_repair` | `{1,18}` |
| 恋愛を成就させたい | `['love']` | `relationship_repair` → `relationship_repair` (unchanged) | `{1,20}` |
| 職場の人間関係を改善したい | `['relationship']` | `relationship_repair` → `relationship_repair` (unchanged) | `{1}` |

Compass fixed fixture (`origin=(35.662443, 139.5920237)`, `direction_context={"referenceDirections": ["東"]}`, identical to every prior correction in this chain):

```
purpose="marriage": Top3 = 明治神宮 / 赤坂氷川神社 / 芝大神宮 (UNCHANGED from the PR #2586 baseline)
  all matched=['marriage'], winner={'marriage': 'gid'}, reason unchanged (generic, Section 8/9)
purpose="love": Top3 = 東京大神宮 / 明治神宮 / 赤坂氷川神社 (byte-identical to baseline)
purpose="relationship": Top3 = 明治神宮 / 赤坂氷川神社 / 芝大神宮 (byte-identical to baseline)
```

No Top3 churn observed in this specific fixture — none of the 3 fixture-matched shrines for `marriage`/`love`/`relationship` carries a `history_theme` value that the `relationship_repair` boost table rewards, so the (real, confirmed-live in the audit's Section 6/7 synthetic-candidate simulation) history-theme mechanism had nothing to act on here. This is consistent with, not contradictory to, the audit's own finding — real-world churn is conditional on which shrines happen to carry a rewarded `history_theme`.

## 7. Ranking Churn

| Observation | Classification |
|---|---|
| `marriage`'s axis resolution changes `other` → `relationship_repair` | `EXPECTED_HISTORY_SIGNAL` (structural — the axis input to the existing, unmodified boost mechanism changes) |
| No score/Top3 change in the fixed Compass fixture (no rewarded `history_theme` present) | `NO_EFFECT` (in this specific fixture — the mechanism is armed but has nothing to act on) |
| Synthetic-candidate contract tests (`test_marriage_consultation_activates_same_history_theme_candidate_boost`) confirm `history_theme_candidate_boost.raw` goes from a would-be `0.0` (under `other`) to `1.0` (under `relationship_repair`) for a `history_theme="縁"` candidate | `EXPECTED_SCORE_CHANGE` (isolated, contract-level proof the mechanism is live) |
| `love`/`relationship` Top3, scores, reasons | `NO_EFFECT` — both already resolved to `relationship_repair` before this change; nothing about their own resolution path was touched |

**Unexpected churn: 0.**

## 8. Candidate Churn

Direction candidate count, Distance candidate count, and `matched_need_tags`/GID-match count were confirmed unchanged across every tested query and every Compass purpose (`marriage`/`love`/`relationship`), both via the fixed-fixture live run (Section 6) and via the audit's own prior synthetic simulation (Section 6/7 of `marriage-consultation-interpreter-coverage.md`, re-verified by this PR's new contract tests). **Candidate pool changes: 0**, as expected — the axis is consulted only inside `_attach_breakdown`, downstream of Direction/Distance filtering and downstream of GID/Text matching itself.

## 9. love Regression

Hard gate, confirmed:

- `恋愛を成就させたい` → `['love']`, unchanged
- `resolve_consultation_axis` for `love` → `relationship_repair`, unchanged (love already had this entry before this PR)
- Compass `purpose="love"` Top3/matched/winner/reason: byte-identical to the pre-PR baseline
- `test_love_consultation_activates_same_history_theme_candidate_boost` (pre-existing, untouched) still passes
- **Unexpected love churn: 0**

## 10. relationship Regression

Hard gate, confirmed:

- `職場の人間関係を改善したい` → `['relationship']`, unchanged
- `resolve_consultation_axis` for `relationship` → `relationship_repair`, unchanged (already had this entry)
- `NEED_TO_GORIYAKU_IDS["relationship"] == {1}`, unchanged
- Compass `purpose="relationship"` Top3: byte-identical to the pre-PR baseline
- All 4 `test_pr2409_*` and `test_relationship_consultation_axis_sharing_does_not_reintroduce_love_reason` tests (pre-existing, untouched) pass
- **Unexpected relationship churn: 0**

## 11. Interpreter Gap Unchanged

**`KNOWN_INTERPRETER_GAP_UNCHANGED`** — re-confirmed this session: `夫婦関係を整えたい` still resolves to `['mental', 'rest']`, never `marriage`. `consultation_interpreter.py`/`need_tags.py` were not touched by this PR.

## 12. Reason Gap Unchanged

**`KNOWN_REASON_GAP_UNCHANGED`** — re-confirmed this session: `"marriage"` is still absent from `_build_need_reason_text`'s `intent_map` (`concierge_chat_ranking.py`, untouched by this PR). A `marriage`-tagged Reason still falls to the generic `"今の願い"` phrasing, confirmed identical to the PR #2586 baseline in Section 6's Compass trace.

## 13. Production Safety

Production Code change: `backend/temples/domain/consultation_axis.py` only — one dict entry added, plus documentation comments. C1, Ranking weights, Lead, Reason templates, `NEED_TEXT_WEIGHTS`, interpreter keywords, canonical `GoriyakuTag` master, `NEED_TO_GORIYAKU_IDS`, `NEED_TAG_ALIASES` — all confirmed unchanged (Section 6/9/10/11/12).
Production DB change: **NO**.
Migration: **none**. New taxonomy/new consultation axis: **none** — `relationship_repair` is an existing, already-shipped axis, reused, not created.

## 14. Follow-up Boundaries

Per `docs/audit/marriage-consultation-interpreter-coverage.md` Section 21/22, the remaining two independent tracks — Interpreter (`夫婦仲`/`夫婦関係` keyword candidates, Section 12/13/14 of that audit) and Reason (`intent_map["marriage"]`, informed by `concierge_plan.py`'s existing "良縁成就" wording) — are **not** started by this PR and remain separate, independently-authorizable follow-ups.
