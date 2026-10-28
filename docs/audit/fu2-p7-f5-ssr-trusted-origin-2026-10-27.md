# FU-2-P7-F5: SSR Trusted Origin Hardening — Audit（2026-10-27）

## 1. Status

```text
RECORD TYPE   = audit-only（BLOCKED before behaviour change: the Production / Preview origin policy is unresolved）
BASELINE      = origin/develop@ec428c4（includes PR #3366）
CHANGED       = this document; one audit-only test file; regenerated call-graph inventory（line numbers）
UNCHANGED     = all application code, auth, cookies, routing, rate limits, recommendation, Premium, Mobile, Goshuin
PRODUCTION    = Vercel project metadata read（domains, protection mode）; env-var listing refused（403）; no values read,
                no traffic, no changes
FINAL STATUS  = PR for Mother Ship; environment policy decision required; STOP
```

Evidence labels: **Code**, **Test**（local test in this PR）, **Vercel**（project metadata via the Vercel API）,
**Docs**（Vercel documentation）, **Inferred**, **Unknown**.

## 2. Conclusion

1. **Six reachable SSR call sites forward credentials to an origin chosen by `resolveServerBaseUrlFromHeaders`.** The
   credentials are the Cookie header, which carries `access_token`, `refresh_token` and `concierge_anon_id`, plus, on
   two of them, `Authorization`. When `WEB_BASE_URL` / `PLAYWRIGHT_BASE_URL` is unset, the origin is
   `${x-forwarded-proto ?? "http"}://${x-forwarded-host ?? host}`.
   - **Code**: `resolveServerBaseUrl.ts:10-19`.
   - **Test**: all six send credentials to a malicious host.
2. **On Vercel the practical exposure is low（Inferred）.**
   - Vercel routes by `Host` to the project's own domains.
   - Vercel documents `x-forwarded-host` as identical to `host`, and `x-forwarded-proto` as `https` in production
     （Docs）.
   - The derived origin is therefore one of the project's own hosts, and the credentials are the requester's own.
   - The risk becomes real when either guarantee does not hold: a different host or proxy in front of the app, a
     non-Vercel runtime, or a platform change.
3. **A fail-closed fix needs a Production / Preview origin policy that this audit cannot establish（§6）.**
   - **Env-var listing:** the Vercel env-var listing returned **403**, so it is **Unknown** whether `WEB_BASE_URL` or
     the System Environment Variables（`VERCEL_*`）are present at runtime.
   - **Preview:** the Preview deployments are SSO-protected. Today's same-host self-fetch carries the visitor's Vercel
     SSO cookie inside the forwarded Cookie header（Inferred）. A policy that changes the Preview destination could
     break Preview SSR.
   - **Decision:** following the task rule, **no application behaviour was changed**. §7 gives the options and §8 the
     environment setup.
4. **The same pattern exists outside `resolveServerBaseUrl`:**
   - `billing.server.ts:21-25`（P4, Premium status）has its own host-derived origin, preferring `NEXT_PUBLIC_APP_URL`;
   - **Constraint:** it is a Premium surface, so it is inventoried here but out of scope for change.

## 3. Call-site and trust-boundary inventory（Code）

