# Web BFF CSRF V-1 — U-5 / U-6 Recovery and Observation Extension Design Approval Record（2026-10-25）

## 1. Approval status and provenance

```text
RECORD TYPE                 = subsequent approval record（documentation only）; supplements #3325 §3, §6, §8.2
U-5                         = B — manual restoration to a previously verified deployment is the preferred
                              Production recovery strategy                          APPROVED（design only）
U-6                         = B — each observation extension duration is determined individually from the
                              unmet acceptance criteria and documented reasons      APPROVED（design only）
DECISION AUTHORITY          = Mother Ship
A-0 RUNTIME IMPLEMENTATION  = NOT APPROVED
L4-O PRODUCTION OBSERVATION = NOT APPROVED
L4-E PRODUCTION ENFORCEMENT = NOT APPROVED
UD-1 to UD-11               = OPEN
RUNTIME IMPLEMENTATION      = NOT AUTHORIZED
PRODUCTION OBSERVATION      = NOT STARTED
PRODUCTION ENFORCEMENT      = NOT STARTED
FINAL STATUS                = STOP
```

**References**（read on `develop@ab83cda`; not edited）:

| record | role here |
| --- | --- |
| `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md`（#3323） | gates L0–L4 and "rollback by revert"（§11） |
| `docs/audit/web-bff-csrf-v1-approval-record-2026-10-24.md`（#3324） | A-7（§4.7）, A-8（§4.8） |
| `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md`（#3325） | O-1 to O-6（§1.1）, duration and extension（§3）, AC-1 to AC-13（§4）, R-1 to R-6（§6）, U-5 / U-6（§8.2） |
| `docs/audit/web-bff-csrf-v1-mode-contract-2026-10-24.md`（#3326） | M-1 to M-6（§7）; "a configuration change alone is not proof" |
| `docs/audit/web-bff-csrf-v1-observe-exceptions-2026-10-25.md`（#3327） | F-3 and observation invalidation（§2.3, §6） |
| `docs/audit/web-bff-csrf-v1-d0-mode-approval-2026-10-25.md`（#3328） | D0 by mode（§2） |
| `docs/audit/web-bff-csrf-v1-production-observation-gate-2026-10-25.md`（#3329） | L4-O / L4-E; P-13 and the U-5 note（§3.1, §3.4） |
| `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md`（#3330, merged `ab83cda`） | U-3 = A, U-4 = A; UD-1 to UD-11（§8） |

**Earlier unresolved clauses addressed by this record（design selection only）:**

| record and clause | text at the time | addressed by |
| --- | --- | --- |
| #3325 §8.2, row U-5 | "the exact rollback commands and mechanism（§6）" — "needs implementation and environment inspection" | U-5 = B selects the **preferred strategy**（§2）. Commands and mechanism stay **unverified**（§6） |
| #3325 §8.2, row U-6 | "the extension length when O-2 applies" — "decided per extension（§3）" | U-6 = B（§8） |
| #3329 §3.4 | U-5 open; whether it must close before L4-O not decided | §7: U-5 = B does not satisfy P-13 |
| #3330 §10, rows U-5 / U-6 | **OPEN** | U-5 = B, U-6 = B |

**What these approvals resolve, and what they do not.**

| resolved（design selection） | not resolved |
| --- | --- |
| U-5: the preferred recovery **strategy** | the operational verification of any recovery mechanism, its commands, permissions and timing（§6） |
| U-6: the **method** for deciding extension length | the scheduling of any observation window or extension（none is scheduled） |

- This record **supplements** the historical records and edits none of them.
- **U-5 and U-6 are design approvals only.** They authorize no runtime implementation, configuration change,
  rollback execution, deployment or Production observation.

**Decision provenance.**

| item | value |
| --- | --- |
| decision maker | Mother Ship |
| decisions | U-5 = B; U-6 = B |
| how received | the task brief for this record, which states both decisions and the authorization boundaries |
| approval timestamp | **not stated** in the brief, and therefore not recorded here |
| signed artifact | none is stored in the repository. This record is the in-repository statement of the decisions |
| test outcomes / deployment history / incidents / observation evidence | **none**. Nothing has been implemented, deployed, restored or observed |
| interpretation | where this record adds an interpretation, it is labeled "interpretation" |

---

## 2. U-5: Approved recovery strategy（decision B）

