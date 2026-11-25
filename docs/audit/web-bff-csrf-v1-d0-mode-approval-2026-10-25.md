# Web BFF CSRF V-1 — C-1 / U-1h D0 Mode and Variable Name Approval Record（2026-10-25）

## 1. Purpose and approval record

```text
RECORD TYPE                 = subsequent approval record（documentation only）; supplements #3326 and #3327
C-1                         = A — D0: `observe` logs a would-be rejection and continues; `enforce` returns 403
                              APPROVED（design only）
U-1h                        = A — `WEB_CSRF_MODE` is the official server-side mode variable name
                              APPROVED（design only）
DECISION AUTHORITY          = Mother Ship
A-0 RUNTIME IMPLEMENTATION  = NOT APPROVED
L4 PRODUCTION ROLLOUT       = NOT APPROVED
RUNTIME IMPLEMENTATION      = NONE EXISTS（no guard, no observation mode, no mode variable）
ENV / PRODUCTION CHANGES    = NOT AUTHORIZED
FINAL STATUS                = STOP
```

**References**（read on `develop@17a7654`; not edited）:

| record | role here |
| --- | --- |
| `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md`（#3323） | D0–D13（§2.2）, `current` selection（§3.4）, D0 fail-closed（§3.5）, logging（§3.6）, `DELETE /api/users/me`（§4.3）, the rejection response（§5） |
| `docs/audit/web-bff-csrf-v1-approval-record-2026-10-24.md`（#3324） | A-1 to A-8; A-7 deadline and conditions（§4.7） |
| `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md`（#3325） | observation mode semantics（§2.1）, O-1 to O-6, AC-6（§4）, monitoring（§5）, U-2 to U-6（§8.2） |
| `docs/audit/web-bff-csrf-v1-mode-contract-2026-10-24.md`（#3326） | U-1a / U-1b / U-1c（§2, §3, §7）, `observe` behaviour（§4）, F-1 to F-3（§6）, T-1 to T-12（§8）, C-1 and U-1h as open（§9.2） |
| `docs/audit/web-bff-csrf-v1-observe-exceptions-2026-10-25.md`（#3327, merged `17a7654`） | U-1d = A, U-1e = B; C-1 and U-1h listed as OPEN（§7） |

**Earlier unresolved clauses closed by this record:**

| record and clause | text at the time | resolved by |
| --- | --- | --- |
| #3326 §6, paragraph "C-1（consistency note）" | "This record follows both: §3.5 for `enforce`, §2.1 for `observe`. Mother Ship may confirm this reading" | C-1 = A（§2） |
| #3326 §9.2, row C-1 | "reconciliation of two approved records; recorded, not decided" | C-1 = A（§2） |
| #3326 §2, row "variable" | "**`WEB_CSRF_MODE`**（proposed name; see U-1h in §9.2）" | U-1h = A（§3） |
| #3326 §9.2, row U-1h | "whether the variable name `WEB_CSRF_MODE` needs its own approval（A-1 approved only `WEB_PUBLIC_ORIGINS`）" | U-1h = A（§3） |
| #3327 §7, rows C-1 and U-1h | both **OPEN** at the time #3327 merged | C-1 = A, U-1h = A |

**What this record is.**

- It **adds** two design decisions. It does not rewrite #3326, #3327 or any earlier record.
- The earlier text that marks C-1 and U-1h as open or proposed stays as written. It was correct when those records
  merged.
- From this record onward, the status of C-1 and U-1h is the one stated here.
- **C-1 and U-1h are design approvals only.** They authorize no code, configuration change, test run, deployment
  or rollout.

**Decision provenance.**

| item | value |
| --- | --- |
| decision maker | Mother Ship |
| decisions | C-1 = A; U-1h = A |
| how received | the task brief for this record, which states both decisions and that A-0 and L4 remain not approved |
| approval timestamp | **not stated** in the brief, and therefore not recorded here |
| signed artifact | none is stored in the repository. This record is the in-repository statement of the decisions |
| implementation evidence | **none**. No code exists and no test has run |
| interpretation | where this record adds an interpretation, it is labeled "interpretation" |

---

## 2. C-1: D0 behaviour by mode（decision A）

### 2.1 What D0 is

D0 is the decision-table row for which the evaluator **could not establish the configured currently served public
origin**（`current` is `null`）, as defined by the final contract:

- the public-origin configuration is missing, malformed or ambiguous（#3323 §3.3）;
- the platform mode is invalid（#3323 §3.1）;
- the request `Host` is absent, duplicated or malformed, or matches no configured entry（#3323 §3.4, §3.7）.

Reason codes（unchanged, #3323 §2.2）: `config_unavailable` / `host_not_configured`.

**C-1 does not change the D0 decision logic or the D0–D13 table.** It decides only what each mode does with the D0
outcome.

### 2.2 Behaviour by mode

| condition | `observe` | `enforce` |
| --- | --- | --- |
| **D0** public-origin failure | record the would-be rejection; continue existing processing | reject with HTTP 403 |
| **F-1** invalid mode configuration | fail closed with HTTP 403 | fail closed with HTTP 403 |
| **F-3** unexpected evaluator error | fail closed with HTTP 403 | fail closed with HTTP 403 |

