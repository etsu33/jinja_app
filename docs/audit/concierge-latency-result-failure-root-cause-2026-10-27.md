# Concierge Recommendation Latency and Result-Failure Root Cause Audit（2026-10-27）

## 1. Status

```text
RECORD TYPE     = read-only audit（documentation only）
BASELINE        = origin/develop@3384392
CODE CHANGES    = NONE（ranking, scores, DB, auth, Premium, timeouts, retries unchanged）
PRODUCTION      = read-only Vercel runtime logs（1-hour retention, statuses / booleans only）; Render logs not accessible
VERDICT         = Backend latency: ROOT CAUSE IDENTIFIED（code + local measurement; production DB latency is a hypothesis）
                  Frontend failure: UNRESOLVED; ranked hypotheses + one observability gap（§6）
FINAL STATUS    = STOP at the PR; no implementation
```

Evidence levels: **Code**（file:line at the baseline）, **Measured**（local run, §4.3）, **Prod log**（Vercel, read-only）,
**Hypothesis**.

---

## 2. Executive summary

1. **The slow phase is per-candidate user-history lookups, which run only for authenticated users. It is not scoring.**
   - `_attach_breakdown` calls three `concierge_history` helpers for each of the 20 pooled candidates（Code:
     `concierge_chat_ranking.py:1325-1339`）.
   - For an anonymous user, all three return before touching the DB.
   - For an authenticated user, they issue **14 sequential queries per candidate**: **280 queries per request**
     （Measured）.
   - At roughly 70 ms per round trip, that is about 1 s per candidate and about 20 s for 20 candidates. This matches
     the observed 1 s spacing between `[dbg] attach_breakdown` lines and the 19.7–20.4 s recommend phase.
   - The fast path（≈ 0.09 s）is the same code with zero queries.
2. **Discriminating branch**: `user is None or not user.is_authenticated` at
   `concierge_history.py:27, 125, 309`. The view passes `user` only when authenticated
   （`api_views_concierge.py:771`）.
3. **Frontend**: nothing in the Browser → BFF → Django path times out or aborts on a 22 s response.
   - The axios instance has no `timeout`（`apps/web/src/lib/api/client.ts:5-8`）.
   - There is no `AbortController` and no watchdog in the Concierge page or hook.
   - The BFF route passes the upstream status and body through（`app/api/concierge/chat/route.ts:61-85, 160-166`）.
   - One production request in the 1-hour Vercel window took ≈ 22.6 s and the BFF returned 200
     （Prod log, §6.1）. The 22 s latency **cannot by itself** trigger the error card.
   - The card "うまく取得できませんでした" appears only when the hook's single `catch` runs
     （`features/concierge/hooks.ts:350-431`, `ConciergeClientFull.tsx:1547, 2060-2062`）. That `catch` also swallows
     exceptions thrown **after** a 200 in response post-processing and UI callbacks, and it logs nothing for them. The
     exact trigger is therefore unresolved（§6）.
4. **Minimal correction（proposal）**:
   - batch-load the user's history for the 20 candidate shrine ids once per request（≈ 5–6 queries instead of 280）,
     with outputs identical to today;
   - separately, split the frontend `try` so that post-processing failures are logged and distinguishable.

   No timeout increase, no retries, no ranking change.

---

## 3. Request path（recommend phase）

| step | code | note |
| --- | --- | --- |
| view | `backend/temples/api_views_concierge.py:757-843` | `build_chat_recommendations(..., user=user if user.is_authenticated else None)`（:771）; logs `[concierge/perf] step=recommend rid=… elapsed=…`（:841） |
| LLM route | `concierge_chat.py:820-848` | `resolve_llm_route`, **before** enrichment; not in the slow interval |
| pool | `concierge_chat.py:850-854` | `_ensure_pool_size(size=20)` → 20 of the ≈ 115 candidates are enriched |
| enrichment loop | `concierge_chat.py:182-233`（called at :879） | sequential `for rec in recs` → `_attach_breakdown` → soft signals → reason → reason source |
| per-candidate history | `concierge_chat_ranking.py:1325-1339` | `calculate_shrine_behavior_signal_breakdown`, `classify_shrine_action_state`, `build_recent_reflection_hint` with `user=user, shrine_id=…` |
| log | `concierge_chat_ranking.py:1633-1650` | `[dbg] attach_breakdown …` at the **end** of each `_attach_breakdown`, so the spacing between two lines = one candidate's work |
| identity | `api_views_concierge.py:886-890` | `[concierge/chat] identity_state authenticated=%s …` after the recommend phase |

---

## 4. Fast path versus slow path

### 4.1 The branch

