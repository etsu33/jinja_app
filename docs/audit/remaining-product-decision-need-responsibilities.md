# Remaining Product-Decision Need Responsibility Audit

> **Status**: AUDIT ONLY. `NEED_TO_GORIYAKU_IDS`, `NEED_TAG_ALIASES`, `NEED_TEXT_WEIGHTS`, consultation-axis logic, interpreter vocabulary, C1, Ranking, Lead, Reason, Direction, Distance, Need/GoriyakuTag taxonomy, Production DB/Seed — all unchanged. No implementation.

## 1. Scope

For each of the 4 Need tags deliberately excluded from the safe Mapping correction (PR #2582) — `marriage`, `communication`, `mental`, `courage` — determine which architectural layer (MAPPING / ALIAS / TAXONOMY / TEXT_COVERAGE / INTERPRETER / EXPLANATION / DATA / MULTI_LAYER) owns the primary unresolved problem, and define the smallest safe next audit/implementation scope per Need. `love`, `career`, `money`, `study`, `protection`, `travel_safe`, `relationship`, `health`, `focus`, `family` are not reopened.

## 2. Base SHA

`origin/develop` at `d9fbf13040332e8d9277424c0e1fb32576b0ec34` (`fix: correct safe remaining Need mappings (#2582)`), after that PR was found still open/draft (CI-green) at this task's Phase 0 and merged with explicit Mother Ship authorization. `git log --oneline 6460bab0..d9fbf130`: single commit, PR #2582 only. Worktree: `/Users/morietsu/Developer/jinja_app-remaining-product-needs-audit`, branch `audit/remaining-product-decision-needs`.

## 3. Sources of Truth

Fresh-read this session: `need_to_goriyaku_tag_ids.py` (confirmed identical to PR #2582's shipped state — `relationship={1}`, `health={7,8,24,33,38}`, `focus={9,10}`, `family={2,26,34}`; `marriage/communication/mental/courage` unchanged), `NEED_TAG_ALIASES` (both copies), `consultation_axis.py`, `NEED_TEXT_WEIGHTS`. **Newly fresh-read this session** (not previously inspected in this audit chain): `backend/temples/services/consultation_interpreter.py` — `NEED_KEYWORDS` (the actual free-text → need_tag extraction vocabulary, upstream of everything else) and `build_need_profile()`'s multi-match behavior. This is the layer highest in the pipeline and turned out to hold the most consequential new evidence in this audit (Sections 5, 9).

## 4. Current State Matrix

| Need | GID Mapping | Alias | Text Coverage | Consultation Axis | DB GID Evidence (sum of shrine counts across mapped ids) |
|---|---|---|---|---|---:|
| marriage | `{1, 27, 29}` | **`marriage → love`** | none | not present in `NEED_TAG_TO_CONSULTATION_AXIS` | 32+2+3=37 (but never consulted, Section 5) |
| communication | `{30, 33, 37, 39}` | none | none | not present | 1+1+1+1=4 |
| mental | `{11, 16, 26, 28, 38}` | none | 9 words | `restart_mindset` (shared with `courage`) | 19+5+1+2+1=28 |
| courage | `{12, 15, 18, 20, 24, 30, 38}` | none | 8 words | `restart_mindset` (shared with `mental`) | 11+1+1+4+1+1+1=20 |

## 5. Marriage Runtime Trace

Traced end-to-end with live code, query `"結婚したい"` ("I want to get married"):

```
"結婚したい"
  → build_need_profile(): NEED_KEYWORDS["marriage"] contains "結婚" → extracted=['marriage'], primary='marriage'
  → _normalize_need_tags(['marriage']) → NEED_TAG_ALIASES["marriage"]="love" → ['love']
  → need_tags_to_goriyaku_ids(['love']) → {1, 20}   (marriage's own {1,27,29} never queried)
  → _attach_breakdown() computes matched_by_gid/matched_by_text against 'love' only
  → C1 / Ranking / Lead / Reason all operate on 'love' evidence
```

**Confirmed empirically**: `interpret_consultation(query="結婚したい", ...)`'s `need_profile.need_tags == ['marriage']` (the interpreter correctly and distinctly recognizes marriage-specific phrasing — see Section 6), but `_normalize_need_tags(['marriage'], max_tags=10) == ['love']` and the resolved GID set is `{1, 20}` (love's set), not `{1, 27, 29}` (marriage's own, unchanged, entry). `NEED_TAG_ALIASES["marriage"] = "love"` is confirmed still present and still applied at the exact point identified in the prior audit (`_normalize_need_tag()`, consumed by both `_attach_breakdown()` and `_prefilter_candidates_for_need()`).

**Classification: `DEAD_MAPPING`.** Not merely `SHADOWED_BY_ALIAS` (which would suggest partial reachability) — the alias fires unconditionally on every `"marriage"` tag, before any GID or Text lookup, so `NEED_TO_GORIYAKU_IDS["marriage"]` and any future `NEED_TEXT_WEIGHTS["marriage"]` entry are 100% unreachable at runtime today.

## 6. Marriage Boundary

| Query | Extracted Need | Alias result | Consultation axis | Resolved GIDs | Top-level evidence |
|---|---|---|---|---|---|
| `結婚したい` | `marriage` | `love` | (marriage: none defined; love: `relationship_repair`) | `{1, 20}` | love's own evidence |
| `結婚につながる良縁がほしい` | `marriage` | `love` | same | `{1, 20}` | love's own evidence |
| `恋愛を成就させたい` | `love` (directly, not via marriage) | `love` (no-op, already love) | `relationship_repair` | `{1, 20}` | love's own evidence |

The interpreter genuinely distinguishes the two concepts at extraction time — `NEED_KEYWORDS["marriage"]` ("結婚"/"婚活"/"夫婦円満"/etc.) is a real, distinct keyword set from `NEED_KEYWORDS["love"]` ("恋愛"/"恋"/"復縁"/"片思い"/"出会い"/"告白"). But by the time any evidence is resolved, both queries land on identical `{1, 20}` GIDs, identical candidate scoring, and (per the codebase's own comment cited in the prior audit) identical love-themed Reason copy.

**Result: `FULL_COLLAPSE`** for `marriage` specifically — not `PARTIAL_COLLAPSE`. (The prior audit's `PARTIAL_COLLAPSE` finding referred to the `relationship`+`marriage`+`love` trio together, correctly noting `relationship` stays separate; isolating `marriage` alone against `love`, as this task requires, the collapse is complete and unconditional.)

## 7. Communication Current Evidence

Current mapping `{30, 33, 37, 39}` = 強運厄除け/病気平癒/延命長寿/農業守護 — none semantically related to communication (re-confirmed, unchanged from the prior semantic audit's classification, all 4 INVALID). No canonical tag among the 39-row master denotes "communication," "conversation," "speech," or "expressing oneself" in any form (re-verified this session by scanning the full label list, Section 4 of `goriyaku-mapping-master-integrity.md`). Shrine counts for the 4 current (wrong) ids: 1 each, 4 total — sparse and irrelevant regardless.

No `NEED_TEXT_WEIGHTS["communication"]` entry exists. `NEED_KEYWORDS["communication"] = ("会話", "発信", "伝える", "話す", "営業", "交渉", "プレゼン", "面接")` **does** exist and is a real, distinct interpreter vocabulary — but see Section 8 for its practical coverage gaps.

**Result: `MULTI_LAYER`** — `NO_CANONICAL_EVIDENCE` (taxonomy) **and** interpreter-vocabulary gaps (Section 8) are both independently confirmed, not merely theorized.

## 8. Communication Runtime

| Query | Extracted Need | Reason |
|---|---|---|
| `人とうまく話せるようになりたい` ("want to become able to talk well with people") | **none** (`extracted=[]`) | No `NEED_KEYWORDS["communication"]` entry matches — the query uses the conjugated form "話せる" (potential form), not the dictionary form "話す" that the keyword list contains; substring matching does not bridge the two |
| `職場でのコミュニケーションを改善したい` ("want to improve workplace communication") | **`relationship`** (not `communication`) | Contains "職場" (workplace), which is in `NEED_KEYWORDS["relationship"]`, not in `NEED_KEYWORDS["communication"]`. Critically, **the katakana word "コミュニケーション" itself is not in `NEED_KEYWORDS["communication"]`** — a query containing the Need's own name, almost verbatim, is silently routed to a different Need entirely |

Both representative queries fail to reach `communication`'s own mapping at all — one produces zero evidence, the other produces `relationship`'s evidence instead. **A Mapping-only fix is not possible with the current canonical master** (Section 7 — no fitting label exists) **and would not even be reached** by either tested query under the current interpreter vocabulary.

## 9. Mental Evidence Boundary

`NEED_TEXT_WEIGHTS["mental"]` (9 words), classified:

| Word | Class |
|---|---|
| 心を整える | MENTAL_CORE |
| 不安 | MENTAL_CORE |
| 落ち着く | MENTAL_CORE |
| 静か | **AMBIGUOUS** — identical word appears in `NEED_TEXT_WEIGHTS["rest"]` too (confirmed by direct comparison) |
| 厄除 | **PROTECTION_ADJACENT** |
| 厄払い | **PROTECTION_ADJACENT** |
| 浄化 | **PROTECTION_ADJACENT** |
| 守護 | **PROTECTION_ADJACENT** |
| 守ってほしい | **PROTECTION_ADJACENT** |

4 of 9 words (44%) are PROTECTION_ADJACENT; 1 of 9 is AMBIGUOUS with `rest`. Only 3 of 9 are unambiguously MENTAL_CORE. Current GID mapping `{11, 16, 26, 28, 38}` — re-verified against the prior semantic audit's classification (0 VALID / 2 QUESTIONABLE [11, 26] / 3 INVALID [16, 28, 38]) — confirmed unchanged, and confirmed to **not itself contain** the protection-specific tag (`2`, 厄除け, which is correctly VALID for `protection`'s own mapping). So mental's remaining problem is **not primarily Mapping** (the GID layer, while weak, doesn't literally duplicate `protection`'s tag) — it is primarily **Text Evidence and Interpreter vocabulary**, both of which genuinely blend mental with protection and with rest (Section 10 confirms this empirically).

## 10. Mental Runtime

| Query | Extracted Need(s) | Resolved GIDs (union) | Notes |
|---|---|---|---|
| `不安を落ち着かせたい` | `['mental']` only | `{11,16,26,28,38}` | Clean, unambiguous — matches only mental's own (weak) mapping |
| `気持ちを整えたい` | **`['mental', 'rest']`** | `{7,8,11,16,26,28,38}` | `NEED_KEYWORDS["mental"]` and `NEED_KEYWORDS["rest"]` both literally contain "整えたい"/"心を整えたい" — confirmed real, not hypothetical, interpreter-layer collision |
| `厄を払って気持ちを切り替えたい` | **`['mental', 'protection']`** | `{2,11,16,26,28,32,38}` | `NEED_KEYWORDS["protection"]` contains "厄"; `NEED_KEYWORDS["mental"]` contains "気持ちを切り替えたい" — confirmed real interpreter-layer collision, and this time it *does* pull in `protection`'s own `厄除け`(id=2) into the resolved GID union (via the co-extracted `protection` tag, not via mental's own set) |

**Result**: protection-adjacent vocabulary causes genuine semantic leakage — not because `mental`'s own GID mapping contains protection tags (it doesn't), but because the **interpreter** frequently co-extracts `mental` alongside `protection` (and separately alongside `rest`) on realistic queries, and the resulting candidate evidence is a *union* of both Needs' GID sets, not a disambiguated single Need. This is evidence at a different, upstream layer than the GID-mapping-only analysis the prior audit performed.

## 11. Courage Evidence Boundary

Current mapping `{12, 15, 18, 20, 24, 30, 38}` = 仕事運/武運長久/夫婦円満/恋愛成就/健康長寿/強運厄除け/足腰健康 — re-confirmed unchanged, re-confirmed against the prior audit's classification (0 VALID / 3 QUESTIONABLE [12,15,30] / 4 INVALID [18,20,24,38]). `NEED_TEXT_WEIGHTS["courage"]` (8 words: 開運/開運祈願/勝運/運を開く/背中を押して/一歩踏み出す/勇気/変わりたい) and `NEED_KEYWORDS["courage"]` (interpreter, 22 phrases including 決断/挑戦/一歩/勇気/変わりたい/踏み出す/前に進/開運/開運祈願/運を開きたい/行動/きっかけ/前向きになりたい, plus 自由に働きたい/会社に縛られたくない which read as independence-flavored) were both fresh-read.

Per current runtime/contracts (not invented): `courage` = **challenge/action-taking** (決断・挑戦・一歩・行動・前向き), reinforced by `NEED_TAG_TO_CONSULTATION_AXIS["courage"] = "restart_mindset"` and that axis's own history-theme weighting (再出発 1.0, 勝負 0.8, 静寂 0.6 — "fresh start," secondarily "competitive drive"). It is **not**, per the runtime's own definitions, primarily about "victory" (勝運/勝負 are only a secondary sub-theme, weight 0.8, not the axis's primary meaning) nor "general fortune" (開運 appears in the interpreter/text vocabulary but is shared broadly across `career` too) nor "confidence" as a standalone concept (勇気 appears once; no dedicated confidence-framing vocabulary exists).

## 12. Courage Runtime

| Query | Extracted Need | Resolved GIDs |
|---|---|---|
| `新しいことに挑戦したい` | `['courage']` | `{12,15,18,20,24,30,38}` |
| `勇気を出したい` | `['courage']` | `{12,15,18,20,24,30,38}` |
| `勝負に勝ちたい` | **`[]` — no extraction at all** | — |

The first two cleanly and exclusively extract `courage` — no interpreter-level collision observed for these direct phrasings (unlike `mental`). The third, a victory/competition-framed query, produces **zero extraction anywhere in the system** — not merely a weak match, but no `NEED_KEYWORDS` entry (courage's own or any other) contains "勝負" or "勝ちたい"/"勝つ" in any form. This reveals a real gap between the `restart_mindset` axis's own documented 勝負(0.8) sub-theme and what the interpreter/text-vocabulary layers actually operationalize for `courage` — the axis-level design intent ("courage" should include competitive/victory framing) was never implemented in either `NEED_KEYWORDS["courage"]` or `NEED_TEXT_WEIGHTS["courage"]`.

**Does the current mapping conflate courage with 勝運/career/general fortune?** At the GID layer: `career`'s `{6,21,30,12,27}` and `courage`'s `{12,15,18,20,24,30,38}` **literally share ids 12 (仕事運) and 30 (強運厄除け)** — confirmed by direct set intersection, both mappings unchanged/protected. At the Text layer: `NEED_TEXT_WEIGHTS["career"]` contains `"勝運": 2` and `NEED_TEXT_WEIGHTS["courage"]` contains `"勝運": 2` as well — the identical word, independently weighted, in both dicts. **Yes — courage is measurably conflated with career at both the GID and Text layers simultaneously**, not "general fortune" broadly (only the specific `勝運`/`仕事運`/`強運厄除け` cluster).

## 13. Cross-Need Collision Matrix

| Need A | Need B | Shared GID | Shared Text | Shared Interpreter Keyword | Runtime Collapse | Risk |
|---|---|---|---|---|---|---|
| marriage | love | `{1}` | none (marriage has no Text entry) | none literally duplicated (distinct lists) | **FULL** (via alias, Section 5) | **HIGH** — by design, but its inertness is itself the risk |
| communication | relationship | none currently | none (communication has no Text entry) | none literally duplicated, but "職場" (relationship) captures workplace-communication queries `communication`'s own list misses (Section 8) | Query-dependent silent misroute, not a structural alias | **MEDIUM** |
| mental | protection | `{11}` (mental QUESTIONABLE / protection VALID) | none literally duplicated in `NEED_TEXT_WEIGHTS` | **"流れが悪い"** (literal, both `NEED_KEYWORDS` lists) | **PARTIAL** (co-extraction, confirmed empirically Section 10) | **MEDIUM-HIGH** |
| mental | rest | none currently (`mental` has no `{7,8}`) | **"静か"** (literal, both `NEED_TEXT_WEIGHTS` lists) | **"整えたい"/"心を整えたい"** (literal, both `NEED_KEYWORDS` lists, confirmed empirically Section 10) | **PARTIAL** (co-extraction) | **MEDIUM** *(bonus finding, not in the task's example list but directly evidenced)* |
| courage | career | `{12, 30}` (both currently) | **"勝運"** (literal, both `NEED_TEXT_WEIGHTS` lists) | none literally duplicated | No co-extraction observed in tested queries, but GID/Text evidence overlap is real and structural | **MEDIUM** |
| courage | protection | none currently | none | none — checked directly, confirmed absent | N/A | **LOW / NOT_APPLICABLE** (evidence-checked, not assumed) |

## 14. Layer Attribution

| Need | Layers (decomposed) |
|---|---|
| marriage | **ALIAS** (sole confirmed root cause — interpreter extraction is correct, GID mapping is inert only because of the alias, not because it is itself wrong) |
| communication | **MULTI_LAYER**: (1) INTERPRETER — `NEED_KEYWORDS["communication"]` misses common conjugations (話せる vs 話す) and misses the word "コミュニケーション" itself; (2) TAXONOMY — no canonical `GoriyakuTag` denotes communication in any form |
| mental | **MULTI_LAYER**: (1) INTERPRETER — literal keyword duplication with `protection` ("流れが悪い") and `rest` ("整えたい"/"心を整えたい"); (2) TEXT_COVERAGE — mental's own `NEED_TEXT_WEIGHTS` blends PROTECTION_ADJACENT (4/9 words) and AMBIGUOUS-with-rest (1/9) vocabulary; (3) TAXONOMY — no canonical tag directly denotes "calm/mental reset" (re-confirmed, prior audit); MAPPING is a minor/secondary contributor (weak but not literally protection-duplicating) |
| courage | **MULTI_LAYER**: (1) MAPPING — literal GID overlap with `career` (ids 12, 30, both currently shared); (2) TEXT_COVERAGE — literal overlap with `career` ("勝運"); (3) DATA/interpreter gap — the axis's own 勝負(0.8) sub-theme has zero operationalized vocabulary anywhere (confirmed via the "勝負に勝ちたい" null-extraction test), a real coverage gap distinct from the career-overlap issue |

## 15. Mapping-only Counterfactual

| Need | If only `NEED_TO_GORIYAKU_IDS` were corrected, would the observed problem be resolved? |
|---|---|
| marriage | **NO** — confirmed empirically (Section 5): any content in `NEED_TO_GORIYAKU_IDS["marriage"]` is never read at runtime while the alias exists |
| communication | **NO** — even a hypothetical perfect canonical tag (none currently exists) would not be reached by queries the interpreter fails to extract as `communication` in the first place (Section 8, both test queries) |
| mental | **PARTIALLY** — could remove the 3 INVALID GID entries (16/28/38, mirroring the already-computed-but-unimplemented `{11,26}` simulation from the prior audit), but would not touch the interpreter-level co-extraction with `protection`/`rest` (Section 10), which happens upstream of any GID lookup |
| courage | **PARTIALLY** — could remove the 4 INVALID GID entries (18/20/24/38, mirroring the prior audit's `{12,15,30}` simulation), but the GID-layer overlap with `career` (ids 12, 30) and the Text-layer overlap ("勝運") would both remain even after that cleanup, since neither is an "invalid" reference per se — they are QUESTIONABLE, shared-but-plausible tags |

## 16. Text-only Counterfactual

| Need | If only Text Evidence were improved (using existing repo vocabulary only), would the problem be resolved? |
|---|---|
| marriage | **NO** — the alias intercepts `need_tags_clean` before the Text-evidence loop runs too (same `need_tags_clean` list feeds both `matched_by_gid` and `matched_by_text`), so a `NEED_TEXT_WEIGHTS["marriage"]` entry would be equally unreachable |
| communication | **PARTIALLY** — adding `NEED_TEXT_WEIGHTS["communication"]` vocabulary would help *only* for the subset of queries the interpreter does correctly extract as `communication` (neither of the 2 tested queries did); does nothing for the interpreter-vocabulary gap itself |
| mental | **PARTIALLY** — narrowing `NEED_TEXT_WEIGHTS["mental"]`'s existing PROTECTION_ADJACENT/AMBIGUOUS words could reduce (not eliminate) the Text-layer confusion, but the co-extraction happens at the separate, upstream `NEED_KEYWORDS` interpreter layer — a Text-only change cannot touch that dict |
| courage | **PARTIALLY** — removing `NEED_TEXT_WEIGHTS["courage"]`'s "勝運" overlap with career would reduce Text-layer conflation, but the GID-layer overlap (ids 12, 30) is a separate mapping-layer fact, unaffected by any Text change |

## 17. Alias/Interpreter Counterfactual

For `marriage`: **an alias change is required before any Mapping or Text change becomes meaningful** — confirmed as the sole blocking layer (Section 14). No interpreter change is needed (interpreter already extracts `marriage` correctly, Section 6); the fix, if pursued, is specifically at the `NEED_TAG_ALIASES` layer, not the `NEED_KEYWORDS` layer.

For `communication`: **an interpreter vocabulary change is required before a taxonomy/mapping decision becomes meaningful** — even a perfect canonical tag would go unused by the 2 representative queries tested (Section 8), both of which fail to extract `communication` at all. No alias exists for `communication`, so this is purely an interpreter (not alias) gap.

Neither is implemented here (constraint: audit only; no alias, interpreter, or vocabulary change made).

## 18. Data Sufficiency

| Need | GID-capable Shrines (sum across current mapping ids, may double-count shrines with multiple tags) | Text-capable Shrines | Any Evidence | Coverage |
|---|---:|---:|---|---|
| marriage | 37 (structurally present, but 0 in practice — Section 5) | 0 (no Text entry) | Effectively **0** at runtime | **ZERO** (functionally, due to alias — not a data problem, a routing problem) |
| communication | 4 | 0 (no Text entry) | 4 shrines, all via semantically wrong tags | **SPARSE** |
| mental | 28 | Not separately counted (Text matches scan `goriyaku`/`description` free text directly, not a fixed shrine set) — qualitatively present given widely-populated `goriyaku`/`description` fields and mental's real 9-word vocabulary | 28+ | **PARTIAL** (real but weak-quality GID evidence, real Text-layer presence) |
| courage | 20 | Same qualitative note as mental — real 8-word vocabulary against widely-populated free text | 20+ | **PARTIAL** |

Data shortage is kept separate from code responsibility per instruction: `communication`'s SPARSE rating reflects genuinely few shrines carrying its (wrong) current tags, not a statement about how many shrines *could* carry a correct communication-relevant tag (unknown, since no such tag exists to measure against — Section 7).

## 19. Need-level Decisions

| Need | Decision |
|---|---|
| marriage | **`ALIAS_DECISION_REQUIRED`** |
| communication | **`MULTI_LAYER_DESIGN_REQUIRED`** (INTERPRETER + TAXONOMY, both independently blocking, decomposed in Section 14) |
| mental | **`MULTI_LAYER_DESIGN_REQUIRED`** (INTERPRETER + TEXT_COVERAGE + TAXONOMY, decomposed in Section 14; MAPPING is secondary) |
| courage | **`MULTI_LAYER_DESIGN_REQUIRED`** (MAPPING + TEXT_COVERAGE + a DATA/interpreter coverage gap for the axis's own 勝負 sub-theme, decomposed in Section 14) |

No Need received `MAPPING_FIX_READY`, `TAXONOMY_DECISION_REQUIRED` alone, `TEXT_BOUNDARY_DECISION_REQUIRED` alone, `DATA_EXPANSION_REQUIRED`, `NO_CHANGE_REQUIRED`, or `INSUFFICIENT_EVIDENCE` — every Need had sufficient fresh evidence gathered this session to support a specific, decomposed decision.

## 20. Follow-up Split

**marriage**: Alias/semantic-boundary decision. Next task: a dedicated audit (not a fix) into whether `NEED_TAG_ALIASES["marriage"]="love"` should be removed (making `marriage` independent, requiring its own GID/Text correction as a follow-on) or formally kept (in which case `NEED_TO_GORIYAKU_IDS["marriage"]`'s content becomes documentation of intent only, and could be simplified/removed in a trivial separate cleanup). Dependency: none upstream; this decision blocks any future marriage-specific Mapping/Text work. Expected touched files if later implemented: `concierge_chat_ranking.py`/`concierge_chat_need.py` (`NEED_TAG_ALIASES`), possibly `need_to_goriyaku_tag_ids.py` afterward.

**communication**: Taxonomy + interpreter audit, two sequenced sub-decisions. Next task: (1) a Mother Ship decision on whether "communication" deserves canonical taxonomy investment at all (a new `GoriyakuTag`, out of scope for any task in this chain so far) or should be retired/merged conceptually; (2) independently and regardless of (1), an interpreter-vocabulary audit for `NEED_KEYWORDS["communication"]` (conjugation coverage, adding "コミュニケーション" itself) — this second piece has no taxonomy dependency and could proceed on its own. Expected touched files if later implemented: `consultation_interpreter.py` (interpreter), `need_to_goriyaku_tag_ids.py` + Model/migration (only if new taxonomy is approved).

**mental**: Text/Interpreter boundary decision. Next task: a dedicated audit of `NEED_KEYWORDS["mental"]` vs `NEED_KEYWORDS["protection"]`/`NEED_KEYWORDS["rest"]` overlap (should "流れが悪い" and "整えたい" belong to one Need exclusively, or is co-extraction actually the intended design — e.g. does a query about both anxiety and misfortune-warding legitimately deserve both Needs' evidence?) — a genuine product question, not a code defect per se. GID-layer cleanup (`{11,26}`, mirroring the prior audit's unimplemented simulation) could proceed independently as a smaller, lower-priority follow-on once/if the interpreter question is resolved. Expected touched files if later implemented: `consultation_interpreter.py`, `concierge_chat_ranking.py` (NEED_TEXT_WEIGHTS), `need_to_goriyaku_tag_ids.py`.

**courage**: Mapping + Text boundary decision, distinct from mental's interpreter-level question. Next task: a Mother Ship decision on whether `courage` and `career` should legitimately continue sharing GID/Text evidence (ids 12/30, word "勝運" — both currently plausible/QUESTIONABLE, not clear errors) or should be disambiguated; separately, whether to add competitive/victory-framing vocabulary (勝負/勝ちたい) to operationalize the `restart_mindset` axis's own documented 0.8-weight sub-theme, currently absent everywhere. The already-computed `{12,15,30}` GID simulation (prior audit) remains available as a smaller, independent follow-on once the QUESTIONABLE-retention question is settled. Expected touched files if later implemented: `need_to_goriyaku_tag_ids.py`, `concierge_chat_ranking.py` (NEED_TEXT_WEIGHTS), `consultation_interpreter.py` (NEED_KEYWORDS, if victory-framing vocabulary is added).

## 21. Technical Dependency Graph

```
marriage alias decision
  → marriage GID/Text mapping becomes meaningful to correct

communication interpreter-vocabulary audit
  → (independent of taxonomy decision; can proceed on its own)

communication taxonomy decision (new GoriyakuTag, out of scope for this chain)
  → a Mapping candidate for communication can be selected
  → (both interpreter fix AND taxonomy decision are needed before a
     Mapping-only PR would have any real effect, per Section 15)

mental interpreter-overlap product decision (mental vs protection vs rest)
  → mental Text-vocabulary narrowing becomes well-scoped
  → mental GID cleanup ({11,26}) can proceed independently, lower priority

courage/career evidence-sharing product decision
  → courage GID cleanup ({12,15,30}) can proceed independently, lower priority
courage victory-framing vocabulary decision
  → (independent of the career-sharing decision; addresses a different gap)
```

Mother Ship chooses execution order; no priority recommendation is made here.

## 22. Mother Ship Decision Inputs

1. `marriage`: keep `NEED_TAG_ALIASES["marriage"]="love"` (and treat `NEED_TO_GORIYAKU_IDS["marriage"]` as intent-only documentation) or de-alias it into an independent Need requiring its own correction?
2. `communication`: invest in new taxonomy for this Need, or accept it will likely never have real GID evidence and focus only on Text/interpreter-layer improvements (which still cannot fully resolve it per Section 15/16)?
3. `communication` interpreter fix: proceed independently of the taxonomy question (Section 21 shows no dependency blocks it)?
4. `mental`: is co-extraction with `protection`/`rest` on ambiguous queries (Section 10) actually undesirable, or does it reflect a legitimate multi-Need consultation the current architecture should keep producing?
5. `courage`/`career`: should evidence-sharing (ids 12/30, "勝運") continue as an accepted, if imprecise, pattern (as `love`/`relationship`/`marriage` already share id=1), or does courage need sharper disambiguation from career?
6. Should the already-computed-but-unimplemented GID-only simulations for `mental` (`{11,26}`) and `courage` (`{12,15,30}`) from the prior semantic-mapping audit proceed as small, independent, lower-priority follow-ons regardless of the larger interpreter/text questions above?

## 23. Limitations

- Runtime traces (Sections 5, 6, 8, 10, 12) used a small, hand-selected set of representative queries per Need (matching the task's own examples), not an exhaustive fixture sweep — broader query coverage could surface additional collision patterns not captured here.
- The MULTI_LAYER decompositions (Section 14) are this audit's own first-pass reading of the evidence; the relative weight/priority between contributing layers (e.g. whether `mental`'s interpreter overlap or its Text-layer ambiguity is the "bigger" problem) is not adjudicated here — both are reported as independently confirmed contributors, without ranking.
- `NEED_KEYWORDS` coverage gaps (Section 8's "話せる" vs "話す" conjugation miss) were identified via the specific test queries used; a systematic audit of Japanese conjugation coverage across all 15 Need tags' keyword lists was not performed (out of scope — this audit is limited to the 4 target Needs).
- Text-capable shrine counts (Section 18) are qualitative, not exact — `matched_by_text` scans free-text `goriyaku`/`description` fields directly rather than a fixed tag relation, so an exact count would require a full-text scan across all shrines, not performed in this audit.

## 24. Out of Scope

UI, frontend, implementation of any alias/interpreter/taxonomy/text/mapping change described in Sections 19–21, new `GoriyakuTag` creation, new Need tag creation, C1/Ranking/Lead/Reason/Direction/Distance changes, Production DB changes, re-opening any of the 10 already-stabilized Need mappings.
