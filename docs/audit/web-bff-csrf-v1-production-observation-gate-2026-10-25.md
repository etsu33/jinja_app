# Web BFF CSRF V-1 — U-2 Production Observation and Enforcement Gates（2026-10-25）

## 1. Approval status and provenance

```text
RECORD TYPE                 = subsequent approval record（documentation only）; supplements #3323 §11 and #3325 §2
U-2                         = A — split L4 into two independently authorized sub-gates L4-O and L4-E
                              APPROVED（design only）
L4-O PRODUCTION OBSERVATION = NOT APPROVED（execution）
L4-E PRODUCTION ENFORCEMENT = NOT APPROVED（execution）
A-0 RUNTIME IMPLEMENTATION  = NOT APPROVED
U-3 / U-4 / U-5 / U-6       = OPEN
APPROVAL AUTHORITY          = Mother Ship
RUNTIME IMPLEMENTATION      = NONE EXISTS
PRODUCTION OBSERVATION      = NOT STARTED
PRODUCTION ENFORCEMENT      = NOT STARTED
FINAL STATUS                = STOP
```

**References**（read on `develop@ee5e758`; not edited）:

| record | role here |
| --- | --- |
| `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md`（#3323） | gates L0–L4（§11）, the rejection response（§5）, D0–D13（§2.2）, logging（§3.6） |
| `docs/audit/web-bff-csrf-v1-approval-record-2026-10-24.md`（#3324） | A-1 to A-8; A-3 conditions（§4.3）; A-7 deadline and conditions（§4.7）; A-8（§4.8） |
| `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md`（#3325） | phases（§2）, observation mode（§2.1）, duration（§3）, AC-1 to AC-13（§4）, privacy（§5）, recovery（§6）, evidence per phase（§8.1）, U-2 to U-6（§8.2） |
| `docs/audit/web-bff-csrf-v1-mode-contract-2026-10-24.md`（#3326） | U-1a / U-1b / U-1c, F-1 to F-3（§6）, manual switching M-1 to M-6（§7） |
| `docs/audit/web-bff-csrf-v1-observe-exceptions-2026-10-25.md`（#3327） | U-1d = A, U-1e = B |
| `docs/audit/web-bff-csrf-v1-d0-mode-approval-2026-10-25.md`（#3328, merged `ee5e758`） | C-1 = A, U-1h = A; U-2 listed as OPEN（§6） |

**Earlier unresolved clauses closed by this record:**

| record and clause | text at the time | resolved by |
| --- | --- | --- |
| #3325 §2.1, "Mapping to the contract gates" | "Whether the Phase 2 authorization is formally recorded as part of L4 or as its own gate is listed as U-2" | U-2 = A（§2） |
| #3325 §8.2, row U-2 | "whether the Phase 2 production observation authorization is a part of L4 or a separate gate" | U-2 = A（§2） |
| #3328 §6, row U-2 | "production observation authorization gate" — **OPEN** | U-2 = A（§2） |

**Gate architecture vs. passing a gate.**

| layer | state after this record |
| --- | --- |
| **gate architecture**（how production authorization is structured） | **approved**: L4 consists of L4-O and L4-E（§2） |
| **passing L4-O**（authorization to start Production observation） | **not approved**. No L4-O GO exists |
| **passing L4-E**（authorization to start Production enforcement） | **not approved**. No L4-E GO exists |

Approving the structure of a gate is not approval to pass it. This record authorizes no code, configuration
change, test run, deployment, observation or enforcement.

**Decision provenance.**

| item | value |
| --- | --- |
| decision maker | Mother Ship |
| decision | U-2 = A |
| how received | the task brief for this record, which states the decision and that A-0, L4-O execution, L4-E execution and any runtime, environment or deployment change are not authorized |
| approval timestamp | **not stated** in the brief, and therefore not recorded here |
| signed artifact | none is stored in the repository. This record is the in-repository statement of the decision |
| test evidence / deployment history | **none**. No implementation exists, no test has run, nothing has been deployed |
| interpretation | where this record adds an interpretation, it is labeled "interpretation" |

---

## 2. Relationship with the existing L4

| source | text |
| --- | --- |
| final contract #3323 §11, row L4 | "explicit Mother Ship go: enforce or report-only（S-4）, the time window, rollback by revert" |
| rollout plan #3325 §2 / §2.1 | Phase 2 needs "a **separate, explicit Mother Ship authorization** for production observation"; Phase 3 needs "an explicit Mother Ship **GO** for enforcement under L4（O-4）"; "This plan keeps both authorizations explicit and separate" |

**Approved reconciliation（U-2 = A）:**

