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
| Provider CA certificate: source, distribution and fingerprint check for `sslrootcert` | **Trust source DECIDED（Mother Ship, 2026-11-02: `ACCEPT_PROVIDER_DASHBOARD_CA`; §8.1.2）.** Local file checks, owner attestation and reacquisition comparison are recorded in §8.1.1. Independent third-party authenticity verification remains **UNVERIFIED** |
| Evidence accepted for CA and hostname verification on the audit connection（`report_db_tls` reports them as `unknown` by design） | **Policy DECIDED（Mother Ship, 2026-11-02: `VERIFY_FULL_WITH_CLIENT_EVIDENCE`; §8.1.2）.** The evidence has not been collected; G-6 remains **UNMET** |
| `kamimusubi_audit_ro` login through the chosen pooler endpoint（username format, session vs transaction mode） | **UNKNOWN**（G-10） |
| TLS policy for the Render Django runtime connection（SPH-21 R-7 `require` or stronger vs `verify-full`） | **Mother Ship decision; not selected here.** It does not change this document's Evidence Coverage gates: anything weaker than `verify-full` is STOP |

#### 8.1.1 Provider CA file — offline checks（2026-11-02, owner-reported; no Production connection）

| Check | Result |
| --- | --- |
| File name | `prod-ca-2021.crt` |
| Local location | `~/.config/kamimusubi/certs/`（outside the repository） |
| File permissions | `600` |
| File SHA-256 | `700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7` |
| Certificate subject CN | `Supabase Root 2021 CA` |
| Certificate expiry | 2031-04-26 |
| Offline check date | 2026-11-02 |

**Acquisition source — OWNER-ATTESTED（2026-11-02）**

| Item | Status |
| --- | --- |
| Source | **OWNER-ATTESTED:** on 2026-11-02 the owner attested that `prod-ca-2021.crt` was downloaded directly from the KAMI MUSUBI Supabase Dashboard > Database Settings > SSL Configuration > Download Certificate |
| Exact download timestamp | **UNKNOWN** |
| Screenshot or other acquisition record | **NOT RECORDED** |

An owner attestation records where the owner says the file came from. It is not independent verification of the
certificate's authenticity. The SHA-256 and offline checks above are unchanged.

**Reacquisition and SHA-256 comparison（2026-11-02, owner-performed; no Production connection）**

| Item | Result |
| --- | --- |
| Reacquisition date | 2026-11-02 |
| Reacquisition time | About 13:26 JST, taken from the downloaded file's modification timestamp（approximate） |
| Source | KAMI MUSUBI Supabase Dashboard > Database Settings > SSL Configuration > Download Certificate（**owner-attested**） |
| Downloaded file | `prod-ca-2021 (1).crt` |
| Existing local file | `prod-ca-2021.crt` |
| SHA-256 of both files | `700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7` |
| Result | **PASS**: identical file content |

| Classification | Status |
| --- | --- |
| Reacquisition reproducibility | **PASS** |
| Independent third-party authenticity verification | **UNVERIFIED** |
| Mother Ship CA trust-source acceptance | **PENDING** |
| Mother Ship TLS evidence-policy approval | **PENDING** |
| G-6 / G-7 | **UNMET** |

The comparison shows that a second download from the same owner-attested source returned the same bytes. It is
**not** independent third-party verification: both files are owner-attested downloads from the same dashboard
source, and no value from an independent source was compared.

**What this does not establish（UNVERIFIED）:**

- The exact time of the original download, and any recorded acquisition evidence: the source is owner-attested
  only, and no screenshot is recorded. The 2026-11-02 reacquisition time is approximate（file modification
  timestamp）.
- Independent verification that the certificate is authentic: **UNVERIFIED**. A matching SHA-256 shows only that the same bytes
  are held. It does not prove the certificate is the provider's genuine CA, and is not treated as authenticity
  evidence here.
