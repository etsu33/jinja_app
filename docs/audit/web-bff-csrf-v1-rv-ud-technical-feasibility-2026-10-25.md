# Web BFF CSRF V-1 — RV / UD Technical Feasibility Assessment（2026-10-25）

## 1. Baseline and authorization status

```text
RECORD TYPE                 = read-only technical feasibility assessment（documentation only）
AUDIT BASELINE              = develop@19b256158e81293d1c52e1d31b9eae8845a3f780（PR #3332 merged）
EVIDENCE BASELINE           = docs/audit/web-bff-csrf-v1-rv-ud-evidence-mapping-audit-2026-10-25.md（#3332）
ITEMS ASSESSED              = 22（RV-1 to RV-11, UD-1 to UD-11）
ITEMS RESOLVED              = 0
A-0 RUNTIME IMPLEMENTATION  = NOT APPROVED
L4-O PRODUCTION OBSERVATION = NOT APPROVED
L4-E PRODUCTION ENFORCEMENT = NOT APPROVED
PRODUCTION / HOSTING        = NOT ACCESSED
FINAL STATUS                = STOP
```

- Code, tests and workflows are unchanged since the #3332 baseline `704ede7`: `git diff --stat 704ede7 19b2561`
  lists only the #3332 audit document. All repository line references below are at
  `19b256158e81293d1c52e1d31b9eae8845a3f780`.
- **Preserved decisions:** U-3 = A, U-4 = A, U-5 = B, U-6 = B and every earlier decision（#3323 to #3331）; the
  #3331 §5.2 interpretation that a restoration weakening active enforcement needs O-5 / O-6 controls（ER-1 to
  ER-5）; the original "rollback by revert" wording（#3323 §11, line 563）; A-7 unchanged; S-6, S-8 remainder and
  S-14 open.
- **A feasibility finding does not resolve an RV or UD item.** Every RV and UD item stays open.

---

## 2. Scope and verification method

### 2.1 Repository inspection（read-only）

Everything inspected by #3332 §2, plus: `apps/web/package.json`（Next.js `16.3.8`, line 38）, `apps/web/next.config.ts`,
`apps/web/src/lib/api/conciergeChat.ts`, `apps/web/src/lib/api/inflight.ts`,
`backend/shrine_project/settings.py`（`LOGGING`, 501 onward）. No test was run.

### 2.2 External technical specifications

- `vercel.com` was **not reachable** from this session（DNS failure）.
- Vercel's published documentation was read through a documentation search tool that queries a third-party index
  of the public docs and **does not access any Vercel account or project**. No project, deployment, environment
  variable or log was read.
- The excerpts below are labelled **EXT-n**. They describe the **general platform**. They are not proof of this
  project's plan, configuration or behaviour, and they are not re-checked against the live docs page.

| id | general platform statement（as returned by the documentation index） | source page |
| --- | --- | --- |
| EXT-1 | `vercel rollback [deployment-id or url]` rolls back **production** deployments to a previous deployment; "On the hobby plan, rollbacks are limited to the immediately preceding production deployment"; a specific older deployment URL is available on Pro and Enterprise | `https://vercel.com/docs/cli/rollback`, `https://vercel.com/docs/deployments/rollback-production-deployment` |
| EXT-2 | REST `POST /v1/projects/{projectId}/rollback/{deploymentId}`: "Point production traffic to a previous production deployment by ID" | `https://vercel.com/docs/rest-api/projects/point-production-traffic-to-a-previous-production-deployment-by-id` |
| EXT-3 | **Deployment type matters:** Instant Rollback reassigns Production traffic to an eligible previously served Production deployment **without rebuilding**; promotion of an already-built staged Production deployment also needs no rebuild; promotion of a **Preview** deployment to Production creates a **new Production build** with Production environment variables. The generic claim that `vercel promote` never rebuilds is invalid. These are general platform rules, not verified for this project. | `https://vercel.com/docs/deployments/promoting-a-deployment`, `https://vercel.com/docs/deployments/promote-preview-to-production`, `https://vercel.com/docs/cli/promote` |
| EXT-4 | after declaring an environment variable: "Redeploy your project after saving to apply changes" | `https://vercel.com/docs/environment-variables/managing-environment-variables` |
| EXT-5 | runtime log entries carry `level`, `message`, `requestMethod`, `requestPath`, `responseStatusCode`, `timestampInMs` | `https://vercel.com/docs/rest-api/logs/get-logs-for-a-deployment` |
| EXT-6 | log drain payloads may include proxy metadata such as `clientIp`, `userAgent` and `referer` | `https://vercel.com/docs/drains` |
| EXT-7 | team members have roles and `teamPermissions`（for example `FullProductionDeployment`）; which role may roll back was **not** found | `https://vercel.com/docs/rest-api/teams/update-a-team-member` |

