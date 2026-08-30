// apps/web/src/lib/concierge/premiumMeaningContext.ts
//
// PremiumMeaningContext -- Contract / Types Foundation (PR-A).
//
// Scope: type + pure Validity derivation only. This module does NOT read
// from any API response, does NOT change Basic Reason / shrine_meaning /
// action_meaning output, and is not wired into buildRecommendationReasonViewModel,
// buildReasonNarrative, or buildMeaningNarrative. Connecting real API data
// into a PremiumMeaningContext (API -> Context mapping) is PR-B, out of
// scope here. This module also does not implement any consultation
// interpretation or Shrine Evidence Relevance judgment logic -- Relevance
// is carried as an explicit input field, never derived from presence.
//
// Responsibility split (per Premium Meaning Architecture v1):
//   Deep Recommendation Reason answers "なぜ今回の相談に対して、この神社なのか"
//   Personal Meaning answers          "この神社を、今回の自分にとってどう捉えられるか"
//   Action Meaning answers            "参拝するとしたら、何を意識して向き合えるか"
//
// This Context expresses the material each Layer is allowed to use, and a
// Validity state each Layer can check before generating anything. It is
// intentionally NOT a copy of the API response shape -- fields are grouped
// by responsibility (consultation / recommendationEvidence / shrineEvidence
// / personalization / validity), and anything that is presentation text,
// internal ranking debug, or a legacy/hardcoded Frontend-only signal is
// excluded (see the "Excluded" list below).

/** A single Recommendation Evidence fact, shaped after the Backend wire
 * contract (ConciergeReasonFact) but narrowed to what Deep Recommendation
 * Reason may use as Evidence. Score/is_primary bookkeeping stays outside
 * the Context -- primary/secondary placement is expressed by which slot
 * of RecommendationEvidence a fact occupies, not by a flag on the fact. */
export type PremiumMeaningReasonFact = {
  type: string;
  label: string;
  evidence: string[];
};

/**
 * Backend-interpreted structured result of the consultation. Deliberately
 * opaque in PR-A: this audit's Source of Truth review did not confirm a
 * stable Backend/API contract field for named sub-concepts such as "state
 * tone" or "emotion intensity" -- the closest current source
 * (`interpret_consultation()`) only reaches the API response under a
 * debug-only key, not as a typed contract field. PR-A does not invent new
 * interpretation concepts; PR-B's API -> Context mapping decides what (if
 * anything) populates this, once a Source of Truth is confirmed. Its
 * presence (non-null) vs absence is still meaningful on its own: it is the
 * signal that the consultation has been structurally interpreted by the
 * Backend, not just classified into a need tag.
 */
export type InterpretedConsultationContext = Record<string, unknown>;

export type PremiumMeaningConsultationContext = {
  /** REQUIRED field slot. Value is nullable when no need tag resolved. */
  primaryNeed: string | null;
  secondaryNeed?: string | null;
  /** REQUIRED field slot. Value is nullable only in states resolveInputType
   * cannot classify; current callers always resolve "need" | "compat". */
  mode: string | null;
  /** REQUIRED field slot (must exist), value nullable. Backend-interpreted
   * structured result only -- never raw free_text. See
   * InterpretedConsultationContext doc for why this stays opaque in PR-A. */
  interpretedContext: InterpretedConsultationContext | null;
  explicitPurpose?: string | null;
  visitPreferences?: unknown | null;
};

export type PremiumMeaningRecommendationEvidence = {
  /** REQUIRED field slot; value nullable (no Backend fact resolved). */
  primaryReasonFact: PremiumMeaningReasonFact | null;
  /** REQUIRED field slot; empty array allowed. */
  secondaryReasonFacts: PremiumMeaningReasonFact[];
};

/** Provenance/coverage summary for Shrine Evidence. Carries only the
 * boolean Fact-ready state (verification_status gate), never the raw
 * ShrineKnowledgeSource records themselves. */
export type ShrineEvidenceVerificationMetadata = {
  deityVerified: boolean;
  historyVerified: boolean;
};