- Mother Ship acceptance of this file as the CA trust source for `sslrootcert`: **PENDING**.
- The approved evidence requirements for CA and hostname verification on the audit connection（Mother Ship TLS
  evidence-policy approval: **PENDING**）.
- Any Production TLS connection verification. No connection was made.

G-6 and G-7 remain **UNMET**. Every STOP condition in §6 is unchanged.

#### 8.1.2 Mother Ship decisions（2026-11-02）: CA trust source and TLS evidence policy

```text
Decision Date: 2026-11-02
CA_TRUST_SOURCE = ACCEPT_PROVIDER_DASHBOARD_CA
TLS_EVIDENCE_POLICY = VERIFY_FULL_WITH_CLIENT_EVIDENCE
```

These are approved **policy decisions**. They are not completed technical verification gates. No runtime validation
is marked PASS by this record.

**CA trust source — `ACCEPT_PROVIDER_DASHBOARD_CA`**

- The Mother Ship accepted the CA obtained through the owner-attested Supabase Dashboard distribution channel
  (§8.1.1).
- The recorded reacquisition and SHA-256 comparison (§8.1.1, reacquisition reproducibility PASS) support this
  operational trust decision.
- Independent third-party authenticity verification remains **UNVERIFIED**. This decision is an operational trust
  decision, not third-party cryptographic verification of the certificate.
- Accepting the trust source does not prove that this CA is compatible with the actual audit connection endpoint.
  That is shown only by an authorized verify-full connection (below).

**TLS evidence policy — `VERIFY_FULL_WITH_CLIENT_EVIDENCE`（approved audit evidence policy）**

Required evidence for a future authorized verification of the audit connection:

1. `sslmode=verify-full`.
2. An explicit `sslrootcert` pointing to the accepted CA.
3. A successful connection using the documented settings and the intended hostname.
4. Client-side TLS confirmation showing `ssl_in_use=true` for that connection.
5. Evidence that CA-chain and hostname verification were enforced by the connection configuration.
6. A separate G-7 verification of the intended project and tenant: the connection URL identity comparison (Gate 1)
   plus owner-held catalog evidence.
7. The existing `pg_stat_ssl` STOP behaviour is preserved: a `false` or `unknown` result is a STOP.

`report_db_tls` reports TLS use and the configured `sslmode` only. It does **not** independently verify the
certificate chain or the hostname; it always prints `certificate_verified=unknown hostname_verified=unknown`.

**Status after these decisions**

| Item | Status |
| --- | --- |
| G-6 TLS | **UNMET** |
| G-7 Target identity | **UNMET** |
| §6 Production STOP conditions | **Unchanged**（all preserved） |
| Dedicated audit-role creation approval | **NOT GRANTED** |
| Production Evidence Coverage execution approval | **NOT GRANTED** |

The "PENDING" entries for these two decisions in §8.1.1 record the status at the time of that evidence. For these
two items they are superseded by this section; the §8.1.1 evidence itself is unchanged.

**Authorization boundary.** These decisions authorize documentation of the CA trust-source policy and the TLS
evidence policy only. They do **not** authorize any of the following:

- Production database connections;
- TLS tests against Production;
- changes to Render or Supabase settings;
- changes to environment variables or credentials;
- creating database users or roles;
- GRANT, REVOKE or other database privilege changes;
- Evidence Coverage queries against Production;
- deployment or merging.

## 9. G-6 / G-7 evidence preflight specification（design only; 2026-11-02）

> **Status: DESIGN.** This section turns the §8.1.2 policy (`VERIFY_FULL_WITH_CLIENT_EVIDENCE`) into a fail-closed
> preflight specification. Nothing here has been run. G-6 and G-7 remain **UNMET**. §6 governs; this section adds
> detail and does not relax any §6 condition. It does not authorize Production connections, role creation, GRANT /
> REVOKE, TLS tests or execution.
>
> Baseline: `develop` @ `5bab0ca9`.

### 9.1 Repository facts this specification relies on（read from the code, not inferred）

