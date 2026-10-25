# Web BFF CSRF V-1 — RV / UD Evidence Mapping Audit（2026-10-25）

## 1. Status

```text
RECORD TYPE                 = read-only evidence mapping audit（documentation only）
AUDIT BASELINE              = develop@704ede7606d49ee8d459b0e061af967d114672ab（PR #3331 merged）
ITEMS MAPPED                = 22（RV-1 to RV-11, UD-1 to UD-11）
DIRECT EVIDENCE             = 0
FULLY VERIFIED ITEMS        = 0
A-0 RUNTIME IMPLEMENTATION  = NOT APPROVED
L4-O PRODUCTION OBSERVATION = NOT APPROVED
L4-E PRODUCTION ENFORCEMENT = NOT APPROVED
PRODUCTION / ENVIRONMENT    = NOT ACCESSED
FINAL STATUS                = STOP
```

**Citation convention.** Every path and line range below refers to the repository content at
`704ede7606d49ee8d459b0e061af967d114672ab`. A permalink is
`https://github.com/etsu33/jinja_app/blob/704ede7606d49ee8d459b0e061af967d114672ab/<path>#L<start>-L<end>`.
`git diff --stat c3642ca 704ede7 -- apps/web backend .github` is empty, so the code and workflows are unchanged
since the final contract's base.

**Method.**

- Read the nine merged CSRF V-1 records（#3323 to #3331）.
- Read the five AC-8 route handlers, `DELETE /api/users/me`, the BFF auth / cookie / logging helpers, the logout
  UI, their tests, the Playwright configuration, the GitHub Actions workflows, the PostHog read-only tooling and the
  operations documents listed in §2.
- Searched the repository（excluding `docs/`）for `WEB_CSRF_MODE`, `WEB_PUBLIC_ORIGINS`, `Sec-Fetch-Site`,
  `requestOrigin`, `publicOrigins`, `evaluator_error` and `mode_config_invalid`: **no match**.
- No test was run. No Production, Vercel, Render, PostHog or environment-variable access was made.

**`NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE`** means nothing was found in the files inspected here. It does not prove
that nothing exists anywhere（for example in a hosting dashboard）.

---

## 2. Inspected scope

| area | paths（at the baseline） |
| --- | --- |
| CSRF V-1 records | `docs/audit/web-bff-csrf-v1-*.md`（9 files, #3323 to #3331） |
| AC-8 routes | `apps/web/src/app/api/auth/login/route.ts`, `apps/web/src/app/api/auth/register/route.ts`, `apps/web/src/app/api/auth/logout/route.ts`, `apps/web/src/app/api/concierge/chat/route.ts`, `apps/web/src/app/api/compass/weekly/route.ts` |
| `DELETE /api/users/me` | `apps/web/src/app/api/users/me/route.ts` |
| auth / cookie / BFF helpers | `apps/web/src/lib/server/authCookies.ts`, `bffFetch.ts`, `backend.ts`, `logging.ts`; `apps/web/middleware.ts` |
| logout UI | `apps/web/src/lib/auth/AuthProvider.tsx`, `apps/web/src/lib/api/auth.ts` |
| tests | the route tests next to each route; `apps/web/src/lib/server/__tests__/bffFetch.refreshIsolation.test.ts`; `apps/web/src/lib/auth/__tests__/*.tsx`; `apps/web/e2e/`; `apps/web/playwright.config.ts` |
| CI | `.github/workflows/web-tests.yml`, `backend-tests.yml`, `codeql.yml`, `deploy.yml.disabled`; `scripts/deploy.sh` |
| analytics | `apps/web/src/lib/analytics/providers.ts`, `apps/web/src/app/providers/ClientBootstrap.tsx`, `scripts/analytics_safety/` |
| operations docs | `docs/ops/*.md`, `docs/runbooks/*.md`, `docs/infra/*.md`, `docs/ci/testing_policy.md` |

---

## 3. Classification scheme

| evidence class | meaning |
| --- | --- |
| **DIRECT** | repository code, test or workflow that itself implements or verifies the requirement |
| **INDIRECT** | existing code or tests that bear on the requirement（a constraint, a building block）but do not implement or verify it |
| **DESIGN_ONLY** | only an approved or proposed contract text exists |
| **NO_EVIDENCE** | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |

| status | meaning |
| --- | --- |
| **VERIFIED** | the requirement is implemented and verified by cited evidence |
| **PARTIAL** | some aspects are established by cited evidence; others are not |
| **UNVERIFIED** | not established; resolvable by future repository work after A-0 |
| **BLOCKED** | cannot be established within current authorization: it needs hosting / Production environment verification or a Mother Ship decision |

