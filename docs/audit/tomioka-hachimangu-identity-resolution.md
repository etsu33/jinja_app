# 富岡八幡宮 Production Identity Resolution

## 1. Audit metadata

| Field | Value |
|---|---|
| Task | Resolve the identity of Production `temples_shrine` rows **id 49** and **id 104** (both `name_jp = 富岡八幡宮`) — the last open `FULL_AUDIT_DENOMINATOR` gate from PR #2612 (`docs/audit/production-canonical-set-preflight.md`) |
| Type | Identity audit. **Read-only.** No Production write, no DB write, no Spreadsheet write, no duplicate cleanup, no migration / seed / model / fixture / Recommendation / GoriyakuTag / Knowledge / frontend / deployment-config change. |
| Branch | `audit/tomioka-hachimangu-identity-resolution` |
| Worktree | `~/Developer/jinja_app-tomioka-hachimangu-identity-resolution` (isolated, from `origin/develop`; control repo untouched) |
| Date | 2026-08-29 |
| Production read | sanctioned read-only path — `scripts/migration_safety/readonly_query.sh` + repo-external `~/.config/kami-musubi/production-db.env` (present on host). Credential value never printed / logged / in argv; every query passed `guard.py check-readonly-sql` (SELECT/SHOW/EXPLAIN/WITH only). SQL kept in an untracked scratch dir. |

### Evidence labels

