# G-7 Dedicated Preflight Runner — Independent Security Review（2026-11-03）

> **Status: Audit / Historical（read-only review; documentation only）.**
>
> - Target: PR #3423 as merged, `develop` @ `afd3fe974`（includes the follow-up commits `9142f04` … `d544297`）.
> - Scope: `scripts/g7_dedicated_preflight_runner.py`, `backend/tests/test_g7_dedicated_preflight_runner.py`,
>   `backend/tests/test_g7_dedicated_preflight_runner_db.py`,
>   `docs/audit/evidence-coverage-production-readiness-2026-11-01.md`（§14, §15）,
>   `docs/runbooks/evidence-coverage-audit.md`（§3.2）.
> - No Production or remote database was contacted. No role, GRANT / REVOKE, migration, deployment or configuration
>   change was made. The runner and its tests are **unchanged** by this review. Code fixes belong in a separate PR.
> - Reproductions used synthetic values, disabled sockets, and a disposable PostgreSQL 16 cluster bound to
>   `127.0.0.1` only（for R5）.
> - **This review approves nothing.** It is not an AG-1 to AG-5 approval. It does not resolve OP-6 or OP-7, and it does
>   not move G-6 or G-7.

```text
ROLE_CREATION_EXECUTION = NOT_AUTHORIZED
GRANT_EXECUTION         = NOT_AUTHORIZED
PRODUCTION_CONNECTION   = STOP
AG-3 / AG-4             = NOT_AUTHORIZED
G6 = UNMET
G7 = UNMET
```

## 0. Verdict

**No High finding. Four Medium findings. OP-6 stays STOP.**

The runner meets the offline contract it claims:

- no Production entry point;
- a fixed SQL registry that is checked by object identity;
- sequential fail-closed execution;
- rollback and close on every `Exception` path;
- fixed-token redaction;
- G-6 / G-7 / AG-3 / AG-4 states that never change.

The findings concern the controls meant to keep a run **offline** and **evidence-grade**:

- The connector provenance check validates the connector class, not the connection that class returns（SR-1）.
- The PF-16 inventory gate trusts a self-declared policy kind（SR-2）.
- Chained together, SR-1 and SR-2 let in-process code run every PF statement, including the PF-16 count SQL, over an
  arbitrary connection object and obtain `preflight_overall=ALL_PASS_OFFLINE`（R4）.
- Live TLS settings and the G-7 identity input are self-reported by the caller（SR-4, SR-5）.

Every finding needs deliberate in-process code. The runner has no driver, and its CLI is STOP-only, so **none of them
opens a Production path in the current tree**. SR-4 and SR-5 are **blockers for any future Production connector**.

## 1. Method

1. Read every in-scope file at `afd3fe974`, and `git diff bcdd14b afd3fe9` for the follow-up commits.
2. Offline reproduction script（synthetic CA, sockets replaced by a function that raises）for R1 to R4 and R9 to R11.
3. Statement-guard search against the local disposable PostgreSQL（R5, R6）.
4. Mutation check on a scratch copy of the runner: removing the STOP after a non-PASS step.
5. The relevant offline test suites（§6）.

## 2. Findings

Severity:

- **Medium**: a documented control is weaker than documented, or a future-Production blocker.
- **Low**: defence-in-depth gap.
- **Info**: hygiene.

| ID | Severity | Title |
| --- | --- | --- |
| SR-1 | Medium | Trusted connector provenance does not constrain the connection object or the method actually called |
| SR-2 | Medium | PF-16 inventory gate accepts a self-declared policy kind |
| SR-3 | Low | Connector provenance can be forged by in-process code |
| SR-4 | Medium | Live TLS settings and `ConnectParams` adherence are self-reported by the connector |
| SR-5 | Medium | PF-0 is a caller-supplied dict, not bound to the opened connection |
| SR-6 | Low | CA file can change between PF-0b hashing and the connector reading it（symlink / TOCTOU） |
| SR-7 | Low | `environ={}` disables the `PG*` TLS environment checks |
| SR-8 | Low | Statement guard allows side-effecting or long-running catalog functions |
| SR-9 | Low | A `BaseException` during rollback skips `close()` |
| SR-10 | Info | No client-side timeout before PF-15 |
| SR-11 | Info | Stale docstring and dead constants |

### SR-1（Medium）Trusted connector provenance does not constrain the connection object or the method actually called

**Evidence**

- `scripts/g7_dedicated_preflight_runner.py:785-802`: `_trusted_offline_connector()` checks:
  - `type(connector).__name__`;
  - `PREFLIGHT_CONNECTOR_KIND` in the class `__dict__`;
  - `inspect.getfile(cls)` and `inspect.getfile(cls.connect)` against the checked-in test file.
