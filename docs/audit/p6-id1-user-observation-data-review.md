# P6 — id1 明治神宮 Stray `user_observation` Data Review

## 1. Executive Summary

The Full Shrine Fact Integrity Audit (`docs/audit/shrine-evidence-integrity-full-audit.md`
§9.4, remediation packet P6 `DATA_REVIEW`) flagged one suspicious Knowledge
record on canonical Shrine **id 1 (明治神宮 / Meiji Jingū)**. This audit
confirms and fully characterises it.

- The record is a **`ShrineKnowledgeSource`** (not a "Fact" — `user_observation`
  is a `ShrineKnowledgeSource.source_type` choice, not a `ShrineDeity` /
  `ShrineHistory` type). Production pk **2**, local dev pk **999004** (PK drift).
- `source_type = user_observation`, `title = テスト神社 境内案内板`
  ("Test Shrine — precincts signboard"), `publisher = テスト神社`,
  `url = ""` (none), `bibliography = テスト神社境内案内板（2026-08-01現地確認）`,
  `verification_status = source_confirmed`, `confidence = medium`.
- **Origin: SEED.** It is `src-999004` in
  `backend/temples/data/knowledge_seeds/batch_1_7_seed.json`, referenced by
  exactly the two 明治神宮 deities (`明治天皇`, `昭憲皇太后`) alongside the
  genuine `src-999005` (明治神宮 official site). Imported to Production
  2026-08-10 by `import_shrine_knowledge` (seed commit `b6a17f90`,
  2026-08-10). Never edited since (`created_at == updated_at`).
- **Semantics: TEST_ARTIFACT.** "テスト神社" is a fabricated placeholder; it
  does not describe 明治神宮 or any real shrine. It is not one of the QA
  *fixture Shrine* rows (`テスト…`, e.g. Production Shrine id 102) — it is a
  fabricated *Source* that shipped inside a real-shrine seed block.
- **Blast radius: ISOLATED.** It is the **only** `user_observation` Source in
  Production (1 of 114 Sources). It touches **1 shrine**, **2 deity Facts**.
  A full sweep of every Source title/note/bibliography and every
  ShrineHistory/ShrineDeity text field for `テスト` / `test` / `ダミー` /
  `dummy` / `サンプル` / `sample` / `境内案内板` returned **nothing else**.
- **Runtime impact of removing it: NONE.** No scoring / ranking / candidate
  eligibility / Need match / Lead / Reason / Concierge / Compass path reads
  `ShrineKnowledgeSource` or `ShrineDeity.sources`. The Recommendation
  Knowledge payload for a deity is `{display_name, sort_order, confidence}`
  only — Source type/title never reach it. Both 明治神宮 deities remain
  Evidence-Gate `usable` via the real `src-999005`, so Reason text and
  confidence labels are byte-identical after removal.
- **Display / audit impact of removing it: small and beneficial.** Shrine
  Detail API stops emitting a citation titled "テスト神社 境内案内板" under
  明治神宮's two enshrined-deity Facts; the Knowledge coverage report loses a
  spurious `source_type_distribution: {user_observation: 1}` entry and
  `total_source_count` / `verified_source_count` drop by 1. **No shrine's
  coverage / fact-ready classification changes.**
- **Integrity classification (audit conclusion): `UNSUPPORTED`.**
  **Recommended data action (audit conclusion): `REMOVE_CANDIDATE`.** The
  disposition of the target Source, the removal scope, the delivery mechanism,
  and the seed fix are **Mother Ship decisions and remain pending** — see §16.
- **`RECOMMENDED_IMPLEMENTATION` (candidate, not a final decision), for P6-DATA
  only:** a scoped, reversible `RunPython` data migration (`0098`),
  identity-guarded, matching by semantic identity never by Source pk, removing
  the 2 M2M links and deleting the Source only when unreferenced, paired with
  removing `src-999004` from `batch_1_7_seed.json` so a future re-import cannot
  reintroduce it.

## 2. Baseline

