# Remaining Need Semantic Decision Packets

## 1. Objective

Prepare Mother Ship decision packets for the four remaining open
semantic-decision surfaces — `family` scope, `mental`/`rest` boundary,
`communication` taxonomy, and `courage`/`career` shared evidence — and
convert whichever structure each decision implies into explicit,
Need-specific future PR blueprints. No product-semantic decision is made
in this document.

## 2. Scope

Fresh-read of current code on `origin/develop` (post-PR #2596, #2599,
#2600, and #2601 merges). Live runtime verification (`extract_need_tags`,
`resolve_need_payload`, `resolve_consultation_axis`,
`build_chat_recommendations`, Django ORM read-only queries) re-run in this
worktree, not copied from a prior session's output.

## 3. Non-Goals

No final selection among any decision packet's options. No REGEX
modification. No taxonomy expansion. No DB/model/migration/seed change. No
product priority ranking.

## 4. Base SHA

`origin/develop` @ `2f41098d`.
Worktree: `/Users/morietsu/Developer/jinja_app-remaining-need-semantic-decisions`,
branch `audit/remaining-need-semantic-decisions`.

## 5. Current Status of #2596

**Merged.** Merge commit `86a5764f9df8e43aea351d52119681f292492057`, all
CI green, exact expected 4-file scope (`concierge_chat_ranking.py`,
`concierge_explanation_payload.py`, new test file, new audit doc). Fresh-
confirmed on `origin/develop`: all 15 canonical Needs resolve to a real
Japanese `label_ja` across all 3 active dict copies.

## 6. R1a Status