**Contract text alone never yields VERIFIED.**

---

## 4. RV mapping records（recovery readiness）

Authoritative definitions: `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:193-203`（table
header at 190-191）. Related contracts for all RV items: the same file §2.1 VD-1 to VD-6（79-84）, §3（111-128）,
§4 R-1 to R-6（138-143）, §5.2 ER-1 to ER-5（173-177）; `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md`
§6（147-161）; `docs/audit/web-bff-csrf-v1-mode-contract-2026-10-24.md` §7（183-196）.

### RV-1

| field | value |
| --- | --- |
| requirement | the exact operational commands for recovery |
| contract | `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:193`; `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md:154-156` |
| source | `scripts/deploy.sh:1-12` is a placeholder（"ここに実デプロイ手順を書く（例）", no real step）. `.github/workflows/deploy.yml.disabled:1-5, 58-61` is a disabled workflow that only calls that placeholder. No recovery command found: `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | none active. `deploy.yml.disabled` is not an active workflow |
| evidence class | **NO_EVIDENCE** |
| status | **UNVERIFIED** |
| proves | the repository holds no deployment or recovery command; deployment is not repository-driven through GitHub Actions |
| does not prove | how Production is actually deployed or restored |
| dependencies | RV-2 to RV-6（the commands depend on the platform operations and permissions） |
| future validation | a documented, reviewed recovery procedure tested outside Production（for example on Preview）once authorized |
| gate | **L4-O**（P-13）; also L4-E（E-9） |

### RV-2

| field | value |
| --- | --- |
| requirement | the supported Vercel rollback / restoration operations |
| contract | `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:194`, §2.3（101-107）; `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md:158` |
| source | `docs/ops/production-bff-hardening.md:74` covers reading Vercel Function Logs only. No restoration procedure: `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **NO_EVIDENCE** |
| status | **BLOCKED**（needs hosting-project inspection, not authorized here） |
| proves | nothing about restoration capability |
| does not prove | that any documented Vercel feature is enabled or usable on the connected Production project |
| dependencies | owner inspection of the hosting project; RV-3 |
| future validation | owner-confirmed list of supported operations for the actual project and plan |
| gate | **L4-O**（P-13） |

### RV-3

| field | value |
| --- | --- |
| requirement | the required permissions and account roles |
| contract | `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:195` |
| source | `.github/workflows/deploy.yml.disabled:28-30` declares GitHub `deployments: write` for a disabled workflow; this is not a hosting-platform role. Otherwise `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **NO_EVIDENCE** |
| status | **BLOCKED** |
| proves | nothing about who can restore Production |
| does not prove | the hosting roles or who holds them |
| dependencies | RV-2 |
| future validation | owner confirmation of the roles needed and of who holds them, by role name only |
| gate | **L4-O**（P-13） |

### RV-4

| field | value |
| --- | --- |
| requirement | configuration-only rollback feasibility |
| contract | `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:196`, §2.2（90-99）; `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md:157` |
| source | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE`. The guard that would read `WEB_CSRF_MODE` does not exist（repository search, §1） |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **NO_EVIDENCE** |
| status | **BLOCKED** |
| proves | — |
| does not prove | that changing a server-side variable changes the running behaviour without a redeploy |
| dependencies | the A-0 implementation（the mode read）; RV-5; platform behaviour |
| future validation | a Preview experiment after A-0 showing whether a configuration change alone changes the effective mode（M-5） |
| gate | **A-0**（implementation）, **L4-O** |

### RV-5

| field | value |
| --- | --- |
| requirement | whether a redeployment is required |
| contract | `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:197`; `docs/audit/web-bff-csrf-v1-mode-contract-2026-10-24.md:190-192` |
| source | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **NO_EVIDENCE** |
| status | **BLOCKED** |
| proves | — |
| does not prove | redeploy behaviour on the hosting platform |
| dependencies | RV-4; platform behaviour |
| future validation | as RV-4 |
| gate | **L4-O** |

### RV-6

| field | value |
| --- | --- |
| requirement | whether historical deployments use the current or the previous environment configuration |
| contract | `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:198`, §2.3（104） |
| source | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **NO_EVIDENCE** |
| status | **BLOCKED** |
| proves | — |
| does not prove | which configuration a restored deployment runs with. This decides whether VD-3（effective mode）of a restoration target can be known in advance |
| dependencies | RV-2; platform behaviour |
| future validation | owner-verified platform behaviour, confirmed on a non-Production target |
| gate | **L4-O** |

