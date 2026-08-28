# NEED_LABELS_JA Completeness Implementation

## 1. Objective

Close the confirmed `NEED_LABELS_JA` completeness defect identified in
[recommendation-semantic-resolution-cross-need.md](./recommendation-semantic-resolution-cross-need.md)
(Section 6/17): 5 of 15 canonical Need tags — `marriage`, `relationship`,
`communication`, `health`, `family` — were absent from every active
Need-to-Japanese-label dictionary, causing the raw English Need key to leak
into user/API-facing `label_ja` fields. Mechanical dictionary-completeness
fix only; no product-semantic decision made or required.

## 2. Base SHA

`origin/develop` @ `ebeb3950828910ab78fe3d4e9023054bbd9cb82e`
(`docs: 全15 Need横断のセマンティック解決度監査 (#2594)`), the precondition
this task required. `origin/develop` has since advanced to `291d3cae`
(`推薦EvidenceとDark UIの最終Visual QA (#2595)`, confirmed docs-only via
`git diff --stat ebeb3950 origin/develop` — a single new file under
`docs/audit/`, zero overlap with the two files this change touches) — not
rebased onto, since there is no conflict to resolve.

Worktree: `/Users/morietsu/Developer/jinja_app-need-labels-ja-completeness`,
branch `fix/need-labels-ja-completeness`.

## 3. Canonical Need Count

Fresh-read from `backend/temples/domain/need_tags.py` `NEED_TAGS` (not
assumed from the prior audit doc): **15**, unchanged — love, relationship,
marriage, communication, career, money, study, health, mental, protection,
courage, focus, rest, family, travel_safe.

## 4. Active NEED_LABELS_JA Locations

Repository-wide search (`grep -rn "NEED_LABELS_JA\|NEED_TAG_LABELS_JA"`,
all extensions, `node_modules`/`.venv` excluded) found **three** active
copies — one more than the prior audit named, because that audit only
searched for the literal string `"NEED_LABELS_JA"` and missed a
differently-named dict serving the identical contract:

| File | Symbol | Runtime responsibility | Status | Need keys present (pre-fix) | Need keys missing (pre-fix) |
|---|---|---|---|---|---|
| `temples/services/concierge_chat_ranking.py:489` | `NEED_LABELS_JA` | `_make_reason_fact()` → `reason_facts[].label_ja` (consumed by `concierge_explanation_payload.py` and any direct API consumer of `reason_facts`) | **Active** | 10 | 5 |
| `temples/services/concierge_chat_ranking.py:576` | `NEED_TAG_LABELS_JA` (via `_need_tag_to_ja()`) | `rank_explanation.primary_label_ja` (line ~2061) and `rank_comparison.shared_need_tags_ja` (line ~2117) — a genuinely separate, previously-undocumented output surface | **Active — newly discovered this task** | 10 | 5 |
| `temples/services/concierge_explanation_payload.py:10` | `NEED_LABELS_JA` | `_explanation_payload.primary_reason.label_ja` (line ~137) and `.primary_need_label_ja` (line ~190, distinct default: bare `None`, not the raw key) | **Active** | 10 | 5 |

No other file in the repository references any of these three symbols
(confirmed via `grep -rln` across `.py`/`.ts`/`.tsx`; no frontend copy
exists — `label_ja` is consumed as opaque data by the frontend, not
re-mapped there).

The pre-fix 10 present keys were textually identical across all three
copies: `study, career, mental, love, money, rest, courage, protection,
focus, travel_safe`. All three copies were missing the identical 5:
`marriage, relationship, communication, health, family`.

## 5. Baseline Missing Labels

Fresh runtime confirmation (not assumed from the prior audit), via
`build_chat_recommendations` with single-candidate fixtures isolating one
Need each:

| Need | `reason_facts[].label_ja` | `_explanation_payload.primary_reason.label_ja` | `_explanation_payload.primary_need_label_ja` | `rank_explanation.primary_label_ja` |
|---|---|---|---|---|
| marriage | `"marriage"` (raw key) | `"marriage"` (raw key) | `None` | `"marriage"` (raw key) |
| relationship | `"relationship"` | `"relationship"` | `None` | `"relationship"` |
| communication | `"communication"` | `"communication"` | `None` | `"communication"` |
| health | `"health"` | `"health"` | `None` | `"health"` |
| family | `"family"` | `"family"` | `None` | `"family"` |
| love (control) | `"恋愛"` (correct) | `"恋愛"` | `"恋愛"` | `"恋愛"` |

`primary_need_label_ja`'s `None` default (vs. the other three call sites'
raw-key default) comes from its own distinct call —
`NEED_LABELS_JA.get(primary_need_tag or "", None)` — which explicitly
passes `None` as the fallback rather than the key itself; still a defect
(silently dropping the field), just a different failure shape than the
other three surfaces.

