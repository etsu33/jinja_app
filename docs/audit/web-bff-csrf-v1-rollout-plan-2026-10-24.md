# Web BFF CSRF V-1 — A-6 Phased Rollout Plan（2026-10-24）

## 1. Purpose and approval status

```text
RECORD TYPE          = rollout plan（documentation only）; supplements #3323 and #3324
A-6                  = B — phased rollout; operational decisions APPROVED（§1.1）
A-0 RUNTIME          = NOT APPROVED
L4 PRODUCTION ROLLOUT = NOT APPROVED
OBSERVATION MODE     = DOES NOT EXIST YET（§2.1, §5.3）
EVIDENCE             = NONE COLLECTED; no phase has started
FINAL STATUS         = STOP
```

**References**（read and preserved; not edited）:

| record | role |
| --- | --- |
| `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md`（#3323, merged `dc17d82`） | implementation contract: D0–D13, public-origin configuration, logging §3.6, tests §8, gates L0–L4 §11 |
| `docs/audit/web-bff-csrf-v1-approval-record-2026-10-24.md`（#3324, merged `1f60058`） | A-1 to A-8 approvals, including the A-3 "test use vs validated reliance" clarification and the A-7 deadline and conditions |

This plan **adds** the A-6 operational decisions. It does not change the historical approval status in either
record: there, A-6 is "approved in principle, details open". This plan records those details as now decided.

### 1.1 Mother Ship decisions recorded（A-6 = B, operational details — APPROVED）

| # | decision |
| --- | --- |
| O-1 | the observation duration is **24 hours** |
| O-2 | if the acceptance criteria are not satisfied, **observation is extended** |
| O-3 | completing 24 hours does **not** automatically authorize enforcement |
| O-4 | production enforcement requires **all acceptance criteria to pass** and a **separate, explicit Mother Ship GO** |
| O-5 | rollback is **manual** and requires **Mother Ship approval** |
| O-6 | disabling CSRF enforcement is an **exceptional security-risk decision**, never an automatic response to operational failures |

### 1.2 What these approvals are, and are not

| layer | state |
| --- | --- |
| design approval | A-6 phased rollout and O-1 to O-6: **approved** |
| runtime implementation | **not authorized**（A-0）. No guard, no observation mode, no instrumentation exists |
| production authorization | **not authorized**（L4）. No production observation and no enforcement may start |

---

## 2. Rollout phases

| phase | content | gates（contract §11） | authorization needed to **start** |
| --- | --- | --- | --- |
| **Phase 0** — local implementation verification | the V-1 implementation PR passes its unit, route and regression tests and the repository hooks; CI is green | **L0, L1** | **A-0**（runtime implementation） |
| **Phase 1** — Preview browser E2E | the contract §8.6 E2E on the PR's Preview, in Chromium, WebKit and Firefox | **L2** | Phase 0 passed; owner access to the SSO-protected Preview |
| **Phase 2** — production observation | the guard runs in production in **observation mode**（§2.1）for the observation period（§3） | **L3** before the start | Phase 1 passed; L3 passed; a **separate, explicit Mother Ship authorization** for production observation |
| **Phase 3** — production enforcement | the guard **blocks** rejected requests in production | **L4** | all acceptance criteria（§4）pass, **and** an explicit Mother Ship **GO** for enforcement under L4（O-4） |

### 2.1 Observation mode

- **Observation mode does not block CSRF requests.** A request the decision table would reject（D0–D13）is logged
  with the §5 fields, and it is then processed as it is today.
- During Phase 2 the existing CSRF exposure（the base contract T1–T11）therefore remains **open in
  production**. Phase 2 measures; it does not protect.
- **Observation mode does not exist today.** The final contract §4 does not define a switch between
  observation and enforcement. Building one is a **future implementation dependency**:
  - it needs A-0;
  - its mechanism must be specified in the V-1 implementation PR（§8.2, U-1）.
- **Mapping to the contract gates（noted, not reinterpreted）.**
  - The contract §11 describes L4 as "explicit Mother Ship go: enforce or report-only". This plan keeps both
    authorizations explicit and separate:
    - Phase 2 needs its own production observation authorization, plus L3;
    - Phase 3 needs the L4 enforcement GO.
  - Neither authorization exists.
  - Whether the Phase 2 authorization is formally recorded as part of L4 or as its own gate is listed as U-2.
- **A-8:** Phase 2 observation is not "V-1 enforced in production"（approval record §4.8）. G3 stays blocked until
  Phase 3 is reached.

---

## 3. Observation duration

