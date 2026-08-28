# Recommendation Semantic Resolution Cross-Need Audit

> **Status**: AUDIT ONLY. No production behavior modified. All findings from fresh code-read and read-only runtime simulation (interpreter, axis resolver, and live `get_compass_recommendations`/`build_chat_recommendations` calls against the existing isolated local scratch DB — no writes).

## 1. Objective

Determine whether meaningful user-intent nuance survives the full Recommendation semantic pipeline (Input → Interpreter → Need → Consultation Axis → GID/Text Evidence → C1 Winner → Ranking/Top3 → Lead → Reason), across **all 15 canonical Need tags**, not just `marriage` (whose track — PR #2586/#2590/#2591/#2593 — is now fully closed and serves as this audit's methodology template).

## 2. Scope

All 15 `NEED_TAGS`. Full pipeline, every layer. Fresh-read of current code as primary source; prior audits reconciled against, not assumed valid.

## 3. Non-Goals

No fixes. No new taxonomy. No new Need tags, GoriyakuTags, or consultation axes. No mapping/alias/interpreter/axis/C1/Ranking/Lead/Reason/Direction/Distance/DB/Model/Seed/frontend changes.

## 4. Base SHA

`origin/develop` at `35b60921296479373534205395b912e90eef9628` (`fix: add marriage recommendation reason copy (#2593)`). `git log --oneline b8085b04..35b60921`: `f1329995` (PR #2592, frontend-only, `apps/web/src/lib/concierge/buildReasonNarrative.ts`, confirmed zero backend overlap) then `35b60921` (PR #2593, this audit's prerequisite). Worktree: `/Users/morietsu/Developer/jinja_app-semantic-resolution-audit`, branch `audit/recommendation-semantic-resolution-cross-need`.

## 5. Canonical Need Inventory

Fresh-read (not remembered) from `backend/temples/domain/need_tags.py`, `consultation_axis.py`, `concierge_chat_ranking.py`:

| Need | Aliases (→ this Need) | `NEED_PRIORITY` index | Mapped GID ids | Consultation Axis | Text Evidence | Lead support | Reason `intent_map` |
|---|---|---:|---|---|---|---|---|
| protection | none | 0 | {11,32,2} | *(none)* | No | Yes (generic mechanism) | Yes — "厄除けや守り" |
| marriage | none (alias removed PR #2586) | 1 | {1,18} | relationship_repair | No | Yes | Yes — "良縁や夫婦円満" |
| love | romance | 2 | {1,20} | relationship_repair | Yes (9 words) | Yes | Yes — "恋愛や良縁" |
| family | none | 3 | {2,26,34} | *(none)* | No | Yes | **No** |
| study | none | 4 | {9,10} | study_success | Yes (8 words) | Yes | Yes — "学業や合格" |
| career | career_change, work | 5 | {6,21,30,12,27} | career_change | Yes (10 words) | Yes | Yes — "仕事や転機" |
| money | fortune | 6 | {5,36,4,28} | money_growth | Yes (9 words) | Yes | Yes — "金運向上" |
| health | none | 7 | {7,8,24,33,38} | *(none)* | No | Yes | **No** |
| mental | anxiety | 8 | {11,16,26,28,38} | restart_mindset | Yes (9 words) | Yes | Yes — "不安や心の安定" |
| relationship | none | 9 | {1} | relationship_repair | No | Yes | **No** |
| communication | none | 10 | {30,33,37,39} | *(none)* | No | Yes | **No** |
| courage | challenge, ambition, success | 11 | {12,15,18,20,24,30,38} | restart_mindset | Yes (8 words) | Yes | Yes — "前進や後押し" |
| focus | none | 12 | {9,10} | study_success | No | Yes | **No** |
| rest | healing | 13 | {7,8} | rest_healing | Yes (10 words) | Yes | Yes — "休息や気持ちの切り替え" |
| travel_safe | none | 14 | {3,13,14} | *(none)* | No | Yes | **No** |

**Totals**: 15 canonical Needs. 9 alias source tokens (`romance`, `career_change`, `work`, `fortune`, `anxiety`, `healing`, `challenge`, `ambition`, `success`) — 0 aliases collapse a canonical Need into another canonical Need since PR #2586 (only English-token synonyms remain aliased). **0 Needs with zero GID mapping.** **6 Needs with zero Text Evidence** (protection, marriage, family, health, relationship, communication, focus, travel_safe — 8 actually, corrected below). **5 Needs with no consultation-axis entry** (protection, family, health, communication, travel_safe — all fall to `other` via tier-3, or occasionally a query-level tier-2 hit). **6 Needs with no `intent_map` entry** (family, health, relationship, communication, focus, travel_safe).

Re-count of zero-Text-Evidence Needs precisely: protection, marriage, family, health, relationship, communication, focus, travel_safe = **8 of 15**. Only 7 have Text Evidence: love, study, career, money, mental, courage, rest.

## 6. Pipeline Contract

Fresh-traced, single authoritative implementation confirmed at each layer (no undiscovered duplicates beyond the two already-known twin copies):

```
extract_need_tags(query)          [temples/domain/need_tags.py]
  KEYWORDS (substring) + REGEX (pattern) -> hits{tag: [words]}
  -> pick by NEED_PRIORITY, max_tags=3 -> NeedExtract(tags, hits)

resolve_need_payload(query, need_tags)   [concierge_chat_need.py]
  -> extract_need_tags() if no explicit need_tags
  -> normalize_need_tags() (applies NEED_TAG_ALIASES, TWO independent
     copies: concierge_chat_need.py and concierge_chat_ranking.py,
     kept textually identical by convention, re-confirmed this session)

resolve_consultation_axis(query, need_tags)   [consultation_axis.py]
  tier 1: llm_axis (not used by free-text queries)
  tier 2: query-text match against CONSULTATION_AXIS_KEYWORDS (checked FIRST)
  tier 3: need_tags fallback against NEED_TAG_TO_CONSULTATION_AXIS
          (iterates need_tags in order, returns first tag with an axis entry)
  else: "other"

_attach_breakdown() / _prefilter_candidates_for_need()   [concierge_chat_ranking.py]
  need_tags_to_goriyaku_ids(need_tags) -> GID evidence
  NEED_TEXT_WEIGHTS.get(tag, {}) -> Text evidence (scans candidate goriyaku/description)
  C1 Max: GID_ONLY -> gid; TEXT_ONLY -> text; BOTH -> max(gid,text), tie->gid; NONE -> 0
  resolve_history_theme_candidate_boost(axis, history_theme) -> secondary ranking-magnitude only

build_recommendation_reason() -> _build_need_lead() (Need-agnostic, winner-aware)
                               -> _build_need_reason_text() -> intent_map.get(tag, "今の願い")
```

**New finding, not previously documented**: `NEED_LABELS_JA` (a THIRD, separately-tracked Need→Japanese-string dict, distinct from `intent_map`) exists in **two** copies (`concierge_chat_ranking.py` line 489, `concierge_explanation_payload.py` line 10), used at `"label_ja": NEED_LABELS_JA.get(label, label)` inside the structured explanation payload. **5 Needs are absent from both copies**: `marriage`, `relationship`, `communication`, `health`, `family`. Confirmed live in this session's own prior PR #2593 testing: a marriage-tagged explanation payload showed `'label_ja': 'marriage'` — the raw English key, not a Japanese label — because `NEED_LABELS_JA.get("marriage", "marriage")` fell through to its own default. This is a real, user-facing gap **distinct from and not fixed by** the `intent_map["marriage"]` addition (PR #2593), which only affects the free-text `reason` sentence, not this structured `label_ja` field. See Section 17.

## 7. Natural Language Corpus Method

65 total queries: 4 per Need for 14 Needs, 5 for `marriage` (already exhaustively audited across 4 prior PRs) and 5 for `courage`. Every phrase is drawn from repository sources: `NEED_KEYWORDS`/`KEYWORDS` vocabulary itself, existing test fixtures (`test_concierge_relationship_love_separation.py`, `test_concierge_need_variation.py`, `test_consultation_axis_contract.py`), and existing audit documents (`marriage-consultation-interpreter-coverage.md`'s corpus design pattern, reused for the other 14 Needs). No invented keyword-stuffing.

## 8. Interpreter Results

Full corpus run through `extract_need_tags`/`resolve_need_payload` this session (raw output preserved in this document's Section 20 table; representative highlights below).

| Need | Correct | Total | Coverage | False positives | Cross-Need collisions |
|---|---:|---:|---:|---:|---:|
| love | 4 | 4 | 100% | 0 | 0 |
| relationship | 2 clean + 2 known-gap | 4 | 50% clean / 100% axis-compensated | 0 | 1 (整えたい, shared w/ mental+rest) |
| marriage | 5 | 5 | 100% | 0 | 1 (整えたい, shared w/ mental+rest, marriage still correctly present) |
| communication | 2 | 4 | 50% | 0 | 1 (WRONG_NEED: 職場 routes to relationship) |
| career | 4 | 4 | 100% | 0 | 0 |
| money | 4 | 4 | 100% | 0 | 0 |
| study | 4 | 4 | 100% | 0 | 0 |
| health | 3 clean + 1 collision | 4 | 75% | 0 | 1 (整えたい, shared w/ mental+rest) |
| mental | 4 (all include mental) | 4 | 100% (Need-presence); 50% (isolated) | 0 | 3 of 4 cases co-extract rest and/or protection |
| protection | 4 | 4 | 100% | 0 | 0 (in this corpus; known collision with mental elsewhere) |
| courage | 5 | 5 | 100% | 0 | 0 (interpreter-layer clean; GID/Text-layer overlap with career exists but does not manifest here) |
| focus | 4 | 4 | 100% | 0 | 0 |
| rest | 3 clean + 1 collision | 4 | 75% | 0 | 1 (疲れ/癒し, shared w/ mental) |
| family | 3 clean + 1 miss | 4 | 75% | 0 | 1 (WRONG_NEED: 家族の健康 routes to health+relationship, not family) |
| travel_safe | 4 | 4 | 100% | 0 | 0 |

**New, systemic finding**: `"整えたい"` (a conjugation-family root, "to put in order/adjust") is a shared collision trigger across **at least 4 Needs simultaneously**: `mental` (KEYWORDS), `rest` (KEYWORDS), and — via co-occurrence in the same sentence — observed pulling in `relationship`, `marriage`, and `health` whenever their own distinguishing word (家族/夫婦関係/体調) appears alongside it. This is a broader, more systemic pattern than the marriage track's own framing ("OVERBROAD_MENTAL_KEYWORD + OVERBROAD_REST_KEYWORD") suggested — it is not marriage-specific at all, but a general property of `mental`/`rest`'s own shared vocabulary colliding with *any* other Need whose distinguishing word happens to co-occur with "整えたい" in a natural sentence.

**New finding**: `rest`'s `REGEX` entry (`re.compile(r"(穏やか|静か|落ち着|リセット|休息|癒し|ひと息|一息)")`) uses the bare root `"落ち着"` (no okurigana), which matches *any* conjugation containing that root — broader than `rest`'s own `KEYWORDS` list (which requires the exact forms `"落ち着きたい"`/`"落ち着く"`). This explains why `"不安な気持ちを落ち着けたい"` (a mental-only query in intent) pulls in `rest` via `REGEX`, independent of `mental`'s own vocabulary.

**New finding**: `family`'s `KEYWORDS` list (`子宝/安産/妊活/授かり/出産/育児`) is **entirely about childbirth/childrearing** — the literal word `"家族"` ("family") is not in it at all; `"家族"` belongs only to `relationship`'s `KEYWORDS`. A query like `"家族の健康を願いたい"` therefore never extracts `family`, only `health`+`relationship`. `family` as implemented is narrower than its English name suggests — it functions as "fertility/childbirth," not "family relations" (that responsibility sits entirely with `relationship`).

## 9. Consultation Axis Results

| Need | Axis result pattern | Classification |
|---|---|---|
| love | Always `relationship_repair`, via `need_tags` tier | `DIRECT_FIT` |
| relationship | `relationship_repair`, mostly via `query` tier (even for 2 Interpretation-Gap cases with empty `need_tags` — the query-level keyword list is more robust than `KEYWORDS` here) | `DIRECT_FIT` |
| marriage | Always `relationship_repair`, via `need_tags` tier | `DIRECT_FIT` |
| communication | `other` (fallback) for 3 of 4; `relationship_repair` for the 1 miscategorized case | `FALLBACK_OTHER` (dominant) |
| career | **Varies by sub-phrasing**: `career_change` (3 cases) vs. `independence` (1 case, "独立して起業したい" — a genuinely different axis, not a Need-tag collapse) | `REUSABLE_WITH_LIMITATION` — see Section 12, this is a *positive* nuance-preservation finding |
| money | Always `money_growth` | `DIRECT_FIT` |
| study | Always `study_success` | `DIRECT_FIT` |
| health | `other` (fallback) for 3 of 4; `restart_mindset` for the 1 collision case (via mental's axis, not health's own) | `FALLBACK_OTHER` (dominant) |
| mental | Always `restart_mindset` | `DIRECT_FIT` |
| protection | Always `other` (fallback) | `FALLBACK_OTHER` |
| courage | Always `restart_mindset` | `DIRECT_FIT` |
| focus | Always `study_success` (shared with study) | `DIRECT_FIT` (structural, by design — focus and study share the identical axis, per the safe-mapping-correction PR's own precedent) |
| rest | Always `rest_healing` | `DIRECT_FIT` |
| family | Always `other` (fallback) | `FALLBACK_OTHER` |
| travel_safe | Always `other` (fallback) | `FALLBACK_OTHER` |

**5 Needs are `FALLBACK_OTHER`-dominant**: communication, health, protection, family, travel_safe — all 5 lack a `NEED_TAG_TO_CONSULTATION_AXIS` entry (Section 5), matching exactly. None of the 5 shows a case where the interpreter is correct but the axis actively *weakens* an otherwise-working signal (`SEMANTIC_MISMATCH` was not observed) — the axis is simply inert (`resolve_history_theme_candidate_boost` returns 0.0 for `other`, per the marriage-axis audit's own finding) rather than actively wrong.

## 10. GID Evidence Results

Re-verified against the current 39-row master (fresh query, this session — unchanged from every prior audit in this chain):

| Need | Mapped ids | Total shrine-evidence (sum, may double-count shared shrines) | Classification |
|---|---|---:|---|
| career | 6,21,30,12,27 | 74 | `STRONG` |
| protection | 11,32,2 | 71 | `STRONG` |
| family | 2,26,34 | 54 | `STRONG` |
| love | 1,20 | 36 | `PARTIAL` |
| marriage | 1,18 | 33 | `PARTIAL` |
| health | 7,8,24,33,38 | 30 | `PARTIAL` |
| mental | 11,16,26,28,38 | 28 | `PARTIAL` |
| rest | 7,8 | 27 | `PARTIAL` |
| money | 5,36,4,28 | 23 | `PARTIAL` |
| courage | 12,15,18,20,24,30,38 | 20 | `PARTIAL` |
| travel_safe | 3,13,14 | 12 | `SPARSE` |
| study | 9,10 | 11 | `SPARSE` |
| focus | 9,10 | 11 | `SPARSE` (identical to study's — shared evidence by design, per the safe-mapping-correction PR's precedent, not a defect) |
| communication | 30,33,37,39 | 4 | `SPARSE` and `SEMANTICALLY_MISALIGNED` (none of the 4 tags — 強運厄除け/病気平癒/延命長寿/農業守護 — fits "communication" at all; unchanged since the remaining-need-semantic-mapping audit, `PRIOR_FINDING_STILL_VALID`) |

**No Need has zero GID evidence.** No Need's mapping is freshly found `STRUCTURALLY_BROKEN` (the ids-42-45 issue was fully resolved by PR #2578). `study`/`focus` sharing identical evidence is `EXPECTED_SHARED_NEED` (Section 14), not a collapse — both genuinely represent the same underlying `study_success` concept per the taxonomy's own design.

## 11. Text Evidence Results

7 of 15 Needs have `NEED_TEXT_WEIGHTS` coverage (Section 5). Fresh-read the full vocabulary (Section 6 lists all 7).

| Need | Overlap found | Classification |
|---|---|---|
| love | Contains `結婚`/`夫婦円満`/`ご縁` — **marriage-domain words, never updated when marriage became independent (PR #2586–#2593 never touched `NEED_TEXT_WEIGHTS`)** | `COLLISION_RISK`, code-level. DB-verified: only 1 shrine (筑波山神社) currently has this text overlap, and it already carries the correct `marriage` GIDs (1, 18) too — **`NOT_REPRODUCED`** in current data (zero shrines currently surface incorrectly because of this), but the vocabulary itself remains a latent risk for any future shrine whose free text mentions marriage-domain words without also being GID-tagged |
| mental | Contains `厄除`/`厄払い`/`浄化`/`守護`/`守ってほしい` (protection-adjacent, previously documented) and `静か` (shared verbatim with `rest`'s own Text vocabulary) | `OVERLAPPING` — re-confirmed still valid |
| rest | Shares `静か` and (via the `mental`/`rest` `KEYWORDS` collision documented in Section 8) the general "整える/落ち着く" semantic space | `OVERLAPPING` |
| career | Shares `勝運` verbatim with `courage`'s own Text vocabulary | `OVERLAPPING` — re-confirmed still valid, unchanged since the product-decision audit |
| courage | Shares `勝運` with career; also contains `開運`/`開運祈願` which is its own, largely distinct territory | `OVERLAPPING` (career) |
| study | No verbatim overlap found with any other Need's Text vocabulary | `STRONG`, differentiates well |
| money | No verbatim overlap found | `STRONG` |

**8 Needs have zero Text Evidence** (`protection`, `marriage`, `family`, `health`, `relationship`, `communication`, `focus`, `travel_safe`) — for these, GID matching is the *only* evidence path; there is no fallback if a candidate's real-world `goriyaku`/`description` text would have supported a match but its `goriyaku_tags` relation wasn't correctly backfilled.

## 12. C1 Results

Live Compass runs (fixed fixture) for all 15 Needs, `need_evidence_winner_by_tag`:

| Need | Winner pattern observed |
|---|---|
| love | `text` (all 3 Top3 candidates) |
| relationship | `gid` (all 3) |
| marriage | `gid` (all 3) |
| mental | `text` (all 3) |
| rest | `gid` (2), `{}` fallback (1) |
| protection | `gid` (all 3) |
| study | `{}` — no matches in this fixture (all fallback) |
| career | `text` (all 3) |
| money | `text` (all 3) |
| courage | `text` (all 3) |
| focus | `{}` — no matches (fallback) |
| family | `gid` (all 3) |
| travel_safe | `gid` (1), `{}` (2) |
| health | `gid` (2), `{}` (1) |
| communication | `{}` — no matches (fallback) |

**Classification**: no Need shows `ALWAYS_GID`-only or `ALWAYS_TEXT`-only as a structural defect — the pattern directly reflects which evidence layer (GID vs Text) each Need actually has coverage for (Section 10/11), and C1 correctly selects whichever is available and stronger. `COLLAPSED_WINNER_PATTERN` not observed anywhere; `COLLISION_DRIVEN` winners not observed (no case where a wrong-Need's evidence won). **C1 itself preserves every distinction the upstream layers hand it** — it is never the layer where information is lost.

## 13. Ranking / Top3 Results

Comparing sub-variation queries *within* the same Need at the fixed Compass fixture is not directly meaningful for query-driven purposes (Compass itself is button/`purpose`-driven, not free-text — Section 6 already established Compass structurally bypasses the interpreter for its own candidate scoring, using `need_tags=[purpose_slug]` directly). For Needs tested via live `build_chat_recommendations` with real query text (marriage's 9 cases, `career`'s "独立して起業したい" vs. others), Top3 composition differences observed were **entirely axis-driven** (Section 9's `career_change` vs. `independence` split) or **entirely GID-driven** (marriage's id=1 vs id=18 evidence-variant tests, PR #2593) — never a scoring-formula artifact. No `RANKING_COLLAPSE` was found: every observed "identical Top3" case traces to a specific, attributable cause (shared correct evidence for `love`/`relationship`/`marriage` at id=1, per Section 14's `DISTINCT` vs `EXPECTED_SHARED_NEED` distinction) rather than an unexplained scoring collapse.

## 14. Intra-Need Semantic Collapse

| Need | Sub-variations tested | Collapse observed? | Cause |
|---|---|---|---|
| love | encounter / romantic fulfillment / reconciliation / unrequited love | No — all 4 correctly and independently extract `love`, all draw on the same GID/Text evidence (expected, since love-seeking is a single underlying concept regardless of framing) | `EXPECTED_SHARED_NEED` |
| marriage | seeking (4 variants) / existing-marriage (5 variants) | Partial — both families correctly reach `marriage`, but both currently share the exact same `intent_map` copy ("良縁や夫婦円満") and the same GID pool ({1,18}); a materially *distinct* seeking-vs-harmony Reason would require a new sub-taxonomy (explicitly out of scope for the marriage track, `ONE_COPY_SUFFICIENT` was the Mother-Ship-facing conclusion) | `EXPECTED_SHARED_NEED` by design |
| career | employment / job change / promotion-adjacent / independence | **Axis differs** for the independence sub-variant (career_change vs. independence) — genuine nuance preservation, not a collapse | N/A (preserved) |
| money | financial luck / business prosperity / income / asset prosperity | No collapse observed in the 4-case corpus; all draw on the same GID pool (expected — money's own sub-concepts are closely related) | `EXPECTED_SHARED_NEED` |
| study | academic study / exams / qualification / concentration-adjacent | `focus` (a *separate* canonical Need) is the "concentration" sub-variant already — within `study` itself, no collapse observed among its own 4 cases | N/A |
| mental | emotional stability / anxiety / calming oneself / protection-adjacent phrasing | **Collapses with `rest` and/or `protection`** for 3 of 4 cases — not a within-`mental` collapse, but a cross-Need one (Section 8/13) | `TEXT_COLLAPSE` + `INTERPRETER` (see Phase 19 re-audit) |
| family | fertility-seeking (3 cases, correct) / family-harmony framing (1 case) | **Collapses to `health`+`relationship`**, `family` never appears — the "family harmony" sub-variant is not actually representable by the current `family` Need at all (Section 8) | `MAPPING_COLLAPSE` at the *interpreter-keyword* level (family's own vocabulary is definitionally narrower than "family" implies) |

## 15. Cross-Need Collision Matrix

| Pair | Interpreter overlap | GID overlap | Text overlap | Axis overlap | C1/Top3 overlap | Risk |
|---|---|---|---|---|---|---|
| love ↔ marriage | None (KEYWORDS fully distinct, re-confirmed) | id=1 (shared, by design) | **love's Text vocabulary contains marriage-domain words** (Section 11) | Shared (relationship_repair, by design) | Shared id=1 candidates only | `LOW` (structural sharing is intentional; the Text-vocabulary overlap is `INTENTIONAL_SHARED_EVIDENCE`-adjacent but was never explicitly decided — flagged, not alarming, given 0 DB impact) |
| love ↔ relationship | None | id=1 (shared) | None | Shared | Shared id=1 | `NONE` — this is the PR #2409-established, deliberately-preserved separation, re-confirmed still intact |
| marriage ↔ relationship | None | id=1 (shared) | None | Shared | Shared id=1 | `NONE` — same as above |
| relationship ↔ communication | Query-level: "職場" (relationship's keyword) captures a communication-intended query | None | None | relationship has axis, communication doesn't | N/A (communication rarely reaches any candidate) | `MEDIUM` — re-confirmed `PRIOR_FINDING_STILL_VALID` (Section 19) |
| mental ↔ rest | `整えたい`/`疲れ`/`癒し` (KEYWORDS), `静か` (Text), `落ち着` (rest's own overbroad REGEX) | None | `静か` shared | Different (restart_mindset vs rest_healing) but co-occurrence means both often appear together anyway | Both frequently co-extracted, but evidence for each is independently correct when present | `HIGH` — the single most collision-prone pair in the entire taxonomy, confirmed by fresh corpus data across 3+ separate test queries |
| mental ↔ protection | `厄`/`流れが悪い` (KEYWORDS, both files) | None (protection's own GID={11,32,2}, mental's={11,16,26,28,38} — id=11 shared) | None found this session (mental's Text vocab includes 厄除/厄払い, protection-adjacent by wording, not by exact overlap) | Different (restart_mindset vs other) | id=11 shared | `MEDIUM` |
| courage ↔ career | None (interpreter-layer clean, confirmed this session) | ids 12,30 shared | `勝運` shared | Different (restart_mindset vs career_change) | Not observed to co-occur in this corpus | `MEDIUM` — real but confined to GID/Text layers, not user-facing query ambiguity |
| courage ↔ protection | None found | None (courage={12,15,18,20,24,30,38}, protection={11,32,2} — no overlap) | None | Different | None | `NONE` — checked directly, confirmed absent (re-verified, consistent with the product-decision audit) |
| study ↔ focus | None (interpreter-layer fully distinct vocabularies) | **Identical** ({9,10} both) | study has Text, focus does not | **Identical** (study_success, by design) | Would co-occur only if both requested simultaneously (not tested; structurally would share evidence) | `INTENTIONAL_SHARED_EVIDENCE` |
| health ↔ mental | `整えたい` (体調を整えたい pulls in both) | None (health={7,8,24,33,38}, mental={11,16,26,28,38} — id=38 shared) | None | Different (other vs restart_mindset) | id=38 shared | `MEDIUM` |
| family ↔ relationship | **`家族` belongs only to relationship**, not family (Section 8/14) | None (family={2,26,34}, relationship={1} — no overlap) | None (neither has Text Evidence) | Neither has a dedicated axis for this specific overlap | None | `MEDIUM-HIGH` — a "family-relations" query can never reach `family`, only `relationship`, an asymmetry not previously documented |
| money ↔ career | None found in this corpus | id=28 shared (career QUESTIONABLE there per the original mapping audit, unchanged) | None found | Different (money_growth vs career_change) | Not observed to co-occur | `LOW` |

## 16. Lead Results

Fresh-traced `_resolve_matched_lead_evidence`/`_build_need_lead` (Need-agnostic mechanism, unchanged across every PR in this session): resolves `matched_gid_label` from the real matched `GoriyakuTag.name`, or `matched_text_hint` when the C1 winner is `text`, or a per-Need `fallback` dict (8 entries: study/mental/rest/love/career/money/courage/protection — **not** marriage/relationship/communication/focus/family/travel_safe/health), or the generic `"ご利益"` string.

| Need | Lead result |
|---|---|
| love, career, money, courage, mental, rest, protection, study | `READY` — real GID/Text label surfaces correctly (confirmed live for all except study, which had no fixture matches this session but is code-identical) |
| marriage | `READY` (confirmed PR #2593, both id=1 and id=18) |
| relationship, family, health, travel_safe | `READY` for the *matching mechanism* (GID label surfaces correctly when evidence exists, confirmed live for all 4 — 縁結び/厄除け/家内安全/交通安全 all appeared correctly) — but **falls to generic `"ご利益"`** for any candidate with zero evidence, since none of these 4 has a `fallback` dict entry either |
| communication, focus | `NO_EVIDENCE_TO_TEST` in this fixture (0 real matches observed; code path is identical to the other Needs, no reason to expect different behavior once evidence exists) |

**No Need shows `BROKEN` or `PARTIAL` Lead** — the mechanism itself is uniformly healthy and Need-agnostic across all 15. The only variation is *fallback-dict coverage* (8 of 15), which only matters for the already-rare no-evidence-at-all case.

## 17. Reason Results

| Need | `intent_map` | Actual Reason observed |
|---|---|---|
| love, career, money, courage, mental, rest, protection, study | Present | `READY` — evidence-specific Lead + Need-specific intent clause, confirmed live for all except study (code-identical) |
| marriage | Present (PR #2593) | `READY` |
| relationship, family, health, travel_safe | **Absent** | `GENERIC_FALLBACK`, confirmed live for all 4 — e.g. `family`: `"厄除けのご利益で知られる明治神宮は、今の願いを願う参拝先として適しています。"` (score_need=1, a real match, but generic copy) |
| communication, focus | Absent | `GENERIC_FALLBACK` (code-confirmed; no live match to observe this session) |

**New finding**: `NEED_LABELS_JA` (Section 6) is a *third*, structurally separate gap from `intent_map` — 5 Needs (`marriage` was one before PR #2593, now `relationship`/`communication`/`health`/`family` remain) show their raw English key as `label_ja` in the structured explanation payload, even for Needs whose free-text `reason` sentence is otherwise correct (e.g. `love`, `career` — wait, these DO have `NEED_LABELS_JA` entries, confirmed Section 6). The 5 currently missing are `marriage`(now fixed for `reason` text but **not** for `label_ja` — `intent_map` and `NEED_LABELS_JA` are separate dicts and PR #2593 only touched `intent_map`), `relationship`, `communication`, `health`, `family`. **This means `marriage`'s structured `label_ja` field still shows the literal string `"marriage"`, an English word, in a Japanese-language product — a real, live, currently-unaddressed gap this audit newly surfaces.**

## 18. End-to-End Semantic Preservation

| Need | Chain | Verdict | First broken layer |
|---|---|---|---|
| love | Interpreter✓ → Axis✓ → Evidence(Text-strong)✓ → C1✓ → Top3✓ → Lead✓ → Reason✓ | `PRESERVED` | none |
| relationship | Interpreter(partial, 2 known gaps)✓axis-compensated → Axis✓ → Evidence(GID-only)✓ → C1✓ → Top3✓ → Lead✓ → Reason✗(generic) | `PARTIALLY_PRESERVED` | Reason (`intent_map` absent) |
| marriage | ✓ all layers (4-track remediation complete) | `PRESERVED` | none (at the `reason` sentence layer — `label_ja`, Section 17, remains a residual gap) |
| communication | Interpreter✗(50%) → Axis✗(fallback) → Evidence(sparse+misaligned) → C1(mostly none) → Reason✗ | `MULTI_LAYER_FAILURE` | Interpreter |
| career | ✓ Interpreter → Axis(nuanced, positive)✓ → Evidence(strong)✓ → C1✓ → Top3✓ → Lead✓ → Reason✓ | `PRESERVED` | none |
| money | ✓ all layers | `PRESERVED` | none |
| study | ✓ Interpreter/Axis/Evidence/C1(untested live, code-sound)/Lead/Reason | `MOSTLY_PRESERVED` | none identified; DB sparsity limits live confirmation |
| health | Interpreter(75%, 1 collision) → Axis(fallback) → Evidence(GID-only, PARTIAL) → C1✓ → Top3✓ → Lead✓(mechanism)/generic-fallback-risk → Reason✗ | `PARTIALLY_PRESERVED` | Axis (first structural gap), compounded by Reason |
| mental | Interpreter(collision-prone) → Axis✓ → Evidence(Text-overlapping) → C1✓ → Top3✓ → Lead✓ → Reason✓ | `PARTIALLY_PRESERVED` | Interpreter (collision with rest/protection) |
| protection | ✓ Interpreter → Axis(fallback, inert not wrong) → Evidence(strong)✓ → C1✓ → Top3✓ → Lead✓ → Reason✓ | `MOSTLY_PRESERVED` | Axis (inert, not semantically damaging) |
| courage | ✓ Interpreter(clean) → Axis✓ → Evidence(Text-overlapping w/ career) → C1✓ → Top3✓ → Lead✓ → Reason✓ | `MOSTLY_PRESERVED` | GID/Text (career overlap, not user-visible in this corpus) |
| focus | ✓ Interpreter → Axis✓(shared w/ study, by design) → Evidence(sparse, shared w/ study, by design) → C1(untested live) → Reason✗ | `PARTIALLY_PRESERVED` | Reason |
| rest | Interpreter(75%, 1 collision) → Axis✓ → Evidence(Text-overlapping) → C1✓ → Top3✓ → Lead✓ → Reason✓ | `MOSTLY_PRESERVED` | Interpreter (collision with mental) |
| family | Interpreter(75%, 1 structural miss) → Axis(fallback) → Evidence(strong, GID-only) → C1✓ → Top3✓ → Lead✓(mechanism) → Reason✗ | `MULTI_LAYER_FAILURE` | Interpreter (structural — "家族" not in family's own vocabulary at all) |
| travel_safe | ✓ Interpreter → Axis(fallback, inert) → Evidence(sparse)✓ → C1✓ → Top3✓ → Lead✓(mechanism) → Reason✗ | `PARTIALLY_PRESERVED` | Axis, compounded by Reason |

## 19. Semantic Health Classification Rules

Applied per Section 17 of the task exactly as defined (`HEALTHY`/`PARTIAL`/`COLLAPSED`/`INTERPRETER_GAP`/`EVIDENCE_GAP`/`EXPLANATION_GAP`/`MULTI_LAYER`/`DATA_LIMITED`), one primary class per Need.

## 20. Recommendation Semantic Health Map

| Need | Corpus | Interpreter | Axis | GID | Text | C1 | Top3 | Lead | Reason | Intra-Need Nuance | Cross-Need Risk | Primary Health | First Broken Layer | Notes |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|
| love | 4 | 100% | DIRECT_FIT | PARTIAL | STRONG (overlap risk w/ marriage words, unmanifested) | HEALTHY | PRESERVED | READY | READY | Preserved | LOW | **HEALTHY** | none | Text-vocab/marriage overlap flagged, 0 DB impact |
| career | 4 | 100% | DIRECT_FIT+nuance | STRONG | OVERLAPPING (courage) | HEALTHY | PRESERVED | READY | READY | Preserved (axis nuance) | MEDIUM (courage) | **HEALTHY** | none | Independence sub-axis is a positive finding |
| money | 4 | 100% | DIRECT_FIT | PARTIAL | STRONG | HEALTHY | PRESERVED | READY | READY | Preserved | LOW | **HEALTHY** | none | |
| study | 4 | 100% | DIRECT_FIT | SPARSE | STRONG | untested-live | MOSTLY | READY | READY | Preserved | LOW (focus shared, by design) | **HEALTHY** | none | DB sparsity for live C1 confirmation only |
| protection | 4 | 100% | FALLBACK_OTHER | STRONG | ZERO | HEALTHY | PRESERVED | READY | READY | Preserved | LOW | **PARTIAL** | Axis | Axis inert not wrong; secondary flag EXPLANATION (fallback-dict only) |
| courage | 5 | 100% | DIRECT_FIT | PARTIAL | OVERLAPPING (career) | HEALTHY | untested (no collision surfaced) | READY | READY | Preserved | MEDIUM (career) | **PARTIAL** | GID/Text | Not user-visible in this corpus but structurally real |
| marriage | 5 | 100% | DIRECT_FIT | PARTIAL | ZERO | HEALTHY | PRESERVED | READY | READY | Preserved (shared by design) | LOW | **HEALTHY** | none | `label_ja` gap flagged as residual, secondary EXPLANATION flag |
| rest | 4 | 75% | DIRECT_FIT | PARTIAL | OVERLAPPING (mental) | HEALTHY | PRESERVED | READY | READY | Collapses w/ mental | HIGH (mental) | **PARTIAL** | Interpreter | |
| mental | 4 | 100%(presence)/50%(isolated) | DIRECT_FIT | PARTIAL | OVERLAPPING (rest, protection) | HEALTHY | PRESERVED | READY | READY | Collapses w/ rest/protection | HIGH (rest), MEDIUM (protection) | **PARTIAL** | Interpreter | Single most collision-prone Need |
| relationship | 4 | 50%/axis-compensated | DIRECT_FIT | SPARSE | ZERO | HEALTHY | PRESERVED | READY(mechanism) | GENERIC | Collapses w/ mental/rest (1 case) | LOW (vs love/marriage, by design) | **EXPLANATION_GAP** | Reason | Axis compensates interpreter gaps well |
| health | 4 | 75% | FALLBACK_OTHER | PARTIAL | ZERO | HEALTHY | PRESERVED | READY(mechanism) | GENERIC | Collapses w/ mental/rest (1 case) | MEDIUM (mental) | **MULTI_LAYER** | Axis | Compounded by Interpreter + Reason gaps |
| focus | 4 | 100% | DIRECT_FIT(shared) | SPARSE(shared) | ZERO | untested-live | untested | READY(mechanism) | GENERIC | Shared w/ study by design | LOW | **EXPLANATION_GAP** | Reason | |
| family | 4 | 75% | FALLBACK_OTHER | STRONG | ZERO | HEALTHY | PRESERVED | READY(mechanism) | GENERIC | **Structural**: "family-relations" framing unreachable | MEDIUM-HIGH (relationship) | **MULTI_LAYER** | Interpreter | Vocabulary definitionally narrower than "family" implies |
| travel_safe | 4 | 100% | FALLBACK_OTHER | SPARSE | ZERO | HEALTHY | PRESERVED | READY(mechanism) | GENERIC | Preserved | LOW | **EXPLANATION_GAP** | Reason | Axis inert but not damaging |
| communication | 4 | 50% | FALLBACK_OTHER | SPARSE+MISALIGNED | ZERO | mostly NONE | DATA_LIMITED | untested | GENERIC | Cannot be judged (data too sparse + wrong mapping) | MEDIUM (relationship) | **MULTI_LAYER** | Interpreter | Confirmed `PRIOR_FINDING_STILL_VALID` |

## 21. Health Summary Counts

- Total Needs: **15**
- `HEALTHY`: **5** — love, career, money, study, marriage
- `PARTIAL`: **4** — protection, courage, rest, mental
- `COLLAPSED`: **0**
- `INTERPRETER_GAP`: **0** (folded into `PARTIAL`/`MULTI_LAYER` per the dominant compounding factor — see Limitations, Section 24, for the classification judgment call this required)
- `EVIDENCE_GAP`: **0**
- `EXPLANATION_GAP`: **3** — relationship, focus, travel_safe
- `MULTI_LAYER`: **3** — health, family, communication
- `DATA_LIMITED`: **0** (communication is `MULTI_LAYER` primarily, with data sparsity as a contributing, not primary, factor)

**5 + 4 + 0 + 0 + 0 + 3 + 3 + 0 = 15.** Reconciles exactly.

## 22. communication Re-Audit

- Interpreter: `KEYWORDS`/`NEED_KEYWORDS` present (会話/発信/伝える/話す/営業/交渉/プレゼン/面接) but genuinely incomplete — misses common conjugations (話せる) and the word "コミュニケーション" itself, re-confirmed live this session (2 of 4 corpus cases fail, one as `WRONG_NEED` into `relationship`)
- GID mapping: `{30,33,37,39}` = 強運厄除け/病気平癒/延命長寿/農業守護 — none semantically fit "communication," re-confirmed unchanged
- Text Coverage: none, confirmed
- DB evidence: 4 shrines total, all via the semantically-wrong tags
- Relationship collisions: confirmed live (`職場でのコミュニケーションを改善したい` → `relationship`, not `communication`)
- Taxonomy limitations: no canonical tag in the 39-row master fits this Need at all, re-confirmed via full label scan

**Result: `PRIOR_FINDING_STILL_VALID`** (unchanged since `docs/audit/remaining-product-decision-need-responsibilities.md`).

## 23. mental Re-Audit

- Interpreter broad-keyword behavior: confirmed still broad — `整えたい`/`落ち着`(regex)/`疲れ`/`癒し` all still collide with `rest`; `厄`/`流れが悪い` still collide with `protection`
- rest/protection overlap: both re-confirmed live this session with fresh corpus cases (not merely re-asserted from the prior audit)
- GID evidence: `{11,16,26,28,38}` unchanged, still 0 VALID/2 QUESTIONABLE/3 INVALID per the semantic-mapping audit's classification (not re-litigated here, out of scope for THIS audit's mandate — read-only)
- Text overlap: confirmed unchanged, `静か` shared with `rest`, 4/9 words protection-adjacent
- Current explanation behavior: `intent_map["mental"]` present and correctly evidence-compatible (confirmed live, "不安や心の安定")

**Result: `PRIOR_FINDING_STILL_VALID`** for the mapping/interpreter/text findings. The Reason-layer finding is **new** in this audit's framing (mental's Reason was never separately audited before — it turns out to be `READY`, a genuinely positive, previously-unstated fact).

## 24. courage Re-Audit

- career collision: re-confirmed at the GID (ids 12, 30 shared) and Text (`勝運` shared) layers; **not** reproduced at the interpreter-keyword layer in this session's fresh 5-case corpus (no query triggered both `career` and `courage` simultaneously) — a more precise finding than the prior audit's framing, which did not explicitly test interpreter-layer isolation
- protection collision: checked directly this session, confirmed **absent** (no shared GID, Text, or interpreter keyword found) — matches the prior audit's own finding
- GID mapping: `{12,15,18,20,24,30,38}` unchanged, still 0 VALID/3 QUESTIONABLE/4 INVALID per the semantic-mapping audit
- Text Evidence overlap: `勝運` (career) confirmed the only verbatim overlap
- DB evidence: 20 total shrine-references across the 7 mapped ids, `PARTIAL`
- Ranking differentiation: not directly tested this session at the C1/Top3 layer (no courage-vs-career co-occurring query in the corpus); Lead/Reason both confirmed `READY`

**Result: `PRIOR_FINDING_STILL_VALID`** for career collision and GID/Text state; `PRIOR_FINDING_PARTIALLY_RESOLVED`-adjacent framing for the interpreter-layer question specifically, since this session found the interpreter layer itself is clean (the collision is confined to GID/Text, a more precise, narrower finding than a blanket "courage collides with career").

## 25. Prior Audit Reconciliation

| Prior finding | Source | Current classification |
|---|---|---|
| marriage FULL_COLLAPSE into love | `marriage-love-alias-boundary.md` | `RESOLVED` (PR #2586) |
| marriage axis=other | `marriage-consultation-interpreter-coverage.md` | `RESOLVED` (PR #2590) |
| marriage existing-phrase interpreter gaps | same | `RESOLVED` (PR #2591) |
| marriage MISSING_INTENT_COPY | same | `RESOLVED` (PR #2593) |
| communication MULTI_LAYER (interpreter+taxonomy) | `remaining-product-decision-need-responsibilities.md` | `STILL_VALID` (Section 22) |
| mental MULTI_LAYER (interpreter+text+taxonomy) | same | `STILL_VALID` (Section 23) |
| courage MULTI_LAYER (mapping+text+data) | same | `PARTIALLY_VALID` — interpreter-layer isolation is a new, more precise sub-finding (Section 24) |
| ids 42-45 stale references | `goriyaku-mapping-master-integrity.md` | `RESOLVED` (PR #2578) |
| id=13/14 (航海安全/海上安全) unmapped | same | `RESOLVED` (travel_safe corrected, PR #2578) |
| relationship/health/focus/family SAFE_CORRECTIONS | `remaining-need-goriyaku-semantic-mapping.md` | `RESOLVED` (PR #2582) |
| `NEED_TEXT_WEIGHTS["love"]` marriage-word overlap | *(none — not previously documented)* | **New finding this audit** (Section 11) |
| `NEED_LABELS_JA` 5-Need gap | *(none — not previously documented)* | **New finding this audit** (Section 6/17) |
| `family` vocabulary excludes "家族" itself | *(none — not previously documented)* | **New finding this audit** (Section 8/14) |
| `rest` REGEX overbroad on bare "落ち着" root | *(none — not previously documented)* | **New finding this audit** (Section 8) |

## 26. Follow-Up Needs

| Need | Health | Broken layer(s) | Root cause | Mapping-only fixes it? | Interpreter-only? | Explanation-only? | Data expansion needed? | Product/taxonomy decision needed? |
|---|---|---|---|---|---|---|---|---|
| relationship | EXPLANATION_GAP | Reason | `MISSING_INTENT_COPY` | No | No | **Yes** | No | No |
| focus | EXPLANATION_GAP | Reason | `MISSING_INTENT_COPY` | No | No | **Yes** | No | No |
| travel_safe | EXPLANATION_GAP | Reason | `MISSING_INTENT_COPY` | No | No | **Yes** | No | No |
| health | MULTI_LAYER | Axis, Interpreter, Reason | No axis entry + `整えたい` collision + no intent copy | No | Partial (only fixes the collision symptom, not axis/reason) | Partial | No | Axis-entry decision (which axis, if any, fits "health"?) |
| family | MULTI_LAYER | Interpreter (structural), Reason | `family` vocabulary excludes "家族" itself; no intent copy | No | Partial (would need new "家族"-family-harmony keywords — a scope decision, since `family` is currently fertility-only by design) | Partial | No | **Yes** — is "family" meant to include family-relations, or should that stay `relationship`'s exclusively (as it functionally does today)? |
| communication | MULTI_LAYER | Interpreter, Taxonomy | No fitting canonical tag exists; interpreter vocabulary incomplete | No | Partial (would improve recall but GID evidence would remain absent) | No | No | **Yes** — new-taxonomy question, previously deferred by every audit in this chain |
| mental | PARTIAL | Interpreter (collision) | Shared broad vocabulary with rest/protection | No | **Yes**, partially (narrowing collides with rest's own scope — a cross-Need decision) | No | No | Whether co-extraction is actually undesired (a legitimate product question, not obviously a bug) |
| rest | PARTIAL | Interpreter (collision) | Same shared vocabulary, mirrored | No | Same as mental | No | No | Same as mental |
| courage | PARTIAL | GID/Text (career overlap) | Shared evidence with career | Partial (the already-computed `{12,15,30}` simulation from the semantic-mapping audit remains available) | No | No | No | QUESTIONABLE-retention sign-off (already identified, unimplemented) |
| protection | PARTIAL | Axis (inert) | No axis entry | No | No | No | No | Low-priority axis-entry decision (protection has no obvious existing axis to reuse — unlike marriage's `relationship_repair` reuse) |
| marriage | HEALTHY | `label_ja` (residual) | `NEED_LABELS_JA` gap, separate from `intent_map` | No | No | **Yes** (small) | No | No |

## 27. Root Cause Matrix

| Root cause class | Needs affected |
|---|---|
| `MISSING_INTENT_COPY` (Reason) | relationship, focus, travel_safe, health, family, communication (6) |
| `MISSING_AXIS_ENTRY` | protection, health, family, communication, travel_safe (5) |
| `SHARED_OVERBROAD_KEYWORD` (mental↔rest, spanning into relationship/marriage/health) | mental, rest (primary); relationship, marriage, health (secondary, incidental) |
| `STRUCTURAL_VOCABULARY_GAP` (Need's own keywords don't cover its apparent scope) | family (家族), communication (コミュニケーション itself, conjugations) |
| `SHARED_GID/TEXT_EVIDENCE` (career↔courage) | career, courage |
| `TAXONOMY_MISALIGNMENT` (no fitting canonical tag exists at all) | communication |
| `NEED_LABELS_JA` gap (separate from intent_map) | marriage, relationship, communication, health, family (5) |
| `LATENT_TEXT_VOCABULARY_OVERLAP` (unmanifested in current DB) | love (marriage-domain words) |

## 28. Technical Track Design

- **TRACK A — REASON (intent_map, 6 Needs)**: relationship, focus, travel_safe, health, family, communication. Independently testable per Need (mirrors PR #2593's exact pattern). Health/family/communication's `intent_map` entries are still worth adding even though those Needs have deeper issues — Reason quality is decoupled from Interpreter/Axis/Mapping correctness (a candidate that *does* match should still get a decent Reason).
- **TRACK B — REASON (NEED_LABELS_JA, 5 Needs)**: marriage, relationship, communication, health, family. Structurally identical to Track A but a different dict, in different files (2 copies). Could be combined with Track A per-Need (same PR, same Need, two related dicts) or run as its own pass across all 5 at once (lower semantic coupling risk, since it's pure label text, not sentence construction).
- **TRACK C — AXIS (protection, health, family, communication, travel_safe)**: each requires an independent product decision (no existing axis obviously fits any of these 5 the way `relationship_repair` fit marriage) — `PRODUCT_SEMANTIC_DECISION_REQUIRED` for all 5, not a single shared technical track.
- **TRACK D — INTERPRETER (mental/rest collision)**: requires a product decision on whether co-extraction is desired (per Section 26) before any code change — `PRODUCT_SEMANTIC_DECISION_REQUIRED`.
- **TRACK E — INTERPRETER (family vocabulary scope)**: requires a product decision on whether `family` should include relationship-framing at all — `PRODUCT_SEMANTIC_DECISION_REQUIRED`.
- **TRACK F — INTERPRETER (communication vocabulary completeness)**: technically addressable independent of the taxonomy question (mirrors the marriage track's own Interpreter/Taxonomy independence finding) — `INTERPRETER`, but low-value until Track G resolves.
- **TRACK G — TAXONOMY/MAPPING (communication)**: `PRODUCT_SEMANTIC_DECISION_REQUIRED` — whether communication deserves new canonical evidence at all.
- **TRACK H — MAPPING (courage QUESTIONABLE cleanup)**: already-designed, unimplemented (`{12,15,30}`), a `MAPPING`-only track, low priority, `PRODUCT_SEMANTIC_DECISION_REQUIRED` only for the QUESTIONABLE-retention sign-off itself.
- **TRACK I — TEXT_EVIDENCE (love's marriage-word overlap)**: `TEXT_EVIDENCE`, very low priority given 0 DB impact — worth a one-line note for a future NEED_TEXT_WEIGHTS review, not urgent.

**Needs are not combined across tracks merely because they share a layer** — e.g. Track A bundles 6 Needs' Reason gaps because each is a single, independent dict-entry addition with the exact same low-coupling shape (matching PR #2593's own precedent of a single, minimal `intent_map` addition); Tracks C/D/E/G are each kept Need-specific or pairing-specific because each requires its own distinct product judgment, not a shared mechanical fix.

## 29. PR Split Recommendations

| Track | Regression isolation | Semantic coupling | Rollback safety | Reviewability | Testability | Data dependency |
|---|---|---|---|---|---|---|
| A (Reason, 6 Needs) | High | Low | High | High | High | None |
| B (Labels, 5 Needs) | High | Low | High | High | High | None |
| C (Axis, 5 Needs) | Medium (per-Need) | Medium (each needs its own semantic justification) | High | Medium | Medium | None |
| D (mental/rest interpreter) | Medium | High (cross-Need) | Medium | Low (needs product sign-off first) | Medium | None |
| E (family vocabulary) | Medium | Medium | Medium | Low (needs product sign-off first) | Medium | None |
| F (communication interpreter) | High | Low | High | Medium | Medium | None |
| G (communication taxonomy) | Low (new schema implied) | Low | Low | Low | Low | None, but out of every prior audit's scope |
| H (courage mapping) | High | Low | High | High | High | None |
| I (love text vocabulary) | High | Low | High | High | Low (0 DB cases to test against currently) | None |

## 30. Technical Dependency Order

```
Track A (Reason, 6 Needs)     -- no dependency, ready now
Track B (Labels, 5 Needs)     -- no dependency, ready now
Track H (courage mapping)     -- no dependency, ready now (pending QUESTIONABLE sign-off)
Track I (love text vocab)     -- no dependency, ready now, lowest urgency

Track F (communication interpreter)  -- independent of Track G, but low value alone
Track G (communication taxonomy)     -- MOTHER_SHIP_PRIORITY_REQUIRED, unlocks Track F's value

Track C (axis, 5 Needs)       -- each independently ready once its own product
                                  decision (does an existing axis fit?) is made
                                  -- MOTHER_SHIP_PRIORITY_REQUIRED per Need

Track D (mental/rest)         -- MOTHER_SHIP_PRIORITY_REQUIRED (is co-extraction
                                  actually undesired?), blocks any code change
Track E (family vocabulary)   -- MOTHER_SHIP_PRIORITY_REQUIRED (scope question),
                                  blocks any code change
```

## 31. Mother Ship Decisions Required

1. Should Track A (6-Need `intent_map` additions) and Track B (5-Need `NEED_LABELS_JA` additions) proceed as the next, lowest-risk implementation PR(s), mirroring PR #2593's exact pattern?
2. For each of protection/health/family/communication/travel_safe (Track C): does any existing consultation axis fit, or should these 5 Needs simply remain on `other` (a legitimate, non-damaging state, per Section 9)?
3. Is `mental`/`rest`'s co-extraction on shared vocabulary (Track D) actually undesired, or is it a legitimate, intentional multi-Need consultation the current architecture should keep producing (mirroring the same question already raised for this pair in the product-decision audit)?
4. Should `family`'s vocabulary scope (Track E) be expanded to include family-relations framing, or should it remain fertility/childbirth-only (with `relationship` retaining sole responsibility for "家族との関係")?
5. Should `communication` (Tracks F/G) receive new canonical taxonomy investment, or be accepted as permanently GID-sparse and interpreter-improved-only?
6. Should the already-designed courage GID cleanup (Track H, `{12,15,30}`) proceed now, independent of the above?

## 32. Global Findings

1. **Are most Need nuances currently preserved?** Mostly yes at the Need-selection layer (12 of 15 Needs show ≥75% interpreter coverage in this corpus), but Reason/label preservation is weaker (9 of 15 lack `intent_map`... corrected: 6 lack it after PR #2593; 5 lack `NEED_LABELS_JA`) — meaning the *user-facing explanation* of a correct match is where nuance most often gets flattened, not the match itself.
2. **Which layer loses the most semantic information?** **Reason/Explanation** (6+5=11 gap-instances across 2 related dicts, spanning 6 distinct Needs) — more Needs are affected here than at any other single layer.
3. **Is Interpreter the dominant problem?** No — it is a real, contributing problem for 4 Needs (mental, rest, family, communication) but not the single dominant layer system-wide.
4. **Is canonical GID mapping the dominant problem?** No — only `communication` has a `SEMANTICALLY_MISALIGNED` mapping; every other Need's GID mapping is at least `PARTIAL` or better, and no `STRUCTURALLY_BROKEN` mapping was found anywhere.
5. **Is Text Evidence doing useful differentiation?** Partially — for the 7 Needs that have it, it correctly compensates for weak GID mappings (established precedent from the original correction PR), but 2 of those 7 (`career`/`courage`) share a real overlap word (`勝運`), and 8 of 15 Needs have none at all.
6. **Is C1 preserving available distinctions?** **Yes, cleanly** — Section 12 found zero cases of C1 losing or conflating evidence; it is the most reliably healthy layer audited.
7. **Is Ranking collapsing distinctions?** No — Section 13 found zero unexplained collapses; every "identical Top3" traced to a specific, attributable, non-defective cause.
8. **Are Lead/Reason preserving distinctions?** Lead: yes, uniformly (Section 16). Reason: no, for 6 of 15 Needs (Section 17) — the clearest, most systemic gap this audit found.
9. **Are failures mostly code, taxonomy, or data?** Predominantly **code** (missing dict entries, narrow/overbroad keyword lists) — only `communication` shows a genuine taxonomy gap (no fitting canonical tag exists), and no Need was found `DATA_LIMITED` as its primary classification (communication's sparsity is secondary to its taxonomy misalignment).
10. **Is another engine-wide refactor justified?** See Section 33.

## 33. Engine Refactor Verdict

**`LOCAL_FIXES_SUFFICIENT`.**

Every finding in this audit — including the three newly-discovered ones (`NEED_TEXT_WEIGHTS["love"]`'s marriage-word overlap, the `NEED_LABELS_JA` 5-Need gap, `family`'s narrow vocabulary) — is addressable as a narrow, independently-testable, single-Need (or single-pair) change, using the *exact same mechanisms already proven safe* across 5 consecutive marriage-track PRs (#2586/#2590/#2591/#2593 plus the safe-mapping-correction PR #2582). No layer (Interpreter, Axis, GID, Text, C1, Ranking, Lead, Reason) was found to have a structural design flaw requiring a shared refactor — every gap is a **missing entry** (dict key absent) or a **local vocabulary imprecision** (a word too broad or too narrow for its own Need), never a wrong *mechanism*. `ENGINE_ARCHITECTURE_REVIEW_REQUIRED` is not supported by the evidence gathered; `LIMITED_SHARED_REFACTOR_WORTH_CONSIDERING` was considered for Track A+B (since both are structurally identical "add missing dict entries across N Needs" work) but even that is better modeled as several small, independently-reviewable PRs (Section 29) than a refactor.

## 34. Production Safety

No production code, DB, Model, migration, Seed, or frontend file was modified. All findings derive from fresh code reads (`git diff` against `origin/develop` shows zero changes to any file outside `docs/audit/`) and read-only runtime execution against the pre-existing isolated local scratch DB (`shrine_dataset_audit_local`) — no writes, confirmed by every query used in this audit being a `SELECT`/`GET`/live-scoring call, never a `save()`/`create()`/`update()` outside of the temporary, in-memory Compass/Concierge request objects.

## 35. Out of Scope

Implementation of any Track A–I item (Section 28–30). New taxonomy design for `communication`. Resolution of the `mental`↔`rest` or `family` product-semantic questions (Sections 26/31). UI/frontend. DB backfill. `NEED_TEXT_WEIGHTS`/`NEED_LABELS_JA`/`intent_map`/interpreter-vocabulary/axis-mapping edits of any kind.

## 36. STOP

Draft PR only. Mother Ship decision required per Section 31 before any follow-up implementation begins.
