# P5-DATA — id 21 / id 22 Recommendation Evidence Tag Reconciliation

## 1. Metadata

| Field | Value |
|---|---|
| Task | P5-DATA — remove the unsupported `goriyaku_tags` M2M relations from shrine ids 21 (長太稲荷神社) and 22 (給田六所神社), per the merged P5 preflight and the FINAL Mother Ship decisions. **Recommendation Evidence M2M reconciliation only** — not prose cleanup, not Knowledge cleanup, not Purpose-mapping work. |
| Branch | `fix/p5-id21-id22-tag-reconciliation` (from fresh `origin/develop`; **does not include the F5 branch**) |
| Base | `origin/develop` @ `20d3dcc843e53b91a1002bfffd7a7c73b792bd5b` (merge of PR #2621 — P5 preflight). Local `develop` synchronized `--ff-only` to the same SHA. Migration `0096` present; P5 preflight audit present. No commits beyond #2621 → no base drift. |
| Worktree | `~/Developer/jinja_app-p5d` (isolated; control repo untouched). |
| Date | 2026-08-30 |
| Production read | sanctioned read-only credential bridge (`scripts/migration_safety/readonly_query.sh` + repo-external `~/.config/kami-musubi/production-db.env`); every query passed `guard.py check-readonly-sql`; credential value never printed / logged / in argv. **No Production write.** |

## 2. Mother Ship decisions (FINAL — applied verbatim)

| # | Decision |
|---|---|
| P5-1 | id 21: REMOVE canonical tags **4 商売繁盛** and **5 五穀豊穣**. |
| P5-2 | id 22: REMOVE canonical tag **7 家内安全**. |
| P5-3 | REMOVE legacy Local-only tag **地域安泰** from ids 21 / 22 **if present**. Match by exact name (PKs differ Local↔Production); do **not** create the tag if absent; Production absence must be a safe no-op. |
| P5-4 | Do **NOT** modify `Shrine.goriyaku` raw prose or `Shrine.history_theme` (separate display/data-hygiene task). |
| P5-5 | Do **NOT** wait for a future id 22 benefit Source. Current eligibility reflects current reviewed evidence; future Source discovery re-activates in a separate reviewed task. |

## 3. Production before-state [prod] (fresh state gate)

| | id 21 長太稲荷神社 | id 22 給田六所神社 |
|---|---|---|
| `place_ref_id` | **NULL** (catalog row; shadow = pk 103, `place_ref` set — never touched) | **NULL** (catalog row; shadow = pk 101) |
| `history_theme` | `守り` | `守り` |
| `Shrine.goriyaku` (raw prose) | `地域に根ざした稲荷社として、商売繁盛や五穀豊穣、日々の暮らしの安定を願う神社。` | `地域の氏神として、暮らしや家内安全、日々の無事を見守る神社。` |
| `goriyaku_tags` | **{4 商売繁盛, 5 五穀豊穣}** — exactly 2, no unexpected tags | **{7 家内安全}** — exactly 1, no unexpected tags |
| `ShrineDeity` / `ShrineHistory` | 0 / 0 (genuine zero-Knowledge) | 2 / 4 (`source_confirmed` / `medium`) |
| `updated_at` | 2026-08-10 01:18 (= migration 0091) | 2026-08-10 01:18 |
| `GoriyakuTag` master | 39 rows, ids 1–39; **`地域安泰` does not exist** | (same) |
| canonical ids | 商売繁盛 = **4**, 五穀豊穣 = **5** | 家内安全 = **7** |

Matches the merged P5 preflight exactly → **`P5_DATA_STATE_DRIFT_REQUIRES_REVIEW` not triggered.** No unexpected tags on either target.

## 4. Local before-state [local `jinja_db`]

| | id 21 | id 22 |
|---|---|---|
| `place_ref_id` | NULL | NULL |
| `goriyaku` / `history_theme` | same prose / `守り` | same prose / `守り` |
| `goriyaku_tags` (drifted local PKs / names) | **{17 商売繁盛, 13 五穀豊穣, 14 地域安泰}** | **{9 家内安全, 14 地域安泰}** |
| `GoriyakuTag` table | drifted 46-row dev table (legacy ids 1–15 + master renumbered from 16); `地域安泰` present at legacy pk 14 | (same) |

**Local/Production semantic difference:** the legacy `地域安泰` tag is attached to **both** shrines locally but absent from Production (migration 0091 attached it only where the label existed — `LOCAL_DEV_ONLY_CONFIRMED`, P5 preflight §13). PK numbers for the same label differ between environments (`DEV_DB_PK_DRIFT`).

## 5. Evidence basis (from merged P5 preflight §6, §10)

Every target relation was **hand-set by migration 0091** (`fill_missing_local_shrine_reason_facts`) from a hard-coded name list — a LEGACY "reason fill" for two zero/weak-Knowledge local shrines. It is **not** parse-derived from the prose and **not** backed by any reviewed `ShrineKnowledgeSource`:

| Shrine · tag | Canonical? | Need-wired? | Reviewed explicit benefit Source? | Eligibility | Preflight class |
|---|---|---|---|---|---|
| 21 · 商売繁盛 (4) | ✓ | `money` | **NO** — id 21 has 0 Knowledge / 0 Source | UNKNOWN | REMOVE_CANDIDATE |
| 21 · 五穀豊穣 (5) | ✓ | `money` | **NO** | UNKNOWN | REMOVE_CANDIDATE |
| 22 · 家内安全 (7) | ✓ | `health`, `rest` | **NO** — id 22's Sources support identity / founding history only (contract §3: history ≠ eligibility; P4 established no benefit Source) | UNKNOWN | REMOVE_CANDIDATE |
| 21/22 · 地域安泰 | ✗ (not in master) | — | — | N/A | N/A (Local-only artifact) |

No target tag was `KEEP_CANDIDATE` (canonical + explicit reviewed Source) or `NORMALIZE_CANDIDATE`.

## 6. Exact M2M removals

`backend/temples/migrations/0097_p5_id21_id22_tag_reconciliation.py` — a scoped reversible `RunPython` data migration (0090 / 0091 / 0094 / 0095 pattern).

| Shrine (guarded: pk + exact `name_jp` + `place_ref_id IS NULL`) | `goriyaku_tags.remove(...)` by exact tag **name** |
|---|---|
| 21 長太稲荷神社 | `商売繁盛`, `五穀豊穣`, `地域安泰` |
| 22 給田六所神社 | `家内安全`, `地域安泰` |

- Tags resolved via `GoriyakuTag.objects.filter(name__in=[…])` — **exact name, never PK**. A name with no row (`地域安泰` in Production) is simply absent from the result → `.remove()` is not called for it → safe no-op. **No `get_or_create`.**
- `.remove()` for a tag not currently attached is itself a no-op → forward is idempotent.
- Shadow rows 103 / 101 have `place_ref` set → excluded by the `place_ref_id IS NULL` guard.

### Local-only `地域安泰` cleanup

`地域安泰` is a legacy label absent from the Production 39-row master. Matching by name:

- **Production**: no `地域安泰` row → `.remove()` never invoked for it → **safe no-op** (Decision P5-3).
- **Local (drifted DB)**: `地域安泰` (legacy pk 14) is attached to ids 21 / 22 → **actually removed**, converging Local to the Production semantic state. The `GoriyakuTag` **row itself is not deleted** — only the M2M relation.

## 7. Preserved — with regression assertions

| Preserved | Test |
|---|---|
| `Shrine.goriyaku` raw prose (both shrines, byte-for-byte) | `test_raw_goriyaku_and_history_theme_preserved` |
| `Shrine.history_theme` (`守り`, both) | `test_raw_goriyaku_and_history_theme_preserved` |
| every `ShrineDeity` / `ShrineHistory` row + `verification_status` / `confidence` / content | `test_knowledge_and_sources_unchanged` |
| every `ShrineKnowledgeSource` row + relations | `test_knowledge_and_sources_unchanged` |
| `GoriyakuTag` master — no row created or deleted (39 rows) | `test_no_goriyaku_tag_master_change` |
| `NEED_TO_GORIYAKU_IDS` / `NEED_TEXT_WEIGHTS` | `test_need_mapping_unchanged` |
| unrelated tags on the target shrines | `test_unrelated_tags_on_targets_remain` |
| unrelated shrines' Recommendation-relevant M2M | `test_unrelated_shrine_m2m_stable`, `test_place_ref_shadow_row_untouched` |

Local dev run confirmed: after `migrate temples` (0097), id 21 / id 22 `goriyaku` text length and `history_theme` are unchanged.

## 8. Recommendation before / after behavior

Persisted `goriyaku_tags` M2M is the **sole** goriyaku input to `score_need` / C1 / `matched_all` / candidate prefilter (P5 preflight §7–§9). Removing the tags removes those M2M-derived matches; **no Need mapping, ranking, scoring, interpreter, C1, Lead, or Reason code is changed.**

| | Before | After |
|---|---|---|
| id 21 · `money` Purpose match (via `商売繁盛`(4) / `五穀豊穣`(5) ∈ `NEED_TO_GORIYAKU_IDS["money"]`) | possible via M2M | **gone** — id 21 has 0 `goriyaku_tags` → no `money` GID intersection. id 21 has 0 Knowledge too → fully Recommendation-inert (parallels `communication = set()`: the candidate takes the C1 NONE branch, `score_need = 0` — the intended contract-correct outcome). |
| id 22 · `health` / `rest` Purpose match (via `家内安全`(7) ∈ `NEED_TO_GORIYAKU_IDS["health"]` and `["rest"]`) | possible via M2M | **gone** — id 22 has 0 `goriyaku_tags`. Its `ShrineDeity` / `ShrineHistory` Knowledge is untouched (still displayed in Shrine Detail; still feeds Reason where applicable). |
| raw prose in Shrine Detail API / `_primary_benefit` fallback | present (fallback only reached when 0 tags) | **unchanged** — the prose is not modified (Decision P5-4); with 0 tags, `_primary_benefit` will now use the prose as fallback (display copy, not scoring) |
| any unrelated shrine | — | unchanged (`test_unrelated_shrine_m2m_stable`) |

Tests `test_id21_money_match_disappears` and `test_id22_health_rest_match_disappears` assert the M2M ∩ `need_tags_to_goriyaku_ids([...])` intersection is non-empty before and empty after.

## 9. Local / Production reproducibility

The same migration artifact yields the intended **semantic** state in both environments despite `GoriyakuTag` PK drift, because every tag is matched by **exact canonical name**:

| | Local expected state | Production expected state |
|---|---|---|
| id 21 `goriyaku_tags` | ∅ (`商売繁盛`, `五穀豊穣`, `地域安泰` all removed) | ∅ (`商売繁盛`, `五穀豊穣` removed; `地域安泰` absent → no-op) |
| id 22 `goriyaku_tags` | ∅ (`家内安全`, `地域安泰` removed) | ∅ (`家内安全` removed; `地域安泰` no-op) |
| `Shrine.goriyaku` / `history_theme` | unchanged | unchanged |
| `GoriyakuTag` master | 46 rows, unchanged (`地域安泰` row kept) | 39 rows, unchanged |

`test_pk_drift_name_based_matching` reproduces the drifted-PK shape (same names at ids 9017 / 9005) and asserts the removal still lands. Verified on the real local DB: BEFORE id 21 `{五穀豊穣, 商売繁盛, 地域安泰}` / id 22 `{家内安全, 地域安泰}` → AFTER forward `∅` / `∅`; `地域安泰` row still present; `GoriyakuTag.count() == 46`.

## 10. Migration safety

- **Scope**: `RECONCILE` list is exactly `[(21, "長太稲荷神社", …), (22, "給田六所神社", …)]`. `test_scope`/`test_unrelated_*` confirm no other shrine changes.
- **Identity guard**: `_target_shrine` = `filter(pk, name_jp=expected, place_ref_id__isnull=True)` — a renamed row, or an environment where only the `place_ref`-set shadow exists, is a no-op (`test_identity_mismatch_is_noop`, `test_place_ref_shadow_row_untouched`).
- **`.only(SHRINE_LOOKUP_FIELDS)`** excludes `location` (the 0091 / 0094 legacy-`text`-column GEOSException guard).
- **Idempotent forward** (`test_forward_idempotent`, run ×3).
- **No `get_or_create`**, no tag row created or deleted in either direction (`test_no_goriyaku_tag_master_change`, `test_reverse_does_not_create_missing_legacy_tag`).

## 11. Reverse behavior

`reconcile_reverse` re-attaches **exactly the relations this migration is designed to remove**, for every name whose `GoriyakuTag` exists in that environment (via the same `filter(name__in=…)` + `.add()`):

- id 21 → re-add `商売繁盛`, `五穀豊穣`, and `地域安泰` **if it exists** (Production: absent → skipped, never created; Local: present → restored).
- id 22 → re-add `家内安全`, and `地域安泰` **if it exists**.

`test_reverse_restores_canonical_relations`, `test_reverse_does_not_create_missing_legacy_tag`. Verified on the local DB: `migrate temples 0096` restored id 21 to `{五穀豊穣, 商売繁盛, 地域安泰}` and id 22 to `{家内安全, 地域安泰}`; re-`migrate temples` re-applies cleanly. (As with 0090 / 0091, reverse assumes the forward starting state, which the fresh state gate confirmed.)

## 12. Production apply status

**`PRODUCTION_ACTIVATION = PENDING_AUTHORIZED_APPLY`** — only a read-only Production credential is available this session; not bypassed, no ad-hoc SQL, no disabled guards. Production `django_migrations` (read-only) shows the latest applied `temples` migration is `0094`; `0095` / `0096` / `0097` are all unapplied. The migration applies on the next authorized `migrate` / deploy, producing the Section 9 Production expected state.

## 13. No taxonomy / no mapping change

`GoriyakuTag` master taxonomy: unchanged (no row created / deleted / renamed; `地域安泰` row is not deleted, only detached in the drifted local DB). `NEED_TO_GORIYAKU_IDS` / `NEED_TEXT_WEIGHTS`: unchanged. No Purpose-mapping work, no replacement tags, no inferred alternative benefits.

## 14. No negative semantic claim

This migration does **not** encode or assert "長太稲荷神社 has no 商売繁盛 blessing" or "給田六所神社 has no 家内安全 blessing". The docstring states the correct framing: **KAMI MUSUBI's current reviewed evidence is insufficient to use these labels as Recommendation Evidence.** It is an evidence-eligibility cleanup of a 2026-vintage LEGACY reason-fill, not a denial of shrine tradition. A future reviewed Source may re-activate them (Decision P5-5).

## 15. Tests

`backend/temples/tests/test_migration_0097_p5_id21_id22_tag_reconciliation.py` — **17 tests**, covering the 22 required checks:

scope = exactly ids 21 / 22 · wrong-identity no-op · `place_ref` shadow untouched · `商売繁盛` + `五穀豊穣` removed from id 21 · `家内安全` removed from id 22 · `地域安泰` removed when present · missing `地域安泰` = safe no-op (+ not created) · unrelated tags on targets remain · raw `goriyaku` unchanged · `history_theme` unchanged · no `GoriyakuTag` master row created/deleted · `NEED_TO_GORIYAKU_IDS` unchanged · `ShrineDeity`/`ShrineHistory` unchanged · `ShrineKnowledgeSource` unchanged · forward idempotent (×3) · reverse restores canonical relations · reverse does not create a missing legacy tag · PK-drift name-based matching · id 21 `money` M2M match disappears · id 22 `health`/`rest` M2M match disappears · unrelated shrine M2M stable.

Also run: migration 0091 tests, migration 0096 tests, need-mapping tests, concierge candidate contract + dedupe tests, `backfill_goriyaku_tags` command tests, Evidence Gate tests, Shrine Detail knowledge API tests → **110 passed** (focused set). **Full `backend/temples` suite: 1946 passed, 13 skipped, 0 failed.** `python manage.py makemigrations temples --check` → "No changes detected". `git diff --check` → clean. markdownlint (`.markdownlint.json`) → 0 issues.

## 16. Remaining unresolved display-copy issue

The `Shrine.goriyaku` prose (`地域に根ざした稲荷社として、…` / `地域の氏神として、…`) and `history_theme = "守り"` — both hand-authored by migration 0091 as display/Reason copy with no reviewed Source — are **deliberately left in place** (Decision P5-4). After this migration, with 0 `goriyaku_tags`, `shrine_meaning_composer._primary_benefit()` will fall back to that prose for id 21 / id 22. Whether to keep, revise, or clear this LEGACY display copy is a **separate display/data-hygiene task**, not P5-DATA.

## 17. Out of scope / follow-ups

- **Display-copy hygiene** for the id 21 / id 22 prose + `history_theme` (Section 16) — separate task.
- **F5** (`fix/migration-0096-reverse-guard`) — migration 0096 reverse-safety fix, delivered as its own PR (`fix: migration 0096のreverseで既存Source関連を保護`), **not** bundled here.
- id 22 future benefit Source review (P4 follow-up F2 = 東京都神社庁 listing) — if it surfaces an explicit benefit statement, `家内安全` could be re-activated in a separate reviewed task (Decision P5-5).
- Not started: P1 / P2 / P6 / P7 / P8, raw-goriyaku cleanup, history_theme cleanup.

## 18. Explicit no-write / STOP confirmation

Nothing was written to Production or the Google Spreadsheet. The local DB was used only to verify the migration (apply / reverse / re-apply cycle). No change to `Shrine.goriyaku`, `Shrine.history_theme`, `GoriyakuTag` master, `NEED_TO_GORIYAKU_IDS`, `NEED_TEXT_WEIGHTS`, Evidence Gate, interpreter, ranking, scoring, C1, Lead, Reason, Compass, Concierge, Knowledge Facts, deity/history content, Source eligibility policy, billing, or the frontend. Only shrine ids 21 and 22 (catalog rows) are affected, and only their `goriyaku_tags` M2M. This branch adds two files: `backend/temples/migrations/0097_p5_id21_id22_tag_reconciliation.py` and its test; plus this audit document. No STOP condition triggered — PR #2621 merged, `develop` synchronized, no base drift, 0096 not applied to Production, id 21 / id 22 state matches the preflight, identities unambiguous, no unexpected tags, canonical ids resolved, Recommendation path matches the audited M2M-only contract, no unrelated regression. PR created. **Not merged.**
