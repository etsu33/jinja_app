> **Status: Audit record (read-only)**
>
> This audit records the security controls and effective production configuration at a point in time.
> The current runtime/security contract lives in `docs/core/runtime-security-baseline.md`. The
> current behaviour of every item is defined by the implementation code and tests.
>
> - Audit date: 2026-10-29
> - Audited code: `develop` @ `b1b6612` (includes H-4 #3377, H-8 #3378, H-9 #3379 and the Shrine write-authorization fix)
> - Method: static reading of code and repository documents; local URL-resolver inventory (local process, no network);
>   read-only Vercel project metadata. **No requests to production, no exploit reproduction, no secret or user-data access.**
> - Changes: this document only. No application code, dependency, test, infrastructure, environment-variable or database change.

# Security Production Hardening Baseline Audit（2026-10-29）

## 0. Conclusion

- **No new Critical issue that can be disclosed publicly** was confirmed in the scope of this public document.
- The Shrine write-authorization fix is **VERIFIED** in the code: catalog writes are staff-only by default, whatever the route.
- **The main gap is fail-open code defaults.** `DEBUG` defaults to on, `SECRET_KEY` silently falls back, no `SECURE_*` settings exist, and the DRF default permission is `AllowAny`. Production is protected only if every environment variable is set correctly.
  - Of these, only `DEBUG=False` has external observational evidence (2026-10 audit).
  - The production value of `SECRET_KEY` is **UNKNOWN**. Prior evidence ("the app starts") also matches the fallback, so it is not evidence that the variable is set.
- **Infrastructure has many evidence gaps:** DB roles, Supabase Data API exposure, backups/PITR, logging and alerting are all UNKNOWN. These are classified as "unverifiable", not as "insecure".
- **Recommended priority** (for Mother Ship to decide): SPH-02 (fail-closed SECRET_KEY) → SPH-21 (Supabase API exposure check) → SPH-03 (HTTPS / cookie hardening) → SPH-07 (DRF default deny).

### Classification and severity definitions

| Classification | Meaning |
| --- | --- |
| VERIFIED | Control confirmed in code, with evidence |
| PARTIAL | Partly confirmed, or code is fine but production is unconfirmed |
| UNKNOWN | Cannot be judged from the repository or permitted evidence. Neither secure nor insecure is assumed |
| FINDING | A gap or weakness exists in the code or configuration |

Severity is a provisional proposal based on impact × preconditions. Code defaults, deployment-configuration evidence and effective production runtime values are recorded separately for each item.

## 1. Summary table

| ID | Component | Classification | Severity (proposed) | One-line summary |
| --- | --- | --- | --- | --- |
| SPH-01 | Django `DEBUG` | PARTIAL | Medium | Code default True; production False (external observation) |
| SPH-02 | Django `SECRET_KEY` | FINDING + UNKNOWN | High (conditional) | No fail-closed when unset; production setting unproven |
| SPH-03 | HTTPS / HSTS / cookies (Django) | FINDING | Medium | No `SECURE_*` / cookie `Secure` settings at all |
| SPH-04 | `ALLOWED_HOSTS` | FINDING | Low | Always adds `.onrender.com` and development hosts |
| SPH-05 | CORS / CSRF trusted origins | PARTIAL | Low | env-driven, credentials allowed; production values UNKNOWN |
| SPH-06 | JWT (SimpleJWT) | PARTIAL | Medium | Not configured, package defaults apply; signed with SECRET_KEY; no rotation |
| SPH-07 | DRF default permission | FINDING | Medium | Default `AllowAny` (fail-open) |
| SPH-08 | Public external-API proxies / route compute | FINDING | Low–Medium | Some public endpoints lack scope throttles (cost / availability) |
| SPH-09 | Throttle store | PARTIAL | Low | LocMem, per-process; disable switch via env |
| SPH-10 | Login throttle | FINDING (known: WS-06) | Medium | Per-username key only (reference) |
| SPH-11 | Admin / introspection endpoints | PARTIAL | Low–Medium | Admin at default path; public OpenAPI; whoami returns only the requester's own info |
| SPH-12 | Shrine write authorization | VERIFIED | — | Default-deny: staff only |
| SPH-13 | Anonymous Shrine ingest | FINDING (residual) | Low–Medium | Unauthenticated Shrine creation (rate-limited) |
| SPH-14 | Privileged deletion cascade | FINDING (residual) | Low | Staff deletion cascades to related data; no soft delete |
| SPH-15 | Next.js image optimisation | FINDING | Low | `dangerouslyAllowLocalIP: true`; development http patterns in all environments |
| SPH-16 | Next.js security headers | FINDING | Low–Medium | No CSP / frame-ancestors etc. |
| SPH-17 | BFF auth cookies | VERIFIED | — | HttpOnly / SameSite=Lax / Secure in production |
| SPH-18 | BFF → Backend trust boundary | PARTIAL | Low | Connection target and HMAC identity are env-driven; production UNKNOWN |
| SPH-19 | Vercel project | PARTIAL | Low | SSO protects non-custom-domain deployments; legacy projects exist |
| SPH-20 | Render runtime | PARTIAL | Low–Medium | start.sh does not print secrets; start command UNKNOWN; Dockerfile.web is a development server |
| SPH-21 | Database (Supabase) | UNKNOWN | High (conditional) | RLS / Data API exposure, role privileges, backups not verified |
| SPH-22 | Logging / observability | PARTIAL | Low | No error tracking or alerting found |
| SPH-23 | Secret management | PARTIAL (known residuals) | Medium | Unresolved items from baseline §14 remain |

## 2. Findings

### SPH-01 Django `DEBUG` — PARTIAL / Medium

- **Evidence:** `backend/shrine_project/settings.py:111` (`DEBUG = env.bool("DEBUG", default=True)`). `docs/audit/production-environment-configuration-verification.md` §Backend, the prior audit of 2026-10, which observed a 404 page without a traceback.
- **Confirmed facts:**
  - The code default is True.
  - Production behaviour was observed as `DEBUG=False` (prior audit, observed from outside).
- **Assumptions:** the production setting has not changed since that observation.
- **Impact:** if the env value is missing in some environment (e.g. a new service or a preview), tracebacks and settings information leak.
- **Current mitigations:** production env (observation); `start.sh` printing only selected settings.
- **Remediation PR:** `security/django-debug-fail-closed`. Default to False, and make development opt-in explicitly. Also add a startup check.

### SPH-02 Django `SECRET_KEY` fallback — FINDING (code) + UNKNOWN (production) / High (conditional)

- **Evidence:** `backend/shrine_project/settings.py:104-109`. When `DJANGO_SECRET_KEY` is unset, a fixed value written in the repository is used (outside CI/pytest as well).
- **Confirmed facts:**
  - No fail-closed exists: there is no `ImproperlyConfigured` when the key is unset.
  - SimpleJWT signs with `SECRET_KEY` (SPH-06).
- **Assumptions:** production has `DJANGO_SECRET_KEY` set. The prior audit's "SET (inferred)" is based on "the app starts", which the fallback also satisfies, so it **does not establish the value is set**.
- **Impact (conditional):** if the fallback were in effect in production, anyone could forge a signature for sessions or JWTs. Because the condition is unconfirmed, this is not concluded to be a vulnerability.
- **Current mitigations:** none in code. Operational config only (prior audit checklist E-5).
- **Next verification:** an owner confirms in the Render dashboard that `DJANGO_SECRET_KEY` **is set** (existence only; never record or show the value).
- **Remediation PR:** `security/secret-key-fail-closed`. Raise `ImproperlyConfigured` when unset outside DEBUG/CI/pytest, and add a test.

### SPH-03 HTTPS / HSTS / cookie security (Django) — FINDING / Medium

- **Evidence:** `backend/shrine_project/settings.py` (whole file). No `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` or `SECURE_REFERRER_POLICY` customisation. `SecurityMiddleware` is enabled (`settings.py:267-276`).
- **Confirmed facts:**
  - Django is not set up to emit HSTS or set the `Secure` attribute on cookies.
  - Django Admin uses session and CSRF cookies.
  - Mobile reaches the backend directly (per `authCookies.ts` comments and the architecture).
- **Assumptions:**
  - Render's edge terminates TLS (not confirmed in this audit).
  - The frontend's HSTS was observed in the prior audit (Vercel side).
- **Impact:** on an http downgrade path, admin session cookies or CSRF tokens may be sent in plaintext. Without the proxy header, `request.is_secure()` cannot reflect the original protocol.
- **Current mitigations:** HTTPS on Vercel and Render (prior audit). The browser mostly talks to the BFF.
- **Remediation PR:** `security/django-https-cookie-hardening`. Production-only settings: `SECURE_PROXY_SSL_HEADER` (scoped to the trust boundary), `SESSION/CSRF_COOKIE_SECURE`, and HSTS introduced in stages.

### SPH-04 `ALLOWED_HOSTS` — FINDING / Low

- **Evidence:** `backend/shrine_project/settings.py:427-435`.
- **Confirmed facts:** besides the env value, `localhost`, `127.0.0.1`, `0.0.0.0`, `web` and `.onrender.com` (all subdomains) are always added.
- **Impact:** reduces the Host-header validation scope. There is no feature here that builds URLs from the Host header (e.g. password-reset email), so the impact is limited.
- **Remediation PR:** `security/allowed-hosts-production-scope`. In production, allow only the explicit host plus `RENDER_EXTERNAL_HOSTNAME`.

### SPH-05 CORS / CSRF trusted origins — PARTIAL / Low

- **Evidence:** `backend/shrine_project/settings.py:438-466`.
- **Confirmed facts:**
  - `CORS_ALLOW_CREDENTIALS = True`.
  - The allowed list comes from env; the default is localhost only. Wildcards are not used.
  - `CSRF_TRUSTED_ORIGINS` automatically adds the Render origin.
- **UNKNOWN:** the actual production env values.
- **Remediation:** a configuration-check item only. A code PR is unnecessary, provided an operations checklist confirms the values.

### SPH-06 JWT (SimpleJWT) — PARTIAL / Medium

- **Evidence:**
  - No `SIMPLE_JWT` in `backend/shrine_project/settings.py`, so the package defaults of `rest_framework_simplejwt/settings.py` apply: access 5 min, refresh 1 day, `ROTATE_REFRESH_TOKENS=False`, HS256, `SIGNING_KEY=SECRET_KEY`.
  - `token_blacklist` is installed (`settings.py:242`).
  - `docs/core/runtime-security-baseline.md` §14 lists "refresh token revocation on logout: DEFERRED".
- **Impact:**
  - A refresh token leaked before logout stays valid for up to 1 day.
  - Signing security depends on SPH-02.
- **Remediation PR:** `security/simplejwt-explicit-config`. Pin the values explicitly; decide on rotation plus blacklist; revoke on logout (an existing DEFERRED item).

### SPH-07 DRF default permission `AllowAny` — FINDING / Medium

- **Evidence:** `backend/shrine_project/settings.py:332`. The local URL-resolver inventory (204 routes) found that authenticated or admin endpoints override the permission explicitly (`IsAuthenticated` / `IsAdminUser`).
- **Confirmed facts:** a new view that forgets a permission class becomes public (fail-open). The Shrine issue fixed this time is an example of the same pattern.
- **Remediation PR:** `security/drf-default-deny`. Change the default to `IsAuthenticated`, and add an allowlist test that pins the intentionally public endpoints. API contracts must not change.

### SPH-08 Public external-API proxies / route compute — FINDING / Low–Medium

- **Evidence:** local inventory.
  - Several `AllowAny` places/geocode endpoints (`backend/temples/api/views/search.py`, `backend/temples/api/views/geocode.py`) rely only on the default anon/user throttles, without scope throttles. Legacy aliases share the same handlers.
  - `RouteAPIView` has `throttle_classes = []` (`backend/temples/api/views/route.py:77`).
- **Impact:** amplified external API cost and route-compute load from anonymous traffic (cost / availability). Not a confidentiality or integrity issue.
- **Current mitigations:** default anon throttle (100/min, WS-04 client identity). The Google Places kill switch (`settings.py:404`).
- **Remediation PR:** `security/public-proxy-throttle-scopes`. Apply scope throttles uniformly to public proxies, and consider retiring legacy aliases.

### SPH-09 Throttle store — PARTIAL / Low

- **Evidence:** `backend/shrine_project/settings.py:364-367` (`DISABLE_THROTTLE`), `387-394` (LocMemCache, which presumes `WEB_CONCURRENCY=1`).
- **Impact:** if workers are added, the throttles are effectively multiplied. If the disable switch is mistakenly set in production, nearly every rate limit is lifted.
- **UNKNOWN:** production `WEB_CONCURRENCY` / `DISABLE_THROTTLE`.
- **Remediation:** before moving to multiple workers, move to a shared cache (separate PR). Fail-closed the disable switch in production.

### SPH-10 Login throttle — FINDING (known: WS-06) / Medium

- **Evidence:** `backend/users/throttles.py:6-14`, `backend/users/api/auth.py:7`, `docs/audit/ws04-throttle-client-identity-design-2026-10-25.md` §3.1 (WS-06).
- **Confirmed facts:** the key is a hash of the username only.
- **Remediation:** follow the existing WS-06 track; this audit does not duplicate it.

### SPH-11 Admin / introspection endpoints — PARTIAL / Low–Medium

- **Evidence:** `backend/shrine_project/urls.py:87` (`admin/`), `:91-92` (whoami ×2), `:96-120` (OpenAPI / Swagger / Redoc, `AllowAny`).
- **Confirmed facts:**
  - whoami returns only the **requester's own** authentication state, username and superuser flag. No information about other users is returned (VERIFIED).
  - Django Admin uses the default path and default authentication, with no additional rate limiting or MFA.
  - The OpenAPI schema is public.
- **Impact:**
  - Admin is a target for password guessing.
  - The schema gives an attacker information about the attack surface (it is not a vulnerability in itself).
- **Remediation PR:** `security/admin-surface-hardening`. Rate-limit admin login and consider an IP restriction or MFA. Gate the schema in production behind staff, or leave it as is; that is a Mother Ship decision.

### SPH-12 Shrine write authorization — VERIFIED

- **Evidence:**
  - `backend/temples/api/views/shrine.py:273-282`. Only `PUBLIC_ACTIONS = {list, retrieve, nearest, ingest}` are `AllowAny`; every other action is `IsAdminUser`.
  - `backend/temples/tests/api/test_shrine_write_authorization.py` checks every registered route for anonymous, ordinary and staff users.
  - Merged into develop as `b1b6612`, identical to the reviewed fix.
- **Confirmed facts:** the default-deny applies regardless of route, and also to actions added in future.
- **Production applicability:** whether the fix has been **deployed** to production is UNKNOWN; deployment was not confirmed in this audit.
- **Next verification:** Mother Ship confirms the production deploy and runs checks on the operations side (out of scope for this audit).

### SPH-13 Anonymous Shrine ingest — FINDING (residual) / Low–Medium

- **Evidence:** `backend/temples/api/views/shrine.py` (the `ingest` action: `AllowAny`, `shrines_ingest` throttle 1/min). `settings.py:330, 360-361, 364-367`: ingest stays throttled even under `DISABLE_THROTTLE`.
- **Confirmed facts:**
  - Unauthenticated users can create Shrine records from an external place ID. This is intended behaviour.
  - A `PlacesError` message is returned in the response. Its content is a fixed category or an upstream error message; the external API key is not included (`backend/temples/services/places.py:328-347`).
- **Impact:** catalog pollution and external API cost (bounded by the rate limit).
- **Remediation PR:** `security/shrine-ingest-authn`. Require authentication, or switch to the submission → review flow (needs a product decision). Fix the error message to a fixed category.

### SPH-14 Privileged deletion cascade — FINDING (residual) / Low

- **Evidence:** `ShrineViewSet` `destroy` (staff only), `backend/temples/models.py` (several `ForeignKey(Shrine, on_delete=CASCADE)`, e.g. around lines 506, 760, 1287, 1405).
- **Impact:** a staff mistake or a compromised staff account deletes other users' related data in a cascade. No soft delete or API deletion audit log exists.
- **Remediation PR:** `security/shrine-delete-safeguard`. Remove API deletion, or move to soft delete, plus an audit log. Changing the data model is a design decision.

### SPH-15 Next.js image optimisation — FINDING / Low

- **Evidence:** `apps/web/next.config.ts:16-34` (`dangerouslyAllowLocalIP: true`; `http://127.0.0.1:8000` and `http://localhost:8000` remotePatterns in every environment, defined twice).
- **Impact:** the image optimiser's private-network protection is turned off. remotePatterns limit the reachable targets, so SSRF is limited to the patterns listed.
- **Remediation PR:** `security/next-image-local-ip-dev-only`. Enable it and the development patterns only when `NODE_ENV !== "production"`.

### SPH-16 Next.js security headers — FINDING / Low–Medium

- **Evidence:** `apps/web/next.config.ts` (no `headers()`), no `vercel.json`. The prior audit observed HSTS on the frontend, provided by Vercel.
- **Confirmed facts:** there is no CSP, `frame-ancestors` / `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` or `X-Content-Type-Options` configuration in the repository.
- **Impact:** no defence in depth against XSS or clickjacking.
- **Remediation PR:** `security/web-security-headers`. Report-Only CSP → enforce in stages.

### SPH-17 BFF auth cookies — VERIFIED

- **Evidence:** `apps/web/src/lib/server/authCookies.ts:31-101`. All auth cookies are `HttpOnly`, `SameSite=Lax` and `Path=/`. `Secure` is set when production and https, based on `x-forwarded-proto`.
- **Note:** the access-token cookie lasts 1 hour, while the JWT access token lasts 5 minutes (refresh-driven); the lifetimes differ.
- **Production applicability:** behaviour on Vercel was not observed in this audit.

### SPH-18 BFF → Backend trust boundary — PARTIAL / Low

- **Evidence:**
  - `apps/web/src/lib/server/backend.ts:7`: the connection target is `DJANGO_ORIGIN` / `BACKEND_ORIGIN`, falling back to `http://127.0.0.1:8000`.
  - `apps/web/src/lib/server/clientIdentity.ts:43-75`: client identity is signed only when `VERCEL=1` and the HMAC secret is set.
  - `backend/shrine_project/settings.py:338-346`: on Render, startup stops on a misconfiguration (WS-04).
- **UNKNOWN:** whether the production env is set. The backend side is fail-closed; the BFF side, if unset, falls back to unsigned behaviour.

### SPH-19 Vercel project — PARTIAL / Low

- **Evidence (Vercel API, read-only, sanitised):**
  - Project `jinja-app-web`: Next.js, Node 24.x.
  - SSO protection is `all_except_custom_domains`; password protection is off; Trusted IPs are off.
  - Two older legacy projects (`v0-*`) exist under the same team.
- **UNKNOWN:**
  - Whether the legacy projects' deployments are still publicly reachable, and what their environment variables contain.
  - The production branch setting (the prior audit's E-items).
- **Remediation:** confirm whether the legacy projects can be deleted or archived (an operations task).

### SPH-20 Render runtime — PARTIAL / Low–Medium

- **Evidence:**
  - `backend/start.sh:7-15` prints only the presence of `DATABASE_URL` (a boolean) and does not print secrets (VERIFIED).
  - Write-capable startup flags are mutually exclusive and fail closed (`:58-119`).
  - `backend/Dockerfile.web:47` uses `CMD` with `migrate && runserver` (a development server).
- **UNKNOWN:**
  - Render's start command, and whether Dockerfile.web is used. The prior audit observed behaviour consistent with gunicorn.
  - The settings for health checks, auto-deploy and the deploy branch.
- **Impact:** if Dockerfile.web's CMD were used in production, it would mean the development server plus automatic migrations (not observed).
- **Remediation:** confirm the dashboard settings, and rename Dockerfile.web or mark it as development-only (separate PR).

### SPH-21 Database (Supabase) — UNKNOWN / High (conditional)

- **Evidence:**
  - `docs/audit/supabase-security-advisor-review.md` (2026-07, a previous audit): `RLS Disabled in Public` is CRITICAL in the Supabase advisor; the exposed schema and anon-key permissions were unverified.
  - `docs/audit/production-db-auth-recovery-evidence-2026-10-22.md`: the production DB password reset was reported; invalidation of the old credential is NOT_VERIFIED.
  - There is no Supabase client usage in the repository (static search).
- **Confirmed facts:** Django connects with a role close to the table owner (per the prior audit). The repository contains no evidence on DB role separation, network restrictions, SSL enforcement, backups/PITR or restore drills.
- **Impact (conditional):** if the Data API exposes the public schema, rows could be read or written with the anon key, independently of Django's authorization.
- **Next verification (owner, dashboard, values must not be recorded):**
  1. The Data API's exposed schemas.
  2. Whether the anon key is public, and its permissions.
  3. Network restrictions and SSL enforcement.
  4. Backups / PITR and the latest restore drill.
  5. Separation of the migration role from the runtime role.
- **Remediation PR:** decide after the checks. Disable Data API exposure or apply RLS (high impact, needs a design decision).
- **Supplement:** `docker-compose.yml` hardcodes a development DB password default value (values not reproduced). It is for local development only, but whether it is the same as the production password is UNKNOWN. Recommend moving it to `.env` (Low).

### SPH-22 Logging / observability — PARTIAL / Low

- **Evidence:**
  - `backend/shrine_project/settings.py:513-554`: console logging only; the `temples.services.google_places` logger is pinned to DEBUG.
  - `backend/temples/services/google_places.py:446-451`: query strings are masked in logs.
  - No error tracking or APM (e.g. Sentry) in `backend/requirements.txt` or `apps/web/package.json`.
- **UNKNOWN:** Render/Vercel log retention, access rights and alert settings.
- **Impact:** slower detection of, and investigation into, attacks and failures.
- **Remediation:** decide on adopting error tracking and alerts. Lower the DEBUG-level logger to INFO in production (separate PR).

### SPH-23 Secret management — PARTIAL (known residuals) / Medium

- **Evidence:**
  - `docs/core/runtime-security-baseline.md` §10, §14, §15.
  - Known DEFERRED items: hardcoded bootstrap credentials, archived CI credentials, past credentials in git history, and the temporary plaintext exposure of CI-generated credentials.
- **This audit:** did not list environment-variable values or names (Vercel environment variables were not fetched). No new secret exposure was observed; a full scan was not done.
- **Remediation:** continue the existing DEFERRED track. Running gitleaks as a CI gate is a separate decision.

## 3. Security architecture summary

### Trust boundaries

| Boundary | Components | Main controls (status) |
| --- | --- | --- |
| PUBLIC → Web (Vercel) | Browser → Next.js / BFF | HTTPS + HSTS (prior-audit observation); auth cookies HttpOnly/Lax/Secure (VERIFIED); no CSP (SPH-16) |
| PUBLIC → Backend (Render) | Mobile and direct access → Django/DRF | TLS (prior-audit observation); default AllowAny (SPH-07); per-endpoint authz (inventory); anon/user/scope throttles (WS-04) |
| BFF → Backend | Vercel server → Render | JWT forwarding; HMAC client identity (env-driven, SPH-18); CSRF (`web-bff-csrf-*` audits) |
| Backend → EXTERNAL | Google Places / Geocode, OSRM, Stripe, LLM | Stripe webhook signature verified, fail-closed when unconfigured (`backend/users/services/stripe_webhook.py:66-81`); Places key masked in logs; kill switch |
| Backend → DB | Django → Supabase Postgres | Role, network, RLS and backups UNKNOWN (SPH-21) |
| TRUSTED | Django Admin, staff API | Default path and default auth (SPH-11); Shrine writes staff-only (SPH-12) |

### Verified protections (VERIFIED)

- Shrine catalog writes are staff-only by default (SPH-12).
- Auth cookie attributes (SPH-17).
- The Stripe webhook checks signatures and refuses to run when unconfigured.
- whoami-type endpoints return only the requester's own information.
- `start.sh` prints no secrets, and its write-capable flags are mutually exclusive.
- The Places photo / proxy path does not include upstream exceptions in the response, and masks the query string in logs.

### Residual risks (provisional priority)

1. SPH-02 SECRET_KEY: production unconfirmed, no fail-closed in code.
2. SPH-21 Supabase API exposure and RLS: unconfirmed.
3. SPH-03 / SPH-06 / SPH-07: fail-open defaults.
4. SPH-13 / SPH-14: Shrine-related residuals.
5. SPH-08 / SPH-15 / SPH-16 / SPH-11: hardening.

### Evidence gaps (verification by the owner in dashboards; never record values)

- Render: whether `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_*`, `CSRF_*`, `WEB_CONCURRENCY` and `DISABLE_THROTTLE` are set; the start command; the deploy branch; log retention.
- Supabase: exposed schemas; anon-key permissions; network restrictions; SSL; backups/PITR; role separation; invalidation of the old credential.
- Vercel: production branch; environment-variable configuration; public reachability of the legacy projects.
- Production deployment of the Shrine authorization fix.

## 4. Follow-up audits (separate investigations; not fixed in this PR)

| ID | Topic | Current state | Next step |
| --- | --- | --- | --- |
| FU-SPH-A | Existing PostGIS integration test failure | `temples/tests/test_import_shrines_seed_command.py::test_production_float8_round_trip_difference_is_not_an_update` fails on `develop` (updated 1 / skipped 0, expected 0 / 1); unrelated to H-8 / H-9. With `--maxfail=1` the rest of the integration suite does not run, **so a full integration pass is unverified** | A separate audit identifies the cause (float8 round-trip comparison) and the scope of impact |
| FU-SPH-B | External consumers of the route API | The DRF 3.18.2 upgrade (#3379) changed the format of `POST /api/route(s)/` validation errors. No consumer exists in the repository; external consumers are UNKNOWN | Owner checks access logs for that endpoint (counts and User-Agent only, no personal data) |

## 5. Recommended updates to related core documents (this PR does not change them)

- **README.md:**
  - Add a link to this audit near line 71 (the description of where security audit records live).
  - Add one line saying that production config verification is tracked in `docs/audit/` evidence gaps (§3).
- **docs/core/architecture.md:**
  - Add one line near line 22 saying the DRF default permission is `AllowAny` and public endpoints are explicit overrides (SPH-07).
  - Add the Supabase Data API as a candidate external access path to the DB trust boundary (SPH-21).
- **docs/core/roadmap.md:**
  - Under Cross-cutting: Security Foundation (around line 441), add as Release Readiness prerequisites: SPH-02 fail-closed, the SPH-21 check, the SPH-03 HTTPS / cookie hardening, and the SPH-07 default deny.
  - Record that the Shrine authorization fix has been merged and that production deployment is still to be confirmed.
- **docs/core/runtime-security-baseline.md (reference):**
  - Add to §15 External Verification: Supabase Data API exposure and backups/PITR.
  - Add a contract to §4 that "public endpoints are maintained as an explicit allowlist".
