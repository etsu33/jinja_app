# Shrine Evidence Audit Readiness

## 1. Audit metadata

| Field | Value |
|---|---|
| Task | Shrine Evidence Audit Readiness (PR-A of the full-integrity-audit sequence) |
| Type | Audit / readiness / documentation only — **no** Shrine data, Knowledge data, GoriyakuTag, Recommendation Engine, fixture, seed, migration, model, or frontend change |
| Branch | `audit/shrine-evidence-audit-readiness` |
| Worktree | `~/Developer/jinja_app-shrine-evidence-audit-readiness` (isolated, created from the base SHA below; control repo untouched) |
| Date | 2026-08-29 |
| Author tooling | read-only Django ORM queries + `python manage.py knowledge_coverage_report` against the local dev DB; repository source read at the base SHA |

### Evidence-labelling convention

- **[repo]** — read directly from tracked source at the base SHA.
- **[dev-db]** — observed this session by read-only query against the **local
  development Postgres DB** (`jinja_db`). This is **not** Production and, per
  §8, is not identical to the tracked seed either. Every `[dev-db]` number is
  a point-in-time local observation and carries `REVALIDATION_REQUIRED`
  against Production for the real audit.
- **[prior]** — a value recorded by an earlier audit document; cited as
  historical context, **not** re-derived here and **not** asserted as current
  Production truth.
- **NOT VERIFIED** — could not be checked this session (e.g. the Google
  Spreadsheet returned HTTP 401; Production DB not accessed).

## 2. Base SHA

- **`origin/develop` @ `6443b84dcdead90128c51709ddc462e7a960f005`** — fetched
  this session; matches the task's stated post-#2609 SHA. `origin/develop`
  had **not** advanced.
- Worktree HEAD = same SHA, working tree clean at checkout.

## 3. Scope / non-scope

### In scope (this PR)

- Inventory of existing shrine / knowledge / fact-integrity / coverage /
  identity audit assets and their current status.
- Classification of each asset: ACTIVE_CONTRACT / CURRENT_TOOLING /
  HISTORICAL_AUDIT / ARCHIVE_REFERENCE / SUPERSEDED / UNCLEAR.
- Identification of the currently-authoritative contracts for shrine
  identity, location, deity, history, tradition, goriyaku, Knowledge Fact
  verification, provenance, Recommendation Evidence eligibility, Readiness,
  and Coverage.
- Google-Spreadsheet responsibility mapping (structure NOT VERIFIED — 401).
- Current DB shrine set (`[dev-db]`) and the DB ↔ Spreadsheet join design
  (join itself NOT executed — spreadsheet inaccessible).
- Existing verification-coverage summary and the remaining unverified
  surface.
- Proposed full-audit row schema, pilot selection (5–10 shrines), and the
  PR-A…PR-E sequence.
- Mother Ship decisions required; final readiness verdict.

### Out of scope (this PR, and enforced)

Shrine production data · Recommendation Engine behaviour · re-auditing all
105/100 shrines · source-by-source external research · DB writes · fixture /
seed / migration / model changes · GoriyakuTag changes · Knowledge data
changes · frontend · **any edit to the Google Spreadsheet** · Production
changes. The only file this PR adds is this document.

## 4. Existing audit asset inventory

`docs/README.md` and `docs/core/README.md` establish the repo's own
governance rule: **`docs/audit/*` holds "監査結果、過去判断、実装計画および
時点記録" (audit results, past decisions, implementation plans, point-in-time
records) and is explicitly NOT used for current-spec judgment** — active
contracts live in `docs/core/`, `docs/knowledge/`, `docs/product/`, plus
implementation code and tests. The inventory below applies that rule.

### 4.1 Active contract documents (authoritative for the full audit)

| Path | Status [repo] | Purpose | Reusable in 105/100-shrine audit? |
|---|---|---|---|
| `docs/knowledge/shrine-knowledge-contract.md` | **Active** (1359 lines) | Normative meaning/source/`verification_status`/`confidence`/Fact-usability/display/AI-generation/conflict rules for `deity`, `shrine_history`, tradition, `ShrineKnowledgeSource` | Yes — the semantic-fact contract the audit measures against |
| `docs/knowledge/recommendation-evidence-review-contract.md` | **Contract definition** (Active) | ELIGIBLE_EXPLICIT / REVIEW_REQUIRED / INELIGIBLE / UNKNOWN rules; PASS / HOLD / NO_EVIDENCE / REVISE review states; `Shrine.goriyaku` reviewed-write rules; provenance format; shrine-level RECOMMENDATION_READY / PARTIALLY_READY / NO_RECOMMENDATION_EVIDENCE / HOLD | Yes — the goriyaku/Recommendation-Evidence contract |
| `docs/knowledge/shrine-profile-spec.md` | Active (knowledge/README 正本) | Shrine knowledge model + recommendation-ready quality definition | Yes |
| `docs/knowledge/shrine-data-guide.md` | Active (knowledge/README 正本) | Data input / source / quality standards | Yes |
| `docs/core/recommendation-readiness.md` | **Active** — Governance Contract | 4-type Coverage taxonomy (**Schema / Populated / Verified / Usable**), Capability Set, Evidence-Gate boundary, 105-shrine Shadow Evaluation field list; explicitly **not** wired to runtime candidate exclusion | Yes — defines Coverage vocabulary + the shadow-eval metric list the full audit populates |
| `docs/core/recommendation-architecture.md` | **Active** | End-to-end Recommendation pipeline; per-stage authoritative data + handoff contract | Yes (context) |
| `docs/core/recommendation-reason-contract.md` | **Active** | Fact / Interpretation / Action, storage, display, compat responsibilities | Yes (context) |
| `docs/product/meaning-translation-mapping.md` | **Active** | `history_theme` generation source / transform / connection (Derived layer) | Yes (Derived-field context) |
| `docs/core/meaning-layer.md`, `meaning-layer-connection.md`, `narrative-guideline.md` | Active | Non-assertion principle, meaning-layer connection | Reference only |
| `docs/knowledge/glossary.md` | Active | Defines **Stored / Derived / Runtime / Governance** layer terms | Yes — layer vocabulary |
| `docs/audit/mixed-confidence-policy-decision.md` | **Decided (技術Policy固定)** — a *decision record*, not an audit | `FULL_SUPPRESSION` retained: on `CONFIDENCE_MIXED` deity facts, whole-fact Reason suppression stays | Yes — a fixed policy the audit must respect, not re-litigate |

