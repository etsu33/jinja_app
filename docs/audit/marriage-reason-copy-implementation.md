# Marriage Reason Copy Implementation

> Closes `MISSING_INTENT_COPY`, the final open item in the marriage Recommendation responsibility matrix (`docs/audit/marriage-consultation-interpreter-coverage.md` Section 18). Adds exactly one `intent_map["marriage"]` entry. Does not touch Lead, mapping, alias, axis, interpreter, C1, Ranking, Direction, or Distance.

## 1. Scope

Single dict-entry addition: `intent_map["marriage"] = "良縁や夫婦円満"` inside `_build_need_reason_text` (`temples/services/concierge_chat_ranking.py`, the sole Reason-construction implementation — confirmed no Compass-specific duplicate exists). No other Need's `intent_map` entry, no Lead code, no mapping/axis/interpreter/C1/Ranking/Direction/Distance change.

## 2. Base SHA

`origin/develop` at `b8085b047919df58c0d54f8e633a1151ae606090` (`fix: improve marriage interpreter coverage (#2591)`). Worktree: `/Users/morietsu/Developer/jinja_app-marriage-reason-copy`, branch `fix/marriage-reason-copy`.

Fresh-confirmed baseline: `NEED_TAG_ALIASES` has no `"marriage"` entry; `NEED_TO_GORIYAKU_IDS["marriage"] == {1, 18}`; `NEED_TAG_TO_CONSULTATION_AXIS["marriage"] == "relationship_repair"`; `KEYWORDS["marriage"]`/`NEED_KEYWORDS["marriage"]` both include `夫婦関係`/`夫婦仲`; a `結婚したい` query's Reason was `"...のご利益で知られる〈shrine〉は、今の願いを願う参拝先として適しています。"` (generic fallback, `intent_map.get("marriage", "今の願い")` → `"今の願い"`).

## 3. Prior Audit / Implementation Sources

