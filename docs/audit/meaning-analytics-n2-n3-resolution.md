# N2 / N3 Resolution Audit — Meaning naming & Shrine Detail analytics granularity

Branch: `audit/meaning-analytics-n2-n3-resolution`
Type: **read-only audit.** No production / behaviour / analytics / test / doc-other-than-this change.
Baseline: `origin/develop` @ `17801e24` (`feat: 神社詳細のMeaning情報階層を再構成 (PR-G3) (#2663)`).
Purpose: turn the unresolved N2 / N3 follow-ups (from `docs/audit/deep-reason-premium-ui-connection.md` §10) into a
fact-based decision packet for Mother Ship. **No implementation. No decision made here.**

Source-of-truth order used: production code → tests → analytics helper/aggregation → API/FE types → latest audit/design docs → older docs.

---

## 1. Scope

- **N2** — audit every `ConsultationMeaning*` / `consultation_meaning` / `PremiumMeaningConsultationContext` symbol: real responsibility, layer, contract linkage, consumers, rename blast radius. Classify N2-A/B/C/D.
- **N3** — audit the Shrine Detail meaning `card_view` analytics: what one "impression" represents today (Model A surface / B semantic-layer / C hybrid), which CardIds fire with/without a rendered surface, downstream consumers, and Policy A/B/C trade-offs.
- **recommendation_meta** — re-confirm the PR-G3 "held" finding and state exactly what it is blocked on (N2 / N3 / D-4 sequencing / nothing).
- Produce the three Mother Ship decision questions.

Out of scope: everything in §15.

---

## 2. Baseline

| | |
|---|---|
| Base / develop SHA | `17801e24` |
| Branch | `audit/meaning-analytics-n2-n3-resolution` — HEAD == `origin/develop` |
| `git diff` / `git diff --cached` | both empty at start |
| Pre-existing untracked (left untouched) | `apps/web/AGENTS.md`, `apps/web/CLAUDE.md` |
| Unexpected tracked diffs | none |

---

## 3. N2 Symbol Inventory

Three distinct concept clusters share "ConsultationMeaning"-shaped names.

### Cluster 1 — API contract type: backend `consultation_meaning` signal (PR-C)

| Symbol | File | Notes |
|---|---|---|
| `consultation_meaning` (JSON field) | backend `temples/api_views_concierge.py:356,687,1053` (from `services/consultation_meaning.py` → `extract_consultation_meaning(query).as_dict()`) | stable top-level field on `ConciergeChatResponse`; backend contract test `test_concierge_chat_consultation_meaning_contract.py` (always present, empty families `[]`, no raw free-text, quota-independent) |
| `ConsultationMeaning` (FE type) | `apps/web/src/lib/api/concierge/types.ts:64` | `{ situation_signals, desired_outcome_signals, explicit_constraint_signals }`, each `Array<{type, evidence: ConsultationMeaningEvidence[]}>`. Mirrors the JSON. Re-exported from the `@/lib/api/concierge` barrel (`concierge.ts:23`). |
| `ConsultationMeaningEvidence` (FE type) | `apps/web/src/lib/api/concierge/types.ts:54` | `{ text: string }`. Re-exported from barrel (`concierge.ts:24`). |
| `situation_signals` / `desired_outcome_signals` / `explicit_constraint_signals` + their `*SignalType` unions | `types.ts:58-71` | the signal taxonomy |

### Cluster 2 — Disconnected Premium-Meaning foundation (PR-A → PR-D)

| Symbol | File | Notes |
|---|---|---|
| `PremiumMeaningConsultationContext` | `apps/web/src/lib/concierge/premiumMeaningContext.ts:73` | camelCase FE shape `{ situationSignals, desiredOutcomeSignals, explicitConstraintSignals }`. Used **only inside `premiumMeaningContext.ts`** (type of `PremiumMeaningContext.consultation`, arg of `isStructuredConsultationContextValid`). |
| `ConsultationMeaningEvidence` (**2nd definition**) | `apps/web/src/lib/concierge/premiumMeaningContext.ts:59` | `{ text: string }` — byte-identical shape to Cluster 1's type, **redefined**, feeds `SituationSignal` / `DesiredOutcomeSignal` / `ExplicitConstraintSignal` in this file. |
| `mapConciergeResponseToPremiumMeaningContext` | `apps/web/src/lib/concierge/mapConciergeResponseToPremiumMeaningContext.ts` | maps Cluster-1 `ConsultationMeaning` → Cluster-2 `PremiumMeaningConsultationContext`. |
| `buildDeepRecommendationReason`, `computePremiumMeaningValidity`, `PremiumMeaningContext` | `buildDeepRecommendationReason.ts`, `premiumMeaningContext.ts` | consume Cluster 2. |

**Production consumers of the entire PR-A→D chain: none** (re-verified: `grep` for `mapConciergeResponseToPremiumMeaningContext` / `buildDeepRecommendationReason` / `computePremiumMeaningValidity` outside their own files + `__tests__` → empty). This is the same "fully disconnected" finding as audit #2656; unchanged.

### Cluster 3 — Heuristic need-tag slot model (active production, presentation layer)

