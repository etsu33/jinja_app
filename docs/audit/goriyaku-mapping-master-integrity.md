# Compass / Concierge Goriyaku Mapping Master Integrity Audit

> **Status**: AUDIT ONLY. `NEED_TO_GORIYAKU_IDS`, `GoriyakuTag`, `backfill_goriyaku_tags`, `NEED_TEXT_WEIGHTS`, C1, Ranking, Lead, Reason, Direction, Distance, consultation interpreter, Purpose taxonomy, Production DB, Production Seed, Knowledge Seed — all unchanged. No new tags, no migration, no frontend/UI change.

## 1. Scope

Determine the exact integrity state of the canonical `GoriyakuTag` master and `NEED_TO_GORIYAKU_IDS` mapping, across **all 15 Need tags** (not only the 5 Purposes — love/career/money/study/protection — corrected in `docs/audit/compass-purpose-goriyaku-mapping-correction.md`), before any correction PR is implemented. Triggered by the Batch 17 Recommendation Evidence Pilot's finding that canonical tag id=13 (`航海安全`) is `CANONICAL_BUT_UNMAPPED` and that `NEED_TO_GORIYAKU_IDS` references ids 42–45, which do not exist in the current 39-row master.

## 2. Base SHA

- Worktree: `/Users/morietsu/Developer/jinja_app-goriyaku-mapping-integrity`
- Branch: `audit/goriyaku-mapping-master-integrity`
- Created from `origin/develop` at `1c94c1a6286f3f1ed274c5871623e6efc7de8f0c` (`docs: Batch 17 Recommendation Evidence Review pilot (#2575)`), after PR #2575 — found still draft/unmerged at this task's Phase 0 — was merged with explicit Mother Ship authorization ("Merge PR #2575 first, then proceed").
- `git log --oneline c93f8ab0..1c94c1a6`: single commit, PR #2575 only. No unrelated changes.

## 3. Sources of Truth

Fresh-read this session: `docs/audit/batch17-recommendation-evidence-review.md`, `docs/knowledge/recommendation-evidence-review-contract.md` (both authored in immediately preceding session turns, re-confirmed unchanged), `backend/temples/domain/need_to_goriyaku_tag_ids.py`, `backend/temples/domain/need_tags.py` (full 15-tag taxonomy), `backend/temples/services/concierge_chat_ranking.py` (`NEED_TEXT_WEIGHTS`), `backend/temples/management/commands/backfill_goriyaku_tags.py`, `backend/temples/management/commands/bootstrap_production_data.py`.

**Newly read this session** (existed but never previously read in this audit chain): `docs/audit/compass-purpose-goriyaku-mapping.md` (the original 5-Purpose semantic audit, 307 lines) and `docs/audit/compass-purpose-goriyaku-mapping-correction.md` (its implementation record, 89 lines). These two documents are the direct ancestor of the current `NEED_TO_GORIYAKU_IDS` state and are treated as authoritative for the 5 Purposes they cover; **the current file's own comment confirms this**: `# love/career/money/study/protection corrected against real GoriyakuTag labels; see docs/audit/compass-purpose-goriyaku-mapping.md ... Other purposes intentionally left untouched (out of scope).`

**Authoritative current master source, confirmed (not assumed from old docs)**: `backend/temples/management/commands/backfill_goriyaku_tags.py`, dynamically populating `GoriyakuTag` via `get_or_create()` from `Shrine.goriyaku` free text, invoked by `bootstrap_production_data.py` (`step="backfill_goriyaku_tags"`, confirmed present at line 30/32, unchanged). The static fixture `backend/temples/fixtures/goriyaku_tags.json` (15 rows, pk 1–15, a different/older ID scheme) **remains confirmed dead code**: `grep -rn "goriyaku_tags\.json\|loaddata.*goriyaku"` across the repo returns 0 matches, re-verified this session.

## 4. Canonical Master

Fresh query, local scratch DB (`shrine_dataset_audit_local`, same seed source as Production):

| ID | Label | Shrine Count | ID | Label | Shrine Count | ID | Label | Shrine Count |
|---:|---|---:|---:|---|---:|---:|---|---:|
| 1 | 縁結び | 32 | 14 | 海上安全 | 4 | 27 | 出世運 | 2 |
| 2 | 厄除け | 51 | 15 | 武運長久 | 1 | 28 | 金運 | 2 |
| 3 | 交通安全 | 6 | 16 | 安産 | 5 | 29 | 芸能運 | 3 |
| 4 | 商売繁盛 | 16 | 17 | 八方除 | 1 | 30 | 強運厄除け | 1 |
| 5 | 五穀豊穣 | 3 | 18 | 夫婦円満 | 1 | 31 | 技芸上達 | 1 |
| 6 | 開運 | 59 | 19 | 八難除 | 1 | 32 | 八方除け | 1 |
| 7 | 家内安全 | 26 | 20 | 恋愛成就 | 4 | 33 | 病気平癒 | 1 |
| 8 | 福徳 | 1 | 21 | 導き | 1 | 34 | 火防 | 2 |
| 9 | 学業成就 | 8 | 22 | 美容 | 2 | 35 | 子宝 | 1 |
| 10 | 合格祈願 | 3 | 23 | 方除け | 1 | 36 | 心願成就 | 2 |
| 11 | 勝運 | 19 | 24 | 健康長寿 | 1 | 37 | 延命長寿 | 1 |
| 12 | 仕事運 | 11 | 25 | 芸能 | 1 | 38 | 足腰健康 | 1 |
| 13 | **航海安全** | **2** | 26 | 家庭円満 | 1 | 39 | 農業守護 | 1 |