**U-5 = B: manual restoration to a previously verified deployment is the preferred recovery strategy.**

This is a **design preference**, not a confirmed operational capability.

### 2.1 What a "previously verified deployment" needs

| # | evidence |
| --- | --- |
| VD-1 | the deployment ID |
| VD-2 | the source commit SHA |
| VD-3 | the effective server-side mode（as verified under M-5, #3326 §7） |
| VD-4 | the applicable configuration revision or configuration state, by name, scope and shape only, **never raw values** |
| VD-5 | the relevant verification evidence（the gates and acceptance checks that target passed） |
| VD-6 | compatibility with the recovery objective approved in the R-3 decision |

- **A successful historical deployment alone is not sufficient** evidence that it remains safe to restore.
- #3325 §6 R-4 already requires restoring to "a verified safe configuration or revision: one that passed its own
  gates before". VD-1 to VD-6 make that evidence explicit.

### 2.2 Alternative options（conditional）

The other options named in #3325 §6 R-3 remain available as **conditional alternatives**. Each needs its own
verification and an explicit Mother Ship approval:

| option | condition |
| --- | --- |
| configuration correction / fix-forward | for example correcting the public-origin configuration（#3325 §6 R-3） |
| configuration-only mode change | only if technically supported **and** verified（feasibility is unverified, §6） |
| Git revert, then verification and deployment | the revert passes the applicable gates before it is deployed |

### 2.3 Not claimed

- **No specific Vercel restoration function** is claimed to be available.
- Restoring an older deployment is **not** claimed to restore its previous environment-variable values.
- Switching a server-side mode is **not** assumed to take effect without redeployment. #3326 §7 records that
  whether a running deployment picks up a changed server-side variable, for example whether a redeploy is
  needed, is unverified.

---

## 3. Relationship to the original "rollback by revert"

| source | text |
| --- | --- |
| final contract #3323 §11, row L4 | "explicit Mother Ship go: enforce or report-only（S-4）, the time window, **rollback by revert**" |
| rollout plan #3325 §6 | "The contract §11 mentions 'rollback by revert'; whether revert is the mechanism is also unverified here" |
| this record | U-5 = B: verified-deployment restoration is the **preferred** approach |

**Reconciliation dependency（open）:**

- The **"rollback by revert"** wording remains part of the historical contract. It is not deleted, overridden or
  reinterpreted here.
- **Verified-deployment restoration** is the approved design preference.
- **Whether it satisfies, supplements or requires a later amendment** to the original L4 rollback requirement is
  subject to separate technical verification and Mother Ship confirmation.
- **If both cannot be satisfied together**, the future approval process **STOPs** and returns the discrepancy to
  Mother Ship.
- **U-5's operational mechanism is not fully resolved** by this record.

---

## 4. Manual recovery lifecycle（preserved）

R-1 to R-6（#3325 §6）, unchanged:

| step | action |
| --- | --- |
| R-1 | detect the incident |
| R-2 | confirm impact and classify the incident（the #3325 §5 fields only） |
| R-3 | present the recovery options and obtain explicit Mother Ship approval（O-5） |
| R-4 | restore only the approved, verified-safe configuration or revision |
| R-5 | re-run the applicable acceptance checks, at least AC-5, AC-6 and AC-10（#3325 §6） |
| R-6 | record the incident, decision, restoration and post-recovery evidence |

Additionally:

- **no automated rollback**;
- **no automatic fail-open**;
- **no silent CSRF bypass**;
- **no unapproved mode change**;
- **no unverified restoration target**;
- **no declaration of successful recovery without effective-state verification**（M-5）.

M-1 to M-6（#3326 §7）are preserved: a recorded Mother Ship decision; the target mode and environment; the
deployment or configuration revision; the verification evidence; confirmation that the change took effect; a
documented recovery plan.

---

## 5. Security-sensitive recovery transitions

### 5.1 Production `observe` recovery

- Restoration may affect availability, telemetry, deployment identity and normal route behaviour.
- It follows R-1 to R-6 and needs explicit authorization（O-5）.

### 5.2 Production `enforce` recovery

Switching `enforce` to `observe` **weakens active CSRF protection**. It requires:

| # | requirement |
| --- | --- |
| ER-1 | explicit Mother Ship recovery authorization under **O-5** |
| ER-2 | explicit acknowledgement of the security-risk exception under **O-6** |
| ER-3 | recorded impact and restoration rationale |
| ER-4 | effective-mode verification afterwards（M-5） |
| ER-5 | incident evidence（R-6, U-4） |

