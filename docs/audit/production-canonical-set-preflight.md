# Production Canonical Set Preflight

## 1. Audit metadata

| Field | Value |
|---|---|
| Task | Production Canonical Set Preflight — resolves the canonical-data gates from PR #2611 (`docs/audit/shrine-evidence-integrity-pilot.md`) before PR-C |
| Type | Preflight / audit. **Read-only.** No Production write, no Recommendation-mapping change, no GoriyakuTag normalization, no duplicate-row deletion, no Knowledge / fixture / seed / model / migration / frontend change. |
| Branch | `audit/production-canonical-set-preflight` |
| Worktree | `~/Developer/jinja_app-production-canonical-set-preflight` (isolated, from `origin/develop`; control repo untouched) |
| Date | 2026-08-29 |
| Production read | via the repo's sanctioned read-only path — `scripts/migration_safety/readonly_query.sh` + the repo-external credential file `~/.config/kami-musubi/production-db.env` (present on this host). The credential value was never printed, logged, or placed in argv; every query passed `guard.py check-readonly-sql` (SELECT/SHOW/EXPLAIN/WITH only). SQL files were kept in an untracked scratch dir. |

### Evidence labels

- **[prod]** — read this session directly from the Production database via the read-only credential bridge.
- **[repo]** — read from tracked source at the base SHA.
- **[MS]** — stated as verified by the Mother Ship in the task brief.
- **[prior]** — value from an earlier audit; context only, not current truth.

## 2. Base SHA

- **`origin/develop` @ `aa654474b6fff11ef716329a5dc9b28f63155bc5`** — fetched this session; matches the task's stated SHA; `origin/develop` had not advanced.
- Worktree HEAD = same SHA; working tree clean at checkout and at commit time.

## 3. Scope / non-scope

### In scope

Discover the supported read-only Production inspection path; verify the Production `GoriyakuTag` table against the canonical 39-row master; read the Production `Shrine` identity set; reconcile QA/test rows and confirmed duplicate rows; construct the unique-real-shrine-identity model; produce the `FULL_AUDIT_DENOMINATOR` decision packet; evaluate the PR-C entry gate; if `GoriyakuTag` is drifted, produce a remediation *decision packet* (not an implementation).

### Non-scope (enforced)

Starting PR-C · remediating any Production data · normalizing `GoriyakuTag` rows · deleting duplicate `Shrine` rows · changing Recommendation mappings · editing the Google Spreadsheet · a fresh coordinate audit · adding a Production endpoint · modifying deployment config · the full backend suite. The only file this task adds is this document.

## 4. Existing contract / code authority

Re-read at the base SHA. **Current code / tests are physical truth; `docs/audit/*` are point-in-time records** (per `docs/README.md` governance, reaffirmed in PR-A/PR-B).

| Concern | Authority [repo] |
|---|---|
| Canonical `GoriyakuTag` master | 39 rows, ids 1–39, names per `docs/knowledge/recommendation-evidence-review-contract.md` §5; pinned by `backend/temples/tests/test_need_to_goriyaku_tag_ids.py` (`CANONICAL_MASTER_ID_RANGE = range(1, 40)`) |
| Need → GID mapping | `backend/temples/domain/need_to_goriyaku_tag_ids.py` `NEED_TO_GORIYAKU_IDS` — `communication = set()`, `family = {16, 35}`, `mental = {11, 26, 28, 38}`, `travel_safe = {3, 13, 14}`, `career ∩ courage = {12, 30}` [repo] |
| Real-vs-QA shrine set | `backend/temples/services/shrine_qa_fixture_exclusion.py` `exclude_qa_fixture_shrines()` — name-convention only (`テスト%`, `test%`, `%承認テスト%`, `%検証%`, and a fixed noisy-name list); **no id hard-coding**, **no non-shrine-name filter** |
| goriyaku text → tag M2M | `backend/temples/management/commands/backfill_goriyaku_tags.py` `parse_goriyaku()` — `GoriyakuTag.objects.get_or_create(name=…)`, name-based |
| Coverage aggregation | `backend/temples/services/knowledge_coverage_report.py` — delegates QA exclusion, fact usability, fact selection to their owners; read-only |
| Production read-only tooling | `scripts/migration_safety/{readonly_query.sh,guard.py,check_credential_presence.sh}` + `README.md` "Credential Bridge" |
| Duplicate structural context | `docs/audit/shrine-dataset-integrity.md` `[prior]` — partial unique constraint `condition=Q(place_ref__isnull=True)` does **not** prevent a `place_ref`-set row duplicating a `place_ref`-NULL row |