| rule | detail |
| --- | --- |
| standard duration | **24 hours** of Phase 2 observation（O-1） |
| extension | if any §4 criterion is not satisfied at the end of the period, observation is **extended**（O-2）. The length of an extension is set when it is decided and recorded with its reason |
| no automatic transition | the end of 24 hours, or of an extension, **does not** move to Phase 3（O-3）. Phase 3 needs O-4 |
| record keeping | when an observation period actually runs, record its **start and end time（UTC）**, the deployment and commit, and any extension with its reason, in an evidence record（§8） |
| dates | **no dates are set by this plan.** No deployment or observation date is assumed |

---

## 4. Acceptance criteria（all must pass before the Phase 3 GO request）

Each criterion needs the stated evidence. **Missing, partial or low-volume evidence is not a PASS.** It is
"not satisfied", which leads to an extension（O-2）or a stop.

| # | criterion | required evidence | not a PASS if |
| --- | --- | --- | --- |
| AC-1 | **L0** local tests | the test run output of the V-1 PR: the contract §8.1–§8.5 and §8.7 suites with pass counts; ESLint and `tsc` clean; the commit SHA | any failure; skipped suites; no recorded SHA |
| AC-2 | **L1** CI | links to the green `web-tests` / `backend-tests` runs on the final PR head | a red or missing run; a run on a different SHA |
| AC-3 | **L2** Preview E2E in **Chromium, WebKit and Firefox** | per browser and version: the contract §8.6 results — first-party POSTs pass; cross-site form POST（urlencoded / text/plain / multipart）, `no-cors` fetch and sandboxed iframe give 403 with the cookie jar unchanged; the browser-sent `Origin` / `Sec-Fetch-Site` on same-origin POST recorded as categories | any browser missing; any row not run |
| AC-4 | A-3 conditions | the A-3 validation tests and the Preview E2E above, passed and recorded（approval record §4.3） | not both recorded. Test use alone does not count |
| AC-5 | **L3** production public-origin configuration | the owner confirms `WEB_PUBLIC_ORIGINS` is set, Production-scoped, with the exact production origin(s), no wildcard and no `0.0.0.0`. Confirmed by name, scope and shape only | not confirmed by the owner, or values pasted into documents |
| AC-6 | no unresolved **D0** configuration failures | the Phase 2 log review shows zero D0 entries. Any D0 found has a recorded root cause and fix, followed by a fresh observation window | any unexplained D0; any D0 after the last fix |
| AC-7 | no unexplained **false positives** | every would-be rejection in Phase 2 reviewed and classified as "attack / non-browser / unexpected client" or "legitimate first-party". Zero unexplained legitimate first-party rejections | any rejection unclassified; any legitimate rejection without an explanation and decision |
| AC-8 | **sufficient legitimate traffic was observed** | the reviewed period contains first-party requests for **each** of the five routes. The count source is an open detail（U-3） | any route with no observed legitimate request in the window. **Low or zero volume is not a PASS** |
| AC-9 | expected **rejection of cross-origin attacks** | the security test results（contract §8.2–§8.3, §8.6）; in production observation, an owner-controlled cross-site test page producing the expected would-be rejection log rows | not run; or the logged row differs from the expected D-row |
| AC-10 | normal flows succeed | login, register, logout, concierge chat, compass weekly with test accounts on Preview（L2）and during Phase 2 | any flow failing, or untested |
| AC-11 | existing `DELETE /api/users/me` contract | the tests of contract §4.3 pass: same-origin → backend DELETE, cookies cleared on 204; both headers absent → 403（S-1 = A）; reference = the configured origin | not run, or deviating |
| AC-12 | logout failure behaviour（A-5） | a test or E2E proving that on a non-2xx logout the UI keeps the authenticated state and shows an error | not run |
| AC-13 | **explicit Mother Ship approval before enforcement** | a recorded GO decision under L4（O-4） | absent. No other criterion substitutes for it |

This plan states **no** observed traffic counts, error rates or test results. None exist yet.

---

## 5. Monitoring and privacy

### 5.1 Fields

Only the fields the contract §3.6 allows:

- the route path;
- the decision row（D0–D13）;
- the reason code.

In observation mode the same fields are used, plus the mode marker defined by the implementation（U-1）.

### 5.2 Never logged or copied into evidence

The raw `Origin`, `Host`, `Cookie`, `Authorization`, access or refresh tokens, any configuration value, and
request bodies. Evidence records contain counts and categories only.

### 5.3 Instrumentation dependency

- The contract §3.6 logs **rejections only**, and the final contract §4 does not define observation mode.
- Report-only behaviour, the mode marker, and any way to count legitimate requests per route（AC-8）would be
  **new runtime instrumentation**.
- That instrumentation is a **future implementation dependency requiring A-0**, and it must follow §5.1–§5.2.
- It is not authorized by this plan.

---

## 6. Rollback（manual procedure proposal）

Applies from Phase 2 onward. **No automatic rollback, no automatic CSRF bypass, no silent weakening**（O-5, O-6）.

