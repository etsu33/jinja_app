> **Status: Read-only readiness audit（documentation only）— Production execution: STOP**
>
> - Audit date: 2026-11-01
> - Base: `develop` @ `c1fd157`
> - No Production DB connection, role creation, GRANT / REVOKE, or Render / Supabase / Vercel change.
> - No credential was retrieved or recorded. The SQL in this document is a proposal for Mother Ship review and has
>   **not** been executed anywhere except where marked "local".

# Evidence Coverage Audit — Production Readiness（2026-11-01）

## 0. Verdict

**NOT READY: STOP.** Local safety evidence is in place. Every Production-side gate is unmet or UNKNOWN:

- a dedicated read-only role;
- its verified privilege boundary;
- verified TLS;
- target identity;
- an approved execution host and credential procedure.

The command's own guard is necessary but not sufficient (§2.2).

## 1. Sources reviewed

| Source | Role in this audit |
| --- | --- |
| `backend/temples/management/commands/evidence_coverage_audit.py` | Guard implementation (`audited_tables()`, read-only transaction, role check) |
| `docs/runbooks/evidence-coverage-audit.md` §2–§3 | Operating rules (production-readonly flags, credential discipline, no AI-agent execution) |
| `docs/audit/sph21-evidence-audit-select-role-matrix-2026-11-01.md` | Least-privilege design, the `postgres` role facts, PR #3403 inventory record |
| `backend/temples/tests/services/test_evidence_coverage_audit_sql_inventory.py`（#3403） | Dynamic SQL inventory plus restricted-role positive / negative control |
| Open PRs #3399（SPH-21 production DB connection, TLS and privilege verification procedure）and #3402（Django TLS read-only probe） | **Unmerged** dependencies for the TLS gate. Not duplicated here |

## 2. Confirmed local safety evidence

### 2.1 Tests（run in this session on a disposable local PostgreSQL 16; not Production）

`temples/tests/services/test_evidence_coverage_audit_sql_inventory.py` plus the other Evidence Coverage test modules
gave **43 passed, 0 skipped**. This covers:

- Observed application reads stay within `audited_tables()` for the Channel B registry states mapped, unmapped-only
  and empty.
- Mapped Channel B reads the concept tag; unmapped does not.
- The guard reads catalog relations only.
- **Restricted-role positive control:** every path succeeds with SELECT on the audited tables only.
- **Negative control:** a missing table grant is detected.

The restricted-role cases skip (`NOT RUN`) when the test role cannot create roles. Locally they **ran** (0 skipped).

On CI, the job uses `postgres:16` with `POSTGRES_USER: admin` (`.github/workflows/backend-tests.yml` unit job). That
image makes this user a superuser, so the cases are expected to run there too. **This is INFERRED:** the CI log line
was not read.

### 2.2 What the command guard does and does not verify（code: CONFIRMED）

| Check | Implemented? | Evidence |
| --- | --- | --- |
| PostgreSQL vendor and outermost transaction | Yes | `_guard_unavailable_reason()` |
| `SET TRANSACTION READ ONLY` with `SHOW transaction_read_only = on` | Yes, fail closed | `_establish_read_only_transaction()` |
| `--confirm-read-only-production` required, `--allow-unguarded-local` refused | Yes | `handle()` |
| Effective role is not a superuser | Yes (`pg_roles.rolsuper`) | `_verify_select_only_role()` |
| No INSERT / UPDATE / DELETE / TRUNCATE on the audited tables | Yes (`has_table_privilege`) | same |
| `rolcreatedb`, `rolcreaterole`, `rolbypassrls`, `rolreplication` | **No** | — |
| Membership in privileged roles; the ability to `SET ROLE` | **No** | — |
| Database `CREATE` / `TEMP`, schema `CREATE` | **No** | — |
| SELECT on non-audited tables (least-privilege breadth) | **No** | — |
| TLS in use and the server certificate verified | **No** | — |
| Target is the intended Production DB | **No**: `target_identity_verified` is always `false` | `handle()` |

The read-only transaction blocks writes even for a powerful role, so the gaps are defence-in-depth and exposure
issues, not write paths. The matrix document already states that these gaps must not be accepted for Production. They
are covered below by an operator pre-flight (§5.3). A code change to the guard would be a separate PR.

### 2.3 Application TLS default（CONFIRMED, code）

`backend/shrine_project/settings.py` sets only `connect_timeout` in the database `OPTIONS`; it does not set `sslmode`.
libpq's default `sslmode` is `prefer`: it attempts TLS but neither requires it nor verifies the server certificate.
TLS verification therefore depends entirely on the connection string used for the audit.