## 5. Production read-path investigation

Candidate paths considered against current repo/config evidence:

| Path | Evidence | Verdict |
|---|---|---|
| A. authenticated Production API exposing all identity fields | no such endpoint found; `docs/ops/production-bff-hardening.md` describes a hardened BFF, not a data-dump API | not used |
| B. **authorized DB connection from an existing configured client** | `scripts/migration_safety/README.md` "Credential Bridge"; `readonly_query.sh` (SELECT-only allow-list, credential parsed to `PG*` env, never in argv); credential file `~/.config/kami-musubi/production-db.env` **present on this host** (`check_credential_presence.sh` → `VAR_SET=1`, `scheme_is_postgres=True`, `has_host/has_port/has_dbname/has_userinfo=True`; value not read) | **USED** |
| C. authorized dump / export | `dump_readonly.sh` exists but produces a full logical dump; not needed for the aggregate/identity questions here, and dumps must never be committed | not used |
| D. existing management/report endpoint | `knowledge_coverage_report` is read-only but runs against `DATABASE_URL` of the invoking env (local), not Production | not used for Production |
| E. CI/deployment artifact | none found containing Production row data | n/a |
| F. Render shell | free-tier; not assumed to exist; not attempted | n/a |

**`PRODUCTION_READ_PATH = DIRECT_DB`** (read-only credential bridge, path B).

Queries executed this session (all SELECT-only, all passed `guard.py`):
`temples_goriyakutag` full table + count; `temples_shrine` aggregate counts + kind breakdown; exact-name duplicate groups; QA-name-pattern rows; duplicate-group detail (address / coords / `place_ref_id` / tag & knowledge counts); rows `id ≥ 95`; all `place_ref`-set rows; id 102 / 105 detail. No `INSERT`/`UPDATE`/`DELETE`/DDL/`EXPLAIN ANALYZE` was issued or attempted.

## 6. Spreadsheet authenticated-read state

| Term | State |
|---|---|
| `PROJECT_SPREADSHEET_READ_PATH` | **VERIFIED** [MS] — the Mother Ship has an authenticated Google Drive / Sheets connection to "神社のDB" (sheet `シート1`), and has directly verified authenticated read works. Known columns include `id, name_jp, address, latitude, longitude, place_ref_id, canonical_status, official_name, official_address, official_source_type, official_source_url, verified_at, reference_latitude, reference_longitude, coordinate_delta_m, coordinate_status, notes, google_place_id, position_source_type, position_source_url, position_source_note`. |
| `MOTHER_SHIP_AUTHENTICATED_SPREADSHEET_READ` | **VERIFIED** [MS] |
| `CODEX_SESSION_SPREADSHEET_ACCESS` | **BLOCKED** — Codex direct HTTP to the sheet returned 401 in PR-A/PR-B; **not re-attempted here** (task: "Do not retry random unauthenticated scraping"). This is a session limitation only. |

**No Spreadsheet cell values are used or invented in this document.** Spreadsheet responsibility is unchanged from PR-A/PR-B: Identity / Location **audit reference**; **not** semantic truth for deity / history / tradition / goriyaku / Recommendation Evidence.

### Required PR-C handoff — DB↔Spreadsheet identity join keys (fallback order)

1. **verified same `id` + at least one corroborating identity field** (name or address or coordinates) — `id` equality **alone does not prove identity**.
2. `official_name` ↔ `name_jp` (normalized).
3. `official_address` ↔ `address` (normalized; format-insensitive — see §10, 富岡八幡宮).
4. coordinates within the Spreadsheet's own `coordinate_delta_m` tolerance / matching `google_place_id`.
5. anything unresolved after 1–4 → `IDENTITY_REVIEW_REQUIRED` (human).

## 7. Production GoriyakuTag master

**Full `temples_goriyakutag` table, read [prod] this session:**

| id | name | id | name | id | name |
|---|---|---|---|---|---|
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
| 13 | 航海安全 | 26 | 家庭円満 | 39 | 農業守護 |

