# Web BFF CSRF — V-1 Final Implementation Contract（2026-10-24）

## 1. Status

```text
SCOPE                         = documentation only — final contract for a later implementation PR
RUNTIME IMPLEMENTATION        = NOT AUTHORIZED（V-1）
runtime / BFF / cookies / auth = UNCHANGED
env vars / deployments        = UNCHANGED / NONE
models / migrations / P1 / P2 = UNCHANGED / NOT IMPLEMENTED
FINAL STATUS                  = STOP — awaiting the approvals in §12
```

- Base: `origin/develop@c3642ca`.
- **Runtime code is unchanged since the audited base `38eca3f`**: `git diff 38eca3f c3642ca -- apps/web backend` is
  empty, so the code facts of the three audits still hold.
- Re-checked on this base:
  - 25 state-changing route files;
  - `isAllowedOrigin` only in `app/api/users/me/route.ts`;
  - test-case counts login 4, register 3, chat 6, compass weekly 3, `users/me` 5.
- **Authoritative sources:**
  - `docs/audit/web-bff-csrf-hardening-contract-2026-10-23.md`（#3319, "the base contract"）;
  - `docs/audit/web-bff-origin-preview-verification-2026-10-23.md`（#3320）;
  - `docs/audit/web-bff-preview-origin-evidence-2026-10-24.md`（#3322）.
- **Precedence:** where this record and the base contract differ, **this record wins**, because it applies the
  Mother Ship decisions below. Where the documents and the code differ, the code wins.

### 1.1 Mother Ship decisions applied（verbatim intent; not reinterpreted）

| id | decision | effect in this contract |
| --- | --- | --- |
| **S-1 = A** | reject when both `Origin` and `Sec-Fetch-Site` are absent | row D13（§2） |
| **S-9 = A** | when `Sec-Fetch-Site: none`, evaluate `Origin` | rows D9–D10 |
| **S-11 = B** | Class B routes go in a separate, time-bound PR | §9; Class B is **out of V-1** |
| **S-3 = B** | use explicitly configured, environment-specific public origins | §3 |
| **S-12**（conditional） | treat `Sec-Fetch-Site: same-origin` as evidence, but reject an explicit contradictory `Origin` | rows D4–D8 |
| **V-1 runtime** | **not authorized** | nothing here may be implemented until §12 approvals |

---

## 2. Request validation — final decision table

### 2.1 Inputs

- `sfs`: the raw `Sec-Fetch-Site` header.
- `origin`: the raw `Origin` header.
- `current`: the **currently served public origin** from §3.4. It is `null` if it cannot be determined.

Header parsing rules:

| rule | detail |
| --- | --- |
| `Sec-Fetch-Site` values | exactly `same-origin`, `same-site`, `cross-site` or `none`, case-sensitive and lower-case. Any other value — empty, other case, a token list, or a comma from a duplicated header — is **unknown** |
| `Origin` — absent | the header is not present |
| `Origin` — `null` | the exact string `null` |
| `Origin` — duplicated | the value contains `,`. Fetch-style `Headers` join repeated fields with `", "` |
| `Origin` — malformed | it fails `new URL()`; the scheme is not `http` / `https`; it has userinfo, a path other than empty, a query or a fragment; or `new URL(origin).origin !== origin` |
| `Origin` — matching | well-formed and **exactly** equal to `current`（scheme, host and port） |
| `Origin` — mismatched / contradictory | well-formed and not equal to `current` |

### 2.2 Table（the first matching row wins）

| # | precondition | `Sec-Fetch-Site` | `Origin` | decision | reason code（log only） |
| --- | --- | --- | --- | --- | --- |
| D0 | `current` is `null`（configuration missing, malformed or ambiguous, or the request host is not configured; §3.4） | any | any | **reject** | `config_unavailable` / `host_not_configured` |
| D1 | — | `cross-site` | any | **reject** | `sfs_cross_site` |
| D2 | — | `same-site` | any | **reject** | `sfs_same_site` |
| D3 | — | unknown or malformed | any | **reject** | `sfs_unknown` |
| D4 | — | `same-origin` | absent | **allow**（S-12: `same-origin` is evidence） | — |
| D5 | — | `same-origin` | matching | **allow** | — |
| D6 | — | `same-origin` | mismatched | **reject**（S-12: contradictory） | `origin_contradicts_sfs` |
| D7 | — | `same-origin` | `null` | **reject** | `origin_null` |
| D8 | — | `same-origin` | duplicated or malformed | **reject** | `origin_malformed` |
| D9 | — | `none` | matching | **allow**（S-9 = A） | — |
| D10 | — | `none` | absent, `null`, duplicated, malformed or mismatched | **reject** | `sfs_none_origin_invalid` |
| D11 | — | absent | matching | **allow** | — |
| D12 | — | absent | `null`, duplicated, malformed or mismatched | **reject** | `origin_invalid` |
| D13 | — | absent | absent | **reject**（S-1 = A） | `headers_absent` |

