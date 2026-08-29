# Shrine Evidence Integrity Full Audit (PR-C)

## 1. Audit metadata

| Field | Value |
|---|---|
| Task | First complete Shrine Evidence Integrity Audit across the canonical Production shrine set. Trace, per unique real shrine identity: approved Source → Knowledge Facts → `Shrine.goriyaku` / `GoriyakuTag` → Recommendation Evidence → current Purpose connectivity. Classify each chain link `MATCH` / `PARTIAL` / `UNSUPPORTED` / `MISSING` / `REVIEW_REQUIRED`. |
| Type | **Audit only.** No repair. No Production / DB / Spreadsheet / Recommendation-logic / `GoriyakuTag` / `Shrine.goriyaku` / Knowledge / Need-mapping / model / migration / fixture / seed / frontend / deployment change. Ends at audit documentation + PR. |
| Branch | `audit/shrine-evidence-integrity-full-audit` |
| Worktree | `~/Developer/jinja_app-shrine-evidence-integrity-full-audit` (isolated, from `origin/develop`; control repo untouched — never reset / cleaned / stashed) |
| Date | 2026-08-29 |
| Companion | [`shrine-evidence-integrity-full-audit-matrix.md`](shrine-evidence-integrity-full-audit-matrix.md) — one canonical row per shrine (103 rows) |
| PR-C predecessors | PR-A `shrine-evidence-audit-readiness.md` (#2610) · PR-B `shrine-evidence-integrity-pilot.md` (#2611) · `production-canonical-set-preflight.md` (#2612) · `tomioka-hachimangu-identity-resolution.md` (#2613) |

### Evidence labels

- **[prod]** — read this session directly from the Production database via the read-only credential bridge.
- **[src]** — official Source page fetched and compared this session (10 shrines).
- **[repo]** — read from tracked source at the base SHA.
- **[MS]** — fixed input supplied by the Mother Ship for PR-C (Section 18).
- **[prior]** — value from an earlier audit; historical snapshot only, superseded by current [prod]/[repo].

## 2. Base SHA

- **`origin/develop` @ `1ecceb0e691050e68fcc0baa90f32940041c6cce`** — `git fetch origin` this session; matches the task's stated prep SHA exactly; `origin/develop` had **not** advanced (HEAD = merge of PR #2613, `mergedAt 2026-08-29T06:47:46Z`). No `BASE_DRIFT`.
- Isolated worktree HEAD = same SHA; working tree clean at checkout and at commit time.
- **`BASE_DRIFT_REQUIRES_REVIEW`: not triggered.**

## 3. Scope / non-scope

### In scope

Canonical-set gate re-read from Production; 103-shrine inventory; existing-Production-evidence snapshot (deity / history / source / goriyaku / tags / verification_status / confidence); Fact-integrity review (sampled Source fetch + comparison); existing-goriyaku integrity review; missing-evidence root-cause classification; current-code Purpose connectivity (canonical + runtime); cross-layer per-shrine status; explicit-denominator aggregates; mechanical consistency checks; known tool/doc drift; remediation **decision packets** (not implementations).

### Non-scope (enforced)

Repairing any layer · deleting / merging Shrine rows · fixing id 105 `広島市` · fixing id 49 富岡八幡宮 coordinate · re-seeding the local dev DB · editing Production / Spreadsheet / Knowledge / `Shrine.goriyaku` / `GoriyakuTag` M2M / Need mappings / interpreter / scoring / C1 / Reason / Lead · adding `GoriyakuTag` labels · models / migrations / fixtures / seeds / frontend / deployment · starting any follow-up track · extrapolating this audit's rates as a forecast.

## 4. Authority hierarchy

Re-read at the base SHA. **Current code / tests / Production data are physical truth; where a historical audit doc disagrees, the drift is recorded and code/data win.**

| Concern | Authority |
|---|---|
| Real-vs-QA shrine set | `backend/temples/services/shrine_qa_fixture_exclusion.py` [repo] — `name_jp` convention only, no id hardcoding |
| Per-Fact usability (Evidence Gate) | `backend/temples/services/evidence_gate.py` `decide_fact_usability(*, verification_status, confidence, source_verification_statuses)` — `usable = fact_ready AND ≥1 fact-ready Source`; `FACT_READY_VERIFICATION_STATUSES = ("source_confirmed", "reviewed")`; `confidence` is metadata only |
| Fact selection (Recommendation) | `backend/temples/services/shrine_knowledge_selector.py` [repo] |
| Coverage aggregation | `backend/temples/services/knowledge_coverage_report.py` + its command [repo] — delegates QA exclusion / usability / selection to their owners; read-only |
| Need → GID mapping | `backend/temples/domain/need_to_goriyaku_tag_ids.py` `NEED_TO_GORIYAKU_IDS` [repo] |
| `goriyaku` text → tag M2M | `backend/temples/management/commands/backfill_goriyaku_tags.py` `parse_goriyaku()` — split `re.compile(r"[、,／/・\|\n\r\t]+")`, `GoriyakuTag.objects.get_or_create(name=…)` — **name-based, PK-agnostic** |
| Evidence eligibility / review states | `docs/knowledge/recommendation-evidence-review-contract.md` — ELIGIBLE_EXPLICIT / REVIEW_REQUIRED / INELIGIBLE / UNKNOWN; PASS / HOLD / NO_EVIDENCE / REVISE; LEGACY_EXISTING / REVIEWED_NEW |
| Knowledge Fact meaning / source / verification | `docs/knowledge/shrine-knowledge-contract.md` (Active) |
| Coverage taxonomy | `docs/core/recommendation-readiness.md` (Active) — Schema / Populated / Verified / Usable |
| Mixed confidence | `docs/audit/mixed-confidence-policy-decision.md` — `FULL_SUPPRESSION` (ACTIVE_DECISION_RECORD, not a contract) |
| Canonical `GoriyakuTag` master + denominator + PK-drift scope | `docs/audit/production-canonical-set-preflight.md` (#2612) + `tomioka-hachimangu-identity-resolution.md` (#2613) |

**Current `NEED_TO_GORIYAKU_IDS` [repo] (re-read at base SHA — full mapping):**

```text
love          {1, 20}            marriage      {1, 18}
relationship  {1}                communication set()          (EVIDENCE_LIMITED / DISABLE_GID_EVIDENCE)
career        {6, 21, 30, 12, 27}  money       {5, 36, 4, 28}
study         {9, 10}            focus         {9, 10}
health        {7, 8, 24, 33, 38}   mental      {11, 26, 28, 38}
protection    {11, 32, 2}        courage       {12, 15, 18, 20, 24, 30, 38}
rest          {7, 8}             family        {16, 35}
travel_safe   {3, 13, 14}
```

Union of mapped canonical ids = **29 of 39** wired.

### Critical semantic rule (applied throughout)

Recommendation Evidence is **never** inferred from shrine name, deity name, historical reputation, famous cultural association, founding story, anecdote, tourism copy, or model/background knowledge — only from an approved Source that **explicitly states** the blessing / prayer benefit. Knowledge-Fact correctness ≠ Recommendation eligibility. A Knowledge Fact or `goriyaku` label is `MATCH` / `PASS` only after its official Source was fetched and compared **this session**; `verification_status = source_confirmed` alone yields `REVIEW_REQUIRED` (pilot M8). `NO_EVIDENCE` requires a fully reviewed Source set with no explicit evidence (pilot M7).

## 5. Canonical 103-unit definition

| Term | Value | Basis |
|---|---|---|
| `RAW_PRODUCTION_SHRINE_ROWS` | **108** | [prod] — `MAX(id) = 108`, `COUNT(DISTINCT id) = 108`, ids 1–108 contiguous |
| `QA_FIXTURE_ROWS` | **1** — id 102 `テスト確認神社 20260611` | [prod] + `shrine_qa_fixture_exclusion` (`name_jp LIKE 'テスト%'`); address `東京テスト`, no coordinates |
| `NON_SHRINE_ARTIFACT_ROWS` | **1** — id 105 `広島市` | [prod] — a city; `place_ref` set; **not** removed by the QA name convention |
| `CONFIRMED_DUPLICATE_EXTRA_ROWS` | **3** — ids 101, 103, 104 | shadows of primaries 22, 21, 49; each `place_ref`-only, 0 deity / 0 history / 0 source, empty goriyaku (#2612 §10, #2613) |
| `AMBIGUOUS_DUPLICATE_EXTRA_ROWS` | **0** | 富岡八幡宮 {49,104} resolved SAME in #2613 |
| **`FULL_AUDIT_DENOMINATOR`** | **103** [MS] | 108 − 1 QA − 1 non-shrine − 3 duplicate shadows |
| `PR_C_CANONICAL_AUDIT_UNIT` | `UNIQUE_REAL_SHRINE_IDENTITY` [MS] | the data-bearing primary id; shadow ids kept only in the evidence table |

**Canonical audit unit ids (103):** 1–100, 106 (北海道神宮), 107 (建部大社), 108 (波上宮).

### Mandatory canonical-set gate — re-read this session [prod]

| Check | Expected | Observed | Result |
|---|---|---|---|
| `RAW_PRODUCTION_SHRINE_ROWS` | 108 | 108 | OK |
| id 102 present, QA-named | yes | `テスト確認神社 20260611` | OK |
| id 105 present, non-shrine | yes | `広島市` | OK |
| shadow rows 101 / 103 / 104 present | yes | `給田六所神社` / `長太稲荷神社` / `富岡八幡宮`, all `place_ref`-set, 0/0/0 | OK |
| primary rows 21 / 22 / 49 present | yes | `長太稲荷神社` / `給田六所神社` / `富岡八幡宮` | OK |
| unique real identity count | 103 | 108 − 1 − 1 − 3 = **103** | OK |
| `GoriyakuTag` | 39 rows, ids 1–39, canonical names | 39 / ids 1–39 / **names exact** | OK |

**`CANONICAL_SET_DRIFT = NOT DETECTED`.** No STOP condition. No silent recalculation.

## 6. Production preflight

Read-only via the sanctioned bridge (`readonly_query.sh` + repo-external `~/.config/kami-musubi/production-db.env`, mode 600). Every SQL file passed `guard.py check-readonly-sql` (SELECT/WITH only). No `UPDATE`/`INSERT`/`DELETE`/`TRUNCATE`/`ALTER`/`DROP`/`CREATE`/`MERGE`. Credential value never printed, logged, or placed in argv. Scratch SQL/JSON kept in an untracked temp dir, not committed.

| Metric | Value [prod] |
|---|---|
| `Shrine` rows | 108; ids 1–108 contiguous |
| rows with latitude AND longitude | 107 / 108 (missing: id 102, QA) |
| rows with `place_ref` set | 4 — ids {101, 103, 104, 105} (all excluded) |
| `GoriyakuTag` | 39 rows, ids 1–39, names exact to the canonical master → `ALIGNED` (independent re-confirmation of #2612 §7) |
| `goriyaku_tags` M2M links | 283, **every** link → a canonical id 1–39 (no non-canonical tag id anywhere) |
| `ShrineDeity` rows | 245 — all `verification_status = source_confirmed`; 240 `high` / 5 `medium`; **every** row has ≥1 Source |
| `ShrineHistory` rows | 195 — 193 `source_confirmed` + **2 `disputed`** (both on id 107 建部大社, `history_type = tradition`); every row has ≥1 Source |
| `ShrineKnowledgeSource` rows | 114 — **all `source_confirmed`**; 113 have a URL; types: `shrine_official` ×100, `cultural_property` ×4, `government` ×2, `secondary_editorial` ×5, `local_history` ×1, `tourism_official` ×1, `user_observation` ×1 |
| `DEV_DB_PK_DRIFT_SCOPE` | `LOCAL_DEV_ONLY_CONFIRMED` (#2612 §9) — Production is the clean 39-row master; not re-litigated |

**Evidence-Gate consequence [prod] + [repo]:** every Source is `source_confirmed`, so `decide_fact_usability` reduces to the Fact's own status. → **all 245 deity Facts are `usable`**; **193 of 195 history Facts are `usable`** (the 2 `disputed` on id 107 are `usable = False` for Recommendation, and render as `disputed` in Shrine Detail via `decide_detail_display_state`). Fact-ready ≈ populated for this set.

## 7. Existing tooling limitations

**`KNOWLEDGE_COVERAGE_TOOL_DENOMINATOR_MISMATCH = TRUE`.** `knowledge_coverage_report` derives its audit target from `exclude_qa_fixture_shrines(Shrine.objects.all())`, which is a **name-convention** filter. Against current Production it removes only id 102 → **`audit_target_shrines = 107`**, still counting the non-shrine row 105 and the three duplicate shadows 101 / 103 / 104. This audit's canonical denominator is **103**. Every metric in Sections 8–14 states its denominator explicitly; a 107-based percentage from the existing report is labelled `TOOLING_DENOMINATOR_MISMATCH` and is **not** compared against a 103-based figure. `knowledge_coverage_report` was not modified; it remains valid for its own factual counts under its own denominator.

## 8. Source review method

- **Authority order:** shrine official site → official religious body / Jinja Honcho → government / municipal / cultural-property → existing approved historical/archival Source → other explicitly approved strong Source. Google Places / PlaceRef = identity/location only. Wikipedia / encyclopedia / blog / social = supplementary context only, never primary Recommendation Evidence.
- **Sampled Source fetch [src] — 10 shrines this session**, chosen to span prefectures, Source types, benefit types, and known edge cases: id 1 明治神宮, id 6 太宰府天満宮, id 10 鶴岡八幡宮 (no official Source — tourism + Wikipedia), id 26 寒川神社 (八方除), id 44 東京大神宮 (縁結び), id 62 小網神社 (金運), id 64 湯島天満宮 (学問), id 99 護王神社 (足腰健康), id 107 建部大社 (2 `disputed` histories), id 108 波上宮 (Batch 17, empty goriyaku).
- **Un-sampled shrines:** the recorded Source (URL on file, `source_confirmed`) was **not** re-fetched. Their Fact fidelity is `REVIEW_REQUIRED` (`SOURCE_AVAILABLE` where a URL exists), never silently upgraded to `MATCH`. A currently-unreachable URL is **not** grounds for `UNSUPPORTED`.
- **`SOURCE_ACCESS`:** all 10 sampled official pages reachable. No `SOURCE_ACCESS = UNAVAILABLE` this session (護王神社's benefit statement is on a sibling page `yuisho/goriyaku.html`, which was fetched).

## 9. Knowledge Fact Integrity results (Dimension A)

`MATCH` / `PARTIAL` / `UNSUPPORTED` / `MISSING` / `REVIEW_REQUIRED`, plus `SOURCE_AVAILABLE` / `SOURCE_UNAVAILABLE` / `SOURCE_NOT_REVIEWABLE`.

### 9.1 Sampled shrines — Fact fidelity confirmed [src]

| Shrine | Deity | History | Notes [src] |
|---|---|---|---|
| 1 明治神宮 | **MATCH** | **MATCH** | 明治天皇 + 昭憲皇太后 exact; 大正9年(1920) 創建 代々木 exact |
| 6 太宰府天満宮 | **MATCH** | **MATCH** | 菅原道真公; 901 左遷 / 903 逝去 / 919 社殿 / 1591 現本殿 |
| 10 鶴岡八幡宮 | **MATCH** | **PARTIAL** | 応神天皇・比売神・神功皇后 triad confirmed on the tourism page; of 5 histories only 由比若宮(1063) + 現在地遷座(1180) confirmed there — id 15/16/17 `REVIEW_REQUIRED`. `PROVENANCE_GAP` — no `shrine_official` Source. |
| 26 寒川神社 | **REVIEW_REQUIRED** | **PARTIAL** | deity names 寒川比古命/寒川比女命 are on the un-fetched `main-deities.html`; history 雄略天皇 + 神亀四年(727) confirmed, 承和十三年 神階 not on the fetched page |
| 44 東京大神宮 | **MATCH** | **MATCH** | 天照皇大神・豊受大神・造化の三神・倭比賣命 exact; 明治13年(1880) 創建 exact |
| 62 小網神社 | **MATCH** | **MATCH** | 倉稲魂神・市杵島比賣神 confirmed (Source also lists 福禄寿); 文正元年(1466) 創建伝承 confirmed |
| 64 湯島天満宮 | **MATCH** | **PARTIAL** | 天之手力雄命 + 菅原道真公 exact; 458 / 1355 道真勧請 confirmed, 2 later histories `REVIEW_REQUIRED` |
| 99 護王神社 | **MATCH** | **MATCH** | 和気清麻呂公命・和気広虫姫命 + 藤原百川公命・路豊永卿命 exact; 神護寺霊社 → 1851 rank → 1874 establishment → 1886 relocation |
| 107 建部大社 | **MATCH** | **MATCH** | 日本武尊 + 大己貴命 exact; 景行天皇46年 起源 + 源頼朝 祈願(平治物語) confirmed; the **2 `disputed` histories** (白鳳4年 675 / 天武天皇4年 676 relocation dates) faithfully mark the Source's own non-specific "天武天皇の時代" — the `disputed` status is a correct transcription of Source uncertainty |
| 108 波上宮 | **MATCH** | **MATCH** | 伊弉冉尊・速玉男尊・事解男尊 + 火神・産土神・少彦名神 exact; 「ものいう石」→ 熊野権現神託 legend + 明治23年(1890) 官幣小社 + 1953/1961/1993–94 rebuilds |

### 9.2 Un-sampled knowledge-bearing shrines (79)

**Fact integrity = `REVIEW_REQUIRED` (`SOURCE_AVAILABLE`).** Structural state is uniform and healthy [prod]: every deity/history Fact `source_confirmed` with ≥1 `source_confirmed` Source, so all are Evidence-Gate `usable`; 77 of 79 have a `shrine_official` Source. What is **not** done: fetching each Source and comparing wording. Per the critical semantic rule this is `REVIEW_REQUIRED`, not `MATCH`.

### 9.3 Zero-Knowledge shrines (14) — Fact dimension = `MISSING`

ids **21, 27, 42, 46, 58, 61, 63, 67, 72, 73, 78, 86, 87, 89** — 0 deity, 0 history, 0 Source. `SOURCE_UNAVAILABLE` (none recorded). These 14 nevertheless carry `goriyaku` + `goriyaku_tags` (Section 11).

### 9.4 Provenance quirks

- id 1 明治神宮 carries a stray `user_observation` Source `テスト神社 境内案内板` (no URL) alongside its real `shrine_official` Source — a leftover test artifact; does not affect fact-readiness. `PROVENANCE_GAP` (record-only).
- ids 10 (鶴岡八幡宮) and 22 (給田六所神社) have Knowledge but **no `shrine_official` / primary Source** — `secondary_editorial` (Wikipedia) + `tourism_official` / `local_history` only. `PROVENANCE_GAP` + `SOURCE_GAP`.

## 10. Recommendation Evidence results (Dimension B)

Per `recommendation-evidence-review-contract.md`: `ELIGIBLE_EXPLICIT` / `REVIEW_REQUIRED` / `INELIGIBLE` / `UNKNOWN`; PASS / HOLD / NO_EVIDENCE / REVISE / UNKNOWN. `UNKNOWN` is a valid PR-C outcome and is **not** converted to `NO_EVIDENCE`.

### 10.1 Sampled `goriyaku` labels reviewed against fetched Source [src]

| Shrine | Label | Source phrase [src] | Eligibility | Review state |
|---|---|---|---|---|
| 6 太宰府 | 学業成就 | 「学問…の神様」/「学業上達祈願」 | ELIGIBLE_EXPLICIT | **PASS** (学問→学業成就 narrow normalization) |
| 6 | 合格祈願 | 「受験合格祈願」 | ELIGIBLE_EXPLICIT | **PASS** |
| 6 | 厄除け | 「厄除けの神様」/「厄除祈願」 | ELIGIBLE_EXPLICIT | **PASS** |
| 1 明治神宮 | 厄除け | 「厄祓等の御祈願」 | ELIGIBLE_EXPLICIT | **PASS** (厄祓→厄除け) |
| 1 | 縁結び | not stated on `/about/` (結婚式 is a service) | REVIEW_REQUIRED | **HOLD** — `UNSUPPORTED` on the checked Source |
| 1 | 交通安全 | not stated on `/about/` | REVIEW_REQUIRED | **HOLD** — `UNSUPPORTED` on the checked Source |
| 44 東京大神宮 | 縁結び | 「縁結びに御利益のある神社としても知られ」 | ELIGIBLE_EXPLICIT | **PASS** |
| 44 | 恋愛成就 | phrase not used | REVIEW_REQUIRED | **HOLD** |
| 62 小網神社 | 強運厄除け | 「強運厄除」 | ELIGIBLE_EXPLICIT | **PASS** |
| 62 | 金運 | 「財運」(銭洗い井) | ELIGIBLE_EXPLICIT | **PASS** (財運→金運 narrow normalization; noted borderline) |
| 62 | 商売繁盛 | phrase not on the fetched page | REVIEW_REQUIRED | **HOLD** |
| 99 護王神社 | 足腰健康 | 「足腰の健康・安全」「足腰の守護神」(`yuisho/goriyaku.html`) | ELIGIBLE_EXPLICIT | **PASS** — DB Source records `yuisho/`; benefit is on the sibling page (same official site) |
| 99 | 厄除け | not stated on either page | REVIEW_REQUIRED | **HOLD** — `UNSUPPORTED` on the checked Source |
| 99 | 勝運 | 「スポーツ守護」「必勝祈願」(sports-bound) | REVIEW_REQUIRED | **HOLD** |
| 26 寒川神社 | 八方除 | 「全国唯一の八方除の守護神」 | ELIGIBLE_EXPLICIT | **PASS** — but tag id 17 八方除 is **UNWIRED** (Section 12); PASS does not route |
| 26 | 開運 | 「福徳開運を招き」 | ELIGIBLE_EXPLICIT | **PASS** |
| 26 | 厄除け | 「すべての悪事災難をとり除き」 | ELIGIBLE_EXPLICIT | **PASS** (explicit misfortune-removal) |
| 10 鶴岡八幡宮 | 勝運 / 仕事運 / 厄除け | tourism page states **no** ご利益 | INELIGIBLE (on this Source) | **HOLD** ×3 — reputation-based inference is not permitted |
| 64 湯島天満宮 | 学業成就 / 合格祈願 / 開運 | recorded `engi.htm` states **no** explicit benefit | UNKNOWN (this Source) | **HOLD** ×3 — needs a benefit-stating page; likely correct but unverified |

Reconciled sampled review-state counts: **PASS = 11 label-items** · **HOLD = 12 label-items** · NO_EVIDENCE = 0 · REVISE = 0.

### 10.2 `goriyaku`-bearing shrines with explicit Source benefit **not captured** (Batch 17)

- **108 波上宮** — Source states 「豊漁」「豊穣」「航路の平安」 (= 航海安全 / 海上安全, both wired to `travel_safe`). `goriyaku` is **empty**. `GORIYAKU_EVIDENCE_GAP` — the `MISSING_PIPELINE_BRIDGE` pattern (`recommendation-evidence-review-contract.md` Background).
- **107 建部大社** — Source states 「御神徳：開運・厄除・災難除・出世・必勝」 and 「縁結び・商売繁盛・家内安全・病気平癒・醸造」. `goriyaku` **empty**. Same gap.
- **106 北海道神宮** — Source not fetched this session; `goriyaku` empty; `[prior]` (`recommendation-evidence-followup-design.md` §6) reports no Source-backed benefit language → eligibility `UNKNOWN` pending a PR-C-style fetch (not `NO_EVIDENCE`).

### 10.3 Un-sampled `goriyaku`-bearing shrines (86)

All carry `LEGACY_EXISTING` `goriyaku` with **no** Recommendation-Evidence-Review provenance record. Eligibility = **`UNKNOWN`** (Source not fetched this session). Not grandfathered — flagged as `PROVENANCE_GAP`. This is the dominant systemic finding (Section 13).

## 11. Goriyaku / GoriyakuTag integrity (Dimension C)

`CANONICAL_MATCH` / `CANONICAL_BUT_UNSUPPORTED` / `TEXT_TAG_MISMATCH` / `NONCANONICAL_LABEL` / `NO_TAG` / `REVIEW_REQUIRED`.

| Observation | Count / ids [prod] |
|---|---|
| `goriyaku` text shape | **98 DELIMITED** (canonical labels, `・`-separated) · **2 PROSE** (ids 21, 22) · **3 EMPTY** (ids 106, 107, 108) |
| delimited shrines whose `parse_goriyaku(goriyaku)` label set **==** `goriyaku_tags` name set | **98 / 98** — exact agreement; no `TEXT_TAG_MISMATCH` among delimited shrines |
| distinct `GoriyakuTag` ids attached across the 103 | **39 / 39** — every canonical tag is used by ≥1 shrine |
| every attached tag id is canonical (1–39) | **yes** — no `NONCANONICAL_LABEL` anywhere |
| `NO_TAG` | ids 106, 107, 108 (Batch 17, empty goriyaku) |
| `TEXT_TAG_MISMATCH` (prose; tags not `parse_goriyaku`-derivable) | ids **21** (`商売繁盛`/`五穀豊穣` hand-set from prose `…商売繁盛や五穀豊穣…`) and **22** (`家内安全` hand-set from prose `…暮らしや家内安全…`) — `TAG_INTEGRITY_GAP` |
| `CANONICAL_MATCH` but Source-support **not** established this session | 96 goriyaku-bearing shrines minus the sampled PASS items — the tag string is mechanically valid, **not** proven Source-backed (`recommendation-evidence-review-contract.md` §5: mechanical validity ≠ Source-backing) |
| `CANONICAL_BUT_UNSUPPORTED` (label PASS-eligible but on an **unwired** tag) | id 26 寒川神社 `八方除` (tag 17); at concept level also ids 34/56 `美容`(22), 52/61/76 `芸能運`(29), 38 `芸能`(25), 77 `技芸上達`(31), 86/97 `火防`(34), 96 `延命長寿`(37), 100 `農業守護`(39), 29 `八難除`(19), 35 `方除け`(23) — all 14 also carry ≥1 wired tag |

**Dimension C headline:** the `goriyaku` / `goriyaku_tags` layer is *mechanically* clean (100% canonical, 100% text↔tag agreement for delimited shrines, all 39 tags exercised) but *evidentially* unbacked at scale — 86 shrines' labels have no reviewed Source, and 3 Batch-17 shrines have Source-explicit benefits with no label.

## 12. Purpose connectivity (Dimension D)

Computed from **current** `NEED_TO_GORIYAKU_IDS` [repo] against the **`ALIGNED`** Production `GoriyakuTag` master (so canonical id == tag PK — the pilot's `PK_DRIFT` blocker does **not** apply to Production).

### 12.1 Canonical name-level connectivity

**29 of 39** canonical concepts are consumed by ≥1 Need:
`{1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,20,21,24,26,27,28,30,32,33,35,36,38}`.

**`UNWIRED_CANONICAL` — 10 of 39:** `八方除`(17), `八難除`(19), `美容`(22), `方除け`(23), `芸能`(25), `芸能運`(29), `技芸上達`(31), `火防`(34), `延命長寿`(37), `農業守護`(39). All ten are niche / non-consultation concepts; none is a Compass/Concierge Purpose axis. `communication = set()` is **`INTENTIONALLY_DISABLED`** (EVIDENCE_LIMITED / DISABLE_GID_EVIDENCE, Mother Ship 2026-08-29) — not accidental data loss; no substitute tag invented.

`安産`(16), `子宝`(35), `航海安全`(13), `海上安全`(14), `足腰健康`(38) are all **WIRED** at the canonical level — see `DOC_DRIFT_CURRENT_MAPPING` (Section 15).

### 12.2 Runtime connectivity (per shrine, `goriyaku_tags` → Need)

| Class | Count (of 103) | ids |
|---|---|---|
| `WIRED` (≥1 tag id ∈ a Need's set) | **100** | every `goriyaku`-bearing shrine |
| `UNWIRED_CANONICAL` (tags present, none consumed) | **0** | — |
| `NOT_APPLICABLE` (zero `goriyaku_tags`) | **3** | 106, 107, 108 |

Every goriyaku-bearing shrine — including all 14 that carry an unwired niche tag — reaches ≥1 Need through a co-attached wired tag (typically `厄除け`/`開運`/`家内安全`/`縁結び`). No shrine is Purpose-orphaned by the mapping.

### 12.3 Per-Need coverage (denominator = 103)

`runtime-backed` = shrines with ≥1 tag id in that Need's set (tag present; **not** Source-verified). `PASS-backed` = shrines with a tag that is also a **confirmed PASS this session** (Section 10.1).

| Need | mapped GIDs | runtime-backed shrines | PASS-backed (this session) | notes |
|---|---|---|---|---|
| love | {1, 20} | 32 | 1 (44) | `縁結び` dominant |
| relationship | {1} | 32 | 1 (44) | |
| marriage | {1, 18} | 32 | 1 (44) | |
| communication | {} | **0** | 0 | `INTENTIONALLY_DISABLED` — expected, not a gap |
| career | {6,21,30,12,27} | 67 | 2 (26, 62) | `開運` very common → broad, weak-signal |
| money | {5,36,4,28} | 20 | 1 (62) | |
| study | {9, 10} | 8 | 1 (6) | `学業成就`/`合格祈願` — 8 shrines |
| focus | {9, 10} | 8 | 1 (6) | identical set to study |
| health | {7,8,24,33,38} | 31 | 1 (99) | |
| mental | {11,26,28,38} | 22 | 2 (62, 99) | |
| protection | {11,32,2} | 55 | 3 (1, 6, 26) | `厄除け` dominant |
| courage | {12,15,18,20,24,30,38} | 19 | 2 (62, 99) | |
| rest | {7, 8} | 28 | 0 | `家内安全`/`福徳` |
| family | {16, 35} | **5** | 0 | `安産`(19,51,72,79,87) + `子宝`(87) — narrowest Purpose |
| travel_safe | {3, 13, 14} | 10 | 0 | `交通安全`/`航海安全`/`海上安全`; 波上宮(108) evidence exists but uncaptured (Section 10.2) |

`PASS-backed` counts are tiny **by construction** — only 10 shrines were Source-reviewed this session and 86 goriyaku-bearing shrines carry unverified `LEGACY_EXISTING` labels.

## 13. Root-cause breakdown (Phase 5)

Audit-only labels; multiple may apply per shrine. Counts over the 103.

| Root cause | Shrines | What it means |
|---|---|---|
| `PROVENANCE_GAP` | **83** | `LEGACY_EXISTING` `goriyaku` with no Recommendation-Evidence-Review provenance record (+ stray/weak Source on 1, 10, 22) |
| `GORIYAKU_EVIDENCE_GAP` | **23** | label unsupported on a fetched Source (1, 10, 64, 99), or Source-explicit benefit not captured as a label (107, 108, + the 14 zero-knowledge shrines whose labels are wholly unbacked, + 44, 62) |
| `SOURCE_GAP` | **16** | 14 zero-Source shrines + 2 with no official/primary Source (10, 22) |
| `KNOWLEDGE_GAP` | **14** | zero deity + zero history (21, 27, 42, 46, 58, 61, 63, 67, 72, 73, 78, 86, 87, 89) |
| `PURPOSE_MAPPING_GAP` | **14** (concept-level; 10 concepts) | a stored tag maps to an `UNWIRED_CANONICAL` concept (id 26 is the only case where the shrine's *defining* benefit is the unwired one) |
| `TAG_INTEGRITY_GAP` | **2** | `goriyaku` stored as prose; tags not `parse_goriyaku`-derivable (21, 22) |
| `IDENTITY_DATA_GAP` | **2** | duplicate-primary shrines carrying a resolved shadow (21↔103, 22↔101; 49↔104 also, matrix-tracked) |
| `TOOLING_GAP` | 1 finding | `KNOWLEDGE_COVERAGE_TOOL_DENOMINATOR_MISMATCH` (Section 7) |
| `DOC_DRIFT` | 1 finding | `recommendation-evidence-review-contract.md` §8/§19 stale re `travel_safe` 13/14 + stale ids 42–45 reference (Section 15) |
| `REVIEW_REQUIRED` | 82 (Dimension A) | Fact fidelity not re-verified this session for 79 un-sampled + 3 sampled-partial |

No generic `DATA_GAP` bucket is used — each shrine's missing layer is named.

## 14. Aggregate 103-shrine results (Phase 8)

### 14.1 Cross-layer status (denominator = 103, mutually exclusive)

| Status | Count | Definition applied |
|---|---|---|
| `MATCH` | **1** | id 6 太宰府天満宮 — Source fetched; deity + history + all 3 `goriyaku` labels confirmed; all wired |
| `PARTIAL` | **84** | Evidence-Gate-usable Knowledge present and Source-linked, but `goriyaku` is `LEGACY_EXISTING` without review provenance and/or Source not re-fetched; includes 8 sampled shrines with mixed confirmation |
| `UNSUPPORTED` | **0** | no whole-shrine case; label-level unsupported-on-source exists for ids 1/10/64/99 |
| `MISSING` | **14** | zero Knowledge + zero Source (the 14 zero-knowledge ids) |
| `REVIEW_REQUIRED` | **4** | ids 10, 22 (no official Source), 26 (deity unconfirmed on fetched page), 106 (empty goriyaku, eligibility UNKNOWN) |
| **Total** | **103** | `1 + 84 + 0 + 14 + 4` |

`AUDITED_UNITS = 103` · `UNAUDITED_UNITS = 0` (every canonical identity classified).

### 14.2 Layer coverage (denominator = 103 canonical)

| Metric | Count | % of 103 |
|---|---|---|
| shrines with any Knowledge (deity or history) | 89 | 86.4% |
| shrines with zero Knowledge | 14 | 13.6% |
| shrines with any deity Fact | 89 | 86.4% |
| shrines with any history Fact | 87 | 84.5% |
| shrines with both deity and history | 87 | 84.5% |
| shrines with any Source | 89 | 86.4% |
| shrines with zero Source | 14 | 13.6% |
| shrines with a `shrine_official` Source | 87 | 84.5% |
| shrines with any `goriyaku` text | 100 | 97.1% |
| shrines with zero `goriyaku` | 3 | 2.9% |
| shrines with any `goriyaku_tags` | 100 | 97.1% |
| shrines with zero `goriyaku_tags` | 3 | 2.9% |
| shrines with ≥1 fact-ready deity Fact | 89 | 86.4% |
| shrines with ≥1 fact-ready history Fact | 87 | 84.5% |
| shrines Purpose-`WIRED` at runtime | 100 | 97.1% |
| shrines with ≥1 **PASS** `goriyaku` label (this session) | 5 | 4.9% |
| shrines with a **HOLD** label (this session) | 5 | 4.9% |
| shrines with **NO_EVIDENCE** (reviewed Source set, none found) | 0 | 0% |
| shrines with eligibility **UNKNOWN** | 98 | 95.1% |

### 14.3 Evidence-item counts (reported separately from shrine counts)

| Item | Count |
|---|---|
| `ShrineDeity` rows | 245 (all usable) |
| `ShrineHistory` rows | 195 (193 usable + 2 `disputed`) |
| `ShrineKnowledgeSource` rows | 114 (all `source_confirmed`; 113 with URL) |
| deity→Source links | 260 |
| history→Source links | 200 |
| `goriyaku` canonical label-items (parsed) | 280 |
| `goriyaku_tags` M2M links | 283 (280 parse-derived + 3 hand-set on ids 21/22) |
| `goriyaku` label PASS-items (this session) | 11 |
| `goriyaku` label HOLD-items (this session) | 12 |

### 14.4 Geographic

30 prefectures / regions represented (Tokyo dominant at 30 of 103; 17 prefectures hold exactly one canonical shrine). Batch 17 adds 北海道 / 滋賀県 / 沖縄県.

## 15. Known documentation / tool drift

| # | Finding | State | Recommendation (record-only) |
|---|---|---|---|
| 1 | `KNOWLEDGE_COVERAGE_TOOL_DENOMINATOR_MISMATCH` | **TRUE** — `knowledge_coverage_report` → `audit_target_shrines = 107` (removes only id 102), still counts id 105 + shadows 101/103/104; canonical audit denominator is 103. | `TOOLING_FIX`: teach `exclude_qa_fixture_shrines` (or a new canonical-set helper) to also drop the `NON_SHRINE_ARTIFACT` row and confirmed duplicate shadows, or add a `canonical_identity` filter. Not changed in PR-C. |
| 2 | `DOC_DRIFT_CURRENT_MAPPING` | **TRUE** — `recommendation-evidence-review-contract.md` §8 and §19 still say `航海安全`/`海上安全` (ids 13/14) are "not wired to a current Need" and reference stale ids 42–45. Current code [repo] has `travel_safe = {3, 13, 14}` and no id > 39 anywhere. | `DOC_RECONCILIATION`: a separate docs-only PR updates §8/§19 to the current mapping. **Not touched in PR-C.** Purpose connectivity here is computed from **current code**, which is physical truth — ids 13/14 are `WIRED`. |

Neither is fixed in PR-C.

## 16. Remediation decision packets (Phase 5 / Remediation Output)

PR-C repairs nothing. Prioritisation is returned to the Mother Ship. Follow-up types: `DATA_REVIEW` / `KNOWLEDGE_BACKFILL` / `SOURCE_BACKFILL` / `GORIYAKU_REVIEW` / `TAG_RECONCILIATION` / `PURPOSE_MAPPING_REVIEW` / `IDENTITY_REMEDIATION` / `COORDINATE_REMEDIATION` / `TOOLING_FIX` / `DOC_RECONCILIATION`.

| # | Affected ids / names | Layer | Current stored state | Source-backed expected state | Risk | Recommended follow-up |
|---|---|---|---|---|---|---|
| P1 | 21 長太稲荷神社, 27 榛名神社, 42 高千穂神社, 46 愛宕神社, 58 靖國神社, 61 花園神社, 63 鳥越神社, 67 千住神社, 72 氷川女體神社, 73 調神社, 78 千葉神社, 86 古峯神社, 87 冠稲荷神社, 89 赤城神社 | Knowledge + Source | 0 deity / 0 history / 0 Source; `goriyaku` labels present but wholly unbacked | at least deity + founding history from an official Source, per `shrine-knowledge-contract.md` | medium — these shrines rank on `goriyaku` with no evidence chain at all | `KNOWLEDGE_BACKFILL` + `SOURCE_BACKFILL` (14 shrines) |
| P2 | all 86 `goriyaku`-bearing shrines with `LEGACY_EXISTING` labels and no review record | Recommendation Evidence provenance | canonical tags attached; no `recommendation-evidence-review-contract.md` provenance | each label PASS/HOLD/NO_EVIDENCE against an explicit official-Source statement | medium — labels drive Compass + Concierge ranking with unverified evidence | `GORIYAKU_REVIEW` — batch by prefecture, per §6 of the Evidence Review Contract; Mother Ship decides retro-review vs record-and-accept per §12 |
| P3 | 108 波上宮, 107 建部大社 (and 106 北海道神宮 pending fetch) | `goriyaku` ← Knowledge bridge | `goriyaku` empty though the Source states explicit 御神徳 (波上宮: 豊漁/豊穣/航路の平安 → 航海安全/海上安全; 建部: 開運/厄除/出世/縁結び/商売繁盛…) | reviewed labels written into `Shrine.goriyaku`, then `backfill_goriyaku_tags` | low — under-recall, not wrong data | `GORIYAKU_REVIEW` (Batch 17 Recommendation Evidence Review) |
| P4 | 10 鶴岡八幡宮, 22 給田六所神社 | Source provenance | Knowledge backed only by `tourism_official` + `secondary_editorial` (10) / `local_history` + `secondary_editorial` (22) — no primary | ≥1 `shrine_official` or cultural-property Source per Fact | medium — Fact fidelity cannot be confirmed to contract standard | `SOURCE_BACKFILL` + `DATA_REVIEW` |
| P5 | 21 長太稲荷神社, 22 給田六所神社 | `goriyaku` text shape | free-sentence prose; `goriyaku_tags` hand-set, not `parse_goriyaku`-derivable | delimiter-separated canonical labels **or** cleared to none, with review provenance | low — tags happen to be reasonable but bypass the pipeline | `TAG_RECONCILIATION` + `GORIYAKU_REVIEW` |
| P6 | 1 明治神宮 | Source | stray `user_observation` "テスト神社 境内案内板" (no URL) alongside the real official Source | remove the test artifact | low | `DATA_REVIEW` |
| P7 | concept-level: `八方除`(17), `八難除`(19), `美容`(22), `方除け`(23), `芸能`(25), `芸能運`(29), `技芸上達`(31), `火防`(34), `延命長寿`(37), `農業守護`(39); shrine 26 寒川神社 most affected (its defining `八方除` PASS does not route) | Purpose mapping | 10 canonical concepts consumed by no Need | Mother Ship decides per concept: wire into a Need, or accept as non-consultation | low–medium — niche; no shrine is Purpose-orphaned (all also carry a wired tag) | `PURPOSE_MAPPING_REVIEW` — Mother Ship only; `NEED_TO_GORIYAKU_IDS` is frozen for PR-C |
| P8 | duplicate shadows 101 (→22), 103 (→21), 104 (→49); non-shrine 105 `広島市`; id 49 coordinate ~306–312 m off (#2613 §12) | identity / coordinate | shadows retained; 105 retained; 49 coordinate imprecise | pre-audit cleanup or carry as `REVIEW_REQUIRED` rows attached to the primary | low (audit denominator already excludes them) | `IDENTITY_REMEDIATION` (101/103/104/105) + `COORDINATE_REMEDIATION` (49) — **not** in PR-C |
| P9 | `knowledge_coverage_report` denominator | tooling | audit target = 107 (name-convention only) | canonical-identity-aware denominator (103) | low — reporting only | `TOOLING_FIX` |
| P10 | `recommendation-evidence-review-contract.md` §8 / §19 | docs | stale "ids 13/14 unwired" + stale ids 42–45 | reconcile to current `NEED_TO_GORIYAKU_IDS` | low | `DOC_RECONCILIATION` |

## 17. Tests / verification

Run in the isolated worktree against `~/Developer/jinja_app/.venv` (Python 3.14, Django 5.2.16), `--reuse-db`.

| Suite | Result |
|---|---|
| `test_need_to_goriyaku_tag_ids.py` + `services/test_evidence_gate.py` + `services/test_evidence_gate_detail_display_state.py` + `services/test_evidence_gate_pilot_regression.py` + `services/test_shrine_knowledge_selector.py` + `services/test_knowledge_coverage_report.py` + `test_knowledge_coverage_report_command.py` + `services/test_shrine_qa_fixture_exclusion.py` + `test_backfill_goriyaku_tags_command.py` + `services/test_shrine_submission_duplicate_candidates.py` + `services/test_concierge_chat_candidates_dedupe.py` + `api/test_concierge_chat_dedupe.py` (one invocation) | **103 passed, 0 failed** |
| `scripts/migration_safety/tests/test_guard.py` (credential bridge / read-only allow-list) | **47 passed, 0 failed** |
| **Total** | **150 passed, 0 failed** |

- **Production access:** every SQL file passed `guard.py check-readonly-sql`; SELECT/WITH only; credential value never printed / logged / in argv; scratch SQL kept in an untracked temp dir.
- **`git diff --check`:** **CLEAN** (staged and unstaged).
- **markdownlint** (repo `.markdownlint.json` rules — MD013 / MD033 / MD041 / MD024 / MD007): **0 issues**. The standalone tool additionally reports `MD060` (compact table-pipe spacing) on every `|---|---|` separator — the established repo-wide house style (every existing `docs/audit/*.md` uses it), not enforced by any CI job or pre-commit hook, matched here for consistency.
- Committed diff contains **only** these two audit documents — no production / config / fixture / seed / model / migration file touched.

## 18. Mother Ship decisions (fixed inputs used)

| Input | Value [MS] |
|---|---|
| `MOTHER_SHIP_PR_C_START` | APPROVED |
| `FULL_AUDIT_DENOMINATOR` | 103 |
| `PRODUCTION_GORIYAKU_MASTER` | ALIGNED |
| `PRODUCTION_GORIYAKU_ROW_COUNT` | 39 |
| `DEV_DB_PK_DRIFT_SCOPE` | LOCAL_DEV_ONLY_CONFIRMED |
| `PROJECT_SPREADSHEET_READ_PATH` | VERIFIED |
| `MOTHER_SHIP_AUTHENTICATED_SPREADSHEET_READ` | VERIFIED |
| `PR_C_CANONICAL_AUDIT_UNIT` | UNIQUE_REAL_SHRINE_IDENTITY |

**Spreadsheet role in PR-C:** identity / address / coordinate reference + audit ledger, **not** semantic truth. `CODEX_SESSION_SPREADSHEET_ACCESS = BLOCKED` (no authenticated snapshot supplied to this session); this is **not** a PR-C blocker because `MOTHER_SHIP_AUTHENTICATED_SPREADSHEET_READ = VERIFIED` and the canonical identity denominator is already fixed at 103. No individual shrine in this audit required Spreadsheet-specific identity confirmation Codex could not obtain — the identity set was fully resolved from Production [prod] + the merged preflight/identity audits (#2612, #2613). No `MOTHER_SHIP_SPREADSHEET_CHECK_REQUIRED` flag raised. No Spreadsheet cell content is used or invented anywhere in this document.

Open decisions returned to the Mother Ship: remediation-packet prioritisation (Section 16, P1–P10); Batch 17 Recommendation Evidence Review timing (P3); LEGACY_EXISTING retro-review vs record-and-accept (P2); the 10 unwired canonical concepts (P7); duplicate-shadow / non-shrine-row disposition (P8).

## 19. Final verdict

**`FULL_INTEGRITY_AUDIT_COMPLETE — EVIDENCE_CHAIN_PARTIAL`.**

All **103** canonical unique real shrine identities are inventoried and classified (`shrine-evidence-integrity-full-audit-matrix.md`, exactly 103 rows). The canonical-set gate, the `GoriyakuTag` `ALIGNED` check, the Need-mapping id resolution, and the mechanical consistency checks all **pass**; no STOP condition was hit.

Cross-layer status over 103: **`MATCH` 1 · `PARTIAL` 84 · `UNSUPPORTED` 0 · `MISSING` 14 · `REVIEW_REQUIRED` 4**.

The evidence chain is **structurally sound and mechanically clean** — Production `GoriyakuTag` is `ALIGNED` 39/39, every `goriyaku_tags` link is canonical, delimited `goriyaku` text and tags agree 98/98, every Knowledge Fact is Evidence-Gate `usable` (bar 2 correctly-`disputed` histories), and 100/103 shrines route to ≥1 Purpose — but **evidentially thin**: 86 goriyaku-bearing shrines carry `LEGACY_EXISTING` labels with no Recommendation-Evidence-Review provenance, 14 shrines have zero Knowledge and zero Source, 3 Batch-17 shrines have Source-explicit benefits not captured as labels, and only 10 official Sources were fetched and compared this session. The dominant systemic gap is **`PROVENANCE_GAP` (83 shrines)**: the Recommendation ranking layer runs on `goriyaku` labels whose Source-backing has never been reviewed to the current contract standard.

Two known drifts persist and are recorded, not fixed: `KNOWLEDGE_COVERAGE_TOOL_DENOMINATOR_MISMATCH` (tool → 107, canonical → 103) and `DOC_DRIFT_CURRENT_MAPPING` (`recommendation-evidence-review-contract.md` §8/§19 stale on `travel_safe` 13/14). Production `GoriyakuTag` alignment is **confirmed `ALIGNED` 39/39** independently this session.

**Explicit no-write confirmation:** nothing was written to Production, the Google Spreadsheet, DB data, Recommendation configuration, Knowledge rows, `GoriyakuTag` rows, `Shrine` rows, `Shrine.goriyaku`, Need mappings, fixtures, seeds, models, migrations, frontend, or deployment configuration. All Production access was read-only through the sanctioned credential bridge (credential value never seen). No `Shrine` row was deleted or merged. This branch adds exactly two files: `docs/audit/shrine-evidence-integrity-full-audit.md` and `docs/audit/shrine-evidence-integrity-full-audit-matrix.md`.

## STOP

PR created. No merge. No repair. No follow-up track started. id 105 `広島市` not fixed. id 49 富岡八幡宮 coordinate not fixed. Duplicate rows not deleted or merged. Local dev DB not re-seeded. `NEED_TO_GORIYAKU_IDS` / interpreter / scoring / C1 / Reason / Lead untouched. `recommendation-evidence-review-contract.md` not edited.