### 4.2 Current tooling (read-only; reusable as audit instruments)

| Asset [repo] | Purpose | Tests [repo] |
|---|---|---|
| `python manage.py knowledge_coverage_report` → `temples/services/knowledge_coverage_report.py` `build_knowledge_coverage_report()` | Read-only Coverage aggregation: total/audit-target shrines, Knowledge/Zero-Knowledge/Deity/History/Source coverage, fact-ready counts, verification-status / confidence / source-type distributions | `test_knowledge_coverage_report.py`, `test_knowledge_coverage_report_command.py` |
| `temples/services/evidence_gate.py` — `decide_fact_usability()` / `EvidenceDecision` / `decide_detail_display_state()` | Single source of truth for per-Fact `usable` on both Recommendation and Detail paths | `test_evidence_gate.py`, `test_evidence_gate_detail_display_state.py`, `test_evidence_gate_pilot_regression.py` |
| `temples/services/shrine_knowledge_selector.py` | Recommendation-side fact selection (consumes Evidence Gate) | `test_shrine_knowledge_selector.py` |
| `temples/services/shrine_qa_fixture_exclusion.py` — `exclude_qa_fixture_shrines()` | Single source of truth for "which Shrine rows are real (audit-target)"; name-convention based | `test_shrine_qa_fixture_exclusion.py` |
| `import_shrine_knowledge.py` / `export_shrine_knowledge.py` / `temples/services/knowledge_seed.py` | Knowledge batch import/export (reproducible seed files from Batch 8 onward) | `test_knowledge_seed_import.py`, `test_batch{9..17}_knowledge_seed.py`, `test_shrine_base_batch17_seed.py` |
| `backfill_goriyaku_tags.py` — `parse_goriyaku()` | `Shrine.goriyaku` free-text → `GoriyakuTag` M2M by exact string match | (covered indirectly; `test_text_evidence_scoring_contract.py` for downstream) |
| `test_gis_migration_0094_shrine_70_coordinates.py`, migration `0094` | Shrine 70 coordinate correction (forward/reverse) | dedicated |
| `test_shrine_duplicate_normalize.py`, `test_gis_knowledge_seed_shrine_identity.py`, `test_shrine_submission_duplicate_candidates.py` | Identity / dedup / submission-duplicate behaviour | dedicated |
| `measure_knowledge_recommendation_quality.py` + `test_recommendation_reason_quality_knowledge_properties.py` | Knowledge → Reason quality measurement | dedicated |

### 4.3 Historical audit / archive records (evidence of what was true *then*; NOT current DB truth)

Point-in-time records. **All state changes below were applied to a local dev
DB only unless a `*-production-import-execution.md` doc says otherwise.**