- **L4 remains** the existing production rollout authorization framework. It is not replaced or bypassed.
- **L4-O and L4-E are two independently authorized stages within L4.**
  - **L4-O** covers the report-only / observation authorization（Phase 2, `observe`）.
  - **L4-E** covers the enforcement authorization（Phase 3, `enforce`）.
- **Neither stage inherits approval from the other.** An L4-O GO says nothing about enforcement; an L4-E decision
  cannot be issued in place of a missing L4-O stage.
- **No implicit, automatic or time-based promotion** between the stages, or from either stage to execution.
- **Both require an explicit and recorded Mother Ship GO.**

**No weakening.** Everything #3323 §11 attaches to L4 still applies:

- no production enforcement without L0–L3 passed and L4（now: L4-E）granted;
- an explicit Mother Ship go;
- a time window（for L4-O: the observation window, §4）;
- a rollback approach. #3323 says "rollback by revert"; whether revert is the mechanism is unverified and open as
  **U-5**（#3325 §6）. This record does not choose it.

The mode contract #3326 M-1 already reads "For Production, `observe` needs the Phase 2 authorization and `enforce` needs the L4 GO".
Under U-2 = A these are the L4-O GO and the L4-E GO respectively.

---

## 3. L4-O: Production observation authorization

L4-O is an explicit permission to start **Phase 2 in Production**（`observe`）, and only after every applicable
prerequisite below has passed.

### 3.1 Prerequisites before L4-O can be granted

Aligned with #3325 §2（phases）, §4（acceptance criteria）and §8.1（evidence per phase）:

| # | prerequisite | source |
| --- | --- | --- |
| P-1 | **A-0** separately approved | #3325 §8.1 Phase 0 |
| P-2 | the future V-1 implementation exists and is verified | #3325 §2 Phase 0 |
| P-3 | **L0** local tests passed（AC-1） | #3323 §11, #3325 §4 |
| P-4 | **L1** CI passed on the verified commit（AC-2） | #3323 §11, #3325 §4 |
| P-5 | **L2** Preview browser E2E passed in Chromium, WebKit and Firefox（AC-3） | #3323 §11, #3325 §4 |
| P-6 | **A-3** conditional Preview validation evidence passed（AC-4）. Test use alone does not count | #3324 §4.3, #3325 §4 |
| P-7 | **L3** Production public-origin configuration inspection passed（AC-5）, by name, scope and shape only | #3323 §11, #3325 §4 |
| P-8 | the observation-mode implementation and its logging tested（U-1; #3326 §8, #3327 §5, #3328 §5） | #3325 §8.1 Phase 2 |
| P-9 | **AC-10** normal-flow evidence on Preview | #3325 §8.1 Phase 2 |
| P-10 | **AC-11** `DELETE /api/users/me` contract tests passed | #3325 §8.1 Phase 2 |
| P-11 | **AC-12** logout failure tests passed（A-5） | #3325 §8.1 Phase 2 |
| P-12 | a documented observation window identified（planned start; standard 24 hours, O-1） | #3325 §3 |
| P-13 | a recovery plan available for this change（M-6） | #3326 §7, #3325 §6 |
| P-14 | the target commit and deployment identifiable（M-3） | #3326 §7 |
| P-15 | a separate, explicit Mother Ship **L4-O GO** recorded（§4） | U-2 = A |

### 3.2 Before Phase 2 vs. during Phase 2

| completed **before** L4-O（no Production traffic needed） | completed only **during** Phase 2（needs Production traffic） |
| --- | --- |
| AC-1, AC-2, AC-3, AC-4, AC-5（L3）, AC-10 on Preview, AC-11, AC-12; P-8, P-12 to P-14 | AC-6（no unresolved D0 in the Phase 2 log review）, AC-7（false-positive classification）, AC-8（legitimate traffic per route）, AC-9 in Production（owner-controlled cross-site test page producing the expected would-be rejection rows）, AC-10 during Phase 2 |

- **Production observation evidence is not a prerequisite for starting observation.** AC-6 to AC-9 and the
  Phase 2 part of AC-10 are produced by Phase 2 itself and belong to L4-E（§6）.
- The AC-9 security test results from §8.2–§8.3 / §8.6 of #3323 are pre-Phase-2 test evidence（they are part of
  L0 and L2）; only the Production part of AC-9 waits for Phase 2.

### 3.3 Acknowledgements an L4-O GO must contain

- **CSRF exposure remains during `observe`.** Observation mode does not block CSRF requests; the base-contract
  T1–T11 exposure stays open in Production during Phase 2（#3325 §2.1, #3326 §4.1）.
- **L4-O does not activate enforcement.** Moving to `enforce` needs L4-E（§6）.
- **F-3 can be user-visible in `observe`.** Under U-1d = A an internal evaluator error returns 403 on all six
  in-scope routes（#3327 §2.5）.

