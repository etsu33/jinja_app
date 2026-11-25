# FU-2-P7-F5: Preview Runtime Environment Probe（2026-10-28）

## 1. Status

```text
RECORD TYPE   = sanitized verification result（audit-only; no diagnostic code in this PR）
BASELINE      = origin/develop@0c66316（includes PR #3368）
PROBE         = temporary branch tmp/fu2-p7-f5-preview-env-probe（commit 9a2075f）→ Preview deployment
                dpl_4QNPxcdgaVECHJD9jkT7obXT8jbB（target = preview）. Instrumentation reverted on that branch
                （c7803dc; tree identical to develop）; never merged. Remote branch deletion was refused（§2）
OUTPUT RULE   = booleans only; no environment value, cookie, JWT, Authorization or share-link token was logged,
                returned, displayed or recorded
PRODUCTION    = not touched（the probe returned immediately when VERCEL_ENV === "production"）
RESULT        = all three variables PASS; hostname consistency PASS
FINAL STATUS  = PR for Mother Ship; STOP
```

## 2. Method

- **Instrumentation（temporary, now removed）:**
  - a server-only helper called at the start of the existing SSR component `ShrineDetailContent`
    （`/shrines/[id]`）;
  - it compared `process.env` against the request host（`x-forwarded-host ?? host`）and wrote one log line,
    `[F5_PREVIEW_ENV_PROBE]`, containing only booleans;
  - no new route, page, API or response field was added;
  - the code did not touch authentication, SSO, origin selection or routing;
  - it sent no request and read no `NEXT_PUBLIC_*` variable.
- **Safety tests before pushing（local, on the temporary branch）:**
  - every output is a boolean;
  - URL-, path- and port-shaped values and non-`vercel.app` values are rejected as hosts;
  - the log contains none of the injected values, nor a cookie;
  - nothing is logged when `VERCEL_ENV=production`;
  - the existing shrine-page tests passed（35 / 35）, and `tsc` / ESLint were clean.
- **Execution:**
  - one anonymous `GET /shrines/1` through each of the two Preview hosts in the deployment metadata:
    - **R1:** the deployment URL;
    - **R2:** the branch alias;
  - access went through Vercel's mechanism for protected deployments. A temporary share link, which expires within
    23 h, may have been created; it was not recorded;
  - both responses were 200 and rendered the shrine page; the response bodies contained no probe output;
  - the booleans were read from the deployment's runtime logs.
- **Clean-up:**
  - **Branch deletion failed:** `git push --delete` to the remote failed repeatedly（the session's git proxy closed
    the connection; retried with backoff）.
  - **Instrumentation removed instead:** a revert commit `c7803dc` was pushed to the temporary branch, whose tree is
    now identical to `develop`. The local branch is deleted. **The remote branch name still exists; Mother Ship or the
    owner can delete it.**
  - **This PR:** it contains no diagnostic code.
  - **Preview deployment `dpl_4QNPxcdgaVECHJD9jkT7obXT8jbB`:** it remains, SSO-protected and not served on any public
    domain. Its code logs booleans only. The owner can delete it in Vercel.
  - **New Preview:** the revert push produced a new Preview without instrumentation.

"Valid host" means a lowercase `vercel.app` hostname: labels `[a-z0-9-]`, no scheme, path, port or whitespace, ≤ 253
characters.

## 3. Sanitized results

| check | R1（deployment URL） | R2（branch alias） | verdict |
| --- | --- | --- | --- |
| `VERCEL === "1"` | true | true | PASS |
| `VERCEL_ENV === "preview"` | true | true | **PASS** |
| `VERCEL_ENV === "production"` | false | false | PASS |
| `VERCEL_URL` present | true | true | **PASS** |
| `VERCEL_URL` valid host | true | true | **PASS** |
| `VERCEL_BRANCH_URL` present | true | true | **PASS** |
| `VERCEL_BRANCH_URL` valid host | true | true | **PASS** |
| `VERCEL_PROJECT_PRODUCTION_URL` present / valid host（supplementary） | true / true | true / true | PASS |
| request host present | true | true | PASS |
| `VERCEL_URL` == request host | **true** | false | consistent |
| `VERCEL_BRANCH_URL` == request host | false | **true** | consistent |
| `VERCEL_PROJECT_PRODUCTION_URL` == request host | false | false | consistent（Preview ≠ production） |
| `VERCEL_URL` == `VERCEL_BRANCH_URL` | false | false | consistent（distinct hosts） |

**Hostname consistency: PASS.**

- R1 used the deployment URL from the Vercel metadata, and the runtime `VERCEL_URL` equals that host.
- R2 used the single branch alias from the metadata, and the runtime `VERCEL_BRANCH_URL` equals that host.
- Neither equals the production URL.
- On this Preview, therefore, the runtime values are exactly the trusted Preview hosts in the deployment metadata.

## 4. Sufficiency for the F5 allowlist design

**Sufficient for Preview.** Option A / B of `fu2-p7-f5-ssr-trusted-origin-2026-10-27.md` §7 can use this rule on
Preview: accept the request host only if it equals `VERCEL_URL` or `VERCEL_BRANCH_URL`. Both are present, valid and
match the request host for the host the visitor used, which keeps same-host cookie forwarding and therefore Preview SSO
working（`fu2-p7-f5-preview-runtime-env-verification-2026-10-27.md` §3）.

Prerequisites and limits for the F5 implementation:

1. **Production:**
   - `VERCEL_PROJECT_PRODUCTION_URL` exists at runtime on Preview, but this probe did **not** run on Production, by
     design;
   - production runtime presence, and whether `WEB_BASE_URL` should be the explicit origin, stay **UNVERIFIED** and
     need the owner's decision（Option A requires setting `WEB_BASE_URL` for Production）.
2. **Other Preview aliases:**
   - only the automatic branch alias was observed;
   - custom Preview domains or manually assigned aliases would not match either variable and would fail closed;
   - none exist today（project metadata）.
3. **Development:**
   - not covered by this probe;
   - keep the localhost rule for `NODE_ENV !== "production"` and no `VERCEL`.
4. **Normalisation:**
   - the runtime values are bare hostnames（valid-host checks passed）;
   - the implementation should compare lowercase hosts and build `https://` itself;
   - it should refuse a request host that matches neither variable, rather than trust `x-forwarded-proto`.
5. **Single observation:**
   - one Preview deployment and two requests;
   - the variables are platform-provided per deployment, so the implementation PR should re-verify on its own Preview
     with a QA login（concierge history and favorites render）.

## 5. Not done

- No Production request or change.
- No environment-variable listing or value read.
- No authenticated SSR exercised.
- No Development probe.
