# Web BFF Origin Verification Gate — Preview / Production（2026-10-23）

## 1. Status

```text
SCOPE                          = read-only investigation + documentation
VERIFIES                       = #3319 §4.4 / §11.1 item 3（S-8）: does req.nextUrl.origin equal the browser-visible origin?
GATE RESULT                    = NOT PASSED — BLOCKED on Vercel（§5）; local Next.js harness shows the assumption fails outside Vercel（§6）
runtime / BFF / cookies / auth = UNCHANGED
CSRF enforcement               = NOT IMPLEMENTED
production settings / secrets  = NOT TOUCHED; no permission error bypassed
requests to Vercel deployments = NONE SUCCEEDED（network policy denied every *.vercel.app host）
Mother Ship policy             = NOT DECIDED（S-1 / S-3 / S-9 / S-11 options only）
FINAL STATUS                   = STOP
```

- Base: `origin/develop@c9a97bc`, which includes the merged #3319 contract
  `docs/audit/web-bff-csrf-hardening-contract-2026-10-23.md`.
- Labels:
  - **Observed（Vercel metadata）** = returned by the Vercel API for this project, read-only.
  - **Observed（local）** = measured in this session on a scratch Next.js 16.3.8 harness or a local mock,
    outside the repository.
  - **Code** = read in source: this repository, or the installed `next@16.3.8` package.
  - **Inference** = reasoned, not executed.
  - **NOT_VERIFIED** = needs access this session did not have.
- No secret, token, cookie value, environment value or protection-bypass credential was read or used.

---

## 2. What the contract needs

From #3319:

- §4.4: `req.nextUrl.origin` must equal the browser-visible origin, including `https`, on every domain that
  serves the app.
- §11.1 item 3（S-8）: this must be checked on a non-production deployment, and the production domain and its
  subdomains must be known（T9）, before implementation.

---

## 3. Deployment and domain inventory（Observed, Vercel metadata）

| item | value |
| --- | --- |
| project | `jinja-app-web`（`prj_odAjGXc6alMlAGSx46q4RQ9EBrjp`）, framework `nextjs`, Node 24.x |
| production branch | `develop`. Latest production deployment `dpl_HrdkkKQsBT4F8wdBfxtK2DFpiJXW` at `c9a97bc`（#3319 merge）, READY |
| project domains（the full list） | `jinja-app-web.vercel.app`（verified, no redirect）. **No custom domain** |
| production aliases | `jinja-app-web.vercel.app`, `jinja-app-web-ejb0515-1459s-projects.vercel.app`, `jinja-app-web-git-develop-ejb0515-1459s-projects.vercel.app` |
| preview deployments | one per pushed branch, e.g. `jinja-app-47cxlku9w-ejb0515-1459s-projects.vercel.app`, branch alias `jinja-app-web-git-audit-web-bff-c-3b3af8-ejb0515-1459s-projects.vercel.app`（#3319 rev 2） |
| deployment protection | `ssoProtection: { enabled: true, deploymentType: "all_except_custom_domains" }`; password protection off; trusted IPs off |
| backend origin（from #3318） | `jinja-backend.onrender.com` |

**Browser-visible origins.** For each host, the origin is `https://<host>`. This is inference: `.app` and
Vercel deployments are HTTPS-only. Which of these hosts an unauthenticated browser can actually open
depends on how "all except custom domains" treats the project's own `vercel.app` domain. That is
**NOT_VERIFIED**（§5）.

---

## 4. Domain and same-site sibling inventory

| host | public suffix | site（registrable domain） | evidence |
| --- | --- | --- | --- |
| `jinja-app-web.vercel.app` | `vercel.app` | `jinja-app-web.vercel.app` | Observed（local）: `publicsuffixlist` 1.1.2.20261021, bundled list, no network |
| `jinja-app-web-git-develop-ejb0515-1459s-projects.vercel.app` | `vercel.app` | itself | same |
| `jinja-app-8ggf0favc-ejb0515-1459s-projects.vercel.app`（a deployment URL） | `vercel.app` | itself | same |
| any other project, e.g. `evil-project.vercel.app` | `vercel.app` | itself | same |
| `jinja-backend.onrender.com` | `onrender.com` | itself | same |

- Because `vercel.app` is a public suffix, **every `*.vercel.app` host is its own site**:
  - production, the other production aliases and every preview are **cross-site to each other**;
  - any other Vercel customer's app is cross-site, too.
