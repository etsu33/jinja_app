# Web/Mobile間接API通信とDjango DBロール/GRANT追加監査（2026-10-25）

## Authority and scope

Mother Ship request: read-only indirect API communication audit and effective Django role-to-GRANT comparison. Baseline `develop@7cf17823c053102e5f20c18f4d2fc672948267e7`. GitHub source/code search and Supabase **SELECT-only metadata query**. No personal data, secrets or DATABASE_URL values acquired. No live API request, DB mutation, runtime, production or configuration changes. A-0/L4-O/L4-E = NOT APPROVED.

## Indirect communication findings

| Source | Static evidence | Conclusion/limit |
| --- | --- | --- |
| Web `apps/web/src/lib/api/client.ts:5-6` | axios `baseURL: '/api'` | App's same-origin API, **not** direct Supabase Data API |
| Web `apps/web/src/lib/server/backend.ts:6,125` | `DJANGO_ORIGIN` / `BACKEND_ORIGIN` / local default, server-side fetch | Django BFF network path exists; actual configured env endpoint not inspected |
| Mobile `apps/mobile/lib/http.ts:2-3,40,78,98,124` | `EXPO_PUBLIC_API_BASE_URL` with local Django default; JWT refresh and other calls through this base | Target is env-dependent; built app's actual URL unverified |
| Other Web usages | `fetch(` in `apps/web/src/lib/api/`, `axios` wrappers, PostHog analytics provider, map-related features | Static searches did not find Supabase SDK, `createClient`, `SUPABASE_URL`, `rest/v1`, or `postgrest` in Web/Mobile. Dynamic/third-party traffic remains unverified |
| Package dependencies | `apps/web/package.json`, `apps/mobile/package.json` | Supabase-specific SDK not observed |

**Result:** no discovered direct or indirect Supabase PostgREST dependency in inspected Web/Mobile paths. This is **STATIC/SEARCH-SCOPED** only, not exhaustive proof that API can be disabled. Production env and distributed Mobile builds not inspected.

## DB roles: independently observed metadata

Supabase PostgreSQL `pg_roles` read-only inspection:

| Role | rolcanlogin | rolbypassrls | Interpretation |
| --- | --- | --- | --- |
| postgres | true | true | Strong DB role, bypasses RLS |
| authenticator | true | false | Login capability; PostgREST role switching is distinct |
| anon | false | false | API request role |
| authenticated | false | false | API authenticated request role |
| service_role | false | true | API service role, privileged |

Previously verified `public` catalog grants: `anon` and `authenticated` SELECT plus write permissions across 61 objects; 59 tables without RLS. Mother Ship Supabase UI screenshot confirmed `public` and `graphql_public` in Data API exposed schemas. The **authorization risk remains high priority**, regardless of Django's code-level non-use of Data API.

Mother Ship reported `DATABASE_URL` exists on Render `jinja-backend`, `DB_USER`/`POSTGRES_USER` absent, and candidate pooler URI username `postgres.uigvlbwnsthqqklzpfml`. This may route to PostgreSQL `postgres`, but it is **not** an independently observed live Django `current_user`. Therefore **effective Django role-to-GRANT mapping is NOT VERIFIED**. This audit does not assume bypass-RLS rights are actually used by Django.

## DB grant design implications

- Django runtime ORM: target-table DML, sequences, schema and PostGIS usage as needed.
- Django migration: additional DDL/ownership privileges; `backend/start.sh` executes `manage.py migrate --noinput` in existing startup path. Splitting roles requires separate deployment/startup review.
- Data API `anon`/`authenticated` broad grants are **not required merely because Django ORM needs table access**. Django's own DB privileges must be assessed independently from API grants.
- No GRANT/RLS revocation or Data API change until inventory, impact tests and mother ship approval. Do not inspect secret URLs, personally identifiable rows or test public access using live sensitive endpoints without explicit additional authorization.

## Next evidence and STOP

1. Owner-approved redacted live Django `current_user` or connection `settings_dict['USER']` attestation (role only) in separate authorized, safe process; currently unavailable without touching runtime/config.
2. Complete indirect source tracing across all third-party and release-configured clients, especially Mobile release build env.
3. Docs-only remediation design with exact per-table GRANT and migration compatibility, safe rollback and test gates.
4. CI/diff review before PR merge, which requires explicit Mother Ship decision.

A-0 / L4-O / L4-E remain NOT APPROVED. No runtime, environment, DB GRANT/RLS, deployment or Production modifications.
