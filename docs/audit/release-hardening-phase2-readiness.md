# Release Hardening Phase 2 — Verification Audit

> Audit-only. The only repo change in this PR is this document. No migration was
> rewritten, no production DB was touched, no production code / config / `.env` /
> test was modified. Confirmed defects are recorded and classified; each becomes a
> follow-up work-package candidate for Mother Ship review.
>
> Section 17 (Phase 2 Status) is a **technical finding only** — not a launch decision.
> Section 16 candidates are **unordered**.

---

## 1. Baseline

| Item | Value |
|---|---|
| Branch | `audit/release-hardening-phase2-readiness` (from `develop`) |
| Base SHA / HEAD | `5ea519392352512c2c0bc866b2e14773530c6a2d` |
| `origin/develop` at audit time | `5ea51939` — `docs: verify backend runtime and critical MVP journey (#2670)` |
| Local `develop` | `5ea51939` — already synced; no fast-forward needed |
| **#2670 merge evidence** | `git log origin/develop` top commit = `5ea51939 docs: verify backend runtime and critical MVP journey (#2670)`. **PASS.** |
| Working tree | clean except two known local untracked files |
| Known untracked (left untouched) | `apps/web/AGENTS.md`, `apps/web/CLAUDE.md` — confirmed untracked / unstaged / unmodified at start and end; excluded from PR |

### Database safety (this audit created and dropped one disposable DB)