**Additional published retention constraints（not verified for this project）:** Vercel reported on 2026-09-16 that Hobby projects retain fewer older deployments beyond their normal retention window; eligible exceptions include recent, active and aliased deployments. On 2026-10-09 Vercel announced that new Pro teams default to 30-day retention; older deployments may be deleted under the applicable policy. Sources: `https://vercel.com/changelog/hobby-projects-now-retain-fewer-deployments-to-free-up-storage`, `https://vercel.com/changelog/new-pro-teams-now-default-to-30-day-deployment-retention`. These announcements do **not** establish this project’s plan, retention policy, deployment inventory or restore eligibility. A previously verified deployment is not necessarily still present or eligible when recovery is needed.

**Not found in the index:** per-plan runtime-log retention periods; whether a rolled-back deployment runs with the
environment variables of its original build or the current ones.

### 2.3 Four evidence levels for recovery

| level | meaning | state for this project |
| --- | --- | --- |
| L-a general platform capability | documented for Vercel in general | EXT-1 to EXT-7 only |
| L-b verified for the KAMIMUSUBI project | confirmed by the owner on the actual project（plan, roles, settings） | **none** |
| L-c procedure tested on a non-Production deployment | a rehearsal with recorded results | **none** |
| L-d Production recovery authorization | a Mother Ship decision under O-5（and O-6 when enforcement weakens） | **none**; L4-O / L4-E not approved |

### 2.4 Classifications

| label | meaning |
| --- | --- |
| STATICALLY_SUPPORTED | established by repository code or tests read here |
| TECHNICALLY_PLAUSIBLE | consistent with code and general specifications, but not demonstrated |
| REQUIRES_ENVIRONMENT_VERIFICATION | needs owner verification on the hosting project or a non-Production rehearsal |
| REQUIRES_RUNTIME_IMPLEMENTATION | needs V-1 code under A-0 before it can be assessed |
| REQUIRES_MOTHER_SHIP_DECISION | a design or policy choice the approvals do not make |
| UNVERIFIED | neither code nor accessible specification settles it |

Each item has one **primary** classification and, where useful, secondary ones.

---

## 3. RV-1 to RV-11 feasibility matrix

Definitions: `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:193-203`. #3332 classification is
shown for each item.

### 3.1 Summary

| id | requirement | #3332 | primary classification | secondary | Mother Ship decision? |
| --- | --- | --- | --- | --- | --- |
| RV-1 | exact operational commands | NO_EVIDENCE / UNVERIFIED | REQUIRES_ENVIRONMENT_VERIFICATION | — | no（procedure accepted at L4-O） |
| RV-2 | supported Vercel restoration operations | NO_EVIDENCE / BLOCKED | REQUIRES_ENVIRONMENT_VERIFICATION | TECHNICALLY_PLAUSIBLE | no |
| RV-3 | permissions and roles | NO_EVIDENCE / BLOCKED | REQUIRES_ENVIRONMENT_VERIFICATION | — | no |
| RV-4 | configuration-only rollback feasibility | NO_EVIDENCE / BLOCKED | REQUIRES_ENVIRONMENT_VERIFICATION | REQUIRES_RUNTIME_IMPLEMENTATION | yes（MS-3） |
| RV-5 | whether a redeploy is required | NO_EVIDENCE / BLOCKED | REQUIRES_ENVIRONMENT_VERIFICATION | TECHNICALLY_PLAUSIBLE | yes（MS-3） |
| RV-6 | which configuration a restored deployment uses | NO_EVIDENCE / BLOCKED | UNVERIFIED | REQUIRES_ENVIRONMENT_VERIFICATION | no |
| RV-7 | auth / session / cookie implications | INDIRECT / PARTIAL | STATICALLY_SUPPORTED（partial） | REQUIRES_ENVIRONMENT_VERIFICATION | no |
| RV-8 | effective-mode verification procedure | DESIGN_ONLY / UNVERIFIED | REQUIRES_RUNTIME_IMPLEMENTATION | REQUIRES_ENVIRONMENT_VERIFICATION | no |
| RV-9 | recovery time | NO_EVIDENCE / BLOCKED | REQUIRES_ENVIRONMENT_VERIFICATION | — | no |
| RV-10 | restoration test results | NO_EVIDENCE / BLOCKED | REQUIRES_MOTHER_SHIP_DECISION | REQUIRES_ENVIRONMENT_VERIFICATION | yes（MS-2） |
| RV-11 | compatibility with "rollback by revert" | DESIGN_ONLY / BLOCKED | REQUIRES_MOTHER_SHIP_DECISION | — | yes（MS-1） |

### RV-1 — exact operational commands

| field | finding |
| --- | --- |
| verified evidence | none for this project. `scripts/deploy.sh:1-12` is a placeholder; `.github/workflows/deploy.yml.disabled:1-5, 58-61` is disabled |
| source paths | as above |
| external specification | EXT-1, EXT-2, EXT-3（level L-a only; EXT-3 distinguishes existing Production deployments from Preview promotion, which triggers a new Production build） |
| unverified assumptions | that the general commands apply to this project's plan and team; that the person executing has the role（RV-3） |
| feasibility | general commands exist for production rollback and promotion. **They are not adopted here as the procedure**: their availability, scope and effects for this project are unknown（RV-2, RV-3, RV-6） |
| future validation | an owner-written procedure based on L-b facts, exercised at L-c where possible（see RV-10） |
| authorization / environment | owner access to the hosting project; no Production operation is authorized |
| Mother Ship decision | not for the commands themselves; the resulting plan is judged at L4-O（P-13） |

