# Communication Interpreter Coverage Implementation

## 1. Objective

Improve natural-language extraction for the existing canonical Need
`communication`, per Track C1 in
[semantic-followup-decision-and-pr-split.md](./semantic-followup-decision-and-pr-split.md)
Section 18/22 — the only remaining-communication track classified
`READY_TO_IMPLEMENT` with no product decision required.

**This PR is interpreter-only.** It does NOT fix Recommendation evidence,
taxonomy, GID mapping, consultation Axis, or Reason for `communication` —
see Section 8 for explicit live proof and the required statement below.

## 2. Base SHA

`origin/develop` @ `2226f01e7880adec96fd077fa85c1c9df82ca389`
(`docs: セマンティック follow-up 決定/PR分割設計 (#2598)`). Worktree:
`/Users/morietsu/Developer/jinja_app-communication-interpreter`, branch
`fix/communication-interpreter-coverage`.

## 3. Fresh Read

Repository-wide search confirmed exactly **two** active interpreter
vocabulary definitions for `communication`, kept synchronized by
established convention (both edited together in PR #2591 for `marriage`):

- `temples/domain/need_tags.py` `KEYWORDS["communication"]` — the real,
  production interpreter (`extract_need_tags`).
- `temples/services/consultation_interpreter.py`
  `NEED_KEYWORDS["communication"]` — explicitly shadow-only per its own
  module docstring ("does not change recommendation ranking"), kept
  textually identical by convention.

Both were identical, 8-word lists before this PR: `会話`, `発信`, `伝える`,
`話す`, `営業`, `交渉`, `プレゼン`, `面接`. No `REGEX` entry exists for
`communication`. `NEED_PRIORITY` places `communication` at index 10 (after
`relationship` at index 9) — unchanged, not modified by this PR.

## 4. Corpus

14 queries: 9 positive (communication-intent) + 5 negative controls,
sourced from repository-supported KEYWORDS vocabulary and the source
audit's own corpus method:

| Concept | Query |
|---|---|
| difficulty communicating | `人とうまく話せるようになりたい`, `人と話すのが怖い` |
| improving interaction (workplace) | `職場でのコミュニケーションを改善したい` |
| communication (existing, control) | `営業で成果を出したい` |
| expressing oneself (existing, control) | `プレゼンが苦手で克服したい` |
| communication (Need's own name) | `コミュニケーション能力を上げたい` |
| difficulty communicating (existing, control) | `初対面の人と話すのが苦手` |
| expressing oneself | `自分の気持ちをうまく伝えられない` |
| conversation (existing, control) | `会話が続かない` |
| relationship control | `職場の人間関係を改善したい` |
| love control | `いい出会いがほしい` |
| marriage control | `結婚したい` |
| family control | `子宝に恵まれたい` |
| mental control | `不安な気持ちを落ち着けたい` |

"Mutual understanding" (e.g. "人と分かり合いたい") was considered and
**deliberately excluded** from both the corpus and the vocabulary
expansion — it is not grounded in any existing product/audit semantics for
`communication`, and could plausibly collide with `relationship`'s own
domain. Documented as a known, unaddressed remaining gap (Section 9), not
silently dropped.

## 5. Safe Interpreter Expansion

5 new entries added to both `KEYWORDS["communication"]` and
`NEED_KEYWORDS["communication"]`:

```python
"コミュニケーション", "話せる", "話せない", "伝えられない", "伝わらない",
```

Each is either the Need's own literal name (`コミュニケーション`) or a
direct conjugation/negation of an **already-present** root
(`話す`→`話せる`/`話せない`; `伝える`→`伝えられない`/`伝わらない`) — no new
semantic family invented, consistent with the source audit's own framing
(Section 18: vocabulary additions are "valid under any Taxonomy outcome"
because they extend an already-established scope). No `REGEX` bare-root
pattern was used (unlike `rest`'s own criticized `落ち着` root) —
all 5 additions are exact conjugated/negated forms, deliberately avoiding
the overbroad-matching failure mode the source audit identified elsewhere.

Not modified: taxonomy, GID mapping, consultation axis, Text Evidence, C1
scoring, Ranking, Lead, Reason.

## 6. Baseline Coverage → After Coverage

| Query | Before | After |
|---|---|---|
| `人とうまく話せるようになりたい` | `hits={}` (**MISSED**) | `communication` ✓ |
| `職場でのコミュニケーションを改善したい` | `['relationship']` (**WRONG_NEED**, communication absent) | `['relationship', 'communication']` (**CORRECT_MULTI_NEED**) |
| `営業で成果を出したい` | `communication` ✓ | `communication` ✓ (unchanged) |
| `プレゼンが苦手で克服したい` | `communication` ✓ | `communication` ✓ (unchanged) |
| `コミュニケーション能力を上げたい` | `hits={}` (**MISSED**) | `communication` ✓ |
| `初対面の人と話すのが苦手` | `communication` ✓ | `communication` ✓ (unchanged) |
| `自分の気持ちをうまく伝えられない` | `hits={}` (**MISSED**) | `communication` ✓ |
| `人と話すのが怖い` | `hits={}` (**MISSED**) | `communication` ✓ |
| `会話が続かない` | `communication` ✓ | `communication` ✓ (unchanged) |

**Baseline coverage**: 5/9 (56%) correct-or-present, 1 `WRONG_NEED`, 3
`MISSED`. **After coverage**: 9/9 (100%) correct-or-multi-need, 0
`WRONG_NEED`, 0 `MISSED` in this corpus.

**This "100%" is not achieved by overmatching generic words** — verified
directly (`test_no_new_word_collides_with_any_other_need_keyword`): none of
the 5 new words appear in any of the other 14 Needs' own `KEYWORDS` lists.

## 7. False Positives / Cross-Need Collisions

**Before**: 0 false positives (communication was under- not over-matching).
**After**: 0 false positives — all 5 negative controls
(`relationship`, `love`, `marriage`, `family`, `mental`) live-verified
**byte-identical** to their pre-change extraction results:

| Control | Query | Result (unchanged before/after) |
|---|---|---|
| relationship | `職場の人間関係を改善したい` | `['relationship']` |
| love | `いい出会いがほしい` | `['love']` |
| marriage | `結婚したい` | `['marriage']` |
| family | `子宝に恵まれたい` | `['family']` |
| mental | `不安な気持ちを落ち着けたい` | `['mental', 'rest']` |

**Cross-Need collisions before**: 0 new. **Cross-Need collisions after**:
1, and it is a **correct, intentional** one — `職場でのコミュニケーションを
改善したい` now produces `['relationship', 'communication']` rather than
losing `communication` entirely; `relationship` remains primary
(`NEED_PRIORITY` index 9 < `communication`'s 10), matching the same
priority-governed co-extraction pattern already established for other
Needs (e.g. `夫婦関係を整えたい` → `['marriage', 'mental', 'rest']`,
re-verified unchanged in this PR's own regression, Section 9).

## 8. Newly Supported Phrases / Primary Need Changes / End-to-End Safety

Newly supported: `人とうまく話せるようになりたい`,
`コミュニケーション能力を上げたい`, `自分の気持ちをうまく伝えられない`,
`人と話すのが怖い` (previously `MISSED`); `職場でのコミュニケーションを
改善したい` (previously `relationship`-only, now correctly multi-Need).
No existing query's *primary* Need changed — `relationship` stays primary
for the one case where both Needs now co-occur.

**Live end-to-end proof through `build_chat_recommendations`**
(`コミュニケーション能力を上げたい`, candidate carrying `communication`'s
real GID id=30 強運厄除け):

```
matched_need_tags: ['communication']   <- was [] before this PR
score_need: 1                          <- was 0 before this PR
consultation_axis: other               <- UNCHANGED (still falls back)
reason: "強運厄除けのご利益で知られる強運厄除け神社は、
         今の願いを願う参拝先として適しています。"   <- UNCHANGED (still generic)
```

**Mapping changed?** No. **Taxonomy changed?** No. **Axis changed?** No.
**Ranking changed?** No.

**`INTERPRETER_IMPROVED_RECOMMENDATION_NOT_FULLY_RESOLVED`** — the
interpreter now correctly recognizes far more communication-intent
queries, but the Need's downstream Recommendation quality remains
unimproved: `communication`'s GID mapping (`{30,33,37,39}`, semantically
unrelated to communication) and consultation axis (no entry, always
`other`) are exactly as broken as documented in
`docs/audit/semantic-followup-decision-and-pr-split.md` Section 17, and
`intent_map` still has no `communication` entry (Reason stays generic).
**Recommendation quality for `communication` is NOT classified as fixed by
this PR.**

## 9. Regression

- Focused: `test_communication_interpreter_coverage.py` (new, 19 tests),
  `test_marriage_interpreter_coverage.py`, `test_marriage_reason_copy.py`,
  `test_need_to_goriyaku_tag_ids.py`,
  `test_concierge_relationship_love_separation.py`,
  `test_concierge_need_variation.py`,
  `test_concierge_eval_queries_seed80.py`,
  `test_consultation_axis_contract.py`, `test_compass_*` (×3),
  `test_concierge_explanation.py` — **239 passed, 0 failed** (no test
  needed updating — the one new cross-Need result, `職場でのコミュニケーシ
  ョンを改善したい`, was not previously asserted by any existing test).
- Full backend suite: **1788 passed, 15 skipped (pre-existing categories
  only), 0 failed**.
- No unexpected cross-Need regression (Section 7). No ranking logic
  change. No mapping change. No taxonomy change.

## 10. Production Safety

Production change is 2 vocabulary-list edits (5 words each) plus
explanatory comments, across `need_tags.py` and
`consultation_interpreter.py`. No Mapping, Axis, Text Evidence, C1,
Ranking, Lead, or Reason file touched.

## 11. Out of Scope

`communication`'s GID mapping, taxonomy fit, consultation axis, Text
Evidence, and `intent_map` Reason entry — all remain
`MOTHER_SHIP_DECISION_REQUIRED`/`BLOCKED_BY_UPSTREAM` per
`docs/audit/semantic-followup-decision-and-pr-split.md`, untouched here.
"Mutual understanding" vocabulary (Section 4) — deliberately not added,
flagged as a remaining gap for a future, separately-justified corpus.

## 12. STOP

Draft PR only. Not merged.
