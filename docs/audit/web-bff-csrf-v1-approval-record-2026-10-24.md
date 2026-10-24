# Web BFF CSRF V-1 — Approval Record A-1 to A-8（2026-10-24）

## 1. Status

```text
RECORD TYPE              = approval record（documentation only）
APPROVALS RECORDED       = A-1 to A-8（Mother Ship, 2026-10-24）
A-0 RUNTIME AUTHORIZATION = NOT APPROVED
IMPLEMENTATION           = NOT STARTED, NOT AUTHORIZED
VERIFICATION             = NOT PERFORMED by this record
DEPLOYMENT / PRODUCTION  = NONE / UNCHANGED
CLASS B VULNERABILITY    = NOT FIXED（risk temporarily accepted under conditions; §4.7）
FINAL STATUS             = STOP
```

---

## 2. Source and contract reference

| item | value |
| --- | --- |
| authoritative contract | `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md` |
| contract PR | #3323, merged to `develop` as `dc17d82` |
| contract sections the approvals refer to | §2.2（D0–D13）, §3（public-origin configuration）, §6（S-2）, §7（S-5）, §9.4（Class B）, §10.5（G1–G4 separation）, §11（gates L0–L4）, §12（approvals A-0 to A-8） |
| earlier records（unchanged） | #3319 base contract, #3320 S-8 gate audit, #3322 S-8 Preview evidence |

**Relationship to the contract.**

- This record **adds** approval status. It does **not** edit or reinterpret the contract.
- The contract text that says "proposal, not approved"（§6, §7, §9.4, §12）stays as written. It was correct when
  #3323 merged.
- From this record onward, the status of A-1 to A-8 is the one in §3 below.
- If an approval here differs in wording from a contract proposal, the **Mother Ship decision as recorded here**
  governs that approval. The contract governs everything else.

---

## 3. Decision table A-1 to A-8

| id | contract item（§12） | Mother Ship decision | status |
| --- | --- | --- | --- |
| **A-1** | the variable name and format `WEB_PUBLIC_ORIGINS`（contract §3.3） | **A**: approve `WEB_PUBLIC_ORIGINS` and its documented format | **approved** |
| **A-2** | the S-12 condition as applied in rows D4–D8, including D4 | **A**: approve S-12 decision rows D4–D8 | **approved** |
| **A-3** | in preview mode, `VERCEL_URL` / `VERCEL_BRANCH_URL` as platform-provided public origins（contract §3.2） | **A**: conditionally approve the Vercel Preview origin variables, subject to validation and E2E | **conditionally approved**（§4.3） |
| **A-4** | S-2: JSON-only request bodies（contract §6） | **A**: approve JSON-only request handling for the four documented routes | **approved**（§4.4） |
| **A-5** | S-5: logout failure behaviour（contract §7） | **A**: preserve authentication state and show an error when logout fails | **approved**（§4.5） |
| **A-6** | S-4: rollout mode（contract §11, L4） | **B**: approve a phased rollout | **approved in principle**. The monitoring duration, switching criteria and rollback procedure remain **open**（§4.6） |
| **A-7** | the Class B time bound, and whether and under which conditions the Class B risk is accepted until then（contract §9.4） | **A**: approve conditional temporary acceptance of the Class B residual risk, with the deadline and conditions in the Mother Ship decision | **conditionally approved**（§4.7） |
| **A-8** | the G3 dependency on V-1 enforcement（contract §10.5） | **A**: require production V-1 enforcement before G3 is enabled | **approved**（§4.8） |
| **A-0** | V-1 runtime implementation authorization | — | **NOT APPROVED** |

---

## 4. Approval conditions

### 4.1 A-1 — `WEB_PUBLIC_ORIGINS`

- Approved as specified in the contract §3.2–§3.3 and §3.7:
  - a server-only variable;
  - a comma-separated list of exact origins;
  - `https`, except loopback hosts;
  - no wildcard, no `0.0.0.0`, no path;
  - an ambiguous configuration fails closed.
- Approving the **name and format** does **not** create or set the variable in any environment. Setting it is
  an implementation and deployment step（L3）, outside this record.

### 4.2 A-2 — rows D4–D8

- Rows D4–D8 of the contract §2.2 are approved as written:
  - D4: `same-origin` with `Origin` absent → allow;
  - D5: `same-origin` with a matching `Origin` → allow;
  - D6–D8: `same-origin` with a contradictory, `null`, malformed or duplicated `Origin` → reject.
- This makes the earlier conditional S-12 approval concrete **for these rows only**. All other rows were already
  fixed by S-1 / S-9 and are unchanged.

### 4.3 A-3 — Vercel Preview origin variables（conditional）

- `VERCEL_URL` and `VERCEL_BRANCH_URL` may be used in preview mode, as defined in the contract §3.2.
- **Conditions that must be met before they are relied on:**
  1. **Validation:** the configuration rules in the contract §3.3 / §3.7 accept them, and unit tests cover them
     present, missing and malformed（contract §8.1）.
  2. **E2E:** a Preview E2E run（contract §8.6, gate L2）confirms that first-party POSTs pass and cross-site
     POSTs fail, on Preview.
- Until both conditions are met, the approval does not count as satisfied.
- Production does **not** use these values（contract §3.2）. A-3 does not change that.

### 4.4 A-4 — JSON-only（S-2）

