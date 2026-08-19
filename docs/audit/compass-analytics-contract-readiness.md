> **Status: Audit / Historical（Phase 8 — Compass Analytics Contract Readiness Audit）**
>
> This document is a docs-only, point-in-time audit. It proposes a target Analytics Contract for Compass; it does not implement any event, does not modify `apps/web/src/lib/analytics/**`, backend instrumentation, Recommendation, Compass behavior, Favorite/Visit/Reflection, entitlement, billing, pricing, models, or migrations. Nothing in `docs/analytics/` is edited by this PR.
>
> Every substantive claim is tagged **FACT** (verified in code as of this audit), **CONTRACT** (an existing binding rule quoted from an Active doc), **INFERENCE** (a conclusion drawn by combining verified facts), **HYPOTHESIS** (an untested product/analytics judgment), or **OPEN DECISION** (a question this audit cannot and does not resolve).

# KAMI MUSUBI — Compass Analytics Contract Readiness Audit (Phase 8)

## 1. Executive Summary

**Compass today has zero analytics instrumentation, and Home has zero analytics instrumentation.** (FACT, re-verified against current code, §3.) Everything in this document is a *proposal* for what would need to exist to answer seven specific, currently-unanswered product questions (§0 goal, restated in §4) — not a description of anything shipped.

