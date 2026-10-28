# FU-2-P7-F5: Preview Runtime Environment Verification（2026-10-27）

## 1. Status

```text
RECORD TYPE   = verification record（audit-only）
BASELINE      = origin/develop@1af2889（includes PR #3367）
SUBJECT       = Preview deployment dpl_3VJjpDwSxmUDmfGT8dBkq4CDW2Cx（branch fix/fu2-p7-f5-ssr-trusted-origin,
                commit d939270 = the code merged as #3367; target = preview）
METHOD        = Vercel deployment metadata（read）; one anonymous GET of an existing SSR page through Vercel's
                access mechanism for protected deployments; existing runtime logs（read）
NOT DONE      = no instrumentation, no diagnostic endpoint, no env-var listing（403 earlier）, no value read,
                no Production change, no change to origin resolution
RESULT        = items 1-3 UNVERIFIED; item 4 partially verified（metadata only）; item 5 verified, with a degradation found
FINAL STATUS  = STOP; merge is Mother Ship's decision
```

Rules followed:

- no environment-variable value, cookie, JWT, `Authorization` or share-link token appears in this document or in the PR;
- host names below are deployment metadata returned by the Vercel API, not environment-variable values.

## 2. Results per item

| # | item | verdict | evidence |
| --- | --- | --- | --- |
| 1 | `VERCEL_ENV` indicates Preview at runtime | **UNVERIFIED** | No existing code reads or logs `VERCEL_ENV`（repository grep: the only `VERCEL*` reads are `VERCEL`, `VERCEL_URL` and `VERCEL_PROJECT_PRODUCTION_URL`）. The deployment's metadata target is `null`, which means preview, and the runtime-log record says `environment=preview`. Both are platform metadata, not the runtime variable |
| 2 | `VERCEL_URL` exists at runtime | **UNVERIFIED** | It is read only in `resolveServerBaseUrl.ts:25`, which is reached only without a host header, and in `lib/url.ts:22`（`getAppUrl`, unreferenced）. No existing response or log reflects it |
| 3 | `VERCEL_BRANCH_URL` exists at runtime | **UNVERIFIED** | Not referenced anywhere in the code |
| 4 | host information matches the Preview metadata | **PARTIAL** | Metadata: deployment URL `jinja-app-37nxqbzgb-…vercel.app`, one branch alias `jinja-app-web-git-fix-fu2-p7-f5-s-0454c3-…vercel.app`. The request's `domain` in the runtime log and the host of the SSR self-fetch URL（`[publicGoshuins.server]` log）both equal the **branch alias**, i.e. the request host. Whether `VERCEL_URL` / `VERCEL_BRANCH_URL` equal these hosts at runtime is **UNVERIFIED**（items 2–3） |
| 5 | existing SSR works on the SSO-protected Preview | **VERIFIED, with degradation** | §3 |

Items 1–3 cannot be verified within the constraints:

- the values must not be logged, returned or inferred;
- no diagnostic API may be added;
- the origin logic must not change;
- no existing runtime signal reports their presence.

A presence-only check would need new code. One way is a temporary server log of booleans（"present", "equals the
request host"）on a non-merged branch's Preview. That is a diagnostic change, so it is **not done** and left for
Mother Ship to authorise（§5）.

## 3. SSO behaviour on Preview（item 5）

The test was one anonymous request（no app login）to `GET /shrines/1` on the branch alias, made through Vercel's access
mechanism for protected deployments（a temporary share link, created by the tool, that expires ≤ 23 h; the token is not
recorded）.

| SSR call | forwards the Cookie header? | result on the SSO-protected Preview | evidence |
| --- | --- | --- | --- |
| page render | — | **200**; the shrine page rendered（title = the shrine's name） | response |
| shrine detail（`getShrineDetailServer`） | no | succeeded（the page has the shrine） | response. Consistent with a configured Backend public URL, i.e. no SSR → BFF self-hop（**Inferred**; the env presence was not read） |
| billing status（`billing.server.ts`, X1） | **yes** | the self-fetch reached the BFF route `/api/billings/status/`; upstream **200**（`hasCookieHeader: true`, no auth cookies） | runtime log `[BFF_UPSTREAM]` |
| public goshuins（`publicGoshuins.server.ts`, N2） | **no** | **failed**: the self-fetch to the branch-alias host got HTML instead of JSON（"Unexpected token '<', "<!DOCTYPE"…"）, and the section rendered empty（`publicGoshuinsPreview: []`） | runtime log `[publicGoshuins.server] fetch failed` |

Interpretation:

- **Fact:** a self-fetch that forwards the browser Cookie passes on Preview, and one that forwards no Cookie receives
  HTML.
- **Inferred:** the HTML is the Vercel Authentication page. The forwarded Cookie carries the visitor's Vercel
  access cookie, here from the share link, so cookie-forwarding self-fetches pass SSO and cookie-less self-fetches do
  not. This confirms, on a live Preview, the assumption in `fu2-p7-f5-ssr-trusted-origin-2026-10-27.md` §4 / §6.
- **Consequence for the F5 policy:**
  - Preview SSR currently depends on sending the visitor's cookies, including the Vercel access cookie, to the
    request host.
  - Pointing Preview SSR at any other origin（the production origin, or `VERCEL_URL` when the visitor used the branch
    alias）would carry a cookie scoped to a different host, or none, and the self-fetch would hit SSO.
  - Option A's "request host only if it equals `VERCEL_URL` or `VERCEL_BRANCH_URL`" keeps the same host, so SSO keeps
    working. It still needs items 2–3 to be true at runtime.
- **Pre-existing degradation, not caused by this work:** on SSO-protected Previews the public-goshuins section
  （cookie-less self-fetch）is always empty. Production is not affected in this way if the production alias is
  unprotected（**Unknown**）. Goshuin is out of scope for change; this is recorded only.

## 4. What was not done

- No environment variable was listed, decrypted or printed. No Production setting, alias or protection setting was
  changed.
- No app login: authenticated Preview SSR（Concierge history, favorites）was **not** exercised. Only cookie forwarding
  through SSO was observed, via billing.
- No synthetic load: one page request.
- Side effect: the Vercel access tool may have created a temporary share link on that Preview deployment. Vercel
  expires it within 23 h; it was not shared or recorded.

## 5. Options to close items 1–3（Mother Ship decision; none implemented）

| option | how | constraint impact |
| --- | --- | --- |
| a. Owner checks the dashboard / CLI | Owner runs `vercel env ls` or opens Settings → Environment Variables and confirms "Automatically expose System Environment Variables". This shows configuration, not runtime presence | none; no runtime proof |
| b. Temporary presence log on a throwaway Preview | Log only booleans（`VERCEL_ENV === "preview"`, `VERCEL_URL` present / equals the deployment host, `VERCEL_BRANCH_URL` present / equals the alias）in one SSR path, on a branch never merged; delete it afterwards | needs explicit authorisation: diagnostic code, although it outputs no values |
| c. Verify through the F5 implementation | Implement Option A with fail-closed behaviour and tests; verify on its own Preview that the concierge / favorites sections render for a QA login | changes app behaviour: a separate PR |

## 6. Tests

- **No code or test change.** No code fact changed. The resolver behaviour is already pinned by
  `apps/web/src/lib/server/__tests__/resolveServerBaseUrl.f5audit.test.ts`（PR #3367）.
- The live Preview observations above are not reproducible as unit tests: they depend on Vercel Authentication.