**Total row count: 39. Min ID: 1. Max ID: 39. Gaps: none (contiguous 1–39). Duplicate labels: none (verified programmatically). Labels with zero Shrine relations: none (minimum shrine_count observed = 1).** This matches the prior pilot's baseline exactly — **current measurement, not carried forward.**

id=13 (航海安全) has **shrine_count=2 today**, independent of any Recommendation Evidence Review activity — i.e., 2 shrines already carry this tag via legacy `goriyaku` free text, meaning the Purpose-connectivity gap (Section 8) already affects real, existing shrines, not only the hypothetical Batch 17 candidate.

## 5. Current Need Mapping

Fresh-read of the full `NEED_TO_GORIYAKU_IDS` dict (all 15 Need tags, not just the previously-audited 5):

| Need Tag | Referenced IDs |
|---|---|
| love | {1, 20} |
| relationship | {1, 27, 34, 43} |
| marriage | {1, 27, 29} |
| communication | {30, 33, 37, 39} |
| career | {6, 21, 30, 12, 27} |
| money | {5, 36, 4, 28} |
| study | {9, 10} |
| health | {7, 8, 44, 45} |
| mental | {11, 16, 26, 28, 38, 43} |
| protection | {11, 32, 2} |
| courage | {12, 15, 18, 20, 24, 30, 38} |
| focus | {3, 4, 39} |
| rest | {7, 8, 43, 44, 45} |
| family | {2, 25, 27, 34, 42} |
| travel_safe | {10, 22, 23} |

All 15 `NEED_TAGS` (`backend/temples/domain/need_tags.py`, "15 tags fixed") have a non-empty entry — no Need tag is entirely absent from the mapping dict.

## 6. ID Integrity

**Total mapping references (sum of all set sizes across 15 Need tags): 60.**

| Classification | Count | IDs |
|---|---:|---|
| VALID_REFERENCE (id exists in master) | 52 | all referenced ids except 42/43/44/45 (33 distinct ids, 52 occurrences) |
| MISSING_MASTER_TAG (id does not exist) | 8 | 42 (family ×1), 43 (relationship, mental, rest ×3), 44 (health, rest ×2), 45 (health, rest ×2) |

**Unique missing IDs: 4 — {42, 43, 44, 45}.** Re-confirmed by fresh, full cross-reference of the entire dict against the 39-row master this session (Section 4), not carried forward from the prior pilot. No additional missing IDs found beyond these 4 across all 15 Need tags.

## 7. Missing ID Archaeology

`git log --oneline -- backend/temples/domain/need_to_goriyaku_tag_ids.py` (6 commits total, full history):

```
2070a600 / 1c5b9ef2  fix: Compass Purposeとご利益mappingを修正 (#2545)  — the 5-Purpose correction (Section 3)
b5f13ac0             rest候補から家内安全を除外 (#1446)
9d7e8a50             needタグとご利益タグの対応を追加 (#1445)         — ORIGINAL creation commit
```

The **original creation commit** (`9d7e8a50`, 2026-06-01) introduced ids 42/43/44/45 for the first time, alongside the entire 15-Purpose mapping, changing every Need tag from `set()` (or `{2}` for protection) to its first non-empty value. No commit message body or linked PR description beyond the title was found (`git log -1 --format=%B` returns only the title). `b5f13ac0` (same day, 26 minutes later) only removed id `9` from `rest` — it did not touch 42–45 and provides no archaeological evidence about their origin.

