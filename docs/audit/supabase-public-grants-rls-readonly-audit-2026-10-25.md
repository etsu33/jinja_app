# Supabase public schema GRANT / RLS / Data API exposure — read-only audit 2026-10-25

## Scope and authority

Mother Ship requested **read-only audit** of public exposure, GRANT and RLS. Supabase project `kami-musubi-db` (`uigvlbwnsthqqklzpfml`), region ap-northeast-1. Read-only metadata from authenticated Supabase `get_advisors(type=security)` and **SELECT-only catalog queries** (`pg_class`, `pg_namespace`, `pg_policies`, `has_*_privilege`, `current_setting`). No user records, tokens, secrets or session values read. No schema/role/GRANT/RLS/API configuration changes; no public request probing.

## Findings, direct evidence

| Control | Verified read-only result | Meaning / limit |
| --- | --- | --- |
| `public` objects, tables & views | 61 `pg_class` objects (`relkind` r/p/v/m) | Inventory scope only |
| RLS disabled | 59 `public` tables with `relrowsecurity=false` | Supabase security advisor independently reports **59 `rls_disabled_in_public` findings (ERROR, EXTERNAL)** |
| `anon` SELECT | 61/61 objects return `has_table_privilege('anon',oid,'SELECT')=true` | Database-grant capability, **not proof of public API response** |
| `anon` write | 61/61 have one or more of INSERT/UPDATE/DELETE | Database-grant capability; not proof of writable API |
| `authenticated` SELECT / write | 61/61 have relevant privileges | Broad role-level grants |
| `public` schema USAGE | `anon`, `authenticated`, `service_role` = true | USAGE prerequisite, not API exposure proof |
| `pg_policies` in public | 0 policies | RLS policies absent for checked schema |
| `pgrst.db_schemas`, `pgrst.db_anon_role` | `current_setting(..., true)` returned NULL | Configuration not exposed by queried database session, **Data API exposed-schema setting remains UNVERIFIED** |

Spot-check on `public.auth_user`, `django_session`, `temples_conciergethread`, `temples_conciergemessage`, `temples_goshuin`, `temples_goshuinimage`, `token_blacklist_outstandingtoken`, `users_userprofile`: all RLS disabled and `anon` SELECT/INSERT/UPDATE/DELETE privileges return **true**. These contain or may contain sensitive classes of records; no row content was inspected.

**Security judgment:** HIGH-PRIORITY POTENTIAL UNAUTHORIZED READ/WRITE if `public` is included in Data API exposed schemas and accessible API keys are obtainable. Evidence demonstrates broad GRANT with RLS off; actual exposed-schema config, usable credentials, gateway behavior, network access, and real unauthorized access remain **UNVERIFIED**. Do **not** assert proven data leakage, breach, exploitation, or API reachability.

## Trust boundaries

Supabase docs: API authorization is layered: exposed schema, GRANT, and RLS. Existing projects may have permissive default grants in `public`; disabling RLS while privileges exist can remove row-level isolation. https://supabase.com/docs/guides/api/securing-your-api . Security advisor finding reference: https://supabase.com/docs/guides/database/database-linter?lint=0013_rls_disabled_in_public .

## Required next read-only audit (separate approval if request probes)

1. Verify Data API exposed schemas via Supabase Dashboard **Integrations → Data API → Settings**, record setting name and timestamp, without copying API keys.
2. Verify public frontend config and Django DB connection role **without revealing credentials**; determine Django dependence on `public` and roles. Use read-only configuration metadata only.
3. Inspect effective role grants/default privileges, table-by-table and function EXECUTE/SECURITY DEFINER where needed; assess API exposure of non-`public` schemas.
4. If exposed `public` is confirmed, classify affected objects and execute a separately approved mitigation plan **before** using any live API probe. Avoid probes that read personal data or write DB rows.
5. Separate migration/PR for least-privilege GRANT, exposed-schema reduction and/or RLS after Django behavior impact analysis, regression tests and recovery planning. **Never bulk-enable RLS or REVOKE across Django tables without explicit Mother Ship authorization.**

## STOP

- This is **read-only finding and documentation**, not remediation.
- A-0 / L4-O / L4-E = **NOT APPROVED**; EU-8=A unchanged.
- No database permissions, schema, RLS, API settings, secrets, runtime, deploy, rollback or Production traffic modified.
- Security risk merits prioritization as a **separate access-control gate**, independent of MS-8/MS-9 evidence storage selection.
