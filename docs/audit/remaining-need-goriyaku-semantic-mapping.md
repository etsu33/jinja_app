# Remaining Need → Goriyaku Semantic Mapping Audit

> **Status**: AUDIT ONLY. `NEED_TO_GORIYAKU_IDS`, canonical `GoriyakuTag`, `NEED_TEXT_WEIGHTS`, C1, Ranking, Lead, Reason, Direction, Distance, consultation interpreter, Need taxonomy, Production DB/Seed — all unchanged. No implementation.

## 1. Scope

Semantic audit of the 8 Need tags left untouched by both the original 5-Purpose correction (`compass-purpose-goriyaku-mapping-correction.md`) and the structural master-integrity correction (`goriyaku-mapping-master-integrity-correction.md`): **relationship, marriage, communication, health, mental, courage, focus, family**. For each: classify current mapped tags (VALID/QUESTIONABLE/INVALID), find CLEAR_MISSING canonical candidates, measure DB evidence, simulate a read-only "safe correction," and determine what (if anything) is safe for a later implementation PR.

## 2. Base SHA

`origin/develop` at `6c221b5be1317225fe9f091d81441b0cc5bd0ea3` (`fix: align Goriyaku mapping with canonical master (#2578)`). `git log --oneline f75d6304..6c221b5b`: single commit, PR #2578 only — no unrelated changes. Worktree: `/Users/morietsu/Developer/jinja_app-remaining-need-mapping-audit`, branch `audit/remaining-need-goriyaku-semantic-mapping`.

## 3. Sources of Truth

