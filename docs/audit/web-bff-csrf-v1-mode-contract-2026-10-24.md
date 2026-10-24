# Web BFF CSRF V-1 — U-1 Mode Switching Contract（2026-10-24）

## 1. Purpose and approval status

```text
RECORD TYPE                 = design contract（documentation only）; supplements #3323, #3324, #3325
U-1a                        = A — explicit server-side mode configuration         APPROVED（design）
U-1b                        = A — fail closed on missing or invalid mode config   APPROVED（design）
U-1c                        = A — manual switching only, after explicit Mother Ship authorization  APPROVED（design）
A-0 RUNTIME IMPLEMENTATION  = NOT APPROVED
L4 PRODUCTION ROLLOUT       = NOT APPROVED
RUNTIME IMPLEMENTATION      = NONE EXISTS
MODE SWITCHING MECHANISM    = NONE EXISTS（no observation mode, no enforcement mode, no guard）
ENV / PRODUCTION CHANGES    = NOT AUTHORIZED
FINAL STATUS                = STOP
```

**References**（read on `develop@de4fed3`; not edited）:

| record | role here |
| --- | --- |
| `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md`（#3323） | D0–D13（§2.2）, the public-origin configuration（§3）, the logging fields（§3.6）, the rejection response（§5）, JSON-only（§6）, logout failure（§7）, gates（§11） |
| `docs/audit/web-bff-csrf-v1-approval-record-2026-10-24.md`（#3324） | A-1 to A-8; the A-3 conditions; the A-7 deadline and conditions; A-8 |
| `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md`（#3325） | A-6 phases and O-1 to O-6; observation mode semantics（§2.1）; AC-1 to AC-13; U-1 to U-6 |

- This record resolves the design of **U-1** from #3325 §8.2 as U-1a / U-1b / U-1c.
- It does not change any earlier decision: A-1 to A-8 and O-1 to O-6 stand as recorded.
- **U-1a, U-1b and U-1c are design decisions.** They authorize no code, configuration change, deployment or rollout.

---

## 2. Mode configuration contract（U-1a）

| item | contract |
| --- | --- |
| variable | **`WEB_CSRF_MODE`**（proposed name; see U-1h in §9.2） |
| scope | **server-only**. Never a `NEXT_PUBLIC_*` variable, never sent to the browser |
| allowed values | exactly `observe` or `enforce`: lower-case, no surrounding whitespace, no list |
| default | **none**. There is **no implicit default to `observe`**, and none to `enforce` either. An unset variable is a configuration error（§3） |
| per environment | set separately for Preview and Production. Setting or changing it in any environment is a configuration change requiring authorization（§7）; **none is authorized** |

**Client input cannot select the mode.**

- No request header, URL parameter, cookie, request body or any other request attribute is read for mode
  selection.
- The mode comes only from the server-side configuration.

**Selection once at request entry.**

- The guard reads `WEB_CSRF_MODE` once, at the start of handling an in-scope request, before any other work.
- That value governs the whole request.
- Reading at request time matches the contract §3.3 handling of `WEB_PUBLIC_ORIGINS`.

**One evaluator.**

- Both modes run the **same** evaluation: the public-origin resolution and the decision table D0–D13 of the
  contract §2.2.
- The modes differ **only** in what happens after a reject outcome（§4, §5）.
- There is no separate rule set for observation.

**No automatic or time-based change.**

- Nothing in code changes the mode: not a timer, a date, a request count, an error rate or the end of the 24-hour
  observation（O-3）.
- The mode changes only through the manual procedure in §7（U-1c）.

---

## 3. Missing or invalid mode configuration（U-1b）

| configuration state | outcome |
| --- | --- |
| `WEB_CSRF_MODE` unset | **fail closed** |
| empty string | **fail closed** |
| unknown value（`report`, `off`, `OBSERVE`, ` enforce`, `true`…） | **fail closed** |
| malformed or ambiguous（`observe,enforce`, several values, control characters） | **fail closed** |
| `observe` | observation mode（§4） |
| `enforce` | enforcement mode（§5） |