- **D0 comes first.** With no trustworthy `current`, nothing is allowed, including `same-origin`. That is how
  S-12 behaves when configuration is missing: **it fails closed and is never silently weakened.** §3.5 covers
  the operational consequence.
- `req.nextUrl.origin`, `Referer`, `X-Forwarded-Host` and `X-Forwarded-Proto` are **not inputs**.
- Every reject row produces the response in §5. The reason code goes only to a server log line（§3.6）, never
  to the response.

---

## 3. Public-origin configuration contract（S-3 = B）

### 3.1 Mode selection（`NODE_ENV` is never used）

| condition | mode |
| --- | --- |
| `VERCEL === "1"` and `VERCEL_ENV === "production"` | **production** |
| `VERCEL === "1"` and `VERCEL_ENV === "preview"` | **preview** |
| `VERCEL === "1"` and any other or missing `VERCEL_ENV` | **invalid** → D0 |
| `VERCEL` unset | **self-hosted**（local development, Docker, any other host） |

### 3.2 Sources per mode

| mode | configured origins | platform-provided values used | notes |
| --- | --- | --- | --- |
| **production** | `WEB_PUBLIC_ORIGINS`（new, server-only, **required**, Production-scoped） | **none** | `VERCEL_URL` in production is the per-deployment URL under Vercel SSO; not a user-facing origin. `VERCEL_PROJECT_PRODUCTION_URL` is **not** used as an authority |
| **preview** | `WEB_PUBLIC_ORIGINS`（optional, Preview-scoped）**plus** the platform values | `VERCEL_URL`, `VERCEL_BRANCH_URL`, each as `https://<value>` | preview hosts are per deployment and cannot be pre-listed. Use of these values is **conditional on approval A-3**（§12） |
| **self-hosted** | `WEB_PUBLIC_ORIGINS`（**required**） | none | local: `http://localhost:3000`. Docker（`apps/web/Dockerfile.frontend`, `next dev -H 0.0.0.0`）: the URL the browser uses, e.g. `http://localhost:3000`; **never** `0.0.0.0`. Self-hosted behind a proxy: the public `https://…` origin, and the proxy must pass the original `Host`（§3.4） |

**Trust assumptions for the platform values:**

- They are set by Vercel, not by the request.
- They need "Automatically expose System Environment Variables" enabled.
- On the S-13 preview they were present and well-formed, because the diagnostic returned `match` rather than
  `inconclusive`（#3322 §4; inference）.
- They are host names without a scheme.

### 3.3 Validation of the configuration（any failure → D0 for every request）

`WEB_PUBLIC_ORIGINS` is a comma-separated list. Platform values are wrapped as `https://<host>`. Each entry
must satisfy all of these rules:

1. It parses with `new URL()`, and `new URL(entry).origin === entry`. That rules out a path, query, fragment,
   userinfo or trailing slash.
2. The scheme is `https`. `http` is allowed **only** for the loopback hosts `localhost`, `127.0.0.1` and `[::1]`.
3. The host is not `0.0.0.0`, `[::]`, a wildcard or empty. Entries containing `*` are rejected: **no wildcard
   subdomain trust**.
4. Duplicates are removed.
5. **Ambiguity:** two entries with the same `host`（host:port）but a different scheme make the whole
   configuration invalid.
6. The list after the steps above is not empty.

The configuration is read at request time from `process.env`, so tests can set it. The rejection log records
only the validation reason code, never the values（§3.6）.

### 3.4 Selecting the currently served public origin（binding）

- `current` is the **configured entry whose `host` equals the request's `Host` header**, compared
  case-insensitively, as host:port.
- If no entry matches, or `Host` is absent, `current = null` and D0 applies.
- **Binding:** an `Origin` is compared **only** with `current`, never with "any configured origin". A page on
  configured origin X posting to configured origin Y arrives with `Host` Y and `Origin` X. It is rejected by D6
  or D12.