| Path | Declared status [repo] | Shrine coverage | Contract or history? | Revalidation |
|---|---|---|---|---|
| `shrine-knowledge-pilot-5-result.md` | **Archive** | 明治神宮, 品川神社, 三峯神社, 神田神社, 給田六所神社 (5) | Historical result | REVALIDATION_REQUIRED (local DB only) |
| `recommendation-fact-integrity-negative-pilot.md` | **Archive** | 長太稲荷神社, 鹿島神宮, 阿佐ヶ谷神明宮 (3) — negative cases (low confidence / disputed / no-source) | Historical result | REVALIDATION_REQUIRED (local DB only) |
| `shrine-knowledge-real-data-pilot-1.md`, `knowledge-model-pilot-2-shinagawa.md` | Archive | Pilot #1 / #2 | Historical | REVALIDATION_REQUIRED |
| `shrine-knowledge-rollout-batch-1..7.md` | Historical (point-in-time) | Batches 1–7 (Django-shell ORM inserts; no reproducible seed until back-converted) | Historical result | REVALIDATION_REQUIRED |
| `knowledge-batch{8..17}-seed-preflight.md` / `-target-selection.md` / `-closure-batch*-reentry.md` | Historical (per-batch record pair) | Batches 8–17 target selection + preflight | Historical result + tooling record | Batch content: REVALIDATION_REQUIRED against current DB |
| `knowledge-batch{10,16}-production-import-execution.md`, `knowledge-batch17-production-import.md` | Historical **execution** records | Production knowledge imports; `knowledge-batch17-production-import.md` names **Batch 16** as "最終Batch実際に投入済み" (Batch 17 import doc present; production ≥ Batch 16, Batch 17 status to reconfirm) | Historical execution record | Production knowledge extent: REVALIDATION_REQUIRED |
| `shrine-dataset-integrity.md` | **Complete** — `RECOMMENDATION_ISSUE_DOMINATES_DATA_IS_NOT_THE_BLOCKER` | Full dataset; **TRACKED SEED / LOCAL DB = 100, PRODUCTION = 105** with 3 exact-duplicate `name_jp` pairs (長太稲荷神社 21/103, 給田六所神社 22/101, 富岡八幡宮 49/104 weaker) — partial unique constraint does not cover `place_ref`-set rows | Historical audit (read-only) | Duplicate-row state: REVALIDATION_REQUIRED against current Production |
| `shrine-70-coordinate-correction.md` | "Local correction verified; Production apply = separate authorized deploy, not performed" | Shrine id=70 coordinates | Historical + migration `0094` | Production apply status: REVALIDATION_REQUIRED |
| `shrine-data-pipeline-phase0-audit.md` | `PHASE0_AUDIT_COMPLETE_NO_MISSING_NO_CONFLICT` | Pipeline inventory | Historical audit | reusable as pipeline map |
| `shrine-geographic-knowledge-coverage.md` | `GEO_KNOWLEDGE_COVERAGE_AUDIT_COMPLETE_NO_STOP` | Geographic/prefecture coverage | Historical audit | prefecture counts: REVALIDATION_REQUIRED |
| `shrine-knowledge-source-automation-readiness.md` | `STOP_GATE_A_TRIGGERED_SOURCE_CONTENT_ACCESS_BLOCKED` | Source-automation feasibility | Historical audit (stopped) | — |
| `shrine-discovery-automation-readiness.md` | `DISCOVERY_READINESS_AUDIT_COMPLETE_PILOT_PARTIAL_KNOWLEDGE_LAYER_STOPPED` | Discovery-automation feasibility | Historical audit + partial pilot | — |
| `knowledge-production-readiness-audit.md` | **Active — Mother Ship Decision Pending** | Production-import readiness | Audit with open MS decision | still open |
| `mixed-confidence-policy-audit.md` | **Active — Decision Pending** (superseded in practice by `-decision.md`) | Mixed-confidence technical comparison | Audit; decision recorded separately | closed by `-decision.md` |
| `shrine-knowledge-recommendation-evidence-bridge.md` (PR #2571), `recommendation-evidence-followup-design.md` (PR #2572) | Historical (feed the Evidence Review Contract) | `MISSING_PIPELINE_BRIDGE` finding + design options | Historical → superseded by `recommendation-evidence-review-contract.md` | — |
| `batch17-recommendation-evidence-review.md` | **REVIEW / AUDIT ONLY** | 北海道神宮 (NO_RECOMMENDATION_EVIDENCE), 建部大社 (HOLD), 波上宮 (partial) | First operational run of the Evidence Review Contract | reusable as the pilot template that already exists |
| `recommendation-v4-reason-facts-e2e-audit.md`, `reason-facts-coverage*.md` | **Archive** | Reason-facts coverage snapshots | Historical | REVALIDATION_REQUIRED |
| `knowledge-base-consistency-audit.md`, `knowledge-base-refactoring.md` | Historical | Knowledge base doc consistency | Historical | — |
| `goriyaku-mapping-master-integrity{,-correction}.md`, `compass-purpose-goriyaku-mapping{,-correction}.md`, `remaining-need-goriyaku-semantic-mapping.md`, `safe-remaining-need-goriyaku-mapping-correction.md` | Historical (Mapping corrections; some superseded by the recent D1a/C-EL/M1/R2 series) | GoriyakuTag ↔ Need mapping | Historical; current mapping truth = `backend/temples/domain/need_to_goriyaku_tag_ids.py` + `docs/audit/recommendation-semantic-followup-closeout.md` | current code is authoritative |

## 5. Contract vs historical classification

| Classification | Members |
|---|---|
| **ACTIVE_CONTRACT** | `docs/knowledge/shrine-knowledge-contract.md`; `docs/knowledge/recommendation-evidence-review-contract.md`; `docs/knowledge/shrine-profile-spec.md`; `docs/knowledge/shrine-data-guide.md`; `docs/core/recommendation-readiness.md`; `docs/core/recommendation-architecture.md`; `docs/core/recommendation-reason-contract.md`; `docs/product/meaning-translation-mapping.md`; `docs/knowledge/glossary.md`; `docs/audit/mixed-confidence-policy-decision.md` (fixed policy record) |
| **CURRENT_TOOLING** | `knowledge_coverage_report` command + service; `evidence_gate.py`; `shrine_knowledge_selector.py`; `shrine_qa_fixture_exclusion.py`; `import/export_shrine_knowledge` + `knowledge_seed.py`; `backfill_goriyaku_tags.py`; `measure_knowledge_recommendation_quality.py`; migration `0094` + its test; identity/dedup tests |
| **HISTORICAL_AUDIT** | `shrine-dataset-integrity.md`; `shrine-70-coordinate-correction.md`; `shrine-geographic-knowledge-coverage.md`; `shrine-data-pipeline-phase0-audit.md`; `knowledge-batch{8..17}-*` (preflight/target/closure/import-execution); `shrine-knowledge-rollout-batch-1..7.md`; `knowledge-production-readiness-audit.md`; `mixed-confidence-policy-audit.md`; `shrine-knowledge-recommendation-evidence-bridge.md`; `recommendation-evidence-followup-design.md`; `batch17-recommendation-evidence-review.md`; `shrine-knowledge-source-automation-readiness.md`; `shrine-discovery-automation-readiness.md`; the goriyaku-mapping-correction audits |
| **ARCHIVE_REFERENCE** | `shrine-knowledge-pilot-5-result.md` (Status: Archive); `shrine-knowledge-real-data-pilot-1.md`; `knowledge-model-pilot-2-shinagawa.md`; `recommendation-fact-integrity-negative-pilot.md` (Status: Archive); `recommendation-v4-reason-facts-e2e-audit.md` (Status: Archive); `reason-facts-coverage*.md`; `knowledge-base-consistency-audit.md` |
| **SUPERSEDED** | old Readiness "Level 0–3" runtime design (superseded by Capability Set inside `recommendation-readiness.md`); `shrine-knowledge-recommendation-evidence-bridge.md` + `recommendation-evidence-followup-design.md` (superseded by `recommendation-evidence-review-contract.md`); the several `goriyaku-mapping-*-correction` audits for the `communication`/`mental`/`family` rows (superseded by the merged D1a/C-EL/M1/R2 series + `recommendation-semantic-followup-closeout.md`) |
| **UNCLEAR** | Exact Production knowledge extent (Batch 16 vs Batch 17) — `knowledge-batch17-production-import.md` exists but names Batch 16 as the last executed import; needs a live Production read to resolve. Marked `UNCLEAR` pending §15 decision. |

## 6. Current authoritative contracts

| Concern | Authoritative source [repo] | Key definition |
|---|---|---|
| Shrine **identity** (name) | `Shrine.name_jp` / `name_romaji` (`backend/temples/models.py:226-227`); dedup via partial unique constraints (`models.py:308-338`, only where `place_ref__isnull=True`) + `shrine_qa_fixture_exclusion.py` (real vs QA-fixture) | No `canonical_status` / `official_name` field in the model — those are **spreadsheet-only** identity-audit metadata |
| **Location** | `Shrine.latitude` / `longitude` (validated ±90/±180) + `location` PointField (SRID 4326); `place_ref` → `PlaceRef` (Google Places link) | Coordinate corrections applied via migrations (e.g. `0094` for id=70); Google Places verification lives in `PlaceRef` / the spreadsheet, not on `Shrine` |
| **deity** | `ShrineDeity` (`models.py:480`), `verification_status`, `confidence`; rules in `shrine-knowledge-contract.md` | Deity name alone is **not** Recommendation Evidence (Evidence Review Contract §2, constraint #14) |
| **shrine history** | `ShrineHistory` (`models.py:523`), same status/confidence fields | Historical anecdote ⇒ REVIEW_REQUIRED, never auto-converted (Evidence Review Contract §3) |
| **tradition** | `ShrineHistory` marked as non-factual lineage per `shrine-knowledge-contract.md`; Evidence Review Contract §3 | Traditions describe belief/practice, not a Source's explicit benefit assertion |
| **goriyaku** | `Shrine.goriyaku` free-text (`models.py:241`) → `backfill_goriyaku_tags.parse_goriyaku()` → `GoriyakuTag` M2M | `recommendation-evidence-review-contract.md` §4–§5: only exact-match to an existing canonical `GoriyakuTag.name` (39 rows) or narrow single-candidate normalization; else HOLD |
| **Knowledge Fact verification** | `KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES` (`models.py:397+`) + `evidence_gate.decide_fact_usability()` | Fact correctness ≠ Recommendation eligibility (Evidence Review Contract §3) |
| **provenance / source** | `ShrineKnowledgeSource` (`models.py:432`), `source_type` choices, M2M `sources` on deity/history; `shrine-knowledge-contract.md` Source 契約 | `verification_status ≥ source_confirmed` ⇒ "verified" |
| **Recommendation Evidence eligibility** | `docs/knowledge/recommendation-evidence-review-contract.md` (§2 eligibility classes, §7 decision states, §8 shrine-level readiness) | PASS / HOLD / NO_EVIDENCE / REVISE; RECOMMENDATION_READY requires a PASS **and** Purpose-wiring |
| **Recommendation Readiness / Coverage** | `docs/core/recommendation-readiness.md` (Governance Contract) | **Schema / Populated / Verified / Usable** Coverage + Capability Set; not wired to runtime exclusion; thresholds "not normative until 105-shrine shadow evaluation" |
| **Coverage layer vocabulary** | `docs/knowledge/glossary.md` | Stored (DB) / Derived (from Stored, e.g. `history_theme`) / Runtime (per-consultation) / Governance (quality/source/ops) |

None of the above is redefined by this document.

## 7. Spreadsheet responsibility

**Spreadsheet content NOT VERIFIED this session** — `https://docs.google.com/
spreadsheets/d/1v6bLXuM1q9UGyZMxv2GvbsFD2ECrE1rHSvKPjydSEP8/…` returned
**HTTP 401 Unauthorized** for both the `/edit` and `?format=csv` URLs. The
column list below is the **task-provided known role**, to be confirmed
against the live sheet by whoever runs PR-B (with authenticated access).

### 7.1 Responsibility matrix

| Layer | Authoritative for | Reference-only for | Never canonical for |
|---|---|---|---|
| **Google Spreadsheet "神社のDB"** | Identity / Location **audit reference**: name, address, lat/long, `canonical_status`, `official_name`, `official_address`, `official_source`, coordinate-audit / Google-Places-verification notes | Cross-check of `Shrine.name_jp`/`address`/`lat`/`lng` and identity disambiguation | deity facts, shrine history, traditions, goriyaku, Recommendation Evidence — those stay under the Knowledge / Source / Evidence contracts (§6) |
| **Shrine DB** (`Shrine` table) | Current **persisted** identity + location + legacy `goriyaku`/`sajin`/`description`/`history_theme` + `goriyaku_tags` M2M | — | external-source truth (that's the spreadsheet's `official_*` + `ShrineKnowledgeSource`) |
| **Knowledge Facts** (`ShrineDeity` / `ShrineHistory`) | Verified **semantic facts** (deity, history, tradition) with `verification_status` / `confidence` | — | Recommendation eligibility by itself (Evidence Review Contract §3) |
| **Official Sources** (`ShrineKnowledgeSource` + spreadsheet `official_source`) | External **primary evidence** / provenance | — | the *meaning* of a fact (that's the Fact row it supports) |
| **GoriyakuTag** (39 canonical rows) + `Shrine.goriyaku` | **Recommendation Evidence** labels | — | new taxonomy (frozen; MS decision required to expand) |
| **Need mapping** (`NEED_TO_GORIYAKU_IDS` / `NEED_TEXT_WEIGHTS`) | **Runtime recommendation semantics** (Need → evidence) | — | shrine-level truth; it is engine wiring, not data |

### 7.2 Canonical-vs-audit-reference decision per field category

| Field category | Spreadsheet role | Rationale |
|---|---|---|
| name / address | **audit-reference** (cross-check `Shrine.name_jp` / `address`) | DB is the persisted system of record; sheet flags drift |
| latitude / longitude | **audit-reference** (Google-Places / coordinate audit) | DB `latitude`/`longitude`/`location` is what the engine uses; sheet is the correction backlog |
| `canonical_status` / `official_name` / `official_address` | **canonical for the identity-audit dimension only** (no DB equivalent field exists) | These are identity-governance metadata; they belong in the audit layer, not the runtime model |
| `official_source` | **audit-reference**, feeds `ShrineKnowledgeSource` review — never auto-imported | Provenance must pass the Source 契約 / Evidence Review Contract |
| deity / history / tradition / goriyaku / Recommendation Evidence | **NOT canonical — explicitly excluded** | Governed by §6 contracts; the sheet must not be treated as a semantic source |

## 8. Current DB ↔ Spreadsheet join

### 8.1 Current DB shrine set — `[dev-db]`

| Metric | Value | Source |
|---|---|---|
| `Shrine` rows total | **105** | `[dev-db]` ORM `count()` |
| `kind='shrine'` | 105 (0 temples) | `[dev-db]` |
| id range | 1..105, **contiguous** | `[dev-db]` |
| QA / test fixture rows (`exclude_qa_fixture_shrines`) | **5** — ids **101–105**: `承認テスト神社`, `admin承認テスト神社`, `重複検証神社`, `重複検証神社`, `重複検証神社（別宮）` | `[dev-db]` + `shrine_qa_fixture_exclusion.py` [repo] |
| **Audit-target real shrines** | **100** (ids 1–100) | `knowledge_coverage_report` "Audit Target Shrines: 100" `[dev-db]` |
| Real-shrine duplicate `name_jp` in dev DB | **0** (only the QA fixture `重複検証神社` repeats) | `[dev-db]` |
| Rows with lat AND lng | 105 / 105 | `[dev-db]` |
| Rows with `place_ref` set | **0** | `[dev-db]` |

**Count reconciliation vs [prior] `shrine-dataset-integrity.md`:**

| Set | Count | Distinct `name_jp` | Extra rows are… |
|---|---|---|---|
| TRACKED SEED / LOCAL DB `[prior]` | 100 | 100 | — |
| **This session's dev DB** `[dev-db]` | 105 | 104 | ids 101–105 = QA/test fixtures (not real shrines) |
| PRODUCTION `[prior]` | 105 | 103 | 3 **duplicate real-shrine** `name_jp` pairs (長太稲荷神社 21/103, 給田六所神社 22/101, + 富岡八幡宮 49/104 weaker) |

⇒ **The "105" in three different places is not the same 105.** The task's
"current 105 Shrine records" most closely matches the raw DB/Production row
count; the real integrity-audit surface is **100** in dev, **~102 unique**
in Production. This discrepancy is itself finding **U-1** (§10).

### 8.2 Join execution

| Join dimension | Result |
|---|---|
| DB id ↔ spreadsheet id | **NOT VERIFIED** — spreadsheet inaccessible (401). Design: attempt `EXACT_ID_MATCH` on a stable id column first; the DB has contiguous ids 1–105 `[dev-db]`, but whether the sheet carries the same id space is unknown |
| all 100/105 DB shrines present in sheet | **NOT VERIFIED** |
| sheet rows not in DB | **NOT VERIFIED** |
| duplicate IDs / names in sheet | **NOT VERIFIED** (DB side: only the QA fixture repeats, `[dev-db]`) |

Join classification counts (`EXACT_ID_MATCH` / `IDENTITY_MATCH` / `AMBIGUOUS`
/ `MISSING_IN_SHEET` / `MISSING_IN_DB`): **all NOT VERIFIED** — cannot be
produced without authenticated spreadsheet access. Producing them is the
first deliverable of PR-B.

## 9. Existing verification coverage

**All figures `[dev-db]` via `knowledge_coverage_report` unless noted — NOT
Production-verified; every row carries `REVALIDATION_REQUIRED`.** Denominator
is the 100 audit-target shrines unless stated.

| Verification type | `[dev-db]` state | Contract basis |
|---|---|---|
| **IDENTITY_VERIFIED** | Model-level: 100/100 have `name_jp`; dedup constraints active only where `place_ref` is null. External identity (`canonical_status`/`official_name`) — **NOT VERIFIED** (spreadsheet). `[prior]` `shrine-dataset-integrity.md` verified the *dataset-structure* question (duplicates, constraints) against a Production dump | `Shrine` model + `shrine-dataset-integrity.md` |
| **LOCATION_VERIFIED** | 100/100 have lat+lng `[dev-db]`. Coordinate *correctness*: only id=70 has a recorded correction (`shrine-70-coordinate-correction.md`, local-verified, Production apply status REVALIDATION_REQUIRED). Google-Places/coordinate audit for the rest — **NOT VERIFIED** (spreadsheet) | migrations + spreadsheet |
| **KNOWLEDGE_VERIFIED** | Knowledge Coverage **86 / 100 (86.0%)**; Zero-Knowledge **14 / 100**; Deity 86, History 84, Both 84, Source 86. Deity-count distribution `{0:14, 1:20, 2:19, 3:27, 4:11, 5:6, 6:1, 7:2}`; History `{0:16, 1:29, 2:26, 3:19, 4:6, 5:4}` `[dev-db]` | `recommendation-readiness.md` §Coverage Taxonomy (**Populated Coverage**) |
| **SOURCE_VERIFIED** | **Verified Source Count 110 / Total 110** (all `source_confirmed`); across all Fact rows the verification-status distribution is `{source_confirmed: 415}` (0 draft/disputed/outdated/rejected among audit-target facts); source-type `{shrine_official: 97, secondary_editorial: 5, cultural_property: 4, tourism_official: 1, government: 1, local_history: 1, user_observation: 1}` `[dev-db]` | `recommendation-readiness.md` §Verified Coverage |
| **FACT_INTEGRITY_VERIFIED** | Only where a prior audit did sentence-level integrity work: Pilot 5 (`shrine-knowledge-pilot-5-result.md`) + negative pilot 3 (`recommendation-fact-integrity-negative-pilot.md`) = **8 shrines** `[prior]`, all local-DB-only. Current DB match to those audited states: **REVALIDATION_REQUIRED** | `recommendation-fact-integrity-negative-pilot.md`, Pilot 5 |
| **GORIYAKU_EVIDENCE_VERIFIED** | **100 / 105 rows** have `goriyaku_tags` + non-empty `goriyaku` text `[dev-db]`, but per `recommendation-evidence-review-contract.md` §12 most of these are **LEGACY_EXISTING** (original seed, never provenance-reviewed). Explicit Evidence-Review-Contract runs: **3 shrines** (`batch17-recommendation-evidence-review.md`: 北海道神宮 = NO_RECOMMENDATION_EVIDENCE, 建部大社 = HOLD, 波上宮 = partial) `[prior]` | Evidence Review Contract §7–§12 |

**Fact-ready (Evidence Gate `usable=True`) Coverage** `[dev-db]`: Deity 86 /
100, History 84 / 100, Any 86 / 100 — i.e. **Usable Coverage ≈ Populated
Coverage** here because every audit-target Fact is `source_confirmed` with a
fact-ready Source. Confidence distribution `{high: 396, medium: 19}`, no
`low` — consistent with `[prior]` `INSUFFICIENT_NEGATIVE_CASES`.

## 10. Unverified surface

The remaining audit surface for the full 105/100-shrine integrity audit.
None is fixed here.

| ID | Unverified surface | Affected set | Why it is open |
|---|---|---|---|
| **U-1** | **"105" identity ambiguity** — dev DB 105 (100 real + 5 QA fixtures) ≠ tracked seed 100 ≠ Production 105 (3 duplicate real-shrine pairs). The canonical audit-target set is undefined across environments | all | §8.1; needs a live Production read + MS decision on which set is "the 105" |
| **U-2** | **Spreadsheet ↔ DB join** — every join dimension (id match, presence, extras, duplicates) | all | spreadsheet 401; §8.2 |
| **U-3** | **Identity governance fields** — `canonical_status` / `official_name` / `official_address` have **no DB column**; their per-shrine values and DB agreement are unknown | all | spreadsheet 401; model has no equivalent |
| **U-4** | **Location correctness** beyond id=70 — Google-Places / coordinate-audit status per shrine; whether id=70's fix is in Production | 99–104 shrines | spreadsheet 401; `shrine-70` Production apply not confirmed |
| **U-5** | **Zero-Knowledge shrines** — **14 / 100** `[dev-db]` have no deity and no history (e.g. id=3 伊勢神宮（内宮）) | 14 | no Knowledge Facts exist to audit; needs Fact generation first |
| **U-6** | **LEGACY_EXISTING goriyaku provenance** — ~100 shrines carry `goriyaku_tags` from the original seed with **no** Evidence-Review-Contract provenance record | ~97 (100 minus the 3 batch-17-reviewed) | Evidence Review Contract §12 explicitly does not retro-validate legacy `goriyaku` |
| **U-7** | **Knowledge present, provenance not re-validated to current standard** — Batches 1–7 were Django-shell ORM inserts; their Source rigor predates the current Source 契約 | Batch 1–7 shrines | `[prior]` `knowledge-batch17-production-import.md` "LOCAL_DB_ONLY … not reproducible" |
| **U-8** | **`goriyaku_tags` present but official support unknown** — for shrines whose tags came from seed inference, not a Source statement | overlaps U-6 | no provenance record links tag → Source phrase |
| **U-9** | **Official source exists but Knowledge incomplete** — shrines with a `ShrineKnowledgeSource` but < full deity+history coverage (`[dev-db]`: 86 with source, 84 with both deity+history ⇒ ~2 have source but not both) | ~2–16 | partial fact generation |
| **U-10** | **Prior-audit DB drift** — Pilot 5 + negative pilot 3 + batches were local-DB-only; the current dev DB has 86-shrine knowledge coverage that no single merged audit documents as its end state | 8 explicitly audited + all batch shrines | `REVALIDATION_REQUIRED` throughout §4.3 / §9 |
| **U-11** | **Production knowledge extent** — Batch 16 vs Batch 17 executed to Production (`UNCLEAR`, §5) | up to a full batch of shrines | needs a live Production read |
| **U-12** | **Purpose-connectivity of PASS evidence** — even a correct PASS (e.g. 航海安全/海上安全 ids 13/14) may route to **no** current Purpose (`recommendation-evidence-review-contract.md` §8; `travel_safe` mapping still `{3,13,14}` but historically flagged) | any voyage-safety / niche-benefit shrine | Mapping-layer question, out of data-audit scope but must be recorded per shrine |
| **U-13** | **mixed-confidence output shape** — shrines with `CONFIDENCE_MIXED` deity facts (e.g. `[prior]` 阿佐ヶ谷神明宮) fall to generic Reason by fixed policy; audit must record which shrines are in this state, not treat it as a bug | ≥1 | `mixed-confidence-policy-decision.md` (fixed) |

## 11. Proposed full-audit matrix

Row schema for the future per-shrine audit. **Not populated here.** Column
values reuse existing repo terminology; new analytical labels are marked
"proposed audit-only".

| Column | Type / vocabulary | Source contract |
|---|---|---|
| `shrine_id` | int (DB `Shrine.id`) | `Shrine` model |
| `name_jp` | str | `Shrine.name_jp` |
| `prefecture` | str (derived from `address` — no DB field; audit-only extraction) | proposed audit-only |
| `spreadsheet_identity_status` | `EXACT_ID_MATCH` / `IDENTITY_MATCH` / `AMBIGUOUS` / `MISSING_IN_SHEET` | §8.2 (join classes) |
| `db_identity_status` | `UNIQUE` / `DUPLICATE_PAIR` / `QA_FIXTURE` | `shrine-dataset-integrity.md` + `shrine_qa_fixture_exclusion.py` |
| `location_status` | `LOCATION_VERIFIED` / `CORRECTION_APPLIED` / `CORRECTION_PENDING` / `UNVERIFIED` | migrations + spreadsheet coord-audit |
| `knowledge_presence` | `has_fact_ready_deity` / `has_fact_ready_history` (bool each) + `zero_knowledge` (bool) | `recommendation-readiness.md` Capability Set |
| `deity_source_status` | `verification_status` value + `confidence` value + source count | `shrine-knowledge-contract.md` Source 契約 |
| `history_source_status` | same shape as deity | same |
| `tradition_source_status` | same shape (tradition rows in `ShrineHistory`) | `shrine-knowledge-contract.md` |
| `goriyaku_source_status` | `LEGACY_EXISTING` / `REVIEWED_NEW` / `NONE` | `recommendation-evidence-review-contract.md` §12 |
| `goriyaku_tag_ids` | list[int] (`Shrine.goriyaku_tags`) | `GoriyakuTag` M2M |
| `recommendation_evidence_eligibility` | `RECOMMENDATION_READY` / `PARTIALLY_READY` / `NO_RECOMMENDATION_EVIDENCE` / `HOLD` | `recommendation-evidence-review-contract.md` §8 |
| `previous_audit_refs` | list[doc path] | §4.3 |
| `revalidation_required` | bool + reason | §9 / §10 |
| `integrity_status` | **`MATCH` / `PARTIAL` / `UNSUPPORTED` / `MISSING` / `REVIEW_REQUIRED`** | proposed audit-only (compatible w/ Evidence Review Contract's PASS/HOLD family) |
| `root_cause` | **`SHEET_DRIFT` / `DB_DRIFT` / `KNOWLEDGE_DRIFT` / `TAG_DRIFT` / `PROVENANCE_WEAK`** — **proposed audit-only labels, NOT product taxonomy** (none of these strings exists in current contracts) | proposed audit-only |
| `remediation_candidate` | free text → later PR-D | proposed audit-only |

### 11.1 Full-audit classification definitions (reuse-first)

| Output | Meaning (aligned to existing terms) |
|---|---|
| **MATCH** | DB ↔ spreadsheet ↔ Source ↔ Knowledge ↔ GoriyakuTag all consistent; any goriyaku evidence is `LEGACY_EXISTING`-valid or `REVIEWED_NEW` PASS |
| **PARTIAL** | some layers consistent, at least one incomplete (e.g. identity+location OK, semantic facts absent) — maps to `PARTIALLY_READY` |
| **UNSUPPORTED** | a value is present (goriyaku tag, deity claim) with **no** Source backing it — maps to Evidence Review Contract `INELIGIBLE` / `HOLD` |
| **MISSING** | expected data absent (Zero-Knowledge, no Source) |
| **REVIEW_REQUIRED** | ambiguity a human must resolve (duplicate identity, `REVIEW_REQUIRED` evidence class, mixed confidence) |

## 12. Pilot selection

10 shrines for PR-B (all `[dev-db]` ids; deliberately mixed difficulty).
Final list confirmable once the spreadsheet is accessible.

| # | Shrine | id `[dev-db]` | Why chosen (variety axis) |
|---|---|---|---|
| 1 | 明治神宮 | 1 | Previously well-verified (Pilot #1); `has_multiple_sources`, high confidence — the "clean MATCH" baseline |
| 2 | 品川神社 | (Pilot #2) | Knowledge-rich, high confidence; second well-verified reference |
| 3 | 伊勢神宮（内宮） | 3 | **Zero-Knowledge** (no deity, no history, empty legacy fields) — the `MISSING` case; also the engine's documented zero-knowledge fallback shrine |
| 4 | 太宰府天満宮 | (seed) | Multiple `GoriyakuTag`s (`学業成就・合格祈願・厄除け`), **LEGACY_EXISTING** goriyaku with no provenance record — the `U-6` case |
| 5 | 建部大社 | (Batch 17) | Has a completed **Fact Integrity / Evidence Review** run ending in **HOLD** (Yoritomo anecdote) — the `REVIEW_REQUIRED` case |
| 6 | 北海道神宮 | (Batch 17) | Evidence Review = **NO_RECOMMENDATION_EVIDENCE** (fully reviewed, terminal) — distinct from "not yet reviewed" |
| 7 | 波上宮 | (Batch 17) | Explicit voyage-safety Source language → potential PASS that may **not** be Purpose-wired (`U-12`) |
| 8 | 長太稲荷神社 | 21 (+103 in Production) | **Duplicate identity pair** in Production + negative-pilot subject (weak/low provenance) — `DB_DRIFT` + `PROVENANCE_WEAK` |
| 9 | 阿佐ヶ谷神明宮 | (negative pilot) | **CONFIDENCE_MIXED** deity facts → generic Reason by fixed policy (`U-13`) |
| 10 | 給田六所神社 | 22 (+101 in Production) | Pilot 5 subject (`medium` confidence, no `shrine_official` source, `has_multiple_sources`) **and** a Production duplicate pair — combines KNOWLEDGE_DRIFT-risk with DB_DRIFT |

Coverage of the required variety: well-verified (1, 2), knowledge-rich (1, 2,
4), knowledge-missing (3), multi-tag (4), prior Fact-Integrity audit (5, 6,
7, 8, 9, 10), historical coordinate correction — **note**: id=70 (`shrine-70`)
is a candidate swap-in if a coordinate-correction case is wanted explicitly;
weak/absent provenance (8, 9). Not only easy cases.

## 13. Full 105-shrine audit plan

### 13.1 PR sequence

| PR | Name | Scope | Explicit non-goals |
|---|---|---|---|
| **PR-A** | **Readiness / inventory** (this PR) | This document only | any data touch |
| **PR-B** | **5–10 shrine integrity pilot** | Run the §11 matrix for the §12 pilot: Spreadsheet ↔ DB ↔ Official Source ↔ Knowledge Facts ↔ GoriyakuTag ↔ Recommendation Evidence. Confirm the row schema + classification labels are workable. Requires **authenticated spreadsheet access** + a **Production (or fresh Production dump) DB read** | no data fixes; no schema change; do not expand to all 105 until the format is confirmed |
| **PR-C** | **Full 105/100-shrine integrity audit** | Populate the matrix for every audit-target shrine; per-shrine `integrity_status` + `root_cause` | no data fixes |
| **PR-D** | **Remediation plan** | Group PR-C findings into isolated fix batches; per batch: risk, contract check, MS decisions needed | no execution |
| **PR-E** | **Data fixes in isolated batches** | Execute PR-D batches one at a time, each its own PR, each behind its own gate (identity fixes ≠ knowledge fixes ≠ goriyaku fixes) | never a single mega-fix PR |

### 13.2 PR-B entry conditions (gates)

1. Authenticated read of the Google Spreadsheet "神社のDB" — column headers,
   row count, id column confirmed (resolves `U-2`, `U-3`).
2. A Production DB read path (the existing `~/.config/kami-musubi/
   production-db.env` credential-bridge pattern, read-only) **or** an
   explicitly authorized fresh Production dump (resolves `U-1`, `U-11`).
3. MS decision on which shrine set is "the 105/100" (§15).

Until (1)–(3) exist, PR-B can only run against `[dev-db]` and its
spreadsheet-side columns stay NOT VERIFIED.

## 14. Known limitations

- **Google Spreadsheet inaccessible** (HTTP 401) — all spreadsheet-derived
  facts in this document are the task-stated known role, NOT VERIFIED.
- **No Production DB access this session** — every count is `[dev-db]`, a
  local Postgres that is neither the tracked seed (100) nor a confirmed
  Production mirror (105 with duplicate pairs).
- The dev DB's ids 101–105 are QA fixtures; Production's extra 5 rows are
  duplicate real shrines — so "id 101" means different things per
  environment.
- Prior audits (Pilot 5, negative pilot, batches 1–17) were local-DB-only
  unless a `*-production-import-execution.md` states otherwise; their
  findings are historical, not current DB truth.
- `prefecture` is not a DB field; any prefecture grouping is an audit-time
  derivation from `address` free text.
- `SHEET_DRIFT` / `DB_DRIFT` / `KNOWLEDGE_DRIFT` / `TAG_DRIFT` /
  `PROVENANCE_WEAK` are **proposed audit-only analytical labels** — they are
  not established in any current contract and must not leak into product
  taxonomy without an MS decision.
- This document does not re-verify the `NEED_TO_GORIYAKU_IDS` "ids 42–45 do
  not exist in the 39-row table" note from the Evidence Review Contract §19;
  the current mapping truth is `backend/temples/domain/
  need_to_goriyaku_tag_ids.py` + `recommendation-semantic-followup-closeout.md`.

## 15. Mother Ship decisions required

1. **Canonical audit-target set** — is the full audit run against the
   **100** real dev shrines, the **105** Production rows (incl. duplicate
   pairs), or a de-duplicated **~102**? (`U-1`)
2. **Production access for PR-B/PR-C** — approve a read-only Production DB
   path (credential-bridge) or authorize a fresh Production dump.
3. **Spreadsheet access** — provide authenticated access (or an exported
   CSV/snapshot) for the identity/location join.
4. **Duplicate real-shrine rows** (長太稲荷神社 21/103, 給田六所神社 22/101,
   富岡八幡宮 49/104) — merge, keep-both-with-canonical-flag, or defer? This
   sets `db_identity_status` semantics.
5. **Zero-Knowledge shrines (14/100 `[dev-db]`)** — in-scope for the
   integrity audit as `MISSING`, or deferred to a separate Fact-generation
   track?
6. **LEGACY_EXISTING goriyaku** (~97 shrines) — does the full audit
   retro-review their provenance to the current Source standard, or record
   them as `LEGACY_EXISTING`-accepted (per Evidence Review Contract §12) and
   move on?
7. **`canonical_status` / `official_name` / `official_address`** — do these
   spreadsheet fields get a DB home (new nullable columns / a side table) in
   a later PR, or stay audit-layer-only?
8. **Proposed audit-only labels** — accept `MATCH/PARTIAL/UNSUPPORTED/
   MISSING/REVIEW_REQUIRED` + the drift root-cause set for the audit output,
   confirming they do not become product taxonomy.
9. **Purpose-connectivity gaps** (`U-12`, e.g. 航海安全/海上安全) — record
   per shrine only, or open a Mapping follow-up?

## 16. Final readiness verdict

**`READINESS_AUDIT_COMPLETE_FULL_AUDIT_BLOCKED_ON_ACCESS`**

- The **contract layer is ready**: every concern (identity, location,
  deity, history, tradition, goriyaku, Fact verification, provenance,
  Recommendation Evidence eligibility, Readiness, Coverage) has a current,
  identifiable authoritative source (§6), and reusable read-only tooling
  exists (`knowledge_coverage_report`, `evidence_gate`,
  `shrine_qa_fixture_exclusion`) (§4.2).
- The **audit design is ready**: the per-shrine matrix (§11), classification
  vocabulary (§11.1), pilot set (§12), and PR-A…PR-E sequence (§13) are
  defined and reuse existing terminology.
- The **full audit cannot start** until three access blockers clear
  (§13.2): authenticated Google Spreadsheet access, a Production DB read (or
  authorized dump), and an MS decision on the canonical 100/105/~102 set.
  Until then, only `[dev-db]`-side observation is possible and the entire
  Spreadsheet↔DB join (§8.2) is NOT VERIFIED.
- **No blocker was found in the engine or the contracts** — the blockers are
  data-access and a scoping decision, not correctness defects.

Recommended next action: **PR-B (5–10 shrine pilot)**, gated on §15
decisions 1–3.

## 17. STOP / No production changes

- Production / Shrine data / Knowledge data / GoriyakuTag / Recommendation
  Engine / fixtures / seed / migrations / models / frontend / the Google
  Spreadsheet: **all unchanged**.
- Files added by this PR: **`docs/audit/shrine-evidence-audit-readiness.md`**
  only.
- `git diff --check`: CLEAN.
- The 5–10 shrine pilot (PR-B) is **not** started.

This branch is docs-only. STOP.