### RV-2 — supported Vercel restoration operations

| field | finding |
| --- | --- |
| verified evidence | none for this project（`docs/ops/production-bff-hardening.md:74` covers log reading only） |
| external specification | EXT-1, EXT-2, EXT-3 |
| unverified assumptions | the project's plan. **If it is on the Hobby plan, EXT-1 limits rollback to the immediately preceding production deployment**, which may not be the verified target that VD-1 to VD-6（#3331 §2.1）require |
| feasibility | restoration of a previous Production deployment is a general platform capability（TECHNICALLY_PLAUSIBLE）. Whether the needed target is reachable depends on plan restrictions **and deployment retention / deletion / eligibility**（REQUIRES_ENVIRONMENT_VERIFICATION）. The 2026-09-16 Hobby and 2026-10-09 new-Pro retention announcements are general external constraints, not project evidence（§2.2） |
| future validation | owner confirmation of the plan, effective deployment-retention policy, existence and current eligibility of the **specific verified restoration target**（deployment ID / commit / mode evidence per VD-1 to VD-6）, and whether the target remains reachable at recovery time. Do not infer restorability merely from old audit evidence. |
| authorization / environment | hosting-project read by the owner |
| Mother Ship decision | no; but a plan limitation would feed MS-2 and P-13 |

### RV-3 — permissions and roles

| field | finding |
| --- | --- |
| verified evidence | none. `.github/workflows/deploy.yml.disabled:28-30` is a GitHub permission in a disabled workflow |
| external specification | EXT-7: a role model exists; the role that permits rollback was not found |
| unverified assumptions | who holds a role able to restore Production |
| feasibility | REQUIRES_ENVIRONMENT_VERIFICATION |
| future validation | owner confirmation of the role name and holders（names of roles only in evidence） |
| authorization / environment | hosting-project read by the owner |
| Mother Ship decision | no |

### RV-4 — configuration-only rollback feasibility

| field | finding |
| --- | --- |
| verified evidence | none; no code reads `WEB_CSRF_MODE`（#3332 §1 search） |
| source paths | the design reads configuration at request time（`docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md` §3.3; #3326 §2）; no implementation |
| external specification | EXT-4: changes need a redeploy to apply |
| unverified assumptions | that a running deployment never sees an updated value without redeploy on this project |
| feasibility | **a configuration-only change should not be assumed to change the effective mode.** EXT-4 indicates a redeploy is needed in general, so a "configuration-only" recovery is likely to be configuration change + redeploy, which creates a new deployment |
| future validation | after A-0, change the value on a Preview deployment and observe the mode marker before and after redeploy（M-5） |
| authorization / environment | A-0 implementation; Preview access; owner configuration change on Preview under a recorded decision（M-1） |
| Mother Ship decision | yes（MS-3）: whether a configuration change followed by redeploy is an acceptable recovery path alongside U-5 = B |

### RV-5 — whether a redeploy is required

| field | finding |
| --- | --- |
| verified evidence | none |
| external specification | EXT-4 |
| feasibility | that a redeploy is required for configuration changes is TECHNICALLY_PLAUSIBLE（EXT-4）; for restoration of an existing deployment, EXT-3 states promotion happens without a rebuild |
| unverified assumptions | both statements for this project |
| future validation | as RV-4 |
| authorization / environment | as RV-4 |
| Mother Ship decision | yes（MS-3） |

### RV-6 — configuration used by a restored deployment

| field | finding |
| --- | --- |
| verified evidence | none |
| external specification | **not found**（§2.2） |
| feasibility | UNVERIFIED. Consequences, statically derivable from the contracts: (a) if a restored V-1 deployment uses current configuration, its effective mode is today's `WEB_CSRF_MODE`, not the mode recorded when it was verified（VD-3）; (b) a restored **pre-V-1** deployment has no guard at all, whatever the configuration, so restoring it from `enforce` disables enforcement and triggers ER-1 to ER-5（#3331 §5.2） |
| future validation | owner-confirmed platform behaviour, then a Preview check with the mode marker |
| authorization / environment | hosting-project knowledge; A-0 for the marker |
| Mother Ship decision | no |

### RV-7 — authentication, session and cookie implications

| field | finding |
| --- | --- |
| verified evidence | `apps/web/src/lib/server/authCookies.ts:21-23, 31-38, 45-71`（cookie names, lifetimes, attributes）; `apps/web/src/lib/server/bffFetch.ts:200-203, 233-237`; `apps/web/src/app/api/concierge/chat/route.ts:112-157`; tests listed in #3332 RV-7 |
| feasibility（STATICALLY_SUPPORTED part） | cookies are stored by the browser with fixed `Max-Age`; tokens are JWTs issued and refreshed through the backend（`apps/web/src/lib/server/bffFetch.ts:78-89`）. A Web deployment change does not itself clear cookies or invalidate tokens. #3323 §4.4 keeps cookies, tokens and attributes out of V-1 scope, so pre-V-1 and V-1 deployments share the same cookie contract |
| not statically supported | (a) A-5 changes the logout UI; restoring a pre-V-1 deployment brings back today's logout UI, which ignores the response status（`apps/web/src/lib/auth/AuthProvider.tsx:197-213`）; (b) behaviour of in-flight requests during the switch |
| future validation | Preview session-continuity check across a restoration: logged-in state, refresh, logout before and after |
| authorization / environment | A-0; Preview |
| Mother Ship decision | no |