- `scripts/g7_dedicated_preflight_runner.py:1139`: the runner then calls `connector.connect(...)` on the **instance**,
  and uses whatever object comes back（`:1148`, `:1061`, `:1178`, `:1183`）. The connection object gets no check.
- `backend/tests/test_g7_dedicated_preflight_runner.py:180-192`: `FakeConnector.__init__(self, conn=None, ...)` stores
  any object and `connect()` returns it unchanged. The trusted class is a generic pass-through.
- The trust anchor is a test file in the repository（`:86-97`）. OP-1 requires a clean checkout on the owner host
  （readiness §14.4）, so `FakeConnector` is importable on exactly the host where a future run would happen.
- Readiness `§15.2`（line 1233）describes the check as "concrete connector class and method provenance". It also
  states that the check is defence in depth, not a sandbox. That caveat is accurate. The first part overstates what is
  enforced.

**Reproduction（R1, R2）.** Load the test module and wrap an arbitrary connection object:

```python
c = UntrustedConnection()                      # any object with live_settings/execute/rollback/close
pf.run_preflight(config, tests.FakeConnector(c))          # R1
fc = tests.FakeConnector(); fc.connect = lambda p: c      # R2: the instance attribute shadows the checked method
pf.run_preflight(config, fc)
```

Observed for both: `stopped_at=PF-16 reason=independent_inventory_missing statements_executed=21`. All of PF-1 to
PF-15 were submitted to the untrusted object.

**Impact.** In-process code needs no forgery to send the full PF sequence over any connection it supplies. The runner
still has no driver, so this is not a Production path by itself.

**Fix direction（future PR）.**

- Make the trusted test connectors non-parametric: build their own fake or loopback connection, and accept no
  injected connection.
- Check `type(connector.__dict__.get("connect"))` / `vars(connector)` for instance overrides, or call
  `type(connector).connect(connector, ...)`.
- Validate the returned connection's class with the same provenance rule.

### SR-2（Medium）PF-16 inventory gate accepts a self-declared policy kind

**Evidence**

- `scripts/g7_dedicated_preflight_runner.py:98-99, 1018-1026`: the gate accepts any policy object whose
  `PREFLIGHT_INVENTORY_POLICY_KIND` attribute equals `"offline_test_double"` and whose `accept()` returns `True`.
- Unlike connectors（SR-1）, the policy has no provenance check.
- `backend/tests/test_g7_dedicated_preflight_runner.py:644`（`test_policy_without_accepted_kind_is_unresolved`）only
  covers a policy that does **not** claim the kind.
- Readiness §14.6.1 / §15.2: `PF16_INDEPENDENT_INVENTORY = UNRESOLVED`. "No PF-16 count query is submitted" without an
  accepted independent inventory.

**Reproduction（R4, chained with R1）**

```python
class SpoofedPolicy:
    PREFLIGHT_INVENTORY_POLICY_KIND = "offline_test_double"
    def accept(self, inventory): return True
pf.run_preflight(config_with_inventory_and_pf17, tests.FakeConnector(UntrustedConnection()), SpoofedPolicy())
```

Observed: `stopped_at=None`, `statements_executed=33`, **`pf16_count_statements_submitted=10`**, `all_pass=True`. The
rendered report contains `preflight_overall=ALL_PASS_OFFLINE`. It also still contains `g6=UNMET`, `g7=UNMET` and
`ag4_preflight_approval=NOT_AUTHORIZED`.

**Impact**

- The UNRESOLVED gate is a string comparison.
- The `ALL_PASS_OFFLINE` token can be produced for a run over an arbitrary connection with a self-approved inventory.
  The persistent UNMET / NOT_AUTHORIZED lines limit the risk of misreading it, but the token itself carries no
  provenance.

**Fix direction（future PR）**

- Apply the same provenance rule as for connectors, or remove the injectable policy until §14.6.1 is decided.
- Optionally emit `ALL_PASS_OFFLINE` only when both connector and policy are the checked-in test doubles.

### SR-3（Low）Connector provenance can be forged by in-process code

**Evidence.** `scripts/g7_dedicated_preflight_runner.py:798-800`:

- `inspect.getfile(cls)` reads `sys.modules[cls.__module__].__file__`;
- `inspect.getfile(cls.connect)` reads `connect.__code__.co_filename`.

In-process code can set both.

