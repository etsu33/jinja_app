# Marriage → Love Alias Boundary Decision Audit

> **Status**: AUDIT / DECISION SUPPORT ONLY. `NEED_TAG_ALIASES`, `NEED_TO_GORIYAKU_IDS`, `NEED_TEXT_WEIGHTS`, consultation-axis mappings, interpreter keywords, C1, Ranking, Lead, Reason, Direction/Distance, Need/GoriyakuTag taxonomy, Production DB/Seed — all unchanged. No implementation.

## 1. Scope

Determine whether `NEED_TAG_ALIASES["marriage"] = "love"` should remain authoritative, or whether `marriage` should become an independently reachable Need. Builds on `docs/audit/remaining-product-decision-need-responsibilities.md`'s finding that `marriage` is a `DEAD_MAPPING` (`FULL_COLLAPSE` into `love`) due to this alias.

## 2. Base SHA

`origin/develop` at `32be25ff2a7cb37834ff73f2b5b797e2044b32bf` (`docs: audit remaining Need responsibility decisions (#2583)`). `git log --oneline d9fbf130..32be25ff`: single commit, PR #2583 only. Worktree: `/Users/morietsu/Developer/jinja_app-marriage-love-boundary`, branch `audit/marriage-love-alias-boundary`.

## 3. Sources of Truth

