# CSRF V-1 EU-2 権限証拠・EU-8 リハーサル判断資料（2026-10-25）

## Scope / STOP

Read-only evidence capture and recorded Mother Ship choice of EU-8 Option A (design scope only). This document does **not** approve, invoke, or prove rollback, promotion, redeployment, environment changes, logging changes, or a rehearsal. No Production traffic-switching operation was performed. A-0, L4-O, and L4-E remain NOT APPROVED. RV-1〜RV-11 and UD-1〜UD-11 remain unresolved.

Reference baseline: [#3333 feasibility audit](web-bff-csrf-v1-rv-ud-technical-feasibility-2026-10-25.md) (§7 MS-1/MS-2/MS-3, §8 EU-2/EU-8), [#3331 recovery extension design](web-bff-csrf-v1-recovery-extension-design-2026-10-25.md). U-5=B is a **design choice**, not proof that the restoration path can be executed.

## EU-2: actual team-role observation (direct project-specific evidence)

| Item | Observed value | Evidence boundary |
| --- | --- | --- |
| Vercel team | `team_T3yjcdUkvzsc99eqYyF2repd` | Authenticated Vercel `get_team` |
| Project | `jinja-app-web`, `prj_odAjGXc6alMlAGSx46q4RQ9EBrjp` | Authenticated Vercel `get_project` |
| Plan | Hobby | Authenticated `get_git_deployment_context` |
| Team member roles | One reported member with `OWNER` | Authenticated `list_team_members` (role only, no personal identifiers exported) |
| Latest Production at read time | `dpl_3yUsDZWaUgTErJ7JPNHp2eU5cDS8`, commit `0bb9ac8f61e4c741d9b9df8561273aa40e5df0ac`, READY | Authenticated `get_project` / `list_deployments` |
| Immediately preceding Production entry | `dpl_2szatFTWf4StSKVQUpAjVurAWP2o`, commit `19b256158e81293d1c52e1d31b9eae8845a3f780`, READY | Authenticated `list_deployments`; candidate flag was true at read time |

### Finding and limitation

**ROLE_CONFIRMED / ACTION_UNVERIFIED.** OWNER role is evidenced for this team, and documented Vercel permissions indicate broad production deployment access. This is *not* an end-to-end confirmation that the specific connected actor can successfully invoke either `request_rollback` or `request_promote`. No write/request operation was invoked, including dry-run-like calls (none were established as guaranteed non-mutating). Plan restrictions, target eligibility, retention and current traffic target require independent verification immediately before any subsequently authorized operation.

EU-2 is **PARTIAL, OPEN**. Do not check off “actual-operation permission verified”.

## EU-8: Mother Ship selected Option A (DESIGN ONLY; NO OPERATIONS APPROVED)

**Mother Ship record (2026-10-25): EU-8 rehearsal approach = Option A.** This approves only the *approach* of read-only recovery-readiness auditing. It does **not** authorize Rollback, Promote, deploy/redeploy, environment-variable changes, a rehearsal execution, or elapsed-time measurement. EU-8 remains **BLOCKED / OPEN**, and RV-9/RV-10/P-13 remain unresolved. PR #3334 is separately awaiting review and merge decision; this choice does not authorize merging it.

**Rationale:** Vercel rollback/promotion can switch Production traffic. An ordinary Preview deploy or preview-only routing test cannot be represented as a rehearsal of the same production restoration operation.

**Choice A — SELECTED by Mother Ship, design only:** Approve *design and read-only readiness audit only*. Verify available candidate, documented roles and ownership, retention, deployment/environment identity, expected recovery operator, evidence capture plan, and rollback exit criteria. Do not execute any rollback/promotion or time an operation. Label EU-8 `BLOCKED: NO APPROVED SAFE REHEARSAL` and keep RV-9/RV-10/P-13 open. Further Mother Ship approval required for a precise rehearsal.

**Choice B — separately scoped non-Production surrogate:** Mother Ship may authorize creation/use of an isolated disposable project/environment (no production domains, customer traffic, secrets or data) to measure a **surrogate** redeploy/traffic-switch workflow. Its timing is only a proxy and cannot satisfy the production-operation rehearsal requirement without an explicitly reviewed equivalence argument. It requires separate scope, cost, access, teardown, and authorization before action.

**Choice C — Production restore rehearsal:** Not covered by current authorization. Requires a separately approved change window, precise target and recovery path, traffic/user impact acceptance, rollback/recovery plan, and required O-5/O-6 signoffs if security controls could be weakened. Do not initiate from this audit.

**MS-2 relationship:** The EU-8 Option A selection does not automatically settle the broader MS-2 contract decision about what counts as a satisfactory non-Production rehearsal. MS-2 remains open unless separately decided by Mother Ship. Any future operation requires separate, precisely scoped approval.

## Evidence-to-gate mapping

- EU-2: role and team ownership are observed; execution rights remain unproven. **PARTIAL / OPEN**.
- EU-8: **Option A SELECTED (design/read-only audit only)**; execution authorization **NONE**; duration **NOT MEASURED**. **BLOCKED / OPEN**.
- MS-1 / MS-2 / MS-3: unresolved. EU-8 Option A selection does not decide the broader MS-2 acceptance contract.
- RV-2 / RV-3 / RV-9 / RV-10 / RV-11 / P-13: continue unresolved. A candidate shown in an API response is not recovery qualification.
- A-0 / L4-O / L4-E: **NOT APPROVED**.

## Safe follow-up

After a separate Mother Ship decision, update the relevant audit gate with timestamp, actor/role evidence, platform plan, exact target eligibility and retention, environment parity, logs/redaction policy, measured timestamps only if an action actually occurred, and review outcome. Never store secrets, environment values, full runtime logs, or identifying team-member details in this document.