- **`Host` is a selector, not an authority.**
  - It can only pick one of the pre-validated configured values.
  - A non-browser client can forge `Host`, but it carries no victim cookies, so there is no CSRF gain.
  - Browsers set `Host` from the URL they request.
- **`X-Forwarded-Host` is ignored entirely.**
- Proxies in front of a self-hosted deployment must forward the original `Host`; otherwise D0 applies（fails
  closed）.
- **`req.nextUrl.origin` is not used.** #3322 showed it equals the platform origin on Vercel Preview for GET.
  #3320 showed it is the bind address off Vercel. Making it an input would add nothing on Vercel and break
  self-hosting.

### 3.5 Behaviour when configuration is missing or invalid（S-12 included）

- Every in-scope route rejects every request with the §5 response（D0）, including first-party same-origin
  requests.
- So **login, register, logout, chat and compass weekly are unavailable** until the configuration is fixed.
  This is deliberate: fail closed, no silent weakening.
- Gates in §11 must catch it before enforcement reaches users:
  - a CI test of the configuration parser;
  - a Preview E2E pass;
  - an owner inspection of the production configuration.

### 3.6 Logging

- One line per rejection: route path, decision row（D0–D13）and reason code.
- **Not logged:** the `Origin` value, `Host`, `Cookie`, `Authorization`, any token, any configuration value,
  the request body.
- Allowed requests are not logged by this helper.

---

## 4. V-1 implementation scope（when authorized）

### 4.1 Routes

| route | handler | change |
| --- | --- | --- |
| `apps/web/src/app/api/auth/login/route.ts` | POST | call the helper first |
| `apps/web/src/app/api/auth/register/route.ts` | POST | same |
| `apps/web/src/app/api/auth/logout/route.ts` | POST | same. The existing GET（JSON only, no cookie change）is unchanged |
| `apps/web/src/app/api/concierge/chat/route.ts` | POST | same |
| `apps/web/src/app/api/compass/weekly/route.ts` | POST | same |
| `apps/web/src/app/api/users/me/route.ts` | DELETE | **replace** the local `isAllowedOrigin` with the helper（§4.3）. PATCH stays in Class B（§9） |

### 4.2 New modules

- `apps/web/src/lib/server/publicOrigins.ts`: mode selection and configuration validation（§3.1–§3.3）; pure,
  reading `process.env`.
- `apps/web/src/lib/server/requestOrigin.ts`: header parsing, the selection in §3.4, the decision table in §2,
  `rejectCrossOriginRequest(req): Response | null` and the log line in §3.6.
- **Must not** reuse `lib/server/resolveServerBaseUrl.ts`: it trusts `X-Forwarded-Host`（Code: lines 12-18）.

### 4.3 Reconciling `DELETE /api/users/me`

| aspect | today（Code） | after V-1 |
| --- | --- | --- |
| reference | `req.nextUrl.origin`（the bind address off Vercel; #3320 §6.3） | `current` from §3.4 |
| `Origin` absent | allowed | allowed only with `Sec-Fetch-Site: same-origin`（D4）; **rejected** when both are absent（D13） |
| `Sec-Fetch-Site` | ignored | D1–D3, D9–D10 apply |
| response on reject | `403`, empty body | the §5 response |
| test "Originが無い場合はBackend DELETEを呼ぶ" | expects a backend call | **rewritten to expect 403**（S-1 = A） |

### 4.4 Out of scope

- Class B（§9）and Class C routes; the backend（§10）.
- Cookies, tokens and their attributes; P1 / P2; mobile（MF-1）; migrations.
- S-2 and S-5 unless approved（§6, §7）.
- Any environment-variable change. The owner adds `WEB_PUBLIC_ORIGINS` as a gate step（§11）.

---

## 5. Rejection response contract

| item | value |
| --- | --- |
| status | `403` |
| body | `{"detail":"forbidden"}`, identical for every reject row |
| headers | `Content-Type: application/json`, `Cache-Control: no-store` |
| `Set-Cookie` | **none**. The helper returns a fresh `Response`, before any cookie code runs |
| backend request | **none**: `djFetch` / `bffFetchWithAuthFromReq` are not called |
| token refresh | **none**: the refresh path is inside the backend helpers, which are not reached |
| request body | **not consumed**: the helper reads only headers and `process.env`, and is called before `req.text()` / `req.json()` |

---

## 6. Content-Type validation（S-2）— proposal, **not approved**

