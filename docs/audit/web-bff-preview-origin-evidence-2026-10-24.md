# Web BFF Origin — S-8 Preview Evidence（2026-10-24）

## 1. Status

```text
SCOPE                     = documentation only; records browser-observed results of the S-13 diagnostic
S-8                       = PARTIALLY VERIFIED — Vercel Preview, GET, Google Chrome on macOS only
V-1                       = NOT fully verified; implementation NOT approved by this record
S-3 / S-12                = evidence updated; NOT selected
PR #3321（diagnostic）     = open, not merged, not closed by this record
runtime / cookies / auth  = UNCHANGED
production                = NOT MODIFIED, NOT TESTED
FINAL STATUS              = STOP
```

- Base: `origin/develop@91c12e4`.
- Builds on:
  - `docs/audit/web-bff-csrf-hardening-contract-2026-10-23.md`（#3319: §4.4, §11.1 item 3）;
  - `docs/audit/web-bff-origin-preview-verification-2026-10-23.md`（#3320, the prior S-8 audit: gate blocked; local
    harness; options S-3a–d, S-12）.
- Diagnostic: PR #3321, `GET /api/qa/origin-diagnostic` at commit `1713e26`.
- Labels:
  - **Reported** = a field value read from the Mother Ship screenshots. This session did **not** observe the
    deployment: `*.vercel.app` is blocked by its network policy, #3320 §5.
  - **Observed（metadata）** = read-only Vercel API data.
  - **Inference** = reasoned.
  - **NOT_VERIFIED** = not tested.

---

## 2. Evidence

### 2.1 Source

| item | value |
| --- | --- |
| date | 2026-10-24 |
| browser | Google Chrome on macOS. The version was not supplied |
| evidence | screenshots supplied by Mother Ship. They are not committed to the repository and contain no header values or cookies, per the #3321 procedure step 5 |
| deployment | `dpl_F3xDgHESv5kuWQhf9MZhs4ptuS7R`: Preview（target `null`）, state READY, branch `qa/web-bff-preview-origin-diagnostic`, commit `1713e26`. It is the only deployment of that commit（Observed（metadata））. The diagnostic returns results only on this branch's previews（#3321 gate）, so the screenshots can only come from this build（Inference） |
| method | the #3321 procedure: from a page on the same host, `fetch('/api/qa/origin-diagnostic')`（GET） |

### 2.2 Observed results（Reported）

| field | deployment URL | branch URL |
| --- | --- | --- |
| `result` | `match` | `match` |
| `reason` | `null` | `null` |
| `referenceKind` | `deployment_url` | `branch_url` |
| `nextUrlOriginKind` | `deployment_url` | `branch_url` |
| `secFetchSite` | `same-origin` | `same-origin` |
| `originHeader` | `absent` | `absent` |

**Not reported:**

- `secFetchSiteIsSameOrigin`, `environment`, `version`. They follow from the reported fields, and their
  values are not recorded here.
- #3321 procedure step 4: a direct address-bar request, expected `secFetchSite: "none"`.

### 2.3 What the results establish

| statement | status | basis |
| --- | --- | --- |
| On this Vercel Preview, a **route handler's** `req.nextUrl.origin` equals the platform origin of the host the browser used, for both the deployment URL and the branch URL | **verified（Preview, GET, Chrome / macOS）** | `result: match`, with `referenceKind` = `nextUrlOriginKind` for both hosts |
| The Next.js fallbacks seen locally in #3320 §6 — bind address, `http://n` placeholder, `http` scheme — do **not** occur on this Preview | verified for these two requests | `nextUrlOriginKind` is a platform kind, not `loopback_or_bind_address`, `placeholder` or `platform_host_scheme_or_port_differs` |
| Chrome sends `Sec-Fetch-Site: same-origin` on a same-origin `fetch` GET on Vercel | verified（Chrome / macOS） | `secFetchSite` |
| A same-origin GET carries no `Origin` | consistent with the Fetch spec and #3321 limitation 5 | `originHeader: absent` |
| Whether the match came from the platform request URL or from the `Host` header | **not distinguishable** | #3321 limitation 3. Either way the browser case matches |

---

## 3. What remains unverified

