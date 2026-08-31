# Personal Meaning / Action Meaning — Shrine Evidence Readiness Audit

Read-only audit. No production code, backend, frontend, or test files were
changed as part of this document. See "Validation" at the end.

## 1. Executive Summary

PR-D found that presence of both a valid Structured Consultation Context and
valid Recommendation Evidence does not prove they are *related* -- no stable
field links a `reason_fact` back to a specific Consultation Meaning v1
signal, so `buildDeepRecommendationReason()` was corrected to always return
`null`.

This audit asks the equivalent question for Personal Meaning
(`Structured Consultation Context × Relevant Shrine Knowledge Evidence`) and
Action Meaning (`valid Personal Meaning + relevant Shrine Context`).

**The answer is the same, but worse: there is no relevance judgment at all
to distrust.** `PremiumMeaningShrineEvidence.relevantToConsultation` and
`.relevantToVisit` -- the two fields the type contract itself designates as
the *only* legitimate basis for `shrineEvidenceValid` /
`relevantShrineContextValid` -- are hardcoded to `null` in the only place in
the entire codebase that constructs a `PremiumMeaningShrineEvidence`
(`mapConciergeResponseToPremiumMeaningContext.ts`), and a full-repository
grep confirms no other code path ever sets them to anything else. This is
not "insufficient proof of relationship" (PR-D's finding); it is **total
absence of a relevance producer**. Consequently `shrineEvidenceValid`,
`relevantShrineContextValid`, `personalMeaningValid`, and `actionMeaningValid`
can never be `true` under current production data, regardless of how
Personal/Action Meaning generation logic is written.

Every existing production narrative path that currently occupies Personal
Meaning's / Action Meaning's UI slots (`buildMeaningNarrative.ts`,
`buildStateNarrative.ts`, `buildRecommendationReasonViewModel.ts`'s slot
builders, `buildDeepReason.ts`) is a generic template keyed by legacy
need_tag JA labels (厄除け/仕事/転機/恋愛/健康/学業) or, in one case, by
literal shrine-name substring matching (`shrineName.includes("三峯")`) --
none of it reads Consultation Meaning v1 signals or Shrine Knowledge Evidence
fields as data, and none of it is reusable under PR-E's "no generic template,
no co-presence assumption" constraint.

**Verdict: BLOCKED.**

## 2. PremiumMeaningContext Shrine Evidence Inventory

Source: `apps/web/src/lib/concierge/premiumMeaningContext.ts` (current
`develop`, `PremiumMeaningShrineEvidence` type, lines 112-144).

| Field | Type | Nullable/Optional | Frontend mapping source | Backend/API source | Real data in production? | Factual | Interpreted | Consultation-specific | Visit-specific |
|---|---|---|---|---|---|---|---|---|---|
| `shrineId` | `number` | required | `resolveShrineId(rec)` (`rec.shrine_id` \| `rec.id`) | `ConciergeRecommendation.shrine_id`/`id` | Yes | identifier, not evidence | No | No | No |
| `deity` | `string \| null` | optional | `rec.recommendation_reason_v4_detail.fact.deity` | `recommendation_reason_v4.py:_build_fact` (`candidate_profile.deity`/`main_deity`/`enshrined_deity`) | Yes, where Fact-ready | Yes | No | No | No |
| `history` | `string \| null` | optional | `...fact.shrine_history` | `_build_fact` (`candidate_profile.history`/`shrine_history`/`origin`) | Yes, where Fact-ready | Yes | No | No | No |
| `historyTheme` | `string \| null` | optional | `...fact.history_theme` | `_build_fact` (`candidate_profile.history_theme`) | Yes, where present | Yes | No | No | No |
| `originSummary` | `string \| null` | optional | `rec.trust_metadata.origin_summary` | `shrine_trust_metadata.py:SHRINE_TRUST_METADATA` (hardcoded per shrine_id) | Only for shrine_id 17, 14 (2 shrines total) | Yes | No | No | No |
| `placeContext` | `string \| null` | optional | `...fact.place_context` | `_build_fact` (`candidate_profile.place_context`/`area_context`/`location_context`) | Yes, where present | Yes | No | No | No |
| `culturalStatus` | `string[] \| null` | optional | `rec.trust_metadata.cultural_status` | `shrine_trust_metadata.py` (hardcoded) | Only for shrine_id 17, 14 | Yes | No | No | No |
| `lineage` | `string \| null` | optional | `rec.trust_metadata.lineage` | `shrine_trust_metadata.py` (hardcoded) | Only for shrine_id 17, 14 | Yes | No | No | No |
| `goriyaku` | `string[] \| null` | optional | `[clean(fact.goriyaku)]` if present | `_build_fact` (`candidate_profile.goriyaku`/`goriyaku_tags`) | Yes, where present | Yes | No | No | No |
| `tradition` | `string \| null` | optional | **hardcoded `null`** | none -- comment: "No stable Concierge Response field exposes tradition ... not sourced here" | **Never** | N/A | N/A | N/A | N/A |
| `verificationMetadata` | `ShrineEvidenceVerificationMetadata \| null` | optional | **hardcoded `null`** | none -- comment: "no per-source verification metadata individually" | **Never** | N/A | N/A | N/A | N/A |
| `relevantToConsultation` | `boolean \| null` | required slot, nullable | **hardcoded `null`** | none | **Never** | N/A | N/A | Intended to be, but no producer exists | No |
| `relevantToVisit` | `boolean \| null` | required slot, nullable | **hardcoded `null`** | none | **Never** | N/A | N/A | No | Intended to be, but no producer exists |

## 3. Source Trace

Traced from real code, no inference:

```
backend/temples/services/recommendation_reason_v4.py:_build_fact()
  (candidate_profile: dict, shrine-side only, explicit docstring
   "Fact must not interpret the user's state or suggest the next action")
  -> fact = {deity, shrine_history, place_context, history_theme, goriyaku,
             visit_style_tags, name, evidence, label}
  -> exposed on API as ConciergeRecommendation.recommendation_reason_v4_detail.fact
       (apps/web/src/lib/api/concierge/types.ts: RecommendationReasonV4Fact)
  -> apps/web/src/lib/concierge/mapConciergeResponseToPremiumMeaningContext.ts
       :mapShrineEvidence() reads fact.deity / fact.shrine_history /
       fact.history_theme / fact.place_context / fact.goriyaku unconditionally
  -> PremiumMeaningShrineEvidence.{deity,history,historyTheme,placeContext,goriyaku}

backend/temples/services/shrine_trust_metadata.py:SHRINE_TRUST_METADATA
  (hardcoded dict[int, ShrineTrustMetadata], only shrine_id 17 and 14 populated)
  -> exposed on API as ConciergeRecommendation.trust_metadata
       {rank_class, cultural_status, lineage, origin_summary}
  -> mapShrineEvidence() reads trust_metadata.origin_summary /
       .cultural_status / .lineage unconditionally
  -> PremiumMeaningShrineEvidence.{originSummary,culturalStatus,lineage}

relevantToConsultation / relevantToVisit:
  -> mapShrineEvidence() sets both to `null` unconditionally, with an
     explicit in-code comment: "Fixed: no Relevance judgment logic exists
     to source from, and Relevance must never be inferred from Evidence
     presence."
  -> No other file in the repository writes to a field named
     relevantToConsultation or relevantToVisit (confirmed by
     `grep -r "relevantToConsultation|relevantToVisit"` across the full
     repo -- the only hits are the type definition, this mapper, the
     validity functions that read it, and test files).
```

`tradition` and `verificationMetadata` have no backend or mapping source at
all -- they are dead fields on the type, always `null`.

## 4. `relevantToConsultation` Audit

- **Where generated:** nowhere. `mapShrineEvidence()` in
  `mapConciergeResponseToPremiumMeaningContext.ts` sets it to `null`
  unconditionally. No backend field, no other frontend module, and no test
  fixture outside this file's own unit tests ever assigns it `true`.
- **Actual type:** `boolean | null` per the `PremiumMeaningShrineEvidence`
  type. In practice, always exactly `null` in every production code path.
- **What would make it true/valid:** nothing does, today. The type's own
  doc comment (lines 125-133) describes the *intended* semantics ("Whether
  Shrine Specific Evidence ... has been judged -- by a Relevance judgment
  NOT implemented in PR-A -- to actually connect to THIS consultation's
  User Context") but explicitly defers the judgment logic itself, and no
  subsequent PR (B/C/D) has implemented it.
- **Does it reference Consultation Meaning v1?** No -- there is no code to
  reference anything.
- **Does it reference need_tag?** No.
- **Does it reference reason_facts?** No.
- **Does it reference raw free_text?** No.
- **Is it inferred from Shrine Knowledge presence alone?** No -- and the
  mapper's own comment explicitly forbids that ("Relevance must never be
  inferred from Evidence presence").
- **Usable as evidence of a semantic relationship?** No. It carries no
  information at all in its current state (constant `null`).
- **Does `relevantToConsultation === true` ever prove a specific Shrine
  Evidence field relates to a specific Consultation Meaning v1 signal?**
  Not applicable -- the value is never `true` in the first place. Even if
  it were implemented, the type is a single coarse boolean covering the
  whole `PremiumMeaningShrineEvidence` bundle (deity + history + place
  Context taken together), not per-field or per-signal, so even a future
  implementation would need a shape change (or a separate per-field/per-
  signal structure) to prove a *specific* Evidence-field ↔ *specific*
  Signal-type relationship, not just "some Shrine Evidence relates to some
  Consultation Context."

## 5. `relevantToVisit` Audit

Identical situation to §4, traced independently:

- **Source:** `mapShrineEvidence()`, hardcoded `null`, same comment as
  `relevantToConsultation`.
- **Generation logic:** none exists.
- **Semantic meaning (intended, per type doc):** "Whether Shrine Context
  has been judged ... relevant to the act of visiting (Action Meaning's
  'Relevant Shrine Context')."
- **Relationship to visit-style signal:** `PremiumMeaningConsultationContext`
  does carry a `visitPreferences?: unknown | null` field, but it is untyped
  (`unknown`) and is not populated by `mapConsultation()` in
  `mapConciergeResponseToPremiumMeaningContext.ts` either (not part of that
  mapping's scope, per its own doc comment) -- so even the input this field
  would need to reason about is not currently wired up.
- **Relationship to consultation context:** none -- no code connects it to
  `situationSignals`/`desiredOutcomeSignals`/`explicitConstraintSignals`.
- **Safe as Action Meaning's basis today?** No -- it is a constant `null`,
  identical to §4's finding.

## 6. Validity Contract Audit

Source: `computePremiumMeaningValidity()`,
`apps/web/src/lib/concierge/premiumMeaningContext.ts` (lines 220-309).

```ts
function isShrineEvidencePresent(shrineEvidence): boolean {
  return Boolean(clean(shrineEvidence.deity) || clean(shrineEvidence.history) || clean(shrineEvidence.placeContext));
}

function isShrineEvidenceValid(shrineEvidence): boolean {
  return isShrineEvidencePresent(shrineEvidence) && shrineEvidence.relevantToConsultation === true;
}

function isRelevantShrineContextValid(shrineEvidence): boolean {
  return isShrineEvidencePresent(shrineEvidence) && shrineEvidence.relevantToVisit === true;
}

const personalMeaningValid = userContextValid && shrineEvidenceValid;
const actionMeaningValid = personalMeaningValid && relevantShrineContextValid;
```

The contract **already draws the exact distinction this audit was asked to
check**, and draws it correctly:

- `shrineEvidencePresent` = **existence only** (deity/history/placeContext
  non-empty). The code comment is explicit: "PRESENCE only -- callers must
  not treat this as Validity by itself."
- `shrineEvidenceValid` / `relevantShrineContextValid` = **presence AND an
  explicit `=== true` relevance judgment**, not "data exists" alone. This is
  the field the code comments describe as semantic-relevance-aware, in
  contrast to `shrineEvidencePresent`.

So the *validity formula itself* does not conflate presence with relevance
-- it correctly requires both. **The problem is entirely upstream**: since
§4/§5 established `relevantToConsultation`/`relevantToVisit` are always
`null` in every real code path, the `=== true` half of both `isShrineEvidenceValid`
and `isRelevantShrineContextValid` can never be satisfied today. The
formula is honest; the input it depends on has never been implemented.
Net effect: `personalMeaningValid` and `actionMeaningValid` are always
`false` under current production data, with no exception.

## 7. Existing Production Personal / Action Meaning Paths

All read directly from current `develop`; none were modified.

| Path | What it actually sources | need_tag dependency | reason_fact dependency | shrine-specific evidence dependency | raw free_text dependency | generic template dependency |
|---|---|---|---|---|---|---|
| `buildMeaningNarrative.ts` (labeled "行動意味" -- legacy Action Meaning) | `need` (legacy JA need_tag label: 厄除け/仕事/金運/転機/恋愛/健康/学業), `shrine.tone` (see next row), a 5-shrine-ID hardcoded `SHRINE_CONTEXT_TABLE`, else place-word text inference (山/森/水/街) | Yes, primary keying axis | No | Only via `shrine.feature`/`SHRINE_CONTEXT_TABLE`, not the `PremiumMeaningShrineEvidence` fields at all | No | Yes -- every branch is a hand-written Japanese sentence keyed by `need`/`tone` |
| `buildStateNarrative.ts` (legacy "状態整理") | Same `need` keying, same hardcoded per-need Japanese sentences | Yes | No | No | No | Yes |
| `buildRecommendationReasonViewModel.ts:buildConsultationMeaningSlots()` | Hardcoded `state`/`wish`/`urgency`/`posture`/`emotionalTone` literals per legacy need_tag JA label | Yes | No | No | No | Yes |
| `buildRecommendationReasonViewModel.ts:buildShrineMeaningSlots()` | `tone` is set by **literal shrine-name substring match**: `shrineName.includes("三峯")` → `"strong"`, `includes("伊勢"\|"内宮")` → `"quiet"`, `includes("乃木")` → `"tight"`, else `"neutral"` | No | Partially (`benefitPrimary` via `reason_facts`) | Only 3 shrines by name string, not by any Evidence field | No | Yes -- name-substring hack, not scalable |
| `recommendation_reason_v4.py:_build_interpretation()` / `_build_action()` | `interpretation_profile` (the **legacy, debug-only** `InterpretationProfile` from `consultation_interpreter.py` -- `state_profile`/`emotion_profile`/`decision_context`/`constraint_profile`/`outcome_hint`) plus `consultation_axis` (a third, independent keyword-matched vocabulary, `domain/consultation_axis.py`) | Indirectly, via `interpretation_profile.need_profile` | No | No -- Fact and Interpretation are built as separate layers by design (`_build_fact`'s own docstring: "Fact must not interpret the user's state") | Indirectly, via `consultation_axis` keyword matching over the query | Templated, but at least evidence-labeled by source strings |
| `buildDeepReason.ts` (legacy, `NarrativeFallback` type -- unrelated to PR-D's `DeepRecommendationReason`) | `findShrineMeaning(shrineName)` (name-keyed lookup) + `buildInterpretation()` (need_tag/tone-templated) | Yes | No | Only via name-keyed lookup table | No | Yes |
| Shrine Detail premium sections (`ShrineDetailArticle.tsx` §③/§④, "この神社で受け取る意味" / "参拝するときの視点") | `detail.shrineMeaning` / `detail.actionMeaning`, both produced by `buildMeaningNarrative()` above | Yes (transitively) | No | Transitively, only via the same hardcoded paths | No | Yes (transitively) |

**Reuse verdict for PR-E:** none of these paths are safe to reuse. Every one
of them either (a) keys off the legacy need_tag JA label rather than
Consultation Meaning v1 signals, (b) keys off literal shrine-name string
matching rather than any typed Evidence field, or (c) reads the debug-only
`InterpretationProfile`, which Task B already established is not a source
of truth. Reusing any of them would reproduce exactly the "co-presence /
generic template" failure mode this audit is explicitly checking for.

## 8. Evidence Classification Matrix

| Field | Classification | Basis |
|---|---|---|
| `deity` | **C. FACTUAL_ONLY** | Real shrine fact (`_build_fact`, shrine-side only by explicit design); no consultation-relevance judgment attached anywhere |
| `history` | **C. FACTUAL_ONLY** | Same as `deity` |
| `historyTheme` | **D. CONDITIONALLY_SAFE** (with the condition unmet today) | A related but distinct signal (`history_theme_candidate_boost > 0`, gated on `consultation_axis`) already exists in the *Recommendation Evidence* path (`concierge_chat_ranking._build_reason_facts`) and could, if wired into `mapShrineEvidence`, gate this field on *some* per-consultation signal. Condition for even conditional safety: (1) `mapShrineEvidence` would need to consult that boost signal (currently it does not -- `historyTheme` is read unconditionally from `fact.history_theme`), and (2) `consultation_axis` is a keyword vocabulary independent of Consultation Meaning v1's 10-type taxonomy, so even gated, it would prove a relationship to a *consultation_axis* value, not to a *specific `situationSignals`/`desiredOutcomeSignals`/`explicitConstraintSignals` entry* as PR-E's stated formula requires. Net: not usable as-is for PR-E's exact formula. |
| `originSummary` | **C. FACTUAL_ONLY** | Hardcoded per-shrine table (`shrine_trust_metadata.py`), shrine-side, only 2 shrines populated |
| `placeContext` | **C. FACTUAL_ONLY** | Same as `deity` |
| `culturalStatus` | **C. FACTUAL_ONLY** | Same as `originSummary` |
| `lineage` | **C. FACTUAL_ONLY** | Same as `originSummary` |
| `goriyaku` | **C. FACTUAL_ONLY** | Shrine-side fact; existing goriyaku-tag matching used for *Recommendation* ranking is a separate, need_tag-driven system, not wired to this field's relevance |
| `tradition` | **E. UNSAFE_FOR_SEMANTIC_JOIN** | No data source exists at all -- always `null` |
| `verificationMetadata` | **E. UNSAFE_FOR_SEMANTIC_JOIN** | No data source exists at all -- always `null` |
| `relevantToConsultation` | **E. UNSAFE_FOR_SEMANTIC_JOIN** | No producer anywhere in the codebase; always `null` |
| `relevantToVisit` | **E. UNSAFE_FOR_SEMANTIC_JOIN** | No producer anywhere in the codebase; always `null` |

No field qualifies as **A. SAFE_FOR_PERSONAL_MEANING** or
**B. SAFE_FOR_ACTION_MEANING** under current data.

## 9. Semantic Join Risks

Risks identified if PR-E were implemented against current data without
addressing the gap in §4/§5:

1. **Silent-always-null risk** (same shape as PR-D, but total): a
   correctly-written, contract-faithful Personal Meaning builder would
   simply never fire in production, since `personalMeaningValid` can never
   be `true`. This is the *safe* failure mode, but it means PR-E would ship
   no visible behavior change while looking complete.
2. **Temptation-to-fabricate risk**: because `shrineEvidencePresent` (mere
   existence of deity/history/placeContext) is easy to satisfy and looks
   superficially like "we have shrine data for this," there is a real risk
   of an implementation quietly substituting `shrineEvidencePresent` for
   `shrineEvidenceValid`, or wiring `relevantToConsultation` to always
   `true` "since we already have deity/history text to show" -- both would
   silently violate the type's own documented contract ("Presence alone,
   NOT Relevance -- must never gate Personal Meaning by itself").
3. **Reuse-of-legacy-templates risk**: §7 shows every existing narrative
   path occupying Personal/Action Meaning's current UI slots is a
   need_tag-keyed or shrine-name-keyed generic template. Under schedule
   pressure, reusing or lightly adapting one of them would reintroduce
   exactly the "co-presence proves relevance" and "generic template"
   failure modes PR-D was reviewed for and PR-E is explicitly asked to
   avoid.
4. **`historyTheme` false-positive risk**: because a per-consultation gate
   for `historyTheme` (the `history_theme_candidate_boost` signal) already
   exists *elsewhere* in the codebase (Recommendation Evidence path) but is
   not wired into `PremiumMeaningShrineEvidence`, a future implementer might
   assume it can be reused directly to prove Personal-Meaning-level
   relevance. §8 explains why it cannot, as-is, satisfy PR-E's exact
   Structured-Consultation-Context-signal-level formula.

## 10. Minimum Missing Contract

Not designed here -- recorded only, per the Audit's explicit constraint.

A future **Shrine Knowledge Relevance Judgment Contract v1** would need, at
minimum:

1. An actual producer for `relevantToConsultation` and `relevantToVisit`
   (today: none exists). This producer would need to be evidence-required
   and inference-free, in the same spirit as PR-C's Extraction Contract --
   not label similarity, not raw free_text comparison, not AI/LLM inference.
2. A shape granular enough to prove *which* Shrine Evidence field relates
   to *which* Consultation Meaning v1 signal (category + type), not a
   single coarse boolean covering the whole Evidence bundle -- otherwise
   "relevant" cannot be traced to a specific claim the way PR-D's
   traceability invariant requires for Deep Recommendation Reason.
3. Its own dedicated design sequence (Contract → Taxonomy/field-mapping →
   Extraction/judgment rules), mirroring the three audits that preceded
   PR-C's implementation, before any Personal/Action Meaning generation
   code is written.
4. A decision on whether `historyTheme`'s existing `consultation_axis`-based
   boost signal is folded into this new contract, superseded by it, or
   kept as a Recommendation-only concern separate from Personal Meaning --
   this is a Mother Ship product/architecture decision, not inferred here.

## 11. Critical Questions -- Answers

**Q1.** No. No field in current data proves a relationship between
Structured Consultation Context and Shrine Evidence. `relevantToConsultation`
/`relevantToVisit` are hardcoded `null` everywhere (confirmed by full-repo
grep); all factual Shrine Evidence fields are generated shrine-side only,
by explicit design (`_build_fact`'s own docstring).

**Q2.** Not applicable -- no such pairing exists today. The closest partial
signal is `historyTheme`'s Recommendation-side `history_theme_candidate_boost`
gate (tied to `consultation_axis`, not to `PremiumMeaningShrineEvidence`,
and not to any Consultation Meaning v1 signal type) -- see §8/§9 for why it
does not qualify.

**Q3.** See §10 (recorded, not designed): a dedicated relevance-judgment
producer and a per-signal-granular shape, developed through its own design
sequence.

**Q4.** No. `personalMeaningValid` requires `shrineEvidenceValid`, which
requires `relevantToConsultation === true`, which never occurs in current
data. A correct implementation would be permanently inert; an incorrect one
would violate the documented presence-vs-relevance boundary.

**Q5.** No, for the same reason plus a second, independent blocker:
`actionMeaningValid` also requires `relevantToVisit === true`, likewise
never produced anywhere.

**Q6.** Structurally yes -- `deepReasonValid` and `personalMeaningValid` are
independent fields in `PremiumMeaningValidity` with no formula dependency on
each other (they share only that both ultimately read
`structuredConsultationContextValid`). But in practice both are blocked
today for their own separate reasons: Deep Reason lacks a *proof* linking
Consultation Context to Recommendation Evidence (PR-D's finding); Personal/
Action Meaning lacks a relevance *producer* at all (this audit's finding).
"Independent" means independently blocked, not that one unblocks the other.

## 12. Final Verdict

# BLOCKED

Current data cannot safely support Personal Meaning or Action Meaning
generation. No Shrine Evidence field is classified SAFE_FOR_PERSONAL_MEANING
or SAFE_FOR_ACTION_MEANING; the two fields designed to carry that judgment
(`relevantToConsultation`, `relevantToVisit`) have zero producers anywhere
in the codebase, so `personalMeaningValid`/`actionMeaningValid` can never be
`true` under current production data. Every existing production narrative
path that currently occupies these UI slots is a generic, need_tag-keyed or
shrine-name-keyed template that would violate PR-E's own stated
constraints if reused.

## Recommended Next Mother Ship Decision

PR-E implementation should not proceed. The next decision point is whether
to commission a dedicated **Shrine Knowledge Relevance Judgment Contract
v1** design sequence (Contract → field/signal mapping → judgment rules),
analogous to the three audits that preceded PR-C, before any Personal
Meaning / Action Meaning implementation work is scheduled.