- **Inference:** with no custom domain, there is **no known same-site sibling origin** today. Threat T9 and the
  Class B same-site exposure（#3319 §4.8）have no reachable origin under the current domain set.
- This changes as soon as a custom domain is added. Every subdomain of that domain, including ones served
  by other services, becomes same-site.
- Browsers ship their own copy of the Public Suffix List; that Chromium / WebKit / Firefox treat `vercel.app`
  this way was **not measured** here（Inference from the list）.

---

## 5. Access to the deployments — blocked

| attempt | result | evidence |
| --- | --- | --- |
| HTTPS GET（headers only, no cookie, no auth）to production `/mypage` and to two preview hosts | **every CONNECT to `*.vercel.app` refused by this session's network gateway（403）** | Observed（local）: agent proxy status, `connect_rejected` for each host |
| browser tests on any deployment | not possible for the same reason | — |
| preview access even with network allowed | previews are under Vercel SSO protection; an unauthenticated browser would get the Vercel login | Observed（Vercel metadata）; effect NOT_VERIFIED |
| a protection bypass（automation secret, share link） | **not attempted**: it would need a secret or a protection change | constraint |
| production runtime logs as indirect evidence | the Hobby plan keeps 1 hour; MCP log records carry no status codes | Observed（Vercel API 400 message） |
| a safe diagnostic endpoint in the deployed app | **none exists**. No GET route handler returns `nextUrl.origin` or `req.url`. The only routes that use `nextUrl.origin` are `POST /api/billings/checkout` / `portal`（create Stripe sessions）and `DELETE /api/users/me`（destructive）. The middleware redirect uses a **relative** `Location`（Observed（local）, §6）, so it reveals nothing | Code: `apps/web/src/app/api/**`; `apps/web/middleware.ts` |

**Blocker:** without network access to `*.vercel.app` and an authorized way past SSO on previews, the
deployed `req.nextUrl.origin` cannot be observed. Running a non-mutating check would also need a diagnostic
route in a deployed build, which is a runtime change.

---

## 6. Local harness: how Next.js 16.3.8 computes `nextUrl.origin`

**Harness:** a scratch Next.js app outside the repository, on `next@16.3.8`（the version pinned in
`apps/web/package.json`）. It has:

- one route handler `/api/origin-probe`（GET / POST）that **returns** `req.nextUrl.origin`, `new URL(req.url)`,
  `Host`, `X-Forwarded-*`, `Origin` and `Sec-Fetch-Site`, and changes nothing;
- a `middleware.js` with the same redirect shape as `apps/web/middleware.ts`.

The real app was **not** run.

### 6.1 Origin comparison matrix（Observed, local）

| # | server | request | `nextUrl.origin` | browser / request `Origin` | match |
| --- | --- | --- | --- | --- | --- |
| H1 | `next start -p 4401`（default hostname） | curl, `Host: 127.0.0.1:4401` | `http://localhost:4401` | — | — |
| H2 | same | `Host: jinja-app-web.vercel.app` | `http://localhost:4401` | — | Host **ignored** |
| H3 | same | `Host: jinja-app-web.vercel.app`, `X-Forwarded-Proto: https` | `https://localhost:4401` | — | only the scheme follows the proxy |
| H4 | same | `Host: internal`, `X-Forwarded-Host: jinja-app-web.vercel.app`, `X-Forwarded-Proto: https` | `https://localhost:4401` | — | `X-Forwarded-Host` **ignored** |
| H5 | same | curl POST, `Origin: https://jinja-app-web.vercel.app`, as H3 | `https://localhost:4401` | `https://jinja-app-web.vercel.app` | **✗** |
| H6 | middleware on `/mypage`, any of the above | — | `http(s)://localhost:4401`; `Location: /login?next=%2Fmypage`（relative） | — | — |
| B1 | `next start -p 4403`（default） | Chromium page `http://localhost:4403`, same-origin `fetch` POST | `http://localhost:4403` | `http://localhost:4403`, `Sec-Fetch-Site: same-origin` | ✓ |
| B2 | same | Chromium page `http://127.0.0.1:4403` | `http://localhost:4403` | `http://127.0.0.1:4403`, `same-origin` | **✗** |
| B3 | `next start -p 4402 -H 0.0.0.0` | Chromium page `http://localhost:4402` | `http://0.0.0.0:4402` | `http://localhost:4402`, `same-origin` | **✗** |
| B4 | same | Chromium page `http://127.0.0.1:4402` | `http://0.0.0.0:4402` | `http://127.0.0.1:4402`, `same-origin` | **✗** |
| B5 | `next dev -p 4404 -H 0.0.0.0`（the shape of `apps/web/Dockerfile.frontend`） | Chromium page `http://localhost:4404` | `http://0.0.0.0:4404` | `http://localhost:4404`, `same-origin` | **✗** |
| B6 | same | Chromium page `http://127.0.0.1:4404` | `http://0.0.0.0:4404` | `http://127.0.0.1:4404`, `same-origin` | **✗** |