- **A previously issued L4-O GO is not standing authorization** to disable enforcement later.
- **Neither rollback nor mode change occurs automatically.**
- Interpretation（recorded only）: under U-5 = B, restoring a deployment whose effective state is weaker than the
  current one — an `observe` deployment, or a pre-V-1 deployment without the guard — disables enforcement just
  as a mode change does. ER-1 to ER-5 therefore apply to it as well.

---

## 6. U-5 unverified operational dependencies

All **UNVERIFIED**:

| # | detail |
| --- | --- |
| RV-1 | the exact operational commands |
| RV-2 | the supported Vercel rollback / restoration operations |
| RV-3 | the required permissions and account roles |
| RV-4 | configuration-only rollback feasibility |
| RV-5 | whether a redeployment is required |
| RV-6 | whether historical deployments use the current or the previous environment configuration |
| RV-7 | authentication, session and cookie implications of restoration |
| RV-8 | the effective-mode verification procedure |
| RV-9 | recovery time and operational duration |
| RV-10 | actual restoration test results |
| RV-11 | compatibility with the original "rollback by revert" requirement（§3） |

These need separate verification before an actual Production recovery plan can be accepted. **No Production
operation is authorized to test them.**

---

## 7. L4-O recovery-plan dependency

P-13 of #3329 is preserved: a documented, credible recovery plan is required before L4-O can be approved.

- **U-5 = B does not itself satisfy P-13.**
- A preferred recovery strategy is **not** an executable, verified recovery plan.
- The plan must identify a **reachable and verified restoration target**（§2.1）and an **operationally supported
  restoration procedure**.
- The required permissions and effective-state checks must be **confirmed**.
- **Unresolved critical dependencies**（§6, §3）**block** the later L4-O execution approval.
- **Mother Ship retains final authority** over the GO / NO-GO decision.

This addresses the open note in #3329 §3.4 only as far as the U-5 strategy selection goes; the judgement of a
concrete plan at L4-O time stays with Mother Ship.

---

## 8. U-6: Approved extension strategy（decision B）

**U-6 = B: each observation extension duration is individually determined, based on the unmet acceptance criteria
and documented reasons.**

Preserved（#3325 §1.1, §3）:

| # | rule |
| --- | --- |
| O-1 | the initial standard observation duration is 24 hours |
| O-2 | if required acceptance criteria remain unmet, observation is extended |
| O-3 | no automatic transition to enforcement |
| O-4 | enforcement requires a separate explicit Mother Ship L4-E GO |
| O-5 / O-6 | manual recovery and security-risk authorization rules are unchanged |

- **No fixed default extension duration** is introduced.
- **No observation window is scheduled.** No future date, time, deadline or automatic recurrence is set.

---

## 9. Extension decision record（future design）

A future record, issued when an extension is decided. **No such record exists.**

| field | content |
| --- | --- |
| observation evidence record ID | the U-4 evidence record（#3330 §6） |
| target deployment ID and commit SHA | of the observed deployment |
| verified effective mode | as confirmed under M-5 |
| existing observation window | start and end in UTC |
| unmet acceptance criteria | the applicable AC rows |
| cause classification | §10 |
| remaining work | the remediation or verification still required |
| fresh window required? | yes / no, with the rule that requires it（§10） |
| proposed extension duration and UTC window | **populated only at decision time** |
| reason for the selected duration | tied to the unmet criteria（U-6 = B） |
| monitoring owner | the responsible reviewer |
| supporting evidence references | with availability status（#3330 §5.3） |
| Mother Ship authorization | the decision reference |
| decision status | `EXTEND` / `STOP` / `REASSESS` |
| effective-state confirmation | when any operational change occurs（M-5） |

- A missing or incomplete evidence record is **never** marked PASS.
- **No extension is authorized automatically** because the original period has expired.

---

## 10. Extension versus fresh observation