| route | proposed rule |
| --- | --- |
| login, register | after the origin check passes: `Content-Type` must be `application/json`（parameters allowed）, otherwise `415`, with no cookie and no backend call |
| chat, compass weekly | same |
| logout | no body; origin check only |

Effect: the login route's `x-www-form-urlencoded` and `multipart/form-data` support（Code: `login/route.ts:11-31`）
would end. No first-party caller or test uses them. **S-2 has no Mother Ship decision.** The implementation
PR includes it only if S-2 is approved.

---

## 7. Logout failure（S-5）— required behaviour proposed, **not approved**

- **Today（Code）:** `AuthProvider.logout`（`lib/auth/AuthProvider.tsx:197-213`）and `lib/api/auth.ts` `logout`
  ignore the response status. A rejected or failed logout still switches the UI to guest while the cookies
  remain.
- **Why V-1 makes this pressing:** D0 or a misconfiguration turns every logout into a 403. Without S-5, the UI
  would say "logged out" while the session stays valid（#3318 I-4）.
- **Proposed behaviour:**
  - On any non-2xx response or network failure, show an error, keep the authenticated UI state, and do
    **not** clear client caches as if logged out.
  - Retry is manual.
  - On 2xx, behave as today.
- **S-5 has no Mother Ship decision.** Approval A-5（§12）asks for it **before production enforcement**.

---

## 8. Tests and regression matrix

### 8.1 Unit — `publicOrigins`

- Each mode in §3.1, including `VERCEL=1` with an unknown or missing `VERCEL_ENV`, and `NODE_ENV` changes having
  no effect.
- Each validation rule in §3.3:
  - a valid list;
  - a trailing slash, a path, a query or userinfo;
  - `http` on a non-loopback host;
  - `0.0.0.0`, `*`, `*.example`;
  - duplicates;
  - an ambiguous http / https pair for the same host;
  - an empty list;
  - a missing variable.
- Preview: platform values present, missing or malformed（with a scheme, with a path）; combined with the
  optional list.
- Production: `VERCEL_URL` and `VERCEL_PROJECT_PRODUCTION_URL` set but `WEB_PUBLIC_ORIGINS` missing → invalid.

### 8.2 Unit — `requestOrigin`（every row D0–D13）

- D0 with every configuration failure, and with a request `Host` not in the list.
- D1–D3, including `Same-Origin`（case）, `same-origin, same-origin`（duplicated）, empty, and `foo`.
- D4–D8 and D9–D10: for each `Origin` class — absent, matching, mismatched, `null`, duplicated, malformed（no
  scheme, `ftp:`, with a path, with userinfo, `https://host:443` vs `https://host`）.
- D11–D13.
- **Binding:** with two configured origins X and Y, `Host` Y with `Origin` X → reject（D6 / D12）.
- `X-Forwarded-Host` set to a configured host while `Host` is not → D0.
- `req.nextUrl.origin` differing from `current` has no effect.
- The log line contains the row and reason only; asserted not to contain the `Origin`, `Host` or cookie values.

### 8.3 Per route（vitest, next to the existing tests）

| case | login | register | logout | chat | compass weekly | users/me DELETE |
| --- | --- | --- | --- | --- | --- | --- |
| allowed（D5, with a configured origin） | existing behaviour unchanged | same | cookies cleared as today | upstream called; anon cookie written as today | relay as today | backend DELETE; cookies cleared on 204 |
| reject（one case per reject class: D0, D1, D2, D3, D6, D7, D8, D10, D12, D13） | §5 response | same | §5, **tokens not cleared** | §5, **no anon cookie** | §5, no relay | §5, no backend call |
| side-effect assertions on every reject | `getSetCookie()` empty; `djFetch` / `bffFetchWithAuthFromReq` called 0 times; the body stream not read; `Cache-Control: no-store` | same | same | same | same | same |

### 8.4 Updating existing tests

- Add a shared test helper that sets same-origin headers（`Host`, `Origin`, `Sec-Fetch-Site: same-origin`）and
  stubs `WEB_PUBLIC_ORIGINS`.
- Apply it to the **16 existing cases** that build requests without either header: login 4, register 3, chat 6,
  compass weekly 3. Without it they would fail on D13.
- Rewrite the `users/me` case "Originが無い場合はBackend DELETEを呼ぶ" to expect 403. Update the other four
  `users/me` cases to the configured-origin reference.

### 8.5 Regression guards

- **Inventory guard:** a test lists every exported POST / PUT / PATCH / DELETE handler under `app/api/**`. It
  fails when a handler is neither in the V-1 list（§4.1）nor in the documented Class B / C lists（§9）.