Browser: Chromium 141.0.7390.37 from `/opt/pw-browsers`.

### 6.2 Why（Code, `next@16.3.8`）

- `dist/server/lib/router-utils/resolve-routes.js:115-118`, used by `next start` / `next dev`:
  - with `experimental.trustHostHeader`, `initURL = https://<Host><url>`;
  - else, with a port, `initURL = <proto>://<hostname or "localhost">:<port><url>`;
  - else, the relative `req.url`.

  `proto` comes from the TLS socket or `X-Forwarded-Proto`.
- `dist/server/next-server.js` `attachRequestMeta`（around lines 1278-1288）: the same rule, with
  `fetchHostname` and `port`. With neither, and without `trustHostHeader`, `initURL` stays relative.
- `dist/server/web/spec-extension/adapters/next-request.js:89-103`: a route handler's `NextRequest` URL is
  `new URL(request.url, initURL)`. If `initURL` is not absolute, the base is the dummy `http://n`.
- `dist/server/lib/start-server.js:288-296`: `next start` sets `__NEXT_PRIVATE_ORIGIN` to
  `<proto>://<hostname>:<port>`.

**Inference:**

- On `next start` and `next dev`, `req.nextUrl.origin` is the **bind address**, not the browser-visible origin.
- The comparison `Origin === req.nextUrl.origin`（#3319 §4.2 R4 / R6 / R7, and today's
  `DELETE /api/users/me`）works only when the browser happens to use exactly that bind address.
- On Vercel the platform builds the request differently. Which branch applies there — an absolute URL from
  the platform, `trustHostHeader`, or the `http://n` fallback — **cannot be determined from this source and
  is NOT_VERIFIED**.

### 6.3 Consequence for code that exists today（Inference）

`DELETE /api/users/me` already compares `Origin` with `req.nextUrl.origin`. Under the repository's Docker
frontend（`next dev -H 0.0.0.0`, `apps/web/Dockerfile.frontend:14`）, the B5 / B6 rows mean a browser-initiated
account deletion would get **403**. Under `next dev` on `localhost:3000`（B1 shape）it would work. Production
behaviour on Vercel is NOT_VERIFIED. The real app was not run.

---

## 7. Browser verification（item 7）

| browser | available here | result |
| --- | --- | --- |
| Chromium 141.0.7390.37 | yes（pre-installed） | same-origin `fetch` POST sends `Origin` = page origin and `Sec-Fetch-Site: same-origin`（B1–B6）. Earlier #3319 mock rows unchanged |
| WebKit | **no**: not installed, and installing Playwright browsers is not permitted in this environment | NOT_VERIFIED |
| Firefox | **no**: same | NOT_VERIFIED |

---

## 8. Unverified assumptions

| # | assumption | blocking? |
| --- | --- | --- |
| U-1 | on Vercel, `req.nextUrl.origin` in a **route handler** equals `https://<host the browser used>` for every serving host（production aliases and previews） | **yes**（S-3, S-8） |
| U-2 | which production aliases are reachable without Vercel SSO under `all_except_custom_domains` | yes（the set of browser-visible origins） |
| U-3 | Vercel forwards a correct `X-Forwarded-Proto` / `Host` to the function | yes, if S-3 uses them |
| U-4 | WebKit / Firefox send `Origin` + `Sec-Fetch-Site: same-origin` on same-origin POSTs, and `Origin` on cross-site POSTs | yes for S-1 and S-9 confidence |
| U-5 | browsers treat `vercel.app` as a public suffix（PSL copy in each browser） | no today（§4 relies on the list） |
| U-6 | no custom domain is planned | yes for S-11 durability |
| U-7 | the deployed build equals `develop` for the code paths involved | partly observed: the production deployment's commit is `c9a97bc` |

---