**Reproduction（R3）.** Without importing the test file: `compile()` a `FakeConnector` class with the test file's path
as filename, register a stub module whose `__file__` is that path, and set `cls.__module__` to it. Observed:
`stopped_at=PF-16`, 21 statements executed.

**Assessment.** The code（`:786-789`）and readiness §15.2 both say that code inside the process is trusted. This is a
documented limitation, so the severity is Low. SR-1 is the cheaper bypass.

### SR-4（Medium, future-Production blocker）Live TLS settings and `ConnectParams` adherence are self-reported by the connector

**Evidence**

- `scripts/g7_dedicated_preflight_runner.py:1147-1153` and `:950-989`: `evaluate_live_settings()` checks whatever
  mapping `conn.live_settings()` returns.
- `:1139-1141`: `ConnectParams(sslmode, sslrootcert)` is passed, but nothing verifies that the connector used it.
- `backend/tests/test_g7_dedicated_preflight_runner_db.py:94-96`: `LocalConnector.connect()` ignores `params`.
- `backend/tests/test_g7_dedicated_preflight_runner_db.py:177-184`: the only real-session sequence test stubs
  `live_settings` with `live_override`.
- The one real-libpq live check（`test_real_libpq_session_without_verify_full_stops_before_sql`）proves only the
  negative case.

**Impact.** §14.5 requires confirming "after connecting that the live conninfo `sslrootcert` equals the explicitly
configured value". In this design that confirmation is only as good as the connector's honesty. A connector could
report `verify-full` while connecting with `sslmode=disable`.

**Unverified.** How a Production connector would read `PQconninfo` / `ssl_in_use` from the same libpq connection object
that executes SQL, as `audit_tls_evidence._conninfo_option` does for the audit command.

**Fix direction（future PR, before any connector）.** Derive live settings inside the runner from the driver object
that executes SQL, or require the connector to expose the raw `pgconn` and read it in the runner. Add a real-libpq
positive test with a local TLS server and a test CA.

### SR-5（Medium, future-Production blocker）PF-0 is a caller-supplied dict, not bound to the opened connection

**Evidence**

- `scripts/g7_dedicated_preflight_runner.py:889-903`: `evaluate_pf0()` accepts any mapping of six `PASS` strings.
  It is not produced or verified by `g7_gate1_identity_check` in-process.
- `:980-984`: the live check accepts `kamimusubi_audit_ro.<any safe suffix>`. The suffix is not compared with the
  project reference that G7-A1 approved.
- Host, port and database name of the live connection are never compared with the G7-A target.
- `ConnectParams`（`:764-769`）carries no target at all; the connector chooses it.

**Impact.** PF-0 PASS does not show that the connection PF-1 to PF-17 ran on is the target G7-A evaluated. Readiness
§14.6 notes that G-7 needs PF-0, PF-16 and PF-17 together. With no binding, that combination cannot be established by
this runner.

**Fix direction（future PR）.**

- Run the G7-A evaluation inside the runner on the same URL the connector will use.
- Compare live `host` / `port` / `dbname` / user suffix against the approved target, without returning them.

### SR-6（Low）CA file can change between PF-0b hashing and the connector reading it（symlink / TOCTOU）

**Evidence.**

- `scripts/g7_dedicated_preflight_runner.py:925-947`: PF-0b resolves the path and hashes the **resolved** file.
- `:1140`: the runner passes the **unresolved** `config.sslrootcert` to the connector.
- `:976`: the live check compares path strings only, not content.

**Reproduction（R10）.**

1. `sslrootcert` is a symlink to the accepted CA.
2. The symlink is re-pointed to a different PEM between PF-0b and `connect()`.
3. Result: `stopped_at=PF-16`, 21 statements executed, `hash_read_at_connect_matches_accepted=False`.

**Impact.** Needs local write access to the CA path. Defence in depth.

**Fix direction.** Pass the resolved path, require a non-symlink regular file owned by the operator with mode `0600`,
and re-hash after the session ends（or hash an fd that libpq is given）.

### SR-7（Low）`environ={}` disables the `PG*` TLS environment checks

**Evidence.**

- `scripts/g7_dedicated_preflight_runner.py:780-782, 908-924`: `PreflightConfig.environ` defaults to `None`, which
  means `os.environ`. An empty mapping silently skips the `PGSSLMODE` / `PGSSLROOTCERT` checks.
- Every unit test passes `environ={}`（`backend/tests/test_g7_dedicated_preflight_runner.py`, `_config()`）.

**Reproduction（R9）.** With `PGSSLROOTCERT=/somewhere/else.crt` in the process environment:

- `environ=None` → `tls_environment_conflict`;
- `environ={}` → `ok`.

**Notes.**

- libpq gives explicit conninfo parameters precedence over `PG*` variables, so the practical effect is limited.
- `PGSERVICE` / `PGSERVICEFILE` / `PGSSLCRL` / `PGSSLNEGOTIATION` are not inspected.

**Fix direction.** Always read `os.environ`, and accept an override only from tests through a private seam.

### SR-8（Low）Statement guard allows side-effecting or long-running catalog functions

**Evidence.** `scripts/g7_dedicated_preflight_runner.py:146-153`: the deny list is an enumeration.

**Reproduction（R6）.** `validate_statement()` returns `(True, 'ok')` for:

- `SELECT pg_stat_reset()`
- `SELECT pg_stat_reset_shared('bgwriter')`
- `SELECT pg_log_backend_memory_contexts(1)`
- `SELECT pg_sleep(3600)`
- `SHOW ALL`

**Not reproduced（R5）.** A literal-desynchronisation bypass using `E'…\'…'` strings. A bounded search found no
PostgreSQL-valid statement that hides `set_config()` from the guard:

- 10 literal forms;
- up to 4 literal pieces around the call;
- each candidate checked on the local disposable database inside `BEGIN READ ONLY`.

The reason: every PostgreSQL-valid backslash escape leaves a backslash outside a regex-literal, and `:170` rejects
that. One guard-accepted string was found, but PostgreSQL rejected it as `unterminated quoted string`. This is a
bounded search, not a proof.

**Assessment.** The guard is documented as defence in depth. The primary control, identity membership in `REGISTRY`
（`:1048`）, holds. No registry statement calls these functions.

**Fix direction.** Prefer an allow-list of function names for any future dynamic statement, or keep the guard purely
as a registry-integrity check.

### SR-9（Low）A `BaseException` during rollback skips `close()`

**Evidence.** `scripts/g7_dedicated_preflight_runner.py:1173-1189`: `_end_session()` catches `Exception` only, and
`close()` follows `rollback()` without a `finally`.

**Reproduction（R11）.** A connection whose `rollback()` raises `KeyboardInterrupt` → `close_called=0`.

**Fix direction.** Wrap `close()` in `try/finally` around the rollback.

### SR-10（Info）No client-side timeout before PF-15

`statement_timeout` is checked only at PF-15（`:713-716`）. A hung `live_settings()` or an earlier statement has no
bound in the runner. Whether the role-level `statement_timeout`（§14.3 condition 3）applies through the pooler is
§14.10 item 4（UNKNOWN）.

### SR-11（Info）Stale docstring and dead constants

- `:1124`: the `run_preflight` docstring still says connectors are accepted by `ACCEPTED_CONNECTOR_KINDS`. Since
  `9142f04` the decision is `_trusted_offline_connector()`.
- `ACCEPTED_CONNECTOR_KINDS`（`:83`）is used only by `test_accepted_connector_kinds_have_no_production_kind`（test
  `:853`）.
- `ProductionConnectionDisabled`（`:130`）is never raised.

## 3. Controls verified as working

| Control | Evidence | Verification |
| --- | --- | --- |
| No Production entry point | `:1134-1135` default `None` → `production_connection_disabled`; `:1197-1201` CLI ignores `argv` and the environment, exits 2 | Tests `test_default_connector_is_the_disabled_production_path`, `test_cli_entry_point_is_disabled`（`:907`） |
| No driver / socket / logging in the runner | imports `:44-55` | Test `test_module_imports_no_driver_socket_or_django`（`:882`） |
| Fixed registry, identity-checked | `:553-748`; `_GuardedSession.submit` `:1047-1063` | Tests `test_session_refuses_statements_outside_the_registry`, `test_pf_sql_is_verbatim_from_section_14_7` |
| Sequential fail-closed | `_record` `:1078-1087`; loop `:1159-1163` | Parametrised STOP tests. A mutant without STOP after PF-0b → **48 failed / 99 passed** on a scratch copy at `afd3fe974` |
| Rollback / close on `Exception` paths; cleanup failure → STOP | `:1164-1189`; `all_pass` `:839-849` | Tests `test_cleanup_failure_turns_all_pass_into_stop`（`:859`）, `test_rollback_error_still_closes`, `test_begin_failure_rolls_back_and_runs_no_pf_sql` |
| PF-0b rejects missing / `system` / relative / invalid / in-repository / mismatched / implicit CA | `:906-947` | Tests in the PF-0b section |
| Live mismatch stops before any SQL, connection closed | `:1147-1153` | Test `test_live_settings_mismatch_stops_before_any_sql`（`:578`） |
| Redaction: fixed tokens only; exception text dropped（`from None`）; PF-16 shares match booleans only | `:851-881`, `:1063`, `:1143`, `:1113-1114` | `_assert_redacted` in the unit tests. Manual review found no path that renders a host, path, user, exception or found relation name |
| PF-16 default gate | `:805-812`, `:1093-1095` | Test `test_missing_inventory_stops_before_count_sql`. Default policy never accepts（`test_default_policy_never_accepts_an_inventory`, `:618`） |
| Persistent G6 / G7 UNMET, AG3 / AG4 NOT_AUTHORIZED | `FINAL_STATE` `:101-110`, rendered unconditionally `:865-868` | Present even in the R4 all-PASS report |
| Local DB adapter is loopback-only | test `_db.py:29-42` | Tests `test_disposable_connector_rejects_remote_config`（`:120`）, `test_disposable_connector_forces_loopback`（`:127`） |
| TLS / RLS / TEMP / approval policies of the audit command unchanged | `git diff d95d911 afd3fe9 -- backend/temples scripts/migration_safety backend/shrine_project` is empty | 144 audit-command tests pass（§6） |