| # | call site | used by（reachable） | destination path | forwards | sensitivity |
| --- | --- | --- | --- | --- | --- |
| C1 | `lib/api/concierge.server.ts:7`（`getConciergeThreadServer`） | `shrines/[id]` with `ctx=concierge&tid`; `/mypage/history/[tid]` | own BFF `/api/concierge-threads/{tid}/` | whole page Cookie | **high**: JWT + anonymous ownership credential |
| C2 | `lib/api/concierge.server.ts:32`（`getConciergeThreadsServer`） | `shrines/[id]`（after C1） | own BFF `/api/concierge-threads/` | whole page Cookie | **high** |
| C3 | `lib/api/favorites.server.ts:12`（`getFavoritesServer`） | `/favorites`, `/mypage` | own BFF `/api/favorites/` | whole page Cookie | **high** |
| C4 | `lib/server/favorites.server.ts:52`（`getShrineFavoriteInitialState`） | `shrines/[id]`; only when `Authorization` / `access_token` / `refresh_token` is present | own BFF `/api/favorites/` | Cookie + `Authorization` | **high** |
| C5 | `lib/api/shrineMeaning.server.ts:55`（`fetchViaBff`） | `shrines/[id]`; the auth-context branch only（P2） | own BFF `/api/shrines/{id}/meaning/` | `cookies().toString()` | **high** |
| C6 | `app/shrines/resolve/page.tsx:21` | `/shrines/resolve?place_id=…` | own BFF `/api/places/resolve/`（POST） | whole page Cookie | **high** |
| C7 | `lib/api/favorites.server.ts:42`（`getShrineFavoriteStateServer`） | **unreferenced** | own BFF `/api/favorites/` | Cookie + `Authorization` | high if revived |
| N1 | `lib/api/shrines.server.ts:41`（fallback when no Backend public URL） | `shrines/[id]` | own BFF `/api/shrines/{id}/data/` | nothing | low（SSRF-shaped GET only） |
| N2 | `lib/api/publicGoshuins.server.ts:6` | `shrines/[id]`, `/shrines/[id]/goshuins` | own BFF `/api/public/goshuins` | nothing | low（Goshuin: no change） |
| N3 | `lib/api/shrines.list.server.ts:10` | **unreferenced**; also calls `resolveServerBaseUrl()` without `await`（latent bug） | — | nothing | none |
| X1 | `lib/api/billing.server.ts:21-25`（own logic, not `resolveServerBaseUrl`） | `shrines/[id]`, `/mypage` | own BFF `/api/billings/status/` | Cookie | **high**（Premium; out of scope） |

All destinations are the app's own BFF routes. The BFF keeps JWT refresh（`bffFetchWithAuthFromReq`）and then calls the
configured Django origin（`getDjangoOrigin()`）, which is not header-derived. **The only header-derived hop is SSR →
BFF.** The impact therefore sits on credentials in transit on that hop.

The resolver's precedence is the same for every caller（Code, Test）:

1. `WEB_BASE_URL`, then `PLAYWRIGHT_BASE_URL`;
2. the request's `x-forwarded-host ?? host`, with `x-forwarded-proto ?? "http"`;
3. `VERCEL_PROJECT_PRODUCTION_URL`;
4. `VERCEL_URL`;
5. `http://localhost:${PORT ?? 3000}`.

The `VERCEL_*` entries only apply when no host header exists.

## 4. Environment contract（what is and is not known）

| environment | trusted Web origin today | evidence |
| --- | --- | --- |
| Production | the project domains are `jinja-app-web.vercel.app`, `jinja-app-web-ejb0515-1459s-projects.vercel.app` and `jinja-app-web-git-develop-ejb0515-1459s-projects.vercel.app`; **no custom domain** | Vercel（project metadata） |
| Production `WEB_BASE_URL` / `NEXT_PUBLIC_APP_URL` / `NEXT_PUBLIC_SITE_URL` | **Unknown**: the env-var listing was refused（403）. Values were not and must not be read | Vercel |
| System env vars at runtime（`VERCEL`, `VERCEL_ENV`, `VERCEL_URL`, `VERCEL_BRANCH_URL`, `VERCEL_PROJECT_PRODUCTION_URL`） | **Unknown**: present only when "Automatically expose System Environment Variables" is on（Docs: `VERCEL=1` signals it）. FU-2-P2's production HMAC check was INCONCLUSIVE for the same reason | Docs; earlier audit |
| Deployment protection | SSO protection on all deployments **except custom domains**. This project has none, so every listed domain falls under the protection rule; whether the production alias is exempt is **Unknown** | Vercel |
| Preview | Each deployment URL and branch alias is its own host. The self-fetch goes to the same host and forwards the browser's Cookie header, which includes Vercel's SSO cookie when protection applies（**Inferred**） | Code + Vercel |
| Development | no `WEB_BASE_URL`, so the request host is used, e.g. `http://localhost:3000`; the E2E runner sets `PLAYWRIGHT_BASE_URL` | Code |
| Header trust on Vercel | Docs: `x-forwarded-host` "is identical to the host header"; `x-forwarded-proto` is `https` in production. Whether a client-supplied `x-forwarded-host` is overwritten was **not tested**（no production traffic allowed） | Docs |

## 5. Security assessment