| helper（`backend/temples/services/concierge_history.py`） | anonymous | authenticated（per candidate） |
| --- | --- | --- |
| `classify_shrine_action_state`（:26-71） | returns `"none"` at :27-28 | up to 5 `.exists()`: reflection, visit, favorite, route_open, detail_view. A user with no history runs all 5 |
| `calculate_shrine_behavior_signal_breakdown`（:124-233） | returns zeros at :125-134 | 8 queries: detail_view `first` + `count`, route_open `first` + `count`, favorite / visit / reflection / action_completed `first` |
| `build_recent_reflection_hint`（:303-322） | returns `None` at :309-310 | 1 query（`select_related("shrine")`） |
| **total** | **0** | **14** for a user with no history（fewer once `classify` short-circuits） |

All queries are sequential, inside a Python `for` loop, with no batching, caching or concurrency. Nothing else in the
loop touches the DB or the network: `build_recommendation_reason`, `_attach_reason_source`,
`_apply_soft_signal_highlights`, `_resolve_direction_bonus` and the Channel B helpers have no ORM or HTTP calls（Code
grep）, which the measurement confirms.

### 4.2 Timing model

| | anonymous | authenticated |
| --- | --- | --- |
| queries in the enrichment loop | 0 | 20 × 14 = 280 |
| expected time | in-process only → ≈ 0.09 s（observed） | 280 × RTT; RTT ≈ 70 ms → ≈ 19.6 s; observed 19.7–20.4 s |
| spacing between `attach_breakdown` lines | ≈ 4–5 ms | ≈ 14 × RTT ≈ 1 s（observed） |

The ≈ 70 ms per query is **inferred** from the observed 1 s / 14 queries. The production DB host / region and the Render
→ DB round-trip time are not recorded in the repository（Hypothesis H-1）. A cross-region round trip（for example
Render Singapore to a DB in another region）would fit this. Small user tables mean execution time is negligible
compared with the round trip.

### 4.3 Local measurement（not committed）

A throwaway pytest under the session scratchpad ran `_attach_chat_rec_enrichment` on 20 freshly created shrines. It used
CI-equivalent settings: Postgres 16, `DISABLE_GIS_FOR_TESTS=1`.

```text
PROBE anonymous_queries=0 authenticated_queries=280 per_candidate=14.0
PROBE by_table= {temples_actionevent: 20, temples_favorite: 40, temples_shrineinteractionlog: 120,
                 temples_shrinereflection: 60, temples_visit: 40}
```

Local loopback latency is far below 1 ms, so absolute time is not representative. The query count is.

### 4.4 Production confirmation available to the owner（read-only, no new traffic）

In Render logs, for each slow `[concierge/perf] step=recommend … elapsed≈20` line, the following
`[concierge/chat] identity_state authenticated=` line should read `True`. For ≈ 0.09 s lines it should read `False`. A
single counter-example（slow + anonymous）would falsify this root cause.

---

## 5. Why about one second per candidate

Each candidate costs a fixed number of sequential round trips: 14 for a user with no history, and fewer as soon as
`classify_shrine_action_state` finds a matching row. The work is serial in one request thread, so the gaps between
`attach_breakdown` lines are almost constant. They scale with RTT, not with candidate content.

No retry, sleep, lock wait or external HTTP call is involved:

- the code has no `sleep` / `requests` / `httpx` in these modules;
- `select_for_update` exists only in `append_chat`（`concierge_history.py:367-372`）, which runs **after** the recommend
  phase.

---

## 6. Frontend result failure

### 6.1 Facts

| item | evidence |
| --- | --- |
| HTTP client | `useConciergeChat.send` → `postConciergeChat` → `apiPost` → axios instance without `timeout`（`lib/api/concierge.ts:40`, `lib/api/http.ts:30-33`, `lib/api/client.ts:5-8`）. axios default = no client timeout |
| aborts / watchdogs | none in `ConciergeClientFull.tsx` or `features/concierge/*`（grep: the only `setTimeout`s are UI / localStorage helpers, `:718`, `:744`） |
| BFF | `app/api/concierge/chat/route.ts`: pass-through of status / body / cookies; no `maxDuration`; a refresh-and-retry path only on upstream 401 |
| production sample | one `POST /api/concierge/chat/` in the 1-hour window: request id timestamp → `[BFF_CHAT_PROXY] status: 200` ≈ **22.6 s**, then `[BFF_CHAT_RETURN] normal`（Prod log; the duration is read from Vercel's request-id timestamp — an inference about the id format） |
| error card | shown when `!isBusy && !isFiltering && !entryValidationError && !!error && !hasCandidates`（`ConciergeClientFull.tsx:1547`）; text "うまく取得できませんでした"（:2062） |
| how `error` is set | only in the hook's `catch`（`hooks.ts:408-431`）. The `try`（:350-407）wraps the HTTP call **and** `normalizeRecommendations`, `normalizeConciergeResponse`, analytics tracking, `persistBirthday` and every `options.on*` callback, including the page's long `onUnified` handler |
| logging | only axios errors are logged（`CONCIERGE_CHAT_ERROR`, :413-420）. A non-axios exception sets the error silently |
| concurrency | `send` sets `sending` but does not refuse a second concurrent call; the `catch` emits `onUnified({ ok:false, recommendations: [] })`, which can overwrite a successful result if it settles later |

