> **Status: Audit / Historical（Compass Runtime / Personal Shrine Continuity Boundary Audit）**
>
> This document is a docs-only, point-in-time audit. It reconciles, but does not silently rewrite, two merged predecessor audits: `docs/audit/compass-free-premium-boundary.md` (#2484, merged) and `docs/audit/compass-premium-personal-continuity.md` (#2485, merged). It contains no code, model, migration, entitlement, pricing, or Analytics implementation changes, and does not modify Concierge, Compass Recommendation Ranking, Evidence Gate, or Shrine Knowledge.
>
> Every substantive claim is tagged **FACT** (verified in code or a canonical doc as of this audit), **INFERENCE** (a conclusion drawn by combining verified facts), **PRODUCT HYPOTHESIS** (an untested reasoning judgment), or **OPEN DECISION** (a question this audit cannot and does not resolve).

# KAMI MUSUBI — Compass Runtime / Personal Shrine Continuity Boundary Audit

## 1. Executive Summary

**The principle under test:**

> Compass is a monthly runtime discovery/action surface. Its recommendation result is not itself a permanent personal history. Personal continuity begins when the user intentionally preserves or performs an action related to a shrine — Favorite, Visit, or Reflection.

**Conclusion: this principle can be formally adopted. It does not conflict with any current canonical contract or shipped code, and it sharpens — rather than contradicts — the prior audit chain.**

Two findings drive this:

1. **Compass genuinely needs zero new persistence to support Personal Shrine Continuity.** `Favorite`, `Visit`, and `ShrineReflection` already each carry a `user` FK, a `shrine` FK, and a creation timestamp (FACT, §4). A cross-time personal timeline (§11) can be assembled entirely by composing/reading these three existing tables. No new "Compass History" table, migration, or canonical record is required to realize the product concept.
2. **This supersedes one specific implication of the prior audit, not its conclusion.** `compass-premium-personal-continuity.md` (#2485) already concluded, in its own §4, that "Personal Continuity, not Compass History" was the right *framing* — this audit agrees and does not revisit that call. But #2485's §5–§6 went on to sketch a "Compass History" *record* (a persisted entity, anchored to a meaningful action, carrying month/purpose/direction/shrine fields) as the mechanism to realize that framing. This audit finds that mechanism unnecessary: the meaningful action itself — the `Favorite`, `Visit`, or `Reflection` row the user already creates — **is** the durable record. Compass does not need to own, mirror, or co-persist any part of it (§3, full reconciliation).

**What remains open is narrower than before:** whether a lightweight *provenance* signal ("this shrine reached the user via Compass") is worth adding to `Favorite`/`Visit`/`Reflection`, and whether that even needs to be durable DB persistence or can stay analytics-only (§6). Nothing about Personal Shrine Continuity itself depends on resolving that question.

**Final Classification: C — NEEDS VALIDATION BEFORE CONTRACT** (§22) — the same overall bucket as #2484 and #2485, for the same reason each time: no architecture conflict exists anywhere in this chain, but no usage evidence yet justifies committing to build anything beyond what's already shipped.

---

## 2. Current Contract State

Re-verified against `develop` at this audit's branch point (both `#2484` and `#2485` confirmed **MERGED** — `git log`: `25d37aa8`, `a52e6716`). All **FACT** unless noted.

- Compass API: `backend/temples/api_views_compass.py:44` — `permission_classes = [AllowAny]`. Unauthenticated, unpremiumed, fully open.
- Compass frontend: `apps/web/src/features/compass/CompassClient.tsx` — birthdate is a fresh `useState("")` re-entered every session (`:28,62,75`); no read from `UserProfile.birthday`; no persistence of any kind; no analytics instrumentation anywhere in the Compass frontend or backend (re-confirmed, no new commits touched this area since #2485).
- `docs/product/compass-product-contract.md` and `compass-mvp-runtime-contract.md` (both Active) — unchanged since the prior audits; both still explicitly defer persistence/entitlement/pricing decisions, consistent with this audit's scope.
- `docs/product/premium-experience.md` (Active) — unchanged; still the canonical Free/Premium value framing (depth/continuity, never access/quality).
- Entitlement (`billing_state.py`, `stripe_webhook.py`) — unchanged since #2485's review; cancellation still only flips `UserProfile.subscription_status`/`current_period_end`, deletes nothing.
- No conflicts found between current canonical docs and current production code. **No conflict found between this audit's conclusions and #2484.** One refinement identified against #2485, detailed in §3.

---

## 3. Previous Compass History Hypothesis — Reconciliation

### 3.1 Where "Compass History" was proposed or implied

**In `#2484` (`compass-free-premium-boundary.md`):** the term "Compass History" is not used as a concrete proposal. §6 Model D ("Continuity Gate") discusses future "cross-month comparison" abstractly and explicitly defers the mechanism to a later audit. §18 lists "Compass month-over-month comparison... requires persistence + Join Key" as a **future, undesigned** item. **Nothing in #2484 requires reconciliation — it made no commitment to a specific persisted entity.**

**In `#2485` (`compass-premium-personal-continuity.md`):** this is where a concrete shape emerged:
- §4 (CONTRACT-level conclusion, already correct and retained): *"a standalone 'Compass History' — a plain log of past Compass runs — risks becoming exactly the 'generic cloud storage' trap... Personal Continuity, not Compass History, is the coherent version."* This already rejected a raw-log model.
- §5 (retained principle, refined below): *"Compass History should record meaningful user actions, not generated output"* — i.e., don't persist every candidate shown, only persist when the user acts.
- §6 (the part this audit refines): a **conceptual minimum dataset** for a persisted record — target month, purpose slug, computed direction, acted-on shrine, Visit/Reflection references, timestamp, user FK — implicitly assuming this record would be a **new Compass-owned entity** (referred to throughout as "a Continuity entry," "a Compass History record").
- §9 (OPEN DECISION, still open, now resolved by this audit — see §6 below): *"extend the Favorite model with an optional Compass-session reference, vs. keep Favorite untouched and build a separate Continuity join table."*

### 3.2 What is retained vs superseded

| #2485 conclusion | Status | Reasoning |
|---|---|---|
| "Personal Continuity, not Compass History" is the right product framing (§4) | **RETAINED — reaffirmed, not revisited** | This audit's own findings independently confirm it |
| Compass History should anchor to meaningful actions, not generated output (§5) | **RETAINED, generalized** | Correct principle; this audit shows the "meaningful action" *itself* (the Favorite/Visit/Reflection row) already satisfies it without needing a second, Compass-owned record of the same fact |
| A new persisted record (month/purpose/direction/shrine/refs) is needed to realize Continuity (§6) | **SUPERSEDED** | §4, §11 of this audit show the timeline composes from existing tables with zero new persistence; the only thing genuinely missing is optional provenance (§6 of this doc), which is a much smaller question than a full history record |
| OPEN DECISION: extend models vs. build a join table (§9 of #2485) | **NARROWED, not fully closed** | This audit resolves the larger question (no new canonical table needed for the timeline itself) but leaves the smaller provenance-tagging question open (§6) |
| Birthdate/precise-origin minimization guidance (§6, §18 of #2485) | **RETAINED, unaffected** | Still applies to whatever provenance/profile work happens later |

**This is a follow-up/reconciliation decision, not a rewrite of #2485.** #2485's own historical audit document is unmodified; its conclusions stand as a record of that point in time. This audit records where current analysis goes further.

---

## 4. Runtime vs Durable Data Matrix

Per the task's required field-by-field classification. All **FACT** for current-state columns; classification itself is **PRODUCT HYPOTHESIS** unless marked otherwise.

| Field | Current state | Classification |
|---|---|---|
| Monthly direction runtime (the computed direction for target month) | Computed per-request, never stored (FACT) | **Runtime only** |
| Direction calculation output (raw kyusei/direction values) | Computed per-request via shared calculation modules, never stored (FACT) | **Runtime only** |
| Recommendation candidate list | Computed per-request, never stored (FACT) | **Runtime only** |
| Displayed recommendation order | Derived from candidate list at request time (FACT) | **Runtime only** |
| Compass explanation text | Generated per-request, never stored (FACT) | **Runtime only** — INFERENCE: should stay regenerated-on-read even if any future feature needs to reference "why," per #2485 §6's existing reasoning (avoids staleness vs. Shrine Knowledge updates) |
| Purpose selection | Entered per-session, submitted in the request body, never stored server-side (FACT) | **Runtime only**, with a narrow exception: **User profile data** only if a user explicitly favorites/visits/reflects on the resulting shrine — at that point the *shrine* becomes durable via the existing action record, but the *purpose value itself* still isn't persisted anywhere (§6 provenance discussion) |
| Origin | Entered per-session (device/manual/prefecture), never stored (FACT) | **Runtime only** |
| Birthdate | Entered per-session even for logged-in users; not read from or written to `UserProfile.birthday` (FACT) | **Runtime only** today; **User profile data** only if a separate, independent product decision is made to let users optionally save it to their profile for prefill convenience — explicitly **not** something this audit proposes or requires |
| target_date / solar-month information | Backend accepts an optional `target_date` param; frontend never sends one, always computes for "now" (FACT, re-confirmed from #2484 research) | **Runtime only** |

**Explicit verifications required by the task:**

- Compass recommendation results do not need permanent persistence for MVP — **confirmed.** No current or proposed feature requires it; composition (§11) works without it.
- Compass direction runtime does not need permanent persistence for MVP — **confirmed**, same reasoning.
- Compass explanation text does not need permanent persistence for MVP — **confirmed**, regeneration is sufficient and preferable (staleness avoidance).
- Birthdate must not be duplicated into a Compass-history event merely for historical display — **confirmed as a hard constraint**; moot in practice today since no such event exists, but binding on any future design.
- Precise origin must not be persisted without a demonstrated product requirement — **confirmed as a hard constraint**, consistent with #2485 §6/§18 and the existing `direction-events.md` analytics-minimization precedent.
- No new DB table is required merely to reproduce old Compass result screens — **confirmed.** Nothing in the current or plausible-future product requires reproducing a *specific past Compass screen*; what has value is the downstream *shrine relationship* (favorited/visited/reflected), which already persists independently via existing models (§11).

---

## 5. Durable Action Boundary

**Boundary confirmed as:**

```
Compass result → Shrine Detail viewed → explicit user action → durable personal record
```

- Viewing a Compass recommendation alone creates no permanent personal record — **confirmed**, FACT (§4, no Compass-side persistence exists at all).
- Viewing Shrine Detail alone creates no permanent personal record — **confirmed**, FACT: `ShrineDetailArticle.tsx` renders content and premium sections but creates no database row merely from a page view (view/impression tracking, if any, would be Analytics-only, §15, never a personal record).
- Favorite is a durable user-intent action — **confirmed**, FACT: `temples.models.Favorite` (`models.py:576-609`), explicit `IsAuthenticated`-only `POST`, `user`+`shrine`/`place_id`+`created_at`.
- Visit is a durable user-action record — **confirmed**, FACT: `Visit` (`models.py:691-712`), `user`+`shrine`+optional `thread`+`visited_at`+`status`.
- Reflection is a durable personal record — **confirmed**, FACT: `ShrineReflection` (`models.py:716-756`), `user`+`shrine`+optional `thread`+`answer`+mood fields+`created_at`.
- Goshuin belongs to the same broader personal shrine journey while remaining its own domain responsibility — **confirmed, with a distinct character** (§10): `Goshuin` (`models.py:860-887`) has `user`+`shrine`+`created_at`/`updated_at`, but also `is_public` (default `False`) and `likes` — it is a **partly social/public** artifact (shareable, likeable), unlike the strictly private `Visit`/`Reflection`/`Favorite` records. It participates in the same journey conceptually but must not be silently merged into a private-continuity model without accounting for its public dimension.

**This audit does not merge these domain models.** Each retains its existing, independent responsibility; Personal Shrine Continuity (§11) is a **read/composition layer over them**, not a new owning model.

---

## 6. Compass Provenance Analysis

The one genuinely open question this audit narrows down to. Evaluated per downstream action:

| Question | Favorite | Visit | Reflection |
|---|---|---|---|
| Is Compass provenance useful for product UX? | PRODUCT HYPOTHESIS: mildly — a "discovered via Compass" label could be shown in a future timeline, but is not required for the timeline to have value (the shrine + timestamp + action type already tell most of the story) | Same | Same |
| Is it useful only for Analytics? | PRODUCT HYPOTHESIS: largely yes — the strongest, most concrete use case identified in this audit is measuring the Compass→Favorite/Visit funnel step (§17), which is an Analytics need, not a personal-record need | Same, and this is also exactly the "Compass → Visit" measurement gap already flagged as unresolved in #2485 §16 | Same |
| Does it need durable DB persistence? | **No, not demonstrated.** INFERENCE: the Analytics use case (funnel measurement) does not require a permanent, queryable DB column on `Favorite` — an event fired at the moment of the action, carrying a `source=compass` tag, satisfies it without adding a field to a personal-data table | Same | Same |
| Can existing event/session context provide it? | **Yes, plausibly** — PRODUCT HYPOTHESIS: if the Favorite/Visit/Reflection creation request already knows which page/flow it originated from (a referrer, a query param, an in-memory session context), an Analytics event can capture `source=compass` at write time without the underlying model needing a new column at all | Same | Same |
| Would adding provenance create unnecessary coupling? | **Yes, if added as a durable FK/enum on the model itself.** INFERENCE: a `Favorite.source` (or similar) column would couple a general-purpose bookmark model to Compass's existence, for a benefit (a UX label) not yet shown to matter to users | Same reasoning applies to `Visit`/`Reflection` | Same |

**Conclusion (PRODUCT HYPOTHESIS, this audit's recommendation): prefer the smallest solution — treat Compass provenance as an Analytics-event concern (§15–§16), not a durable-schema concern, until a specific UX requirement (e.g., a "discovered via Compass" badge in a shipped Personal Shrine Continuity view) is actually being built and demonstrably needs it.** This keeps Compass an entry surface only — it never becomes the owner, or even a referenced dependency, of `Favorite`/`Visit`/`Reflection` records. This directly satisfies the task's stated constraint: *"Compass must remain an entry surface, not become the owner of Favorite / Visit / Reflection records."*

**OPEN DECISION, explicitly narrower than #2485 left it:** if/when a UX requirement for provenance display is confirmed, the schema choice (light enum column vs. separate lightweight join) is still undecided — but this is now a small, contained decision, not a prerequisite for Personal Shrine Continuity to exist at all.

---

## 7. Favorite Boundary

Unchanged from #2485's findings, reconfirmed:

- Responsibility: "I like / want to remember this shrine" — a plain, context-free user↔shrine bookmark (`models.py:576-609`).
- No overlap or conflict with the Personal Shrine Continuity concept — Favorite is one of the three input streams the timeline composes from (§11), not a competing concept.
- No change proposed to Favorite's model, API, or entitlement rules (`IsAuthenticated`-only, unchanged).

**Classification: CLEAR**, no conflict.

---

## 8. Visit Boundary

Unchanged from #2485, reconfirmed:

- Responsibility: "the user actually went" — `user`+`shrine`+optional `thread`(→Concierge)+`visited_at`+`status ∈ {added, removed}`.
- No planned/scheduled state exists (still true, unchanged) — out of scope for this audit, same as #2485 §13's deferred "Plan layer."
- Visit remains authoritative for visit date/status/completion; a future timeline composition reads from it, never duplicates or shadows it.
- Visits not originating from Compass (manual, or Concierge-`thread`-linked) remain fully first-class and unaffected.

**Classification: CLEAR**, no conflict.

---

## 9. Reflection Boundary

Unchanged from #2485, reconfirmed:

- Responsibility: "what the user experienced/felt" — `user`+`shrine`+optional `thread`+`answer`/mood fields+`created_at`. No direct FK to `Visit` (links back via `thread` only, same pattern as `Visit`).
- Reflection content must never be used to retroactively rewrite any earlier record (Compass-sourced or otherwise) — reaffirmed as a hard constraint, consistent with #2485 §11.
- Reflection remains meaningful without Compass, and Compass remains usable without Reflection — both reaffirmed, unchanged.

**Classification: CLEAR**, no conflict.

---

## 10. Goshuin Boundary

New to this audit (not covered in #2484/#2485). FACT, `backend/temples/models.py:860-887`:

- Fields: `user` (FK, CASCADE), `shrine` (FK, CASCADE, non-nullable), `title`, `is_public` (default `False`), `likes`, `created_at`, `updated_at`. Related model `GoshuinImage` holds actual image attachments.
- **Distinct character from Favorite/Visit/Reflection:** Goshuin carries `is_public` and `likes` — it is a **partly social/shareable** artifact, not a strictly private record. (FACT; separately, #2485 flagged that `MAX_MY_GOSHUINS_FREE=10` currently ignores Premium status entirely — that finding is unchanged and remains a separate, already-flagged bug outside this audit's scope, not re-litigated here.)
- **Belongs to the same broader personal shrine journey — optionally** (per the task's own framing). INFERENCE: a Goshuin row has the same minimal shape needed for timeline composition (`user`, `shrine`, `created_at`), so it *could* participate in a Personal Shrine Continuity view exactly like Favorite/Visit/Reflection, with no schema change required to make that possible.
- **Must not be merged into a unified "history" model.** Its public/social dimension (`is_public`, `likes`) is a materially different responsibility from Favorite/Visit/Reflection's private-record character, and collapsing them would blur that distinction for no demonstrated benefit — consistent with the task's explicit instruction not to merge domain models merely to build a Compass history feature.

**Classification: CLEAR, with an explicit "optional participant" note** — Goshuin can be included in a future composed timeline read-model without any model change, but its social dimension should stay visible/distinct in any such view rather than flattened into the same private-record shape as Visit/Reflection.

---

## 11. Personal Shrine Continuity Model

**This is not a new database model.** Per the task's framing and this audit's findings (§4–§10), it is a **read-model/composition concept**: a view that queries across `Favorite`, `Visit`, `ShrineReflection`, and optionally `Goshuin`, grouped by timestamp (and, per existing product precedent, most naturally by month — see §12/§16 for why month-grain already matters elsewhere in this product), to present the example timeline shape the task describes:

```
2026-08
- Favorite: Shrine A
- Visit: Shrine B
- Reflection: Shrine B

2026-09
- Visit: Shrine C
- Reflection: Shrine C
```

Checklist, all **FACT** (re-confirmed from §4/§7-10 model inspection):

- Do existing `Favorite` records contain sufficient timestamps? **Yes** — `created_at`.
- Do existing `Visit` records contain sufficient timestamps? **Yes** — `visited_at` (and implicit creation time).
- Do existing `Reflection` records contain sufficient timestamps? **Yes** — `created_at`.
- Can `Goshuin` records optionally participate? **Yes**, structurally (§10), with the public/social caveat noted.
- Are existing user relationships sufficient? **Yes** — every model FKs directly to `user`; no cross-model join key is missing for a per-user composition.
- Could a read-model/composition layer create the timeline without a new canonical history table? **Yes — this is the central finding of this audit.**
- Does Compass need to own any of this data? **No.** Compass is the *entry surface* that may lead a user toward these actions; it owns none of the records the timeline is built from.

**Classification: this concept is structurally READY to compose (no schema blocker), but product/usage-validation status is separate — see §13, §22.**

---

## 12. Compass History vs Personal Continuity Comparison

| Dimension | Model A — Compass History | Model B — Personal Shrine Continuity |
|---|---|---|
| 1. Product meaning | "What Compass told you" — a system-output log | "What you did about your shrine journey" — a user-intent record |
| 2. User value | PRODUCT HYPOTHESIS: weaker — re-reading past system outputs has unclear recurring appeal (the "generic cloud storage" risk #2485 §4 already flagged) | PRODUCT HYPOTHESIS: stronger — mirrors the already-validated pattern that Reflection/Visit are worth returning to because the user put something of themselves into them |
| 3. Premium value | Would require inventing a new premium surface around raw system output | Extends the *already-Active* Premium principle (`premium-experience.md`: depth/continuity of the user's own record, never system-output access) |
| 4. Data duplication | High — would duplicate purpose/direction/shrine data that's either ephemeral-by-design or already captured elsewhere once acted on | None — composes existing rows, adds nothing duplicated |
| 5. Privacy | Higher surface — would newly persist direction/purpose (and risk pressure toward persisting birthdate/origin) tied to identity, for content the user never asked to keep | Lower surface — persists only what the user already explicitly chose to save (Favorite/Visit/Reflection), unchanged from today |
| 6. Storage complexity | New table, new migration, new retention/ownership policy | Zero new storage; a query/read-model layer only |
| 7. Explainability | Requires explaining to users why a system output was kept without being asked | Self-evident — "here's what you saved/did," matches user's own mental model |
| 8. Existing architecture fit | Would require Compass to gain a persistence responsibility it has never had (FACT, §2) | Fits the existing pattern exactly — `Visit`/`Reflection` already reference `ConciergeThread` this same way for Concierge; Compass would simply not need an equivalent, since it doesn't need to co-own anything |
| 9. MONTH model | Compatible either way (both can group by month) | Compatible; month-grouping falls out naturally from existing timestamps, no dependency on Compass's own MONTH runtime grain |
| 10. Long-term extensibility | Locks in an assumption (raw output worth keeping) that may not survive first contact with real usage | Extensible without commitment — provenance (§6), Plan-layer (#2485 §13), and Compare-layer (#2485 §14) can all be layered on later without having built a Compass History table first |

**Verdict: PERSONAL SHRINE CONTINUITY PREFERRED.**

Not HYBRID: the task instructs against choosing hybrid merely to preserve both ideas, and no dimension above favors Model A strongly enough to justify carrying its cost (new table, new privacy surface, weaker user-value hypothesis) alongside Model B. The one thing Model A could theoretically provide that Model B cannot — a literal replay of a past Compass screen — was explicitly confirmed in §4 as **not required** for MVP or for any currently-identified product need.

---

## 13. Free / Premium Boundary

Re-audited against the proposed boundary in the task, cross-checked with #2484's already-established, unchanged conclusions:

**Free/Anonymous** — confirmed unchanged and correct: use Compass, see monthly direction, choose purpose, receive shrine recommendations, open Shrine Detail, identical Recommendation quality. All re-confirmed FACT (§2).

**Registered User** — this audit invents no new entitlement rule, per the task's instruction. Existing account-linked durable actions (Favorite/Visit/Reflection, all already `IsAuthenticated`) continue exactly as they work today.

**Premium** — re-evaluated with this audit's sharper framing:

- Premium value does not depend on hiding Compass results — **confirmed**, unaffected, no change proposed.
- Premium value does not depend on better Recommendation quality — **confirmed**, unaffected.
- Premium value does not depend on storing every Compass execution — **confirmed, and now more strongly true than in #2485**, since §11–§12 show the entire Personal Shrine Continuity concept works without storing *any* Compass execution, not just without storing "every" one.
- Personal continuity is a plausible Premium layer — **confirmed as plausible (PRODUCT HYPOTHESIS)**, reaffirming #2485's conclusion, now grounded in a concretely composable data model rather than an abstract future schema.
- Current pricing/entitlement code does not need modification in this audit — **confirmed**, no code touched, no entitlement logic proposed.

**Classification: no conflict; Free Compass Access READY, Premium Continuity NEEDS VALIDATION** (§22, consistent with #2484/#2485).

---

## 14. Cancellation / Re-subscription Considerations

Not re-litigated in depth (already addressed in #2485 §8); revisited only for consistency with this audit's tighter model, where Personal Shrine Continuity has **even less** cancellation complexity than #2485 anticipated, because there is no separate "Continuity data" to manage — the underlying records (Favorite/Visit/Reflection) were never Premium-exclusive to begin with.

| Item | Classification |
|---|---|
| Existing `Favorite`/`Visit`/`Reflection` records remain retained regardless of Premium status | **Existing Contract** — FACT, `visit-reflection-flow.md`'s "保存そのものをPremium限定にはしない," reconfirmed unaffected; these are Free-tier-owned records already, Premium continuity would only ever be a *view* over them |
| Cancellation does not delete personal records | **Existing Contract** (as code behavior) — FACT, §2, cancellation only flips `subscription_status`; nothing deletes `Favorite`/`Visit`/`Reflection`/`Goshuin` today, and no new deletion is proposed |
| Premium continuity/analysis UI may become unavailable on cancellation | **Recommended**, not yet an existing contract — consistent with #2485's recommendation, unresolved as formal policy |
| Re-subscription may restore Premium continuity access | **Recommended**, natural consequence of the above, not yet formal policy |

**No change from #2485's classification here.** Still flagged **PRODUCT DECISION REQUIRED** overall (§22) — this audit does not finalize it, per its own scope constraints.

---

## 15. Analytics Metric Classification

Per the task's required split into engagement / retention / conversion, refining #2485 §15-17:

**Usage / Engagement metrics** (diagnostic, not primary retention signal):
- Compass Start
- Compass Result (success/zero-candidates/direction-unavailable/backend-error, kept distinct per #2485 §16)
- Compass → Shrine Detail
- Compass → Favorite
- Compass → Visit
- Visit → Reflection

**Retention metrics** (see §16 for the primary-hypothesis argument):
- Same-month Compass Repeat Usage — **engagement signal, not primary retention** (§16)
- Next-month Compass Return
- Month-over-Month Compass Return — **candidate primary retention hypothesis** (§16)

**Conversion metrics** (unchanged from #2485 §15-16):
- Upgrade CTA exposure, checkout start, conversion rate by originating surface.

**Analytics vs Personal History separation** — reaffirmed unchanged from #2485 §15: Analytics remains aggregate/anonymous product measurement; Personal Shrine Continuity remains account-owned, user-facing, never an analytics source. This audit's §6 provenance conclusion (prefer Analytics-event tagging over a durable DB field) makes this separation *more* load-bearing than before, not less — the provenance signal itself is explicitly recommended to live on the Analytics side of this boundary.

**Classification: CLEAR**, consistent with #2485.

---

## 16. Month-over-Month Return Hypothesis

The task asks whether `Month-over-Month Compass Return` is a better primary retention hypothesis than same-month repeat usage.

**PRODUCT HYPOTHESIS, and this audit's answer: yes.**

Reasoning (INFERENCE, combining several already-established facts):
- Compass's own product grain is MONTH, not day or session (`premium-visit-compass-time-model-contract.md`, Active, unchanged) — a retention metric should match the grain of the thing being retained-in.
- #2485 §8's own findings already characterized same-month purpose/origin changes as **intentional exploration behavior the product was built to encourage**, not overuse — i.e., same-month repeat is closer to a *usability/engagement* signal ("did the user find the exploration controls useful") than a *retention* signal ("does the product keep bringing the user back over time").
- A user who explores heavily within one month but never returns the following month has demonstrated engagement, not retention — conflating the two risks reading a high same-month-repeat rate as false evidence that Premium Continuity would retain subscribers, when it may only prove the free exploration UI works.

**This audit does not delete same-month repeat from consideration** — per the task's explicit instruction, it remains diagnostically useful (e.g., to validate Hypothesis A from #2485, or to debug whether the purpose/origin controls are discoverable at all). It is reclassified from "candidate primary retention metric" to **engagement metric**, with **Month-over-Month Compass Return promoted to primary retention hypothesis**, and **Next-month Compass Return** retained as its simplest first measurable form (a single-step version of the same underlying signal, already listed as Hypothesis D in #2485 §17).

---

## 17. Premium Validation Funnel

Defined, not implemented, per the task's instruction. Extends #2485 §17's hypotheses A–E with the reconciled funnel shape:

```
Compass → Shrine Detail → Favorite / Visit → Reflection → Next-month Compass Return
```

**Premium hypothesis under test (not validated by this audit):** personal shrine experiences accumulate → the user wants cross-month continuity → a Premium continuity surface has value.

**Evidence needed before implementing a new Premium continuity schema or UI** (PRODUCT HYPOTHESIS, this audit's recommendation, consistent with and slightly sharpened from #2485 §21):
1. Real signal on the *engagement* steps (Compass→Shrine Detail, Compass→Favorite/Visit) — measurable today with ordinary event analytics, no new persistence (§6, §15).
2. Real signal on Month-over-Month Compass Return specifically (§16) — the actual retention signal to watch, not same-month repeat.
3. Given (1) and (2) look healthy, only then is there a basis to prototype a Personal Shrine Continuity *view* (composed, per §11, from already-existing data — this step still requires no new schema) and observe whether users engage with it.
4. Only after (3) shows engagement with the composed view itself would there be evidence to consider any *new* schema work (e.g., durable provenance, per §6) — and even then, the smallest addition first, not a full history table.

**This hypothesis is explicitly not treated as validated by this audit.**

---

## 18. DB / Persistence Impact

- No new DB table proposed or required (§4, §11, §12).
- No migration created in this branch (verified — docs-only diff, §19/§21).
- No modification to `Favorite`, `Visit`, `ShrineReflection`, or `Goshuin` schemas proposed.
- The only persistence-adjacent open question (§6, provenance) is explicitly recommended to start as an **Analytics event property**, not a schema change, until a concrete UX requirement demonstrates otherwise.

**Net persistence impact of adopting this audit's conclusions: zero**, which is itself evidence supporting the primary goal — the principle under test can be adopted without any implementation debt being incurred first.

---

## 19. Contract Conflicts

**None found.** Specifically checked and cleared:

- vs. `compass-product-contract.md` / `compass-mvp-runtime-contract.md`: both already defer persistence decisions; this audit's "no persistence needed" conclusion is consistent with, not contrary to, their deferral.
- vs. `premium-experience.md`: unaffected; this audit's Premium framing (accumulated shrine journey, not stored Compass output) is a direct application of that document's existing depth/continuity principle, not a new one.
- vs. `#2484`: no conflict (§3.1) — #2484 made no commitment this audit contradicts.
- vs. `#2485`: one refinement, not a conflict, fully reconciled in §3.2 — #2485's *framing* conclusion is retained; its *implied mechanism* (a new persisted record) is superseded by a lower-cost composition approach that achieves the same product goal.
- vs. `docs/analytics/direction-events.md`: unaffected; this audit's Analytics recommendations (§6, §15) extend its existing prohibited-attribute pattern rather than deviating from it.
- vs. Architecture Constraints listed in the task (Concierge, Ranking, Evidence Gate, Shrine Knowledge, Compass Product Promise): all confirmed untouched — this audit proposes no change to any of them.

---

## 20. Open Product Decisions

1. Whether/when to add a lightweight Compass-provenance signal (Analytics-event-first, per §6), and if ever promoted to durable data, what shape it takes.
2. Whether a future Personal Shrine Continuity *view* should include `Goshuin` by default or as an opt-in, given its public/social dimension (§10).
3. Cancellation policy formalization — "retain records, hide continuity UI" remains **Recommended**, not yet **Existing Contract** (§14, carried from #2485).
4. Numeric thresholds for "sufficient signal" on Month-over-Month Return before prototyping a composed timeline view (§17, step 2→3) — not set by this audit.
5. Whether/how to eventually let users optionally save birthdate to `UserProfile` for Compass prefill convenience — explicitly out of scope, unrelated to Personal Shrine Continuity itself (§4).
6. Account-deletion interaction (distinct from Premium cancellation) — still outside this audit's evidence base, carried forward unresolved from #2485 §8.

---

## 21. Recommended Next Phase

Unchanged in spirit from #2485 §21, sharpened by this audit's zero-persistence finding:

1. Instrument the cheaply-measurable engagement steps (Compass→Shrine Detail, Compass→Favorite, Compass→Visit) using ordinary event analytics — no schema change required (§15, §18).
2. Track Month-over-Month Compass Return, not same-month repeat, as the primary retention signal to watch (§16).
3. If and only if engagement + month-over-month return show real signal, prototype a Personal Shrine Continuity **read-model/view** composed from existing `Favorite`/`Visit`/`Reflection` (and optionally `Goshuin`) data — this step still requires no new table (§11), making it a comparatively low-cost validation step even at this later stage.
4. Only after users demonstrably engage with that composed view should any new schema (provenance, or anything beyond composition) be considered, and only the smallest version first.

This sequencing means the product can move meaningfully closer to validating Premium Personal Continuity **without** ever having built a Compass History table — directly fulfilling this audit's primary goal.

---

## 22. Final Classification

```
Compass Runtime Persistence:   NOT REQUIRED
Personal Shrine Continuity:    NEEDS VALIDATION
Compass History:               NOT RECOMMENDED
Free Compass Access:           READY
Premium Continuity:            NEEDS VALIDATION
Analytics Readiness:           PARTIAL
```

**Overall: C — NEEDS VALIDATION BEFORE CONTRACT.**

Not A: Premium Continuity and the composed-timeline concept both still lack real usage evidence (§17, §21). Not B: the open items (§20) are genuinely evidentiary, not just implementation-detail product decisions — the core "will users want this" question is unanswered, same as #2484 and #2485. Not D: this audit found **zero** architecture conflicts (§19), and in fact found a strictly cheaper path to the same product goal than the prior audit anticipated — the opposite of a conflict.

This is the third audit in this chain (#2484 → #2485 → this document) to land on **C**, and each time for a tightening reason: #2484 found no conflict but no evidence; #2485 found no conflict but no connective plumbing; this audit finds no conflict, and — critically — confirms **no plumbing is even needed** to validate the core hypothesis. The remaining gap is evidence alone, not architecture, not contract, and no longer even schema design.