## 3. Production facts already recorded（from existing documents）

| Fact | Status |
| --- | --- |
| The Django runtime connects as `postgres`（`current_user` / `session_user`, 2026-11-01 diagnostic）; the role has CREATEDB, CREATEROLE and BYPASSRLS | RECORDED（matrix doc）. **Unsuitable for the audit; must not be used** |
| Dedicated audit role | **Does not exist**（design only） |
| Production TLS on the actual connection | **UNKNOWN**（#3399 / #3402 unmerged） |
| Production table ACLs for a new role | **UNKNOWN** |
| Pooler compatibility of a custom role (Supavisor username format, transaction vs session mode) | **UNKNOWN** |

## 4. Production readiness checklist / unmet gates

| Gate | Requirement | Status |
| --- | --- | --- |
| G-1 Local inventory | `audited_tables()` equals the observed reads; restricted-role controls run, not skipped | **MET（local）**; CI INFERRED |
| G-2 Dedicated role | A separate LOGIN role (proposed name `kamimusubi_audit_ro`), not `postgres` and not the Django runtime role | **UNMET**（not created; needs approval） |
| G-3 Role attributes | NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION, NOBYPASSRLS; no membership in other roles | **UNMET** |
| G-4 Privilege boundary | CONNECT on the database, USAGE on `public`, SELECT on exactly `audited_tables()`（10 tables on `develop` today）; no write, DDL, TEMP or CREATE; no SELECT on other application tables | **UNMET** |
| G-5 Session defaults | `default_transaction_read_only = on` and a `statement_timeout` set on the role | **UNMET**（proposal） |
| G-6 TLS | `sslmode=verify-full` with the provider CA certificate in the audit connection string; `pg_stat_ssl.ssl = true` for the session | **UNMET / UNKNOWN**（the CA file and pooler TLS behaviour are unverified; depends on #3399 / #3402） |
| G-7 Target identity | An operator pre-check proves the session is the intended Production database before the command runs | **UNMET**（the command cannot do this） |
| G-8 Credential handling | The secret lives in a mode-600 file outside the repository, is loaded as an env var only, and never appears in argv, logs, output, PRs or AI sessions; the role is disabled or its password rotated after the run | **UNMET**（procedure proposed in §5; not adopted） |
| G-9 Execution host | An owner-controlled host with network access to the database, running a clean checkout of a specified `develop` commit | **UNMET**（choice pending; §5.1） |
| G-10 Pooler compatibility | The custom role can log in through the chosen endpoint, and the single-transaction command works there | **UNKNOWN** |
| G-11 Output handling | Raw JSON stays outside the repository; only a summary goes into an audit document | Defined in the runbook §3.2; **adoption per run** |
| G-12 Approval | Mother Ship approves the role SQL (§5.2), the host, the credential procedure and the run window | **UNMET** |

## 5. Proposed read-only execution architecture（for review; nothing executed）

### 5.1 Host

| Option | Assessment |
| --- | --- |
| **Owner's local machine, clean checkout of an approved `develop` SHA, dedicated venv**（precedent: `docs/audit/local-mac-direct-migration-execution-safety.md`） | **Recommended.** The owner holds the credential; nothing is deployed; output stays local |
| Render web service (env var + startup flag) | Not recommended: it mixes audit credentials into the production web runtime; Render free has no shell |
| AI / cloud agent session | **Excluded** by the runbook §2.6 |

### 5.2 Role（proposal SQL, executed by the owner after approval; the password is set interactively and never written here）

```sql
CREATE ROLE kamimusubi_audit_ro LOGIN
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT
  CONNECTION LIMIT 1 VALID UNTIL '<short expiry, set at approval time>';
-- password: set interactively (e.g. psql \password), never in a file in the repository or in shell history
GRANT CONNECT ON DATABASE <database> TO kamimusubi_audit_ro;
GRANT USAGE ON SCHEMA public TO kamimusubi_audit_ro;
-- generate the table list from `audited_tables()` on the approved SHA; do not copy a list from this document
GRANT SELECT ON TABLE <each table from audited_tables()> TO kamimusubi_audit_ro;
ALTER ROLE kamimusubi_audit_ro SET default_transaction_read_only = on;
ALTER ROLE kamimusubi_audit_ro SET statement_timeout = '60s';
-- after the run:
ALTER ROLE kamimusubi_audit_ro NOLOGIN;   -- or DROP ROLE after revoking grants
```

