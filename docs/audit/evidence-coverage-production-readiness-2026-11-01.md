> **Status: Read-only readiness audit（documentation only）— Production execution: STOP**
>
> - **2026-11-01 Mother Ship decision:** the role is dedicated to Evidence Coverage Audit; its approved name is
>   `kamimusubi_audit_ro`. Production role creation is **NOT APPROVED**, and the role **has not been created**.
>   Production connection, grants and audit execution remain **STOP**. The naming approval does not authorize
>   provisioning, GRANT / REVOKE or Production execution.
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
| #3399 `docs/audit/sph21-production-db-connection-verification-2026-11-01.md`（merged `32257cff`）, #3402 `report_db_tls` + `docs/runbooks/db-tls-probe.md`（merged `0ca270e4`）, #3408 `backend/tests/test_db_tls_options_propagation.py`（merged `a79bc38e`） | Canonical TLS / target-identity procedure (Gate 1 / Gate 2), the client-side TLS probe, and offline option-propagation tests. G-6 / G-7 reference them and do not redefine them. None of them has been run against Production |

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
| Production TLS on the actual connection | **UNKNOWN**: the procedure (#3399) and the probe (#3402) are merged; neither has been run in Production |
| Production table ACLs for a new role | **UNKNOWN** |
| Pooler compatibility of a custom role (Supavisor username format, transaction vs session mode) | **UNKNOWN** |

## 4. Production readiness checklist / unmet gates

| Gate | Requirement | Status |
| --- | --- | --- |
| G-1 Local inventory | `audited_tables()` equals the observed reads; restricted-role controls run, not skipped | **MET（local）**; CI INFERRED |
| G-2 Dedicated role | A separate LOGIN role dedicated to Evidence Coverage Audit, with the **approved name `kamimusubi_audit_ro`**（2026-11-01）; not `postgres` and not the Django runtime role | **UNMET**: name approved; creation **NOT APPROVED** and not created |
| G-3 Role attributes | NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION, NOBYPASSRLS; no membership in other roles | **UNMET** |
| G-4 Privilege boundary | CONNECT on the database, USAGE on `public`, SELECT on exactly `audited_tables()`（10 tables on `develop` today）; no write, DDL, TEMP or CREATE; no SELECT on other application tables | **UNMET** |
| G-5 Session defaults | `default_transaction_read_only = on` and a `statement_timeout` set on the role | **UNMET**（proposal） |
| G-6 TLS | Per the connection-verification document's Gate 2: `sslmode=verify-full` with the approved provider CA (`sslrootcert`) in the audit connection string, **explicit CA and hostname verification**, and client-side `ssl_in_use=true` from `report_db_tls` on the same connection settings. `pg_stat_ssl.ssl = true` is supplementary only (§5.3) | **UNMET / UNKNOWN**（the provider CA acquisition, the pooler TLS behaviour and the accepted evidence for CA / hostname verification are unverified or undecided; §8） |
| G-7 Target identity | (a) the connection-verification document's **Gate 1** secret-safe comparison of the audit connection string（`target_project_match`, `endpoint_kind`, `port_match`, `db_name_match`, `sslmode_class`）, **and** (b) the §5.3 catalog checks against the owner-held inventory. A shared pooler hostname that passes `verify-full` does **not** prove project / tenant identity | **UNMET**（the command cannot do this） |
| G-8 Credential handling | The secret lives in a mode-600 file outside the repository, is loaded as an env var only, and never appears in argv, logs, output, PRs or AI sessions; the role is disabled or its password rotated after the run | **UNMET**（procedure proposed in §5; not adopted） |
| G-9 Execution host | An owner-controlled host with network access to the database, running a clean checkout of a specified `develop` commit | **UNMET**（choice pending; §5.1） |
| G-10 Pooler compatibility | The custom role can log in through the chosen endpoint, and the single-transaction command works there | **UNKNOWN** |
| G-11 Output handling | Raw JSON stays outside the repository; only a summary goes into an audit document | Defined in the runbook §3.2; **adoption per run** |
| G-12 Approval | Mother Ship approves the role SQL (§5.2), the host, the credential procedure and the run window. The 2026-11-01 naming decision is **not** this approval | **UNMET**（naming only） |

## 5. Proposed read-only execution architecture（for review; nothing executed）

### 5.1 Host

| Option | Assessment |
| --- | --- |
| **Owner's local machine, clean checkout of an approved `develop` SHA, dedicated venv**（precedent: `docs/audit/local-mac-direct-migration-execution-safety.md`） | **Recommended.** The owner holds the credential; nothing is deployed; output stays local |
| Render web service (env var + startup flag) | Not recommended: it mixes audit credentials into the production web runtime; Render free has no shell |
| AI / cloud agent session | **Excluded** by the runbook §2.6 |

### 5.2 Role（proposal SQL, executed by the owner after approval; the password is set interactively and never written here）

**The role name is approved; this SQL is not.** Running it requires a separate Mother Ship approval of role creation and grants.

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
SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid();                                                        -- expect t（supplementary only, see below）
-- G-7 target identity (catalog only; record pass/fail, not values)
SELECT current_database();
SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname = 'public' AND c.relkind IN ('r','p');                                                        -- compare with the owner's recorded inventory
```

- The breadth query may also list relations that are readable through PUBLIC grants (for example, extension-owned
  tables). Any relation other than `audited_tables()` is a **STOP** until it is explained and approved.
- The target-identity check compares against the owner-held Production inventory (the table count and name set).
  Record only PASS / FAIL in shared documents. It complements, and does not replace, the Gate 1 comparison of the
  connection string (G-7 (a)): a schema-identical database elsewhere would pass the catalog check alone.
- **`pg_stat_ssl` is supplementary evidence.** Through a pooler it describes the server-side session the pooler
  holds, and cannot on its own prove that the client-to-pooler leg is encrypted（connection-verification document,
  Gate 2）. A false or unknown value is still a STOP (§6); a true value is not sufficient for G-6.
- **Client-side TLS use:** before the audit command, run `python manage.py report_db_tls`（#3402; no SQL, credential-
  safe）with the same audit `DATABASE_URL`. `ssl_in_use=true` proves only that this client connection uses TLS. It
  does **not** prove CA or hostname verification; the probe always prints
  `certificate_verified=unknown hostname_verified=unknown`.

### 5.4 Connection and credential handling

- The connection string carries `sslmode=verify-full` and `sslrootcert=<path to the provider CA file>`. Both are
  read from the mode-600 file into `DATABASE_URL` for that shell only.
- **Option propagation: CONFIRMED offline（#3408）.** With synthetic URLs and a mocked `psycopg.connect`, both
  options reach Django `OPTIONS` and the psycopg connect arguments unchanged. Settings and Django add, default or
  validate no TLS option. This is configuration propagation only, **not** evidence that a certificate or hostname
  was verified on a real connection.
- The shared pooler hostname is what `verify-full` checks. Hostname verification does not establish which project /
  tenant the session belongs to; that is G-7 (a).
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

0. A separate Mother Ship approval of role creation and grants for `kamimusubi_audit_ro`. The 2026-11-01 naming
   approval is not sufficient.
1. G-2 to G-5 are created exactly as approved, and the §5.3 pre-flight passes with zero unexplained relations.
2. G-6: TLS is verified: `verify-full` with the approved CA, explicit CA and hostname verification evidence of a
   kind the Mother Ship accepts, client-side `ssl_in_use=true` (`report_db_tls`), and `pg_stat_ssl.ssl = t` as
   supplementary evidence. #3399 / #3402 / #3408 are merged; none of them is itself Production evidence.
3. G-7: Gate 1 (connection string: project / tenant, endpoint kind, port, database name) **and** the catalog
   pre-check against the owner-held inventory both pass.
4. G-8 / G-9: the credential file, host and post-run disable steps are approved and followed.
5. G-10: login through the chosen endpoint works with the custom role.
6. The approved `develop` SHA is recorded, and its `audited_tables()` matches the granted set.

**STOP if any of the following holds:**

- The only available role is `postgres`, or any role with superuser / CREATEDB / CREATEROLE / BYPASSRLS.
- TLS cannot be verified (`sslmode` weaker than `verify-full`, or `pg_stat_ssl.ssl` is false or unknown).
- Client-side `ssl_in_use` is not `true`, or CA / hostname verification has no accepted evidence.
- Only the shared pooler hostname is verified, with no Gate 1 project / tenant match.
- Any readable relation outside `audited_tables()` is unexplained.
- The target identity is unproven.
- Execution would happen inside an AI / cloud agent session or a production web runtime.

## 7. Limitations

- No Production catalog was read. Every Production statement is from existing documents or is UNKNOWN.
- Supabase-specific behaviour (custom-role login through the pooler, CA certificate distribution, PUBLIC grants on
  extension tables) is not verified here.
- The CI execution of the restricted-role cases is inferred from the workflow, not read from logs.

## 8. Status after the 2026-11-01 naming decision

| Item | Status |
| --- | --- |
| Role scope | Dedicated to Evidence Coverage Audit — **DECIDED** |
| Role name `kamimusubi_audit_ro` | **APPROVED** |
| Role exists in Production | **NO**（not created） |
| Role creation / GRANT / REVOKE | **NOT APPROVED** |
| Production connection / audit execution | **STOP** |
| SELECT boundary | Exactly `audited_tables()` on the approved SHA（10 tables on `develop` today） — unchanged |
| TLS / target identity / credential / least-privilege gates（G-3 to G-11） | Unchanged, all still UNMET or UNKNOWN |
| Relation to PR #3406 `km_audit_ro` | **Resolved:** #3406 (merged `80cd4d03`) maps the 10-table audit row to `kamimusubi_audit_ro` and states that the generic `km_audit_ro` is not its alias; the future use of `km_audit_ro` is undecided |

**TODO（owner / Mother Ship）**

- [x] Clarify the scope of `km_audit_ro` in #3406 against `kamimusubi_audit_ro`（#3406 merged）.
- [ ] Decide on role creation and grants (§5.2): a separate approval.
- [x] Confirm the `dj_database_url` `sslmode` / `sslrootcert` pass-through (offline, #3408; propagation only).
- [ ] Resolve the TLS gate (G-6): provider CA acquisition, and the evidence accepted for CA / hostname verification
  (Mother Ship decisions; §8.1).
- [ ] Approve the execution host, credential procedure and run window (G-8, G-9).
- [ ] Verify custom-role login through the chosen endpoint (G-10).

### 8.1 Unresolved TLS items（UNKNOWN / Mother Ship decisions）

| Item | Status |
| --- | --- |
| Provider CA certificate: source, distribution and fingerprint check for `sslrootcert` | **UNKNOWN**; Mother Ship decision |
| Evidence accepted for CA and hostname verification on the audit connection（`report_db_tls` reports them as `unknown` by design） | **Mother Ship decision**; until decided, G-6 is UNMET |
| `kamimusubi_audit_ro` login through the chosen pooler endpoint（username format, session vs transaction mode） | **UNKNOWN**（G-10） |
| TLS policy for the Render Django runtime connection（SPH-21 R-7 `require` or stronger vs `verify-full`） | **Mother Ship decision; not selected here.** It does not change this document's Evidence Coverage gates: anything weaker than `verify-full` is STOP |
