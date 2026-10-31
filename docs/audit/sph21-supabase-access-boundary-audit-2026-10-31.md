> **Status: Audit record (read-only)**
>
> Security Gate SPH-21. Supabase / PostgreSQL access-boundary audit. Evidence gathering only: no SQL against
> production, no user record read, no GRANT / REVOKE / ALTER, no RLS or Supabase configuration change,
> no environment change.
>
> - Audit date: 2026-10-31
> - Audited code: `develop` @ `f7ebe46981bb7c2f56fd72a7af209380de0d1fc3` (includes Gate P3 and #3389)
> - Method: static reading of code, configuration and repository documents; local model-metadata inventory
>   (Django `apps.get_models()`, local process, no production connection). Earlier dated evidence is cited from
>   `docs/audit/supabase-security-advisor-review.md` (2026-07-08 screenshot provided by Mother Ship).
> - Not available in this session: Supabase Dashboard / Management API / catalog access, and `supabase.com`
>   documentation (blocked by the session's network policy). Statements about Supabase platform defaults below are
>   marked **general knowledge, not re-verified in this session**.

# SPH-21 Supabase Access Boundary Audit（2026-10-31）

## 1. Executive summary

- **Verified (repository; limited to the reviewed static evidence: code, dependency manifests, environment
  templates and migrations at the base commit):**
  - The application reaches the database only through Django: Web → BFF (Vercel) → Django (Render) → PostgreSQL
    (Supabase); Mobile → Django.
  - No Supabase client library and no Supabase URL / anon / service-role key are referenced by Web, Mobile or the
    backend code, or by any environment template in the repository.
  - The repository creates no database functions, views, triggers, RLS policies or grants. Only the `postgis` and
    `pg_trgm` extensions and indexes are created through migrations.
- **Verified (dated, 2026-07-08):**
  - The Supabase Security Advisor reported **"RLS Disabled in Public" (CRITICAL)** for tables including
    `auth_user`, `django_session` and `temples_visit` (`supabase-security-advisor-review.md`).
  - Its current state is UNKNOWN.
- **Unknown (decisive):**
  - Whether the Supabase Data API is enabled and exposes `public`.
  - Whether the `anon` / `authenticated` roles hold privileges on the application tables.
  - Which role Django connects as at runtime, and that role's attributes and effective privileges.
- **Combined risk (hypothetical, high impact):** if the Data API exposes `public` and those roles hold table
  privileges, then the Django authorization layer could be bypassed for user data. Such data includes password
  hashes, sessions, consultation history, birth data and visit history. Supabase has historically granted those
  roles privileges on tables created in `public` (general knowledge, not re-verified). This report does **not**
  claim a confirmed vulnerability: the preconditions are unverified.
- **Backup / PITR:** UNKNOWN (`supabase-backup-capability-gate.md`: `BACKUP_CAPABILITY_UNKNOWN`).
- **Verdict:** **INCOMPLETE — decisive evidence requires Mother Ship dashboard / catalog checks (§9, §11).**

## 2. System architecture and trust boundaries

| Hop | Evidence | Status |
| --- | --- | --- |
| Browser → Web BFF (Vercel) | `apps/web/src/lib/server/backend.ts` (`djFetch`), BFF route handlers | VERIFIED (code) |
| BFF → Django (Render) | `DJANGO_ORIGIN` / `BACKEND_ORIGIN` (`backend.ts:7`) | VERIFIED (code) |
| Mobile → Django | Mobile calls the backend API; no Supabase reference in `apps/mobile` (repository search) | VERIFIED (code) |
| Django → PostgreSQL | `DATABASE_URL` parsed by `dj_database_url` (`backend/shrine_project/settings.py:157-204`); ENGINE PostGIS / PostgreSQL | VERIFIED (code) |
| Database host | Supabase project referenced as `kami-musubi-db` (`production-db-auth-recovery-evidence-2026-10-22.md`) | VERIFIED (document) |
| Direct browser / mobile → Supabase | No `@supabase/*` dependency, no `supabase` reference in `apps/web`, `apps/mobile`, `backend/requirements*.txt`, `pnpm-lock.yaml`; no `SUPABASE_*` / `*ANON_KEY` / `*SERVICE_ROLE*` variable in code or `.env.example` files | **VERIFIED: none in repository** |
| Supabase Data API (PostgREST) | Not used by the application; platform-side state unknown | UNKNOWN |
| TLS to the database | No `sslmode` in settings; depends on `DATABASE_URL` parameters and server enforcement | UNKNOWN |
| Connection mode (direct vs pooler) and role | Not in repository | UNKNOWN |

The only `supabase` references in the repository are in `scripts/migration_safety/`. That guard refuses Supabase
hosts as restore targets; it is a local safety tool, not a runtime path.

## 3. Sensitive-data inventory (model metadata only)

All application tables are in schema `public` (Django default; no `db_table` schema qualification).
**Intended access model:** server-only, through Django with per-view authorization.
**Actual roles with access:** the Django connection role (UNKNOWN identity); `anon` / `authenticated`: UNKNOWN.
**RLS:** "disabled" was observed on 2026-07-08 for the tables marked †, and is UNKNOWN for the rest.

| Table | Data classification | Owner model | Evidence |
| --- | --- | --- | --- |
| `auth_user` † | Credentials (password hash), username, email, staff / superuser flags | per user | model metadata; Advisor 2026-07-08 |
| `django_session` † | Session keys and data | per session | same |
| `token_blacklist_outstandingtoken` / `_blacklistedtoken` | JWT identifiers / tokens, user FK | per user | model metadata |
| `users_userprofile` | Birth date / time / place, Stripe customer / subscription identifiers | per user | model metadata |
| `temples_conciergethread` / `temples_conciergemessage` | Consultation history (free text), `anonymous_id` | per user or anonymous id | model metadata |
| `temples_concierge_recommendation_log` | User FK, query, coordinates | per user | model metadata |
| `temples_conciergeusage`, `temples_featureusage` | Usage counters, user / `anon_id` | per user / anon | model metadata |
| `temples_weekly_presentation_snapshot` | User / `anonymous_id` | per user / anon | model metadata |
| `temples_visit` † | Visit history (user, time, thread) | per user | model metadata; Advisor 2026-07-08 |
| `temples_shrinereflection`, `temples_shrineinteractionlog`, `temples_actionevent` | User behaviour linked to user / thread | per user | model metadata |
| `temples_favorite` | Favourites | per user | model metadata |
| `temples_goshuin`, `temples_goshuinimage` | User-uploaded record metadata | per user (public flag) | model metadata |
| `temples_shrinesubmission` | User submissions (address, coordinates), reviewer FK | per user | model metadata |
| `django_admin_log` † | Admin actions, user FK | staff | model metadata; Advisor |
| `auth_group*`, `auth_user_groups` †, `auth_user_user_permissions` † | Authorization data | system | model metadata; Advisor |
| `temples_shrine` and knowledge / catalog tables (`temples_shrine*`, `temples_deity` †, `place_ref` †, `place_cache`, …) | Public catalog, operational data (no personal data except `temples_shrine.owner` FK) | system | model metadata |
| `favorites_favorite` †, `temples_shrine_deities` † | **Not in current models** (seen in Production by the Advisor) — legacy / drift tables | unknown | Advisor 2026-07-08 vs model metadata |

Totals: 58 model tables (including auto-created M2M and PostGIS `spatial_ref_sys` / `geometry_columns`). No user
record was read.

## 4. Data API exposure inventory

| Item | Status | Notes |
| --- | --- | --- |
| Data API enabled | UNKNOWN | Dashboard: Project Settings → Data API |
| Exposed schemas | UNKNOWN | Platform default has included `public` (general knowledge, not re-verified) |
| Application tables in an exposed schema | **Conditional:** every application table is in `public`, so all are reachable *if* `public` is exposed | §3 |
| `anon` / `authenticated` table, sequence, function privileges | UNKNOWN | Catalog check in §11 (D-1a) |
| Privileged keys in browser-exposed config | **VERIFIED SECURE CONTROL (repository):** no Supabase key of any kind is referenced | §2 |
| Database access restricted to backend services | PARTIAL: the application path is Django-only. Platform-side restriction (network restrictions, Data API) is UNKNOWN | — |

RLS is relevant only if untrusted roles can reach the tables: Django's own connection role is normally the table
owner or has BYPASSRLS, so RLS mainly matters for `anon` / `authenticated` through the Data API. Table privileges
(GRANT) and row policies (RLS) are separate controls; either one can close the path.

## 5. Database roles and privileges

| Item | Status |
| --- | --- |
| Role Django connects as at runtime | UNKNOWN (credentials are not in the repository; a prior audit inferred an owner-like role, not verified). The SQL Editor's `current_user` does not identify it; see D-1b (§11) |
| SUPERUSER / CREATEDB / CREATEROLE / BYPASSRLS, role memberships and table ownership of that role | UNKNOWN until D-1b |
| Separation of migration role vs runtime role | UNKNOWN (migrations run from the same service per `docs/infra/render-startup.md`; separate role not evidenced) |
| Unnecessary write / DDL privileges | UNKNOWN (runtime needs DML; DDL needed only when migrations run on start) |
| Old-credential invalidation after the 2026-10-22 reset | NOT_VERIFIED (`production-db-auth-recovery-evidence-2026-10-22.md`) |
| Database access logging / alerting | UNKNOWN |

## 6. RLS, policies, views and functions

| Item | Status | Evidence |
| --- | --- | --- |
| RLS on application tables | **VERIFIED FINDING (dated):** disabled on at least 15 `public` tables as of 2026-07-08; full list and current state UNKNOWN | Advisor screenshot |
| Policies created by the application | **NONE (VERIFIED, repository):** no `CREATE POLICY` / `ENABLE ROW LEVEL SECURITY` in migrations | migration search |
| Views / functions / triggers / SECURITY DEFINER created by the application | **NONE (VERIFIED, repository):** migrations contain only extension creation, indexes, table repair and drops (`RunSQL` in 0034, 0085, 0086, 0108) | migration search |
| "Function Search Path Mutable" / "Security Definer View" warnings | UNKNOWN (object names not captured; likely platform or extension objects) | Advisor review §2–3 |
| Extensions in `public` (`postgis`, `pg_trgm`) | VERIFIED (migrations). Exposure of extension functions via RPC is UNKNOWN | `0021`, `0025`, `0027`, `0036` |
| Supabase Storage | NOT APPLICABLE as far as repository evidence shows (no Supabase Storage usage) | repository search |
| Supabase Auth | NOT APPLICABLE as far as repository evidence shows (authentication is Django / SimpleJWT) | code |

## 7. Backup and recovery evidence

- Plan, automatic backups, retention, PITR and restore procedure: **UNKNOWN**. The prior gate classified this as
  `BACKUP_CAPABILITY_UNKNOWN` and listed the dashboard checks (`supabase-backup-capability-gate.md`).
- **Repository controls (VERIFIED):** `scripts/migration_safety/` provides a dump / isolated-restore workflow with a
  guard that refuses non-local and protected restore targets. It is a local procedure; no evidence of a production
  restore drill.

## 8. Confirmed findings

| ID | Finding | Classification |
| --- | --- | --- |
| SPH21-01 | RLS disabled on `public` tables holding user data (`auth_user`, `django_session`, `temples_visit`, …) per the Supabase Security Advisor | **VERIFIED FINDING (dated 2026-07-08); exploitability UNKNOWN** |
| SPH21-02 | Legacy tables present in Production but absent from current models (`favorites_favorite`, `temples_shrine_deities`) | **VERIFIED FINDING (dated); content / ownership UNKNOWN** |
| SPH21-03 | Application data path is Django-only; no Supabase key or client in browser / mobile / backend code | **VERIFIED SECURE CONTROL** |
| SPH21-04 | No application-created SECURITY DEFINER functions, views, policies or grants | **VERIFIED SECURE CONTROL** (repository) |

**SPH21-01 detail.**

- **Preconditions for real exposure (all unverified):**
  - the Data API is enabled;
  - `public` is exposed;
  - `anon` / `authenticated` hold privileges on these tables;
  - a caller holds the project's anon (publishable) key. That key is designed to be public, but it is not
    published by this repository.
- **Potential impact:** read or modify user data outside Django's authorization (credentials hashes, sessions,
  consultation history, birth data).
- **Affected component:** the Supabase project configuration, not application code.
- **Remediation:** see R-1 to R-3.
- **Runtime behaviour: UNKNOWN until D-1b (§11) identifies Django's runtime role and its effective privileges.**
  - Disabling the Data API is expected not to affect Django, because Django does not call the Data API.
  - Revoking `anon` / `authenticated` privileges is not automatically zero-impact. It would affect Django if its
    runtime role were one of those roles, a member of them, or otherwise depended on their grants.
  - Enabling RLS would affect Django unless its runtime role owns the tables (without `FORCE ROW LEVEL SECURITY`)
    or has BYPASSRLS.
- **Mother Ship approval:** required.

**SPH21-02 detail.**

- **Precondition:** the same exposure path as SPH21-01.
- **Impact:** stale user data (favourites) outside the current schema.
- **Remediation:** R-5, after a content review.
- **Runtime behaviour:** none.
- **Mother Ship approval:** required.

## 9. Unknowns and evidence gaps

1. The Data API's enabled state and exposed schemas.
2. `anon` / `authenticated` privileges on `public` tables, sequences and functions.
3. Current RLS state for every `public` table (the 2026-07 list was partial).
4. The Django connection role and its attributes; migration vs runtime role separation.
5. Network restrictions and SSL enforcement on the Supabase project; the `sslmode` in `DATABASE_URL`.
6. Plan, backups, PITR, restore procedure and the latest restore drill.
7. Database access logs and alerting.
8. Old-credential invalidation after the 2026-10-22 password reset.
9. Current Supabase platform defaults (official documentation not reachable in this session).

## 10. Proposed remediation PR breakdown (not implemented)

| ID | Change | Type | Runtime impact | Approval |
| --- | --- | --- | --- | --- |
| R-1 | Owner runs the read-only checks in §11 (D-1a platform / catalog, D-1b Django runtime role) and records results without credentials or user data | Ops evidence | None | Mother Ship |
| R-2 | Disable the Data API, or remove `public` from exposed schemas (Django does not use it) | Supabase config | Expected none for Django (it does not call the Data API); any unknown Data API consumer would break | Mother Ship |
| R-3 | Revoke `anon` / `authenticated` privileges on application tables / sequences / functions in `public`, and/or enable RLS without permissive policies on them (only after confirming the Django role is owner or BYPASSRLS) | DB change (migration or ops SQL) | **UNKNOWN until D-1b**; not to be treated as zero-impact before Django's runtime role and effective privileges are verified | Mother Ship |
| R-4 | Dedicated least-privilege runtime role for Django; separate migration role | Ops / config | Credential rotation required | Mother Ship |
| R-5 | Review and retire legacy drift tables (`favorites_favorite`, `temples_shrine_deities`) | DB change | None (not in current models) | Mother Ship |
| R-6 | Confirm backups / PITR and run a restore drill | Ops | None | Mother Ship |
| R-7 | Require TLS (`sslmode=require` or stronger) for the Django connection, if not already | Config | None expected | Mother Ship |

## 11. Mother Ship decision gates

- **D-1a (platform and catalog evidence, first).**
  - Supabase Dashboard: Data API on / off, and the exposed schemas.
  - Run these read-only catalog queries as the project owner. They read catalog metadata only, never table rows;
    record the results without secrets.
  - In the Supabase SQL Editor, `current_user` is the role that executes the editor's SQL (typically the project's
    administrative role). It is **not necessarily** the role Django uses at runtime, so the first query describes
    the editor role, `anon` and `authenticated` only. Django's role is identified separately in D-1b.
    - `SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls FROM pg_roles WHERE rolname IN (current_user, 'anon', 'authenticated');`
    - `SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relkind IN ('r','p','v','m') ORDER BY 1;`
    - `SELECT table_name, grantee, privilege_type FROM information_schema.role_table_grants WHERE table_schema = 'public' AND grantee IN ('anon','authenticated') ORDER BY 1, 2, 3;`
    - `SELECT n.nspname, p.proname, p.prosecdef FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.prosecdef AND n.nspname = 'public';`
