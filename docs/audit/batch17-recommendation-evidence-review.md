# Batch 17 Recommendation Evidence Review (Pilot)

> **Status**: REVIEW / AUDIT ONLY. This is the first operational run of `docs/knowledge/recommendation-evidence-review-contract.md` against real Batch 17 Source content. No `Shrine.goriyaku` write, no `GoriyakuTag` M2M write, no new tag, no Mapping change, no Engine change, no Production DB write. Does not continue into Evidence Production Import. Does not start Batch 18.

## 1. Scope

Execute `docs/knowledge/recommendation-evidence-review-contract.md` against the three Batch 17 shrines (北海道神宮・建部大社・波上宮) to validate whether the Contract produces reproducible, non-speculative PASS/HOLD/NO_EVIDENCE/REVISE decisions, and to trace any PASS item through to actual Purpose connectivity — keeping **Evidence Review success** (Gate A) and **Purpose Connectivity success** (Gate B) explicitly separate throughout, per the Contract's own architecture.

## 2. Base SHA

- Worktree: `/Users/morietsu/Developer/jinja_app-batch17-recommendation-evidence`
- Branch: `review/batch17-recommendation-evidence`
- Created from `origin/develop` at `c93f8ab091e2c583664e95a18d3e20c61b178282` (`docs: define Recommendation Evidence Review contract (#2574)`).
- `git log --oneline a592c82f..c93f8ab0`: `c93f8ab0` (PR #2574) ← `e36e906a` (`主要5画面をDark UIへ統一 (#2573)`, unrelated concurrent frontend work). `git diff a592c82f c93f8ab0 -- backend/` returns 0 lines — confirms zero backend drift since the Contract PR; only frontend Dark UI token changes landed alongside it.

## 3. Contract Source of Truth

Fresh-read of `docs/knowledge/recommendation-evidence-review-contract.md` (unchanged since authored in the immediately preceding session turn). Definitions used verbatim, not redefined:

- **ELIGIBLE_EXPLICIT**: Source explicitly states a blessing/benefit category. **REVIEW_REQUIRED**: semantically related material, no explicit statement (anecdote, deity association, tradition). **INELIGIBLE**: model knowledge, name inference, popularity, tourism copy. **UNKNOWN**: Source text unavailable/insufficient.
- **PASS**: explicit evidence + clean canonical mapping. **HOLD**: evidentiary ambiguity or no clean canonical match. **NO_EVIDENCE**: Source reviewed in full, no explicit content. **REVISE**: evidence sound, wording/label needs correction.
- **RECOMMENDATION_READY**: ≥1 PASS item, Purpose-wired. **PARTIALLY_READY**: ≥1 PASS item exists, review incomplete or item not yet confirmed Purpose-wired. **NO_RECOMMENDATION_EVIDENCE**: review complete, all NO_EVIDENCE.

## 4. Canonical GoriyakuTag Baseline

Fresh-read against the local scratch DB (`shrine_dataset_audit_local`), same seed source as Production, re-verified this session.

**Master table** (39 rows, ids 1–39, contiguous, no gaps):

| ID | Label | ID | Label | ID | Label |
|---:|---|---:|---|---:|---|
| 1 | 縁結び | 14 | 海上安全 | 27 | 出世運 |
| 2 | 厄除け | 15 | 武運長久 | 28 | 金運 |
| 3 | 交通安全 | 16 | 安産 | 29 | 芸能運 |
| 4 | 商売繁盛 | 17 | 八方除 | 30 | 強運厄除け |
| 5 | 五穀豊穣 | 18 | 夫婦円満 | 31 | 技芸上達 |
| 6 | 開運 | 19 | 八難除 | 32 | 八方除け |
| 7 | 家内安全 | 20 | 恋愛成就 | 33 | 病気平癒 |
| 8 | 福徳 | 21 | 導き | 34 | 火防 |
| 9 | 学業成就 | 22 | 美容 | 35 | 子宝 |
| 10 | 合格祈願 | 23 | 方除け | 36 | 心願成就 |
| 11 | 勝運 | 24 | 健康長寿 | 37 | 延命長寿 |
| 12 | 仕事運 | 25 | 芸能 | 38 | 足腰健康 |
| 13 | **航海安全** | 26 | 家庭円満 | 39 | 農業守護 |

**`NEED_TO_GORIYAKU_IDS` cross-reference** (fresh-read `backend/temples/domain/need_to_goriyaku_tag_ids.py`, unchanged):

| Tag ID | Canonical label if present | Referenced Purpose(s) | Exists in master? |
|---:|---|---|---|
| 1,2,3,4,5,6,7,8,9,10,11,12,15,16,18,20,21,22,23,24,25,26,27,28,29,30,32,33,34,36,37,38,39 | (as above) | love/relationship/marriage/communication/career/money/study/health/mental/protection/courage/focus/rest/family/travel_safe (33 distinct ids, spread across all 15 Purposes) | Yes — HEALTHY |
| 42 | — | `family` | **No — MAPPING_REFERENCES_MISSING_TAG** |
| 43 | — | `relationship`, `mental`, `rest` | **No — MAPPING_REFERENCES_MISSING_TAG** |
| 44 | — | `health`, `rest` | **No — MAPPING_REFERENCES_MISSING_TAG** |
| 45 | — | `health`, `rest` | **No — MAPPING_REFERENCES_MISSING_TAG** |
| 13 (航海安全) | 航海安全 | *(none — not referenced by any `NEED_TO_GORIYAKU_IDS` entry)* | Yes, but **CANONICAL_BUT_UNMAPPED** |
| 14, 17, 19, 31, 35 | 海上安全, 八方除, 八難除, 技芸上達, 子宝 | *(none)* | Yes, but **CANONICAL_BUT_UNMAPPED** |

Re-check requested by task: **id=13 (航海安全) exists in the master (confirmed) and is CANONICAL_BUT_UNMAPPED (confirmed — no `NEED_TO_GORIYAKU_IDS` entry references 13). ids 42/43/44/45 are all confirmed MAPPING_REFERENCES_MISSING_TAG** — none exists in the current 39-row master.

## 5. Mapping Master Integrity

See Section 4. Both findings from PR #2572/#2574's Limitations sections are **re-confirmed, not newly discovered**, via direct fresh code/DB inspection this session (not carried forward from memory).

## 6. 北海道神宮 Source Inventory

| Source key | source_type | URL | verification_status / confidence | Text availability |
|---|---|---|---|---|
| `batch17-hokkaidojingu-official` | shrine_official | hokkaidojingu.or.jp/history.html | source_confirmed / high | Full text preserved in `batch_17_seed.json` |

4 `deity` entries (大国魂神・大那牟遅神・少彦名神・明治天皇, all `role: unknown`) — **classified INELIGIBLE as standalone Recommendation Evidence candidates** (constraint #14: no deity→benefit inference; deity identity alone is never Recommendation Evidence under Contract §3). Not entered into the decision table below.

3 `shrine_history` entries, all `source_confirmed`, all citing the same Source:

| Item | Content | Evidence classification |
|---|---|---|
| H1 (founding) | "明治2年9月1日、明治天皇の聖旨により…北海道鎮座神祭が斎行された。" | INELIGIBLE-content — pure administrative/ceremonial dating, no benefit language |
| H2 (historical_event) | "明治4年5月に社名が札幌神社と定められ…遷座祭が行われた。" | INELIGIBLE-content — renaming/relocation record only |
| H3 (historical_event) | "昭和39年に明治天皇が増祀され…北海道神宮へ改称された。" | INELIGIBLE-content — renaming record only |

No `SOURCE_TEXT_REQUIRED` items — the single Source's full text is preserved and was reviewed in full.

## 7. 北海道神宮 Review

| Shrine | Source | Source Evidence | Proposed canonical Goriyaku | Existing Tag | Decision | Reason |
|---|---|---|---|---|---|---|
| 北海道神宮 | `batch17-hokkaidojingu-official` | H1: enshrinement ceremony narrative | — | — | **NO_EVIDENCE** | No blessing/benefit statement anywhere in the text |
| 北海道神宮 | `batch17-hokkaidojingu-official` | H2: renaming to 札幌神社, relocation | — | — | **NO_EVIDENCE** | Administrative record only |
| 北海道神宮 | `batch17-hokkaidojingu-official` | H3: renaming to 北海道神宮 | — | — | **NO_EVIDENCE** | Administrative record only |

PASS=0, HOLD=0, NO_EVIDENCE=3, REVISE=0.

**Final Evidence Status: NO_RECOMMENDATION_EVIDENCE.** Fully reviewed; no PASS forced (per Contract's explicit instruction — NO_EVIDENCE is a valid, terminal, non-speculative outcome).

**Purpose Connectivity: NO_PASS_EVIDENCE** (no PASS item exists to trace).

## 8. 建部大社 Source Inventory

| Source key | source_type | URL | verification_status / confidence | Text availability |
|---|---|---|---|---|
| `batch17-takebetaisha-official-about` | shrine_official | takebetaisha.jp/about/ | source_confirmed / high | Full text preserved |
| `batch17-takebetaisha-official-highlights` | shrine_official | takebetaisha.jp/features/ | **disputed** (per its one citing item) / high | Full text preserved |
| `batch17-takebetaisha-japan-heritage` | government | japan-heritage.bunka.go.jp | **disputed** (per its one citing item) / high | Full text preserved |

2 `deity` entries (日本武尊・大己貴命, `role: unknown`) — **INELIGIBLE as standalone evidence**, same rule as Section 6. Not entered below.

4 `shrine_history` entries:

| Item | Content | Evidence classification |
|---|---|---|
| H1 (tradition, source_confirmed) | "景行天皇46年（西暦116年）、日本武尊の功績をたたえ…社殿を創建して…" | INELIGIBLE-content — founding legend, no benefit statement |
| H2-A (tradition, **disputed**) | "白鳳4年（675年）に瀬田へ遷し祀られた" | INELIGIBLE-content (no benefit language) **and** barred by `disputed` status regardless (Contract §3, Recommendation Contract: disputed Facts never used) |
| H2-B (tradition, **disputed**) | "天武天皇4年（676年）に現在地へ移されたと伝わる" | Same as H2-A |
| H4 (tradition, source_confirmed) | "源頼朝が平家に捕らわれた際に当社で前途を祈願し、後に源氏再興を果たして再び参拝し、神宝と神領を寄進した" | **REVIEW_REQUIRED** — a specific historical figure's prayer act and a subsequent narrated outcome (clan restoration), but no explicit blessing-category word (no "開運"/"出世運"/"仕事運" or equivalent term anywhere in the sentence) |

No `SOURCE_TEXT_REQUIRED` items.

## 9. 建部大社 Review

| Shrine | Source | Source Evidence | Proposed canonical Goriyaku | Existing Tag | Decision | Reason |
|---|---|---|---|---|---|---|
| 建部大社 | `batch17-takebetaisha-official-about` | H1: founding legend | — | — | **NO_EVIDENCE** | No benefit statement |
| 建部大社 | `batch17-takebetaisha-official-highlights` | H2-A: 675年 relocation (disputed) | — | — | **NO_EVIDENCE** | No benefit statement; also `disputed`, barred independently |
| 建部大社 | `batch17-takebetaisha-japan-heritage` | H2-B: 676年 relocation (disputed) | — | — | **NO_EVIDENCE** | Same as H2-A |
| 建部大社 | `batch17-takebetaisha-official-about` | H4: Yoritomo prayer-then-restoration anecdote | *(candidate, unresolved)* | *(candidate: 出世運 id27 / 仕事運 id12 / 開運 id6 — none confirmed)* | **HOLD** | Fact correctness ≠ Recommendation eligibility (Contract §3): the anecdote narrates a specific outcome for a specific historical figure, not a Source-stated blessing category available to worshippers generally. Converting "prayed, then later succeeded" into any of the plausible career-adjacent labels would require the reviewer to supply the categorization the Source itself never states — exactly the Interpretation→Fact conversion the Contract prohibits (constraint #16, #17). Multiple candidate labels are also plausible with no clear single winner, an independent HOLD trigger (Contract §4). |

PASS=0, HOLD=1, NO_EVIDENCE=3, REVISE=0.

**Final Evidence Status: HOLD.** No PASS exists; at least one item (H4) remains HOLD; the historical-Fact confidence of H4 (`source_confirmed`) was explicitly **not** reused as Recommendation-eligibility confidence, per Contract §3 and this task's instruction.

**Purpose Connectivity: NO_PASS_EVIDENCE.**

## 10. 波上宮 Source Inventory

| Source key | source_type | URL | verification_status / confidence | Text availability |
|---|---|---|---|---|
| `batch17-naminouegu-official` | shrine_official | naminouegu.jp/yuisyo.html | source_confirmed / high | Full text preserved |

6 `deity` entries (伊弉冉尊・速玉男尊・事解男尊・火神・産土神・少彦名神) — **INELIGIBLE as standalone evidence**, same rule as Sections 6/8. Not entered below.

6 `shrine_history` entries:

| Item | Content | Evidence classification |
|---|---|---|
| H1 (founding, source_confirmed) | "古くから人々が海の彼方のニライカナイの神々に**豊漁・豊穣と平穏**を祈り、波の上の崖端を聖地・拝所として祈りを捧げた" | **ELIGIBLE_EXPLICIT (content)** — explicit statement of what was prayed for |
| H2 (tradition, source_confirmed) | "南風原の崎山の里主が海浜で霊石を得て祈ったところ**豊漁**となり…" | **ELIGIBLE_EXPLICIT (content)** — explicit prayer→outcome statement |
| H3 (regional_context, source_confirmed) | "那覇港を往来する船が**航海の平安**を祈り、琉球王府も深く信仰し…" | **ELIGIBLE_EXPLICIT (content)** — explicit statement of what ships' crews prayed for |
| H4 (historical_event, source_confirmed) | "明治23年に官幣小社へ列格した" | INELIGIBLE-content — administrative status record |
| H5 (historical_event, source_confirmed) | "先の大戦で被災した" | INELIGIBLE-content — historical record |
| H6 (historical_event, source_confirmed) | "昭和28年に本殿と社務所…平成5年には…社殿が竣工した" | INELIGIBLE-content — reconstruction record |

**Important, per task instruction**: maritime historical context alone does not equal `航海安全`. H1/H2's "豊漁・豊穣" (bountiful catch / abundant harvest) is a **different, distinct benefit category** from voyage safety — it was evaluated on its own merits below, not folded into the 航海安全 finding. Only H3's explicit "航海の平安を祈り" (prayed for the peace/safety of the voyage) was evaluated against `航海安全`.

## 11. 波上宮 Review

| Shrine | Source | Source Evidence | Proposed canonical Goriyaku | Existing Tag | Decision | Reason |
|---|---|---|---|---|---|---|
| 波上宮 | `batch17-naminouegu-official` | H1: "豊漁・豊穣と平穏を祈り" | *(candidate, unresolved)* | *(no canonical tag for fishing-catch abundance; id5 五穀豊穣 is grain-harvest-specific, a different domain from 豊漁/漁業)* | **HOLD** | Explicit benefit language exists, but no existing `GoriyakuTag` cleanly represents "bountiful catch" (漁) as opposed to "abundant grain harvest" (穀物) — id5's domain (穀物) does not match the Source's domain (漁業). Per Contract §6, when Source states a benefit but no current label represents that specific category, the correct decision is HOLD, not a nearby-but-wrong label |
| 波上宮 | `batch17-naminouegu-official` | H2: "祈ったところ豊漁となり" | *(same as H1)* | *(same as H1)* | **HOLD** | Same reasoning as H1 — explicit prayer→outcome statement, but no clean canonical match for the fishing-catch domain |
| 波上宮 | `batch17-naminouegu-official` | H3: "航海の平安を祈り" | 航海安全 | **id 13 (航海安全)** | **PASS** | Source explicitly names the prayer object as the voyage's peace/safety ("航海の平安"), a narrow, single-candidate normalization of the existing canonical label 航海安全 (shared root term 航海). This is an exact-domain, word-level match, not a cross-domain analogy |
| 波上宮 | `batch17-naminouegu-official` | H4: 官幣小社列格 | — | — | **NO_EVIDENCE** | Administrative record only |
| 波上宮 | `batch17-naminouegu-official` | H5: 戦災 | — | — | **NO_EVIDENCE** | Historical record only |
| 波上宮 | `batch17-naminouegu-official` | H6: 再建・竣工 | — | — | **NO_EVIDENCE** | Reconstruction record only |

PASS=1, HOLD=2, NO_EVIDENCE=3, REVISE=0.

**Final Evidence Status: PARTIALLY_READY** (Gate A only — see Section 13 for why this is explicitly not upgraded to RECOMMENDATION_EVIDENCE_READY). At least one PASS exists; two items remain HOLD pending either an expanded canonical vocabulary (out of scope, would require a Mother Ship taxonomy decision) or further Source research.

**Purpose Connectivity: CANONICAL_BUT_UNMAPPED** (Section 12) — this is a Gate B finding and, per this task's explicit instruction, does **not** downgrade the Gate A PARTIALLY_READY status above.

## 12. Recommendation Connectivity

| Shrine | Canonical Tag | Tag ID | Evidence Decision | Purpose Connectivity | Connected Purpose(s) |
|---|---|---:|---|---|---|
| 北海道神宮 | — | — | (no PASS) | NO_PASS_EVIDENCE | — |
| 建部大社 | — | — | (no PASS) | NO_PASS_EVIDENCE | — |
| 波上宮 | 航海安全 | 13 | PASS | **CANONICAL_BUT_UNMAPPED** | none — id 13 is not referenced by any `NEED_TO_GORIYAKU_IDS` entry (Section 4) |

Trace for the one PASS item: Reviewed Recommendation Evidence ("航海の平安を祈り") → canonical tag 航海安全 (id 13) → **`NEED_TO_GORIYAKU_IDS` lookup: no Purpose key contains 13** → connectivity dead-ends here. This is a real, reproduced Mapping-layer gap (Section 4/16), not a Review-layer defect — the Review correctly identified valid, Source-backed, canonically-resolvable evidence; the engine's Purpose Mapping simply does not yet route that canonical tag anywhere.

## 13. Evidence vs Purpose Separation

**Gate A — Recommendation Evidence** (is the Source-backed semantic evidence safe and reviewed?): 波上宮's H3 item = **YES**, safely reviewed, PASS.

**Gate B — Purpose Connectivity** (does existing engine mapping connect that tag to a current Purpose?): 波上宮's 航海安全 = **NO**, not connected to any Purpose today.

波上宮 is therefore formally in the state **`EVIDENCE_READY_BUT_PURPOSE_UNMAPPED`** for this one item — a valid, expected state per the Contract's own design (Section 8's worked example anticipated exactly this outcome for 航海安全/id 13). The shrine's Evidence-layer status (PARTIALLY_READY, Section 11) was **not** downgraded on account of this Gate B finding, per this task's explicit instruction ("Do NOT downgrade valid Recommendation Evidence solely because Purpose Mapping is missing").

## 14. Batch 17 Final Matrix

| Shrine | PASS | HOLD | NO_EVIDENCE | REVISE | Evidence Status | Purpose Connectivity |
|---|---:|---:|---:|---:|---|---|
| 北海道神宮 | 0 | 0 | 3 | 0 | NO_RECOMMENDATION_EVIDENCE | NO_PASS_EVIDENCE |
| 建部大社 | 0 | 1 | 3 | 0 | HOLD | NO_PASS_EVIDENCE |
| 波上宮 | 1 | 2 | 3 | 0 | PARTIALLY_READY | CANONICAL_BUT_UNMAPPED |
| **Total** | **1** | **3** | **9** | **0** | — | — |

No shrine reached RECOMMENDATION_EVIDENCE_READY (would require a PASS item that is *also* Purpose-wired — none exists in this batch). This is not a Pilot failure: **pilot success means the Contract produced reproducible, non-speculative decisions for all 13 reviewed history items across 3 shrines, not that every shrine PASS.**

## 15. Contract Operability

1. Can reviewers decide without model knowledge? **Yes** — every decision above cites exact Source text; the one PASS was a direct word-level match (航海→航海安全), not cultural/model inference.
2. Is explicit Source evidence sufficient? **Yes** — the ELIGIBLE_EXPLICIT rule combined with the exact-match/narrow-normalization rule was enough to reach one real PASS and to correctly withhold two evidence-adjacent-but-unmatched items (豊漁/豊穣).
3. Can ambiguous evidence safely HOLD? **Yes** — demonstrated for 建部大社's Yoritomo anecdote (no explicit benefit word) and 波上宮's H1/H2 (explicit benefit, but no matching label).
4. Can NO_EVIDENCE be recorded without forcing a semantic label? **Yes** — 9 of 13 items resolved NO_EVIDENCE with zero forced labels, including all 3 of 北海道神宮's items.
5. Can canonical mapping be performed without inventing new tags? **Yes** — the one PASS resolved to an existing tag (id 13); no new tag was proposed anywhere, even where an explicit benefit existed with no clean match (H1/H2 correctly HOLD rather than inventing a "豊漁" tag).
6. Is provenance preserved? **Yes** — every table row cites shrine, Source key, exact/paraphrased Source phrase, and reasoning (Sections 7/9/11).
7. Is Evidence Review clearly separate from Knowledge Fact review? **Yes** — no `history_type`, `verification_status`, or deity `role` decision already finalized in `shrine-expansion-batch1-human-review.md` was altered or reinterpreted; H4's `source_confirmed` Fact-confidence was explicitly not reused as Recommendation-eligibility confidence (Section 9).

**Result: `CONTRACT_OPERATIONAL_WITH_GAPS`.** All 7 operability checks pass cleanly on the Review-layer itself; the "gaps" are exclusively Mapping-layer (Section 16), not Contract-layer — the Contract correctly surfaced them rather than papering over them.

## 16. Mapping Gap Findings

**Finding A** (航海安全 id=13 exists but has no Purpose mapping): **CONFIRMED** — re-verified by fresh grep of `NEED_TO_GORIYAKU_IDS` this session (Section 4), and now additionally reproduced operationally: this pilot's one PASS item hits this exact gap in practice, not just in the abstract.

**Finding B** (`NEED_TO_GORIYAKU_IDS` references ids 42–45 absent from the canonical master): **CONFIRMED** — re-verified by fresh cross-reference of the full referenced-id set against the 39-row master this session. Not reproduced as a live blocker in this pilot (none of Batch 17's evidence touched these ids), but confirmed to exist independently of this pilot's specific findings.

Neither finding is fixed in this task, per constraint #21 and #8–#10.

## 17. Semantic Coverage Projection (read-only)

| PASS item | Purpose-connected? | Classification |
|---|---|---|
| 波上宮 / 航海安全 (id 13) | No | **SEMANTIC_EVIDENCE_GAIN_ONLY** |

Zero items in this pilot qualify as `POTENTIAL_PURPOSE_COVERAGE_GAIN`. No invented/simulated mapping was used to produce this result.

## 18. Compass / Concierge Shared Result

Both engines read the same `Shrine.goriyaku`/`goriyaku_tags` fields and the same `NEED_TO_GORIYAKU_IDS`/`NEED_TEXT_WEIGHTS` structures (re-confirmed unchanged, Section 2). If 波上宮's 航海安全 PASS item were hypothetically applied, both engines would consume it identically — but neither would produce a Purpose match from it today, since the gap is in the shared Mapping layer both engines read, not in either engine individually.

**Result: `SHARED_BUT_MAPPING_GAP`.**

## 19. Batch 18 Sequencing

Weighing: (a) Contract operability is confirmed clean (Section 15); (b) the two Mapping gaps found are narrow — Finding A affects only the 航海安全/海上安全 (id 13/14) domain and similar unmapped-but-canonical tags (id 17,19,31,35), not the Purposes most likely to matter for upcoming Batch 18 shrines' likely content (multiple Purposes — study, love, career, money, health, protection, courage, focus — all have fully HEALTHY, correctly-wired tag sets per Section 4); Finding B (ids 42-45) affects `family`/`mental`/`health`/`rest`/`relationship` partially but those Purposes retain other valid, existing ids in their sets too, so they are not entirely broken, only partially thinned. Neither gap blocks the review process itself or blocks discovery of PASS-and-connected evidence for most Purposes.

**Result: `START_BATCH_18_FACTS_AND_RUN_EVIDENCE_REVIEW_AFTERWARD`.** The Contract is ready to reuse; Batch 18 Fact Generation need not wait on a Mapping fix, since the fix (Option B below) is independent, narrowly scoped, and does not block Fact Generation or Knowledge Human Review for the 4 pending shrines.

## 20. Next PR Options

- **Option A (Batch 17 Recommendation Evidence Data Application)**: technically available — the one PASS (航海安全) could be safely written to `Shrine.goriyaku` without any fabrication — but would currently yield zero measurable Purpose-coverage gain (Section 17), since it dead-ends at Gate B. Low value right now.
- **Option B (Mapping Master Integrity Audit)**: motivated by two independently-reproduced findings (Section 16) that are broader than this single pilot — id 13/14/17/19/31/35 are all canonical-but-unmapped, and ids 42–45 are referenced-but-missing across 5 Purposes. An audit (not yet a fix) of the full Mapping/master relationship would clarify how many future PASS items are likely to hit the same dead-end, informing whether Batch 18's eventual Evidence Review pass is worth the reviewer effort for Purposes affected by Finding B.
- **Option C (Batch 18 Fact Generation)**: viable now per Section 19; independent of Option B.
- **Option D (Contract Revision)**: not warranted — Section 15 found zero Contract-layer defects.

**Recommended smallest safe next PR: Option B (Mapping Master Integrity Audit)** — docs/audit-only, directly motivated by two concrete, reproduced findings from this pilot, and unblocks confident interpretation of *future* Evidence Review pilots (not just this one). Option C (Batch 18 Fact Generation) may proceed independently/in parallel, since Section 19 found it non-blocked.

## 21. Mother Ship Decision Inputs

1. Should a Mapping Master Integrity Audit (Option B) be commissioned next, before or in parallel with Batch 18 Fact Generation?
2. Should the single 波上宮 PASS item (航海安全, Gate A success / Gate B gap) be held pending a Mapping fix, or is Gate-A-only documentation sufficient for now (no Production write either way, per this task's constraints)?
3. Should 建部大社's Yoritomo anecdote (HOLD) be pursued further — e.g. searching for a second Source that explicitly names the implied benefit — or left HOLD indefinitely as an accepted Contract outcome?
4. Should Batch 18 Fact Generation start now per Section 19's recommendation?

## 22. Limitations

- This pilot reviewed only the Source text already committed to `batch_17_seed.json`; it did not attempt new Source discovery (out of scope, and the environment's `EGRESS_BLOCKED` constraint documented in earlier sessions would prevent it regardless).
- The HOLD decisions for 波上宮 H1/H2 (豊漁・豊穣) reflect this audit's judgment that no existing `GoriyakuTag` cleanly represents "bountiful catch" as distinct from "abundant grain harvest" (id 5). This is itself a reviewer-level judgment call under the Contract, not a mechanically-derived fact — a future reviewer could reach the same or a different HOLD/PASS conclusion; this pilot does not treat its own HOLD calls as final Human Review sign-off, only as a demonstration of the Contract's decision process.
- 建部大社's H4 HOLD (Yoritomo anecdote) is presented as the single most contract-relevant test case in this pilot precisely because it is genuinely hard — this audit does not claim certainty that HOLD is the only defensible outcome, only that PASS was not defensible without an unsupported interpretive leap.
- GoriyakuTag vocabulary (39 rows) and `NEED_TO_GORIYAKU_IDS` were re-verified against the local scratch DB and `develop`'s tracked code this session, not against Production directly.

## 23. Out of Scope

UI, frontend, Mapping implementation/fixes, C1 changes, Recommendation Engine changes, Production Evidence writes, Batch 18 implementation, new canonical tags.