| Fact | Value |
|---|---|
| Server | PostgreSQL **18.0 (Homebrew)**, `127.0.0.1:5432` — local dev install |
| PostGIS | **3.6.0** available |
| Disposable DB created | `jinja_migration_audit_p2` (host `127.0.0.1`, user `admin`, engine `django.contrib.gis.db.backends.postgis`) |
| Proof local/dev | connection target `127.0.0.1`; no offsite DSN in `.env` / `.env.local` / `.env.test` (all `postgi?s?://…@127.0.0.1:5432/…`); server is a Homebrew local install |
| Cleanup | `DROP DATABASE jinja_migration_audit_p2` at end of audit — confirmed |
| Local `jinja_db` | **not migrated further** by this audit — still `0099` applied, `0100`/`0101` pending (unchanged from PR #2670) |
| Local QA-only runtime overrides (never written to a file, never committed) | backend `runserver` started once with `BILLING_STUB_PLAN=free BILLING_STUB_ACTIVE=0` then once with `…=premium …=1` for Phase 6; disposable user `rt_audit_tmp` (from PR #2670) reused for login |

---

## 2. Migration Source Contract

Read directly from source — `backend/temples/migrations/0100_*.py` (630 lines) and
`0101_*.py` (375 lines). **Neither migration has any schema operation** — each is a
single `migrations.RunPython(forward, reverse)`. Dependency chain is strictly
linear: `0099 ← 0100 ← 0101`.

### 0100 — P8-A duplicate-shadow cleanup (101→22, 103→21, 104→49)

| Dimension | Contract |
|---|---|
| Rows touched (real remediation) | `ShrineInteractionLog` pk 2 → `shrine_id 22`; pk 4 → `shrine_id 21`; raw `DELETE FROM temples_shrine` for ids **101, 103, 104**. Shadow `place_ref` rows **kept** (orphaned — `DROP_SHADOW_ONLY`). Primaries 21/22/49 untouched. |
| Fail-closed policy | `P8_A_PRESTATE_POLICY = FAIL_CLOSED` — one atomic unit; any PRE failure raises `PreconditionViolation`; with `Migration.atomic=True` the whole `RunPython` rolls back and 0100 is not recorded. No repair, no guess, no partial cleanup. |
| The **only** clean no-op (forward) | shadow pks 101/103/104 **all absent** AND primary pks 21/22/49 **all absent** AND neither audited `ShrineInteractionLog` event (`user_id=1` + `detail_view` + `metadata.ctx=map` + exact `created_at`) exists **anywhere** → `return` (fresh / pre-seed lineage). |
| Fail-closed forward branches | shadows absent but any primary present → RAISE ("primaries-only is not a fresh lineage"); shadows absent but an audited IL event exists anywhere → RAISE; all three shadows present → full PRE (exact `name_jp`/`address`/`lat`/`lng`/`place_ref_id` per shadow; primary identity; **id 49 coordinate must equal the P8-C-corrected `(35.6717809, 139.799519)` — read-only, requires 0099 first**; every shadow zero-payload across ~11 relation tables + counters; exactly one audited IL per shadow 101 & 103, zero on 104) → mutate; partial shadow set → RAISE. |
| Reversibility | **Yes** — `cleanup_reverse` recreates the three shadow rows from a static embedded snapshot at their original pks, then moves the two IL rows back. Fail-closed reverse PRE (full audited post-forward shape must be exactly present). |
| Idempotent on re-run after a real forward? | **No** (shadows gone + primaries present → RAISE) — but Django never re-runs an applied migration, so this is not a defect. |
| `location` guard | `.only(...)` excludes `location` from every SELECT (prod `temples_shrine.location` is legacy `text` vs historical `PointField` → avoids `GEOSException`). |

### 0101 — P8-B remove non-shrine artefact id 105 (`広島市`)

| Dimension | Contract |
|---|---|
| Rows touched | raw `DELETE FROM temples_shrine WHERE id = 105`. `place_ref` row `ChIJu0_z7giZWjURcvfBz1DO5Ac` **kept** (`DROP_SHRINE_LINK_ONLY`). |
| Fail-closed policy | `P8_B_PRESTATE_POLICY = FAIL_CLOSED`, reversible single-row removal. |
| Clean no-op (forward) | Shrine pk 105 **absent** AND `place_ref` `ChIJu0_z7giZWjURcvfBz1DO5Ac` **absent** → `return`. |
| Fail-closed forward branches | pk 105 absent but that `place_ref` present → RAISE; pk 105 present → full PRE: exact `kind='shrine'` / `name_jp='広島市'` / `address='日本、広島県広島市'` / `lat=34.3852894` / `lng=132.4553055` / `place_ref_id`; every semantic text blank; every counter 0; `owner_id` NULL; `place_ref.snapshot_json['types']` **is a list containing `"locality"` and not `"place_of_worship"`** (strict — empty/absent/non-list → RAISE); **0 rows** in all 14 `Shrine`-FK relation tables (each checked only if its column exists) → delete. |
| Reversibility | **Yes** — `restore_artifact_reverse` recreates pk 105 from static constants and re-links the same `place_ref_id`; fail-closed reverse PRE. |

### Where the real-remediation pre-state comes from

Neither migration, nor any earlier migration, nor any seed in the `0001→0101`
chain creates shadows 101/103/104, artefact 105, or the two audited
`ShrineInteractionLog` rows. That pre-state exists **only in the production
database** (documented in `docs/audit/p8-identity-coordinate-remediation.md`
§3 "Production Fresh Read", "re-confirmed by a read-only Production PRE read for
this PR"). → **`PRESTATE_DEPENDENCY_IDENTIFIED`**: on any DB that does not already
carry the production P8 subject, 0100/0101 take the documented fresh-lineage
no-op path.

---

## 3. Clean DB Migration Result

| Item | Result |
|---|---|
| DB | `jinja_migration_audit_p2` — fresh, 0 tables before migrate, PostGIS 3.6 extension enabled, PostgreSQL 18 / `127.0.0.1` |
| `manage.py check` | `System check identified no issues (0 silenced).` |
| Full `migrate` (0001 → 0101, all apps) | **every migration `... OK`** — no warning, no traceback, no `PreconditionViolation` |
| `temples.0100_p8a_duplicate_shrine_shadow_cleanup` | **OK** |
| `temples.0101_p8b_remove_non_shrine_artifact_id105` | **OK** |
| `migrate --check` after | exit **0** (all applied) |
| `showmigrations temples` | `[X] 0100_…`, `[X] 0101_…` |
| Audited P8 pks on the clean DB | 21 / 22 / 49 / 101 / 103 / 104 / 105 → **all ABSENT** (total shrines = 0) → 0100 & 0101 took the **fresh-lineage clean no-op** path (explicitly supported by their source) |
| Dedicated migration tests (`pytest`) | `test_migration_0100_p8a_duplicate_shrine_shadow_cleanup.py` + `test_migration_0101_p8b_remove_non_shrine_artifact_id105.py` → **71 passed** — these construct the audited pre-state and verify the **real remediation** forward (`test_valid_forward_moves_logs_and_deletes_shadows`, `…_forward_succeeds`), reverse restore (`test_valid_forward_then_reverse_restores`), forward/reverse/forward determinism, `test_forward_leaves_primary_semantic_data_untouched`, and every fail-closed branch |

**Classification: `CLEAN_DB_PASS`.** Migrations `0001 → 0101` apply cleanly on a
genuinely clean PostGIS database; 0100/0101 no-op safely; the real remediation
path is covered by 71 passing tests.

---

## 4. Production-Representative Difference

| Shrine pk | Clean DB (`…audit_p2`) | Local `jinja_db` (the PR #2670 failure DB) | Production — per repo record (`p8-…-remediation.md` §3, §22.3, §23) |
|---|---|---|---|
| 101 | ABSENT | **`承認テスト神社`** / `東京都テスト区1-2-3` (QA fixture) | `給田六所神社` shadow (`place_ref` `ChIJl-MEep…`, zero-data) → **DELETED 2026-08-30** |
| 103 | ABSENT | **`重複検証神社`** / `千代田区重複1-1-1` (QA fixture) | `長太稲荷神社` shadow → **DELETED 2026-08-30** |
| 104 | ABSENT | **`重複検証神社`** / `中央区重複2-2-2` (QA fixture) | `富岡八幡宮` shadow → **DELETED 2026-08-30** |
| 105 | ABSENT | **`重複検証神社（別宮）`** / `港区重複3-3-3` (QA fixture) | `広島市` locality artefact (`types=["locality","political"]`) → **DELETED 2026-08-30** |
| 21 / 22 / 49 | ABSENT | PRESENT, identity matches the audited primaries; id 49 at `(35.6717809, 139.799519)` | PRESENT, unchanged `name_jp`/`address`; id 49 coordinate corrected by 0099 |
| `temples` migration head | `0101` (this audit) | `0099` applied; `0100`/`0101` **pending & fail-closed** | **`0101` applied** — `PRODUCTION_TEMPLES_HEAD = 0101_p8b_remove_non_shrine_artifact_id105` |

- **Local `jinja_db` fail-close cause (RF-1 from PR #2670):** ids 101/103/104 exist
  but hold **QA fixtures** (`承認テスト神社`, `重複検証神社`…), not the audited
  shadows and not absent → `_assert_shadow_identity` raises `PRESTATE_MISMATCH`.
  This is the fail-closed guard working **as designed** against non-audited data.
  Local `jinja_db` is simply behind the repo/production migration head. Not a
  product defect, not production-representative, not on any deploy path.
- **Production pre-state / post-state:** `p8-identity-coordinate-remediation.md`
  **§22** is a read-only preflight (Production head at `0094`; every 0095–0101
  forward PRE satisfied by the current / projected Production state; deploy
  mechanism resolved). **§23** records the applied result: the chain
  `0095 → 0101` **was applied to Production on 2026-08-30** (ledger 04:46:32–34
  UTC) via `manage.py migrate temples 0101 --noinput` (LOCAL_DIRECT runbook),
  `migrate` exit `0`, all `OK`, **no manual repair**. Post-deploy verification
  passed: raw `temples_shrine` 108 → **104**; ids 101/103/104/105 absent;
  21/22/49 present & unchanged; id 49 `= 35.6717809, 139.799519`; IL pk 2 →
  shrine 22, IL pk 4 → shrine 21 (each exactly one global match on its primary);
  shadow + artefact `place_ref` rows orphaned; canonical recommendation evidence
  intact.
- **This audit did not independently re-read the production database.** The
  production state above rests on the detailed in-repo §23 post-deploy
  verification record → **`PRODUCTION_PRESTATE_VERIFIED_BY_REPO_RECORD`**
  (not `UNVERIFIED` — strongly evidenced; not `RUNTIME_VERIFIED` by me).

---

## 5. Migration Release Risk

**`MIGRATION_RELEASE_SAFE`.**

Exact conditions supporting this:

1. **Production is already at `0101`.** `p8-identity-coordinate-remediation.md`
   §23: `PRODUCTION_TEMPLES_HEAD = 0101_p8b_remove_non_shrine_artifact_id105`,
   applied 2026-08-30, `migrate` exit 0, full post-deploy verification passed.
   Django will not re-execute a recorded-applied migration.
2. **Repo migration head == production migration head** at develop `5ea51939`:
   `0101` is the latest `temples` migration (no `0102+`); `users` at `0006`,
   `favorites` at `0002` — both already current on Production per §22.1.
   → **the next deploy has zero pending migrations.**
3. **A genuinely fresh DB applies `0001 → 0101` cleanly** — verified this audit
   (`jinja_migration_audit_p2`); 0100/0101 take the fresh-lineage no-op path.
4. **The only environment where 0100/0101 fail-close is local `jinja_db`**, whose
   pk 101/103/104/105 hold QA fixtures — the guard operating as designed against
   non-audited data. That DB is not production and not on any deploy path.

Residual: this audit did not independently re-read the production DB; item 1
rests on the in-repo §23 record.

---

## 6. Free-Tier Shrine Detail Runtime (@375px)

### Billing source-of-truth (traced before any env change)

```
Shrine Detail SSR  apps/web/src/app/shrines/[id]/page.tsx:282
  getBillingStatusServer()                 apps/web/src/lib/api/billing.server.ts
    fetch(${origin}/api/billings/status/)   apps/web/src/app/api/billings/status/route.ts
      IF  NODE_ENV != "production"  AND  NEXT_PUBLIC_FORCE_BILLING_PLAN === "premium"
          -> hardcoded { plan:"premium", is_active:true }         (short-circuit)
      ELSE
          -> bffFetchWithAuthFromReq(... "/api/billings/status/")  (proxy to backend)
             backend billing_state.get_billing_status()
             stub provider -> BILLING_STUB_PLAN / BILLING_STUB_ACTIVE  (env is truth)
  isPremiumActive = plan === "premium" && is_active === true     (boolean)
resolveAccessLevel(billing, isAuthenticated)   apps/web/src/lib/premium/accessLevel.ts
  !auth -> "anonymous" ;  premium+active -> "premium" ;  else -> "free"
```

**Why PR #2670 rendered premium:** its `apps/web/.env.local` had
`NEXT_PUBLIC_FORCE_BILLING_PLAN=free` — which is **not** `"premium"`, so the BFF
did **not** short-circuit; it proxied to the backend, whose `.env.local` had
`BILLING_STUB_PLAN=premium` / `BILLING_STUB_ACTIVE=1`. The **backend stub** was
the controlling layer.

### This audit — Free verified two ways

Backend `runserver` restarted with `BILLING_STUB_PLAN=free BILLING_STUB_ACTIVE=0`
(local QA runtime only, uncommitted):

- **Anonymous** (guest, no cookie) — `resolveAccessLevel → "anonymous"`.
- **Free** (logged in as disposable `rt_audit_tmp` via the web BFF login route) —
  `GET /api/billings/status/` → `{plan:"free", is_active:false, provider:"stub"}`;
  `GET /api/users/me/` → `rt_audit_tmp`. `resolveAccessLevel → "free"`.

### Free @375px result (identical for anonymous and free)

| Check | Result |
|---|---|
| Page loads / no crash | PASS |
| Page-level horizontal scroll | none (`scrollWidth == clientWidth == 375`, 0 offenders) |
| Reaches bottom | yes |
| `shrine-detail-premium-teaser` present | **1** (was **0** when premium) — text: "ここから、より深い意味へ / この神社が選ばれた深い理由と、あなたにとっての意味を深められます。 / ログインして意味を深掘りする" |
| Premium CTA | `/auth/login?returnTo=%2Fbilling%2Fupgrade` |
| `recommendation_meta` | **visible** — "この神社が1位の理由 / 近さや候補条件を含めた総合順位です。特に 悩みとの一致 が順位を押し上げています。" (free = `visible` per `cardVisibility.ts`) |
| Public shrine facts | visible — 御祭神 (乃木希典命, 乃木静子命), 由緒・歴史 with `period_text`, 出典 |
| `saved_record` | **visible** for free ("参拝お疲れさまでした / あなたの参拝が記録されました…") — anonymous = `hidden`, free = `visible`; correctly differentiated |
| **Premium content leak** | **NONE.** "③ 今回の相談との意味" (`personal_meaning` full body), "④ 参拝するときの視点" (`action_meaning`), `previous_comparison` / `history_shift` / `deep_reflection` — **all ABSENT** for free. The text under "神社との意味の接続" is `context_reason` (free = `visible` per policy), not gated content. `full_body_len` ≈ 949 (free) vs ≈ 1024 with §3/§4 (premium). |
| Access level / visibility captured | `accessLevel = "free"` / `"anonymous"`; gated meaning cards = `teaser`; `context_reason` / `recommendation_meta` = `visible`; `previous_comparison` etc. = `hidden` |

**No `STOP-C`** — no Premium content leakage on the Free tier.

### Observations (recorded as findings, see §14)

- **RH2-F3** — the Premium CTA on the **free-authenticated** view still reads
  "ログインして意味を深掘りする" and links via `/auth/login?returnTo=/billing/upgrade`,
  routing an already-logged-in user back through login. Copy / funnel defect
  (not a leak).
- The teaser renders as a **single consolidated block**, not per-semantic lines.

---

## 7. Premium Regression Smoke

Backend restarted with `BILLING_STUB_PLAN=premium BILLING_STUB_ACTIVE=1`; same
logged-in session; `/shrines/59?ctx=concierge&tid=803` reloaded @375px.

| Check | Result |
|---|---|
| `GET /api/billings/status/` | `{plan:"premium", is_active:true}` |
| `shrine-detail-premium-teaser` | **0** — no Free teaser seam |
| Upgrade CTA links | **0** — no duplicate / Free CTA |
| Full Meaning body | **present** — "③ 今回の相談との意味" and "④ 参拝するときの視点" both render |
| `recommendation_meta` | still visible |

Premium still renders the full body with no Free seam. The Free/Premium boundary
switches cleanly on `billingStatus`.

---

## 8. External API / Map Runtime — RF-5 Reclassification

The PR #2670 "blank light area" on Shrine Detail is **not a map** and **not
gated by any external-API flag**. It is:

```tsx
// apps/web/src/components/shrine/detail/ShrineDetailHeroCard.tsx:17
<div className="relative h-32 w-full bg-slate-100">
  {imageUrl ? (
    <Image src={imageUrl} alt={title} fill className="object-cover" ... />
  ) : null}
</div>
```

| Fact | Evidence |
|---|---|
| `bg-slate-100` is a hardcoded Tailwind light gray with **no dark-mode variant and no `--kt-color-*` token** | source; computed style at runtime `lab(96.286 …)` on the dark page |
| `imageUrl` (`heroImageUrl` in `ShrineDetailArticle.tsx:429/703`) is **always null** | the Shrine API returns **no image field at all** — `GET /api/shrines/59/` has no `image_url` / `photo_url` / `imageUrl`; a 20-shrine list scan found 0 with any image |
| Therefore the empty `h-32` light box renders on **every** shrine detail page | source + data |
| `NEXT_PUBLIC_DISABLE_EXTERNAL_APIS` has **zero consumers** in `apps/web/src` | `grep` — dead env var; enabling external APIs changes nothing |
| **No interactive map exists in current web source** | no `maplibre-gl` / `leaflet` / `mapbox` / `google.maps` import anywhere in `apps/web/src`; `MapPageClient.tsx` is a place-search + nearby-card list; Directions is a Google Maps **URL handoff** only (`GoogleMapRouteLink.tsx`, verified working in PR #2670) |

**RF-5 → `CONFIRMED_UI_DEFECT`** (not `BLOCKED_BY_ENVIRONMENT`). A theme-unaware
empty image placeholder, environment-independent, affecting 100% of shrine detail
pages in dark mode. No external credentials were needed, and none were created
(`STOP-D` not reached).

Map runtime check on Shrine Detail: **N/A — there is no map on Shrine Detail.**

---

## 9. Analytics Duplicate Verification — RF-6 Measurement

### Trigger (source)

`apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx:573` — one
`useEffect` fires every meaning `card_view` / `card_partial_view`. It has **no
dedupe guard** (no fired-ref, no impression key). Its 20-entry dependency array
includes referentially-unstable values — notably `resolvedSaveActionNode` (a
`useMemo`'d React node, recomputed when `visitSummary` changes) and the raw
arrays `freeMeaningBlockCardIds` / `premiumMeaningBlockCardIds` (alongside their
`…Key` string deps). A second effect at `:553` calls `getVisits()` async →
`setVisitSummary` → `resolvedSaveActionNode` recomputes → dep identity changes →
the analytics effect re-runs.

### Reproduction matrix (dev sink `localStorage["app:track:dev-events"]`, free-auth session)

| Case | Action | `card_view` per cardId | `shrine_detail_view` | Δ vs prior |
|---|---|---|---|---|
| **A** | Initial load, **no interaction** | **3×** (context_reason, shrine_meaning, consultation_summary, saved_record, recommendation_meta); `card_partial_view:personal_meaning` = **3×** | **1×** | baseline |
| **B** | Scroll fully down + back up, **no navigation** | 3× | 1× | **+0** |
| **C** | `resize` event; open Deep Dive panel ("質問する"); type into textarea | 3× | 1× | **+0** |
| **D** | Navigate to `/` then back to the detail page | **3×** (fresh page view) | 1× | new page view, still 3×/cardId |

- **Scroll alone does NOT re-emit** (Case B = +0). This **revises the PR #2670
  hypothesis** that events "re-fire on scroll" — that session's large repeat
  count came from re-navigating to the page several times, not scrolling.
- **In-page re-renders do NOT re-emit** (Case C = +0).
- The 3× is a **mount-time multi-fire**: mount (1) + React StrictMode dev
  double-invoke (1) + `getVisits` async settle → re-render (1). `next.config`
  does not set `reactStrictMode` → App Router default `true` in dev.
  **Production estimate: ~2× per page view** (mount + `getVisits` settle; no
  StrictMode).
- `shrine_detail_view` (a different, simpler effect) fires **exactly 1×** — page-level transition metrics are unaffected.

### Contract

`docs/analytics/analytics-card-events.md` §"dedupe responsibility" and §"firing
layer の責務" explicitly assign **"event dedupe" and "resultSetId 単位の重複防止"
to the firing-layer component**. There is no documented downstream dedupe by key
(`aggregateCardCtr` in `cardCtr.ts` has no live consumer — audit #2669).

### Classification: `ANALYTICS_DUPLICATE_CONFIRMED`

The same semantic impression (`cardId` + `shrineId` + `recommendationInstanceId`
+ `visibility` + `accessLevel`) re-emits ≥ 2× within one page view, with no
firing-layer dedupe as the contract requires.

**Impact estimate:**

- Shrine Detail `card_view` / `card_partial_view` impression counts for
  `context_reason`, `shrine_meaning`, `consultation_summary`, `personal_meaning`,
  `saved_record`, `recommendation_meta` inflated **~2× (prod)**.
- CTR denominators for those cards inflated ~2× → **CTR understated ~50%**.
- `personal_meaning` teaser → upgrade **Premium funnel** conversion understated.
- Result↔Detail comparison (`recommendation-result-detail-instrumentation-contract.md`
  §7 join) — the **Detail-side** exposure count is inflated ~2×, distorting any
  Result-impression / Detail-impression ratio.
- `shrine_detail_view` and page-level funnel: **not affected**.

No event name or dedupe code was changed (`STOP-E` respected).

---

## 10. Deployment Architecture (evidence)

### Frontend — Vercel

| Fact | Evidence |
|---|---|
| Linked Vercel project | `.vercel/project.json` — `projectName: "jinja-app-web"`, `projectId: prj_odAjGXc6…`, `orgId: team_T3yj…` (committed) |
| No `vercel.json` in repo | → build/output/env configured in the **Vercel dashboard** (auto-detected Next.js; `apps/web` app; `next build`) |
| Build command | `apps/web/package.json` → `"build": "next build"` |

### Backend — Render Web Service

| Fact | Evidence |
|---|---|
| Start command | `backend/start.sh` — prints `=== Render startup ===`, reads `RENDER_EXTERNAL_HOSTNAME`, ends `exec gunicorn shrine_project.wsgi:application --bind 0.0.0.0:${PORT} --workers … --timeout 120` |
| Container build | `backend/Dockerfile.web` — `python:3.11-slim` + GDAL / GEOS / PROJ / `libpq` / `postgresql-client` + `requirements.txt`. Its `CMD` (`migrate && runserver`) is the **docker-compose / local** default, **not** the Render path |
| Static files | `whitenoise==6.12.0` in `requirements.txt`; `STATIC_ROOT = BASE_DIR/"staticfiles"` |
| Migrations on start | `start.sh` runs `python manage.py migrate --noinput` **only** when `RUN_MIGRATIONS_ON_START=1` (default `0` → prints "Skipping migrations."). A read-only `showmigrations` diagnostics block runs earlier, wrapped so it cannot abort startup |
| One-shot gated ops | `RUN_STARTUP_CHECK`, `RUN_SHRINE_REFLECTION_REPAIR`, `RUN_FAVORITE_REPAIR_ON_START`, `RUN_FEATUREUSAGE_REPAIR_ON_START`, `RUN_BOOTSTRAP_ON_START` (→ `bootstrap_production_data` / `import_shrines_seed` + `backfill_goriyaku_tags`) — all default `0` |

### Repo automation

| Fact | Evidence |
|---|---|
| `.github/workflows/deploy.yml.disabled` | disabled — deployment is via provider push-integration + the manual migration runbooks, not a repo workflow |
| Active CI | `web-tests.yml`, `backend-tests.yml`, `backend-integration.yml`, `backend-pr.yml`, `mobile-ci.yml`, `codeql.yml`, `dependency-review.yml`, `readme-guard.yml`, `runner-smoke.yml` |
| Deploy docs | `docs/infra/render-startup.md` (normal deploy / migration deploy / repair+bootstrap flags), `docs/infra/env_policy.md`, `docs/audit/production-migration-local-execution-runbook.md` (marked 正本 / canonical) |

### Runtime configuration (`backend/shrine_project/settings.py`)

| Item | Handling |
|---|---|
| `ALLOWED_HOSTS` | env-driven; auto-appends `RENDER_EXTERNAL_HOSTNAME` and `.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | env-driven; auto-appends `https://{RENDER_EXTERNAL_HOSTNAME}` |
| `CORS_ALLOWED_ORIGINS` | env-driven (`django-cors-headers==4.9.0`) |
| `DATABASE_URL` | `dj_database_url` + PostGIS engine (`postgis://`) in prod; localhost in every committed `.env*` |
| Storage | `STORAGE_BACKEND` env — `local` (default) **or `r2`** → Cloudflare R2 via `django-storages` S3Boto3 (`R2_ENDPOINT_URL` / `R2_PUBLIC_BASE_URL` / AWS keys). `django-storages>=1.14.6` + `boto3` in `requirements.txt` → **durable object storage is supported**, env-gated |
| Billing / Map / Analytics vars | `BILLING_PROVIDER` + `BILLING_STUB_*` / `STRIPE_*`; `GOOGLE_MAPS_API_KEY` / `GOOGLE_PLACES_API_KEY`; `NEXT_PUBLIC_POSTHOG_KEY` / `_HOST` — all external, dashboard-set |

---

## 11. Migration-on-Deploy Path (incl. Render constraint)

| Question | Answer |
|---|---|
| Where does `manage.py migrate` currently run on deploy? | **Nowhere automatically.** `start.sh` skips it unless `RUN_MIGRATIONS_ON_START=1`. |
| Shell-free migration paths (Render free tier has no Shell) | **Two, both documented.** (1) **Render env-var toggle** — set `RUN_MIGRATIONS_ON_START=1`, trigger a manual deploy, wait for "migrations completed" in logs, set it back to `0`, redeploy (`docs/infra/render-startup.md`). (2) **LOCAL_DIRECT** — an operator runs `manage.py migrate` from `backend/` with `USE_GIS=1` and the production `DATABASE_URL` sourced inside a command subshell (`docs/audit/production-migration-local-execution-runbook.md`, canonical). |
| Was a real migration deploy performed this way? | **Yes** — `p8-…-remediation.md` §23: the full `temples` chain `0095 → 0101` applied to Production on **2026-08-30** via LOCAL_DIRECT, `migrate` exit 0, full post-deploy verification passed. |
| 0100/0101 implications for the **next** deploy | **None.** Production is at `0101`; repo head is `0101`; the next deploy has no pending `temples` migrations. RF-1 (local `jinja_db` fail-close) is off the deploy path. |
| Partial-apply semantics | each of `0095…0101` is its own `RunPython` in its own transaction (`Migration.atomic=True`, PostgreSQL) → if migration *N* raises, *N* rolls back and is not recorded; `0095…N-1` remain applied; `migrate` exits non-zero and (toggle path) `start.sh` `set -e` aborts before gunicorn. Recoverable by fixing the cause and re-running (every fail-closed migration re-validates its full PRE). (`p8-…-remediation.md` §22.6) |
| Render Shell proposal | **not made** — this document proposes no "SSH into Render and run migrate" procedure. |

---

## 12. Deployment Readiness

**`DEPLOYMENT_READY_WITH_EXTERNAL_CONFIGURATION`.**

- The repo is **sufficient**: a Render start command (`start.sh` → gunicorn), a
  container build (`Dockerfile.web`), static serving (`whitenoise`), env-aware
  `ALLOWED_HOSTS` / `CORS` / `CSRF`, optional durable storage (`STORAGE_BACKEND=r2`),
  two documented Shell-free migration paths, a data-bootstrap gate, and a linked
  Vercel project (`.vercel/project.json`).
- A **real production deployment path is evidenced end-to-end** — the P8
  migration chain was applied to Production on 2026-08-30 with full post-deploy
  verification (`p8-…-remediation.md` §23). "No `render.yaml` / `vercel.json` /
  active deploy workflow" does **not** mean the app cannot deploy — deployment is
  **provider-dashboard-managed**.
- **External / unverifiable from this environment:** the Vercel and Render
  dashboard configuration (service settings, build commands) and all production
  secrets (`DATABASE_URL`, `R2_*`, `STRIPE_*`, `GOOGLE_*`, `NEXT_PUBLIC_POSTHOG_*`,
  the concrete `ALLOWED_HOSTS` / `CORS` / `CSRF` values). No provider dashboard
  was accessed (`STOP-F` / `STOP-G` respected).

---

## 13. Release Hardening Matrix

| Item | Previous state | Current state | Evidence | Release impact |
|---|---|---|---|---|
| **0100 clean DB** | `UNVERIFIED` (PR #2670 RF-1: fail-closed on local `jinja_db`) | **`CLEAN_DB_PASS`** | full `migrate 0001→0101` on fresh `jinja_migration_audit_p2` → `[X] 0100`; 71 dedicated migration tests pass | none — no-op on fresh DB; already applied to prod |
| **0101 clean DB** | `UNVERIFIED` | **`CLEAN_DB_PASS`** | `[X] 0101` on the same fresh DB; tests pass | none |
| **Production migration pre-state** | `PRODUCTION_PRESTATE_UNVERIFIED` (PR #2670) | **`VERIFIED_BY_REPO_RECORD`** | `p8-…-remediation.md` §22 (preflight) + §23 (applied 2026-08-30, post-deploy verification passed) | none — prod head `= 0101 =` repo head; next deploy has no pending migrations |
| **Free Shrine Detail** | `UNVERIFIED` (local billing stub forced premium) | **`PASS` @375px, no leak** | teaser present, §3/§4 premium body absent, `recommendation_meta` + public facts visible, no h-scroll, reaches bottom; anon + free both checked | none functional; **RH2-F3** CTA copy/funnel |
| **Map / external API (RF-5)** | assumed `BLOCKED_BY_ENVIRONMENT` | **`CONFIRMED_UI_DEFECT`** | `ShrineDetailHeroCard.tsx:17` `bg-slate-100`, no dark token; Shrine API has no image field; `DISABLE_EXTERNAL_APIS` has 0 consumers; no map library in web source | **RH2-F1** — R3 cosmetic, dark mode, **every** shrine detail page |
| **Analytics duplicate (RF-6)** | `ANALYTICS_DUPLICATE_UNVERIFIED` | **`ANALYTICS_DUPLICATE_CONFIRMED`** | Cases A–D: 3× per cardId/page view in dev (~2× prod est.); scroll (B) and re-render (C) add **0**; no firing-layer dedupe vs `analytics-card-events.md` contract | **RH2-F2** — R3 metrics integrity (CTR denominators ~2×, funnel rates understated); no user-facing impact |
| **Deployment** | `DEPLOYMENT_PARTIAL` / "stub" (PR #2669) | **`DEPLOYMENT_READY_WITH_EXTERNAL_CONFIGURATION`** | `.vercel/project.json`, `start.sh`, `Dockerfile.web`, `render-startup.md`, LOCAL_DIRECT runbook, real 2026-08-30 deploy (§23) | provider-dashboard config + secrets external / not verifiable here |

---

## 14. Confirmed Findings

### RH2-F1 — `ShrineDetailHeroCard` empty image placeholder is theme-unaware and always rendered

- **Reproduction:** open any `/shrines/[id]` at 375px in dark mode — a ~128 px light-grey rectangle sits above "神社について".
- **Expected:** a hero image, or a graceful dark-theme placeholder, or no slot when there is no image.
- **Actual:** `<div class="relative h-32 w-full bg-slate-100"></div>` — empty; `bg-slate-100` is a hardcoded Tailwind light gray with no dark-mode variant / no `--kt-color-*` token; `imageUrl` is always null because the Shrine API exposes no image field.
- **Evidence:** `apps/web/src/components/shrine/detail/ShrineDetailHeroCard.tsx:17`; runtime `elementFromPoint` → `div.relative h-32 w-full bg-slate-100`, computed `lab(96.286 …)`; `GET /api/shrines/59/` has no `image_url`/`photo_url`; 20-shrine list scan → 0 with an image.
- **Severity:** R3 (cosmetic, but on 100% of shrine detail pages in dark mode).
- **Release impact:** visual polish only; no functional break. Reclassifies PR #2670 RF-5 from `BLOCKED_BY_ENVIRONMENT` to `CONFIRMED_UI_DEFECT`.
- **Follow-up:** WP-1.

### RH2-F2 — Shrine Detail meaning `card_view` events fire ~2×/page view (3× dev) with no firing-layer dedupe

- **Reproduction:** load `/shrines/59?ctx=concierge&tid=…`, no interaction; read `localStorage["app:track:dev-events"]` → each of `context_reason` / `shrine_meaning` / `consultation_summary` / `saved_record` / `recommendation_meta` `card_view` = 3×; `personal_meaning` `card_partial_view` = 3×; `shrine_detail_view` = 1×. Scrolling (Case B) and in-page re-render (Case C) add 0.
- **Expected:** one impression per card per page view (contract assigns dedupe to the firing layer — `docs/analytics/analytics-card-events.md`).
- **Actual:** the `useEffect` at `ShrineDetailArticle.tsx:573` has no dedupe guard; re-runs on mount + StrictMode (dev) + `getVisits` async settle.
- **Evidence:** measured Cases A–D; `ShrineDetailArticle.tsx:553` (`getVisits` → `setVisitSummary`), `:543` (`resolvedSaveActionNode` useMemo), `:664-684` (dep array); `analytics-card-events.md` §"dedupe responsibility".
- **Severity:** R3 (analytics integrity — inflated impressions ~2×, CTR understated ~50%, Premium-teaser funnel and Result↔Detail join distorted; no user impact).
- **Release impact:** dashboards / experiment readouts for Shrine Detail card metrics are biased until deduped.
- **Follow-up:** WP-2.

### RH2-F3 — Free-authenticated Premium CTA uses "ログイン" copy and routes via `/auth/login`

- **Reproduction:** log in as a non-premium user, open `/shrines/[id]?ctx=concierge&tid=…` — the teaser CTA reads "ログインして意味を深掘りする" and links to `/auth/login?returnTo=%2Fbilling%2Fupgrade`.
- **Expected:** an already-authenticated free user should see upgrade-oriented copy and go straight to `/billing/upgrade`.
- **Actual:** login-oriented copy + a login round-trip for a logged-in user.
- **Evidence:** runtime DOM on the free-auth session (§6); `authedUser: "rt_audit_tmp"`, `billing.plan: "free"`.
- **Severity:** R3 (funnel friction + copy; no content leak).
- **Follow-up:** WP-3.

### RH2-F4 — `NEXT_PUBLIC_DISABLE_EXTERNAL_APIS` is a dead env var

- **Reproduction:** `grep -rn "DISABLE_EXTERNAL_APIS" apps/web` → only the `.env` files; 0 consumers in `apps/web/src`.
- **Expected:** either the flag gates external calls, or it is removed.
- **Actual:** set to `1` in `apps/web/.env.local` but read by nothing.
- **Evidence:** `grep`; also no `maplibre-gl` / `leaflet` / `mapbox` import anywhere in `apps/web/src` despite `NEXT_PUBLIC_MAP_PROVIDER=maplibre` and the roadmap's "MapLibre GL JS" claim.
- **Severity:** R4 (config hygiene / doc-vs-code drift).
- **Follow-up:** WP-4.

### RH2-F5 — Local `jinja_db` cannot advance past `0099` (QA-fixture pre-state)

- **Reproduction:** `cd backend && python manage.py migrate temples` against local `jinja_db` → `0100` raises `PRESTATE_MISMATCH: shadow pk 101 name_jp is '承認テスト神社', expected '給田六所神社'`.
- **Expected (dev experience):** a local dev DB can reach the repo migration head.
- **Actual:** local `jinja_db` holds QA fixtures at pk 101/103/104/105; the fail-closed guard (correctly) refuses.
- **Evidence:** §4 table; `showmigrations temples` → `0100`/`0101` `[ ]`.
- **Severity:** R0 (environment / dev-experience only — **not** a product defect; production and fresh DBs are unaffected).
- **Follow-up:** WP-5.

*(No STOP condition was triggered: no clean-DB migration failure (STOP-A), no unknown/production DB connection (STOP-B), no Premium leak on Free (STOP-C), no new credential/paid service (STOP-D), no analytics fix started (STOP-E), no production secret/env change (STOP-F), no provider dashboard action (STOP-G).)*

---

## 15. Still Unverified

| Item | Reason |
|---|---|
| Production DB state | not independently re-read this session — rests on the in-repo `p8-…-remediation.md` §23 post-deploy verification record |
| Vercel + Render dashboard configuration & all production secrets | external to the repo; no provider dashboard accessed |
| Production `STORAGE_BACKEND` value (local vs `r2`) and R2 wiring | env-gated; the concrete production value is not in the repo |
| Whether any shrine anywhere has a hero image | the Shrine API exposes **no image field at all** — likely a data-model gap upstream of RH2-F1's rendering defect; not resolved here |
| LLM recommendation path | `CONCIERGE_USE_LLM` default `False`; correct, and out of scope |
| Production analytics delivery (PostHog) | dev sink only (PostHog initialises only in a production build with a key) |

---

## 16. Follow-up Work Package Candidates

> Unordered. Returned to Mother Ship.

### WP-1 — `ShrineDetailHeroCard` empty-state + shrine image field decision (RH2-F1)
- Give the `h-32` slot a `--kt-color-*` background and a placeholder graphic (or omit the slot) when `imageUrl` is null; separately decide whether the Shrine serializer should expose an image URL at all.
- Files: `apps/web/src/components/shrine/detail/ShrineDetailHeroCard.tsx`; possibly `backend/temples/api/serializers/*shrine*` + model.
- Scope: S (frontend empty-state) / M (if adding an image field end-to-end).
- Release impact: dark-mode visual polish on every shrine detail page.

### WP-2 — Firing-layer dedupe for Shrine Detail card_view analytics (RH2-F2)
- Add an impression guard (fired-`Set` keyed by `cardId` + `shrineId` + `recommendationInstanceId`, or a per-page-view ref) in the `ShrineDetailArticle` analytics effect, per `analytics-card-events.md` §"dedupe responsibility". Stabilise the effect deps (drop the raw arrays; keep the `…Key` strings; memoise `resolvedSaveActionNode` inputs).
- Files: `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx`; tests under `…/__tests__/`.
- Scope: S–M.
- Release impact: restores Shrine Detail impression / CTR / funnel accuracy.

### WP-3 — Free-authenticated Premium CTA copy + direct upgrade link (RH2-F3)
- When the viewer is authenticated and non-premium, show upgrade copy and link straight to `/billing/upgrade` (no `/auth/login` round-trip).
- Files: the Shrine Detail Premium teaser / CTA component (`ShrineDetailArticle.tsx` teaser region); shared CTA/href helper.
- Scope: S.
- Release impact: removes a funnel round-trip for logged-in free users.

### WP-4 — Remove dead `NEXT_PUBLIC_DISABLE_EXTERNAL_APIS` + reconcile map claims (RH2-F4)
- Delete the unused env var (or wire it), and correct `docs/core/roadmap.md`'s "MapLibre GL JS" statement to match the actual state (no map library in `apps/web/src`; `/map` is a place-search + nearby-card list; Directions is a URL handoff).
- Files: `apps/web/.env*` (local, uncommitted — or the committed `.env.example`), `docs/core/roadmap.md`.
- Scope: S.
- Release impact: config hygiene / removes doc-vs-code drift.

### WP-5 — Local dev DB refresh path so `0100`/`0101` stop blocking `migrate` (RH2-F5)
- Document (or script) a supported way to bring a QA-fixture-polluted local `jinja_db` to the repo migration head — e.g. a clean reseed from `import_shrines_seed` + backfills into a fresh DB, or a local-only fixture-reconciliation step. Production and fresh DBs are already fine.
- Files: `docs/` runbook; possibly a management command or Makefile target (implementation is a separate PR).
- Scope: S–M.
- Release impact: none on production; unblocks local development against the current chain.

---

## 17. Release Hardening Phase 2 Status

**`PHASE2_VERIFIED_WITH_LIMITATIONS`.**

Every Phase 2 checklist item moved from `UNVERIFIED` to a definite state:

- 0100 / 0101 clean-DB migration → **`CLEAN_DB_PASS`** (+ 71 migration tests).
- Production migration pre/post-state → **`VERIFIED_BY_REPO_RECORD`** (`p8-…` §23: applied 2026-08-30, post-deploy verification passed).
- Migration release risk → **`MIGRATION_RELEASE_SAFE`** (prod head == repo head == `0101`; next deploy has no pending migrations).
- Free-tier Shrine Detail runtime → **`PASS` @375px, no Premium content leak** (anonymous + free both checked); Premium regression → **PASS**.
- RF-5 (map / blank box) → **`CONFIRMED_UI_DEFECT`** (RH2-F1) — environment-independent.
- RF-6 (analytics duplicate) → **`ANALYTICS_DUPLICATE_CONFIRMED`** (RH2-F2) — ~2× per page view; scroll and re-render do not add.
- Deployment readiness → **`DEPLOYMENT_READY_WITH_EXTERNAL_CONFIGURATION`**.

**No release-blocking runtime defect was found.** RH2-F1 / F2 / F3 are R3
(visual polish, analytics-metric integrity, funnel copy); RH2-F4 is R4; RH2-F5 is
R0 (local dev environment only).

**Limitations:** the production database was not independently re-read this
session (production migration state rests on the in-repo §23 record), and the
Vercel / Render dashboard configuration plus all production secrets are external
and could not be verified from this environment. This is a technical finding, not
a launch decision.

---

## Appendix — Commands executed (verification only)

| Command | Result |
|---|---|
| `git fetch origin` / `git log origin/develop` | #2670 at `origin/develop` HEAD `5ea51939` |
| `psql … CREATE DATABASE jinja_migration_audit_p2` + `CREATE EXTENSION postgis` | clean PostGIS DB, 0 tables |
| `manage.py check` (clean DB) | no issues |
| `manage.py migrate` 0001→0101 + all apps (clean DB) | every migration `OK`; `migrate --check` → 0; `[X] 0100`, `[X] 0101` |
| `pytest test_migration_0100_*.py test_migration_0101_*.py` | **71 passed** |
| `psql … DROP DATABASE jinja_migration_audit_p2` | dropped (teardown) |
| `manage.py runserver` with `BILLING_STUB_PLAN=free …=0`, then `=premium …=1` | Free + Premium runtime QA (local, uncommitted) |
| Browser @375px: Concierge → Shrine Detail as guest, then logged in as `rt_audit_tmp` | Free/anon teaser present, no leak; Premium regression PASS |
| Analytics dev-sink reads (Cases A–D) | 3× per cardId/page view (dev); scroll/re-render +0 |
| `grep` — `DISABLE_EXTERNAL_APIS`, `maplibre-gl`, `bg-slate-100`, migration files, `start.sh`, `settings.py` | evidence in §2, §8, §10 |
| `npx tsc -p tsconfig.json --noEmit` (`apps/web`) — from PR #2670 lineage; re-run | exit 0 |

**Local dev mutations by this audit:** created + dropped `jinja_migration_audit_p2`
(disposable, local); started/stopped local `runserver` with temporary billing-stub
env; logged the browser session in as the pre-existing disposable `rt_audit_tmp`.
Local `jinja_db` migration state and data were **not** changed. No production
system was touched.