Row-by-row against the canonical master (`recommendation-evidence-review-contract.md` §5, id = list position):

| Metric | Value |
|---|---|
| `PRODUCTION_GORIYAKU_ROW_COUNT` | **39** ([prod] `count(*)`, `min(id)=1`, `max(id)=39`) |
| `EXPECTED_CANONICAL_ROW_COUNT` | 39 |
| `ALIGNED_COUNT` | **39 / 39** — every `production_id` → `production_name` equals the `expected_canonical_name` |
| `NAME_MISMATCH_COUNT` | **0** |
| `MISSING_COUNT` | **0** |
| `EXTRA_COUNT` | **0** |
| `PK_DRIFT` rows | **0** |

**`PRODUCTION_GORIYAKU_MASTER = ALIGNED`.**

Consequently `NEED_TO_GORIYAKU_IDS` [repo] resolves correctly against Production: `family = {16, 35}` → 安産 + 子宝; `study = {9, 10}` → 学業成就 + 合格祈願; `travel_safe = {3, 13, 14}` → 交通安全 + 航海安全 + 海上安全; `communication = set()` (EVIDENCE_LIMITED). The Phase 2 critical-rule condition ("if ANY canonical id maps to the wrong name, stop") is **not triggered** — Production is clean, no escalation, no remediation packet needed (§14).

### DEV_DB_PK_DRIFT_SCOPE

PR #2611 found a **46-row** `GoriyakuTag` table in the local dev DB (`jinja_db`) with ids 1–15 = a legacy taxonomy and ids 16–46 = the canonical master renumbered from 16, causing e.g. `family = {16, 35}` to resolve to 厄除け / 出世運 locally and 太宰府天満宮 to miss `study`. **That is now confirmed `LOCAL_DEV_ONLY`.**

**`DEV_DB_PK_DRIFT_SCOPE = LOCAL_DEV_ONLY_CONFIRMED`** — Production is the clean 39-row master; the local dev DB is a drifted, non-canonical substrate. This is a **de-escalation** of PR #2611 §20.2. Local-dev reproducibility fix is a separate future recommendation (§15.6); **not done here** (the local dev DB is not modified by this task).

## 8. Production Shrine set

**[prod], read-only, 2026-08-29:**

| Metric | Value |
|---|---|
| `RAW_PRODUCTION_SHRINE_ROWS` | **108** (ids 1–108, contiguous; `min_id=1`, `max_id=108`) |
| `kind` breakdown | `shrine` = 108, `temple` = 0 |
| rows with latitude AND longitude | 107 / 108 (the one without: id 102, a QA row) |
| rows with `place_ref_id` set | **4** — ids `{101, 103, 104, 105}` |

**Tail rows (id ≥ 95) [prod]** — where the non-standard rows sit:

| id | name_jp | address | has place_ref | note |
|---|---|---|---|---|
| 95–100 | 忌宮神社 / 高良大社 / 寳登山神社 / 枚岡神社 / 護王神社 / 阿蘇神社 | (real addresses) | no | real shrines |
| **101** | 給田六所神社 | 〒157-0064 東京都世田谷区給田１丁目３−７ | **yes** | duplicate shadow of id 22 |
| **102** | テスト確認神社 20260611 | 東京テスト | no | **QA/test row** (0 lat/lng, 0 tags, 0 knowledge, empty goriyaku/sajin) |
| **103** | 長太稲荷神社 | 〒157-0065 東京都世田谷区上祖師谷１丁目３−１０ | **yes** | confirmed duplicate shadow of id 21 (§10) |
| **104** | 富岡八幡宮 | 〒135-0047 東京都江東区富岡１丁目２０−３ | **yes** | **candidate** shadow of id 49 — identity `AMBIGUOUS_PENDING_IDENTITY_CONFIRMATION` (§10) |
| **105** | 広島市 | 日本、広島県広島市 | **yes** | **NON-SHRINE** — coords (34.3853, 132.4553) = Hiroshima City centre; `google_place_id` for the city; 0 tags, 0 deity, 0 history, empty goriyaku/sajin. A geocoding artifact, not a shrine. |
| **106** | 北海道神宮 | 北海道札幌市中央区宮ヶ丘474 | no | real shrine (Batch 17) |
| **107** | 建部大社 | 滋賀県大津市神領1-16-1 | no | real shrine (Batch 17) |
| **108** | 波上宮 | 沖縄県那覇市若狭1-25-11 | no | real shrine (Batch 17) |