### RV-7

| field | value |
| --- | --- |
| requirement | authentication, session and cookie implications of restoration |
| contract | `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:199` |
| source | `apps/web/src/lib/server/authCookies.ts:21-23`（Max-Age: access 1 h, refresh 7 days, anon 90 days）, `:31-38`（`Secure` only in production over https）, `:45-71`（HttpOnly, `SameSite=Lax`, `Path=/`）; `apps/web/src/lib/server/bffFetch.ts:200-203`（401 → refresh → retry）, `:233-237`（refreshed access cookie written）; `apps/web/src/app/api/concierge/chat/route.ts:112-157`（chat's own refresh flow）; `apps/web/src/app/api/auth/logout/route.ts:6-12` and `apps/web/src/app/api/users/me/route.ts:55-62`（cookie deletion with `Path=/` and `Max-Age=0` only, not through `authCookies.ts`） |
| test | `apps/web/src/app/api/auth/login/route.test.ts:66, 118`（cookies issued; `Secure` in production + https）; `apps/web/src/lib/server/__tests__/bffFetch.refreshIsolation.test.ts:99-355`（refresh isolation, refreshed-cookie contract, 401-only retry）; `apps/web/src/app/api/concierge/chat/__tests__/route.test.ts:108, 157`（refresh success / failure） |
| CI | `.github/workflows/web-tests.yml:53-54`（`test:contract` runs vitest）and `:140-142`（`test:cov`） |
| evidence class | **INDIRECT** |
| status | **PARTIAL** |
| proves | the current cookie attributes and refresh behaviour are defined in code and covered by unit tests. Cookies live in the browser with fixed lifetimes; a Web deployment change does not itself clear them |
| does not prove | what happens to sessions when a different deployment is restored: compatibility of the restored code with existing cookies and backend tokens, or any effect of a restored pre-V-1 deployment on CSRF exposure（#3331 §5.2 interpretation） |
| dependencies | the A-0 implementation; RV-6 |
| future validation | a session-continuity check across restoration on Preview: logged-in state, refresh and logout before and after |
| gate | **A-0**, **L4-O** |

### RV-8

| field | value |
| --- | --- |
| requirement | the effective-mode verification procedure |
| contract | `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:200`, §5.2 ER-4（176）; `docs/audit/web-bff-csrf-v1-mode-contract-2026-10-24.md:187`（M-5） |
| source | no mode or mode marker exists（repository search, §1）. `docs/ops/production-smoke-checklist.md:23-32` lists Production smoke targets（login, `/api/users/me/`, chat and others）; it does not check any CSRF mode and does not include register, logout or compass weekly |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **DESIGN_ONLY** |
| status | **UNVERIFIED** |
| proves | M-5 defines what verification must show（the mode marker in log lines and an owner-controlled test request） |
| does not prove | that a procedure exists or works; the smoke checklist cannot observe a CSRF mode |
| dependencies | the A-0 implementation of the mode marker（#3326 §4.2）; log access within retention（UD-4） |
| future validation | a written procedure, exercised on Preview in both modes |
| gate | **A-0**, **L4-O**, **L4-E** |

### RV-9

| field | value |
| --- | --- |
| requirement | recovery time and operational duration |
| contract | `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:201`; `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md:159` |
| source | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **NO_EVIDENCE** |
| status | **BLOCKED** |
| proves | — |
| does not prove | any recovery duration |
| dependencies | RV-1, RV-2, RV-10 |
| future validation | timed rehearsal on a non-Production target |
| gate | **L4-O** |

### RV-10

| field | value |
| --- | --- |
| requirement | actual restoration test results |
| contract | `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:202` |
| source | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **NO_EVIDENCE** |
| status | **BLOCKED** |
| proves | — |
| does not prove | that any restoration has ever been performed or succeeded |
| dependencies | RV-1 to RV-9 |
| future validation | an authorized rehearsal with recorded results（U-4 evidence record） |
| gate | **L4-O** |

### RV-11