| id | severity | finding | evidence |
| --- | --- | --- | --- |
| F5-1 | **Low**（Vercel） / **High** off-platform | Credentials go to a request-derived origin when no trusted origin is configured | Code; Test（12 `it.fails` + 12 pinned cases） |
| F5-2 | Low | Protocol downgrade: a missing or `http` `x-forwarded-proto` makes SSR send credentials over plain HTTP to that host | Code; Test |
| F5-3 | Low | `VERCEL_PROJECT_PRODUCTION_URL` / `VERCEL_URL` are consulted only after the request host, so they never constrain it | Code; Test |
| F5-4 | Info | The same pattern exists in `billing.server.ts`（P4, Premium）; out of scope for change here | Code |
| F5-5 | Info | `shrines.list.server.ts` misses an `await`（URL becomes `[object Promise]…`）; the function is unreferenced | Code |

Not affected:

- the BFF → Django hop, which uses the configured Django origin;
- anonymous favorites and meaning, which forward nothing without an auth cookie;
- N1 and N2, which carry no credentials.

Anonymous Concierge still forwards `concierge_anon_id`（Test）, which is required for ownership（FU-2-P7 §5）.

**Counter-evidence:** on Vercel, as documented, a malicious `Host` does not reach this deployment and
`x-forwarded-host` equals `host`. F5-1 is a defence-in-depth gap rather than a demonstrated exploit. **Blind spot:**
the overwrite behaviour was not verified against the live platform.

## 6. Why implementation is blocked

A correct fix must:

- send sensitive SSR requests only to a trusted origin, without a silent fallback to header-derived ones;
- require HTTPS in production;
- keep Preview, local development, JWT refresh through the BFF, and anonymous ownership working.

Each option needs a fact or decision this audit does not have:

1. **Which origin is trusted in Production?** `WEB_BASE_URL`, `VERCEL_PROJECT_PRODUCTION_URL` or a fixed domain. Whether
   either variable exists at runtime is Unknown（403）, and there is no custom domain yet.
2. **Preview behaviour.**
   - Routing Preview SSR to a configured origin, e.g. production, would send preview cookies across environments and
     read production data.
   - Routing it to `VERCEL_URL`, the deployment URL, may differ from the branch alias the visitor used; the SSO cookie
     scope is Inferred.
   - Allowing "the request host if it is one of `VERCEL_URL` / `VERCEL_BRANCH_URL`" depends on the system variables
     being exposed.
3. **Missing configuration.** "Fail closed" means the sensitive SSR sections render as signed-out or empty. If
   Production lacks the variable, Concierge history, favorites, place resolution and the authenticated shrine meaning
   degrade immediately after deploy.

## 7. Options for Mother Ship（none implemented）

| option | rule for credential-forwarding SSR（C1–C6） | Production need | Preview | Dev | risk |
| --- | --- | --- | --- | --- | --- |
| **A. Explicit origin（recommended）** | Use `WEB_BASE_URL` only. When `VERCEL_ENV=production`, require `https:` and refuse any other value; when it is missing, skip the fetch（sections degrade） | set `WEB_BASE_URL=https://jinja-app-web.vercel.app`（or the future custom domain） | allow the request host only if it equals `VERCEL_URL` or `VERCEL_BRANCH_URL`; otherwise skip | `http://localhost:*` / `127.0.0.1` when `NODE_ENV !== "production"` | needs `VERCEL_ENV` / `VERCEL_URL` / `VERCEL_BRANCH_URL` exposed; a missing var is visible as degraded sections |
| B. Host allowlist | Request host accepted only if it is in an allowlist built from `WEB_BASE_URL`, `VERCEL_PROJECT_PRODUCTION_URL`, `VERCEL_URL` and `VERCEL_BRANCH_URL`, plus an optional `TRUSTED_WEB_HOSTS`（non-secret） | the same exposure as A; no new value if the system vars are exposed | works for branch aliases | localhost rule | larger trusted set; aliases must be listed |
| C. Remove the self-hop for C1–C6 | SSR calls Django directly with the needed credentials | no Web origin needed | — | — | **rejected** for P7（FU-2-P7 §8: refresh cannot be persisted in SSR; credential handling duplicated） |
| D. Accept the risk on Vercel | Document that host trust relies on Vercel and set `WEB_BASE_URL` in Production only | set `WEB_BASE_URL` | unchanged | unchanged | off-platform exposure remains; no code change |

