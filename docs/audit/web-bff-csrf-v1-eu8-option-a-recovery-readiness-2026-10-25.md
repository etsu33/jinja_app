# CSRF V-1 EU-8 Option A — read-only recovery readiness audit (2026-10-25)

## Scope and authorization

Mother Ship selected EU-8 **Option A** in #3334: **design / read-only recovery readiness only**. This audit performs Vercel authenticated GET/read/list operations only. It grants **no** Rollback, Promote, redeploy, environment-variable modification, traffic switch, rehearsal execution, or elapsed-time measurement. A-0, L4-O, L4-E remain **NOT APPROVED**.

Baseline: [EU-2 / EU-8 Mother Ship record](web-bff-csrf-v1-eu2-permissions-eu8-rehearsal-decision-2026-10-25.md), [feasibility audit](web-bff-csrf-v1-rv-ud-technical-feasibility-2026-10-25.md), [recovery-extension design](web-bff-csrf-v1-recovery-extension-design-2026-10-25.md).

## Project-specific read-only evidence (snapshot; non-durable eligibility)

Read methods: Vercel authenticated `get_project`, `list_deployments` scoped to production, `list_team_members`, and `list_deployment_aliases` for two older deployment IDs. No environment values, runtime log content, PII, or secrets fetched.

- Team: `team_T3yjcdUkvzsc99eqYyF2repd`; project: `jinja-app-web` (`prj_odAjGXc6alMlAGSx46q4RQ9EBrjp`).
- Plan: **Hobby** (previous authenticated evidence). One team-member role returned: **OWNER**. This is evidence of role, not action success.
- Project `latestDeployment`: `dpl_6gwoQP4XjFRxxAR3ad5X3t8yPzrB`, `READY`, `production`, commit `db54e108ec6bab54d023d2c8c9099260fe899d73` (#3334).
- Prior Production: `dpl_3yUsDZWaUgTErJ7JPNHp2eU5cDS8`, `READY`, commit `0bb9ac8f61e4c741d9b9df8561273aa40e5df0ac` (#3333), reported `isRollbackCandidate=true`.
- Older Production: `dpl_2szatFTWf4StSKVQUpAjVurAWP2o`, `READY`, commit `19b256158e81293d1c52e1d31b9eae8845a3f780` (#3332), reported `isRollbackCandidate=false` **now**, although it was reported `true` in the preceding audit. This demonstrates that candidate eligibility is time-dependent.
- Both explicit `list_deployment_aliases` requests (for #3333 and #3332 deployments) returned an empty alias list. An empty result is **not evidence** about current production domain routing or permitted traffic switching.

Observed flags are transient platform snapshots, **not proof** that a deployment can be restored at the time of an incident. No rollback eligibility claim survives future deploys without a fresh check.

## A-plan readiness checklist: observations versus gaps

| Check | Status | Evidence or missing requirement |
| --- | --- | --- |
| Team / project identity | OBSERVED | Authenticated project read |
| Plan limits | OBSERVED | Hobby; any actual action subject to current platform restrictions |
| Team operator role | ROLE_OBSERVED | OWNER role reported; requester-specific rollback/promote action authorization not exercised |
| Current and prior Production identities | OBSERVED | Ready deployments and Git SHAs recorded above |
| Candidate eligibility at response time | SNAPSHOT_ONLY | `isRollbackCandidate` varies with subsequent releases |
| Retention and restorability at incident time | UNVERIFIED | Need contemporaneous availability and eligibility |
| Effective env/mode compatibility after restore | UNVERIFIED | No environment values collected; prior deployment may carry historical config |
| Domain / traffic assignment | UNVERIFIED | Alias queries empty; no authoritative traffic-switch proof |
| Named recovery operator and backup | UNVERIFIED | No person assigned in this audit |
| Recovery runbook/exit criteria and evidence custody | DESIGN_GAP | Need reviewed exact target, prerequisites, success/failure criteria and privacy-safe evidence |
| Recovery elapsed time | NOT MEASURED | Operation not authorized and not attempted |

## Recovery preflight contract — proposed, not approved

Before any separately authorized production operation, record a fresh immutable target deployment ID and SHA, target creation date, current Production assignment, plan/role and valid candidate status, preservation/retention, env/mode compatibility, domain and user impact, owner/backup, success/failure/STOP criteria, acceptable evidence and logging redaction, and rollback-specific O-5/O-6 decisions if reduced protection is possible. A documentation snapshot must not substitute for a real rehearsal or an incident-time preflight.

## Final status and gates

- **EU-8**: Option A read-only audit **PERFORMED**; rehearsal approach choice **SELECTED**; recovery-duration validation **BLOCKED / OPEN**.
- **EU-2**: **PARTIAL / OPEN** (role observed; actual Rollback/Promote authorization untested).
- **MS-1 / MS-2 / MS-3** remain unresolved; selecting EU-8 Option A does not decide the broader MS-2 acceptance criterion.
- **RV-2 / RV-3 / RV-4 / RV-5 / RV-6 / RV-9 / RV-10 / RV-11 / P-13** remain unresolved; **RV-1〜RV-11, UD-1〜UD-11** unchanged.
- **A-0 / L4-O / L4-E**: **NOT APPROVED**.
- **No** runtime code, environment, deployment, aliases, logging configuration, production traffic, or secrets changed.

This document is evidence of a read-only audit, **not** evidence of a successful recovery rehearsal.