- **D-1b (Django runtime role, read-only, no credentials).**
  - Goal: the role **name** and its attributes. Never record or paste a password, a connection string or
    `DATABASE_URL`.
  - Option 1: while the Render service is running, list the roles connected to the database:
    `SELECT DISTINCT usename, application_name FROM pg_stat_activity WHERE datname = current_database();`
    Then attribute the Django sessions to their role. Omit client addresses from the record.
  - Option 2: read only the user-name component of the configured connection in the Render dashboard, without
    copying the rest of the value.
  - Then, for that role name (shown as `<django_role>`), record:
    - `SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls, rolinherit FROM pg_roles WHERE rolname = '<django_role>';`
    - `SELECT r.rolname AS member_of FROM pg_auth_members m JOIN pg_roles r ON r.oid = m.roleid JOIN pg_roles u ON u.oid = m.member WHERE u.rolname = '<django_role>';`
    - `SELECT tableowner, count(*) FROM pg_tables WHERE schemaname = 'public' GROUP BY tableowner;`
  - Until D-1b is recorded, Django's runtime role and its attributes remain **UNKNOWN**. The runtime impact of
    R-3 also remains UNKNOWN.
- **D-2:** if D-1a shows exposure and D-1b is recorded, choose R-2 (configuration), R-3 (database), or both.
- **D-3:** decide the R-4 role separation and its credential-rotation window.
- **D-4:** decide R-5 (legacy tables) after a content review.
- **D-5:** confirm R-6 (backups / PITR) before any further schema change.
- **Network:** to let a future session verify current Supabase documentation, allow `supabase.com` in the
  environment's network settings.

## 12. Final verdict

**INCOMPLETE.**

- Within the reviewed static evidence (code, dependency manifests, environment templates and migrations at the
  base commit), the repository-side boundary shows Django-only access, no Supabase keys or clients, and no
  application-created privileged database objects. This does not cover provider-side configuration, objects
  created outside the migrations, or runtime state.
- Django's runtime role and its attributes remain UNKNOWN (D-1b). RLS or GRANT remediation must not be treated as
  zero-impact before they are verified.
- The decisive platform-side controls (Data API exposure, `anon` / `authenticated` privileges, current RLS state,
  role attributes, backups) cannot be verified without Mother Ship's dashboard or catalog access.
- SPH21-01 is high-impact if its preconditions hold and should be the first decision gate (D-1a / D-1b / D-2).

README.md, `docs/core/architecture.md` and `docs/core/roadmap.md` are unchanged: no authoritative contract change
was identified or approved.