`docs/audit/marriage-consultation-interpreter-coverage.md` Section 16 (Reason Audit — the exact `MISSING_INTENT_COPY` finding, and confirms this gap is shared with 5 other Need tags, not marriage-unique) and Section 17 (Existing Copy Search — `concierge_plan.py`'s `WISH_HINTS` "良縁成就" phrase, `ADAPTATION_REQUIRED`). `docs/audit/marriage-need-independence-implementation.md`, `docs/audit/marriage-consultation-axis-implementation.md`, `docs/audit/marriage-interpreter-coverage-implementation.md` (prior tracks in the same responsibility matrix, all confirmed unchanged by this PR).

## 4. Current Reason Contract

Fresh-traced the full entry-to-output path (single, non-duplicated implementation, confirmed via repo-wide grep — `_build_need_reason_text`/`intent_map`/`_build_need_lead` all live only in `concierge_chat_ranking.py`, used identically by both Compass and Concierge):

```
build_recommendation_reason(rec, public_mode, birthdate, need_tags, need_gid_label_by_id)
  -> if rec["_primary_reason_label"]: _build_need_reason_text(primary_label, ...)
  -> elif matched_need_tags: _build_need_reason_text(matched_tags[0], ...)
  -> else: generic ultimate fallback ("今の悩みや願いに合わせて...")

_build_need_reason_text(tag, name, goriyaku, matched_gid_label, matched_text_hint):
  intent_map = {study, mental, rest, love, career, money, courage, protection}  <- "marriage" absent (before this PR)
  user_intent = intent_map.get(tag, "今の願い")
  if name:
      lead = _build_need_lead(tag, goriyaku, matched_gid_label=, matched_text_hint=)  <- UNCHANGED, Need-agnostic
      return f"{lead}のご利益で知られる{name}は、{user_intent}を願う参拝先として適しています。"
  ... (a second, twin `mapping` dict for the name-less case -- confirmed unreachable
       in practice: build_recommendation_reason always passes a real shrine `name`)
```

Traced for 4 Needs: `love` (has `intent_map` entry, "恋愛や良縁") and `protection` (has entry, "厄除けや守り") both produce evidence-flavored, Need-specific Reason text; `marriage` (before this PR, absent) and `relationship` (absent, confirmed still absent — unmodified, per constraint #7) both fall to the generic `"今の願い"` phrasing.

## 5. Marriage Baseline

| Query | Winning evidence | Lead | Reason | Classification |
|---|---|---|---|---|
| 結婚したい | id=1 (縁結び), gid | 縁結び | "縁結びのご利益で知られる〈shrine〉は、今の願いを願う参拝先として適しています。" | `GENERIC_FALLBACK` |
| 結婚につながる良縁がほしい | id=1, gid | 縁結び | same generic pattern | `GENERIC_FALLBACK` |
| 夫婦円満を願いたい | id=1/18 depending on candidate | varies | same generic pattern | `GENERIC_FALLBACK` |
| 夫婦仲を良くしたい | (post-PR #2591 coverage) | varies | same generic pattern | `GENERIC_FALLBACK` |
| 夫婦関係を整えたい | (post-PR #2591 coverage) | varies | same generic pattern | `GENERIC_FALLBACK` |

**Confirmed exact missing contract: `MISSING_INTENT_COPY`** — `intent_map` had no `"marriage"` key, matching the hypothesis exactly.

## 6. Existing Copy Inventory

| Source | Existing wording/purpose | Suitable for marriage Reason? |
|---|---|---|
| `concierge_plan.py` `WISH_HINTS` | `("縁結び", "良縁成就を願う参拝に")` — a substring-keyed (not Need-tag-keyed) copy table for a different feature (itinerary/plan copy), distinct from `("恋愛", "恋愛成就の祈りに")` | `ADAPTATION_REQUIRED` — the phrase concept ("良縁") is directly reusable; the exact sentence form is not, since `intent_map`'s values are short 2-clause noun phrases (e.g. `"恋愛や良縁"`), not full sentences |
| `_build_need_reason_text` `intent_map["love"]` | `"恋愛や良縁"` — the closest existing sibling entry, same dict, same sentence template | `NOT_SUITABLE` as-is (would collapse marriage back into love's own copy, violating requirement 4) but establishes the exact grammatical pattern (`"AやB"`) to follow |
| Canonical `GoriyakuTag` labels | `id=1` "縁結び" (already `love`'s own Lead-source label), `id=18` "夫婦円満" (marriage's own unique label, confirmed in `marriage-love-alias-boundary.md` Section 10 as the master's clearest marriage-specific tag) | `DIRECT_REUSE` — both are real, already-shipped canonical strings, not invented |
| `docs/knowledge/shrine-knowledge-contract.md` / other Meaning Layer docs | No marriage-specific Recommendation copy guidance found | `NOT_SUITABLE` (nothing found) |

## 7. Semantic Requirements

Both marriage-seeking (結婚したい/結婚につながる良縁/結婚相手とのご縁) and existing-marriage (夫婦円満/夫婦仲/夫婦関係) phrasing must be acceptably covered by one entry, without inventing `marriage_seeking`/`marriage_repair` subtypes (constraint #21, no new Need tags).

**Result: `ONE_COPY_SUFFICIENT`.** A compound phrase combining `良縁` (marriage's own extraction keyword and love's Lead label, "good match/connection" — covers seeking) with `夫婦円満` (marriage's own unique GID-18 label — covers existing-marriage harmony) reads naturally for all 6 example phrasings, verified in Section 11.

## 8. Selected Copy

- **Source wording**: `良縁` (from `KEYWORDS["marriage"]`/`NEED_KEYWORDS["marriage"]`, and the existing `love` intent_map value's own second word) + `夫婦円満` (id=18's real, unmodified `GoriyakuTag.name`)
- **Adaptation rationale**: follows the exact `intent_map`'s established `"AやB"` 2-clause grammatical pattern (matching `"恋愛や良縁"`, `"厄除けや守り"`, `"仕事や転機"`); deliberately excludes `恋愛` to avoid collapsing into `love`'s own phrasing (requirement 4); uses only real, already-shipped strings (requirement 8, smallest possible copy change — no invented conceptual language)
- **Final value**: `intent_map["marriage"] = "良縁や夫婦円満"`

## 9. Implementation

```python
# temples/services/concierge_chat_ranking.py, _build_need_reason_text
intent_map = {
    "study": "学業や合格",
    "mental": "不安や心の安定",
    "rest": "休息や気持ちの切り替え",
    "love": "恋愛や良縁",
    "career": "仕事や転機",
    "money": "金運向上",
    "courage": "前進や後押し",
    "protection": "厄除けや守り",
    "marriage": "良縁や夫婦円満",   # <- added
}
```

The twin, name-less `mapping` dict (used only when `build_recommendation_reason` is called without a shrine `name`) was **not** touched — confirmed via code trace that `build_recommendation_reason` always passes a real shrine `name`, making that branch unreachable in practice; adding to it would exceed "the minimum existing-pattern implementation required for `intent_map[\"marriage\"]`" (Core Goal, singular reference to `intent_map`).

## 10. Evidence Variant Results

Live `build_chat_recommendations`, with real `GoriyakuTag` rows (id=1 "縁結び", id=18 "夫婦円満") created in an isolated test DB:

| Evidence | Winner | Lead | Reason |
|---|---|---|---|
| id=1 (縁結び) | `{'marriage': 'gid'}` | `縁結び` | `"縁結びのご利益で知られる〈shrine〉は、良縁や夫婦円満を願う参拝先として適しています。"` |
| id=18 (夫婦円満) | `{'marriage': 'gid'}` | `夫婦円満` | `"夫婦円満のご利益で知られる〈shrine〉は、良縁や夫婦円満を願う参拝先として適しています。"` |

Both compatible — the evidence-specific Lead clause (unmodified) always cites the real matched tag; the new shared `user_intent` clause never claims evidence the shrine doesn't have (it is a general statement of consultation intent, identical in structure to every other Need's entry).

## 11. Natural Language Regression

All 9 required queries (4 seeking + 5 existing-marriage), real production path:

| Query | Normalized Need | Axis | Reason contains |
|---|---|---|---|
| 結婚したい | `['marriage']` | relationship_repair | `良縁や夫婦円満を願う参拝先として` |
| 結婚につながる良縁がほしい | `['marriage']` | relationship_repair | same |
| 結婚相手とのご縁がほしい | `['marriage']` | relationship_repair | same |
| 良い人と結婚したい | `['marriage']` | relationship_repair | same |
| 夫婦関係を整えたい | `['marriage','mental','rest']` | relationship_repair | same (when marriage evidence wins) |
| 夫婦仲を良くしたい | `['marriage']` | relationship_repair | same |
| 夫婦円満を願いたい | `['marriage']` | relationship_repair | same |
| 結婚生活を良くしたい | `['marriage']` | relationship_repair | same |
| パートナーとの結婚生活に悩んでいる | `['marriage']` | relationship_repair | same |

Need extraction, axis resolution, and Compass Top3 (fixed fixture) are all byte-identical to the PR #2591 baseline — only Reason text changed for marriage-tagged results.

## 12. love Regression

Hard gate, confirmed:

- `恋愛を成就させたい`/`復縁したい`/`新しい出会いがほしい` → `['love']`, unchanged
- Compass `purpose="love"` Reason: `"...恋愛や良縁を願う参拝先として..."` — byte-identical to every prior baseline in this chain
- `test_love_reason_unchanged`, `test_love_match_is_unaffected_and_still_produces_love_reason` (pre-existing, untouched) pass
- **Unexpected love Reason churn: 0**

## 13. relationship Regression

Hard gate, confirmed:

- `職場の人間関係を改善したい`/`友人との関係を見直したい` → unchanged extraction
- Compass `purpose="relationship"` Reason: `"...今の願いを願う参拝先として..."` — **still generic, unchanged** (relationship's own `intent_map` gap is untouched, per constraint #7 — not this PR's scope)
- All `test_pr2409_*` regression tests (pre-existing, untouched) pass
- **Unexpected relationship Reason churn: 0**

## 14. mental/rest Controls

Hard gate, confirmed:

- `気持ちを整えたい` → `['mental','rest']`, Reason `"...不安や心の安定を願う参拝先として..."` (mental's own entry) — unchanged, no marriage copy leakage
- `少し休みたい` → `['rest']`, Reason `"...休息や気持ちの切り替えを願う参拝先として..."` — unchanged
- **Marriage Reason text (`良縁や夫婦円満`) never appears for a non-marriage primary Need — confirmed**

## 15. Ranking Invariance

Compass fixed fixture (`origin=(35.662443, 139.5920237)`, `direction_context={"referenceDirections": ["東"]}`), all 7 Needs tested (marriage/love/relationship/mental/rest/protection/study):

| Need | Candidate count | score_need | C1 winner | Top3 order |
|---|---:|---:|---|---|
| marriage | 3 | 1 (all) | `gid` (all) | Unchanged |
| love | 3 | 1 (all) | `text` (all) | Unchanged |
| relationship | 3 | 1 (all) | `gid` (all) | Unchanged |
| mental | 3 | 1 (all) | `text` (all) | Unchanged |
| rest | 3 | 1/1/0 | `gid`/`gid`/`{}` | Unchanged |
| protection | 3 | 1 (all) | `gid` (all) | Unchanged |
| study | 3 | 0 (all, fallback) | `{}` (all) | Unchanged |

**Every field except `reason` text is byte-identical to the pre-PR baseline, for every Need tested — confirmed via direct comparison, not merely asserted.** No STOP condition triggered.

## 16. Lead Invariance

Confirmed hard gate: `_build_need_lead`/`_resolve_matched_lead_evidence` are unmodified (0-line diff in this PR's scope). Section 10's evidence-variant results show Lead correctly resolves to `縁結び`/`夫婦円満` exactly as it would have before this PR (the mechanism was already `READY`, per `marriage-consultation-interpreter-coverage.md` Section 15) — this PR only changed what comes *after* the Lead clause in the sentence, not the Lead resolution itself.

## 17. Reason Before/After

```
BEFORE: "縁結びのご利益で知られる明治神宮は、今の願いを願う参拝先として適しています。"
AFTER:  "縁結びのご利益で知られる明治神宮は、良縁や夫婦円満を願う参拝先として適しています。"
```

## 18. Production Safety

Production Code change: `temples/services/concierge_chat_ranking.py` — one dict entry (plus documentation comment) inside `_build_need_reason_text`'s `intent_map`. Lead logic, mapping, alias, axis, interpreter vocabulary, `NEED_PRIORITY`, C1, Ranking weights, Text Evidence weights, candidate filtering, Direction, Distance — all confirmed unchanged (Sections 12–16).
Production DB change: **NO**.
Migration: **none**. New taxonomy/Need/GoriyakuTag/consultation axis: **none**.

## 19. Remaining Marriage Gaps

**None known at the backend Recommendation-responsibility level.** Cross-referencing the responsibility matrix first established in `docs/audit/marriage-consultation-interpreter-coverage.md` Section 18:

| Layer | Status (this PR) |
|---|---|
| Alias | `CLOSED` (PR #2586) |
| Mapping | `CLOSED` (PR #2586) |
| Interpreter | `CLOSED` (PR #2591 — both remaining gaps resolved) |
| Consultation Axis | `CLOSED` (PR #2590) |
| C1 | `CLOSED` (never open) |
| Ranking | `CLOSED` (never open) |
| Lead | `CLOSED` (never open — confirmed `READY` from the start) |
| Reason | **`CLOSED`** (this PR) |

Every layer in the marriage independence responsibility matrix is now closed. Any further marriage-related work (e.g. broader natural-language coverage beyond the audited `夫婦`-root family, or splitting the shared Reason copy into seeking/existing-marriage variants) would be a new, separately-scoped product initiative, not a continuation of this responsibility matrix.

## 20. Out of Scope

`communication`/`mental`/`courage` mapping-layer product decisions (per `docs/audit/remaining-product-decision-need-responsibilities.md`, unrelated to marriage and unaddressed here), UI/frontend, `NEED_TEXT_WEIGHTS` (fresh-read confirmed the Reason contract lives entirely in `intent_map`, not `NEED_TEXT_WEIGHTS` — no change was required or made there), DB/Model/migration changes, new taxonomy.