| ID | Fact | Source |
| --- | --- | --- |
| F-1 | `report_db_tls` opens Django's `default` connection (`ensure_connection()`), then reads `pgconn.ssl_in_use` and an allowlisted protocol token. It issues no SQL | `backend/temples/management/commands/report_db_tls.py` `inspect_tls()` |
| F-2 | The `sslmode` it prints comes from `settings_dict["OPTIONS"]["sslmode"]`, the **configured** value, and not from the live libpq connection. Invalid or missing values print `unspecified` | same, `inspect_tls()` |
| F-3 | It always prints `certificate_verified=unknown hostname_verified=unknown`. It emits no backend PID, connection identifier, host or user | same, `Command.handle()` |
| F-4 | `evidence_coverage_audit` collects no TLS or `pg_stat_ssl` evidence. It reads inside one `transaction.atomic()` block after the read-only guard | `backend/temples/management/commands/evidence_coverage_audit.py` `handle()` |
| F-5 | `report_db_tls` and `evidence_coverage_audit` are separate management commands, so each run uses its own process and its own database connection | Django management command model |
| F-6 | Settings add no TLS option; `sslmode` / `sslrootcert` come only from `DATABASE_URL`. Offline tests show that both reach the psycopg connect arguments unchanged | `backend/shrine_project/settings.py`; `backend/tests/test_db_tls_options_propagation.py`（#3408） |
| F-7 | `CONN_MAX_AGE` is 600 when `DEBUG` is false. Django may close a connection and open a new one; nothing in the repository records whether a given command reused or reopened its connection | `settings.py` `build_database_config()` |
| F-8 | No application code reads `pg_backend_pid()` or `pg_stat_ssl` | repository search（`backend/`） |

### 9.2 Evidence classes

| Class | Meaning | Example source | Proves |
| --- | --- | --- | --- |
| C1 Configuration propagation | The settings would pass the options to the driver | #3408 tests | Options are not lost in Django. Says nothing about a live connection |
| C2 Configured connection settings | What the connection is configured to use | Operator's private env file; the `report_db_tls` `sslmode=` token, which echoes the configured value（F-2） | What the connection was asked to do. **Not** what the actual connection enforced |
| C2E Effective connection evidence | Evidence observed on the actual connection | A live libpq parameter or another approved observation of the actual audit connection（for `sslmode`: not available today, GAP-1）; live observations such as `ssl_in_use` and catalog results | What the actual connection did or showed |
| C3 Successful verified connection | A connection succeeded with `sslmode=verify-full` and the accepted `sslrootcert` | A successful command run under C2 | Per libpq's documented `verify-full` behaviour, the server certificate chained to `sslrootcert` and the certificate matched the hostname connected to. **This libpq behaviour is cited, not re-verified here（GAP-5）** |
| C4 Independent third-party authenticity | The CA is the provider's genuine CA, established independently of the dashboard channel | None | **UNVERIFIED**（§8.1.1 / §8.1.2）. Not implied by C1–C3 |

### 9.3 Evidence matrix

Each item has three possible results. **PASS** means the item matches its expected value. **FAIL** means it is
observed and does not match. **UNKNOWN** means it is not observed, ambiguous or not correlated. **Any FAIL or UNKNOWN
on a required item is a STOP**（§9.5）.

