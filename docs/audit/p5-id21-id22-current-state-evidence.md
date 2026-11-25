# P5 Preflight — id 21 / id 22 Current-State Evidence Freeze

## 1. Metadata

| Field | Value |
|---|---|
| Task | P5 preflight — **read-only** current-state freeze for Shrine ids 21 (長太稲荷神社) and 22 (給田六所神社) before P5 `TAG_RECONCILIATION`. No normalize / delete / add / rewrite of any data. |
| Type | Audit-only gate. Decision packet, no mutation. |
| Branch | `audit/p5-id21-id22-current-state-evidence` |
| Base | `origin/develop` @ `607de72b925ba33323f0248ec31cabf4d0767d2c` (= expected historical merge after P4; PR #2620 / migration 0096 **present**). `git fetch origin` this session. Intervening since P4-plan: PR #2619 (`docs/audit/premium-personalization-deep-search-audit.md`, docs-only) + PR #2620 (P4). Neither materially alters `Shrine.goriyaku` / `GoriyakuTag` / recommendation mapping / `backfill_goriyaku_tags` / Recommendation Evidence contract / migrations 0091·0094·0095·0096 / Evidence Gate / Knowledge Source models / candidate·scoring path → **no `BASE_DRIFT` STOP**. |
| Local branch SHA | `607de72b925ba33323f0248ec31cabf4d0767d2c` (worktree HEAD, clean) |
| Worktree | `~/Developer/jinja_app-p5` (isolated; control repo untouched). |
| Date | 2026-08-29 |
| Production read | sanctioned read-only credential bridge (`scripts/migration_safety/readonly_query.sh` + repo-external `~/.config/kami-musubi/production-db.env`); every query passed `guard.py check-readonly-sql`; credential value never printed / logged / in argv. **No Production write.** |

## 2. Repository paths inspected

`backend/temples/models.py` (Shrine / GoriyakuTag / ShrineDeity / ShrineHistory / ShrineKnowledgeSource, M2M relations) · `backend/temples/domain/need_to_goriyaku_tag_ids.py` (`NEED_TO_GORIYAKU_IDS`, `need_tags_to_goriyaku_ids`) · `backend/temples/services/evidence_gate.py` · `backend/temples/services/shrine_knowledge_selector.py` · `backend/temples/services/concierge_chat_candidates.py` · `backend/temples/services/concierge_chat_ranking.py` · `backend/temples/services/recommendation_score_components.py` · `backend/temples/services/recommendation_score_v2.py` · `backend/temples/services/shrine_meaning_composer.py` · `backend/temples/management/commands/backfill_goriyaku_tags.py` · `backend/temples/api/serializers/shrine.py` (`ShrineDetailSerializer`) · migrations `0090` / `0091` / `0094` / `0095` / `0096` · `docs/knowledge/recommendation-evidence-review-contract.md` (incl. P10 reconciliation) · `docs/audit/shrine-evidence-integrity-full-audit.md` · `docs/audit/source-backfill-id10-id22-reproducibility.md` (P4).

## 3. Local current state [local `jinja_db`]

| | id 21 | id 22 |
|---|---|---|
| name_jp / address | 長太稲荷神社 / `日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０` | 給田六所神社 / `日本、〒157-0064 東京都世田谷区給田１丁目３−７` |
| `place_ref_id` | NULL (single row — no shadow locally) | NULL (single row — no shadow locally) |
| `history_theme` | `守り` | `守り` |
| `Shrine.goriyaku` (raw) | `地域に根ざした稲荷社として、商売繁盛や五穀豊穣、日々の暮らしの安定を願う神社。` (**prose**, one sentence, no `・`) | `地域の氏神として、暮らしや家内安全、日々の無事を見守る神社。` (**prose**) |
| `updated_at` | 2026-07-04 13:39 (local seed run) | 2026-07-04 13:39 |
| `goriyaku_tags` (local pk, name) | **(13 五穀豊穣)(14 地域安泰)(17 商売繁盛)** — 3 rows | **(9 家内安全)(14 地域安泰)** — 2 rows |
| ShrineDeity | 0 | 2 — 11 大国魂大神 `primary`, 12 天照皇大神 `secondary` (`source_confirmed` / `medium`) |
| ShrineHistory | 0 | 4 — 12 `founding` 「武蔵総社六所宮よりの分霊勧請」, 13 `historical_event` 「村社列格」, 14 「社殿改築」, 15 「神明社の合祀」 (`source_confirmed` / `medium`) |
| Sources | 0 | `secondary_editorial` (Wikipedia) + `local_history` (tesshow.jp) + **`government`** on history 12 only = the **P4 `dentou-hasshin.bunka.go.jp` source, applied locally by migration 0096** |
| migrations 0091/0094/0095/0096 applied | all applied locally | all applied locally |

**Local `GoriyakuTag` table is the drifted 46-row dev table** (`DEV_DB_PK_DRIFT_SCOPE = LOCAL_DEV_ONLY_CONFIRMED`, PR #2612): legacy ids 1–15 + canonical master renumbered from 16. So local pk 13 = 五穀豊穣, 14 = **地域安泰**, 17 = 商売繁盛, 9 = 家内安全 — **not** the Production canonical numbering.

## 4. Production current state [prod]

| | id 21 | id 22 |
|---|---|---|
| name_jp / address | 長太稲荷神社 / `日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０` | 給田六所神社 / `日本、〒157-0064 東京都世田谷区給田１丁目３−７` |
| lat / lng | 35.660614 / 139.6017688 | 35.662443 / 139.5920237 |
| `place_ref_id` | **NULL** — catalog row; **shadow = id 103** (`place_ref` set) — `SAME_REAL_SHRINE_DUPLICATE`, excluded per PR #2612/#2614 | **NULL** — catalog row; **shadow = id 101** (`place_ref` set) — excluded |
| `history_theme` | `守り` | `守り` |
| `Shrine.goriyaku` (raw) | `地域に根ざした稲荷社として、商売繁盛や五穀豊穣、日々の暮らしの安定を願う神社。` (**prose**) | `地域の氏神として、暮らしや家内安全、日々の無事を見守る神社。` (**prose**) |
| `created_at` / `updated_at` | 2026-06-11 05:49 / **2026-08-10 01:18** (= migration 0091) | 2026-06-11 05:49 / **2026-08-10 01:18** (= migration 0091) |
| `goriyaku_tags` (canonical pk, name) | **(4 商売繁盛)(5 五穀豊穣)** — 2 rows | **(7 家内安全)** — 1 row |
| ShrineDeity | **0** | 2 — 39 大国魂大神 `primary`, 40 天照皇大神 `secondary` (`source_confirmed` / `medium`, sources 24+25) |
| ShrineHistory | **0** | 4 — 27 `founding` 「武蔵総社六所宮よりの分霊勧請」, 28 「村社列格」, 29 「社殿改築」, 30 「神明社の合祀」 (`source_confirmed` / `medium`) |
| ShrineKnowledgeSource | **0** | 24 `secondary_editorial` `source_confirmed`/`medium` (Wikipedia); 25 `local_history` `source_confirmed`/`medium` (tesshow.jp). **The P4 `dentou-hasshin.bunka.go.jp` government source is NOT present** — migration 0096 is `PENDING_AUTHORIZED_APPLY`. |
| Disputed Facts | none | none |

**id 21 = a genuine zero-Knowledge shrine** (0 deity / 0 history / 0 source) — matches PR #2614 (`MISSING`) and PR #2611 (§12 "genuine Zero-Knowledge").

## 5. Spreadsheet identity reconciliation

Spreadsheet is identity / location reference only; not modified; row-id equality not used as proof. Direct Codex spreadsheet read remains blocked this session; reconciliation via Production [prod] + merged identity audits (#2612 canonical-set preflight, #2613/#2614) + the id22 observation carried in the P4 task.

| Shrine | Reference identity | Production [prod] | Coordinates | Class |
|---|---|---|---|---|
| id 21 長太稲荷神社 | 長太稲荷神社 / 世田谷区上祖師谷1丁目3-10 (per #2612 §10 — `SAME_REAL_SHRINE_DUPLICATE` pair {21, 103}, byte-identical address + coords between catalog row 21 and its shadow) | 長太稲荷神社 / `…世田谷区上祖師谷１丁目３−１０` | 35.660614 / 139.6017688 | **NORMALIZED_MATCH** (name exact; `1丁目3-10` == `１丁目３−１０`; coords consistent; id 21 is the data-bearing catalog primary) |
| id 22 給田六所神社 | 給田六所神社 / 東京都世田谷区給田1丁目3-7 (P4 task-supplied spreadsheet observation) | 給田六所神社 / `…世田谷区給田１丁目３−７` | 35.662443 / 139.5920237 | **NORMALIZED_MATCH** (name exact; `1丁目3-7` == `１丁目３−７`; coords consistent) |

No `AMBIGUOUS` / `MISMATCH`. Both Production rows are the `place_ref IS NULL` catalog primaries; the `place_ref`-set shadows (103, 101) are excluded from the canonical set (#2612 / #2614) and are **not** P5 targets.

## 6. Migration 0091 origin analysis

`backend/temples/migrations/0091_fill_missing_local_shrine_reason_facts.py` — read in full.

| # | Question | Finding |
|---|---|---|
| 1 | Why id21/id22 got prose `goriyaku` | 0091 hard-codes an `updates` list for **exactly** 長太稲荷神社 + 給田六所神社. Both are small local 世田谷区 shrines that had **no Knowledge** and empty reason material; the migration name is `fill_missing_local_shrine_reason_facts` — it fills `history_theme` + `goriyaku` + tags so the Reason pipeline has non-empty input. |
| 2 | Where the prose came from | **Hand-authored inside the migration** (lines 43, 49). Not from a Source, a catalog field, or a Knowledge Fact. Editorial descriptive sentences. |
| 3 | Intended as | **Display / Reason copy + seed enrichment** — explicitly a **LEGACY reason-fill**, *not* reviewed Recommendation Evidence. No Source, no `verification_status`, no contract process. `history_theme="守り"` is a Reason-generation hint. |
| 4 | How M2M was derived | `tags = list(GoriyakuTag.objects.filter(name__in=item["tags"]))` then `shrine.goriyaku_tags.add(*tags)` — **hand-set from a hard-coded name list** (`["商売繁盛","五穀豊穣","地域安泰"]` for id21; `["地域安泰","家内安全"]` for id22). **Not parse-derived** from the prose. |
| 5 | Label not in canonical master | `filter(name__in=[…])` returns only the rows that exist → a missing label is **silently omitted**, no error, no warning, and the other tags + field updates still apply. |
| 6 | Mechanism | **`filter(name__in=…)` + `.add()`.** Not `get`, not `get_or_create`, not `.first()`. **0091 cannot create a `GoriyakuTag`.** |
| 7 | Silently no-op'd labels | **`地域安泰` for BOTH id21 and id22.** `地域安泰` is not in the Production 39-row canonical master → dropped in Production. In the drifted Local DB `地域安泰` exists (legacy pk 14) → it *was* attached locally. (Existing test `test_gis_migration_0091_shrine_reason_facts.py::test_d_missing_tag_is_silently_skipped_without_blocking_field_updates` pins this behavior.) |
| 8 | Documented legacy/catalog limitations | **Yes** — the catalog-vs-`place_ref`-duplicate-row problem is documented at length (`_resolve_target_shrine`, lines 14–26; ordering by `place_ref_id IS NULL` first). **Not documented**: the `地域安泰`-not-in-master silent drop, and that the prose is non-Source-backed reason copy. |

**id 22 known-observation verification:** ✓ prose contains 家内安全 / daily-safety copy (「暮らしや家内安全、日々の無事を見守る」); ✓ canonical tag 家内安全 (Production pk 7) is attached; ✓ intended `地域安泰` did **not** become a canonical tag (absent from the 39-row master → dropped in Production; present only in the drifted Local DB).

## 7. Raw `goriyaku` behavior (runtime role)

| Question | Answer (current code = source of truth) |
|---|---|
| A. Is `Shrine.goriyaku` parsed dynamically during recommendation requests? | **No.** The raw text is passed through unparsed — `concierge_chat_candidates.py:125` `"goriyaku": getattr(s, "goriyaku", None)`. `parse_goriyaku` (in `backfill_goriyaku_tags.py`) has **no runtime caller**. |
| B. Is Recommendation based only on persisted `GoriyakuTag` M2M? | For **`score_need` / C1 / matched_all / candidate prefilter**: **yes, M2M only** — `concierge_chat_candidates.py:67` `filter(goriyaku_tags__id__in=…)`; `:138` `"goriyaku_tag_ids": [t.id for t in s.goriyaku_tags.all()]`; `concierge_chat_ranking.py` matches `rec["goriyaku_tag_ids"]` against `need_tags_to_goriyaku_ids([tag])`. Raw `goriyaku` text has **no role in scoring/ranking**. |
| C. `backfill_goriyaku_tags` role | **Manual / admin management-command tooling** (`class Command(BaseCommand)`; run by hand). Not runtime code, not a migration. It is the tool that *would* parse `goriyaku` prose → tags via `parse_goriyaku` + `get_or_create` — but it is **not on the request path** and was **not** the mechanism for id21/id22 (their tags were hand-set by 0091). |
| D. Could changing raw prose alone change Recommendation behavior today? | **Marginally, and not for id21/id22 as they stand.** `shrine_meaning_composer._primary_benefit()` returns `goriyaku_tags[0]` if any tag exists, **else** the raw `goriyaku` — so the prose is a *primary-benefit fallback only when a shrine has zero tags*. id21 (2 tags) / id22 (1 tag) never reach that fallback. The raw prose also appears in `build_source_fields` (`ShrineMeaningSourceV2` payload) and adds +0.2 to a **shadow-only** profile-completeness metric (`recommendation_score_components.py:120`, docstring "shadow observation only"). None of this is `score_need` / ranking. |
| E. Could changing M2M alone change Recommendation behavior today? | **Yes, materially.** The persisted `goriyaku_tags` M2M drives `score_need` / matched_all / candidate prefilter. e.g. id21's `商売繁盛`(4) → `money` mapping → id21 currently registers a `money` Purpose match; removing it drops that match and its `score_need` contribution. |
| F. Does any API/UI display raw `Shrine.goriyaku` independently from scoring? | **Yes.** `ShrineDetailSerializer.Meta.fields` includes `"goriyaku"` — the raw field is returned in the Shrine Detail API response (unfiltered model field). `shrine_meaning_composer.build_source_fields` also emits it in the meaning source payload. So the prose is surfaced to clients via Shrine Detail regardless of scoring. |

## 8. M2M behavior (runtime role)

The persisted `goriyaku_tags` M2M is the **sole** goriyaku input to `score_need` / C1 / `matched_all` / candidate prefilter (Section 7.B/7.E). For id21/id22 the M2M was **hand-set by migration 0091** from a hard-coded name list (Section 6.4), **not** parse-derived from the prose and **not** from any reviewed Source. There is **no test-time or request-time re-derivation** of the M2M from the prose.

## 9. Recommendation runtime path

```text
Shrine.goriyaku (raw prose)  ──(NOT parsed at request time)──▶  ✗  (Reason/meaning fallback only when 0 tags; Shrine Detail display; shadow completeness metric)

Shrine.goriyaku_tags (persisted M2M, hand-set by 0091)
  └▶ concierge_chat_candidates.build_chat_candidates  → filter(goriyaku_tags__id__in=…) + candidate["goriyaku_tag_ids"]
     └▶ concierge_chat_ranking  → for each need_tag: expected_gids = need_tags_to_goriyaku_ids([tag]); match vs candidate goriyaku_tag_ids
        └▶ matched_all / score_need / C1  →  Lead / Reason
```

`backfill_goriyaku_tags` (manual command) sits **outside** this path. `parse_goriyaku` is command-only.

## 10. Source Evidence matrix

Canonical Need mapping (fresh read `need_to_goriyaku_tag_ids.py` @ base): `商売繁盛`(4) → **money**; `五穀豊穣`(5) → **money**; `家内安全`(7) → **health, rest**.

### id 21 長太稲荷神社

| Tag (canonical) | Origin | Canonical? | Need-mapped? | Which Needs | Reviewed explicit benefit Source? | Eligibility (contract) | Class |
|---|---|---|---|---|---|---|---|
| 4 商売繁盛 | 0091 hand-set list (prose mentions 商売繁盛) | ✓ | ✓ | money | **NO** — 0091 hand-authored prose; id 21 has **0 Knowledge / 0 Source**; no Source states this benefit | **UNKNOWN** (no reviewed Source set exists — not `NO_EVIDENCE`, which requires a fully reviewed set) | **REMOVE_CANDIDATE** |
| 5 五穀豊穣 | 0091 hand-set list (prose mentions 五穀豊穣) | ✓ | ✓ | money | **NO** — same | **UNKNOWN** | **REMOVE_CANDIDATE** |
| *(地域安泰)* | 0091 intended; absent from master | ✗ | — | — | — | N/A | **N/A** — never a canonical tag in Production (Local-only artifact of the PK drift) |
| raw `goriyaku` prose | 0091 hand-authored | — (not a tag) | — | — | — | N/A | **N/A** — `LEGACY_EXISTING` Reason/display copy; not a benefit declaration; not parse-mapped |

### id 22 給田六所神社

| Tag (canonical) | Origin | Canonical? | Need-mapped? | Which Needs | Reviewed explicit benefit Source? | Eligibility (contract) | Class |
|---|---|---|---|---|---|---|---|
| 7 家内安全 | 0091 hand-set list (prose mentions 家内安全) | ✓ | ✓ | health, rest | **NO** — 0091 hand-authored prose. id 22 *has* Knowledge (deities + founding history) but its Sources (Wikipedia 24, tesshow 25, and — pending — the P4 government `dentou-hasshin` source) support **founding history + deity identity only**. P4 explicitly established: government Source corroborates *founding history only*; **deity / history / 「地域の氏神」 character does not justify a benefit label**. No Source states 家内安全 as this shrine's ご利益. | **UNKNOWN** — reviewed Sources address identity/history, not a benefit claim (contract §3: history ≠ Recommendation eligibility) | **REMOVE_CANDIDATE** |
| *(地域安泰)* | 0091 intended; absent from master | ✗ | — | — | — | N/A | **N/A** — Local-only |
| raw `goriyaku` prose | 0091 hand-authored | — | — | — | — | N/A | **N/A** — `LEGACY_EXISTING` Reason/display copy |

**No tag on either shrine reaches `KEEP_CANDIDATE` (canonical + explicit reviewed Source) or `NORMALIZE_CANDIDATE` (evidence supports the concept, representation inconsistent).** All Recommendation tags are `REMOVE_CANDIDATE` (canonical, Need-wired, runtime effect — but present solely due to 0091 LEGACY reason-fill, with no explicit Source evidence).

## 11. id 21 classification

- **Identity**: 長太稲荷神社, an 稲荷社 (Inari shrine), 世田谷区上祖師谷; catalog row (pk 21, `place_ref` NULL); shadow = pk 103. Fresh-read — **NORMALIZED_MATCH** to reference (Section 5). Not assumed from historical docs.
- **`goriyaku` form**: **PROSE** (single sentence, no delimiter), not delimited canonical labels.
- **M2M origin**: **hand-set by migration 0091** from `["商売繁盛","五穀豊穣","地域安泰"]`; Production attached {4 商売繁盛, 5 五穀豊穣} (地域安泰 dropped — not in master). **Not parse-derived.**
- **Source evidence**: **none** — 0 deity, 0 history, 0 source. Genuine zero-Knowledge.
- **Part of the known prose exception from the full audit**: **YES** — PR #2614 (`shrine-evidence-integrity-full-audit.md`) classifies id 21 as `MISSING` (zero Knowledge + zero Source) and one of the 2 `PROSE`-goriyaku shrines; PR #2611 §12/§17 flags it as genuine Zero-Knowledge (`P8` identity context).
- **Tag classes**: 商売繁盛 → `REMOVE_CANDIDATE`; 五穀豊穣 → `REMOVE_CANDIDATE`. Prose → `N/A`.
- **Runtime**: id 21 currently registers a `money` Purpose match via `商売繁盛`(4); `五穀豊穣`(5) also maps to `money` (redundant). Removing both tags removes id 21's only Need match. The prose does not affect scoring (id 21 has tags, so no `_primary_benefit` fallback).

## 12. id 22 classification

- **Identity**: 給田六所神社, 世田谷区給田; catalog row (pk 22, `place_ref` NULL); shadow = pk 101. **NORMALIZED_MATCH** (Section 5).
- **`goriyaku` form**: **PROSE**.
- **M2M origin**: **hand-set by migration 0091** from `["地域安泰","家内安全"]`; Production attached {7 家内安全} (地域安泰 dropped). **Not parse-derived.**
- **Source evidence**: deities + histories exist (`source_confirmed` / `medium`), backed by Wikipedia + tesshow + (pending) the P4 government Source — all supporting **identity / founding history only**. **No benefit Source.**
- **P4 Phase-6 rule applied**: founding-history Source does not justify 家内安全; deity/history does not justify a benefit; 「地域の氏神」 does not justify a Recommendation tag.
- **Tag class**: 家内安全 → `REMOVE_CANDIDATE` (per the Evidence contract, not per 0091's historical intent). Prose → `N/A`.
- **Runtime**: id 22 currently registers `health` + `rest` Purpose matches via `家内安全`(7). Removing it removes those. Prose does not affect scoring (id 22 has a tag).

## 13. Local / Production drift

| Dimension | id 21 | id 22 | Class |
|---|---|---|---|
| identity (name / address) | MATCH | MATCH | **MATCH** |
| `place_ref` (catalog primary) | NULL / NULL | NULL / NULL | **MATCH** |
| shadow row presence | Local: none · Prod: pk 103 exists | Local: none · Prod: pk 101 exists | **EXPECTED_ENVIRONMENT_DRIFT** (local dev DB has no `place_ref` shadow rows — PR #2611) |
| `history_theme` | 守り / 守り | 守り / 守り | **MATCH** |
| `Shrine.goriyaku` (raw prose) | identical | identical | **MATCH** |
| `goriyaku_tags` — **PKs** | Local {13,14,17} · Prod {4,5} | Local {9,14} · Prod {7} | **EXPECTED_ENVIRONMENT_DRIFT** (`DEV_DB_PK_DRIFT` — 46-row local table vs 39-row canonical master; PK numbers differ for the same label) |
| `goriyaku_tags` — **semantic label set** | Local {五穀豊穣, **地域安泰**, 商売繁盛} · Prod {商売繁盛, 五穀豊穣} | Local {家内安全, **地域安泰**} · Prod {家内安全} | **UNEXPECTED_DRIFT (semantic)** — Local carries `地域安泰` on **both** shrines; Production does not. Cause: migration 0091 (`filter(name__in=…)` + `.add()`) attached `地域安泰` only where the label exists — it exists in the drifted Local table (legacy pk 14) but **not** in the Production canonical master, so 0091 silently dropped it in Production (Section 6.7). This is a **`LOCAL_DEV_ONLY` artifact**, confined to the dev DB; it does **not** indicate a Production data problem. |
| ShrineDeity / ShrineHistory (semantic: names, roles, types, titles, `verification_status`, `confidence`) | n/a (both zero) | Local 2d/4h ≡ Prod 2d/4h (same names/roles/types/titles, all `source_confirmed`/`medium`) | **MATCH** (row PKs differ — `EXPECTED`) |
| id 22 founding-history Sources | n/a | Local: `{government, secondary_editorial, local_history}` · Prod: `{secondary_editorial, local_history}` | **EXPECTED_ENVIRONMENT_DRIFT** — migration **0096** (P4) is applied Local, `PENDING_AUTHORIZED_APPLY` in Production. The extra `government` (`dentou-hasshin.bunka.go.jp`) is the intended-but-not-yet-deployed P4 change. |
| migrations 0091/0094/0095/0096 recorded | all applied Local | (Production migration ledger not queried this session — read-only scope limited to data; 0096 not-yet-applied is evident from the absent P4 Source) | **EXPECTED** |

**Semantic materiality:** the only semantic difference is the Local-only `地域安泰` tag (a legacy non-canonical label), which is a known, scoped, dev-DB-only artifact — it does **not** make Local and Production materially differ in a way that blocks P5. The Production canonical state ({商売繁盛,五穀豊穣} on id21, {家内安全} on id22) is the one P5 will reconcile.

## 14. 0096 reverse edge-case result

**`0096_REVERSE_EDGE_CASE = CONFIRMED`** (in code).

`0096.apply_source_backfill` reuses a pre-existing `ShrineKnowledgeSource` when one already matches `url` + `source_type` (`_get_or_create_source`), and `h.sources.add(src)` is a no-op if the relation already exists → **forward is effectively a no-op when the Source row and its target-history relation both pre-exist.** But `0096.revert_source_backfill` then calls `h.sources.remove(src)` **unconditionally** for every target history, and deletes the Source row if it is left unreferenced. Reverse does **not** record whether forward actually created the relation → **reverse would remove a pre-existing (non-0096) relation, and could delete a pre-existing Source row.** (Contrast: `0095` reverts only when the current state exactly matches what its forward wrote; `0090` similarly. `0096`'s reverse lacks that guard.)

**`PRODUCTION_IMPACT = NONE_CURRENTLY`.** The edge case requires a `ShrineKnowledgeSource` with the exact P4 URL (`https://online.bunka.go.jp/heritages/detail/160978` for id 10, `https://www.dentou-hasshin.bunka.go.jp/search/158.html` for id 22) **already related** to the target histories **before** 0096 forward. Production [prod, this session]: id 10 histories carry only sources 13 (`tourism_official`) + 14 (`secondary_editorial`); id 22 founding history carries only 24 (`secondary_editorial`) + 25 (`local_history`). **Neither P4 URL exists in Production.** So on the next authorized apply, 0096 forward genuinely creates the Source + relations, and a later reverse removes exactly those. The edge case would only bite if someone independently added those exact `bunka.go.jp` URLs to id 10 / id 22 **before** 0096 is deployed.

**Recorded as known technical debt.** Not modified in this audit (P5 preflight = audit-only). Follow-up packet: F5.

## 15. Candidate P5 actions (decision packet — no mutation performed)

| Shrine | Stored value | Evidence state | Runtime impact | Candidate action |
|---|---|---|---|---|
| id 21 長太稲荷神社 | `goriyaku` prose (0091, hand-authored); `goriyaku_tags` = {4 商売繁盛, 5 五穀豊穣} (0091 hand-set list, not parse-derived) | **UNKNOWN** for every tag — id 21 has 0 Knowledge / 0 Source; no reviewed Source states any benefit; prose is `LEGACY_EXISTING` Reason copy | M2M drives a `money` Purpose match (via 商売繁盛; 五穀豊穣 also→money, redundant). Raw prose: Shrine Detail display + shadow completeness metric only; **not** scoring (tags present ⇒ no `_primary_benefit` fallback) | **tags {4,5}: REMOVE_CANDIDATE** · **prose: HOLD** (Mother Ship: retain as Reason/display copy, or also clear? id 21 becomes fully Recommendation-inert without the tags — acceptable per contract for a zero-Knowledge shrine, but a product call) |
| id 22 給田六所神社 | `goriyaku` prose (0091); `goriyaku_tags` = {7 家内安全} (0091 hand-set) | **UNKNOWN** — reviewed Sources support identity/founding history only; P4 established no benefit Source; contract §3: history ≠ benefit | M2M drives `health` + `rest` Purpose matches (via 家内安全). Raw prose: display + shadow metric only | **tag {7}: REMOVE_CANDIDATE** · **prose: HOLD** (same product call) |

## 16. Mother Ship decisions required

**`MOTHER_SHIP_DECISION_REQUIRED`** — multiple reasonable choices remain:

1. **Scope of removal per shrine** — remove the Recommendation `goriyaku_tags` M2M only, **or** also clear the `Shrine.goriyaku` prose, **or** also clear `history_theme="守り"` (all three set by 0091 as one LEGACY reason-fill). The prose still feeds Shrine Detail display and (for a 0-tag shrine) the Reason `_primary_benefit` fallback; clearing it removes that display text with no verified replacement.
2. **Post-removal Reason behavior** — with tags removed, id 21 is fully Recommendation-inert (no Need match); id 22 loses `health`/`rest`. Confirm this is the intended contract-correct outcome for zero/weak-Knowledge shrines (parallels `communication = set()` — a candidate takes the C1 NONE branch, `score_need = 0`).
3. **`地域安泰` Local-only artifact** — decide whether the P5 remediation migration should also explicitly `remove` `地域安泰` from id 21 / id 22 so that Local and Production converge (it is currently attached only in the drifted dev DB). This is a Local-cleanliness call, not a Production data issue.
4. **id 22 future benefit review** — if a later official/religious-body Source (P4 follow-up F2 = 東京都神社庁 listing) is found to explicitly state a benefit, `家内安全` could move `REMOVE_CANDIDATE → NORMALIZE_CANDIDATE / KEEP_CANDIDATE`. Decide whether P5 waits for that or proceeds now.
5. **0096 reverse edge case (F5)** — approve a tiny follow-up to make `0096.revert_source_backfill` guard against removing pre-existing relations (record-only state marker, or `0095`-style exact-match check), scheduled before 0096 is applied to Production. `PRODUCTION_IMPACT` is `NONE_CURRENTLY`, so this is not urgent.

## 17. Explicit no-write confirmation

Nothing was written to Production, the local DB, the Google Spreadsheet, `Shrine.goriyaku`, `goriyaku_tags`, `GoriyakuTag`, `ShrineDeity`, `ShrineHistory`, `ShrineKnowledgeSource`, `NEED_TO_GORIYAKU_IDS`, `NEED_TEXT_WEIGHTS`, the Evidence Gate, the interpreter, scoring, ranking, C1, Lead, Reason, Compass, Concierge, or the frontend. **No data migration was created.** All Production access was read-only via the sanctioned bridge (credential value never seen). No shrine other than id 21 and id 22 was analysed as a remediation target. This branch adds **one file**: `docs/audit/p5-id21-id22-current-state-evidence.md`.

## Follow-up packets

| # | Packet |
|---|---|
| F5 | Guard `0096.revert_source_backfill` so it removes only the relations `0096` forward actually added (and deletes the Source row only when forward created it) — before 0096 is applied to Production. `PRODUCTION_IMPACT` currently `NONE`. |
| P5-DATA | The actual `TAG_RECONCILIATION` remediation for id 21 / id 22, gated on the Section 16 Mother Ship decisions. Reversible scoped `RunPython` migration (0090/0095/0096 pattern), identity-guarded (`pk` + `name_jp` + `place_ref IS NULL`), scope = exactly id 21 / id 22, `goriyaku_tags.remove(...)` by canonical name (never `get_or_create`), Local↔Production reproducible (match by canonical label name, not PK — mirrors 0096's identity-based approach given the dev-DB PK drift). |

## STOP / completion

No STOP condition triggered: id 21 / id 22 identity is `NORMALIZED_MATCH` (unambiguous); Local ↔ Production semantic state matches on the dimensions P5 acts on (the only semantic difference — Local-only `地域安泰` — is a scoped, understood dev-DB artifact); the Recommendation runtime path is fully determined (M2M-only for scoring; raw prose = display/fallback); every current tag traces to a canonical id; the Evidence state is established (all `UNKNOWN` / `REMOVE_CANDIDATE`); migration 0091's intent (LEGACY reason-fill) does **not** conflict with the current contract in a way requiring a product-semantics ruling to *classify* (it only requires one to *decide the remediation scope*, Section 16); no new taxonomy term is required. **Audit document only. No data migration, no Production write, no tag/goriyaku/mapping mutation.** PR created. **Not merged.** P5-DATA and F5 are follow-ups; P1 / P2 / P6 / P7 / P8 not started.
