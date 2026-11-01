> **Status: Read-only audit（documentation only）**
>
> - Audit date: 2026-11-01
> - Base: `develop` @ `7f16d97`
> - No production request, load test, env change, or backend / frontend / DB / throttle change.
> - No secret, IP address, token or signature is recorded.

# WS-04 Production Identity Evidence（after PR #3400）

## 0. Verdict

**The WS-04 BFF attestation path is working in production: VERIFIED at aggregate level.**

- The production `throttle identity summary` logs show 33 valid HMAC attestations and 0 rejections.
- No request fell back to `remote`.

**Nearby production identity is not verified.** `GET /api/places/nearby/` (and its aliases) began using WS-04 only
with PR #3400. No Nearby-specific measurement exists. The summary log has no per-endpoint field, so these counts
cannot be attributed to Nearby. **Status: UNKNOWN.**

## 1. Evidence

### 1.1 Deployment（git: VERIFIED; Render: supplied by Mother Ship）

| Item | Value | Source | Status |
| --- | --- | --- | --- |
| PR #3400 merge commit | `681db738`（2026-11-01T13:55:38+09:00） | `git log origin/develop` | VERIFIED |
| Render deploy of `681db738` | succeeded | Mother Ship（Render dashboard） | SUPPLIED, not independently checked |
| Live deploy | `59fb5153`（#3403, 2026-11-01T14:04:14+09:00） | Mother Ship | SUPPLIED, not independently checked |
| `681db738` is an ancestor of `59fb5153` | yes | `git merge-base --is-ancestor` | VERIFIED |
| WS-04 / throttle code changed between `681db738` and `59fb5153` | **no**: an empty diff for `backend/shrine_project/`, `temples/api/views/search.py`, `temples/api/urls.py` and `apps/web/src/lib/server/` | `git diff --stat` | VERIFIED |

