# Web BFF CSRF V-1 — U-3 / U-4 Observation Evidence Design Approval Record（2026-10-25）

## 1. Approval status and provenance

```text
RECORD TYPE                 = subsequent approval record（documentation only）; supplements #3325 §4, §5, §8.2
U-3                         = A — dedicated server-side aggregation is the authoritative source of legitimate
                              first-party request counts（AC-8）                    APPROVED（design only）
U-4                         = A — GitHub audit documentation is the authoritative record of observation and
                              incident evidence, referencing independently verifiable supporting evidence
                                                                                    APPROVED（design only）
DECISION AUTHORITY          = Mother Ship
U-5                         = OPEN
U-6                         = OPEN
A-0 RUNTIME IMPLEMENTATION  = NOT APPROVED
L4-O PRODUCTION OBSERVATION = NOT APPROVED
L4-E PRODUCTION ENFORCEMENT = NOT APPROVED
RUNTIME INSTRUMENTATION     = NOT IMPLEMENTED
PRODUCTION OBSERVATION      = NOT STARTED
PRODUCTION ENFORCEMENT      = NOT STARTED
FINAL STATUS                = STOP
```

**References**（read on `develop@8714854`; not edited）:

| record | role here |
| --- | --- |
| `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md`（#3323） | D0–D13（§2.2）, logging fields and restrictions（§3.6）, `DELETE /api/users/me`（§4.3）, gates L0–L4（§11） |
| `docs/audit/web-bff-csrf-v1-approval-record-2026-10-24.md`（#3324） | A-1 to A-8; A-7（§4.7）; A-8（§4.8） |
| `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md`（#3325） | AC-1 to AC-13（§4）, monitoring and privacy（§5）, recovery（§6）, U-3 to U-6（§8.2） |
| `docs/audit/web-bff-csrf-v1-mode-contract-2026-10-24.md`（#3326） | validated server-side mode and report-only semantics（§2, §4）, mode marker（§4.2）, M-1 to M-6（§7） |
| `docs/audit/web-bff-csrf-v1-observe-exceptions-2026-10-25.md`（#3327） | U-1d = A, U-1e = B, the would-be `415` record dependency（§4.3） |
| `docs/audit/web-bff-csrf-v1-d0-mode-approval-2026-10-25.md`（#3328） | C-1 = A, U-1h = A |
| `docs/audit/web-bff-csrf-v1-production-observation-gate-2026-10-25.md`（#3329, merged `8714854`） | L4-O and L4-E as independent execution gates; U-4 noted as affecting L4-O records（§3.4） |

**Earlier unresolved clauses closed by this record（design level only）:**

| record and clause | text at the time | resolved by |
| --- | --- | --- |
| #3325 §8.2, row U-3 | "the source for counting legitimate first-party requests per route（AC-8）" | U-3 = A（§2） |
| #3325 §8.2, row U-4 | "where the observation and incident evidence records are stored, and their format" | U-4 = A（§5, §6） |
| #3325 §4, row AC-8 | "The count source is an open detail（U-3）" | U-3 = A（§2） |
| #3329 §3.4 and §8, rows U-3 / U-4 | U-4 affects where the L4-O record is stored; U-3 and U-4 **OPEN** | U-3 = A, U-4 = A |

**What this record is.**

- It **supplements** the historical records. It does not edit, replace or reinterpret their decisions.
- The earlier text that marks U-3 and U-4 as open stays as written. It was correct when those records merged.
- **U-3 and U-4 are design approvals only.** They authorize no runtime implementation, instrumentation, logging
  change, storage creation, configuration change, deployment or Production observation.

**Decision provenance.**

| item | value |
| --- | --- |
| decision maker | Mother Ship |
| decisions | U-3 = A; U-4 = A |
| how received | the task brief for this record, which states both decisions and that A-0, L4-O and L4-E remain not approved |
| approval timestamp | **not stated** in the brief, and therefore not recorded here |
| signed artifact | none is stored in the repository. This record is the in-repository statement of the decisions |
| traffic numbers / implementation evidence / test results | **none**. Nothing is implemented, collected or run |
| interpretation | where this record adds an interpretation, it is labeled "interpretation" |

---

## 2. U-3: Authoritative legitimate-traffic count source（decision A）

### 2.1 Approved design

A **dedicated server-side aggregation mechanism** is the authoritative source of legitimate first-party request
counts for **AC-8**.

### 2.2 AC-8 route scope（unchanged）