## 4. Test coverage gaps（regression tests to add in the fix PR）

1. A trusted `FakeConnector` wrapping a foreign connection object（R1）, and an instance-level `connect` override（R2）.
2. A policy that claims `PREFLIGHT_INVENTORY_POLICY_KIND = "offline_test_double"` from an untrusted class（R4）.
3. `environ={}` versus the process environment（R9）.
4. A symlinked CA re-pointed after PF-0b（R10）.
5. A `BaseException` in `rollback()` still closes（R11）.
6. A real-libpq **positive** live-settings test against a local TLS server with a test CA. Today only the negative case
   and a stubbed `live_override` exist（SR-4）.
7. A binding test: live host / port / dbname / user suffix against the G7-A target（SR-5）.
8. Guard regressions for the R6 functions, and a property test for literal desynchronisation（R5）.
9. `LocalConnector` ignores `ConnectParams`. No test shows that the TLS params reach a real connection.

## 5. Unresolved assumptions and residual risks

1. **Threat model.** The runner assumes that all code in the process is trusted（`:786-789`, §15.2）. SR-1 to SR-3 are
   in-scope only if that assumption is narrowed. This review treats it as a documented assumption, not a defect, and
   rates accordingly.
2. **OS-level isolation.** Network isolation of the test process is assumed, not verified. CI and this review relied
   on socket monkeypatching（unit tests）and loopback `hostaddr`（DB tests）.
3. **Every readiness §14.10 item is UNKNOWN.** That covers the pooler, `pg_stat_ssl`, `CONNECTION LIMIT 1`,
   `ALTER ROLE … SET` defaults, RLS / legacy relations and provider catalog restrictions.
4. **`PF16_INDEPENDENT_INVENTORY = UNRESOLVED`**（§14.6.1）. SR-2 must be fixed before any policy implementation is
   introduced.
5. **No Production connector exists.** SR-4 and SR-5 describe properties that connector must have. They cannot be
   verified now.
6. **R5 search is bounded.** The absence of a guard bypass is not proven.
7. **Line numbers refer to `afd3fe974`.**

## 6. Tests run（offline / local disposable PostgreSQL 16, Python 3.13; CI uses 3.11）

| Suite | Result |
| --- | --- |
| `backend/tests/test_g7_dedicated_preflight_runner.py`, `…_db.py`, `test_g7_gate1_identity_check.py`, `temples/tests/test_report_db_tls.py` | 214 passed |
| `temples/tests/services/test_evidence_coverage_audit*.py`, `test_audit_tls_evidence.py`, `test_audit_rls_ca_fail_closed.py`, `tests/test_db_tls_options_propagation.py` | 144 passed |
| `scripts/migration_safety/tests/test_guard.py` | 49 passed |
| Mutation（STOP removed after PF-0b, scratch copy） | 48 failed / 99 passed（detected） |

## 7. Recommended next steps（each needs its own PR and approval; none is authorized here）

1. Fix PR for SR-1, SR-2, SR-7, SR-9 and SR-11, with the regression tests in §4 items 1 to 5. This keeps the offline-only
   scope.
2. Design note for SR-4 / SR-5（runner-derived live settings and target binding）before any Production connector is
   proposed.
3. Optional hardening for SR-6 and SR-8.
4. OP-6 remains **STOP** until those changes are merged and independently re-reviewed.
