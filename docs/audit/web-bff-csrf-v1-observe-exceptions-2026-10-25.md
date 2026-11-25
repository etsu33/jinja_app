# Web BFF CSRF V-1 — U-1d / U-1e Observation-Mode Exceptions Approval Record（2026-10-25）

## 1. Approval status and provenance

```text
RECORD TYPE                 = subsequent approval record（documentation only）; supplements #3326
U-1d                        = A — unexpected internal evaluator error in `observe` fails closed（403）   APPROVED（design）
U-1e                        = B — in `observe`, non-JSON input on the four A-4 routes is observed and recorded;
                              existing request processing continues                                   APPROVED（design）
A-0 RUNTIME IMPLEMENTATION  = NOT APPROVED
L4 PRODUCTION ROLLOUT       = NOT APPROVED
RUNTIME IMPLEMENTATION      = NONE EXISTS（no guard, no observation mode, no instrumentation）
ENV / PRODUCTION CHANGES    = NOT AUTHORIZED
FINAL STATUS                = STOP
```

**References**（read on `develop@60fbf67`; not edited）:

| record | role here |
| --- | --- |
| `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md`（#3323） | D0–D13（§2.2）, D0 fail-closed（§3.5）, logging（§3.6）, the rejection response（§5）, JSON-only（§6）, `DELETE /api/users/me`（§4.3）, gates（§11） |
| `docs/audit/web-bff-csrf-v1-approval-record-2026-10-24.md`（#3324） | A-4（§4.4）, A-5（§4.5）, A-7 deadline and conditions（§4.7）, A-8（§4.8） |
| `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md`（#3325） | observation mode semantics（§2.1）, AC-1 to AC-13（§4）, monitoring and privacy（§5）, U-2 to U-6（§8.2） |
| `docs/audit/web-bff-csrf-v1-mode-contract-2026-10-24.md`（#3326, merged `60fbf67`） | U-1a / U-1b / U-1c, F-1 to F-3（§6）, `observe` logging（§4.2）, route notes（§4.3）, T-1 to T-12（§8）, open questions（§9.2） |

**Clauses of #3326 resolved by this record:**

| #3326 clause | text being resolved | resolved by |
| --- | --- | --- |
| §6 table, row F-3, column `observe` | "U-1d — Mother Ship decision required" | U-1d = A（§2） |
| §6, paragraph "F-3 in `observe`" | "Until U-1d is decided, the implementation must not ship `observe` mode" | U-1d = A（§2）. The decision is made; shipping still needs A-0 and the gates |
| §4.3 table, row "login, register, chat, compass weekly（JSON-only, A-4）" | "whether the A-4 `415` rule applies in `observe` or is only recorded is **not derivable**" | U-1e = B（§3） |
| §8, T-7 | "`observe` → per U-1d once decided" | §2.3, §5 |
| §8, T-8 | "its `observe` behaviour per U-1e once decided" | §3.3, §5 |
| §9.2, rows U-1d and U-1e | open questions | closed by this record（design only） |

**What this record is.**

- It **adds** two design decisions to #3326. It does not rewrite #3326 or any earlier record.
- The text of #3326 that marks U-1d and U-1e as open stays as written. It was correct when #3326 merged.
- From this record onward, the status of U-1d and U-1e is the one stated here.
- **U-1d and U-1e are design approvals only.** They authorize no code, configuration change, test run, deployment
  or rollout.

**Decision provenance.**

| item | value |
| --- | --- |
| decision maker | Mother Ship |
| decisions | U-1d = A; U-1e = B |
| how received | the task brief for this record, which states both decisions and that they do not authorize implementation |
| approval timestamp | **not stated** in the brief, and therefore not recorded here |
| signed artifact | none is stored in the repository. This record is the in-repository statement of the decisions |
| implementation evidence | **none**. No code exists and no test has run |
| interpretation | where this record adds an interpretation, it is labeled "interpretation" |

---

## 2. U-1d: Unexpected internal evaluator errors（decision A）

### 2.1 Definition

An **unexpected internal evaluator error**（F-3）is a failure inside the guard that **prevents a valid D0–D13
evaluation** from being produced. Examples: an exception thrown inside the guard, or an internal state the
decision table cannot reach（for example no row matched, or an unknown internal result）.

### 2.2 Distinction from other categories