| field | value |
| --- | --- |
| requirement | compatibility of verified-deployment restoration（U-5 = B）with the original "rollback by revert" requirement |
| contract | `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md:563`（L4: "rollback by revert"）; `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md:161`; `docs/audit/web-bff-csrf-v1-recovery-extension-design-2026-10-25.md:111-128, 203, 340` |
| source | not applicable（a contract reconciliation） |
| test | not applicable |
| CI | not applicable |
| evidence class | **DESIGN_ONLY** |
| status | **BLOCKED**（requires technical verification and Mother Ship confirmation） |
| proves | both texts exist; #3331 §3 records the reconciliation as open and requires a STOP if both cannot hold |
| does not prove | that restoration satisfies, supplements or amends "rollback by revert" |
| dependencies | RV-1 to RV-10; a Mother Ship decision |
| future validation | Mother Ship confirmation recorded in a later approval record |
| gate | **L4-O**（P-13）, **L4-E** |

---

## 5. UD mapping records（aggregation and evidence readiness）

Authoritative definitions: `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:259-269`（table
header at 257-258）. Related contracts for all UD items: the same file §2.3 AG-1 to AG-10（93-102）, §3.2（135-145）,
§5.3（187-197）, §11 EV-1 to EV-10（331-340）; `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md` §3.6
（168-173）.

### UD-1

| field | value |
| --- | --- |
| requirement | exact aggregation implementation |
| contract | `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:259`, §2.1（68-71）, §2.3（93-102） |
| source | no server-side CSRF aggregation: `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE`. The only analytics provider is client-side PostHog: `apps/web/src/lib/analytics/providers.ts:1, 28-30, 43`, loaded from a `"use client"` module（`apps/web/src/app/providers/ClientBootstrap.tsx:1`） |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **NO_EVIDENCE** |
| status | **UNVERIFIED** |
| proves | no server-side request aggregation exists for the five AC-8 routes |
| does not prove | anything about counts. Client-side events are not server-side request counts |
| dependencies | UD-2, UD-8, UD-9, UD-10, UD-11; privacy validation |
| future validation | an aggregation design reviewed against AG-1 to AG-10, implemented and unit-tested after A-0 |
| gate | **A-0**; evidence used at **L4-E**（AC-8） |

### UD-2

| field | value |
| --- | --- |
| requirement | instrumentation design and the logging-contract extension, including counting allowed requests |
| contract | `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:260`, §3.2（135-145）; `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md:170-173`; `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md` §5.3（131-137） |
| source | `apps/web/src/lib/server/logging.ts:18-33`（`serverLog`, one JSON line per event）; `:7, 20`（`debug` / `info` are emitted only when `NODE_ENV !== "production"` and `DEBUG_LOG === "1"`; in production only `warn` / `error` are emitted）. Routes log ad hoc: `apps/web/src/app/api/auth/login/route.ts:52-55, 70-74, 85-91, 103-108, 120-123`; `apps/web/src/app/api/auth/register/route.ts:49-52, 70-74, 85-90`; `apps/web/src/app/api/concierge/chat/route.ts`（`console.log` / `console.warn` throughout）; `apps/web/src/lib/server/bffFetch.ts:162-179, 208-215`. None of these is the #3323 §3.6 CSRF line |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` for server logging. `apps/web/src/lib/client/__tests__/logging.test.ts` tests the client logger only |
| CI | not applicable |
| evidence class | **INDIRECT** |
| status | **UNVERIFIED** |
| proves | a structured server log helper exists; it suppresses `info` / `debug` in production |
| does not prove | any CSRF instrumentation or allowed-request counting. Note: an `info`-level counter through `serverLog` would emit nothing in production |
| dependencies | separate design and privacy validation; A-0; UD-3 |
| future validation | a logging-extension design that states its level and fields, with tests asserting that only approved fields appear |
| gate | **A-0**; Production use at **L4-O** |

### UD-3

| field | value |
| --- | --- |
| requirement | logging reason-code names, including the would-be `415` record |
| contract | `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:261`; `docs/audit/web-bff-csrf-v1-final-contract-2026-10-24.md` §2.2 table（63-80, reason codes per row）; `docs/audit/web-bff-csrf-v1-mode-contract-2026-10-24.md` §3（`mode_config_invalid`）, §6（`evaluator_error`）; `docs/audit/web-bff-csrf-v1-observe-exceptions-2026-10-25.md` §4.3（the would-be `415` code is unnamed） |
| source | none of these codes appears in code（repository search, §1） |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **DESIGN_ONLY** |
| status | **UNVERIFIED** |
| proves | the D-row codes, `mode_config_invalid` and `evaluator_error` are specified in design |
| does not prove | implementation; the would-be `415` code does not exist even in design |
| dependencies | UD-2; separate design validation for the `415` record |
| future validation | unit tests asserting the exact code for each D-row, F-1, F-3 and the `415` record |
| gate | **A-0** |

### UD-4

