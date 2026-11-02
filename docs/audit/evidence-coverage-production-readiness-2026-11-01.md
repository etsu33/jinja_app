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
| TLS in use and the server certificate verified | **Observed, not verified**（#3415）: effective `sslmode`, `ssl_in_use` and `pg_stat_ssl` are recorded on the audit connection, and production-readonly stops without `verify-full`. Certificate and hostname verification are not performed by the command（§9.8） | `audit_tls_evidence.py` |
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
       has_schema_privilege('public', 'CREATE');                                                                  -- expect f, f, f（TEMP: PUBLIC-derived `t` accepted with documented risk, §11.1）
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
- Row-level security is enabled on any `audited_tables()` table and its effect on the audit role is not approved and
  explained (§10.2 F-B).

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
| C3 Verified connection（`VERIFIED_CONNECTION`） | A connection succeeded, **and** approved evidence shows that `verify-full` with the accepted `sslrootcert` was actually enforced on that connection（G6-E2b PASS） | G6-E4b | Per libpq's documented `verify-full` behaviour, the server certificate chained to `sslrootcert` and the certificate matched the hostname connected to. **This libpq behaviour is cited, not re-verified here（GAP-5）.** A connection that only succeeded under the configured settings is `CONNECT_SUCCESS`（C2E, G6-E4a）, not C3 |
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
| G6-E4a Connection success（`CONNECT_SUCCESS`） | G-6 | `report_db_tls` exits 0 with G6-E1, E2a and E3 in force (the connection succeeded) | Exit 0 | `<EXIT_STATUS>` | Same env file, same session window as the audit | C2E | PASS on exit 0 with E1, E2a and E3 PASS; FAIL on a connection or TLS error; UNKNOWN if E1, E2a and E3 are not all PASS. **A PASS here shows only that a connection succeeded; it does not establish CA or hostname verification** | Record the exit status and the `[db-tls-probe]` line only; never exception text |
| G6-E4b Verified connection（`VERIFIED_CONNECTION`） | G-6 | Combination of G6-E4a with approved evidence, from the same relevant connection, that `verify-full` was actually enforced（G6-E2b） | E4a PASS, E2b PASS and E3 PASS on the same connection | `<VERIFIED_CONNECTION>` | E4a and E2b must describe the same relevant connection | C3 | PASS only if E4a, E2b and E3 are all PASS for the same connection. FAIL if any of them is FAIL. **UNKNOWN while E2b is UNKNOWN.** Never inferred from E2a（configuration） | Record PASS / FAIL / UNKNOWN only |
| G6-E5 Client-side TLS use | G-6 | `report_db_tls` `ssl_in_use=` token | `true` | `<SSL_IN_USE>` | **Must be tied to the audit's own connection. Not supported today（GAP-2）**; only the same env file, host and time window can be shown | C2E | PASS needs `true` **and** an accepted correlation（§9.4）; FAIL on `false`; UNKNOWN if the token is missing or the correlation is not accepted | Token only |
| G6-E6 `pg_stat_ssl` | G-6（supplementary） | `SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid();` as the audit role（§5.3） | `t` | `<PG_STAT_SSL>` | Must run on the same server-side session as the audit reads. Through a pooler, see §9.4（GAP-3, GAP-4） | Supplementary | `t` is supplementary only and never sufficient alone; `f` is a STOP; no row, an error or `unknown` is a STOP | Boolean only; never the PID or `client_addr` |
| G6-E7 Contradiction check | G-6 | Compare E5 and E6 | No contradiction | `<CONSISTENT: yes/no>` | Same run | — | Any contradiction (for example E5 `true` with E6 `f`, or the reverse) is a STOP | — |
| G7-A1–A6 Connection identity | G-7 | Gate 1 secret-safe parse of the audit connection string（connection-verification document） | A1 project, A2 tenant, A3 endpoint kind, A4 database name, A5 port, A6 username format（for example `<role>.<tenant>` on a pooler）: each equals the approved target | `<A1..A6: PASS/FAIL/UNKNOWN>` | Same env file as G-6 | C2 | PASS only if all six PASS. Any FAIL is FAIL; a malformed or missing field is UNKNOWN | Record PASS / FAIL per field only; never a project reference, host, user or URL |
| G7-B1 Catalog comparison | G-7 | §5.3 catalog queries as the audit role | Table count and name set equal the owner-held, independently retained inventory | `<CATALOG_MATCH: yes/no>` | Same connection as the audit (single session window) | C2E | PASS on an exact match; FAIL on any difference; UNKNOWN if the inventory or the result is missing | Record match yes / no only |
| G7-B2 Owner confirmation | G-7 | Owner records that the matched target is the intended one | Explicit confirmation | `<OWNER_CONFIRMED: yes/no, date>` | After A and B1 | Attestation | PASS only with an explicit dated confirmation; absent is UNKNOWN | No identifiers |

A shared pooler hostname that passes `verify-full`（G6-E4b）does **not** satisfy G-7. G-7 needs A1–A6, B1 and B2.