| category | what it is | how it is handled | F-3? |
| --- | --- | --- | --- |
| **F-1** invalid mode configuration（#3326 §3） | `WEB_CSRF_MODE` is unset, empty, unknown or malformed; no valid mode exists | fail closed in every mode; reason code `mode_config_invalid`; no mode marker | **no** |
| **F-2** public-origin resolution failure（D0; #3323 §3.4–§3.5） | `current` is `null`: configuration missing, malformed or ambiguous, or the host is not configured | a **valid** evaluation result: row D0, reason `config_unavailable` / `host_not_configured`. `observe`: would-be rejection, the request continues（#3326 §6）. `enforce`: rejected | **no** |
| **normal reject outcome**（D1–D3, D6–D8, D10, D12, D13） | the decision table ran and returned a reject row | a **valid** evaluation result. `observe`: would-be rejection, recorded, the request continues. `enforce`: rejected | **no** |
| **F-3** unexpected internal evaluator error | the guard could not produce any valid D0–D13 result | §2.3 | **yes** |

- **F-3 is never recorded as D0 or as any D-row.** It has no decision row.
- **D0 is not an evaluator error.** D0 is a defined row of the table, and its `observe` handling stays as #3326 §6
  F-2 states（see C-1, §7）. U-1d does not change it.
- A configuration validation failure that the contract already maps to D0（#3323 §3.3: "any failure → D0"）is
  D0, not F-3.

### 2.3 F-3 in `observe`（U-1d = A）

| requirement | value |
| --- | --- |
| status | **HTTP 403** |
| body | `{"detail":"forbidden"}` |
| headers | `Content-Type: application/json`, `Cache-Control: no-store` |
| `Set-Cookie` | **never** |
| backend request | **never** |
| token refresh | **never** |
| request body | **not consumed** before the rejection |
| log | reason code **`evaluator_error`**（§4） |
| allowed? | **never** recorded or counted as allowed |
| acceptance | the affected observation window is **invalid for acceptance purposes**（#3326 §6: "it fails the observation window for that route"; §6 of this record） |

- This is the #3323 §5 rejection response, the same response used for F-1.
- **No fail-open under an internal error.** In `observe`, F-3 is the one evaluator outcome that blocks the
  request. Every valid D-row outcome（D0 included）is still only recorded（#3326 §4.1）.

### 2.4 F-3 in `enforce`

Unchanged from #3326 §6: the request is not processed; 403 with the #3323 §5 response; logged as
`evaluator_error`. No fail-open.

### 2.5 Consequences（interpretation; recorded, not decided further）

- U-1d names no route restriction, so F-3 fail-closed applies to **every in-scope route** in `observe`: login,
  register, logout, concierge chat, compass weekly and `DELETE /api/users/me`.
- On `DELETE /api/users/me` in `observe`, the existing `isAllowedOrigin` check keeps deciding for valid
  evaluations（#3326 §4.3）. On F-3 the request is rejected with 403 regardless of that check. This makes the route
  stricter, never weaker.
- On logout, an F-3 403 is a non-2xx response, so A-5 applies: the client keeps the authenticated state and shows
  an error（#3324 §4.5）. A-5 itself is not yet implemented（A-0）.
- **Blind spot.** In `observe`, F-3 makes the affected requests fail for real users, unlike every other
  observation outcome. A defect in the guard can therefore cause user-visible outages during Phase 2. The
  pre-Phase-2 gates（AC-1 to AC-5, AC-10 to AC-12）must exercise the guard enough to make F-3 in production
  unlikely; this record defines no additional gate.

---

## 3. U-1e: Non-JSON requests in observation mode（decision B）

### 3.1 Scope

The four A-4 routes（#3324 §4.4, #3323 §6）:

| route | handler |
| --- | --- |
| login | `POST /api/auth/login` |
| register | `POST /api/auth/register` |
| concierge chat | `POST /api/concierge/chat` |
| compass weekly | `POST /api/compass/weekly` |

**Excluded:**

- **logout** — it has no body; only the origin check applies（#3324 §4.4）. It is not subject to JSON-only
  validation in either mode.
- **`DELETE /api/users/me`** — not an A-4 route. Its existing protection is not weakened: in `observe` the existing
  `isAllowedOrigin` check keeps deciding（#3326 §4.3）; in `enforce` the new evaluator replaces it as #3323 §4.3
  specifies. U-1e does not touch it.

### 3.2 `observe`（U-1e = B）