Fresh-read this session: `docs/audit/remaining-product-decision-need-responsibilities.md`, `docs/audit/remaining-need-goriyaku-semantic-mapping.md`, current `NEED_TAG_ALIASES` (both copies), current `need_to_goriyaku_tag_ids.py` (marriage/love/relationship confirmed unchanged), `consultation_axis.py`. **Newly, decisively fresh-read this session**: `backend/temples/tests/test_concierge_relationship_love_separation.py` (the actual PR #2409 test suite — not previously read in this audit chain) and `backend/temples/domain/need_tags.py` (`KEYWORDS`, `extract_need_tags`) and `backend/temples/services/concierge_chat_need.py` (`resolve_need_payload`). This last group of reads produced the audit's central correction (Section 5).

## 4. Current Semantic Definitions

| Need | Current semantic definition | Source |
|---|---|---|
| love | Romantic love-seeking: new encounters, romantic fulfillment, reconciliation | `need_tags.py` `KEYWORDS["love"]` (恋愛/恋/復縁/片思い/両思い/出会い/告白) and `consultation_interpreter.py` `NEED_KEYWORDS["love"]` (near-identical list) |
| marriage | Marriage-seeking and marriage-institution concepts: matchmaking toward marriage, marriage-focused dating (婚活), *and* existing marital harmony | `need_tags.py` `KEYWORDS["marriage"]` and `consultation_interpreter.py` `NEED_KEYWORDS["marriage"]` — **both independently define the identical list**: 縁結び/良縁/結婚/婚活/結縁/ご縁/夫婦円満 |
| relationship | Interpersonal relationships broadly: workplace, family, friends — explicitly not limited to or centered on romance | `need_tags.py` `KEYWORDS["relationship"]`, `consultation_axis.py`'s `relationship_repair` keyword list (家族との関係/職場の人間関係/友人との関係), and `test_concierge_relationship_love_separation.py`'s own PR #2409 rationale |

`marriage` **does** have an independent definition at the domain-keyword layer (two independent files agree on identical keywords) — it is not undefined, contrary to what a naive reading of "no `NEED_TAG_TO_CONSULTATION_AXIS` entry" might suggest.

## 5. Runtime Trace

**Critical correction to the prior audit's framing**: this codebase has two parallel need-extraction layers, and only one of them affects real ranking.

- `temples/services/consultation_interpreter.py` (`interpret_consultation`, `build_need_profile`) — its own docstring states: *"This service intentionally does not change recommendation ranking. It prepares structured input for debug payloads, Meaning Translation Layer, and future Score v3 shadow observation."* **Shadow-only.** The prior audit's Section 5/6 traced this layer and its conclusions about extraction remain factually accurate for *that layer's own behavior*, but this layer does not drive real Recommendation output.
- `temples/domain/need_tags.py` (`extract_need_tags`) → `temples/services/concierge_chat_need.py` (`resolve_need_payload`) — **this is the real, ranking-affecting path** for natural-language Concierge queries (`build_chat_recommendations` calls `resolve_need_payload` directly, confirmed at `concierge_chat.py:679`).
- For Compass (button-based purpose selection): `need_tags=[purpose_slug]` is fed directly into `_prefilter_candidates_for_need`/`_attach_breakdown`, which call `_normalize_need_tags()` in `concierge_chat_ranking.py` — a **third, independent copy** of the alias-consuming logic, confirmed unchanged and confirmed to still apply the alias (re-verified this session, matching the prior audit).

### love

```
"恋愛を成就させたい" → extract_need_tags() → raw=['love']
  → resolve_need_payload() → normalize_need_tags(['love']) → ['love']  (no-op, love is not an alias source)
  → consultation_axis: relationship_repair
  → GID {1,20} / Text (love has 9 words) → C1 → Ranking → Lead → Reason
```

### marriage

```
"結婚したい" → extract_need_tags() → raw=['marriage']   <- CORRECTLY DISTINCT from love here
  → resolve_need_payload() → normalize_need_tags(['marriage']) → ['love']   <- COLLAPSE POINT
  → consultation_axis: relationship_repair (same as love, since tag is now 'love')
  → GID {1,20} (love's set; marriage's own {1,27,29} never read)
  → C1 / Ranking / Lead / Reason all operate on 'love' evidence, indistinguishable from a real love query
```

**The collapse point is precisely and only `resolve_need_payload`'s / `_normalize_need_tags`'s call into `NEED_TAG_ALIASES`** — extraction upstream is correct; the alias table is the sole point of information loss.

### relationship (control)

```
"人間関係を見直したい" → extract_need_tags() → raw=['relationship']
  → resolve_need_payload() → normalize_need_tags(['relationship']) → ['relationship']   <- no collapse, confirmed
  → consultation_axis: relationship_repair
  → GID {1} → ... → Lead → Reason (relationship-specific, per PR #2409's test suite)
```

## 6. Alias Authority

Full current `NEED_TAG_ALIASES` table (fresh-read, both copies confirmed identical):

| Alias | Source Need | Target Need | Surface synonym? | Semantic collapse? |
|---|---|---|---|---|
| marriage | (English token "marriage") | love | Contested — see below | Yes, confirmed (Section 5) |
| romance | (English token "romance") | love | Yes — "romance" is a plain English synonym of "love," no independent Japanese keyword list exists for it | Not applicable (no independent concept to lose) |
| anxiety | (English token "anxiety") | mental | Yes | Not applicable |
| healing | (English token "healing") | rest | Yes | Not applicable |
| career_change | (English token) | career | Yes | Not applicable |
| work | (English token) | career | Yes | Not applicable |
| fortune | (English token) | money | Yes | Not applicable |
| challenge | (English token) | courage | Yes | Not applicable |
| ambition | (English token) | courage | Yes | Not applicable |
| success | (English token) | courage | Yes | Not applicable |

**The table's design intent (A: surface/spelling synonyms of English tokens an LLM or user might emit, canonicalized to the matching Japanese-keyword-driven Need) holds cleanly for every entry except `marriage`.** Every other alias source (romance/anxiety/healing/career_change/work/fortune/challenge/ambition/success) has **no independent Japanese keyword list of its own** in either `need_tags.py` or `consultation_interpreter.py` — they are purely English-token spelling variants with nothing to lose by aliasing. `marriage` is the **sole exception**: it has its own, real, independently-defined Japanese keyword list (Section 4) that is discarded by the alias. This makes `marriage → love` structurally inconsistent with the alias table's own design pattern (B: semantic normalization across distinct intents), even though the existing test suite's comment (Section 7) frames it as intended to be category A.

## 7. Natural Language Cases

Traced via the real, ranking-affecting path (`extract_need_tags` → `resolve_need_payload`), not the shadow layer:

| Query | Raw extracted | After alias (real path) | Consultation axis |
|---|---|---|---|
| 新しい出会いがほしい | `['love']` | `['love']` | relationship_repair |
| 恋愛を成就させたい | `['love']` | `['love']` | relationship_repair |
| 復縁したい | `['love']` | `['love']` | relationship_repair |
| 結婚したい | `['marriage']` | `['love']` | relationship_repair |
| 結婚につながる良縁がほしい | `['marriage']` | `['love']` | relationship_repair |
| **夫婦関係を整えたい** | **`['mental', 'rest']`** | **`['mental', 'rest']`** | restart_mindset, rest_healing |
| 人間関係を見直したい | `['relationship']` | `['relationship']` | relationship_repair |

**Unexpected, significant new finding**: `夫婦関係を整えたい` ("want to improve our marital relationship") — a query about an *existing* marriage, not marriage-seeking — extracts **neither `marriage`, `love`, nor `relationship`**. It is captured entirely by `mental`/`rest`'s literal keyword overlap on "整えたい" (already documented as a cross-Need collision in the prior audit, Section 10/13 there). This means: for this entire class of marriage-relevant query (existing-marriage maintenance, as opposed to marriage-seeking), **the alias question is never even reached** — the interpreter routes it elsewhere first. This is evidence the alias is not the *only* barrier to marriage-relevant recommendations; interpreter coverage is a separate, prior gap for at least one real query pattern.

## 8. Extraction Comparison

**Classification: `MIXED`.**

- `結婚したい` / `結婚につながる良縁がほしい`: **`DISTINGUISHABLE_BEFORE_ALIAS`** — `extract_need_tags` cleanly and correctly separates these from `love`-only phrasing (Section 7); the alias is the sole point of collapse.
- `夫婦関係を整えたい`: **neither distinguishable nor collapsed — never extracted as marriage-related at all** (a distinct, upstream interpreter-coverage gap, not an alias effect).
- General love phrasing (新しい出会い/恋愛/復縁): cleanly stays `love`, never touches `marriage`'s keyword list at all — no ambiguity here.

## 9. Evidence Comparison

| Layer | love | marriage |
|---|---|---|
| Current GID mapping | `{1, 20}` | `{1, 27, 29}` (unchanged; never read at runtime, Section 5) |
| Canonical labels | 縁結び, 恋愛成就 | 縁結び, 出世運, 芸能運 |
| DB shrine counts | 1→32, 20→4 (36 total refs) | 1→32, 27→2, 29→3 (37 total refs, but 27/29 fresh-classified INVALID, Section 10) |
| Text Evidence | 9 words, real | none |
| Matched candidates (this fixture, Section 12) | 東京大神宮/明治神宮/赤坂氷川神社, all via love text evidence | Same 3 shrines when aliased (Section 12-A); different, partly-wrong Top3 when unaliased with the current unfixed mapping (Section 12-B) |

## 10. Canonical Marriage Evidence

Fresh classification, not inherited from prior audits:

| Tag | Label | Classification |
|---|---|---|
| 1 | 縁結び | **SHARED** — good-connections concept applies to love-seeking, marriage-seeking, and general relationship-building alike; already an accepted 3-way shared pattern in the codebase |
| 20 | 恋愛成就 | **LOVE_CORE** — specifically romantic fulfillment/dating success, not marriage-as-institution |
| **18** | **夫婦円満** | **MARRIAGE_CORE** — the single clearest marriage-specific canonical label in the entire 39-row master (existing marital harmony, not romance-seeking). **Currently misassigned to `courage` (INVALID there, confirmed in the prior audit), unused by `marriage` itself** |
| 27 | 出世運 | not marriage-related — career advancement |
| 29 | 芸能運 | not marriage-related — performing-arts luck |
| — | (「良縁」as a standalone tag) | Does not exist as its own `GoriyakuTag` — 良縁 is interpreter/keyword vocabulary only, mapped in practice via id=1 |

## 11. DB Coverage

- love-relevant evidence: id=1 (32 shrines) + id=20 (4 shrines) = substantial, and id=1 is shared with marriage
- marriage-specific evidence (id=18 only, since 27/29 are not marriage-relevant): **1 shrine**
- shared evidence (id=1): 32 shrines

**Classification: `SPARSE`** for genuinely marriage-*distinct* evidence. An independent marriage Need would be structurally reachable and would produce real output (via the shared id=1), but would almost never diverge from `love`'s own Top3 in practice — only 1 shrine nationwide (id=18) carries evidence that could differentiate a marriage-specific result from a love-specific one, and that shrine did not appear in this audit's fixed test fixture (Section 12-C confirms this empirically: even the "fixed" `{1,18}` mapping produced a Top3 driven entirely by shared id=1, identical in composition to what id=1 alone would produce).

## 12. Current Alias Baseline (Counterfactual A)

Read-only `patch.dict` simulation, live `get_compass_recommendations(purpose="marriage", ...)`, fixed origin/direction (identical fixture used throughout this audit chain):

```
Top3: 東京大神宮 / 明治神宮 / 赤坂氷川神社
matched=['love'] for all three, winner={'love': 'text'}
Reason: "縁結びのご利益で知られる東京大神宮は、恋愛や良縁を願う参拝先として適しています。"
```

**Identical in composition, ordering, and reason text to a direct `purpose="love"` control run** (re-confirmed this session) — empirically confirms `FULL_COLLAPSE`, not merely structurally inferred.

## 13. Remove-Alias Simulation (Counterfactuals B & C)

**B — alias removed only, current unfixed mapping `{1,27,29}` retained:**

```
Top3: 明治神宮 / 花園神社 / 赤坂氷川神社
matched=['marriage'] for all three (marriage IS now reachable)
花園神社 matches via id=29 (芸能運, INVALID) -- "芸能運のご利益で知られる花園神社は、今の願いを願う参拝先として適しています。"
明治神宮/赤坂氷川神社 match via id=1 (VALID) but get GENERIC reason copy
  ("今の願いを願う参拝先として") -- not love's "恋愛や良縁を願う" flavor, because
  no intent_map/Reason entry exists for "marriage" (same gap `protection` had before its own fix)
```

Alias removal alone makes `marriage` reachable but surfaces a real wrong match (id=29) and produces generic, non-marriage-flavored Reason copy even for correct matches.

**C — alias removed + mapping fixed to `{1, 18}` (VALID + CLEAR_MISSING, mirroring the prior semantic-mapping audit's already-computed candidate):**

```
Top3: 明治神宮 / 赤坂氷川神社 / 芝大神宮
matched=['marriage'] for all three, all via id=1 (this fixture's candidate pool
  happens to contain no id=18-carrying shrine -- expected, only 1 exists nationwide, Section 11)
Reason: still generic ("今の願いを願う参拝先として") -- the Reason-copy gap
  persists regardless of mapping correctness; it is a separate, EXPLANATION-layer gap
```

**Candidate count / Direction count / Distance count**: identical across A/B/C/control (all `state=recommendation_success`, `count=3`) — confirms this simulation did not and could not touch Direction/Distance (same candidate pool reused throughout, only `purpose`/mapping/alias varied).

## 14. Marriage Mapping Assessment

Fresh-verified against the current 39-row master (not inherited):

| ID | Classification |
|---:|---|
| 1 | **VALID** |
| 27 | **INVALID** |
| 29 | **INVALID** |

**1 VALID, 0 QUESTIONABLE, 2 INVALID.** The current `{1, 27, 29}` mapping is not semantically acceptable as-is even if made reachable — Counterfactual B (Section 13) demonstrates this concretely (a real, visible wrong match via id=29 in this fixture).

## 15. Boundary Quality

**love vs marriage**: Candidate overlap is total under the current alias (Section 12). Under a corrected, unaliased mapping (Section 13-C), overlap remains very high in practice (both draw overwhelmingly on shared id=1, per Section 11's DB sparsity finding) but the underlying *evidence set* is no longer identical (marriage would draw only on `{1,18}`, never on love's `{20}` 恋愛成就). Reason text would need independent copy to actually read as marriage-flavored rather than love-flavored.

**Result: `MEANINGFUL_PARTIAL_SEPARATION`** — not `WELL_SEPARATED` (evidence is too thin and too shared to reliably diverge in practice), not `REDUNDANT` (id=18 is a real, distinct, if sparse, differentiator that legitimately belongs only to marriage), not `SEMANTICALLY_WRONG` (the concept itself — marriage as distinct from general romantic love-seeking — is real and independently confirmed at the domain-keyword layer, Section 4).

**marriage vs relationship**: No shared GID currently (`relationship={1}` post-correction, `marriage={1,27,29}` — actually id=1 IS shared with relationship too, re-checked). Keyword lists are fully distinct (no literal overlap found between `NEED_KEYWORDS["marriage"]` and `NEED_KEYWORDS["relationship"]`). `relationship`'s own scope (per Section 4 and PR #2409's own documented rationale) is explicitly broader than romance — workplace/family/friends — while `marriage` is romance/matrimony-specific. **Result: `WELL_SEPARATED`** — no evidence of confusion between these two at any layer checked.

## 16. Product Meaning

Per current product copy/contracts (no new design performed): a user selecting or expressing `marriage` intent would, per the domain keyword list itself (結婚/婚活/夫婦円満), reasonably expect either (a) matchmaking specifically oriented toward marriage (as opposed to casual dating) or (b) support/harmony for an *existing* marriage — both meaningfully different from `love`'s scope (new encounters, general romantic fulfillment, reconciliation). No current Reason/Lead copy distinguishes these expectations from `love`'s (Section 13).

**Result: `PARTIAL_DISTINCTION`.** The domain/keyword layer documents a real, existing distinction (not `NO_DOCUMENTED_DISTINCTION`); it is not fully contradictory (not `CONTRADICTORY_DEFINITIONS` — the alias-layer rationale and the keyword-layer definition don't directly contradict, they simply operate at different granularity: the alias table was designed to canonicalize English *tokens*, while the keyword lists independently capture Japanese *concepts*); but the distinction is not fully "existing" in a product sense either, since it has never been surfaced end-to-end (Reason copy, Section 13) and one entire query pattern (existing-marriage maintenance, Section 7) doesn't even reach either concept today.

## 17. Consultation Axis

`marriage` currently has no `NEED_TAG_TO_CONSULTATION_AXIS` entry. Its content (marriage-seeking specifically) is a natural subset of what `relationship_repair` already documents as in-scope (`CONSULTATION_AXIS_KEYWORDS["relationship_repair"]` already includes relationship-adjustment language broadly, and the axis is already explicitly shared by `love` and `relationship` today, per the existing code comment cited in the prior audit).

**Result: `CURRENT_AXIS_REUSABLE`** (`relationship_repair`) — no new axis would be required if `marriage` became independent.

## 18. Reason / Lead Feasibility

Section 13 (Counterfactuals B/C) empirically confirms: even with a correct GID match (via id=1 or id=18), `marriage` currently falls back to the generic "今の願いを願う参拝先として" phrasing rather than a marriage-flavored equivalent of love's "恋愛や良縁を願う". This mirrors the exact, already-documented gap `protection` had before its own `intent_map` situation was assessed in an earlier audit this session. Adding a `marriage`-specific entry to the existing `intent_map`/`_build_need_lead` fallback structure would follow an established, low-risk, already-proven pattern (not a redesign of the Reason system).

**Result: `MINOR_COPY_GAP`.**

## 19. Options

- **Option A (Keep alias)**: `marriage` remains a UI/input synonym of `love`. Semantic fidelity: low for marriage-seeking-specific and existing-marriage queries (Section 15/16), though DB sparsity (Section 11) means the *practical* output difference would often be small even if fixed. Backward compatibility: perfect (status quo). Ranking churn: none. Implementation complexity: none. Product clarity: low (a real, keyword-documented distinction is silently discarded). Data sufficiency: irrelevant (never reached). Regression risk: none.
- **Option B (Remove alias only)**: uses current `{1,27,29}` mapping as-is. Semantic fidelity: **worse than Option A in one respect** — Section 13-B shows a real wrong match (id=29) would surface. Not recommended standalone.
- **Option C (Remove alias + correct mapping, e.g. `{1,18}`)**: Semantic fidelity: meaningfully better than A for marriage-seeking queries reaching `marriage` correctly; still generic Reason copy without Section 18's minor addition. Backward compatibility: `love`-only test coverage (`test_love_synonym_aliases_are_unchanged`, parametrized over `["marriage", "romance"]`) would need explicit, deliberate updating — not silent breakage, since that test directly asserts the current behavior and any alias change must consciously revise it. Ranking churn: `EXPECTED_SEMANTIC_CHURN` only (Section 20). Implementation complexity: low (mirrors the already-executed `travel_safe`/safe-Need-mapping correction pattern). Data sufficiency: SPARSE (Section 11) — real but thin. Regression risk: low, contingent on also fixing Section 7's separate interpreter-coverage gap for existing-marriage queries not being mistaken for "the fix didn't work."
- **Option D (Remove marriage as an independent Need concept, conceptual only)**: Would formalize what the alias already does today — collapse marriage fully into love, but explicitly at the taxonomy/domain-keyword level too (not attempted or recommended; conflicts with constraint #11 "do not add a new Need" only in the reverse direction, and would require removing `need_tags.py`'s independent marriage `KEYWORDS` entry, itself a non-trivial domain-layer change, not evaluated further here as it was not requested to be implemented).

## 20. Regression Impact

For Option C specifically (the only option with a defined implementation path):

- Affected extraction fixtures: `test_concierge_relationship_love_separation.py`'s `test_love_synonym_aliases_are_unchanged` (parametrized `["marriage", "romance"]`) would need its `"marriage"` case explicitly removed/revised — a deliberate, visible test change, not silent breakage. `test_marriage_keyword_phrasing_still_resolves_to_love_via_unchanged_alias` would need renaming/reworking entirely, since its premise (marriage stays aliased) would no longer hold.
- Affected ranking fixtures: `test_need_to_goriyaku_tag_ids.py`'s existing `marriage == {1,27,29}` pin would need updating to the corrected set.
- Likely Top3 churn: `EXPECTED_SEMANTIC_CHURN` only, per Section 13's own empirical measurement (id=29's false match disappears; correct id=1/id=18 matches replace it) — no `UNEXPECTED_RISK` observed in this audit's simulation.
- Reason churn: would require the Section 18 copy addition to avoid a *visible regression in polish* (marriage queries would resolve correctly but read generically) — `EXPECTED`, not risky, but incomplete without it.
- Lead churn: not separately measured; expected to follow the same GID-evidence-first pattern already governing every other Need (`_resolve_matched_lead_evidence`), unchanged code path.

## 21. Decision

**`PRODUCT_SEMANTIC_DECISION_REQUIRED`.**

Not `KEEP_MARRIAGE_ALIAS_TO_LOVE`: the domain-keyword layer (two independently-maintained files, Section 4) demonstrably and deliberately treats marriage as distinct, and a real, unused, marriage-specific canonical tag (`夫婦円満`, id=18) exists in the master today — dismissing this as "already decided" would not account for evidence gathered since PR #2409's own comment was written (constraint #21 explicitly warns against assuming the status quo is correct merely because legacy code does so).

Not `REMOVE_ALIAS_USE_EXISTING_MAPPING` (Option B): Section 13-B demonstrates this alone produces a real regression (a wrong id=29 match) relative to today's at-least-consistent (if semantically mislabeled) love-collapse behavior.

Not `REMOVE_ALIAS_AND_FIX_MAPPING` (Option C) as an immediate, unconditional recommendation: while technically ready (Section 13-C, 20), Section 7's discovery — that a real class of marriage-relevant query (`夫婦関係を整えたい`, existing-marriage maintenance) never reaches `marriage` at all today, regardless of the alias — means fixing only the alias+mapping would not deliver the full, intuitively-expected marriage experience, and Section 11's DB sparsity means the practical, user-visible improvement from Option C alone would be modest (mostly reusing `love`'s own shared id=1 evidence). Implementing Option C without acknowledging this limits its value and could be mistaken for "marriage is now fully fixed" when it is not.

The genuinely open product question — is `marriage` (as scoped by its own keyword list: seeking-marriage *and* existing-marriage-harmony) valuable enough to the product to justify (a) de-aliasing, (b) the Section 18 copy work, and (c) a separate interpreter-coverage fix for existing-marriage phrasing, given (d) currently sparse distinguishing DB evidence — is a Mother Ship call this audit surfaces with full technical grounding but does not make.

## 22. Follow-up Scope

**If Mother Ship approves de-aliasing (Option C)**, the smallest implementation PR:

- `backend/temples/services/concierge_chat_ranking.py`: remove `"marriage": "love"` from `NEED_TAG_ALIASES`
- `backend/temples/services/concierge_chat_need.py`: remove `"marriage": "love"` from its independent copy of `NEED_TAG_ALIASES`
- `backend/temples/domain/need_to_goriyaku_tag_ids.py`: `"marriage": {1, 27, 29}` → `{1, 18}`
- Deliberately update `test_concierge_relationship_love_separation.py`'s `test_love_synonym_aliases_are_unchanged` (drop `"marriage"` from its parametrization, keep `"romance"`) and rework/rename `test_marriage_keyword_phrasing_still_resolves_to_love_via_unchanged_alias`
- Update `test_need_to_goriyaku_tag_ids.py`'s `marriage == {1,27,29}` pin
- **Optionally, in the same or a follow-on PR**: a minimal `intent_map`/`_build_need_lead` fallback entry for `marriage` (Section 18) to avoid the generic-Reason gap

**Separately, regardless of the above**: an interpreter-coverage audit/fix for existing-marriage phrasing (`夫婦関係`-type queries currently misrouted to `mental`/`rest`, Section 7) — independent of the alias decision, its own follow-up track, out of scope for this specific PR.

## 23. Mother Ship Decision Inputs

1. Is the marriage-seeking vs existing-marriage-harmony distinction (Section 4/16) valuable enough to the product to de-alias, given DB evidence is currently SPARSE (Section 11) and the practical Top3 difference from `love` would often be small?
2. If yes: authorize the Section 22 implementation PR (alias removal + mapping fix + test updates)?
3. Should the Section 18 Reason-copy addition ship in the same PR, or as an immediate follow-on (to avoid shipping a "technically correct but reads generic" intermediate state)?
4. Should the Section 7 interpreter-coverage gap (`夫婦関係を整えたい` misrouted to mental/rest) be tracked as a dependent or independent follow-up?
5. Is `id=18`'s current misassignment to `courage` (INVALID there, per the prior semantic-mapping audit) itself worth flagging for that audit's own eventual follow-up, independent of this marriage decision?

## 24. Limitations

- This audit's Section 21 Decision reflects the evidence gathered, not a resolution of the underlying product question — genuinely reasonable people could weigh Section 11's DB sparsity more heavily toward `KEEP_MARRIAGE_ALIAS_TO_LOVE`, or weigh Section 4/10's domain-keyword evidence more heavily toward `REMOVE_ALIAS_AND_FIX_MAPPING`; this audit presents both sides with equal rigor rather than picking one.
- The counterfactual simulations (Sections 12/13) used a single fixed origin/direction fixture (consistent with every prior correction PR in this audit chain for comparability) — different fixtures could surface `id=18`'s real (if sparse) differentiating effect, not observed here due to its single-shrine nationwide presence.
- Section 7's `夫婦関係を整えたい` finding was discovered via this audit's own required test-case list; a systematic sweep of all plausible existing-marriage phrasings was not performed.
- `resolve_need_payload`'s behavior was verified directly (not via a full HTTP/API round-trip); the Compass path (`get_compass_recommendations`) was verified via its own orchestrator function directly, consistent with every prior audit in this chain.

## 25. Out of Scope

`communication`, `mental`, `courage` (per the immediately preceding audit, unaddressed here), UI/frontend, new taxonomy, Production DB mutation, unrelated mapping cleanup (e.g. `id=18`'s misassignment to `courage` is noted but not corrected here — that belongs to the separate 8-Purpose semantic-mapping follow-up already recommended in an earlier audit).
