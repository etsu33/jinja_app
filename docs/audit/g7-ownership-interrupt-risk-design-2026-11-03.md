# G7 offline preflight ownership / interrupt risk design audit (Issue #3426)

- Status: **DESIGN AUDIT ONLY / NOT AN IMPLEMENTATION APPROVAL**
- Baseline: `develop` @ `f9cf35c440caef533640744c9f67cf0384c23dc4` (merged PR #3425)
- Scope: offline test double and local disposable PostgreSQL connector only.
- Out of scope: Production connection, role creation, GRANT/REVOKE, deployment/config/secrets, DB migrations, approval of PF-16 evidence, SR-4/SR-5 implementation.
- Invariant: `OP-6=STOP`, `G6=UNMET`, `G7=UNMET`, `AG-3/AG-4=NOT_AUTHORIZED`, `PRODUCTION_CONNECTION=STOP`.
- Sources: `scripts/g7_dedicated_preflight_runner.py`, `backend/tests/test_g7_dedicated_preflight_runner.py`, `backend/tests/test_g7_dedicated_preflight_runner_db.py`, `docs/audit/evidence-coverage-production-readiness-2026-11-01.md` §15.6, and prior PR #3425 security review.
- Evidence classification: **CODE CONFIRMED** = read at baseline; **REPORTED TEST** = prior PR output, not independently rerun for this audit; **PROPOSED TEST** = future, not executed.

## 1. Verified implementation-to-risk mapping

| ID | Code location / verified condition | Threat and limitation | Existing evidence | Scope of follow-up |
| --- | --- | --- | --- | --- |
| R1: allocation-to-record interrupt | `backend/tests/test_g7_dedicated_preflight_runner_db.py`: `LocalConnector.connect()` calls `_open_loopback_raw()` then `allocated.append(raw)` then `_unadopted.append(raw)`. `FakeConnector.connect()` creates `FakeResource()` then records it. | A `BaseException` delivered between acquisition and the first registration leaves a resource not available to `release_unadopted()`. This is not addressed merely by catching exceptions in `run_preflight()`. | **CODE CONFIRMED** for instruction window; prior tests cover failure *after* recording, not this window. | Define resource acquisition/registration guarantee and test seam; no untrusted returned-object method calls. |
| R2: transfer flag window | `scripts/g7_dedicated_preflight_runner.py`: after `_trusted_offline_connection()`, sequential assignments `conn = returned` then `transferred = True`; inner `finally` calls `_release_unadopted()` if false, outer `finally` calls `_end_session(conn,...)`. | Interrupt between assignments may invoke connector release and runner close on same handle. psycopg double-close has been *reported* as safe for tested driver; other drivers are not covered. | **CODE CONFIRMED** for the two assignments; **REPORTED TEST** for psycopg idempotent close. | Explicitly specify safe ownership handoff or a deterministic interruption experiment; reject dependence on general driver idempotency. |
| R3: release without time bound | `_release_unadopted()` invokes `type(connector).release_unadopted(connector)` synchronously; `LocalConnector.release_unadopted()` loops over stored raw handles and calls `raw.close()`. | If a trusted local test connector hangs in cleanup, the calling preflight has no enforced deadline. An exception handler does not bound execution time. | **CODE CONFIRMED**; timeout guarantee not present. | Evaluate bounded subprocess cleanup vs explicit documented operational limit. Do not claim Python threads or ordinary try/except can safely terminate a blocked close. |
| R4: same-process spoofing (SR-3) | `_trusted_instance()` checks `inspect.getfile`, exact class name, class method provenance, and instance shadowing; trusted connector files are Python test modules. | A malicious actor already executing Python in the same process may forge or mutate trusted state. Provenance checks are not a sandbox. | **CODE CONFIRMED**; OS isolation not evaluated. | Specify threat model, subprocess/namespace/container isolation boundary, network denial, and tests. |

## 2. Proposed deterministic reproduction tests and acceptance criteria

### R1: unregistered handle

- **Injection point:** after raw handle acquisition returns but before `_unadopted.append(raw)`; use an isolated disposable fake/loopback connector harness. Merely injecting an exception after the append is insufficient.
- **Positive control:** demonstrate the acquired handle exists and is still open immediately before forcing interruption (fake resource state; real DB uses a separate autocommit observer by exact backend PID).
- **Fail signal:** after interruption, at least one originally opened handle remains reachable/open or its backend PID remains present beyond a bounded observation window. Retain only boolean/count tokens, not backend identifiers.
- **PASS criterion:** every connector-owned handle created in the tested interruption window is released exactly once in the fake; local PostgreSQL backend disappears as observed by a separate autocommit connection. If an exception can arrive in a window Python cannot eliminate, document the guarantee limit explicitly and classify remaining risk for Mother Ship.
- **Safety:** never touch an arbitrary rejected Connection object; no Production endpoint.

### R2: handoff double-close

- **Injection point:** between `conn = returned` and `transferred = True`; reproducible scheduling hook must be test-only and must not be callable from Production input.
- **Instrumentation:** count `release_unadopted()`, `rollback()`, `close()` per resource, not merely total calls. Include a deliberately non-idempotent fake close to detect double-close.
- **PASS criterion:** no resource is leaked; exactly one party is responsible for releasing any accepted resource under every injected handoff failure. If the implementation intentionally depends on idempotent psycopg close, bound that guarantee to the exact local connector and record a counterexample with a non-idempotent fake.
- **Regression criterion:** rejected object methods never called; STOP cannot become `ALL_PASS_OFFLINE`.

### R3: bounded cleanup

- **Injection point:** trusted fake connector cleanup that blocks indefinitely, in an isolated subprocess with external watchdog.
- **PASS criterion:** test harness terminates in a defined deadline and reports STOP or a fixed failure token without leaking secrets. Distinguish *harness deadline* from an *actual Runner-enforced timeout*. Only claim the latter if a reliable killable process boundary is implemented and separately tested.
- **Trade-off:** a thread timeout is not sufficient to prove underlying blocked libpq call stopped. Signal-handling and cleanup cancellation may themselves create R1/R2 races.
- **Open design decision:** whether to introduce subprocess isolation to bound cleanup, or retain timeout as an explicitly accepted risk. No implementation until Mother Ship decides.

### R4: process trust boundary

- **Positive control:** intentionally forged same-process test double demonstrates that source-code provenance alone cannot be a security boundary; execute only in a disposable harness without credentials.
- **Isolation test plan:** launch runner in a controlled child process/container with explicit allowlisted loopback-only network access; block external egress, production DNS, credential/environment mounts and inherited sensitive file descriptors; make controls measurable.
- **PASS criterion:** adversarial Python in the runner process cannot reach external networks or production secrets even when provenance is bypassed, *if* OS-level sandboxing is declared in scope. Without sandbox, mark R4 as open, not solved.
- **Open decision:** isolation implementation / platform support / CI viability; do not use in-process monkeypatching as evidence of network isolation.

## 3. Cross-cutting invariants and evidence protocol

1. `run_preflight(config, connector=None)` returns STOP; Production connector kind never added by this issue.
2. Unexpected inputs, rejected connector and returned Connection, or release failure must never submit a registry SQL statement or produce PASS after STOP; accepted local run follows read-only fixed registry.
3. No exception messages, driver conninfo, hostnames, credential paths, backend PIDs, usernames, or secrets in report, test logs, screenshots or PR text.
4. When querying `pg_stat_activity`, use a **separate autocommit observer** and **positive control** to avoid PostgreSQL transaction snapshot caching; fail tests if the positive control cannot see a live backend. Only local disposable database.
5. Distinguish test observations from actual guarantee: **pass/fail/unknown**, source SHA, environment class, CI job ID, mutation/negative controls. Do not treat earlier PR output as new independent execution.
6. Every implementation change must include negative tests proving the test can detect deliberate leak/double-release and must run relevant unit/DB/xdist suites and security static checks. Integration CI skipped is not PASS.
7. Update `README.md`, `architecture.md`, `roadmap.md` **only if** the implementation changes documented architecture/product scope. If not, record a no-change determination, and keep this audit in `docs/audit/`.
8. No new runtime methods callable from untrusted returned objects. Connector owns cleanup until Runner validates and adopts the return.

## 4. Proposed PR split (not authorized for execution)

- **PR-A, R1/R2**: minimal ownership-handoff mechanism and deterministic fail-injection tests. Consider a single atomic resource owner/lease object or a scoped acquisition context; reject any design that treats two independent booleans or unchecked return-object methods as a security guarantee.
- **PR-B, R3**: timeout / watchdog design and test contract only; implementation requires Mother Ship decision on subprocess boundary.
- **PR-C, R4**: OS-level sandbox feasibility and threat-model design; implement separately only if approved.

## 5. Gate to advance from audit to implementation

- [x] Source and issue mapping written against `f9cf35c440caef533640744c9f67cf0384c23dc4`.
- [x] Proposed reproduction cases, positive controls, negative controls, and acceptance criteria documented.
- [ ] Independent reviewer confirms the test hooks cannot escape offline/local-only scope.
- [ ] Mother Ship chooses implementation scope and whether R3/R4 require blocking guarantees.
- [ ] Separate code PRs and PR-specific tests created by Codex as authorized.
- [ ] Independent regression review and updated risk register.
- [ ] Mother Ship approves merging any implementation.

**This audit does not mark Issue #3426 resolved and grants no Production execution authority.**