AC-8 requires observed legitimate first-party requests for **each of the five routes**（#3325 §4）:

| # | route |
| --- | --- |
| 1 | `POST /api/auth/login` |
| 2 | `POST /api/auth/register` |
| 3 | `POST /api/auth/logout` |
| 4 | `POST /api/concierge/chat` |
| 5 | `POST /api/compass/weekly` |

- **AC-8 is not redefined to require a sixth route.**
- **`DELETE /api/users/me`** keeps its separately specified protection and verification requirements: AC-11
  （#3325 §4）, #3323 §4.3, and the `observe` behaviour in #3326 §4.3. U-3 does not change them.

### 2.3 Requirements on the future aggregation

| # | requirement |
| --- | --- |
| AG-1 | one **consistent counting contract** across the five routes |
| AG-2 | the **CSRF evaluator result**（the D-row category, or F-3）is kept distinct from the **route's actual processing result** |
| AG-3 | legitimate first-party observations are distinguished from **known QA or owner-controlled test traffic**, where verifiable evidence supports the distinction |
| AG-4 | **browser-provided assertions alone**（request headers, client-declared values）are **not** sufficient proof of legitimate traffic |
| AG-5 | the **effective server-side mode** is used; client-supplied mode values are never read（#3326 §2） |
| AG-6 | the reviewed observation window is **correlated with the target deployment and commit** |
| AG-7 | **missing aggregation coverage and failed collection** are detected or exposed, never silently absent |
| AG-8 | an **auditable per-route summary** can be produced |
| AG-9 | **duplicates and retries** do not silently corrupt the stated counting semantics |
| AG-10 | AC-8's existing **five-route coverage requirement** is preserved |

### 2.4 What "legitimate first-party" means

- It is an **evidence-based operational classification**, not proof of a unique human user.
- When verification is insufficient, the observation is classified as **unknown** or **unverified**, never as
  legitimate by assumption.
- **No numerical acceptance threshold** is set by this record.
- The rollout plan condition stands: **low, zero or unverified coverage is not automatically a PASS**（#3325 §4,
  AC-8: "Low or zero volume is not a PASS"）.

---

## 3. Future aggregation boundaries

### 3.1 Conceptual information for review

The categories a reviewer needs. This is **not** an implementation schema.

| category | purpose |
| --- | --- |
| route identifier | which of the five AC-8 routes |
| observation window | the UTC period the count covers |
| verified mode classification | the effective mode, as the validated internal classification（#3326 §4.2） |
| aggregated request count | the per-route count under the counting contract（AG-1） |
| evaluator outcome category | allow / would-be rejection / F-3 |
| processing-result category | the route's actual outcome category |
| QA / test traffic classification | where supported by verifiable evidence（AG-3） |
| aggregation completeness / verification status | complete, incomplete, failed or unverified（AG-7） |

These are **design categories**. They are **not** permission to add Production log fields or to collect any
sensitive data.

### 3.2 Relationship to the approved logging contract

- **The approved CSRF rejection logging contract is unchanged**: one line per rejection with the route path, the
  decision row and the reason code（#3323 §3.6）, plus the mode marker designed in #3326 §4.2.
- #3323 §3.6 states "Allowed requests are not logged by this helper". **Counting allowed requests extends that
  contract.** Any such telemetry requires:
  1. separate design and privacy validation;
  2. explicit **A-0** runtime authorization;
  3. the appropriate later Production authorization（L4-O for Phase 2）.
- Interpretation（recorded only）: until that telemetry is designed, validated and authorized, U-3 = A identifies the
  authoritative source but **no source exists**. AC-8 cannot be satisfied before then.

### 3.3 Not chosen here

Database tables, SQL schemas, event names, logging reason codes, analytics providers, sampling rates, storage
engines, collection middleware and identifier strategies. These are **unverified implementation details**.

---

## 4. Existing CSRF rules and observation behaviour（preserved）

- **D0–D13** decision table（#3323 §2.2）, unchanged.
- **C-1 = A**: D0 in `observe` is recorded and existing processing continues; D0 in `enforce` returns 403（#3328 §2）.
- **U-1d = A**: unexpected evaluator errors fail closed with 403 in both modes（#3327 §2）.
- **U-1e = B**: non-JSON input on the four A-4 routes is observed without introducing a new `415` in `observe`
  （#3327 §3）.