- **[prod]** — read this session directly from the Production database (read-only credential bridge).
- **[src]** — fetched this session from a public identity source (classified in §10 as `MUNICIPAL_OFFICIAL` or `SUPPLEMENTARY_SOURCE`).
- **[MS]** — stated as verified by the Mother Ship (PR #2612 brief / this task brief).
- **[prior]** — value from an earlier audit; context only. **Current Production read-only evidence wins.**

## 2. Base SHA

- **`origin/develop` @ `9d102b86b29a6653923f45fa6db78e4b54330f68`** — fetched this session; matches the task's stated SHA; `origin/develop` had not advanced.
- Worktree HEAD = same SHA; working tree clean at checkout and at commit time.

## 3. Scope / non-scope

### In scope

A complete read-only snapshot of Production rows 49 and 104 and the PlaceRef linked from 104; address normalization (for comparison only) against a `MUNICIPAL_OFFICIAL` source; geodesic coordinate comparison (provider + supplementary published coordinates — the municipal source carries no coordinate); a `MUNICIPAL_OFFICIAL` identity-only check of 富岡八幡宮; a shadow-generation-pattern comparison against the two confirmed duplicate pairs (101 = 給田六所神社, 103 = 長太稲荷神社); a single identity classification; the resulting `FULL_AUDIT_DENOMINATOR` value; the PR-C entry-gate packet.

### Non-scope (enforced)

Starting PR-C · deleting / merging any Shrine row · duplicate remediation · fixing id 105 `広島市` · re-seeding the local dev DB · auditing deity / history / goriyaku / Recommendation Evidence for either row · any Production / Spreadsheet / DB write. The only committed change is this document.

## 4. Prior ambiguity

PR #2612 §10 classified 富岡八幡宮 {49, 104} as **`AMBIGUOUS_PENDING_IDENTITY_CONFIRMATION`**: same name + same normalized street lot + a zero-data `place_ref` shadow pattern were *suggestive*, but the pair's coordinates differ by ~300 m (unlike the two byte-identical confirmed pairs), the Google Spreadsheet's row id 49 has **no** populated `reference_latitude` / `reference_longitude` / `coordinate_delta_m` / `coordinate_status` [MS], and Spreadsheet row-id 104 is an unrelated QA fixture (`重複検証神社`) — so no Spreadsheet-side row corresponds to the Production shadow. This task obtains the missing piece: an **official real-world address** for 富岡八幡宮 from a `MUNICIPAL_OFFICIAL` source (§10).

> **Spreadsheet row-id ≠ Production row-id.** Spreadsheet id 49 = 富岡八幡宮; Spreadsheet id 104 = an unrelated QA fixture [MS]. No id-equality join between the two namespaces is used anywhere below.

## 5. Production id 49 snapshot

`[prod]`, read-only:

| Field | Value |
|---|---|
| `id` | 49 |
| `kind` | `shrine` |
| `name_jp` | 富岡八幡宮 |
| `name_romaji` | *(empty)* |
| `address` | `東京都江東区富岡1-20-3` |
| `latitude` / `longitude` | **35.6733 / 139.7967** |
| `place_ref_id` | **NULL** |
| `goriyaku` (text) | `勝運・商売繁盛` |
| `sajin` | *(empty)* |
| GoriyakuTag relations | **2** |
| deity facts | **1** |
| history facts | **2** |
| `created_at` | 2026-06-11 05:49:02.627992+00 |
| `updated_at` | 2026-06-11 05:49:02.628411+00 — *never updated after creation* |

(`location` geometry not selected — Production's `temples_shrine.location` is a legacy `text`-typed column per `docs/audit/shrine-70-coordinate-correction.md`; `latitude`/`longitude` are the canonical stored numeric fields.)

**Role:** the **data-bearing primary** row — it holds the goriyaku text, the GoriyakuTag links, and the deity/history knowledge.

## 6. Production id 104 snapshot

`[prod]`, read-only:

| Field | Value |
|---|---|
| `id` | 104 |
| `kind` | `shrine` |
| `name_jp` | 富岡八幡宮 |
| `name_romaji` | *(empty)* |
| `address` | `日本、〒135-0047 東京都江東区富岡１丁目２０−３` |
| `latitude` / `longitude` | **35.6717809 / 139.799519** |
| `place_ref_id` | **`ChIJK11I4BGJGGAR5mZswigcu58`** |
| `goriyaku` (text) | *(empty)* |
| `sajin` | *(empty)* |
| GoriyakuTag relations | **0** |
| deity facts | **0** |
| history facts | **0** |
| `created_at` | 2026-06-12 01:31:31.140665+00 |
| `updated_at` | 2026-06-12 01:31:31.141346+00 — *never updated after creation* |

**Role:** a **zero-data row** — no goriyaku, no tags, no knowledge; carries only an identity + a Google `place_ref`; created the day after id 49 and never touched again.

## 7. PlaceRef evidence

The `PlaceRef` linked from id 104 (`place_ref` PK is the Google Place ID), `[prod]` read-only:

| Field | Value |
|---|---|
| `place_id` (PK) | `ChIJK11I4BGJGGAR5mZswigcu58` |
| `name` | 富岡八幡宮 |
| `address` | `日本、〒135-0047 東京都江東区富岡１丁目２０−３` |
| `latitude` / `longitude` | 35.6717809 / 139.799519 |
| `synced_at` | 2026-06-12 01:31:30.616988+00 — **~0.5 s before id 104's `created_at`** |
| `snapshot_json` keys | `{formatted_address, geometry, icon, name, photos, place_id, types}` |
| `snapshot_json → name` | 富岡八幡宮 |
| `snapshot_json → formatted_address` | `日本、〒135-0047 東京都江東区富岡１丁目２０−３` |
| `snapshot_json → place_id` | `ChIJK11I4BGJGGAR5mZswigcu58` (matches PK) |
| `snapshot_json → types` | `["establishment", "place_of_worship", "point_of_interest", "tourist_attraction"]` |
| `snapshot_json → geometry.location` | `{"lat": 35.6717809, "lng": 139.799519}` |

The PlaceRef is a Google Places record whose own `name` is `富岡八幡宮`, whose `types` include **`place_of_worship`**, and whose coordinate/address match id 104's exactly. (No irrelevant raw payload — `icon` / `photos` values — is reproduced here.)

## 8. Address normalization

Comparison only. **No stored address is rewritten.**

| Source | Raw form | Normalized form |
|---|---|---|
| Production id 49 `address` | `東京都江東区富岡1-20-3` | `東京都江東区富岡1-20-3` |
| Production id 104 `address` | `日本、〒135-0047 東京都江東区富岡１丁目２０−３` | `東京都江東区富岡1-20-3` |
| id 104 PlaceRef `formatted_address` | `日本、〒135-0047 東京都江東区富岡１丁目２０−３` | `東京都江東区富岡1-20-3` |
| **江東区 official (MUNICIPAL_OFFICIAL, §10)** | `東京都江東区富岡 1丁目20番3号` | `東京都江東区富岡1-20-3` |
| Spreadsheet row for 富岡八幡宮 (row id 49) | not read this task; PR #2612 recorded its identity as 富岡八幡宮 [MS] | — |

Normalization steps applied (all reversible presentation / lot-notation aspects): full-width → half-width digits (`２０−３` → `20-3`); `丁目 / 番 / 号` notation → hyphen (`1丁目20番3号` → `1-20-3`; `１丁目２０−３` → `1-20-3`); strip leading `日本、`; strip `〒135-0047` (135-0047 **is** the postal code for 江東区富岡 — consistent, not conflicting); collapse Japanese whitespace.

**Address identity classification: `ADDRESS_IDENTITY = NORMALIZED_MATCH`** — Production id 49, Production id 104, the id 104 PlaceRef, **and the 江東区 MUNICIPAL_OFFICIAL address** all normalize to the identical street lot `東京都江東区富岡1-20-3`. The differences are entirely full-width/half-width, `丁目/番/号` vs hyphen, postal-code presence, and `日本、`-prefix variants.

## 9. Coordinate comparison

Geodesic (haversine, WGS-84 mean radius). Points:

- **A** = Production id 49 coord: `35.6733, 139.7967`
- **B** = Production id 104 coord: `35.6717809, 139.799519`
- **C** = id 104 PlaceRef (Google provider) coord: `35.6717809, 139.799519` — **identical to B**
- **D** = Spreadsheet row-49 coord: **NOT AVAILABLE** — PR #2612 [MS] confirmed Spreadsheet row id 49 has no populated `reference_latitude` / `reference_longitude`
- **E** = published supplementary coordinate for 富岡八幡宮 (§10, Wikipedia `SUPPLEMENTARY_SOURCE`): `35.6717528, 139.7995833`. The **MUNICIPAL_OFFICIAL** source (§10) gives the address `富岡 1丁目20番3号` but **no coordinate**; E is corroborating context only, not the decision basis.

| Pair | Distance |
|---|---|
| A ↔ B | **305.6 m** |
| A ↔ C | 305.6 m (C == B) |
| **B ↔ C** (id 104 vs its Google provider coord) | **0.0 m** |
| B ↔ E (id 104 vs supplementary published coord) | 6.6 m — corroborating |
| A ↔ E (id 49 vs supplementary published coord) | 312.1 m |
| confirmed pairs, for contrast: 給田六所 22↔101, 長太稲荷 21↔103 | **0.0 m each** (byte-identical) |

**Per-coordinate classification:**

- **B / C (id 104 + its PlaceRef): `SAME_PRECINCT`.** id 104's stored coordinate equals its Google `place_of_worship` provider coordinate exactly, and both sit 6.6 m from the published supplementary coordinate for 富岡八幡宮. This coordinate is *on the real shrine grounds* at the MUNICIPAL_OFFICIAL address.
- **A (id 49): `OUTSIDE_EXPECTED_PRECINCT`.** ~306–312 m NW of B/C/E. This is an **imprecise manually-seeded coordinate on the pre-existing primary row** — a position-quality defect (same class as `docs/audit/shrine-70-coordinate-correction.md`, where id 70's stored coordinate pointed ~250 m off at a nearby bakery). It is **not** evidence of a second shrine: id 49's *address* normalizes to the MUNICIPAL_OFFICIAL address (§8), and id 104 + its provider coordinate independently pin the real location.
- Overall: coordinate evidence is **consistent with SAME** — the coordinate delta is an id 49 position-quality defect, used here as an observation, not as a decision rule.

## 10. Real-world identity evidence (`MUNICIPAL_OFFICIAL` primary)

Identity-only. Source preference order for this task: (1) shrine official site → (2) official shrine organisation / Jinja Honcho → (3) **government / municipal / cultural-property** → (4) Google Places identity already stored → (5) other strong identity-only source.

- (1) 富岡八幡宮 official site `https://www.tomiokahachimangu.or.jp/` — **unreachable this session** (`ECONNREFUSED`).
- (2) not separately reached.
- **(3) — PRIMARY identity source used (source-hierarchy tier 3, ahead of Google Places and any encyclopedia): 江東区 (Koto City) official website.**

### Primary — `SOURCE_TYPE = MUNICIPAL_OFFICIAL`

**江東区 official page for 富岡八幡宮 — `https://www.city.koto.lg.jp/promotion/spot/tomioka.html`** `[src]` (fetched this session; also independently verified by the Mother Ship [MS], who additionally notes 江東区 cultural-property pages identify 富岡八幡宮 at 富岡1-20-3):

| Field | Value (verbatim) |
|---|---|
| 名称 (name) | `富岡八幡宮` |
| 所在地 (address) | `東京都江東区富岡 1丁目20番3号` |

`SOURCE_TYPE = MUNICIPAL_OFFICIAL` — satisfies preference tier 3, ahead of Google Places and ahead of any encyclopedia.

### Provider-identity source (separate) — Google PlaceRef

`[prod]`, stored on Production id 104 (§7). **Identity / position evidence only — NOT a factual/semantic source:**

| Field | Value |
|---|---|
| provider `name` | `富岡八幡宮` |
| provider `formatted_address` | `日本、〒135-0047 東京都江東区富岡１丁目２０−３` |
| provider `types` | includes `place_of_worship` |
| provider coordinate | `35.6717809, 139.799519` — **equals Production id 104's coordinate** |

### Supplementary context — `SUPPLEMENTARY_SOURCE`

**Wikipedia (EN), `https://en.wikipedia.org/wiki/Tomioka_Hachiman_Shrine`** `[src]` — **not authoritative**, retained only as supplementary context: it gives a published coordinate `35°40′18.31″N 139°47′58.50″E` = `35.6717528, 139.7995833` for 富岡八幡宮 in Tomioka, Kōtō. (The earlier draft's global-uniqueness phrasing "one primary … at this location" is **removed** — it is not needed for the SAME decision and is not asserted by the municipal source.)

### Cross-check

| Cross-check | Result |
|---|---|
| MUNICIPAL_OFFICIAL name ↔ id 49 / id 104 `name_jp` | `富岡八幡宮` — match |
| MUNICIPAL_OFFICIAL address `東京都江東区富岡 1丁目20番3号` ↔ both Production rows' + PlaceRef normalized address | `東京都江東区富岡1-20-3` — `NORMALIZED_MATCH` (§8) |
| Google PlaceRef provider identity | `place_of_worship` named `富岡八幡宮` at that address; provider coordinate == id 104 coordinate |
| id 104 coordinate ↔ Wikipedia supplementary coordinate | 6.6 m (§9) — consistent, corroborating; not the basis of the decision |
| id 49 coordinate ↔ that same address's shrine location | ~312 m off (§9) — a position-quality defect on the pre-existing row (see §12), **not** evidence of a second shrine |

## 11. Shadow-pattern comparison

Against the two **confirmed** duplicate pairs (PR #2612 §10): 給田六所神社 {22 primary, 101 shadow} and 長太稲荷神社 {21 primary, 103 shadow}. All values `[prod]`.

| Signal | 101 (給田六所 shadow) | 103 (長太稲荷 shadow) | **104 (富岡 candidate)** |
|---|---|---|---|
| primary `created_at` | 06-11 05:49:02.11 | 06-11 05:49:02.09 | 06-11 05:49:02.63 |
| shadow `created_at` | 06-11 07:18:01.73 | 06-11 08:00:18.64 | **06-12 01:31:31.14** |
| primary → shadow gap | ~1.5 h | ~2.2 h | **~19.7 h (next day)** |
| shadow `place_ref` set | yes | yes | **yes** |
| PlaceRef `synced_at` vs shadow `created_at` | −0.5 s | −0.5 s | **−0.5 s** |
| PlaceRef `name` == shrine `name_jp` | yes | yes | **yes (富岡八幡宮)** |
| PlaceRef `formatted_address` == shadow `address` | yes (identical) | yes (identical) | **yes (identical)** |
| PlaceRef `types` include `place_of_worship` | yes | yes | **yes** (+ `tourist_attraction`) |
| shadow `name_romaji` | empty | empty | **empty** |
| shadow `goriyaku` | empty | empty | **empty** |
| shadow tags / deity / history | 0 / 0 / 0 | 0 / 0 / 0 | **0 / 0 / 0** |
| shadow `updated_at` == `created_at` (never touched) | yes | yes | **yes** |
| shadow coord == primary coord | **byte-identical** | **byte-identical** | **differs ~306 m** |

**`SHADOW_PATTERN_MATCH = STRONG`.** Id 104 matches every structural signal of the confirmed shadow rows — a `place_ref`-only row created ~0.5 s after its PlaceRef sync, self-named, address-identical to its PlaceRef, zero data, never updated. The **two** points of difference are: (a) it was created the next day rather than the same day (consistent with the same Google-Places discovery/resolve workflow being run again ~20 h later), and (b) its coordinate came from the PlaceRef geocode and therefore differs from id 49's *imprecise* manual coordinate (§9). Neither difference indicates a second real shrine.

## 12. Identity decision

**`SAME_REAL_SHRINE_DUPLICATE`.**

Composite rationale — no single signal is used alone, and **not** same-name-alone:

1. **Same normalized official address** (`ADDRESS_IDENTITY = NORMALIZED_MATCH`, §8) — Production id 49, Production id 104, the id 104 PlaceRef, **and the 江東区 `MUNICIPAL_OFFICIAL` address (`東京都江東区富岡 1丁目20番3号`)** all normalize to the identical street lot `東京都江東区富岡1-20-3`.
2. **id 104 PlaceRef identifies 富岡八幡宮 at that address** (§7, §10) — the stored Google provider record is `name = 富岡八幡宮`, `types` include `place_of_worship`, `formatted_address` normalizes to the same lot. (Provider identity/position evidence only — not a semantic source.)
3. **id 104 coordinate equals its PlaceRef coordinate** exactly (§9, B ↔ C = 0.0 m), and is 6.6 m from the published supplementary coordinate for 富岡八幡宮 (corroborating).
4. **id 104 is a zero-data `place_ref` shadow** (§6) — no goriyaku, no tags, no deity/history; identity + `place_ref` only.
5. **`SHADOW_PATTERN_MATCH = STRONG`** (§11) — id 104 reproduces every structural marker of the two confirmed zero-data `place_ref` shadow rows (101, 103).
6. **id 49 is the data-bearing pre-existing row** (§5) — created first (2026-06-11), holds the goriyaku text, GoriyakuTag links, and deity/history.
7. **id 49's coordinate drift (~306–312 m) is a position-quality defect**, not evidence of a separate shrine — its address still normalizes to the `MUNICIPAL_OFFICIAL` address; the delta is *explained*, not used to decide.

`AMBIGUOUS_PENDING_IDENTITY_CONFIRMATION` is **not** retained: PR #2612's missing piece — an official real-world address for the shrine — is now supplied by a `MUNICIPAL_OFFICIAL` source, and it matches both rows.

`DISTINCT_SHRINES_SAME_NAME` is **rejected**: it would require two separate real 富岡八幡宮 registered at the same street lot `東京都江東区富岡1-20-3`. The `MUNICIPAL_OFFICIAL` source lists 富岡八幡宮 at that single address; id 104's PlaceRef is the `place_of_worship` record for that address. (This decision does not rely on a global "only one 富岡八幡宮 anywhere" claim — other 富岡八幡宮 exist elsewhere in Japan; it relies on there being one shrine at *this lot*.)

**Audit unit (PR-C):** the data-bearing primary **id 49**, with **id 104** retained in the evidence table as its shadow (PR #2611 §8 pattern). *No row is deleted or merged by this task.*

### Data-quality note (observation only, not fixed here)

Production id 49's stored coordinate (`35.6733, 139.7967`) is ~306–312 m from id 104 / its Google provider coordinate / the published supplementary coordinate for the shrine. A coordinate correction for id 49 (the pattern of `docs/audit/shrine-70-coordinate-correction.md`) may be warranted — **out of scope for this task**; recorded for the Mother Ship (§15.7).

## 13. Denominator consequence

Because the classification is **`SAME_REAL_SHRINE_DUPLICATE`** (Phase 7, first branch):

| Term | Value |
|---|---|
| `RAW_PRODUCTION_SHRINE_ROWS` | 108 [prod] / [MS] |
| `QA_FIXTURE_ROWS` | 1 (id 102) |
| `NON_SHRINE_ARTIFACT_ROWS` | 1 (id 105 `広島市` — unchanged; not fixed here) |
| `POST_QA_PRODUCTION_ROWS` | 107 |
| **`CONFIRMED_DUPLICATE_EXTRA_ROWS`** | **3** (shadow rows 101, 103, **104**) |
| **`AMBIGUOUS_DUPLICATE_EXTRA_ROWS`** | **0** |
| **`UNIQUE_REAL_SHRINE_IDENTITIES`** | **103** (107 − 1 non-shrine − 3 duplicate shadows) |
| **`RECOMMENDED_FULL_AUDIT_DENOMINATOR`** | **103** |

The candidate range from PR #2612 (103–104) collapses to a single value: **103**.

## 14. PR-C gate consequence

**Do not start PR-C.** Updated gate packet:

| Gate | State | Basis |
|---|---|---|
| Production Shrine set | **GREEN** | PR #2612 §8 + this task §5–§6 |
| Production GoriyakuTag master | **GREEN** | PR #2612 §7 — `ALIGNED` 39/39 |
| Spreadsheet read path | **GREEN** | project-level `MOTHER_SHIP_AUTHENTICATED_SPREADSHEET_READ = VERIFIED` [MS] |
| Production PK drift | **GREEN** | `DEV_DB_PK_DRIFT_SCOPE = LOCAL_DEV_ONLY_CONFIRMED` |
| **Denominator** | **GREEN** | this task — `UNIQUE_REAL_SHRINE_IDENTITIES = 103`, single value, no remaining ambiguity |

**`PR_C_ENTRY_GATE = READY_PENDING_MOTHER_SHIP_SIGNOFF`**

All five gates are GREEN. The denominator is now **numerically determined (103)**. This task only *prepares* the decision packet — the Mother Ship gives the final PR-C start decision and the sign-off on the anomalous-row dispositions (§15).

## 15. Remaining Mother Ship decisions

The 富岡八幡宮 identity question (PR #2612 §15.1) is **resolved** — `SAME_REAL_SHRINE_DUPLICATE`, denominator 103. The remaining items are carried forward from PR #2612 §15 unchanged:

1. **Approve `FULL_AUDIT_DENOMINATOR = 103`** — now backed by a single determined value (§13), no candidate range.
2. **Duplicate shadow rows 101 / 103 / 104** (all zero-data `place_ref` shadows) — pre-audit cleanup in a separate, gated, isolated PR, or carried into PR-C's matrix as `REVIEW_REQUIRED` rows attached to their primary identity (21 / 22 / 49). **Not deleted or merged by PR-C.**
3. **Non-shrine row id 105 `広島市`** — pre-audit removal (separate gated PR) or carried as `MISSING` / `REVIEW_REQUIRED`. **Not fixed here.**
4. **`shrine_qa_fixture_exclusion` scope** — whether to add a non-shrine-geocode-artifact guard. Separate PR; out of scope.
5. **Local dev DB `GoriyakuTag` re-seed** — the local `jinja_db` still carries the drifted 46-row table; a separate local-dev-only remediation is recommended. **Not done here.**
6. **PR-C audit unit for a `SAME_REAL_SHRINE_DUPLICATE` pair** — confirm it is the data-bearing primary id (21 / 22 / **49**), shadow id retained in the evidence table.
7. **id 49 coordinate accuracy** (new, §12) — id 49's stored coordinate is ~306–312 m from id 104 / its Google provider coordinate / the published supplementary coordinate for 富岡八幡宮, while its address normalizes to the `MUNICIPAL_OFFICIAL` address; consider a coordinate correction (shrine-70 pattern) as a separate isolated PR.

## 16. Tests / verification

- Newest `origin/develop` recorded: `9d102b86b29a6653923f45fa6db78e4b54330f68` (§2).
- Isolated worktree confirmed; control repo not modified.
- **All Production queries passed `guard.py check-readonly-sql`** (SELECT-only); credential value never exposed; no write / DDL / `EXPLAIN ANALYZE` issued.
- **Tests (this worktree, `--reuse-db`, run per file — `pytest.ini` `--maxfail=1` + `-p pytest_env` blocks multi-file invocation):**

  | File | Result |
  |---|---|
  | `services/test_shrine_qa_fixture_exclusion.py` | 2 passed |
  | `services/test_shrine_submission_duplicate_candidates.py` | 4 passed |
  | `services/test_concierge_chat_candidates_dedupe.py` | 5 passed |
  | `api/test_concierge_chat_dedupe.py` | 2 passed |
  | `test_gis_knowledge_seed_shrine_identity.py` | 1 passed |
  | `test_knowledge_coverage_report_command.py` | 3 passed |
  | `services/test_knowledge_coverage_report.py` | 8 passed |
  | `test_need_to_goriyaku_tag_ids.py` | 19 passed |
  | `scripts/migration_safety/tests/test_guard.py` (credential bridge / read-only allow-list) | 47 passed |
  | **Total** | **91 passed, 0 failed** |

- **`git diff --check`: CLEAN.** No production code / config / fixture / seed / model / migration changed. Only this doc is added.
- **markdownlint:** 0 issues against the repo's `.markdownlint.json` rules (MD013 / MD033 / MD041 / MD024 / MD007). The standalone tool additionally reports `MD060` (compact table-pipe spacing) on every `|---|---|` separator row — this is the established repo-wide house style (the same style in every existing `docs/audit/*.md`; ~252 such findings in the two most recent merged audit docs), it is **not** enforced by any CI job or pre-commit hook, and it is matched here for consistency.

## 17. Final verdict

- **富岡八幡宮 Production {49, 104} = `SAME_REAL_SHRINE_DUPLICATE`.** id 49 is the data-bearing pre-existing primary; id 104 is a zero-data Google-`place_ref` shadow. Decided from the composite (§12): (i) `ADDRESS_IDENTITY = NORMALIZED_MATCH` — id 49, id 104, the id 104 PlaceRef, and the **江東区 `MUNICIPAL_OFFICIAL`** address (`東京都江東区富岡 1丁目20番3号`) all normalize to `東京都江東区富岡1-20-3`; (ii) id 104's PlaceRef is Google's `place_of_worship` record named `富岡八幡宮` at that address; (iii) id 104's coordinate == its PlaceRef coordinate; (iv) id 104 is a zero-data shadow; (v) `SHADOW_PATTERN_MATCH = STRONG`; (vi) id 49 is the pre-existing data-bearing row; (vii) id 49's ~306–312 m coordinate drift is a position-quality defect, not a second shrine. Not same-name-alone.
- **`CONFIRMED_DUPLICATE_EXTRA_ROWS = 3`** (101, 103, 104); **`AMBIGUOUS_DUPLICATE_EXTRA_ROWS = 0`**.
- **`UNIQUE_REAL_SHRINE_IDENTITIES = 103`**; **`RECOMMENDED_FULL_AUDIT_DENOMINATOR = 103`** (candidate range from PR #2612 collapses to a single value).
- **`PR_C_ENTRY_GATE = READY_PENDING_MOTHER_SHIP_SIGNOFF`** — all five gates GREEN, denominator numerically determined. Mother Ship gives the final PR-C start decision and the anomalous-row dispositions (§15).
- Kept unchanged: Production `GoriyakuTag` = `ALIGNED` 39/39; `DEV_DB_PK_DRIFT_SCOPE = LOCAL_DEV_ONLY_CONFIRMED`; `PRODUCTION_READ_PATH = DIRECT_DB`; id 105 `広島市` non-shrine finding; **no Production remediation performed**.

**Explicit confirmation:** nothing was written to Production, the Google Spreadsheet, DB data, Recommendation configuration, Knowledge, `GoriyakuTag` rows, `Shrine` rows, `Shrine.goriyaku`, Need mappings, fixtures, seeds, models, migrations, or deployment configuration. All Production access was read-only via the repo's sanctioned credential bridge (credential value never seen). No Shrine row was deleted or merged. The only change in this branch is the new file `docs/audit/tomioka-hachimangu-identity-resolution.md`.

## STOP

PR created. No merge. PR-C not started. Duplicate remediation not started. id 105 `広島市` not fixed. Local dev DB not re-seeded.