### 3.4 Dependencies affecting L4-O（noted, not decided）

- **U-4**（evidence storage and format）is open, so where the L4-O decision record（§4）and its evidence references
  are stored is not decided.
- **U-5**（rollback mechanism）is open. P-13 requires a recovery plan for the change; this record does not decide
  whether U-5 must be closed first. Interpretation: a recovery plan whose restore mechanism is unverified may not
  satisfy M-6, and Mother Ship judges that when an L4-O GO is requested.

---

## 4. L4-O decision record（future template）

A proposed template for the record issued when Mother Ship later decides L4-O. **No GO decision exists now**, and
no record of this kind has been created.

| field | content |
| --- | --- |
| gate identifier | `L4-O` |
| decision | `GO` / `NO-GO` |
| target environment | `Production` |
| authorized mode | `observe` |
| target commit SHA | full SHA of the verified commit |
| deployment identifier | the Production deployment ID |
| L0–L3 evidence references | links to the AC-1 to AC-5 evidence |
| pre-observation acceptance evidence | references for AC-10（Preview）, AC-11, AC-12 and the observation-mode tests（P-8） |
| observation window（UTC） | planned start, and planned end of the standard 24 hours; actual start and end, and any extension with its reason, are recorded in the observation evidence record（#3325 §3） |
| monitoring owner | the person responsible for the Phase 2 log review |
| recovery-plan reference | the M-6 plan for this change |
| Mother Ship authorization reference | where the decision is recorded |
| approval date / time and approver identity | filled in **only** when an actual decision is issued |
| acknowledgements | §3.3 |

**Never recorded:** raw environment-variable values, raw request headers（`Origin`, `Host`）, cookies,
`Authorization`, tokens or request bodies（#3325 §5.2）. Configuration is confirmed by name, scope and shape only.

An L4-E record would use the same fields with authorized mode `enforce`, the completed observation evidence
record, AC-1 to AC-12 references and the AC-13 decision. Its exact form is likewise a future template.

---

## 5. Observation operation（preserved）

A-6 rules, unchanged（#3325 §1.1）:

| # | rule |
| --- | --- |
| O-1 | the standard observation duration is 24 hours |
| O-2 | observation is extended when required acceptance criteria are unmet |
| O-3 | no automatic transition after the duration |
| O-4 | an explicit Mother Ship GO is required before enforcement（now: L4-E） |
| O-5 | rollback is manual and requires Mother Ship approval |
| O-6 | disabling enforcement is an exceptional security-risk decision |

Mode-contract decisions, unchanged:

- **C-1 = A:** D0 in `observe` is logged and existing processing continues（#3328 §2.4）.
- **U-1d = A:** internal evaluator errors fail closed with 403（#3327 §2.3）.
- **U-1e = B:** non-JSON input on the four A-4 routes is observed without imposing the new `415`（#3327 §3.2）.
- **`DELETE /api/users/me`:** the existing `isAllowedOrigin` protection keeps deciding in `observe`（#3326 §4.3）.
- **U-1h = A:** `WEB_CSRF_MODE` is the approved variable name（#3328 §3）.

**Observation mode is not successful CSRF protection.** It measures; it does not protect（#3325 §2.1）.

---

## 6. L4-E: Production enforcement authorization

L4-E is **independent of L4-O**. Before Mother Ship can approve L4-E:

| # | requirement | source |
| --- | --- | --- |
| E-1 | the observation period has completed with sufficient evidence, recorded with start and end（UTC）and any extensions | #3325 §3, §8.1 Phase 3 |
| E-2 | AC-1 to AC-12 all satisfy the rollout plan; missing, partial or low-volume evidence is not a PASS | #3325 §4 |
| E-3 | no unresolved D0 configuration failures（AC-6） | #3325 §4, #3328 §2.4 |
| E-4 | legitimate-request coverage verified for each route（AC-8）; the count source is U-3 | #3325 §4 |
| E-5 | false-positive findings classified and resolved per the existing acceptance rules（AC-7） | #3325 §4 |
| E-6 | would-be JSON `415` compatibility reviewed: request formats inspected; no legitimate client unexpectedly failing | #3327 §6 |
| E-7 | expected attack-rejection outcomes verified（AC-9） | #3325 §4 |
| E-8 | no unresolved `evaluator_error` occurrence | #3327 §6 |
| E-9 | the recovery procedure for this change documented（M-6） | #3326 §7 |
| E-10 | Mother Ship explicitly issues a separate **L4-E GO**（AC-13） | #3325 §4, U-2 = A |

- **No success thresholds or traffic volumes** are set by this record.
- **None of these substitutes for L4-E:** an L4-O GO, a successful deployment, or the end of a 24-hour period（or
  of an extension）.