This directly reproduces, with live runtime evidence rather than static
code reading, the `'label_ja': 'marriage'` output observed in an earlier
session's own JSON dump during the marriage-reason-copy PR's testing —
confirming the defect survived PR #2593 (which only added `marriage` to
the unrelated `intent_map` Reason-sentence dict, not to any `NEED_LABELS_JA`
copy).

## 6. Label Contract

Existing convention, read from the 10 pre-existing entries (identical
across all three copies): short (1–4 kanji/word), neutral noun phrases;
either a single canonical noun (`恋愛`, `金運`, `休息`) or two related
terms joined by `・` (`転機・仕事`, `厄除け・守り`, `学業・合格`,
`前進・後押し`, `移動・安全`, `集中・継続`, `不安・心`). None are
sentences, none make outcome/religious claims, none reference a specific
shrine.

Proposed labels for the 5 missing Needs, derived from each Need's own
current repository semantics (KEYWORDS vocabulary, mapped canonical
`GoriyakuTag` names, and — for wording precedent only, not semantic
authority — the existing `intent_map` Reason phrase):

| Need | Existing semantic definition (current code) | Proposed label | Source |
|---|---|---|---|
| marriage | Interpreter: `結婚`, `夫婦円満`, `夫婦仲`, `夫婦関係` (KEYWORDS). GID: `{1 縁結び, 18 夫婦円満}`. `intent_map`: `"良縁や夫婦円満"`. | `結婚・夫婦円満` | Own GID names (1, 18) + own `intent_map` phrase; two-word joined form matches `career`/`protection`/`study` convention and avoids collapsing into `love`'s `"恋愛"`. |
| relationship | Interpreter: `人間関係`, `職場の人間関係`, `友人`, `家族との関係`, etc. (KEYWORDS). GID: `{1 縁結び}` (shared with love/marriage). | `人間関係` | Literal term already used inside the Need's own KEYWORDS/query corpus (e.g. `"職場の人間関係を改善したい"`); single canonical noun, matches `love`/`money`/`rest` single-term convention. |
| communication | Interpreter: `営業`, `交渉`, `プレゼン`, `面接`, `会話`, `発信`, `伝える`, `話す` (KEYWORDS). GID: `{30,33,37,39}` (semantically weak — a separate, already-flagged `DECISION_REQUIRED` finding, out of scope here). | `コミュニケーション` | The Need's own name, in the katakana form already used in the corpus query `"職場でのコミュニケーションを改善したい"`; single canonical term, does not presuppose a resolution to the taxonomy-mismatch finding. |
| health | Interpreter: `健康`, `病気`, `体力`, `体調` (KEYWORDS). GID: `{7,8,24,33,38}` (家内安全/福徳/健康長寿/病気平癒/足腰健康). | `健康` | Direct single-term match to the Need's own dominant KEYWORDS entry and to GID id=24's own name root (`健康長寿`); mirrors `love`/`money`/`rest`'s single-noun convention. |
| family | Interpreter: `子宝`, `安産`, `妊活`, `授かり`, `出産`, `育児` (KEYWORDS — fertility/childbirth-centered). GID: `{2 厄除け, 26 家庭円満, 34 火防}` (household-protection-centered — a different emphasis than the interpreter vocabulary; this internal inconsistency is exactly why family's scope is a separate `MOTHER_SHIP_DECISION_REQUIRED` item in the companion audit, not resolved here). | `家族` | Deliberately the plainest, most literal, scope-neutral rendering of the Need's own canonical key — does not lean toward either the interpreter's narrow (fertility) reading or the GID mapping's broader (household-harmony) reading, so this label commits to nothing the pending Mother Ship decision (`docs/audit/semantic-followup-decision-and-pr-split.md`) has not yet settled. |

No existing label was renamed. All five proposed labels are short, neutral,
non-explanatory, and make no outcome or religious claim.

## 7. Added Labels

Added the same 5 entries, with identical text, to all three confirmed
active copies (Section 4):

```python
"marriage": "結婚・夫婦円満",
"relationship": "人間関係",
"communication": "コミュニケーション",
"health": "健康",
"family": "家族",
```

## 8. Before / After

| Need | `label_ja` before | `label_ja` after |
|---|---|---|
| marriage | `"marriage"` (raw key) | `"結婚・夫婦円満"` |
| relationship | `"relationship"` | `"人間関係"` |
| communication | `"communication"` | `"コミュニケーション"` |
| health | `"health"` | `"健康"` |
| family | `"family"` | `"家族"` |

Live-verified across all four output surfaces (`reason_facts[].label_ja`,
`_explanation_payload.primary_reason.label_ja`,
`_explanation_payload.primary_need_label_ja`,
`rank_explanation.primary_label_ja`) for all 5 Needs — see
[test_need_labels_ja_completeness.py](../../backend/temples/tests/test_need_labels_ja_completeness.py).

## 9. Synchronization Check

All three active copies contain identical text for all 15 canonical Need
keys (verified programmatically; see `test_all_active_copies_synchronized_for_every_canonical_need`
in the test file). No divergence.

## 10. Regression

- Focused: `test_need_labels_ja_completeness.py` (new, 17 tests, all
  passing), `test_concierge_explanation.py`,
  `test_concierge_explanations.py`, `test_concierge_explanations_contract.py`,
  `test_marriage_reason_copy.py`, `test_marriage_interpreter_coverage.py`,
  `test_protection_explanation_coverage.py`,
  `test_compass_recommendation_orchestrator.py`, `test_compass_runtime.py`,
  `test_compass_direction_filter.py`, `test_compass_recommendations_api.py`,
  `test_concierge_primary_reason_unification_contract.py`,
  `test_signal_authority_explanation_alignment_contract.py`,
  `test_signal_authority_knowledge_explanation_contract.py`,
  `test_recommendation_reason_v4.py`,
  `test_recommendation_reason_v4_authority_alignment.py` — **250 passed, 0
  failed**.
- Full backend suite: **1769 passed, 15 skipped (pre-existing categories
  only: GDAL unavailable, PostGIS unavailable, `GOOGLE_PLACES_API_KEY`
  unset, one ambiguous-axis-family case), 0 failed**.
- **Ranking churn**: 0 — no test asserting Top3 order/composition changed
  its expected result; `_score_total`/`breakdown` fields untouched by this
  change (label dicts are read only at explanation-payload construction
  time, downstream of scoring).
- **Reason churn**: 0 — the free-text `reason` sentence (built from
  `intent_map`, a separate, untouched dict) is byte-identical before and
  after for all 5 Needs; live-verified (e.g. family's `reason` still reads
  `"...今の願いを願う参拝先として適しています。"`, the same generic
  fallback as before — only `label_ja` changed).
- **Lead churn**: 0 — `_build_need_lead`/`_resolve_matched_lead_evidence`
  not touched; Lead clause text unchanged in every live-verified case.
- **Top3 churn**: 0 — candidate ordering is a function of `_score_total`,
  untouched by this change; `test_compass_recommendation_orchestrator.py`'s
  ordering-sensitive tests all pass unchanged.

## 11. Production Safety

Production changes are exactly 27 inserted lines across 2 files (19 in
`concierge_chat_ranking.py` — both `NEED_LABELS_JA` and
`NEED_TAG_LABELS_JA`, 8 in `concierge_explanation_payload.py`), all
dictionary-entry additions. No existing key's value changed. No alias,
interpreter, Axis, GID mapping, Text Evidence, C1, Ranking weight, Lead,
Reason (`intent_map`), DB, model, migration, seed, or frontend file
touched — confirmed via `git diff --stat` (Section 12 below) showing only
the two service files plus the new test file and this doc.

## 12. Out of Scope

- Any `intent_map` (Reason free-text sentence) addition for `relationship`,
  `communication`, `health`, `family`, `focus`, `travel_safe` — a separate,
  semantically-gated decision, addressed in
  `docs/audit/semantic-followup-decision-and-pr-split.md` (Deliverable B).
- `family`'s scope ambiguity (narrow/fertility vs. broad/household) —
  explicitly not resolved by this label choice (Section 6); Mother Ship
  decision packet in the companion audit.
- `communication`'s taxonomy/GID mismatch — untouched.
- `mental`/`rest` interpreter collision — untouched.
- `courage`/`career` shared evidence — untouched.
- Any Need alias, interpreter keyword, consultation-axis mapping, GID
  mapping, Text Evidence weight, C1 logic, ranking weight, Lead builder,
  DB row, migration, seed, or frontend file.

## 13. Remaining Explanation Gaps

`label_ja` completeness is now closed for all 15 canonical Needs. The
Reason free-text sentence (`intent_map`) remains incomplete for 6 Needs
(`relationship`, `focus`, `travel_safe`, `health`, `family`,
`communication`) — a distinct, separate dict from `NEED_LABELS_JA`/
`NEED_TAG_LABELS_JA`, not modified by this change. See Deliverable B
(`docs/audit/semantic-followup-decision-and-pr-split.md`) for the
SEMANTIC_SAFE / DECISION_REQUIRED classification of each.

## 14. STOP

Draft PR only. Not merged. No further action taken under this deliverable.