export type PremiumMeaningShrineEvidence = {
  /** REQUIRED. */
  shrineId: number;
  deity?: string | null;
  history?: string | null;
  historyTheme?: string | null;
  originSummary?: string | null;
  placeContext?: string | null;
  culturalStatus?: string[] | null;
  lineage?: string | null;
  goriyaku?: string[] | null;
  tradition?: string | null;
  verificationMetadata?: ShrineEvidenceVerificationMetadata | null;
  /**
   * REQUIRED field slot; value nullable. Whether Shrine Specific Evidence
   * (deity / history / placeContext) has been judged -- by a Relevance
   * judgment NOT implemented in PR-A -- to actually connect to THIS
   * consultation's User Context, as distinct from merely existing for the
   * shrine. Presence of deity/history/placeContext alone must never imply
   * this is true; null/false means "not yet judged relevant" and is
   * treated as not relevant for Personal Meaning Validity purposes.
   */
  relevantToConsultation: boolean | null;
  /**
   * REQUIRED field slot; value nullable. Whether Shrine Context has been
   * judged -- again, no judgment logic in PR-A -- relevant to the act of
   * visiting (Action Meaning's "Relevant Shrine Context"), as a signal
   * distinct from `relevantToConsultation`. Kept separate so
   * actionMeaningValid is not a tautological re-use of the boolean that
   * already gates personalMeaningValid.
   */
  relevantToVisit: boolean | null;
};

export type PremiumMeaningPersonalization = {
  birthdate?: string | null;
  astroElement?: string | null;
  profileContext?: unknown | null;
  direction?: string | null;
};

export type PremiumMeaningValidity = {
  /** Structured Consultation Context VALID: primaryNeed alone is NOT
   * sufficient (see isConsultationContextValid doc). */
  consultationContextValid: boolean;
  /** Structured User Context VALID for Personal Meaning's formula. Equal to
   * consultationContextValid -- this Contract treats "User Context" and
   * "Consultation Context" as the same underlying concept; kept as its own
   * field because the original PR-A Required Context Fields list named it
   * explicitly. */
  userContextValid: boolean;
  recommendationEvidenceValid: boolean;
  /** Shrine Specific Evidence PRESENT: deity/history/placeContext exist.
   * Presence alone, NOT Relevance -- must never gate Personal Meaning by
   * itself. */
  shrineEvidencePresent: boolean;
  /** Relevant Shrine Specific Evidence VALID: PRESENT and explicitly judged
   * relevantToConsultation. This is the field Personal Meaning's formula
   * actually uses. */
  shrineEvidenceValid: boolean;
  /** Relevant Shrine Context VALID for Action Meaning: PRESENT and
   * explicitly judged relevantToVisit. Distinct signal from
   * shrineEvidenceValid -- see relevantToVisit doc. */
  relevantShrineContextValid: boolean;
  deepReasonValid: boolean;
  personalMeaningValid: boolean;
  actionMeaningValid: boolean;
};

export type PremiumMeaningContext = {
  shrineId: number;
  consultation: PremiumMeaningConsultationContext;
  recommendationEvidence: PremiumMeaningRecommendationEvidence;
  shrineEvidence: PremiumMeaningShrineEvidence;
  personalization: PremiumMeaningPersonalization;
  validity: PremiumMeaningValidity;
};

function clean(value?: string | null): string {
  return (value ?? "").trim();
}

/**
 * Structured Consultation Context VALID: a resolved primaryNeed alone is
 * NOT sufficient -- a Backend-interpreted structured payload
 * (interpretedContext) must also be present. This is what lets two
 * requests carrying the same primaryNeed diverge in Validity depending on
 * consultation context, once PR-B actually populates interpretedContext;
 * PR-A implements no interpretation logic itself, only this Contract-level
 * distinction.
 */
function isConsultationContextValid(consultation: PremiumMeaningConsultationContext): boolean {
  return Boolean(clean(consultation.primaryNeed)) && consultation.interpretedContext !== null;
}

/**
 * Shrine Specific Evidence PRESENT (structural only): at least one field of
 * Shrine Specificity MEDIUM or higher exists. goriyaku tags alone are
 * shared across many shrines (LOW specificity) and do not satisfy "他神社
 * へ簡単に置換できない"; deity / history (HIGH) and placeContext (MEDIUM)
 * are the fields this Contract treats as Shrine Specific Evidence.
 * PRESENCE only -- callers must not treat this as Validity by itself.
 */