### RV-8 — effective-mode verification procedure

| field | finding |
| --- | --- |
| verified evidence | none; no mode marker exists |
| source paths | `apps/web/src/lib/server/logging.ts:7, 20`（production emits only `warn` / `error`） |
| external specification | EXT-5: runtime logs carry level, message, path and status, so a marker in a log message is observable in general |
| feasibility | REQUIRES_RUNTIME_IMPLEMENTATION. A marker that M-5 relies on must be emitted at a level that is produced in production（not `info` / `debug` through `serverLog`）. An owner-controlled test request（M-5）can show 403 in `enforce` and a would-be-rejection line in `observe` |
| unverified assumptions | log access and retention on this project（UD-4） |
| future validation | the procedure exercised on Preview in both modes; the exact expected log line asserted by a unit test |
| authorization / environment | A-0; Preview; log access |
| Mother Ship decision | no（M-5 already defines the requirement） |

### RV-9 — recovery time

| field | finding |
| --- | --- |
| verified evidence | none |
| feasibility | REQUIRES_ENVIRONMENT_VERIFICATION; depends on RV-1 to RV-5 |
| future validation | timed rehearsal（see RV-10） |
| Mother Ship decision | no |

### RV-10 — restoration test results

| field | finding |
| --- | --- |
| verified evidence | none |
| external specification | EXT-1 and EXT-2 describe rollback as pointing **production** traffic to a previous **production** deployment |
| feasibility | the exact restoration operation of U-5 = B acts on production traffic in general. **A non-Production rehearsal of the identical operation may not exist.** A Preview can rehearse deploying a known-good commit and verifying it, but not necessarily the production rollback itself |
| future validation | Mother Ship defines what counts as an acceptable rehearsal; then it is run and recorded（U-4） |
| authorization / environment | rehearsal authorization; any Production rehearsal would need its own Mother Ship decision |
| Mother Ship decision | **yes（MS-2）** |

### RV-11 — compatibility with "rollback by revert"

| field | finding |
| --- | --- |
| verified evidence | contracts only: `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md:563`; `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md:161`; `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:111-128` |
| comparison（not a decision） | see table below |
| feasibility | both mechanisms are technically plausible in general; which satisfies the L4 requirement is a contract question |
| future validation | Mother Ship confirmation in a later record |
| Mother Ship decision | **yes（MS-1）**. This assessment does not decide whether to amend #3323 §11 |

| aspect | rollback by revert（#3323 §11） | verified-deployment restoration（U-5 = B） |
| --- | --- | --- |
| artefact | a new commit and a new build | an **eligible previously served Production deployment**（Instant Rollback: no rebuild）; Preview-to-Production promotion is **not equivalent** and triggers a new Production build（EXT-3） |
| passes CI again | yes（the revert commit runs `web-tests.yml`） | no new CI run; relies on the target's earlier evidence（VD-5） |
| repository history | records the rollback | does not change `develop` / `main`; the deployed code and the branch head diverge until reconciled |
| configuration | the new build uses current configuration | unverified（RV-6） |
| speed | build and deploy time | likely faster; unverified（RV-9） |
| reaches older targets | an available commit, subject to build/deploy feasibility | plan-dependent **and retention/eligibility-dependent**（EXT-1; 2026-09-16 and 2026-10-09 retention announcements, §2.2） |

---

## 4. UD-1 to UD-11 feasibility matrix

Definitions: `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:259-269`.

### 4.1 Summary

| id | requirement | #3332 | primary classification | secondary | Mother Ship decision? |
| --- | --- | --- | --- | --- | --- |
| UD-1 | aggregation implementation | NO_EVIDENCE | REQUIRES_RUNTIME_IMPLEMENTATION | REQUIRES_MOTHER_SHIP_DECISION | yes（MS-8） |
| UD-2 | instrumentation and logging-contract extension | INDIRECT | REQUIRES_MOTHER_SHIP_DECISION | REQUIRES_RUNTIME_IMPLEMENTATION | yes（MS-4, MS-11） |
| UD-3 | reason-code names | DESIGN_ONLY | REQUIRES_MOTHER_SHIP_DECISION | STATICALLY_SUPPORTED（existing names） | yes（MS-5） |
| UD-4 | retention period | NO_EVIDENCE | REQUIRES_ENVIRONMENT_VERIFICATION | REQUIRES_MOTHER_SHIP_DECISION | yes（MS-9） |
| UD-5 | storage permissions and access | NO_EVIDENCE | REQUIRES_MOTHER_SHIP_DECISION | REQUIRES_ENVIRONMENT_VERIFICATION | yes（MS-9） |
| UD-6 | supporting evidence durability | NO_EVIDENCE | REQUIRES_ENVIRONMENT_VERIFICATION | TECHNICALLY_PLAUSIBLE | no |
| UD-7 | export and integrity | NO_EVIDENCE | TECHNICALLY_PLAUSIBLE | REQUIRES_MOTHER_SHIP_DECISION | yes（MS-10） |
| UD-8 | completeness verification | NO_EVIDENCE | REQUIRES_RUNTIME_IMPLEMENTATION | TECHNICALLY_PLAUSIBLE | no |
| UD-9 | duplicates and retries | INDIRECT | STATICALLY_SUPPORTED（analysis） | REQUIRES_MOTHER_SHIP_DECISION | yes（MS-6） |
| UD-10 | QA / test traffic separation | NO_EVIDENCE | REQUIRES_MOTHER_SHIP_DECISION | — | yes（MS-7） |
| UD-11 | storage provider / database | DESIGN_ONLY | REQUIRES_MOTHER_SHIP_DECISION | — | yes（MS-8） |