### 6.2 Conclusion and hypotheses

A 22 s response does **not** cause the failure through a timeout: there is none on the client, and the BFF returned
200 after 22.6 s. The exact trigger cannot be determined from server logs, because the only frontend failure branch
records nothing for non-HTTP errors. Ranked hypotheses:

| id | hypothesis | consistency with "Django 200 + BFF 200 + error shown" | how to confirm |
| --- | --- | --- | --- |
| HF-1 | an exception thrown **after** the 200 inside the `try`（normalisation or the page's `onUnified` / navigation logic）is caught and shown as a failure | fully consistent; no server-side trace by design | browser console / a non-axios error log in the `catch`（§7 F-2） |
| HF-2 | a transport failure between Vercel and the browser after the BFF finished（mobile backgrounding, network change, connection reset）→ axios "network error" | consistent; more likely the longer the request（22 s vs 2–3 s）, so it **correlates** with the slow path without being a timeout | the UI message suffix "(network error)"; browser console `CONCIERGE_CHAT_ERROR` |
| HF-3 | a concurrent second `send` fails or settles later and its `catch` overwrites the first success with empty recommendations | consistent only if the second request failed or is still pending; the long window makes duplicates more likely | Django / BFF logs showing two chat requests in one session within ~22 s |
| HF-4 | a Vercel function duration limit | **not consistent**: the BFF logged its 200 return after 22.6 s | — |

---

## 7. Minimal correction proposal（not implemented）

| id | change | preserves quality because | scope |
| --- | --- | --- | --- |
| B-1 | before the enrichment loop, batch-load the authenticated user's history for the ≤ 20 candidate shrine ids. Use one aggregate query per table: interaction logs（count + latest per shrine and action type）, favorite / visit（`status="added"`）/ reflection / action_completed latest per shrine, and the latest reflection per shrine for the hint. Pass the precomputed maps to `_attach_breakdown`, so the three helpers read from the map instead of querying | the same inputs（counts, latest timestamps, `_recency_multiplier`, same filters）produce the same signals, `action_state` and hint; ranking and scores are unchanged by construction; anonymous behaviour is unchanged | `concierge_history.py`（new batch function）, `concierge_chat_ranking.py`（optional prefetched-map parameter）, `concierge_chat.py`（one call before the loop）; ≈ 280 → ≈ 6 queries per request |
| F-1 | make `send` ignore a second call while one is in flight, or discard results from superseded requests（a request token） | no duplicate recommendations; no retries added | `features/concierge/hooks.ts` |
| F-2 | split the `try`: HTTP errors vs post-processing errors. Log the latter with a safe, value-free message（error name, stage）, without consultation text or tokens | changes no data; makes HF-1 observable | `features/concierge/hooks.ts` |

Not recommended: raising timeouts（none exists to raise）, client retries（may duplicate threads or recommendations）,
reducing the pool below 20（changes ranking input）.

---

## 8. Regression test plan

| # | test | layer |
| --- | --- | --- |
| R-1 | `_attach_chat_rec_enrichment` with 20 candidates: anonymous → 0 queries; authenticated → a **constant** query count independent of the candidate count（`django_assert_max_num_queries`）; fails today with 280 | backend |
| R-2 | equivalence: for a user with a mix of detail views, route opens, favorites, visits（added / not added）, reflections and completed actions across candidates and recency buckets, the batched path yields identical `breakdown_detail`, `_score_total`, `action_state`, `reflection_hint` and final order to the current per-candidate path（golden fixture captured before the change） | backend |
| R-3 | fast path unchanged: anonymous result byte-identical before and after | backend |
| R-4 | `step=recommend` elapsed stays bounded with simulated per-query latency（a DB wrapper adding a fixed delay per execute）: 20 candidates × delay no longer scales linearly | backend |
| R-5 | hook: an HTTP 200 whose post-processing throws → error logged with the stage, no consultation text in the log | web |
| R-6 | hook: a second `send` during an in-flight request is ignored or superseded; a late failure cannot clear an earlier success | web |
| R-7 | hook: a slow（22 s, fake timers）successful response renders recommendations and no error card | web |
| R-8 | existing Concierge / Compass suites（`web-contract`, direction E2E, backend Concierge tests）unchanged | existing |

---

## 9. Unresolved and constraints

- **H-1**: production DB location and round-trip time are not recorded; the 70 ms figure is inferred from 1 s / 14
  queries. §4.4 gives a read-only check that can falsify the root cause.
- The frontend trigger（HF-1…HF-3）needs browser-side evidence; server logs cannot distinguish them today（F-2 closes
  this gap）.
- Vercel runtime logs are retained for 1 hour（Hobby）. Render logs were not accessible in this session.
- Nothing was changed, deployed or retried. No consultation text, tokens or IPs were read or recorded.