- **Evaluate CSRF rules** with the existing shared evaluator（public-origin resolution and D0–D13; #3326 §2）.
  There is no separate rule set.
- **A non-`application/json` request is a would-be `415` condition**（the A-4 rule）.
- **Record** the observation（§4）. **Do not** issue a new `415` response solely because of A-4.
- **Continue the pre-V-1 request-processing behaviour.** Existing responses and side effects are preserved:
  status, body, `Set-Cookie` and backend calls are what the route produces today.
- **No media-type promise.** U-1e does not claim that a pre-existing route accepts every media type. Whatever a
  route does today with a given `Content-Type`（accepting it, failing to parse it, or returning its own error）
  stays exactly as it is. For example, the login route today parses `x-www-form-urlencoded` and
  `multipart/form-data`（#3323 §6）; other routes may reject such bodies through their existing logic.
- **No weakening.** No existing route-level validation is removed, relaxed or bypassed.
- **Ordering**（interpretation, derived from "would-be" = what `enforce` would do）: in `enforce`, A-4 runs only
  after the origin check passes（#3323 §6）. So in `observe`, the would-be `415` is recorded only when the
  evaluation returns an allow row（D4, D5, D9, D11）. When the evaluation returns a reject row, the would-be
  outcome is that CSRF row, as `enforce` would answer 403 first. On F-3, §2.3 applies and the request is rejected
  before any `Content-Type` check.

### 3.3 `enforce`

- **A-4 is preserved**（#3324 §4.4, #3323 §6）.
- After CSRF validation passes, a non-`application/json` request on the four routes receives **`415`**
  （`Content-Type` parameters allowed, per #3323 §6）.
- For this rejection: **no backend call** and **no cookie mutation**.
- CSRF rejections（403）still come first（#3323 §5）.

---

## 4. Recording requirements and privacy

### 4.1 Minimal observation signal

The signal must let a reviewer tell three outcomes apart without any request data:

| outcome | route path | decision row | reason code | mode marker |
| --- | --- | --- | --- | --- |
| normal CSRF would-be rejection（`observe`） | yes | the D-row（D0–D3, D6–D8, D10, D12, D13） | the row's reason code（#3323 §2.2） | `observe` |
| internal evaluator error（F-3） | yes | **none**（F-3 has no row） | **`evaluator_error`** | `observe` or `enforce` |
| would-be JSON-only `415`（`observe`） | yes | none（not a CSRF row） | a **new** JSON-only reason code（§4.3） | `observe` |

- The fields are the #3323 §3.6 fields（route path, decision row, reason code）plus the #3326 §4.2 mode marker.
- The mode marker is the fixed classification value defined in #3326 §4.2, never the raw configuration value.
- The `Content-Type` value itself is **not** logged; only the fact that the A-4 condition was met.

### 4.2 Never logged

- the raw `Origin`;
- the raw `Host`;
- `Cookie`;
- `Authorization`;
- access or refresh tokens;
- environment-variable values（including `WEB_CSRF_MODE` and `WEB_PUBLIC_ORIGINS`）;
- request bodies.

Evidence records copy counts and categories only（#3325 §5.2）.

### 4.3 Dependencies beyond the approved logging contract

| item | status |
| --- | --- |
| `evaluator_error` | already specified for F-3 in #3326 §6（design）. A log line without a decision row is a shape #3326 already uses for `mode_config_invalid`（§3） |
| mode marker | designed in #3326 §4.2; its instrumentation does not exist（#3325 §5.3） |
| **would-be `415` record** | **new**. #3323 §3.6 logs CSRF rejections only, and no reason code exists for the A-4 condition. Its name and log line are an **implementation dependency requiring A-0 and separate design validation**. This record does not name or approve one |
| production logging permissions | **not broadened**. Nothing here authorizes logging beyond #3323 §3.6 and #3326 §4.2 |

---

## 5. Acceptance criteria（future tests; requires A-0）

**No test is implemented or run by this record.** These refine #3326 T-7 and T-8.