### UD-1 — aggregation implementation

| field | finding |
| --- | --- |
| requirement | a dedicated server-side aggregation that is authoritative for AC-8（U-3 = A; AG-1 to AG-10） |
| reusable | the five route handlers as entry points; `serverLog`（`apps/web/src/lib/server/logging.ts:18-33`）as a structured line emitter |
| not implemented | any counter, sink or summary; PostHog（`apps/web/src/lib/analytics/providers.ts:1, 28-30, 43`）is client-side and not authoritative |
| candidate approaches（not selected） | (A) one structured log line per in-scope request outcome at a production-emitted level, aggregated from a durable log sink; (B) a server-side write to a dedicated aggregation store; (C) per-instance buffering with periodic flush to a store |
| constraints found | module-scope state is per server instance（`apps/web/src/lib/server/bffFetch.ts:54`）, so in-memory counts are not authoritative across instances. #3323 §5 forbids any backend request on rejection; a store reached through the Django backend（`djFetch` / `bffFetchWithAuthFromReq`）would conflict with that on the reject path unless explicitly exempted |
| privacy / security | only route identifier, window, mode classification, outcome categories and counts（#3330 §3.1, §7）; no IP, user agent, user ID, token or body. Counting must not delay or alter the response in `observe`（#3326 §4.1） |
| tests needed | per-route counting unit tests; no-side-effect tests on the reject path（no backend call, no cookie）; behaviour-preservation tests in `observe` |
| dependencies / boundary | MS-8; UD-2; A-0; Production use only after L4-O |

### UD-2 — instrumentation and logging-contract extension

| field | finding |
| --- | --- |
| requirement | design of the extension, including counting allowed requests（#3330 §3.2） |
| reusable | `serverLog` JSON lines; `scripts/analytics_safety/guard.py` as a pattern for allow-list and redaction tests（different dataset） |
| not implemented | any CSRF log line; #3323 §3.6 logs rejections only（`docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md:170-173`） |
| constraints found | `serverLog` spreads any `data` object into the line（`apps/web/src/lib/server/logging.ts:22-27`）, so an allow-list must be enforced by the caller or a wrapper; `info` / `debug` are dropped in production（`apps/web/src/lib/server/logging.ts:7, 20`）; existing route logs are ad hoc（`apps/web/src/app/api/auth/login/route.ts:120-123` logs an exception message） |
| candidate approaches | (A) a dedicated CSRF log function with a fixed field allow-list at `warn`; (B) a separate sink outside the console log; (C) change `serverLog` level behaviour under A-0 |
| privacy / security | if platform log drains are used, EXT-6 indicates drain payloads may carry `clientIp` and `userAgent`; forwarding them would breach #3330 §7 unless filtered |
| tests needed | a test asserting each CSRF line contains only approved fields（AC / T-11 of #3326 §8）; a test that the line is emitted with `NODE_ENV=production` |
| dependencies / boundary | **MS-4**（allowed-request counting and level）, **MS-11**（drains）; A-0 |

### UD-3 — reason-code names

| field | finding |
| --- | --- |
| requirement | names for every outcome, including the would-be `415` record |
| reusable | the D-row codes（#3323 §2.2）, `mode_config_invalid`（#3326 §3）, `evaluator_error`（#3326 §6）are designed（STATICALLY_SUPPORTED as design） |
| not implemented | all codes; the would-be `415` code is not named even in design（#3327 §4.3） |
| candidate approaches | a single code constant module imported by guard and tests |
| privacy / security | codes are fixed strings; no request data |
| tests needed | one assertion per D-row, F-1, F-3 and the `415` record |
| dependencies / boundary | **MS-5**; A-0 |

### UD-4 — evidence retention period