- **Never silently switch to `observe`**, or to any other mode, when the configuration is not exactly one allowed
  value.
- **The fail-closed response** is the existing rejection contract（contract §5）:
  - HTTP **403**, body **`{"detail":"forbidden"}`**;
  - `Content-Type: application/json`, **`Cache-Control: no-store`**;
  - **no `Set-Cookie`**, **no backend request**, **no token refresh**, **the request body is not consumed**.
- **Logged** as one line: route path, reason code `mode_config_invalid`, no mode marker（there is no valid mode）.
  The configured value is **not** logged（§4.2）.
- **Operational consequence:** when the mode configuration is invalid, every in-scope route is unavailable:
  login, register, logout, concierge chat, compass weekly and `DELETE /api/users/me`. This is deliberate, and it
  matches the contract §3.5 posture for the public-origin configuration. Gates must catch it before users do
  （§8, §9）.
- **Testing:** the exact validation rules and their runtime integration must be implemented and tested **after
  A-0 approval**. Nothing is tested by this record.

---

## 4. Observation mode（`observe`）

### 4.1 Behaviour

- **Evaluate the same rules** used by enforcement: public-origin resolution and D0–D13（§2）.
- **Record** each would-be rejection outcome（§4.2）.
- **Continue the existing request processing flow** unchanged. The route behaves, responds and sets cookies
  exactly as it does today（with the exceptions in §4.3）.
- **CSRF attacks are not blocked.** During observation the existing CSRF exposure（the base contract T1–T11）
  **remains open**. This mirrors the rollout plan §2.1.
- **D0 in observe**: a public-origin resolution failure is a would-be rejection. It is logged and the request
  continues, as the rollout plan §2.1 states for D0–D13. It is a failing observation for AC-6（§6, C-1）.

### 4.2 Monitoring（the contract §3.6 fields only）

**Logged:**

- the route path;
- the decision row（D0–D13）;
- the reason code;
- a non-sensitive **mode marker**（`observe` / `enforce`）, needed to tell observation logs from enforcement logs.

**Never logged:** the raw `Origin`, `Host`, `Cookie`, `Authorization`, access or refresh tokens, any environment or
configuration value, or request bodies.

- Allowed requests are not logged by the guard（contract §3.6）.
- Counting legitimate traffic stays open as **U-3**（rollout plan §8.2）.
- **The report-only instrumentation does not exist and requires A-0.**

### 4.3 Route-specific notes in `observe`

| route | note |
| --- | --- |
| `DELETE /api/users/me` | today it already **blocks** cross-origin requests with its own `isAllowedOrigin` check（contract §4.3）. Observation must not weaken an existing protection, so in `observe` that **existing check keeps deciding** exactly as today, and the new evaluator's outcome is only recorded. The new evaluator replaces it as the authority only in `enforce`（§5）. Today's check keeps its known S-14 limitation（it compares with `req.nextUrl.origin`） |
| login, register, chat, compass weekly（JSON-only, A-4） | whether the A-4 `415` rule applies in `observe` or is only recorded is **not derivable** from the approvals（U-1e, §9.2） |
| logout（A-5） | A-5 is client behaviour on a non-2xx logout. In `observe` no CSRF 403 is produced, but A-5 still applies to other failures. It does not depend on the mode |

---

## 5. Enforcement mode（`enforce`）

- Apply **D0–D13 exactly** as the contract §2.2 specifies, with the public-origin configuration of §3.
- **Reject before reading the body.** The guard reads only headers and server configuration.
- After a rejection: the §3 response; **no backend call, no token refresh, no cookie**.
- Valid requests continue through their **existing logic** unchanged.
- **JSON-only（A-4）:** after the origin check passes, a non-`application/json` body on login, register, chat or
  compass weekly gets `415`, with no cookie and no backend call（contract §6）.
