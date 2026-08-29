# Shrine Evidence Integrity Pilot

## 1. Audit metadata

| Field | Value |
|---|---|
| Task | Shrine Evidence Integrity Pilot — **PR-B** of the full-integrity-audit sequence (PR-A = `docs/audit/shrine-evidence-audit-readiness.md`, merged as #2610) |
| Type | Audit / pilot. **Read-only.** No Shrine data, Knowledge data, GoriyakuTag, `Shrine.goriyaku`, Need mapping, Evidence Gate, Recommendation Engine, seed, fixture, model, migration, frontend, or Google Spreadsheet change. |
| Branch | `audit/shrine-evidence-integrity-pilot` |
| Worktree | `~/Developer/jinja_app-shrine-evidence-integrity-pilot` (isolated, from `origin/develop`; control repo untouched) |
| Date | 2026-08-29 |

### Evidence labels

- **[repo]** — read from tracked source at the base SHA.
- **[dev-db]** — read-only query against the **local development Postgres** (`jinja_db` @ 127.0.0.1). **Not Production.** See §7 — this DB is not a confirmed Production mirror and, as §16 shows, its `GoriyakuTag` PK space does not match the canonical-master numbering the code assumes.
- **[src]** — content fetched this session from an official shrine website (URLs recorded in the DB).
- **[prior]** — value from an earlier audit document; not re-derived here.
- **NOT VERIFIED** — could not be checked this session.

## 2. Base SHA

- **`origin/develop` @ `ece435611dbc44412edf824ad8f75bff27e3c702`** (merge of PR #2610). Fetched this session; matches the task's stated SHA.
- Worktree HEAD = same SHA; working tree clean at checkout and at commit time (`git status --porcelain` empty except this new file).

## 3. Scope / non-scope

### In scope

Access gate; strongest available read for the canonical shrine set; duplicate-candidate reconciliation from current data; `FULL_AUDIT_DENOMINATOR` decision packet; final pilot selection (5–10 real shrine identities); Spreadsheet↔DB identity audit; current DB semantic snapshot per pilot shrine; official-source spot audit; Source↔Knowledge-Fact integrity; Source↔goriyaku/GoriyakuTag integrity; **current-code** Purpose connectivity; per-shrine integrity matrix; aggregate; method verdict; PR-C spec.

### Non-scope (enforced)

DB writes · Production writes · Spreadsheet edits · Shrine / Knowledge Fact / GoriyakuTag / `Shrine.goriyaku` / Need-mapping / Evidence-Gate / Recommendation-Engine modification · seed / fixture / model / migration · frontend / API · new taxonomy · starting PR-C · remediation PRs · extrapolating pilot rates to all shrines.

## 4. Existing contracts and current-code authority

Re-read at the base SHA. **Current code / tests / DB are physical truth; where a historical audit doc disagrees, the drift is recorded and code wins** (task "Critical Authority Rule").

| Concern | Current authority [repo] |
|---|---|
| Real-vs-QA shrine set | `backend/temples/services/shrine_qa_fixture_exclusion.py` — name-convention exclusion, no hard-coded ids |
| Coverage aggregation | `backend/temples/services/knowledge_coverage_report.py` + `management/commands/knowledge_coverage_report.py` — delegates QA exclusion, fact usability (Evidence Gate), fact selection to their owners; read-only |
| Per-Fact usability | `backend/temples/services/evidence_gate.py` `decide_fact_usability(*, verification_status, confidence, source_verification_statuses)` — `usable = fact_ready AND ≥1 fact-ready source`; `confidence` is metadata only |
| Fact selection (Recommendation) | `backend/temples/services/shrine_knowledge_selector.py` |
| Need → GID mapping | `backend/temples/domain/need_to_goriyaku_tag_ids.py` `NEED_TO_GORIYAKU_IDS` |
| goriyaku text → tag M2M | `backend/temples/management/commands/backfill_goriyaku_tags.py` `parse_goriyaku()` — `GoriyakuTag.objects.get_or_create(name=…)`, **name-based, PK-agnostic** |
| Evidence eligibility / review states | `docs/knowledge/recommendation-evidence-review-contract.md` (ELIGIBLE_EXPLICIT / REVIEW_REQUIRED / INELIGIBLE / UNKNOWN; PASS / HOLD / NO_EVIDENCE / REVISE; LEGACY_EXISTING) |
| Knowledge Fact meaning / source / verification | `docs/knowledge/shrine-knowledge-contract.md` (Active) |
| Coverage taxonomy | `docs/core/recommendation-readiness.md` (Active) — Schema / Populated / Verified / Usable |
| Mixed confidence | `docs/audit/mixed-confidence-policy-decision.md` — `FULL_SUPPRESSION` (ACTIVE_DECISION_RECORD, not a contract; PR-A §4.1a). Not re-litigated. |

**Current-code mapping values, re-confirmed [repo] + `test_need_to_goriyaku_tag_ids.py` (115-test run, all pass):**

```
communication = set()          (EVIDENCE_LIMITED / DISABLE_GID_EVIDENCE)
family        = {16, 35}        (NARROW / DROP_ALL — intent: 安産 + 子宝)
mental        = {11, 26, 28, 38}  (id 16 excluded)
travel_safe   = {3, 13, 14}     (intent: 交通安全 + 航海安全 + 海上安全)
career∩courage = {12, 30}       (KEEP_SHARED, intentional)
```

`test_need_to_goriyaku_tag_ids.py` pins `CANONICAL_MASTER_ID_RANGE = range(1, 40)` — i.e. **the mapping is authored against a 39-row canonical `GoriyakuTag` master numbered 1–39**. This is the key premise §16 tests against the live DB.

The stale "ids 13/14 not wired to any Purpose" note in `recommendation-evidence-review-contract.md` §8/§19 is **not reproduced** — current code wires `travel_safe = {3, 13, 14}` [repo].

## 5. Access gate

| Data source | State this session |
|---|---|
| Google Spreadsheet "神社のDB" | **`CODEX_SESSION_SPREADSHEET_ACCESS = BLOCKED`** — no authenticated snapshot/export supplied to this worktree or session; direct fetch of `/edit` and `?export=csv` returns HTTP 401. Per PR-A this is a session/environment limitation, **not** a project-wide failure (Mother Ship authenticated Drive/Sheets access exists). No unauthenticated scraping attempted beyond the two canonical URLs. **No spreadsheet cell content is used or invented in this document.** |
| Production DB (direct read-only) | **not available** — no credential path supplied to this session |
| Production DB dump / export | **not supplied** |
| Production API (all identity fields) | not used — no evidence it exposes `canonical_status` / `official_*` / coordinate-audit fields |
| Local dev DB (`jinja_db`) | available, read-only — used for all `[dev-db]` observations, explicitly **not** as Production truth |
| Official shrine websites | reachable — used for the §13 spot audit (2 shrines) |

## 6. Spreadsheet access path

- Required dimensions (task list): `id, name_jp, address, latitude, longitude, canonical_status, official_name, official_address, official_source_type, official_source_url, verified_at, reference_latitude, reference_longitude, coordinate_delta_m, coordinate_status, notes, google_place_id, position_source_type, position_source_url, position_source_note`.
- **None read this session.** The Spreadsheet↔DB identity join (§11) is therefore **NOT VERIFIED**.
- Path for PR-C: a Mother Ship operator or connected Google Drive/Sheets environment supplies a read-only CSV/snapshot of the sheet with the columns above; PR-B/PR-C then join on a verified id correspondence (§11 method).

## 7. Production / canonical shrine set

**`CANONICAL_REAL_SHRINE_SET = NOT VERIFIED`** — no Production read path this session (§5). The denominator decision (§9) is therefore held.

What is known, `[dev-db]` only (read-only, `jinja_db`, 2026-08-29):

| Metric | Value |
|---|---|
| `Shrine` rows total (`RAW_DB_ROW_COUNT`) | **105** |
| ids | 1..105, contiguous |
| QA/test fixture rows (`exclude_qa_fixture_shrines` [repo]) — `QA_FIXTURE_COUNT` | **5** — ids 101–105: `承認テスト神社`, `admin承認テスト神社`, `重複検証神社`, `重複検証神社`, `重複検証神社（別宮）` |
| real rows (post QA exclusion) — `REAL_DB_ROW_COUNT` | **100** (ids 1–100) |
| real-shrine duplicate `name_jp` | **0** |
| rows with lat AND lng | 105 / 105 |
| rows with `place_ref` set | **0** |
| `knowledge_coverage_report` "Audit Target Shrines" | 100 |

**Drift vs `[prior]`:** `[prior]` `shrine-dataset-integrity.md` recorded Production = 105 rows with 3 duplicate real-shrine `name_jp` pairs (~102 unique); this dev DB has **no** such duplicate real rows and its extra 5 rows are QA fixtures. The two 105s are still different sets, and neither is confirmed as current Production.

## 8. Duplicate reconciliation

Re-checked the three historical duplicate candidates from **current** `[dev-db]` data:

| Candidate | `[dev-db]` rows | name_jp | address | lat / lng | place_ref | Classification |
|---|---|---|---|---|---|---|
| 長太稲荷神社 | **1** (id 21) | 長太稲荷神社 | 〒157-0065 東京都世田谷区上祖師谷１丁目３−１０ | 35.660614 / 139.6017688 | — | **`NOT_DUPLICATED_CURRENTLY`** (dev DB). `[prior]` Production had 21/103. |
| 給田六所神社 | **1** (id 22) | 給田六所神社 | 〒157-0064 東京都世田谷区給田１丁目３−７ | 35.662443 / 139.5920237 | — | **`NOT_DUPLICATED_CURRENTLY`** (dev DB). `[prior]` Production had 22/101. |
| 富岡八幡宮 | **1** (id 49) | 富岡八幡宮 | 東京都江東区富岡1-20-3 | 35.6733 / 139.7967 | — | **`NOT_DUPLICATED_CURRENTLY`** (dev DB). `[prior]` Production had 49/104 (weaker candidate). |

Nothing deleted or merged. **The duplicate question is `AMBIGUOUS` overall**: current Production is unread, and the last-recorded Production state disagrees with this dev DB. Whether the 3 pairs still exist in Production is `NOT VERIFIED`. Where a pair does exist, the audit unit is the *real shrine identity* while every DB row is preserved in the evidence table (no PR-B row-deletion choice).

## 9. Denominator decision packet

Computed from current evidence only.

| Term | Value | Basis |
|---|---|---|
| `RAW_DB_ROW_COUNT` | **105** | `[dev-db]` |
| `QA_FIXTURE_COUNT` | **5** | `[dev-db]` + `shrine_qa_fixture_exclusion.py` |
| `REAL_DB_ROW_COUNT` | **100** | `[dev-db]` (105 − 5) |
| `CONFIRMED_DUPLICATE_ROW_COUNT` | **0** in this dev DB; **NOT VERIFIED** for Production | §8 |
| `UNIQUE_REAL_SHRINE_IDENTITY_COUNT` | **100** if this dev DB is canonical; **NOT VERIFIED** — last-recorded Production state implies ~102 | §7–§8 |

**Recommendation: `FULL_AUDIT_DENOMINATOR = MOTHER_SHIP_DECISION_PENDING`.** Evidence is incomplete: `CANONICAL_REAL_SHRINE_SET` is unread, and the local dev DB and the last-recorded Production state disagree on both row count composition and duplicates. The number is **not inferred**. It is 100 / ~102 / 105 / another reconciled value pending a Production read + Mother Ship decision (§20.1).

## 10. Pilot selection

Started from the PR #2610 candidate pool. Re-validated each against the **current `[dev-db]` canonical set**.

### Rejected (absent from current canonical set)

| Candidate | Reason |
|---|---|
| 建部大社 | **not present in `[dev-db]`** (`Shrine.objects.filter(name_jp__icontains='建部')` → 0). It is a Batch-17 shrine; this dev DB predates Batch-17 import. Its `[prior]` HOLD result (`batch17-recommendation-evidence-review.md`) cannot be revalidated here → **prior-audit-vs-current-DB drift**. |
| 北海道神宮 | not present in `[dev-db]` (same as above; `[prior]` NO_RECOMMENDATION_EVIDENCE). |
| 波上宮 | not present in `[dev-db]` (same; `[prior]` "partial / voyage-safety PASS candidate"). |

### Final pilot (8 real shrine identities, all present in `[dev-db]`)

| # | Shrine | id | Variety axis it covers |
|---|---|---|---|
| P1 | 明治神宮 | 1 | previously well-verified (Pilot #1); `shrine_official` sources; source spot-audited (§13) |
| P2 | 品川神社 | 50 | previously well-verified (Pilot #2); `has_multiple_sources`; multi-fact |
| P3 | 太宰府天満宮 | 6 | multiple GoriyakuTags; **LEGACY_EXISTING** goriyaku; source spot-audited (§13); archetypal `study` shrine — used to test Purpose connectivity |
| P4 | 伊勢神宮（内宮） | 3 | `[prior]` "Zero-Knowledge" (`recommendation-readiness.md`); **now has 1 deity + 1 history** in `[dev-db]` → prior-audit drift; history `history_type = tradition` |
| P5 | 阿佐ヶ谷神明宮 | 29 | **CONFIDENCE_MIXED** deity set (`high`, `medium`, `medium`) → `FULL_SUPPRESSION` case |
| P6 | 給田六所神社 | 22 | **no `shrine_official` source** (`secondary_editorial` + `local_history`), all `medium`; `goriyaku` stored as a prose sentence, not delimited labels |
| P7 | 護王神社 | 99 | niche benefit (`足腰健康`); 4 deities + 2 histories, all `high` / `shrine_official`; history faithfully transcribes the source's own "創建年は伝えられていません" uncertainty |
| P8 | 長太稲荷神社 | 21 | **genuine Zero-Knowledge** (0 deity, 0 history); historical duplicate candidate (now `NOT_DUPLICATED_CURRENTLY`, §8) |

Swap-in noted, not used: **多摩川浅間神社 (id 70)** — coordinate-correction subject (migration `0094`; stored coords corrected from a nearby bakery ~250 m off). Deferred to a coordinate-focused PR-C round because the coordinate-audit dimension needs the Spreadsheet's `reference_latitude` / `coordinate_status` columns, which are unread (§6).

## 11. Spreadsheet ↔ DB identity results

**`CODEX_SESSION_SPREADSHEET_ACCESS = BLOCKED`** (§5). No sheet rows read. Therefore, for every pilot shrine:

| Dimension | Result |
|---|---|
| `spreadsheet_identity_status` (`EXACT_ID_MATCH` / `IDENTITY_MATCH` / `AMBIGUOUS` / `MISSING_IN_SHEET` / `MISSING_IN_DB`) | **NOT VERIFIED** for all 8 |
| name / official_name / address / official_address / coordinates / canonical_status / coordinate_status / official source metadata | **NOT VERIFIED** for all 8 |
| `SHEET_DRIFT` / `DB_DRIFT` / `IDENTITY_REVIEW_REQUIRED` | cannot be assessed |

DB-side identity facts that *are* known `[dev-db]` (name_jp, address, lat/lng — §12) are recorded but not joined. **No join results are invented.** This dimension is the first deliverable of PR-C once §6's access path exists.

## 12. Current semantic DB snapshots

Read-only `[dev-db]`. `goriyaku_tag` column shows **(PK, name)** — the PK space is analysed in §16.

| id | name_jp | address | lat / lng | `goriyaku` (text) | `goriyaku_tags` (PK, name) | deity / history rows | Source types (distinct) |
|---|---|---|---|---|---|---|---|
| 1 | 明治神宮 | 東京都渋谷区代々木神園町1-1 | 35.6764 / 139.6993 | `縁結び・厄除け・交通安全` | (1 縁結び)(16 厄除け)(10 交通安全) | 2 / 1 | `shrine_official`, `user_observation` |
| 50 | 品川神社 | 東京都品川区北品川3-7-15 | 35.6229 / 139.7426 | `開運・金運` | (18 開運)(36 金運) | 3 / 3 | `shrine_official` (multi-source) |
| 6 | 太宰府天満宮 | 福岡県太宰府市宰府4-7-1 | 33.5213 / 130.5351 | `学業成就・合格祈願・厄除け` | (3 学業成就)(4 合格祈願)(16 厄除け) | 1 / 1 | `shrine_official` |
| 3 | 伊勢神宮（内宮） | 三重県伊勢市宇治館町1 | 34.455 / 136.7256 | `開運・厄除け・家内安全` | (16 厄除け)(9 家内安全)(18 開運) | 1 / 1 (`history_type=tradition`) | `shrine_official` |
| 29 | 阿佐ヶ谷神明宮 | 東京都杉並区阿佐谷北1-25-5 | 35.705 / 139.6353 | `厄除け・八難除・縁結び` | (28 八難除)(16 厄除け)(1 縁結び) | 3 / 0 | `shrine_official`, `secondary_editorial` |
| 22 | 給田六所神社 | 〒157-0064 東京都世田谷区給田1丁目3−7 | 35.662443 / 139.5920237 | `地域の氏神として、暮らしや家内安全、日々の無事を見守る神社。` | (14 地域安泰)(9 家内安全) | 2 / 4 | `secondary_editorial`, `local_history` |
| 99 | 護王神社 | 京都府京都市上京区烏丸通下長者町下ル桜鶴円町 | 35.0186 / 135.7583 | `足腰健康・厄除け・勝運` | (45 足腰健康)(16 厄除け)(20 勝運) | 4 / 2 | `shrine_official` |
| 21 | 長太稲荷神社 | 〒157-0065 東京都世田谷区上祖師谷1丁目3−10 | 35.660614 / 139.6017688 | *(empty)* | *(none)* | 0 / 0 | *(none)* |

Evidence-Gate `usable` (`decide_fact_usability`, `[dev-db]`): every deity/history row above is `usable = True` for P1–P7 (all `verification_status = source_confirmed`, all with ≥1 `source_confirmed` source). P8 has no facts. This matches `knowledge_coverage_report` [dev-db]: Fact-ready Deity 86/100, History 84/100 — i.e. **Usable Coverage ≈ Populated Coverage** in this DB (no `draft`/`disputed`/`no-source` facts among audit-target shrines).

## 13. Official Sources

Spot audit of the two pilot shrines whose official source is recorded in `[dev-db]`, fetched this session **[src]**. (P4–P8 official-source fetching is deferred to PR-C — see §19; the DB already records `shrine_official` URLs for P4/P7.)

### P1 — 明治神宮 · `https://www.meijijingu.or.jp/about/` [src]

| Category | Source content [src] |
|---|---|
| DEITY | 明治天皇, 昭憲皇太后 — "第122代天皇の明治天皇と皇后の昭憲皇太后を御祭神としておまつりしています。" |
| HISTORY | 大正9年(1920) 創建, 代々木; national-sentiment founding narrative |
| TRADITION | — |
| EXPLICIT_GORIYAKU | "…**家内安全、厄祓**等の御祈願をとり行っています。" (household-safety, warding prayers). Wedding ceremonies are **performed** ("結婚式") but stated as a service, not a 縁結び benefit. **No 縁結び statement. No 交通安全 statement.** |
| OTHER | — |

### P3 — 太宰府天満宮 · `https://www.dazaifutenmangu.or.jp/about/goyuisho` [src]

| Category | Source content [src] |
|---|---|
| DEITY | 菅原道真公 — hall built above his burial site |
| HISTORY | 903 逝去 → 味酒安行 埋葬・祀庿 → 919 勅命で社殿造営; 現本殿 1591 (小早川隆景), 国重要文化財 |
| TRADITION | ox-cart legend (遺骸を運ぶ牛が動かなくなった → 神意) |
| EXPLICIT_GORIYAKU | opening line: "**学問・文化芸術・厄除けの神様**"; prayer menu: **受験合格祈願**, **学業上達祈願**, **厄除祈願** |
| OTHER | — |

No Wikipedia/tourism page was used as primary proof for either — official pages were available and sufficient (contract order-of-preference respected).

## 14. Knowledge Fact integrity results

Per-Fact classification (`MATCH` / `PARTIAL` / `UNSUPPORTED` / `MISSING` / `REVIEW_REQUIRED`).

| Shrine | Fact | DB value `[dev-db]` | Source support | verification_status / confidence | Classification |
|---|---|---|---|---|---|
| P1 明治神宮 | deity | 明治天皇 (+2nd row) | [src] states 明治天皇 + 昭憲皇太后 | `source_confirmed` / `high` | **MATCH** (confirm 2nd row = 昭憲皇太后 in PR-C) |
| P1 | history | "明治神宮は…大正9年（1920）に創建された。" (`official_origin`) | [src] 大正9年(1920) 創建, 代々木 | `source_confirmed` / `high` | **MATCH** |
| P3 太宰府 | deity | 菅原道真公 (`primary`) | [src] 菅原道真公 | `source_confirmed` / `high` | **MATCH** |
| P3 | history | "昌泰4年（901年）…左遷され、延喜3年（903年）…延喜19年（919…" (`official_origin`) | [src] 903 逝去 / 919 勅命 (DB adds the 901 exile detail; consistent) | `source_confirmed` / `high` | **MATCH** |
| P4 伊勢内宮 | deity | 天照大御神 (`primary`) | official URL recorded; not re-fetched this session | `source_confirmed` / `high` | **REVIEW_REQUIRED** (fetch in PR-C — but note `[prior]` "Zero-Knowledge" is now stale) |
| P4 | history | "…垂仁天皇の御代…" (`history_type = tradition`) | not re-fetched | `source_confirmed` / `medium` | **REVIEW_REQUIRED** — tradition-type; wording must be checked against the source for non-assertive lineage phrasing (`shrine-knowledge-contract.md`) |
| P5 阿佐ヶ谷 | deity ×3 | 天照大神 (`primary`, official) + 2 `secondary` | primary URL `shinmeiguu.com`; secondaries cite ja.wikipedia | primary `high`; secondaries `medium` | **REVIEW_REQUIRED** + **`CONFIDENCE_MIXED`** — `FULL_SUPPRESSION` applies to Reason (decision record; not a defect) |
| P6 給田六所 | deity ×2 / history ×4 | 大国魂大神 ほか | **no `shrine_official`** — `secondary_editorial` (Wikipedia) + `local_history` (tesshow.jp) | all `medium` | **REVIEW_REQUIRED** + **`PROVENANCE_WEAK`** — allowed source types per contract, but no primary/official source for any fact |
| P7 護王神社 | deity ×4 / history ×2 | 和気清麻呂公命 ほか | official `gooujinja.or.jp/yuisho/` recorded; history text explicitly quotes the source's "創建年は伝えられていません" | `source_confirmed` / `high` | **MATCH** (provisional; confirm in PR-C) — good example of faithful uncertainty transcription |
| P8 長太稲荷 | — | none | — | — | **MISSING** (Zero-Knowledge) |

`source_confirmed` in the DB is **not** treated as sufficient on its own — P1/P3 were confirmed against fetched source text; P4–P7 are `REVIEW_REQUIRED` pending a PR-C fetch.

## 15. Goriyaku / Recommendation Evidence results

Applying `recommendation-evidence-review-contract.md` to each pilot shrine's `goriyaku` tags. **Tag PK vs name is analysed here by name** (the contract is name-based, via `backfill_goriyaku_tags`); the PK-space problem is §16.

| Shrine | goriyaku label | Source phrase [src] / provenance | Eligibility | Review state | DB tag integrity |
|---|---|---|---|---|---|
| P3 太宰府 | 学業成就 | "学問…の神様" + 学業上達祈願 [src] | `ELIGIBLE_EXPLICIT` | **PASS** (narrow normalization 学問→学業成就) | **MATCH** |
| P3 | 合格祈願 | "受験合格祈願" [src] | `ELIGIBLE_EXPLICIT` | **PASS** | **MATCH** |
| P3 | 厄除け | "厄除けの神様" + 厄除祈願 [src] | `ELIGIBLE_EXPLICIT` | **PASS** | **MATCH** |
| P1 明治神宮 | 厄除け | "厄祓等の御祈願" [src] | `ELIGIBLE_EXPLICIT` | **PASS** (厄祓→厄除け) | **MATCH** |
| P1 | 縁結び | not stated on `/about/` [src] ("結婚式" is a service, not a benefit statement) | `REVIEW_REQUIRED` / `INELIGIBLE` on this source | **HOLD** | **UNSUPPORTED** on the checked source · `LEGACY_EXISTING_WITHOUT_PROVENANCE` |
| P1 | 交通安全 | not stated on `/about/` [src] | `REVIEW_REQUIRED` / `INELIGIBLE` on this source | **HOLD** | **UNSUPPORTED** on the checked source · `LEGACY_EXISTING_WITHOUT_PROVENANCE` |
| P2 品川神社 | 開運, 金運 | not fetched this session | `UNKNOWN` | pending | **REVIEW_REQUIRED** · `LEGACY_EXISTING_WITHOUT_PROVENANCE` (no review doc) |
| P4 伊勢内宮 | 開運, 厄除け, 家内安全 | not fetched | `UNKNOWN` | pending | **REVIEW_REQUIRED** · `LEGACY_EXISTING_WITHOUT_PROVENANCE` |
| P5 阿佐ヶ谷 | 厄除け, 八難除, 縁結び | not fetched | `UNKNOWN` | pending | **REVIEW_REQUIRED** · `LEGACY_EXISTING_WITHOUT_PROVENANCE` |
| P6 給田六所 | *(prose sentence, tags 地域安泰 + 家内安全)* | prose text is not a benefit declaration; `地域安泰` label not literally in the text | `REVIEW_REQUIRED` | **HOLD** | **UNSUPPORTED / REVIEW_REQUIRED** — tag set may have been hand-set, not `backfill`-derived; `地域安泰` is also an **UNWIRED** GID (§16) |
| P7 護王神社 | 足腰健康, 厄除け, 勝運 | official URL recorded, not fetched | `UNKNOWN` | pending | **REVIEW_REQUIRED** · `LEGACY_EXISTING_WITHOUT_PROVENANCE` |
| P8 長太稲荷 | *(none)* | — | — | `NO_EVIDENCE` (no goriyaku, no source) | **MISSING** |

**`LEGACY_EXISTING_WITHOUT_PROVENANCE` count in the pilot: 5 shrines** (P1, P2, P4, P5, P7) carry seed `goriyaku` with no Evidence-Review-Contract provenance record. Not grandfathered — flagged.

## 16. Purpose connectivity from current code

Read `backend/temples/domain/need_to_goriyaku_tag_ids.py` [repo] and checked it against the **live `[dev-db]` `GoriyakuTag` table**.

### 16.1 CRITICAL DRIFT — `GoriyakuTag` PK space ≠ canonical-master numbering (this dev DB)

- `NEED_TO_GORIYAKU_IDS` and `test_need_to_goriyaku_tag_ids.py` assume a **39-row canonical master, ids 1–39**, where e.g. `id 9 = 学業成就`, `id 16 = 安産`, `id 35 = 子宝`, `id 3 = 交通安全` (`recommendation-evidence-review-contract.md` §5 lists this master).
- The **live `[dev-db]` `GoriyakuTag` table has 46 rows**: ids **1–15 = a legacy taxonomy** (tracked fixture `backend/temples/fixtures/goriyaku_tags.json`, compound names like `子宝・安産`, `厄除け・方除け`, `勝運・必勝祈願`), then ids **16–46 = (most of) the canonical master, renumbered starting at 16** (`id 16 = 厄除け`, `id 35 = 出世運`, `id 42 = 子宝`, …). No migration or tracked seed creates ids 16–46 — they were added out-of-band.
- Result: interpreting `NEED_TO_GORIYAKU_IDS` against this dev DB's PKs is **semantically wrong**:

| Need | mapping ids [repo] | Names those ids hold **in this dev DB** | Intended names (canonical master) |
|---|---|---|---|
| `study` | `{9, 10}` | 家内安全, 交通安全 | 学業成就, 合格祈願 |
| `family` | `{16, 35}` | 厄除け, 出世運 | 安産, 子宝 |
| `travel_safe` | `{3, 13, 14}` | 学業成就, 五穀豊穣, 地域安泰 | 交通安全, 航海安全, 海上安全 |
| `mental` | `{11, 26, 28, 38}` | 厄除け・方除け, 八方除, 八難除, 強運厄除け | 勝運, 家庭円満, 金運, 強運厄除け |

- **Live proof — 太宰府天満宮 (id 6)**, `goriyaku_tags` PKs `[3, 4, 16]` (学業成就 / 合格祈願 / 厄除け):
  - `study = {9, 10}` → **no intersection** with `[3, 4, 16]` → 太宰府天満宮, the archetypal exam-success shrine, **does not match `study` via GID** in this DB.
  - `money = {4, 5, 28, 36}` → intersects PK `4` → 太宰府 **spuriously matches `money`**.
  - `family = {16, 35}` → intersects PK `16` → 太宰府 **spuriously matches `family`**.

### 16.2 Consequence for the pilot

`purpose_connectivity` (Phase 10) **cannot be meaningfully audited against this dev DB.** Two possibilities, both `NOT VERIFIED` without Production access:

1. **Dev-DB-only corruption** — Production has the clean 39-row master at ids 1–39, the legacy 15-row block was never present / already cleaned there, and this dev DB is simply an unreliable substrate. (The mapping code + tests would then be correct against Production.)
2. **Production also drifted** — Production carries the same 46-row mixed table, in which case the live Recommendation Engine mis-routes Purposes (e.g. 太宰府 → `money`/`family`, not `study`) for real users.

### 16.3 UNWIRED canonical tags (independent, name-level) [dev-db] + [repo]

By **name**, several canonical GoriyakuTag concepts are consumed by no Need in `NEED_TO_GORIYAKU_IDS`: 商売繁盛, 福徳, 航海安全, 海上安全, 安産, 恋愛成就, 美容, 芸能運, 技芸上達, 八方除け, 火防, 子宝, 心願成就, 延命長寿, 足腰健康, 農業守護, 地域安泰. Notable for the pilot: **`安産` and `子宝` (family's *intent*) and `足腰健康` (P7 護王神社's headline benefit) are UNWIRED by name** — `family = {16, 35}` only reaches them if the DB numbering matches the canonical master (§16.1). `communication = set()` is intentionally UNWIRED (EVIDENCE_LIMITED). `travel_safe = {3, 13, 14}` **is** wired [repo] — the stale "13/14 unwired" doc note is not reproduced.

## 17. Per-shrine integrity matrix

`integrity_status ∈ {MATCH, PARTIAL, UNSUPPORTED, MISSING, REVIEW_REQUIRED}`. Root-cause labels are **audit-only** (not product taxonomy): `SHEET_DRIFT`, `DB_DRIFT`, `KNOWLEDGE_DRIFT`, `TAG_DRIFT`, `PROVENANCE_WEAK`.

| # | shrine_identity | db_rows | spreadsheet_identity | location | knowledge | deity | history | tradition | source_provenance | current_goriyaku | goriyaku_tags (PK,name) | rec_evidence_items | purpose_connectivity | **integrity_status** | root_causes | remediation_candidate | prior_audit_refs | revalidation_required |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 明治神宮 | id 1 | NOT VERIFIED | lat/lng present; correctness NOT VERIFIED | present | MATCH [src] | MATCH [src] | n/a | strong (`shrine_official`) | `縁結び・厄除け・交通安全` | (1,縁結び)(16,厄除け)(10,交通安全) | 厄除け=PASS; 縁結び=HOLD/UNSUPPORTED; 交通安全=HOLD/UNSUPPORTED | **BLOCKED (§16)** | **REVIEW_REQUIRED** | `TAG_DRIFT` (PK space), `PROVENANCE_WEAK` (2/3 tags unbacked on checked source) | re-review 縁結び/交通安全 against full official source set; do not drop yet | Pilot #1 | yes |
| P2 | 品川神社 | id 50 | NOT VERIFIED | present; NOT VERIFIED | present (3d/3h) | REVIEW_REQUIRED | REVIEW_REQUIRED | n/a | strong (multi `shrine_official`) | `開運・金運` | (18,開運)(36,金運) | UNKNOWN (not fetched) | **BLOCKED (§16)** | **REVIEW_REQUIRED** | `TAG_DRIFT` | fetch official source; run Evidence Review | Pilot #2 | yes |
| P3 | 太宰府天満宮 | id 6 | NOT VERIFIED | present; NOT VERIFIED | present | MATCH [src] | MATCH [src] | ox-cart legend noted | strong (`shrine_official`) | `学業成就・合格祈願・厄除け` | (3,学業成就)(4,合格祈願)(16,厄除け) | 学業成就/合格祈願/厄除け = **PASS ×3** | **BROKEN in this DB** — tags `[3,4,16]` miss `study={9,10}`, spuriously hit `money`/`family` (§16.1) | **REVIEW_REQUIRED** | `TAG_DRIFT` (severe) | do **not** touch tags; resolve canonical `GoriyakuTag` table first | Pilot pool | yes |
| P4 | 伊勢神宮（内宮） | id 3 | NOT VERIFIED | present; NOT VERIFIED | **present now** (1d/1h) | REVIEW_REQUIRED | REVIEW_REQUIRED (`tradition`) | tradition-type; wording check needed | `shrine_official` recorded | `開運・厄除け・家内安全` | (16,厄除け)(9,家内安全)(18,開運) | UNKNOWN | **BLOCKED (§16)** | **REVIEW_REQUIRED** | `KNOWLEDGE_DRIFT` (prior "Zero-Knowledge" now stale), `TAG_DRIFT` | fetch source; verify tradition wording is non-assertive | `recommendation-readiness.md` (Zero-Knowledge — stale) | yes |
| P5 | 阿佐ヶ谷神明宮 | id 29 | NOT VERIFIED | present; NOT VERIFIED | present (3d/0h) | REVIEW_REQUIRED; **CONFIDENCE_MIXED** | MISSING (0 history) | n/a | mixed: 1 `shrine_official` + 2 `secondary_editorial` | `厄除け・八難除・縁結び` | (28,八難除)(16,厄除け)(1,縁結び) | UNKNOWN | **BLOCKED (§16)** | **REVIEW_REQUIRED** | `PROVENANCE_WEAK` (secondaries), `TAG_DRIFT` | none in PR-B; `FULL_SUPPRESSION` already governs Reason | `mixed-confidence-policy-decision.md` | yes |
| P6 | 給田六所神社 | id 22 | NOT VERIFIED | present; NOT VERIFIED | present (2d/4h) | REVIEW_REQUIRED | REVIEW_REQUIRED | founding-lineage phrasing | **no `shrine_official`** (`secondary_editorial` + `local_history`), all `medium` | prose sentence | (14,地域安泰)(9,家内安全) | 地域安泰 is UNWIRED (§16.3); prose ≠ benefit statement | **UNSUPPORTED** | `PROVENANCE_WEAK`, `TAG_DRIFT`, `DB_DRIFT` (goriyaku stored as prose) | seek an official source; re-derive tags from an explicit benefit statement or set to none | Pilot #5 (`給田六所`) | yes |
| P7 | 護王神社 | id 99 | NOT VERIFIED | present; NOT VERIFIED | present (4d/2h) | MATCH (provisional) | MATCH (provisional; faithful uncertainty) | n/a | strong (`shrine_official`) | `足腰健康・厄除け・勝運` | (45,足腰健康)(16,厄除け)(20,勝運) | `足腰健康` UNWIRED by name (§16.3); rest BLOCKED (§16.1) | **REVIEW_REQUIRED** | `TAG_DRIFT` | fetch source to confirm PASS for 足腰健康/厄除け/勝運; note 足腰健康 has no Purpose route | negative-pilot pool / niche | yes |
| P8 | 長太稲荷神社 | id 21 | NOT VERIFIED | present; NOT VERIFIED | **absent** | MISSING | MISSING | n/a | none | *(empty)* | *(none)* | none | n/a | **MISSING** | `KNOWLEDGE_DRIFT` (no facts), historical-duplicate context | Fact generation track; identity check vs Production 21/103 pair | `shrine-dataset-integrity.md`, negative-pilot | yes |

## 18. Aggregate pilot findings

Pilot n = 8 real shrine identities. **Not extrapolated to the full set** — this is a method-validation sample.

| Dimension | Result |
|---|---|
| Identity match rate (Spreadsheet↔DB) | **0 / 8 verifiable** — `CODEX_SESSION_SPREADSHEET_ACCESS = BLOCKED` |
| Location match rate | **0 / 8 verifiable** — coordinates present in DB for 7/8, correctness needs Spreadsheet `reference_*` columns |
| Knowledge Fact: `MATCH` | 4 fact-groups fully source-checked this session (P1 deity+history, P3 deity+history) |
| Knowledge Fact: `REVIEW_REQUIRED` | P2, P4, P5, P6, P7 (source not re-fetched) |
| Knowledge Fact: `MISSING` | P8 (Zero-Knowledge); P5 has 0 history |
| Source provenance quality | strong (`shrine_official`): P1, P2, P3, P4, P7 · mixed: P5 · **weak (no official)**: P6 · none: P8 |
| GoriyakuTag: `MATCH` | P3 (3/3 PASS by name) |
| GoriyakuTag: `UNSUPPORTED` (on checked source) | P1 (縁結び, 交通安全); P6 (prose) |
| GoriyakuTag: `REVIEW_REQUIRED` | P2, P4, P5, P7 (source not fetched) |
| `LEGACY_EXISTING_WITHOUT_PROVENANCE` | **5 / 8** (P1, P2, P4, P5, P7) |
| Recommendation Evidence PASS / HOLD / NO_EVIDENCE / REVISE | PASS = 4 label-items (P3 ×3, P1 厄除け) · HOLD = 3 (P1 ×2, P6) · NO_EVIDENCE = 1 shrine (P8) · REVISE = 0 · remaining = UNKNOWN (not fetched) |
| Purpose-wired PASS evidence count | **0 confirmed** — every PASS is blocked by the §16 `GoriyakuTag` PK drift; 太宰府's 3 PASS labels do not reach `study` in this DB |
| Needs represented (by intended tag names in the pilot) | study, money-ish (開運/金運), family-ish (厄除け), protection (厄除け), courage (勝運/開運), health (足腰健康 — UNWIRED), relationship/love (縁結び), travel (交通安全) |

## 19. Method problems / revisions

| # | Problem found | Required revision for PR-C |
|---|---|---|
| M1 | **`GoriyakuTag` PK space is ambiguous** — the audit substrate (this dev DB) has a 46-row table whose PKs do not match `NEED_TO_GORIYAKU_IDS`'s canonical-master numbering (§16). Purpose connectivity is un-auditable. | PR-C must run against a DB whose `GoriyakuTag` table **is** the canonical 39-row master (Production, or a Production dump). The matrix needs a new column `goriyaku_tag_master_alignment ∈ {ALIGNED, PK_DRIFT, UNKNOWN}` computed by comparing every `GoriyakuTag.name` to the canonical §5 list and checking PK == canonical id. Mother Ship decision needed on the canonical `GoriyakuTag` table (§20). |
| M2 | **No Spreadsheet access in-session** — the entire identity/location dimension is `NOT VERIFIED`. | PR-C gated on a Mother-Ship-supplied read-only Spreadsheet CSV/snapshot (§6). Identity join method itself (compare name/official_name/address/coords/canonical_status) is defined and ready; it just needs the data. |
| M3 | **No Production read** — canonical shrine set + duplicate state + Production knowledge extent all `NOT VERIFIED`; dev DB disagrees with `[prior]` Production on rows and duplicates. | PR-C gated on a read-only Production DB path or an authorized dump. `FULL_AUDIT_DENOMINATOR` decision (§9, §20). |
| M4 | **Prior-audit-vs-current-DB drift** — Batch-17 shrines (建部大社 / 北海道神宮 / 波上宮) absent from this dev DB; 伊勢神宮（内宮） no longer Zero-Knowledge. Historical audit results cannot be assumed to describe the audited DB. | Matrix already carries `prior_audit_refs` + `revalidation_required`. PR-C must re-observe every cited shrine's current state before reusing a `[prior]` verdict; add an explicit `prior_result_still_holds ∈ {YES, NO, N/A}` column. |
| M5 | **`goriyaku` stored as prose** (P6) breaks the `backfill_goriyaku_tags` delimiter assumption. | Add matrix flag `goriyaku_text_shape ∈ {DELIMITED_LABELS, PROSE, EMPTY}`; PROSE rows are automatically `REVIEW_REQUIRED` for tag provenance. |
| M6 | `decide_fact_usability` is keyword-only (`verification_status`, `confidence`, `source_verification_statuses`) — an audit helper must build the source-status list from the M2M, not call positionally. | Documented here; PR-C uses the keyword form (as this pilot did after correction). No production helper added. |

The identity/knowledge/source/goriyaku **method mechanics worked end-to-end** for the shrines where data was available (P1, P3 fully; P6/P7 partially) — the blockers are data access and the `GoriyakuTag` table, not the matrix design.

## 20. Mother Ship decisions

1. **`FULL_AUDIT_DENOMINATOR`** — hold or set (100 / ~102 / 105 / other). Blocked on a Production read (§9, M3).
2. **Canonical `GoriyakuTag` table** — is Production's `GoriyakuTag` the clean 39-row master (ids 1–39), or does it carry the same 46-row legacy+master mix as this dev DB (§16)? If the latter, `NEED_TO_GORIYAKU_IDS` is mis-wired in Production and that is a separate, higher-priority track than this data audit. **PR-C cannot audit Purpose connectivity until this is answered.**
3. **Production DB read path** for PR-B/PR-C (read-only credential bridge or authorized dump).
4. **Spreadsheet access** — supply a read-only CSV/snapshot with the §6 columns.
5. **Duplicate real-shrine rows** (長太稲荷神社, 給田六所神社, 富岡八幡宮) — confirm current Production state; decide merge / keep-both-with-canonical-flag / defer. (No PR-B action.)
6. **`LEGACY_EXISTING_WITHOUT_PROVENANCE`** (5/8 in the pilot; likely ~most of the ~86 goriyaku-bearing shrines) — does PR-C retro-review provenance to the current Source standard, or record-and-accept per Evidence Review Contract §12?
7. **UNWIRED benefit tags** (`安産`, `子宝`, `足腰健康`, `航海安全`, `海上安全`, …) — is a Purpose-routing follow-up wanted, or recorded per shrine only? (Out of this audit's authority to change mappings.)
8. **`canonical_status` / `official_name` / `official_address`** — DB home (later PR) or audit-layer only? (Repeat of PR-A §15.7.)
9. **Audit-only labels** — accept `MATCH/PARTIAL/UNSUPPORTED/MISSING/REVIEW_REQUIRED` + the drift root-cause set for PR-C output; confirm they never enter product taxonomy.

## 21. PR-C specification

**Do not start.** Defined here only.

- **Name:** Shrine Evidence Full Integrity Audit.
- **Input set:** the confirmed `FULL_AUDIT_DENOMINATOR` (§20.1) — i.e. every real shrine identity in the canonical Production set, QA fixtures excluded via `shrine_qa_fixture_exclusion`.
- **Substrate requirements (hard gates):**
  1. Read-only Production DB or an authorized Production dump (M3).
  2. That DB's `GoriyakuTag` table verified `ALIGNED` to the canonical 39-row master, or an explicit Mother Ship ruling on §20.2. If `PK_DRIFT`, **stop and escalate** — do not audit Purpose connectivity on a drifted table.
  3. A read-only Google Spreadsheet CSV/snapshot with the §6 columns (M2).
- **Source requirements:** official shrine site → official jinja organisation → government / cultural-property → other contract-permitted types. Wikipedia/tourism only when no official source exists. No deity/history/reputation/AI → benefit inference.
- **Batching:** by prefecture (derived from `address`), ~10–15 shrines per batch; each batch its own section in the output doc, committed incrementally; identity/location dimension first (fast, spreadsheet-join), then knowledge/source/goriyaku (slow, per-shrine fetch).
- **Output document(s):** `docs/audit/shrine-evidence-full-integrity-audit.md` (matrix + aggregate), plus one Evidence-Review provenance appendix per batch following `recommendation-evidence-review-contract.md` §6.
- **Verification checks per batch:** `knowledge_coverage_report` diff vs baseline (must be 0 — read-only); Evidence-Gate test suite; `git diff --check`; markdownlint; no production file touched.
- **STOP conditions:** any `GoriyakuTag` `PK_DRIFT` on the audited DB; any required production-code change discovered; Spreadsheet access lost mid-run; a Mother Ship decision from §20 still pending for that dimension. On STOP: record and escalate, never fix in PR-C.

## 22. Final verdict

**`PILOT_BLOCKED_ON_CANONICAL_SET`**

Three canonical prerequisites are unmet this session and each independently blocks a required phase:

1. **`CANONICAL_REAL_SHRINE_SET = NOT VERIFIED`** — no Production read (§7). Phase 1 / denominator (§9) held.
2. **Canonical `GoriyakuTag` table not established** — the local dev DB's 46-row `GoriyakuTag` PK space does not match the canonical-master numbering `NEED_TO_GORIYAKU_IDS` assumes (§16). Phase 10 (Purpose connectivity) is un-auditable; 太宰府天満宮's 3 valid PASS labels do not reach `study` in this DB.
3. **`CODEX_SESSION_SPREADSHEET_ACCESS = BLOCKED`** — no identity/location join (§11). Phase 5 held.

The **matrix and method for the knowledge / source / goriyaku layers are validated** — they ran end-to-end for the shrines with available data (P1, P3 fully; P6, P7 partially), producing concrete `MATCH` / `UNSUPPORTED` / `HOLD` / `MISSING` results and a `LEGACY_EXISTING_WITHOUT_PROVENANCE = 5/8` finding. PR-C is specified (§21) and can proceed once §20's decisions 1–4 land. No blocker was found in the Recommendation Engine contracts themselves; the `GoriyakuTag` PK drift is a **data / seed integrity** issue whose Production reach is unknown and is escalated as §20.2.

**No Production DB, no Spreadsheet, no Recommendation Engine config, no Knowledge data, no GoriyakuTag, no `Shrine.goriyaku`, no Need mapping, no fixture/seed/model/migration, and no frontend was changed by this task.** This branch adds one file: `docs/audit/shrine-evidence-integrity-pilot.md`.