| field | finding |
| --- | --- |
| requirement | how long each evidence source is kept |
| reusable | none. `.github/workflows/web-tests.yml:86-92, 144-150` upload artifacts without `retention-days` |
| not implemented / unknown | platform log retention on this project; the 1-hour figure（#3325 §8.2）is from #3320 and not re-verified; EXT index returned no per-plan figure |
| candidate approaches | (A) review within platform retention and copy aggregates into the U-4 audit record; (B) a durable sink with a declared retention; (C) explicit `retention-days` on CI artifacts used as evidence |
| privacy / security | longer retention of aggregates only; no raw request data |
| tests needed | none in code; a recorded retention confirmation per source |
| dependencies / boundary | owner verification; **MS-9** |

### UD-5 — storage permissions and access controls

| field | finding |
| --- | --- |
| requirement | who can read and write evidence |
| reusable | the least-privilege read pattern of `scripts/analytics_safety/README.md:8-12`（PostHog `query:read`, human-provisioned）as a precedent only |
| not implemented | any access control for CSRF evidence |
| candidate approaches | write-only ingestion credential for the runtime; read-only credential for reviewers; GitHub repository permissions for the U-4 audit record |
| privacy / security | no credential may appear in evidence or logs（#3330 §7） |
| tests needed | credential-absence and redaction tests modelled on the analytics-safety tests |
| dependencies / boundary | **MS-9**; UD-11; owner setup |

### UD-6 — supporting evidence durability

| field | finding |
| --- | --- |
| requirement | evidence remains accessible for review（#3330 §5.3） |
| reusable | git history makes the U-4 audit record itself durable（TECHNICALLY_PLAUSIBLE for reviewed summaries） |
| not implemented | durability of the underlying evidence（logs, artifacts, aggregates） |
| candidate approaches | copy aggregate summaries and their integrity hashes into the audit record（UD-7）; keep source data in a sink with declared retention（UD-4） |
| privacy / security | aggregates only in git; nothing user-identifying |
| tests needed | a review check that every cited source is reachable at review time（EV-7） |
| dependencies / boundary | UD-4, UD-7; owner verification |

### UD-7 — export and integrity verification

| field | finding |
| --- | --- |
| requirement | a way to export evidence and show it was not altered |
| reusable | `scripts/analytics_safety/posthog_baseline_report.py` shows an aggregate-only JSON export pattern（different dataset, no integrity check） |
| not implemented | any CSRF export or integrity mechanism |
| candidate approaches | (A) aggregate JSON export with a SHA-256 digest recorded in the audit record; (B) commit the aggregate file in the audit PR so git provides immutability; (C) a signed artifact |
| privacy / security | aggregates only |
| tests needed | export schema test; digest reproducibility test |
| dependencies / boundary | **MS-10**; UD-1 |

### UD-8 — data collection completeness

| field | finding |
| --- | --- |
| requirement | missing or failed collection is detected（AG-7, EV-2） |
| reusable | none |
| not implemented | any completeness signal |
| candidate approaches | (A) per-window collection status emitted by the aggregation; (B) cross-check aggregate per-route totals against platform request-level entries（EXT-5: path and status）within retention; (C) explicit "collection failed" outcome counted rather than dropped |
| privacy / security | cross-checks use path, status and counts only |
| tests needed | simulate sink failure and show the window is marked incomplete, not PASS |
| dependencies / boundary | UD-1; A-0 |

### UD-9 — duplicated or retried requests

| field | finding |
| --- | --- |
| requirement | retries and duplicates do not silently corrupt counting semantics（AG-9） |
| static analysis（STATICALLY_SUPPORTED） | (a) BFF-internal retries are upstream calls, not inbound requests: `apps/web/src/lib/server/bffFetch.ts:135-144`（pre-refresh）, `:200-203`（401 → refresh → retry）, `apps/web/src/app/api/concierge/chat/route.ts:112-157`. Counting at BFF entry counts each inbound request once; counting upstream calls would over-count. (b) Browser-side retries or double submits arrive as separate inbound requests; without a trusted identifier they cannot be merged. (c) `getRequestId`（`apps/web/src/lib/server/logging.ts:13-16`）takes `x-request-id` first, which any client can set, so it is not proof and not a dedup key |
| not implemented | any counting point or dedup rule |
| candidate approaches | define the unit as "inbound requests received by the handler"（not user actions）; count at handler entry once per invocation; do not dedup on client-controlled values |
| privacy / security | no per-request identifier is stored in evidence |
| tests needed | a 401 → refresh → retry request counts once; two identical inbound requests count twice |
| dependencies / boundary | **MS-6**（counting semantics）; A-0 |

### UD-10 — QA / test traffic separation

| field | finding |
| --- | --- |
| requirement | known QA traffic is distinguished where verifiable（AG-3, EV-3） |
| reusable | none（no internal-traffic marker in `apps/web/src` or `backend`） |
| candidate approaches | (A) QA runs recorded with UTC windows in the audit record and excluded by window; (B) a server-side classification of designated QA accounts that emits only a boolean category, never an identifier; (C) a secret marker used only to **exclude** traffic from the legitimate count |
| privacy / security | (B) must not put account identifiers into evidence（#3330 §7）. (C) a forged marker can only reduce the legitimate count, which errs on the conservative side, but the marker must never be treated as proof of legitimacy（AG-4） |
| tests needed | QA-classified requests excluded from legitimate counts; would-be rejections still recorded regardless of QA classification |
| dependencies / boundary | **MS-7**; A-0 |