- **Logout failure（A-5）:** the client keeps the authenticated state and shows an error on a non-2xx logout,
  including a CSRF 403（contract §7）.
- **`DELETE /api/users/me`:** the new evaluator replaces `isAllowedOrigin` as specified in the contract §4.3.
  The reference is the configured origin; both headers absent → 403; the §5 response.

---

## 6. Runtime evaluation failures

| # | failure | `observe` | `enforce` |
| --- | --- | --- | --- |
| F-1 | **invalid mode configuration**（§3） | fail closed（403, §3 response）. "Every mode" includes this case, because no valid mode exists | fail closed（same） |
| F-2 | **public-origin resolution failure**（D0: configuration missing, malformed or ambiguous, or the host is not configured） | a would-be rejection: logged as D0, the request continues（rollout plan §2.1）. **Counts against AC-6** | rejected with the §3 response（contract §3.5） |
| F-3 | **unexpected internal evaluator error**（an exception or an impossible state inside the guard, not a D-row outcome） | **U-1d — Mother Ship decision required**. It must not be recorded as a valid request or as a completed observation. It must be logged as `evaluator_error`（no request data）, and it fails the observation window for that route | **the request is not processed**: 403 with the §3 response, logged as `evaluator_error`. No fail-open |

- **F-3 in `observe`.** The approvals do not say whether to fail closed（403）or to continue the existing flow
  after logging. Continuing would be fail-open behaviour under an internal error, which is **not authorized** by
  any approval. Until U-1d is decided, the implementation must not ship `observe` mode.
- **C-1（consistency note）:** the contract §3.5 says D0 fails closed with every route unavailable. That text was
  written before modes existed and describes enforcement. For `observe`, the rollout plan §2.1（approved A-6
  operations）says D0–D13 outcomes are logged and processed. This record follows both: §3.5 for `enforce`, §2.1
  for `observe`. Mother Ship may confirm this reading（§9.2）.

---

## 7. Manual mode switching（U-1c）

A change of the mode in any environment, including setting it for the first time, requires **all** of:

| # | requirement |
| --- | --- |
| M-1 | a **recorded Mother Ship decision** authorizing the change. For Production, `observe` needs the Phase 2 authorization and `enforce` needs the L4 GO（rollout plan §2） |
| M-2 | the **target mode** and the **affected environment**（Preview / Production） |
| M-3 | the **deployment or configuration revision** identified: the deployment ID and commit, and when and by whom the configuration was changed. No values are recorded |
| M-4 | the **verification evidence** required for that transition: for `observe` → `enforce`, AC-1 to AC-13 of the rollout plan |
| M-5 | **confirmation that the change actually took effect** on the running deployment. For example, the guard's log lines carry the new mode marker, and an owner-controlled test request shows the expected behaviour（403 in `enforce`, a logged would-be rejection in `observe`） |
| M-6 | a **documented recovery plan** for that change（rollout plan §6） |

- **A configuration change alone is not proof** that the effective mode changed. Whether and when a running
  deployment picks up a changed server-side variable（for example, whether a redeploy is needed）is unverified;
  see U-5 in the rollout plan.
- **No automatic promotion** from `observe` to `enforce`, ever（O-3, O-4）.
- **`enforce` → `observe` weakens CSRF defence.** It is a rollback under **O-5**（manual, Mother Ship approval）
  and an exceptional security-risk decision under **O-6**. It is never an automatic response to operational
  failures.

---

## 8. Acceptance tests（future; requires A-0）

No test is implemented or run by this record.