**Note — PR #2611 correction:** 建部大社 / 北海道神宮 / 波上宮 **do exist in Production** (ids 106–108). PR #2611 rejected them from the pilot only because they were absent from the *local dev DB*; that was a dev-DB staleness artifact, not a canonical-set fact.

**Delta vs `[prior]`:** `shrine-dataset-integrity.md` recorded Production = 105 rows. Now 108 = the same 105 (real 100 + rows 101–105) **plus 3 Batch-17 imports** (106–108). Consistent with `knowledge-batch17-production-import.md`.

## 9. QA fixture reconciliation

Applying `shrine_qa_fixture_exclusion.exclude_qa_fixture_shrines` **conceptually** [repo] (name-convention: `テスト%`, `test%`, `%承認テスト%`, `%検証%`, noisy-name list):

| Row matched by the rule | id | name_jp | Disposition |
|---|---|---|---|
| `name_jp LIKE 'テスト%'` | **102** | テスト確認神社 20260611 | **QA fixture — excluded** |

`QA_FIXTURE_ROWS = 1` (id 102). **This is the only row the current repo function removes from Production.**

### QA-exclusion gap (new finding)

**Id 105 `広島市` is a non-shrine identity row that `shrine_qa_fixture_exclusion` does NOT catch** — its name contains no `テスト` / `検証` / `test` / noisy token, so the name-convention rule passes it through as if it were a real shrine. It is a Google-Places geocoding artifact (a city). This is not a QA fixture and not a real shrine; it needs its own disposition (§15.3) and, separately, the exclusion function may warrant a non-shrine-artifact guard (§15.5, out of this task's scope).

The local dev DB's QA fixtures (`承認テスト神社`, `admin承認テスト神社`, `重複検証神社`×3 at ids 101–105) are **NOT present in Production** — those are local-dev-only rows. Production's ids 101/103 are confirmed duplicate shadows, 104 is a candidate shadow (identity pending, §10), and 102/105 are the test/artifact rows above.

> **Spreadsheet row-id ≠ Production row-id.** The Mother Ship's authenticated Spreadsheet inspection [MS] confirms Spreadsheet **id 104 is a QA fixture named `重複検証神社`**, *not* the Production shadow row. Spreadsheet row-id equality therefore **cannot** be used to validate any Production identity claim; the join must use the §6 fallback order (name / official_name / address / coordinates / Google Place identity), never id alone.

## 10. Duplicate real-shrine reconciliation

Exact-name duplicate groups in Production [prod] — **all three historical candidates, and no others**:

| Group | ids | address | coords | place_ref | tags / deity / history | Classification |
|---|---|---|---|---|---|---|
| **長太稲荷神社** | 21 | 〒157-0065 …上祖師谷１丁目３−１０ | 35.660614 / 139.6017688 | — | 2 / 0 / 0 | primary |
| | 103 | *(identical)* | *(identical)* | `ChIJX19mq8nxGGARsA2kP4gX90M` | 0 / 0 / 0 | shadow → **`SAME_REAL_SHRINE_DUPLICATE`** |
| **給田六所神社** | 22 | 〒157-0064 …給田１丁目３−７ | 35.662443 / 139.5920237 | — | 1 / 2 / 4 | primary (holds all knowledge) |
| | 101 | *(identical)* | *(identical)* | `ChIJl-MEepfxGGAR1Eo44p__GaE` | 0 / 0 / 0 | shadow → **`SAME_REAL_SHRINE_DUPLICATE`** |
| **富岡八幡宮** | 49 | 東京都江東区富岡1-20-3 | 35.6733 / 139.7967 | — | 2 / 1 / 2 | primary |
| | 104 | 〒135-0047 東京都江東区富岡１丁目２０−３ | 35.6717809 / 139.799519 | `ChIJK11I4BGJGGAR5mZswigcu58` (PlaceRef `name = 富岡八幡宮`) | 0 / 0 / 0 | candidate shadow → **`AMBIGUOUS_PENDING_IDENTITY_CONFIRMATION`** |

- **長太稲荷 {21, 103} / 給田六所 {22, 101}: `SAME_REAL_SHRINE_DUPLICATE` — CONFIRMED.** address and coordinates **byte-identical** between the pair; the shadow row's `place_ref` PlaceRef carries the *same* name and *same* address as the primary; shadow row has zero tags / zero knowledge; created within the same window. Two independent identity signals agree → confirmed.
- **富岡八幡宮 {49, 104}: `AMBIGUOUS_PENDING_IDENTITY_CONFIRMATION`.** The evidence is *suggestive but not conclusive*, and per the Mother Ship's ruling, **same name is not proof**:
  - *For SAME:* id 49's manual address (`…富岡1-20-3`) and id 104's PlaceRef address (`…富岡１丁目２０−３`) resolve to the **same street lot, 江東区富岡 1-20-3**; the PlaceRef row is itself named `富岡八幡宮`; id 104 was created 2026-06-12, one day after id 49 (2026-06-11) and follows the identical zero-data `place_ref`-shadow pattern as the two confirmed pairs.
  - *Against / unresolved:* coordinates are **~300 m apart** (unlike the two confirmed pairs, which are byte-identical); the designated Identity/Location audit reference — the Google Spreadsheet — has **no populated `reference_latitude` / `reference_longitude` / `coordinate_delta_m` / `coordinate_status`** for its row id 49 [MS], so the requested coordinate confirmation **cannot be performed from the current audit columns**; and Spreadsheet id 104 is an unrelated QA fixture (`重複検証神社`), so no Spreadsheet-side row corresponds to the Production shadow.
  - **No stronger *independent* current read-only evidence is available in this task.** The address-lot match plus PlaceRef self-name is the strongest obtainable here and is not sufficient to override the Mother Ship's conservative stance. → held as `AMBIGUOUS_PENDING_IDENTITY_CONFIRMATION`.
- **No rows deleted or merged.** Every DB row is preserved. For each *confirmed* pair the audit unit (PR-C) is the **data-bearing primary id** (21, 22), with the shadow id kept in the evidence table (per PR #2611 §8). For 富岡, both rows (49, 104) enter PR-C as a `REVIEW_REQUIRED` identity pair until confirmed.

| Term | Value |
|---|---|
| `CONFIRMED_DUPLICATE_EXTRA_ROWS` | **2** (shadow rows 101, 103) |
| `AMBIGUOUS_DUPLICATE_EXTRA_ROWS` | **1** (shadow row 104 — 富岡八幡宮) |

## 11. Canonical real-shrine identity set

| Term | Value | Derivation |
|---|---|---|
| `RAW_PRODUCTION_SHRINE_ROWS` | **108** | [prod] |
| `QA_FIXTURE_ROWS` | **1** | id 102 (§9) |
| `POST_QA_PRODUCTION_ROWS` | **107** | 108 − 1 (what the current repo QA function removes). **Still includes id 105 `広島市`**, which is not a real shrine — so this is *not* "real shrine rows" without qualification. |
| `NON_SHRINE_ARTIFACT_ROWS` | **1** | id 105 `広島市` (§9 gap) — a Google-Places geocode artifact, not a shrine and not a QA fixture |
| `CONFIRMED_DUPLICATE_EXTRA_ROWS` | **2** | shadow rows 101, 103 (§10 — both byte-identical to their primary, two independent identity signals) |
| `AMBIGUOUS_DUPLICATE_EXTRA_ROWS` | **1** | shadow row 104 (§10 — 富岡八幡宮; `AMBIGUOUS_PENDING_IDENTITY_CONFIRMATION`) |
| `UNIQUE_REAL_SHRINE_IDENTITIES` | **103 if 富岡 {49,104} is SAME · 104 if DISTINCT** | 107 − 1 (非-shrine 105) − 2 (confirmed dup shadows) − (1 if 富岡 SAME, else 0) |

The two confirmed duplicate pairs are **fully supported** (§10: byte-identical address+coords + PlaceRef self-name agreement). The non-shrine row (id 105) is unambiguous. **富岡八幡宮 {49,104} is not resolvable from current read-only evidence** (§10) — its ~300 m coordinate delta and the absence of Spreadsheet coordinate-audit values for row 49 leave it `AMBIGUOUS_PENDING_IDENTITY_CONFIRMATION`. Therefore `UNIQUE_REAL_SHRINE_IDENTITIES` has a **candidate range of 103–104**, not a single finalized value.

## 12. FULL_AUDIT_DENOMINATOR packet

Definition: *number of unique real shrine identities that must undergo the full Evidence Integrity audit.*

| Field | Value |
|---|---|
| `RAW_PRODUCTION_SHRINE_ROWS` | 108 |
| `QA_FIXTURE_ROWS` | 1 |
| `NON_SHRINE_ARTIFACT_ROWS` | 1 (id 105 `広島市`) |
| `POST_QA_PRODUCTION_ROWS` | 107 (108 − QA; still contains the non-shrine row) |
| `CONFIRMED_DUPLICATE_EXTRA_ROWS` | 2 (shadow rows 101, 103) |
| `AMBIGUOUS_DUPLICATE_EXTRA_ROWS` | 1 (shadow row 104 — 富岡八幡宮) |
| `UNIQUE_REAL_SHRINE_IDENTITIES` | **103** if 富岡 {49,104} is SAME · **104** if DISTINCT |

**`FULL_AUDIT_DENOMINATOR = MOTHER_SHIP_DECISION_PENDING`** — candidate range **103–104**, pending 富岡八幡宮 {49,104} identity confirmation (§10).

This is computed from a direct read-only Production read (not inferred from the historical 100 / 102 / 105 figures). It is **not** finalized at 103: the 富岡 identity question is unresolved, and the disposition of the QA row (102), the non-shrine row (105), and the confirmed/ambiguous duplicate shadow rows (101, 103, 104) still needs a Mother Ship ruling (§15). Whatever the disposition of those anomalous rows, the *real shrine identity* count is **103 or 104**, decided solely by 富岡.

## 13. PR-C entry gate

| # | Condition | State | Evidence |
|---|---|---|---|
| 1 | Production Shrine set verified | **GREEN** | §8 — 108 rows read, all identity fields, classified |
| 2 | Production GoriyakuTag master state verified | **GREEN** | §7 — 39 rows, ids 1–39, `ALIGNED`, 0 mismatch |
| 3 | Spreadsheet authenticated read path available | **GREEN (project)** | §6 — `MOTHER_SHIP_AUTHENTICATED_SPREADSHEET_READ = VERIFIED`. PR-C must actually receive the snapshot; Codex session path stays `BLOCKED`. |
| 4 | `FULL_AUDIT_DENOMINATOR` determinable or MS-approved | **RED** | §12 — **not finalized.** `MOTHER_SHIP_DECISION_PENDING`, candidate range 103–104. Blocked on (a) 富岡八幡宮 {49,104} identity confirmation and (b) final denominator sign-off. |
| 5 | No unresolved Production `GoriyakuTag` `PK_DRIFT` | **GREEN** | §7 — Production `ALIGNED`; the PR #2611 drift is `LOCAL_DEV_ONLY_CONFIRMED` |

**`PR_C_ENTRY_GATE = BLOCKED_ON_DENOMINATOR_DECISION`**

Technical gates 1, 2, 3, 5 are GREEN. Gate 4 is **RED** — the denominator is **not** technically finalized. Two things must resolve before PR-C locks its input set:

- **富岡八幡宮 {49,104} identity confirmation** — resolve `AMBIGUOUS_PENDING_IDENTITY_CONFIRMATION` (§10) to `SAME` or `DISTINCT`. This alone sets `UNIQUE_REAL_SHRINE_IDENTITIES` to 103 or 104. Current read-only sources cannot settle it (no Spreadsheet coordinate-audit values for row 49; Spreadsheet id 104 is an unrelated QA fixture); it needs a Mother Ship / human identity ruling, ideally with a field-authoritative source (shrine official record, an updated Spreadsheet coordinate audit for row 49, or a manual on-map check).
- **Final denominator sign-off** — approve the resulting 103 or 104, and rule on the pre-audit disposition of the anomalous rows: QA row 102, non-shrine row 105 (`広島市`), and the duplicate shadow rows 101 / 103 (confirmed) / 104 (pending).

Until both land, PR-C stays blocked. All other technical prerequisites are satisfied.

## 14. Goriyaku remediation packet, if needed

**Not needed.** Production `temples_goriyakutag` is `ALIGNED` (§7): 39 rows, ids 1–39, every id → correct canonical name, 0 `NAME_MISMATCH` / `EXTRA_ROW` / `MISSING_ROW` / `PK_DRIFT`. Phase 8 does not apply. `NEED_TO_GORIYAKU_IDS` is correctly wired against Production. No data migration, no relation remapping, no pre-fix test work is required for Production.

(Phase 9 applies instead — see §7 `DEV_DB_PK_DRIFT_SCOPE = LOCAL_DEV_ONLY_CONFIRMED` and §15.6 for the local-dev-only follow-up.)

## 15. Mother Ship decisions

1. **富岡八幡宮 {49, 104} identity — REQUIRED, blocks the denominator.** Resolve `AMBIGUOUS_PENDING_IDENTITY_CONFIRMATION` (§10) to `SAME` or `DISTINCT`. Current read-only sources cannot settle it: the Spreadsheet's row id 49 has **no populated** `reference_latitude` / `reference_longitude` / `coordinate_delta_m` / `coordinate_status` [MS], and Spreadsheet id 104 is an unrelated QA fixture (`重複検証神社`), so no Spreadsheet row corresponds to the Production shadow. Needs a Mother Ship / human identity ruling (shrine official record, an updated row-49 coordinate audit, or a manual on-map check). This alone sets `UNIQUE_REAL_SHRINE_IDENTITIES` to **103 (SAME)** or **104 (DISTINCT)**.
2. **Final `FULL_AUDIT_DENOMINATOR` sign-off** (§12) — currently `MOTHER_SHIP_DECISION_PENDING`, candidate range **103–104**. Approve the value that follows from decision 1.
3. **Duplicate shadow rows** — 101 / 103 (confirmed shadows of 給田六所神社 / 長太稲荷神社, 0 tags & 0 knowledge) and 104 (candidate shadow of 富岡八幡宮): pre-audit cleanup (a separate, gated, isolated PR), or carried into PR-C's matrix as `REVIEW_REQUIRED` rows attached to their primary identity? **Do not delete in PR-C.**
4. **Non-shrine row id 105 `広島市`** (Hiroshima City geocode artifact, place_ref, 0 data) — pre-audit removal (separate gated PR), or carried as a `MISSING` / `REVIEW_REQUIRED` row? It is currently a real `temples_shrine` row that the QA-exclusion function passes through.
5. **`shrine_qa_fixture_exclusion` scope** — should it gain a guard for non-shrine geocode artifacts (city / prefecture / station names, or rows whose only identity signal is a `google_place_id` with no shrine-typed content)? Separate PR; **out of this task's scope**; noted because §9's gap will otherwise recur.
6. **Local dev DB `GoriyakuTag` reproducibility** — the local `jinja_db` carries the drifted 46-row table (§7). Approve a separate local-dev-only remediation / re-seed so future audits and pilots run on a canonical substrate. **Not a Production issue**; not done here.
7. **PR-C audit unit for a `SAME_REAL_SHRINE_DUPLICATE` pair** — confirm it is the data-bearing primary id (21 / 22, and 49 if 富岡 resolves to SAME), with the shadow id retained in the evidence table (PR #2611 §8 pattern).

## 16. Tests / verification

- Base SHA confirmed: `aa654474b6fff11ef716329a5dc9b28f63155bc5` = `origin/develop`.
- Isolated worktree confirmed; control repo untouched (`git status` in the control repo not run against it; this worktree is separate).
- **Read-only Production access** via `scripts/migration_safety/readonly_query.sh`; every SQL file passed `guard.py check-readonly-sql`; credential never exposed.
- **Test runs (this worktree, `--reuse-db`, run per file — `pytest.ini` `--maxfail=1` + `-p pytest_env` interferes with multi-file invocation):**

  | File | Result |
  |---|---|
  | `test_need_to_goriyaku_tag_ids.py` (Need mapping + `CANONICAL_MASTER_ID_RANGE`) | 19 passed |
  | `services/test_shrine_qa_fixture_exclusion.py` | 2 passed |
  | `services/test_knowledge_coverage_report.py` | 8 passed |
  | `test_knowledge_coverage_report_command.py` | 3 passed |
  | `services/test_evidence_gate.py` | 17 passed |
  | `test_backfill_goriyaku_tags_command.py` | 3 passed |
  | `test_gis_knowledge_seed_shrine_identity.py` | 1 passed |
  | `services/test_shrine_submission_duplicate_candidates.py` | 4 passed |
  | `services/test_concierge_chat_candidates_dedupe.py` | 5 passed |
  | `api/test_concierge_chat_dedupe.py` | 2 passed |
  | `test_family_gid_mapping_narrow.py` | 15 passed |
  | `test_communication_gid_evidence_disabled.py` | 13 passed |
  | `scripts/migration_safety/tests/test_guard.py` (credential bridge / read-only allow-list) | 47 passed |
  | **Total** | **139 passed, 0 failed** |

  (`test_shrine_duplicate_normalize.py` from an earlier task's list does not exist at this SHA — `test_shrine_submission_duplicate_candidates.py` is the current duplicate-candidate test.)
- **`git diff --check`: CLEAN.** No production code, config, fixture, seed, model, or migration changed. Only this doc is added.
- **markdownlint:** 0 issues (repo `.markdownlint.json`).

## 17. Final verdict

- **`PRODUCTION_READ_PATH = DIRECT_DB`** (sanctioned read-only credential bridge; credential never seen).
- **`PRODUCTION_GORIYAKU_MASTER = ALIGNED`** — 39 rows, ids 1–39, exact canonical master, 0 drift. The PR #2611 `PK_DRIFT` is **`LOCAL_DEV_ONLY_CONFIRMED`** (`DEV_DB_PK_DRIFT_SCOPE = LOCAL_DEV_ONLY_CONFIRMED`). No remediation packet needed for Production.
- **Production Shrine set = read and classified:** 108 raw rows → −1 QA row (id 102) → `POST_QA_PRODUCTION_ROWS = 107` → −1 **non-shrine artifact** (id 105 `広島市`) → −2 **confirmed** duplicate shadows (101, 103) → −(1 if 富岡 {49,104} is SAME) **candidate** shadow (104) → **`UNIQUE_REAL_SHRINE_IDENTITIES` = 103 (富岡 SAME) or 104 (富岡 DISTINCT)`**.
- **`FULL_AUDIT_DENOMINATOR = MOTHER_SHIP_DECISION_PENDING`**, candidate range **103–104** — **not** finalized at 103. The 富岡八幡宮 {49,104} identity question (`AMBIGUOUS_PENDING_IDENTITY_CONFIRMATION`, §10) is the sole determinant and cannot be settled from current read-only sources.
- **`PR_C_ENTRY_GATE = BLOCKED_ON_DENOMINATOR_DECISION`** — technical gates 1, 2, 3, 5 GREEN; gate 4 RED. PR-C is blocked specifically on **(a) 富岡八幡宮 identity confirmation** and **(b) final denominator sign-off** (plus the disposition of the anomalous rows 102 / 105 / 101 / 103 / 104). The denominator is **not** treated as technically finalized while (a) is open.
- New findings surfaced for Mother Ship: a non-shrine geocode-artifact row that the QA-exclusion function does not catch (id 105 `広島市`); zero-data `place_ref` duplicate shadow rows still present in Production (101, 103 confirmed; 104 pending); 富岡八幡宮 {49,104} is an unresolved identity pair; the local dev DB needs a canonical `GoriyakuTag` re-seed before it is used as an audit substrate again.
- Confirmed unchanged: Production `GoriyakuTag` = `ALIGNED` 39/39; `DEV_DB_PK_DRIFT_SCOPE = LOCAL_DEV_ONLY_CONFIRMED`; `PRODUCTION_READ_PATH = DIRECT_DB`; id 105 `広島市` non-shrine finding; **no Production remediation performed**.

**Explicit confirmation:** nothing was written to Production, the Google Spreadsheet, DB data, Recommendation configuration, Knowledge data, `GoriyakuTag` rows, `Shrine` rows, `Shrine.goriyaku`, Need mappings, fixtures, seeds, models, or migrations. All Production access was read-only via the repo's sanctioned credential bridge. The only change in this branch is the new file `docs/audit/production-canonical-set-preflight.md`.
