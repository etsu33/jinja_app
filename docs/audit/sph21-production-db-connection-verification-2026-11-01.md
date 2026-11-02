# SPH-21 follow-up: Production DB connection and privilege verification (2026-11-01)

> Status: **DESIGN ONLY / NOT RUN**. Supplements `docs/audit/sph21-supabase-access-boundary-audit-2026-10-31.md` (D-1b, R-7). This document does not authorize Production execution or changes.
> Source: Owner's 2026-11-01 Supabase dashboard observations, Codex read-only design review, existing SPH-21. No secrets collected.

## Goal and boundaries

Confirm (1) the actual Render Django database target without exposing `DATABASE_URL`, (2) TLS encryption and server identity validation separately, and (3) effective privileges of the actual runtime role and any future audit-only role. Do not mistake a successful Supabase SQL Editor TLS connection for the Render application's TLS status.

**Prohibited in this step:** output/copy full connection URLs or passwords; Production SQL execution; GRANT/REVOKE/CREATE ROLE; migrations; Render env changes, startup hooks, deploys, or service restarts; enabling Supabase Enforce SSL or adjusting network restrictions. All verification remains pending Mother Ship approval.

## Observed facts and unknowns

- Owner confirms Render `DATABASE_URL` exists, but deliberately did not share its value. The project is `kami-musubi-db` (Supabase ref `uigvlbwnsthqqklzpfml`).
- Supabase Session pooler is offered as an IPv4-supported candidate on port 5432, **not proven to be Render's actual connection method**.
- Owner observed Supabase `Enforce SSL = OFF` and no network restrictions on 2026-11-01. Changing either is out of scope.
- SQL Editor session reported TLSv1.3; separate `pg_stat_activity` output showed internal platform connections but did not identify Render. Render TLS and actual Django role remain **UNKNOWN**.
- Reviewed Django settings parse `DATABASE_URL` via `dj_database_url`; they do not explicitly force `ssl_require`. An explicit `sslmode` can be carried in URL options. Do not infer deployed TLS settings from this static finding alone.
- PR #3396 is reported merged into develop; this follow-up does not alter its audit guard.
- The earlier Codex design lived in a session scratchpad path and is **not assumed to be a durable repository artifact**. This is a source-limited formalization, not a verbatim copy.

## Gate 1: Secret-safe target identity comparison

**Operator-only, no production connectivity required.** In the private environment that already possesses the connection value, parse the URL and compare independently against the approved project and connection type. Do not paste the URL into ChatGPT, GitHub issues/PRs, shell history, logs, screenshots or terminal output. Never display URL userinfo, project ref, password or connection options containing credentials.

Record only:
- `target_project_match = PASS / FAIL / UNKNOWN` (verify the tenant project ref in pooler username, not merely the pooler hostname).
- `endpoint_kind = DIRECT / SESSION_POOLER / TRANSACTION_POOLER / UNKNOWN`.
- `port_match = PASS / FAIL / UNKNOWN`, `db_name_match = PASS / FAIL / UNKNOWN`.
- `role_category = ADMIN_LIKE / APP_DEDICATED / UNKNOWN` (never print a credential-bearing username).
- `sslmode_explicit = YES / NO / UNKNOWN`; and `sslmode_class = VERIFY_FULL / VERIFY_CA / REQUIRE / PREFER_OR_WEAKER / UNKNOWN`.
- Operator, timestamp, and environment reviewed, without connection string excerpts.

Pooler hostnames may serve multiple projects; hostname alone cannot prove tenant identity. Reject malformed URL or missing project identity as UNKNOWN, not PASS. A dashboard check is only configuration evidence and cannot conclusively prove the Django process's live role or transport. If the dashboard's Reveal control could expose a password, do not use it for a screenshot or shared session. Any locally executed parser must be reviewed first for credential redaction and use of hidden input; no such script is executed by this PR.

## Gate 2: TLS assurance

Distinguish:
1. **Client configuration:** Django effective `sslmode` (and relevant `sslrootcert` / driver options) in the actual runtime.
2. **Client-to-pooler (or direct DB) transport:** live client connection has TLS; collect only boolean/protocol, never `PGconn.info` in full (may contain credentials).
3. **CA validation:** issuer is trusted, with correct CA chain.
4. **Hostname verification:** verified against the exact endpoint hostname, including any pooler endpoint.

Pass for a future hardened audit connection requires `verify-full` with trusted CA/hostname success, unless Mother Ship explicitly approves a documented lesser control. `require` enforces encryption but is not a general guarantee of hostname validation. SQL Editor's `pg_stat_ssl` result confirms only that editor's connection; with poolers, backend `pg_stat_ssl` may not observe the application-to-pooler leg. Non-authenticated `openssl` examination is a candidate **only after** network and approval review and must not be mistaken for proof of Django's effective configuration. Existing Supabase SSL enforcement OFF is not permission to change it.

## Gate 3: Actual application role / effective privileges

First identify the actual Django DB role through D-1b (prefer secure operator-side parsing, otherwise approved live runtime check). SQL Editor `current_user` is not Django's identity. For an approved, catalog-only session review, inspect:
- `pg_roles` attributes (`rolsuper`, `rolcreatedb`, `rolcreaterole`, `rolbypassrls`, `rolinherit`, `rolcanlogin`).
- Effective inherited role privileges and roles reachable by `SET ROLE` (not just direct membership).
- `has_table_privilege` for SELECT/INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER on relevant tables, including ownership and public grants.
- `has_schema_privilege` for USAGE and CREATE; `has_database_privilege` for CONNECT/CREATE/TEMPORARY.
- Sequence access, executable `SECURITY DEFINER` functions, and default privileges for future objects.