- **A-8 unchanged:** G3 stays blocked until V-1 is actually enforced in Production（#3324 §4.8）. Phase 2
  observation does not count.

---

## 7. Manual mode changes and recovery

The mode contract #3326 M-1 to M-6 are preserved. Every mode change, in any environment, requires:

| # | requirement |
| --- | --- |
| M-1 | a recorded Mother Ship decision |
| M-2 | the target mode and the identified environment |
| M-3 | the deployment or configuration revision |
| M-4 | the verification evidence for that transition |
| M-5 | confirmation that the change actually took effect |
| M-6 | a documented recovery plan |

In particular:

| change | authorization |
| --- | --- |
| first Production `observe` | **L4-O GO** |
| `observe` → `enforce` in Production | **L4-E GO** |
| `enforce` → `observe` | explicit Mother Ship rollback approval and security-risk acknowledgement under **O-5 / O-6** |

- **The existence of a configuration variable or a deployed revision is not proof of the effective mode**（M-5,
  #3326 §7）.
- **No automated fallback to observation.**
- **No silent disablement of CSRF defence.**
- Exact rollback commands and deployment mechanisms are **not chosen here**; they remain **U-5**.

---

## 8. Remaining open dependencies

| id | dependency | status |
| --- | --- | --- |
| **U-3** | source for legitimate first-party request counts（AC-8） | **OPEN** |
| **U-4** | evidence storage location and format | **OPEN** |
| **U-5** | rollback mechanism and exact commands | **OPEN** |
| **U-6** | extension length for each observation-period extension | **OPEN** |
| **S-6** | backend defense in depth | **OPEN** |
| **S-8 remainder** | browser, POST and Production verification | **OPEN** |
| **S-14** | Docker / self-hosted behaviour | **OPEN** |
| instrumentation | the mode marker and report-only instrumentation（#3325 §5.3, #3326 §4.2）; the would-be `415` log record（#3327 §4.3） | **OPEN**: implementation dependencies requiring A-0 and separate design validation |
| **A-0** | runtime implementation authorization | **NOT APPROVED** |
| **L4-O / L4-E** | execution of either gate | **NOT APPROVED** |

This record does not resolve U-3 to U-6.

**A-7 is preserved unchanged**（#3324 §4.7）: the Class B deadline（before general release; before a custom domain
is attached; the Class B PR merged no later than 14 days after the V-1 implementation PR merges）and the conditions
of the temporary risk acceptance. **The 14-day clock starts when the V-1 implementation PR merges**, not when this
documentation PR merges. It has not started. The Class B vulnerability is not fixed.

Interpretation（recorded only）: the 14-day clock runs from the implementation merge, while L4-O and L4-E each need
their own evidence and GO. Phases 1–3 may still be in progress while the clock runs（#3325 §7）.

### 8.1 Future synchronization（not done here）

- #3323 §11, #3325 §2.1 / §8.2 and #3328 §6 still describe L4 as a single gate or U-2 as open. A later
  documentation PR may add a pointer to this record there, if Mother Ship wants the historical records annotated.
  That is a proposal only.
- `README.md`, `architecture.md` and `roadmap.md` are unchanged.

---

## 9. Future acceptance tests and review criteria

**Nothing here is executed by this record.**

| # | case |
| --- | --- |
| G-1 | an L4-O GO cannot be recorded while any P-1 to P-14 prerequisite lacks its evidence reference |
| G-2 | an L4-O GO does not grant L4-E: the Production mode stays `observe` until a separate L4-E record exists |
| G-3 | an L4-E GO requires AC-1 to AC-12 PASS and an explicit AC-13 decision |
| G-4 | observation does not transition to enforcement automatically（#3326 T-12） |
| G-5 | incomplete, partial or low-volume observation evidence is recorded as "not satisfied", never as PASS |
| G-6 | every mode change carries M-1 to M-6 and the applicable L4-O / L4-E / O-5 decision |
| G-7 | invalid mode configuration remains fail closed（F-1, #3326 T-2） |
| G-8 | this documentation approval activates no runtime behaviour: no code, variable or deployment changes with it |
| G-9 | G3 remains blocked before Production enforcement（A-8） |

---

## 10. STOP

```text
U-2  = A — design approved
A-0  = NOT APPROVED
L4-O = NOT APPROVED
L4-E = NOT APPROVED
runtime code                 UNCHANGED
API routes                   UNCHANGED
authentication / cookies     UNCHANGED
environment variables        UNCHANGED
Production                   UNCHANGED
deployment                   NONE
observation                  NOT STARTED
enforcement                  NOT STARTED
automated promotion          NONE
automated rollback           NONE
G1–G5                        NOT IMPLEMENTED
PR merge                     NONE
```