- **Class B guard:** one test per Class B handler asserts it does **not** call the helper yet. It is deleted by
  the Class B PR.

### 8.6 Browser E2E（Preview only; not Production）

Run on Chromium, **WebKit and Firefox**:

- First-party login, logout, register, chat and compass weekly succeed.
- A cross-site attack page（the #3318 §7.2 shapes: form POST urlencoded / text/plain / multipart, `fetch`
  `no-cors`）gets 403 and leaves the cookie jar unchanged.
- A sandboxed iframe（`Origin: null`）gets 403.
- Address-bar navigation is not a POST and is not tested as one.
- Browser-sent `Origin` / `Sec-Fetch-Site` on same-origin **POST** on the Preview is recorded. This closes
  #3322 N-2 / N-3 for Preview only.

### 8.7 Docker / localhost

- `next dev -H 0.0.0.0` with `WEB_PUBLIC_ORIGINS=http://localhost:3000`:
  - a browser at `http://localhost:3000` passes;
  - a browser at `http://127.0.0.1:3000` gets 403 unless that origin is configured too.

  This replaces the bind-address mismatch in #3320 §6.

---

## 9. Class B follow-up PR contract（S-11 = B）

**Not part of V-1. Implementing it needs new Mother Ship authorization.**

### 9.1 Files（from the base contract §2.2; re-checked on `c3642ca`）

**Class B — 16 files:**

1. `app/api/users/me/route.ts`（PATCH）
2. `app/api/favorites/route.ts`
3. `app/api/favorites/[id]/route.ts`
4. `app/api/favorites/preload/route.ts`
5. `app/api/my/goshuins/route.ts`
6. `app/api/my/goshuins/[id]/route.ts`
7. `app/api/shrine-interactions/route.ts`
8. `app/api/shrine-submissions/route.ts`
9. `app/api/shrines/[id]/reflection/route.ts`
10. `app/api/shrines/[id]/visit/route.ts`
11. `app/api/compass/recommendations/route.ts`
12. `app/api/billings/checkout/route.ts`
13. `app/api/billings/portal/route.ts`
14. `app/api/shrines/route.ts`
15. `app/api/shrines/ingest/route.ts`
16. `app/api/my/shrines/ingest/route.ts`

**Mixed B / C — 4 files:**

1. `app/api/my/shrines/route.ts`
2. `app/api/deep-dive/ask/route.ts`
3. `app/api/places/find/route.ts`
4. `app/api/places/resolve/route.ts`

### 9.2 Risk

- These handlers act with the victim's `SameSite=Lax` cookies. Cross-site requests do not carry those cookies.
- **Same-site cross-origin** requests do carry them（#3319 §2.1, Chromium mock）. Such a request could add or
  delete favourites and goshuins, post interactions, submissions, visits and reflections, change the profile
  （PATCH `users/me`）, or start billing checkout or portal sessions as the victim.
- Today no same-site sibling origin is known, because `vercel.app` is a public suffix and there is no custom
  domain（#3320 §4; inference）. A custom domain with subdomains makes the risk reachable.

### 9.3 Required coverage

- The same helper and the same decision table（§2）on every Class B and B / C state-changing handler.
- The same §5 response.
- The S-2 content-type rule, if approved.
- Removal of the Class B guard test（§8.5）.
- Per-handler tests as in §8.3, and the E2E rows in §8.6 for a representative sample: favourites, goshuins,
  billing checkout, PATCH `users/me`.

### 9.4 Deadline（proposal; needs approval A-7）

- The Class B PR is merged **before general release**, and **before any custom domain is attached to the
  project**, whichever comes first.
- Proposed target: within **14 days after the V-1 PR merges**.
- Until then, the §9.2 risk is the accepted residual.

---

## 10. Decision and risk register

### 10.1 Approved

- **S-1 = A:** reject when both headers are absent.
- **S-9 = A:** evaluate `Origin` when `Sec-Fetch-Site: none`.
- **S-11 = B:** Class B goes in a separate, time-bound PR.
- **S-3 = B:** explicitly configured, environment-specific public origins.
- Earlier: S-13 diagnostic（conditional; its job is done, cleanup per #3322 §5）.

### 10.2 Conditionally approved

- **S-12:** `same-origin` is evidence; reject a contradictory `Origin`. Applied in D4–D8. The condition is
  carried as A-2.

### 10.3 Still open

