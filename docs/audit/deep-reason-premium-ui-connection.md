# Deep Reason → Premium UI Connection & Visual Experience Audit

Branch: `audit/deep-reason-premium-ui-connection`
Scope: **audit + design specification only.** No production behaviour, generation, ranking,
entitlement, analytics, or routing changes. No broad UI redesign.
Baseline: `origin/develop` @ `53e07496` (feat: add Deep Recommendation Reason v1 (#2655)).

---

## 1. Executive Summary

### 1.1 Connection

The **Deep Recommendation Reason v1 pipeline (PR-A → PR-D) is fully disconnected from
production.** It is implemented, unit-tested, and typechecked, but nothing in the
production render tree consumes it:

| Module | Purpose | Production consumers |
|---|---|---|
| `premiumMeaningContext.ts` (PR-A) | `PremiumMeaningContext` contract + `computePremiumMeaningValidity` | none |
| `mapConciergeResponseToPremiumMeaningContext.ts` (PR-B) | API → `PremiumMeaningContext` | none |
| backend `consultation_meaning` field (PR-C) | stable situation / desired-outcome / constraint signals | only PR-B (which itself has none) |
| `buildDeepRecommendationReason.ts` (PR-D) | Deep Recommendation Reason `lines` + `sources` | none — only its own test file |

What Premium users **actually** see today as "deep" meaning on Shrine Detail comes from
two *older* heuristic paths:

* `buildRecommendationReasonViewModel` → `buildMeaningNarrative` / `buildStateNarrative`
  (need-tag → hardcoded template slots), and
* `buildDeepReason.ts` (a `NarrativeFallback` builder, unrelated to `buildDeepRecommendationReason`)
* plus backend `recommendation_reason_v4_detail` when present.

So "Deep Recommendation Reason v1 exists" is true; "Deep Recommendation Reason v1 is
connected" is false.

Two further connection defects:

* **`recommendation_meta` ("Recommendation Evidence" / rank reason) renders nowhere.**
  It is generated (`buildRecommendationMeta`), passed into `ShrineDetailArticle`, and
  fires a `card_view` analytics event — but no JSX renders `rankTitle` / `rankBody`.
  `RecommendationMetaSection.tsx` exists and is imported by nothing.
* **Name collision.** `buildConsultationMeaningSlots` / `ConsultationMeaningSlots`
  (production, heuristic, need-tag driven) vs the `consultation_meaning` API field /
  `PremiumMeaningConsultationContext` (disconnected, real signal extraction). Same words,
  unrelated data. High risk for the next implementer.

### 1.2 Premium / Free contract

`cardVisibility.ts` is internally consistent and matches the fixed boundary
(Consultation Summary FREE-full for all; Basic Reason + Evidence FREE; Deep Reason /
Personal Meaning / Action Meaning PREMIUM with Guest = Free teaser). **No body-content
leak was found** in the current renderers (post-#2654 `shrine_meaning` teaser fix).
The contract is fine. The *presentation* of the teaser is the problem (§6).

### 1.3 Visual experience

Both the Concierge Result and Shrine Detail screens have converged on **one repeated
surface**: `rounded + border + bg-background-subtle + shadow-medium + p-4`, stacked in a
`space-y-4` column, each block prefixed by an 11px letter-spaced uppercase gray caption.
The Concierge Result renders up to **five** of these in a row (runtime match, trust,
history, shrine meaning, action meaning), then a sixth near-identical surface for the
consultation summary. There is
no heading scale, no elevated tier for Primary content, and Premium is expressed as a
loud amber box repeated up to four times across the two screens. For Guest / Free the
two deep-meaning surfaces are full-chrome cards containing a single "Premiumで読めます"
sentence.

The task's preferred direction — **less card stacking, stronger reading flow** — is
**endorsed by this audit**. See §9 for three concrete directions and §10 for the PR split.

---

## 2. Connection Matrix

Legend: ✅ present & wired · ⚠️ present but partial/indirect · ❌ absent/disconnected

| Meaning | Generated | API | Mapped (FE) | Context | Visibility | Rendered | Actual UI |
|---|---|---|---|---|---|---|---|
| **context_reason** (Basic Reason) | ✅ `buildReasonSection` / `buildRecommendationReasonViewModel` (`buildShrineDetailModel.ts`) | ⚠️ `reason` / `reason_facts` / `explanation` on `ConciergeRecommendation` (`api/concierge/types.ts`) | ✅ `buildRecommendationReasonDetail` (`shrines/[id]/page.tsx:118`) | n/a (no `PremiumMeaningContext`) | ✅ `getVisibilityForCard("context_reason")` = `visible/visible/visible` (`ShrineDetailArticle.tsx:455`) | ✅ `buildContextReasonSections` → `ShrineDetailSections` → `ShrineReasonSection` (`ShrineDetailArticle.tsx:675`) | ✅ Shrine Detail only. In practice `freeDisplaySections` rarely contains a `reason` kind (they live in `premiumDisplaySections`), so the visible "basic reason" on Shrine Detail is often just `supplementSection`. Concierge Result has no `context_reason` card — the basic reason there is the always-on Hero `conclusionLines` (`buildHeroConclusionLines`). |
| **recommendation_meta** (Recommendation Evidence / rank) | ✅ `buildRecommendationMeta` (`buildShrineDetailModel.ts:233`) | ✅ `rank_explanation`, `rank_comparison` (`api/concierge/types.ts:233`) | ✅ spread via `{...model}` (`shrines/[id]/page.tsx:518`) | n/a | ⚠️ `getVisibilityForCard("recommendation_meta")` = `visible/visible/visible` (`ShrineDetailArticle.tsx:462`) | ❌ **no JSX** — only a `card_view` analytics event (`ShrineDetailArticle.tsx:586-600`). `RecommendationMetaSection.tsx` exists, imported nowhere. | ❌ **Not shown to any user.** Analytics fires for a card that has no surface. |
| **shrine_meaning** (Deep Recommendation Reason surface) | ✅ **heuristic** `buildMeaningNarrative` (`meaningCore` / `shrineMeaning`) via `buildRecommendationReasonViewModel:512` | ⚠️ derived from `reason_facts` + `need`; also `recommendation_reason_v4_detail` (`api/concierge/types.ts:156`) | ✅ Concierge: `buildRecommendationReasonViewModel` called inline (`ConciergeSectionsRenderer.tsx:864`). Detail: `recommendationReasonDetail.shrineMeaning` (`shrines/[id]/page.tsx:172`) | ❌ **not** from `PremiumMeaningContext` | ✅ `getVisibilityForCard("shrine_meaning")` = `teaser/teaser/visible` (`ConciergeSectionsRenderer.tsx:328`) | ✅ Concierge: `conciergeSoftCardClass` section (`ConciergeSectionsRenderer.tsx:1065`). Detail: premium `meaning` section → `ShrineJudgeSection` (`ShrineDetailArticle.tsx:677`) | ✅ shown. Premium: full heuristic text. Guest/Free: one-line teaser card. |
| **personal_meaning** (Personal Meaning) | ✅ **heuristic / payloadV2 / reasonV4** — `buildPremiumDisplaySections` + `buildMeaningSectionsFromPayloadV2` + `reasonV4` (`buildShrineDetailModel.ts:1125`, `:1611`) | ⚠️ `shrineMeaningPayloadV2` (`api/shrineMeaning.ts`), `recommendation_reason_v4_detail` | ✅ `premiumDisplaySections` on model, spread to `ShrineDetailArticle` | ❌ not from `PremiumMeaningContext` | ✅ `getVisibilityForCard("personal_meaning")` = `teaser/teaser/visible` (`ShrineDetailArticle.tsx:456`) | ✅ visibility gate for the whole `premiumSections` bundle: `visible` → `ShrineDetailSections`; `teaser` → `PremiumUpgradePrompt` (`ShrineDetailArticle.tsx:677-683`) | ✅ Shrine Detail only. Not a distinct data field — it is the gate name for the premium meaning bundle. No Concierge consumer. |
| **action_meaning** (Action Meaning) | ✅ **heuristic** `buildMeaningNarrative` `buildReflectionQuestion` → `actionMeaning`; Detail: `buildActionSection` / reasonV4 `actionText` | ⚠️ derived from `need` + `reason_facts`; `recommendation_reason_v4_detail.action` | ✅ Concierge: `reasonVm.detail.actionMeaning` (`ConciergeSectionsRenderer.tsx:1085`). Detail: `recommendationReasonDetail.actionMeaning` (`shrines/[id]/page.tsx:173`) | ❌ not from `PremiumMeaningContext` | ✅ `getVisibilityForCard("action_meaning")` = `teaser/teaser/visible` (`ConciergeSectionsRenderer.tsx:329`) | ✅ Concierge: `conciergeSoftCardClass` section "今の自分への問い" (`:1076`). Detail: premium `action` section → `ShrineActionSection` | ✅ shown. Premium: full. Guest/Free: one-line teaser. |
| **Deep Recommendation Reason v1** (`buildDeepRecommendationReason`) | ✅ `buildDeepRecommendationReason.ts` (PR-D) | ❌ no dedicated API field; would need `consultation_meaning` + `reason_facts` via `PremiumMeaningContext` | ❌ `mapConciergeResponseToPremiumMeaningContext` has **no production caller** | ❌ `PremiumMeaningContext` built nowhere in prod | ❌ no `CardId`, not in `cardVisibility.ts` | ❌ | ❌ **Never reaches production.** |
| **consultation_summary** (Consultation Summary) | ✅ **heuristic** `buildStateNarrative` → `state.consultationSummary` (need-tag templates) | ⚠️ backend `consultation_meaning` exists but is **not** the source; heuristic uses `reason_facts` + `need` | ✅ Concierge: `reasonVm.detail.consultationSummary` (`ConciergeSectionsRenderer.tsx:1091`). Detail: `recommendationReasonDetail.consultationSummary` | ❌ backend `consultation_meaning` → only `mapConciergeResponseToPremiumMeaningContext` (dead) | ✅ `getVisibilityForCard("consultation_summary")` = `visible/visible/visible` (post-#2654) | ✅ `ConciergeConsultationSummary` (`:1091`); Detail: `ShrineProposalSection` lead | ✅ shown to all. Content is heuristic, **not** the PR-C signal extraction. |

### Supporting / disconnected modules

| Module | State |
|---|---|
| `mapConciergeResponseToPremiumMeaningContext.ts` | ❌ no non-test consumer |
| `premiumMeaningContext.ts` (`PremiumMeaningContext`, `computePremiumMeaningValidity`) | ❌ no non-test consumer |
| backend `consultation_meaning` API field | ⚠️ typed + mapped into the dead `PremiumMeaningContext` only |
| `RecommendationMetaSection.tsx` | ❌ imported nowhere |
| `GoshuinLimitBadge.tsx` (CTA-C candidate on Shrine Detail) | ❌ imported nowhere — dead |
| `buildDeepReason.ts` (`NarrativeFallback`) | ✅ wired (`shrines/[id]/page.tsx:161`) — this is the *old* deep reason, not PR-D |

---

## 3. Current Production Path

### 3.1 Concierge Result (`ConciergeClientFull` → `ConciergeSectionsRenderer`)

Data: `POST /api/concierge-chat` (`ConciergeChatResponse`) → `buildPayloadFromUnified` →
`payload.sections`. Inside the `recommendations` section, for the hero item:

```
buildRecommendationReasonViewModel({ rec, reasonFacts, mode, needTags })   // heuristic
  → buildReasonNarrative      → conclusionLines (Hero)          [always shown]
  → buildStateNarrative       → detail.consultationSummary
  → buildMeaningNarrative     → detail.shrineMeaning / detail.actionMeaning
```

Render order in the `max-w-md` `space-y-4` column:

1. `ConciergeTopRecommendationHero` — name, eyebrow, `conclusionLines`, action, **the one strong CTA** `神社の詳細を見る` (`bg-action-primary`)
2. `DirectionReferenceCard`
3. `runtimeMatchLines` — soft card — "今回の相談との接点"
4. `trustMetadata` — soft card
5. `historyThemeDisplay` — soft card — "この神社をどう捉えるか（KAMI MUSUBIの解釈）" or "この神社が持つ文脈"
6. `shrine_meaning` — soft card — "相談から見た意味（KAMI MUSUBIの解釈）"  ← teaser for Guest/Free
7. `action_meaning` — soft card — "今の自分への問い"                      ← teaser for Guest/Free
8. `ConciergeConsultationSummary` — `bg-surface-default` card — "今回の相談の整理"
9. `ShrineSaveButton` (subtle)
10. `ConciergePremiumEntryCard` — amber card — **CTA-A**
11. `迷った時だけ、ほかの神社を見る` toggle → compact cards
12. `save_prompt` button

Then, back in `ConciergeClientFull`:

13. `PremiumStateDeltaCard` — amber card — **CTA-B** — *only when `previous_comparison !== "hidden"`, i.e. Premium only*
14. `isUiPaywall` box — bordered — **CTA-C** (quota) — when free limit reached

### 3.2 Shrine Detail (`shrines/[id]/page.tsx` → `ShrineDetailArticle`)

Data: `GET /api/shrines/{id}` + (from `tid`) selected `ConciergeRecommendation` →
`buildShrineDetailModel` (+ `buildRecommendationReasonDetail` → `reasonVm.detail`,
`buildDeepReason` fallback). `{...model}` spread into `ShrineDetailArticle`.

Render order in the `<article>` `space-y-4`:

1. `ShrineDetailHeroHeader` — bordered/shadow — title, "この神社の意味", copy
2. `ShrineDetailHeroCard` — image
3. `directionSupportCopy` — bordered (optional)
4. `ShrineDetailStateDeltaSection` — bordered; amber **CTA-B** branch when not Premium (only after `actionState` visited/reflected)
5. after-visit copy — bordered emerald (optional)
6. `ShrineDetailSections(contextReasonSections)` — **context_reason** (`ShrineReasonSection` / `ShrineProposalSection` / `ShrineSupplementSection`, each bordered)
7. `personalMeaningVisibility === "visible"` → `ShrineDetailSections(premiumSections)` — **personal_meaning / shrine_meaning / action_meaning** (`ShrineJudgeSection`, `ShrineActionSection` — `ShrineActionSection` item uses `bg-premium-surface` + `border-premium-border` + shadow)
8. `personalMeaningVisibility === "teaser"` → `PremiumUpgradePrompt` — amber card — **CTA-A**
9. `factSection` → `ShrineFactSection` — bordered
10. `ShrineDeepDivePrompt` — bordered
11. save/visit/reflection block — bordered emerald with a **nested** bordered inner block + nested `ShrineReflectionPrompt` (bordered emerald)
12. goshuin section
13. fallback benefit `DetailDisclosureBlock`

`recommendation_meta` — no entry in this list (see §4).

---

## 4. Disconnected / Partial Paths

| # | Path | Evidence | Severity |
|---|---|---|---|
| D1 | Deep Recommendation Reason v1 → UI | `grep buildDeepRecommendationReason` → only `__tests__/buildDeepRecommendationReason.test.ts` | P1 |
| D2 | `PremiumMeaningContext` / PR-B mapper → anything | `grep mapConciergeResponseToPremiumMeaningContext` / `computePremiumMeaningValidity` → no non-test caller | P1 |
| D3 | backend `consultation_meaning` (PR-C) → UI | consumed only by D2 (dead). Production `consultation_summary` string is `buildStateNarrative` heuristic, need-tag driven (`buildConsultationMeaningSlots:279`) | P1 |
| D4 | `recommendation_meta` render | `ShrineDetailArticle.tsx` references `recommendationMeta` only in the analytics `useEffect` (`:586-600`, deps `:635-637`); no JSX. `RecommendationMetaSection` imported nowhere | P1 |
| D5 | `recommendation_meta` analytics without UI | a `card_view` for `recommendation_meta` is emitted whenever `rankTitle && rankBody`, describing a surface the user cannot see — pollutes CTR/exposure analysis | P1 |
| D6 | Name collision `consultation_meaning*` | `ConsultationMeaningSlots` (heuristic, `buildRecommendationReasonViewModel.ts:109`) vs `ConsultationMeaning` API type (`api/concierge/types.ts:64`) vs `PremiumMeaningConsultationContext` | P2 |
| D7 | `GoshuinLimitBadge` (CTA-C on Detail) | imported nowhere | P2 (dead code; **do not fix here** — record) |

---

## 5. UI Hierarchy Findings

### 5.1 Concierge Result @ 375px

| Level | Should contain | Currently rendered as |
|---|---|---|
| **Primary** | recommended shrine, the recommendation itself, why this shrine, link to detail | `ConciergeTopRecommendationHero` — the *only* block with distinct treatment (first position + one filled CTA). `conclusionLines` (why this shrine) live inside it. |
| **Secondary** | shrine meaning, action meaning, consultation context | blocks 6–8 (`shrine_meaning`, `action_meaning`, `ConciergeConsultationSummary`) — **same** border / bg / shadow / padding / caption style as Tertiary |
| **Tertiary** | runtime-match detail, trust metadata, history framing, "other shrines" | blocks 3–5 + toggle — **same** treatment as Secondary |

**Hierarchy is visually flat from block 3 downward.** Primary is distinguishable;
Secondary and Tertiary are not distinguishable from each other. Consultation context
(block 8, FREE, arguably Secondary-high) sits *after* the two Premium teasers (blocks
6–7), so the free reading order is: why-this-shrine → runtime match → trust → history →
*[locked]* → *[locked]* → your-consultation-context. The intended order is
Recommendation → Why this shrine → Why it matters to you → What to keep in mind →
Evidence.

### 5.2 Shrine Detail @ 375px

| Level | Should contain | Currently rendered as |
|---|---|---|
| **Primary** | shrine name + one-line meaning, hero image, basic reason | `ShrineDetailHeroHeader` (bordered/shadow) + `ShrineDetailHeroCard` — reasonable, but the header is a *card*, not a page-level title |
| **Secondary** | premium meaning bundle (deep reason / personal / action), or its teaser | block 7/8 — `ShrineJudgeSection` (`<details>`), `ShrineActionSection` (amber), or `PremiumUpgradePrompt` (amber) |
| **Tertiary** | shrine facts, deep-dive prompt, rank evidence, save/visit/reflection, goshuin | blocks 9–13 — each a sibling bordered surface; the save block nests borders 3 deep |

**`recommendation_meta` ("なぜ1位か / 1位との違い") — the item the fixed boundary calls
"Recommendation Evidence" and puts in FREE — is not in the hierarchy at all** because it
is not rendered (§4 D4).

### 5.3 Where hierarchy is unclear

* Concierge blocks 3–8: no size, weight, colour, or spacing signal separates
  "supporting fact" from "core meaning".
* Both screens: section identity is a repeated 11px uppercase gray caption, not a
  heading. There is no `h2`/`h3` scale.
* Premium teaser (amber box) is visually *heavier* than the Secondary meaning content it
  gates — the upsell out-shouts the product.

---

## 6. Visual Findings by Severity

Category tags: **Hierarchy · Density · Typography · Surface · Premium · CTA · Mobile · Duplication**

### P1 — High

| # | Category | Finding | Evidence |
|---|---|---|---|
| V1 | Hierarchy / Density | Concierge Result renders **up to 5 consecutive visually-identical** `conciergeSoftCardClass` surfaces (`rounded border bg-background-subtle shadow-medium p-4`, same 11px caption) — runtime match, trust, history, shrine meaning, action meaning — immediately followed by a 6th near-identical surface (`ConciergeConsultationSummary`, `bg-surface-default` + shadow). No Primary/Secondary/Tertiary differentiation. | `ConciergeSectionsRenderer.tsx:53` (class), blocks at `:1003`, `:1029`, `:1051`, `:1065`, `:1076`; `ConciergeConsultationSummary.tsx:15` at `:1091` |
| V2 | Hierarchy | Reading order: `consultation_summary` (FREE context) renders **after** `shrine_meaning` + `action_meaning` (PREMIUM teasers). | `ConciergeSectionsRenderer.tsx:1065` → `:1076` → `:1091` |
| V3 | Density / Premium | Guest/Free: `shrine_meaning` and `action_meaning` each render a **full bordered card whose entire content is one "Premiumで読めます" sentence** + a caption. Two high-chrome near-empty cards back to back. | `ConciergeSectionsRenderer.tsx:1073-1078`, `:1082-1087` |
| V4 | Typography | **No heading scale.** Section identity is carried only by `text-xs font-semibold tracking-[0.12em] text-[--kt-color-text-muted]`; body is uniformly `text-sm leading-7 text-secondary`. Primary, Secondary, Tertiary use the same type. | `ConciergeSectionsRenderer.tsx:1054`, `:1068`, `:1079`; `ShrineReasonSection.tsx`, `ShrineJudgeSection.tsx` |
| V5 | Surface | Only two surfaces in active use on the result screen (`bg-background-subtle`, `bg-surface-default`), applied without a Primary/elevated tier. `shadow-medium` is applied uniformly, so elevation conveys nothing. | `ConciergeSectionsRenderer.tsx:53-60` |
| V6 | Premium | Premium is expressed as an **amber border + amber fill + "Premium" wording**, repeated in `ConciergePremiumEntryCard`, `PremiumUpgradePrompt`, `ShrineDetailStateDeltaSection` (non-premium branch), `PremiumStateDeltaCard` (non-premium branch) — up to **4 amber upsell boxes across the 2 screens**, same treatment for CTA-A and CTA-B. | `ConciergeSectionsRenderer.tsx:59` `conciergePremiumCardClass`; `ShrineDetailArticle.tsx:189`, `:302`; `PremiumStateDeltaCard.tsx:59` |
| V7 | CTA | CTA-A and CTA-B are visually interchangeable (amber box + `bg-premium-accent` button + `/billing/upgrade`), diluting each responsibility. They do not co-occur in one Concierge viewport (CTA-B is Premium-gated there) but read as "the same box" across screens. | as V6 |
| V8 | Duplication (presentation) | `shrine_meaning` ("相談から見た意味（KAMI MUSUBIの解釈）") and `historyThemeDisplay` ("この神社をどう捉えるか（KAMI MUSUBIの解釈）") are adjacent and both framed as "KAMI MUSUBI's interpretation of this shrine". | `ConciergeSectionsRenderer.tsx:1051-1063` vs `:1065-1074` |

### P2 — Medium

| # | Category | Finding | Evidence |
|---|---|---|---|
| V9 | CTA / Density | Logged-in free user at quota: `ConciergePremiumEntryCard` (CTA-A) + `save_prompt` button + `isUiPaywall` box (CTA-C) can stack consecutively — 3 conversion prompts, no single primary. | `ConciergeSectionsRenderer.tsx:1108`, `:1257`; `ConciergeClientFull.tsx:1960` |
| V10 | Typography | Every meaning/fact block repeats an 11px letter-spaced uppercase gray caption; repeated micro-labels stand in for a real heading hierarchy. | `ConciergeSectionsRenderer.tsx` captions passim |
| V11 | Typography | `ConciergeConsultationSummary` renders a full paragraph in `text-base font-semibold leading-8`; meaning cards use `text-sm ... leading-7`. Equivalent-priority content, inconsistent type; bold-as-emphasis on body copy. | `ConciergeConsultationSummary.tsx:35` |
| V12 | Duplication (presentation) | `runtimeMatchLines` ("今回の相談との接点") and `shrine_meaning` ("相談から見た意味") both answer "how this shrine connects to your consultation"; for Free the second is only a teaser, so the screen poses the question twice and answers it once. | `ConciergeSectionsRenderer.tsx:1003` vs `:1065` |
| V13 | Duplication (mapping) | Detail: `recommendationReasonDetail.consultationSummary` → falls back to `conciergeDeepReason.interpretation`; `shrineMeaning` → `conciergeDeepReason.shrineMeaning`. Same fallback source can surface in `ShrineProposalSection` lead **and** `ShrineJudgeSection`. | `shrines/[id]/page.tsx:169-174`; `buildShrineDetailModel.ts:592-613` |
| V14 | Duplication (presentation) | Guest/Free teaser strings for `shrine_meaning` and `action_meaning` are both "…は、Premiumで読めます。" — two sections whose only content is the same sentence pattern. | `ConciergeSectionsRenderer.tsx:1075`, `:1084` |
| V15 | Surface | Borders do all separation work; reducing `p-4`+border+`shadow-medium` on every block in favour of spacing + one surface step would remove most of the visual noise without new tokens. | both screens |
| V16 | Mobile (static) | `PremiumUpgradePrompt` / `ConciergePremiumEntryCard` CTA `<a>` is `inline-flex px-3 py-2 text-xs` ≈ 30–34px tall — under the 44px tap-target guideline. | `ShrineDetailArticle.tsx:197`; `ConciergeSectionsRenderer.tsx:135` |
| V17 | Mobile (static) | `ConciergeConsultationSummary` header is a 3-pill `flex-wrap` row (`今回の相談の整理` + modeLabel + appliedLabel); a long `appliedLabel` wraps to 2 rows at 375px and pushes the summary down. | `ConciergeConsultationSummary.tsx:17-33` |
| V18 | Mobile (static) | Fallback escape-hatch is a `grid-cols-2` of buttons with `px-4 py-3 text-sm` JP labels ("近くの神社を静かに見る" / "条件を広げて見直す"); at 375px each column ≈ 155px → labels wrap to 2 lines, uneven heights. | `ConciergeSectionsRenderer.tsx:814-840` |
| V19 | Surface / Premium | Teaser is *truncation to zero*, not a faded continuation of visible content. Nothing communicates "there is a deeper layer here" except an ad box. | `ConciergeSectionsRenderer.tsx:1075`; `ShrineDetailArticle.tsx:681` |

### P3 — Polish

| # | Category | Finding |
|---|---|---|
| V20 | Density | Vertical scroll inflated by `p-4` on every card + `space-y-4` gaps + per-card shadow; the meaning region is ~6 card-heights for ~4 short paragraphs of content. |
| V21 | CTA | `isUiPaywall` box and `ConciergePremiumEntryCard` both link `/billing/upgrade` with different copy and different visual style. |
| V22 | Typography | `ShrineDetailHeroHeader` "この神社の意味" caption + hero meaning copy is the closest thing to a page title but is wrapped in a shadowed card, not presented as an `h1`. |
| V23 | Premium | `ShrineActionSection` item uses `bg-premium-surface` + `border-premium-border` + `shadow-medium` per **item**, so a 2-item premium action list is two gold sub-cards inside a section. |

---

## 7. Duplication Findings

| Pair | Type | Verdict |
|---|---|---|
| `context_reason` vs `shrine_meaning` | presentation | Not semantically duplicate (basic "why chosen" vs interpretive "meaning"), but on Shrine Detail `context_reason`'s visible content is often only `supplementSection`, so the distinction is invisible to the user. **Presentation** — candidate for §10 PR. |
| `shrine_meaning` vs `personal_meaning` | mapping / presentation | On Detail these are the *same* `premiumSections` bundle behind one gate (`personalMeaningVisibility`); `shrine_meaning` and `personal_meaning` are two `CardId`s for one rendered block. Not user-visible duplication, but a **mapping** redundancy that makes analytics ambiguous. |
| `personal_meaning` vs `action_meaning` | presentation | Distinct content (interpretation vs "what to keep in mind"), distinct sections. No duplication. Framing captions are close ("今回の相談との意味" / "参拝するときの視点") — minor. |
| `runtimeMatchLines` vs `shrine_meaning` | **presentation** | Same question ("接点 / 相談から見た") asked in two adjacent surfaces. |
| `historyThemeDisplay` vs `shrine_meaning` | **presentation** | Both "KAMI MUSUBI's reading of this shrine", adjacent, same caption grammar. |
| Detail proposal lead vs judge section | **mapping** | Shared `conciergeDeepReason` fallback can print the same sentence twice. |
| `shrine_meaning` teaser vs `action_meaning` teaser | **presentation** | Identical "…Premiumで読めます。" sentence in two cards. |

**No generation duplication found.** `buildReasonNarrative` / `buildStateNarrative` /
`buildMeaningNarrative` emit distinct strings for distinct slots; every overlap above is
in *framing and placement*, or in *fallback mapping*. → Only presentation items are
candidates for the UI PR. Mapping items (V13, `shrine_meaning`/`personal_meaning` double
CardId) should be reported to Mother Ship as a separate mapping-cleanup task; they are
**not** UI work and not in scope here.

---

## 8. Mobile 375px Findings

Verification method: **static** (Tailwind class analysis against a 375px / `max-w-md`
column). A live device pass requires the app running against a populated backend
(Concierge Result needs a completed consultation) and is deferred to the implementation
PR — see §11.

| # | Check | Result (static) |
|---|---|---|
| M1 | horizontal overflow | No obvious offender; all containers `w-full` inside `max-w-md`. **Confirm live.** |
| M2 | clipped text / CTA labels | Risk: `grid-cols-2` fallback buttons (V18) and 3-pill header (V17) wrap; no truncation classes, so it grows vertically rather than clipping. |
| M3 | tap targets | `text-xs px-3 py-2` CTA links (V16) below 44px. Preset chips `px-3 py-1 text-xs` (`:730`) ≈ 26px — below guideline. |
| M4 | surface padding | Uniform `p-4` — adequate, arguably heavy given the stacking. |
| M5 | section spacing | `space-y-4` everywhere — no larger gap at Primary→Secondary→Tertiary transitions. |
| M6 | teaser dominates viewport | Guest/Free: blocks 6–7 are two ~96px amber-captioned cards for zero content (V3); block 10 CTA-A card is ~150px. Teaser+CTA occupy a large share of the meaning region. |
| M7 | Premium CTA repeated | Concierge: 1× CTA-A (+ paywall box when at quota). Detail: 1× CTA-A, +1× CTA-B after a visit. Across a session, 3–4 amber boxes (V6). |
| M8 | first-viewport intent | Hero (`ConciergeTopRecommendationHero`) carries name + eyebrow + conclusion + CTA — intent is understandable in the first viewport. **OK.** |
| M9 | sticky / bottom nav overlap | `ConciergeLayout` / `ShrineDetailShell` + global `BottomNav` not inspected line-by-line here; the result column ends with `pb-0` (`ConciergeSectionsRenderer.tsx:612`) and `ConciergeClientFull` wraps in `p-4`. **Confirm live** that the final `save_prompt` / paywall box is not hidden behind `BottomNav`. |
| M10 | excessive scroll | Yes (V20). ~6 card-heights of chrome for ~4 paragraphs in the meaning region. |

---

## 9. Recommended UI Directions (max 3 — decision deferred to Mother Ship)

All three keep `cardVisibility.ts`, the design-token system, generation, ranking,
analytics, and routing **unchanged**. They differ only in DOM structure + token
*selection* + copy placement.

### Direction A — Editorial single-flow

**Concept.** The recommendation result is one article, not a card feed. A page-level
title (shrine name + one-line meaning), then labelled sections separated by whitespace
and a hairline, not by boxes. Body carries the content; captions become real headings
(`text-sm font-semibold text-primary`, not 11px uppercase gray). Premium content is an
**inline continuation** of its section that fades into a one-line unlock affordance —
same section, same heading, no separate box.

**Information hierarchy.**
Recommended shrine (title) → Why this shrine (basic reason, always) → Why it matters to
you (deep reason / personal meaning — Premium; fades for Free) → What to keep in mind
(action meaning — Premium; fades for Free) → Your consultation context (summary) →
Evidence & details (trust, history, rank reason, "other shrines") in a lower-emphasis
block or `<details>`.

**Strengths.** Removes V1/V3/V5/V15/V20 outright. Premium reads as "a deeper layer here"
(V19), not an ad. Fixes reading order (V2). One heading system (V4/V10).
**Weaknesses.** Biggest DOM change of the three. Needs a real type scale decision. Fade
teaser needs a token for the mask (can reuse `--kt-color-background` stops — no new
colour). Risks under-selling Premium if the fade is too subtle.
**Implementation impact.** `ConciergeSectionsRenderer` recommendations branch rewritten;
`ShrineDetailArticle` sections 6–10 restructured; `ShrineReason/Judge/Action/Supplement`
lose their outer `border`/`bg`/`shadow`. ~1 PR per screen.
**Mobile.** Shorter page, fewer tap targets, clearer transitions. Fade teaser must be
tested at 375px for legibility of the last visible line.

### Direction B — Two grouped surfaces

**Concept.** Keep surfaces, but collapse the 6-card stack into **two** elevated
surfaces with internal dividers instead of per-item borders:
`この神社について` (runtime match + trust + history) and
`意味` (why this shrine → why it matters to you → what to keep in mind → your context).
Premium content sits inside the `意味` surface with a single unlock row at the bottom of
that surface — one Premium affordance per screen, not per section.

**Information hierarchy.** Primary = Hero (unchanged, still the only filled CTA).
Secondary = the `意味` surface (elevated, `bg-surface-default`, subtle top accent).
Tertiary = the `この神社について` surface (flat, `bg-background-subtle`, collapsible).

**Strengths.** Much smaller change than A; keeps a familiar "card" feel. Directly kills
V1, V3, V6 (one Premium row), V9 (one CTA in the meaning region). Divider-based internal
structure gives hierarchy without a full type overhaul.
**Weaknesses.** Still box-driven; doesn't fully deliver "reading flow". Two large
surfaces can feel monolithic. Needs one elevated-surface token step (already available:
`bg-surface-default` vs `bg-background-subtle`).
**Implementation impact.** `ConciergeSectionsRenderer` groups blocks 3–5 and 6–8 into
two wrappers; teaser rendering moves to one shared unlock row; `ShrineDetailArticle`
groups sections 6–10. Analytics `card_view` calls unchanged (still per `CardId`).
**Mobile.** Fewer borders, fewer shadows, ~2 card-heights saved. Collapsible Tertiary
surface removes blocks 3–5 from the default viewport.

### Direction C — Progressive disclosure hybrid

**Concept.** Primary always open: Hero + basic reason + a **one-line lead** of the deep
meaning. Secondary/Tertiary (full deep reason, action meaning, trust, history, rank
evidence) live behind inline "続きを読む" expanders **within one surface per screen**.
For Guest/Free the expander for gated content is replaced by the unlock affordance
(so the teaser *is* the collapsed state — no empty card).

**Information hierarchy.** Depth = interaction, not scroll. Primary visible; everything
else is one tap away in place.
**Strengths.** Shortest default page; teaser and "collapsed" become the same control
(kills V3, V14, V19). Good for the "feels intentional" goal on first load.
**Weaknesses.** The task explicitly says *don't* reach for accordions before trying
hierarchy+spacing. Hides meaning that is arguably the product. Expander state + analytics
(`card_view` on expand) needs care to not change the analytics contract. Motion-readiness
(Phase F) is fine but the collapsed default may read as "empty" to Premium users too.
**Implementation impact.** New disclosure primitive (or reuse `DetailDisclosureBlock`);
visibility→(open|collapsed|locked) mapping; per-screen wrapper.
**Mobile.** Best first-viewport density; risk of "where did the content go" and of
double-tap fatigue in the meaning region.

**Audit lean (not a decision):** **A** best matches the stated principle and the desired
reading experience; **B** is the lowest-risk first step and could be PR-G1 with A as a
follow-up; **C** only if Mother Ship wants interaction-driven depth. Recommend
**B now, A as the target**, C rejected unless explicitly chosen.

---

## 10. Proposed PR Split

Derived from the findings, one responsibility each. Presentation-only; no generation,
ranking, entitlement, analytics, or routing changes.

| PR | Title | Scope | Fixes | Files (candidate) |
|---|---|---|---|---|
| **PR-G1** | Concierge Result reading-flow restructure | Collapse the 6-card stack (Direction B grouping, or A if chosen); fix section order so consultation context precedes the deep-meaning teasers; introduce one heading level; reduce per-block border/shadow/padding. | V1, V2, V4, V5, V10, V15, V20, V12 | `features/concierge/components/ConciergeSectionsRenderer.tsx`, `ConciergeConsultationSummary.tsx`, `ConciergeTopRecommendationHero.tsx` |
| **PR-G2** | Premium meaning surface & teaser treatment | One Premium affordance per screen; teaser = faded/continuation in-section, not an empty bordered card; unify CTA-A visual language and separate it from CTA-B; de-dupe the two teaser one-liners. | V3, V6, V7, V9, V14, V19, V23 | `ConciergeSectionsRenderer.tsx` (`ConciergePremiumEntryCard`, `shrine_meaning`/`action_meaning` teaser), `components/shrine/detail/ShrineDetailArticle.tsx` (`PremiumUpgradePrompt`), `components/shrine/detail/ShrineActionSection.tsx` |
| **PR-G3** | Shrine Detail meaning layout + `recommendation_meta` render decision | Editorial layout for sections 6–10; flatten the nested-border save/visit/reflection block; **decide**: render `recommendation_meta` (wire `RecommendationMetaSection` into the FREE reason area) **or** delete the component + its analytics event. | V4 (detail), 5.2, D4, D5, V13, V15 (detail) | `components/shrine/detail/ShrineDetailArticle.tsx`, `ShrineDetailSections`, `ShrineReasonSection.tsx`, `ShrineJudgeSection.tsx`, `RecommendationMetaSection.tsx` |
| **PR-G4** *(mobile polish, optional / fold into G1–G3)* | 375px tap targets & wrap fixes | CTA `<a>` min-height 44px; preset chip height; `grid-cols-2` fallback → stacked at ≤390px; `ConciergeConsultationSummary` header wrap. | V16, V17, V18, M2, M3 | as above + `ConciergeSectionsRenderer.tsx` filter/fallback |

### Non-UI items → report to Mother Ship (NOT part of PR-G*)

| Item | Type | Note |
|---|---|---|
| **N1 — Deep Recommendation Reason v1 connection** | product / generation-adjacent | `buildDeepRecommendationReason` + `mapConciergeResponseToPremiumMeaningContext` + backend `consultation_meaning` need a production consumer, or an explicit decision to shelve PR-A→PR-D. Category **B**. Blocks any UI PR that intends to *show* real Deep Reason rather than the current heuristic. |
| **N2 — `consultation_meaning` name collision** | refactor | Rename the heuristic `ConsultationMeaningSlots` / `buildConsultationMeaningSlots` **or** the disconnected `PremiumMeaningConsultationContext` before N1 work starts. |
| **N3 — `shrine_meaning` vs `personal_meaning` double CardId on Detail** | mapping / analytics | One rendered block, two `CardId`s, two `card_view` events. Decide the intended granularity. Analytics-contract-adjacent → Mother Ship. |
| **N4 — dead code** | cleanup | `GoshuinLimitBadge.tsx` and (pending G3 decision) `RecommendationMetaSection.tsx` unused. Record only; do not fix opportunistically. |

---

## 11. Tests / Verification Performed

* **Static / structural only** — this is a docs PR; no code changed, no tests added or run.
* Connection claims verified by `grep` over `apps/web/src` for every builder / type /
  component named in §2 and §4 (import + call-site search, `__tests__` excluded for the
  "production consumer" determination).
* Render-order and surface claims verified by reading the JSX of
  `ConciergeSectionsRenderer.tsx`, `ConciergeClientFull.tsx`, `ShrineDetailArticle.tsx`,
  `ShrineDetailSections`, `Shrine{Reason,Judge,Action,Supplement}Section.tsx`,
  `ConciergeConsultationSummary.tsx`, `PremiumStateDeltaCard.tsx`, `GoshuinLimitBadge.tsx`
  at `origin/develop` `53e07496`.
* `cardVisibility.ts` matrix cross-checked against the fixed boundary and against the
  post-#2654 renderer behaviour.
* **Not performed:** live 375 / 390 / 430px device pass. The Concierge Result screen
  requires a completed consultation against a populated backend; deferred to the
  implementation PR (§8 M1, M9 flagged for live confirmation).
* No audit-enabling (category A) code change was required.

---

## 12. Files Changed

* `docs/audit/deep-reason-premium-ui-connection.md` — this document (new).

No source files changed.

---

## 13. PR URL

_(to be filled after `gh pr create` — see branch `audit/deep-reason-premium-ui-connection`)_

---

## 14. STOP — Mother Ship Decision Required

Decisions requested:

1. **UI direction** — A (editorial single-flow, target), B (two grouped surfaces,
   lowest-risk first step), or C (progressive disclosure). Audit lean: **B now → A
   later; reject C** unless interaction-driven depth is explicitly wanted.
2. **`recommendation_meta`** (PR-G3) — render it into the FREE reason area, or delete
   `RecommendationMetaSection` + its `card_view` event? Today it is generated + tracked
   but invisible.
3. **N1 — Deep Recommendation Reason v1 connection** — schedule a connection PR
   (wire `buildDeepRecommendationReason` via `PremiumMeaningContext`), or formally shelve
   PR-A→PR-D? UI PRs can proceed on the current heuristic meaning text either way, but
   should not claim to surface "Deep Recommendation Reason v1" until this is resolved.
4. **N2 naming / N3 double-CardId** — approve as separate non-UI cleanup tasks before
   N1.
5. **PR-G4** — standalone mobile-polish PR, or fold into G1–G3?

No implementation will start until Mother Ship returns a direction.
