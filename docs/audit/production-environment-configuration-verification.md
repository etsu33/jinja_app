# Production Environment Configuration Verification

> **Audit only. No production code / config / `.env` changed. No deploy, no
> migration run, no production DB write, no billing transaction.** The only repo
> change in the PR that introduces this file is this document.
>
> **No secret value is recorded anywhere in this document.** Environment items are
> reported only as `SET` / `NOT_SET` / `UNKNOWN` / `NOT_REQUIRED` /
> `UNVERIFIED_EXTERNAL_CONFIGURATION`.

---

## 1. Scope

Verify, ahead of Test Release Critical Journey QA:

- Repo deployment architecture (Render backend, Vercel frontend).
- Production backend reachability + runtime posture (read-only HTTP smoke).
- Production frontend reachability + the Browser → BFF → Backend request path.
- Presence (not values) of critical backend / frontend environment configuration.
- Production migration state, with attention to `temples/0102`.
- Security: `DEBUG`, CORS, CSRF, HTTPS, no client-side secret exposure.
- Geolocation production preconditions (secure context) — tie-in to RH3-4 (#2677).

**Not in scope / not touched:** Evidence Foundation, Recommendation, Ranking,
Meaning, Premium, Analytics schema, Geolocation re-implementation, MapLibre, IaC,
`render.yaml` / `vercel.json` creation, any deploy or migration execution.

---

## 2. Current commit

| Item | Value |
|---|---|
| Branch | `audit/production-environment-configuration` (from `develop`) |
| Base SHA / HEAD | `dbe686b1b245740e3ec9ab27c3c511c19eb44ce4` |
| `origin/develop` | `dbe686b1 docs: モバイルWeb現在地取得不具合の原因を監査 (RH3-4) (#2677)` |
| HEAD == origin/develop | yes |
| Working tree | clean except known untracked `apps/web/AGENTS.md`, `apps/web/CLAUDE.md` (untouched) |
| Duplicate PR / branch for this topic | none |
| Local `manage.py check` (repo baseline) | `System check identified no issues (0 silenced).` |

---

## 3. Deployment Architecture (repo evidence)

| Layer | Fact | Source |
|---|---|---|
| Backend | **Render** Web Service, GitHub-triggered deploy | `docs/infra/env_policy.md` ("Backend: Render"), `backend/start.sh` (`=== Render startup ===`, `RENDER_EXTERNAL_HOSTNAME`) |
| Backend start command | `backend/start.sh` → `exec gunicorn shrine_project.wsgi:application --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY} --timeout 120 --worker-tmp-dir /dev/shm` | `backend/start.sh:112` |
| Backend container | `backend/Dockerfile.web` (python:3.11-slim + GDAL/GEOS/PROJ/libpq + `requirements.txt`, `whitenoise`). `Dockerfile.web`'s own `CMD` (`migrate && runserver`) is the local/compose default, not the Render path. | `backend/Dockerfile.web` |
| Backend migrations on start | `start.sh` runs `python manage.py migrate --noinput` **only if `RUN_MIGRATIONS_ON_START=1`**; default `0` → "Skipping migrations." | `backend/start.sh:54-58`, `docs/infra/render-startup.md` |
| Backend migration deploy paths | (a) Render env-var toggle `RUN_MIGRATIONS_ON_START=1` → manual deploy → revert; (b) `LOCAL_DIRECT` operator run (`docs/audit/production-migration-local-execution-runbook.md`, canonical — used for the P8 chain 2026-08-30 per `p8-identity-coordinate-remediation.md` §23) | docs cited |
| Frontend | **Vercel**, project `jinja-app-web` (`projectId prj_odAjGXc6…`, `orgId team_T3yj…`), GitHub-triggered | `.vercel/project.json`, `docs/infra/env_policy.md` |
| IaC in repo | none — no `render.yaml` / `vercel.json` / root `Dockerfile`. Both services are **provider-dashboard-configured**. | `find` |
| Deploy CI workflow | `.github/workflows/deploy.yml.disabled` (disabled). Active CI is test/lint only. | `.github/workflows/` |

---

## 4. Render (production backend)

Public production URL: **`https://jinja-backend.onrender.com`** (referenced in repo
docs — not a secret).

| Item | Result / status |
|---|---|
| Service reachable | **YES** — `GET /` → 200, HTTP/2, TLS |
| `GET /api/` | 200 |
| `GET /api/shrines/?limit=1` | 200, valid JSON, **`count: 104`** |
| `GET /healthz/` | **200** (health endpoint exists) |
| `GET /api/schema/` | 200 |
| `GET /api/health/` | 404 (this path, seen in some docs, does not exist — `/healthz/` is the real one) |
| `GET /admin/` | 302 → login (expected) |
| `GET /<nonexistent>` | 404, **generic "Not Found" page, no Django traceback** → `DEBUG=False` |
| `GET /api/shrines/99999999/` | 404 (not a 500 traceback) |
| Deploy branch (Render dashboard) | **`UNVERIFIED_EXTERNAL_CONFIGURATION`** — not in repo; `env_policy.md` defers to "各サービスの設定を正本とする" |
| Build command (Render dashboard) | **`UNVERIFIED_EXTERNAL_CONFIGURATION`** |
| Start command (Render dashboard) | Repo provides `backend/start.sh`; the dashboard value is `UNVERIFIED_EXTERNAL_CONFIGURATION` but runtime behaviour (gunicorn, `RENDER_EXTERNAL_HOSTNAME` honoured, `DEBUG=False`, migrations skipped by default) is consistent with `start.sh`. |
| Migration method in effect | `start.sh` default skips migrations → migrations are applied out-of-band (env toggle or LOCAL_DIRECT). Current toggle state `UNVERIFIED_EXTERNAL_CONFIGURATION` (docs require it be left at `0`). |

Backend response security headers (on `/api/shrines/`): `x-frame-options: DENY`,
`x-content-type-options: nosniff`, `referrer-policy: same-origin`,
`cross-origin-opener-policy: same-origin`, `vary: origin` (CORS active). No
`Strict-Transport-Security` from Django (`SECURE_HSTS_SECONDS` not set in
`settings.py`) — mitigated: the browser never reaches this origin directly (§10).

---

## 5. Backend Environment (presence only — no values)

| Config | Evidence | Status |
|---|---|---|
| `DATABASE_URL` | `/api/shrines/` serves 104 real rows from Postgres; P8 remediation reflected | **SET** (inferred from live DB-backed responses) |
| `SECRET_KEY` | app runs, `/admin/` session redirect works | **SET** (inferred) |
| `DEBUG` | 404 → generic page, no traceback; clean JSON error bodies | **SET to `False`** (inferred; `settings.py` default is `True`, so it is explicitly overridden) |
| `ALLOWED_HOSTS` | `jinja-backend.onrender.com` serves 200 (no `DisallowedHost` 400); `settings.py` also auto-appends `.onrender.com` + `RENDER_EXTERNAL_HOSTNAME` | **SET / satisfied** |
| `CORS_ALLOWED_ORIGINS` | preflight `OPTIONS` from `https://jinja-app-web.vercel.app` → `access-control-allow-origin` echoed, `access-control-allow-credentials: true`; a random `https://evil.example.com` origin → **no ACAO** (not a wildcard) | **SET correctly** (explicit allowlist incl. the prod frontend origin) |
| `CSRF_TRUSTED_ORIGINS` | no CSRF fatal error observed; `settings.py` auto-appends `https://{RENDER_EXTERNAL_HOSTNAME}` | **SET / satisfied** (partial — no cookie-auth POST was exercised) |
| `BILLING_PROVIDER` | `/api/billings/status/` → `provider: "stripe"` (NOT `"stub"`), guest → `{plan:"free", is_active:false}` | **SET to `stripe`** — production billing is not in stub mode |
| `STRIPE_SECRET_KEY` / price / webhook secret | not exercised (no checkout, no real payment) | **UNVERIFIED_EXTERNAL_CONFIGURATION** |
| `STORAGE_BACKEND` / `R2_*` (Cloudflare R2) | no goshuin image loaded in the smoke; not observable externally | **UNVERIFIED_EXTERNAL_CONFIGURATION** |
| PostHog (`NEXT_PUBLIC_POSTHOG_KEY` / `_HOST`) — see §9 | client loads `us-assets.i.posthog.com` + posts to `us.i.posthog.com/e/` with a `phc_…` publishable key | **SET** (US region) |
| Google Maps / Places | Directions is a Google Maps URL handoff (no API key client-side). Places is used only by shrine-registration / ingest (admin, not Critical Journey). | **NOT_REQUIRED** for the Critical Journey |
| OpenAI / Concierge LLM | Mother Ship: LLM not required for MVP. `CONCIERGE_USE_LLM` default `False` → production concierge path is the heuristic. | **NOT_REQUIRED** (key state UNVERIFIED, non-blocking) |

---

## 6. Backend Runtime Smoke

All read-only `GET`. No write request was made to production.

| Route | Code | Note |
|---|---|---|
| `GET /` | 200 | reachable |
| `GET /api/` | 200 | DRF root |
| `GET /api/shrines/?limit=1` | 200 | JSON, `count: 104` |
| `GET /healthz/` | 200 | health OK |
| `GET /api/schema/` | 200 | OpenAPI schema served |
| `GET /admin/` | 302 | login redirect |
| `GET /<bad route>` | 404 | generic page, **no debug traceback** |

No fatal `5xx` observed. No debug information leak.

---

## 7. Migration State

| Fact | Value |
|---|---|
| Repo migration head (`temples`, production lineage `backend/temples/migrations/`) | **`0102_history_theme_assignment_foundation`** |
| `0102` content | a single `migrations.CreateModel("HistoryThemeAssignment", …)` — **pure schema, new isolated table**, no `RunPython` / `RunSQL`, no change to any existing table, no data touch. Its partial-unique constraint is on the new table only. |
| `0102` runtime consumer | **none** — PR #2675: `evidence_taxonomy.py` / `HistoryThemeAssignment` "はRecommendation / Ranking / Concierge のいずれからもimportされていない → ランタイム挙動への影響なし". `Shrine.history_theme` remains the Recommendation compatibility path. |
| `0102` production-apply record | **none found** in any `docs/`. PR #2675 states the `0102` migration "は本PRでの初回pushまで一度もpush/適用されていなかった". |
| Production migration head (observed) | **`temples/0101` confirmed** — `/api/shrines/` `count == 104` exactly matches `p8-identity-coordinate-remediation.md` §23 post-deploy verification (`RAW_SHRINE_COUNT = 104` after 0095→0101 applied 2026-08-30; ids 101/103/104/105 removed). |
| Production `0102` state | **`UNVERIFIED_EXTERNAL_CONFIGURATION`** — no DB / dashboard access. Likely pending (authored after the last recorded prod apply), but cannot be confirmed. |
| `0102` impact on Critical Journey QA | **none** — new empty table, no consumer on any Critical-Journey path. Its state does not block Concierge → Recommendation → Result → Shrine Detail → Directions → Save / Visit / Reflection. |
| Recommended action | Apply `temples/0102` to production (env-toggle or LOCAL_DIRECT runbook) as a standard **pre-Test-Release deploy step**. Low risk (isolated `CreateModel`). Not a Critical Journey QA blocker. |
| CI NoGIS lineage | `backend/temples/migrations_nogis/0009_historythemeassignment.py` mirrors `0102` for the CI-only NoGIS mode (`docs/audit/production-migration-modules-nogis-root-cause.md`). Not a production artefact. |

**Do not run migrations as part of this audit — status only.** Status: production
at `0101` (observed), `0102` pending/unknown (non-blocking for QA).

---

## 8. Vercel (production frontend)

Public production URL: **`https://jinja-app-web.vercel.app`**.

| Item | Result / status |
|---|---|
| Project | `jinja-app-web` (linked; `.vercel/project.json`) |
| Reachable | **YES** — `GET /` → 200, HTTP/2, `server: Vercel`, `x-vercel-cache: HIT` |
| SSR routes | `GET /shrines/49` → 200, 0 redirects; `GET /concierge` → 200; `GET /compass` → 200 |
| BFF routes served by Vercel | `GET /api/shrines/?limit=1` → 200; `GET /api/billings/status/` → 200 |
| Framework | Next.js (Turbopack build; `_next/static/immutable/*` chunks) — consistent with `apps/web/package.json` (`"build": "next build"`) |
| HSTS | `strict-transport-security: max-age=63072000; includeSubDomains; preload` present on the frontend |
| Production branch (Vercel dashboard) | **`UNVERIFIED_EXTERNAL_CONFIGURATION`** |
| Build / output / Node version (Vercel dashboard) | **`UNVERIFIED_EXTERNAL_CONFIGURATION`** (runtime is consistent with a standard Next.js build) |

---

## 9. Frontend Environment (presence / routing — no values)

`NEXT_PUBLIC_*` referenced in client code (all public-by-design; none is a
server secret): `NEXT_PUBLIC_API_BASE`, `NEXT_PUBLIC_API_BASE_URL`,
`NEXT_PUBLIC_APP_URL`, `NEXT_PUBLIC_APP_VERSION`, `NEXT_PUBLIC_BASE_URL`,
`NEXT_PUBLIC_SITE_URL`, `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST`,
`NEXT_PUBLIC_FORCE_BILLING_PLAN`, `NEXT_PUBLIC_DEMO_MODE`,
`NEXT_PUBLIC_ENABLE_DEBUG_PAGES`, `NEXT_PUBLIC_ENABLE_CONCIERGE_DEBUG_PANEL`,
`NEXT_PUBLIC_DEBUG_LOG`.

| Config | Evidence | Status |
|---|---|---|
| Backend connection (client) | `apps/web/src/lib/api/http.ts:60` — `base = process.env.NEXT_PUBLIC_API_BASE || "/api"`. Observed: browser calls **`jinja-app-web.vercel.app/api/*`** only. | **SET to a BFF-relative base** (`/api`, or unset) — browser does **not** call the Render origin |
| Backend connection (server) | `lib/server/backend.ts`, `lib/api/*.server.ts` use server-only `DJANGO_ORIGIN` / `BACKEND_ORIGIN` / `DJANGO_API_BASE_URL` | **SET** (inferred — BFF proxy returns backend data) |
| PostHog | client loads `us-assets.i.posthog.com/array/phc_…/config.js` and posts to `us.i.posthog.com/e/` | `NEXT_PUBLIC_POSTHOG_KEY` + `_HOST` **SET** (US) |
| `NEXT_PUBLIC_FORCE_BILLING_PLAN` | inert in a Vercel production build — the BFF short-circuit is gated on `NODE_ENV !== "production"`; prod billing returned real `provider: "stripe"` | not a production risk |
| `NEXT_PUBLIC_ENABLE_DEBUG_PAGES` / debug panels | value in Vercel prod not observed | **UNVERIFIED_EXTERNAL_CONFIGURATION** (low risk; noted for the dashboard checklist) |
| Guard scripts | `apps/web/package.json` has `guard:no-backend-direct` and `guard:no-next-public-in-server` (block direct `:8000` refs outside server/BFF dirs, and `NEXT_PUBLIC_*` in `src/lib/server` / `src/app/api`) | present |

---

## 10. Frontend → Backend Path

```
Browser (https://jinja-app-web.vercel.app)
  └── fetch("/api/…")                    ← BFF-relative (NEXT_PUBLIC_API_BASE unset or "/api")
        └── Vercel-hosted Next.js route (apps/web/src/app/api/**/route.ts)
              └── server-side fetch → Render backend (DJANGO_ORIGIN / BACKEND_ORIGIN)
                    https://jinja-backend.onrender.com/api/…
```

Runtime evidence (production, loaded `https://jinja-app-web.vercel.app/shrines/49`):

- Client API calls observed: `jinja-app-web.vercel.app/api/shrine-interactions/`,
  `jinja-app-web.vercel.app/api/visits/`, `jinja-app-web.vercel.app/api/billings/status/`.
- **Zero** browser requests to `jinja-backend.onrender.com`.
- `GET https://jinja-app-web.vercel.app/api/shrines/?limit=1` returns the same body
  as `GET https://jinja-backend.onrender.com/api/shrines/?limit=1` → BFF proxy works.
- Client JS bundle scan (14 chunks): **0** occurrences of `jinja-backend.onrender.com`.

**Contract holds: Browser → Vercel BFF → Render Backend.** No backend-only origin
or server-only endpoint is exposed to the browser.

---

## 11. Security

| Aspect | Result |
|---|---|
| HTTPS — frontend | TLS, HTTP/2, **HSTS** `max-age=63072000; includeSubDomains; preload` |
| HTTPS — backend | TLS, HTTP/2. No Django `SECURE_HSTS_SECONDS` / `SECURE_SSL_REDIRECT` in `settings.py` — **mitigated**: the browser only ever reaches the backend via the Vercel BFF (server-to-server), never directly. |
| Client-side secret exposure | **None found.** 14 client chunks scanned: 0 Stripe `sk_live`/`sk_test`, 0 AWS `AKIA…`, 0 OpenAI `sk-…`, 0 `DJANGO_SECRET_KEY`, 0 `R2_*` secret, 0 `onrender.com` origin. Only public value present: PostHog `phc_…` publishable key (safe in client). |
| `NEXT_PUBLIC_*` misuse | None — every `NEXT_PUBLIC_*` in client code is public-by-design. `guard:no-next-public-in-server` enforces the boundary in CI. |
| Django `DEBUG` | **`False`** in production (404 → generic page, no traceback; clean JSON error bodies). |
| `ALLOWED_HOSTS` | satisfied (200, no `DisallowedHost`); `settings.py` auto-appends `.onrender.com` + `RENDER_EXTERNAL_HOSTNAME`. No wildcard `*` observed. |
| CORS | Explicit allowlist. Preflight from the prod frontend origin → allowed with credentials; random origin → rejected (no ACAO). `CORS_ALLOW_CREDENTIALS = True`. Not `CORS_ALLOW_ALL`. |
| CSRF | No CSRF fatal error observed on the read-only smoke. `CSRF_TRUSTED_ORIGINS` auto-appends the render origin. **Partial** — a cookie-authenticated POST was not exercised against production (deliberately, to avoid a write). |
| Mixed content / HTTP↔HTTPS mismatch | none — all observed requests are `https:`. |
| Backend security headers | `x-frame-options: DENY`, `x-content-type-options: nosniff`, `referrer-policy: same-origin`, `cross-origin-opener-policy: same-origin`. |

---

## 12. Geolocation Production Preconditions (RH3-4 tie-in)

On `https://jinja-app-web.vercel.app` (production), measured in-page:

| Precondition | Result |
|---|---|
| `location.protocol` | `https:` |
| `window.isSecureContext` | **`true`** |
| `'geolocation' in navigator` | **`true`** |
| Origin type | a normal secure web origin — `getCurrentPosition` / `watchPosition` are available |

**The production environment satisfies the geolocation secure-context
requirement.** RH3-4 (#2677) found the mobile geolocation issue is a **code**
concern (missing `timeout` at `ranking` / `CompassClient.useDevice`), **not** a
production environment problem. GEO-1 (secure context) and GEO-9 (environment
configuration) are **not** contributing factors — confirmed here.

---

## 13. External / Unverified Items (provider dashboards — for Mother Ship / user)

Cannot be verified without Render / Vercel dashboard access:

| # | Item | Where to check |
|---|---|---|
| E-1 | **`temples/0102` production migration state** (apply it if pending — env toggle `RUN_MIGRATIONS_ON_START=1` deploy → revert, or LOCAL_DIRECT runbook). Non-blocking for Critical Journey QA. | Render env + a read-only `showmigrations` / `migrate --check` |
| E-2 | Render **deploy branch** (expect the release branch; confirm it matches intent) | Render dashboard → Settings |
| E-3 | Render **build command** and **start command** (expect `backend/start.sh`) | Render dashboard → Settings |
| E-4 | Render env: `RUN_MIGRATIONS_ON_START` currently `0` / unset (per runbook it must be) | Render dashboard → Environment |
| E-5 | Render env presence: `DATABASE_URL`, `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` (behaviourally confirmed here, but confirm they are literally set, not defaulted) | Render dashboard → Environment |
| E-6 | Render env: `BILLING_PROVIDER=stripe` (confirmed via runtime) + `STRIPE_SECRET_KEY` / `STRIPE_PRICE_ID` (or `STRIPE_PREMIUM_PRICE_ID`) / `STRIPE_WEBHOOK_SECRET` presence; Stripe **live vs test** mode | Render dashboard + Stripe dashboard |
| E-7 | Render env: `STORAGE_BACKEND` (`local` vs `r2`) + `R2_ENDPOINT_URL` / `R2_PUBLIC_BASE_URL` / R2 access keys — required for durable goshuin / user images in production | Render dashboard + Cloudflare R2 |
| E-8 | Vercel **production branch** + build settings + Node version | Vercel dashboard → Settings |
| E-9 | Vercel env: `NEXT_PUBLIC_API_BASE` unset or `/api` (confirmed via runtime — browser never hits `onrender.com`); `DJANGO_ORIGIN` / `BACKEND_ORIGIN` / `DJANGO_API_BASE_URL` set to the Render URL (server-only) | Vercel dashboard → Environment Variables |
| E-10 | Vercel env: `NEXT_PUBLIC_ENABLE_DEBUG_PAGES` / `NEXT_PUBLIC_DEMO_MODE` / `NEXT_PUBLIC_FORCE_BILLING_PLAN` **not** set to a debug/override value in production | Vercel dashboard → Environment Variables |
| E-11 | Backend `RUN_*_REPAIR` / `RUN_BOOTSTRAP_ON_START` flags all `0` in production | Render dashboard → Environment |

---

## 14. Final Verdict

### `PRODUCTION_ENV_VERIFIED`

for the purpose of proceeding to **Production URL Critical Journey QA**.

Basis (all runtime-observed on production):

- Frontend `https://jinja-app-web.vercel.app` reachable; SSR routes 200; HSTS present.
- Backend `https://jinja-backend.onrender.com` reachable; `/`, `/api/`,
  `/api/shrines/`, `/healthz/`, `/api/schema/` all healthy; no `5xx`; **`DEBUG=False`**.
- **Browser → Vercel BFF → Render Backend** path confirmed; browser makes **zero**
  direct calls to the Render origin; client bundle carries **no** backend origin
  and **no** secret.
- **CORS** is a correct explicit allowlist (prod frontend allowed with
  credentials; foreign origin rejected).
- **Production billing provider is `stripe`** (not stub); a guest resolves to
  `free / inactive` correctly.
- **PostHog analytics is live** in production (US region, publishable key).
- Production DB is at **`temples/0101`** (shrine count `104` matches the P8
  post-deploy verification) — a coherent, remediated schema.
- **Geolocation secure-context precondition is satisfied** on the production
  origin.
- No client-side secret exposure; `DEBUG=False`; CORS/CSRF/HTTPS coherent.

Caveats carried forward (do not block Critical Journey QA, must be closed before
Test Release):

1. **`temples/0102`** production apply state is `UNVERIFIED_EXTERNAL_CONFIGURATION`
   (likely pending). It is an isolated new table with **no Critical-Journey
   consumer**, so Critical Journey QA can proceed; apply it as a standard
   pre-Test-Release deploy step (§7, E-1).
2. Dashboard-only items E-2 … E-11 are `UNVERIFIED_EXTERNAL_CONFIGURATION` — a
   human must confirm them in the Render / Vercel / Stripe / Cloudflare consoles
   before Test Release. Runtime behaviour is consistent with all of them being
   correctly set, but this audit cannot see the dashboards.
3. CSRF was only exercised read-only; a cookie-authenticated POST path against
   production is left for the Critical Journey QA (Save / Visit / Reflection).
4. R2 storage (E-7) is unverified — if `STORAGE_BACKEND=local` in production,
   goshuin / user images are not durable across Render restarts (not a Critical
   Journey blocker; a Test Release data-durability concern).

---

## 15. Files changed

`docs/audit/production-environment-configuration-verification.md` (this file)
only. **No production code, no test, no config, no `.env`.**