Fresh-read this session: `need_to_goriyaku_tag_ids.py` (confirmed identical to PR #2578's shipped state), `need_tags.py` (15-tag taxonomy), `NEED_TEXT_WEIGHTS` (`concierge_chat_ranking.py`), canonical `GoriyakuTag` master (39 rows, re-queried, identical shrine counts to the prior audit). **Newly fresh-read this session** (not previously inspected in this audit chain): `backend/temples/domain/consultation_axis.py` (`NEED_TAG_TO_CONSULTATION_AXIS`, `CONSULTATION_AXIS_KEYWORDS`) and `backend/temples/services/concierge_chat_ranking.py` / `concierge_chat_need.py`'s `NEED_TAG_ALIASES` + `_normalize_need_tag` — this second read surfaced the single most consequential finding in this audit (Section 16).

## 4. Current Mapping Inventory

| Need | Current IDs |
|---|---|
| relationship | {1, 27, 34} |
| marriage | {1, 27, 29} |
| communication | {30, 33, 37, 39} |
| health | {7, 8} |
| mental | {11, 16, 26, 28, 38} |
| courage | {12, 15, 18, 20, 24, 30, 38} |
| focus | {3, 4, 39} |
| family | {2, 25, 27, 34} |

| Need | ID | Canonical Label | Shrine Count |
|---|---:|---|---:|
| relationship | 1 | 縁結び | 32 |
| relationship | 27 | 出世運 | 2 |
| relationship | 34 | 火防 | 2 |
| marriage | 1 | 縁結び | 32 |
| marriage | 27 | 出世運 | 2 |
| marriage | 29 | 芸能運 | 3 |
| communication | 30 | 強運厄除け | 1 |
| communication | 33 | 病気平癒 | 1 |
| communication | 37 | 延命長寿 | 1 |
| communication | 39 | 農業守護 | 1 |
| health | 7 | 家内安全 | 26 |
| health | 8 | 福徳 | 1 |
| mental | 11 | 勝運 | 19 |
| mental | 16 | 安産 | 5 |
| mental | 26 | 家庭円満 | 1 |
| mental | 28 | 金運 | 2 |
| mental | 38 | 足腰健康 | 1 |
| courage | 12 | 仕事運 | 11 |
| courage | 15 | 武運長久 | 1 |
| courage | 18 | 夫婦円満 | 1 |
| courage | 20 | 恋愛成就 | 4 |
| courage | 24 | 健康長寿 | 1 |
| courage | 30 | 強運厄除け | 1 |
| courage | 38 | 足腰健康 | 1 |
| focus | 3 | 交通安全 | 6 |
| focus | 4 | 商売繁盛 | 16 |
| focus | 39 | 農業守護 | 1 |
| family | 2 | 厄除け | 51 |
| family | 25 | 芸能 | 1 |
| family | 27 | 出世運 | 2 |
| family | 34 | 火防 | 2 |

## 5. Need Semantic Boundaries

Runtime-authoritative sources checked first (per instruction), not intuition:

| Need | `NEED_TAG_TO_CONSULTATION_AXIS` | `NEED_TEXT_WEIGHTS` vocabulary (if any) | Resolved boundary |
|---|---|---|---|
| relationship | `relationship_repair` (shared with `love`) | none | Interpersonal relationships broadly — `CONSULTATION_AXIS_KEYWORDS["relationship_repair"]` explicitly lists 職場の人間関係/家族との関係/友人との関係 (workplace/family/friend relations), i.e. deliberately **broader than romantic love** (PR #2409, quoted verbatim in Section 16) |
| marriage | **not present** in `NEED_TAG_TO_CONSULTATION_AXIS` | none | No independent runtime axis definition exists. See Section 16 — this Need is aliased to `love` upstream of any axis/mapping lookup, making an independent boundary definition moot at runtime |
| communication | **not present** | none | No runtime semantic-axis or text-vocabulary definition exists anywhere in the codebase for this Need. Boundary must be inferred from the Need tag's own name only |
| health | **not present** | none | No runtime semantic-axis or text-vocabulary definition exists. Boundary inferred from name only (general physical health/wellbeing, distinct from `protection`'s misfortune-warding domain per the already-corrected Purpose) |
| mental | `restart_mindset` (**shared with `courage`**) | 厄除/厄払い/浄化/心を整える/不安/落ち着く/静か/守護/守ってほしい (9 words) | The official axis (`restart_mindset`, max-weight history_theme = 再出発 1.0, then 勝負 0.8, 静寂 0.6) blends "psychological reset/fresh start" with "regaining resolve," while the Text vocabulary skews toward calm/anxiety-relief **and explicitly contains protection-adjacent words** (厄除/厄払い/守護) — Section 17 examines this tension directly |
| courage | `restart_mindset` (shared with `mental`) | 開運/開運祈願/勝運/運を開く/背中を押して/一歩踏み出す/勇気/変わりたい (8 words) | Taking action / moving forward decisively — the action-oriented end of the shared `restart_mindset` axis |
| focus | `study_success` (**identical axis to `study`**) | none (`study` itself has 8 words; `focus` has zero, despite sharing its axis) | Concentration/exam-preparation focus — officially the *same* underlying concept as `study` at the axis level, but under-resourced relative to `study` at both the GID and Text layers |
| family | **not present** | none | No independent runtime axis; overlaps with `relationship_repair`'s explicit keyword scope (家族との関係) without having its own axis entry |

## 6. Current Mapping Classification

| Need | ID | Label | Classification | Reason |
|---|---:|---|---|---|
| relationship | 1 | 縁結び | **VALID** | direct — good-connections concept applies broadly, consistent with the axis's documented scope |
| relationship | 27 | 出世運 | **INVALID** | career advancement, no relation to interpersonal relationships |
| relationship | 34 | 火防 | **INVALID** | fire prevention, no semantic connection |
| marriage | 1 | 縁結び | VALID *(see Section 16 — moot at runtime)* | matchmaking, direct |
| marriage | 27 | 出世運 | INVALID *(moot)* | career, unrelated |
| marriage | 29 | 芸能運 | INVALID *(moot)* | performing-arts luck — already flagged INVALID for `love` in the original 5-Purpose audit for the identical reason |
| communication | 30 | 強運厄除け | **INVALID** | broad fortune/warding compound, zero semantic link to communication |
| communication | 33 | 病気平癒 | **INVALID** | illness recovery, unrelated |
| communication | 37 | 延命長寿 | **INVALID** | longevity, unrelated |
| communication | 39 | 農業守護 | **INVALID** | agricultural protection, unrelated |
| health | 7 | 家内安全 | **QUESTIONABLE** | household safety, indirect for personal physical health |
| health | 8 | 福徳 | **QUESTIONABLE** | general fortune/virtue, indirect |
| mental | 11 | 勝運 | **QUESTIONABLE** | "victory" nuance closer to `restart_mindset`'s 勝負(0.8) sub-theme than to calm/reset itself — plausible but not direct |
| mental | 16 | 安産 | **INVALID** | safe childbirth, unrelated |
| mental | 26 | 家庭円満 | **QUESTIONABLE** | family stability could indirectly support mental calm, weak/indirect link — also a stronger `family` candidate, Section 7 |
| mental | 28 | 金運 | **INVALID** | money luck, unrelated |
| mental | 38 | 足腰健康 | **INVALID** | leg/hip health, unrelated — a `health` candidate instead, Section 7 |
| courage | 12 | 仕事運 | **QUESTIONABLE** | work-luck, indirect backing-for-action link |
| courage | 15 | 武運長久 | **QUESTIONABLE** | martial fortune — plausible fit for the axis's 勝負(0.8) sub-theme, though specifically combat-flavored |
| courage | 18 | 夫婦円満 | **INVALID** | marital harmony, unrelated — a `marriage` candidate instead, Section 7 |
| courage | 20 | 恋愛成就 | **INVALID** | romantic fulfillment, unrelated — cross-purpose duplicate of `love`'s correct use of the same id |
| courage | 24 | 健康長寿 | **INVALID** | health/longevity, unrelated — a `health` candidate instead |
| courage | 30 | 強運厄除け | **QUESTIONABLE** | broad "strong fortune," loosely action/backing-adjacent |
| courage | 38 | 足腰健康 | **INVALID** | leg/hip health, unrelated — a `health` candidate instead |
| focus | 3 | 交通安全 | **INVALID** | traffic safety — identical to `study`'s pre-correction broken set, see Section 5 |
| focus | 4 | 商売繁盛 | **INVALID** | business prosperity, unrelated |
| focus | 39 | 農業守護 | **INVALID** | agricultural protection, unrelated |
| family | 2 | 厄除け | **QUESTIONABLE** | broad misfortune-warding, plausibly protective-of-household but not family-specific |
| family | 25 | 芸能 | **INVALID** | performing arts, unrelated |
| family | 27 | 出世運 | **INVALID** | career, unrelated |
| family | 34 | 火防 | **QUESTIONABLE** | fire prevention — household/family safety framing is more plausible here than in `relationship`, still indirect |

**Totals**: VALID 2 (relationship:1, marriage:1 — marriage's moot per Section 16), QUESTIONABLE 9, INVALID 20.

## 7. Missing Canonical Candidates

| Need | Candidate ID | Label | Classification | Reason |
|---|---:|---|---|---|
| marriage | 18 | 夫婦円満 | **CLEAR_MISSING** | direct marital-harmony match; currently misassigned to `courage` (INVALID there) |
| health | 24 | 健康長寿 | **CLEAR_MISSING** | direct health/longevity match; currently misassigned to `courage` (INVALID there) |
| health | 33 | 病気平癒 | **CLEAR_MISSING** | direct illness-recovery match; currently misassigned to `communication` (INVALID there) |
| health | 38 | 足腰健康 | **CLEAR_MISSING** | direct (specific-subset) health match; currently misassigned to both `mental` and `courage` (INVALID in both) |
| family | 26 | 家庭円満 | **CLEAR_MISSING** | direct family-harmony match; currently misassigned to `mental` (QUESTIONABLE there) |
| focus | 9, 10 | 学業成就, 合格祈願 | **CLEAR_MISSING** *(shared, not new)* | `focus` officially shares `study`'s exact `consultation_axis` (`study_success`, Section 5); these are `study`'s own already-VALID tags — precedent for shared evidence across distinct Need tags already exists (id=1 is shared by love/relationship/marriage today) |
| relationship | — | — | NOT_RELEVANT | no additional direct canonical label found beyond id=1 |
| communication | — | — | **NOT_RELEVANT / taxonomy gap** | no canonical tag in the 39-row master denotes "communication" in any form; this Need cannot be corrected via mapping alone (Section 9) |
| mental | — | — | **NOT_RELEVANT / taxonomy gap** | no canonical tag directly denotes "calm/composure/mental reset"; 26 (家庭円満) is a better fit for `family` (above) than for `mental` itself |
| courage | — | — | **NOT_RELEVANT / taxonomy gap** | no canonical tag directly denotes "courage/backing/taking the leap" |

Only CLEAR_MISSING items are correction candidates; POSSIBLE_MISSING was not needed as a separate bucket here — every genuine candidate found was either unambiguous (CLEAR) or entirely absent (NOT_RELEVANT/taxonomy gap).

## 8. Cross-Need Collision Matrix

| Tag | Need A | Need B | Same semantic role? | Collision risk |
|---|---|---|---|---|
| 1 (縁結び) | love (VALID) | relationship (VALID) / marriage (VALID, moot) | Yes — an established, accepted shared-evidence pattern (3-way) | **LOW** |
| 18 (夫婦円満) | courage (INVALID, current) | marriage (CLEAR_MISSING) | No — single current user is simply wrong, not a real collision | LOW (misassignment, not collision) |
| 20 (恋愛成就) | love (VALID) | courage (INVALID) | No — courage's use is a plain error | **HIGH** (same tag, unrelated purposes; courage's use should be removed) |
| 24 (健康長寿) | courage (INVALID, current) | health (CLEAR_MISSING) | No — misassignment, not collision | LOW |
| 26 (家庭円満) | mental (QUESTIONABLE, current) | family (CLEAR_MISSING) | No — mental's use is weak/indirect at best | MEDIUM |
| 27 (出世運) | career (VALID) | relationship (INVALID) / family (INVALID) | No — only career's use is correct | **HIGH** (3-way, 2 of 3 wrong) |
| 28 (金運) | money (VALID) | mental (INVALID) | No | MEDIUM-HIGH |
| 30 (強運厄除け) | career (QUESTIONABLE) | communication (INVALID) / courage (QUESTIONABLE) | Partially — broad multi-purpose tag genuinely could apply loosely to career/courage, not communication | MEDIUM |
| 34 (火防) | relationship (INVALID) | family (QUESTIONABLE) | Partially — family's framing is more plausible | MEDIUM |
| 38 (足腰健康) | mental (INVALID) | courage (INVALID) | No — both wrong; health is the real target | LOW-in-practice (double-misassignment, not a legitimate shared concept) |
| 11 (勝運) | protection (VALID) | mental (QUESTIONABLE) | Partially | MEDIUM |

This matters because, per the task's framing, shared tags can make different consultation intents converge on the same recommendations — but the matrix shows nearly every real collision here is a **misassignment** (a tag correctly belonging to one Need and wrongly present in another), not a legitimate case of two Needs genuinely sharing the same evidence (id=1 is the one clean exception, an already-accepted pattern).

## 9. Text Coverage Boundary

| Need | Text Coverage | Vocabulary Count |
|---|---|---:|
| relationship | NO | 0 |
| marriage | NO | 0 |
| communication | NO | 0 |
| health | NO | 0 |
| mental | YES | 9 |
| courage | YES | 8 |
| focus | NO | 0 |
| family | NO | 0 |

Only `mental` and `courage` have any Text-layer fallback among these 8. This means for the other 6 (relationship, marriage, communication, health, focus, family), **mapping health *is* the whole story** — there is no Text Evidence compensating for GID errors the way `study`/`money` were compensated before their own correction shipped. A broken GID mapping for these 6 produces broken or absent Recommendation Evidence with no safety net.

## 10. DB Evidence Coverage

(Shrine counts from Section 4's table, plus CLEAR_MISSING candidates from Section 7.)

| Need | Tag | Status | Shrine Count |
|---|---|---|---:|
| relationship | 1 縁結び | VALID | 32 |
| relationship | 27 出世運 | INVALID | 2 |
| relationship | 34 火防 | INVALID | 2 |
| marriage | 18 夫婦円満 | CLEAR_MISSING | 1 |
| communication | *(none)* | taxonomy gap | — |
| health | 7 家内安全 | QUESTIONABLE | 26 |
| health | 8 福徳 | QUESTIONABLE | 1 |
| health | 24 健康長寿 | CLEAR_MISSING | 1 |
| health | 33 病気平癒 | CLEAR_MISSING | 1 |
| health | 38 足腰健康 | CLEAR_MISSING | 1 |
| mental | 11 勝運 | QUESTIONABLE | 19 |
| mental | 26 家庭円満 | QUESTIONABLE | 1 |
| courage | 12 仕事運 | QUESTIONABLE | 11 |
| courage | 15 武運長久 | QUESTIONABLE | 1 |
| courage | 30 強運厄除け | QUESTIONABLE | 1 |
| focus | 9 学業成就 | CLEAR_MISSING (shared) | 8 |
| focus | 10 合格祈願 | CLEAR_MISSING (shared) | 3 |
| family | 2 厄除け | QUESTIONABLE | 51 |
| family | 26 家庭円満 | CLEAR_MISSING | 1 |
| family | 34 火防 | QUESTIONABLE | 2 |

**Need with zero usable GID Evidence**: `communication` — no VALID/QUESTIONABLE tag exists and no CLEAR_MISSING candidate exists either; this Need has genuinely zero real GID-evidence path available in the current taxonomy.
**Need with very sparse evidence**: `marriage` (best candidate 18, shrine_count=1 — and moot regardless, Section 16), `family`'s CLEAR_MISSING candidate 26 (shrine_count=1), `health`'s three CLEAR_MISSING candidates (1 each).
**Need with broad/high-overlap evidence**: `relationship` (id=1, 32 shrines — but shared 3-way with love/marriage), `family` (id=2, 51 shrines — the single largest tag in the whole master, already the driver of `protection`'s correct mapping too).

## 11. Need Health Matrix

| Need | VALID | QUESTIONABLE | INVALID | CLEAR_MISSING | Text Coverage | Health |
|---|---:|---:|---:|---:|---|---|
| relationship | 1 | 0 | 2 | 0 | NO | **PARTIAL** (1 real VALID anchor, 2 dead weight) |
| marriage | 1 | 0 | 2 | 1 | NO | **INSUFFICIENT_EVIDENCE** *(nominal mapping is PARTIAL, but the alias in Section 16 makes GID-mapping health an unanswerable question at the runtime level — see Section 16)* |
| communication | 0 | 0 | 4 | 0 | NO | **BROKEN** (0 real evidence, no fixable path within current taxonomy) |
| health | 0 | 2 | 0 | 3 | NO | **PARTIAL** (currently 0 VALID, but 3 clean CLEAR_MISSING candidates exist — highly fixable) |
| mental | 0 | 2 | 3 | 0 | YES | **PARTIAL** (Text layer provides real fallback; GID layer alone is weak) |
| courage | 0 | 3 | 4 | 0 | YES | **PARTIAL** (same reasoning as mental) |
| focus | 0 | 0 | 3 | 2 (shared) | NO | **BROKEN**, but cleanly fixable (identical situation to `study` pre-correction) |
| family | 0 | 2 | 2 | 1 | NO | **PARTIAL** (id=2's 51-shrine base is a real, if imprecise, anchor; 26 would meaningfully sharpen it) |

## 12. Hypothetical Corrected Mappings

Per rule: existing VALID retained, existing QUESTIONABLE retained (not pruned — constraint #21), INVALID removed, CLEAR_MISSING added. No case here required choosing among competing QUESTIONABLE candidates, so `PRODUCT_DECISION_REQUIRED` was not triggered at the mechanical-construction level for any of the 8 (a separate, higher-level product question is flagged in Section 20 regardless).

| Need | Current | Simulated |
|---|---|---|
| relationship | `{1, 27, 34}` | `{1}` |
| marriage | `{1, 27, 29}` | `{1, 18}` *(Section 16: simulated set is correct in isolation but inert at runtime)* |
| communication | `{30, 33, 37, 39}` | `{}` *(genuinely empty — no fabricated replacement, per instruction)* |
| health | `{7, 8}` | `{7, 8, 24, 33, 38}` |
| mental | `{11, 16, 26, 28, 38}` | `{11, 26}` |
| courage | `{12, 15, 18, 20, 24, 30, 38}` | `{12, 15, 30}` |
| focus | `{3, 4, 39}` | `{9, 10}` |
| family | `{2, 25, 27, 34}` | `{2, 26, 34}` |

## 13. Runtime Baseline

Fixed fixture (identical to prior correction PRs for direct comparability): `origin = {"lat": 35.662443, "lng": 139.5920237}`, `direction_context = {"referenceDirections": ["東"], "calculationMethod": "annual_monthly_kyusei_v1"}`, live unmodified `get_compass_recommendations()`. Current-mapping Top3 per Need (state, score_need, matched, winner, reason):

| Need | Top3 (current mapping) |
|---|---|
| relationship | 明治神宮(1,gid)/赤坂氷川神社(1,gid)/日枝神社(1,gid via 出世運 — **false match**) |
| marriage | 東京大神宮(1,text)/明治神宮(1,text)/赤坂氷川神社(1,text) — **all matched via `love`, not `marriage`'s own mapping at all** (Section 16) |
| communication | 長太稲荷神社(0,fallback,dup)/長太稲荷神社(0,fallback,dup)/明治神宮(0,fallback) |
| health | 乃木神社(1,gid)/靖國神社(1,gid)/長太稲荷神社(0,fallback) |
| mental | 明治神宮(1,text)/赤坂氷川神社(1,text)/靖國神社(1,text) |
| courage | 花園神社(1,text)/乃木神社(1,text)/靖國神社(1,text) |
| focus | 明治神宮(1,gid via 交通安全 — **false match**)/花園神社(1,gid via 商売繁盛 — **false match**)/日枝神社(1,gid via 商売繁盛 — **false match**) |
| family | 明治神宮(1,gid)/赤坂氷川神社(1,gid)/日枝神社(1,gid via 出世運 — **false match**) |

## 14. Read-only Simulation

| Need | Before Top3 | After Top3 | Change |
|---|---|---|---|
| relationship | 明治神宮/赤坂氷川神社/**日枝神社** | 明治神宮/赤坂氷川神社/**芝大神宮** | rank3: `INVALID_MATCH_REMOVED` (出世運) → `EXISTING_MATCH_PRESERVED` (縁結び, different shrine) |
| marriage | 東京大神宮/明治神宮/赤坂氷川神社 | **identical** | `NO_CHANGE` — see Section 16, mapping is unreachable regardless of content |
| communication | 長太稲荷神社(dup)/長太稲荷神社(dup)/明治神宮 (all fallback) | **identical** | `NO_CHANGE` (visible) — real effect is nationwide: BEFORE could theoretically false-match 1 of 4 sparsely-held tags somewhere; AFTER (`{}`) cannot match anywhere, ever |
| health | 乃木神社/靖國神社/長太稲荷神社 | **identical** | `NO_CHANGE` (visible) — `CANDIDATE_POOL_LIMITATION`: none of the 3 CLEAR_MISSING tags' shrines fell within this fixture's candidate pool |
| mental | 明治神宮/赤坂氷川神社/靖國神社 | **identical** | `NO_CHANGE` — removed ids (16/28/38) were not driving any Top3 slot in this fixture; retained ids (11/26) unaffected |
| courage | 花園神社/乃木神社/靖國神社 | **identical** | `NO_CHANGE` — same reasoning as mental |
| focus | 明治神宮/花園神社/日枝神社 (**all 3 false matches**) | 長太稲荷神社(dup)/長太稲荷神社(dup)/明治神宮 (**all fallback**) | `INVALID_MATCH_REMOVED` ×3 — mirrors `study`'s own pre-correction pattern exactly (`CANDIDATE_POOL_LIMITATION` explains why no new true match appears in *this* fixture, even though `{9,10}` are DB-wide real, per Section 10) |
| family | 明治神宮/赤坂氷川神社/**日枝神社** | 明治神宮/赤坂氷川神社/**靖國神社** | rank3: `INVALID_MATCH_REMOVED` (出世運) → `EXISTING_MATCH_PRESERVED` (厄除け, different shrine) |

## 15. Ranking Churn Attribution

| Need | Cause | Expected/Unexpected |
|---|---|---|
| relationship | INVALID_MAPPING_REMOVAL | EXPECTED_SEMANTIC_CHURN |
| marriage | *(inert — Section 16)* | N/A, not applicable to standard categories |
| communication | INVALID_MAPPING_REMOVAL (nationwide effect not visible in this fixture) | EXPECTED_SEMANTIC_CHURN (invisible-here) |
| health | CLEAR_MISSING_ADDITION + CANDIDATE_POOL_LIMITATION | EXPECTED_SEMANTIC_CHURN (invisible-here) |
| mental | INVALID_MAPPING_REMOVAL (non-driving ids) | EXPECTED (no visible churn, correctly inert-in-fixture) |
| courage | INVALID_MAPPING_REMOVAL (non-driving ids) | EXPECTED (no visible churn, correctly inert-in-fixture) |
| focus | INVALID_MAPPING_REMOVAL + CANDIDATE_POOL_LIMITATION | EXPECTED_SEMANTIC_CHURN |
| family | INVALID_MAPPING_REMOVAL | EXPECTED_SEMANTIC_CHURN |

**Unexpected churn: 0** across all 8 Needs. Every observed (or knowingly-invisible-in-this-fixture) change traces to a specific, understood cause.

## 16. Relationship / Marriage Boundary

**This is the audit's most consequential finding.** Fresh-read of `backend/temples/services/concierge_chat_ranking.py` (and its duplicate in `concierge_chat_need.py`) found:

```python
NEED_TAG_ALIASES: Dict[str, str] = {
    "marriage": "love",
    "romance": "love",
    ...
}
```

consumed by `_normalize_need_tag()` → `_normalize_need_tags()`, which **both** `_attach_breakdown()` (line 1071) **and** `_prefilter_candidates_for_need()` (line 1596) call on `need_tags` *before* any GID lookup occurs. Directly confirmed: `_normalize_need_tag("marriage")` → `"love"`. Consequently, `need_tags_to_goriyaku_ids([tag])` inside the matching loop is called with `tag="love"`, **never** `tag="marriage"` — `NEED_TO_GORIYAKU_IDS["marriage"]` is never read by this code path regardless of its contents. Empirically confirmed in Section 13/14: `marriage`'s Top3 is driven entirely by `love`'s own mapping/text evidence (`matched=['love']`, reason text is love-themed — "恋愛や良縁を願う"), identical whether `marriage`'s own entry is `{1,27,29}` (current) or the simulated `{1,18}`.

Meanwhile, **`relationship` is deliberately *not* in `NEED_TAG_ALIASES`**, with an extensive code comment (quoted verbatim, both files) explaining why: *"'relationship' is a distinct, first-class need tag... It must NOT be aliased to 'love' here: doing so collapsed workplace/family/friend relationship consultations into romantic-love recommendation reasons (docs/audit/concierge-l1-freetext-readiness.md Finding C, PR #2409)."* This confirms `relationship` genuinely operates independently at runtime — its own `{1,27,34}`/simulated `{1}` mapping is live and consulted, as Section 14's real Top3 churn for `relationship` demonstrates.

**Result: `PARTIAL_COLLAPSE`.** `relationship` remains `WELL_SEPARATED` from `love` (confirmed independent, own mapping drives its own results). `marriage`, however, is **fully and deliberately collapsed into `love`** — not "converging" as an unintended side effect of tag-sharing, but by an explicit, already-shipped, documented `NEED_TAG_ALIASES` entry that predates every mapping-correction PR in this audit chain. This is not a mapping defect this audit's scope can fix (constraint: mapping changes only, and constraint #14's precedent — do not touch relationship↔love aliasing — implies alias-table changes are a separate, more sensitive concern than GID-mapping corrections). It does mean: **`NEED_TO_GORIYAKU_IDS["marriage"]` is currently dead configuration** for GID-matching purposes — any future correction to its contents (Section 7/12) would be semantically correct in isolation but would have zero observable runtime effect until/unless the `marriage → love` alias itself is revisited, which this audit explicitly does not recommend or evaluate (out of scope, a distinct and larger product/architecture decision).

## 17. Mental Boundary

Per Section 5, `mental` shares its official `consultation_axis` (`restart_mindset`) with `courage`, and its Text vocabulary (家除/厄払い/守護/守ってほしい, among others) contains genuinely protection-adjacent words. Checked directly against the current (post-fix) GID mapping `{11, 16, 26, 28, 38}`:

- None of these 5 tags is itself a protection-category label (`厄除け` id=2, the tag that *is* protection-specific and VALID for the `protection` Purpose, is **not** present in `mental`'s GID set)
- 11 (勝運) leans toward the axis's 勝負 sub-theme, not protection
- 16/28/38 are simply unrelated (childbirth/money/leg-health)
- 26 (家庭円満) is family-harmony, not protection

**Result: `HEALTHY`** on the specific question "does the current GID mapping introduce protection semantics" — it does not; zero of the 5 current tags belongs to the protection category. The protection-adjacent language exists **only in the Text-evidence layer** (out of scope here — constraint #4, do not modify `NEED_TEXT_WEIGHTS`), not in the GID mapping. Separately, and independently of the protection question, `mental`'s GID-layer *semantic fit to its own restart-mindset/calm axis* remains weak (Section 11: PARTIAL, 0 VALID / 2 QUESTIONABLE / 3 INVALID), and the taxonomy contains no clean direct label for "calm/composure/reset" (Section 7) — so `mental`'s overall Need Health is PARTIAL, but its specific protection-boundary question is HEALTHY.

## 18. Health Boundary

Post structural fix, `health`'s remaining current mapping `{7, 8}` (家内安全/福徳) provides **general household-safety and general-fortune** framing — not specific physical health, not disease-recovery. Checked against the taxonomy for what actually exists:

- General health/longevity: 24 健康長寿 — exists, currently misassigned to `courage`
- Disease-specific healing: 33 病気平癒 — exists, currently misassigned to `communication`
- Specific-subset physical health (mobility): 38 足腰健康 — exists, currently misassigned to both `mental` and `courage`
- No canonical tag makes any medical-efficacy claim beyond naming these blessing categories (Contract-consistent — this audit records taxonomy alignment only, per instruction, and asserts nothing about actual health outcomes)

**Result**: the master genuinely contains a well-formed sub-taxonomy for "health" (general, longevity, disease-specific, mobility-specific) — it is simply **entirely scattered across other Needs' mappings today**, none of it currently assigned to `health` itself. This is the cleanest, most mechanically resolvable finding in this audit (Section 20).

## 19. Safe Corrections

**SAFE_CORRECTIONS** (current tag exists, semantic mapping direct, no product decision required, no new taxonomy, simulation exposed no unexplained behavior):

- `relationship`: remove 27, 34 → `{1}`
- `health`: add 24, 33, 38 (keep 7, 8) → `{7, 8, 24, 33, 38}`
- `focus`: remove 3, 4, 39; add 9, 10 → `{9, 10}`
- `family`: remove 25, 27; add 26 (keep 2, 34) → `{2, 26, 34}`

**NOT classified as ready SAFE_CORRECTIONS despite passing the mechanical rule**:

- `marriage`: the simulated `{1, 18}` set is itself mechanically safe (VALID+CLEAR_MISSING only), but Section 16 shows it would be **inert** at runtime under the current `NEED_TAG_ALIASES` — implementing it would not be unsafe, but would also not be a real fix, and risks being mistaken for one. Held pending the separate alias question (Section 20/23), not because the mapping itself is wrong.

## 20. Product Decisions Required

- `mental`: `{11, 26}` (remove 16, 28, 38; keep QUESTIONABLE 11, 26) — mechanically SAFE by the rule, but per constraint #21 QUESTIONABLE retention itself needs Mother Ship sign-off before implementation, and Section 17's finding (taxonomy has no clean "calm/reset" label at all) means even a fully "corrected" mental mapping stays structurally weak — worth deciding whether that's acceptable or whether `mental` needs a different treatment entirely (e.g., leaning harder on its real Text-layer coverage instead of GID)
- `courage`: `{12, 15, 30}` (remove 18, 20, 24, 38; keep QUESTIONABLE 12, 15, 30) — same QUESTIONABLE-retention sign-off need; same taxonomy-gap caveat (no direct "courage" label exists)
- `communication`: simulated `{}` — technically the cleanest possible SAFE_CORRECTION (all INVALID removed, nothing fabricated), but an intentionally-empty Purpose mapping is itself a product decision (does Concierge want `communication` to always fall back to distance-order with zero real Evidence, or should this Need be reconsidered entirely — e.g. mapped onto `relationship`'s tags, or retired) — not decided by this audit
- `marriage`: the underlying `NEED_TAG_ALIASES["marriage"] = "love"` architecture question (Section 16/23) — whether `marriage` should remain a `love` alias (in which case its `NEED_TO_GORIYAKU_IDS` entry is dead weight worth documenting/removing in its own small follow-up) or be de-aliased into an independent Need (a materially larger, riskier change well beyond a mapping-only audit)

## 21. Implementation Split Options

- **Option A (all 8 in one PR)**: rejected — bundles `marriage`'s inert change, `communication`'s empty-set product question, and two QUESTIONABLE-retention sign-offs into a single review, obscuring which parts are truly safe.
- **Option B (safe corrections only, one PR)**: `relationship` + `health` + `focus` + `family` (Section 19). Highest safety/lowest review burden of any bundled option — mirrors exactly the pattern of the already-shipped `travel_safe` + stale-id-removal PR (#2578).
- **Option C (clustered PRs)**: `{relationship, family}` (both share the 27/34 misassignment pattern and both resolve cleanly) + `{health}` (its own clean, high-confidence 3-tag addition) + `{focus}` (shares `study`'s exact precedent and tag set) — three small, thematically coherent PRs.
- **Option D (one Need per PR)**: maximal isolation and rollback granularity, but four PRs for four mechanically-identical "remove INVALID, add CLEAR_MISSING" edits is disproportionate review overhead for the risk level established by this audit and by PR #2578's precedent (a 6-Need structural change shipped safely in one PR).

**Recommended: Option B.** All 4 SAFE_CORRECTIONS pass the same "VALID/CLEAR_MISSING only, zero product decision, zero unexplained simulation behavior" bar simultaneously, exactly mirroring how PR #2578 safely bundled 5 stale-id removals + 1 clear remapping into one PR. `mental`/`courage`/`communication`/`marriage` are deliberately excluded and left for a separate follow-up once their respective product decisions (Section 20) are resolved.

## 22. Recommendation

**`SAFE_CORRECTION_PR_READY`** — for the 4-Need subset only (`relationship`, `health`, `focus`, `family`; Option B, Section 21). The remaining 4 (`marriage`, `communication`, `mental`, `courage`) require Mother Ship product decisions first (Section 20) and are correctly excluded from immediate implementation, not because they're unsafe to leave as-is, but because a mechanically-correct edit for them would either be inert (`marriage`) or requires accepting a genuinely-empty mapping / QUESTIONABLE-retention as intentional (`communication`/`mental`/`courage`).

**Exact before/after for the ready subset**:

```
"relationship": {1, 27, 34} -> {1}
"health":       {7, 8}      -> {7, 8, 24, 33, 38}
"focus":        {3, 4, 39}  -> {9, 10}
"family":       {2, 25, 27, 34} -> {2, 26, 34}
```

## 23. Mother Ship Decision Inputs

1. Implement the `SAFE_CORRECTION_PR_READY` subset (`relationship`/`health`/`focus`/`family`, Section 22) next?
2. `marriage`: keep the pre-existing `NEED_TAG_ALIASES["marriage"] = "love"` as-is (in which case a small, separate follow-up could simplify/remove `NEED_TO_GORIYAKU_IDS["marriage"]`'s now-confirmed-dead content, or leave it as harmless unused documentation of intent) — or open a **separate, larger** audit into de-aliasing `marriage` into an independent Need? This audit does not recommend either; it only surfaces that the current state is a live inconsistency between the Need-taxonomy layer (independent) and the alias layer (collapsed).
3. `communication`: accept a permanently-empty `NEED_TO_GORIYAKU_IDS["communication"]` (given the taxonomy has no fitting label at all), or should this be raised as a candidate for the "new taxonomy" conversation explicitly deferred by every task in this audit chain so far (out of scope for all of them, including this one)?
4. `mental`/`courage`: accept `{11,26}`/`{12,15,30}` (QUESTIONABLE-only, taxonomy-gap-limited) as the ceiling of what mapping alone can achieve, or treat these two as needing deeper product attention given neither has a clean canonical label?
5. Should `focus`'s adoption of `study`'s exact `{9,10}` set (Section 7/19) proceed under the existing shared-evidence precedent (id=1 today), or does Mother Ship want a distinct focus-specific `GoriyakuTag` label eventually (a "new taxonomy" question, out of scope for this audit and for any of its recommended near-term PRs)?

## 24. Limitations

- Semantic classifications (Section 6) are this audit's own first-pass reading of label meaning against runtime-authoritative Need boundaries (Section 5), not a Mother Ship-approved final classification — consistent with how the master-integrity audit's own 10-Purpose sweep was scoped.
- Section 16's alias finding was discovered via fresh code-reading during this task, not anticipated by the task's own phase structure — it materially changes how `marriage` must be treated (Section 19/20/22) relative to a naive reading of the task's Phase 10/17 rules, and is flagged prominently rather than silently folded into the standard SAFE_CORRECTIONS bucket.
- DB evidence (Section 10) and runtime simulation (Sections 13/14) were run against the local scratch DB (`shrine_dataset_audit_local`), not Production directly; both are expected to match Production's state (same seed source, same code) but this was not independently re-verified against Production.
- `communication`'s "no canonical tag exists" finding (Section 7) reflects an exhaustive read of the current 39-row master's labels; it does not evaluate whether a *new* tag would be appropriate (explicitly out of scope, constraint #3/#12).

## 25. Out of Scope

UI, frontend, C1 redesign, Text Evidence correction, Reason copy, Lead copy, Direction/Distance changes, new taxonomy, Production DB changes, implementation of any correction described in Sections 19–22, resolution of the `marriage`/`NEED_TAG_ALIASES` architecture question (Section 16/23).