| finding | consequence | source |
| --- | --- | --- |
| insufficient legitimate traffic（AC-8） | may justify an **extension**, provided collection remains credible | #3325 §4, #3330 §2 |
| unclassified would-be CSRF rejections（AC-7） | investigation and documented resolution | #3325 §4 |
| D0（AC-6） | root-cause analysis, a fix, and a **fresh observation window** | #3325 §4, #3328 §2.4 |
| F-3 | root-cause investigation and remediation; the affected observation window is **invalidated** | #3327 §2.3, §6 |
| failed or incomplete telemetry | never treated as successful evidence | #3325 §4, #3330 §2.4 |
| material change in the observed implementation or deployment | evidence **reassessment** | M-3, M-4 |

- **No duration is prescribed for a fresh window.** Whether a fresh window uses the O-1 standard duration is not
  decided here.
- All existing acceptance rules are preserved.

---

## 11. Relationship to U-3 and U-4

- **U-3 = A:** server-side aggregation is the authoritative source for legitimate first-party request counts
  （#3330 §2）.
- **U-4 = A:** GitHub audit documentation is the authoritative evidence and decision record, referring to
  independently verifiable support（#3330 §5）.

An extension decision uses those evidence responsibilities.

- Legitimate traffic counts are **never** invented or inferred from missing or expired data.
- **A link to expired platform logs is not sufficient evidence**（#3330 §5.3）.
- Retention, access control, instrumentation and supporting-evidence durability remain subject to UD-1 to UD-11.

---

## 12. Future acceptance checks（not executed）

| # | check |
| --- | --- |
| RX-1 | a recovery proposal identifies a verified deployment and configuration state（VD-1 to VD-6） |
| RX-2 | no restoration occurs without Mother Ship authorization |
| RX-3 | `enforce` → `observe` requires an O-6 risk acknowledgement |
| RX-4 | the effective restored mode is verified |
| RX-5 | the required AC-5, AC-6 and AC-10 rechecks are recorded |
| RX-6 | U-5 design approval alone cannot satisfy P-13 |
| RX-7 | a missing rollback mechanism blocks L4-O execution approval |
| RX-8 | each observation extension has a documented reason and an individually approved duration |
| RX-9 | D0 and F-3 trigger fresh-observation requirements under their existing contracts |
| RX-10 | missing or expired evidence is not PASS |
| RX-11 | no automatic extension-to-enforcement transition exists |
| RX-12 | no runtime operation is authorized by this document |

No tests are implemented or run as part of this PR.

---

## 13. Remaining unresolved items

| item | status |
| --- | --- |
| UD-1 to UD-11（#3330 §8） | **OPEN** |
| S-6 backend defense in depth | **OPEN** |
| S-8 remainder: browser, POST and Production verification | **OPEN** |
| S-14 Docker / self-hosted behaviour | **OPEN** |
| instrumentation and logging-contract extensions | **OPEN** |
| exact rollback commands（RV-1） | **UNVERIFIED** |
| hosting-platform behaviour and permissions（RV-2 to RV-6） | **UNVERIFIED** |
| recovery timing and test evidence（RV-9, RV-10） | **UNVERIFIED** |
| concrete observation extension schedules | **NONE**; decided per extension |
| verified-deployment restoration vs "rollback by revert"（§3, RV-11） | **OPEN** |
| A-0 / L4-O / L4-E | **NOT APPROVED** |

**A-7 is preserved unchanged**（#3324 §4.7）. The 14-day Class B deadline starts when the future CSRF V-1 runtime
implementation PR merges. **This documentation PR does not start, reset or extend it.** The other deadlines and
conditions stand, and the Class B vulnerability is not fixed.

### 13.1 Future synchronization（not done here）

- #3323 §11, #3325 §6 / §8.2, #3329 §3.4 and #3330 §10 still show "rollback by revert" or U-5 / U-6 as open. A
  later documentation PR may add a pointer to this record there, if Mother Ship wants the historical records
  annotated. That is a proposal only.
- `README.md`, `architecture.md` and `roadmap.md` are unchanged.

---

## 14. STOP

```text
U-5  = B — design approved
U-6  = B — design approved
A-0  = NOT APPROVED
L4-O = NOT APPROVED
L4-E = NOT APPROVED
runtime code                 UNCHANGED
API routes                   UNCHANGED
authentication / cookies     UNCHANGED
environment variables        UNCHANGED
hosting configuration        UNCHANGED
Production                   UNCHANGED
deployment                   NONE
rollback operation           NONE
mode change                  NONE
observation extension        NONE SCHEDULED
logging / telemetry          NO NEW
storage implementation       NONE
PR merge                     NONE
```