| Evidence ID | Gate | Collection mechanism | Expected value | Actual value（placeholder） | Correlation requirement | Class | PASS / FAIL / UNKNOWN rule | Redaction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G6-E1 Endpoint and hostname | G-6 / G-7 | Operator inspects the private audit connection string offline (Gate 1 parser) | Endpoint kind and hostname are the approved ones | `<ENDPOINT_KIND>`, `<HOST_CLASS>` | Same env file as G6-E2 to E5 and G7-A | C2 | PASS if both match the approval; FAIL if they differ; UNKNOWN if it cannot be parsed | Record the endpoint kind and PASS / FAIL only; never the hostname or URL |
| G6-E2a Configured `sslmode` | G-6 | (a) configured value from the env file; (b) `report_db_tls` `sslmode=` token（configured value, F-2） | (a) and (b) both `verify-full` | `<SSLMODE_CONFIGURED>` | (b) runs with the same env file as the audit | C2 | **Configuration PASS** needs (a) and (b) to equal `verify-full`. Any other value is FAIL; `unspecified` or missing is UNKNOWN | Record the mode token only |
| G6-E2b Effective `sslmode` | G-6 | Evidence from the actual audit connection that `verify-full` was enforced（for example a live libpq connection parameter）. **No such mechanism exists today（GAP-1）** | Observed `verify-full` on the actual connection | `<SSLMODE_EFFECTIVE>` | Must come from the actual audit connection, not from the configuration | C2E | **Effective PASS** needs evidence from the actual connection that `verify-full` was enforced. A different observed value is FAIL; unavailable evidence is **UNKNOWN** | Record the mode token only |
| G6-E3 `sslrootcert` is the accepted CA | G-6 | Operator computes the SHA-256 of the file named by `sslrootcert` in the env file and compares it with §8.1.1 | `700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7` | `<SHA256_MATCH: yes/no>` | Same env file | C2 | PASS if the hash matches and the option is explicitly set; FAIL on a mismatch; UNKNOWN if the option is unset or the file is unreadable | Record match yes / no only; never a local absolute path |
| G6-E4 Successful verified connection | G-6 | `report_db_tls` exits 0 with G6-E1, E2a and E3 in force (the connection succeeded) | Exit 0 | `<EXIT_STATUS>` | Same env file, same session window as the audit | C3 | PASS on exit 0 with E1, E2a and E3 PASS; FAIL on a connection or TLS error; UNKNOWN if E1, E2a and E3 are not all PASS | Record the exit status and the `[db-tls-probe]` line only; never exception text |
| G6-E5 Client-side TLS use | G-6 | `report_db_tls` `ssl_in_use=` token | `true` | `<SSL_IN_USE>` | **Must be tied to the audit's own connection. Not supported today（GAP-2）**; only the same env file, host and time window can be shown | C2E | PASS needs `true` **and** an accepted correlation（§9.4）; FAIL on `false`; UNKNOWN if the token is missing or the correlation is not accepted | Token only |
| G6-E6 `pg_stat_ssl` | G-6（supplementary） | `SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid();` as the audit role（§5.3） | `t` | `<PG_STAT_SSL>` | Must run on the same server-side session as the audit reads. Through a pooler, see §9.4（GAP-3, GAP-4） | Supplementary | `t` is supplementary only and never sufficient alone; `f` is a STOP; no row, an error or `unknown` is a STOP | Boolean only; never the PID or `client_addr` |
| G6-E7 Contradiction check | G-6 | Compare E5 and E6 | No contradiction | `<CONSISTENT: yes/no>` | Same run | — | Any contradiction (for example E5 `true` with E6 `f`, or the reverse) is a STOP | — |
| G7-A1–A6 Connection identity | G-7 | Gate 1 secret-safe parse of the audit connection string（connection-verification document） | A1 project, A2 tenant, A3 endpoint kind, A4 database name, A5 port, A6 username format（for example `<role>.<tenant>` on a pooler）: each equals the approved target | `<A1..A6: PASS/FAIL/UNKNOWN>` | Same env file as G-6 | C2 | PASS only if all six PASS. Any FAIL is FAIL; a malformed or missing field is UNKNOWN | Record PASS / FAIL per field only; never a project reference, host, user or URL |
| G7-B1 Catalog comparison | G-7 | §5.3 catalog queries as the audit role | Table count and name set equal the owner-held, independently retained inventory | `<CATALOG_MATCH: yes/no>` | Same connection as the audit (single session window) | C2E | PASS on an exact match; FAIL on any difference; UNKNOWN if the inventory or the result is missing | Record match yes / no only |
| G7-B2 Owner confirmation | G-7 | Owner records that the matched target is the intended one | Explicit confirmation | `<OWNER_CONFIRMED: yes/no, date>` | After A and B1 | Attestation | PASS only with an explicit dated confirmation; absent is UNKNOWN | No identifiers |

