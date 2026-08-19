> **Status: Audit / Historical（Compass Premium Personal Continuity Boundary Audit）**
>
> This document is a docs-only, point-in-time audit, following on from `docs/audit/compass-free-premium-boundary.md` (Phase 7, merged to `develop`). It contains no code, model, migration, entitlement, pricing, or Analytics implementation changes. It does not modify Concierge behavior, Compass Recommendation quality/ranking, or Shrine Knowledge authority.
>
> Every substantive claim is tagged **FACT** (verified in code or a canonical doc as of this audit), **INFERENCE** (a conclusion this audit draws by combining verified facts), **PRODUCT HYPOTHESIS** (an untested reasoning judgment this audit proposes), or **OPEN DECISION** (a question this audit cannot and does not resolve — flagged for explicit product sign-off).

# KAMI MUSUBI — Compass Premium Personal Continuity Boundary Audit

## 1. Executive Summary

**Central question restated:** can Compass stay fully useful for everyone while Premium becomes valuable because a user's monthly Compass experiences become a private, persistent, connected personal journey over time?

**Answer: yes, conditionally.** The hypothesis —

```
Free    = Discover this month's direction and shrine candidates.
Premium = Preserve → Connect → Reflect → Compare.
```

— is **coherent and consistent with every existing canonical contract** this audit could find (`premium-experience.md`'s depth/continuity framing, Visit/Reflection's existing "saving is Free, comparing is Premium" pattern, and the prior Compass audit's own deferred recommendation of a future Continuity Gate). It requires no change to Free Compass, no new gating, and no conflict with Concierge, Ranking, or Shrine Knowledge boundaries (§19).

**But it is not yet a contract, for one concrete reason:** nothing in the current product links a Compass session to anything else a user does. Favorites carry no source field. Visit and Reflection link only to `ConciergeThread` (Concierge consultations), never to Compass. Compass itself persists nothing at all — not even a logged-in user's own birthdate, which is re-entered by hand every single session (FACT, `CompassClient.tsx:28,62,75`). "Personal Continuity" as a product idea is sound; as a system, every connective piece of it still needs to be designed and none of it should be built before the underlying usage hypotheses (§17) are checked against real behavior — the same discipline already applied to Compass itself before this audit, and to Deep Dive before that.

**Final Classification: C — NEEDS VALIDATION BEFORE CONTRACT** (§22). This is a direct continuation of the prior audit's own classification, one layer deeper: that audit concluded Compass's Continuity Gate was "the correct future direction, not implementable yet." This audit designs what that direction concretely means, and confirms it is still not implementable yet — for evidence reasons, not architecture conflicts.

---

## 2. Current-State Evidence

All **FACT**, verified against `develop` at commit `25d37aa8` (this audit's branch point) — i.e. after Phase 7's `compass-free-premium-boundary.md` was merged.

**Compass today:**
- `backend/temples/api_views_compass.py:21,44` — `CompassRecommendationsView.permission_classes = [AllowAny]`. Compass requires **no authentication at all**, not just no Premium.
- `apps/web/src/features/compass/CompassClient.tsx:28` — birthdate is a plain `useState("")` text input, submitted fresh each request (`:75`); it is **not** read from `UserProfile.birthday` even for a logged-in user. Compass has zero account awareness of any kind.
- No Compass analytics instrumentation exists anywhere (frontend or backend) — confirmed by exhaustive grep across `apps/web/src/features/compass/**`, `apps/web/src/app/compass/**`, and the Compass backend service files.
- No persistence, no history, no month-selection UI (all reconfirmed from Phase 7; unchanged since).

**Account/auth model:**
- No custom User model; plan state lives on a separate `UserProfile` (`backend/users/models.py:5-36`) via `stripe_customer_id/subscription_id/price_id`, `subscription_status`, `current_period_end` — not a boolean flag. `is_staff` also auto-grants premium (`billing_state.py:136-141`).
- Anonymous users are tracked only for Concierge, via a signed, HttpOnly `concierge_anon_id` cookie (`anonymous_id.py`, 90-day expiry) — Compass doesn't use this or any other identifier.
- **No anonymous→account claim/merge mechanism exists anywhere in the codebase.** An anonymous `ConciergeThread` is never reassigned to a `user` after signup/login (confirmed by grep for `claim/merge/migrate_anon/attach_user` — no hits).
- `docs/core/auth-flow.md:21-23` (Active): the canonical rule is that consultation/browsing works unauthenticated, and **save actions** are what trigger the auth requirement ("保存操作から認証を要求する").

**Entitlement/cancellation, as actually implemented:**
- `backend/users/services/stripe_webhook.py:352-357` — on `customer.subscription.deleted`, the handler sets `subscription_status` to Stripe's status string (or `"canceled"`) and `current_period_end = None`. **Nothing else happens.** No Favorite, Visit, Reflection, or ConciergeThread row is touched, deleted, or anonymized anywhere in the cancellation path.

**Favorites:**
- Live model `temples.models.Favorite` (`models.py:576-609`): `user` (FK, `IsAuthenticated`-only, no anonymous favoriting), `shrine` or `place_id`, `created_at`. **No provenance field** — no `source`, `thread`, or any reference to what caused the favorite.
- A second, structurally different `Favorite` model exists at `backend/favorites/models.py` but is **not wired into any URL route** — dead code, not the live contract. Not relevant to this audit's boundary but worth a separate cleanup note (out of scope here).

**Visit / Reflection:**
- `Visit` (`models.py:691-712`): `user`, `shrine`, `thread` (nullable FK → `ConciergeThread`, on_delete=SET_NULL, help text literally: "参拝のきっかけとなった相談スレッド（Recommendation Snapshotへの接続キー）"), `visited_at` (defaults to now), `note`, `status ∈ {added, removed}` — **no planned/scheduled state, only active/soft-deleted.**
- `ShrineReflection` (`models.py:716-756`): `user`, `shrine`, `thread` (same pattern as Visit), `history_theme` (snapshot), `prompt`, `answer`, `mood_before/after`, `created_at`. **No direct FK to Visit** — it reaches back to "why" only via `thread`, same as Visit does.
- The connective mechanism this codebase already uses — a nullable FK to `ConciergeThread` on both Visit and Reflection — **has no Compass equivalent.** There is no `CompassSession`/`CompassThread` concept for a future Compass-originated Visit or Reflection to reference.

**Analytics precedent for personal-data boundaries:**
- `docs/analytics/direction-events.md:20-29` (Active) — an explicit prohibited-attribute list for Concierge's direction-signal analytics events: no lat/long, address, station, prefecture, search terms, **birthdate**, consultation text, profile input, the actual computed direction/fortune outcome, the visit-date value, or shrine name/anything individually reconstructable. Only booleans/enums allowed.
- No `posthog.identify()` call exists anywhere in `apps/web/src` — analytics currently has no linkage between a browser-local `analyticsSessionId` and a backend `user_id`/`anon_id`. `docs/analytics/analytics-payload-audit.md:390-417` independently confirms this as a known, already-documented gap ("user-level retention" / "session attribution" listed as 未完成).

---

## 3. Free Compass Boundary

| Item | Determination | Basis |
|---|---|---|
| Should Compass remain available to unauthenticated users? | **Yes, unchanged.** | FACT: already `AllowAny` today, and nothing in this audit's Continuity design requires changing that — Continuity is additive, gated by account+Premium, not by removing anonymous access to Discover. |
| Should registered Free users retain the full current Compass experience? | **Yes, unchanged.** | Same reasoning; Free = Discover, full stop. |
| Do Free and Premium users receive the same Recommendation quality? | **Yes, confirmed, and must stay that way.** | FACT: no premium-specific Compass logic exists anywhere in the current code; this audit's Architecture Constraints (§19) explicitly forbid introducing any. |
| Should Premium value avoid being created by hiding Compass results? | **Confirmed as a hard requirement.** | Matches `premium-experience.md`'s banned-framing pattern (never make Free feel deliberately weaker); Phase 7 already established this and this audit does not revisit it. |
| Should direction output become Premium-only? | **No.** | Would be Model A (Feature Gate), already rejected in Phase 7 §6 as contradicting the shipped Home-entry "Premium Neutrality" decision. |
| Should Shrine Recommendation output become Premium-only? | **No.** | Same reasoning. |
| Should Shrine Detail access change for Compass monetization? | **No — out of scope, governed by its own existing contract.** | Shrine Detail's Free/Premium boundary (basic facts free, personalized supplement premium) was set by `premium-experience.md` and reaffirmed in Phase 7; this audit does not touch it. |
| Any existing entitlement behavior conflicting with this boundary? | **None found.** | FACT: Compass has zero entitlement checks today (confirmed §2); there is nothing to conflict with. |

**Conclusion: READY** (see §22) — no change to Free Compass is proposed or required by this audit.

---

## 4. Premium Personal Continuity Definition

**Compass History (standalone) vs Personal Continuity (higher-level) — evaluated:**

INFERENCE: a standalone "Compass History" — a plain log of past Compass runs — risks becoming exactly the "generic cloud storage" trap the task warns against (§4 checklist): a list of past outputs with no clear reason to open it twice. It also has no natural connection to what the user actually *did* (favorited/visited/reflected), because no such connection exists in the data model today (§2).

**Personal Continuity, defined one level higher, is the coherent version:**

```
Personal Continuity
├── Save        (existing — Favorite; already Free by contract)
├── Plan        (does not exist yet — see §13)
├── Visit       (existing — already Free by contract)
├── Reflection  (existing — already Free by contract)
└── Compare     (does not exist yet — see §14)
```

PRODUCT HYPOTHESIS: "continuity" in KAMI MUSUBI specifically means — *the ability to see how a user's monthly Compass-driven intent (a stated purpose and a computed direction) connects across time to what the user actually did about it (favorited, visited, reflected)*, turning a series of otherwise-isolated one-shot Compass sessions into one connected personal journey. This is narrower than "History" (which could mean anything, including candidates never acted on) and is explicitly **not** the same as generic bookmarking/cloud storage, because its value comes from the *connection*, not from storage capacity or list length.

**Current-month vs multi-month value, separated per the task's explicit instruction:**

- **First-Premium-month value (does not require 2+ months):** the connective view itself — "this month you asked about Career, Compass pointed Northwest, and you favorited/visited/reflected on Shrine X" — is a complete, one-month artifact with real value on day one of a subscription. This satisfies the checklist requirement that Premium provide value before any multi-month data exists.
- **Multi-month value (requires accumulation):** comparison across purposes/directions over time (§14), and any pattern recognition — explicitly deferred as FUTURE, not MVP, and bounded by strict non-interpretation rules (§14, §18).

**Verdict: SUPPORTED (PRODUCT HYPOTHESIS, well-grounded)** — Personal Continuity, not Compass History, is the correct framing. This is the recommendation carried through the rest of this document.

---

## 5. Compass History Responsibility

The task's distinction — generated ≠ viewed ≠ saved ≠ planned ≠ visited ≠ reflected — maps directly onto real gaps in the current schema (§2): Visit's `status` only distinguishes `added`/`removed` (no planned state), and nothing today records "viewed" or "generated" at all.

**PRODUCT HYPOTHESIS (this audit's recommendation): Compass History should record meaningful user actions, not generated output.**

Reasoning (INFERENCE): the codebase already has exactly this pattern for Concierge — Visit and Reflection reference `ConciergeThread` to answer "why," but nothing persists *every shrine a Concierge conversation ever surfaced*. Only the shrine the user actually acted on gets a durable record. Compass should follow the identical shape: a Compass session that produces candidates the user ignores leaves no trace; a Compass session where the user favorites, plans (§13), visits, or reflects on a resulting shrine creates one continuity entry anchored to that action.

Explicit checklist answers:
- Should all generated recommendation candidates ever be persisted? **No.**
- Should Compass History become an indiscriminate activity log? **No — this is the specific failure mode this recommendation is designed to avoid.**
- Does "recommended" ≠ "viewed" ≠ "saved" matter here? **Yes** — but this audit recommends the product only needs to persist at the "saved/planned/visited/reflected" end of that chain, not instrument every intermediate state. Whether "viewed" needs its own signal at all is an **Analytics** question (§15-16), not a **Personal History** one.

---

## 6. Minimum Persistence Dataset

No database model is created by this audit (§19). The following is a conceptual minimum, evaluated field-by-field per the checklist.

| Field | Persist? | Reasoning |
|---|---|---|
| Target/effective month | **Yes** | Small, canonical, already the product's grain unit (`MONTH`, per `premium-visit-compass-time-model-contract.md`) |
| Selected purpose | **Yes, as the existing canonical `need_tag` slug** | Reuses existing taxonomy; Architecture Constraints (§19) forbid inventing a new one |
| Calculated reference direction | **Yes, as the value itself, but only within the user's own account-scoped record** | See privacy note below — this is *not* the same context as the `direction-events.md` analytics prohibition |
| Recommendation explanation text | **OPEN DECISION — lean toward regenerate, not store verbatim** | INFERENCE: storing derivable text duplicates data and risks going stale relative to updated Shrine Knowledge; storing only the inputs (purpose, direction, month, shrine id) is likely sufficient to regenerate an equivalent explanation on read. Flagged open because reproducibility-over-time hasn't been weighed against regeneration cost. |
| Direction explanation text | Same as above | Same reasoning |
| Selected/meaningfully-interacted-with shrine | **Yes — only the acted-on shrine(s), never the full candidate list** | Per §5 |
| Relationship to Visit | **Yes, nullable reference** | Mirrors the existing `thread` FK pattern already used by Visit/Reflection |
| Relationship to Reflection | **Yes, nullable reference** | Same |
| Creation timestamp | **Yes** | Trivial, required for any timeline (§12) |
| User/account ownership | **Yes, non-nullable, authenticated-user-only FK** | Per §7, Continuity begins after Premium activation — there is no anonymous-Compass-history case to support, so this can be simpler than `ConciergeThread`'s dual `user`/`anonymous_id` design |
| Birthdate | **No, do not duplicate per-entry** | FACT: Compass doesn't even use the account's own `UserProfile.birthday` today — it's re-entered every session. A Continuity record should not become the first place birthdate gets silently persisted per-entry. If prefill-from-profile is ever built, that's a separate, one-time account-level field, not a per-history-entry copy — **OPEN DECISION**, not required for Continuity itself. |
| Precise origin | **No — omit, or coarse-only if a clear UX need is shown** | PRODUCT HYPOTHESIS: the continuity value is about the *purpose→direction→shrine* journey, not a location trail. Mirrors the existing analytics precedent of never persisting precise coordinates (§2), applied here as a data-minimization default even though this is personal, not analytics, data. |

**Privacy-sensitive fields, explicitly justified:**
- **Birthdate** — not persisted per-entry (see above); the only pre-existing storage of it at all is the optional `UserProfile.birthday` field, itself not currently read by Compass.
- **Precise origin** — not persisted; if origin-history is ever shown to have real user-facing continuity value, prefer a coarse representation (e.g., prefecture-level) over exact coordinates, matching the same discipline `direction-events.md` already applies elsewhere in this codebase.
- **Direction/purpose result values** — **INFERENCE, explicitly flagged as an inference, not a literal restatement of existing contract:** `direction-events.md`'s ban on persisting the actual computed direction/fortune outcome applies to *anonymous, aggregate Analytics events* (§2). A user's own account-scoped, access-controlled Personal History record is a different data-protection context — the same category as `ShrineReflection.answer`, which already stores free-text personal reflection content today. This audit infers the analytics prohibition does not automatically extend to the user's own private record, but flags this explicitly so the distinction is never silently assumed without review.

---

## 7. Pre-Premium / Post-Premium Boundary

**Preferred hypothesis, evaluated and supported: Personal Compass History begins after Premium activation. Free usage is not secretly stored.**

- Should pre-Premium Compass usage be retroactively imported? **No.** INFERENCE: this is not just a policy preference — it's the path of least resistance given current architecture, since **nothing is stored today** (FACT, §2). There is nothing to import. Choosing "no retroactive import" costs nothing and avoids the exact trap the checklist warns against (secretly storing Free usage as future monetization leverage).
- Should Free users have hidden personal Compass history stored merely for future monetization? **No — confirmed as a hard requirement**, consistent with current reality (zero storage exists) and with this product's established trust posture (`premium-experience.md`'s Concierge-protection precedent, extended here).
- Anonymous/product Analytics vs user-facing Personal History: kept explicitly separate (§15) — an aggregate "Compass was used N times today" analytics counter is fine; a per-user retained log tied to identity before Premium is not.
- Should a user explicitly trigger the first saved record? **PRODUCT HYPOTHESIS: no special ceremony needed** — the first meaningful action (favorite/plan/visit/reflect linked to a Compass session) taken *after* Premium activation becomes the first Continuity entry automatically, the same way Favorite/Visit/Reflection creation already works today (an ordinary user action, not a distinct "start my history" step).
- Empty-state UX for a newly subscribed Premium user with no history yet: **PRODUCT HYPOTHESIS**, not decided here — something like "your journey starts now; this month's Compass result is your first entry" is the shape of what's needed, but copy/UX is out of this audit's scope.
- First-month value even with no historical data: **satisfied** — see §4's "first-Premium-month value" analysis (the connective view of *this* month alone already has value).

---

## 8. Cancellation / Re-subscription Options

Evaluated per the task's three options, against current code behavior (§2, cancellation already implemented and verified to delete nothing):

| Option | Evaluation |
|---|---|
| Delete history on cancellation | **Reject.** Irreversible, poor UX, and — importantly — doesn't even match what "history" would consist of: the underlying Favorite/Visit/Reflection rows are **not** Premium-exclusive data (saving itself has always been Free, per `visit-reflection-flow.md`'s existing "保存そのものをPremium限定にはしない"). Only the *connective* Continuity view would be Premium-gated. Deleting the connections would mean destroying data the user created under a Free-tier guarantee. |
| Retain but hide continuity UI | **Recommended (PRODUCT HYPOTHESIS).** Matches current code precedent exactly: cancellation today only flips `subscription_status`/`current_period_end`, touching nothing else (FACT, §2). Extending that same pattern to a future Continuity feature is the smallest, most consistent change — no new deletion logic, no new retention policy to design from scratch. |
| Retain with limited read-only access | **Defer, not rejected outright.** A softer, more generous variant, but adds a third access mode with no current evidence it's needed. Per the "smallest coherent boundary" principle carried over from Phase 7, this audit does not recommend building it without a demonstrated need. |
| Re-subscription restoration | **Natural consequence of "retain, hide UI."** Since nothing is deleted, reactivating Premium simply restores visibility into already-intact data — no special restoration logic required beyond the existing entitlement check already in place. |

- **Privacy / account-deletion implications:** explicitly out of this audit's evidence base. Premium *cancellation* is a distinct event from *account deletion* — this audit only addresses the former. Whatever the product's existing account-deletion policy is (not reviewed here) should govern full data removal; this audit does not assume or define one. **OPEN DECISION.**

**Recommended (not decided) policy: retain history, hide/disable Premium-only continuity UI on cancellation; re-subscription restores access to the still-intact data.** Flagged as **PRODUCT DECISION REQUIRED** (§22) — this is a real policy call with user-trust and support-cost implications, not something this audit can finalize unilaterally even though it has a clear recommendation.

---

## 9. Compass History vs Favorites

| | Favorite | Compass History (proposed) |
|---|---|---|
| Meaning | "I like / want to remember this shrine" | "This shrine was part of my personal Compass journey" |
| Current contract | Plain user↔shrine bookmark, no provenance (FACT, §2) | Does not exist yet |
| Overlap risk | Low, if kept separate | — |

- Does an automatically-generated Compass candidate become a Favorite on its own? **No — and this is already true today.** FACT: Favorite creation is a distinct, explicit `POST /favorites/` call; nothing in Compass's code creates one automatically.
- Should a Favorite action taken *from* the Compass results screen carry a reference to the Compass session that produced it? **Yes — this is the proposed connection point.** This is the "meaningful action" trigger described in §5/§6. **OPEN DECISION** on implementation shape: extend the `Favorite` model with an optional Compass-session reference, vs. keep `Favorite` untouched and build a separate Continuity join table that references existing `Favorite` rows by id. Both are viable; this audit does not choose (no migrations authorized, §19).
- Avoid duplicating the same concept under two names: **satisfied** — Favorite stays "I want to remember this shrine" (context-free); Compass History stays "why/when this shrine entered my journey" (context-rich). They compose rather than compete.

**Classification: CLEAR** (§22).

---

## 10. Compass History vs Visit History

| | Compass History (proposed) | Visit History (existing) |
|---|---|---|
| Answers | Why / when / through which monthly context a shrine entered the journey | Where the user actually went |
| Authority | Would be new | `Visit` model, existing (`models.py:691-712`) |

- Current Visit History authority: confirmed as `Visit` (§2) — unchanged, unaffected by this audit.
- Compass History must not replace Visit History: **confirmed** — Compass History (if built) answers "why/when," never "did they go" or "when did they go." Visit's `visited_at`/`status` remain sole authority for that.
- How would a Compass record reference a later Visit? **Mirror the existing pattern** — `Visit` already has an optional `thread` FK for exactly this purpose (referencing back to "why"); a parallel optional Compass-session reference on `Visit` (or an equivalent join) is the natural, precedented shape. Not decided here (no migrations).
- Can a Visit exist without Compass? **Yes, must remain true** — most Visits today are either manual or Concierge-thread-linked; Compass-linked Visits would be additive, never a requirement.
- Non-Compass visits remain first-class: **confirmed**, no change proposed to Visit's existing behavior for non-Compass-originated visits.
- Ownership of visit date/status/completion state: **stays solely with `Visit`** — a Compass History record would reference a Visit by id, never duplicate or shadow `visited_at`/`status`.

**Classification: CLEAR** (§22).

---

## 11. Compass History vs Reflection Timeline

| | Compass | Visit | Reflection |
|---|---|---|---|
| Answers | What direction/purpose led toward the shrine | What happened behaviorally | What the user experienced/felt afterward |

- Current Reflection authority: confirmed as `ShrineReflection` (§2) — unchanged.
- Compass History must not duplicate Reflection content: **confirmed as a hard requirement** — a Compass record should reference a `ShrineReflection` by id, never copy `answer`/`mood_before`/`mood_after` into itself.
- Compass → Visit → Reflection linkage: same reference-chain pattern as §10, not a content merge.
- Reflection remains meaningful without Compass: **yes, already true today** (most current reflections are Concierge-thread-linked or standalone).
- Compass remains usable without Reflection: **yes, already true today** (Compass is fully standalone, §2).
- Must not use Reflection content to retroactively rewrite the original Compass result: **confirmed as a hard requirement** — a Compass History entry, once created, should represent an immutable snapshot of "why/when," preserving data integrity and user trust; what the user later feels about the visit (Reflection) must never mutate the historical Compass record itself.

**Classification: CLEAR** (§22).

---

## 12. Personal Timeline Model

The task's example groups the timeline by month, mirroring Compass's own MONTH-grain design.

- Should month be the primary grouping unit? **Yes.** INFERENCE: this is the only grouping that requires no new concept — it reuses Compass's existing Time Model (`premium-visit-compass-time-model-contract.md`, MONTH grain, already Active).
- Consistency with the existing MONTH Compass model: **confirmed**, no conflict.
- Multiple uses within one month: PRODUCT HYPOTHESIS — **only the session(s) tied to a meaningful action (§5) become permanent timeline entries.** Pure exploration (trying purposes/origins without ever favoriting/planning/visiting/reflecting) should not clutter the personal timeline — this both satisfies the "avoid indiscriminate activity log" principle (§5) and naturally deduplicates repeated identical runs without needing separate dedup logic.
- Different purposes in the same month creating separate entries: **yes, if each leads to a distinct meaningful action** — that's real signal (the user pursued two different intents), not duplication.
- Origin changes creating separate entries: same logic — only material if a meaningful action follows.
- Avoid inventing meaning from historical patterns unless supported by actual user data: **carried forward explicitly into §14** (Compare layer) as a hard constraint, not just a timeline-display concern.

---

## 13. Plan / Future Action Layer

- Does "want to visit this month" already exist elsewhere? **No.** FACT: `Favorite` has no monthly/purpose framing (general, undated bookmark); `Visit.status` only has `{added, removed}` — no scheduled/planned state (§2). This is a genuine gap, not a duplicate of an existing feature.
- Compare to Favorites: Favorite is general and undated; a Plan concept would be dated/purpose-anchored and tied to a specific Compass session — different enough not to collapse into one concept, per the same reasoning as §9.
- Compare to Visit state: Visit only records what already happened; a Plan would need to exist *before* a Visit record does.
- **Classification: FUTURE** (not MVP, not Reject). INFERENCE: it's coherent and non-redundant, and it completes the Compass→Plan→Visit→Reflection flow the task describes — but building it means new schema (new Visit states or a new lightweight model), which is real production work not authorized in this docs-only audit, and not yet justified by evidence that the simpler Save→Visit→Reflect loop is insufficient on its own. Recommend revisiting after core Continuity linkage (§6, §9-11) ships and is observed.

---

## 14. Compare / Long-Term Reflection Layer

- Which comparisons can be derived objectively from user behavior? Purely factual ones: purpose distribution across months ("Career/Challenge in August, Relationships in September"), frequency counts ("selected Career/Challenge twice in the last three months"). Both are direct aggregations of stored, meaningful-action-linked entries (§6) — no interpretation required.
- Separate factual summaries from spiritual interpretation: **required, hard rule.** INFERENCE, extending an already-Active product-wide principle: `docs/core/meaning-layer.md`'s non-assertion principle (already load-bearing across Concierge/Compass per the Phase 7 research) applies identically here — a Compare feature may state *what the user selected*, never *what it means*, *what will happen*, or *who they are*.
- Do not infer destiny, future outcomes, psychological state, or spiritual meaning from usage patterns: **explicit hard constraint**, carried into §19's Architecture Impact as well.
- Minimum data volume before comparison becomes useful: **PRODUCT HYPOTHESIS — at least two distinct months of meaningful-action-linked entries.** One month has nothing to compare against; that's exactly why §4 places all first-month value in the connective Save/Visit/Reflect view, not in Compare.
- **Classification: FUTURE** (not MVP, not Reject) — same reasoning as Plan (§13): coherent, not redundant with anything existing, but premature to build before Hypotheses A–E (§17) — especially D (next-month return) — are validated against real usage. Building Compare to solve a retention problem before confirming the problem exists would repeat the exact mistake this audit is structured to avoid.
- Does it strengthen recurring Premium value? **PRODUCT HYPOTHESIS: plausibly yes, conditional on Hypothesis D holding.** If users don't return month-to-month at all, Compare has nothing to operate on regardless of how well-designed it is.

---

## 15. Analytics vs Personal History

Two explicitly separate data responsibilities, following an already-Active precedent (`direction-events.md`) rather than inventing a new rule:

- **Analytics** = aggregate/anonymous product measurement (discovery rate, activation rate, exposure) — never the personal record itself.
- **Personal Compass History** = account-owned, user-facing, access-controlled — never queried as an analytics source, never used to backfill aggregate dashboards directly.
- Anonymous Free Compass usage may be measured: **yes, at enum/boolean level only** (e.g., "a Compass session started," "purpose selected: yes/no," never which purpose, never the computed direction value, never birthdate or origin) — matching `direction-events.md`'s existing prohibited-attribute list, extended by this audit to Compass by the same logic.
- Birthdate must not be sent to Analytics: **confirmed, already an explicit existing rule** (`direction-events.md:20-29`), directly applicable.
- Precise origin must not be sent to Analytics: **confirmed, same basis.**
- Identifiers required for repeat-usage measurement: FACT — no `posthog.identify()` linkage exists between the browser-local `analyticsSessionId` and any backend `user_id`/`anon_id` (§2). For **Premium** (authenticated) users, `user_id`-based measurement is available without new privacy tradeoffs (they're already identified for billing). For **Free/anonymous** users, reliable cross-session "next-month return" measurement is **not** currently possible without new plumbing — this is a pre-existing, independently-documented gap (`analytics-payload-audit.md`), not something this audit needs to solve, but Phase 8 planning should know it inherits this gap rather than treating it as new.
- Existing analytics privacy contracts preserved: **yes** — this audit adds a Compass-specific application of an existing rule, it does not weaken or replace any current contract.

**Classification: CLEAR** (§22).

---

## 16. Phase 8 Analytics Requirements (definitions only — no implementation)

Per the task, defining names/intents, not schemas or thresholds:

- Home → Compass discovery (impression → click)
- Compass start (entry → form interaction begins)
- Purpose selection — measurable at enum level (which of the 15 canonical `need_tag` values, since these are already non-sensitive product taxonomy, not personal data)
- Origin-completion state — measurable as a boolean/enum (device / manual / prefecture / disabled), **never** precise coordinates
- Compass submission (form → request sent)
- Recommendation success / zero candidates / direction unavailable / backend error — four distinct outcome states, not collapsed into one "failure" bucket
- Recommendation exposure (result rendered)
- Compass → Shrine Detail transition (candidate click-through)
- Compass → Visit — **OPEN DECISION**: FACT, this cannot be reliably measured today because no reference mechanism connects a Visit back to the Compass session that produced it (§2, §10). Two paths exist: (a) wait for the full Continuity schema (§6) to provide this link as a side effect, or (b) build a lightweight, analytics-only ephemeral reference (not full Personal History) purely to measure this funnel step sooner. This audit does not choose between them.
- Same-month Compass repeat usage (Hypothesis A, §17)
- Repeat usage after changing purpose (without necessarily logging which purpose, if enum-level tracking is preferred)
- Repeat usage after changing origin, **without logging the origin itself** — only that a change occurred
- Future next-month return usage (Hypothesis D, §17) — for authenticated users only, per the identifier gap above
- Avoid double-counting with existing Recommendation Analytics: Compass events must use a distinct, Compass-specific event namespace (e.g., a `compass_*` prefix) rather than reusing Concierge's `recommendation_*` event family, since they are different products per the existing Concierge/Compass responsibility contract.
- Minimum observation sample before revisiting monetization: **OPEN DECISION** — exact thresholds (sample size, duration) are not this audit's to set; flagged for whoever scopes Phase 8 to define against real traffic volume, consistent with this audit not making numeric commitments it can't evidence.

---

## 17. Premium Validation Hypotheses

| Hypothesis | KPI | Measurable before History exists? |
|---|---|---|
| **A** — same-month reuse | % of Compass sessions that change purpose or origin and resubmit within the same month | **Yes** — needs only ordinary event analytics (§16), no persistence |
| **B** — Compass drives Shrine Detail exploration | Compass → Shrine Detail click-through rate | **Yes** — same, event + referrer, no persistence needed |
| **C** — Compass contributes to actual Visit behavior | Rate of Visits attributable to a prior Compass session | **Partially** — needs at minimum a lightweight reference mechanism (§16 open item); not measurable with zero plumbing, but doesn't need the *full* Continuity schema either |
| **D** — users return to Compass in a later month | % of accounts using Compass in month N and again in month N+1 | **Yes, for authenticated users** — needs only a per-account "used Compass in month M" timestamp/flag, not full session content; harder for anonymous users (identifier gap, §15) |
| **E** — demonstrated demand to preserve/revisit prior Compass experiences | Proxy signals (repeat-favoriting from Compass results) or direct qualitative signal (support requests, user feedback) | **Weakest to measure quantitatively pre-prototype** — PRODUCT HYPOTHESIS: may require qualitative research or a minimal opt-in prototype rather than pure analytics |

- Hypotheses measurable before any History schema exists: **A, B, D** (D with the caveat above).
- Hypotheses requiring a later Continuity prototype: **C** (fully) and the strongest form of **E**.
- **Evidence that would argue against building Premium History:** low/no same-month repeat use (A fails), no next-month return at all (D fails), and negligible Compass→Visit contribution even directionally (C fails). If these converge, there is no journey to preserve, and building Continuity would be exactly the "elegant architecture nobody uses" failure mode the task explicitly warns against.

---

## 18. Privacy / Data-Minimization Considerations

Consolidated from §6 and §15:

- **Birthdate**: never persisted per-Continuity-entry; the only existing storage is the optional, not-currently-used `UserProfile.birthday`. Never sent to Analytics (existing rule, reaffirmed).
- **Precise origin**: never persisted in Continuity history by default; coarse-only if a specific UX need is later demonstrated. Never sent to Analytics (existing rule, reaffirmed).
- **Direction/purpose result values**: acceptable to persist in the user's own account-scoped Personal History (INFERENCE, explicitly distinguished from the Analytics-context prohibition — see §6's flagged nuance); never acceptable in aggregate Analytics.
- **Explanation/direction text**: lean toward regeneration over verbatim storage, minimizing duplicated sensitive-adjacent content at rest (§6, OPEN DECISION on final approach).
- **Cross-cutting rule carried from Phase 7 and reaffirmed here**: data minimization is the default whenever a field's necessity isn't clearly demonstrated — "do not add persistence merely because persistence may be useful later" (§19) applies field-by-field, not just at the feature level.

---

## 19. Architecture Impact

Confirmed respected by this audit (docs-only; verified no code was touched in this branch):

- Concierge responsibility: unmodified.
- Compass Recommendation quality / Ranking weights: unmodified, no Premium-specific scoring introduced or proposed.
- Direction "accuracy" for Premium: not proposed — Premium's entire value proposition here is connective/retrospective, never a "better" calculation.
- Daily plate logic: not proposed, consistent with the existing Time Model audit's rejection of day-level freshness.
- Shrine Knowledge authority: unmodified; no Runtime signal is proposed to overwrite it.
- Purpose taxonomy: no new taxonomy proposed — §6 explicitly reuses the existing canonical `need_tag` slugs.
- Persistence: none added — §6 is a conceptual minimum-dataset analysis, not a schema; no migrations exist in this branch.
- Pricing / entitlement: unmodified.
- History / Analytics: not implemented — both remain design-only (§6, §16).
- Production code: **zero diff** (verify via `git status`/`git diff` at PR time — docs-only commit).

---

## 20. Open Product Decisions

Consolidated list, none resolved by this audit:

1. Schema approach for connecting Favorite/Visit/Reflection to a future Compass session: extend those models with an optional reference, vs. a separate Continuity join table. (§6, §9)
2. Persist regenerable explanation/direction text verbatim vs. regenerate on read. (§6)
3. Whether/how to let logged-in users prefill birthdate from `UserProfile` — a separate infra question, not required for Continuity itself. (§6, §18)
4. Whether coarse origin representation is worth persisting at all, or omit origin from history entirely. (§6, §18)
5. Cancellation policy: retain-and-hide (this audit's recommendation) vs. any alternative — requires explicit product sign-off, not just this audit's reasoning. (§8)
6. Account-deletion interaction with Premium continuity data — outside this audit's evidence base; depends on the product's existing (unreviewed here) account-deletion policy. (§8)
7. Plan layer (§13): build or not — deferred pending evidence from initial Continuity usage, not decided here.
8. Compare layer (§14) minimum sample thresholds — not numerically set here.
9. How to measure "Compass → Visit" pre-persistence: lightweight analytics-only reference vs. wait for full Continuity schema. (§16)
10. Minimum observation sample size/duration before Phase 8 or a Continuity prototype is greenlit — not set here.

---

## 21. Recommended Next Phase

**Not** Phase 8 Analytics implementation, and **not** History persistence — both remain unauthorized by this audit.

PRODUCT HYPOTHESIS, the recommended sequence: instrument the hypotheses that are cheaply measurable *without any new personal-data schema* — Hypothesis A (same-month reuse) and Hypothesis B (Compass → Shrine Detail click-through) need only ordinary, already-precedented event analytics (§16), not Continuity plumbing. A simple per-account "used Compass in month M" flag would additionally give an early, low-cost read on Hypothesis D. This lets the product observe real signal on whether Compass creates repeat engagement at all, before any Continuity schema, Favorite/Visit/Reflection linkage, or Phase 8 event contract is built.

Only if A/B/D show real signal should Personal Continuity schema design and a full Phase 8 event contract be scoped as an actual implementation phase — mirroring both this product's own established "observe before investing" discipline (Deep Dive Observation Phase) and Phase 7's identical conclusion about Compass itself.

---

## 22. Final Classification

```
Compass Free Access:              READY
Premium Personal Continuity:      NEEDS VALIDATION
Compass History Responsibility:   NEEDS CLARIFICATION
History Persistence Model:        NOT READY
Favorites Boundary:               CLEAR
Visit Boundary:                   CLEAR
Reflection Boundary:              CLEAR
Premium Cancellation Policy:      PRODUCT DECISION REQUIRED
Analytics Separation:             CLEAR
Phase 8 Analytics Readiness:      PARTIAL
```

**Overall: C — NEEDS VALIDATION BEFORE CONTRACT.**

Not A: multiple items above are explicitly not ready. Not B: the core Continuity concept itself — not just implementation details — needs field validation (§17), so "product decisions" alone understates what's missing. Not D: no architecture conflict was found anywhere in this audit; every open item is additive and consistent with existing precedent, blocked by absence of evidence, not by contradiction.

This mirrors, and is a direct continuation of, the prior audit's own classification (`compass-free-premium-boundary.md`: "PREMIUM BOUNDARY NEEDS VALIDATION"). Both audits land in the same place for the same underlying reason: Compass is new, unmeasured, and this product has an established, deliberate practice of not building monetization or deep persistence ahead of real usage evidence.