| # | test |
| --- | --- |
| T-1 | `observe` and `enforce` are each selected only by the exact value |
| T-2 | unset, empty, unknown, upper-case, whitespace-padded and multi-value → the §3 fail-closed response, with no side effects |
| T-3 | **no client override**: headers, query parameters, cookies and bodies that name a mode have no effect in either mode |
| T-4 | **identical evaluation**: for every D0–D13 input case, the evaluator returns the same row and reason in both modes |
| T-5 | `observe` keeps the existing processing: status, body, `Set-Cookie` and backend calls equal the pre-V-1 behaviour for both would-be rejected and allowed requests. `DELETE /api/users/me` keeps today's `isAllowedOrigin` decision（§4.3） |
| T-6 | `enforce` returns 403 with no `Set-Cookie`, no backend call, no refresh and an unread body, for each reject row |
| T-7 | internal evaluator error: `enforce` → 403, no processing; `observe` → per U-1d once decided; never logged as allowed |
| T-8 | JSON-only（A-4）in `enforce`; its `observe` behaviour per U-1e once decided |
| T-9 | logout failure UI（A-5）on a 403 and on a network failure |
| T-10 | Preview browser E2E（Chromium, WebKit, Firefox）in each mode on the Preview（rollout plan AC-3） |
| T-11 | logging: each line has only the route, row, reason and mode marker, and no `Origin`, `Host`, cookie, token, configuration value or body |
| T-12 | **no automatic switching**: no code path changes the mode. A static check finds no write to the mode, and no time- or count-based branch selects it |

---

## 9. Dependencies and unresolved gates

### 9.1 Preserved（unchanged）

| item | state |
| --- | --- |
| A-0 | **not approved** |
| L4 | **not approved** |
| A-3 | conditional: Preview validation and E2E; test use is not validated reliance |
| A-6 | O-1 to O-6: 24-hour observation; extended when the criteria are unmet; an explicit GO before enforcement; manual recovery with Mother Ship approval |
| A-7 | the Class B deadline and conditions unchanged. **The clock starts at the V-1 implementation PR merge**, not at observation or enforcement. This record does not reset it |
| A-8 | G3 requires actual production **enforcement**; `observe` does not count |
| U-2 to U-6 | open（rollout plan §8.2）. U-1 is designed here; its implementation needs A-0 |
| S-6, S-8 remainder, S-14 | open |

### 9.2 Unresolved questions from this record

| id | question | why it is open |
| --- | --- | --- |
| **U-1d** | in `observe`, what happens after an **unexpected internal evaluator error**: fail closed（403）, or continue the existing flow with an `evaluator_error` record | no approval covers it; continuing would be fail-open, which is not authorized. `observe` must not ship until decided |
| U-1e | in `observe`, is the A-4 JSON-only `415` enforced, or only recorded | A-4 approves JSON-only; A-6 / §2.1 say observation keeps the existing behaviour. The approvals do not settle which wins |
| C-1 | confirm that the contract §3.5 D0 fail-closed applies to `enforce`, and that the rollout plan §2.1 applies to `observe`（§6） | reconciliation of two approved records; recorded, not decided |
| U-1h | whether the variable name `WEB_CSRF_MODE` needs its own approval（A-1 approved only `WEB_PUBLIC_ORIGINS`） | the name is a proposed implementation detail here |

### 9.3 Future synchronization（not done here）

`README.md`, `architecture.md` and `roadmap.md` are unchanged. When V-1 is implemented, the environment-variable
documentation（for example `.env.example`）will need `WEB_PUBLIC_ORIGINS` and `WEB_CSRF_MODE`, without values,
in the implementation PR under A-0.

---

## 10. STOP

```text
runtime code                 UNCHANGED
API routes                   UNCHANGED
cookies / authentication     UNCHANGED
environment variables        UNCHANGED（WEB_CSRF_MODE not created）
Production                   UNCHANGED
deployment                   NONE
rollout                      NONE
automatic enforcement        NONE
CSRF bypass                  NONE
G1–G5                        NOT IMPLEMENTED
PR merge                     NONE
A-0 = NOT APPROVED
L4  = NOT APPROVED
```
