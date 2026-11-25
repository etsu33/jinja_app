# Recommendation Semantic Follow-up Closeout

## 1. Scope

Final closeout audit for the Recommendation Semantic Follow-up series after
all four production tracks merged:

| Track | PR | Summary |
|---|---|---|
| D1a | [#2605](https://github.com/etsu33/jinja_app/pull/2605) | `mental` interpreter gains additive coverage for the desiderative calming form `落ち着け(たい\|たく)` |
| C-EL | [#2606](https://github.com/etsu33/jinja_app/pull/2606) | `communication` GID evidence disabled (`NEED_TO_GORIYAKU_IDS["communication"] = set()`) |
| M1 | [#2607](https://github.com/etsu33/jinja_app/pull/2607) | `family` GID mapping narrowed to `{16, 35}`; `mental` drops id 16 |
| R2 | [#2608](https://github.com/etsu33/jinja_app/pull/2608) | `intent_map["family"] = "子宝や安産"` |

This is an **audit / documentation** task. No production behavior was
modified. This branch is **docs-only** (see §19).

### Evidence-labelling convention used in this document

- **[repo]** — read directly from production source at the base SHA below.
- **[runtime]** — observed this session by executing `extract_need_tags`,
  `_attach_breakdown`, `_build_need_lead`, `_build_need_reason_text`, and
  `build_chat_recommendations` against the isolated local scratch DB
  (read-only; no DB rows mutated). Script:
  `scratchpad/closeout_audit.py` (not committed).
- **[prior]** — value recorded by an earlier audit and **not** re-derived
  here; cited as historical context only, never presented as freshly
  re-counted.

## 2. Base SHA / Environment

- **Base SHA:** `226c9a820210c25d30b23b072ae3ea822bf4195c` (`origin/develop`,
  merge commit of R2 [#2608](https://github.com/etsu33/jinja_app/pull/2608)).
- **Worktree:** `~/Developer/jinja_app-recommendation-semantic-closeout`,
  branch `audit/recommendation-semantic-followup-closeout`, confirmed clean
  at checkout.
- **Control repo:** not modified.
- **Test DB:** pre-existing local Postgres/PostGIS scratch DB, `--reuse-db`,
  read-only for this audit.
- **Audit date:** 2026-08-29.

## 3. Integrated Changes Reviewed

Exact production surface touched by the four tracks, all re-read at the base
SHA:

| File / symbol | Track(s) | Current state [repo] |
|---|---|---|
| `backend/temples/domain/need_tags.py` — `REGEX["mental"]` | D1a | contains `re.compile(r"落ち着け(たい\|たく)")`; `REGEX["rest"]` unchanged (single `re.compile(r"(穏やか\|静か\|落ち着\|リセット\|休息\|癒し\|ひと息\|一息)")`) |
| `backend/temples/domain/need_to_goriyaku_tag_ids.py` — `NEED_TO_GORIYAKU_IDS` | C-EL, M1 | `communication: set()`, `family: {16, 35}`, `mental: {11, 26, 28, 38}` |
| `backend/temples/services/concierge_chat_ranking.py` — `_build_need_reason_text.intent_map` | R2 | `"family": "子宝や安産"` (14 of 15 Needs now present; only `communication` absent) |

No interpreter vocabulary was expanded for `communication`, `family`,
`courage`, or `career`. No consultation-axis, `NEED_TEXT_WEIGHTS`, C1
scoring, Lead-hierarchy, or ranking logic was changed by any track.

## 4. Canonical 15 Need List

Discovered from repository truth — `backend/temples/domain/need_tags.py`
`NEED_TAGS` [repo]:

```
love, relationship, marriage, communication, career, money, study,
health, mental, protection, courage, focus, rest, family, travel_safe
```

Count = **15**. `NEED_PRIORITY` (tie-break order, strongest first) [repo]:

```
protection, marriage, love, family, study, career, money, health,
mental, relationship, communication, courage, focus, rest, travel_safe
```

`NEED_TAG_ALIASES` [repo] (`concierge_chat_need.py`): English-key → canonical
only (`romance→love`, `anxiety→mental`, `healing→rest`,
`career_change→career`, `work→career`, `fortune→money`,
`challenge/ambition/success→courage`). No canonical Need is aliased away;
`marriage` and `relationship` were explicitly removed from this table in
prior work and normalize to themselves.

Compass reuses this exact 15-tag set as its `purpose` vocabulary — see §14.

## 5. Interpreter Matrix

Method: one representative positive query per Need through
`extract_need_tags(q, max_tags=3)` [runtime], plus collision/negative
controls. "Vocabulary" column summarised from `KEYWORDS` / `REGEX` [repo].
No vocabulary was expanded during this audit.

| Need | Representative query | Extracted [runtime] | Status |
|---|---|---|---|
| love | `いい出会いがほしい` | `['love']` | DIRECTLY_RECOGNIZED |
| relationship | `職場の人間関係を改善したい` | `['relationship']` | DIRECTLY_RECOGNIZED |
| marriage | `結婚したい` | `['marriage']` | DIRECTLY_RECOGNIZED |
| communication | `コミュニケーション能力を上げたい` | `['communication']` | DIRECTLY_RECOGNIZED (recognition only; evidence intentionally disabled — §10) |
| career | `転職を考えている` | `['career']` | DIRECTLY_RECOGNIZED |
| money | `金運を上げたい` | `['money']` | DIRECTLY_RECOGNIZED |
| study | `試験に合格したい` | `['study']` | DIRECTLY_RECOGNIZED |
| health | `健康でいたい` | `['health']` | DIRECTLY_RECOGNIZED |
| mental | `不安を和らげたい` | `['mental']` | DIRECTLY_RECOGNIZED |
| protection | `厄除けをしたい` | `['protection']` | DIRECTLY_RECOGNIZED |
| courage | `新しいことに挑戦したい` | `['courage']` | DIRECTLY_RECOGNIZED |
| focus | `集中力を高めたい` | `['focus']` | DIRECTLY_RECOGNIZED |
| rest | `少し休みたい` | `['rest']` | DIRECTLY_RECOGNIZED |
| family | `子宝に恵まれたい` | `['family']` | DIRECTLY_RECOGNIZED (narrow) |
| travel_safe | `交通安全を祈願したい` | `['travel_safe']` | DIRECTLY_RECOGNIZED |

All 15 Needs are DIRECTLY_RECOGNIZED for at least one representative
in-vocabulary query. No Need is BROKEN, FALLBACK_DEPENDENT, or
PARTIALLY_RECOGNIZED at the interpreter layer for its representative query.
`communication` is DIRECTLY_RECOGNIZED at the interpreter layer and
INTENTIONALLY_LIMITED at the evidence layer (a distinct property — §10).

### Collision / negative controls [runtime]

| Query | Result | Note |
|---|---|---|
| `気持ちを落ち着けたい` | `['mental', 'rest']` | D1a target — both, as intended |
| `落ち着ける場所に行きたい` | `['rest']` | potential/adnominal form — `mental` **not** gained |
| `気持ちを落ち着けて静かに過ごしたい` | `['rest']` | connective form — `mental` **not** gained |
| `心を整えたい` | `['mental', 'rest']` | pre-existing shared-vocabulary co-extraction, unchanged |
| `疲れを癒したい` | `['mental', 'rest']` | pre-existing, unchanged |
| `静かに過ごしたい` | `['rest']` | rest-only, unchanged |
| `家族円満を願いたい` | `['relationship']` | `family` interpreter stays narrow — `家族` belongs to `relationship` |
| `家族の健康を願いたい` | `['health', 'relationship']` | `family` absent — narrow boundary holds |
| `家庭を整えたい` | `['mental', 'rest']` | `family` absent |
| `親子関係を良くしたい` | `['relationship']` | `family` absent |
| `安産祈願をしたい` | `['family']` | correct narrow match |
| `職場でのコミュニケーションを改善したい` | `['relationship', 'communication']` | #2601 recall intact; `relationship` primary by priority (index 9 < 10) |
| `人と話すのが怖い` | `['communication']` | #2601 recall intact |

### Special verifications (task §A)

- **mental/rest:** `気持ちを落ち着けたい` → `['mental','rest']` ✔;
  `落ち着ける場所に行きたい` → `['rest']` (no incorrect `mental`) ✔; D1a is
  additive — `REGEX["rest"]` byte-identical to pre-D1a [repo] ✔.
- **communication:** #2601 interpreter vocabulary
  (`コミュニケーション`/`話せる`/`話せない`/`伝えられない`/`伝わらない`
  + the original 8) is present in `KEYWORDS["communication"]` [repo] and
  active [runtime] even though scoring evidence is disabled.
- **family:** `KEYWORDS["family"] = ["子宝","安産","妊活","授かり","出産","育児"]`
  [repo] — unchanged, fertility/childbirth/parenting only; `家族`/`家庭`/
  `親子` route to `relationship`, never `family` [runtime].
- **courage/career:** shared interpreter surface (`挑戦`/`道を開く`/`勝運`
  text) and shared GIDs `{12, 30}` [repo] behave as before; no
  false-positive regression in the boundary corpus (§16).

## 6. Need → GID Mapping Matrix

Read from `backend/temples/domain/need_to_goriyaku_tag_ids.py`
`NEED_TO_GORIYAKU_IDS` [repo], verified via `need_tags_to_goriyaku_ids`
[runtime]:

| Need | GID set [repo] | Classification |
|---|---|---|
| love | `{1, 20}` | VALID |
| relationship | `{1}` | VALID (shares id 1 with love/marriage — intentional, `縁結び`) → VALID_WITH_SHARED_EVIDENCE |
| marriage | `{1, 18}` | VALID_WITH_SHARED_EVIDENCE (id 1) |
| communication | `set()` | INTENTIONALLY_EMPTY |
| career | `{6, 12, 21, 27, 30}` | VALID_WITH_SHARED_EVIDENCE (ids 12, 30 shared with courage) |
| money | `{4, 5, 28, 36}` | VALID |
| study | `{9, 10}` | VALID (shares with focus — same domain) → VALID_WITH_SHARED_EVIDENCE |
| health | `{7, 8, 24, 33, 38}` | VALID_WITH_SHARED_EVIDENCE (ids 7/8 shared with rest; 38 with courage/mental) |
| mental | `{11, 26, 28, 38}` | VALID_WITH_SHARED_EVIDENCE (id 11 with protection/courage; 38 with courage/health) |
| protection | `{2, 11, 32}` | VALID_WITH_SHARED_EVIDENCE (id 11) |
| courage | `{12, 15, 18, 20, 24, 30, 38}` | VALID_WITH_SHARED_EVIDENCE (ids 12, 30 with career; 18/20 with marriage/love; 38 with mental/health) |
| focus | `{9, 10}` | VALID_WITH_SHARED_EVIDENCE (identical to study — same domain) |
| rest | `{7, 8}` | VALID_WITH_SHARED_EVIDENCE (ids 7/8 with health) |
| family | `{16, 35}` | VALID |
| travel_safe | `{3, 13, 14}` | VALID |

No Need mapping is PARTIAL or BROKEN. No mapping was changed by this audit.

### Explicit verifications (task §B) [runtime]

- `communication == set()` ✔
- `family == {16, 35}` ✔
- `mental == {11, 26, 28, 38}` ✔
- `2 in protection` ✔ (`protection == {2, 11, 32}`)
- courage ∩ career `= {12, 30}` ✔ (KEEP_SHARED preserved)
- `travel_safe == {3, 13, 14}` ✔ (`交通安全/航海安全/海上安全`; the prior
  invalid `{10, 22, 23}` is not present)
- stale ids 42–45: **not present** in any Need mapping ✔

### Orphaned canonical tags (context, not a blocker)

All referenced GIDs across the 15 Needs [runtime]: `{1..16, 18, 20, 21, 24,
26, 27, 28, 30, 32, 33, 35, 36, 38}`. Canonical master range is 1–39
([prior], `test_need_to_goriyaku_tag_ids.py` `CANONICAL_MASTER_ID_RANGE`).
Unreferenced canonical ids: `{17, 19, 22, 23, 25, 29, 31, 34, 37, 39}`.

Of these, this series newly un-referenced **34** (was family-only, dropped
by M1) and **37, 39** (were communication-only, dropped by C-EL); it also
**resolved** the previously-orphaned id **35** (`子宝`) by mapping it to
`family`. Orphaned tags are unused evidence labels only — no code path
errors on them, and the decision packets explicitly accepted leaving them
in the master (see §15, DATA_GAP / INTENTIONAL_LIMITATION).

## 7. C1 Evidence Matrix

C1 Max contract, read from `_attach_breakdown` [repo]
(`concierge_chat_ranking.py` ~L1178–1201):

```
GID_ONLY  -> gid_score  (flat 2.0 weighted)
TEXT_ONLY -> text_score  (Σ integer weight × 1.2)
BOTH      -> winner = "text" if text_weighted > gid_weighted else "gid"   (strict >, so tie -> GID)
NONE      -> not entered into need_evidence_winner_by_tag; contributes 0
score_need = len(distinct needs with tag OR text OR gid evidence)
```

`need_evidence_winner_by_tag` is populated **only** by iterating
`set(matched_by_gid) | set(matched_by_text)` — i.e. winner metadata exists
only where GID or Text evidence actually matched. NONE → no winner key.

Per-Need possible evidence paths (`NEED_TEXT_WEIGHTS` keys [repo] =
`{study, career, courage, mental, love, money, rest}`; GID = non-empty
mapping):

| Need | GID path | Text path | Possible C1 branches | GID_ONLY [runtime] |
|---|---|---|---|---|
| love | yes | yes | GID_ONLY / TEXT_ONLY / BOTH | `matched=['love'] winner={'love':'gid'} score_need=1` |
| relationship | yes | no | GID_ONLY / NONE | `winner={'relationship':'gid'} score_need=1` |
| marriage | yes | no | GID_ONLY / NONE | `winner={'marriage':'gid'} score_need=1` |
| communication | **no** | **no** | **NONE only** | `matched=[] winner={} score_need=0` (candidate carried former GID 30) |
| career | yes | yes | GID_ONLY / TEXT_ONLY / BOTH | `winner={'career':'gid'} score_need=1` |
| money | yes | yes | GID_ONLY / TEXT_ONLY / BOTH | `winner={'money':'gid'} score_need=1` |
| study | yes | yes | GID_ONLY / TEXT_ONLY / BOTH (+study_bonus) | `winner={'study':'gid'} score_need=1` |
| health | yes | no | GID_ONLY / NONE | `winner={'health':'gid'} score_need=1` |
| mental | yes | yes | GID_ONLY / TEXT_ONLY / BOTH | `winner={'mental':'gid'} score_need=1` |
| protection | yes | no | GID_ONLY / NONE | `winner={'protection':'gid'} score_need=1` |
| courage | yes | yes | GID_ONLY / TEXT_ONLY / BOTH | `winner={'courage':'gid'} score_need=1` |
| focus | yes | no | GID_ONLY / NONE | `winner={'focus':'gid'} score_need=1` |
| rest | yes | yes | GID_ONLY / TEXT_ONLY / BOTH | `winner={'rest':'gid'} score_need=1` |
| family | yes | no | GID_ONLY / NONE | `winner={'family':'gid'} score_need=1` (gid 16) |
| travel_safe | yes | no | GID_ONLY / NONE | `winner={'travel_safe':'gid'} score_need=1` |

### Explicit confirmations (task §C) [runtime]

| Check | Result |
|---|---|
| communication recognised query + candidate with former GIDs `[30,33,37,39]` | `matched=[] winner={} score_need=0` — no substitute/fallback evidence |
| communication with no valid Text Evidence | C1 branch = NONE, `score_need == 0` |
| family + GID 16 | `matched=['family'] winner={'family':'gid'} score_need=1` |
| family + GID 35 | `matched=['family'] winner={'family':'gid'} score_need=1` |
| family + former GID 2 | `matched=[] winner={} score_need=0` |
| family + former GID 26 | `matched=[] winner={} score_need=0` |
| family + former GID 34 | `matched=[] winner={} score_need=0` |
| mental + GID 16 | `matched=[] winner={} score_need=0` — id 16 no longer mental evidence |
| mental + GID 11 | `matched=['mental'] winner={'mental':'gid'} score_need=1` |
| protection + GID 2 | `matched=['protection'] winner={'protection':'gid'} score_need=1` |
| career + GID 30 / GID 12 | `winner={'career':'gid'}` each |
| courage + GID 30 / GID 12 | `winner={'courage':'gid'}` each |
| career + `勝運` text (GID-less) | `winner={'career':'text'}` `rank_w=2.4` |
| courage + `勝運` text (GID-less) | `winner={'courage':'text'}` `rank_w=3.6` (weight 3 × 1.2) |

No invalid GID produced a winner. C1 logic not modified.

## 8. Lead Coverage

Active Lead path: `_build_need_lead` [repo] (`concierge_chat_ranking.py`
~L1951). Hierarchy (unchanged):

```
1. matched_gid_label   (winner-aware: resolved from candidate GID ∩ Need mapping)
2. matched_text_hint
3. Purpose fallback dict  {study, mental, rest, love, career, money, courage, protection}
4. generic "ご利益"
```

Observed with a shrine name set and **no** matched GID/text (so the Lead
falls to level 3 or 4) [runtime]:

| Need | Lead (no matched evidence) | Need-specific? | Generic intentional? | Invalid GID label surfaced? |
|---|---|---|---|---|
| love | `良縁成就` | yes (Purpose fallback) | — | no |
| career | `仕事運` | yes | — | no |
| money | `金運` | yes | — | no |
| study | `学業成就` | yes | — | no |
| protection | `厄除け` | yes | — | no |
| marriage | `ご利益` | no | yes — no Purpose-fallback entry by design; a real match yields `縁結び`/`夫婦円満` | no |
| relationship | `ご利益` | no | yes — same | no |
| health | `ご利益` | no | yes — same | no |
| focus | `ご利益` | no | yes — same | no |
| travel_safe | `ご利益` | no | yes — same | no |
| family | `ご利益` | no | yes — no Purpose-fallback entry; a real match yields `安産`/`子宝` (winner-aware) | no |
| communication | `ご利益` | no | **yes — intended**; no GID mapping so level-1 can never fire, no Purpose fallback, so generic is the only path (§10) | **no** — the disabled `{30,33,37,39}` labels are never reachable because the mapping is empty |

Winner-aware Lead behaviour is intact: when a candidate carries a valid
Need GID, level 1 returns that GoriyakuTag's label (e.g. family + id 16 →
Lead `安産`, verified in `test_reason_family.py`). `communication` cannot
fabricate a Need-specific evidence Lead from disabled GIDs — the mapping is
`set()`, so `matched_gid_label` is always `None` for it. No new Lead copy
added.

## 9. Reason Coverage

Active Reason path: `build_recommendation_reason` → `_build_need_reason_text`
[repo]. `intent_map` (the `if name:` path, common case) has entries for
**14 of 15** Needs; the secondary `mapping` (name-empty path) has 8.

| Need | `intent_map` phrase [repo] | Classification |
|---|---|---|
| love | `恋愛や良縁` | SPECIFIC_REASON |
| relationship | `人間関係の改善や修復` | SPECIFIC_REASON (R1b) |
| marriage | `良縁や夫婦円満` | SPECIFIC_REASON (independent, not collapsed into love) |
| communication | *(absent)* → `今の願い` | GENERIC_BY_DESIGN (§10) |
| career | `仕事や転機` | SPECIFIC_REASON |
| money | `金運向上` | SPECIFIC_REASON |
| study | `学業や合格` | SPECIFIC_REASON |
| health | `健康や体調の安定` | SPECIFIC_REASON (R1b) |
| mental | `不安や心の安定` | SPECIFIC_REASON |
| protection | `厄除けや守り` | SPECIFIC_REASON |
| courage | `前進や後押し` | SPECIFIC_REASON |
| focus | `集中や習慣づくり` | SPECIFIC_REASON (R1a) |
| rest | `休息や気持ちの切り替え` | SPECIFIC_REASON |
| travel_safe | `移動や旅の安全` | SPECIFIC_REASON (R1a) |
| family | `子宝や安産` | SPECIFIC_REASON (R2) |

14/15 SPECIFIC_REASON; 1/15 (`communication`) GENERIC_BY_DESIGN. None
PARTIAL or BROKEN.

### Explicit verifications (task §E) [runtime]

- `family` reason string uses `子宝や安産`:
  `_build_need_reason_text("family", name="テスト神社")` →
  `"…テスト神社は、子宝や安産を願う参拝先として適しています。"` ✔
- family + valid GID 16/35 → reason contains `子宝や安産を願う参拝先として`
  and **not** `今の願いを願う参拝先として`
  (`test_reason_family.py`, all pass) ✔
- former Family GIDs 2/26/34 → `matched_need_tags == []` →
  `_primary_reason_label == "fallback"` → generic
  `今の願いを願う参拝先として` — the family-specific phrase is **not**
  emitted ✔ (`test_reason_family.py::test_former_family_gids_do_not_yield_family_reason`)
- relationship / health / focus / travel_safe intent_map phrases unchanged
  from R1a/R1b ✔
- marriage independent reason (`良縁や夫婦円満`) active, distinct from love
  (`恋愛や良縁`) ✔
- communication → generic where evidence is absent ✔ (intended)
- No reason text is derived from invalid evidence: `communication` cannot
  reach the `if primary_label` branch with a Need label because it never
  scores; `family` cannot cite ids 2/26/34 because they no longer match ✔

## 10. Communication Closeout

Required dedicated verification of the adopted `EVIDENCE_LIMITED` /
`DISABLE_GID_EVIDENCE` contract (Mother Ship 2026-08-29;
[#2604](https://github.com/etsu33/jinja_app/pull/2604) doc,
[#2606](https://github.com/etsu33/jinja_app/pull/2606) impl).

| Contract clause | Result | Source |
|---|---|---|
| interpreter recognition remains active | `extract_need_tags("コミュニケーション能力を上げたい") → ['communication']`; #2601 vocabulary present | [runtime] / [repo] |
| `NEED_TO_GORIYAKU_IDS["communication"] == set()` | ✔ | [repo] / [runtime] |
| no communication Text Evidence introduced | `"communication" not in NEED_TEXT_WEIGHTS` | [repo] / [runtime] |
| C1 evidence branch == NONE | candidate with former GIDs `[30,33,37,39]` → `matched=[] winner={}` | [runtime] |
| `score_need == 0` | ✔ for communication-only query + candidate | [runtime] |
| no substitute / default / fallback score | `score_need = len(matched_all) = 0`; no special-casing in `_attach_breakdown` for communication | [repo] / [runtime] |
| no invalid GID winner metadata | `need_evidence_winner_by_tag == {}` for communication | [runtime] |
| ranking / Top3 relies only on remaining factors | with `score_need = 0`, ranking falls through to element / popular / distance / direction (Compass) — no Need-axis contribution | [repo] |
| generic Lead / Reason is expected, not a defect | Lead `ご利益`, Reason `今の願い` — the only reachable paths given empty mapping + no `intent_map` entry | [runtime] |

**Final communication status:**

- **Semantic recognition:** `DIRECTLY_RECOGNIZED` — the interpreter
  correctly identifies communication intent.
- **Recommendation evidence eligibility:** `INTENTIONALLY_LIMITED
  (EVIDENCE_LIMITED / DISABLE_GID_EVIDENCE)` — `score_need == 0` for
  communication-only inputs is the adopted, contract-correct behaviour, not
  a defect. Not classified as BROKEN.

## 11. Mental / Rest Closeout

| Check | Result | Source |
|---|---|---|
| D1a target `気持ちを落ち着けたい` → both | `['mental', 'rest']` | [runtime] |
| existing mental-only queries stay mental | `不安を和らげたい → ['mental']` | [runtime] |
| existing rest-only queries stay rest | `少し休みたい → ['rest']`, `静かに過ごしたい → ['rest']` | [runtime] |
| no broad `落ち着` regex regression | `落ち着ける場所に行きたい → ['rest']` (not mental); `落ち着けて… → ['rest']`; D1a pattern is `落ち着け(たい\|たく)` only, `REGEX["rest"]` unchanged | [runtime] / [repo] |
| no scoring / Reason logic altered by D1a | D1a diff was `need_tags.py` REGEX + a new test file only; `intent_map`, C1, Lead untouched | [repo], PR #2605 |

The `心を整えたい` / `疲れを癒したい` → `['mental','rest']` co-extraction is
**pre-existing** (shared `整えたい`/`疲れ`/`癒し` vocabulary) and was not
introduced or widened by D1a.

**Classification: `ACCEPTABLE_SHARED_INTENT`.** The overlap reflects
genuinely dual-relevant calming/rest language; D1a made it strictly
additive for one previously-misrouted query and narrowed nothing.

## 12. Family Narrow Boundary Closeout

Integrated M1 + R2 contract, layer by layer:

| Layer | Expected | Observed | Source |
|---|---|---|---|
| Interpreter | narrow (fertility/childbirth/parenting) | `KEYWORDS["family"]` unchanged; `家族`/`家庭`/`親子` route to `relationship` | [repo] / [runtime] |
| Mapping | `family == {16, 35}` | ✔ | [repo] / [runtime] |
| Evidence | GID 16 / 35 valid; GID 2 / 26 / 34 invalid for family | GID 16→`winner={'family':'gid'}`; GID 35→same; GID 2/26/34→`matched=[]` | [runtime] |
| Reason | `子宝や安産`; not generic for valid family evidence | `intent_map["family"] == "子宝や安産"`; valid GID → specific, former GID → generic | [repo] / [runtime] |
| Non-regression: protection retains id 2 | `protection == {2, 11, 32}` | ✔ | [runtime] |
| Non-regression: mental excludes id 16 | `mental == {11, 26, 28, 38}`; mental + GID 16 → no match | ✔ | [runtime] |

**Classification: `CONSISTENT`.** Interpreter → Mapping → Evidence → Reason
all express the same narrow fertility/childbirth meaning with no
contradiction. (See §15 for the reduced-evidence-pool DATA_GAP, which is a
data-coverage note, not an engine inconsistency.)

## 13. Courage / Career KEEP_SHARED Closeout

Adopted decision: `KEEP_SHARED` (Mother Ship 2026-08-29) — ids `{12, 30}`
and the `勝運` Text-Evidence term stay shared between `courage` and
`career`; no production PR was cut for this track.

| Check | Result | Source |
|---|---|---|
| shared GIDs still present | `courage ∩ career = {12, 30}` | [repo] / [runtime] |
| shared Text term still present | `NEED_TEXT_WEIGHTS["career"]["勝運"]` and `["courage"]["勝運"]` both present (weights 2 and 3) | [repo] |
| no new false-positive regression | boundary/eval corpus green (§16); `新しいことに挑戦したい → ['courage']`, `転職を考えている → ['career']` — no cross-leak | [runtime] / §16 |
| C1 behaviour under existing rules | career/courage + GID 12/30 → each scores its own Need's `winner='gid'`; `勝運` text alone → `winner='text'` per Need | [runtime] |
| evidence requiring immediate separation | none observed; removing `{12, 30}` would drop `courage` from ~20 to ~8 shrine-references (`PARTIAL`→`SPARSE`) — [prior], `semantic-followup-decision-and-pr-split.md` §21, **not re-counted here** | [prior] |

**Classification: `KEEP_SHARED_STABLE`.** No runtime evidence contradicts
the adopted decision. The prior rationale (separation materially reduces
`courage` evidence coverage) is cited unchanged; this audit does not
re-derive or alter it.

## 14. Concierge / Compass Shared Contract

Traced from `backend/temples/services/compass_recommendation_orchestrator.py`
[repo].

**Compass entry point:** `run_compass_recommendation(...)` →
`build_chat_recommendations(query="", need_tags=[purpose_slug],
public_mode="need", flow="A", ...)` (L223 and L286). `purpose_slug` must be
one of `NEED_TAGS` (L195 `if purpose_slug not in NEED_TAGS`). Per
`docs/product/compass-mvp-runtime-contract.md` §§187–203, Compass reuses the
existing 15 `need_tag` slugs directly with **no** translation layer.

| Engine layer | Shared with Concierge? | Detail |
|---|---|---|
| Need → GID mapping (`NEED_TO_GORIYAKU_IDS`) | **Shared** | Compass passes `need_tags=[purpose_slug]`; `_attach_breakdown` calls `need_tags_to_goriyaku_ids` identically. C-EL and M1 therefore apply to Compass. |
| C1 scoring (`_attach_breakdown`, C1 Max) | **Shared** | Same function, same contract. |
| `need_evidence_winner_by_tag` | **Shared** | Same. |
| `NEED_TEXT_WEIGHTS` / Text Evidence | **Shared** | Compass passes `query=""`, so Text Evidence only fires from candidate `goriyaku`/`description` material — same code path. |
| Lead (`_build_need_lead`) | **Shared** | Same. |
| Reason (`build_recommendation_reason` / `_build_need_reason_text`) | **Shared** | R2's `intent_map["family"]` applies to Compass `purpose="family"`. |
| Free-text interpreter (`extract_need_tags`) | **NOT shared** | Compass never calls it — the Need is the pre-selected `purpose_slug`, and `query=""`. **D1a therefore does not affect Compass.** |
| Consultation-axis resolution from free text | **Partly** | Compass passes an `interpretation_profile` from `interpret_consultation`, not from `extract_need_tags`; axis still feeds `resolve_history_theme_candidate_boost` in shared ranking. |
| Pre-ranking candidate space | **NOT shared** | Compass adds `filter_candidates_by_direction` (bearing) + `_apply_compass_distance_stage` (15→30→60 km) before ranking. Concierge does not. |
| Entry surface | **NOT shared** | Compass deliberately does **not** route through `ConciergeChatView` / compat-mode (`compass-mvp-runtime-contract.md` §6). |

**Result:** the four tracks' effect on Compass —
- **D1a:** no effect (interpreter not in Compass path).
- **C-EL:** applies — Compass `purpose="communication"` yields `score_need
  = 0` for every candidate; ranking then relies on direction/distance/
  popular/element only. Contract-consistent.
- **M1:** applies — Compass `purpose="family"` scores only GID 16/35
  candidates.
- **R2:** applies — Compass `purpose="family"` recommendations get the
  `子宝や安産` Reason.

Concierge and Compass share the recommendation-engine **evidence, mapping,
C1, winner-metadata, Lead, and Reason** layers exactly. They differ in
**intent acquisition** (interpreter vs pre-selected purpose) and in
**candidate-space shaping** (Compass direction+distance stages). No
product-level equivalence is assumed. No frontend/UI inspected or changed.

## 15. Known Gaps Reclassification

Re-read against current runtime behaviour after D1a/C-EL/M1/R2. Prior
sources: `semantic-followup-decision-and-pr-split.md`,
`remaining-need-semantic-decision-packets.md`,
`compass-recommendation-engine-finalization.md`,
`remaining-need-goriyaku-semantic-mapping.md`.

| # | Gap (as previously recorded) | Reclassification | Basis |
|---|---|---|---|
| 1 | `family` had no `intent_map` Reason entry (generic fallback) | **CLOSED** | R2 #2608 added `子宝や安産`; [runtime] confirms specific reason for valid family evidence |
| 2 | `family` GID mapping inconsistent with its interpreter vocabulary (mapped household ids 2/26/34, not fertility ids 16/35) | **CLOSED** | M1 #2607: `family == {16, 35}`; [runtime] interpreter↔mapping↔evidence↔reason all narrow (§12) |
| 3 | id 16 (`安産`) mis-assigned to `mental` | **CLOSED** | M1: `mental == {11, 26, 28, 38}`; mental + GID 16 → no match [runtime] |
| 4 | `communication` mapped to semantically-invalid GIDs `{30,33,37,39}` | **CLOSED (as INTENTIONAL_LIMITATION going forward)** | C-EL #2606: mapping now `set()`; adopted `EVIDENCE_LIMITED` policy — see #7 |
| 5 | `気持ちを落ち着けたい` misrouted to `rest` only (mental lost) | **CLOSED** | D1a #2605: now `['mental', 'rest']` [runtime] |
| 6 | `communication` evidence limitation / "permanently GID-sparse?" | **INTENTIONAL_LIMITATION** (was PRODUCT_DECISION) | Mother Ship adopted `EVIDENCE_LIMITED` + `DISABLE_GID_EVIDENCE`. A future communication-specific taxonomy is `FUTURE_ENHANCEMENT` (tracks C2/C2m/C2t/C3/R3 in the decision packet, **not pursued**) |
| 7 | `family` reduced evidence pool | **DATA_GAP** | [prior] `remaining-need-semantic-decision-packets.md` §§9–10: family's effective pool moved from ~54 shrine-refs (id 2 ×51, shared with protection) to ~6 (id 16 ×5 + id 35 ×1). **Not re-counted this session.** This is a data-coverage property (few shrines carry `安産`/`子宝`), not an engine defect; adding fertility shrines/tags is `FUTURE_ENHANCEMENT`. Explicitly accepted by the DROP_ALL decision ("do not retain household GIDs merely to preserve evidence volume") |
| 8 | mental / rest shared-vocabulary overlap | **INTENTIONAL_LIMITATION** (`ACCEPTABLE_SHARED_INTENT`, §11) | Pre-existing co-extraction on `整えたい`/`疲れ`/`癒し`; D1a did not widen it; Mother Ship chose `EXPAND_MENTAL` (additive) over the narrowing options |
| 9 | courage / career shared evidence (`{12,30}`, `勝運`) | **PRODUCT_DECISION (KEEP_SHARED), stable** | §13; `KEEP_SHARED_STABLE`; separation cost cited [prior], not re-derived |
| 10 | `study` sparse geographic evidence | **DATA_GAP** | [prior] `compass-recommendation-engine-finalization.md` §22 (Evidence Coverage = PARTIAL, "SHOULD_FIX", Engine PR-B optional). Untouched by this series; **not re-measured**. Engine scoring/ranking healthy; the gap is DB shrine geographic distribution |
| 11 | `protection` Text Coverage not in production `NEED_TEXT_WEIGHTS` | **FUTURE_ENHANCEMENT** | [prior] same doc §21 "LATER", `LOW_VALUE`. Unchanged |
| 12 | `love` structural `TEXT_ONLY = 0` design question | **FUTURE_ENHANCEMENT** | [prior] same doc §21 "LATER" (design point). Unchanged; note `NEED_TEXT_WEIGHTS["love"]` **does** exist [repo], so love can take TEXT_ONLY/BOTH — this item is a curation/design question, not an engine gap |
| 13 | one `career` / 赤坂氷川神社 winner↔Reason-source conflict | **PRODUCT_DECISION / FUTURE_ENHANCEMENT** | [prior] same doc §23 Engine PR-C ("SHOULD_FIX, optional, high complexity"). Not in this series' scope; no evidence it regressed |
| 14 | remaining generic Lead/Reason behaviour (marriage/relationship/health/focus/travel_safe/family Lead = `ご利益` without a matched GID; communication Lead+Reason generic) | **INTENTIONAL_LIMITATION** | §8/§9. For all except `communication`, a real matched GID yields a specific, winner-aware Lead; the generic value only appears absent evidence. `communication` generic is by design (#7). No new Lead copy is planned in this series |
| 15 | stale / unmapped canonical tags | **DATA_GAP / INTENTIONAL_LIMITATION** | §6. ids `{17,19,22,23,25,29,31,34,37,39}` unreferenced; `34/37/39` newly so via this series; decision packets explicitly leave them in the master. No code path errors. id 35 previously orphaned is now **resolved** |
| 16 | duplicate shrine rows (長太稲荷神社 id 21/103) | **DATA_GAP** | [prior] `compass-recommendation-engine-finalization.md` §21 / `shrine-dataset-integrity.md`. Out of engine scope; unchanged |
| 17 | QUESTIONABLE mappings from `compass-purpose-goriyaku-mapping-correction.md` not re-verified | **PRODUCT_DECISION (deferred)** | [prior]; not in this series' scope; no re-verification performed here either |

No item reclassifies as **REGRESSION** or **BLOCKER**.

### §15 count reconciliation

- **Unique gap items: 17** (rows 1–17 above).
- **Category assignments: 20.** The categories are **not** mutually
  exclusive — 3 items are intentionally multi-classified (2 categories
  each), so 17 unique items + 3 extra assignments = 20.
- **Multi-classified items:**
  - **#4** (`communication` mapped to invalid GIDs) = `CLOSED` +
    `INTENTIONAL_LIMITATION` — the invalid-mapping defect is *closed*
    (mapping is now `set()`), while the resulting no-GID-evidence state
    *continues* as the adopted `EVIDENCE_LIMITED` policy.
  - **#13** (`career` / 赤坂氷川神社 winner↔Reason-source conflict) =
    `PRODUCT_DECISION` + `FUTURE_ENHANCEMENT` — [prior] flagged it as
    "SHOULD_FIX, optional" (a product call) *and* as an optional future
    Engine PR-C.
  - **#15** (stale / unmapped canonical tags) = `DATA_GAP` +
    `INTENTIONAL_LIMITATION` — it is a data-coverage artefact *and* the
    decision packets explicitly chose to leave the ids in the master.
- **Per-category totals** (counting every assignment):

  | Category | Count | Items |
  |---|---|---|
  | CLOSED | 5 | 1, 2, 3, 4, 5 |
  | INTENTIONAL_LIMITATION | 5 | 4, 6, 8, 14, 15 |
  | DATA_GAP | 4 | 7, 10, 15, 16 |
  | PRODUCT_DECISION | 3 | 9, 13, 17 |
  | FUTURE_ENHANCEMENT | 3 | 11, 12, 13 |
  | **Total assignments** | **20** | (17 unique items) |

  (The `(was PRODUCT_DECISION)` note on item 6 and the `FUTURE_ENHANCEMENT`
  mentions inside the Basis prose of items 6 and 7 describe the *prior*
  classification and *derived follow-up actions* respectively; they are not
  additional current classifications and are not counted above.)

## 16. Regression Results

Runner: `pytest -q --reuse-db` via the repo's `PYTEST` invocation, Python
3.14 venv, local Postgres/PostGIS scratch DB.

### Focused sets (task §L)

`test_mental_rest_interpreter_coverage`, `test_communication_interpreter_coverage`,
`test_communication_gid_evidence_disabled`, `test_marriage_interpreter_coverage`,
`test_family_gid_mapping_narrow`, `test_reason_family`,
`test_need_to_goriyaku_tag_ids`, `test_text_evidence_scoring_contract`,
`test_need_lead_purpose_alignment`, `test_reason_relationship_health`,
`test_reason_focus_travel_safe`, `test_marriage_reason_copy`,
`test_protection_explanation_coverage`, `test_need_labels_ja_completeness`,
`services/test_concierge_need_taxonomy`, `services/test_concierge_boundary_eval_queries`,
`services/test_consultation_interpreter`:

**276 passed, 0 failed, 0 skipped, 1 warning.**

### Full backend suite

**1889 passed, 13 skipped, 73 warnings, 0 failed** (~26 s).

Skips (all pre-existing environment skips, unrelated to this series):
- `test_concierge_l1_freetext_readiness.py:268` ×4 — "no axis family pinned
  for theme='ambiguous'"
- `test_gis_smoke.py:11` ×1 — GDAL not available locally
- `conftest.py:52` ×8 — PostGIS not available in this environment

The 1889/13/73 figure matches R2 #2608's own merge-time result exactly
(this worktree is at that merge SHA with no code changes). [prior] baseline
in `compass-recommendation-engine-finalization.md` §22 was 1698 passed / 15
skipped (PR #2563) — the pass count grew with the four tracks' own added
tests (D1a +19, C-EL +14, M1 +17, R2 +15) plus unrelated intervening work;
skip drift (15→13) is environmental, not a regression.

### `git diff --check`

**CLEAN.** Working tree contains only this new document (see §1/§19).

### Representative 15-Need matrix [runtime]

Query → extracted Need → GID-only C1 (candidate carrying one mapped GID,
empty goriyaku text) → Lead class (no-evidence fallback) → Reason class:

| Need | Query | Extracted | GID ev. | Text ev. possible | C1 winner (GID_ONLY) | score_need | Lead class | Reason class |
|---|---|---|---|---|---|---|---|---|
| love | いい出会いがほしい | love | id 1 → yes | yes | gid | 1 | Purpose-specific (`良縁成就`) | SPECIFIC |
| relationship | 職場の人間関係を改善したい | relationship | id 1 → yes | no | gid | 1 | generic (`ご利益`) / specific on match | SPECIFIC |
| marriage | 結婚したい | marriage | id 18 → yes | no | gid | 1 | generic / specific on match | SPECIFIC |
| communication | コミュニケーション能力を上げたい | communication | **none** | **no** | — (NONE) | **0** | generic (by design) | GENERIC_BY_DESIGN |
| career | 転職を考えている | career | id 12 → yes | yes | gid | 1 | Purpose-specific (`仕事運`) | SPECIFIC |
| money | 金運を上げたい | money | id 5 → yes | yes | gid | 1 | Purpose-specific (`金運`) | SPECIFIC |
| study | 試験に合格したい | study | id 9 → yes | yes | gid | 1 | Purpose-specific (`学業成就`) | SPECIFIC |
| health | 健康でいたい | health | id 7 → yes | no | gid | 1 | generic / specific on match | SPECIFIC |
| mental | 不安を和らげたい | mental | id 11 → yes | yes | gid | 1 | Purpose-specific (`心願成就`) | SPECIFIC |
| protection | 厄除けをしたい | protection | id 2 → yes | no | gid | 1 | Purpose-specific (`厄除け`) | SPECIFIC |
| courage | 新しいことに挑戦したい | courage | id 15 → yes | yes | gid | 1 | Purpose-specific (`開運`) | SPECIFIC |
| focus | 集中力を高めたい | focus | id 9 → yes | no | gid | 1 | generic / specific on match | SPECIFIC |
| rest | 少し休みたい | rest | id 7 → yes | yes | gid | 1 | Purpose-specific (`心身浄化`) | SPECIFIC |
| family | 子宝に恵まれたい | family | id 16 → yes | no | gid | 1 | generic / `安産`\|`子宝` on match | SPECIFIC (`子宝や安産`) |
| travel_safe | 交通安全を祈願したい | travel_safe | id 3 → yes | no | gid | 1 | generic / specific on match | SPECIFIC |

14/15 Needs: DIRECTLY_RECOGNIZED interpreter + valid GID evidence + specific
Reason. 1/15 (`communication`): DIRECTLY_RECOGNIZED interpreter, NONE
evidence, `score_need = 0`, generic Lead/Reason — all by adopted design.

## 17. ENGINE_READY Final Verdict

Terminology reused from `docs/audit/compass-recommendation-engine-finalization.md`
(§22): the readiness states in use are `ENGINE_READY_WITH_KNOWN_GAPS` /
(implicit `ENGINE_READY`) / `NOT_READY`.

### Reconciliation performed before the verdict

- Interpreter matrix (§5) vs mapping matrix (§6) vs C1 matrix (§7):
  consistent for all 15 Needs. The only Need where interpreter status and
  evidence status differ is `communication`, and that difference is the
  adopted `EVIDENCE_LIMITED` contract, not a mismatch.
- Family layer chain (§12): `CONSISTENT` across Interpreter → Mapping →
  Evidence → Reason.
- Test pass count (§16) reconciled against R2's merge-time figure (exact
  match) and against the [prior] 1698 baseline (growth explained by the
  four tracks' added tests + intervening work; no regression).
- No historical decision was overwritten: KEEP_SHARED, EVIDENCE_LIMITED,
  and the DROP_ALL family policy are all cited as adopted and left intact.

### Blocker test

A gap is treated as a blocker only if current integrated behaviour
**violates an adopted contract**, **produces invalid evidence/scoring**, or
**is a material regression**. Checked:

- No adopted contract is violated (C1 Max intact; `communication == set()`;
  `family == {16,35}`; `mental == {11,26,28,38}`; `protection ∋ 2`;
  courage∩career `= {12,30}`; no stale 42–45).
- No invalid evidence: no disabled/removed GID produces a winner or a Lead
  label anywhere (§7, §8).
- No regression: full suite green; focused sets green; interpreter
  collision controls all hold; D1a strictly additive.

**No blocker discovered.**

### Verdict

**`ENGINE_READY_WITH_KNOWN_GAPS`.**

The recommendation engine's core logic — interpreter, Need→GID mapping, C1
Max scoring, winner metadata, Lead hierarchy, Reason contract — operates
correctly and consistently across all 15 Needs after D1a/C-EL/M1/R2. The
remaining gaps (§15) are data-coverage limitations (`study` geography,
`family` fertility-shrine count), adopted product limitations
(`communication` EVIDENCE_LIMITED, mental/rest shared intent,
courage/career KEEP_SHARED), and optional future enhancements (protection
Text coverage, communication taxonomy, one legacy Reason-source conflict).
None of them violates a contract or degrades engine correctness.

This verdict is unchanged in kind from the prior
`compass-recommendation-engine-finalization.md` verdict. Against the §15
reclassification (17 unique gap items, 20 category assignments, 3 items
multi-classified), this series **CLOSED 5 items** (§15 rows 1–5 — rows 1–3
and 5 cleanly, plus row 4 whose invalid-mapping defect is fixed while its
evidence limitation continues as the adopted `EVIDENCE_LIMITED` policy) and
**formalised 5 items as `INTENTIONAL_LIMITATION`** (rows 4, 6, 8, 14, and
part of 15). The rest are pre-existing `DATA_GAP` / `PRODUCT_DECISION` /
`FUTURE_ENHANCEMENT` items carried forward unchanged. **REGRESSION = 0,
BLOCKER = 0.**

## 18. Follow-up Items

Not implemented here (audit only). No new fixes were derived into code.

| Item | Type | Owner note |
|---|---|---|
| Communication-specific canonical taxonomy (C2 → C2m → C2t → C3 → R3 chain) | FUTURE_ENHANCEMENT | Blocked on a Mother Ship investment decision; decision packet already scoped it |
| `family` fertility-shrine / `安産`·`子宝` tag coverage expansion | DATA_GAP / FUTURE_ENHANCEMENT | Data work, not engine work; do not add non-fertility GIDs |
| `study` shrine geographic distribution (Engine PR-B) | DATA_GAP | [prior] optional; scoring/ranking unchanged |
| `protection` Text Coverage SET-A (Engine PR-A) | FUTURE_ENHANCEMENT | [prior] `LOW_VALUE`, Mother Ship call |
| `career` / 赤坂氷川神社 winner↔Reason-source conflict (Engine PR-C) | FUTURE_ENHANCEMENT | [prior] high complexity; unverified for regression here |
| Orphaned canonical ids `{17,19,22,23,25,29,31,34,37,39}` | DATA_GAP | Housekeeping; leaving them in the master is the accepted state |
| Re-verify legacy QUESTIONABLE mappings | PRODUCT_DECISION (deferred) | [prior]; out of scope of this series |
| duplicate shrine rows (長太稲荷神社) | DATA_GAP | [prior]; dataset-integrity scope |

## 19. STOP / No Production Changes

- Production code changed: **none**.
- Files added by this PR: **`docs/audit/recommendation-semantic-followup-closeout.md`** only.
- `git diff --check`: CLEAN.
- No blocker discovered — therefore no blocker report, and nothing to fix
  in a separate branch.
- Audit helper `scratchpad/closeout_audit.py` was run for [runtime]
  observations and is **not committed**.

This branch is docs-only. STOP.