- **F-1** has no valid mode, so the two columns name the same outcome; #3326 §6: "'Every mode' includes this case,
  because no valid mode exists".
- **F-3** in `observe` is U-1d = A（#3327 §2.3）; in `enforce` it is #3326 §6.

### 2.3 D0 is distinct from F-1 and F-3

| category | nature | evaluation result |
| --- | --- | --- |
| **D0** | a **valid evaluator outcome**: the table ran and the first matching row is D0 | yes: row D0 with its reason code |
| **F-1** | the mode configuration is invalid; the guard has no valid mode to apply（#3326 §3） | none; reason `mode_config_invalid`, no mode marker |
| **F-3** | an **unexpected internal error** inside the guard that prevents any valid D0–D13 result（#3327 §2.1） | none; reason `evaluator_error`, no decision row |

- **D0 is not an unexpected internal error.** A configuration problem that the contract maps to D0（#3323 §3.3:
  "any failure → D0"）stays D0. It is never recorded as F-3, and F-3 is never recorded as D0（#3327 §2.2）.
- **D0 is not F-1.** `WEB_PUBLIC_ORIGINS` problems lead to D0; `WEB_CSRF_MODE` problems lead to F-1. The two are
  validated and logged separately.

### 2.4 D0 in `observe`

- **Record** D0 with its existing reason code（`config_unavailable` / `host_not_configured`）and the `observe`
  mode marker（#3326 §4.2）.
- **Continue the pre-V-1 request-processing behaviour.** Status, body, `Set-Cookie` and backend calls are what the
  route produces today（#3325 §2.1, #3326 §4.1）.
- **No new CSRF rejection** is introduced solely because of D0.
- **D0 is an unsuccessful observation** for the acceptance criteria: AC-6 requires zero unresolved D0 entries, and
  any D0 needs a recorded root cause and fix followed by a fresh observation window（#3325 §4）.
- **No weakening of route-specific checks.** On `DELETE /api/users/me` the existing `isAllowedOrigin` check keeps
  deciding exactly as today（#3326 §4.3）. A D0 observation is recorded and does not replace or relax that check.
- **`observe` does not protect against CSRF.** The existing exposure（the base contract T1–T11）remains open during
  observation（#3325 §2.1, #3326 §4.1）.

### 2.5 D0 in `enforce`

The existing rejection response（#3323 §5）:

| item | value |
| --- | --- |
| status | **HTTP 403** |
| body | `{"detail":"forbidden"}` |
| headers | `Content-Type: application/json`, `Cache-Control: no-store` |
| `Set-Cookie` | **none** |
| backend request | **none** |
| token refresh | **none** |
| request body | **not consumed** before the rejection |

Every in-scope route is unavailable while D0 persists in `enforce`. This is the deliberate fail-closed posture
of #3323 §3.5.

### 2.6 Interpretation confirmed by C-1 = A

| source | text | applies to |
| --- | --- | --- |
| final contract §3.5（#3323） | "Every in-scope route rejects every request with the §5 response（D0）" | **`enforce`**. The text was written before modes existed and describes enforcement |
| rollout plan §2.1（#3325） | "A request the decision table would reject（D0–D13）is logged with the §5 fields, and it is then processed as it is today" | **`observe`** |

- #3326 §6 recorded this mode-specific reading as C-1 and left it for Mother Ship to confirm.
- **C-1 = A confirms it.** Neither source text is edited; each is read as applying to its own mode.

---

## 3. U-1h: Official mode variable name（decision A）

### 3.1 Approved name and values

| item | value |
| --- | --- |
| official name | **`WEB_CSRF_MODE`** |
| approved values | exactly `observe` or `enforce`（unchanged, #3326 §2） |

### 3.2 Preserved design contract（U-1a / U-1b / U-1c, #3326）

- **Server-side configuration only.**
- **No `NEXT_PUBLIC_*` exposure**; never sent to the browser.
- **No client override**: no header, URL parameter, cookie, body or other request attribute selects the mode.
- **No implicit default**: neither `observe` nor `enforce`.
- **Missing or invalid values fail closed**（F-1, #3326 §3）.
- **A single validated mode** is selected once at request entry and governs the whole request.
- **Manual switching only**, after an explicit, recorded Mother Ship authorization（M-1 to M-6, #3326 §7）.
- **No automatic promotion or rollback**（O-3, O-5, O-6）.

### 3.3 Scope of the approval

U-1h = A approves the **variable name and its design contract only**. It does **not** authorize:

- creating the variable;
- updating `.env` or `.env.example`;
- adding it to Vercel or another hosting platform;
- reading it from runtime code;
- changing deployment configuration;
- activating observation or enforcement.

Each of these requires the applicable later authorizations, including A-0 and the production rollout gates
（L3, the Phase 2 authorization, L4）.

---

## 4. Cross-contract consistency

All earlier decisions stand unchanged:

| decision | source | state |
| --- | --- | --- |
| U-1a = A | #3326 §2 | preserved |
| U-1b = A | #3326 §3 | preserved |
| U-1c = A | #3326 §7 | preserved |
| U-1d = A | #3327 §2 | preserved |
| U-1e = B | #3327 §3 | preserved |
| A-1 to A-8 | #3324 §3 | preserved |
| O-1 to O-6 | #3325 §1.1 | preserved |

Specifically:

- **U-1d:** F-3 in `observe` returns 403 on all six in-scope routes（#3327 §2.5）.
- **U-1e:** non-JSON input on the four A-4 routes is observed without imposing a new `415` in `observe`（#3327 §3.2）.
- **U-1e ordering**（#3327 §3.2, interpretation）: the would-be `415` is recorded only when the evaluation returns an
  allow row. With C-1 = A, a D0 outcome is a reject row, so a D0 request records D0, not a would-be `415`.
- **`DELETE /api/users/me` in `observe`:** the existing `isAllowedOrigin` protection keeps deciding（#3326 §4.3）.
- **A-7:** the conditional Class B risk acceptance and its deadline are unchanged（§6）.

This record introduces **no new default, no bypass mode and no exceptional case**.

---

## 5. Future acceptance tests（requires A-0）

**No test is implemented or run by this record.** These refine #3326 T-1 to T-5, T-11, T-12 for C-1 and U-1h.

| # | test |
| --- | --- |
| DM-1 | D0 in `observe`（for example `WEB_PUBLIC_ORIGINS` unset or a `Host` matching no entry）records D0 with its reason code and the `observe` marker; status, body, `Set-Cookie` and backend calls equal the pre-V-1 behaviour |
| DM-2 | D0 in `enforce` returns 403, `{"detail":"forbidden"}`, `Content-Type: application/json`, `Cache-Control: no-store`; no `Set-Cookie`, no backend request, no token refresh, body not read |
| DM-3 | F-1（invalid `WEB_CSRF_MODE`）is fail closed with or without a valid public-origin configuration, and is logged as `mode_config_invalid`, not as D0 |
| DM-4 | F-3 is fail closed in both modes and is logged as `evaluator_error`, not as D0 |
| DM-5 | headers, query parameters, cookies and bodies naming a mode do not override `WEB_CSRF_MODE` |
| DM-6 | only the exact values `observe` and `enforce` are accepted; unset, empty, other case, whitespace-padded and multi-value inputs are F-1 |
| DM-7 | in `observe`, `DELETE /api/users/me` keeps the existing `isAllowedOrigin` decision, including during D0 |
| DM-8 | each log line contains only the route path, the decision row（if any）, the reason code and the mode marker（if any）; no `Origin`, `Host`, cookie, `Authorization`, token, configuration value or body |
| DM-9 | an observation window containing a D0 entry is reported as not satisfying AC-6 until its root cause and fix are recorded and a fresh window passes |
| DM-10 | no code path changes the mode automatically: no write to the mode, and no time-, count- or error-based branch selecting it |

No runtime tests or code changes are authorized by this documentation task.

---

## 6. Remaining unresolved items

| id | item | status |
| --- | --- | --- |
| **U-2** | production observation authorization gate | **OPEN** |
| **U-3** | legitimate request-count source | **OPEN** |
| **U-4** | evidence storage and format | **OPEN** |
| **U-5** | rollback mechanism | **OPEN** |
| **U-6** | observation extension duration | **OPEN** |
| **S-6** | backend defense in depth | **OPEN** |
| **S-8 remainder** | browser, POST and Production verification | **OPEN** |
| **S-14** | Docker / self-hosted behaviour | **OPEN** |
| instrumentation | the mode marker and report-only instrumentation（#3325 §5.3, #3326 §4.2）; the would-be `415` log record（#3327 §4.3） | **OPEN**: implementation dependencies requiring A-0 and separate design validation |
| **A-0** | runtime implementation authorization | **NOT APPROVED** |
| **L4** | production rollout authorization | **NOT APPROVED** |

This record does not infer or decide any of these.

**A-7 is preserved unchanged**（#3324 §4.7）: the Class B deadline（before general release; before a custom domain
is attached; the Class B PR merged no later than 14 days after the V-1 implementation PR merges）and the conditions
of the temporary risk acceptance. **The 14-day clock has not started.** It begins at the merge of the V-1 runtime
implementation PR, not at this documentation PR. The Class B vulnerability is not fixed.

### 6.1 Future synchronization（not done here）

- #3326 §2, §6 and §9.2 and #3327 §7 still show C-1 and U-1h as open or proposed. A later documentation PR may add a
  pointer to this record there, if Mother Ship wants the historical records annotated. That is a proposal only.
- `README.md`, `architecture.md`, `roadmap.md`, `.env` and `.env.example` are unchanged.

---

## 7. STOP

```text
A-0 = NOT APPROVED
L4  = NOT APPROVED
runtime implementation       NONE
API routes                   UNCHANGED
authentication / cookies     UNCHANGED
environment variables        UNCHANGED（WEB_CSRF_MODE not created anywhere）
Production                   UNCHANGED
deployment                   NONE
rollout                      NONE
automatic enforcement        NONE
automatic rollback / bypass  NONE
G1–G5                        NOT IMPLEMENTED
PR merge                     NONE
```