| field | value |
| --- | --- |
| requirement | evidence retention period |
| contract | `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:262`, §5.3（194-196）; `docs/audit/web-bff-csrf-v1-rollout-plan-2026-10-24.md:198`（1-hour platform log retention, citing #3320 §5） |
| source | `.github/workflows/web-tests.yml:86-92, 144-150` upload artifacts without `retention-days`; no `retention-days` appears in any workflow. Platform log retention: not re-verified here |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | as source |
| evidence class | **NO_EVIDENCE** |
| status | **UNVERIFIED** |
| proves | the repository does not set artifact retention; it falls to platform defaults, which are not recorded in the repository |
| does not prove | any retention period for CI artifacts or Production logs. The 1-hour figure is an earlier audit observation, not re-verified |
| dependencies | owner confirmation of platform retention; UD-6 |
| future validation | a recorded retention decision and its confirmation for each evidence source |
| gate | **L4-O**（monitoring plan）, **L4-E** |

### UD-5

| field | value |
| --- | --- |
| requirement | storage permissions and access controls |
| contract | `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:263` |
| source | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` for CSRF evidence. `scripts/analytics_safety/README.md:8-12` describes a least-privilege read pattern for a different dataset（PostHog, human-provisioned, not wired into CI） |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **NO_EVIDENCE** |
| status | **UNVERIFIED** |
| proves | — |
| does not prove | who can read or write CSRF observation evidence |
| dependencies | UD-11 |
| future validation | an access-control decision recorded with the evidence design |
| gate | **L4-O** |

### UD-6

| field | value |
| --- | --- |
| requirement | supporting evidence durability |
| contract | `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:264`, §5.3（187-197） |
| source | `.github/workflows/web-tests.yml:86-92`（Playwright report uploaded only on failure）, `:144-150`（coverage artifact）; no retention set. `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` for any durable evidence store |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | as source |
| evidence class | **NO_EVIDENCE** |
| status | **UNVERIFIED** |
| proves | existing CI artifacts are not designed as durable evidence |
| does not prove | that any supporting evidence remains accessible for review（U-4 requires this） |
| dependencies | UD-4, UD-7 |
| future validation | per-source durability confirmation before an acceptance criterion relies on it |
| gate | **L4-E**（and the L4-O monitoring plan） |

### UD-7

| field | value |
| --- | --- |
| requirement | evidence export and integrity-verification mechanism |
| contract | `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:265` |
| source | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` for CSRF evidence. `scripts/analytics_safety/posthog_baseline_report.py` exports aggregate PostHog analytics only; it has no integrity verification and is unrelated to CSRF |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **NO_EVIDENCE** |
| status | **UNVERIFIED** |
| proves | — |
| does not prove | any export or integrity mechanism for CSRF evidence |
| dependencies | UD-1, UD-11 |
| future validation | a designed export with an integrity check, reviewed before use |
| gate | **L4-E** |

### UD-8

| field | value |
| --- | --- |
| requirement | data collection completeness verification |
| contract | `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:266`, AG-7（99） |
| source | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **NO_EVIDENCE** |
| status | **UNVERIFIED** |
| proves | — |
| does not prove | that missing or failed collection would be detected |
| dependencies | UD-1 |
| future validation | tests that simulate a collection gap and show it is reported, not silently absent（EV-2） |
| gate | **A-0**; relied on at **L4-E** |

### UD-9

| field | value |
| --- | --- |
| requirement | handling of duplicated or retried requests |
| contract | `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:267`, AG-9（101） |
| source | `apps/web/src/lib/server/logging.ts:13-16`（`getRequestId` takes `x-request-id`, `x-vercel-id` or `cf-ray` from request headers, else a random UUID）; `apps/web/src/lib/server/bffFetch.ts:135-144, 200-203` and `apps/web/src/app/api/concierge/chat/route.ts:112-157`（one inbound request can cause a refresh call and a second upstream call） |
| test | `apps/web/src/lib/server/__tests__/bffFetch.refreshIsolation.test.ts:158`（same-identity refresh dedup）, `:325`（401 → refresh → retry） |
| CI | `.github/workflows/web-tests.yml:53-54` |
| evidence class | **INDIRECT** |
| status | **UNVERIFIED** |
| proves | upstream retries exist inside the BFF, so counting at the upstream would differ from counting at BFF entry; a request-correlation helper exists |
| does not prove | any dedup mechanism for counts. `getRequestId` trusts client-suppliable `x-request-id`, which AG-4 does not allow as proof |
| dependencies | UD-1; the counting contract（AG-1） |
| future validation | the counting contract defines the counting point and duplicate semantics; tests with retried and repeated requests |
| gate | **A-0** |