A shared pooler hostname that passes `verify-full`（G6-E4）does **not** satisfy G-7. G-7 needs A1–A6, B1 and B2.

**Configuration PASS alone cannot satisfy G-6.** G6-E2a（configured `sslmode`, C2）shows only what the connection
was asked to use. G-6 needs G6-E2b（effective `sslmode`, C2E）as well. G6-E4's success under the configured settings
is not, by itself, G6-E2b evidence. Accepting that inference in place of G6-E2b would require a separate, explicit Mother Ship decision; none has
been made.
Until G6-E2b is PASS, G-6 is UNMET.

**Synthetic example（illustration only; not real values）:**

```text
G6-E1 endpoint_kind=SESSION_POOLER host_class=APPROVED_POOLER  -> PASS
G6-E2a sslmode_configured=verify-full probe_sslmode=verify-full     -> Configuration PASS
G6-E2b sslmode_effective=NOT_AVAILABLE                         -> Effective UNKNOWN (GAP-1)  => STOP
G6-E3 sslrootcert_set=yes sha256_match=yes                     -> PASS
G6-E4 report_db_tls exit=0                                     -> PASS
G6-E5 ssl_in_use=true correlation=CONFIG_AND_WINDOW_ONLY       -> UNKNOWN (GAP-2)  => STOP
G6-E6 pg_stat_ssl=t                                            -> supplementary
G7-A  A1..A6=PASS
G7-B1 catalog_match=yes ; G7-B2 owner_confirmed=yes 2026-11-XX -> PASS
RESULT: STOP (G6-E2b UNKNOWN, G6-E5 UNKNOWN)
```

### 9.4 Connection correlation and pooler semantics

**Client side（`report_db_tls`）**

- Today, `ssl_in_use` describes the connection that `report_db_tls` itself opened, in its own process（F-1, F-5）.
  It is not the connection `evidence_coverage_audit` uses.
- Neither command emits a connection identifier（F-3）. If Django reopens a connection（F-7）, nothing records it.
- Correlation available today: **same env file, same host, same time window**. That is configuration-level
  correlation, not connection identity（GAP-2）.
- Exact correlation would need the audit command to record the TLS state of its own connection inside its own
  transaction（GAP-3）. That is a separate code PR and is not part of this design.
- Whether configuration-level correlation is acceptable for G6-E5 is a **Mother Ship decision**. Until it is
  decided, G6-E5 is UNKNOWN, which is a STOP.

**Server side（`pg_stat_ssl`）**

| Path | What `pg_stat_ssl` for `pg_backend_pid()` describes |
| --- | --- |
| Direct PostgreSQL | The client's own TLS session with PostgreSQL |
| Pooler, session mode | The pooler-to-PostgreSQL session that serves this client session. It does not describe the client-to-pooler leg |
| Pooler, transaction mode | The server session for **the current transaction only**. A later transaction may use another backend. The query must run in the same transaction as the audit reads; today it does not（F-4, GAP-3） |

- How Supavisor reports backend identity, and whether a client-visible backend PID corresponds to `pg_backend_pid()`,
  is **UNKNOWN（GAP-4）**.
- The §6 rule is unchanged: `pg_stat_ssl.ssl` false or unknown is a STOP. A missing row, an error, an unavailable
  view or a contradiction with G6-E5 is treated as unknown, which is a STOP.
- No other signal substitutes for `pg_stat_ssl`, and `pg_stat_ssl` substitutes for no other item.

**What may be recorded:** the mode token, `ssl_in_use`, the protocol token, the exit status, PASS / FAIL /
UNKNOWN per item, hash-match yes / no, and dates.

**What must never be logged:** connection strings, passwords, project references, hostnames, usernames, local
absolute paths, backend PIDs, client addresses, the full `pgconn.info`, and exception text.

