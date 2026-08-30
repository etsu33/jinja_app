# Production `MIGRATION_MODULES` / `migrations_nogis` Root Cause Audit

> **Status: Completed — read-only audit only. No Production write. No migration
> file, settings, or `start.sh` change. No migration executed. No `--fake`
> used. No repair/bootstrap run.**
>
> **Classification: `HISTORICAL_INCIDENT_RESOLVED` (up to `temples 0094`) +
> `LIVE_STRUCTURAL_RISK_UNPATCHED` (for any future `migrate` invocation,
> `0095` onward)**

## 0. Scope and method

Purely local, read-only investigation of this repository: `git log`/`git
show` (full history, not the shallow clone this session started with —
`git fetch --unshallow origin` was run to see history predating the visible
window), and direct reading of `backend/shrine_project/settings.py` and
`backend/temples/migrations_nogis/`. No Production DB connection was made in
this task; findings about Production's actual `django_migrations` /
`temples_shrine` schema state are **cited from the prior live, read-only
audit** `docs/audit/production-migration-execution-gate.md` (Phase 2/3,
executed via the sanctioned credential bridge in an earlier session) and
`docs/audit/p8-identity-coordinate-remediation.md` (latest known ledger
position). Nothing in this document required or performed a new Production
connection.

---

## 1. `MIGRATION_MODULES` — where it's defined, and what fires it

`backend/shrine_project/settings.py`, current (`origin/develop` HEAD):

```python
USE_SQLITE = env_bool("USE_SQLITE", default=False)
USE_GIS = env_bool("USE_GIS", default=True)
DISABLE_GIS_FOR_TESTS = env_bool("DISABLE_GIS_FOR_TESTS", default=False)

if IS_PYTEST and DISABLE_GIS_FOR_TESTS:
    USE_GIS = False
...
# ---- NoGIS固定（テスト/CIで使う）: DB構成は変えず migration だけ切り替える ----
if not USE_GIS and not USE_SQLITE:
    MIGRATION_MODULES = {**globals().get("MIGRATION_MODULES", {})}
    MIGRATION_MODULES["temples"] = "temples.migrations_nogis"
```

(`settings.py` lines ~71-77 and ~191-194.)

`env_bool` treats any **explicitly-set** value not in `{"1","true","yes","on"}`
(case-insensitive) as `False` — including `"0"`, `"false"`, `"False"`, `"no"`,
or a typo like `"fasle"`. Unset means the `default` (`True` for `USE_GIS`,
`False` for `USE_SQLITE`).

**Firing condition (item 1/2):** `MIGRATION_MODULES["temples"]` is set to
`"temples.migrations_nogis"` whenever, at settings-import time, **`USE_GIS`
resolves falsy AND `USE_SQLITE` resolves falsy** — i.e., "a real
PostgreSQL/PostGIS-capable database is configured, but GIS itself is turned
off." There is **no** `IS_PYTEST` or `CI` guard on this specific condition —
that guard exists only on the separate, narrower `USE_GIS = False` override
two lines above (line 76), which is itself pytest-scoped and cannot fire
outside a pytest process. **The `MIGRATION_MODULES` switch itself has no such
scoping**; it fires in any Python process that imports these settings —
`gunicorn`, `manage.py migrate`, `manage.py showmigrations`, a Render Shell
session, anything — as long as the two booleans resolve that way.

**Relationship to `USE_GIS` / `USE_SQLITE` / DATABASE config (item 3):**
`build_database_config()` (same file, ~line 137) selects the DB `ENGINE`
using the **same** `USE_GIS` flag:

```python
"ENGINE": ("django.contrib.gis.db.backends.postgis" if USE_GIS
           else "django.db.backends.postgresql"),
```

So `USE_GIS` is the single control variable for **two independent
consequences that always move together**: (a) which DB backend Django uses
against the real Postgres server, and (b) which `temples` migration module
set Django's migration loader reads from. They cannot diverge from each
other — but that is exactly the danger: **one accidental env-var value flips
both at once**, silently, with no explicit "nogis mode" log line anywhere in
this code path (the only trace is the resulting migration graph itself).

For Production specifically: `USE_SQLITE` is always `False` (Production uses
Supabase Postgres, never SQLite — confirmed by every prior migration audit in
this repo). So **for Production, the entire condition collapses to: "is
`USE_GIS` falsy?"** — a single environment variable.