**Critical structural evidence** (from `docs/audit/compass-purpose-goriyaku-mapping-correction.md` line 23, its own author's words): *"`backfill_goriyaku_tags`はShrineの`goriyaku`テキスト解析順にIDを動的採番するため、フレッシュなtest DBでは監査時のID体系...を再現できない"* — the canonical master's ID numbering is **not a portable, stable ID space**. It is produced fresh by `get_or_create()` in Shrine-processing order every time the backfill command runs against a database, and depends on exactly which distinct `goriyaku` phrases exist and in what order they are first encountered. A DB rebuild, a different Shrine seed ordering, or different historical `goriyaku` text content can all produce a different maximum ID and different id→label assignments.

**Classification per missing ID**:

| ID | Classification | Reasoning |
|---:|---|---|
| 42 | **DIFFERENT_MASTER_SCHEME** | No direct evidence of a specific deleted/renamed label. Well-evidenced structural explanation: ids above the current max (39) are consistent with a prior backfill run (at or before 2026-06-01) having encountered more distinct `goriyaku` phrases, or encountered them in a different order, than the current master reflects. This is the repo's own documented architectural property (above), not speculation. |
| 43 | Same as 42 | Same reasoning; referenced by 3 Purposes (relationship, mental, rest), suggesting whatever label it once was may have been a broadly-applicable one, but this is not independently provable |
| 44 | Same as 42 | Same reasoning; referenced by 2 Purposes (health, rest) |
| 45 | Same as 42 | Same reasoning; referenced by 2 Purposes (health, rest) |

**No ID is classified HISTORICAL_TAG_IDENTIFIED, STALE_REFERENCE, or RENAMED_OR_RENUMBERED** — none of those classifications is provable without a snapshot of the master at commit time, which does not exist (the master was never a tracked file; it is DB-only, generated at runtime). Per constraint #23 and the task's explicit HOLD instruction, **the specific original label identity of 42/43/44/45 is UNKNOWN and not guessed.**

## 8. Unmapped Canonical Tags

Tags that exist in the master (Section 4) but are referenced by **no** Need tag's `NEED_TO_GORIYAKU_IDS` set (structural state only — mapping desirability evaluated separately in Section 10):

| Tag ID | Canonical Label | Shrine Count | Mapped Purpose Count |
|---:|---|---:|---:|
| 13 | 航海安全 | 2 | 0 — **UNMAPPED** |
| 14 | 海上安全 | 4 | 0 — **UNMAPPED** |
| 17 | 八方除 | 1 | 0 — **UNMAPPED** |
| 19 | 八難除 | 1 | 0 — **UNMAPPED** |
| 31 | 技芸上達 | 1 | 0 — **UNMAPPED** |
| 35 | 子宝 | 1 | 0 — **UNMAPPED** |

6 of 39 canonical tags (15%) are structurally unmapped. All other 33 tags are `MAPPED` (referenced by at least one Need tag).

## 9. Taxonomy Connectivity

Fresh-read `backend/temples/domain/need_tags.py`'s 15-tag list (Section 5) for a semantic home for id=13 `航海安全`:

- **`travel_safe`** — the Need tag's own name is literally "travel safety." Its current mapping is `{10, 22, 23}` = 合格祈願 (exam-passing, study-domain), 美容 (beauty), 方除け (directional misfortune warding). **None of these three is a travel-safety label.** Meanwhile 航海安全 ("voyage safety") and 海上安全 ("maritime safety", id=14) — both direct travel/voyage-safety labels — and 交通安全 (id=3, "traffic safety" — the single most literal match for "travel_safe") all exist in the master and are **not** referenced by `travel_safe`.
- No other Need tag (protection, health, family, etc.) has a comparably direct name-level match to "voyage/maritime safety."

**Result: `EXISTING_NEED_CLEAR_MATCH` — `travel_safe`.** This is not a "semantically close" inference (constraint #21) but a direct, name-level correspondence: the Need tag's own English identifier and the candidate labels' Japanese meanings denote the same category (travel/voyage safety), the same standard this audit applies to e.g. `study`↔学業成就 (Section 3's already-accepted VALID precedent). No new Need tag is proposed; `travel_safe` already exists in the runtime taxonomy and is currently mapped to unrelated labels.

## 10. Semantic Integrity

Classification (VALID/QUESTIONABLE/INVALID/UNKNOWN) for **every** current mapping reference across all 15 Need tags. The 5 previously-corrected Purposes (love/career/money/study/protection) are re-verified against the current file state (confirmed identical to the correction PR's intended output, Section 3) rather than assumed still valid.

| Need Tag | Reference | Classification | Reason |
|---|---|---|---|
| **love** | 1 縁結び | VALID | direct |
| | 20 恋愛成就 | VALID | direct (post-correction) |
| **career** | 6 開運, 21 導き, 30 強運厄除け | QUESTIONABLE ×3 | broad/general fortune, career-specificity weak (per original audit, unchanged) |
| | 12 仕事運, 27 出世運 | VALID ×2 | direct (post-correction) |
| **money** | 5 五穀豊穣, 36 心願成就 | QUESTIONABLE ×2 | agricultural/general-wish domain, indirect (per original audit, unchanged) |
| | 4 商売繁盛, 28 金運 | VALID ×2 | direct (post-correction) |
| **study** | 9 学業成就, 10 合格祈願 | VALID ×2 | direct (post-correction) |
| **protection** | 11 勝運 | QUESTIONABLE | "victory" nuance stronger than "warding/protection" (per original audit, unchanged) |
| | 32 八方除け, 2 厄除け | VALID ×2 | direct (2 added by correction) |
| **relationship** | 1 縁結び | VALID | direct |
| | 27 出世運 | **INVALID** *(new finding)* | career advancement, unrelated to interpersonal relationships |
| | 34 火防 | **INVALID** *(new finding)* | fire prevention, no semantic connection to relationships |
| | 43 | MISSING_MASTER_TAG | Section 7 |
| **marriage** | 1 縁結び | VALID | direct |
| | 27 出世運 | **INVALID** *(new finding)* | career, unrelated to marriage |
| | 29 芸能運 | **INVALID** *(new finding)* | performing-arts luck — this exact id was already classified INVALID for `love` in the original audit ("芸能・パフォーマンス運勢であり恋愛と無関係"); same problem recurs here for `marriage` |
| **communication** | 30 強運厄除け | QUESTIONABLE *(new finding)* | no direct link, broad fortune tag |
| | 33 病気平癒 | **INVALID** *(new finding)* | illness recovery, unrelated |
| | 37 延命長寿 | **INVALID** *(new finding)* | longevity, unrelated |
| | 39 農業守護 | **INVALID** *(new finding)* | agricultural protection, unrelated |
| **health** | 7 家内安全, 8 福徳 | QUESTIONABLE ×2 *(new finding)* | household-safety / general-fortune, indirect for personal health |
| | 44, 45 | MISSING_MASTER_TAG | Section 7. **Direct matches 健康長寿(24)/病気平癒(33) exist in master and are unused by `health`** |
| **mental** | 11 勝運, 26 家庭円満 | QUESTIONABLE ×2 *(new finding)* | indirect |
| | 16 安産, 28 金運, 38 足腰健康 | **INVALID** ×3 *(new finding)* | childbirth / money / leg-health, all unrelated to mental wellbeing |
| | 43 | MISSING_MASTER_TAG | Section 7 |
| **courage** | 12 仕事運, 15 武運長久, 24 健康長寿, 30 強運厄種け | QUESTIONABLE ×4 *(new finding)* | indirect but plausible (backing/fortune-adjacent) |
| | 18 夫婦円満, 38 足腰健康 | **INVALID** ×2 *(new finding)* | marital harmony / leg-health, unrelated |
| | 20 恋愛成就 | **INVALID** *(new finding)* | romantic fulfillment, unrelated to courage — and cross-purpose duplicate of `love`'s (correctly) VALID use of the same id |
| **focus** | 3 交通安全, 4 商売繁盛, 39 農業守護 | **INVALID** ×3 *(new finding)* | **Identical set to `study`'s pre-correction, already-INVALID mapping** (`{3,4,39}` — see Section 3's `Before` column). This is the single highest-confidence finding in this audit: `focus` was never updated when `study` was corrected, and still carries `study`'s old broken mapping verbatim |
| **rest** | 7 家内安全, 8 福徳 | QUESTIONABLE ×2 *(new finding)* | indirect; no canonical "rest/relaxation" label exists in the master at all (confirmed by `NEED_TEXT_WEIGHTS["rest"]` vocabulary — 休息/癒し/静か/リセット — none of which has a matching `GoriyakuTag`) |
| | 43, 44, 45 | MISSING_MASTER_TAG ×3 | Section 7. **60% of this Purpose's mapping is phantom IDs** |
| **family** | 2 厄除け, 34 火防 | QUESTIONABLE ×2 *(new finding)* | indirect (household protection broadly) |
| | 25 芸能, 27 出世運 | **INVALID** ×2 *(new finding)* | performing arts / career, unrelated to family |
| | 42 | MISSING_MASTER_TAG | Section 7. **Direct match 家庭円満(26) exists in master, currently misused by `mental` (QUESTIONABLE there) instead of used here (would be VALID)** |
| **travel_safe** | 10 合格祈願 | **INVALID** *(new finding)* | exam-passing, unrelated — and cross-purpose duplicate of `study`'s (correctly) VALID use of the same id |
| | 22 美容 | **INVALID** *(new finding)* | beauty, unrelated |
| | 23 方除け | QUESTIONABLE *(new finding)* | directional misfortune warding, loosely travel-adjacent historically |
| | *(none currently)* | — | **交通安全(3)/航海安全(13)/海上安全(14) all exist, unused by `travel_safe` — see Section 9** |

**Cross-purpose duplication pattern** (mirrors the original audit's id=4/id=28 finding, now found at larger scale): id=20 (love VALID / courage INVALID), id=27 (career VALID / relationship INVALID / family INVALID), id=34 (relationship INVALID / family QUESTIONABLE), id=10 (study VALID / travel_safe INVALID). In each case the same tag ID is correctly used by one Purpose and incorrectly reused by another — consistent with the original audit's hypothesis that "IDs were confused between Purposes during mapping authorship," now observed across a wider set of Purposes than originally audited.

## 11. Full Need × Tag Matrix

Consolidated, separating **Structural Integrity** (does the tag exist?) from **Semantic Integrity** (does the label belong to that Need?) per the task's explicit instruction not to collapse them:

| Need | Tag ID | Label | Structural Integrity | Semantic Integrity |
|---|---:|---|---|---|
| love | 1 | 縁結び | VALID_REFERENCE | VALID |
| love | 20 | 恋愛成就 | VALID_REFERENCE | VALID |
| relationship | 1 | 縁結び | VALID_REFERENCE | VALID |
| relationship | 27 | 出世運 | VALID_REFERENCE | INVALID |
| relationship | 34 | 火防 | VALID_REFERENCE | INVALID |
| relationship | 43 | — | **MISSING_MASTER_TAG** | N/A |
| marriage | 1 | 縁結び | VALID_REFERENCE | VALID |
| marriage | 27 | 出世運 | VALID_REFERENCE | INVALID |
| marriage | 29 | 芸能運 | VALID_REFERENCE | INVALID |
| communication | 30 | 強運厄除け | VALID_REFERENCE | QUESTIONABLE |
| communication | 33 | 病気平癒 | VALID_REFERENCE | INVALID |
| communication | 37 | 延命長寿 | VALID_REFERENCE | INVALID |
| communication | 39 | 農業守護 | VALID_REFERENCE | INVALID |
| career | 6,21,30 | 開運/導き/強運厄除け | VALID_REFERENCE ×3 | QUESTIONABLE ×3 |
| career | 12,27 | 仕事運/出世運 | VALID_REFERENCE ×2 | VALID ×2 |
| money | 5,36 | 五穀豊穣/心願成就 | VALID_REFERENCE ×2 | QUESTIONABLE ×2 |
| money | 4,28 | 商売繁盛/金運 | VALID_REFERENCE ×2 | VALID ×2 |
| study | 9,10 | 学業成就/合格祈願 | VALID_REFERENCE ×2 | VALID ×2 |
| health | 7,8 | 家内安全/福徳 | VALID_REFERENCE ×2 | QUESTIONABLE ×2 |
| health | 44,45 | — | **MISSING_MASTER_TAG** ×2 | N/A |
| mental | 11,26 | 勝運/家庭円満 | VALID_REFERENCE ×2 | QUESTIONABLE ×2 |
| mental | 16,28,38 | 安産/金運/足腰健康 | VALID_REFERENCE ×3 | INVALID ×3 |
| mental | 43 | — | **MISSING_MASTER_TAG** | N/A |
| protection | 11 | 勝運 | VALID_REFERENCE | QUESTIONABLE |
| protection | 32,2 | 八方除け/厄除け | VALID_REFERENCE ×2 | VALID ×2 |
| courage | 12,15,24,30 | 仕事運/武運長久/健康長寿/強運厄除け | VALID_REFERENCE ×4 | QUESTIONABLE ×4 |
| courage | 18,38,20 | 夫婦円満/足腰健康/恋愛成就 | VALID_REFERENCE ×3 | INVALID ×3 |
| focus | 3,4,39 | 交通安全/商売繁盛/農業守護 | VALID_REFERENCE ×3 | **INVALID ×3 (100%)** |
| rest | 7,8 | 家内安全/福徳 | VALID_REFERENCE ×2 | QUESTIONABLE ×2 |
| rest | 43,44,45 | — | **MISSING_MASTER_TAG ×3 (60%)** | N/A |
| family | 2,34 | 厄除け/火防 | VALID_REFERENCE ×2 | QUESTIONABLE ×2 |
| family | 25,27 | 芸能/出世運 | VALID_REFERENCE ×2 | INVALID ×2 |
| family | 42 | — | **MISSING_MASTER_TAG** | N/A |
| travel_safe | 23 | 方除け | VALID_REFERENCE | QUESTIONABLE |
| travel_safe | 10,22 | 合格祈願/美容 | VALID_REFERENCE ×2 | INVALID ×2 |

## 12. Current Data Impact

| Gap | Affected Tag | Shrine Count | Current Purpose Gain Lost |
|---|---|---:|---:|
| Missing mapped ID (42) | *(no tag — id doesn't exist)* | 0 (structurally impossible; measured, not assumed) | 0 |
| Missing mapped ID (43) | *(no tag)* | 0 | 0 |
| Missing mapped ID (44) | *(no tag)* | 0 | 0 |
| Missing mapped ID (45) | *(no tag)* | 0 | 0 |
| Canonical unmapped tag | 航海安全 (id 13) | **2** (existing legacy shrines) **+ 1** (波上宮, Batch 17 PASS candidate, not yet in Production — Section 13) | 3 shrines' evidence cannot create `travel_safe` Purpose coverage today |
| Canonical unmapped tag | 海上安全 (id 14) | 4 (existing legacy shrines) | 4 shrines' evidence cannot create `travel_safe` Purpose coverage today, same root cause |
| Semantic misassignment | 交通安全 (id 3, currently only in `focus`, INVALID there) | 6 | `travel_safe`'s single most literal candidate label is entirely unused by `travel_safe` |

No unapproved mapping was simulated to produce these numbers — all counts are direct `GoriyakuTag`-to-`Shrine` relation counts (Section 4) or direct references to the Batch 17 pilot's already-recorded PASS item (Section 13).

## 13. Batch 17 / 波上宮 Impact

Re-evaluated per `docs/audit/batch17-recommendation-evidence-review.md`:

- PASS Recommendation Evidence: "航海の平安を祈り" (H3, `source_confirmed`)
- Canonical tag: 航海安全
- Tag ID: 13
- Current Purpose connectivity: `CANONICAL_BUT_UNMAPPED` (re-confirmed, Section 8)
- Likely existing Need target if CLEAR: **`travel_safe`** (Section 9, `EXISTING_NEED_CLEAR_MATCH`)
- Whether mapping integrity blocks Recommendation readiness: **Yes, for Purpose-matching specifically** — the evidence itself remains valid and reviewed (Gate A, unaffected); only Gate B (Purpose Connectivity) is blocked

**Result: `BLOCKED_BY_MAPPING`.** Distinct from `SEMANTIC_ONLY_NO_PURPOSE` (which would imply no reasonable existing-taxonomy fix exists) — here a specific, well-evidenced fix path exists (Section 9), it simply has not been implemented, and this audit does not implement it. Evidence is not activated in this task (constraint #24).

## 14. Compass / Concierge Shared Impact

Traced: `NEED_TO_GORIYAKU_IDS` → `need_tags_to_goriyaku_ids()` → `_prefilter_candidates_for_need()` / `_attach_breakdown()` in `backend/temples/services/concierge_chat_ranking.py` — the same functions both Compass (`get_compass_recommendations`) and Concierge (`build_chat_recommendations`) call, re-confirmed unchanged this session (identical to every prior fresh-read this session and the immediately preceding two tasks). Every finding in Sections 6–11 (missing IDs, unmapped tags, semantic misassignments) is read from this single shared dict — there is no Compass-specific or Concierge-specific copy or override.

**Result: `SHARED_IMPACT`.** Every gap found in this audit affects both engines identically and simultaneously; none is engine-specific.

## 15. Need Health Matrix

| Need | Valid Mapping Count | Missing Count | Invalid Count | Health |
|---|---:|---:|---:|---|
| love | 2 | 0 | 0 | **HEALTHY** |
| study | 2 | 0 | 0 | **HEALTHY** |
| career | 2 | 0 | 0 (3 QUESTIONABLE) | PARTIAL |
| money | 2 | 0 | 0 (2 QUESTIONABLE) | PARTIAL |
| protection | 2 | 0 | 0 (1 QUESTIONABLE) | PARTIAL |
| relationship | 1 | 1 | 2 | BROKEN |
| marriage | 1 | 0 | 2 | BROKEN |
| communication | 0 | 0 | 3 (1 QUESTIONABLE) | BROKEN |
| health | 0 | 2 | 0 (2 QUESTIONABLE) | BROKEN |
| mental | 0 | 1 | 3 (2 QUESTIONABLE) | BROKEN |
| courage | 0 | 0 | 3 (4 QUESTIONABLE) | BROKEN |
| focus | 0 | 0 | **3 (100%)** | BROKEN |
| rest | 0 | 3 | 0 (2 QUESTIONABLE) | BROKEN |
| family | 0 | 1 | 2 (2 QUESTIONABLE) | BROKEN |
| travel_safe | 0 | 0 | 2 (1 QUESTIONABLE) | BROKEN |

**HEALTHY: 2. PARTIAL: 3. BROKEN: 10. UNMAPPED (empty set): 0.**

**This is the audit's most consequential finding**: the original correction PR explicitly scoped itself to 5 of 15 Purposes ("Other purposes intentionally left untouched (out of scope)"). This audit confirms that scoping decision left **10 of 15 Purposes (67%) structurally BROKEN**, unaudited since the mapping's original authorship on 2026-06-01 — a materially larger integrity gap than the "ids 42–45 + id=13" framing that motivated this task alone would suggest. This matters directly for natural-language Concierge coverage: 8 of these 10 broken Purposes (all except mental and rest) also have **zero `NEED_TEXT_WEIGHTS` coverage** (Section 5's cross-check), meaning Concierge has no text-based fallback compensation for their broken GID mapping either — unlike `study`/`money` in the original 5, where text coverage fully compensated for mapping errors even before the correction shipped.

## 16. Correction Feasibility

| Gap | Feasibility |
|---|---|
| ids 42/43/44/45 stale references | **SAFE_CORRECTION_AVAILABLE** — removing references to nonexistent ids is a pure subtraction, no new data needed, matches Option A's precedent exactly |
| id=13 (航海安全) unmapped, `travel_safe` misassigned | **SAFE_CORRECTION_AVAILABLE** — Section 9's `EXISTING_NEED_CLEAR_MATCH` gives a specific, evidenced replacement using only existing tags (3, 13, 14) and the existing Need tag, no new taxonomy |
| The other 8 BROKEN Purposes' QUESTIONABLE/INVALID entries (relationship, marriage, communication, health, mental, courage, family) | **CORRECTION_REQUIRES_PRODUCT_DECISION** — several MISSING-candidate labels are clear (e.g. 家庭円満→family, 健康長寿/病気平癒→health) mirroring the original 5-Purpose pattern, but a full pass needs the same rigor (DB evidence + simulation) as `compass-purpose-goriyaku-mapping.md` applied to the original 5, which this audit did not execute for these 8 (would exceed this task's scope) |
| Whether 42–45's original intended labels can be restored | **MASTER_RECONCILIATION_REQUIRED** if restoration (as opposed to removal) is desired — no unique current-ID replacement is provable (Section 7) |

## 17. id 42–45 Decision

| ID | Referencing Need(s) | Historical label known? | Current canonical equivalent exists? | Replacement uniquely provable? | Safe action |
|---:|---|---|---|---|---|
| 42 | family | No | Unknown — no evidence links it to any specific current tag | No | **REMOVE_STALE_REFERENCE** (or `HOLD_FOR_TAXONOMY_DECISION` if `family`'s broader semantic gaps, Section 15, are addressed together) |
| 43 | relationship, mental, rest | No | Unknown | No | **REMOVE_STALE_REFERENCE** |
| 44 | health, rest | No | Unknown | No | **REMOVE_STALE_REFERENCE** |
| 45 | health, rest | No | Unknown | No | **REMOVE_STALE_REFERENCE** |

No id is classified `RESTORE_MASTER_TAG_REQUIRES_SEPARATE_DECISION` — restoration is not recommended, since there is zero evidence identifying what any of these ids denoted (Section 7); removal (of the dangling reference only, not of any live data) is the safe default absent that evidence. This audit does not take the action.

## 18. 航海安全 Decision

- Exists in master? **Yes** (id 13, Section 4)
- Shrine count: **2**
- Recommendation Evidence use: **1 reviewed PASS item** (波上宮, Batch 17 pilot, Gate A succeeded — `docs/audit/batch17-recommendation-evidence-review.md`)
- Existing Need semantic match: **`travel_safe`** (Section 9, direct name-level correspondence)
- Candidate mapping: add `13` (and, by the same evidence, `3` and `14`) to `travel_safe`'s set, replacing its current `{10, 22, 23}` (all INVALID/QUESTIONABLE per Section 10)
- Confidence: **High** — based on the Need tag's own name, not inference from shrine reputation, deity, or general knowledge

**Result: `SAFE_EXISTING_NEED_MAPPING_AVAILABLE`.** No mapping is added in this task.

## 19. Regression Boundary

Any future correction PR must preserve:

- love mapping `{1, 20}` unchanged
- career mapping `{6, 21, 30, 12, 27}` unchanged unless independently proven (Section 16 does not propose changing it)
- money mapping `{5, 36, 4, 28}` unchanged
- study `{9, 10}` unchanged
- protection `{11, 32, 2}` unchanged
- C1 Max, Ranking weights, Reason generation, Lead generation, Direction filter, Distance boundary — all unchanged (none inspected for modification in this audit)
- the existing Recommendation Evidence Review Contract (`docs/knowledge/recommendation-evidence-review-contract.md`) — unchanged
- unrelated Need mappings (any Need tag not explicitly included in a given correction PR's stated scope) — unchanged
- no new `GoriyakuTag` rows
- no Production/local DB writes
- no N+1 query introduction in any future implementation

## 20. PR Options

- **Option A (Structural Integrity Only)**: remove references to ids 42/43/44/45 across relationship/mental/health/rest/family. Safety: high (pure subtraction, zero new data). Scope: 5 Need tags' sets shrink by 1 element each (mental/rest lose 2-3 elements). Regression risk: near-zero — these ids never matched anything (structurally impossible, Section 12), so removing them changes no runtime behavior at all, only removes dead references. Auditability: high. Recommendation impact: **zero measurable change** (these ids matched 0 shrines before and after). Rollback: trivial.
- **Option B (Structural + Clear Unmapped Canonical Tags)**: Option A + add id=13 (and by the same evidence, 3/14) to `travel_safe`, replacing its current INVALID/QUESTIONABLE set. Safety: high — Section 9's evidence is as strong as the original audit's VALID-classification standard. Scope: 6 Need tags touched. Regression risk: low, isolated to `travel_safe`'s own candidate pool (currently 0 real matches per Section 12, so this can only add coverage, not remove any existing real match). Recommendation impact: **real, measurable** — connects 2 existing + 1 pending shrine to a Purpose that currently matches nothing.
- **Option C (Full Mapping Semantic Cleanup)**: revisit all QUESTIONABLE/unused labels across the 10 BROKEN Purposes found in Section 15. Safety: medium — requires the same DB-evidence + simulation rigor as the original 5-Purpose audit, not yet performed for these 10. Scope: large (up to 8 Purposes' worth of INVALID removal + MISSING addition). This is effectively a **second full audit**, not a direct implementation step.
- **Option D (Split PRs)**: PR-1 = Option A+B combined (structural + the one clear semantic addition); PR-2 = a new, dedicated semantic audit (mirroring `compass-purpose-goriyaku-mapping.md`'s methodology exactly) for the remaining 8 BROKEN Purposes; PR-3 = that audit's own correction PR, once produced.

Comparison favors **Option D**: PR-1 (structural + travel_safe) is safe, small, immediately actionable, and fully evidenced by this audit alone — no further research needed. Option C's remaining scope (8 Purposes) is real and substantial (Section 15) but requires dedicated audit work this task did not perform (constraint: audit only, and even a full semantic pass for 8 Purposes would itself warrant its own document, following the precedent this repository already set for the original 5).

## 21. Recommendation

**`STRUCTURAL_PLUS_CLEAR_MAPPING`** — for the immediate next PR (Option D's PR-1: Option A + B combined). This is the smallest safe change that is both fully evidenced by this audit and immediately implementable without further research.

**Exact next implementation PR scope**: modify `backend/temples/domain/need_to_goriyaku_tag_ids.py` only —
1. Remove `43` from `relationship`, `mental`, `rest`; remove `44`/`45` from `health`, `rest`; remove `42` from `family` (Section 17)
2. Replace `travel_safe`'s `{10, 22, 23}` with `{3, 13, 14}` (Section 18)
3. No other Need tag's set changes
4. New tests mirroring `test_need_to_goriyaku_tag_ids.py`'s existing pattern (exact-set assertions for the 6 touched Need tags + an unchanged-assertion for the other 9)

**Separately**, given Section 15's finding (10 of 15 Purposes BROKEN, 67% of the taxonomy), this audit recommends a **second, dedicated Mapping Semantic Audit** — scoped to the remaining 8 Purposes (relationship, marriage, communication, health, mental, courage, family — travel_safe addressed by this PR) — mirroring `docs/audit/compass-purpose-goriyaku-mapping.md`'s exact methodology (DB shrine-count evidence, `patch.dict` simulation, VALID/QUESTIONABLE/INVALID/MISSING classification) before any correction to those Purposes is implemented. This is Option D's PR-2, a Mother Ship decision (Section 22), not started by this task.

## 22. Mother Ship Decision Inputs

1. Should the `STRUCTURAL_PLUS_CLEAR_MAPPING` PR (Section 21, scope 1–4) be implemented next?
2. Should a second, dedicated Mapping Semantic Audit be commissioned for the remaining 8 BROKEN Purposes (relationship, marriage, communication, health, mental, courage, family), mirroring the original 5-Purpose audit's methodology?
3. Should the `focus`={3,4,39} finding (Section 10 — identical to `study`'s pre-correction broken set) be treated as a priority within that follow-up audit, given its unusually high confidence (100% INVALID, exact match to an already-solved prior case)?
4. Should `NEED_TEXT_WEIGHTS` coverage for the 8 text-uncovered Purposes (relationship, marriage, communication, health, protection, focus, family, travel_safe) be scoped as a parallel or follow-on track (out of this audit's scope, but directly informs Concierge's natural-language coverage per Section 15)?
5. Should the dead static fixture `backend/temples/fixtures/goriyaku_tags.json` (confirmed unused, Section 3) be removed in a separate, trivial cleanup PR?

## 23. Limitations

- This audit performed semantic classification (VALID/QUESTIONABLE/INVALID) for 10 previously-unaudited Purposes based on label meaning alone, without the DB-evidence-with-simulation rigor (`patch.dict` Before/After Top3 comparison) the original 5-Purpose audit used. The classifications in Section 10/11 should be treated as a first-pass finding requiring the same simulation-based verification before implementation, consistent with Section 21's recommended second audit.
- The archaeology in Section 7 establishes a well-evidenced *mechanism* (dynamic, run-order-dependent ID assignment) for why ids 42–45 are missing, but cannot and does not claim to know their original label identity — this is an honest `DIFFERENT_MASTER_SCHEME`/`UNKNOWN` classification, not a resolved one.
- GoriyakuTag master (39 rows) and `NEED_TO_GORIYAKU_IDS` were re-verified against the local scratch DB and `develop`'s tracked code this session, not against Production directly.
- This audit does not verify whether Production's `GoriyakuTag` master matches the local scratch DB's 39-row state exactly (both are seeded from the same tracked fixtures and the same `bootstrap_production_data.py` orchestration, so a match is expected but not independently re-confirmed here).

## 24. Out of Scope

UI, frontend, Recommendation Evidence data activation (the 波上宮 PASS item remains un-activated, per `batch17-recommendation-evidence-review.md`'s own STOP), Batch 18 Fact Generation, new Need/Purpose taxonomy, Engine/scoring redesign, DB master mutation, C1/Ranking/Lead/Reason/Direction/Distance/consultation-interpreter changes, implementation of any correction described in Sections 20–21.