- **U-1e ordering**（#3327 §3.2, interpretation）: a would-be `415` is recorded only after an allow outcome.
- **U-1h = A**: `WEB_CSRF_MODE` is the approved variable name（#3328 §3）.
- **`DELETE /api/users/me`**: the existing protections stand（#3323 §4.3, #3326 §4.3）.
- **No automatic mode promotion**（O-3, #3326 §2）and **no automatic security bypass**（O-5, O-6）.

This record changes no request handling and no logging behaviour.

---

## 5. U-4: Evidence system of record（decision A）

### 5.1 Approved design

**GitHub audit documentation** is the authoritative, human-reviewable record of observation evidence, incidents,
acceptance assessments and Mother Ship decisions. An audit record may **reference independently verifiable
supporting evidence**, for example future CI results, deployment identifiers, approved aggregated statistics and
QA evidence.

### 5.2 Separation of responsibilities

| layer | responsibility |
| --- | --- |
| server-side aggregation（U-3） | supplies the count evidence for AC-8 |
| supporting evidence | provides independently verifiable results where available（CI runs, deployment identifiers, QA results） |
| GitHub audit documents（U-4） | record reviewed summaries, evidence references, decisions, unresolved findings and approval history |

### 5.3 Limits

- **GitHub documentation does not replace the underlying evidence.** It records what was reviewed and decided.
- **A hyperlink alone is insufficient** when its target is unavailable, inaccessible or no longer retained.
- **Completeness, durability and accessibility** of the evidence are checked before an acceptance criterion is
  declared satisfied.
- **GitHub does not store Production request logs** or all underlying evidence. This record does not claim it does.
- Durability is a real constraint: the platform log retention was observed as 1 hour on the current plan（#3325 §8.2,
  citing #3320 §5）. Evidence that depends on short-lived platform logs must be reviewed within that period or
  preserved by a validated means（§8）.
- **No new storage system** is created or authorized.

---

## 6. Evidence record structure（conceptual future format）

A conceptual Markdown structure for a future observation evidence record. **No such record exists**, no template
file is created, and no measurement is filled in.

| section | content |
| --- | --- |
| evidence record identifier | a stable identifier for the record |
| target commit SHA | the full repository commit SHA |
| target deployment identifier | the deployment ID |
| environment and verified effective mode | for example Production / `observe`, as confirmed under M-5（#3326 §7） |
| observation window | start and end in UTC |
| extension history | each extension with its reason（O-2; the length is U-6） |
| AC-8 counts | aggregate legitimate-request counts for each of the five AC-8 routes, with completeness status |
| would-be CSRF rejection classifications | per AC-7: attack / non-browser / unexpected client, or legitimate first-party |
| D0 and F-3 findings | AC-6 D0 entries; `evaluator_error` occurrences（#3327 §6）; root cause and fix for each |
| would-be `415` compatibility findings | request-format categories reviewed for the four A-4 routes（#3327 §6） |
| AC-6 to AC-10 findings | the assessment of each criterion |
| L0–L3 references | AC-1 to AC-5 test and configuration-verification references |
| AC-11 and AC-12 references | `DELETE /api/users/me` contract tests; logout failure tests |
| acceptance status | per applicable criterion: PASS / not satisfied, with the reason |
| unresolved incidents | open incidents and root-cause findings |
| supporting evidence references | each reference with its availability status at review time |
| monitoring / review owner | the responsible reviewer |
| Mother Ship authorization references | the decisions relied on |
| L4-O / L4-E decision status | GO / NO-GO / not requested, with references（#3329 §4） |

No raw confidential material is included（§7）.

---

## 7. Privacy and evidence restrictions

Never stored in application observation logs or in GitHub audit evidence:

- the raw `Origin`;
- the raw `Host`;
- cookies;
- `Authorization` headers;
- access or refresh tokens;
- environment-variable values;
- request bodies;
- secrets or credentials.

**Not introduced** into this evidence design: user identifiers, IP addresses, full user-agent strings or
user-level histories. Evidence uses **aggregate values and classifications only**.

**Appearing in §3 or §6 is not approval for Production logging.** No field is approved for Production logging by
this record.

---

## 8. Unverified details and future dependencies

Not approved by U-3 = A or U-4 = A, and **unresolved**:

| # | detail |
| --- | --- |
| UD-1 | exact aggregation implementation |
| UD-2 | instrumentation design and the logging-contract extension（including counting allowed requests） |
| UD-3 | logging reason-code names（including the would-be `415` record, #3327 §4.3） |
| UD-4 | evidence retention period |
| UD-5 | storage permissions and access controls |
| UD-6 | supporting evidence durability |
| UD-7 | evidence export and integrity-verification mechanism |
| UD-8 | data collection completeness verification |
| UD-9 | handling of duplicated or retried requests |
| UD-10 | separation of QA / test traffic from production user traffic |
| UD-11 | selection of a storage provider or database, where needed |