| Symbol | File | Notes |
|---|---|---|
| `ConsultationMeaningSlots` (type) | `apps/web/src/lib/concierge/buildRecommendationReasonViewModel.ts:109` | `{ needPrimary, needSecondary, state, wish, urgency, posture, emotionalTone }` |
| `buildConsultationMeaningSlots(params: BuildParams)` | `buildRecommendationReasonViewModel.ts:279` | **hardcoded** slot values selected by `params.needTags[0]` (`厄除け` / `仕事` / …). Takes `BuildParams` (rec / needTags / mode). **Reads nothing from the API `consultation_meaning` field.** |
| Consumers | `buildMeaningNarrative.ts` (:24,:473), `buildReasonNarrative.ts` (:21,:257,:363,:595), `buildStateNarrative.ts` (:13-14,:141) | all sibling files in `lib/concierge/`; feed `reasonVm.detail.{shrineMeaning, actionMeaning, consultationSummary}` → **rendered on Concierge Result AND Shrine Detail**. |
| External consumers | **none** — `grep ConsultationMeaningSlots` outside `lib/concierge/` → empty. Exported from `buildRecommendationReasonViewModel.ts` but only consumed by siblings. |

---

## 4. N2 Responsibility Matrix

| Symbol | File | Actual Responsibility | Layer | Runtime / API | Consumers | Rename Risk |
|---|---|---|---|---|---|---|
| `consultation_meaning` (JSON field) | backend `api_views_concierge.py` / `services/consultation_meaning.py` | Extracted consultation signals (situation / desired-outcome / constraint) from free text | **Stored/Derived** (backend-computed, serialized) | **API contract** (backend contract test locks it) | FE: `ConsultationMeaning` type; runtime: `mapConciergeResponseToPremiumMeaningContext` only | **High** — renaming the wire field breaks the API contract + backend test + FE type. Not a FE-only rename. |
| `ConsultationMeaning` (FE type) | `api/concierge/types.ts:64` | FE mirror of the JSON field | Presentation-adjacent API type | mirrors API | `mapConciergeResponseToPremiumMeaningContext.ts` (disconnected); barrel re-export unused externally | **Low-Med** — FE-only symbol, but its name *correctly* mirrors the wire field; renaming it desyncs from the JSON key. Best left matching `consultation_meaning`. |
| `ConsultationMeaningEvidence` (`types.ts:54`) | `api/concierge/types.ts` | `{text}` evidence span for a signal | API type | mirrors API | `ConsultationMeaning` sub-shape; barrel re-export unused externally | **Low** — FE-only; keep matching the wire. |
| `ConsultationMeaningEvidence` (`premiumMeaningContext.ts:59`) | `lib/concierge/premiumMeaningContext.ts` | **duplicate** `{text}` (same shape, different file) | FE type | none | `premiumMeaningContext.ts` internal, disconnected | **Low** — pure redundancy; could `import` from `types.ts` instead. Part of the shelve-or-connect (N1) decision. |
| `PremiumMeaningConsultationContext` | `premiumMeaningContext.ts:73` | camelCase FE consultation context for the (dead) Deep-Reason validity/builder | FE type | none | `premiumMeaningContext.ts` internal only | **Low** — disconnected; rename or delete is safe but belongs with N1. |
| `ConsultationMeaningSlots` | `buildRecommendationReasonViewModel.ts:109` | Heuristic need-tag → hardcoded emotional/urgency/posture slot bag | **Presentation** (template lookup) | **none** — no API, no persistence, no analytics, no public type | `buildMeaningNarrative` / `buildReasonNarrative` / `buildStateNarrative` (active) | **Low** — FE-internal (`lib/concierge`), exported but only sibling-consumed, no contract linkage. Safe mechanical rename. |
| `buildConsultationMeaningSlots` | `buildRecommendationReasonViewModel.ts:279` | builder for the above | Presentation | none | same 3 siblings | **Low** — same. |

---

## 5. N2 Classification

### N2 Questions — answers

1. **Are the flagged symbols the same concept?** **No.** Three concepts: (1) API `ConsultationMeaning` = extracted signal payload; (2) `PremiumMeaningConsultationContext` = disconnected FE context for the dead Deep-Reason chain; (3) `ConsultationMeaningSlots` = heuristic need-tag template bag. They share only the word.
2. **What's the difference?** (1) is real, backend-derived, per-consultation signal data on the wire. (3) is a frontend lookup table keyed on `needTags[0]` with hardcoded strings — it never touches the `consultation_meaning` field. (2) is (1) re-shaped for a builder that has no production consumer.
3. **Which name misleads most?** **`ConsultationMeaningSlots` / `buildConsultationMeaningSlots`** — an engineer reading `buildConsultationMeaningSlots` in `buildStateNarrative` reasonably assumes it consumes the `consultation_meaning` signal; it does not. This is the collision that causes real confusion (an active-production symbol impersonating the API concept).
4. **Rename-only side?** **Yes — Cluster 3** (`ConsultationMeaningSlots` / `buildConsultationMeaningSlots`). FE-internal, exported-but-sibling-only, zero contract linkage.
5. **Rename impact of Cluster 3 on API response / serializer / persisted data / analytics / FE public type / tests?**
   - API response: **none** (never referenced backend-side).
   - serializer: **none**.
   - persisted data: **none**.
   - analytics: **none** (no analytics payload field, no event references it).
   - FE public type: **none** exported past `lib/concierge` siblings.
   - tests: **zero** test files reference `ConsultationMeaningSlots` / `buildConsultationMeaningSlots` (`grep` in `apps/web/src/**/*.test.*` → empty). Mechanical identifier rename, **no expectation change**.