| Field | Value |
|---|---|
| Task | P6 `DATA_REVIEW` — audit + decision packet for the stray `user_observation` record on canonical Shrine id 1. **Audit-only.** No data deleted or mutated. Does not continue to P8. |
| Repository | `~/Developer/jinja_app` (control); isolated worktree `~/Developer/jinja_app-p6`. |
| Branch | `audit/p6-id1-user-observation-data-review` |
| Base | `origin/develop` @ `92004df5c35a3872f66d81362d2bdfada77a3095` (verified fresh — matches the expected post-#2625 baseline; PR #2623 / #2624 / #2625 all merged). Working tree clean; no unrelated local files touched. |
| Date | 2026-08-30 |
| Production read | sanctioned read-only credential bridge (`scripts/migration_safety/readonly_query.sh` + repo-external `~/.config/kami-musubi/production-db.env`); every statement passed `guard.py` `is_readonly_sql`; credential value never printed / logged / in argv. **No Production write.** |

## 3. Production Fresh Read

Read-only, 2026-08-30. Production `django_migrations` latest `temples` =
`0094_fix_shrine_70_coordinates` (2026-08-23); 0095–0098 unapplied.

Global Knowledge counts:

| Metric | Value |
|---|---|
| `ShrineKnowledgeSource` total | 114 |
| …of `source_type = user_observation` | **1** (pk 2) |
| …`user_observation` with `verification_status ∈ {source_confirmed, reviewed}` | 1 |
| `ShrineHistory` total / `ShrineDeity` total | 195 / 245 |
| shrines with ≥1 history / ≥1 deity | 87 / 89 |
| orphan `user_observation` Sources (cited by nothing) | 0 |

## 4. Shrine Identity

| Field | Production value |
|---|---|
| pk | 1 |
| `kind` | shrine |
| `name_jp` | 明治神宮 |
| `name_romaji` | (empty) |
| `address` | 東京都渋谷区代々木神園町1-1 |
| `latitude` / `longitude` | 35.6764 / 139.6993 |
| `place_ref_id` | **NULL** (catalog row, not a map-resolve shadow) |
| `history_theme` | (empty) |
| `created_at` / `updated_at` | 2026-06-11 05:49:01 / 2026-06-11 05:49:01 |

**Identity guard — PASS.** pk 1 + `name_jp = 明治神宮` + address
`東京都渋谷区代々木神園町1-1` + coordinates in Yoyogi + `place_ref_id IS NULL`
all agree, and `docs/audit/shrine-evidence-integrity-full-audit.md` lists
"id 1 明治神宮" as one of the 103 canonical Production identities. This is the
real flagship Meiji Jingū. It is **not** a QA fixture — the
`exclude_qa_fixture_shrines` name conventions (`テスト…`, `test…`, `承認テスト`,
`検証`, `住所なし神社`, …) do not match it. The only `テスト`-named Production
Shrine is **id 102 `テスト確認神社 20260611`** (`東京テスト`), which has **no**
Knowledge Facts and is unrelated to this record.

## 5. Target Record

It is a **`ShrineKnowledgeSource`**, not a Fact row. (The remediation packet's
phrase "user_observation Knowledge Fact / fact_type" is loose wording; the
schema has no `fact_type` and no `user_observation` Fact — `user_observation`
is one of the ten `ShrineKnowledgeSource.SOURCE_TYPE_CHOICES`, `models.py:444`.)

| Field | Value |
|---|---|
| pk (Production) | **2** |
| pk (local dev `jinja_db`) | **999004** — PK drift; match by semantic identity, never pk |
| `source_type` | `user_observation` |
| `title` | `テスト神社 境内案内板` |
| `publisher` | `テスト神社` |
| `url` | `""` (none) |
| `bibliography` | `テスト神社境内案内板（2026-08-01現地確認）` |
| `accessed_at` | NULL |
| `verified_at` | 2026-08-01 07:30:00+00 |
| `verification_status` | `source_confirmed` |
| `confidence` | `medium` |
| `language` | `ja` |
| `note` | `""` |
| `created_at` / `updated_at` | 2026-08-10 07:16:40 / 2026-08-10 07:16:40 (identical → never modified post-import) |
| AI / generated metadata | none (no such field on the model; `note` empty) |

**Related Facts** (via `temples_shrinedeity_sources`):

| Fact | pk (prod) | shrine | `verification_status` / `confidence` | its Sources |
|---|---|---|---|---|
| `ShrineDeity` 明治天皇 (role `enshrined`, sort 0) | 1 | id 1 明治神宮 | source_confirmed / high | **{1 `shrine_official` (明治神宮 公式サイト「明治神宮とは」, `source_confirmed`), 2 `user_observation` (target)}** |
| `ShrineDeity` 昭憲皇太后 (role `enshrined`, sort 1) | 2 | id 1 明治神宮 | source_confirmed / high | **{1 `shrine_official`, 2 `user_observation` (target)}** |

No `ShrineHistory` cites the target. id 1's single history — `official_origin`
"明治神宮の創建" (pk 1) — cites only Source 1 (`shrine_official`).
Reverse trace: the target Source is cited by **exactly these two deity Facts**,
both on Shrine id 1; it is not an orphan.

**Related Source rows:** the target Source has no child rows; the sibling
real Source it stands next to is pk 1 `shrine_official`
`https://www.meijijingu.or.jp/about/` (`source_confirmed`).

## 6. Origin Trace

**Classification: `SEED`.**

- `grep` for `境内案内板` / `テスト神社 境内` / `user_observation` across the
  repo resolves to one data location:
  `backend/temples/data/knowledge_seeds/batch_1_7_seed.json`.
- In that seed it is source key **`src-999004`**, with field values
  byte-identical to the Production row (title, publisher, empty url,
  bibliography, `verified_at`, `source_confirmed`, `medium`, `ja`).
- It is listed among 59 seed Sources (between real official Sources) and is
  referenced by **`source_keys: ["src-999005", "src-999004"]`** on the two
  明治神宮 deity blocks (`明治天皇`, `昭憲皇太后`) — and by nothing else in the
  41-shrine seed.
- The seed file has a single commit in its history: **`b6a17f90`**
  "Knowledge DataのProduction投入基盤と再現可能なimport手順を実装"
  (2026-08-10 11:15:50 +0900). Production Source pk 2 `created_at` is
  2026-08-10 07:16:40 UTC (16:16 JST) — a `import_shrine_knowledge
  batch_1_7_seed.json` run the same day.
- No migration, fixture (`fixtures/`), management command, test, admin action,
  or external import script defines or would recreate this content. It is not
  a `TEST_ARTIFACT` in the pytest sense (no test references it); it is a
  fabricated placeholder Source authored directly into the seed JSON.

Importer behaviour (`import_shrine_knowledge` + `services/knowledge_seed.py`),
relevant to remediation:

- URL-less Sources are de-duplicated by `source_type + title + url="" [+
  bibliography]` (`resolve_source_identity`). Re-importing `batch_1_7_seed.json`
  after the row is deleted would **re-CREATE** the Source (fresh pk).
- Deities are matched by `shrine + display_name`; an existing deity is
  `SKIP_EXISTS` — the importer never re-runs `.sources.set()` on it. So once
  the M2M link is removed on Production, **a re-import will not restore the
  link** (it would only leave a new orphan Source row).
- ⇒ A complete fix pairs the Production data removal with deleting
  `src-999004` (and its two `source_keys` entries) from the seed JSON.

## 7. Runtime Usage

`source_type` is referenced in runtime code only as a **display / metadata**
field; nothing special-cases `user_observation`, and nothing filters Sources by
type. Evidence Gate keys on `verification_status` alone.

| Path | Reads `ShrineKnowledgeSource` / `*.sources`? | Classification |
|---|---|---|
| Recommendation candidate selection (`concierge_chat_candidates.build_chat_candidates`) | candidate pool = `Shrine` + `goriyaku_tags` + `exclude_qa_fixture_shrines` + geo; then **attaches** `knowledge_deities` / `knowledge_histories` via `shrine_knowledge_selector` | `NOT_USED` for eligibility; Knowledge is attached but not gating |
| `score_need` / C1 / `matched_all` / ranking / Need match | `goriyaku_tags` (GID) only | `NOT_USED` |
| Lead selection | derived from score/rank | `NOT_USED` |
| Reason generation (`concierge_chat._build_reason` et al.) | uses the Knowledge **payload** — `knowledge_deities[*].display_name` / `.confidence`, `knowledge_histories[*].content` / `.confidence` / `.history_type` | `USED` (payload only — see below) |
| `shrine_knowledge_selector.fetch_fact_ready_knowledge_{deities,histories}` | prefetches only fact-ready Sources, calls `evidence_gate.decide_fact_usability`, then emits `{display_name, sort_order, confidence}` (deity) / `{history_type, title, content, period_text, sort_order, confidence}` (history) | Source used **only** as the boolean "≥1 fact-ready Source?" — type/title/url never emitted |
| Evidence Gate (`evidence_gate.decide_fact_usability` / `decide_detail_display_state`) | consumes `source_verification_statuses` | `USED` (status only; not `source_type`, not `url`, not `confidence`) |
| Shrine Detail API (`ShrineDeitySerializer` / `ShrineHistorySerializer` `get_sources` → `_fact_ready_sources`) | serialises each fact-ready Source incl. `source_type`, `title`, `url` | `DISPLAY_ONLY` |
| Knowledge coverage report (`knowledge_coverage_report` service + command) | counts Sources; `source_type_distribution`, `total_source_count`, `verified_source_count`, per-shrine source counts | `AUDIT_ONLY` |
| Deep Dive (`deep_dive_retrieval`, `api/serializers/deep_dive`, `api/views/deep_dive`) | surfaces Sources incl. `source_type` | `DISPLAY_ONLY` (feature in Observation Phase) |
| Concierge input / Compass | no Knowledge-Source read | `NOT_USED` |
| Admin (`temples/admin.py`) | `list_filter` / `list_display` on `source_type` | `ADMIN_ONLY` |
| `shrine_meaning_composer` | builds meaning from `goriyaku` / tags; no Source read | `NOT_USED` |

**Net:** the target Source influences runtime **only** as one of two
`source_verification_statuses` inputs to `decide_fact_usability` for deities 1
and 2. Because each of those deities **also** cites Source 1
(`shrine_official`, `source_confirmed`), removing the target leaves ≥1
fact-ready Source → `usable` stays `True` → the Knowledge payload
(`display_name`, `confidence`) is unchanged → Reason text and confidence
labels are unchanged.

## 8. Evidence Gate

| Question | Answer |
|---|---|
| 1. Is `user_observation` a valid Fact type in the schema? | **No — it is not a Fact type.** It is a valid `ShrineKnowledgeSource.source_type` choice (`models.py:444`). Facts are `ShrineDeity` (`role`) / `ShrineHistory` (`history_type`). |
| 2. Can it become a fact-ready Fact? | N/A (not a Fact). As a **Source**, `verification_status ∈ {source_confirmed, reviewed}` makes it a "fact-ready Source" (`evidence_gate.FACT_READY_VERIFICATION_STATUSES`). The target row is `source_confirmed` → it **is** a fact-ready Source. |
| 3. Does it require a Source? | N/A. As a Source, `ShrineKnowledgeSource.clean()` requires `verified_at` when status ∈ {source_confirmed, reviewed}; the row has `verified_at = 2026-08-01` so it passes `clean()`. **No `url` is required** (`URLField(blank=True)`). |
| 4. Can it participate in Recommendation Evidence? | Yes, structurally: a fact-ready `user_observation` Source satisfies a Fact's "≥1 fact-ready Source" requirement exactly like any other type — `source_type` is never checked by the gate. (The separate *Recommendation Evidence Review Contract* for `goriyaku` labels concerns `Shrine.goriyaku_tags`, not Knowledge Sources.) |
| 5. Can a URL-less `user_observation` Source still count as usable evidence? | **Yes.** The gate inspects `verification_status` only — never `url` or `source_type`. A URL-less `user_observation` / `source_confirmed` row fully satisfies the Source side of `decide_fact_usability`. This is why the artifact is easy to miss. |
| 6. Does the target row currently pass or fail the Evidence Gate? | A Source in isolation has no pass/fail. Its **effect**: it is a fact-ready Source and contributes to deities 1 & 2 being `usable` — but **redundantly**, since Source 1 (`shrine_official`) already satisfies the gate. Not load-bearing. |
| 7. Does its presence affect Knowledge coverage metrics? | Yes, numerically: `source_type_distribution` carries `user_observation: 1`; `total_source_count` / `verified_source_count` each include it; per-shrine source count for id 1 is +1. **No coverage classification** (knowledge / deity / history / fact-ready / zero-knowledge) for any shrine depends on it. |

The Evidence Gate is **not** modified by this task.

## 9. Semantic Review

Content: `title = テスト神社 境内案内板`, `publisher = テスト神社`,
`bibliography = テスト神社境内案内板（2026-08-01現地確認）`.

- `テスト神社` = literally "Test Shrine". `境内案内板` = "precincts information
  board". The record claims to be an on-site observation of a signboard at a
  shrine named "Test Shrine".
- It does **not** describe canonical id 1 (明治神宮): the publisher is
  "テスト神社", not "明治神宮"; no URL; the sibling real Source for the same
  Facts is the 明治神宮 official site. Prior audit
  (`deep-dive-production-runtime-readiness.md` §3.1) independently noted it
  "神社名と矛盾する" ("contradicts the shrine name").
- It does **not** describe another real shrine — there is no "テスト神社" real
  shrine; the only `テスト`-named Production Shrine (id 102
  `テスト確認神社 20260611`) is itself a QA fixture and is unrelated.
- It is a **fabricated placeholder Source** authored into `batch_1_7_seed.json`
  (`src-999004`) and imported alongside genuine data.

**Verdict: TEST_ARTIFACT / QA placeholder.** Not a real-world citation; does
not establish anything about 明治神宮 or any real shrine.

## 10. Contamination Search

Production sweeps (read-only, 2026-08-30):

| Sweep | Result |
|---|---|
| `ShrineKnowledgeSource` where `source_type = user_observation` | **1 row** — pk 2 (the target) |
| `ShrineKnowledgeSource` where `title`/`note`/`bibliography` ILIKE `%テスト%` / `%test%` / `%ダミー%` / `%dummy%` / `%サンプル%` / `%sample%` / `%境内案内板%` | **1 row** — pk 2 (the target); nothing else |
| `ShrineHistory` where `title`/`content` matches the same test-like patterns (incl. `%テスト神社%`) | **0 rows** |
| `ShrineDeity` where `display_name`/`canonical_name` matches the same patterns | **0 rows** |
| orphan `user_observation` Sources | **0** |
| every Fact citing any `user_observation` Source | 2 — `ShrineDeity` pk 1 & 2, both Shrine id 1 明治神宮 |
| `Shrine` rows named `テスト…` / `test…` | 1 — id 102 `テスト確認神社 20260611` (QA fixture Shrine; **no Knowledge Facts**) |

**Blast radius:**

| Dimension | Count |
|---|---|
| total `user_observation` Facts (= Sources) | 1 |
| shrines affected | 1 (id 1 明治神宮) |
| Fact links affected | 2 (deities `明治天皇`, `昭憲皇太后`) |
| source-backed | the Source has no URL; each affected Fact **also** has 1 real `shrine_official` Source |
| source-less | 0 affected Facts lose fact-readiness |
| fact-ready count | Source is `source_confirmed`; both affected Facts are fact-ready & `usable` **independently** of it |
| Evidence-Gate-usable Facts touched | 2 (remain usable after removal) |
| suspicious test-like rows elsewhere | **0** |

Exact rows requiring review: **`ShrineKnowledgeSource` (prod pk 2 / local pk
999004)** and its two `temples_shrinedeity_sources` links to `ShrineDeity`
`明治天皇` and `昭憲皇太后` on Shrine id 1. Nothing else.

**`P6_CONTAMINATION_SCOPE = ISOLATED`.**

## 11. Integrity Classification

**Integrity dimension: `UNSUPPORTED`.** The record presents itself as a
verified real-world citation (`source_confirmed`, `現地確認`) but is a
fabricated test placeholder — no URL, publisher "テスト神社", no correspondence
to 明治神宮 or any real shrine, authored into the seed as `src-999004`. It
supplies no genuine evidentiary support to the Facts it is attached to.
(Not `REVIEW_REQUIRED`: the seed + semantic + provenance evidence is
conclusive. Not `MISSING`: the row exists. Not `PARTIAL` / `MATCH`: it
corroborates nothing real.)

**Recommended Data Action: `REMOVE_CANDIDATE`.** (Audit-only task — no
deletion performed.) Evidence: `SEED` origin, `TEST_ARTIFACT` semantics, zero
runtime dependency, redundant to the real `shrine_official` Source, `ISOLATED`
blast radius, and it currently produces a visible display defect on a flagship
shrine (Section 12/13).

## 12. Recommendation Impact

**SCORING IMPACT — `NONE`.** If the target Source (and its 2 links) were
removed:

| Path | Change |
|---|---|
| Recommendation candidate eligibility | none — pool = `goriyaku_tags` + `exclude_qa_fixture_shrines` + geo; no Source read |
| `score_need` | none — GID intersection only |
| C1 | none |
| ranking | none |
| Need match | none |
| Lead | none |
| Reason | none — deities 1 & 2 stay `usable` via Source 1, so `knowledge_deities` payload (`display_name`, `confidence`) is unchanged; `knowledge_histories` never referenced the target |
| Concierge result | none |
| Compass result | none |

## 13. Display / Knowledge Impact

**DISPLAY / KNOWLEDGE IMPACT — small, beneficial:**

| Surface | Change on removal |
|---|---|
| Shrine Detail API (`/shrines/1`) | under deities `明治天皇` and `昭憲皇太后`, the `sources` array drops the entry `{source_type: "user_observation", title: "テスト神社 境内案内板", url: ""}` (2 → 1 each). Deity **display state stays `full`**. Net effect: an embarrassing bogus citation stops being served on Meiji Jingū's page. |
| Deep Dive Source lists | same Source no longer surfaced (feature in Observation Phase; no functional change) |
| Knowledge coverage report | `source_type_distribution` loses `user_observation: 1`; `total_source_count` 114 → 113; `verified_source_count` −1; `source_count_distribution` for id 1 shifts one bucket. **`knowledge_coverage`, `deity_coverage`, `history_coverage`, `both_deity_and_history_coverage`, `fact_ready_*`, `zero_knowledge` — all unchanged** (id 1 still has deity + history + Source 1). |
| Admin | one fewer `user_observation` row in the Source list filter |

**`P6_RECOMMENDATION_IMPACT = NONE`. `P6_KNOWLEDGE_COVERAGE_IMPACT =
YES_NON_MATERIAL`** (audit-report metrics only: `total_source_count` /
`verified_source_count` −1, `source_type_distribution` drops
`user_observation:1`; **zero** change to any shrine's coverage
classification).

## 14. Proposed Remediation

> **Superseded by §18.4.** This section is the pre-implementation proposal. The
> delivered migration uses a stricter **`P6_0098_PRESTATE_POLICY = FAIL_CLOSED`**
> contract: the "safe no-op" / "idempotent after deletion" framing below is
> **withdrawn** — once `Shrine` pk 1 exists, an unexpected pre-state raises and
> aborts instead of silently no-opping. See §18.4–§18.6 for the contract that
> was actually built.

**Not implemented in this task.** For P6-DATA:

### Delivery mechanism — comparison

| Option | Assessment |
|---|---|
| **A. scoped reversible `RunPython` data migration** | Matches repo convention (0090 / 0091 / 0094 / 0095 / 0096 / 0097 are all scoped, identity-guarded, idempotent, reversible `RunPython`). Version-pinned, CI-tested, reviewable, lands through the same authorized `migrate` path as the pending 0095–0097, recorded in `django_migrations`. Reverse re-creates the exact seed row + links. **Recommended.** |
| B. management command | One-off, not version-pinned, no automatic reverse, no ledger record, easy to misrun. Repo commands are for repeatable ingestion (`import_shrine_knowledge`), not one-shot deletions. Rejected. |
| C. manual Production deletion | No identity guard, no test, no reverse, no audit trail; contradicts the `scripts/migration_safety` "no ad-hoc Production writes" posture. Rejected. |

### `RECOMMENDED_IMPLEMENTATION` — candidate design, not a `FINAL_DECISION`

This section is the audit's engineering recommendation for *how* a removal
would be built **if** the Mother Ship decides to remove (§16). It is not a
decision and nothing here is implemented in this task.

Next migration number after `0097` → **`0098`** (confirm against `develop` at
implementation time; do not hard-code).

- **Shrine identity guard:** `Shrine` matched by `pk=1` **AND**
  `name_jp="明治神宮"` **AND** `place_ref_id IS NULL`; any mismatch ⇒ whole
  migration is a no-op. `.only(...)` excludes `location` (the 0091/0094 legacy
  `text`-column GEOSException guard).
- **Source identity — never by pk** (Production pk 2 vs local pk 999004).
  Match `ShrineKnowledgeSource` by **`source_type="user_observation"` AND
  `title="テスト神社 境内案内板"` AND `url=""` AND
  `bibliography="テスト神社境内案内板（2026-08-01現地確認）"`** (and assert
  `publisher="テスト神社"`). If 0 rows or >1 rows match ⇒ no-op (log).
- **Fact identity:** the two `ShrineDeity` rows matched by `shrine_id=1` +
  `display_name IN ("明治天皇","昭憲皇太后")`; only act on links that
  currently exist.
- **Forward:** `deity.sources.remove(target)` for each of the two deities;
  then `target.delete()` **iff** `not target.deities.exists() and not
  target.histories.exists()` (guards against an unrelated Fact having been
  attached in the meantime).
- **Reverse:** `get_or_create` the Source with the exact seed field values
  (`source_confirmed`, `medium`, `ja`, `verified_at=2026-08-01T07:30:00+00:00`)
  and re-add it to the two deities — mirroring 0096's reversibility contract.
- **Idempotent:** re-running forward after it has run is a no-op (0 matches /
  links already gone).
- **Removal-scope candidate options** (the target *is* a Source, so the scope
  is expressed in Source terms — Mother Ship selects one, see §16):
  - `SOURCE_AND_RELATIONS` — remove the 2 `ShrineDeity ↔ Source` M2M links
    **and** delete the now-orphan `ShrineKnowledgeSource` row. *(This is the
    scope the candidate design above is written for; an orphan test Source
    carries no provenance value.)*
  - `RELATIONS_ONLY` — remove the 2 M2M links, **retain** the Source row
    (conservative; leaves an orphan row that still shows in
    `source_type_distribution`).
  - `KEEP` — take no action (record the finding only).

### Companion seed fix (same P6-DATA PR, or an explicitly linked one)

Remove `src-999004` from `backend/temples/data/knowledge_seeds/batch_1_7_seed.json`
and delete `"src-999004"` from both 明治神宮 deity `source_keys`
(`["src-999005", "src-999004"]` → `["src-999005"]`). Without this, a future
`import_shrine_knowledge batch_1_7_seed.json` re-creates the Source as an
orphan row (it would **not** re-link it to the SKIP_EXISTS deities, but the
stray row would reappear in coverage metrics).

## 15. Future Regression Contract

A P6-DATA implementation must add tests asserting:

1. **exact target removed** — after forward, no `ShrineKnowledgeSource` with
   `source_type="user_observation"` + `title="テスト神社 境内案内板"` +
   `url=""` remains, and neither 明治神宮 deity cites it.
2. **unrelated id 1 Facts preserved** — `ShrineDeity` `明治天皇` / `昭憲皇太后`
   rows still exist, still `source_confirmed` / `high`, still cite Source 1
   (`shrine_official`); `ShrineHistory` "明治神宮の創建" untouched.
3. **other shrines' Facts preserved** — a spot-check shrine (e.g. 伏見稲荷大社)
   Deity/History/Source counts unchanged.
4. **wrong shrine identity = no-op** — if `Shrine` pk 1 is renamed / carries a
   `place_ref`, forward makes no change.
5. **Source identity mismatch = no-op** — a `user_observation` row with a
   different `title` or a non-empty `url` is not touched; >1 match ⇒ no-op.
6. **reverse restores the exact row** — after forward→reverse, the Source
   exists again with all seed field values and both deity links restored.
7. **no Source row accidentally deleted** — Source 1 (`shrine_official`) and
   every other Source row count unchanged; the target is deleted **only** when
   it has no remaining deity/history references.
8. **Recommendation behaviour unchanged** — `fetch_fact_ready_knowledge_deities([1])`
   returns the same `{display_name, confidence}` payload before and after
   (both deities remain `usable`); a candidate-build / Reason snapshot for
   明治神宮 is byte-identical.
9. **Evidence Gate unchanged** — `decide_fact_usability` for deities 1 & 2 is
   `usable=True` before and after.
10. **Knowledge coverage delta is exactly as expected** — `total_source_count`
    / `verified_source_count` −1; `source_type_distribution` loses the
    `user_observation` key; `knowledge_coverage` / `deity_coverage` /
    `history_coverage` / `fact_ready_*` / `zero_knowledge` counts **unchanged**.
11. **idempotent forward** (run ×3) and **forward→reverse→forward** cycle
    deterministic.
12. **PK-drift safety** — a test that builds the Source at a non-canonical pk
    (e.g. 999004) still has forward match and remove it (name/field-based).

## 16. Mother Ship Decision Packet

The three categories below are kept strictly separate. Only the first is a set
of audit conclusions; nothing in it authorises a change.

### 16.1 Established findings (audit conclusions — technically verified)

```text
P6_INTEGRITY_CLASSIFICATION  = UNSUPPORTED
P6_RECOMMENDED_DATA_ACTION   = REMOVE_CANDIDATE
P6_RECOMMENDATION_IMPACT     = NONE
P6_KNOWLEDGE_COVERAGE_IMPACT = YES_NON_MATERIAL   (audit report only: total_source_count / verified_source_count -1; source_type_distribution drops user_observation:1; NO shrine coverage classification changes)
P6_CONTAMINATION_SCOPE       = ISOLATED           (1 ShrineKnowledgeSource row, 1 shrine id 1, 2 ShrineDeity M2M links; full sweep found nothing else)
```

### 16.2 `RECOMMENDED_IMPLEMENTATION` (engineering recommendation — NOT a `FINAL_DECISION`)

Applicable only if 16.3 resolves to a removal. Detailed in §14:

- scoped **reversible `RunPython`** data migration (`0098`; number +
  `dependencies` confirmed against `develop` at implementation time), CI-tested
  — **not** a management command, **not** a manual Production deletion;
- **semantic identity matching, never the Source pk** — on
  `source_type` / `title` / `url=""` / `bibliography` (Production pk 2 vs
  local pk 999004);
- Shrine guard `pk=1 AND name_jp="明治神宮" AND place_ref_id IS NULL`; deities
  matched by `shrine_id=1` + `display_name`;
- forward removes the **2 `ShrineDeity ↔ Source` M2M links**, then deletes the
  Source row **only when it is unreferenced** by any deity/history; reverse
  recreates the seed row and re-links both deities;
- **companion seed cleanup**: remove `src-999004` (and its two `source_keys`
  entries) from `backend/temples/data/knowledge_seeds/batch_1_7_seed.json` to
  prevent re-import from reintroducing an orphan row;
- the 12-point regression contract in §15.

### 16.3 Mother Ship decisions — PENDING (governance judgment, not technical facts)

```text
P6_TARGET_SOURCE_STATUS = PENDING_MOTHER_SHIP
P6_REMOVAL_SCOPE        = PENDING_MOTHER_SHIP
P6_DELIVERY             = PENDING_MOTHER_SHIP
P6_SEED_FIX             = PENDING_MOTHER_SHIP
```

| Field | Candidate options | Audit's recommendation (non-binding) |
|---|---|---|
| `P6_TARGET_SOURCE_STATUS` | `REMOVE` / `KEEP` | `REMOVE` — harmless to Recommendation, but served as a bogus citation on 明治神宮's Shrine Detail page; origin is a fabricated seed placeholder |
| `P6_REMOVAL_SCOPE` | `SOURCE_AND_RELATIONS` / `RELATIONS_ONLY` / `KEEP` | `SOURCE_AND_RELATIONS` — the orphan test Source has no provenance value |
| `P6_DELIVERY` | `REVERSIBLE_DATA_MIGRATION` / `MANAGEMENT_COMMAND` / `MANUAL` / `N_A` | `REVERSIBLE_DATA_MIGRATION` (scoped `RunPython` `0098`) — matches repo convention 0090–0097 |
| `P6_SEED_FIX` | `BUNDLED_WITH_MIGRATION_PR` / `SEPARATE_LINKED_PR` / `NONE` | `BUNDLED_WITH_MIGRATION_PR` — otherwise a later `import_shrine_knowledge` re-creates the orphan row |

Additional pending item: **sequencing** relative to the still-unapplied
0095–0097 — the `0098` number and `dependencies` must be finalised against
`develop` at P6-DATA implementation time.

## 17. STOP

This is an audit / decision packet only.

- **No** Fact, Source, or M2M row was deleted or modified. **No** Production
  write (read-only ledger + inspection queries only, every statement
  `guard.py`-checked; credential never exposed). **No** Spreadsheet access.
- **No** migration created; **no** application code, Evidence Gate, Knowledge
  model, taxonomy, `goriyaku`, mapping, Recommendation, frontend, or mobile
  change. This PR is **docs-only** (`docs/audit/p6-id1-user-observation-data-review.md`).
- Baseline confirmed: `origin/develop` @ `92004df5c35a3872f66d81362d2bdfada77a3095`.
- **Does not** implement P6-DATA. **Does not** continue to P8.

Next step is a Mother Ship decision on §16.3, then a separate P6-DATA PR
implementing §16.2 if a removal is chosen.

## 18. Implementation outcome (P6-DATA)

The audit findings (§1–§15) are unchanged. This section records the
implementation only.

### 18.1 Mother Ship decisions (final, as supplied)

```text
P6_TARGET_SOURCE_STATUS = REMOVE
P6_REMOVAL_SCOPE        = SOURCE_AND_RELATIONS
P6_DELIVERY             = REVERSIBLE_DATA_MIGRATION
P6_SEED_FIX             = BUNDLED_WITH_MIGRATION_PR
```

### 18.2 Delivery

- Branch `fix/p6-remove-stray-user-observation-source` from `origin/develop` @
  `e6aa8d818914e5b5768de7bfa88be782f2894f8d` (post-PR #2627). Isolated
  worktree; working tree otherwise clean.
- **Migration identifier: `temples/migrations/0098_remove_stray_test_source_id1.py`**
  — verified as the next number against `develop` (0090–0097 present);
  `dependencies = [("temples", "0097_p5_id21_id22_tag_reconciliation")]`.
  Scoped reversible `RunPython`, GIS-lineage only (like 0095–0097; no
  `migrations_nogis` counterpart).

### 18.3 Production migration ledger — hard gate (fresh read-only)

Latest applied `temples` migration in Production =
**`0094_fix_shrine_70_coordinates`** (2026-08-23). **`0095`, `0096`, `0097`,
`0098` are all `<NOT APPLIED>`.** So 0098 is a new unapplied migration appended
to the linear chain; on the next authorized Production `migrate` it runs after
0095→0096→0097. No Production write in this task.

### 18.4 Reverse-safety correction — `P6_0098_PRESTATE_POLICY = FAIL_CLOSED`

The first implementation treated "shrine identity mismatch", "zero Source
matches", and ">1 Source matches" as **successful safe no-ops**, and forward as
generally idempotent (a re-run after deletion found 0 matches → no-op). That is
**not** exactly reversible: without persistent migration-owned state, once the
Source row is deleted there is no durable marker distinguishing (A) the Source
was absent before forward from (B) the Source existed and forward deleted it —
so `reverse` on a "Case Z" pre-state (valid shrine, stray Source absent) would
**fabricate** contamination that never existed; and a pre-state with only one
of the two approved relations would have forward remove that one and reverse
add **both**.

**Corrected contract: `P6_0098_PRESTATE_POLICY = FAIL_CLOSED`.** Those claims
are withdrawn. 0098 applies only to the exact audited Production shape:

- **Applicability boundary — the one clean no-op.** If `Shrine` pk 1 does not
  exist at all (a fresh/empty database migrated from scratch, or any database
  without this subject), forward and reverse are both a clean no-op — `migrate`
  on an empty database still succeeds.
- **Once a `Shrine` pk 1 row exists, forward asserts the complete PRE contract
  and raises** `RuntimeError("[temples.0098] PRESTATE_MISMATCH: …")` on any
  deviation, aborting the migration transaction so 0098 is **not** recorded as
  applied. Unexpected state is an error, never repaired or guessed at.
- Therefore, on a database that has `Shrine` pk 1, a **recorded/applied 0098
  implies the exact reversible PRE contract held**.

### 18.5 Forward behaviour

If `Shrine` pk 1 is absent → clean no-op. Otherwise **all** of the following
must hold or forward **raises** before any mutation:

1. the `Shrine` pk 1 row has `name_jp = 明治神宮` and `place_ref_id IS NULL`
   (`.only(...)` excludes `location`);
2. **exactly one** `ShrineKnowledgeSource` matches the full semantic identity
   `source_type=user_observation` + `title=テスト神社 境内案内板` +
   `publisher=テスト神社` + `url=""` +
   `bibliography=テスト神社境内案内板（2026-08-01現地確認）` (never pk —
   Production pk 2, local pk 999004); 0 or >1 → raise;
3. **exactly** the two `ShrineDeity` rows `明治天皇` and `昭憲皇太后` exist on
   `shrine_id = 1` (missing / duplicate / extra → raise);
4. **both** cite the target Source (either relation absent → raise), and the
   target Source is cited by **only** those two relations — no third deity, no
   history (→ raise), so the row is safely deletable and exactly reversible.

Then, and only then: remove the Source from both deities and `src.delete()`
(it is now provably unreferenced). A second forward after a successful apply
finds zero Source matches → **raises** (`PRESTATE_MISMATCH`) — there is no
"idempotent re-run" claim.

### 18.6 Reverse behaviour

Reverse runs only after a forward that applied the remediation or was a clean
no-op. It restores **only** when it can see the audited shape — `Shrine` pk 1 =
明治神宮 / `place_ref_id IS NULL` **and** exactly the two target deities. On any
other database (fresh, partially shaped, or a full temples migration-chain
reversal in tests/tooling) reverse is a **clean no-op** and never fabricates
the stray Source. It raises only on genuine ambiguity (more than one Source
already matches the semantic identity). When it restores: reuse an equivalent
Source row if exactly one is present (never duplicating), else recreate it from
the reviewed seed values (`source_confirmed` / `medium` / `ja` /
`verified_at=2026-08-01T07:30:00+00:00` / no URL); re-link **only** `明治天皇`
and `昭憲皇太后`. Never by pk; never recreates the deities; never touches the
genuine `shrine_official` Source. `forward → reverse` restores the exact
pre-state (only the recreated Source's pk may differ); `forward → reverse →
forward` is deterministic.

### 18.7 Seed cleanup (`BUNDLED_WITH_MIGRATION_PR`)

`backend/temples/data/knowledge_seeds/batch_1_7_seed.json`:

- `src-999004` removed from `sources` (59 → 58 entries; no reference remains
  anywhere in the file).
- Both 明治神宮 deity blocks: `source_keys` `["src-999005", "src-999004"]` →
  `["src-999005"]`.
- The genuine `src-999005` (`shrine_official`,
  `https://www.meijijingu.or.jp/about/`) is untouched.
- Verified: a future `import_shrine_knowledge batch_1_7_seed.json` can no
  longer create the test Source (`test_seed_no_longer_defines_the_test_source`).

### 18.8 Regression

- `test_migration_0098_remove_stray_test_source_id1.py` — **30 tests** for the
  fail-closed contract: applicability boundary (no `Shrine` pk 1 → clean
  no-op, forward + reverse); exact Production-shaped PRE → forward succeeds;
  **forward raises** on — zero Source, zero-Source-with-full-deities, multiple
  Source matches, renamed shrine, `place_ref`-set shrine, bibliography
  mismatch, non-empty-url mismatch, missing 明治天皇, missing 昭憲皇太后,
  duplicate 明治天皇, only-明治天皇 relation, only-昭憲皇太后 relation, neither
  relation, Source also cited by a history; failed forward leaves the DB
  semantically unchanged; second forward after a successful apply raises;
  reverse restores the exact pre-state (Source fields + exactly the two
  links); `forward → reverse → forward` deterministic; reverse reuses an
  existing Source (no duplicate) ×2; genuine `shrine_official` Source
  untouched; unrelated Source/history references untouched; pk-drift
  irrelevant (Source at pk 999004 still matched/removed); Evidence Gate
  usability unchanged; Recommendation Knowledge payload unchanged; scoring
  inputs untouched; Knowledge coverage delta exactly `total_source_count −1` /
  `user_observation 1→0` with no shrine classification change; seed no longer
  defines the test Source.
- Focused regression (0091 GIS / 0095 / 0096 / 0097 / 0098 migration tests,
  Evidence Gate, Shrine Knowledge selector, Knowledge coverage command,
  Shrine Knowledge models + migration): **152 passed** (nogis lineage).
- Full `backend/temples`, fresh test DB, both migration lineages:
  **nogis (CI-equivalent): 1964 passed, 12 skipped, 0 failed**;
  **GIS lineage: 1976 passed, 13 skipped, 0 failed**. Skips are the
  pre-existing GDAL / PostGIS / ambiguous-axis ones, unchanged. A fresh
  `migrate` in the GIS lineage runs 0098 as the applicability-boundary no-op
  (empty `temples_shrine`) and succeeds.
- `python manage.py makemigrations temples --check --dry-run` → "No changes
  detected in app 'temples'" (both lineages).
- `git diff --check` → clean.

### 18.9 Impact (matches the audit)

- **Evidence Gate:** `明治天皇` / `昭憲皇太后` remain `usable` via the genuine
  `shrine_official` Source — unchanged.
- **Recommendation:** `fetch_fact_ready_knowledge_deities([1])` payload
  byte-identical (`display_name`, `confidence`); no scoring / ranking / C1 /
  Lead / Reason / Need-mapping / GoriyakuTag change.
- **Knowledge coverage:** `total_source_count` / `verified_source_count` −1;
  `source_type_distribution` loses `user_observation:1`; **no** shrine's
  coverage classification changes.
- **Shrine Detail API:** 明治神宮's two enshrined-deity Facts stop serving the
  `テスト神社 境内案内板` citation (2 → 1 sources each).

### 18.10 Status

- **Production write status: NONE.** Read-only ledger check only; every
  statement `guard.py`-checked; credential never printed / logged / in argv.
- **Spreadsheet write status: NONE** (not accessed).
- **Deployment status: PENDING** — PR created against `develop`, **not
  merged**. 0098 applies to Production only on the next authorized `migrate`.
- Changed files (this PR): `backend/temples/migrations/0098_remove_stray_test_source_id1.py`
  (new), `backend/temples/tests/test_migration_0098_remove_stray_test_source_id1.py`
  (new), `backend/temples/data/knowledge_seeds/batch_1_7_seed.json` (seed
  cleanup), `docs/audit/p6-id1-user-observation-data-review.md` (this section).
- P8 not started.