**The central finding that shapes this whole contract: KAMI MUSUBI already has a mature, tested recommendation-analytics system (Concierge's `recommendationInstanceId`, `trackCardEvent`, `shrine_detail_view`, `favorite_click`/`shrine_decision`, `visit_done`, `reflection_prompt_view`/`reflection_saved`) — and Compass can reuse almost all of it.** The gaps are narrow and specific, not architectural:

1. Home has no instrumentation at all — needs a minimal impression/click pair.
2. The existing `source`/`ctx` typing is fragmented across five different narrow unions, none of which include `"home"` or `"compass"` — needs extension, not replacement.
3. `Favorite`/`Visit`/`Reflection` events currently **hardcode** `source: "shrine_detail"` regardless of how the user actually arrived — they do not read the page's own `ctx` value, even though `Shrine Detail`'s view event already threads one. This is a property-plumbing gap, not a missing event.
4. Compass has no equivalent of Concierge's `recommendation_instance_id` — needs one, but it can be a stateless, response-only identifier (no DB write), mirroring the ephemeral character of Compass itself.
5. Cross-session attribution (Compass → Favorite/Visit days or weeks later) is **not achievable** with analytics-context alone and is correctly out of scope for this phase — classified explicitly as a **MEASUREMENT GAP**, not solved by inventing a fake identifier.

**No new database field, table, or migration is proposed anywhere in this document.** Every proposed mechanism is either (a) an analytics event/property, (b) a query-parameter/prop extension already structurally identical to the existing `ctx=map|concierge` pattern, or (c) a stateless per-request identifier computed and returned in an API response, never persisted.

**Final Classification: B — READY WITH MEASUREMENT GAPS** (§27). The contract is well-defined and buildable from existing patterns; the gaps that remain (cross-session attribution, a canonical source enum) are honestly out of reach for an analytics-only phase, not blockers to shipping the rest.

---

## 2. Source-of-Truth Hierarchy

Per the task's required priority and `docs/product/README.md`/`docs/analytics/README.md`'s own rules (re-verified, FACT):

1. Active/canonical Product Contracts (`docs/product/compass-product-contract.md`, `compass-mvp-runtime-contract.md`, `premium-experience.md` — unchanged since the prior audit chain, §2 of `compass-runtime-personal-continuity-boundary.md`).
2. Current production Analytics contracts/code — `apps/web/src/lib/analytics/**`, `packages/shared/directionAnalytics.ts`, backend `api_views_compass.py` and `compass_recommendation_orchestrator.py` (this audit re-read all of these directly; see §3).
3. Current tests (`recommendationInstanceIdPropagation.test.tsx` and siblings, confirmed FACT to exist and pass as of this audit's research pass).
4. Merged Compass audits (#2484, #2485, #2486) — used as historical record of decisions already made, not re-litigated.
5. Reference/archive docs — `docs/analytics/analytics-card-events.md` and `card-ctr-aggregation.md` are both marked `Status: Archive` (confirmed, FACT) and are cited here only as historical context, never as current contract.

**Doc placement decision for this document (CONTRACT-application, not itself a new rule):** `docs/analytics/README.md` states Active documents hold "現行のEvent、Payload、KPIおよび計測契約" and requires event/payload changes to update contract docs "同じPRで" as the implementation. Since this document defines a **target** contract for events that do not exist in code yet, and this phase explicitly forbids implementation, it cannot honestly be filed as an Active `docs/analytics/` contract — doing so would create exactly the kind of doc/code mismatch this repo's own conventions warn against (the `comparison_preview` event found declared-but-never-called in `billing.ts`, §3.6, is a live example of what happens when a doc and code drift apart). This document is therefore filed under `docs/audit/` as a **readiness proposal**; the recommendation (§25, PR-A) is that the actual `docs/analytics/compass-analytics-contract.md` Active document gets created *in the same PR* as the first real instrumentation, populated from this audit's content once implemented and verified — not before.

---

## 3. Current Analytics Inventory

All **FACT**, re-verified against current `develop` code (not assumed from prior audits).

### 3.1 Home
**Zero instrumentation.** No `track`/`capture`/`posthog` call exists anywhere under `apps/web/src/features/home/**`. `HomeCompassSection.tsx` is a plain `<Link href="/compass">` with no `onClick` handler — no event fires on click today.

### 3.2 Concierge / Recommendation
| Event | Trigger | Key properties |
|---|---|---|
| `concierge_result_impression` | new result item mount (dedup'd) | — |
| `card_view` / `card_partial_view` / `card_teaser_view` (via `trackCardEvent`) | per-card mount (dedup'd) | `cardId`, `source: AnalyticsSource`, `accessLevel`, `visibility`, `shrineId`, `recommendationRank`, `recommendationInstanceId`, `resultSetId`, `threadId`, `sessionId` |
| `save_prompt_view` / `save_prompt_click` | prompt shown/clicked | — |
| `premium_preview_click` | premium CTA click | — |
| `shrine_detail_transition` | "神社の詳細を見る" click | `recommendationInstanceId` and others |

`AnalyticsSource` (`cardEvents.ts:5`) is a closed 4-value union: `"concierge_result" | "shrine_detail" | "billing_upgrade" | "mypage"`. It does not include `"home"` or `"compass"`.

### 3.3 Shrine Detail
`shrine_detail_view` (`ShrineDetailViewTracker.tsx`) derives `source` from a `ctx` prop, itself parsed from the page's `ctx` URL query param via `normalizeCtx` (`page.tsx:55-57`), which currently accepts **only** `"map" | "concierge"` — any other value (including a would-be `"compass"` or `"home"`) normalizes to `null` and falls into the default `"shrine_detail"` bucket. `ShrineDetailArticle.tsx` separately fires `card_view`/`card_partial_view` with `source` **hardcoded** to `"shrine_detail"`, ignoring `ctx` entirely.

### 3.4 Favorite / Visit / Reflection
All three are instrumented (contrary to what one might assume from Compass's zero-instrumentation state):
- **Favorite**: `ShrineSaveButton.tsx` fires `favorite_click` (always) and `shrine_decision` (action: "save", on success) via raw `track()`, both including `recommendationInstanceId`. No `source` property at all.
- **Visit**: `ShrineDetailArticle.tsx:759` fires `visit_done` via `trackSearchEvent` immediately after a successful visit creation, `source` **hardcoded** to `"shrine_detail"`, plus `shrineId`, `threadId`, `historyTheme`, `accessLevel`, `mode`, `recommendationInstanceId`.
- **Reflection**: `ShrineReflectionPrompt.tsx` fires `reflection_prompt_view` (mount) and `reflection_saved` (submit), both `source` **hardcoded** `"shrine_detail"`, both carrying `recommendationInstanceId`.

**None of these three can currently distinguish a Compass-originated (or Home-originated) shrine relationship from any other**, even within the same page session — this is the concrete gap §12–§14 propose to close.

### 3.5 Direction
Re-verified accurate against current code (6 events in `DIRECTION_EVENT_NAMES`, `packages/shared/directionAnalytics.ts:1-8`, all with live call sites). This is the **only** event family with a runtime-enforced allowlist (`sanitizeDirectionEventPayload`, backed by `directionAnalyticsForbiddenKeys.json`) — every other event family (Card, Search, Billing, Retention) is TypeScript-typed only, with **no runtime validation** that a value matches its declared union. This matters directly for §22 (Privacy) — Direction's pattern is the one to imitate for any Compass property carrying sensitive-adjacent data.

Prohibited-attributes list, quoted exactly (`docs/analytics/direction-events.md:20-28`, confirmed unchanged):
> 緯度・経度、住所、駅名、都道府県名、検索語 / 生年月日、相談文、プロフィール入力 / 実際の方位、吉凶、予定日そのもの / shrine名、個別ユーザーを方位評価する属性

### 3.6 Premium / Billing
`upgrade_click`, `checkout_started`, `checkout_success`, `premium_active` (all via `trackBillingEvent`). `comparison_preview` is **declared in the type but never actually called anywhere** — a live doc/code discrepancy, flagged here as evidence for why this audit avoids writing a premature Active contract (§2). `premium_history_comparison_view`/`_click` exist separately via `trackRetentionEvent`. **None of these are touched or duplicated by this audit** — Compass has no Premium surface today (§13 of `compass-free-premium-boundary.md`, unaffected).

### 3.7 Card Analytics (generic system)
The live, current system is `trackCardEvent` (`cardEvents.ts`) — shared by Concierge and Shrine Detail, **not used anywhere in Home**. `docs/analytics/analytics-card-events.md` and `card-ctr-aggregation.md` are both `Status: Archive` — historical only, not contract.

### 3.8 Event registry
**No central event-name registry exists.** Each domain module (`cardEvents.ts`, `searchEvents.ts`, `billing.ts`, `retentionEvents.ts`, `directionAnalytics.ts`) defines its own separate TypeScript union; the base `track()` function accepts any raw string with no compile-time or runtime constraint. Extending for Compass means adding to (or alongside) the closest-shaped existing module, not touching one shared file.

### 3.9 Identity
`analyticsSessionId` (random `crypto.randomUUID()`, persisted in `localStorage`) is the only identity value attached client-side. **No `posthog.identify()` call exists anywhere** (frontend or backend, re-verified with a fresh repo-wide grep). **The backend sends zero PostHog events of any kind** — backend "analytics" (`ActionEvent`, `behavior_funnel.py`, `concierge_observability.py`) is internal Django-DB-only telemetry, entirely separate from PostHog. No `user_id` is ever attached to a PostHog event today, for any surface, Compass or otherwise.

### 3.10 Recommendation identity contract (mature, reusable)
`recommendation_instance_id` (backend) / `recommendationInstanceId` (frontend) is an established, heavily-tested identity concept — set server-side in `api_views_concierge.py` from the per-request `rid`, propagated through the entire Concierge→Shrine Detail→Favorite→Visit→Reflection chain, with dedicated contract tests. **This is Concierge-specific today** — Compass has no equivalent (§9, §11). `resultSetId` is a separate, deliberately lesser concept: a frontend-only ephemeral dedup key, never persisted, explicitly not treated as a session identifier in existing docs.

### 3.11 Compass backend result states (re-verified directly from code, not assumed)
`backend/temples/services/compass_recommendation_orchestrator.py:47-51` — five distinct states actually exist:

```
STATE_INVALID_PURPOSE               = "invalid_purpose"
STATE_DIRECTION_FILTER_UNAVAILABLE  = "direction_filter_unavailable"
STATE_DIRECTION_ZERO_CANDIDATES     = "direction_zero_candidates"
STATE_EVIDENCE_ZERO_CANDIDATES      = "evidence_zero_candidates"
STATE_RECOMMENDATION_SUCCESS        = "recommendation_success"
```

Plus an unstructured `{"state": "error"}` / HTTP 500 path from the view's own exception handler (`api_views_compass.py:67-72`) — note this is a **different response shape** (bare dict, no `purpose`/`direction_context`/`recommendations` keys) than the five states above, which all share the full `body` shape. **`STATE_EVIDENCE_ZERO_CANDIDATES` is a fifth state not mentioned in this task's own funnel description** (§8 of the task listed only `direction_zero_candidates`, not `evidence_zero_candidates`) — flagged explicitly per the task's own instruction not to collapse states: these two "zero candidates" states have different causes (no shrine survives the direction filter vs. direction-filtered candidates exist but the Evidence Gate rejects all of them) and must stay distinct in the contract (§10).

---

## 4. Compass Funnel

```
Home
→ Compass discovery      [REQUIRED — impression: OPTIONAL, click: REQUIRED]
→ Compass entry          [REQUIRED]
→ purpose selected       [NOT NEEDED as a separate event — derivable from Activation]
→ origin ready           [NOT NEEDED as a separate event — derivable from Activation]
→ birthdate ready        [NOT NEEDED as a separate event — derivable from Activation]
→ Compass submit         [REQUIRED — this is "Activation", §6]
→ Compass result         [REQUIRED — this is "Completion", §6, with result_state, §10]
→ Recommendation exposure [REQUIRED — reuse card_view pattern]
→ Shrine Detail          [REQUIRED — reuse shrine_detail_view, extend ctx]
→ Favorite               [REQUIRED — reuse favorite_click/shrine_decision, extend source]
→ Visit                  [REQUIRED — reuse visit_done, extend source]
→ Reflection             [DERIVABLE — reuse reflection_prompt_view/reflection_saved unchanged, join via existing identifiers]
```

**Why purpose/origin/birthdate "readiness" are not separate events (HYPOTHESIS, reasoned):** `CompassClient.tsx` currently **blocks submission client-side** until purpose, origin, and birthdate are all valid (`if (!purpose || !birthdate.trim() || !origin) return`, FACT) — there is no current UI state where a partial-but-attempted submission is distinguishable from "still filling the form." Given the task's own Primary Goal ("not track every click"), instrumenting three additional pre-submit milestones would violate that goal for a form-completion signal that the Activation event's own payload already captures completely (purpose slug, origin_mode, and an always-true `has_birthdate` at the moment Activation fires, since submission is gated on it today). If the client-side gate is ever loosened to allow partial submission attempts, this section should be revisited — not before.

---

## 5. Event Reuse Matrix

| Compass funnel step | Reuse existing? | Mechanism |
|---|---|---|
| Home discovery (impression) | New, but same *shape* as `trackCardEvent` | Extend `AnalyticsSource` with `"home"`, or a lightweight sibling event — see §6 |
| Home discovery (click) | New, minimal | Same as above |
| Compass entry | New (Compass has no page-view event of any kind today) | Minimal, one-off event |
| Compass Activation (submit) | New (no Compass event exists) | New event, payload modeled on existing Direction/Card payload minimalism |
| Compass Completion (result) | New | Same event as Activation, or immediately-following event carrying `result_state` (§10) |
| Recommendation exposure | **Reuse `card_view`/`trackCardEvent`** | Extend `AnalyticsSource` with `"compass"`; Compass supplies its own `recommendationInstanceId` (§9) in place of Concierge's |
| Shrine Detail | **Reuse `shrine_detail_view`** | Extend `normalizeCtx` to accept `"compass"` alongside existing `"map"`/`"concierge"` |
| Favorite | **Reuse `favorite_click`/`shrine_decision`** | Thread the page's `ctx`-derived source into `ShrineSaveButton.tsx`'s existing `track()` calls (currently missing entirely, not just hardcoded) |
| Visit | **Reuse `visit_done`** | Change `source` from hardcoded `"shrine_detail"` to the page's actual `ctx`-derived value |
| Reflection | **Reuse `reflection_prompt_view`/`reflection_saved`, no change needed** | Same-page correlation via existing `recommendationInstanceId`/session context already suffices (§15) |
| Same-month repeat | **Derive from Activation/Completion events**, no new event | Aggregate by `analyticsSessionId`/`user_id` + calendar month |
| Month-over-month return | **Derive from Activation/Completion events**, no new event | Same, aggregated across months (§17) |

**No planned Compass metric requires a brand-new event where an existing canonical event can safely carry `source=compass` instead** — this satisfies §22/§23's explicit anti-duplication instruction. The only genuinely new events are the three that have no existing analogue at all: Home discovery, Compass entry, and Compass Activation/Completion.

---

## 6. Required New Events

Minimal set, consistent with §23's "fewer canonical events + clear properties" principle:

1. **`home_compass_entry_click`** (or: extend `trackCardEvent` with `source: "home"`, `cardId: "compass_entry"`) — fires on click of the Home Compass section link. *(Impression variant OPTIONAL — see §4; since the section renders unconditionally for all users today, per-user Home traffic volume, if ever instrumented, would approximate the impression denominator without a dedicated event.)*
2. **`compass_entry`** — fires on `/compass` page mount. Property: `referrer_source` (coarse: `"home" | "direct" | "other"`, derived from how the page was reached, not full URL/referrer string).
3. **`compass_result`** — fires once per successful or failed submit, carrying `result_state` (§10) as the single source of truth for success/failure classification (task's own suggested design, adopted). This event **is** both "Activation" and "Completion" in one — see §6 rationale below.

**Why one event, not two ("Activation" then "Completion" separately):** INFERENCE — Compass's own request is synchronous and stateless (submit → immediate result, no intermediate pending state a user can abandon mid-flight the way a multi-step form could). A separate Activation event firing before Completion would, in practice, always pair 1:1 with a Completion event except for network failures already coverable by treating "activation fired, no completion" as its own diagnostic signal without a dedicated second event. Two events here would be exactly the "track every click" pattern the task's Primary Goal warns against. **OPEN DECISION, flagged explicitly**: if product wants to measure network-level submit failures (request never reached the server) as distinct from `result_state: "error"` (request reached the server, which then failed), that would justify a second event — not decided here, no evidence of need found.

No other new events are proposed. Everything downstream (Recommendation exposure, Shrine Detail, Favorite, Visit, Reflection) reuses existing events per §5.

---

## 7. Event Property Contracts

| Event | Property | Type | Notes |
|---|---|---|---|
| `home_compass_entry_click` | `source` | `"home"` (new enum value) | |
| `compass_entry` | `referrer_source` | `"home" \| "direct" \| "other"` | coarse only |
| `compass_result` | `result_state` | `"invalid_purpose" \| "direction_filter_unavailable" \| "direction_zero_candidates" \| "evidence_zero_candidates" \| "recommendation_success" \| "error"` | mirrors backend states exactly (§3.11), all six kept distinct |
| `compass_result` | `purpose` | canonical `need_tag` slug | INFERENCE: consistent with existing precedent — Concierge analytics already send canonical-taxonomy-derived properties (`historyTheme`, `consultationAxis`); purpose is a fixed enum, not free text, so this does not create a new PII exposure category |
| `compass_result` | `origin_type` | `"device" \| "manual" \| "prefecture" \| "unavailable" \| "denied"` | reuses the same coarse-categorical philosophy as Direction's existing `origin_type`/`has_origin` allowlisted properties (§3.5) — never precise coordinates |
| `compass_result` | `has_birthdate` | boolean | HYPOTHESIS-flagged: currently always `true` at this event, since client-side submission is gated on it (§4); included for schema stability if the gate is ever loosened |
| `compass_result` | `purpose_changed` | boolean | per task §18 — whether this submit's purpose differs from the same session's immediately-previous submit; never the old/new values themselves |
| `compass_result` | `origin_mode_changed` | boolean | same pattern, origin only |
| `compass_result` | `recommendation_instance_id` | new, Compass-scoped, stateless (§9) | replaces Concierge's `rid`-derived id for this surface |
| `compass_result` | `shrine_ids` / per-shrine `rank` (via reused `card_view`) | existing shape | see §11, reused unchanged |
| Reused `card_view` (Recommendation exposure) | `source` | `"compass"` (new enum value) | |
| Reused `shrine_detail_view` | `ctx` / `source` | `"compass"` (new accepted value in `normalizeCtx`) | |
| Reused `favorite_click`/`shrine_decision`, `visit_done`, `reflection_*` | `source` | inherits page's `ctx`-derived value, including `"compass"` when applicable | see §12-§15 for the plumbing gap this closes |

**Never included, anywhere, per §24 (Privacy):** birthdate value, exact coordinates, raw address/station text, purpose free text (only the canonical slug), Reflection `answer` content, any note/free-text field, email, nickname.

---

## 8. Provenance Model

**Smallest viable contract, per the task's own instruction to prefer analytics context over DB schema:**

- **`source`** — the only property genuinely required. Answers "did this action originate from the Compass experience?" Values needed: extend existing fragmented unions with `"compass"` (and `"home"` for the discovery step) rather than inventing a new canonical enum from scratch — INFERENCE: since no canonical enum exists today (§3.8, confirmed fragmented across five separate unions), this audit does **not** propose creating one as a prerequisite; that would be new, unrelated scope. Each existing union gets the minimal addition it needs.
- **`recommendation_instance_id`** — needed (§9), but as the *existing* concept applied to Compass, not a new property category.
- **NOT needed**: `previous_source`, a separate `context` object, or `entry_surface` as a distinct property from `source` — INFERENCE: these would be redundant with `source` for Compass's actual shape (a single, direct, same-page entry point), and adding them would violate §23's "what product decision becomes possible because this exists?" test. If a future surface has multi-hop provenance (e.g., Compass → saved for later → returned via a different surface), that is explicitly the cross-session case already classified as a MEASUREMENT GAP (§12-§13) that no property design can solve without persistence — out of this phase's scope.

**This keeps Compass an entry surface, never an owner** — `source: "compass"` is a property value on events that already belong to Recommendation/Shrine Detail/Favorite/Visit/Reflection's existing contracts, not a new Compass-owned event family shadowing them.

---

## 9. Identity / Anonymous Measurement

- Anonymous session: **existing `analyticsSessionId`** (localStorage UUID), reused unchanged — Compass requires no login (FACT, `AllowAny`), so this must remain sufficient on its own for anonymous measurement, and it already is used consistently across every other domain (§3.9).
- Logged-in Free/Premium distinction: **not attached to any analytics event today, for any surface** (§3.9) — this is a pre-existing gap this audit does not create and is not in scope to fix; Compass inherits the same limitation every other surface already has. Cohort-level Free-vs-Premium breakdowns of Compass usage are therefore **not currently possible** from PostHog data alone; only DB-level (billing_state) joins could provide it, which is outside Analytics' responsibility (§23).
- `recommendationInstanceId`: needs a **Compass-specific value**, generated **stateless and response-only** — computed at request time in `CompassRecommendationsView.post()` (e.g., a UUID minted alongside the existing `result.state` computation) and returned in the JSON body for the frontend to attach to `compass_result` and all downstream reused events, exactly mirroring how `rid` already works for Concierge. **No DB write, no new table, no migration** — this satisfies the task's explicit "no persistence schema" constraint while still providing the same-request correlation key every downstream reused event already expects.
- `threadId`: **not applicable, and must not be faked.** Compass has no `ConciergeThread` (FACT, confirmed across the full prior audit chain). Reused events (`card_view`, `shrine_detail_view`, `favorite_click`, `visit_done`, `reflection_*`) should simply omit `threadId` when `source: "compass"`, relying on `recommendationInstanceId` alone as the correlation key for that flow — consistent with how `resultSetId` already exists as a fallback when `recommendationInstanceId` is unavailable in other flows (§3.10), so the reused events' code paths already tolerate a missing `threadId`.
- Login is never required to measure Compass use — confirmed by construction (all of the above works entirely off `analyticsSessionId` and the new stateless `recommendation_instance_id`, neither of which requires authentication).

---

## 10. Result-State Semantics

Per §3.11's re-verified backend states, mapped 1:1, no collapsing:

| `result_state` | Counts as Activation success? | Counts as Completion? | In error rate? | In Recommendation CTR denominator? |
|---|---|---|---|---|
| `recommendation_success` | Yes | Yes | No | **Yes** |
| `direction_zero_candidates` | Yes (valid input, valid computation) | Yes (a definitive result state, not a failure) | No | **No** — zero candidates means no recommendation was exposed to click through on |
| `evidence_zero_candidates` | Yes | Yes | No | **No**, same reasoning, kept distinct from the above per §3.11's finding that these are causally different states |
| `direction_filter_unavailable` | Yes (input was valid) | Yes (a defined, reachable outcome) | HYPOTHESIS: arguably yes for *system* error-rate tracking (something upstream couldn't compute), but not user-error — recommend a **separate** `system_unavailable_rate` rollup distinct from `invalid_purpose`-style user error, rather than merging both into one "error rate" | **No** |
| `invalid_purpose` | **No** — this is a client/input validation failure, not a valid activation | No | HYPOTHESIS: track separately as an input-validation rate, not blended into system error rate (different fix: form validation vs. backend health) | **No** |
| `error` (HTTP 500, unstructured) | No | No | **Yes** — this is the true system-error bucket | **No** |

**This audit explicitly does not collapse `direction_filter_unavailable` and `direction_zero_candidates`/`evidence_zero_candidates`**, per the task's direct instruction — all three are kept as distinct `result_state` values with distinct interpretive rules above, even though a naive implementation might be tempted to bucket "no direction signal" and "no shrines" together.

---

## 11. Recommendation Attribution

- `recommendationInstanceId` in Compass flow: **does not exist today**; proposed as a new, stateless, response-only identifier (§9).
- `resultSetId`: **not needed for Compass** — INFERENCE: it exists in the Concierge world specifically as a fallback dedup key when `recommendationInstanceId` might be absent across a multi-turn thread; Compass's single-request, threadless shape means the new `recommendation_instance_id` alone is sufficient without needing the fallback concept at all.
- `shrineId` and `rank`: **available** — the backend response already includes `result.recommendations` (a list; per orchestrator code, ranked); the frontend already has the pattern to extract `shrineId`/`recommendationRank` per item from an identical Concierge response shape, so reusing `card_view` for Compass's recommendation list requires no new extraction logic, only wiring.
- `source="compass"`: **can be added to `trackCardEvent`'s existing `AnalyticsSource` union** — confirmed structurally trivial (§3.2, it's a closed TS union with 4 existing values; a 5th is additive, not a breaking change).
- Are current Recommendation events too Concierge-specific to reuse? **No, with one exception.** `card_view`/`trackCardEvent`'s payload shape (`cardId`, `source`, `shrineId`, `recommendationRank`, `recommendationInstanceId`, `resultSetId`, `threadId`, `sessionId`) is generic enough to carry Compass data once `source` is extended and `threadId` is treated as optional/omittable (§9). The exception is `concierge_result_impression`, which is Concierge-named and Concierge-scoped by its own event name — this one should **not** be reused for Compass; `card_view` (the more generic sibling) is the correct reuse target instead.

**Conclusion: document as reuse-with-extension, not a contract mismatch.** No new Recommendation-family event is required.

---

## 12. Shrine Detail Attribution

**DIRECT attribution is achievable, same-navigation, no session ambiguity.**

- Existing `shrine_detail_transition` event (fired from within Compass results, mirroring Concierge's existing pattern of firing it from `ConciergeSectionsRenderer.tsx`) plus extending `normalizeCtx` (`page.tsx:55-57`) to accept `"compass"` alongside its current `"map" | "concierge"` values — this closes the loop so `shrine_detail_view`'s `ctx`-derived `source` correctly reads `"compass"` when a user arrives via a Compass result link.
- `shrineId`: available directly from the clicked recommendation.
- `rank`: available, same source as §11.
- `recommendationInstanceId`/`resultSetId`: the new Compass `recommendation_instance_id` (§9) carries through via the same URL-param or in-memory hand-off pattern already used for the Concierge case (confirmed structurally identical — this is the existing `ctx=map|concierge` mechanism, just adding a third accepted value).
- Anonymous compatibility: **yes**, unaffected — this entire mechanism is URL/prop-based, requires no identity beyond `analyticsSessionId`.
- Duplicate tracking risk: **low** — `ShrineDetailArticle.tsx`'s separate `card_view`/`card_partial_view` calls currently hardcode `source: "shrine_detail"` regardless of `ctx` (§3.4) — this is a **required fix**, not a new risk: without it, a Compass-originated Shrine Detail page view would emit `shrine_detail_view{source:"compass"}` from one component but `card_view{source:"shrine_detail"}` from another, on the same page load — an internal contradiction. Both must read from the same `ctx`-derived value.

**Classification: this metric is well-suited to answer "does Compass create real shrine exploration" — READY once the `normalizeCtx` extension + the `ShrineDetailArticle.tsx` hardcoding fix both ship (§25, PR-C).**

---

## 13. Favorite Attribution

Evaluated against the task's five options (A-E):

- **A (durable DB provenance)**: rejected, per the task's explicit preference and consistent with `compass-runtime-personal-continuity-boundary.md` §6's conclusion (no DB persistence needed for provenance).
- **B (URL/query context)**: usable **only for the initiating page load** — if Favorite is clicked on the same Shrine Detail page reached via a Compass link (same navigation, `ctx=compass` present), this works, same mechanism as §12.
- **C (in-memory/session context)**: functionally the same as B for a single-page-session interaction — no meaningful difference for Favorite specifically, since favoriting typically happens on the same page view as arrival.
- **D (analytics event property only)**: **this is the recommended combination with B/C** — `ShrineSaveButton.tsx`'s existing `favorite_click`/`shrine_decision` calls currently carry **no `source` property at all** (§3.4) — the required fix is additive (add the property), not a rewrite.
- **E (not reliably measurable yet)**: **applies to any Favorite that happens in a later session** — the task's own example ("discover via Compass → leave → return later → favorite later") describes exactly this case, and per the prior audit chain (`compass-runtime-personal-continuity-boundary.md` §2, no anonymous→account claim mechanism, no cross-session identity linkage exists anywhere in this codebase), this is honestly **not solvable with analytics context alone**.

**Defined split:** `Compass → Favorite Rate (same-session)` — numerator: `favorite_click`/`shrine_decision` events carrying `source: "compass"` (via the same-page `ctx` threading fix), denominator: Compass Completion events with `result_state: "recommendation_success"`. **Cross-session Compass→Favorite is classified MEASUREMENT GAP, not estimated, not proxied.**

---

## 14. Visit Attribution

Same reasoning as §13, with a sharper caveat the task itself raises: a Visit is, by its nature, even more likely than a Favorite to happen in a **later** session than the Compass discovery (physically going to a shrine takes real-world time).

Classification per the task's four-tier scale:
- **DIRECT**: not available (no backend-persisted linkage, and even same-session "visit" would be an unusual same-sitting action for a physical-world event).
- **SESSION-LEVEL**: achievable **only** for the (likely rare) case where a Visit is logged in the same browser session as the Compass discovery (e.g., a user already near a shrine, discovers it via Compass, immediately marks a visit) — same `ctx`-threading fix as Favorite, extending `visit_done`'s currently-hardcoded `source: "shrine_detail"` (§3.4) to read the actual `ctx` value.
- **WEAK**: any Visit logged in a later session **cannot** be attributed even weakly without new persistence — this audit does not propose a weak-attribution heuristic (e.g., "last Compass session within N days") because it would fabricate a causal claim the data doesn't support.
- **NOT AVAILABLE**: cross-session, as above.

**Compass → Visit Rate is defined only at the SESSION-LEVEL tier**, with an explicit caveat in the KPI definition itself (§18) that this numerator will likely be small and should not be read as "true" Compass-driven visit rate — it measures only the same-session subset, by construction. This is the honest ceiling of what current architecture supports, per the task's explicit instruction not to claim causal attribution beyond it.

---

## 15. Reflection Attribution

- Is Visit→Reflection already measurable independently of Compass? **Yes.** `visit_done` and `reflection_saved` both already carry `recommendationInstanceId` and fire from the same `ShrineDetailArticle.tsx` page context (§3.4) — this transition is joinable today via existing identifiers, with zero Compass involvement required.
- **No new Compass-specific Reflection event is proposed** — per the task's explicit instruction to reuse rather than create one "unless Compass provenance is still reliably available and provides real decision value." Provenance *is* available at the SESSION-LEVEL tier (§14) via the same `ctx` threading fix, and no additional Reflection-specific mechanism is needed beyond what `visit_done`'s fixed `source` property (once un-hardcoded, §14) already carries — `reflection_saved` inherits the same session/page context it already correlates with `visit_done` today.
- Primary Personal Continuity validation question ("do users who move from Compass into real actions also continue into Reflection?") is answerable **only for the SESSION-LEVEL-attributed subset** — same honesty caveat as §14, not over-claimed.

---

## 16. Same-Month Engagement

**Same-Month Compass Repeat Usage** = a user/session (`analyticsSessionId`, or `user_id` where available) fires more than one `compass_result` event within the same calendar month.

- Measurable reliably: **yes**, using only existing/proposed event timestamps and `analyticsSessionId` — no new persistence needed.
- **Explicitly classified as an ENGAGEMENT KPI, not primary retention** — per the task's own instruction and consistent with `compass-runtime-personal-continuity-boundary.md` §16's prior finding: repeated same-month use may reflect purpose change, origin change, retry-after-zero-result, curiosity, or accidental repeat, none of which are retention signals on their own. `purpose_changed`/`origin_mode_changed` (§7) let this KPI be further segmented (e.g., "repeat due to exploration" vs. "repeat with identical inputs," a possible retry/confusion signal) without adding a new event.

---

## 17. Month-over-Month Return

**Primary retention hypothesis**, per the task's own framing and consistent with the prior audit chain's conclusion.

**Month-over-Month Compass Return** = a user/session with a `compass_result` event (any `result_state`, or `recommendation_success` only — see open decision below) in calendar month M and again in calendar month M+1 (or any later month, for a looser "eventual return" variant).

- Does current analytics identity survive across months? **Only weakly for anonymous users.** `analyticsSessionId` is `localStorage`-persisted, which survives across months **on the same browser/device**, but is lost on cache clear, private browsing, or a different device — HYPOTHESIS: anonymous month-over-month return is systematically **undercounted**, not overcounted, since the failure mode is losing the identifier, not double-counting. Logged-in users provide a genuinely stronger cohort **only if** a `user_id` is ever attached to analytics events — which, per §9, **does not happen today for any surface**, not just Compass. This is a pre-existing gap, not something this audit can resolve within Compass-only scope.
- **Calendar month vs. Compass solar-month index — explicit tradeoff, not silently chosen:**
  - **Calendar month (A)**: simpler, matches how analytics tooling (PostHog) natively buckets time, matches how "same-month repeat" (§16) is already defined here for consistency.
  - **Compass solar-month index (B)**: matches the actual product/domain model (`premium-visit-compass-time-model-contract.md`'s MONTH grain is solar, not calendar — CONTRACT, unchanged), so a user near a solar-month boundary might be product-scoped into a different "month" than their calendar-month analytics bucket would suggest.
  - **HYPOTHESIS, this audit's recommendation: use calendar month (A) for analytics/KPI reporting, and reserve solar-month (B) for any future in-product display logic** (e.g., what Compass itself shows the user as "this month's direction") — the two serve different consumers (aggregate measurement vs. individual product display) and conflating them risks off-by-a-few-days errors in retention counts for a boundary effect that doesn't matter at aggregate scale. **This is still flagged as an OPEN DECISION** (§26) since it is a judgment call, not derived from an existing analytics contract precedent — no existing doc addresses this specific tradeoff.

---

## 18. KPI Definitions

| KPI | Numerator | Denominator | Grain | Required event(s) | Attribution limit | Sample caveat |
|---|---|---|---|---|---|---|
| **Compass Home Discovery Rate** | `home_compass_entry_click` | Home page views (if ever instrumented) or, absent that, reported as raw click volume only | session | `home_compass_entry_click` (+ future Home page-view event, not proposed here) | none | denominator currently unavailable — see §26 |
| **Compass Activation Rate** | `compass_result` events with any `result_state` (i.e., a submit was attempted and reached the backend) | `compass_entry` events | session | `compass_entry`, `compass_result` | none | small-N caveat, §20 |
| **Compass Result Success Rate** | `compass_result{result_state:"recommendation_success"}` | all `compass_result` events | session | `compass_result` | none, but see §10 for why `error`/`invalid_purpose` should be reported separately, not just subtracted | §20 |
| **Compass → Shrine Detail CTR** | `shrine_detail_view{source:"compass"}` | `card_view{source:"compass"}` (Recommendation exposure) or `compass_result{result_state:"recommendation_success"}` | per-recommendation-instance | `card_view`, `shrine_detail_view` | direct, same-navigation only | §20 |
| **Compass → Favorite Rate (same-session)** | `favorite_click`/`shrine_decision{source:"compass"}` | `compass_result{result_state:"recommendation_success"}` | session | as above + `favorite_click` | same-session only, explicit MEASUREMENT GAP beyond that (§13) | §20 |
| **Compass → Visit Rate (same-session)** | `visit_done{source:"compass"}` | same as Favorite | session | `visit_done` | same-session only, likely low-yield by nature (§14) | §20 |
| **Visit → Reflection Rate (where attribution valid)** | `reflection_saved` correlated to a `visit_done` via existing `recommendationInstanceId`/page context | `visit_done` (all sources, or `source:"compass"` subset for the Compass-specific read) | session | `visit_done`, `reflection_saved` (both existing, unchanged) | inherits whatever attribution tier the underlying `visit_done` had (§15) | §20 |
| **Same-Month Compass Repeat Usage** | sessions/users with ≥2 `compass_result` in the same calendar month | all sessions/users with ≥1 `compass_result` that month | month | `compass_result` | ENGAGEMENT only, not retention (§16) | §20 |
| **Month-over-Month Compass Return** | sessions/users with `compass_result` in month M and month M+1 | sessions/users with `compass_result` in month M | month-pair | `compass_result` | anonymous undercounting risk (§17) | §20 |

---

## 19. Premium Continuity Validation Hypotheses

Restated from `compass-premium-personal-continuity.md` §17 and `compass-runtime-personal-continuity-boundary.md` §17, mapped to this contract's concrete KPIs:

| Hypothesis | Supporting evidence (if KPI is healthy) | Evidence against | Observable now (post-instrumentation)? | Required sample |
|---|---|---|---|---|
| **A** — Compass drives meaningful Shrine Detail exploration | Healthy Compass→Shrine Detail CTR | Near-zero CTR despite successful results | **Yes**, immediately after PR-C ships (§25) | qualitative, §20 |
| **B** — Compass drives durable actions (Favorite/Visit) | Non-trivial same-session Favorite/Visit rate | Near-zero rate | **Partially** — only the same-session tier is observable; cross-session remains a MEASUREMENT GAP regardless of sample size | qualitative, §20 |
| **C** — Compass users continue into Reflection | Healthy Visit→Reflection rate on the Compass-attributed subset | Low continuation even where attribution holds | **Yes**, for the same-session-attributed subset only | qualitative, §20 |
| **D** — Users return to Compass in a later month | Healthy Month-over-Month Return | Near-zero return | **Yes**, but only after ≥2 calendar months of instrumented data exist by construction | at least 2 calendar months of data, structurally required, not a policy choice |
| **E** — Cross-month shrine behavior is rich enough to justify a Continuity surface | Some combination of B+C+D all showing real signal, sustained across 3+ months | Any of B/C/D failing, or D succeeding only for a small anonymous-favorable subset (masking a real undercounting problem, §17) | **Only after** A-D show sustained signal; no direct event measures "richness" itself — this remains a qualitative synthesis judgment, not a single KPI | HYPOTHESIS: no single number suffices; requires the qualitative, session-diversity-based judgment this repo already uses elsewhere (§20) |

**This audit does not treat any of A-E as validated.** No Premium conversion event is defined or proposed anywhere in this document, per the task's explicit instruction (§20 of the task) — Premium doesn't have a Compass-specific surface yet, so there is nothing to instrument a conversion funnel for.

---

## 20. Minimum Observation Gate

**No numeric threshold is set — this follows an established, repeated pattern in this repository, not an omission.**

Precedent found and directly applicable (FACT, all re-verified):
- `docs/audit/posthog-recommendation-quality-observation-cadence.md` §11: explicitly `NOT_DEFINED` for sample-count thresholds, "根拠なく数値を設定しない."
- `docs/audit/recommendation-quality-observation-operations.md` §3: formalizes independent-session-unit-based qualitative gating (uses `threadId` diversity, not elapsed time or a raw count) as the standing Observation Operations Contract.
- `docs/audit/deep-dive-production-go.md` §6: qualitative Observation Phase gate, no number, matches this project's own remembered precedent for Deep Dive.

**Applying the same pattern to Compass (HYPOTHESIS, this audit's proposal, not a new numeric policy):** treat any headline percentage from §18's KPIs as non-decision-grade until:
1. Multiple **independent** Compass sessions have accumulated (independent unit: `analyticsSessionId`, or `user_id` where available — mirroring the `threadId`-diversity principle from the Concierge precedent, adapted since Compass has no thread), **and**
2. At least **2 distinct calendar months** of `compass_result` data exist (a structural minimum for Month-over-Month Return to be computable at all, not a policy choice — §19 Hypothesis D), **and**
3. Both same-session-attributed Favorite/Visit and the CTR metric show **some** non-zero, non-noise signal across that session diversity (qualitative "does the funnel show life at all" check, not a percentage target).

**Explicitly classified as OPEN PRODUCT/ANALYTICS DECISION**, per the task's own instruction: no repository precedent defines what "sufficient diversity" numerically means even for the established Concierge pattern — this audit does not invent a number where none exists upstream either.

---

## 21. Double-Counting Risks

| Existing event family | Overlap risk with proposed Compass metrics | Resolution |
|---|---|---|
| Recommendation impressions (`card_view` et al.) | Compass reuses the same event — risk is conflating Concierge-sourced and Compass-sourced impressions in aggregate dashboards if `source` is dropped in a query | Always segment by `source` in any Compass-specific report; never aggregate `card_view` totals without it |
| Shrine Detail transitions | Same event, same risk | Same resolution — segment by `source`/`ctx` |
| Favorite events | Same event (`favorite_click`/`shrine_decision`), currently has **no** `source` at all — so today, 100% of Favorite events are already unattributable to any surface, Compass or otherwise; adding `source` fixes this for **all** surfaces, not just Compass | The fix is additive and improves existing Concierge/Shrine-Detail attribution as a side effect, not just Compass's |
| Visit events | Same reasoning — currently hardcoded to `"shrine_detail"` for 100% of visits regardless of true origin; the fix corrects existing mis-attribution, not just adds new Compass coverage | Same |
| Reflection events | No change proposed (§15) — no new overlap introduced | N/A |
| Direction events | No overlap — Direction events are a separate, unrelated event family (Concierge's direction-signal surfacing inside recommendation cards, §3.5), not something Compass's own direction computation should emit into, since Compass's direction runtime is a different product surface with its own contract | Compass must **not** emit into `DIRECTION_EVENT_NAMES` — that family's prohibited-attribute allowlist and its own contract are scoped to Concierge's `direction_reference` feature specifically, not to Compass generally |
| Home CTA events | None exist today (§3.1) — no overlap possible yet; the new `home_compass_entry_click` should be named/shaped so that if Home later gets a generic CTA-tracking system, this event can be migrated into it rather than needing to coexist as a permanent one-off | Flag in §26 as a forward-compatibility note, not a blocker |

**No planned Compass event duplicates an existing canonical event's responsibility.** The corrections identified above (Favorite/Visit `source`) are net improvements to the existing contract's accuracy, not Compass-specific scope creep.

---

## 22. Privacy / Data Minimization

Explicitly prohibited in every Compass-related payload proposed in this document (re-affirmed, matches §3.5's Direction precedent and the task's own list verbatim):

birthdate value, exact latitude/longitude, raw address, raw station string, Reflection content (`answer`), personal note text, any free-form user text, email, nickname.

**Coarse classifications used throughout this contract:** `origin_type` (5-value enum, §7), `result_state` (6-value enum, §10), `has_birthdate` (boolean), `purpose` (canonical slug, not free text), `purpose_changed`/`origin_mode_changed` (booleans, never old/new values).

**One gap worth flagging (INFERENCE):** unlike Direction events, none of the *existing* Card/Search/Billing event families have runtime-enforced allowlists (§3.5) — only Direction does. This contract's privacy guarantees for Compass properties are therefore currently only as strong as **TypeScript-compile-time** typing, same as the rest of the (non-Direction) analytics surface — not a Compass-specific weakness, but worth naming: if this contract is ever implemented, extending `sanitizeDirectionEventPayload`-style runtime validation to Compass's new properties would be a meaningfully stronger privacy guarantee than what the rest of the codebase currently has, at the cost of being inconsistent with how Card/Search/Billing events work today. **OPEN DECISION** (§26).

---

## 23. Personal History Separation

Stated explicitly, per the task's requirement:

**Analytics events defined in this contract are NOT Personal Shrine Continuity, and must never be treated as such.**

- Do not reconstruct a user-facing "Compass History" from PostHog data — PostHog data is aggregate/session-scoped by design (§9's identity limitations alone make it unsuitable: no reliable `user_id` linkage exists today), and reconstructing per-user history from it would silently violate the conclusion already reached in `compass-runtime-personal-continuity-boundary.md` (Personal Shrine Continuity composes from `Favorite`/`Visit`/`Reflection`, never from Compass-side data of any kind, analytics included).
- Do not treat PostHog data retention settings as product persistence policy — these are operationally unrelated; PostHog's retention window has no bearing on what a user's account is entitled to see about their own shrine journey.
- Do not promise users that "your Compass activity is saved" based on the existence of this analytics contract — nothing in this document creates a user-facing feature; it exists purely for internal product measurement.

`Favorite`/`Visit`/`Reflection` remain the durable, user-owned product domains, entirely unmodified by anything in this document.

---

## 24. Current vs Future Analytics

**CURRENT (proposed as buildable now, this document's actual scope):**
- Home discovery (§6)
- Compass entry/Activation/Completion (§6)
- Shrine Detail exploration attribution (§12)
- Favorite/Visit attribution at the same-session tier (§13-14)
- Reflection continuation via existing events (§15)
- Same-month engagement (§16)
- Month-over-month return (§17)

**FUTURE (explicitly not defined here, would require a Personal Continuity surface to exist first, per `compass-runtime-personal-continuity-boundary.md`'s own current-vs-future separation):**
- Any event measuring engagement with a Personal Shrine Continuity *view* (doesn't exist yet).
- History-comparison usage events.
- Premium continuity engagement/upgrade-conversion events specific to a continuity feature (no such feature exists to instrument — §19).
- Cross-session Compass provenance of any kind, should a future phase decide it's worth new persistence (explicitly out of this phase's authority to decide).

No future event is defined in this document, per the task's explicit instruction.

---

## 25. Implementation PR Split

Proposed, not implemented. Adapted from the task's example split to match what this audit actually found (some suggested PRs collapse or reorder based on real dependencies discovered):

- **PR-A: Analytics type/enum foundation.** Extend `AnalyticsSource` (and sibling unions where needed) with `"compass"`/`"home"`; extend `normalizeCtx` to accept `"compass"`. No behavior change, no new events fire yet — purely additive typing, low risk, independently reviewable. *(This is a smaller, more contained scope than the task's example PR-A, since no new source-enum system needs building — only extension of existing narrow unions, §3.8/§8.)*
- **PR-B: Home → Compass lifecycle instrumentation.** `home_compass_entry_click`, `compass_entry`, `compass_result` (with `result_state`, §10), plus the new stateless `recommendation_instance_id` minted in `CompassRecommendationsView` (§9, no persistence). Ships the full discovery→activation→completion funnel.
- **PR-C: Recommendation / Shrine Detail provenance extension.** Wire `card_view{source:"compass"}` into Compass's result rendering; ship the `normalizeCtx`/`ShrineDetailArticle.tsx` fix from §12 (both the new `"compass"` value and the existing hardcoding inconsistency between `shrine_detail_view` and `card_view`).
- **PR-D: Favorite / Visit attribution fix.** Add `source` (currently entirely absent) to `favorite_click`/`shrine_decision`; change `visit_done`'s `source` from hardcoded `"shrine_detail"` to the page's actual `ctx`-derived value. **Note (INFERENCE): this PR improves attribution accuracy for Concierge/Shrine-Detail-originated actions too, not just Compass** (§21) — it may be worth landing independently of Compass work, on its own merits, since it fixes a pre-existing gap.
- **PR-E: Observation query / dashboard.** Build the KPI queries from §18 once PR-A through D have shipped and accumulated the qualitative sample described in §20. No new events, read-only against already-shipped data.

**This audit does not force a 1:1 match to the task's example split** — PR-D in particular is called out as potentially valuable as a standalone fix regardless of Compass, and PR-A is narrower than a generic "foundation" PR would need to be, since no canonical enum system is being built, only minimal extension of what exists.

---

## 26. Open Decisions

1. Whether a second event is needed to distinguish network-level submit failure from `result_state:"error"` (§6) — no evidence of need found, not decided.
2. Whether Home discovery needs an impression event in addition to the click event, once Home traffic volume is ever instrumented as a denominator (§4, §18) — deferred, no Home instrumentation exists to build on yet.
3. Calendar month vs. Compass solar-month index for retention reporting — this audit recommends calendar month for analytics, solar-month reserved for product display, but flags this as a judgment call with no existing precedent to lean on (§17).
4. Whether to extend Direction-style runtime payload validation (`sanitizeDirectionEventPayload`) to Compass's new properties, vs. accepting the same TypeScript-only guarantee the rest of the non-Direction analytics surface has (§22).
5. Numeric thresholds for the Minimum Observation Gate (§20) — explicitly not set, follows existing repo-wide precedent of qualitative-only gating.
6. Whether `home_compass_entry_click` should be designed for eventual migration into a future generic Home CTA-tracking system, or treated as a permanent one-off (§21).
7. How (or whether) to eventually attach a real `user_id` to analytics events for logged-in users — a pre-existing, cross-cutting gap (§9) this audit surfaces but cannot resolve within Compass-only scope.

---

## 27. Final Classification

```
Compass Discovery Measurement:      PARTIAL   (click: READY to build; impression/denominator: not yet possible, Home has zero base instrumentation)
Compass Activation Measurement:     READY     (well-defined, single new event, no dependency gaps)
Compass Result Measurement:         READY     (all 5 backend states + error path directly mapped, §10)
Compass → Shrine Detail:            READY     (direct attribution, reuse existing event + one typed extension + one bug fix)
Compass → Favorite:                 PARTIAL   (same-session: READY; cross-session: explicit MEASUREMENT GAP, not solvable this phase)
Compass → Visit:                    PARTIAL   (same-session only, likely low-yield by the nature of physical visits, §14)
Visit → Reflection:                 READY     (already measurable independently of Compass, no new work needed)
Same-Month Engagement:              READY     (derivable from proposed events, no new instrumentation beyond §6)
Month-over-Month Retention:         PARTIAL   (structurally requires ≥2 months of data to exist before it's computable at all, and anonymous identity is undercounting-prone, §17)
Privacy Contract:                   READY     (follows established Direction-event precedent for coarse classification; one open note about runtime-validation strength, §22, not a blocker)
Premium Continuity Validation:      PARTIAL   (Hypotheses A-D observable once instrumented; E requires sustained multi-month signal across all of them, no shortcut exists)
```

**Overall: B — READY WITH MEASUREMENT GAPS.**

Not A: several dimensions (Discovery denominator, cross-session Favorite/Visit, Month-over-Month's structural 2-month minimum) are honestly not fully closeable within this phase, no matter how well-specified the contract is. Not C: the contract itself is not ambiguous or contested — every property, event, and reuse decision in this document traces to a concrete, re-verified piece of current code or an existing, unmodified precedent; there is no unresolved *contract* question blocking implementation, only known, named measurement limits. Not D: no architecture conflict exists anywhere — every proposed mechanism reuses existing patterns (the `ctx` query-param threading, the `AnalyticsSource` union extension, the stateless per-request identifier pattern already proven by Concierge's `rid`) rather than requiring new infrastructure.

This is the fourth audit in the Compass chain (#2484 → #2485 → #2486 → this document) and the first to reach a **B** rather than a **C** — because, unlike the product-boundary questions those three addressed, this document's job was to define a *contract*, and a contract can be fully specified even while the *evidence* it would produce remains unknown. The open items in §26 are genuinely small and enumerable, not a sign the contract itself is unready.