The live backend therefore runs the WS-13 Nearby view (#3400), assuming the Live deploy is `59fb5153` as supplied.

### 1.2 Identity summary logs（supplied by Mother Ship）

Seven `throttle identity summary` lines, October 31 to November 1, summed (direct Render read-only log inspection; UTC timestamps: 2026-10-31 09:32:56, 10:29:49, 10:35:10, 11:56:57, 21:52:07, 22:30:38, and 2026-11-01 00:34:51). **All seven predate the PR #3400 deploy (2026-11-01 04:55:40 UTC).**

| Counter | Sum | Meaning（`backend/shrine_project/throttling.py`） |
| --- | --- | --- |
| `bff` | **33** | Identity from a valid BFF HMAC attestation (`resolve_client_ident`, path `bff`) |
| `edge` | **3** | No valid attestation; identity from `CF-Connecting-IP`, which is used only when `THROTTLE_TRUSTED_EDGE=render-cloudflare` |
| `remote` | **0** | Fallback to `REMOTE_ADDR` (shared proxy address) |
| `attestation_valid` | **33** | HMAC, IP, ±60 s window and constant-time signature all passed |
| `attestation_rejected` | **0** | No malformed, expired, bad-signature, incomplete or secret-unconfigured attestation |
| `attestation_absent` | **3**（directly observed） | Seven log lines each include this field; sum is 3 |

## 2. Interpretation

| Statement | Status | Basis |
| --- | --- | --- |
| The Vercel BFF signs, and the Render backend accepts, HMAC attestations | **VERIFIED**（aggregate） | `attestation_valid=33`, `rejected=0`. A secret missing on either side would produce 0 valid, or `secret_unconfigured` / `bad_signature` rejections |
| `KM_CLIENT_IDENTITY_SECRET` is configured on both sides and matches | **VERIFIED by inference**（values not read） | Same counters; no value was accessed |
| Vercel's `x-forwarded-for` reached the signer as a single valid address for those requests | **VERIFIED by inference** | `clientIdentity.ts` signs only a single valid IP |
| `THROTTLE_TRUSTED_EDGE=render-cloudflare` is active, and `CF-Connecting-IP` was present for unattested requests | **VERIFIED by inference** | The `edge` path is reachable only with that setting and a valid header; `remote=0` |
| No request was grouped into the shared `REMOTE_ADDR` bucket in the observed windows | **VERIFIED**（observed windows only） | `remote=0` |
| Which endpoints the 36 requests hit | **UNKNOWN** | The summary has no endpoint field |
| Whether any of the 36 requests is a Nearby request after #3400 | **UNKNOWN** | All seven observed summaries predate the #3400 deployment; no post-merge Nearby-specific identity evidence was found in the checked period. Before #3400, Nearby did not call WS-04 identity at all (manual `REMOTE_ADDR` throttle; #3398 N-1 / N-2) |
| Production Nearby throttle buckets are per client | **UNKNOWN**（expected by code: PARTIAL） | Code: Nearby uses the same `resolve_client_ident` (#3400 tests). Production evidence for the endpoint: none |

## 3. Residual risk matrix

| ID | Risk | Status | Impact | Next evidence / mitigation |
| --- | --- | --- | --- | --- |
| W-1 | Nearby production identity is unmeasured after #3400 | UNKNOWN | If Nearby requests arrived unattested, they would fall to `edge`. Through the Web BFF they should carry an attestation (`app/api/places/nearby/route.ts` uses `clientIdentityFrom: req`) | An endpoint-specific measurement: a summary window known to contain only Nearby traffic, or a bounded per-endpoint observability counter (needs a code PR and approval) |
| W-2 | The summary is aggregate-only, per process and reset on deploy. A window is logged only when a request arrives ≥ 300 s after the window started, so low traffic undercounts and the last open window is never logged | PARTIAL | 36 requests across seven windows is a small sample | A "first seen per (path, outcome)" INFO line (proposed in the post-#3394 observability audit); not implemented |
| W-3 | The 3 `edge` requests were unattested: Mobile direct calls, server-side recursive BFF calls, or direct API callers | PARTIAL | Recursive server-side BFF calls carry the Vercel egress address as their `edge` identity, so they share one bucket（`bff-anonymous-identity-paths-audit-2026-10-26.md` §2, conclusion 3）. Open PR #3358 addresses one such path | Continue the FU-2 direct-signing work; not in this audit's scope |
| W-4 | `LocMemCache` buckets are per process; current Gunicorn worker count is **1** | VERIFIED current configuration / FUTURE RISK | Render startup log shows `WEB_CONCURRENCY=1` on both post-#3400 deploys. `backend/start.sh` passes it to gunicorn; settings use `LocMemCache`. Multiple future workers or instances would split rate-limit counters | Before scaling workers or instances, move throttle cache to a shared backend and revalidate rate limits |
| W-5 | The Vercel `x-forwarded-for` trust rests on Vercel documentation (overwritten, single client IP) | PARTIAL | A proxy placed in front of Vercel would make every user share that proxy's address. This fails closed (over-throttles); it does not bypass | Revisit if a CDN or custom proxy is added |
| W-6 | Secret rotation or mismatch | MONITORED | It would appear as `attestation_rejected>0` with `reason=bad_signature` WARNING lines | Alert on that WARNING |
| W-7 | Vercel Preview deployments and the secret | UNKNOWN | Whether Preview holds the production secret and talks to the production backend is not recorded | Owner check of Vercel environment scoping (names only) |
| W-8 | `edge` trust depends on Cloudflare overwriting `CF-Connecting-IP` on Render | PARTIAL | Supported by the earlier spoof diagnostic（WS-04 design §11.2）, not re-tested here | No action; re-test only if the Render edge changes |

## 4. Explicit UNKNOWN items

1. Nearby-specific production identity distribution after #3400 (W-1).
2. Which endpoints produced the 36 observed requests.
3. No post-#3400 Nearby-specific identity summary was observed in the checked period; whether Nearby traffic occurred cannot be established from these logs.
4. The effective Nearby throttle rate was not directly observed; `THROTTLE_PLACES_NEARBY` is absent and code default is `30/min`.
5. Vercel Preview secret scoping.
6. Actual individual-user distribution of Nearby throttle buckets (distinct users cannot be inferred from aggregate BFF counts).

## 5. Related open PRs（checked 2026-11-01）

- #3358（public goshuins SSR → Django direct with page identity）touches WS-04 signing on another path. It does not
  conflict with this document.
- No open PR edits `ws04-throttle-client-identity-design-2026-10-25.md` or the Nearby audit.

## 6. Limitations

- Original PR evidence was supplied by Mother Ship. A separate read-only verification accessed the connected Render service metadata, deploy history, and filtered existing logs directly. No request was sent to the production API. Log searches are bounded to the specified time windows and do not prove absence of traffic.
- The counters are aggregate. No statement here identifies a user, an address or a request.

## 7. Follow-up verification (2026-11-01, read-only)

- **Render deployment independently verified:** commit `681db738` (#3400) deployed successfully at 2026-11-01 04:56 UTC; subsequent commit `59fb5153` (#3403) was Live at 05:05 UTC. `jinja-backend` runs one Render instance (`numInstances=1`).
- **Worker count directly observed:** startup lines on both deploys say `WEB_CONCURRENCY=1` (04:56:40 and 05:05:20 UTC). The variable is absent from owner-observed custom Render environment entries; Render and `backend/start.sh` default to 1. The active process count beyond this observed startup configuration was not independently enumerated.
- **Cache:** `backend/shrine_project/settings.py` configures `django.core.cache.backends.locmem.LocMemCache`. Per-process throttle state is a scaling constraint, not a demonstrated current multi-worker defect.
- **Render variable names (owner-observed, values not read):** `THROTTLE_TRUSTED_EDGE` and `KM_CLIENT_IDENTITY_SECRET` present; `THROTTLE_PLACES_NEARBY`, `DISABLE_THROTTLE`, `WEB_CONCURRENCY` absent. The startup guard requires `THROTTLE_TRUSTED_EDGE=render-cloudflare` when `RENDER_EXTERNAL_HOSTNAME` is present; its literal runtime value was not read. The prior `edge` observations support operational trust at that time.
- **Vercel Production variable names (connector metadata, decrypt=false):** `KM_CLIENT_IDENTITY_SECRET` present as Sensitive; `BACKEND_ORIGIN` and `DJANGO_API_BASE_URL` present. No values were read. This establishes scoping, not the contents of the currently deployed function environment.
- **Post-deploy log search:** between 2026-11-01 04:55:38 UTC and 12:00 UTC, filtered searches found no `throttle identity summary` and no `/api/places/nearby/` log match; a separate search found no `ImproperlyConfigured` message. These non-matches **do not** prove zero requests or successful per-client Nearby throttling.
- **Status remains:** WS-04 HMAC BFF acceptance VERIFIED in the pre-#3400 aggregate windows; post-#3400 Nearby-specific identity remains **UNKNOWN**. No synthetic requests, key disclosure, configuration edits, or production tests were performed.