### UD-10

| field | value |
| --- | --- |
| requirement | separation of QA / test traffic from production user traffic |
| contract | `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:268`, AG-3（95） |
| source | no internal / QA traffic marker found in `apps/web/src` or `backend`: `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| test | `NO_EVIDENCE_FOUND_IN_INSPECTED_SCOPE` |
| CI | not applicable |
| evidence class | **NO_EVIDENCE** |
| status | **UNVERIFIED** |
| proves | — |
| does not prove | that QA traffic could be told apart from user traffic |
| dependencies | UD-1; privacy validation（no user identifiers, #3330 §7） |
| future validation | a verifiable, privacy-preserving QA classification and tests（EV-3） |
| gate | **A-0**; relied on at **L4-E** |

### UD-11

| field | value |
| --- | --- |
| requirement | selection of a storage provider or database, where needed |
| contract | `docs/audit/web-bff-csrf-v1-observation-evidence-design-2026-10-25.md:269`, §3.3（147-150）, §5.1（172-177） |
| source | not applicable（a selection decision） |
| test | not applicable |
| CI | not applicable |
| evidence class | **DESIGN_ONLY** |
| status | **UNVERIFIED** |
| proves | U-4 = A fixes GitHub audit documents as the record of reviewed evidence; the store for aggregated counts is not chosen |
| does not prove | where counts are stored, or that any store exists |
| dependencies | UD-1, UD-4, UD-5 |
| future validation | a recorded selection with privacy and retention review |
| gate | **A-0** |

---

## 6. Classification summary

| class | RV | UD | total |
| --- | --- | --- | --- |
| DIRECT | 0 | 0 | **0** |
| INDIRECT | 1（RV-7） | 2（UD-2, UD-9） | **3** |
| DESIGN_ONLY | 2（RV-8, RV-11） | 2（UD-3, UD-11） | **4** |
| NO_EVIDENCE | 8（RV-1 to RV-6, RV-9, RV-10） | 7（UD-1, UD-4 to UD-8, UD-10） | **15** |

| status | RV | UD | total |
| --- | --- | --- | --- |
| VERIFIED | 0 | 0 | **0** |
| PARTIAL | 1（RV-7） | 0 | **1** |
| UNVERIFIED | 2（RV-1, RV-8） | 11 | **13** |
| BLOCKED | 8（RV-2 to RV-6, RV-9 to RV-11） | 0 | **8** |

Note: the NO_EVIDENCE RV items are RV-1, RV-2, RV-3, RV-4, RV-5, RV-6, RV-9 and RV-10.

---

## 7. Test and CI coverage matrix

| area | existing evidence（file:line at baseline） | classification |
| --- | --- | --- |
| login | `apps/web/src/app/api/auth/login/route.test.ts:50`（429, 2 cases）, `:66`（200 + cookies）, `:88`（401）, `:104`（503）, `:118`（`Secure`）. No `Origin` / `Sec-Fetch-Site` case | partially covers related behaviour; **dedicated CSRF V-1 coverage missing** |
| registration | `apps/web/src/app/api/auth/register/__tests__/route.test.ts:52, 71`（3 cases）, `:89, 105` | partially covers related behaviour; **dedicated CSRF V-1 coverage missing** |
| logout | no route test for `apps/web/src/app/api/auth/logout/route.ts` found. UI: `apps/web/src/lib/auth/__tests__/AuthProvider.conciergeStorage.test.tsx:56-71` and `apps/web/src/lib/auth/__tests__/meRecoveryState.test.tsx:256` cover the **success** path only; the code ignores the response status（`apps/web/src/lib/auth/AuthProvider.tsx:197-213`, `apps/web/src/lib/api/auth.ts:37-45`）, so A-5 is not implemented | **dedicated CSRF V-1 coverage missing**（route and A-5） |
| concierge chat | `apps/web/src/app/api/concierge/chat/__tests__/route.test.ts:61, 82, 108, 157, 182, 202` | partially covers related behaviour; **dedicated CSRF V-1 coverage missing** |
| weekly Compass | `apps/web/src/app/api/compass/weekly/__tests__/route.test.ts:21, 39, 50` | partially covers related behaviour; **dedicated CSRF V-1 coverage missing** |
| `DELETE /api/users/me` | `apps/web/src/app/api/users/me/__tests__/route.test.ts:34`（same origin）, `:46, 56`（cross-origin / invalid → 403, no backend, no cookie）, `:66`（`Origin` absent → backend called）, `:78, 95`（cookie deletion only on 204） | **directly covers today's `isAllowedOrigin` contract**; partial for V-1. `:66-76` asserts the pre-V-1 behaviour that #3323 §4.3 says will be rewritten to 403（S-1 = A） |
| D0–D13 decision table | none | **dedicated CSRF V-1 coverage missing** |
| mode configuration, F-1 / F-2 / F-3 | none | **dedicated CSRF V-1 coverage missing** |
| OBSERVE vs ENFORCE | none | **dedicated CSRF V-1 coverage missing** |
| JSON-only and would-be `415` | route tests send only `application/json`（for example `apps/web/src/app/api/auth/login/route.test.ts:33`）. `apps/web/src/app/api/auth/login/route.ts:19-27` accepts urlencoded and multipart without a test | **dedicated CSRF V-1 coverage missing** |
| logging privacy | no server-logging test; `apps/web/src/lib/client/__tests__/logging.test.ts` is client-only | **dedicated CSRF V-1 coverage missing** |
| aggregation completeness and duplicates | `apps/web/src/lib/server/__tests__/bffFetch.refreshIsolation.test.ts:158`（refresh dedup, not counting） | **dedicated CSRF V-1 coverage missing** |
| evidence retention and durability | no test; workflows set no artifact retention | **cannot determine from inspected evidence** |
| recovery and effective-mode verification | none | **dedicated CSRF V-1 coverage missing** |
| browser E2E | `apps/web/playwright.config.ts:22-39` defines `chromium` and `webkit` only（no Firefox）; CI runs `apps/web/e2e/05_direction_flow.spec.ts` on Chromium only（`apps/web/package.json:22`, `.github/workflows/web-tests.yml:84`）; no CSRF spec in `apps/web/e2e/` | **dedicated CSRF V-1 coverage missing**; AC-3 also needs Firefox and Preview runs |

### 7.1 Workflow triggers and filters

| workflow | triggers（file:line） | path filter | relevance |
| --- | --- | --- | --- |
| `web-tests.yml`（`web-ci`） | `workflow_dispatch`; `push` to `develop`, `main`; `pull_request` to any branch（6-25） | `apps/web/**`, `packages/shared/**`, `package.json`, `pnpm-lock.yaml`, the workflow itself（11-16, 20-25） | runs vitest（`test:contract` 53-54, `test:cov` 140-142）, ESLint, `tsc`, guards（including `guard:no-next-public-in-server` 163-165, relevant to U-1a）, and the Chromium direction E2E（84）. **Does not run for docs-only PRs** |
| `backend-tests.yml` | `workflow_call`, `workflow_dispatch`（3-21） | — | backend only; no CSRF V-1 tests exist |
| `codeql.yml` | `pull_request` to `main`, `develop`; weekly `schedule`; `workflow_dispatch`（7-12） | — | static analysis only. **CodeQL success is not CSRF behavioural test success** |
| `deploy.yml.disabled` | would be `push` / `workflow_dispatch`（2-10） | — | disabled; calls the placeholder `scripts/deploy.sh` |

---

## 8. Conclusions

| category | items |
| --- | --- |
| **DESIGN APPROVED** | U-3 = A, U-4 = A, U-5 = B, U-6 = B and all earlier decisions; the contracts behind RV-1 to RV-11 and UD-1 to UD-11 |
| **SOURCE VERIFIED** | only existing, non-CSRF behaviour: cookie attributes and refresh（RV-7）, the server log helper（UD-2）, BFF retries and the request-id helper（UD-9）, today's `DELETE /api/users/me` `isAllowedOrigin` check |
| **TEST COVERAGE VERIFIED** | only existing behaviour: route contracts for the five AC-8 routes（except a logout route test）, refresh isolation, and today's `DELETE /api/users/me` contract. No CSRF V-1 behaviour |
| **IMPLEMENTATION NOT VERIFIED** | the CSRF guard, D0–D13, `WEB_CSRF_MODE`, F-1 / F-3, OBSERVE / ENFORCE, JSON-only `415`, A-5 logout failure, CSRF logging, aggregation（UD-1 to UD-3, UD-8 to UD-10）, effective-mode verification（RV-8） |
| **ENVIRONMENT VERIFICATION REQUIRED** | RV-2 to RV-6, RV-9, RV-10; platform log and artifact retention（UD-4, UD-6）; storage access（UD-5） |

### 8.1 Evidence gaps before each gate

**Before A-0 can produce a reviewable implementation PR**（design inputs needed）:

- G-A1: logging-extension and aggregation design with privacy validation（UD-1, UD-2, UD-9, UD-10）, including
  the log level in production（`serverLog` drops `info`）.
- G-A2: name for the would-be `415` record（UD-3）.
- G-A3: counting point relative to BFF retries（UD-9）.

**Before L4-O**:

- G-O1: all P-1 to P-15 evidence（#3329 §3.1）, including dedicated tests for every row of the coverage matrix
  marked "missing", a logout route test, A-5 tests, and Preview E2E in Chromium, WebKit **and Firefox**（the
  Playwright configuration has no Firefox project today）.
- G-O2: a recovery plan meeting P-13: RV-1 to RV-10 verified on a non-Production target, and RV-11 confirmed by
  Mother Ship.
- G-O3: an effective-mode verification procedure（RV-8）.
- G-O4: a monitoring and evidence-collection plan（#3330 §9）resolving UD-4 to UD-6 for the sources it relies on.

**Before L4-E**:

- G-E1: AC-8 counts from a working aggregation with completeness, duplicate and QA handling（UD-1, UD-8 to UD-10）.
- G-E2: durable, accessible supporting evidence with an export and integrity mechanism（UD-6, UD-7）.
- G-E3: all AC-1 to AC-12, then AC-13.

### 8.2 Source / contract observations

| # | observation | consequence |
| --- | --- | --- |
| O-1 | `apps/web/playwright.config.ts:22-39` has no Firefox project, while AC-3 and #3323 §8.6 require Firefox | the V-1 PR must add Firefox coverage or AC-3 cannot pass |
| O-2 | `serverLog` emits `info` / `debug` only outside production（`apps/web/src/lib/server/logging.ts:7, 20`） | instrumentation must not rely on `info` in production, or must change this behaviour under A-0 |
| O-3 | `getRequestId` trusts client-supplied `x-request-id`（`apps/web/src/lib/server/logging.ts:13-16`） | not acceptable as proof or dedup key under AG-4 |
| O-4 | logout and `DELETE /api/users/me` delete cookies with `Path` and `Max-Age` only, not through `authCookies.ts`（`apps/web/src/app/api/auth/logout/route.ts:9-10`, `apps/web/src/app/api/users/me/route.ts:55-62`） | recorded for RV-7; not a CSRF contract conflict |
| O-5 | #3323 §1 lists test counts "login 4, register 3, chat 6, compass weekly 3, `users/me` 5"; these match the number of plain `it(` calls, excluding `it.each`（login, register and `users/me` each have one `it.each` in addition） | counting-method note, not a contradiction; unchanged code since `c3642ca` |
| O-6 | the 1-hour platform log retention（#3325 §8.2）comes from #3320 §5 and was not re-verified here | treat as unverified until confirmed（UD-4） |
| O-7 | the Production smoke checklist（`docs/ops/production-smoke-checklist.md:23-32`）omits register, logout and compass weekly | it cannot serve as AC-10 evidence for all five routes as written |

No contradiction between the CSRF contracts and the current code was found: the contracts describe future behaviour,
and the code does not yet implement it.

---

## 9. Preserved decisions and open items

- **U-3 = A**, **U-4 = A**, **U-5 = B**, **U-6 = B**: preserved.
- **#3331 §5.2 interpretation**: restoring a deployment weaker than the current state（an `observe` or pre-V-1
  deployment）requires ER-1 to ER-5. Preserved.
- **RV-1 to RV-11** and **UD-1 to UD-11**: none is resolved by this audit.
- **"rollback by revert" reconciliation**（RV-11）: **OPEN**.
- **S-6, S-8 remainder, S-14**: **OPEN**.
- **A-7**: unchanged. The 14-day Class B deadline starts when the V-1 runtime implementation PR merges; it has not
  started, and this audit neither starts nor resets it.

---

## 10. STOP

```text
A-0  = NOT APPROVED
L4-O = NOT APPROVED
L4-E = NOT APPROVED
runtime code / API routes        UNCHANGED
authentication / cookies         UNCHANGED
environment variables            UNCHANGED（none read）
Vercel / Render configuration    UNCHANGED（not accessed）
Production API / logs            NOT ACCESSED
deployment / rollback            NONE
mode switching                   NONE
telemetry / storage / migrations NONE
tests                            NOT RUN; NOT MODIFIED
earlier CSRF records             NOT EDITED
PR merge                         NONE
```