### UD-11 — storage provider or database

| field | finding |
| --- | --- |
| requirement | where aggregates are stored, if a store is needed |
| reusable | the Django backend database exists（`backend/shrine_project/settings.py`）, but see the UD-1 constraint on backend calls; GitHub audit records are fixed by U-4 = A for reviewed summaries |
| candidate approaches | (A) a dedicated store outside the request path to the backend API; (B) the backend database through a path exempted from #3323 §5 by explicit decision; (C) log sink only（no separate store） |
| privacy / security | aggregates only; access per UD-5 |
| tests needed | depends on the selection |
| dependencies / boundary | **MS-8**; UD-4, UD-5 |

---

## 5. Reusable implementation components

| component | path:lines | reuse for | limitation |
| --- | --- | --- | --- |
| cookie contract | `apps/web/src/lib/server/authCookies.ts:17-23, 31-38, 45-101` | unchanged cookie behaviour under V-1（RV-7） | logout and `DELETE /api/users/me` bypass it（`apps/web/src/app/api/auth/logout/route.ts:9-10`, `apps/web/src/app/api/users/me/route.ts:55-62`） |
| server log helper | `apps/web/src/lib/server/logging.ts:18-33` | CSRF log line（UD-2）, mode marker（RV-8） | drops `info` / `debug` in production（7, 20）; no field allow-list |
| request id helper | `apps/web/src/lib/server/logging.ts:13-16` | log correlation only | client-controllable; not proof, not a dedup key |
| BFF backend helpers | `apps/web/src/lib/server/bffFetch.ts:121-240`; `apps/web/src/lib/server/backend.ts:16` | unchanged allowed-request processing | must not be called on rejection（#3323 §5） |
| route test patterns | `apps/web/src/app/api/**/__tests__/route.test.ts`, `apps/web/src/app/api/auth/login/route.test.ts` | extending to D0–D13, modes and `415` | none cover `Origin` / `Sec-Fetch-Site` today |
| refresh-isolation tests | `apps/web/src/lib/server/__tests__/bffFetch.refreshIsolation.test.ts:88-381` | retry semantics for UD-9 tests | not counting tests |
| NEXT_PUBLIC guard | `apps/web/package.json:28`; `.github/workflows/web-tests.yml:163-165` | U-1a "never `NEXT_PUBLIC_*`" for `WEB_CSRF_MODE` | text search only |
| analytics-safety pattern | `scripts/analytics_safety/README.md:8-12` and its tests | allow-list / redaction test design（UD-2, UD-5） | different dataset; not CSRF evidence |
| Playwright | `apps/web/playwright.config.ts:22-39` | Preview E2E（AC-3） | no Firefox project |
| web CI | `.github/workflows/web-tests.yml:6-25, 53-54, 140-142` | running new unit tests（AC-1, AC-2） | E2E job runs one spec on Chromium（84） |

Observation: the client calls `/api/concierge/chat/` with a trailing slash（`apps/web/src/lib/api/conciergeChat.ts:4`）
while `apps/web/next.config.ts:13-14` sets `trailingSlash: false` and `skipTrailingSlashRedirect: true`. A route
identifier for counting should come from the handler, not the raw request path. How Next.js `16.3.8` matches the
slashed path was not verified here.

---

## 6. Required additional tests（future; not implemented）

| # | test | approach / item | acceptance link |
| --- | --- | --- | --- |
| FT-1 | every D0–D13 row per route, both modes | guard | AC-1, AC-9, #3326 T-4 |
| FT-2 | F-1 matrix（unset, empty, case, whitespace, multi-value） | mode config | #3326 T-2 |
| FT-3 | F-3 injected error → 403, no side effects, `evaluator_error` | guard | #3327 OX-1 to OX-4 |
| FT-4 | `observe` preserves status, body, `Set-Cookie`, backend calls | guard | #3326 T-5 |
| FT-5 | JSON-only `415` in `enforce`; no `415` in `observe`; ordering after allow | A-4 / U-1e | #3327 OX-5 to OX-7 |
| FT-6 | logout route test, and A-5 UI on non-2xx and network failure | logout | AC-12 |
| FT-7 | `DELETE /api/users/me` rewritten to S-1 = A in `enforce`; today's decision in `observe` | users/me | AC-11, #3323 §4.3 |
| FT-8 | CSRF log line contains only approved fields and is emitted under `NODE_ENV=production` | UD-2, RV-8 | #3326 T-11, EV-5 |
| FT-9 | per-route counting at handler entry; refresh-retry counts once; two inbound requests count twice | UD-1, UD-9 | AC-8, EV-1, EV-2 |
| FT-10 | sink failure marks the window incomplete | UD-8 | EV-2, EV-7 |
| FT-11 | QA-classified traffic excluded from legitimate counts; would-be rejections still recorded | UD-10 | EV-3 |
| FT-12 | aggregate export schema and digest reproducibility | UD-7 | EV-6 |
| FT-13 | no client input selects the mode | mode config | #3326 T-3 |
| FT-14 | Preview E2E in Chromium, WebKit and Firefox, both modes | E2E | AC-3, #3326 T-10 |
| FT-15 | Preview rehearsal of the accepted recovery path with mode-marker verification | RV-4, RV-8, RV-10 | M-5, RX-1 to RX-5 |
| FT-16 | session continuity across restoration on Preview | RV-7 | AC-10 |

