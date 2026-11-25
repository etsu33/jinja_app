# Supabase Data API exposure and Django effective DB role — read-only follow-up (2026-10-25)

## Scope and authority

Mother Ship requested read-only inspection of (1) exposed Data API schemas and (2) Django effective production DB connection role. Based on develop `7cf17823c053102e5f20c18f4d2fc672948267e7`, Supabase project metadata, SQL session metadata and existing GitHub source. **No database rows with personal information, credentials, environment variable values, Data API key values, public endpoint probes, DB mutations, permissions or runtime modifications read or made.**

## Outcome summary

| Requested item | Result | Why |
| --- | --- | --- |
| Data API exposed schemas | **NOT VERIFIED** | `current_setting('pgrst.db_schemas', true)` in privileged SQL session returned NULL. This **does not** prove disabled or private; Supabase project metadata connector does not expose configured Data API schemas. |
| Django production effective DB role | **NOT VERIFIED** | Django source defines env-driven DB configuration, but source alone does not reveal which environment settings are effective on Render. Render service inspection was blocked because no workspace was selected. |
| SQL audit session user | **VERIFIED: postgres** | Read-only SQL `current_user` and `session_user` both return `postgres`, `current_database()` is `postgres`; **not Django role proof**. |
| Relevant code dependency | **VERIFIED** | `backend/shrine_project/settings.py` lines ~144–205 uses `DATABASE_URL` parsed via `dj_database_url.parse` when present; else DB_USER/POSTGRES_USER fallback. No secret material retrieved. |
| Previously verified high-risk role grants | **STILL RELEVANT** | Prior #3341 read-only result: 59 RLS-off `public` tables and 61 public objects with anon grants. Exposure would depend on effective Data API configuration, key issuance and access path. No breach proven. |

## Safe evidence completion steps

1. Authenticated Supabase Dashboard → Project → Integrations → Data API → Settings. **Record only the exposed schema names and whether the Data API is enabled. Do not copy, reveal, or capture API keys.**
2. Render workspace selection must be explicitly confirmed by Mother Ship before service inspection. For selected Django service, verify **non-secret role name and database endpoint identity only**, not URL/password. If environment tools cannot safely redact values, **do not fetch raw env**; instead inspect an authorized redacted configuration report or use a separately approved safe method.
3. Compare configured Django role name with Supabase PostgreSQL roles and grants, ensuring no privileged `postgres` / `service_role` credential is exposed to web clients. This comparison alone does not authorize changes.
4. If `public` exposed schemas are confirmed, conduct a separately approved remediation impact analysis covering Django ORM, migration roles, PostgREST GRANT/RLS, rollback plan and protected tests. No live API probes reading private records, no write probes.
5. Track uncertainty explicitly: **not verified ≠ safe**; do not authorize CSRF aggregate schema creation nor any bulk REVOKE / RLS changes from this audit.

## STOP

This is **documentation-only**. A-0 / L4-O / L4-E = **NOT APPROVED**. No credentials, grants, RLS, schema, Data API settings, deploy, log, runtime, Production or restored configurations changed. Parent access-control audit PR #3341 remains separately reviewable.