- If a detail is essential for credible AC-8 verification or safe Production operation, it must be **resolved
  and validated before the relevant later gate**.
- None of them is marked resolved here.

---

## 9. Relationship with L4-O and L4-E

**L4-O**（#3329 §3）:

- requires the existing pre-observation prerequisites P-1 to P-15;
- is **NOT APPROVED**;
- may not rely on evidence that only Production observation produces（AC-6 to AC-9, AC-10 in Production）as a
  precondition to starting observation（#3329 §3.2）;
- must have a **documented monitoring and evidence-collection plan** before an actual GO. Interpretation: under
  U-3 / U-4 that plan names the aggregation that will produce AC-8 counts and the audit record that will hold the
  evidence; both need the dependencies in §8 that apply to them.

**L4-E**（#3329 §6）:

- is **NOT APPROVED**;
- requires the completed observation evidence and all AC-1 to AC-12;
- requires a separate explicit Mother Ship GO under AC-13;
- does **not** follow automatically from a completed 24-hour observation period（O-3）.

**U-3 and U-4 design approval satisfies neither execution gate.**

**A-8 unchanged:** G3 stays blocked until V-1 is actually enforced in Production（#3324 §4.8）.

---

## 10. Remaining open items

| id | item | status |
| --- | --- | --- |
| **U-5** | manual rollback mechanism and exact commands | **OPEN** |
| **U-6** | observation extension length and operational conditions | **OPEN** |
| **S-6** | backend defense in depth | **OPEN** |
| **S-8 remainder** | browser, POST and Production verification | **OPEN** |
| **S-14** | Docker / self-hosted behaviour | **OPEN** |
| instrumentation and evidence implementation | UD-1 to UD-11（§8）; the mode marker and report-only instrumentation（#3325 §5.3, #3326 §4.2） | **OPEN** |
| **A-0** | runtime implementation authorization | **NOT APPROVED** |
| **L4-O / L4-E** | execution of either gate | **NOT APPROVED** |

**A-7 is preserved unchanged**（#3324 §4.7）. The 14-day Class B deadline starts when the CSRF V-1 runtime
implementation PR merges. **It has not started, and this documentation PR neither starts nor resets it.** The
other deadlines and conditions stand, and the Class B vulnerability is not fixed.

### 10.1 Future synchronization（not done here）

- #3325 §4 / §8.2 and #3329 §3.4 / §8 still show U-3 and U-4 as open. A later documentation PR may add a pointer
  to this record there, if Mother Ship wants the historical records annotated. That is a proposal only.
- `README.md`, `architecture.md` and `roadmap.md` are unchanged.

---

## 11. Future acceptance criteria（review checks; not executed）

| # | check |
| --- | --- |
| EV-1 | all five AC-8 routes have verifiable server-side counts for the observation window |
| EV-2 | missing, duplicated or incomplete aggregation is detectable and does not silently pass |
| EV-3 | known QA / test traffic cannot silently substitute for legitimate Production traffic |
| EV-4 | the recorded effective mode corresponds to the verified Production deployment |
| EV-5 | CSRF rejection logging stays within the approved fields（#3323 §3.6, #3326 §4.2） |
| EV-6 | evidence records include the relevant AC assessments and supporting references |
| EV-7 | missing or expired supporting evidence does not become PASS |
| EV-8 | sensitive request and authentication values are excluded |
| EV-9 | no acceptance criterion is marked PASS solely because an audit document exists |
| EV-10 | neither L4-O nor L4-E is implicitly authorized |

No tests are implemented or run by this PR.

---

## 12. STOP

```text
U-3  = A — design approved
U-4  = A — design approved
U-5 / U-6                    OPEN
A-0  = NOT APPROVED
L4-O = NOT APPROVED
L4-E = NOT APPROVED
runtime code                 UNCHANGED
API routes                   UNCHANGED
authentication / cookies     UNCHANGED
environment variables        UNCHANGED
hosting configuration        UNCHANGED
database migrations          NONE
telemetry / logging          UNCHANGED
storage implementation       NONE
Production                   UNCHANGED
deployment                   NONE
observation                  NOT STARTED
enforcement                  NOT STARTED
PR merge                     NONE
```