| step | action | owner |
| --- | --- | --- |
| R-1 detect | an operational incident is observed: legitimate users blocked, D0 in production, an unexpected rejection pattern, unavailability of the five routes | anyone; reported to the owner |
| R-2 confirm impact | establish what fails, for whom, since when, and which D-row or reason code is involved. Use the §5 fields only | owner / implementer |
| R-3 Mother Ship decision | present the impact and the options: fix forward（e.g. correct the configuration）, return to observation, or return to a previous revision. **Disabling enforcement is an exceptional security-risk decision**（O-6）and must be named as such | **Mother Ship approval required**（O-5） |
| R-4 restore | apply only the approved option, to a **verified safe configuration or revision**: one that passed its own gates before | owner, as approved |
| R-5 re-verify | re-run the affected acceptance criteria（at least AC-5, AC-6, AC-10）against the restored state before declaring recovery | owner / QA |
| R-6 record | write an incident evidence record: the timeline（UTC）, impact, decision and approver, what was restored, and the re-verification results. No raw headers or tokens | owner |

**Unverified until implementation and environment inspection:**

- the exact operational commands;
- whether a configuration-only rollback is possible or a redeploy is needed;
- how a previous revision is restored on Vercel（e.g. promotion or rollback of a deployment）;
- how long each step takes.

The contract §11 mentions "rollback by revert"; whether revert is the mechanism is also unverified here.

---

## 7. Dependencies（preserved, not changed）

| item | state |
| --- | --- |
| **A-0** | runtime implementation **not approved**. Blocks Phase 0 and everything after it |
| **L4** | production rollout **not approved**. Blocks Phase 3; and, per §2.1 / U-2, any production observation authorization |
| **A-3** | conditional: validation tests and Preview E2E must pass（approval record §4.3）. Test use ≠ validated reliance. Production never uses the Preview platform values |
| **A-7** | Class B temporary acceptance with its deadline: before general release; before a custom domain; Class B PR merged ≤ 14 days after the V-1 implementation PR merges. Conditions: no new same-site sibling origin; the deferred inventory does not expand; any violation → reassessment. **The 14-day clock starts at the V-1 implementation PR merge, as recorded in #3324. This plan neither resets nor extends it.** The Class B vulnerability is not fixed |
| **A-8** | G3 must not start before V-1 is **enforced** in production（Phase 3）. Observation does not count |
| S-6, S-8 remainder, S-14 | **open** |

Note on timing（inference, recorded only）: A-7's 14-day clock runs from the V-1 implementation PR merge, not
from Phase 3. Phases 1–3 may still be in progress while the clock runs.

---

## 8. Evidence and remaining gates

### 8.1 Evidence required before each phase（none exists yet）

| before | evidence required |
| --- | --- |
| Phase 0 | the A-0 approval record |
| Phase 1 | AC-1, AC-2 |
| Phase 2 | AC-3, AC-4, AC-5（L3）, AC-10 on Preview, AC-11, AC-12; the observation-mode implementation present and tested（U-1）; the Phase 2 authorization record（U-2） |
| Phase 3 | an evidence record of the completed observation period（start and end UTC, any extensions）; AC-6, AC-7, AC-8, AC-9, AC-10 in production; all AC-1 to AC-12 PASS; then AC-13（the L4 GO） |

### 8.2 Unresolved operational details（cannot be determined from the current contract）

| id | detail | why it is open |
| --- | --- | --- |
| U-1 | the mechanism that selects observation vs enforcement（for example a server-only configuration flag）, its default, and its mode marker in logs | not defined in the final contract §4; needs A-0 and a contract addition in the implementation PR |
| U-2 | whether the Phase 2 production observation authorization is a part of L4 or a separate gate | the contract §11 L4 covers "enforce or report-only"; this plan requires both to be explicit and separate |
| U-3 | the source for counting legitimate first-party requests per route（AC-8） | the contract §3.6 does not log allowed requests; the platform log retention was observed as 1 hour on the current plan（#3320 §5） |
| U-4 | where the observation and incident evidence records are stored, and their format | not specified |
| U-5 | the exact rollback commands and mechanism（§6） | needs implementation and environment inspection |
| U-6 | the extension length when O-2 applies | decided per extension（§3） |

### 8.3 Proposed future synchronization（not done here）

None of `README.md`, `architecture.md` or `roadmap.md` is changed. When V-1 is implemented, a later PR may add a
short pointer to these audit records in the security section of the architecture documentation. That is a
proposal only.

---

## 9. STOP

```text
STOP — no runtime implementation
STOP — no CSRF guard implementation; no observation mode
STOP — no API route modifications
STOP — no cookie or authentication changes
STOP — no environment variable changes
STOP — no deployment or Production changes
STOP — no automatic enforcement; no automatic rollback or bypass
STOP — no G1–G5 implementation
A-0 = NOT APPROVED
L4  = NOT APPROVED
```
