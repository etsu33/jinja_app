# Batch 17 Recommendation Evidence — Review + Safe Activation (P3)

## Metadata

| Field | Value |
|---|---|
| Task | P3 — first contract-driven Recommendation Evidence **remediation** pilot: approved Source → Knowledge Facts → eligibility review → existing canonical `GoriyakuTag` normalization → PASS/HOLD/NO_EVIDENCE/REVISE/UNKNOWN → PASS-only `Shrine.goriyaku` + M2M activation → current Purpose-connectivity verification. Template for later P1/P2. |
| Scope | **Shrine ids 106 / 107 / 108 only.** Not broadened. |
| Relationship to the prior review | `docs/audit/batch17-recommendation-evidence-review.md` (PR #2575) was a **REVIEW-ONLY pilot** run against a local scratch DB / `batch_17_seed.json`, **before** the `travel_safe` mapping correction, with **no write**. P3 is the **activation** pass: fresh **Production** read, current (P10-corrected) mapping, and a committed scoped data migration. The prior doc is prior context only; its conclusions were re-derived here, not copied. (The task named this file `batch17-recommendation-evidence-review.md`, but that path is an already-merged doc — this activation record is kept at a distinct path to preserve that history.) |
| Branch | `fix/batch17-recommendation-evidence-review` |
| Base | `origin/develop` @ `a98e3c0a47121392643819662adda18151f95e5e` (merge of PR #2616). `git fetch origin` this session; `develop` had not advanced beyond the expected merge → `BASE_DRIFT_REQUIRES_REVIEW` not triggered. |
| Worktree | `~/Developer/jinja_app-p3` (isolated; control repo untouched). |
| Date | 2026-08-29 |
| Contract | `docs/knowledge/recommendation-evidence-review-contract.md` (incl. the P10 reconciliation merged in PR #2616). Review states used exactly: PASS / HOLD / NO_EVIDENCE / REVISE / UNKNOWN. Eligibility classes: ELIGIBLE_EXPLICIT / REVIEW_REQUIRED / INELIGIBLE / UNKNOWN. No new persisted DB state invented. |
| Production read | sanctioned read-only credential bridge (`scripts/migration_safety/readonly_query.sh` + repo-external `~/.config/kami-musubi/production-db.env`). Every query passed `guard.py check-readonly-sql`. Credential value never printed / logged / in argv. **No Production write path is available in this session.** |

### Current-state gate (fresh read [prod])

| id | name_jp | address | `goriyaku` | `goriyaku_tags` | `updated_at` |
|---|---|---|---|---|---|
| 106 | 北海道神宮 | 北海道札幌市中央区宮ヶ丘474 | *(empty)* | 0 | 2026-08-23 09:04:13 |
| 107 | 建部大社 | 滋賀県大津市神領1-16-1 | *(empty)* | 0 | 2026-08-23 09:04:13 |
| 108 | 波上宮 | 沖縄県那覇市若狭1-25-11 | *(empty)* | 0 | 2026-08-23 09:04:13 |

All three still have **empty `goriyaku` and zero `goriyaku_tags`** (unchanged since Batch 17 import). **`BATCH17_TARGET_STATE_DRIFT` = NOT DETECTED.** Re-verified immediately before finalizing the activation artifact — still no drift.

### Canonical `GoriyakuTag` master

Fresh read [prod]: **39 rows, ids 1–39, canonical names exact** (id 3 = 交通安全, id 13 = 航海安全, id 14 = 海上安全, …). Every PASS label below resolves by exact name to an existing row. **No new `GoriyakuTag` is created.**

### Current Purpose mapping

Fresh read `backend/temples/domain/need_to_goriyaku_tag_ids.py` [repo]: `travel_safe = {3, 13, 14}` (P10 truth confirmed). Purpose connectivity is checked **only after** the evidence review, and is never used to justify a PASS.

### Source access result

| Shrine | Recorded Source(s) [prod] | Re-fetched this session? | Result |
|---|---|---|---|
| 106 北海道神宮 | 110 `shrine_official` `由緒` `https://www.hokkaidojingu.or.jp/history.html` | **NO** | `hokkaidojingu.or.jp` returns an **expired TLS certificate**; the whole domain is unreachable via the fetch tool. No other Source is recorded for 106. → **SOURCE_ACCESS = UNAVAILABLE** for 106. |
| 107 建部大社 | 111 `shrine_official` `https://takebetaisha.jp/about/`; 112 `shrine_official` `https://takebetaisha.jp/features/`; 113 `government` `https://japan-heritage.bunka.go.jp/ja/culturalproperties/result/6883/` | **YES** (all 3) | All reachable and reviewed this session. |
| 108 波上宮 | 114 `shrine_official` `波上宮由緒` `https://naminouegu.jp/yuisyo.html` | **YES** + also fetched the official 御祈願 page `https://naminouegu.jp/kigan.html` (linked from the site menu "御祈願・挙式") | Both reachable and reviewed this session. |

## Per-shrine current state [prod]

### 106 北海道神宮

| Layer | Detail |
|---|---|
| Deity ×4 | 234 大国魂神, 235 大那牟遅神, 236 少彦名神, 237 明治天皇 — all `source_confirmed` / `high`, Source 110 |
| History ×3 | 183 `founding` 「明治2年の北海道鎮座神祭を創祀とする由緒」; 184 `historical_event` 「明治4年の札幌神社への社名決定と円山遷座」; 185 `historical_event` 「昭和39年の明治天皇増祀と北海道神宮への改称」 — all `source_confirmed` / `high`, Source 110 |
| Source ×1 | 110 `shrine_official` `source_confirmed` `high` (`由緒` page) |
| Disputed Facts | **0** |
| `goriyaku` / M2M | empty / none |

### 107 建部大社

| Layer | Detail |
|---|---|
| Deity ×2 | 238 日本武尊, 239 大己貴命 — `source_confirmed` / `high`, Sources 111 + 113 |
| History ×4 | 186 `tradition` 「景行天皇46年を起源とする創建由緒」 (`source_confirmed`); **187 `tradition` 「白鳳4年（675年）に瀬田へ遷し祀られたとする由緒」 (`disputed`)**; **188 `tradition` 「天武天皇4年（676年）に現在地へ移されたと伝わる由緒」 (`disputed`)**; 189 `tradition` 「源頼朝の祈願と源氏再興後の寄進伝承」 (`source_confirmed`) — all `high` |
| Source ×3 | 111 `shrine_official` (`建部大社について`); 112 `shrine_official` (`見どころ`); 113 `government` (bunka.go.jp cultural-property) — all `source_confirmed` / `high` |
| Disputed Facts | **2** — history 187, 188 (both `history_type = tradition`, `verification_status = disputed`, `confidence = high`). **Not touched, not promoted, not used as evidence, no benefit inferred from their narrative.** |
| `goriyaku` / M2M | empty / none |

### 108 波上宮

| Layer | Detail |
|---|---|
| Deity ×6 | 240 伊弉冉尊, 241 速玉男尊, 242 事解男尊 (`unknown` role); 243 火神, 244 産土神, 245 少彦名神 (`enshrined`) — all `source_confirmed` / `high`, Source 114 |
| History ×6 | 190 `founding`; 191 `tradition` (御鎮座伝説 — content contains 「霊石を得て祈ったところ豊漁となり」); 192 `regional_context` (琉球王府と海上交通); 193 `historical_event` (明治23年官幣小社); 194 `historical_event` (戦争被災); 195 `historical_event` (昭和28年以降 再建) — all `source_confirmed` / `high`, Source 114 |
| Source ×1 (recorded) | 114 `shrine_official` `source_confirmed` `high` (`波上宮由緒`). The official 御祈願 page fetched this session is the same domain, not a separately recorded Source row. |
| Disputed Facts | **0** |
| `goriyaku` / M2M | empty / none |

## Evidence item table

Review unit = **one Source-backed benefit candidate**. Eligibility + review state per candidate; a shrine may carry several.

| # | Shrine | Source | Source phrase (verbatim / close paraphrase) [src] | Eligibility | Proposed canonical label | Tag id | Purpose wiring (current code) | Review state | Reviewer rationale | Write |
|---|---|---|---|---|---|---|---|---|---|---|
| 106-1 | 北海道神宮 | 110 `由緒` | *(not re-fetched — expired TLS cert; page content not reviewable this session)* | **UNKNOWN** | — | — | — | **UNKNOWN** | Only recorded Source unreachable; no other approved Source. Contract: incomplete Source access ⇒ UNKNOWN, **not** NO_EVIDENCE / INELIGIBLE. Prior audits' "no benefit language" note is **not** copied as a conclusion. | no |
| 106-2 | 北海道神宮 | deity / founding history | 大国魂神・大那牟遅神・少彦名神・明治天皇; 明治2年創祀 → 明治4年札幌神社 → 昭和39年北海道神宮 | INELIGIBLE *(as evidence)* | — | — | — | *(not a candidate)* | Deity identity + institutional / founding chronology only. Critical inference prohibition: no benefit derivable from these. | no |
| 107-1 | 建部大社 | 111 `about/` | 御神徳（日本武尊）:「**開運**・厄除・災難除・出世・必勝」 | ELIGIBLE_EXPLICIT | 開運 | 6 | career | **PASS** | Exact-string 御神徳 stated by the shrine's own page for its main deity. Exact canonical match. | write |
| 107-2 | 建部大社 | 111 `about/` | 御神徳（日本武尊）:「開運・**厄除**・災難除・出世・必勝」 | ELIGIBLE_EXPLICIT | 厄除け | 2 | protection | **PASS** | 厄除ける → 厄除け: narrow surface-form of the same concept (trailing kana). | write |
| 107-3 | 建部大社 | 111 `about/`; 113 gov | 御神徳（日本武尊）:「…**出世**・必勝」;「除災・**出世**の神として信仰を集めている」 | ELIGIBLE_EXPLICIT | 出世運 | 27 | career | **PASS** | 出世 → 出世運: `-運` is the master's benefit-category suffix (cf. 仕事運/金運). Single clean target; corroborated by the government cultural-property page. | write |
| 107-4 | 建部大社 | 111 `about/` | 御神徳（日本武尊）:「…**必勝**」 | ELIGIBLE_EXPLICIT | 勝運 | 11 | mental / protection / courage | **PASS** | 必勝 → 勝運: same concept (winning), `-運` category form; 武運長久 (longevity) is a different concept, so a single clean target. Weaker (one Source, normalization) — noted. | write |
| 107-5 | 建部大社 | 111 `about/` | 御神徳（大己貴命）:「**縁結び**・商売繁盛・家内安全・病気平癒・醸造」 | ELIGIBLE_EXPLICIT | 縁結び | 1 | love / relationship / marriage | **PASS** | Exact-string 御神徳 for the 権殿 deity 大己貴命. Exact canonical match. | write |
| 107-6 | 建部大社 | 111 `about/` | 御神徳（大己貴命）:「縁結び・**商売繁盛**・家内安全・病気平癒・醸造」 | ELIGIBLE_EXPLICIT | 商売繁盛 | 4 | money | **PASS** | Exact canonical match. | write |
| 107-7 | 建部大社 | 111 `about/` | 御神徳（大己貴命）:「…**家内安全**・病気平癒・醸造」 | ELIGIBLE_EXPLICIT | 家内安全 | 7 | health / rest | **PASS** | Exact canonical match. | write |
| 107-8 | 建部大社 | 111 `about/` | 御神徳（大己貴命）:「…**病気平癒**・醸造」 | ELIGIBLE_EXPLICIT | 病気平癒 | 33 | health | **PASS** | Exact canonical match. | write |
| 107-9 | 建部大社 | 111 `about/` | 御神徳（日本武尊）:「…**災難除**…」 | ELIGIBLE_EXPLICIT *(concept)* | *(none)* | — | — | **HOLD** | No canonical label for 災難除 specifically; would be semantic expansion or a duplicate of 厄除け (already PASS via 107-2). HOLD, no new tag. | no |
| 107-10 | 建部大社 | 111 `about/` | 御神徳（大己貴命）:「…**醸造**」 | ELIGIBLE_EXPLICIT *(concept)* | *(none)* | — | — | **HOLD** | No canonical label for 醸造 (brewing). HOLD, no new tag. | no |
| 107-11 | 建部大社 | 112 `features/` | 「源氏の再興を祈願されました。後に大願成就したことから『頼朝公の出世水』と呼ばれ」 | REVIEW_REQUIRED | — | — | — | **HOLD** | Historical anecdote (Yoritomo success-water). An anecdote does not itself state a benefit. Not used. (The 出世運 PASS rests on the explicit 御神徳 list, not this anecdote.) | no |
| 107-12 | 建部大社 | histories 187 / 188 | *(disputed tradition histories)* | INELIGIBLE *(disputed Facts not usable)* | — | — | — | *(not a candidate)* | `disputed` Facts are not usable Recommendation Facts; not promoted, status unchanged, no benefit inferred from their narrative. | no |
| 108-1 | 波上宮 | 御祈願 page + 114 `由緒` | 御祈願一覧:「…**海上安全**」; 由緒:「出船は神に航路の平安を祈り、入船は航海無事の感謝を捧げた」 | ELIGIBLE_EXPLICIT | 海上安全 | 14 | **travel_safe** | **PASS** | Exact-string category on the official 御祈願 page; and the shrine's own 由緒 is centred on maritime / voyage safety. Strongest, most distinctive 波上宮 benefit. | write |
| 108-2 | 波上宮 | 御祈願 page | 「神前結婚式・**家内安全**・商売繁盛・初宮詣・厄祓・車祓・安産祈願」 | ELIGIBLE_EXPLICIT | 家内安全 | 7 | health / rest | **PASS** | Exact canonical match on the official 御祈願 category list. | write |
| 108-3 | 波上宮 | 御祈願 page | 「…家内安全・**商売繁盛**…」 /「**商売繁盛**、健康祈願、…」 (listed twice) | ELIGIBLE_EXPLICIT | 商売繁盛 | 4 | money | **PASS** | Exact canonical match; explicitly listed twice. | write |
| 108-4 | 波上宮 | 御祈願 page | 「…初宮詣・**厄祓**・車祓・安産祈願」 | ELIGIBLE_EXPLICIT | 厄除け | 2 | protection | **PASS** | 厄祓 → 厄除け: established narrow surface-form normalization. | write |
| 108-5 | 波上宮 | 御祈願 page | 「…厄祓・車祓・**安産祈願**」 | ELIGIBLE_EXPLICIT | 安産 | 16 | family | **PASS** | 安産祈願 → 安産: drop 祈願 suffix; single clean target. | write |
| 108-6 | 波上宮 | 御祈願 page | 「**交通安全祈願**」 | ELIGIBLE_EXPLICIT | 交通安全 | 3 | travel_safe | **PASS** | 交通安全祈願 → 交通安全: drop 祈願 suffix; exact concept. (車祓 corroborates.) | write |
| 108-7 | 波上宮 | 御祈願 page | 「…心願成就、**合格祈願**、良縁祈願…」 | ELIGIBLE_EXPLICIT | 合格祈願 | 10 | study / focus | **PASS** | Exact canonical match on the official 御祈願 list. | write |
| 108-8 | 波上宮 | 御祈願 page | 「…神恩感謝、**心願成就**、合格祈願…」 | ELIGIBLE_EXPLICIT | 心願成就 | 36 | money | **PASS** | Exact canonical match. | write |
| 108-9 | 波上宮 | 御祈願 page | 「…**健康祈願**…」 | ELIGIBLE_EXPLICIT *(concept)* | *(none — 健康長寿 adds 長寿)* | — | — | **HOLD** | No canonical label for bare 健康. 健康長寿 (id 24) adds "longevity" the Source did not state → semantic expansion, forbidden. HOLD. | no |
| 108-10 | 波上宮 | 御祈願 page | 「…**攘災招福**…」 | REVIEW_REQUIRED | *(none clean)* | — | — | **HOLD** | Compound set-phrase; splits ambiguously across 厄除け (already PASS) / 開運. No single clean canonical target. HOLD. | no |
| 108-11 | 波上宮 | 御祈願 page | 「…**良縁祈願**…」 | REVIEW_REQUIRED | *(≥2 plausible)* | — | — | **HOLD** | 良縁 maps plausibly to 縁結び (1) **and** 恋愛成就 (20) **and** 夫婦円満 (18). Contract: ≥2 plausible ⇒ HOLD. | no |
| 108-12 | 波上宮 | 114 `由緒` | 「出船は神に**航路の平安**を祈り、入船は**航海無事**の感謝を捧げた」 | REVIEW_REQUIRED | *(→ 航海安全 id 13?)* | — | — | **HOLD** | The 由緒 references voyage safety only in past-tense historical narrative, not a present-tense benefit declaration; the official 御祈願 page states **海上安全** (108-1 PASS), not 航海安全. 航海安全 (id 13) held pending an explicit declaration. | no |
| 108-13 | 波上宮 | history 191 (`tradition`) | content:「霊石を得て**祈ったところ豊漁となり**」 | REVIEW_REQUIRED | *(→ 豊漁: no canonical label)* | — | — | **HOLD** | Explicit outcome language exists, but 豊漁 has no canonical `GoriyakuTag`; the Fact is `tradition` (御鎮座伝説). HOLD, no new tag. | no |

## Shrine-level result (contract §8)

| Shrine | Result | Basis |
|---|---|---|
| 106 北海道神宮 | **UNKNOWN / review incomplete** | Only recorded Source unreachable this session; no PASS, no completed Source set. Explicitly **not** `NO_RECOMMENDATION_EVIDENCE` (terminal; needs a fully reviewed Source set). Re-review when `hokkaidojingu.or.jp` is reachable, or another approved Source is added. |
| 107 建部大社 | **RECOMMENDATION_READY** | ≥1 PASS whose resulting `GoriyakuTag` is Purpose-wired (all 8 PASS labels wired). Full Source set (111 / 112 / 113) reviewed this session; other candidates are HOLD (no canonical label) — non-blocking. |
| 108 波上宮 | **RECOMMENDATION_READY** | ≥1 PASS, Purpose-wired (all 8 PASS labels wired, incl. 海上安全 → `travel_safe`). Official 由緒 + 御祈願 pages reviewed. Other candidates HOLD. |

### Reviewer note — generic 御祈願 menu items

For 107 and 108 several PASS labels (家内安全, 商売繁盛, 厄除け, 安産, 交通安全, 合格祈願, 心願成就) come from the shrines' standard 御祈願 / 御神徳 lists — the near-universal Japanese prayer menu — rather than a shrine-distinctive statement. They are genuinely `ELIGIBLE_EXPLICIT` by the letter of the contract (the official Source explicitly names the benefit category and it maps exactly to a canonical label), so they PASS. The distinctive, Source-emphasised benefits are **出世運 / 勝運 / 開運** (107) and **海上安全** (108); each is listed first in its `goriyaku` string per the contract's evidence-strength order convention. A future policy could choose to HOLD generic-menu items; this pilot follows the current contract as written.

## Activation summary

Applied by a reversible, scoped data migration (see "Activation mechanism"). **106 is not activated.**

| id | `goriyaku` before | `goriyaku` after | `goriyaku_tags` before | `goriyaku_tags` after (id · name) |
|---|---|---|---|---|
| 106 北海道神宮 | *(empty)* | *(empty — unchanged)* | *(none)* | *(none — unchanged)* |
| 107 建部大社 | *(empty)* | `開運・厄除け・出世運・勝運・縁結び・商売繁盛・家内安全・病気平癒` | *(none)* | 6 開運 · 2 厄除け · 27 出世運 · 11 勝運 · 1 縁結び · 4 商売繁盛 · 7 家内安全 · 33 病気平癒 |
| 108 波上宮 | *(empty)* | `海上安全・家内安全・商売繁盛・厄除け・安産・交通安全・合格祈願・心願成就` | *(none)* | 14 海上安全 · 7 家内安全 · 4 商売繁盛 · 2 厄除け · 16 安産 · 3 交通安全 · 10 合格祈願 · 36 心願成就 |

`goriyaku` text (split on the `backfill_goriyaku_tags.parse_goriyaku` delimiter `・`) exactly equals the M2M canonical-label set for each shrine — no `HOLD` / `UNKNOWN` / `NO_EVIDENCE` candidate appears in either.

## Purpose connectivity verification (current code, verification only — no mapping change)

| Shrine | PASS label (tag id) | Currently wired Need(s) [repo] |
|---|---|---|
| 107 | 開運 (6) | career |
| 107 | 厄除け (2) | protection |
| 107 | 出世運 (27) | career |
| 107 | 勝運 (11) | mental, protection, courage |
| 107 | 縁結び (1) | love, relationship, marriage |
| 107 | 商売繁盛 (4) | money |
| 107 | 家内安全 (7) | health, rest |
| 107 | 病気平癒 (33) | health |
| 108 | 海上安全 (14) | **travel_safe** |
| 108 | 家内安全 (7) | health, rest |
| 108 | 商売繁盛 (4) | money |
| 108 | 厄除け (2) | protection |
| 108 | 安産 (16) | family |
| 108 | 交通安全 (3) | travel_safe |
| 108 | 合格祈願 (10) | study, focus |
| 108 | 心願成就 (36) | money |

**Every PASS label is Purpose-wired. `PASS_BUT_UNWIRED` count = 0.** P7 is unchanged; no mapping was added. Ordering was established Source-truth → review decision → canonical label → data activation → connectivity — never Purpose → desired label → reinterpret Source.

## Activation mechanism

Repository convention for a scoped Production data change to `Shrine.goriyaku` / `goriyaku_tags` is a **reversible `RunPython` data migration** (precedents: `0090_add_rest_healing_tag_to_silent_shrines`, `0091_fill_missing_local_shrine_reason_facts`, `0094_fix_shrine_70_coordinates`). `backfill_goriyaku_tags` was **rejected** as the write path: it has no id-scoping flag (processes every empty-tag shrine) and calls `GoriyakuTag.objects.get_or_create(name=…)` (can silently create a tag).

**`backend/temples/migrations/0095_batch17_recommendation_evidence_activation.py`** (data-only; `makemigrations --check` reports no model changes):

- acts on **pk 107 and 108 only** (106 not in the activation list);
- each shrine guarded by expected `name_jp` + `address` — a mismatch makes that shrine a no-op (0094 pattern);
- forward only acts when `goriyaku` is empty **and** `goriyaku_tags` is empty (re-run / already-activated ⇒ no-op — `BATCH17_TARGET_STATE_DRIFT` self-guard ⇒ idempotent);
- labels resolved by **exact name** against the live master via `GoriyakuTag.objects.filter(name=…).first()`; a missing label makes that shrine a no-op — **never `get_or_create`**;
- `SELECT` excludes `location` (`.only(...)`, the 0091/0094 legacy-`text`-column guard);
- reverse clears `goriyaku` + M2M **only** when the current state exactly matches what forward wrote (never clobbers a later edit).

### Production write safety gate

| # | Check | Result |
|---|---|---|
| 1 | exact planned before/after for 106/107/108 | shown above (Activation summary) |
| 2 | no target drift since read | re-verified [prod] immediately before finalizing — 106/107/108 still empty `goriyaku` / 0 tags / `updated_at` 2026-08-23 09:04:13 |
| 3 | every proposed tag exists in the current master | 13 distinct labels re-queried [prod]; all present (ids 1,2,3,4,6,7,10,11,14,16,27,33,36) |
| 4 | no proposed label would trigger `get_or_create` | migration uses `filter(name=…).first()`; missing label ⇒ no-op. Tests `test_no_new_goriyaku_tag_is_created`, `test_missing_canonical_label_makes_that_shrine_noop` |
| 5 | write scope is exactly 106/107/108 | activation list = {107, 108}; 106 excluded; test `test_activation_is_scoped_to_107_108_only` (106 + an unrelated shrine both unchanged) |
| 6 | sanctioned Production write mechanism | **only a READ-ONLY Production credential is available in this session.** Not bypassed. No ad-hoc SQL, no disabled guards, no invented credentials. The migration is the repository's sanctioned write path; it applies on the next authorized `migrate` / deploy. |

**`PRODUCTION_ACTIVATION = PENDING_AUTHORIZED_APPLY`** — the reviewed evidence + the deterministic, tested, reversible migration are committed; Production rows 107 / 108 are mutated only when the migration is applied through the normal authorized deploy path.

## Safety confirmation

- **No inferred benefit** — every PASS rests on an explicit benefit-category statement in the shrine's own official Source (御神徳 list / 御祈願 category list). No PASS derives from shrine name, deity name, deity role, historical fame, founding story, anecdote, tradition, tourism reputation, or background knowledge.
- **No new taxonomy** — no `GoriyakuTag` created; every label is an existing canonical row; `makemigrations --check` = no model changes.
- **No mapping change** — `NEED_TO_GORIYAKU_IDS` / `NEED_TEXT_WEIGHTS` untouched; `travel_safe = {3, 13, 14}` unchanged; P7 not started.
- **No disputed-Fact promotion** — 建部大社 histories 187 / 188 remain `disputed`; not read as evidence; no benefit inferred from their narrative; the `verification_status` / `confidence` of no Fact changed.
- **No other Shrine modification** — only pk 107 and 108; 106 and every other row untouched (test-verified).
- **No `ShrineDeity` / `ShrineHistory` / `ShrineKnowledgeSource` change**; no Evidence Gate / interpreter / scoring / ranking / C1 / Lead / Reason / Compass / Concierge / frontend / Google Spreadsheet change.

## Tests

`backend/temples/tests/test_migration_0095_batch17_recommendation_evidence.py` (11 tests — forward/reverse functions exercised directly against the real models via a tiny `apps` shim):

| Mandatory check | Test |
|---|---|
| 1 only PASS labels written | `test_forward_writes_exactly_the_pass_label_set` |
| 2 HOLD / UNKNOWN / NO_EVIDENCE never written | `test_hold_and_unknown_candidates_are_not_written` |
| 3 all written labels already exist | covered by 1 + `test_missing_canonical_label_makes_that_shrine_noop` |
| 4 no new `GoriyakuTag` | `test_no_new_goriyaku_tag_is_created`, `test_missing_canonical_label_makes_that_shrine_noop` |
| 5 M2M exactly equals PASS set | `test_forward_writes_exactly_the_pass_label_set` |
| 6 scoped to 106/107/108 (only 107/108 written) | `test_activation_is_scoped_to_107_108_only` |
| 7 idempotent | `test_forward_is_idempotent` |
| 8 unrelated rows unchanged | `test_activation_is_scoped_to_107_108_only`, `test_target_with_preexisting_state_is_not_overwritten` |
| 9 Evidence Gate unchanged | `test_need_mapping_and_evidence_gate_untouched_by_this_migration` |
| 10 Need mapping unchanged | `test_need_mapping_and_evidence_gate_untouched_by_this_migration` |
| + identity-mismatch no-op / reverse restores empty / reverse leaves later edits alone | `test_pk_present_but_identity_mismatch_is_noop`, `test_reverse_restores_empty_state`, `test_reverse_leaves_a_later_edit_alone` |

Local migration application: `python manage.py migrate temples` applies `0095` cleanly; `migrate temples 0094` reverses it cleanly; re-apply cleanly. Full `backend/temples` suite: **1918 passed, 13 skipped, 0 failed**. Focused regression (need mapping, evidence gate ×3, knowledge selector, backfill, coverage, concierge candidate/dedupe, Batch 17 seed, migration 0094): **145 passed**. `git diff --check`: clean. markdownlint (`.markdownlint.json` rules): 0 issues.

## Newly discovered inconsistencies

- **`hokkaidojingu.or.jp` TLS certificate is expired** — blocks any re-fetch of 北海道神宮's only recorded Source this session. Recorded as `SOURCE_ACCESS = UNAVAILABLE` → 106 stays UNKNOWN. A future re-review needs a reachable Source (or an added approved Source).
- **The task named the output file `docs/audit/batch17-recommendation-evidence-review.md`, but that path is an already-merged doc** (PR #2575, the review-only pilot). This activation record is at `docs/audit/batch17-recommendation-evidence-activation.md` to preserve that history; the prior doc is unchanged.
- 建部大社 `features/` page contributes only an anecdote (`頼朝公の出世水`); DB history 189 transcribes the Yoritomo narrative. Neither is used — the 出世運 PASS rests solely on the explicit 御神徳 list. Noted so a later reviewer does not double-count.
- 波上宮 history 191 (`tradition`) content contains the exact 「祈ったところ豊漁となり」 outcome phrasing the contract §3 cites as 波上宮's explicit-evidence example — but 豊漁 has no canonical `GoriyakuTag`, so it is non-actionable regardless (HOLD).

## STOP / completion

No STOP condition triggered (targets untouched, master aligned, identities unambiguous, no PASS needs new taxonomy or a mapping change, write mechanism safely scoped, read-only Production controls respected). PR created. **Not merged.** P3 not broadened. P1 / P2 / P4 / P5 / P6 / P7 / P8 not started.