---

## 7. Design decisions requiring Mother Ship approval

| id | decision | items |
| --- | --- | --- |
| MS-1 | whether verified-deployment restoration satisfies, supplements or requires amending "rollback by revert" | RV-11 |
| MS-2 | what counts as an acceptable non-Production rehearsal, given that general rollback operations act on production traffic | RV-10, P-13 |
| MS-3 | whether configuration change followed by redeploy is an accepted recovery path alongside U-5 = B | RV-4, RV-5 |
| MS-4 | the logging-contract extension: counting allowed requests, the emitted level, the fields | UD-2 |
| MS-5 | the reason-code name for the would-be `415` record | UD-3 |
| MS-6 | counting semantics: inbound requests at handler entry, not user actions; no dedup on client values | UD-9 |
| MS-7 | the QA traffic classification method | UD-10 |
| MS-8 | the aggregation approach and store, including whether any path to the Django backend may be exempted from #3323 §5 | UD-1, UD-11 |
| MS-9 | retention periods and access controls | UD-4, UD-5 |
| MS-10 | the integrity mechanism for exported evidence | UD-7 |
| MS-11 | whether platform log drains may be used, given that drain payloads can include `clientIp` and `userAgent` | UD-2, UD-6 |

---

## 8. Environment-dependent unknowns

| # | unknown | items |
| --- | --- | --- |
| EU-1 | the project's plan tier（Hobby limits rollback to the immediately preceding production deployment, EXT-1） | RV-2, RV-10 |
| EU-2 | roles able to roll back or promote, and who holds them | RV-3 |
| EU-3 | whether configuration changes take effect without redeploy | RV-4, RV-5 |
| EU-4 | which configuration a restored deployment runs with | RV-6 |
| EU-5 | runtime log retention and access on the project | RV-8, UD-4 |
| EU-6 | availability of log drains or another durable sink | UD-2, UD-6 |
| EU-7 | whether the platform overwrites client-supplied request-id headers | UD-9 |
| EU-8 | recovery duration | RV-9 |
| EU-9 | how the deployed Next.js version routes the trailing-slash chat path | UD-1（route identifier） |

None was checked against the hosting project in this assessment.

---

## 9. Dependencies before A-0

- MS-4, MS-5, MS-6 and MS-8 decided, or the implementation PR proposes them for separate validation（the
  logging extension and aggregation need design and privacy validation, #3330 §3.2）.
- A CSRF log design that does not depend on `info` in production（`apps/web/src/lib/server/logging.ts:7, 20`）and enforces a field
  allow-list（`apps/web/src/lib/server/logging.ts:22-27`）.
- A counting point at handler entry that excludes BFF-internal retries（UD-9）.
- A test plan covering FT-1 to FT-13.

## 10. Dependencies before L4-O

- All P-1 to P-15（#3329 §3.1）, including FT-1 to FT-14 passing and Preview E2E with Firefox.
- P-13 recovery plan: EU-1 to EU-4 and EU-8 answered by the owner（L-b）; **the specific verified recovery target must still exist, remain retained, be eligible and reachable under the actual project plan and retention policy at the time of recovery**（RV-2, VD-1 to VD-6; public retention changes are not project proof）; MS-1, MS-2 and MS-3 decided; FT-15 and
  FT-16 run where MS-2 allows（L-c）.
- RV-8 effective-mode procedure written and exercised on Preview.
- A monitoring and evidence-collection plan（#3330 §9）resolving EU-5, EU-6, MS-9, MS-11 for the sources it relies
  on.
- A separate L4-O GO（L-d for observation）.

## 11. Dependencies before L4-E

- Completed observation evidence with AC-8 counts from a working aggregation（UD-1, UD-8 to UD-10）.
- Durable, accessible supporting evidence with export and integrity（UD-4, UD-6, UD-7; MS-10）.
- All AC-1 to AC-12 PASS, then AC-13.
- An enforcement-phase recovery plan meeting ER-1 to ER-5（#3331 §5.2）, including the case of restoring a
  pre-V-1 or `observe` deployment（RV-6 consequence）.

---

## 12. Final STOP

```text
RV-1 to RV-11                    UNRESOLVED（feasibility assessed only）
UD-1 to UD-11                    UNRESOLVED（feasibility assessed only）
A-0  = NOT APPROVED
L4-O = NOT APPROVED
L4-E = NOT APPROVED
runtime code / tests             UNCHANGED; tests NOT RUN
environment variables            NOT READ; NOT MODIFIED
Vercel / Render projects         NOT ACCESSED（documentation index only）
Production requests              NONE
deployment / rollback / mode     NONE
database / storage / telemetry   UNCHANGED
historical CSRF records          NOT EDITED
PR merge                         NONE
```