- The four documented routes are login, register, concierge chat and compass weekly（contract §6）.
- After the origin check passes, a non-`application/json` body gets `415`, with no cookie and no backend call.
- Logout is not affected: it has no body, and only the origin check applies.

### 4.5 A-5 — logout failure（S-5）

- On a non-2xx logout response or a network failure:
  - the client keeps the authenticated state;
  - it shows an error;
  - it does **not** clear client caches as if logged out.
- On 2xx, behaviour is unchanged（contract §7）.
- The contract tied this to production enforcement. It is approved, and implementing it remains subject to A-0.

### 4.6 A-6 — phased rollout（S-4）

- **Approved:** a phased rollout, not immediate full enforcement.
- **Open:**
  - the exact monitoring or observation duration;
  - the criteria for switching from one phase to the next;
  - the rollback procedure.
- This record does not define phases, durations or criteria.
- L4（production rollout authorization）stays open, and needs these details.

### 4.7 A-7 — conditional temporary acceptance of the Class B residual risk

**What is accepted.** The same-site cross-origin CSRF risk on the 20 deferred Class B and B / C handler files
（contract §9.1–§9.2）may remain while the separate Class B PR is prepared. This is accepted **temporarily and
only under the conditions below**.

**What is not claimed.** The underlying Class B vulnerability is **not fixed**. No Class B handler has CSRF
protection today, and this record changes no code.

**Deadline**（all must hold; the earliest governs）:

1. Class B protection is completed **before general release**.
2. Class B protection is completed **before a custom domain is attached** to the project.
3. The Class B PR merges **no later than 14 days after the V-1 PR merges**.

**Conditions during the temporary acceptance period:**

4. **No new same-site sibling origin** may be introduced. That includes a custom domain, a subdomain or a
   shared registrable domain.
5. The **deferred handler inventory must not expand** without a new Mother Ship decision. The baseline is the 20
   files in the contract §9.1, enforced by the inventory guard in the contract §8.5.
6. **Any violation requires immediate reassessment** by Mother Ship.

**Clock.**

- Deadline 3 is measured from the merge of the V-1 implementation PR.
- That PR does not exist, and cannot be created until A-0 is approved. So the 14-day period has **not started**.
- Deadlines 1 and 2 apply regardless.

### 4.8 A-8 — G3 dependency

- The handoff G3 user-facing flow must not be enabled until V-1 is **enforced in production**.
- Enforcement in report-only or observation mode during a phased rollout（A-6）does not count as enforced.
  This is inference from "enforcement". It is recorded so it can be confirmed when the A-6 phases are defined.
- G1–G5 are otherwise unchanged by this record（§5）.

---

## 5. Remaining open decisions

| id | decision | status |
| --- | --- | --- |
| **A-0** | V-1 runtime implementation authorization | **open — not approved** |
| S-6 | backend defense in depth for direct `AllowAny` anon-cookie endpoints | open |
| S-8（remainder） | browser coverage（WebKit, Firefox）, POST, Production verification | open |
| S-14 | Docker and self-hosted operational verification | open |
| A-6 details | observation period, switching criteria, rollback procedure | open |
| L4 | production rollout authorization | open |
| G2–G5 | handoff implementation gates（G1 remains conditionally approved, per its own record） | open / not approved |

---

## 6. Approval, implementation and verification are separate

| layer | state after this record |
| --- | --- |
| **Approval**（policy） | A-1, A-2, A-4, A-5, A-8 approved. A-3 and A-7 conditionally approved. A-6 approved in principle with its details open. **A-0 not approved** |
| **Implementation**（code） | **none**. No helper, no route change, no test, no environment variable. Nothing may start until A-0 |
| **Verification**（evidence） | only the earlier Preview GET evidence（#3322）. No POST, WebKit, Firefox, Docker or Production verification. The A-3 conditions are unmet. L0–L4 not started |

**An approval in this record is not evidence that anything works, and it does not authorize writing code.**

---

## 7. Implementation and deployment STOP

```text
STOP — no runtime implementation（A-0 not approved）
STOP — no CSRF guard, no route edits, no cookie or authentication changes
STOP — no environment variables set（WEB_PUBLIC_ORIGINS is approved in format only）
STOP — no deployment, no Production change, no rollout（L4 open; A-6 details open）
STOP — no G1–G5 implementation; G3 additionally blocked by A-8 until V-1 is enforced in production
```

---

## 8. Decision provenance

| item | value |
| --- | --- |
| decision maker | Mother Ship |
| date | 2026-10-24 |
| how received | the task brief for this record, which states A-1 to A-8, the A-7 deadline and conditions, and the still-open list |
| prior state | the contract §12（#3323）listed A-0 to A-8 as outstanding |
| artifacts | no separate signed artifact is stored in the repository. This record is the in-repository statement of those decisions |
| interpretation | decisions are recorded as stated. Where this record adds an interpretation, it is labeled: the §4.7 clock start and the §4.8 meaning of "enforced" |
| supersedes | only the **status** of A-1 to A-8 in the contract §12. No earlier text is edited |

---

## 9. Not done

```text
runtime code / BFF routes / frontend       UNCHANGED
cookies / authentication                   UNCHANGED
environment variables                      NONE SET
models / migrations                        UNCHANGED
deployments / Production                   NONE / UNCHANGED
CSRF guard / Class B protection            NOT IMPLEMENTED
G1–G5                                      NOT IMPLEMENTED
A-0                                        NOT APPROVED
PRs                                        none merged
```