### 9.5 Preflight STOP matrix（fail closed）

Each row is required. **Absent, FAIL or UNKNOWN means STOP.** There are no automatic retries, no fallback to the
Django runtime role (`postgres`) and no privilege escalation. A STOP is reported as is, and the run ends.

| # | Preflight item | Required state | Current state（2026-11-02） | Result |
| --- | --- | --- | --- | --- |
| P-1 | Mother Ship execution approval | Explicit approval for a named run window | NOT GRANTED | STOP |
| P-2 | Dedicated-role creation approval（`kamimusubi_audit_ro`） | Approved and executed by the owner（§5.2） | NOT GRANTED | STOP |
| P-3 | Database privileges | §5.3: exactly `audited_tables()` SELECT; no write, DDL, TEMP, CREATE; no memberships | Not observable（no role） | STOP |
| P-4 | G-6 evidence | G6-E1 to E5 PASS, E6 `t`, E7 consistent | Not collected; GAP-1 / GAP-2 / GAP-3 open | STOP |
| P-5 | G-7 evidence | G7-A1–A6, B1, B2 PASS | Not collected | STOP |
| P-6 | Execution host | Approved owner host, clean checkout of the approved SHA（§5.1） | Not approved | STOP |
| P-7 | Credential handling procedure | §5.4 adopted（mode-600 file, env only, post-run NOLOGIN） | Proposed, not adopted | STOP |
| P-8 | Pooler compatibility | Audit-role login through the chosen endpoint confirmed（G-10） | UNKNOWN | STOP |
| P-9 | Approved SHA vs audited table set | `audited_tables()` on the approved SHA equals the granted set（§6 item 6） | No approved SHA; no grants | STOP |
| P-10 | TLS observations | No failed, missing or contradictory observation（E4–E7） | None collected | STOP |

**Overall: STOP.** G-6 **UNMET**, G-7 **UNMET**, Production execution **STOP**.

### 9.6 Design gaps（not fixed here）

| Gap | Description | Effect |
| --- | --- | --- |
| GAP-1 | `report_db_tls` reports the configured `sslmode`, not the live libpq parameter | G6-E2a（configuration）can PASS, but G6-E2b（effective）is UNKNOWN, so G-6 stays UNMET |
| GAP-2 | No exact correlation between `report_db_tls` and the audit connection（separate processes, no identifier） | G6-E5 is UNKNOWN unless the Mother Ship accepts configuration-level correlation |
| GAP-3 | `evidence_coverage_audit` records no TLS or `pg_stat_ssl` evidence inside its own transaction | Exact client-side correlation and transaction-mode `pg_stat_ssl` correlation are impossible today |
| GAP-4 | Supavisor backend identity / PID semantics are UNKNOWN | G6-E6 meaning through the pooler is uncertain |
| GAP-5 | libpq `verify-full` semantics are cited from libpq documentation, not re-verified against the provider endpoint | C3 rests on that documented behaviour |
| GAP-6 | Nothing records that CA-chain and hostname verification were enforced, other than a successful `verify-full` connection（C3） | Accepting C3 as policy item 5 evidence is a Mother Ship decision |
| GAP-7 | Audit-role pooler compatibility（username format, mode） | P-8 UNKNOWN |

### 9.7 Remaining Mother Ship decisions

1. Whether a successful `verify-full` connection with the accepted `sslrootcert`（C3, G6-E4）is accepted as the
   §8.1.2 item 5 evidence（GAP-5, GAP-6）.
2. Whether configuration-level correlation is acceptable for G6-E5, or whether a code PR adding in-transaction TLS
   evidence（GAP-2, GAP-3）is required first.
3. Dedicated-role creation and grants（P-2, P-3）.
4. Execution host, credential procedure and run window（P-1, P-6, P-7）.
5. Render Django runtime TLS policy（SPH-21 R-7）: out of scope for these gates, still undecided.