Constraints for any implementation:

- one shared resolver for C1–C6 that never falls back to request headers in production;
- no change to the BFF, cookies or JWT refresh;
- `tid` / ids stay validated（FU-2-P7-B）;
- no values are logged;
- the tests in §9 flip from `it.fails` to `it`.

## 8. Environment setup instructions（for Option A or D; Mother Ship / owner action）

1. In the Vercel project `jinja-app-web` → Settings → Environment Variables, add `WEB_BASE_URL` for **Production**
   only, set to the canonical HTTPS origin. Today that is `https://jinja-app-web.vercel.app`; use the custom domain if
   one is added. It is not a secret.
2. In Settings → Environment Variables, confirm that **"Automatically expose System Environment Variables"** is
   enabled. This provides `VERCEL`, `VERCEL_ENV`, `VERCEL_URL`, `VERCEL_BRANCH_URL` and
   `VERCEL_PROJECT_PRODUCTION_URL`, and is also the precondition for FU-2-P2 signing（`VERCEL=1`）.
3. Do **not** set `WEB_BASE_URL` for Preview to the production origin, because Preview cookies would go to Production.
4. Local development needs nothing. `PLAYWRIGHT_BASE_URL` stays the E2E override.
5. After the change, verify through the existing logs rather than synthetic traffic: there should be no
   `GET_CONCIERGE_THREAD_FAILED` increase, and favorites / history still render for a QA account.

## 9. Tests（local only）

`apps/web/src/lib/server/__tests__/resolveServerBaseUrl.f5audit.test.ts`: **29 passed, 12 expected fail**.

- **Resolver precedence:** `WEB_BASE_URL` wins; `x-forwarded-host` beats `host`; the `http` default and a downgraded
  `x-forwarded-proto` are followed; `VERCEL_*` are not consulted when a host header is present.
- **Malicious headers:** for each of C1–C6, with a malicious `x-forwarded-host` and with a malicious `host`:
  - current behaviour pinned: credentials sent to that host;
  - desired property as `it.fails`: no credentials to an untrusted host;
  - with `WEB_BASE_URL`, credentials stay on the configured origin.
- **Anonymous visitor:** favorites and meaning send nothing; Concierge forwards only `concierge_anon_id`.

Other checks:

- `tsc --noEmit` exit 0; ESLint clean;
- `pnpm audit:bff-identity:check` RECONCILED after regenerating the inventory（line numbers only）.

Not covered here, because they belong to the eventual implementation:

- Production / Preview / Development routing under a chosen policy;
- missing-configuration fail-closed behaviour.

## 10. Blind spots

- **Env-var state:** runtime env-var presence is Unknown（403）; no values were read.
- **Vercel header handling:** whether Vercel overwrites a client-supplied `x-forwarded-host` was not tested, since no
  production traffic is allowed.
- **SSO scope:** whether the production alias is exempt from SSO protection, and how far the SSO cookie reaches on
  Preview, are Inferred.
- **`billing.server.ts`:** P4 is excluded by the Premium constraint and needs its own decision.

## 11. Follow-up: Preview runtime verification（2026-10-27）

See `fu2-p7-f5-preview-runtime-env-verification-2026-10-27.md`. Results:

- `VERCEL_ENV`, `VERCEL_URL` and `VERCEL_BRANCH_URL` at runtime are **UNVERIFIED**: no existing signal, and no
  diagnostic code was added;
- the request host equals the Preview's branch-alias metadata;
- on the SSO-protected Preview, a cookie-forwarding SSR self-fetch passes, and a cookie-less one receives HTML（public
  goshuins rendered empty）. This confirms the §4 / §6 assumption that Preview SSR depends on same-host cookie
  forwarding.

## 12. Follow-up: Preview runtime probe（2026-10-28）

See `fu2-p7-f5-preview-env-probe-2026-10-28.md`. Results:

- on Preview, `VERCEL_ENV === "preview"`, and `VERCEL_URL` / `VERCEL_BRANCH_URL` are present, valid hosts and equal the
  request host for the deployment URL and the branch alias respectively（PASS）;
- the Preview part of the allowlist design is supported by runtime data;
- Production remains UNVERIFIED by design.

