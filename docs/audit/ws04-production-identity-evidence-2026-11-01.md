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

Seven `throttle identity summary` lines, October 31 to November 1, summed:

| Counter | Sum | Meaning（`backend/shrine_project/throttling.py`） |
| --- | --- | --- |
| `bff` | **33** | Identity from a valid BFF HMAC attestation (`resolve_client_ident`, path `bff`) |
| `edge` | **3** | No valid attestation; identity from `CF-Connecting-IP`, which is used only when `THROTTLE_TRUSTED_EDGE=render-cloudflare` |
| `remote` | **0** | Fallback to `REMOTE_ADDR` (shared proxy address) |
| `attestation_valid` | **33** | HMAC, IP, ±60 s window and constant-time signature all passed |
| `attestation_rejected` | **0** | No malformed, expired, bad-signature, incomplete or secret-unconfigured attestation |
| `attestation_absent` | **3**（derived） | Not supplied. Each request increments one path and one outcome counter, so absent = 36 − 33 − 0 |

## 2. Interpretation

| Statement | Status | Basis |
| --- | --- | --- |
| The Vercel BFF signs, and the Render backend accepts, HMAC attestations | **VERIFIED**（aggregate） | `attestation_valid=33`, `rejected=0`. A secret missing on either side would produce 0 valid, or `secret_unconfigured` / `bad_signature` rejections |
| `KM_CLIENT_IDENTITY_SECRET` is configured on both sides and matches | **VERIFIED by inference**（values not read） | Same counters; no value was accessed |
| Vercel's `x-forwarded-for` reached the signer as a single valid address for those requests | **VERIFIED by inference** | `clientIdentity.ts` signs only a single valid IP |
| `THROTTLE_TRUSTED_EDGE=render-cloudflare` is active, and `CF-Connecting-IP` was present for unattested requests | **VERIFIED by inference** | The `edge` path is reachable only with that setting and a valid header; `remote=0` |
| No request was grouped into the shared `REMOTE_ADDR` bucket in the observed windows | **VERIFIED**（observed windows only） | `remote=0` |
| Which endpoints the 36 requests hit | **UNKNOWN** | The summary has no endpoint field |
| Whether any of the 36 requests is a Nearby request after #3400 | **UNKNOWN** | The log timestamps relative to the `681db738` deploy were not supplied. Before #3400, Nearby did not call WS-04 identity at all (manual `REMOTE_ADDR` throttle; #3398 N-1 / N-2) |
| Production Nearby throttle buckets are per client | **UNKNOWN**（expected by code: PARTIAL） | Code: Nearby uses the same `resolve_client_ident` (#3400 tests). Production evidence for the endpoint: none |

## 3. Residual risk matrix

| ID | Risk | Status | Impact | Next evidence / mitigation |
| --- | --- | --- | --- | --- |
| W-1 | Nearby production identity is unmeasured after #3400 | UNKNOWN | If Nearby requests arrived unattested, they would fall to `edge`. Through the Web BFF they should carry an attestation (`app/api/places/nearby/route.ts` uses `clientIdentityFrom: req`) | An endpoint-specific measurement: a summary window known to contain only Nearby traffic, or a bounded per-endpoint observability counter (needs a code PR and approval) |
| W-2 | The summary is aggregate-only, per process and reset on deploy. A window is logged only when a request arrives ≥ 300 s after the window started, so low traffic undercounts and the last open window is never logged | PARTIAL | 36 requests across seven windows is a small sample | A "first seen per (path, outcome)" INFO line (proposed in the post-#3394 observability audit); not implemented |
| W-3 | The 3 `edge` requests were unattested: Mobile direct calls, server-side recursive BFF calls, or direct API callers | PARTIAL | Recursive server-side BFF calls carry the Vercel egress address as their `edge` identity, so they share one bucket（`bff-anonymous-identity-paths-audit-2026-10-26.md` §2, conclusion 3）. Open PR #3358 addresses one such path | Continue the FU-2 direct-signing work; not in this audit's scope |
| W-4 | `LocMemCache` buckets are per process; production `WEB_CONCURRENCY` is UNKNOWN | UNKNOWN | With more than one worker, the effective limit is multiplied and the counters split | Record `WEB_CONCURRENCY` from Render settings (value only, no secret) |
| W-5 | The Vercel `x-forwarded-for` trust rests on Vercel documentation (overwritten, single client IP) | PARTIAL | A proxy placed in front of Vercel would make every user share that proxy's address. This fails closed (over-throttles); it does not bypass | Revisit if a CDN or custom proxy is added |
| W-6 | Secret rotation or mismatch | MONITORED | It would appear as `attestation_rejected>0` with `reason=bad_signature` WARNING lines | Alert on that WARNING |
| W-7 | Vercel Preview deployments and the secret | UNKNOWN | Whether Preview holds the production secret and talks to the production backend is not recorded | Owner check of Vercel environment scoping (names only) |
| W-8 | `edge` trust depends on Cloudflare overwriting `CF-Connecting-IP` on Render | PARTIAL | Supported by the earlier spoof diagnostic（WS-04 design §11.2）, not re-tested here | No action; re-test only if the Render edge changes |

## 4. Explicit UNKNOWN items

1. Nearby-specific production identity distribution after #3400 (W-1).
2. Which endpoints produced the 36 observed requests.
3. Timestamps of the seven summaries relative to the `681db738` deploy.
4. The supplied `attestation_absent` value (derived as 3 here).
5. Production `WEB_CONCURRENCY`, `THROTTLE_PLACES_NEARBY`, `DISABLE_THROTTLE`.
6. Vercel Preview secret scoping.
7. Independent confirmation of the Render deploy status (supplied by Mother Ship).

## 5. Related open PRs（checked 2026-11-01）

- #3358（public goshuins SSR → Django direct with page identity）touches WS-04 signing on another path. It does not
  conflict with this document.
- No open PR edits `ws04-throttle-client-identity-design-2026-10-25.md` or the Nearby audit.

## 6. Limitations

- All production figures were supplied by Mother Ship from the Render dashboard; this session cannot reach Render.
- The counters are aggregate. No statement here identifies a user, an address or a request.
