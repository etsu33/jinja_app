# Marriage Consultation Axis / Interpreter Coverage Audit

> **Status**: AUDIT ONLY. No alias, mapping, interpreter, consultation-axis, C1, Ranking, Lead, Reason, Direction/Distance, DB, Model, migration, Seed, or frontend/UI change. Read-only runtime simulation only.

## 1. Scope

For the now-independent `marriage` Need (PR #2586): determine whether it should reuse the existing `relationship_repair` consultation axis, measure what that axis decision actually changes downstream, map its current natural-language recognition coverage, root-cause the cases where existing-marriage phrasing is misclassified into `mental`/`rest`, and define the smallest safe technical follow-up split. `love`, `relationship`, `communication`, `mental`, `courage` mappings are not reopened.

## 2. Base SHA

`origin/develop` at `b755645504219d0c0983d426c43698a860d638d3` (`推薦EvidenceとDark UIの全体回帰を監査 (#2587)`). `git log --oneline 0edf0d55..b7556455`: `dfa9107f` (PR #2586, this audit's own prerequisite) then `b7556455` (PR #2587, docs-only, `docs/audit/app-wide-evidence-dark-ui-regression.md`, zero backend overlap). Worktree: `/Users/morietsu/Developer/jinja_app-marriage-consultation-audit`, branch `audit/marriage-consultation-interpreter-coverage`.

Fresh-confirmed baseline: `NEED_TAG_ALIASES` has no `"marriage"` entry in either copy; `NEED_TO_GORIYAKU_IDS["marriage"] == {1, 18}`; `love == {1,20}`, `relationship == {1}` unchanged; 0 structurally invalid mapping references.

## 3. Sources of Truth

Fresh-read this session: `docs/audit/marriage-love-alias-boundary.md`, `docs/audit/marriage-need-independence-implementation.md`, `consultation_axis.py` (`resolve_consultation_axis`, `CONSULTATION_AXIS_KEYWORDS`, `NEED_TAG_TO_CONSULTATION_AXIS`, `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` in `concierge_chat_ranking.py`), `consultation_interpreter.py` (`NEED_KEYWORDS`), `need_tags.py` (`KEYWORDS`, `extract_need_tags`), `concierge_chat_need.py` (`resolve_need_payload`), `concierge_chat.py` (confirms `resolve_consultation_axis` is called in the **real** production path at line 685, not only the shadow `interpret_consultation` layer), `_build_need_lead`/`_resolve_matched_lead_evidence`/`_build_need_reason_text` (`concierge_chat_ranking.py`), `concierge_plan.py` (`WISH_HINTS`, a separate, parallel copy-generation system).

## 4. Current Runtime Trace

Query `結婚したい`, real production path (`extract_need_tags` → `resolve_need_payload` → `resolve_consultation_axis`):

```
"結婚したい"
  → extract_need_tags(): raw=['marriage'], hits={'marriage': ['結婚','結婚']}
  → resolve_need_payload(): normalized=['marriage']  (no alias, confirmed absent)
  → resolve_consultation_axis(query="結婚したい", need_tags=['marriage']):
      tier 1 (llm_axis): not provided, skipped
      tier 2 (query keyword, CONSULTATION_AXIS_KEYWORDS): no match -- "結婚したい" contains
        none of relationship_repair's keywords (人間関係/職場の人間関係/家族との関係/
        友人との関係/対人関係/関係を整理/関係を修復/関係がうまくいかない/仲直り)
      tier 3 (need_tags fallback, NEED_TAG_TO_CONSULTATION_AXIS): "marriage" absent -> no match
      -> axis = "other", source = "fallback"
  → need_tags_to_goriyaku_ids(['marriage']) = {1, 18}
  → C1: GID_ONLY path always (marriage has no NEED_TEXT_WEIGHTS entry, confirmed --
    TEXT_ONLY/BOTH states are structurally unreachable for this Need); winner={'marriage':'gid'}
  → history_theme_candidate_boost: 0.0 always (HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS has no
    "other" row, confirmed -- .get(axis, {}) returns {})
  → Top3 (fixed Compass fixture): 明治神宮 / 赤坂氷川神社 / 芝大神宮, all matched via id=1
  → Lead: real matched GoriyakuTag label (id=1 -> "縁結び"), correctly resolved (Section 15)
  → Reason: generic fallback "...のご利益で知られる〈shrine〉は、今の願いを願う参拝先として
    適しています。" (intent_map has no "marriage" entry, confirmed, Section 16)
```

Confirms exactly the hypothesized baseline (Need=`marriage`, axis=`other`) — fresh runtime result matches prediction.

## 5. Consultation Axis Inventory

| Axis | Purpose (per `CONSULTATION_AXIS_KEYWORDS`/history-theme table) | History-theme top weights | Score contribution | Filters |
|---|---|---|---|---|
| `other` | Fallback/undetermined axis — no dedicated keyword list, no `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` row | none (boost always 0.0) | None — contributes nothing to `history_theme_candidate_boost` | none |
| `relationship_repair` | Interpersonal-relationship repair broadly (人間関係/職場/家族/友人), explicitly documented to include 恋愛 (romantic love) at the axis level too (Section 6 of `marriage-love-alias-boundary.md`) | 縁=1.0, 静寂=0.7, 守り=0.5, 再出発=0.4, 復興=0.4, 学び=0.2, 勝負=0.1 | Real, measured (Section 7) — feeds `score_need_rank_weighted`/`score_v3`'s `history_signal` component via `resolve_history_theme_candidate_boost` | none |

`relationship_repair` semantically covers **(A) marriage-seeking well** — its top-weighted theme (縁="connection/bond", 1.0) is a direct conceptual match for matchmaking-toward-marriage, the same theme already legitimately shared by `love`. It covers **(B) existing-marital-relationship less directly** — the axis's `CONSULTATION_AXIS_KEYWORDS` list (人間関係/職場の人間関係/家族との関係/友人との関係/対人関係/関係を整理/関係を修復/関係がうまくいかない/仲直り) contains general relationship-repair language that could apply to marital harmony by extension, but has no marriage-specific term. **A and B are not identical fits** — A is direct, B is looser/inherited-by-generality.

## 6. other vs relationship_repair Simulation

Read-only `patch.dict(NEED_TAG_TO_CONSULTATION_AXIS, {"marriage": "relationship_repair"})`, live `build_chat_recommendations(query="結婚したい", ...)`, two synthetic candidates (both `goriyaku_tag_ids=[1]`, one with `history_theme="縁"` at 2000m, one with no theme at 200m):

```
BASELINE (marriage -> other):
  order = [神社B(no theme, 200m), 神社A(縁テーマ, 2000m)]
  神社A: history_signal=0.0, score_v3=0.4949
  神社B: history_signal=0.0, score_v3=0.5423
  (distance dominates; theme contributes nothing)

COUNTERFACTUAL (marriage -> relationship_repair):
  order = [神社A(縁テーマ, 2000m), 神社B(no theme, 200m)]   <- ORDER FLIPPED
  神社A: history_signal=1.0, score_v3=0.5949
  神社B: history_signal=0.0, score_v3=0.5423
  (縁-theme boost overcomes the distance disadvantage)
```

- Direction candidate count: unchanged (0 in this synthetic 2-candidate fixture; axis does not touch Direction filtering, confirmed by code path — `resolve_history_theme_candidate_boost` is called only inside `_attach_breakdown`, downstream of Direction/Distance)
- Distance candidate count: unchanged (same reasoning)
- GID match count: unchanged (`matched_need_tags=['marriage']` for both candidates, both conditions)
- Text match count: unchanged (0, always — marriage has no `NEED_TEXT_WEIGHTS`)
- History-theme boost: **0.0 → 1.0** for the 縁-themed candidate — the entire measured effect
- score_v3: **0.4949 → 0.5949** for the 縁-themed candidate (`score_v3` is itself `mode: "shadow"` per the breakdown dict, but see Section 7 — the actual returned recommendation *order* changed too, confirming a live, non-shadow ranking effect, not merely the shadow score field)
- Top3 / recommendation order: **changed** — the 縁-themed, farther candidate overtakes the closer, theme-less one

## 7. Axis Churn Attribution

| Change | Classification |
|---|---|
| `history_signal` 0.0 → 1.0 for 縁-themed candidates | `CONSULTATION_AXIS_HISTORY_BOOST` |
| Recommendation order flip (縁-themed candidate overtakes closer candidate) | `RANK_ORDER_CHANGE` / `TOP3_CHANGE` |
| `matched_need_tags`, GID/Text match counts | `NO_EFFECT` |
| Direction/Distance candidate pools | `NO_EFFECT` |
| Any unrelated Need's scoring | `NO_EFFECT` (not tested directly here, but the boost function is scoped strictly to the `tag`/`consultation_axis` pair passed in for `marriage`'s own `_attach_breakdown` call) |

**Does axis selection materially change recommendation quality?** Yes, but narrowly and predictably: it activates a real, bounded ranking-magnitude mechanism (history-theme affinity) for shrines whose `history_theme` happens to be `縁` (or, to a lesser degree, `静寂`/`守り`/`再出発`/`復興`/`学び`/`勝負`) — it can reorder Top3 among *already-matched* `marriage` candidates, but (per Section 8) never creates or removes a match itself.

## 8. Axis Semantic Safety

Verified directly in Section 6's simulation: in both conditions, `matched_need_tags == ['marriage']` (Need tag never changes), the GID set consulted is always `{1, 18}` (`need_tags_to_goriyaku_ids(['marriage'])`, unaffected by axis), and `need_evidence_winner_by_tag == {'marriage': 'gid'}` (C1 winner unaffected). The axis change only ever touched `history_signal`/ranking order among candidates that had *already* matched via `marriage`'s own GID evidence — it cannot manufacture a match for a candidate that doesn't carry id=1 or id=18, and it cannot suppress one that does.

**Result: `SAFE_TO_REUSE`.** Reusing `relationship_repair` does not collapse `marriage` toward `relationship`/`love` semantics at the matching layer — it only adds a secondary, bounded ranking-refinement signal, structurally identical to how `love` and `relationship` already both use this same axis today without losing their own independent `NEED_TO_GORIYAKU_IDS` identity.

## 9. Marriage Natural Language Corpus

All 15 required cases run via the real path (`extract_need_tags` → `resolve_need_payload` → `resolve_consultation_axis`):

| # | Query | Category |
|---|---|---|
| 1 | 結婚したい | seeking |
| 2 | 結婚につながる良縁がほしい | seeking |
| 3 | 結婚相手とのご縁がほしい | seeking |
| 4 | 良い人と結婚したい | seeking |
| 5 | 夫婦関係を整えたい | existing |
| 6 | 夫婦仲を良くしたい | existing |
| 7 | 夫婦円満を願いたい | existing |
| 8 | 結婚生活を良くしたい | existing |
| 9 | パートナーとの結婚生活に悩んでいる | existing |
| 10 | 恋愛を成就させたい | control (love) |
| 11 | 復縁したい | control (love) |
| 12 | 職場の人間関係を改善したい | control (relationship) |
| 13 | 友人との関係を見直したい | control (relationship) |
| 14 | 気持ちを整えたい | control (mental) |
| 15 | 少し休みたい | control (rest) |

## 10. Interpreter Funnel

| # | Query | Keyword hits | Raw Needs | Normalized Needs | Axis | Classification |
|---|---|---|---|---|---|---|
| 1 | 結婚したい | marriage:[結婚] | [marriage] | [marriage] | other | `CORRECT_MARRIAGE` |
| 2 | 結婚につながる良縁がほしい | marriage:[良縁,結婚] | [marriage] | [marriage] | other | `CORRECT_MARRIAGE` |
| 3 | 結婚相手とのご縁がほしい | marriage:[結婚,ご縁] | [marriage] | [marriage] | other | `CORRECT_MARRIAGE` |
| 4 | 良い人と結婚したい | marriage:[結婚] | [marriage] | [marriage] | other | `CORRECT_MARRIAGE` |
| 5 | 夫婦関係を整えたい | mental:[整えたい], rest:[整えたい] | [mental,rest] | [mental,rest] | restart_mindset | `MENTAL_FALSE_POSITIVE` + `REST_FALSE_POSITIVE` |
| 6 | 夫婦仲を良くしたい | (none) | [] | [] | other | **no category fits — total miss, not a false positive; classified `GENERIC`** |
| 7 | 夫婦円満を願いたい | marriage:[夫婦円満] | [marriage] | [marriage] | other | `CORRECT_MARRIAGE` |
| 8 | 結婚生活を良くしたい | marriage:[結婚] | [marriage] | [marriage] | other | `CORRECT_MARRIAGE` |
| 9 | パートナーとの結婚生活に悩んでいる | marriage:[結婚] | [marriage] | [marriage] | other | `CORRECT_MARRIAGE` |
| 10 | 恋愛を成就させたい | love:[恋愛,恋] | [love] | [love] | relationship_repair | `CORRECT_LOVE_CONTROL` |
| 11 | 復縁したい | love:[復縁] | [love] | [love] | relationship_repair | `CORRECT_LOVE_CONTROL` |
| 12 | 職場の人間関係を改善したい | relationship:[人間関係,職場] | [relationship] | [relationship] | relationship_repair | `CORRECT_RELATIONSHIP_CONTROL` |
| 13 | 友人との関係を見直したい | (none — NEED_KEYWORDS gap, pre-existing per PR #2409's own test) | [] | [] | relationship_repair (via query-level tier 2) | `CORRECT_RELATIONSHIP_CONTROL` (axis correct even though need_tags extraction is a known, pre-existing, unrelated gap) |
| 14 | 気持ちを整えたい | mental:[気持ちを整えたい,整えたい], rest:[整えたい] | [mental,rest] | [mental,rest] | restart_mindset | `CORRECT_MENTAL_CONTROL` + `CORRECT_REST_CONTROL` (this IS mental/rest's own correct scope — not a false positive when the query is genuinely about mental/rest) |
| 15 | 少し休みたい | rest:[休みたい] | [rest] | [rest] | rest_healing | `CORRECT_REST_CONTROL` |

**Interesting side-finding**: case 13's axis resolves correctly via **tier 2** (query-level `CONSULTATION_AXIS_KEYWORDS` match on "友人との関係") even though **tier 3** (need_tags fallback) would fail (empty need_tags) — demonstrating the query-level axis layer is sometimes more robust than the need-tag-extraction layer for `relationship_repair`. No equivalent query-level marriage-specific entry exists in `CONSULTATION_AXIS_KEYWORDS["relationship_repair"]` (its list is 人間関係/職場の人間関係/家族との関係/友人との関係/対人関係/関係を整理/関係を修復/関係がうまくいかない/仲直り — no marriage-specific term), so this same safety net would not apply to a hypothetical marriage-only query with zero `marriage` keyword hits (case 6).

## 11. Marriage Coverage Metrics

**Marriage seeking coverage**: 4/4 correct = **100%** (cases 1–4)

**Existing-marriage coverage**: 3/5 correct = **60%** (cases 7, 8, 9 correct; case 5 misclassified to mental+rest; case 6 total miss). This is materially better than the prior audit's single-case finding suggested — phrasings containing `結婚` (e.g. "結婚生活") or `夫婦円満` verbatim already work correctly regardless of seeking-vs-existing framing; only phrasings using `夫婦関係`/`夫婦仲` without either of those anchor words fail.

## 12. mental/rest Misclassification Root Cause

**Case 5 (`夫婦関係を整えたい`)**:
- Matched token: `整えたい`, present verbatim in both `NEED_KEYWORDS["mental"]` (as `心を整えたい`/`気持ちを整えたい`/`整えたい`) and `NEED_KEYWORDS["rest"]` (as `心を整えたい`/`整えたい`)
- Matched regex: n/a — `NEED_KEYWORDS` uses plain substring containment (`_collect_hits`), not regex, for this dict
- Extraction ordering: `_collect_hits` iterates `NEED_KEYWORDS` in dict-definition order (mental appears before rest); both nonetheless appear in the result since `_collect_hits` collects **all** matches, not first-match-only
- Whether multiple Needs were generated: yes — `['mental', 'rest']`
- Normalization effect: none (neither `mental` nor `rest` is an alias source)
- Final Need list: `['mental', 'rest']` — `marriage` never appears, because no `marriage`-keyword substring is present in this exact phrasing (`夫婦関係` itself is not currently a `marriage` keyword — only `夫婦円満` is)

**Root cause: `OVERBROAD_MENTAL_KEYWORD` + `OVERBROAD_REST_KEYWORD` (`COMBINATION`)** — not `MISSING_MARRIAGE_KEYWORD` in isolation. Even if a `marriage` keyword were added to catch "夫婦関係" (Section 13), it would **add** `marriage` to the extracted set alongside the still-present `mental`/`rest` false positives, not **replace** them — `_collect_hits` has no exclusivity mechanism between Needs.

**Case 6 (`夫婦仲を良くしたい`)**:
- Matched token: none, anywhere
- Final Need list: `[]`
- Root cause: **`MISSING_MARRIAGE_KEYWORD`**, cleanly — no other Need's keyword list matches this phrasing either, so no collision would result from adding coverage here.

## 13. Minimal Marriage Interpreter Candidates

Drawn only from the existing marriage keyword family (縁結び/良縁/結婚/婚活/結縁/ご縁/**夫婦円満**) — no vocabulary invented from general knowledge:

| Candidate | Source | Intended subtype | Current collision risk |
|---|---|---|---|
| `夫婦関係` | Morphological relative of the existing `夫婦円満` keyword (shared `夫婦` root); literally the noun form of "marital relationship" | existing-marriage | Does not appear in any other Need's `NEED_KEYWORDS`/`KEYWORDS` list (checked directly) — but the query it targets (case 5) *already* independently triggers `mental`/`rest` via a *different* word (`整えたい`) in the same sentence, so adding this candidate would not, by itself, resolve case 5's false positives (Section 12) |
| `夫婦仲` | Same `夫婦` root family | existing-marriage | Does not appear in any other Need's keyword list; the query it targets (case 6) has no competing match at all |

Classification: **`SAFE`** for both, as isolated keyword additions (neither collides with an existing keyword in any other Need's list) — but their *practical* effect differs (Section 14): `夫婦仲` would cleanly close case 6's total miss; `夫婦関係` would only add `marriage` alongside case 5's pre-existing false positives, not remove them. No `AMBIGUOUS` or `REJECT` candidates were found from within the existing repo-documented marriage vocabulary family — a broader search (e.g. adding `パートナー`, `婚姻`) was not performed, per the constraint against inventing vocabulary from general knowledge.

## 14. Cross-Need Collision Risk

| Candidate | marriage | love | relationship | mental | rest | family | Risk |
|---|---|---|---|---|---|---|---|
| `夫婦関係` | adds correctly | no overlap | no overlap | **no overlap itself, but case 5 already collides via a different word (`整えたい`), unresolved by this candidate** | same as mental | no overlap | `LOW` (no new collision introduced) but **does not close the mental/rest false-positive gap** |
| `夫婦仲` | adds correctly | no overlap | no overlap | no overlap | no overlap | no overlap | `LOW` — cleanly resolves case 6 with no side effects observed |

## 15. Lead Audit

Traced `_resolve_matched_lead_evidence`/`_build_need_lead` directly (code, not just observed output): the winner-aware Lead mechanism is **fully Need-agnostic** — it resolves `matched_gid_label` by looking up whichever real `GoriyakuTag.name` actually matched for the given `tag` (any Need tag, including `marriage`), with a documented lowest-id-wins tie-break when multiple GIDs match the same candidate. Confirmed via the Section 4 trace: a `marriage` match via id=1 correctly produces Lead=`"縁結び"` (the real label). By the same mechanism (untested directly here, but structurally identical, no `marriage`-specific branching exists anywhere in this function), a match via id=18 would correctly produce Lead=`"夫婦円満"`.

**Result: `READY`.** No Lead code change is needed for either id=1 or id=18 evidence — the existing, unmodified, generic mechanism already handles both correctly.

## 16. Reason Audit

Traced `_build_need_reason_text`: its `intent_map` (used for the with-name branch, the one actually exercised in the live pipeline) contains exactly 8 entries — `study`/`mental`/`rest`/`love`/`career`/`money`/`courage`/`protection`. **7 of the 15 Need tags have no entry** — `relationship`, `marriage`, `communication`, `focus`, `family`, `travel_safe` (6, all missing) — `marriage` is not uniquely deficient; it shares this gap with most of the taxonomy. Any Need tag absent from `intent_map` falls to the generic `"今の願い"` string, producing the observed generic Reason text.

**Missing contract, precisely**: `MISSING_INTENT_COPY` — a Need-tag → short Japanese phrase mapping for the Reason sentence's object clause (`"...を願う参拝先として"`). This is a data/copy gap (a dict entry), not a missing evidence-handoff (the evidence, via Lead, is already correctly flowing — Section 15) and not a missing label (the `_build_need_lead`'s separate `fallback` dict, used only when there is literally no matched evidence at all, is a distinct, lower-priority gap that also lacks a `marriage` entry, but is rarely reached since `marriage` almost always resolves via GID when it matches at all).

## 17. Existing Copy Search

| Source file | Wording purpose | Suitability |
|---|---|---|
| `backend/temples/services/concierge_plan.py` `WISH_HINTS` | A parallel, substring-keyed (not Need-tag-keyed) copy-generation table for a different feature (itinerary/plan copy). Contains `("縁結び", "良縁成就を願う参拝に")`, distinct from `("恋愛", "恋愛成就の祈りに")` — i.e., this *other* system already draws a "良縁成就" (marriage/good-match-flavored) vs "恋愛成就" (romance-flavored) distinction in its own wording | The **phrase itself** ("良縁成就を願う参拝に" or a derivative, e.g. "良縁成就"/"夫婦円満") is directly reusable wording; the **mechanism** differs (substring-over-goriyaku-text vs Need-tag `intent_map` lookup), so integrating it into `_build_need_reason_text`'s `intent_map` would require adaptation, not a direct code copy |

**Result: `ADAPTATION_REQUIRED`.** No Need-tag-keyed marriage copy exists anywhere in the repo, but a real, already-shipped, marriage-appropriate *phrase* ("良縁成就") exists in a sibling system and could inform (not be mechanically copied into) a future `intent_map["marriage"]` entry.

## 18. Responsibility Matrix

| Layer | Status | Root cause | Needs implementation? |
|---|---|---|---|
| Alias | `CLOSED` | n/a (PR #2586) | No |
| Mapping | `CLOSED` | n/a (PR #2586, `{1,18}`) | No |
| Interpreter | `PARTIAL` | Case 6: `MISSING_MARRIAGE_KEYWORD`. Case 5: `OVERBROAD_MENTAL_KEYWORD`+`OVERBROAD_REST_KEYWORD` (a `mental`/`rest` problem, not fixable from marriage's side alone) | Yes, for case 6 only; case 5 requires touching `mental`/`rest`'s own keyword scope (out of this task's constraints and arguably a separate Need's own decision) |
| Consultation Axis | `OPEN` | `marriage` absent from `NEED_TAG_TO_CONSULTATION_AXIS`; falls to `other`, which has no history-theme boost row | Yes, if the axis reuse is approved (Section 8, `SAFE_TO_REUSE`) |
| C1 | `CLOSED` | n/a — GID_ONLY path confirmed healthy, winner always `gid` (marriage has no Text evidence, structurally) | No |
| Ranking | `CLOSED` | n/a — `score_total`/candidate selection confirmed unaffected by the axis question; only the secondary `history_theme_candidate_boost` is affected, and only when the axis is `other` vs an entry with a boost table | No (Ranking *weights* are unchanged either way; only the axis *input* to an existing, unmodified Ranking component is open) |
| Lead | `CLOSED` | n/a — confirmed `READY`, Need-agnostic mechanism already correctly handles both id=1 and id=18 | No |
| Reason | `OPEN` | `MISSING_INTENT_COPY` — `intent_map` has no `marriage` entry (shared gap with 5 other Needs) | Yes, if pursued (small, low-risk, established pattern) |

## 19. Implementation Dependency Analysis

- **Does Axis depend on Interpreter?** No — the axis fix (`NEED_TAG_TO_CONSULTATION_AXIS["marriage"] = "relationship_repair"`) is a single dict-entry addition, independently testable via the tier-3 fallback path regardless of what the interpreter extracts, as long as `marriage` is the resolved Need tag (already true today for cases 1–4, 7–9).
- **Does Interpreter depend on Axis?** No — adding `夫婦仲`/`夫婦関係` keywords to `NEED_KEYWORDS["marriage"]`/`KEYWORDS["marriage"]` is independently testable and has no axis dependency.
- **Does Reason depend on either?** No, technically — an `intent_map["marriage"]` entry is a pure string addition, independently testable. It is, however, **most valuable once** the axis and/or interpreter fixes ship, since more marriage-tagged consultations would then reach a state where the Reason text is user-visible and worth being accurate.
- **Can all three be independently tested?** Yes — confirmed by this audit's own methodology: Section 6 tested the axis change in isolation (mapping/alias/interpreter untouched); Section 12/13 analyzed interpreter candidates without touching axis/mapping; Reason's `intent_map` gap (Section 16) was identified independently of both.

## 20. PR Split Options

| Option | Isolation | Regression visibility | Semantic coupling | Rollback safety | Reviewability |
|---|---|---|---|---|---|
| A — Axis only | High | High (Section 6's simulation methodology directly reusable as a regression test) | Low (touches only `NEED_TAG_TO_CONSULTATION_AXIS`) | High (single dict entry) | High |
| B — Interpreter only | High | Medium (interpreter changes affect matched keyword surface, needs the false-positive-count regression gate from Section 12) | Low (touches only `NEED_KEYWORDS`/`KEYWORDS["marriage"]`) | High | High |
| C — Axis + Interpreter together | Medium | Medium | Low-medium (still two independently-testable changes, but reviewed together) | Medium | Medium |
| D — Axis + Interpreter + Reason | Low | Low (three concerns in one diff, harder to attribute any single regression) | Medium (Reason wording review is a different kind of review — product/copy — than the other two) | Medium | Low |
| E — Three separate PRs | Highest | Highest | Lowest | Highest | Highest |

## 21. Recommended Technical Split

**`THREE_SEPARATE_PRS`.**

Reasoning: Section 19 confirms all three (axis, interpreter, Reason) are genuinely independent — no technical dependency forces bundling. Section 20's qualitative scoring favors maximal isolation given the audit's own findings show each layer has a distinct root cause (axis: absent taxonomy entry; interpreter: two *different* sub-problems, case 5 vs case 6; Reason: a copy gap shared with 5 other Needs, not marriage-specific). Bundling risks conflating an axis-caused Top3 churn with an interpreter-caused extraction churn during review, exactly the kind of ambiguity this audit chain has consistently avoided by keeping corrections narrow (PR #2578, #2582, #2586 each targeted one layer).

## 22. Future Regression Gates

**Marriage independence** (already established, PR #2586 — re-verify, don't re-implement):
- [ ] alias absent in both `NEED_TAG_ALIASES` copies
- [ ] mapping `{1, 18}`
- [ ] `結婚したい` normalizes to `['marriage']`, not `['love']`

**Love**:
- [ ] `恋愛を成就させたい`/`復縁したい` still extract `['love']`
- [ ] Compass `purpose="love"` Top3 unchanged from the PR #2586 baseline

**Relationship**:
- [ ] `職場の人間関係を改善したい` still extracts `['relationship']`
- [ ] Compass `purpose="relationship"` Top3 unchanged

**Interpreter** (if Option B/case-6 fix ships):
- [ ] `夫婦仲を良くしたい` now extracts `marriage`
- [ ] All 15 corpus cases from Section 9 re-run; controls (10–15) produce identical need_tags to this audit's baseline
- [ ] mental/rest false-positive count for case 5 does not increase (adding `夫婦関係` should not remove the mental/rest signal — case 5 remains a known, separate `mental`/`rest` keyword-scope issue, out of scope)
- [ ] No query in the existing `test_concierge_need_variation.py`/`test_concierge_relationship_love_separation.py`/`test_concierge_eval_queries*.py` suites gains a new, previously-absent Need tag

**Axis** (if Option A ships):
- [ ] Only `marriage`-tagged consultations show churn (re-run love/relationship/mental/courage/study/career/money/protection controls, confirm 0 change — none of these Needs' own `NEED_TAG_TO_CONSULTATION_AXIS` entries are touched)
- [ ] Candidate pool (Direction/Distance) identical before/after for every tested query — the axis fix must never change *which* candidates are eligible, only their relative order among already-matched candidates
- [ ] C1 (`matched_need_tags`, `need_evidence_winner_by_tag`) unchanged for every tested query
- [ ] `score_total` (the live, non-shadow total) unchanged — only `score_v3`/ranking-order effects are expected, consistent with Section 6/7's findings

**Explanation**:
- [ ] Reason output for `love`/`relationship`/`career`/`money`/`study`/`courage`/`protection`/`mental`/`rest` unchanged if/when a `marriage` `intent_map` entry is added — confirm no accidental dict-ordering or shared-helper regression

## 23. Mother Ship Decision Inputs

1. Authorize Option A (Axis) as the first of the three PRs, given Section 8's `SAFE_TO_REUSE` finding and Section 21's `THREE_SEPARATE_PRS` recommendation?
2. Authorize Option B (Interpreter) — specifically the `夫婦仲` addition (clean, Section 13/14) — while explicitly deferring `夫婦関係` (Section 12, would not resolve its own target query's false positives without also touching `mental`/`rest`)?
3. Should the `mental`/`rest` "整えたい" overlap (Section 12, case 5) be raised as its own follow-up item for those Needs' eventual `MULTI_LAYER_DESIGN_REQUIRED` resolution (`docs/audit/remaining-product-decision-need-responsibilities.md`), rather than attempted from marriage's side?
4. Authorize a future Reason `intent_map["marriage"]` entry, informed by (not copied from) `concierge_plan.py`'s existing "良縁成就" wording (Section 17), as the third, lowest-urgency PR?
5. Confirm the recommended execution order (Axis, then Interpreter, then Reason) or specify a different priority — Section 19 establishes no technical ordering is required, so this is a pure product-sequencing choice.

## 24. Limitations

- Section 6's simulation used synthetic, hand-built candidates (not real DB-backed shrines) to isolate the axis effect precisely; the magnitude of real-world Top3 churn once shipped would depend on how many real marriage-matching shrines carry a `縁`-adjacent `history_theme`, not measured here.
- Section 13's candidate set was deliberately restricted to the `夫婦`-root family already present in `marriage`'s own keyword list, per the task's explicit instruction not to invent vocabulary from general knowledge; a broader natural-language coverage study (e.g. testing "パートナー"/"婚姻"-flavored phrasing) was not performed and would require separate, explicit authorization to draw on vocabulary beyond the existing repo.
- The `score_v3`/`history_signal` field observed in Section 6 is documented in its own breakdown dict as `"mode": "shadow"`; this audit's own evidence (the changed recommendation *order*, not just the shadow score value) supports treating the axis's effect on Top3 as real/live, but a full trace of exactly which score field (`score_need_rank_weighted` vs `score_v3`) drives the final sort order was not completed with the same rigor as the rest of this audit — flagged as the one point requiring re-verification before an Axis-only implementation PR ships.
- Existing Copy Search (Section 17) was a targeted grep-based search, not an exhaustive repo-wide audit of every Japanese-string constant.

## 25. Out of Scope

`communication`/`mental`/`courage` (per the prior product-decision-responsibility audit, unaddressed here except as context for Section 12's collision finding), UI/frontend, implementation of any axis/interpreter/Reason change described in Sections 13/16/21, DB/Model/migration changes, new taxonomy, `love`/`relationship` mapping changes.