## 9. Implications and options（not decisions）

### S-3 — how the expected origin is derived

| option | evidence | risk |
| --- | --- | --- |
| S-3a `req.nextUrl.origin` only | **fails** off-Vercel（§6.1 H5, B2–B6）; unknown on Vercel（U-1） | if U-1 is false, every legitimate POST in scope gets 403 |
| S-3b explicit allowlist from configuration（per environment: the production origin, preview origins, local dev origins） | no dependence on how Next computes the URL | previews have per-deployment hosts. The list would have to be built from Vercel's system environment variables for the deployment and branch URL; their exact values are NOT_VERIFIED here. Stale lists break deploys |
| S-3c compare `Origin` with the request's `Host` / `X-Forwarded-Host` | matches how browsers address the server | depends on the proxy setting those headers correctly（U-3）. `Host` is forgeable only by non-browser clients, which carry no victim cookies（Inference） |
| S-3d **make `Sec-Fetch-Site: same-origin` authoritative**. Change #3319 R6 so that a present `Sec-Fetch-Site: same-origin` allows regardless of the expected origin. Use the expected origin only when Fetch Metadata is absent（R7–R10） | removes the S-3 dependency for every browser that sends Fetch Metadata（all current browser rows here） | the R6 consistency check is lost; older browsers still need S-3a / b / c. This is a contract change to #3319 R6 |

**Options to evaluate:** S-3d combined with S-3b or S-3c for the fallback rows. S-3a alone is contradicted by
the local evidence. This is not a decision.

### S-11 — accept the Class B same-site residual risk?

| option | basis |
| --- | --- |
| S-11a accept now, with a **trigger**: re-open when any custom domain or subdomain is added to the project, or when the app is served from a shared registrable domain | §4: no same-site sibling exists under `vercel.app` today（Inference from the PSL） |
| S-11b do not accept; pull S-7（Class B）into V-1 | protects against a future custom domain without relying on a trigger |
| S-11c accept with a hard date for S-7 | — |

**Options to evaluate:** S-11a, with the trigger written into the release checklist and the #3319 S-10
inventory guard. Not a decision.

### S-1 and S-9

- **S-1**（both headers absent）: no new data. Every browser POST observed here carried both headers. WebKit
  and Firefox remain unmeasured（U-4）.
- **S-9**（`Sec-Fetch-Site: none`）: no new data. It did not occur on any POST here.
- Both remain as framed in #3319.

---

## 10. What would unblock S-8（for Mother Ship / the owner）

1. **Network:** allow `jinja-app-web.vercel.app` and the preview host pattern in this environment's network
   settings. Only the owner can change this.
2. **Preview access under SSO:** an authorized path chosen by the owner, such as testing from the owner's
   logged-in browser. This session will not create share links or use automation-bypass secrets on its own.
3. **Observation point:** either
   - approve a temporary, read-only diagnostic route on a **preview-only** branch that returns
     `req.nextUrl.origin`, `Host`, `X-Forwarded-*`, `Origin` and `Sec-Fetch-Site`（a runtime change; needs approval）;
     or
   - accept S-3d, which makes the S-3 dependency much smaller.
4. **Browsers:** a WebKit and Firefox run, on a machine where they are installed.

---

## 11. Decision table（remaining）

| id | decision | status after this record |
| --- | --- | --- |
| S-8 | origin verification on a non-production deployment | **blocked**（§5, §10） |
| S-3 | expected-origin derivation | open; options §9. Local evidence against S-3a |
| S-12（new） | change #3319 R6 so that `Sec-Fetch-Site: same-origin` is authoritative（S-3d） | open |
| S-11 | Class B residual risk | open; options §9; today no same-site sibling exists（Inference） |
| S-13（new） | approve a temporary preview-only diagnostic route | open |
| S-14（new） | the existing `DELETE /api/users/me` origin check under Docker / self-hosting（§6.3） | open; same root cause as S-3 |
| S-1, S-9 | — | unchanged from #3319 |

---

## 12. Not done

```text
runtime / BFF / frontend / backend / mobile code   UNCHANGED
CSRF enforcement                                   NOT IMPLEMENTED
cookies / auth / tokens                            UNCHANGED
models / migrations / database                     UNCHANGED
production settings, protection, env vars          NOT TOUCHED
requests to Vercel deployments                     none reached them（network policy）
scratch harness（Next.js app, Chromium scripts）    outside the repository; not committed
```