**Merged.** [PR #2599](https://github.com/etsu33/jinja_app/pull/2599)
(`fix: add focus and travel safety reason copy`), all CI green. Fresh-
confirmed on `origin/develop`: `intent_map` now has 11 entries (added
`focus`, `travel_safe`); both resolve to their new copy, live-reconfirmed.

## 7. R1b Status

**Merged.** [PR #2600](https://github.com/etsu33/jinja_app/pull/2600)
(`fix: add relationship and health reason copy`). `relationship` and
`health` now use dedicated Reason copy on current `origin/develop`.
The generic Reason fallback gap for these two Needs is closed.

## 8. Communication C1 Status

**Merged.** [PR #2601](https://github.com/etsu33/jinja_app/pull/2601)
(`fix: improve communication interpreter coverage`). Current
`origin/develop` includes the approved communication interpreter vocabulary
expansion. Interpreter recall is improved, while the separate communication
taxonomy, GID mapping, Axis, Text Evidence, and Reason gaps remain unresolved.

This document's Decision Packet C (Sections 19–22) therefore evaluates the
remaining downstream semantic-design questions against the post-C1 state;
it does not treat the interpreter improvement as full Recommendation
resolution.

## 9. Family Current Contract

Fresh-read, re-confirmed unchanged since the prior audit:

- **KEYWORDS**: `["子宝", "安産", "妊活", "授かり", "出産", "育児"]` —
  entirely fertility/childbirth-centered. The literal word `"家族"` is
  **not present**; it belongs exclusively to `relationship`'s KEYWORDS.
- **REGEX**: none.
- **GID mapping**: `{2, 26, 34}` = 厄除け (51 shrines, shared with
  `protection`), 家庭円満 (1 shrine), 火防 (2 shrines) — reads as
  household-protection/harmony, not fertility.
- **ids 16/35 status** (fresh-reconfirmed this worktree): id=16 `安産`
  (safe childbirth, 5 shrines) is currently owned by `mental`
  (`NEED_TO_GORIYAKU_IDS["mental"] = {11,16,26,28,38}`), not `family`. id=35
  `子宝` (blessed with children, 1 shrine) is **owned by no Need** — one of
  8 orphaned canonical `GoriyakuTag` ids in the current 39-row master.
- **Text Evidence**: none (`NEED_TEXT_WEIGHTS` has no `family` entry).
- **Axis**: no `NEED_TAG_TO_CONSULTATION_AXIS` entry — always `other`.
- **Existing product/docs wording**: fresh-searched `docs/product/` this
  session — the only mention of `family` is as one of the 15 fixed tag
  names in `compass-mvp-runtime-contract.md`; no document anywhere states
  an intended scope.
- **DB evidence**: 51 shrines carry id=2 (dominant, shared with
  `protection`'s own primary id), 1 carries id=26, 2 carry id=34.
- **Collision with relationship**: `家族円満を願いたい`→`relationship`
  only; `親子関係を良くしたい`→`relationship` only; `家族の健康を願いたい`
  →`health`+`relationship` (family absent in all three).
- **Collision with health**: same third example above.
- **Examples requested by this task**, fresh-run:

| Query | Result |
|---|---|
| `家族円満を願いたい` | `relationship` (family absent) |
| `家族の健康を願いたい` | `health`+`relationship` (family absent) |
| `親子関係を良くしたい` | `relationship` (family absent) |
| `家庭を整えたい` | `mental`+`rest` (via `整えたい`; neither family nor relationship — `relationship`'s KEYWORDS has `家族` but not `家庭`) |
| `子宝に恵まれたい` | `family` (correct) |
| `安産祈願をしたい` | `family` (correct) |

Family's interpreter vocabulary, GID mapping, and the master's own
best-fitting tags for that vocabulary remain three mutually inconsistent
signals.

## 10. Family Option A — FAMILY_SCOPE_NARROW

Family remains pregnancy/childbirth/parenting-centered, matching current
KEYWORDS.

| Impact area | Assessment |
|---|---|
| Interpreter | None required. |
| GID Mapping | Real correction needed regardless of option: reassign id=16 (安産) from `mental`→`family`; add orphaned id=35 (子宝); decide fate of ids 2/26/34 (household-flavored, poor fit here). |
| Taxonomy | None — ids 16/35 already exist in the master. |
| Axis | No existing axis fits "fertility/childbirth" well; stays `other`, or a new axis is a separate, smaller decision. |
| Text Evidence | Low-risk mechanical addition (`子宝`, `安産`, `妊活`, etc.), once mapping is corrected. |
| DB evidence implications | Family's practical evidence pool shifts from the current 54-shrine household-flavored pool (dominated by id=2's 51 shrines, shared with `protection`) to a genuinely fertility-specific 6-shrine pool (5+1). Smaller but semantically honest. |
| Migration risk | None. |
| Regression risk | Low — `mental`'s own test fixtures must be checked for reliance on id=16 (none found in this fresh read, but must be verified at implementation time). |
| Future PR count | 2 (mapping correction; Reason addition) + optionally 1 (Text Evidence). |

## 11. Family Option B — FAMILY_SCOPE_BROAD

Family becomes a broader household/family-relationship intent, absorbing
territory currently owned exclusively by `relationship`.

| Impact area | Assessment |
|---|---|
| Interpreter | High-impact: adding `家族`/`家庭`/`親子関係`/`家族円満` to `family`'s KEYWORDS directly overlaps `relationship`'s own KEYWORDS (`家族`, `親子` already there). `family` sits at `NEED_PRIORITY` index 3, `relationship` at index 9 — `family` would begin **winning** the priority-pick for queries currently resolving to `relationship`, a real, silent behavioral change. |
| GID Mapping | Moderate: id=26 (家庭円満) is already a good fit; fertility ids (16, 35) need a decision on whether they stay within the now-broader `family`. |
| Taxonomy | None new needed. |
| Axis | `relationship_repair` is a natural reuse. |
| Text Evidence | New entries needed (e.g. `家族円満`). |
| DB evidence implications | Evidence pool grows to include `relationship`'s own id=1 territory conceptually, but no GID overlap exists today between `family`{2,26,34} and `relationship`{1} — a genuinely new evidence question, not just interpreter. |
| Migration risk | None new needed, but requires an explicit design decision on whether family's fertility-sense is retained alongside or removed. |
| Regression risk | High and *deliberate* — intentionally creates a new priority-order-sensitive overlap with `relationship`, requiring its own collision-handling design and dedicated regression corpus. |
| Future PR count | 3+ (interpreter+priority-collision design; mapping; axis/Reason) — highest-risk option. |

## 12. Family Option C — FAMILY_SPLIT_REQUIRED

The current single `family` tag cannot safely represent both concepts.

| Impact area | Assessment |
|---|---|
| Interpreter | Depends on sub-option: (a) a 16th canonical Need tag — touches `NEED_TAGS`, `NEED_PRIORITY`, and every Need-keyed dict in the codebase (`KEYWORDS`, `REGEX`, `NEED_TO_GORIYAKU_IDS`, `NEED_TAG_TO_CONSULTATION_AXIS`, `NEED_TEXT_WEIGHTS`, `NEED_LABELS_JA` ×3 copies, `intent_map`) — the single most invasive change surveyed; or (b) a documentation-only decision that `relationship` already fully owns "family relations" and `family` stays narrow — collapses into Option A plus a written note. |
| GID Mapping | High if (a); none if (b). |
| Taxonomy | High if (a) — changes the canonical Need *count*, beyond this document's own authority to decide. None if (b). |
| Axis | Reuse `relationship_repair` if (a); none if (b). |
| Text Evidence | Only relevant if (a). |
| DB evidence implications | Only relevant if (a) — would need its own evidence pool distinct from both `family`'s current one and `relationship`'s. |
| Migration risk | High if (a); none if (b). |
| Regression risk | Aims to eliminate the collision by construction, but a poorly-scoped new tag under (a) could recreate it as a 16th collision surface. |
| Future PR count | 4+ if (a); 0 (docs-only) if (b). |

## 13. Family Technical Comparison

| Criterion | Option A (Narrow) | Option B (Broad) | Option C (Split) |
|---|---|---|---|
| Interpreter change | None | High, deliberate collision | None (a) / High (b, new tag) |
| Mapping change | Moderate | Moderate | None (b) / High (a) |
| New taxonomy | No | No | No (b) / Would need a new Need tag concept (a) — out of this audit's authority |
| Regression risk | Low | High | Low (b) / Highest (a) |
| PR count | 2–3 | 3+ | 0 (b) / 4+ (a) |

`TECHNICALLY_LOWEST_RISK`: **Option A (FAMILY_SCOPE_NARROW)** — requires
no interpreter change, no new taxonomy, and its mapping correction
(reassign id=16, add id=35) is valid under any of the three options, since
all three retain some fertility-relevant evidence attached to `family`.
This is a technical-risk observation only, not a product recommendation.

## 14. Mental Current Contract

Fresh-read, unchanged: KEYWORDS include `"心を整えたい"`, `"心を整える"`,
`"気持ちを整えたい"`, `"気持ちを切り替えたい"`, the bare root
`"整えたい"`, `"疲れ"`, `"疲れて"`, `"疲れている"`, `"疲労"`, `"癒し"`.
REGEX adds `心を整え` and `疲れ(て|が|た)?`. GID: `{11,16,26,28,38}`
(includes the family-relevant id=16 misassignment, Section 9). Axis:
`restart_mindset` (`DIRECT_FIT`). `intent_map`: present,
`"不安や心の安定"`.

**New, previously-undiscovered finding this session**: `need_tags.py` also
defines a **third, separate** text-hint structure, `NEED_TEXT_HINTS`
(distinct from `concierge_chat_ranking.py`'s `NEED_TEXT_WEIGHTS`), whose
`"mental"` entry explicitly includes `"落ち着きたい"`, `"落ち着ける"`,
alongside `不安`, `落ち込む`, `気持ち`, `心`, `悩み`, `疲れ`,
`疲れている`, `しんどい`, `心を整えたい`, `気持ちを整えたい`, `流れが悪い`,
`最近うまくいかない`. **Repository-wide search confirms `NEED_TEXT_HINTS`
is defined but never imported or referenced anywhere else in the codebase
— dead code, inert.** Noted for completeness; does not affect any live
behavior or any conclusion in this document.

## 15. Rest Current Contract

Fresh-read, unchanged: KEYWORDS include `"休みたい"`, `"休息"`, `"疲れ"`,
`"回復"`, `"睡眠"`, `"眠れない"`, `"リセット"`, `"穏やか"`, `"静か"`,
`"落ち着きたい"`, `"落ち着く"`, `"心を整えたい"`, the bare root
`"整えたい"`, `"自然"`, `"ゆっくり"`, `"過ごしたい"`, `"癒し"`, and more.
REGEX: a single bare-root pattern
`re.compile(r"(穏やか|静か|落ち着|リセット|休息|癒し|ひと息|一息)")` — the
`落ち着` root has no okurigana, matching any conjugation containing it,
including `落ち着け` (causative-potential), which `rest`'s own KEYWORDS
does not itself list. GID: `{7,8}`. Axis: `rest_healing` (`DIRECT_FIT`).
`intent_map`: present, `"休息や気持ちの切り替え"` (also unaffected by
`NEED_TEXT_HINTS["rest"]`, same dead-code status as Section 14).

## 16. Mental/Rest Collision Corpus

Fresh-run in this worktree (not reused verbatim from a prior session's
output):

| Query | Interpreter hits | Normalized tags | Axis | GID evidence |
|---|---|---|---|---|
| `気持ちを落ち着けたい` | `{'rest': ['落ち着']}` | `['rest']` | `rest_healing` (need_tags) | `{7,8}` |
| `心を整えたい` | `{'mental': ['心を整えたい','整えたい','心を整え'], 'rest': ['心を整えたい','整えたい']}` | `['mental','rest']` | `restart_mindset` (need_tags) | `{7,8,11,16,26,28,38}` |
| `不安を和らげたい` | `{'mental': ['不安']}` | `['mental']` | `restart_mindset` (need_tags) | `{11,16,26,28,38}` |
| `少し休みたい` | `{'rest': ['休みたい']}` | `['rest']` | `rest_healing` (query) | `{7,8}` |
| `静かに過ごしたい` | `{'rest': ['静か','過ごしたい','静か']}` | `['rest']` | `rest_healing` (query) | `{7,8}` |
| `疲れを癒したい` | `{'mental': ['癒し','疲れ','疲れ'], 'rest': ['疲れ','癒し','癒し']}` | `['mental','rest']` | `rest_healing` (query) | `{7,8,11,16,26,28,38}` |
| `落ち着ける場所に行きたい` | `{'rest': ['落ち着']}` | `['rest']` | `rest_healing` (query) | `{7,8}` |

Full pipeline trace for the sharpest case (`気持ちを落ち着けたい`):
`Input → raw Need=['rest'] → normalized=['rest'] → primary=rest → Axis=
rest_healing → evidence GID={7,8} → C1: mental-evidence-only candidate
scores score_need=0 (evidence never checked, mental never in play) →
rest-evidence-only candidate scores score_need=1 → Top3: rest-evidence
candidate ranks ahead of mental-evidence candidate → Lead: rest-evidence
candidate cites its real GID label; mental-evidence candidate falls to
generic "ご利益" → Reason: rest-flavored copy for a mental-intent query.`
Live-verified in the source audit (`docs/audit/semantic-followup-decision-
and-pr-split.md` Section 15); re-confirmed here via fresh corpus re-run
(interpreter/axis/GID layers, table above) — the downstream Lead/Reason
mechanism itself is unchanged by anything in this task's earlier phases
(R1a/R1b/C1 never touch `mental`/`rest`).

`気持ちを落ち着けたい` remains the sharpest finding: a mental/emotional-
intent query resolves to `rest` **only**, with `mental` entirely absent —
not merely a collision, a real misroute.

## 17. Mental/Rest Options

**REGEX is not modified anywhere in this document — options describe
technical shape only.**

### Option A — Keep current co-extraction as intentional
| Impact | Assessment |
|---|---|
| Interpreter | None |
| Priority | None |
| Mapping | None |
| Ranking risk | None — status quo |
| Explanation impact | None |
| Control regression risk | None (no change) |

### Option B — Narrow rest's bare-root matching
(e.g. require okurigana: `落ち着(き\|く\|いた)` instead of the bare `落ち着`)
| Impact | Assessment |
|---|---|
| Interpreter | Changes `rest`'s single REGEX entry |
| Priority | None |
| Mapping | None |
| Ranking risk | Low-medium — must re-verify every other `rest`-REGEX-dependent case; `落ち着ける場所に行きたい` would also stop matching `rest` via REGEX unless `mental` gains its own coverage for the causative form |
| Explanation impact | `気持ちを落ち着けたい` would then extract neither Need (a `MISSED` regression) unless paired with Option C |
| Control regression risk | Medium — the 7-query corpus plus any existing `rest`-REGEX test coverage |

### Option C — Expand mental coverage while allowing overlap
(add `落ち着け` to `mental`'s own KEYWORDS/REGEX, additive, not replacing rest's)
| Impact | Assessment |
|---|---|
| Interpreter | Adds a `mental` REGEX/KEYWORDS entry |
| Priority | None |
| Mapping | None |
| Ranking risk | Low — additive; `気持ちを落ち着けたい` becomes `mental`+`rest` (matches the existing `心を整えたい` pattern) rather than `rest`-only |
| Explanation impact | Positive — mental-intent queries would surface mental evidence, not just rest's |
| Control regression risk | Low — same 7-query corpus |

### Option D — Reduce shared vocabulary, establish stricter separation
(remove `整えたい`/`疲れ`/`癒し` from one Need's KEYWORDS)
| Impact | Assessment |
|---|---|
| Interpreter | Non-trivial — requires per-Need judgment on which Need "owns" each shared word |
| Priority | None |
| Mapping | None |
| Ranking risk | Medium — a real behavior change for every query currently co-extracting both |
| Explanation impact | Would sharpen Reason/Lead differentiation, at the cost of losing legitimate dual-relevance cases (e.g. `疲れを癒したい` arguably IS both mental and physical) |
| Control regression risk | Medium-high — full corpus, both isolated and collision cases |

## 18. Mental/Rest Technical Comparison

| Criterion | A (keep) | B (narrow rest) | C (expand mental) | D (deduplicate) |
|---|---|---|---|---|
| REGEX touched | No | Yes | Yes (new entry) | Possibly |
| Introduces new MISSED case | No | Yes, unless paired with C | No | No |
| Regression corpus size | None | Full | Full | Full |
| Reversibility | N/A | Medium | High | Low |

`TECHNICALLY_LOWEST_RISK`: **Option A (keep current co-extraction as
intentional)** — zero code change, zero regression surface. This is a
technical-risk observation only; it does not address whether the
`気持ちを落ち着けたい` mental-loss behavior (Section 16) is acceptable
product behavior, which remains an open product question regardless of
technical risk ranking.

## 19. Communication Current Contract

Fresh-read against **current, post-C1** `origin/develop` state
(Section 8):

- **Interpreter**: PR #2601 expanded both active communication vocabulary
  copies from the original 8-word set by adding
  `コミュニケーション`, `話せる`, `話せない`, `伝えられない`, `伝わらない`.
  The approved C1 regression corpus improved to 9/9 communication coverage
  with zero new false positives across the recorded negative controls.
  Interpreter recall is therefore improved and is no longer the primary
  unresolved communication defect.
- **Priority**: `communication` at `NEED_PRIORITY` index 10 (after
  `relationship` at 9) — unchanged.
- **Normalized Need behavior**: no alias maps to or from `communication`.
- **Consultation axis**: no `NEED_TAG_TO_CONSULTATION_AXIS` entry, no
  `CONSULTATION_AXIS_KEYWORDS` entry anywhere — fresh-confirmed zero
  references to `communication` in `consultation_axis.py` — always `other`.
- **GID mapping**: `{30, 33, 37, 39}` = 強運厄除け, 病気平癒, 延命長寿,
  農業守護 — none semantically fit "communication."
- **Tag-name semantic validity**: see Section 20 (existing taxonomy
  candidate review).
- **DB evidence count**: 4 shrines total across the 4 mapped ids (1 each).
- **Text Evidence availability**: none (`NEED_TEXT_WEIGHTS` has no
  `communication` entry).
- **Relationship overlap**: `職場` remains a relationship-side keyword,
  so communication-intended queries containing workplace language can
  still co-extract or compete with `relationship`. PR #2601 improves
  communication recall but does not redefine the communication /
  relationship semantic boundary.
- **Lead**: mechanism-healthy but evidence-starved for the 4 semantically
  weak GIDs.
- **Reason**: no `intent_map` entry — generic fallback.
- **Current Top3 behavior**: a candidate carrying only communication's
  weak GIDs still ranks correctly relative to unrelated candidates (C1/
  Ranking mechanism itself is unaffected by evidence quality), but the
  Reason/Lead text it produces does not read as "communication" evidence
  to a user.

## 20. Existing Taxonomy Candidate Review

Fresh-read of all 39 canonical `GoriyakuTag` rows for plausible fit to
"communication skill/ability":

| id | Name | Classification | Rationale |
|---|---|---|---|
| 30 | 強運厄除け (strong-luck warding) | `NOT_FIT` | Warding/luck concept, unrelated to interpersonal communication. |
| 33 | 病気平癒 (illness recovery) | `NOT_FIT` | Health concept, unrelated. |
| 37 | 延命長寿 (longevity) | `NOT_FIT` | Health/longevity concept, unrelated. |
| 39 | 農業守護 (agricultural protection) | `NOT_FIT` | Agriculture concept, unrelated. |
| 21 | 導き (guidance) | `PARTIAL_FIT` | "Guidance" could loosely support decision-making/direction-seeking, but is currently `career`'s own id — reuse would create a new cross-Need overlap, and "guidance" is not specifically about interpersonal communication. |
| 25 | 芸能 (performing arts) | `PARTIAL_FIT` | Performance/expression-adjacent, but oriented toward artistic skill, not interpersonal communication; currently orphaned (owned by no Need). |
| 29 | 芸能運 (performing-arts luck) | `PARTIAL_FIT` | Same caveat as id=25; currently orphaned. |
| 31 | 技芸上達 (skill improvement) | `PARTIAL_FIT` | General "skill improvement" is broad enough to loosely cover communication-skill-building, but is equally applicable to any skill; currently orphaned. |
| All remaining 31 ids | — | `NOT_FIT` or `MISLEADING` | Reviewed individually (縁結び, 厄除け, 開運, 家内安全, 福徳, 学業成就, 合格祈願, 勝運, 仕事運, 交通安全, 海上安全, 航海安全, 武運長長, 安産, 八方除, 夫婦円満, 八難除, 恋愛成就, 健康長寿, 家庭円満, 出世運, 金運, 心願成就, 火防, 子宝, 美容, 方除け, 八方除け) — none plausibly represent "communication ability" without significant semantic stretching. |

**No `CLEAR_FIT` candidate exists in the current 39-row master.** The 4
`PARTIAL_FIT` candidates (21, 25, 29, 31) are, at best, adjacent-skill or
adjacent-guidance concepts, not communication-specific, and 3 of the 4 are
currently unowned by any Need (a separate, pre-existing orphaned-tag
observation, out of this document's scope to resolve).

## 21. Communication Taxonomy Options

Answering the 5 required questions:

1. **Does a valid existing canonical tag exist?** No — 0 `CLEAR_FIT`, 4
   `PARTIAL_FIT` at best (Section 20).
2. **Would approximate reuse cause semantic leakage?** Yes for the current
   `{30,33,37,39}` set (already causes it — a communication-tagged Lead
   cites 強運厄除け/病気平癒/延命長寿/農業守護, none recognizable as
   communication evidence). Reusing a `PARTIAL_FIT` id like 21 (導き, career's
   own) would also cause leakage in the other direction (career's own
   evidence pool would need a decision on whether to share it).
3. **Is a new canonical tag required?** Only if the answer to "is investment
   in `communication` worth it" (Option B below) is yes — not otherwise.
4. **Could communication remain interpreter-only without Recommendation
   evidence?** Yes, technically — Track C1 ([PR #2601](https://github.com/etsu33/jinja_app/pull/2601))
   already demonstrates this is possible: interpreter recall improves
   independent of evidence quality, at the cost of a match that scores but
   cannot produce meaningful Lead/Reason text.
5. **What downstream layers depend on the taxonomy decision?** GID Mapping
   (directly), Text Evidence (directly, once Mapping exists), Axis (weakly
   — a real axis choice presupposes knowing what evidence anchors the Need),
   Reason (blocked via Mapping). Interpreter does **not** depend on it
   (Section 8, PR #2601).

### Option A — Reuse an existing canonical tag
No `CLEAR_FIT` candidate exists (Section 20); the best `PARTIAL_FIT`
options (21, 25, 29, 31) either create new cross-Need sharing questions
(21, already `career`'s) or remain semantically loose (25/29 performing-
arts-flavored, 31 generically skill-flavored) — **explicitly stated as
required**: this option has no strong candidate to reuse.

### Option B — Add new communication-specific GoriyakuTag taxonomy
Would require new canonical rows (out of this document's authority to
create) and, per the Global Safety Rules, is not something this task
implements — a pure Mother Ship investment decision.

### Option C — Keep communication recognized but Recommendation-evidence-limited
Accept the current interpreter-only path (Track C1) as the durable state;
`communication` remains matchable (`score_need` can be 1) but its Lead/
Reason quality stays generic/unrelated indefinitely.

## 22. Communication Dependency Graph

```
Taxonomy/Mapping Decision (Mother Ship)
    |
    +--> [if Option B] new canonical GoriyakuTag rows
    |       |
    |       +--> Mapping correction
    |               |
    |               +--> Text Evidence
    |               |
    |               +--> Axis choice
    |               |
    |               +--> Reason (intent_map)
    |
    +--> [if Option A or C] no further chain -- Option A has no strong
              candidate (Section 21); Option C stops here by design

Interpreter vocabulary (Track C1, PR #2601) -- INDEPENDENT, already
  merged, does not depend on and is not depended on
  by any node above.
```

`TECHNICALLY_LOWEST_RISK`: **Option C (keep communication recognized but
Recommendation-evidence-limited)** — zero new taxonomy, zero mapping
churn, zero new cross-Need sharing questions; the interpreter improvement
already merged (PR #2601) delivers its own independent value under this
option with no further work required. This is a technical-risk
observation only.

## 23. Courage Current Contract

Fresh-read, unchanged: `NEED_TO_GORIYAKU_IDS["courage"] = {12,15,18,20,24,30,38}`
— 仕事運, 武運長久, 夫婦円満, 恋愛成就, 健康長寿, 強運厄除け, 足腰健康.
`NEED_TEXT_WEIGHTS["courage"]` includes `勝運` at weight 3 (its highest
tier), alongside `開運`/`開運祈願`/`運を開く`/`背中を押して`/
`一歩踏み出す`/`勇気`/`変わりたい`. Total DB evidence: 20 shrine-
references across the 7 ids.

## 24. Courage/Career Shared Evidence

Fresh-confirmed this worktree: `NEED_TO_GORIYAKU_IDS["career"] = {6,21,30,12,27}`.
**Shared ids: `{12, 30}`** (仕事運, 11 shrines; 強運厄除け, 1 shrine) —
official members of both Needs' mapped sets. `NEED_TEXT_WEIGHTS` also
shares `勝運` verbatim (career weight 2, courage weight 3).

**Winning evidence / Top3 behavior** (fresh live re-run, three synthetic
candidates: shared-id=12 only, courage-exclusive id=15, career-exclusive
id=21):

| Query (intent) | id=12 candidate | id=15 candidate (courage-only) | id=21 candidate (career-only) |
|---|---|---|---|
| `新しいことに挑戦したい` (courage) | `matched=['courage']`, `winner={'courage':'gid'}` | `matched=['courage']`, `winner={'courage':'gid'}` | `matched=[]`, `score_need=0` |
| `転職を考えている` (career) | `matched=['career']`, `winner={'career':'gid'}` | `matched=[]`, `score_need=0` | `matched=['career']`, `winner={'career':'gid'}` |

**Zero observed leakage in either direction** — the shared-id candidate's
matched Need, winner, and (by extension) Reason/Lead correctly and
exclusively track whichever Need the query actually expressed.

**Removal simulation** (fresh-computed, current shrine counts):

| Need | Total with shared ids | Total without ids {12,30} |
|---|---:|---:|
| courage | 20 | **8** |
| career | 74 | 62 |

Removing the shared ids costs `courage` a real, quantified 60% reduction
in its evidence pool (`PARTIAL`→`SPARSE` by the source audit's own
banding); `career` is comfortably unaffected either way (`STRONG` in both
cases).

## 25. Courage Options

### Option A — Keep shared evidence intentionally
| Impact | courage evidence | career evidence | Ranking churn | C1 impact | Top3 impact | Semantic precision | Data sparsity risk |
|---|---:|---:|---|---|---|---|---|
| | 20 | 74 | None | None | None | Two independently-defensible readings of `勝運`/id=12/id=30 (Section 26 of the source audit answered Q1/Q2 both "yes") | id=30's 1-shrine sample stays thin regardless |

### Option B — Separate GID mapping only
(remove ids 12/30 from one Need's `NEED_TO_GORIYAKU_IDS` set)
| Impact | courage evidence | career evidence | Ranking churn | C1 impact | Top3 impact | Semantic precision | Data sparsity risk |
|---|---:|---:|---|---|---|---|---|
| If removed from courage | **8** | 74 | Medium — any candidate previously matching courage via 12/30 alone would stop matching | C1 has nothing to evaluate for those candidates under courage | Some previously-ranked candidates drop out of courage's Top3 entirely | Improves (courage's remaining evidence is 100% courage-exclusive) | Increases — courage's total pool nearly halves |
| If removed from career | 20 | 62 | Low — career stays `STRONG` regardless | Same, career-side | Minimal — career's Top3 barely changes | Improves for career | Minimal — career stays comfortably resourced |

### Option C — Separate Text Evidence only
(remove `勝運` from one Need's `NEED_TEXT_WEIGHTS`)
| Impact | courage evidence | career evidence | Ranking churn | C1 impact | Top3 impact | Semantic precision | Data sparsity risk |
|---|---:|---:|---|---|---|---|---|
| | Unchanged (GID) | Unchanged (GID) | Low — only affects candidates whose free text contains 勝運 without the matching GID already present | Text-only winners for that word would disappear from one Need | Low, since GID evidence for both Needs is unaffected | Improves Reason/Lead specificity slightly | None — Text Evidence removal doesn't reduce GID-based evidence counts |

### Option D — Separate both GID + Text Evidence
Combines B and C's effects; same evidence-count consequences as whichever
side of Option B is chosen, plus Option C's Text-side effect.

## 26. Courage Technical Comparison

| Criterion | A (keep) | B (mapping only) | C (text only) | D (both) |
|---|---|---|---|---|
| Evidence-count cost to courage | None | Up to −60% (if removed from courage) | None | Up to −60% (if removed from courage) |
| Evidence-count cost to career | None | Minimal either way | None | Minimal either way |
| Observed real-world harm today | None (Section 24) | N/A (preventative) | N/A (preventative) | N/A (preventative) |
| Regression corpus needed | None | Full career+courage evidence recount | Small (Text-evidence-only queries) | Full |

`TECHNICALLY_LOWEST_RISK`: **Option A (keep shared evidence
intentionally)** — zero evidence-count cost to either Need, zero observed
real-world harm (Section 24's live proof), zero regression surface. This
is a technical-risk observation only; it does not resolve whether the
overlap was ever *deliberately* designed (Section 21 of the source audit:
repository evidence is insufficient to assert intent either way).

## 27. Mother Ship Decision Matrix

| Topic | Current Behavior | Problem | Option A | Option B | Option C | Technical Consequence | Decision Required |
|---|---|---|---|---|---|---|---|
| Family scope | KEYWORDS=fertility-only; GID={2,26,34}=household-flavored; ids 16/35 (best fertility fits) sit outside family's mapping | Three internally-inconsistent signals for what "family" means | `FAMILY_SCOPE_NARROW` (`TECHNICALLY_LOWEST_RISK`) | `FAMILY_SCOPE_BROAD` | `FAMILY_SPLIT_REQUIRED` | Narrow: 2–3 PRs, no taxonomy change. Broad: 3+ PRs, deliberate new `relationship` collision. Split: 0 PRs (docs-only) or 4+ PRs (new 16th Need tag) | Yes |
| Mental/rest boundary | Shared vocabulary (`整えたい`,`疲れ`,`癒し`) plus rest's bare-root REGEX causes co-extraction and, in one case, complete `mental` loss | Intentional multi-Need signaling, or a defect? | Keep as-is (`TECHNICALLY_LOWEST_RISK`) | Narrow rest's REGEX root | Expand mental's own coverage (additive) | Keep: 0 PRs. Narrow: 1 PR + full REGEX-dependent regression, risks a new MISSED case. Additive: 1 PR, lower risk | Yes |
| Communication taxonomy | No canonical tag fits (0 `CLEAR_FIT`, Section 20); current mapping is a placeholder | Invest in new evidence, or accept permanent GID-sparsity? | Reuse existing tag (no strong candidate exists) | Add new canonical taxonomy | Interpreter-recognized, evidence-limited (`TECHNICALLY_LOWEST_RISK`) | Reuse: not viable per Section 20/21. New taxonomy: full Mapping/Axis/Reason chain. Evidence-limited: PR #2601 already delivers this option's full value | Yes |
| Courage/勝運 evidence boundary | ids 12/30 officially shared with career; zero leakage observed live; removing costs courage real evidence strength (−60%) | Intentional, or should it be separated? | Leave as-is (`TECHNICALLY_LOWEST_RISK`) | Remove courage's claim on 12/30 | Remove career's claim on 12/30 | Leave: 0 PRs. Remove-from-courage: 1 PR, courage evidence −60%. Remove-from-career: 1 PR, career minimally affected | Yes |
| Missing Reason items (decision-gated) | `family`, `communication` remain on generic fallback Reason text | Blocked by the two decisions above, not by Reason-writing itself | Resolve via Family Scope Decision first | Resolve via Communication Taxonomy Decision first | — | See Section 28's R2/R3 tracks | Yes (inherited) |

## 28. Future Need-Specific PR Blueprints

### family

| Field | Interpreter | Mapping | Reason | Taxonomy (if split) |
|---|---|---|---|---|
| Track ID | E1 | M1 | R2 | S1 |
| Need | family | family | family | family |
| Decision dependency | Family Scope Decision = BROAD or SPLIT(a) | Family Scope Decision (any option) | Family Scope Decision + M1 | Family Scope Decision = SPLIT(a) |
| Objective | Expand KEYWORDS to household/family-relations vocabulary | Reassign id=16, add id=35, resolve ids 2/26/34 | Add `intent_map` entry | Introduce new canonical Need tag + full dict wiring |
| Layer | Interpreter | Mapping | Reason | Taxonomy (system-wide) |
| Likely files | `need_tags.py`, `consultation_interpreter.py` | `need_to_goriyaku_tag_ids.py` | `concierge_chat_ranking.py` | `need_tags.py`, `consultation_axis.py`, `need_to_goriyaku_tag_ids.py`, `concierge_chat_ranking.py` (×2 dicts), `concierge_explanation_payload.py` |
| Non-goals | No mapping/axis change in same PR | No interpreter/axis/Reason change in same PR | No mapping/interpreter change | No changes to any other Need's existing behavior |
| Test corpus | Explicit `relationship` regression corpus (priority-order risk) | `mental`'s own fixtures re-checked for id=16 reliance | Same gates as R1a/R1b | Full 15→16-Need regression across every dict |
| Regression gates | 0 failures, existing skips only | 0 failures; `mental` evidence-count re-verified | 0 failures, Ranking/Lead/Top3 churn=0 | 0 failures across entire suite; explicit before/after Need-count assertion |
| Dependency | Family Scope Decision, likely after M1 | Family Scope Decision | Family Scope Decision, M1 | Family Scope Decision |
| Suggested branch | `fix/family-interpreter-vocabulary-expansion` | `fix/family-gid-mapping-correction` | `fix/reason-copy-family` | `feat/family-split-taxonomy` (illustrative) |
| Suggested commit | `fix: expand family interpreter vocabulary` | `fix: correct family GID mapping` | `fix: add reason copy for family` | `feat: split family into two canonical needs` (illustrative) |
| Completion definition | New KEYWORDS entries; `relationship` regression corpus proves no unintended priority-order change | id=16→family, id=35 added, ids 2/26/34 resolved per decision; `mental`'s fixtures still pass | `intent_map["family"]` present; completeness test passes | New Need tag fully wired across every dict; full suite green |

### mental/rest

| Field | Interpreter boundary | Regex narrowing | Keyword split |
|---|---|---|---|
| Track ID | D1a (Option C: expand mental) | D1b (Option B: narrow rest) | D1c (Option D: deduplicate) |
| Need | mental, rest | rest | mental, rest |
| Decision dependency | Mental/Rest Boundary Decision = Option C | Mental/Rest Boundary Decision = Option B | Mental/Rest Boundary Decision = Option D |
| Objective | Add `mental` coverage for `落ち着け` causative form, additive | Narrow `rest`'s bare REGEX root to require okurigana | Remove shared words from one Need's KEYWORDS |
| Layer | Interpreter | Interpreter (REGEX) | Interpreter |
| Likely files | `need_tags.py` | `need_tags.py` | `need_tags.py`, `consultation_interpreter.py` |
| Non-goals | No Mapping/Axis/Reason change | No Mapping/Axis/Reason change; must not silently create a new MISSED case (pair with D1a if narrowing) | No Mapping/Axis/Reason change |
| Test corpus | Full 7-query corpus (Section 16) | Full 7-query corpus + any existing rest-REGEX coverage | Full 7-query corpus, isolated and collision cases |
| Regression gates | 0 failures; `気持ちを落ち着けたい` becomes `['mental','rest']` | 0 failures; every other REGEX-dependent case re-verified | 0 failures; explicit before/after co-extraction table |
| Dependency | Mental/Rest Boundary Decision | Mental/Rest Boundary Decision | Mental/Rest Boundary Decision |
| Suggested branch | `fix/mental-rest-boundary-expand-mental` | `fix/mental-rest-boundary-narrow-rest-regex` | `fix/mental-rest-boundary-deduplicate` |
| Suggested commit | `fix: add mental coverage for causative calming form` | `fix: narrow rest bare-root regex` | `fix: deduplicate mental/rest shared vocabulary` |
| Completion definition | `気持ちを落ち着けたい`→`['mental','rest']`, corpus green | No REGEX-dependent case newly MISSED, corpus green | Each shared word has exactly one owning Need, corpus green |

### communication

Communication Interpreter (Track C1) is already implemented as
[PR #2601](https://github.com/etsu33/jinja_app/pull/2601) and is **not
duplicated** below.

| Field | Taxonomy | Mapping | Axis | Text Evidence | Reason |
|---|---|---|---|---|---|
| Track ID | C2 | C2m | C3 | C2t | R3 |
| Need | communication | communication | communication | communication | communication |
| Decision dependency | Communication Taxonomy Decision = Option B | C2 (only if Option B) | C2 | C2m | C2m |
| Objective | Add new canonical `GoriyakuTag` row(s) for communication | Point `NEED_TO_GORIYAKU_IDS["communication"]` at the new row(s) | Add axis entry if one fits post-Mapping | Add Text Evidence words | Add `intent_map` entry |
| Layer | Taxonomy (new DB rows) | Mapping | Axis | Text Evidence | Reason |
| Likely files | new migration + `GoriyakuTag` seed data | `need_to_goriyaku_tag_ids.py` | `consultation_axis.py` | `concierge_chat_ranking.py` | `concierge_chat_ranking.py` |
| Non-goals | No Need-count change | No interpreter/axis change in same PR | — | — | — |
| Test corpus | New taxonomy-specific tests | Full communication corpus (this doc + PR #2601's) | 0 failures | 0 failures | Same gates as R1a/R1b |
| Regression gates | 0 failures, explicit before/after GoriyakuTag-count assertion | 0 failures, DB evidence count re-verified | 0 failures | 0 failures | 0 failures, Ranking/Lead/Top3 churn=0 |
| Dependency | Communication Taxonomy Decision | C2 | C2 (via C2m) | C2m | C2m |
| Suggested branch | `feat/communication-canonical-taxonomy` (illustrative) | `fix/communication-gid-mapping` | `fix/communication-axis` | `fix/communication-text-evidence` | `fix/reason-copy-communication` |
| Suggested commit | `feat: add communication canonical evidence tags` (illustrative) | `fix: map communication to new canonical evidence` | `fix: add communication consultation axis` | `fix: add communication text evidence` | `fix: add reason copy for communication` |
| Completion definition | New rows exist, reviewed for genuine communication fit | `NEED_TO_GORIYAKU_IDS["communication"]` points at real evidence, DB count check passes | Axis resolves for communication queries where appropriate | Text-evidence-driven matches surface correctly | `intent_map["communication"]` present, completeness test passes |

### courage

Combined evidence implementation (Track G-combined) is listed **only** for
completeness in case Mother Ship explicitly selects Option D — it is not a
default or assumed path.

| Field | Mapping review | Text Evidence review | Combined (only if explicitly selected) |
|---|---|---|---|
| Track ID | G1a | G1b | G1c |
| Need | courage, career | courage, career | courage, career |
| Decision dependency | Courage Evidence Decision = Option B | Courage Evidence Decision = Option C | Courage Evidence Decision = Option D |
| Objective | Remove ids 12/30 from one Need's mapping | Remove `勝運` from one Need's Text Evidence | Both of the above together |
| Layer | Mapping | Text Evidence | Mapping + Text Evidence |
| Likely files | `need_to_goriyaku_tag_ids.py` | `concierge_chat_ranking.py` | Both |
| Non-goals | No interpreter/axis/reason change | No interpreter/axis/reason change | No interpreter/axis/reason change |
| Test corpus | Full career+courage evidence recount (Section 24's removal simulation, live-verified) | Text-evidence-only query set | Union of both |
| Regression gates | 0 failures; explicit before/after evidence-count assertion (courage −60% if removed from courage) | 0 failures; small Text-evidence-specific corpus | 0 failures; both assertions |
| Dependency | Courage Evidence Decision | Courage Evidence Decision | Courage Evidence Decision (explicit Option D only) |
| Suggested branch | `fix/courage-career-gid-mapping-review` | `fix/courage-career-text-evidence-review` | `fix/courage-career-evidence-separation` |
| Suggested commit | `fix: adjust courage/career shared GID mapping` | `fix: adjust courage/career shared text evidence` | `fix: separate courage and career shared evidence` |
| Completion definition | ids 12/30 assigned per decision, evidence-count table matches prediction | `勝運` assigned per decision | Both completion definitions met |

## 29. Technical Dependency Order

```
[Already completed, no further decision needed]
  R1a (merged, #2599) -- focus, travel_safe Reason
  R1b (merged, #2600) -- relationship, health Reason
  C1  (merged, #2601) -- communication interpreter vocabulary

[Gated on Family Scope Decision]
  M1 --> R2
  E1 (only if BROAD/SPLIT(a))
  S1 (only if SPLIT(a))

[Gated on Communication Taxonomy Decision]
  C2 --> C2m --> C2t
              --> C3
              --> R3
  (Option A/C: no further chain)

[Gated on Mental/Rest Boundary Decision]
  D1a (Option C) / D1b (Option B) / D1c (Option D) -- mutually exclusive,
  only one is implemented depending on which option is chosen

[Gated on Courage Evidence Decision, independent of all above]
  G1a / G1b / G1c -- mutually exclusive except G1c which combines a and b
```

No business/product priority is assigned to any track or decision — order
above is technical dependency only.

## 30. Production Safety

No production code, DB, model, migration, seed, or frontend file was
modified by this deliverable. The staged scope is limited to this single
audit document. All findings derive from
fresh code reads and read-only runtime execution (`extract_need_tags`,
`resolve_need_payload`, `resolve_consultation_axis`,
`build_chat_recommendations`, Django ORM `.count()`/`SELECT` queries only)
against the pre-existing isolated local scratch DB — no writes.

## 31. Out of Scope

Selection of a final option for any of the four decision packets.
Implementation of any track listed in Section 28. REGEX modification of
any kind. New taxonomy or canonical `GoriyakuTag` rows. Any DB/model/
migration/seed/frontend change. Further implementation beyond the already
merged PR #2600 and PR #2601 — their merged state is read-only input to
this document (Sections 7–8).

## 32. STOP

Draft PR only. Four Mother Ship decisions (family scope, mental/rest
boundary, communication taxonomy, courage/career evidence) remain open.
R1a, R1b, and C1 are merged; those completed tracks are unaffected by this
document.