| # | item | why it matters | status |
| --- | --- | --- | --- |
| N-1 | **Production** domains（`jinja-app-web.vercel.app` and the other production aliases） | V-1 enforcement runs there | **NOT_VERIFIED**. The diagnostic returns 404 outside its preview branch by design; equality on Production is an inference from the same platform |
| N-2 | **POST**（and other state-changing methods） | V-1 checks only state-changing requests | **NOT_VERIFIED**. The diagnostic is GET-only; the same `nextUrl` construction for POST is an inference |
| N-3 | `Origin` on a same-origin POST on Vercel | the R4 / R6 / R7 comparisons use it | NOT_VERIFIED on Vercel; Chromium local mock only（#3319 §10） |
| N-4 | **Safari / WebKit** | Fetch Metadata and `Origin` behaviour; S-1, S-9 | **not tested** |
| N-5 | **Firefox** | same | **not tested** |
| N-6 | Chrome on other platforms; the exact Chrome version | — | not recorded |
| N-7 | `Sec-Fetch-Site: none` on Vercel（procedure step 4） | S-9 | not reported |
| N-8 | self-hosted / Docker / `next dev`（#3320 §6: mismatch locally） | `DELETE /api/users/me` today, S-14 | unchanged: mismatch observed locally |
| N-9 | a custom domain, if one is added | T9, S-11 | none exists today（#3320 §3） |

**V-1 is not fully verified.** This record closes only the Preview / GET / Chrome part of S-8.

---

## 4. Decision evidence update（no selection）

### S-3 — how the expected origin is derived

| option | evidence before（#3320） | evidence added here |
| --- | --- | --- |
| S-3a `req.nextUrl.origin` only | contradicted off-Vercel（bind address）; unknown on Vercel | **supported on Vercel Preview for GET**（both hosts match）. Still contradicted for self-hosted / Docker / `next dev`. Production and POST unverified（N-1, N-2） |
| S-3b configured allowlist | independent of Next's URL construction | unchanged. On Preview, the platform values it would use（`VERCEL_URL`, `VERCEL_BRANCH_URL`）were present and well-formed, since the diagnostic would otherwise have returned `inconclusive` |
| S-3c `Host` / `X-Forwarded-Host` comparison | depends on the proxy | unchanged. On Preview, `Host` equalled a platform host for both requests, otherwise the result would be `inconclusive` |
| S-3d / S-12 `Sec-Fetch-Site: same-origin` authoritative | removes the S-3 dependency for Fetch Metadata browsers | Chrome sent `same-origin` on Vercel（GET）. That supports the premise for Chrome. WebKit and Firefox are untested（N-4, N-5） |

**Reading（not a decision）:**

- On Vercel Preview, the evidence no longer blocks S-3a.
- The off-Vercel mismatch still applies to every non-Vercel runtime, including the repository's Docker frontend.
- S-3a also rests on N-1 and N-2.
- Mother Ship decides whether that is enough.

### S-12 — make `Sec-Fetch-Site: same-origin` authoritative

| aspect | update |
| --- | --- |
| need on Vercel Preview | lower: `nextUrl.origin` already matches there |
| need off Vercel | unchanged: S-12 is the only option here that tolerates the bind-address mismatch |
| premise（browser sends `same-origin`） | supported for Chrome / macOS on Vercel; WebKit / Firefox not tested |

S-12 remains **open**.

### Other decisions

| id | update |
| --- | --- |
| S-8 | **partially verified**（§3） |
| S-1, S-9 | no new evidence; step 4（N-7）was not reported |
| S-11 | unchanged（#3320 §9） |
| S-13 | the diagnostic did its job; cleanup per §5 after evidence review |
| S-14 | unchanged（N-8） |
| V-1 | **not approved** by this record; blockers in #3319 §11.1 remain except the Preview part of item 3 |

---

## 5. Cleanup checklist for PR #3321（after evidence review）

This record does not perform any of these steps.

- [ ] Mother Ship confirms the evidence in §2 is sufficient for the Preview part of S-8.
- [ ] Optional, before cleanup: Mother Ship re-runs procedure step 4（N-7）, and the WebKit / Firefox checks
      if available, on the same preview.
- [ ] **Close PR #3321 without merging.**
- [ ] Delete the branch `qa/web-bff-preview-origin-diagnostic`.
- [ ] Confirm that `apps/web/src/app/api/qa/origin-diagnostic/` does not exist on `develop`. It never did: #3321
      was not merged.
- [ ] Confirm that `grep -rn "origin-diagnostic" apps/web/src` on `develop` returns nothing.
- [ ] Optional, owner: delete Preview deployment `dpl_F3xDgHESv5kuWQhf9MZhs4ptuS7R`. It stays behind Vercel SSO
      until then.
- [ ] Keep the screenshots outside the repository; record only the fields in §2.2.

---

## 6. Not done

```text
runtime / BFF / frontend / backend code   UNCHANGED
cookies / auth                            UNCHANGED
models / migrations                       UNCHANGED
production                                NOT MODIFIED, NOT TESTED
PR #3321                                  NOT merged, NOT closed
V-1                                       NOT approved
S-3 / S-12                                NOT selected
```
