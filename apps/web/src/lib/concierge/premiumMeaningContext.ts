// apps/web/src/lib/concierge/premiumMeaningContext.ts
//
// PremiumMeaningContext -- Contract / Types Foundation (PR-A, updated PR-C).
//
// Scope: type + pure Validity derivation only. This module does NOT read
// from any API response, does NOT change Basic Reason / shrine_meaning /
// action_meaning output, and is not wired into buildRecommendationReasonViewModel,
// buildReasonNarrative, or buildMeaningNarrative. Connecting real API data
// into a PremiumMeaningContext (API -> Context mapping) is
// mapConciergeResponseToPremiumMeaningContext.ts. This module does not
// implement any consultation extraction or Shrine Evidence Relevance
// judgment logic itself -- both are carried as explicit input, never
// derived from presence or computed here.
//
// PR-C update: the PR-A opaque `interpretedContext` placeholder is replaced
// by the approved Consultation Meaning v1 signals (situationSignals /
// desiredOutcomeSignals / explicitConstraintSignals), now that
// `consultation_meaning.py` provides a stable Source of Truth. Validity
// formulas are redefined accordingly -- see computePremiumMeaningValidity.
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
 * Consultation Meaning v1 (PR-C) signal shapes. Evidence-required,
 * unordered, no primary/secondary ranking, no confidence score -- see
 * docs/audit (Consultation Meaning Extraction Contract v1) for the full
 * design. These supersede the PR-A opaque `interpretedContext` placeholder
 * now that a stable Source of Truth exists (`consultation_meaning.py`,
 * exposed via the stable `consultation_meaning` API field, never `_debug`).
 */
export type SituationSignalType = "depleted" | "undecided" | "stalled";

export type DesiredOutcomeSignalType = "decide" | "clarify" | "progress" | "calm";

export type ExplicitConstraintSignalType = "time" | "money" | "other_person_availability";

export type ConsultationMeaningEvidence = { text: string };

export type SituationSignal = { type: SituationSignalType; evidence: ConsultationMeaningEvidence[] };

export type DesiredOutcomeSignal = {
  type: DesiredOutcomeSignalType;
  evidence: ConsultationMeaningEvidence[];
};

export type ExplicitConstraintSignal = {
  type: ExplicitConstraintSignalType;
  evidence: ConsultationMeaningEvidence[];
};

export type PremiumMeaningConsultationContext = {
  /** REQUIRED field slot. Value is nullable when no need tag resolved.
   * Recommendation-facing auxiliary use only (Deep Reason via
   * consultationContextValid, see below) -- MUST NOT satisfy Structured
   * Consultation Meaning validity (userContextValid). need_tag remains a
   * Recommendation Signal only. */
  primaryNeed: string | null;
  secondaryNeed?: string | null;
  /** REQUIRED field slot. Value is nullable only in states resolveInputType
   * cannot classify; current callers always resolve "need" | "compat".
   * Same Recommendation-facing-only restriction as primaryNeed. */
  mode: string | null;
  /** REQUIRED field slots; empty arrays allowed. Consultation Meaning v1 --
   * the sole basis for Structured Consultation Meaning validity
   * (userContextValid / consultationContextValid). Never derived from
   * need_tag, matched_need_tags, Recommendation results, Ranking output,
   * shrine data, or legacy InterpretationProfile fields. */
  situationSignals: SituationSignal[];
  desiredOutcomeSignals: DesiredOutcomeSignal[];
  explicitConstraintSignals: ExplicitConstraintSignal[];
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
  /** Structured Consultation Context VALID: derived ONLY from
   * situationSignals / desiredOutcomeSignals / explicitConstraintSignals
   * (see isStructuredConsultationContextValid doc). primaryNeed / mode are
   * explicitly NOT sufficient -- need_tag remains a Recommendation Signal
   * only and must never satisfy this. */
  consultationContextValid: boolean;
  /** Structured User Context VALID for Personal Meaning's formula. Equal to
   * consultationContextValid -- both resolve via the same
   * structuredConsultationContextValid computation; kept as its own field
   * because the original PR-A Required Context Fields list named it
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
 * Structured Consultation Context VALID (PR-C): true when at least one
 * Consultation Meaning v1 signal exists, across any of the three families.
 * primaryNeed / mode are deliberately excluded -- need_tag remains a
 * Recommendation Signal only and must never satisfy Structured Consultation
 * Meaning validity (Mother Ship rule, need_tag Responsibility Audit).
 */
function isStructuredConsultationContextValid(consultation: PremiumMeaningConsultationContext): boolean {
  return (
    consultation.situationSignals.length > 0 ||
    consultation.desiredOutcomeSignals.length > 0 ||
    consultation.explicitConstraintSignals.length > 0
  );
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
 * Formulas (PR-C, per approved Consultation Meaning v1 contract):
 *   structuredConsultationContextValid = situationSignals.length > 0 ||
 *     desiredOutcomeSignals.length > 0 || explicitConstraintSignals.length > 0
 *   consultationContextValid = structuredConsultationContextValid
 *   userContextValid         = structuredConsultationContextValid
 *   deepReasonValid          = consultationContextValid + Valid primary Recommendation Evidence
 *   personalMeaningValid     = userContextValid + Relevant Shrine Specific Evidence (shrineEvidenceValid)
 *   actionMeaningValid       = personalMeaningValid + Relevant Shrine Context (relevantShrineContextValid)
 *
 * primaryNeed / secondaryNeed / mode are NOT sufficient for
 * consultationContextValid or userContextValid -- need_tag remains a
 * Recommendation Signal only (Mother Ship rule, need_tag Responsibility
 * Audit). consultationContextValid and userContextValid both resolve via
 * the same structuredConsultationContextValid computation and are kept as
 * two fields because the original PR-A Required Context Fields list named
 * userContextValid explicitly.
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
  const structuredConsultationContextValid = isStructuredConsultationContextValid(context.consultation);
  const consultationContextValid = structuredConsultationContextValid;
  const userContextValid = structuredConsultationContextValid;
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