6. **Dead/disconnected symbols?** **Yes** — Cluster 2 entirely (`PremiumMeaningConsultationContext`, the 2nd `ConsultationMeaningEvidence`), plus the whole PR-A→D chain. Not deleted here (audit N1 / this task's scope exclusion).
7. **Rename-only PR separable?** **Yes** for Cluster 3 (see §16 PR-N2).

### Classification

| Cluster | Class | Rationale |
|---|---|---|
| Cluster 3 (`ConsultationMeaningSlots` / `buildConsultationMeaningSlots`) | **N2-A** — pure internal naming collision, safe mechanical rename | FE-internal, no contract/analytics/persistence linkage, only sibling consumers. This *is* the collision N2 flagged. |
| Cluster 1 (`ConsultationMeaning` / `ConsultationMeaningEvidence` API types + `consultation_meaning` field) | **N2-B** — bound to the API/runtime contract | The name is *correct* (mirrors the wire field). Renaming would need a backend contract review and is unwarranted — it should keep the name. No action needed beyond "leave it". |
| Cluster 2 (`PremiumMeaningConsultationContext`, 2nd `ConsultationMeaningEvidence`, PR-A→D) | **N2-C** — dead / disconnected | Zero production consumers. Rename or delete is safe but is really the N1 "connect or shelve PR-A→D" decision. **Do not touch in the N2 rename PR.** |
| The historical audit note ("collision") | Partially **N2-D** — the *API-side* names are not a real collision (they are contract-correct). The real, actionable collision is Cluster 3 only. |

**Net:** N2 = **N2-A for Cluster 3** (rename the heuristic slot model) + **N2-C** for Cluster 2 (leave for N1) + **N2-B** for Cluster 1 (leave as-is, name is correct).

---

## 6. N2 Rename Impact (Cluster 3, the only actionable rename)

Proposed: `ConsultationMeaningSlots` → e.g. `NeedTagMeaningSlots`; `buildConsultationMeaningSlots` → `buildNeedTagMeaningSlots` (final name is Mother Ship's to bless).

| Surface | Impact |
|---|---|
| `buildRecommendationReasonViewModel.ts` | type + function definition + one internal ref (`:422`) |
| `buildMeaningNarrative.ts` | 1 import, 3 type refs, 1 call |
| `buildReasonNarrative.ts` | 1 import, 3 calls |
| `buildStateNarrative.ts` | 1 import (type + fn), 4 type refs, 1 call |
| Tests | **no test references** `ConsultationMeaningSlots` / `buildConsultationMeaningSlots` at all — nothing to update |
| API / serializer / persisted data / analytics events / analytics payload / dedupe / dashboards | **none** |
| FE public types / barrels / cross-package | **none** |
| Backend | **none** |

**Blast radius: 4 source files + their unit tests, mechanical identifier rename, no contract touched.** Rename-only PR is safe.

---

## 7. N3 Production Path (Shrine Detail meaning analytics)

```
page.tsx  (server)
  builds model via buildShrineDetailModel({... freeDisplaySections, premiumDisplaySections,
    recommendationRankExplanation, recommendationRankComparison ...})
  → {...model} + recommendationInstanceId, stateDelta, isPremiumActive → <ShrineDetailArticle>

ShrineDetailArticle  (client)
  freeSections   = freeDisplaySections.map(i=>i.section)          (hasLayeredSections)
  premiumSections= premiumDisplaySections.map(i=>i.section)
  contextReasonSections = buildContextReasonSections(freeSections, contextReasonVisibility)
  freeMeaningBlockCardIds    = collectMeaningBlockCardIds(contextReasonSections)   // item.key ∈ {consultation_summary, shrine_meaning, action_meaning}
  premiumMeaningBlockCardIds = collectMeaningBlockCardIds(premiumSections)         // same
  contextReasonVisibility   = getVisibilityForCard("context_reason")        // visible / visible / visible
  personalMeaningVisibility = getVisibilityForCard("personal_meaning")      // teaser / teaser / visible
  recommendationMetaVisibility = getVisibilityForCard("recommendation_meta")// visible / visible / visible
  previousComparisonVisibility = isPremiumActive ? getVisibilityForCard("previous_comparison") : "teaser"

  useEffect (deps: visibilities, *MeaningBlockCardIdKey, has*Sections, recommendationInstanceId,
             recommendationMeta.rank{Title,Body}, stateDelta, saved node, historyTheme, shrineId):
    if hasContextReasonSections           → trackShrineDetailCardView(context_reason,  vis=contextReasonVisibility)
    for id in freeMeaningBlockCardIds      → trackShrineDetailCardView(id,             vis=contextReasonVisibility)
    if hasPremiumSections                  → trackShrineDetailCardView(personal_meaning,vis=personalMeaningVisibility)
    for id in premiumMeaningBlockCardIds   → trackShrineDetailCardView(id,             vis=personalMeaningVisibility)
    if resolvedSaveActionNode              → trackShrineDetailCardView(saved_record,   vis="visible")
    if recommendationMeta.rankTitle&&Body  → trackCardEvent(recommendation_meta,       vis=recommendationMetaVisibility)   // NO DOM
    if stateDelta && prevCmp!=="hidden"    → trackCardEvent(previous_comparison,       vis=previousComparisonVisibility)

trackShrineDetailCardView:  early-return if vis==="hidden";
  event = (vis==="partial"||vis==="teaser") ? "card_partial_view" : "card_view"
  source: "shrine_detail";  payload: cardId, accessLevel, visibility, shrineId, historyTheme,
          payloadSource, recommendationInstanceId.   NO resultSetId. NO dedupe ref.

trackCardEvent → serializeCardAnalyticsPayload (drops undefined) → getAnalyticsProvider().track(event, payload)
```

Notes:
- `ShrineDetailArticle` hardcodes `resolveAccessLevel(..., isAuthenticated=true)` → accessLevel is `free` or `premium` only; there is no `anonymous` on Shrine Detail.
- **No dedupe.** Concierge's `ConciergeSectionsRenderer` keeps a `trackedCardEventKeysRef` keyed on `resultSetId:event:cardId[:shrineId]`; `ShrineDetailArticle` has **no equivalent** and sends **no `resultSetId`**. It relies on effect-dep stability (~one fire per mount).
- `collectMeaningBlockCardIds` only extracts item keys `consultation_summary` / `shrine_meaning` / `action_meaning` from `kind:"meaning"` sections. `personal_meaning` and `context_reason` have **no item key** — they are bundle-level CardIds fired from `has*Sections` booleans.
- Render gating: premium meaning sections render only when `personalMeaningVisibility === "visible"` (premium). For free, `personalMeaningVisibility === "teaser"` → `<PremiumUpgradePrompt>` renders instead; `premiumSections` is still non-empty (model builds it), so `premiumMeaningBlockCardIds` is still populated and its events still fire.

---

## 8. CardId / DOM / Event Matrix (Shrine Detail)

Assumes `ctx=concierge&tid=…` with a shrine that has both free (`context_reason`) content and premium meaning sections containing `shrine_meaning` + `action_meaning` items, plus `recommendationMeta` and `stateDelta` present.

### Free (and "guest" — treated as free)

| CardId | Visibility (resolved) | Actual DOM / UI content | Unique visual surface? | Event fired | Dedupe key |
|---|---|---|---|---|---|
| `context_reason` | `visible` | `ShrineDetailSections(contextReasonSections)` — `ShrineReasonSection` / `ShrineProposalSection` / `ShrineSupplementSection` (`variant="plain"` after PR-G3) | ✅ yes (the free interpretation flow) | `card_view` | none (no resultSetId, no ref) |
| `personal_meaning` | `teaser` | `<PremiumUpgradePrompt>` (generic upgrade teaser) | ⚠️ shares the **same** `PremiumUpgradePrompt` surface with `shrine_meaning` + `action_meaning` below | `card_partial_view` | none |
| `shrine_meaning` | `teaser` (`personalMeaningVisibility`) | **none per-item** — the premium `ShrineJudgeSection` is not rendered for free; only `PremiumUpgradePrompt` is, and it has no per-item teaser | ❌ **no dedicated surface** | `card_partial_view` | none |
| `action_meaning` | `teaser` | same as `shrine_meaning` — no per-item surface | ❌ **no dedicated surface** | `card_partial_view` | none |
| `consultation_summary` | `teaser` (if item.key present in a premium `meaning` section) | none per-item | ❌ | `card_partial_view` | none |
| `recommendation_meta` | `visible` | **none** — no JSX renders `rankTitle`/`rankBody`. `RecommendationMetaSection.tsx` imported nowhere | ❌ **no surface at all** | `card_view` | none |
| `saved_record` | `visible` | save/visit/reflection block | ✅ yes | `card_view` | none |
| `previous_comparison` | `teaser` (non-premium override) | `ShrineDetailStateDeltaSection` renders only when `actionState ∈ {visited, reflected}`; **event fires whenever `stateDelta` exists**, regardless of `actionState` | ⚠️ often no surface (event fires, section only on visited/reflected) | `card_partial_view` | none |

### Premium

| CardId | Visibility | DOM | Unique surface? | Event | Dedupe |
|---|---|---|---|---|---|
| `context_reason` | `visible` | free interpretation flow (plain) | ✅ | `card_view` | none |
| `personal_meaning` | `visible` | `ShrineDetailSections(premiumSections)` bundle (`ShrineJudgeSection` + `ShrineActionSection`, plain) | ⚠️ **overlaps** `shrine_meaning` + `action_meaning` (same rendered bundle) | `card_view` | none |
| `shrine_meaning` | `visible` | `ShrineJudgeSection` item(s) inside that bundle | ⚠️ sub-part of the `personal_meaning` bundle DOM | `card_view` | none |
| `action_meaning` | `visible` | `ShrineActionSection` item inside that bundle | ⚠️ sub-part of the `personal_meaning` bundle DOM | `card_view` | none |
| `consultation_summary` | `visible` (if key present) | item inside the bundle | ⚠️ sub-part | `card_view` | none |
| `recommendation_meta` | `visible` | **none** | ❌ no surface | `card_view` | none |
| `saved_record` | `visible` | save block | ✅ | `card_view` | none |
| `previous_comparison` | `visible` | `ShrineDetailStateDeltaSection` (visited/reflected only) — event fires whenever `stateDelta` | ⚠️ often no surface | `card_view` | none |

### Flags (explicitly called out per the task)

| Flag | CardId(s) | Detail |
|---|---|---|
| **UI表示なしで view event だけ発火** | `recommendation_meta` | Fires `card_view`/`card_partial_view` whenever `rankTitle && rankBody`; **no JSX** anywhere. Locked by `ShrineDetailArticle.test.tsx:347-411`. |
| **UI表示なしで view event だけ発火 (conditional)** | `previous_comparison` | Event fires when `stateDelta` exists; the visible `ShrineDetailStateDeltaSection` only renders when `actionState ∈ {visited, reflected}` → event without surface in the common case. |
| **1 DOM に複数 view event** (premium) | `personal_meaning` + `shrine_meaning` + `action_meaning` [+ `consultation_summary`] | One rendered `ShrineDetailSections(premiumSections)` bundle → 3–4 distinct `card_view`s (bundle umbrella + per-type). |
| **1 surface に複数 view event / content overlap** (free) | `personal_meaning` + `shrine_meaning` + `action_meaning` | One rendered `<PremiumUpgradePrompt>` → 3 `card_partial_view`s. |
| **teaser しか出ていないのに per-type exposure 相当 event** (free) | `shrine_meaning`, `action_meaning`, `consultation_summary` | Their `card_partial_view` fires for free from `premiumMeaningBlockCardIds`, but the premium per-item sections are **not rendered** and `PremiumUpgradePrompt` carries **no per-item teaser** (contrast: Concierge PR-G2 follow-up added per-card teasers to the seam). |
| **visibility と event condition 不一致** | `previous_comparison` | Fires on `stateDelta` presence, not on `previousComparisonVisibility`-driven rendering; and its visibility is a non-`getVisibilityForCard` override (`isPremiumActive ? … : "teaser"`). |
| **DOM に存在しない CardId** | `recommendation_meta` | (same as row 1) |
| **cross-surface event-name inconsistency** | `shrine_meaning` / `action_meaning` teaser | Shrine Detail emits `card_partial_view` for `teaser` visibility; Concierge (`resolveConciergeCardViewEvent`) emits `card_teaser_view`. Same concept, different event name by surface. |
| **no dedupe / no resultSetId on Shrine Detail** | all Shrine Detail `card_view`s | `trackShrineDetailCardView` sends no `resultSetId` and there is no `trackedCardEventKeysRef`; dedupe policy (`docs/analytics/analytics-card-events.md`: "同一 cardId の card_view は同一 resultSetId 内で原則1回") is not enforceable on this surface. |

---

## 9. N3 Event Traces

### `shrine_meaning` (premium)
`buildMeaningNarrative` (heuristic) / payloadV2 premium block / reasonV4 → `premiumDisplaySections` (`buildShrineDetailModel`) → `premiumSections` → `collectMeaningBlockCardIds` sees `item.key === "shrine_meaning"` → `premiumMeaningBlockCardIds` includes it → effect `.forEach` → `trackShrineDetailCardView({cardId:"shrine_meaning", visibility: personalMeaningVisibility="visible", …recommendationInstanceId})` → `event: "card_view"` → `trackCardEvent` → `serializeCardAnalyticsPayload` → provider. **DOM:** `ShrineJudgeSection` item rendered (premium). Dedupe: none.

### `personal_meaning` (premium)
`hasPremiumSections === true` (bundle non-empty) → effect → `trackShrineDetailCardView({cardId:"personal_meaning", visibility:"visible"})` → `card_view`. **DOM:** the whole `ShrineDetailSections(premiumSections)` bundle (same DOM that `shrine_meaning`/`action_meaning` point into). Dedupe: none.

### `shrine_meaning` (free)
Identical mapping, but `personalMeaningVisibility === "teaser"` → `trackShrineDetailCardView` → `event: "card_partial_view"`, `visibility: "teaser"`. **DOM:** premium bundle **not** rendered; `<PremiumUpgradePrompt>` rendered instead (generic, no per-item teaser). Dedupe: none.

### `recommendation_meta`
backend `rank_explanation` / `rank_comparison` (only `ctx=concierge && tid`) → `page.tsx:343` → `buildRecommendationMeta` → `{rankTitle, rankBody, rankExplanation, rankComparison}` → `{...model}` → `ShrineDetailArticle`. Effect: `if (recommendationMeta?.rankTitle && recommendationMeta?.rankBody)` → `trackCardEvent({event: recommendationMetaVisibility==="partial"||"teaser" ? "card_partial_view" : "card_view", cardId:"recommendation_meta", source:"shrine_detail", visibility: recommendationMetaVisibility="visible", shrineId, historyTheme, payloadSource})`. **No `recommendationInstanceId` on this call** (unlike the meaning-block calls). **DOM: none.** Dedupe: none. Locked by test.

### `context_reason` (both)
`buildContextReasonSections(freeSections, "visible")` → non-empty → effect `if (hasContextReasonSections)` → `card_view` (`visibility: "visible"`). **DOM:** `ShrineDetailSections(contextReasonSections)` (plain, PR-G3). Dedupe: none.

---

## 10. Downstream Analytics Consumers

| Consumer | Location | Uses `shrine_meaning` / `personal_meaning` / `action_meaning`? | Evidence |
|---|---|---|---|
| `aggregateCardCtr` | `apps/web/src/lib/analytics/cardCtr.ts` | **Yes, as separate rows.** `CARD_VISIBILITY_EVENTS = {card_view, card_partial_view, card_teaser_view}`; `buildGroupKey = source::cardId::visibility::accessLevel::historyTheme` → **each `cardId` is its own CTR row** with its own `cardVisibilityCount` / `premiumClickCount` / `ctr`. | `cardCtr.ts:26-51` |
| `aggregateCardCtr` live consumer | — | **None in `apps/web/src`.** `grep` for `aggregateCardCtr` / `cardCtr` outside its file + `__tests__` → empty. It is a tested pure utility, **not wired into any rendered view or job**. | grep |
| `docs/analytics/premium-analytics-dashboard.md` | doc | Lists `shrine_meaning` / `action_meaning` / `consultation_summary` under `source: shrine_detail` "view count" collection (`:40-42`, `:188-190`), but the **primary conversion table** (`:139-146`) only names `context_reason`, `personal_meaning`, `saved_record`, `previous_comparison`, `history_shift`, `deep_reflection`. So the per-type meaning CardIds are **collected, not a headline CTR metric**. | doc |
| `docs/analytics/card-ctr-aggregation.md` | doc | Same — lists them (`:160-162`, `:182-183`) as inputs; example rows only for `context_reason` / `personal_meaning` (`:253-254`). | doc |
| `docs/analytics/shrine-detail-analytics-route.md` | doc (older) | **Only** names `context_reason`, `personal_meaning`, `saved_record` as Shrine Detail card-view candidates (`:142-143`, `:171-172`, `:275-283`). **Does not mention** `shrine_meaning` / `action_meaning` / `consultation_summary` — predates their addition. | doc |
| `docs/audit/recommendation-result-detail-instrumentation-contract.md` §7 | doc | **This is why the per-type events exist.** Defines the "Minimum Stable Join Contract" `(recommendationInstanceId, shrineId)` with **`cardId` as the compared dimension** — "`shrine_meaning` on Result joins to `shrine_meaning` on Detail, `action_meaning` to `action_meaning`". Stated purpose: a future funnel `count(DISTINCT (recommendationInstanceId, shrineId, cardId))` **"segmented by `cardId ∈ {shrine_meaning, action_meaning, consultation_summary}`"** to measure Result→Detail duplicate-exposure / drop-off **per meaning type**. | `:196-262` |
| `docs/audit/cross-platform-event-contract.md` | doc | Notes the Web `card_view` family "is scattered across many events and needs consolidation" for a unified `recommendation_view` (`:360`). Recognises fragmentation. | doc |
| Backend / SQL / dbt / dashboards (repo) | — | No `*.sql` / dashboard job in the repo references these cardIds. `score_v3_dashboard` is unrelated (score, not card CTR). | grep |
| Tests | `ShrineDetailArticle.test.tsx:347-423` (`recommendation_meta` + `previous_comparison` `card_view`), `:425-492` (`shrine_meaning` / `action_meaning` / `consultation_summary` `card_view` + `recommendationInstanceId` + `shrineId`); `cardCtr.test.ts` (aggregation groups by cardId) | Yes — the per-type Detail events **and** `recommendation_meta`'s UI-less event are **locked by tests**. | |

**Summary:** The per-type `shrine_meaning` / `action_meaning` / `consultation_summary` Detail events are **intentional (Model B / semantic-layer)** per the instrumentation contract §7, aggregated per-cardId by `aggregateCardCtr` (which has **no live consumer**), and named in the premium-analytics-dashboard doc as collected inputs but **not** as headline CTR metrics. No production SQL/dashboard/job currently reads them. `recommendation_meta`'s Detail `card_view` fires with no surface and is also test-locked.

---

## 11. N3 Policy A / B / C Comparison

**Which model is the current contract?** **Model C — Hybrid**, defined by `docs/audit/recommendation-result-detail-instrumentation-contract.md` §7:
- `context_reason` and `personal_meaning` behave as **surface** CardIds (fired from `has*Sections` booleans — "the free interpretation block / the premium meaning bundle was exposed").
- `shrine_meaning` / `action_meaning` / `consultation_summary` behave as **semantic-layer** CardIds (fired per `item.key` — "this meaning type was in the exposure"), explicitly to support a per-type Result↔Detail funnel.
- The boundary is defined in that §7 contract, **not** in `shrine-detail-analytics-route.md` (which is older and only knows the surface CardIds).

So today: `personal_meaning` (surface) DOM-overlaps `shrine_meaning` + `action_meaning` (semantic) for premium; for free, all three point at one generic `PremiumUpgradePrompt`; `recommendation_meta` has an event but no surface at all.

### Policy A — Surface granularity (one rendered surface → one CardId)

Keep `context_reason`, `personal_meaning`, `saved_record`, `previous_comparison`; **drop** the per-type `shrine_meaning` / `action_meaning` / `consultation_summary` Detail `card_view`s; **drop** the UI-less `recommendation_meta` event (or only fire it once it renders).

| Aspect | Effect |
|---|---|
| Event volume | −2 to −4 `card_view`s per Shrine Detail render (premium); −3 `card_partial_view`s (free). |
| Contract | **Breaks** the §7 Result↔Detail per-type join (would need a different join key, e.g. keep `shrine_meaning`/`action_meaning` on Result only and use `recommendationRank`/`shrineId` on Detail). |
| Dashboards | `premium-analytics-dashboard.md` / `card-ctr-aggregation.md` input lists must drop the per-type rows; no live consumer breaks (none exists). `aggregateCardCtr` still works (just fewer rows). |
| Tests | `ShrineDetailArticle.test.tsx:425-492` (per-type `card_view`) **must change**; `:347-411` (`recommendation_meta`) **must change**. → analytics-contract change. |
| Migration | If any offline query already segments Detail exposure by `cardId ∈ {shrine_meaning,…}`, historical data becomes non-comparable. **Unknown** — no such query is in the repo. |
| Visibility alignment | Improves — 1 CardId per visible surface; removes the "event without DOM" flags. |
| G1/G3 alignment | Consistent with "reduce card stacking" (fewer semantic events for one narrative). |

### Policy B — Semantic granularity, kept (status quo intent), made honest

Keep the per-type events (Model C as-is), but **prove each corresponds to visible content**:
- For **premium**, they already do (`ShrineJudgeSection` / `ShrineActionSection` render the items).
- For **free**, add per-type teaser content to the Shrine Detail teaser surface (mirroring the Concierge PR-G2 follow-up), so `shrine_meaning` / `action_meaning` `card_partial_view` map to a real per-type teaser line.
- Decide `personal_meaning` role: keep as an umbrella "bundle exposed" event **or** drop it as redundant with the per-type events.
- `recommendation_meta`: either render it (surface) or stop firing its event.

| Aspect | Effect |
|---|---|
| Event volume | Unchanged (or −1 if `personal_meaning` umbrella dropped). |
| Contract | §7 join preserved. |
| UI | Needs a small Shrine Detail free-teaser change (per-type lines) — presentation PR, no analytics change if events already fire. |
| Tests | Per-type event tests **unchanged**; free-teaser DOM tests **added**. |
| Duplicate-count risk | `personal_meaning` + per-type still double-counts the same premium bundle in `aggregateCardCtr` unless `personal_meaning` is dropped or documented as a distinct "bundle" metric. |
| Honesty | Improves — every event maps to visible content; the "no DOM" flags for the meaning types go away (but `recommendation_meta` still needs its own resolution). |

### Policy C — UI split so each semantic event has its own visible section

Render `shrine_meaning`, `personal_meaning`, `action_meaning` as **separate labelled sections** (each its own `<h2>` surface) so surface == semantic 1:1.

| Aspect | Effect |
|---|---|
| Events | Unchanged; each now has a dedicated surface. |
| UI | **Directly conflicts with G1/G3** ("less card stacking, one continuous Meaning narrative"). Re-introduces 3 stacked meaning sections. |
| Premium Meaning UX | More fragmented; against Direction C. |
| Visual hierarchy | Worse (more headings competing). |
| Free | Would need 3 teaser stubs → the exact "repeated teaser cards" G2 removed. |

**No option is free of trade-offs. Two are viable (A and B). Decision returned to Mother Ship (§13).**

---

## 12. recommendation_meta Dependency

Re-confirmed (PR-G3 finding stands):
- **What:** backend `ConciergeRecommendation.rank_explanation` + `rank_comparison` → `buildRecommendationMeta` → `{rankTitle: "この神社が1位の理由"|"1位との違い", rankBody: summary|comparison_summary, rankExplanation, rankComparison}`. **Ranking evidence**, not shrine facts, not personal meaning. Only present with `ctx=concierge && tid`.
- **State:** backend-emitted ✅; mapped into the model ✅; own `CardId` in `cardVisibility.ts` (`visible/visible/visible`) ✅; `card_view` / `card_partial_view` event **already fires** (test-locked) ✅; **no JSX consumer** (`RecommendationMetaSection.tsx` imported nowhere) ✅.

Answers:

1. **Is an analytics change needed to render it in the Evidence layer?** **No, technically.** The event already fires with a fixed payload/CardId/visibility. Adding a JSX consumer that renders `rankTitle`/`rankBody` in the Evidence layer, **without** adding a second event, is a pure-presentation change.
2. **Would rendering improve UI/analytics alignment?** **Yes.** It converts an "event with no surface" flag into an honest impression.
3. **Direct dependency on N2?** **None.** `recommendation_meta` shares no symbol with the `ConsultationMeaning*` clusters.
4. **Technical dependency on N3?** **None for a pure render add.** It is its own CardId, not part of the `personal_meaning` / `shrine_meaning` / `action_meaning` bundle-vs-item mechanism (`collectMeaningBlockCardIds` never touches it).
5. **Or only D-4 sequencing?** **Mostly D-4 + policy coherence.** Mother Ship D-4 said "complete N2/N3 before any analytics-contract-related change involving `recommendation_meta`." A pure render add is arguably *not* an analytics-contract change — **but** it is the exact pattern N3 Policy A would resolve by *removing* the event. If Policy A is chosen, adding a surface for `recommendation_meta` runs opposite to the policy; if Policy B, adding the surface is the correct fix. So the render decision is **coupled to the N3 policy choice**, not to N3's code.
6. **Proceed after N2 only?** No — N2 is unrelated.
7. **Proceed after N3 only?** **Yes** — once Mother Ship picks the N3 policy, `recommendation_meta` follows it (Policy A → drop event; Policy B → render in Evidence, no event change).
8. **Both needed?** No.
9. **Neither technically needed?** For a *pure* render-in-Evidence with no event change: technically unblocked. But it would pre-empt the N3 Policy A/B decision, so it should wait for it.

**Classification: Case B — must wait for the N3 analytics-contract (Policy A/B) decision.** Not a hard technical block; a policy-coherence block.

---

## 13. Mother Ship Decisions Required

### Decision N2

> **Which concept keeps the `ConsultationMeaning` name, and what is the heuristic slot model renamed to?**
> - **A. API/runtime type keeps `ConsultationMeaning`** (it mirrors the backend `consultation_meaning` wire field); rename the heuristic FE slot model `ConsultationMeaningSlots` / `buildConsultationMeaningSlots` → e.g. `NeedTagMeaningSlots` / `buildNeedTagMeaningSlots`. **(Audit recommendation.)**
> - B. Rename the API-side FE type instead (not recommended — desyncs from the wire key; needs backend contract review = N2-B).
>
> **Evidence:** the heuristic model reads `params.needTags`, never `consultation_meaning`; it is FE-internal with no contract linkage (N2-A, §5–6). The API type's name is contract-correct. Cluster 2 (`PremiumMeaningConsultationContext`, duplicate `ConsultationMeaningEvidence`) is dead code (N2-C) and belongs to the N1 "connect or shelve PR-A→D" decision, **not** this rename.
>
> _If A: this is a **pure internal rename** — no product decision, no contract/analytics/persistence/public-type impact; a rename-only PR (§16 PR-N2) is sufficient. Mother Ship approval is only for the new name._

### Decision N3

> **What should one Shrine Detail Meaning impression represent?**
>
> | Option | vs current impl | Analytics impact | UI impact | Risk |
> |---|---|---|---|---|
> | **A. One visible UI surface = one CardId** | Drop the per-type `shrine_meaning`/`action_meaning`/`consultation_summary` Detail `card_view`s + the UI-less `recommendation_meta` event; keep `context_reason`/`personal_meaning`/`saved_record`/`previous_comparison` | Event volume −2…−4/render; **breaks §7 per-type Result↔Detail join** (needs a rework); `aggregateCardCtr` loses per-type rows (no live consumer); **`ShrineDetailArticle.test.tsx:347-492` expectations change** | None (fewer events, no DOM change) | Historical per-`cardId` Detail segmentation (if any offline query exists — none in repo) becomes non-comparable |
> | **B. One semantic Meaning layer = one CardId (keep Model C), made honest** | Keep per-type events; add per-type teaser lines to the Shrine Detail free teaser surface so free events map to visible content (mirror Concierge PR-G2 follow-up); decide `personal_meaning` umbrella keep/drop; resolve `recommendation_meta` (render in Evidence, no event change) | No event add/rename/remove (unless `personal_meaning` umbrella dropped); §7 join preserved | Small free-teaser presentation change; Evidence render for `recommendation_meta` | `personal_meaning` + per-type still double-counts the same premium bundle in any per-cardId aggregation unless `personal_meaning` is dropped/relabelled |
> | **C. Split the UI so each semantic event has its own visible section** | Render `shrine_meaning` / `personal_meaning` / `action_meaning` as separate `<h2>` surfaces | Events unchanged | **Conflicts with G1/G3 / Direction C** — re-stacks meaning cards; worse hierarchy; re-introduces the repeated teaser cards G2 removed | Product-direction regression |
>
> **Audit lean:** **B** (keep the §7 semantic contract, make it honest) — or **A** if Mother Ship wants the simplest event model and accepts reworking the §7 join. **Reject C.** Codex does not choose.

### Decision recommendation_meta

> **Is `recommendation_meta` Evidence integration still blocked?**
> - A. Presentation-only integration can proceed now.
> - **B. Must wait for the N3 analytics-contract (Policy A/B) decision.** **(Audit finding.)**
> - C. Must wait for another dependency.
>
> **Evidence:** No N2 dependency (§12 Q3). No N3 *code* dependency for a pure render add (§12 Q4). But `recommendation_meta`'s current state ("event fires, no surface") is exactly what N3 Policy A would fix by *removing* the event and Policy B by *adding* the surface — so the render decision is **coupled to the N3 policy choice** (§12 Q5). It can proceed **immediately after** the N3 decision, following it: Policy A → drop the event (no render); Policy B → render `rankTitle`/`rankBody` in the Evidence layer, no event change. Not a standalone card either way (Mother Ship D-2).

---

## 14. Deferred

- **N2 rename (Cluster 3)** — held for Decision N2 approval of the new name. Rename-only PR then (§16 PR-N2).
- **N2-C dead code** (`PremiumMeaningConsultationContext`, duplicate `ConsultationMeaningEvidence`, PR-A→D chain) — held for the N1 "connect or shelve" decision; **not** part of the N2 rename.
- **N3 event model** — held for Decision N3 (A / B).
- **recommendation_meta Evidence render** — held for Decision N3 (Case B); then follows the chosen policy.
- **Shrine Detail dedupe / `resultSetId` parity with Concierge** — noted (§8 flags); no decision requested here, but relevant to whichever N3 policy lands.
- **Cross-surface `card_partial_view` vs `card_teaser_view` naming** — noted (§8); part of the "event consolidation" already flagged in `cross-platform-event-contract.md`.
- **Combined G1+G2+G3 pixel QA (375/390/430)** — still outstanding (backend unavailable).
- **PR-G4** — not started.

---

## 15. Out of Scope (this task changed none of these)

N2 rename · N3 event fix · CardId change · event add/remove · analytics payload change · dedupe change · `recommendation_meta` JSX · Premium UI · Shrine Detail UI · Concierge UI · backend · Meaning generation · Recommendation / Ranking · visibility · routing · test expectation changes · PR-G4.

---

## 16. Recommended PR Decomposition (if/when Mother Ship approves — not implemented here)

| PR | Scope | Depends on | Analytics contract change? |
|---|---|---|---|
| **PR-N2** — rename-only | `ConsultationMeaningSlots` → `NeedTagMeaningSlots`, `buildConsultationMeaningSlots` → `buildNeedTagMeaningSlots` across the 4 `lib/concierge` files + their unit tests. Mechanical. | Decision N2 (name) | **No** |
| **PR-N3** — Shrine Detail analytics model | Implement the chosen Policy A **or** B. If A: remove per-type Detail `card_view`s + the UI-less `recommendation_meta` event, update `ShrineDetailArticle.tsx` effect + `ShrineDetailArticle.test.tsx`, update the §7 instrumentation contract + `premium-analytics-dashboard.md` + `shrine-detail-analytics-route.md`. If B: add per-type free teaser content, decide `personal_meaning` umbrella, no event change, update free-teaser tests. | Decision N3 | **A: yes. B: no (unless `personal_meaning` dropped).** |
| **PR-N3b** — recommendation_meta | Follows PR-N3's policy: A → nothing (event removed in PR-N3); B → render `rankTitle`/`rankBody` in the Shrine Detail Evidence layer (`<details>` or a low-emphasis section), **no** new event, **not** a standalone card. Update `ShrineDetailArticle.test.tsx` render assertion (not the event). | PR-N3 | **No** (render-only) |
| **PR-N1** (separate track) | Connect or shelve PR-A→D (`mapConciergeResponseToPremiumMeaningContext`, `buildDeepRecommendationReason`, `PremiumMeaningContext`); dedupe `ConsultationMeaningEvidence`. | Mother Ship N1 decision | depends |
| **Mobile QA** | Combined G1+G2+G3 (+N3) pixel pass at 375/390/430 × guest/free/premium once a backend + consultation is available. | backend | n/a |
| **PR-G4** | Not started; separate decision. | — | n/a |

---

**STOP.** Audit only. No production code changed. Awaiting Mother Ship: Decision N2, Decision N3, Decision recommendation_meta.