| # | test |
| --- | --- |
| OX-1 | an internal evaluator failure（for example an injected exception inside the guard）in `observe` returns 403 with `{"detail":"forbidden"}`, `Content-Type: application/json` and `Cache-Control: no-store` |
| OX-2 | after that failure: no backend request, no `Set-Cookie`, no token refresh, and the request body is not read |
| OX-3 | the failure produces one log line with reason `evaluator_error`, no decision row, and no `Origin`, `Host`, cookie, token, configuration value or body |
| OX-4 | F-3 is not counted as an allowed request or as a successful observation, and an observation window containing it is reported as not valid for acceptance |
| OX-5 | in `observe`, non-JSON input on login, register, chat and compass weekly does not produce the new A-4 `415` |
| OX-6 | in `observe`, for those routes, status, body, `Set-Cookie` and backend calls equal the pre-V-1 behaviour for JSON and non-JSON input; the would-be `415` is recorded without the `Content-Type` value |
| OX-7 | in `enforce`, after CSRF checks pass, non-`application/json` input on the four routes returns `415` with no backend call and no cookie change; CSRF-rejected input returns 403, not `415` |
| OX-8 | no regression on logout（no JSON-only check; A-5 on a non-2xx）or on `DELETE /api/users/me`（`observe`: the existing `isAllowedOrigin` decision; `enforce`: #3323 §4.3） |
| OX-9 | the future implementation PR includes browser E2E（#3323 §8.6; Chromium, WebKit and Firefox）and the regression tests above |

---

## 6. ENFORCE transition requirements

The observation period **cannot be considered successful** if any of the following holds:

| # | condition | related criteria |
| --- | --- | --- |
| E-1 | an `evaluator_error` occurrence remains without a recorded root cause and fix, followed by a fresh observation window | AC-6（by analogy）, AC-7 |
| E-2 | the request formats（`Content-Type` categories）that reach the four A-4 routes have not been inspected | AC-7, AC-8 |
| E-3 | a legitimate client would unexpectedly fail after JSON-only enforcement（a would-be `415` from a first-party caller without an explanation and decision） | AC-7, AC-10 |
| E-4 | any required acceptance evidence is missing | AC-1 to AC-13（#3325 §4） |

- **No traffic thresholds** are set by this record.
- **The 24-hour observation period does not authorize an automatic transition**（O-3）. If a criterion is not
  satisfied, observation is extended（O-2）.
- **A separate Mother Ship GO under L4 remains mandatory**（O-4, AC-13）.

---

## 7. Remaining unresolved decisions

| id | decision | status |
| --- | --- | --- |
| **C-1** | confirm the interpretation of D0 across `observe`（#3325 §2.1）and `enforce`（#3323 §3.5）; #3326 §6 | **OPEN**. U-1d does not decide it（§2.2） |
| **U-1h** | approve or reconsider the proposed name `WEB_CSRF_MODE` | **OPEN** |
| **U-2 to U-6** | remaining rollout operational details（#3325 §8.2） | **OPEN** |
| **S-6** | backend defense in depth | **OPEN** |
| **S-8 remainder** | POST, browser（WebKit, Firefox）and Production verification | **OPEN** |
| **S-14** | Docker / self-hosted behaviour | **OPEN** |
| **A-0** | runtime implementation authorization | **NOT APPROVED** |
| **L4** | production rollout authorization | **NOT APPROVED** |
| new（§4.3） | the would-be `415` log record: name and line format | implementation dependency; needs A-0 and separate design validation |

**A-7 is preserved unchanged**（#3324 §4.7）:

- the Class B deadline: before general release; before a custom domain is attached; the Class B PR merged no
  later than 14 days after the V-1 implementation PR merges;
- the conditional risk acceptance and its conditions: no new same-site sibling origin; the deferred inventory
  does not expand; any violation → immediate reassessment;
- the 14-day clock starts at the V-1 implementation PR merge. **This record neither resets nor extends it.** It
  has not started. The Class B vulnerability is not fixed.

### 7.1 Future synchronization（not done here）

- #3326 §6, §8 and §9.2 still show U-1d and U-1e as open. A later documentation PR may add a pointer to this
  record there, if Mother Ship wants the historical records annotated. That is a proposal only.
- `README.md`, `architecture.md` and `roadmap.md` are unchanged.

---

## 8. STOP

```text
runtime code                 UNCHANGED（no implementation）
API routes                   UNCHANGED
cookies / authentication     UNCHANGED
environment variables        UNCHANGED（none created）
WEB_CSRF_MODE                UNCHANGED（does not exist）
Production                   UNCHANGED
deployment                   NONE
rollout                      NONE
automatic enforcement        NONE
automatic rollback           NONE
G1–G5                        NOT IMPLEMENTED
PR merge                     NONE
A-0 = NOT APPROVED
L4  = NOT APPROVED
```
