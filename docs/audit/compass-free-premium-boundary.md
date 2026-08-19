> **Status: Audit / Historical（Phase 7 — Free/Premium Boundary Audit）**
>
> This document is a docs-only, point-in-time audit. It contains no code, model, migration, entitlement, pricing, paywall, Analytics, Compass behavior, or Concierge behavior changes. It does not alter the wording of any existing canonical document. Where this audit reaches a conclusion, that conclusion is a **PRODUCT DECISION proposal for review**, not an implemented change.
>
> Every substantive claim below is tagged **FACT** (verified in code or a canonical doc as of this audit), **CONTRACT** (an existing binding rule quoted from an Active doc), **HYPOTHESIS** (this audit's own untested reasoning), or **PRODUCT DECISION** (a recommendation requiring explicit sign-off before any implementation phase).

# KAMI MUSUBI — Compass-Inclusive Free / Premium Boundary Audit

## 1. Executive Summary

**Headline conclusion:** the existing Free/Premium boundary — already Active in `docs/product/premium-experience.md` and already shipped in code for Concierge, Shrine Detail, and Visit/Reflection — does **not** need to change to accommodate Compass. Compass's currently-shipped experience (purpose selection, origin selection, one current-month direction result) should stay **entirely Free**, unchanged from its state today. There is no currently-implemented Compass capability that meets this product's own bar for "recurring value worth paying for" — the candidate recurring value (month-to-month direction change, cross-month comparison) is not built yet.

This audit therefore does not add a new gate. It **confirms an absence of a new gate is correct for now**, and records the specific future capability (persisted month-over-month Compass history/comparison) that would become a legitimate Premium candidate if and when it is built — using the same Continuity Gate pattern the product already uses for Reflection.

**Final Classification: PREMIUM BOUNDARY NEEDS VALIDATION** (scoped specifically to Compass; the pre-existing non-Compass boundary is unaffected and remains its own settled contract — see §21).

**Why not READY:** Compass shipped (PR #2479) and got a Home entry point (PR #2483) only very recently, with zero observed usage data. This product has an established, deliberate pattern of separating "ship and observe" from "monetize" — the same pattern already recorded for Deep Dive (`docs/audit/deep-dive-production-go.md` §6: Observation Phase, no new implementation until usage data or a validated user problem justifies it). Recommending a Compass-specific Premium gate today — even a well-reasoned future one — before any usage signal exists would repeat the mistake that principle exists to prevent.

**Why not BLOCKED:** there is no unresolved contract conflict and no sustainability gap. The product's existing Premium value (Concierge depth, Shrine Detail personalization, Reflection/Visit continuity) is real, already shipped, already coherent, and untouched by this audit. Compass simply isn't part of the Premium boundary yet, and that is a valid, intentional state — not a blocker.

---

## 2. Current Product Inventory

All rows are **FACT**, sourced from the codebase and current Active docs (see full citations in §11 and inline).

| Capability | Current route/surface | User value | Current gate | Value timing | Depends on stored history? | Improves Recommendation quality? | Improves continuity/action? | Canonical contract |
|---|---|---|---|---|---|---|---|---|
| Home | `apps/web/src/app/page.tsx` → `HomeMainClient.tsx` | Entry/orientation | Ungated | N/A | No | No | No | `docs/product/home-hero-final-wireframe.md` |
| Concierge (consultation) | `apps/web/src/app/concierge/ConciergeClientFull.tsx` | Consultation → basic recommendation | **Usage-gated**: 3/day free+anonymous, unlimited premium (`backend/temples/services/quota_policy.py`) | Repeat-use | No (quota only; no personalization from history yet) | No (basic tier) | Partial | `docs/product/premium-experience.md` §画面別の境界 |
| Recommendation Result (basic) | Rendered inside Concierge | "Why this shrine" (basic reason) | Free | Repeat-use | No | Yes (core function) | No | `docs/product/premium-experience.md` |
| Recommendation Result (depth) | `ConciergeSectionsRenderer.tsx`, `PremiumStateDeltaCard.tsx` | Deeper reason, compatibility explanation, prior-context comparison | **Premium** | Recurring/time-updating (depends on accumulated consultations) | Yes | Yes (explanation depth, not ranking) | Yes | `premium-experience.md`; enforced via `getVisibilityForCard` / `cardVisibility.ts` |
| Shrine Detail (basic) | `apps/web/src/app/shrines/[id]/page.tsx` | 由緒・所在地・ご利益・公開御朱印 | Free | One-time (per shrine) | No | No | No | `premium-experience.md` |
| Shrine Detail (personalized) | `ShrineDetailArticle.tsx:172, 290-310` | Personal-fit supplement, "change since last time" | **Premium** | Recurring/time-updating | Yes | No | Yes | `premium-experience.md` |
| Compass (purpose + origin + monthly direction) | `apps/web/src/app/compass/page.tsx` → `CompassClient.tsx` | Monthly orientation + candidate shrines for a chosen purpose/origin | **Ungated** (no frontend or backend check; backend view docstring states explicitly no gating "Phase 5時点で") | One-time per session today (see §3, §8) | No — stateless, no persistence (`compass-mvp-runtime-contract.md` §7) | Yes (candidate narrowing within month) | Action-adjacent (points at "go this month"), not continuity | `docs/product/compass-product-contract.md`, `compass-mvp-runtime-contract.md` |
| Visit (log a visit) | `backend/temples/api/views/visit.py`; consumed via `apps/web/src/lib/api/visits.ts`, `MyPageView.tsx`, `ShrineDetailArticle.tsx` | Record that a visit happened | Free ("保存そのものをPremium限定にはしない" — `visit-reflection-flow.md:349+`) | Repeat-use | Creates history | No | Yes | `docs/product/visit-reflection-flow.md` |
| Reflection (write) | `backend/temples/api/views/reflection.py`; consumed via `ShrineReflectionPrompt.tsx` (create only) | Capture short reflection after a visit | Free | Repeat-use | Creates history | No | Yes | `visit-reflection-flow.md` |
| Reflection (compare/review history) | Backend `GET /api/reflections/` exists; **not consumed anywhere in `apps/web`** — no web screen exists | Compare against past reflections, recurring themes | **Premium** (per contract) — but **not reachable on web today**; a web-side gap, not a gating decision | Recurring/continuity | Yes | No | Yes | `visit-reflection-flow.md` |
| Journey Timeline | Backend `GET /api/journeys/timeline/` exists; **not consumed anywhere in `apps/web`** | Chronological consultation→recommendation→visit→reflection view | Free by contract ("Journey Timeline自体は無料ユーザーでも利用できる" — `journey-timeline-design.md`); Premium reserved for future long-history/search/compare | Recurring | Yes | No | Yes | `docs/product/journey-timeline-design.md` |
| Favorites/save | `apps/web/src/hooks/useFavorite.ts`, backend `FavoriteViewSet` | Bookmark a shrine | Free (documented free limit of 10 in `quota_policy.py`, **not actually enforced in code**) | Repeat-use | Creates a small history | No | Slight (revisit intent) | `premium-experience.md` ("最小限の保存・御朱印管理"は Free) |
| Goshuin upload | `backend/temples/api/views/goshuin.py`, `goshuin_limit.py` | Record a shrine seal | Flat `MAX_MY_GOSHUINS_FREE = 10` for **all** users including Premium (limit function ignores plan) | Repeat-use | Creates history | No | Slight | Inconsistent with `premium-experience.md`'s "保存・記録の深さを広げる" Premium promise — see §17 open item |
| Premium upgrade entry points | `PremiumStateDeltaCard.tsx`, `PremiumUpgradePrompt` (Shrine Detail), Concierge quota-exhausted CTA, `/billing/upgrade` | — | N/A (these *are* the paywall surfaces) | — | — | — | — | `docs/product/billing-paywall.md`, `docs/product/monetization-flow-design.md` |

---

## 3. One-Time Value vs Recurring Value

Classification per the task's A–F taxonomy. **FACT** unless marked otherwise.

| Capability | Class | Reasoning |
|---|---|---|
| Concierge consultation (basic recommendation) | B (repeat-use) + F (recommendation-quality) | Free-tier value; each consultation independently useful, quota-limited not content-limited |
| Basic "why this shrine" | A (one-time, per shrine) + F | Understood once per recommendation instance |
| Shrine Detail (basic facts) | A (one-time, per shrine) | Static reference content |
| Shrine Detail (personalized reason) | C (time-updating) + D (history-dependent) | Changes as user's consultation history accumulates |
| Monthly Compass direction | **C (time-updating) — but only nominally today.** HYPOTHESIS: the *design intent* is C, but the *shipped* capability recomputes statelessly per request with no month-selection UI (§8) — so today it behaves as **A (one-time)** in practice, not yet C. Do not assume C merely because it uses a month unit — the task explicitly warns against this, and the code confirms the warning is warranted. |
| Purpose variation within Compass | B (repeat-use) + E (convenience) | Implemented, changes candidate set live within a session — genuinely repeat-use today |
| Origin variation within Compass | B (repeat-use) + E | Same — implemented and live |
| Saved history (Visit log) | D (history/continuity) | Real DB record, but currently only a flat list, no comparison |
| Month-to-month Compass comparison | **Not implemented.** Would be D if built. Currently: N/A. |
| Reflection continuity (compare past reflections) | D — **CONTRACT-defined Premium value**, but **not reachable on web** (§2) | `visit-reflection-flow.md` treats this as the canonical Premium recurring value; the web client gap means this contract is not yet fully realized in the product users can touch |
| Visit history (list) | D, currently Free, shallow (list only, no comparison) | |
| Personal trend analysis | D + F (if it ever influences ranking) — **currently unimplemented anywhere** (Journey Timeline Phase 2, explicitly future per `journey-timeline-design.md`) | HYPOTHESIS-free: doc explicitly marks this "現行MVPには含めない" |

---

## 4. Free Experience Minimum

| Check | Status | Evidence |
|---|---|---|
| Free user can experience a complete meaningful path | ✅ | Concierge (3 free uses/day) → basic recommendation → Shrine Detail (basic facts) → Visit/Reflection (save, free) → Compass (fully free, unlimited) all reachable with no payment |
| Free Recommendation remains trustworthy | ✅ | Free tier gets the same underlying ranking (`recommend_limit_for_user` caps *count* shown at 3 vs 6 for Premium — a breadth cap, not a quality cap; core reason logic is shared, not degraded) |
| Basic "why this shrine" remains understandable | ✅ | `premium-experience.md` Free tier explicitly includes "基本推薦" and "神社ごとの基本説明" |
| Shrine Knowledge is not artificially hidden to manufacture Premium value | ✅ | Shrine Detail basic facts (由緒・所在地・ご利益・公開御朱印) are Free by contract; only *personalized* supplement is gated |
| Concierge remains useful without Premium | ✅ | See §9 |
| Compass value can be understood before asking for payment | ✅ (trivially — Compass has no payment prompt anywhere today) | Confirmed no Premium badge/lock exists on `/compass` or its Home entry (`compass-home-entry-ia.md` §8 "Premium Neutrality") |
| Free experience still creates a real action opportunity | ✅ | Compass surfaces a concrete "go this month" direction + shrine candidates; Concierge → Shrine Detail → Visit is a full free action loop |

**Conclusion:** the Free minimum is already sound and this audit finds no reason to touch it. Adding a Compass-specific gate would be the one change that could break this — which is exactly the "what can we hide" trap the task instructions warn against, and this audit declines it (§16).

---

## 5. Premium Value Principle

Task's hypothesis under test: *"Premium value should lean toward time / direction / continuity / history / action rather than 'Free Recommendation is intentionally worse.'"*

**Classification: SUPPORTED — and already the shipped design, independent of this audit.**

Evidence (FACT):
- `premium-experience.md` line 13: 「神社を探せる」ことではなく、「なぜ自分に合うのかが分かり、記録として積み上がる」ことに価値を置く — value is explained-fit + accumulation, not access.
- Explicit banned framings (`premium-experience.md:65-70`): 「地図が高機能になる」「検索条件が増える」「近い神社をもっと探せる」「経路案内が便利になる」, with the summary rule "Map / Search は到達手段であり、Premium 訴求の主語にしない."
- Code confirms this is enforced, not aspirational: Free and Premium Concierge share the same underlying recommendation function; Premium changes *depth of explanation* (`PremiumStateDeltaCard`, personalized Shrine Detail sections) and *breadth* (`recommend_limit_for_user`: 3 vs 6 shown), never the correctness or trustworthiness of the core "why."

This means the hypothesis doesn't need to be newly adopted by this audit — it needs to be **extended consistently to Compass**, not reinvented. Applying it to Compass: Compass's core direction/candidate computation must stay Free-quality-equal regardless of any future gate; only depth/continuity add-ons (month history, comparison) would ever be Premium candidates. No such add-ons exist yet (§3), so there is nothing for a Compass gate to attach to today.

---

## 6. Gate Model Comparison

### Model A — Feature Gate (Compass itself is Premium-only)

- Clarity: high (binary), but **directly contradicts an already-made, adjacent PRODUCT DECISION**: `compass-home-entry-ia.md` §8 explicitly chose a neutral (non-emerald) CTA tone specifically *to avoid implying a future Premium tier* when adding Compass to Home. Gating Compass now would retroactively invalidate that decision's stated intent within the same release cycle.
- Conversion potential: HYPOTHESIS — likely low-to-moderate; user cannot evaluate "monthly direction guidance" before paying, and the category is unfamiliar (this is not a known SaaS pattern like "unlimited seats").
- User understanding before purchase: poor — nothing to preview.
- Recurring value: none created by gating alone; gating a feature doesn't make its underlying value recurring if it wasn't already (§3 shows it currently isn't).
- Risk of making Compass invisible: high — new features that require payment before any trial are the ones most likely to be ignored at a Home entry point, undermining the just-shipped discovery investment (PR #2483).
- Home discovery implications: would force `compass-home-entry-ia.md` to be revisited/contradicted.
- Retention implications: none — gating a one-time-feeling experience doesn't build a recurring reason to return.

**Verdict: reject.** Contradicts an adjacent shipped decision and gates a feature whose value isn't recurring yet.

### Model B — Depth Gate (basic Compass free, deeper interpretation/continuity Premium)

- Free value sufficiency: would remain sufficient (current experience *is* what would stay free).
- Natural upgrade moment: theoretically after first result, "want deeper interpretation" — but HYPOTHESIS: today there is no additional "深掘り" content designed or built for Compass (unlike Concierge, which has `PremiumStateDeltaCard` ready to reuse this pattern). Depth Gate requires a defined deeper layer that doesn't exist.
- Risk of arbitrary information hiding: real — task explicitly warns against manufacturing Premium value by hiding basic understanding; without a genuinely deeper interpretation already designed, a Depth Gate here would default to exactly that trap.
- Recommendation trust / retention: neutral to positive *if* a real deeper layer is designed later; currently N/A.

**Verdict: not actionable today** — no deeper Compass content exists to gate. Worth keeping as a *future* candidate once/if a genuine "深掘り" layer (e.g., richer 相性 explanation between purpose and shrine, matching Concierge's existing pattern) is designed — see §12.

### Model C — Usage Gate (limited free Compass uses)

- User comprehension: moderate — users already understand this pattern from Concierge's 3/day quota.
- Monthly reuse: HYPOTHESIS — Compass's natural cadence is monthly (per its own Time Model contract), so a *daily* usage cap doesn't map to its usage rhythm at all; within one month, repeat use (purpose/origin exploration) is core to understanding the feature, not overuse to prevent.
- Frustration risk: high if capped too low, given exploration (changing purpose/origin) is itself the intended in-session behavior (§3) — capping it would punish the exact behavior the UI was built to encourage.
- Compatibility with current plan/quota system: technically compatible (`quota_policy.py` pattern exists) but **no `compass` entry exists in `QUOTA_POLICY` today** (FACT, confirmed by code research) — would require net-new plumbing.

**Verdict: reject for MVP.** Poor fit for Compass's actual usage shape (session-level exploration, not daily spam); would need new quota infra for a benefit that doesn't match the task's core principle (recurring value, not friction).

### Model D — Continuity Gate (current result free; history/comparison/continuity Premium)

- Monthly subscription fit: HYPOTHESIS — the best conceptual fit of all four models, since it monetizes the thing a monthly product naturally accrues (a growing personal record across months), matching the pattern already Active for Reflection (`visit-reflection-flow.md`: comparison/organization Premium, saving free).
- User trust: high — mirrors an already-trusted, already-shipped pattern elsewhere in the product; nothing novel to explain.
- Implementation complexity: currently **high**, because the prerequisite (persisting Compass results, adding a Join Key to connect them across months) does not exist (`compass-mvp-runtime-contract.md` §7: explicitly Session/Runtime-only, no persistence "necessary" for MVP).
- Retention potential: HYPOTHESIS — likely strong once built, for the same reason Reflection's continuity gate is retention-shaped: it rewards staying subscribed across months rather than any single visit.
- Relationship with Visit/Reflection: natural — could become one continuity surface, not three separate ones.
- Enough Premium value today vs future-only: **future-only.** This is the honest answer the task explicitly asks for (§18): current Compass does not yet justify a Continuity Gate by itself, because there is nothing continuous to gate.

**Verdict: correct target model for Compass, but not implementable yet.** This is the one to build toward, not the one to ship now.

---

## 7. Hybrid Options

Per the task's instruction to prefer the smallest coherent boundary and not add mechanisms for their own sake: **no hybrid is recommended for Compass today.** The smallest coherent boundary is "Compass stays entirely Free, unchanged" (Model D deferred, Models A/B/C rejected). Introducing a hybrid now would mean gating something to satisfy a matrix rather than because a genuine second value tier exists — exactly what §7 of the task instructs against.

The *existing* hybrid (Depth Gate for Concierge + Shrine Detail, Continuity Gate for Reflection/Visit) already covers the rest of the product and needs no change.

---

## 8. Compass-Specific Value Audit

| Question | Answer |
|---|---|
| Is one Compass result valuable enough on its own? | **HYPOTHESIS, plausible-yes**: a monthly direction + narrowed shrine candidates for a stated purpose is a complete, self-contained answer to "where should I go this month." No usage data exists yet to confirm actual perceived value (this is exactly why §21 classifies as NEEDS VALIDATION). |
| Is there a reason to use Compass again in the same month? | **FACT, yes** — changing purpose or origin produces a different, tested result (`test_changing_purpose_changes_recommendation_order`) within the same month; this is real repeat-use value that exists today. |
| Is there a reason to return next month? | **Not currently supported by the product** — the frontend has no month picker and always computes for "now" (`CompassClient.tsx:26`); the backend accepts an unused `target_date` param. Nothing in the UI currently prompts or rewards a next-month return. This is a genuine product gap independent of monetization, worth noting as an open item (§17), not a Premium lever by itself. |
| Does changing purpose create sufficiently different value? | **FACT, yes** (see above) — verified by backend test. |
| Does changing origin create meaningful exploration? | **FACT, implemented** (device/manual/prefecture modes); depth of "meaningfulness" is HYPOTHESIS/unmeasured. |
| Which value is truly recurring? | Only the in-session purpose/origin exploration (B — repeat-use), confirmed today. Cross-month recurrence is designed-for by the Time Model (MONTH grain) but not yet built into any user-facing flow. |
| Which value currently exists vs only exists in future designs? | **Current:** purpose exploration, origin exploration, one coherent monthly result. **Future-only:** month selection/navigation, cross-month comparison, connection to Reflection/Visit (no Join Key exists). |

---

## 9. Concierge Protection

| Check | Status |
|---|---|
| Concierge Recommendation quality is not reduced for Free | ✅ **CONTRACT**, `concierge-compass-product-responsibility-contract.md` §10: 「Concierge品質はPremium価値創出のために意図的に劣化させられてはならない」 |
| Core consultation understanding is not Premium-only | ✅ Free tier gets 基本推薦 + 基本説明 by contract, confirmed shipped |
| Primary Recommendation reason remains trustworthy | ✅ Same ranking/reason pipeline for both tiers; Premium changes explanation depth and shown-count (3→6), not correctness |
| Premium does not become "we explain why only if you pay" | ✅ — the *primary* reason is Free; Premium adds *additional* compatibility/continuity explanation on top, doesn't withhold the primary one |
| Existing Free usage limits are evaluated separately from quality | ✅ this audit treats them separately (see below) |

**Usage restriction vs quality degradation, made explicit:**
- Usage restriction (legitimate, already shipped): 3 consultations/day for Free+anonymous; 3 shrines shown vs 6 for Premium.
- Quality degradation (would violate the contract, **not found**): no evidence the underlying ranking, reasoning, or shrine data differs by tier.
- **Risk flagged, out of this audit's scope to fix:** `FeatureUsage` (the quota counter) has no date/period field, and the code research found no verified daily-reset mechanism — a legacy `ConciergeUsage` model is blended in via `max()`, which can only raise the effective count, never lower it. This is a data-integrity risk to the *usage-restriction* mechanism, not a quality-degradation issue, and not something this docs-only audit can or should fix. Recorded as an open item (§17).

---

## 10. Compass / Concierge Relationship

**CONTRACT** (already established, not re-litigated here — `concierge-compass-product-responsibility-contract.md`, classification "B — CLEAR WITH CONTRACT FOLLOW-UP"):
- Concierge = 「相談から意味を見つける」
- Compass = 「時間と方向から行動のきっかけを作る」
- Signal reuse (shared calculation modules) ≠ authority reuse (Compass does not inherit Compat Mode's product-level restrictions, and does not gain any new authority to explain "why this shrine").
- Gate B (`concierge-first-final-spec.md:29`, 方位のUI前面化 restriction *inside Concierge*) remains unchanged and untouched by Compass's existence.

**This audit's addition:** the Concierge→Compass future path (Concierge → shrine → "when should I go?" → Compass → visit → Reflection) described in the task is a plausible **future** upgrade path, but nothing in the current product implements a transition *from* Concierge *into* Compass with any carried context — they are two independently-entered surfaces today (Compass is reached from Home, not from a Concierge result). Per the task's own instruction (§10: "Do not require this future path for the current MVP boundary unless already implemented"), this audit does not treat that transition as a current upgrade moment (see §12).

**Premium monetization of the relationship itself:** **NOT SUPPORTED today** — there is no continuity artifact connecting the two products yet (no Join Key, confirmed in §8). Monetizing "the relationship" would mean monetizing something that doesn't exist. Deferred to future work, same as Model D in §6.

---

## 11. Home / Discovery Boundary

The task requires separating four distinct things. All FACT, from code and `compass-home-entry-ia.md`:

- **Discovery** — ✅ full. `HomeCompassSection` on Home, plainly labeled ("今月から探す" / "参拝コンパスを見る"), ranked above the utility SUB PATHS section.
- **Access** — ✅ full and free. Clicking through reaches `/compass` with zero gate.
- **Value exposure** — ✅ full. The entire current Compass experience (purpose, origin, result) is exposed before any payment concept appears anywhere in the flow.
- **Upgrade** — N/A today. There is no upgrade prompt anywhere in the Compass flow, and this audit recommends not adding one (§16).

**Explicit confirmation of the task's framing rule:** "A Premium feature does not automatically need to be hidden from Home" — moot here, since Compass isn't a Premium feature today; but worth recording that *if* a future Continuity Gate (§6 Model D) is built, the existing Home entry, discovery, and access should stay exactly as-is — only a new, separate continuity/comparison surface (reached from within Compass after a user has multiple months of results) would carry any gate. This preserves `compass-home-entry-ia.md`'s Premium Neutrality decision permanently, not just for this release.

---

## 12. Upgrade Moment Analysis

| Candidate moment | User already understood value? | Interruption cost | Perceived fairness | Conversion potential | Retention relevance | Implementation complexity | Verdict |
|---|---|---|---|---|---|---|---|
| Before entering Compass | No | High (blocks first-touch entirely) | Low | HYPOTHESIS: low (nothing to evaluate) | None | Low | Reject (= Model A) |
| After showing monthly direction | Partially | Medium | Medium | HYPOTHESIS: low-medium | None (one-shot) | Low | Reject — nothing recurring to sell yet |
| Before shrine recommendations (inside Compass) | No | High | Low | Low | None | Low | Reject |
| After first Compass result | Yes | Low | Medium | HYPOTHESIS: low — user has no second data point to compare against, so "upgrade for comparison" has nothing to compare | Low | Medium (needs a CTA + copy) | Defer — premature, no comparison exists yet |
| On second use (same month, changed purpose/origin) | Yes | Low | High (already engaged) | HYPOTHESIS: still low — this is Free-tier exploration by design (§8), gating it would punish intended behavior | Low | — | Reject — would gate a Free-by-design behavior |
| When a second month's result becomes available | Yes (would have real prior context) | Low | High | HYPOTHESIS: highest of all candidates — this is the one moment where "compare this month to last month" is a real, self-evident, ungated-preview-then-gated-depth pitch, matching the existing Reflection pattern | HYPOTHESIS: highest — directly rewards continued subscription across the natural monthly cadence | High — requires persistence + Join Key (not built) | **Best future candidate. Not buildable today.** |
| When connecting Reflection/history to Compass | Yes | Low | High | Medium (future) | High (future) | High (no Join Key exists) | Future candidate, dependent on the above |

**Primary conclusion:** every currently-buildable upgrade moment for Compass is weak; the one strong candidate (second-month comparison) requires unbuilt persistence. This is the clearest evidence for this audit's core recommendation: don't force an upgrade moment into today's Compass, wait for the natural one to become buildable.

---

## 13. Current Premium Contract Reconciliation

Read against `docs/product/premium-experience.md` (Active) and the four Compass-chain audits that already flagged this exact question as open:

- **Existing banned framings** ("better search," "stronger map," "better recommendation" — see §5 exact quotes) — Compass's raw pitch ("direction/place/time") was already flagged by `premium-visit-compass-recommendation-feasibility.md`, `premium-visit-compass-time-model-contract.md`, and `compass-contract-reconciliation-direction-audit-completion.md` as *at risk* of reading like this banned framing unless personal/continuity value is foregrounded. **This audit resolves that open flag**: because Compass is staying Free with no Premium pitch attached at all right now, the risk doesn't materialize — there is no Compass Premium copy to violate the rule. The risk becomes live again only when/if a future Continuity Gate is designed (§6 Model D), at which point that copy must explicitly foreground "継続する行動文脈" (comparison/continuity across months), never "better direction-finding" — consistent with `premium-experience.md`'s existing rule, applied to Compass rather than reinvented.
- **`concierge-compass-product-responsibility-contract.md`'s own open item**, "Premium Compatibility: NEEDS CLARIFICATION" — **this audit closes that item** with the recommendation in §16: Compass is Free today, Continuity Gate is the correct future direction, no gate is added now.
- **No conflicts found** between this recommendation and any Active contract. `compass-product-contract.md` §12 explicitly defers Paywall/pricing/entitlement decisions to a later document — this audit is that later document, and it defers further, for evidence reasons (§21), not authority reasons.

---

## 14. Current vs Future Premium

**CURRENT PREMIUM (unchanged by this audit, already shipped):**
- Concierge: recommendation depth, compatibility explanation, continuity analysis (`PremiumStateDeltaCard`), 6 vs 3 shrines shown.
- Shrine Detail: personalized reason supplement, "change since last visit" delta.
- Reflection (contract-level; web UI gap noted in §2): comparison/organization of accumulated reflections.

**FUTURE PREMIUM (not implemented, not to be built under this Phase's authorization):**
- Compass month-over-month comparison (Model D, §6) — requires persistence + Join Key.
- Compass "深掘り" interpretation layer (Model B, §6) — requires new content design, doesn't exist even in draft form today.
- Reflection web UI reaching parity with its own existing backend/contract (a product gap, not a monetization one).
- Journey Timeline Phase 2 (search, comparison, statistics, emotion trend) — already explicitly marked future-only in `journey-timeline-design.md`.

This audit does not require any future item to justify the current boundary (per task §18) — the current boundary is already justified by what's shipped for Concierge/Shrine Detail/Reflection, independent of Compass entirely.

---

## 15. KPI Requirements (definitions only — no implementation)

Per task §16, defining what Phase 8 Analytics would need to measure, without building it:

**Free value:**
- Concierge completion rate (consultation started → recommendation shown)
- Compass discovery rate (Home impression → Compass entry click)
- Compass activation rate (Compass entry → first result completion)
- Compass in-session repeat rate (purpose or origin changed within the same session)

**Premium intent:**
- Upgrade CTA exposure (by surface: Concierge, Shrine Detail — Compass has none today, so N/A until §6 Model D ships)
- Checkout start rate
- Conversion rate, by originating surface

**Recurring value:**
- Concierge repeat-day rate (returns after quota reset)
- Compass same-session repeat-use rate (already meaningful today, per §8)
- Compass next-month return rate (**cannot be measured today** — no month-selection UI exists to generate this signal; this KPI itself depends on the future work in §14)
- Reflection/Visit continuation rate

This section defines the metric *names and intent* only, as instructed; no event schema, table, or instrumentation is created here.

---

## 16. CVR / Retention Tradeoff

Applied to the one real decision this audit makes (leave Compass Free, defer Model D):

- **Short-term CVR effect:** none — this audit adds no new paywall, so no immediate CVR change in either direction.
- **Medium-term retention effect:** HYPOTHESIS, likely neutral-to-positive — keeping Compass fully free and well-exposed via its new Home entry protects the discovery investment already made (PR #2483) and gives the product more time to accumulate the usage signal a real Continuity Gate would need to be well-calibrated.
- **Risks avoided by this recommendation:**
  - Free value too low — avoided (nothing removed).
  - Premium value too weak — avoided (no weak Premium pitch is shipped; Model D is deferred until it can be strong).
  - Paywall too early — this is the risk a Feature/Depth/Usage gate would have created today; explicitly avoided by this recommendation.
  - Recurring promise unsupported — avoided; this audit refuses to sell "continuity" before continuity is built.
- **Risk accepted by this recommendation:** near-term Premium CVR from Compass specifically is $0, since no gate exists. This is accepted deliberately, per the task's own decision priority ordering (§17 of the task: sustainable recurring value > trust > consistency > CVR > simplicity).

---

## 17. Options Matrix

| | Free value quality | Premium CVR hypothesis | Premium retention hypothesis | Product coherence | Implementation complexity | Trust risk | Current-feature support | Future-feature dependency |
|---|---|---|---|---|---|---|---|---|
| **Model A — Feature Gate** | Destroyed for Compass | Low (nothing to preview) | None | Contradicts shipped Home-entry decision | Low | High (breaks Premium Neutrality promise just made) | None | None |
| **Model B — Depth Gate** | Preserved | Unknown — no deeper content exists to sell | Unknown | Consistent in principle, but nothing to gate | Medium (needs new content design first) | Medium (risk of manufactured hiding if rushed) | None | High (needs a designed "深掘り" layer) |
| **Model C — Usage Gate** | Degraded (punishes intended in-session exploration) | Low-medium | Low (mismatched cadence — daily cap on a monthly-cadence feature) | Poor fit | Medium (new quota infra) | Medium | None | None |
| **Model D — Continuity Gate** | Preserved | Unknown, but best long-run fit hypothesis | Highest hypothesis of all four | Highest — mirrors existing Reflection pattern | High (persistence + Join Key required) | Low (once built, matches trusted existing pattern) | None | High (persistence, month picker, comparison UI) |
| **Recommended: No gate now, Model D as future target** | Fully preserved | 0 near-term (deliberate) | Preserves future retention upside | Highest — smallest coherent change (§7) | None required now | Lowest | Full (matches what's shipped) | Explicit, scoped future item |

---

## 18. Recommended Boundary

**Recommended Free Boundary:**
Everything currently Free stays Free, unchanged: Concierge (3/day quota, basic recommendation + basic reason), Shrine Detail basic facts, full Compass (purpose selection, origin selection, one monthly result, unlimited in-session exploration), Visit logging, Reflection writing, Favorites.

**Recommended Premium Boundary:**
Unchanged from what's already shipped: Concierge recommendation depth/compatibility/continuity explanation, Shrine Detail personalized reason + "change since last visit," Reflection comparison/organization (contract-level; web UI gap is a separate, non-monetization backlog item).

**Recommended Gate Type:** HYBRID (already shipped: Depth Gate for Concierge + Shrine Detail, Continuity Gate for Reflection) — **no new gate added for Compass.**

**Compass Free Exposure:** FULL BASIC EXPERIENCE.

**Concierge Impact:** NONE. §9 confirms no quality degradation exists or is proposed.

**Current Premium Value Proposition:** unchanged — "深掘りされた理由、相性の説明、継続する記録" (per `premium-experience.md`), independent of Compass.

**Future Premium Expansion:** Compass Continuity Gate (Model D) — cross-month comparison, once persistence + Join Key + a month-selection UI exist. Not authorized by this Phase.

**Primary Conversion Moment:** unchanged, existing ones (Concierge quota-exhausted CTA, Shrine Detail state-delta prompt). No new Compass-originated conversion moment exists today; the best future one is second-month Compass comparison (§12).

**Primary Retention Mechanism:** accumulated personal record (Reflection/Visit history + depth explanations), unchanged. Compass could add to this in the future via month-over-month continuity, once built.

**Pricing Ready:** NO (out of scope by task design, and `pricing.md`/`premium-experience.md` both already state price is undecided).

**Analytics Contract Ready To Design:** PARTIALLY — the KPI *names* are defined in §15 and could inform a future Phase 8 scope, but a full event/schema contract is not ready and is explicitly not authorized here.

---

## 19. Open Decisions

Not resolved by this audit, flagged for separate, appropriately-scoped follow-up (none of these are part of this Phase's authorization):

1. **Quota reset integrity** (§9): `FeatureUsage` has no date/period field; the daily Concierge quota's reset behavior could not be verified in code. This affects the *existing* usage-restriction mechanism's correctness, not the Free/Premium boundary itself — worth a focused bug investigation.
2. **Goshuin upload limit ignores plan** (§2): `MAX_MY_GOSHUINS_FREE = 10` applies to Premium users too, inconsistent with `premium-experience.md`'s stated Premium promise of expanded save/record depth. Worth a focused product/bug review, separate from this boundary audit.
3. **Reflection web UI gap** (§2, §14): the backend `GET /api/reflections/` list endpoint and the Journey Timeline endpoint are both unconsumed by `apps/web`. This is a product-completeness gap for an *already-Free* feature (Journey Timeline) and an already-Premium contract item (Reflection comparison) — neither is a boundary decision, both are implementation backlog.
4. **Compass month-selection UI** (§8, §12): no way to view a different target month exists in the frontend even though the backend already accepts `target_date`. Building this is a prerequisite for the future Continuity Gate, but is itself a product feature decision independent of monetization, and not authorized here.
5. **When to revisit this audit:** recommended trigger is real Compass usage data (discovery rate, activation rate, in-session repeat rate — §15) or a concrete validated user request for month-over-month comparison — mirroring the same observation-before-investment discipline already applied to Deep Dive.

---

## 20. Final Classification

**PREMIUM BOUNDARY NEEDS VALIDATION**

Scoped precisely: this applies to the *Compass-specific* extension of the Premium boundary. The pre-existing, non-Compass boundary (Concierge/Shrine Detail/Reflection) is not in question, is already shipped, already coherent, and is explicitly reaffirmed unchanged by this audit — it would be inaccurate to call the whole product's boundary "not ready" when most of it already is.

What's needed before Compass could earn a READY classification for its own gate: real usage evidence (discovery/activation/repeat-use data) and, separately, the actual construction of the one feature worth gating (cross-month continuity) — neither is authorized under this Phase, both are exactly the kind of "wait for data" prerequisite the task's own decision priority (§17: sustainable recurring value first, CVR last) calls for.