---

## 2. `migrations_nogis` — full inventory (item 4)

```
backend/temples/migrations_nogis/
├── __init__.py
├── 0001_initial.py
├── 0002_goshuin_shrine.py
├── 0003_backfill_missing_tables.py
├── 0004_conciergethread_anonymous_id_and_user_nullable.py
├── 0005_goshuin_and_goshuinimage.py
├── 0006_goshuin_columns_repair.py
├── 0007_shrine_history_theme_shrine_idx_shrine_history_theme.py
└── 0008_actionevent_conciergehistory_and_more.py
```

8 migrations total, `0001` → `0008`, a single strictly linear dependency
chain (`0002` depends only on `0001`, `0003` only on `0002`, … `0008` only on
`0007` — verified by reading every file's `dependencies = [...]`). This is a
**periodically hand-regenerated squashed snapshot** intended, per its own
comment in `settings.py`, for "test/CI use" — it exists to let `USE_GIS=0`
CI/local runs build a working `temples` schema without needing GDAL/PostGIS
installed, by squashing the *current* model state into a short migration set
rather than replaying the real, 99-file incremental history.

It is **not derived from, branched from, or kept in sync automatically with**
`backend/temples/migrations/` — the two are independently authored files
targeting the same Django app. `migrations_nogis` has been manually
regenerated/extended **8 separate times** across the repo's history (one
commit per file's introduction; see §4), most recently on **2026-08-05**.

---

## 3. `0080_actionevent_conciergehistory_and_more` — provenance (item 5/6)

**No file named `0080_actionevent_conciergehistory_and_more` has ever existed
anywhere in this repository's full git history** (checked with `git log --all
--diff-filter=A --name-only`, zero hits, full unshallowed history).

**What does exist:** `backend/temples/migrations_nogis/0008_actionevent_conciergehistory_and_more.py`
— an exact, unique match on the descriptive part of the name, differing only
in the numeric prefix (`0008` vs. the requested `0080`). This is almost
certainly the migration the task's premise refers to; **`0080` is a
transcription slip for `migrations_nogis`'s `0008`**, likely because it is
easy to conflate with the *real* chain's unrelated `temples/migrations/0080_shrine_visit_style_tags.py`
(a completely different migration, same numeric-adjacent territory,
different lineage) when reading Production logs or `showmigrations` output
that mixes both naming conventions.

`git log --diff-filter=A --follow` confirms **`0008_actionevent_conciergehistory_and_more.py`
was added on 2026-08-05**, commit `8ec979ca4` ("fix(backend):
temples.migrations_nogisをmodels.pyの現状へ追従(S2.5C)" / PR #2242) — a
routine catch-up regeneration bringing the nogis squash forward to match
`models.py`'s then-current shape. This date matters: it is **two months
after** Production's confirmed nogis-lineage application date (2026-06-07,
see §5) — so `0008` (nogis) **did not exist yet** when Production's
historical nogis-lineage migrations ran, and could not have been the one
Production applied. Production's nogis-origin ledger entries stop at `0007`
(§5), consistent with this timeline.

Full nogis-file creation history (`git log --diff-filter=A --follow`, full
history):

| File | First commit | Date |
|---|---|---|
| `0001_initial.py` | `0b02e5548` | 2025-11-10 |
| `0002_goshuin_shrine.py` | `90a5a941b` | 2025-11-29 |
| `0004_conciergethread_anonymous_id_and_user_nullable.py` | `4c8917b30` | 2025-12-08 |
| `0006_goshuin_columns_repair.py` | `5fa55d8bb` | 2025-12-12 |
| `0007_shrine_history_theme_shrine_idx_shrine_history_theme.py` | `52951af2d` | 2026-05-13 |
| `0003_backfill_missing_tables.py` | `7d45686c9` | 2026-03-17 |
| `0005_goshuin_and_goshuinimage.py` | `22b98997d` | 2026-03-27 |
| `0008_actionevent_conciergehistory_and_more.py` | `8ec979ca4` | 2026-08-05 |

(Note the non-monotonic numbering-vs-date order for `0003`/`0005` vs `0004`/
`0006` — the nogis file numbers were assigned at authoring time and don't
perfectly track commit date order across the whole history; not itself a
finding, just an observation while reconstructing the timeline.)

---

## 4. The exact commit that made this reachable in Production (new finding)

`git log -S"not USE_GIS and not USE_SQLITE"` isolates one commit:

**`d5655e17b` — "Use nogis migrations when USE_GIS is false" — 2026-03-16,
author `morietsu`.**

Before this commit, the guard was:

```python
if IS_PYTEST and DISABLE_GIS_FOR_TESTS and not USE_SQLITE:
    USE_GIS = False
    DATABASES["default"]["ENGINE"] = "django.db.backends.postgresql"
    MIGRATION_MODULES = {**globals().get("MIGRATION_MODULES", {})}
    MIGRATION_MODULES["temples"] = "temples.migrations_nogis"
```

— scoped to `IS_PYTEST` (true only inside an actual pytest run, per
`IS_PYTEST`'s own definition using `PYTEST_CURRENT_TEST` / `"pytest" in
sys.argv`) **and** `DISABLE_GIS_FOR_TESTS`. This combination is structurally
unreachable from a live Render `gunicorn` or `manage.py migrate` process —
`IS_PYTEST` cannot be true there.

The commit changed it to:

```python
if not USE_GIS and not USE_SQLITE:
    ...
    MIGRATION_MODULES["temples"] = "temples.migrations_nogis"
```

— dropping **both** the `IS_PYTEST` and `DISABLE_GIS_FOR_TESTS` conditions,
leaving only the two DB-shape booleans. This is the single change that made
it possible for a **live, non-test process** (including Production) to
switch `temples`'s migration lineage, merely by `USE_GIS` resolving falsy.
**This condition is unchanged from 2026-03-16 to the current `origin/develop`
HEAD** (`git log -S` finds no subsequent commit re-touching this exact
substring) — it is still live today.

---

## 5. `migrations` vs `migrations_nogis` — lineage comparison and divergence point (item 7)

| | `temples/migrations/` | `temples/migrations_nogis/` |
|---|---|---|
| File count | 99 (`0001`…`0099`, current `develop`) | 8 (`0001`…`0008`) |
| Authoring model | Real incremental history, one migration per schema/data change, going back to the project's start | Periodically **regenerated squash snapshot**, rewritten wholesale to match `models.py`'s current shape (not incremental against its own prior state in the same way) |
| Intended runtime | Real Postgres + PostGIS (`USE_GIS=True`, the Production/normal-dev default) | `USE_GIS=False` test/CI runs only, per its own settings.py comment |
| Shared ancestry | **None.** Independently authored files; not a squash-of / branch-of relationship. Both target the same Django app's models, but as two parallel, hand-maintained migration graphs |
| `0001_initial` content | `ConciergeHistory` / `Favorite` / `GoriyakuTag` / `Goshuin` / `RankingLog` / `Shrine` (lat/lng only at that point) / `ViewLike` / `Visit` | `PlaceRef` / `Shrine` (`kind`/`location as text`/`place_ref`/`owner`/`astro_elements`/etc.) / `GoriyakuTag` / `Deity` / `ShrineDeities` / `Visit` — a **materially different initial schema**, not just a renamed file |

**The divergence point is not a single commit in a shared history — the two
directories have never shared history.** They are two independently
hand-written descriptions of "what the `temples` app's tables should look
like," reconciled only by the fact that Django's migration ledger
(`django_migrations`) is a flat `(app, name)` table that has **no way to
record which physical directory produced a given recorded name** — which is
the mechanism that turned a settings misconfiguration into a schema-lineage
mixing incident (§6).

---

## 6. Production `django_migrations` ledger — consistency with the two lineages (item 8)

Cited from `docs/audit/production-migration-execution-gate.md` Phase 3
(live, read-only Production query, executed in a prior session via the
sanctioned credential bridge — **not re-verified with a new Production
connection in this task**, per this task's read-only constraint):

- `django_migrations` for `app='temples'` contains **two naming lineages**:
  1. `0001_initial` … `0007_shrine_history_theme_shrine_idx_shrine_history_theme`
     — names matching `migrations_nogis` exactly, applied **2026-06-07
     01:35 (UTC-ish, as recorded)**.
  2. `0002_initial` … `0089_actionevent` — names matching `temples/migrations/`
     exactly, applied **2026-06-11 08:49**. (`0001_initial` is **not**
     re-recorded in this pass, since a row already exists with that exact
     name from lineage 1 — Django's loader treats it as already applied and
     never re-runs it, regardless of which file actually produced it.)
- **Only one row exists for `(temples, 0001_initial)`** (`COUNT(*) > 1` = 0
  rows, checked directly) — confirming the ledger cannot itself disambiguate
  which `0001_initial.py` (real vs. nogis) that row refers to.
- **Direct schema inspection of `temples_shrine` in Production matches
  `migrations_nogis/0001_initial.py`'s design** (`kind`/`location as
  text`/`place_ref_id`/`owner_id`/`astro_elements`/`views_30d`/
  `favorites_30d`/`popular_score`/`last_popular_calc_at`/`kyusei` present;
  the real chain's simple `name_jp`-only initial shape is absent) — **this is
  the direct evidence, not an inference,** that Production's `temples_shrine`
  table was physically built from `migrations_nogis`, not `migrations/`.
- The table **also** carries `history_theme` (real chain's `0084`) and
  `visit_style_tags` (real chain's `0080`) — proving the *later* real-chain
  migrations genuinely ran on top of that nogis-rooted table afterward.
- `postgis` extension **is** installed (`pg_extension` confirmed `3.3.7`) —
  evidence a real-chain migration that creates the extension did run at some
  point; `pg_trgm` is **not** installed, suggesting the corresponding
  real-chain migration section did not run (out of scope for that prior
  audit, not re-investigated here).

**Most recent known ledger position** (`docs/audit/p8-identity-coordinate-remediation.md`,
citing a fresher live check than the Gate document above):
`temples` latest applied = **`0094_fix_shrine_70_coordinates`**. `0095`
through (as of `develop` HEAD today) `0099` are merged to `develop` but
**unapplied** to Production.

**Consistency verdict:** the ledger is internally consistent with the
"nogis-rooted, then grafted with the real chain" narrative — `0090`-`0094`
are all either self-guarding `RunPython` (no-ops if their target row is
absent/mismatched) or purely additive `AddField`/`CreateModel` operations
(per `production-migration-0090-0093-safety.md` and `production-migration-execution-gate.md`
Phase 3), which is *why* they were able to apply successfully on top of a
schema whose root diverges from what a naive "replay `migrations/0001`
onward" model would assume. **This is survivorship, not by design** — the
next migration in the real chain that happens to assume a real-chain-shaped
column that nogis's schema doesn't have (or vice versa) would fail exactly
the way `production-migration-execution-gate.md` Phase 3 individually
re-verified for `0090`-`0093` was needed for. No such verification has yet
been done for `0095`-`0099` in this task (out of the read-only scope granted
here) — see §8.

---

## 7. Root Cause classification

Two distinct but related findings, requiring two different classifications:

### 7.1 Historical incident (already occurred; already survived up to `0094`)

**`NOGIS_LINEAGE_HISTORICAL_CONTAMINATION` — RESOLVED (by survivorship, not
by design) through `temples 0094`.**

Mechanism, in order:
1. **2026-03-16** (`d5655e17b`): the `MIGRATION_MODULES["temples"] =
   "temples.migrations_nogis"` guard was loosened from a
   pytest-only-reachable condition to a bare `not USE_GIS and not
   USE_SQLITE` check, reachable from any live process, including Production.
2. Sometime before **2026-06-07**, Production's `USE_GIS` resolved falsy in
   whatever process ran `migrate` at that point — most plausibly an
   explicit `USE_GIS=0`-equivalent environment variable set as a workaround
   (e.g., for a GDAL/PostGIS unavailability issue at that point in Render's
   environment; this exact class of failure — `ImproperlyConfigured: Could
   not find the GDAL library` — was independently encountered and had to be
   fixed by installing GDAL in this very session's earlier sandboxed
   verification work, so it is a documented real-world failure mode for this
   codebase, not a hypothetical) — though this specific attribution is a
   plausible reconstruction from evidence, not a directly observed Render
   env-var read in this session.
3. `manage.py migrate` (or equivalent) ran against Production with
   `MIGRATION_MODULES["temples"] = "temples.migrations_nogis"` active,
   applying nogis's `0001`-`0007` (2026-06-07), building `temples_shrine`
   with the nogis-shaped schema.
4. By **2026-06-11**, `USE_GIS` was (presumably) corrected back to its true
   default, and `migrate` ran again — now resolving the real
   `temples/migrations/`. Django's loader saw `(temples, 0001_initial)`
   already recorded (from nogis) and skipped it, then applied
   `migrations/0002_initial` through `0089_actionevent` on top of the
   nogis-rooted schema. This worked because the individual operations that
   ran happened to tolerate the mismatch (several of `0081`/`0082`/`0085`/
   `0086` are documented in other audits as force-recreate/repair
   migrations specifically written to reconcile drifted schema state).
5. `0090`-`0094` (verified individually safe in prior audits) applied
   cleanly afterward for the same additive/self-guarding reasons.

### 7.2 Live structural risk (current, unpatched, forward-looking)

**`ENV_VAR_DEPENDENT_MIGRATION_LINEAGE_SELECTION_NOT_DEPLOY_SAFE` —
UNRESOLVED, still live on `origin/develop` HEAD today.**

The §4 commit's loosened condition has never been re-scoped. Nothing in the
current codebase prevents the exact same class of incident from recurring on
any future `migrate` invocation (whether via `RUN_MIGRATIONS_ON_START=1`, a
Render Shell session, or a One-Off Job) if `USE_GIS` ever resolves falsy in
that specific process — whether from a deliberate env var change, a typo
(`env_bool` treats any non-`{1,true,yes,on}` value as false, silently, with
no validation/warning), an Environment Group misconfiguration, or a
copy/paste error in the Render dashboard.

**Concrete difference for `0095` onward, if this recurs:** unlike the
`0001_initial` name collision (§6, now behind Production), `migrations_nogis`
has **no** migration numbered `0095`-`0099` at all (it stops at `0008`). So a
future `migrate temples 0095_batch17_recommendation_evidence_activation`
invocation, if it happened to run with the nogis lineage active, would very
likely fail **loudly** — Django's `MigrationLoader` would be unable to find a
migration file matching that name in `temples.migrations_nogis`, and/or
would find `(temples, 0094_fix_shrine_70_coordinates)` in the ledger with no
corresponding node in the (nogis) graph it just built, raising a hard error
(a `NodeNotFoundError`-class failure or an equivalent "cannot find migration"
error) rather than silently corrupting anything further. This is the most
plausible concrete shape of a "Production migration failure" for `0095`+ if
one has been observed, though this task did not have access to an actual
Render deploy log or Render Dashboard environment-variable listing to
confirm the live value of `USE_GIS` in Production at the moment of any such
failure — that confirmation requires either a Render Dashboard read (out of
this session's access) or inspecting the Render Logs output of the
diagnostic block already shipped in PR #2632 / #2634 (which logs
`RENDER_GIT_COMMIT` and `temples` `0079`-`0089` state on every startup, but
does **not** currently log the resolved `USE_GIS` value itself — see
candidate fix §8.4).

---

## 8. Safe fix candidates (NOT implemented — audit only, per this task's constraints)

Ordered by how immediately actionable and low-risk each is; none of these
were implemented in this task.

1. **Confirm the live `USE_GIS` resolution in Production directly, before
   anything else.** The single highest-value, lowest-risk next step: read
   Production's actual Render environment variable value for `USE_GIS`
   (Render Dashboard access — out of this session's reach) and/or extend the
   existing start.sh diagnostic (PR #2632/#2634 lineage) to explicitly log
   `USE_GIS` / `USE_SQLITE` / whether `MIGRATION_MODULES["temples"]` was
   overridden, at the same point in `start.sh` where the `0079`-`0089`
   diagnostic already runs. This is additive, read-only, and fail-safe by
   the same pattern already established and shipped — a natural, minimal
   follow-up PR, not implemented here.
2. **If `USE_GIS` is confirmed falsy in Production: fix the environment
   variable itself**, not the code. Setting it back to unset (default
   `True`) or explicitly `1` is an ops/environment change, not a migration or
   settings change, and directly removes the live risk (§7.2) with the
   smallest possible blast radius. This should be verified (via candidate
   #1's diagnostic) to have actually taken effect in a real running process
   before any `migrate temples 0095` attempt.
3. **Code hardening candidate**: restore a deploy-safety scope to the
   `MIGRATION_MODULES` switch in `settings.py`, e.g. re-adding a `CI`/
   `IS_PYTEST`/`DISABLE_GIS_FOR_TESTS`-class guard so the switch can only
   ever fire in a recognized test/CI context — matching the ORIGINAL
   pre-`d5655e17b` design intent already documented by the code's own "テスト
   /CIで使う" comment, which the 2026-03-16 change silently broke. This is a
   `settings.py` change and is explicitly out of scope for this task
   (`settingsを変更しない`); flagged here as a candidate for a dedicated,
   separate, carefully-tested follow-up PR.
4. **Extend the existing `start.sh` diagnostic** (already shipped,
   fail-safe-verified in PR #2632/#2634) to also log the resolved
   `DATABASES["default"]["ENGINE"]` and whether `MIGRATION_MODULES` was
   overridden for `temples`, giving direct, ongoing visibility into this
   exact risk on every future deploy without needing Render Dashboard
   access. A natural, small, additive follow-up to the already-established
   pattern.
5. **Before attempting `0095` in Production, individually re-verify its
   target row/column preconditions against Production's live schema** —
   the same methodology `production-migration-execution-gate.md` Phase 3
   already used for `0090`-`0093`, and the same methodology
   `scripts/migration_safety/sql/temples_0095_0098_preflight.sql` (this
   session's own earlier deliverable) already codifies for `0095`-`0098`.
   That preflight SQL remains valid and unaffected by this audit's findings
   — it checks Production's actual current row/relation state directly,
   which is correct regardless of which lineage produced that state.
6. **Long-term structural candidate (larger, not urgent):** consider moving
   `migrations_nogis` out of the `temples` app's default-importable path
   (e.g., only reachable via a dedicated test-settings module never loaded
   by `DJANGO_SETTINGS_MODULE` in any real deploy), so no combination of
   environment variables can ever again redirect a live process's migration
   lineage. This removes the hazard class entirely rather than re-scoping
   its trigger condition, but is the largest change of the candidates listed
   and should be a deliberate, separately-reviewed decision.

---

## 9. Production migration resumption — can `0095`-`0099` proceed?

**Not yet — `STOP_REQUIRES_PRODUCTION_ENV_VERIFICATION` (Mother Ship
decision required), not because `0095`-`0099` themselves are unsafe, but
because the precondition that made `0090`-`0094` succeed (§7.1) has not been
re-confirmed for whatever process will run `0095` next.**

Specifically outstanding before resumption:
- §8.1: confirm the live `USE_GIS` resolution in the exact Render
  process/environment that will execute the next `migrate` command. This is
  a prerequisite this audit could not satisfy (no Render Dashboard / live
  log access in this session).
- If that confirms `USE_GIS` is currently (and will remain, for the deploy
  in question) resolving `True`/default — as the evidence in §6 suggests it
  was by 2026-06-11 and has stayed for `0090`-`0094` to succeed — then the
  `0095`-`0098` preflight already built in this session
  (`scripts/migration_safety/sql/temples_0095_0098_preflight.sql`) plus the
  execution-order/verification design already built in
  `production-migration-execution-gate.md` remain the correct, already-designed
  path forward, with no changes needed on account of this audit's findings.
- If `USE_GIS` is instead found to be falsy in that process, resumption must
  wait for §8.2 (env var fix) and re-verification, not for a code or
  migration change.

**This task does not authorize resuming Production migration. That decision,
and the live-environment confirmation it depends on, is Mother Ship's.**

---

## Stop Conditions (compliance)

- [x] 読み取り・監査のみ（遵守。Production DB接続は本タスクでは新規に行っていない — §0参照）
- [x] Production DBを書き換えない（遵守）
- [x] migrationファイルを変更しない（遵守）
- [x] settingsを変更しない（遵守）
- [x] start.shを変更しない（遵守）
- [x] `RUN_MIGRATIONS_ON_START`を変更しない（遵守）
- [x] `--fake`を使用しない（遵守）
- [x] repair/bootstrapを実行しない（遵守）
- [x] Production migrationを実行しない（遵守）

## Repository Changes

- `docs/audit/production-migration-modules-nogis-root-cause.md`: this
  document (new).
- No other file changed.