Do not query user records, secrets, token tables' contents or other application data. Metadata is sufficient.

**Runtime role:** Django may need DML and migrations may currently run on startup; do not revoke its grants based on the future audit-role standard. **Future audit role:** separate LOGIN, non-superuser, no BYPASSRLS/CREATEDB/CREATEROLE, SELECT + schema USAGE on only required tables, no write/DDL/TEMP/role escalation. Verify owner and inherited grants. Creating the role or changing app connections requires a separate approved operation.

## Execution gates and outcomes

| Step | Scope | Status | Approval |
| --- | --- | --- | --- |
| Create/update this design document | repository docs only | Documented | Ordinary PR review |
| Private comparison of Render target identity | operator-only, no connection | NOT RUN | Mother Ship |
| Read-only Supabase catalog queries | Production metadata | NOT RUN | Mother Ship |
| Non-authenticated TLS handshake inspection | remote network access | NOT RUN | Mother Ship |
| Django runtime identity / TLS instrumentation | possible deployment changes | NOT RUN | Separate explicit approval |
| Enforce SSL / new role / database or environment changes | Production change | NOT RUN | Separate explicit approval |
| Evidence Coverage Audit PR #3396 Production run | Production reads | NOT RUN | Separate explicit approval and least-privilege role gate |

**Current outcome:** Render connection host/port/project and SSL mode **NOT VERIFIED**. DB effective role and its privileges **NOT VERIFIED**. STOP. Report failures as FAIL or UNKNOWN without guessing and do not auto-remediate.

## Source links

- SPH-21: `docs/audit/sph21-supabase-access-boundary-audit-2026-10-31.md` §§2, 5, 9, 10 (R-7), 11 (D-1b).
- Existing `docs/runbooks/evidence-coverage-audit.md` for the separate Production audit safety gate.
- Postgres libpq SSL behavior, Supabase pooler/SSL documentation: require independent live verification of current provider details before approval.


## Owner-approved operational verification: 2026-11-01

- **Verified Django runtime role, D-1b role identity:** the owner explicitly approved a one-shot read-only probe on Render `jinja-backend`. The deploy identified in the owner's 13:25 JST screenshot (commit `1246e91`) reached Live and emitted `[db-role-probe] current_user=postgres session_user=postgres` at approximately 13:24 JST. This is Django's `default` database connection, **not** the dashboard SQL Editor.
- **Role properties, owner-supplied Supabase catalog result:** `rolsuper=false`, `rolcreatedb=true`, `rolcreaterole=true`, `rolbypassrls=true`, `rolinherit=true`, `rolcanlogin=true` for `postgres`. Thus the observed Django role is powerful and **not eligible as a SELECT-only audit credential**. Effective inherited/schema/DDL privileges beyond these flags still require inspection.
- **Target identification (owner observation):** Render DATABASE_URL has Session pooler form with a tenant-scoped `postgres.<project-ref>` username, confirmed host `aws-1-ap-northeast-1.pooler.supabase.com`, port 5432, database `postgres`, and **no explicit `sslmode` in the provided URL**. The actual DB password was not shared. This is configuration evidence, not proof of negotiated TLS, certificate verification, or hostname verification.
- **Recovery:** owner reported returning `RUN_DB_ROLE_PROBE_ON_START` to `0`. Render list_deploys then reported latest deployment `dep-dbjbv267bikc73f0ona0` started 2026-11-01 04:26:48Z (**13:26 JST**) and `status=live`; preceding probe deployment `dep-dbjbt90ae00c73dpdhk0` was deactivated. The Render API does not independently attest the current env value in this review. App-wide regression/health verification was not performed.
- **TLS_RUNTIME_UNKNOWN:** neither the SQL Editor's TLSv1.3 observation nor the role probe's SQL establishes the actual Django-to-pooler TLS session. Existing `report_db_role` collects role identity only. Require a separate, redacted client-side TLS probe on the actual Django connection with explicit approval for any deploy. Never infer `ssl_in_use` from the URL or the pooler-to-Postgres `pg_stat_ssl` result.

### Dedicated audit role: least-privilege design, not executed

Proposed separate `kamimusubi_audit_ro` (placeholder): LOGIN and schema USAGE; SELECT **only** on the precise tables required by `evidence_coverage_audit` including intermediary/source/eligibility tables after code-based inventory. No INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, CREATE, TEMP, CREATEDB, CREATEROLE, BYPASSRLS, SUPERUSER, or escalation through role membership/SET ROLE. Inspect effective grants from PUBLIC, inherited roles, table ownership, default privileges, sequences, and executable SECURITY DEFINER functions. This is not a substitute for read-only transaction enforcement in PR #3396. The live Django application stays on its existing role until a separate migration/rotation plan is approved. **No CREATE ROLE/GRANT/REVOKE or production Evidence Audit run is authorized by this record.**

### Updated status

- D-1b role **identity: VERIFIED** (`postgres`). D-1b effective-privileges detail: **PARTIAL**.
- Render deployment restoration: **Live VERIFIED**; restored env setting is **owner-reported**, not independently read.
- Production TLS / CA / hostname verification: **UNKNOWN**.
- Audit-only role: **DESIGNED IN PRINCIPLE, NOT CREATED**.
- Production data and schema changes: **NONE** by this documentation task. STOP.