S-2, S-4（rollout: enforce vs report-only）, S-5, S-6（backend defense in depth）, S-8（Production / POST /
WebKit / Firefox）, S-10（the inventory guard; included in §8.5 as a proposal）, S-14（Docker / self-hosting;
addressed by §3.2 if approved）, and A-1 to A-8 in §12.

### 10.4 Residual risks

| id | risk | status |
| --- | --- | --- |
| R-B | Class B same-site CSRF（§9.2） | accepted until the Class B deadline |
| R-C | Class C routes have no check | low CSRF value; tracked in §9.1 B / C |
| R-D | **direct backend exposure**: `AllowAny` chat and compass weekly accept cross-site form posts at the backend origin（#3319 §5）. JWT is header-based; Django session CSRF is enforced; `CsrfExemptSessionAuthentication` is unused | no change in V-1（S-6 open） |
| R-M | **MF-1**: mobile sends concierge chat unauthenticated（#3318 §8） | separate issue, outside V-1 |
| R-X | XSS or a compromised first-party origin passes any origin check | out of scope |
| R-O | **operational**: missing or invalid configuration makes the five routes unavailable（§3.5） | mitigated by the §11 gates |
| R-P | Production POST behaviour is not yet observed | §11 gates; Preview GET evidence is not proof |

### 10.5 Separation from G1–G4（handoff grant gates）

- V-1 changes **none** of the handoff gates G1–G5（`concierge-handoff-grant-schema-proposal.md` §1.1）:
  - G1 stays conditionally approved;
  - G2–G5 stay not approved.
- **Dependency, recorded but not decided（A-8）:** the handoff claim relies on login CSRF being closed
  （#3318 C-3）. The G3 user-facing flow should not be enabled before V-1 is enforced in production.

---

## 11. Deployment gates

| gate | what | who | proves |
| --- | --- | --- | --- |
| L0 local unit | §8.1–§8.5 and §8.7 pass; ESLint, `tsc`; repository hooks | implementer | logic and side effects |
| L1 CI | `backend-tests` / `web-tests` workflows green on the PR | CI | the same in CI; no regression elsewhere |
| L2 Preview E2E | §8.6 on Chromium, WebKit and Firefox against the PR's Preview（SSO; owner access） | owner or delegated QA | real platform headers and POST on **Preview** |
| L3 Production configuration inspection | the owner confirms `WEB_PUBLIC_ORIGINS` is set Production-scoped with the exact production origin(s), and that no wildcard or `0.0.0.0` is present. Confirmation is by name, scope and shape, never by sharing values in documents | owner | D0 will not trigger in production |
| L4 Production rollout authorization | explicit Mother Ship go: enforce or report-only（S-4）, the time window, rollback by revert | Mother Ship | — |

- **Preview GET evidence（#3322）is not proof of Production POST behaviour.**
- **No production enforcement** without L0–L3 passed and L4 granted.
- After rollout: a QA login, logout and chat on production with test accounts; then a cross-site attack page
  from a separate origin under owner control, Chromium only, as a smoke check. This needs L4.

---

## 12. Outstanding Mother Ship approvals

| id | approval needed | blocks |
| --- | --- | --- |
| **A-0** | **V-1 runtime implementation authorization** | everything in §4 |
| A-1 | the variable name and format `WEB_PUBLIC_ORIGINS`（§3.3） | §4.2 |
| A-2 | confirm the S-12 condition as applied in D4–D8, including D4（`same-origin` with `Origin` absent → allow） | §2 |
| A-3 | in preview mode, use of `VERCEL_URL` / `VERCEL_BRANCH_URL` as platform-provided public origins（§3.2） | Preview usability; without it previews fail closed unless each is listed |
| A-4 | S-2 JSON-only | §6 |
| A-5 | S-5 logout failure behaviour, before production enforcement | §7, L4 |
| A-6 | S-4 rollout mode | L4 |
| A-7 | the Class B deadline（§9.4） | §9 |
| A-8 | the G3 dependency on V-1 enforcement（§10.5） | handoff G3 |
| — | S-6, S-8 remainder, S-14 | stay open |

---

## 13. Not done

```text
runtime code / BFF routes / frontend      UNCHANGED
cookies / authentication / tokens         UNCHANGED
environment variables                     UNCHANGED（WEB_PUBLIC_ORIGINS is proposed, not created）
models / migrations                       UNCHANGED
deployments                               NONE
P1 / P2                                   NOT IMPLEMENTED
PRs                                       none merged
```
