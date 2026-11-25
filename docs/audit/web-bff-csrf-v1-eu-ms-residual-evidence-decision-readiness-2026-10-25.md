# CSRF V-1: EU残存証拠・MS判断整理・EU-8実測承認境界（2026-10-25）

## Scope and STOP

Read-only inspection and decision preparation **only**. EU-8 Option A selected by Mother Ship means read-only recovery-readiness audit; it does not authorize a timed recovery rehearsal. No environment variable value, secrets, production runtime logs, mutation or request probe was collected or performed. No Rollback, Promote, deploy, CSRF runtime change or production alteration. **A-0 / L4-O / L4-E NOT APPROVED.**

Basis: [#3333 feasibility](web-bff-csrf-v1-rv-ud-technical-feasibility-2026-10-25.md), [#3334 EU-2/EU-8 choice](web-bff-csrf-v1-eu2-permissions-eu8-rehearsal-decision-2026-10-25.md), [#3335 read-only preflight](web-bff-csrf-v1-eu8-option-a-recovery-readiness-2026-10-25.md). This is a current evidence inventory, not approval of any of the listed design alternatives.

## EU-3〜EU-5, EU-7, EU-9 evidence matrix

| ID | Project-specific read-only finding | Remaining gap / conclusion |
| --- | --- | --- |
| EU-3: config propagation | Vercel project `jinja-app-web` is dashboard-configured according to existing repo audit; authenticated `get_project` returns its linked deployment identity. | Whether a concrete configuration change reaches a particular deployment remains **UNVERIFIED**. Platform-level guidance that changes require new deployment is not a project-level test. No config changes authorized. |
| EU-4: restored deployment configuration | Authenticated `get_deployment` for `dpl_3yUsDZWaUgTErJ7JPNHp2eU5cDS8` returned `READY / production`, metadata but **no env configuration in the response**. | CSRF mode, environment snapshot compatibility and post-restoration behavior **UNVERIFIED**. This omission is not evidence that a deployment lacks environment variables. Do not collect secret values merely for the audit. |
| EU-5: runtime log retention and access | Previously authenticated `get_runtime_logs` aggregation for Preview over 30 minutes returned an empty level-count table; Hobby plan evidenced through `get_git_deployment_context`. | Authenticated count query succeeded, but it did not prove retention horizon, completeness, individual log read permission across environments, or a durable audit sink. **PARTIAL / OPEN**. |
| EU-7: platform request ID rewriting | Repo `apps/web/src/lib/server/logging.ts` reads client-supplied `x-request-id` before `x-vercel-id` and `cf-ray`; otherwise generates a UUID. | The deployed Vercel proxy's rewriting behavior **UNVERIFIED** without a controlled non-production ingress test. Client-supplied value must not be trusted as unique server-side count/dedup evidence. |
| EU-9: trailing slash route | `apps/web/src/lib/api/conciergeChat.ts` sends POST `/api/concierge/chat/`. `apps/web/next.config.ts` has `trailingSlash:false`, `skipTrailingSlashRedirect:true`, and empty custom `rewrites()`. Authenticated Vercel `list_project_routes(q=concierge/chat)` returned zero project-level rules. Current Vercel project reported Node `24.x`. | Next.js App Router handling of the exact deployed path **UNVERIFIED**; absence of project-level route rules is not evidence of Next internal routing. Non-production controlled test required. |

**Snapshot caution:** A newly observed Vercel `latestDeployment` ID may differ from #3335 simply because docs-only merges trigger deploys. No deployment status or candidate eligibility captured here should supersede a fresh incident-time preflight.

## MS-1〜MS-11: decision options and dependencies — ALL UNAPPROVED

| ID | Mother Ship must decide | Technical options / prerequisite, not decision |
| --- | --- | --- |
| MS-1 | How verified deployment restore relates to `rollback by revert` | Amend contract / dual-path with precedence / retain revert-only. Resolve RV-11 and exceptions O-5/O-6 before operational use. Hobby target limitations matter. |
| MS-2 | Acceptable non-Production rehearsal evidence | Read-only preflight / isolated surrogate (non-equivalent without proof) / separately authorized Production change. EU-8 Option A does **not** approve an action or automatically fulfill RV-10/P-13. |
| MS-3 | Config change + redeploy as secondary recovery | Approve / prohibit / contingency-only, subject to EU-3/EU-4 and weaker-control approval gates. |
| MS-4 | Allowed-request logging schema | Dedicated structured server-side record with fixed allowlisted fields and levels; do not assume production `info` is emitted (current helper suppresses it). |
| MS-5 | Would-be 415 reason-code label | Choose stable code, e.g. `content_type_would_reject_415`; verify existing naming contract. |
| MS-6 | Counting unit | Count received BFF handler requests, not user actions/internal retries; avoid dedup keyed on externally supplied request ID. |
| MS-7 | QA classification | Authenticated internal test metadata / server-generated marker; never solely untrusted client claim. |
| MS-8 | Aggregation system of record | Durable server-side aggregation, no Django call on CSRF rejection side-effect path absent explicit #3323 contract change. |
| MS-9 | Retention and access control | Specify aggregation/evidence duration, allowed reviewers and deletion policy; EU-5 log horizon is not assumed sufficient. |
| MS-10 | Export integrity | Deterministic exported evidence digest + immutable GitHub review references; define provenance, reviewer and change controls. |
| MS-11 | Whether to use log drains | No drains presently configured from EU-6 audit; use only after privacy and potential `clientIp`/`userAgent` filtering, access controls, approval and real subscription availability are checked. |

**Decision status:** NONE of MS-1〜MS-11 are newly chosen by this audit. Existing U-5=B and EU-8=A are separate recorded decisions; do not infer MS-1 or MS-2 from them. All eleven require independent Mother Ship selection/recording.

## EU-8 timed rehearsal approval gate (separate request; NOT GRANTED)

No elapsed-time claim is made. EU-8 option A's read-only audit is complete, but **EU-8 recovery duration stays BLOCKED / OPEN**. If Mother Ship later wishes to authorize a non-production surrogate or Production rehearsal, it must separately specify:

1. Exact target project, environment and immutable source/target deployment IDs; exclude actual Production routing unless separately approved.
2. Permitted operations, including whether test deployment creation, promote, rollback, configuration modification and cleanup are allowed.
3. Operator role, access, cost and data-isolation constraints; no real customer data or production secrets for surrogate testing.
4. Preflight and stop criteria, protection-mode/environment compatibility, fallback, potential user impact and required O-5/O-6 approvals if weaker protection can result.
5. Timing start/stop definitions, required evidence and redaction/retention, and how surrogate result would be distinguished from real Production restore capability.

**Until an explicit new authorization covering these fields is recorded, no rehearsal or measurement is performed.** The existing choice of A is not that authorization.

## Gate summary

- EU-3, EU-4, EU-5, EU-7, EU-9: **OPEN**, evidence scope documented above.
- EU-2 actual operations: **OPEN**; EU-8 duration **BLOCKED / OPEN**.
- RV-1〜RV-11 and UD-1〜UD-11: **unresolved**.
- MS-1〜MS-11: **pending Mother Ship**.
- A-0 / L4-O / L4-E: **NOT APPROVED**.
- Document-only; no runtime, environment, deployment, logging, traffic or secret changes.