function isShrineEvidencePresent(shrineEvidence: PremiumMeaningShrineEvidence): boolean {
  return Boolean(clean(shrineEvidence.deity) || clean(shrineEvidence.history) || clean(shrineEvidence.placeContext));
}

/**
 * Relevant Shrine Specific Evidence VALID: PRESENT is necessary but not
 * sufficient -- `relevantToConsultation` must also be explicitly true.
 * PR-A carries this as an input field only; no Relevance judgment logic is
 * implemented here.
 */
function isShrineEvidenceValid(shrineEvidence: PremiumMeaningShrineEvidence): boolean {
  return isShrineEvidencePresent(shrineEvidence) && shrineEvidence.relevantToConsultation === true;
}

/**
 * Relevant Shrine Context VALID (Action Meaning's Shrine Context signal):
 * PRESENT and explicitly judged `relevantToVisit`. Kept independent of
 * `relevantToConsultation` so Action Meaning's formula does not collapse
 * into a tautological re-use of Personal Meaning's gate.
 */
function isRelevantShrineContextValid(shrineEvidence: PremiumMeaningShrineEvidence): boolean {
  return isShrineEvidencePresent(shrineEvidence) && shrineEvidence.relevantToVisit === true;
}

/**
 * Recommendation Evidence VALID (per Evidence Validity Rules): a primary
 * reason fact resolved by the Backend must be present.
 */
function isRecommendationEvidenceValid(recommendationEvidence: PremiumMeaningRecommendationEvidence): boolean {
  const fact = recommendationEvidence.primaryReasonFact;
  return Boolean(fact && clean(fact.type) && clean(fact.label));
}

/**
 * Derives the full Validity state from the rest of a PremiumMeaningContext.
 *
 * Formulas (fixed by PR-A spec, refined per Mother Ship review):
 *   deepReasonValid      = consultationContextValid + Valid primary Recommendation Evidence
 *   personalMeaningValid = userContextValid + Relevant Shrine Specific Evidence (shrineEvidenceValid)
 *   actionMeaningValid   = personalMeaningValid + Relevant Shrine Context (relevantShrineContextValid)
 *
 * "Valid Consultation Context" and "Valid User Context" both resolve via
 * isConsultationContextValid -- this Contract treats them as the same
 * underlying concept, exposed as two fields (consultationContextValid,
 * userContextValid) because the original Required Context Fields list
 * named userContextValid explicitly.
 *
 * actionMeaningValid intentionally does NOT reuse shrineEvidenceValid --
 * relevantShrineContextValid is a distinct signal (relevantToVisit, not
 * relevantToConsultation) so this is not a tautological AND of the same
 * boolean that already gates personalMeaningValid.
 *
 * Pure function: reads only the fields already present on the Context
 * passed in. Does not fetch, infer, or call out to any API/Backend data,
 * and does not judge Relevance itself -- relevantToConsultation /
 * relevantToVisit must already be set on the input.
 */
export function computePremiumMeaningValidity(
  context: Pick<PremiumMeaningContext, "consultation" | "recommendationEvidence" | "shrineEvidence">,
): PremiumMeaningValidity {
  const consultationContextValid = isConsultationContextValid(context.consultation);
  const userContextValid = consultationContextValid;
  const recommendationEvidenceValid = isRecommendationEvidenceValid(context.recommendationEvidence);
  const shrineEvidencePresent = isShrineEvidencePresent(context.shrineEvidence);
  const shrineEvidenceValid = isShrineEvidenceValid(context.shrineEvidence);
  const relevantShrineContextValid = isRelevantShrineContextValid(context.shrineEvidence);

  const deepReasonValid = consultationContextValid && recommendationEvidenceValid;
  const personalMeaningValid = userContextValid && shrineEvidenceValid;
  const actionMeaningValid = personalMeaningValid && relevantShrineContextValid;

  return {
    consultationContextValid,
    userContextValid,
    recommendationEvidenceValid,
    shrineEvidencePresent,
    shrineEvidenceValid,
    relevantShrineContextValid,
    deepReasonValid,
    personalMeaningValid,
    actionMeaningValid,
  };
}