**Configuration PASS alone cannot satisfy G-6.** G6-E2a（configured `sslmode`, C2）shows only what the connection
was asked to use. G-6 needs G6-E2b（effective `sslmode`, C2E）as well. G6-E4a's `CONNECT_SUCCESS` under the configured settings
is not, by itself, G6-E2b evidence, and it is not `VERIFIED_CONNECTION`（G6-E4b）. Accepting that inference in place of G6-E2b would require a separate, explicit Mother Ship decision; none has
been made.
Until G6-E2b is PASS, G-6 is UNMET.

**Synthetic example（illustration only; not real values）:**

```text
G6-E1 endpoint_kind=SESSION_POOLER host_class=APPROVED_POOLER  -> PASS
G6-E2a sslmode_configured=verify-full probe_sslmode=verify-full     -> Configuration PASS
G6-E2b sslmode_effective=NOT_AVAILABLE                         -> Effective UNKNOWN (GAP-1)  => STOP
G6-E3 sslrootcert_set=yes sha256_match=yes                     -> PASS
G6-E4a report_db_tls exit=0                                    -> CONNECT_SUCCESS (PASS)
G6-E4b verified_connection (needs E2b)                         -> UNKNOWN (E2b UNKNOWN)  => STOP
G6-E5 ssl_in_use=true correlation=CONFIG_AND_WINDOW_ONLY       -> UNKNOWN (GAP-2)  => STOP
G6-E6 pg_stat_ssl=t                                            -> supplementary
G7-A  A1..A6=PASS
G7-B1 catalog_match=yes ; G7-B2 owner_confirmed=yes 2026-11-XX -> PASS
RESULT: STOP (G6-E2b UNKNOWN, G6-E4b UNKNOWN, G6-E5 UNKNOWN)
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
| P-4 | G-6 evidence | G6-E1, **E2a and E2b**, E3, **E4a and E4b**, E5 PASS; E6 `t`; E7 consistent. E2a or E4a alone never suffices | Not collected; GAP-1 / GAP-2 / GAP-3 open | STOP |
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
| GAP-6 | Nothing records that CA-chain and hostname verification were enforced, other than `VERIFIED_CONNECTION`（C3, G6-E4b）, which itself needs G6-E2b. `CONNECT_SUCCESS`（G6-E4a）alone is not this evidence | Accepting C3 as policy item 5 evidence is a Mother Ship decision; until G6-E2b exists, C3 cannot be reached |
| GAP-7 | Audit-role pooler compatibility（username format, mode） | P-8 UNKNOWN |

### 9.7 Remaining Mother Ship decisions

1. Whether `VERIFIED_CONNECTION`（C3, G6-E4b: `CONNECT_SUCCESS` plus approved evidence that `verify-full` with the
   accepted `sslrootcert` was enforced on the relevant connection）is accepted as the §8.1.2 item 5 evidence
   （GAP-5, GAP-6）. `CONNECT_SUCCESS` alone is not proposed as that evidence.
2. Whether configuration-level correlation is acceptable for G6-E5, or whether a code PR adding in-transaction TLS
   evidence（GAP-2, GAP-3）is required first.
3. Dedicated-role creation and grants（P-2, P-3）.
4. Execution host, credential procedure and run window（P-1, P-6, P-7）.
5. Render Django runtime TLS policy（SPH-21 R-7）: out of scope for these gates, still undecided.

### 9.8 Implemented: in-transaction TLS self-observation（code; not run in Production）

**Mother Ship decision:** `AUDIT_TLS_EVIDENCE_IMPLEMENTATION = IN_TRANSACTION_SELF_OBSERVATION`.

**What the code now does**（`backend/temples/services/audit_tls_evidence.py`, called from
`evidence_coverage_audit`）:

- **Timing and connection:** after the read-only guard succeeds, inside the same transaction and on the audit's own
  connection, the command records `execution.tls_evidence`. This is a backward-compatible extension: a new key,
  with `schema_version` unchanged.
- **Values recorded（redacted state tokens only）:**
  - `effective_sslmode`: from the **live libpq conninfo** (`pgconn.info`), never from Django settings. Verified
    locally against psycopg 3.3.4 / libpq 18: the live conninfo reports the mode the connection was opened with,
    including libpq defaults.
  - `sslrootcert_configured`: presence only, never the path.
  - `client_ssl_in_use`: from `pgconn.ssl_in_use` of that connection.
  - `server_pg_stat_ssl`: queried in a savepoint of the same read-only transaction.
  - `client_server_consistency`, `connection_correlation`: same driver connection object at the end of the
    audit, or `mismatch`.
  - `certificate_verified` / `hostname_verified`: always `unknown`.
  - `gate_evaluation`: always `not_evaluated`.
- **production-readonly fails closed, before reading data,** unless all of the following hold:
  - `effective_sslmode` = `verify-full`;
  - `sslrootcert` is configured;
  - `ssl_in_use` = true;
  - `pg_stat_ssl` = true;
  - client and server observations are not contradictory.

  If the audit ends on a different connection, the report is discarded. There are no retries and no fallback.
- `--allow-unguarded-local` records `tls_evidence = {"collection": "not_collected_unguarded"}`.

**Effect on the §9.6 gaps（mechanism only; no Production evidence exists）:**

| Gap | Status |
| --- | --- |
| GAP-1 effective `sslmode` | **Mechanism implemented**: live conninfo on the audit connection. G6-E2b stays UNKNOWN until an authorized run records it |
| GAP-2 correlation | **Mechanism implemented**: the evidence comes from the audit's own connection, with a same-connection check |
| GAP-3 in-transaction evidence | **Mechanism implemented**: `pg_stat_ssl` is read in the audit's read-only transaction（savepoint） |
| GAP-4 pooler backend semantics | **Open**: `pooler_detection` is always `unknown`. Agreement between the client and server values does not exclude a pooler |
| GAP-5 / GAP-6 libpq `verify-full` semantics as CA / hostname evidence | **Open**: the collector observes the effective mode and does not verify certificates or hostnames itself. §9.7 item 1 is unchanged |
| GAP-7 audit-role pooler login | **Open** |

**New finding（local test DB）:** after `SET ROLE` to an unprivileged role, `pg_stat_ssl` returned no row for the
session's own backend, so the result is `unknown`, which fails closed. **The audit role must be the login
(session) role, not a role reached through `SET ROLE`.** Whether the same visibility rule applies through the
provider's pooler is UNKNOWN.

**Tests:** `backend/temples/tests/services/test_audit_tls_evidence.py`（offline synthetic connections plus the
local disposable test DB）.

**Unchanged:** G-6 **UNMET**, G-7 **UNMET**, every §6 STOP condition, and §9.5（Production STOP）. The code has not
been run against Production.

## 10. Dedicated-role preflight audit（2026-11-02; documentation only）

> **Status: AUDIT.** No Production connection, Production SQL, role creation, GRANT / REVOKE, credential or
> environment change, or deployment. Baseline: `develop` @ `55c45bd6`. G-6 **UNMET**, G-7 **UNMET**, Production
> **STOP**. This section adds findings; it relaxes no §6 or §9.5 condition.
>
> Local evidence below comes from a disposable local PostgreSQL 16.15 cluster with Django 5.2.17, psycopg 3.3.4 and
> libpq 18. Every local role and database was dropped afterwards.

### 10.1 Facts confirmed（code or local run）

| ID | Fact | Source |
| --- | --- | --- |
| R-1 | `audited_tables()` is derived at runtime from `_AUDITED_MODELS`（6 models plus their M2M through tables）. It yields the 10 tables listed in §5.2 on this baseline | `evidence_coverage_audit.py` |
| R-2 | **Full command as a LOGIN role, least privilege（local）.** A role with LOGIN, NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION, NOBYPASSRLS, NOINHERIT and CONNECTION LIMIT 1, holding only CONNECT, `public` USAGE and SELECT on `audited_tables()`, completed the whole command on populated data（mapped registry）: the guard was established, TLS evidence was collected with `pg_stat_ssl=true`, and `current_user = session_user`. In production-readonly mode, `_verify_select_only_role()` passed and the run then stopped at the TLS gate（`effective_sslmode_not_verify_full`, `sslrootcert_not_configured`）, as designed | local scratch test; not committed |
| R-3 | The existing restricted-role test（#3403）runs the **service function** under `SET ROLE`, not the command as a login role. Under `SET ROLE`, `pg_stat_ssl` shows no row（§9.8）, so R-2 is the relevant evidence for the command path | `test_evidence_coverage_audit_sql_inventory.py` |
| R-4 | The command's own role check covers only `rolsuper` and INSERT / UPDATE / DELETE / TRUNCATE on the audited tables（§2.2）. G-3 / G-4 breadth stays an operator preflight（§5.3） | `_verify_select_only_role()` |
| R-5 | Django 5.2 drops OPTIONS `assume_role` from the connect parameters and issues `SET ROLE` after connecting. **The audit connection must not set `assume_role`**: the login role itself must be `kamimusubi_audit_ro`（§9.8 finding） | Django `postgresql/base.py` |
| R-6 | Django 5.2 uses client-side binding cursors and sets `prepare_threshold=None` by default, so it creates no server-side prepared statements | same |
| R-7 | The whole audit, including TLS collection, runs inside one `transaction.atomic()` | `handle()` |
| R-8 | At connect time, Django may run `SET TIME ZONE`（`TIME_ZONE = "Asia/Tokyo"`, `USE_TZ = True`）outside the audit transaction. With the PostGIS engine it also reads `pg_type` to register geometry types. Both are catalog or session operations, not table reads | Django `postgresql/base.py`, `postgis/base.py`; `settings.py` |

### 10.2 Findings that change the preflight

| ID | Finding | Evidence | Effect |
| --- | --- | --- | --- |
| F-A | **Database TEMP is granted to PUBLIC by default.** A new role therefore has `has_database_privilege(..., 'TEMP') = t`, and §5.3 expects `f`. Meeting `f` needs `REVOKE TEMPORARY ON DATABASE ... FROM PUBLIC`, a global PUBLIC change, which §5.2 excludes | local: `t` for a role with no TEMP grant | Under the current §5.2 rule the §5.3 check fails, so the result is **STOP**. **A Mother Ship decision is needed:** either accept PUBLIC TEMP for this role as documented residual risk, or approve the global revoke as a separate SPH-21 change. This audit does neither. Production's actual TEMP ACL is **UNKNOWN** |
| F-B | **Row-level security can silently reduce results.** For a NOBYPASSRLS role with SELECT on a table that has RLS enabled and no policy for the role, the query returns **0 rows without an error**. The Django runtime role `postgres` has BYPASSRLS（§3）, so the application would not show this | local: an RLS-enabled table returned 0 of 2 rows | A run could produce a plausible but wrong report. **Preflight addition:** read `pg_class.relrowsecurity` for every `audited_tables()` table, and compare row counts with the owner-held inventory. RLS that is enabled and not explained is a **STOP**（added to §6）. Production's RLS state for these tables is **UNKNOWN** |
| F-C | **G-5 role defaults can be overridden by the session.** The role can run `SET default_transaction_read_only = off` and `SET statement_timeout = 0` | local | G-5 is defence in depth only. The boundaries remain the privileges（G-3 / G-4）and the command's own `SET TRANSACTION READ ONLY` guard |
| F-D | **Connection errors expose identifiers on stderr.** The command does not catch connection failures. A failed connect prints a traceback that contains the **server address, the username and the `sslrootcert` path**. The password was not printed | local, synthetic URLs | G-8: raw stderr is sensitive and must never be pasted into a PR, an issue or an AI session; record only PASS / FAIL. Redacting connection errors in the command would be a separate code PR（not proposed here）. `report_db_tls` already redacts its errors（`backend/tests/test_db_tls_options_propagation.py`） |
| F-E | **No Gate 1 parser exists in the repository.** `scripts/migration_safety/check_credential_presence.sh` reports structural booleans only（scheme, host, port, database name, userinfo present）. It does not compare the project / tenant, endpoint kind or port with an approved target | repository search | G-7 (a) has no implemented tool. The connection-verification document requires any local parser to be reviewed for redaction before use. **G-7 stays UNMET** |
| F-F | **The credential bridge drops `sslrootcert`.** `guard.py pg_env_exports()` exports `PGSSLMODE` but not `PGSSLROOTCERT`. Running the §5.3 preflight through `readonly_query.sh` with `verify-full` would therefore not use the accepted CA file. libpq would fall back to its default root file, or fail | `scripts/migration_safety/guard.py` | The way the §5.3 preflight connects is **undefined**. It must use the same explicit `sslrootcert`（G6-E3）as the audit, or a reviewed change to the bridge. Until then, P-4 / P-10 cannot be correlated with the preflight |

### 10.3 G-7 offline identity check（what can be done without a connection）

- **Possible offline, by the owner only, in the private environment:** a Gate 1 comparison of the audit connection
  string. It checks the tenant-scoped username, endpoint kind, port, database name and `sslmode` class against the
  approved target, and records PASS / FAIL / UNKNOWN only. **It needs a reviewed parser, which does not exist（F-E）.**
- **Not possible offline:** G7-B1（the catalog comparison）needs the audit-role connection. G7-B2（the owner
  confirmation）follows B1.
- The owner-held inventory for B1 must be retained independently **before** the run. It should also hold expected
  per-table row counts, because of F-B.

### 10.4 G-8 / G-9 controls（status）

| Control | Status |
| --- | --- |
| Mode-600 credential file outside the repository, loaded as an env var | Precedent exists（`scripts/migration_safety` credential bridge）; **not adopted** for this audit, and the bridge lacks `sslrootcert`（F-F） |
| No URL in argv, history or logs | Holds for the command's normal output. **Fails on connection errors**（F-D）: stderr must be treated as sensitive |
| Clean checkout of an approved SHA on an owner host | Not approved（P-6）. The host needs Python dependencies from `backend/requirements.txt`, and GDAL / GEOS if `USE_GIS` stays at its default `true`. `DJANGO_SECRET_KEY` must be set; any non-production value suffices for this command |
| Post-run NOLOGIN / password rotation | Proposed（§5.2）; **not adopted** |
| AI / cloud agent execution | Excluded（runbook §2.6）; unchanged |

### 10.5 G-10 pooler compatibility — unknowns

| Item | Status |
| --- | --- |
| Custom-role login through the provider pooler（tenant-scoped username format, password / auth lookup for a new role） | **UNKNOWN** |
| Whether `CONNECTION LIMIT 1` counts pooler-held server connections and can block the run | **UNKNOWN** |
| Whether role-level `ALTER ROLE ... SET` defaults（G-5）are applied on pooled server connections | **UNKNOWN**（the command's own guard does not depend on them; F-C） |
| `pg_stat_ssl` visibility of the audit role's own backend through the pooler | **UNKNOWN**（visible locally for a login role; R-2） |
| Transaction-mode pooler | The audit's reads and TLS collection share one transaction（R-7）, and Django creates no prepared statements（R-6）. Django's connect-time `SET TIME ZONE`（R-8）would not reliably persist. Its effect on the report is not analysed. **Session mode**（the endpoint kind observed for Render, connection-verification document）avoids this; the audit endpoint is not chosen |
| Session vs transaction endpoint for the audit | **Not decided**（G7-A3） |

### 10.6 Decisions needed（no change to existing decisions）

1. F-A: either accept PUBLIC TEMP as a residual risk, or approve a separate global `REVOKE TEMPORARY` change.
2. F-B: the expected RLS state of `audited_tables()` in Production and how it is checked（the preflight addition
   above）.
3. F-E / F-F: whether to build and review a Gate 1 parser, and how the §5.3 preflight connects with the explicit
   CA. Either would be a separate PR.
4. The audit endpoint kind（session vs transaction pooler, or direct）.

**Unchanged:** P-1 to P-10 remain STOP. G-6 and G-7 remain **UNMET**. Role creation and grants are **NOT APPROVED**.

## 11. Mother Ship decisions on the §10 findings and their implementation（2026-11-02）

> **Status: DECIDED（policy）and IMPLEMENTED（code, offline tests only）.** No Production connection, role
> creation, GRANT / REVOKE, Production environment change, deployment or audit execution. G-6 **UNMET**, G-7
> **UNMET**, Production **STOP**. Every §6 / §9.5 condition stands. No other role privilege requirement is
> relaxed.

| Decision | Value | Implemented in |
| --- | --- | --- |
| TEMP | `TEMP_POLICY = ACCEPT_PUBLIC_TEMP_WITH_DOCUMENTED_RISK` | This document（§11.1） |
| RLS | `RLS_POLICY = FAIL_CLOSED_WITH_VISIBILITY_AUDIT` | `backend/temples/services/audit_rls_visibility.py`, `evidence_coverage_audit`（§11.2） |
| CA propagation | `CA_PROPAGATION_POLICY = EXPLICIT_SSLROOTCERT_FAIL_CLOSED` | `audit_tls_evidence.py`（explicit CA functions）, `evidence_coverage_audit`; **only the production-readonly audit connection path**（§11.3） |
| G-7 parser | `G7_PARSER_POLICY = LOCAL_OFFLINE_REDACTED` | **Not yet implemented.** A separate PR follows after this one is merged |

### 11.1 TEMP: accepted with documented risk（resolves §10.2 F-A as policy）

- The §5.3 TEMP check is no longer a STOP **if, and only if, the privilege comes from the default PUBLIC grant**.
  The role must not receive TEMPORARY directly or through a membership. G-3 already requires no memberships.
- **Unchanged:** database CREATE `f`, schema CREATE `f`, no write-class privilege, no memberships, NOBYPASSRLS and
  the other G-3 / G-4 rules. §5.2 still makes no PUBLIC or default-privilege change.
- **Documented residual risk:**
  - Anyone holding the credential can create temporary objects. Temporary objects live only for the session, and
    they need a session outside a read-only transaction. The audit command never creates them.
  - Temporary objects use resources（`temp_buffers`, temporary files）. Mitigations are `statement_timeout`, a
    short `VALID UNTIL`, `CONNECTION LIMIT` and NOLOGIN after the run（§5.2）.
  - No persistent object and no write to application tables is possible through TEMP.

### 11.2 RLS: fail closed, with a visibility audit（mechanism for §10.2 F-B）

Inside the guarded read-only transaction, after the read-only guard and the TLS observation, on the same
connection:

1. `SET LOCAL row_security = off`; `SHOW row_security` must return `off`, otherwise the command stops before
   reading（every guarded run）.
   - **This is not an RLS bypass.** With `row_security = off`, PostgreSQL raises SQLSTATE 42501 ("query would be
     affected by row-level security policy") for any read that a policy would filter, instead of returning fewer
     rows. Roles that already bypass RLS（superuser, BYPASSRLS, table owner without FORCE）are unaffected, and
     nothing is granted. Local evidence: an RLS-enabled table returned 0 rows to the restricted role by default,
     and an error under `row_security = off`.
2. A catalog-only visibility audit is recorded as `execution.rls_visibility`. It covers `relrowsecurity` /
   `relforcerowsecurity` for every `audited_tables()` table, and whether the effective role is a superuser or has
   BYPASSRLS. Only table names, booleans and fixed tokens are recorded; no row is read.
3. **production-readonly stops before reading** if any of the following holds:
   - row security is not `off`;
   - any audited table has RLS enabled;
   - the RLS state is unknown（an unresolved table or a catalog error）;
   - the effective role can bypass RLS, or that is unknown.
4. If a read is refused during the audit, the command stops with `row_level_security_would_apply` or
   `privilege_missing`（SQLSTATE 42501）, produces no report, and prints no table name or driver text.

`execution.rls_visibility` is a backward-compatible extension; `schema_version` is unchanged. Unguarded local runs
record `{"collection": "not_collected_unguarded"}`. The owner-held per-table row counts（§10.3）stay part of the
G7-B1 preflight; this mechanism does not replace them.

### 11.3 Explicit CA propagation（mechanism for §10.2 F-F, audit path only）

The production-readonly connection path of `evidence_coverage_audit` now:

- **Checks before connecting**, using configured values as a gate and never as TLS evidence. It requires
  `sslmode=verify-full` and an explicit, non-empty `sslrootcert` in `DATABASE_URL`. `sslrootcert=system` is refused.
  If any of these is missing, it stops without opening a connection.
- **Checks after connecting:** the live libpq conninfo `sslrootcert` must equal the explicitly configured value
  （`ca_propagation = explicit_match`）. The other outcomes are `mismatch`, `system`, `implicit`（for example from a
  `PG*` environment variable）, `not_configured` and `unknown`; each of them stops the run. Paths are compared,
  never printed.
- **Redacts connection failures**（§10.2 F-D, production-readonly path）: a failed connect raises a fixed message
  without the host, user, certificate path or driver text. The driver exception is not chained.

**Not changed:** the Django runtime connection settings, `report_db_tls`, and the `scripts/migration_safety`
credential bridge. The bridge still does not export `sslrootcert`, so **the way §5.3 runs its catalog queries with
the explicit CA is still undefined**（§10.6 item 3）. G6-E3（the CA file hash）remains an operator check.

### 11.4 Status after this section

| Item | Status |
| --- | --- |
| §10.2 F-A TEMP | **Policy decided**（accepted with documented risk） |
| §10.2 F-B RLS | **Mechanism implemented**; Production RLS state **UNKNOWN** until an authorized run |
| §10.2 F-C session-overridable defaults | Unchanged（defence in depth only） |
| §10.2 F-D connection-error exposure | **Redacted** on the production-readonly path; local runs unchanged |
| §10.2 F-E Gate 1 parser | **Not implemented**; separate PR（`LOCAL_OFFLINE_REDACTED`） |
| §10.2 F-F CA propagation | **Audit command path implemented**; the §5.3 preflight connection method is still undefined |
| G-6 / G-7 | **UNMET** |
| Role creation / GRANT / REVOKE / Production execution | **NOT APPROVED / STOP** |

## 12. G-7 Gate 1 offline identity parser（2026-11-02; code and offline tests only）

> **Status: IMPLEMENTED（local tool）.** Mother Ship decision `G7_PARSER_POLICY = LOCAL_OFFLINE_REDACTED`. Nothing
> was run against a real connection string. G-6 **UNMET**, G-7 **UNMET**, Production **STOP**. This resolves the
> "no parser exists" part of §10.2 F-E only.

**Tool:** `scripts/g7_gate1_identity_check.py`（standard library only）. **Tests:**
`backend/tests/test_g7_gate1_identity_check.py`（synthetic values; socket creation and name resolution are made to
fail in every test）.

| Field | Compared with the owner-approved target | UNKNOWN when |
| --- | --- | --- |
| G7-A1 project | The user-name suffix of `<role>.<suffix>` equals `project_ref`. **The host name is never used** | No suffix, more than one `.`, or an invalid target value |
| G7-A2 tenant | The host equals the approved `pooler_host`（exact, case-insensitive） | No host, or the target value is missing |
| G7-A3 endpoint kind | Derived only for the approved pooler host, an explicit port（5432 → `SESSION_POOLER`, 6543 → `TRANSACTION_POOLER`）and a `<role>.<suffix>` user name; equals `endpoint_kind` | Any other host, a missing or unsupported port, or an ambiguous user name |
| G7-A4 database name | The single path segment equals `dbname` | No path, or a nested path |
| G7-A5 port | The explicit port equals `port` | No explicit port（the libpq default is not evidence） |
| G7-A6 user-name format | The user name is exactly `<role>.<suffix>`; a user name without a suffix is FAIL | No user name, or an ambiguous one |

- **Treated as UNKNOWN for every field:** a malformed URL, a non-PostgreSQL scheme, a fragment, multiple hosts,
  IPv6 literals and an unencoded reserved character in the credentials. libpq query parameters that override
  `host` / `hostaddr` / `port` / `user` / `dbname` / `service` make the affected fields UNKNOWN.
- **Supported formats: the two pooler kinds only**（decision of 2026-11-02）. Direct connections are not supported,
  so they are always UNKNOWN; no verified record of that format exists in this repository.
- **Output:** `g7_<field>=PASS|FAIL|UNKNOWN`, `g7_gate1_overall`, `g7_b1_catalog=not_evaluated`,
  `g7_b2_owner_confirmation=not_evaluated` and **`g7_satisfied=false` always**. Exit status 0 only when all six are
  PASS. Input problems print a fixed `g7_gate1_input=<token>`. The tool never prints the URL, password, host,
  user name, project reference, tenant identifier, file paths, argv or exception text.
- **Inputs:** the URL comes only from an environment variable（default `DATABASE_URL`）. The target JSON must be a
  regular file outside the repository that group and others cannot access.

**Remaining limitations**

- It checks the configuration string only. It does not prove which database a live session reaches. That needs
  G7-B1（the catalog comparison）and G7-B2（the owner confirmation）, which are separate and not evaluated.
- The target is only as independent as its source. The owner must take it from the provider dashboard, not copy it
  from the connection string being checked.
- The port-to-kind mapping（5432 / 6543）is the provider convention approved for this tool. It has not been
  re-verified against the provider here.
- The tool has not been run on the owner host. Running it is an operator step and needs no Production connection.

## 13. Required database access inventory for the audit role（2026-11-02; repository evidence only）

> **Status: AUDIT（documentation only）.** Baseline: `develop` @ `85b311cf`. No Production or remote database was
> contacted. No role, GRANT / REVOKE or configuration change was made. **This section describes what the code
> requires. It says nothing about what Production grants**; no Production privilege is inferred from code. G-6
> **UNMET**, G-7 **UNMET**, Production **STOP**. The TEMP decision（§11.1）and the RLS fail-closed policy（§11.2）
> are unchanged.
>
> **Method:**
> 1. Static trace of `evidence_coverage_audit` and every helper it calls, plus model metadata and migrations.
> 2. Corroboration on the local disposable test database: every statement issued by the full guarded command was
>    captured and resolved with `EXPLAIN (VERBOSE)`, for the three Channel B registry states（mapped / unmapped-only
>    / empty）. The capture harness was not committed; the committed equivalent is #3403
>    `test_evidence_coverage_audit_sql_inventory.py`.

### 13.1 Call graph（application-data reads）

| Step | Source | Reads |
| --- | --- | --- |
| Default scope（QA-fixture exclusion） | `services/evidence_coverage_audit.py:629` → `services/knowledge_coverage_report.py:54` → `services/shrine_qa_fixture_exclusion.py:40-44` | `temples_shrine`（id, filtered by `name_jp`） |
| `--scope-id` / `--scope-ids-file` | `commands/knowledge_coverage_report.py` `_parse_scope_ids_file` | Local file only, no DB |
| Deities + all Sources | `services/evidence_coverage_audit.py:427, 431` | `temples_shrinedeity`, `temples_shrinedeity_sources`, `temples_shrineknowledgesource` |
| Histories + all Sources | same `:448` | `temples_shrinehistory`, `temples_shrinehistory_sources`, `temples_shrineknowledgesource` |
| Shared Eligibility（fact-ready） | same `:465-466` → `services/shrine_knowledge_selector.py:30, 49, 89` | the same deity / history / Source tables |
| Channel B typed need match | same `:470` → `services/channel_b_typed_need_match.py:109, 115, 133` | `temples_shrinesourcefact`, `temples_shrinesourcefact_sources`, `temples_shrineknowledgesource`, `temples_goriyakutag`（only when a mapped Fact exists） |
| Source-fact attribution | `services/evidence_coverage_audit.py:473` | `temples_shrinesourcefact`, `temples_shrinesourcefact_sources`, `temples_shrineknowledgesource` |
| Shrines + legacy tags | same `:495` | `temples_shrine`, `temples_shrine_goriyaku_tags`, `temples_goriyakutag` |

- The registry is built from repository data（`domain/source_fact_mapping_registry_v1.py:291`）.
  `validate_registry_db_consistency()`（`:210`）is **not** called on the audit path.
- `is_recommendation_eligible()`, `evidence_gate`, `NEED_TO_GORIYAKU_IDS` and `PREF_CHOICES` issue no query.
- No `select_related`, raw SQL or `.raw()` touches application data. Foreign keys that are loaded but never followed
  （`Shrine.place_ref`, `Shrine.owner`）cause no read of `place_ref` or the user table.
- Physical names: none of the six models sets `db_table`; all three M2M through tables are auto-created
  （`models.py:262, 511, 772, 921`）. No migration renames them（`AlterModelTable` / `db_table` appear only for
  other tables）.

### 13.2 Access matrix

**Application tables（schema `public`）**

| Object | Operation | Required privilege | Source | Confidence |
| --- | --- | --- | --- | --- |
| `temples_shrine` | SELECT | SELECT | `evidence_coverage_audit.py:495`; `knowledge_coverage_report.py:54` | CONFIRMED（static + local capture） |
| `temples_shrine_goriyaku_tags` | SELECT（prefetch join） | SELECT | `evidence_coverage_audit.py:495` | CONFIRMED |
| `temples_goriyakutag` | SELECT | SELECT | `evidence_coverage_audit.py:495`; `channel_b_typed_need_match.py:133` | CONFIRMED（read in every registry state through the tag prefetch） |
| `temples_shrinedeity` | SELECT | SELECT | `evidence_coverage_audit.py:431`; `shrine_knowledge_selector.py:49` | CONFIRMED |
| `temples_shrinedeity_sources` | SELECT | SELECT | prefetch at the same lines | CONFIRMED |
| `temples_shrinehistory` | SELECT | SELECT | `evidence_coverage_audit.py:448`; `shrine_knowledge_selector.py:89` | CONFIRMED |
| `temples_shrinehistory_sources` | SELECT | SELECT | prefetch at the same lines | CONFIRMED |
| `temples_shrineknowledgesource` | SELECT | SELECT | `evidence_coverage_audit.py:427`; `shrine_knowledge_selector.py:30` | CONFIRMED |
| `temples_shrinesourcefact` | SELECT | SELECT | `evidence_coverage_audit.py:473`; `channel_b_typed_need_match.py:115` | CONFIRMED |
| `temples_shrinesourcefact_sources` | SELECT | SELECT | prefetch at the same lines | CONFIRMED |
| `public` schema | name resolution | USAGE | all of the above | CONFIRMED（required for any unqualified table access） |
| database | connect | CONNECT | connection | CONFIRMED（requirement; Production ACL UNKNOWN） |

**Catalog, statistics and functions（visibility, not application SELECT）**

| Object | Operation | Source | Path | Confidence |
| --- | --- | --- | --- | --- |
| `pg_roles`（view over `pg_authid`） | SELECT | `evidence_coverage_audit.py:127`; `audit_rls_visibility.py:34` | role check（production-readonly）; RLS bypass check（every guarded run） | CONFIRMED（local capture shows `pg_authid` through the view） |
| `pg_class` + `to_regclass()` + `unnest()` | SELECT | `audit_rls_visibility.py:28` | RLS visibility（every guarded run） | CONFIRMED |
| `has_table_privilege()` | function | `evidence_coverage_audit.py:136` | role check（production-readonly） | CONFIRMED |
| `pg_stat_ssl`（view over a statistics function）+ `pg_backend_pid()` | SELECT | `audit_tls_evidence.py:44` | TLS evidence（every guarded run, in a savepoint） | CONFIRMED（a row is visible only for the login role itself; §9.8） |
| `pg_type` | SELECT | Django `contrib/postgres/signals.py`（hstore / citext OIDs, on `connection_created`, cached per process）; Django PostGIS `register_geometry_adapters` when the GIS engine is used | connect time, outside the guarded transaction | CONFIRMED from Django 5.2 source; not seen in the local capture because of the per-process cache and the non-GIS test engine |
| libpq conninfo / `ssl_in_use` | client-side only | `audit_tls_evidence.py:68, 137` | no SQL | CONFIRMED |

**Session-level operations（no table privilege needed）**

| Statement | Source | Scope |
| --- | --- | --- |
| `SET TRANSACTION READ ONLY` / `SHOW transaction_read_only` | `evidence_coverage_audit.py:112-113` | guarded transaction |
| `SET LOCAL row_security = off` / `SHOW row_security` | `audit_rls_visibility.py:48-49` | guarded transaction only; **not an RLS bypass**（§11.2） |
| `SAVEPOINT` / `RELEASE SAVEPOINT` | `audit_tls_evidence.py`（`pg_stat_ssl` read） | guarded transaction |
| `SET TIME ZONE`（only if the server zone differs from `Asia/Tokyo`） | Django `postgresql/base.py` `_configure_timezone` | connect time |

No INSERT, UPDATE, DELETE, TRUNCATE, DDL, `COPY`, `LOCK`, temporary object or sequence access appears on any path.

### 13.3 `audited_tables()` coverage

- `audited_tables()`（`evidence_coverage_audit.py:92`）yields exactly the 10 application tables in §13.2.
- The local capture read exactly the same 10 tables in all three registry states: **no missing entry and no
  unnecessary entry.**
- `audited_tables()` enumerates forward M2M fields only. That is sufficient: the reverse relations from
  `ShrineKnowledgeSource` use the same three through tables.
- **Must not be granted:** the ORM-less legacy table `temples_shrine_deities`（the field was removed in migration
  0072; migration 0100 refers to it as legacy）. No audit path reads it. Whether it still exists in Production is
  **UNKNOWN**.
- **Caveat:** `audited_tables()` is a code-level list. Any future model or helper change can widen the reads; #3403
  guards this in CI.

### 13.4 Minimum privilege proposal（proposal only — nothing is granted）

**Granted today: nothing.** The role does not exist, and creation and grants are **NOT APPROVED**（§8）.

| Proposed | Why |
| --- | --- |
| LOGIN; NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION, NOBYPASSRLS, NOINHERIT; no memberships | G-3. The audit must use the login role itself, not `SET ROLE`（§9.8） |
| CONNECT on the database | connection |
| USAGE on schema `public` | name resolution |
| SELECT on exactly the 10 tables of `audited_tables()` on the approved SHA | §13.2 |
| Nothing else: no write-class privilege, no CREATE on the database or schema, no sequence privilege | §13.2 shows no other need |
| TEMPORARY: only through the default PUBLIC grant | accepted with documented risk（§11.1）; never granted directly |
| Catalog / statistics visibility and function EXECUTE through the **default** PUBLIC grants only | §13.2. No extra grant is proposed. If a provider default removes any of them, the command fails closed rather than needing a new grant |

### 13.5 UNKNOWN（needs a later, authorized DB-side check）

1. Whether Production keeps the default PUBLIC visibility of `pg_roles`, `pg_class`, `pg_type` and `pg_stat_ssl`,
   and EXECUTE on `has_table_privilege`, `to_regclass`, `unnest` and `pg_backend_pid`.
2. Whether `pg_stat_ssl` shows the audit role's own backend through the provider pooler（§10.5）.
3. The RLS state of the 10 tables in Production（§11.2; the run stops if any has RLS）.
4. The Production ACLs of the 10 tables, of schema `public` and of the database, including PUBLIC and
   provider-default grants that would widen what the role can read（§5.3 breadth check）.
5. Whether `temples_shrine_deities` or other legacy relations exist and are readable through PUBLIC.
6. Whether the `postgis`, `hstore` or `citext` types exist（only the connect-time `pg_type` lookups depend on them;
   absence is tolerated by the code）.

### 13.6 Decisions and STOP conditions（unchanged unless stated）

- **Decisions still open:**
  - role creation and grants（§8 / P-2, P-3）;
  - execution host, credential procedure and run window（P-1, P-6, P-7）;
  - the §5.3 preflight connection method with an explicit CA（§11.3）;
  - the audit endpoint kind（§10.6）.
- **STOP（unchanged）:** every §6 and §9.5 condition. In particular, STOP if:
  - any readable relation outside the 10 tables is unexplained;
  - any of the 10 tables has RLS enabled;
  - the role can bypass RLS;
  - TLS or target identity is not established（G-6 / G-7 **UNMET**）.