- Do not change `PUBLIC` grants or default privileges globally as part of this; that is a separate SPH-21 decision.
- The table set on `develop` today is `temples_goriyakutag`, `temples_shrine`, `temples_shrine_goriyaku_tags`,
  `temples_shrinedeity`, `temples_shrinedeity_sources`, `temples_shrinehistory`, `temples_shrinehistory_sources`,
  `temples_shrineknowledgesource`, `temples_shrinesourcefact`, `temples_shrinesourcefact_sources`. Regenerate it at
  approval time.

### 5.3 Operator pre-flight（run as the audit role, read-only catalog queries; every check must pass）

```sql
-- G-3 attributes and memberships
SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls FROM pg_roles WHERE rolname = current_user;
SELECT count(*) FROM pg_auth_members WHERE member = (SELECT oid FROM pg_roles WHERE rolname = current_user);   -- expect 0
-- G-4 database / schema capabilities
SELECT has_database_privilege(current_database(), 'CREATE'), has_database_privilege(current_database(), 'TEMP'),
       has_schema_privilege('public', 'CREATE');                                                                  -- expect f, f, f
-- G-4 table breadth: readable relations in public must equal audited_tables()
SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname = 'public' AND c.relkind IN ('r','p','v','m') AND has_table_privilege(c.oid, 'SELECT') ORDER BY 1;
-- G-4 no write-class privilege anywhere in public
SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname = 'public' AND c.relkind IN ('r','p')
   AND has_table_privilege(c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER');                        -- expect 0
-- G-5 / G-6 session
SHOW default_transaction_read_only;                                                                              -- expect on
SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid();                                                        -- expect t
-- G-7 target identity (catalog only; record pass/fail, not values)
SELECT current_database();
SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname = 'public' AND c.relkind IN ('r','p');                                                        -- compare with the owner's recorded inventory
```

- The breadth query may also list relations that are readable through PUBLIC grants (for example, extension-owned
  tables). Any relation other than `audited_tables()` is a **STOP** until it is explained and approved.
- The target-identity check compares against the owner-held Production inventory (the table count and name set).
  Record only PASS / FAIL in shared documents.

### 5.4 Connection and credential handling

- The connection string carries `sslmode=verify-full` and `sslrootcert=<path to the provider CA file>`. Both are
  read from the mode-600 file into `DATABASE_URL` for that shell only. Whether `dj_database_url` passes these query
  parameters to libpq unchanged must be confirmed locally first (UNKNOWN; no code change proposed here).
- Never put the URL in argv, shell history or logs. The command does not print the role or host (code: CONFIRMED).
- After the run: `unset DATABASE_URL`, delete the local file or keep it outside synced folders, and set the role to
  NOLOGIN.

### 5.5 Run

1. Run the pre-flight (§5.3). All checks must pass.
2. Run `evidence_coverage_audit --data-origin production-readonly --confirm-read-only-production --format json`.
3. Confirm `execution.read_only_guard == postgresql_transaction_read_only` and `select_only_role_verified == true`.
4. Record `target_identity_verified=false` as expected, alongside the pre-flight PASS from §5.3.

## 6. STOP / GO criteria for Mother Ship review

**GO requires all of the following:**

1. G-2 to G-5 are created exactly as approved, and the §5.3 pre-flight passes with zero unexplained relations.
2. G-6: TLS is verified (`verify-full`, `pg_stat_ssl.ssl = t`). #3399 / #3402 are merged, or equivalent evidence is
   recorded.
3. G-7: the target-identity pre-check passes against the owner-held inventory.
4. G-8 / G-9: the credential file, host and post-run disable steps are approved and followed.
5. G-10: login through the chosen endpoint works with the custom role.
6. The approved `develop` SHA is recorded, and its `audited_tables()` matches the granted set.

**STOP if any of the following holds:**

- The only available role is `postgres`, or any role with superuser / CREATEDB / CREATEROLE / BYPASSRLS.
- TLS cannot be verified (`sslmode` weaker than `verify-full`, or `pg_stat_ssl.ssl` is false or unknown).
- Any readable relation outside `audited_tables()` is unexplained.
- The target identity is unproven.
- Execution would happen inside an AI / cloud agent session or a production web runtime.

## 7. Limitations

- No Production catalog was read. Every Production statement is from existing documents or is UNKNOWN.
- Supabase-specific behaviour (custom-role login through the pooler, CA certificate distribution, PUBLIC grants on
  extension tables) is not verified here.
- The CI execution of the restricted-role cases is inferred from the workflow, not read from logs.
