// apps/web/src/lib/concierge/buildDeepRecommendationReason.ts
//
// Deep Recommendation Reason v1 (PR-D).
//
// Answers only "なぜ今回の相談に対して、この神社なのか" -- pairs the
// Structured Consultation Context (PR-C: situationSignals /
// desiredOutcomeSignals / explicitConstraintSignals) with Recommendation
// Evidence (reason facts), both already carried on PremiumMeaningContext.
// Does NOT judge "この神社を、今回の自分にとってどう捉えられるか" (Personal
// Meaning / PR-E) or "参拝するとしたら、何を意識して向き合えるか" (Action
// Meaning / PR-E) -- neither is implemented here.
//
// This module does not redefine the PR-C signal taxonomy or the
// Recommendation Evidence fact shape -- it imports both from
// ./premiumMeaningContext and normalizes only what it actually used into
// DeepRecommendationReason's own sources shape.

import type {
  DesiredOutcomeSignal,
  ExplicitConstraintSignal,
  PremiumMeaningContext,
  PremiumMeaningReasonFact,
  SituationSignal,
} from "./premiumMeaningContext";

export type DeepRecommendationReasonConsultationSource = {
  category: "situation" | "desired_outcome" | "explicit_constraint";
  type: string;
  evidence: string[];
};

export type DeepRecommendationReasonRecommendationSource = {
  role: "primary" | "secondary";
  text: string;
};

export type DeepRecommendationReason = {
  lines: string[];
  sources: {
    consultation: DeepRecommendationReasonConsultationSource[];
    recommendation: DeepRecommendationReasonRecommendationSource[];
  };
};

export type DeepRecommendationReasonResult = DeepRecommendationReason | null;

function clean(value?: string | null): string {
  return (value ?? "").trim();
}

type ConsultationSignal = SituationSignal | DesiredOutcomeSignal | ExplicitConstraintSignal;

type UsableSignal = {
  category: DeepRecommendationReasonConsultationSource["category"];
  type: string;
  evidenceTexts: string[];
};

const CATEGORY_NOUN: Record<UsableSignal["category"], string> = {
  situation: "状態",
  desired_outcome: "ご希望",
  explicit_constraint: "状況",
};

function evidenceTextsOf(signal: ConsultationSignal): string[] {
  return signal.evidence.map((e) => clean(e.text)).filter((t) => t.length > 0);
}

function toUsableSignals(
  category: UsableSignal["category"],
  signals: ConsultationSignal[],
): UsableSignal[] {
  const out: UsableSignal[] = [];
  for (const s of signals) {
    const evidenceTexts = evidenceTextsOf(s);
    if (evidenceTexts.length > 0) out.push({ category, type: s.type, evidenceTexts });
  }
  return out;
}

/**
 * Collects every consultation signal that actually carries usable
 * (non-empty) evidence, in a fixed, documented priority order: situation
 * (current state) before desired_outcome (goal) before explicit_constraint
 * (limiting condition) -- the same field order as
 * PremiumMeaningConsultationContext / StructuredConsultationContextV1.
 * This ordering is a builder-level display choice for selecting which
 * signal(s) to surface in `lines`; it is not the Extraction Contract's "no
 * primary/secondary ranking" rule, which governs extraction only.
 */
function collectUsableSignals(consultation: PremiumMeaningContext["consultation"]): UsableSignal[] {
  return [
    ...toUsableSignals("situation", consultation.situationSignals),
    ...toUsableSignals("desired_outcome", consultation.desiredOutcomeSignals),
    ...toUsableSignals("explicit_constraint", consultation.explicitConstraintSignals),
  ];
}

function toConsultationSource(signal: UsableSignal): DeepRecommendationReasonConsultationSource {
  return { category: signal.category, type: signal.type, evidence: signal.evidenceTexts };
}

function factLabel(fact: PremiumMeaningReasonFact | null | undefined): string {
  return clean(fact?.label);
}

function buildPrimaryLine(signal: UsableSignal, primaryFactLabel: string): string {
  const noun = CATEGORY_NOUN[signal.category];
  const quoted = signal.evidenceTexts[0];
  return `「${quoted}」という今回の${noun}に、この神社の「${primaryFactLabel}」という点が重なっています。`;
}

function buildSecondaryFactLine(signal: UsableSignal, secondaryFactLabel: string): string {
  const noun = CATEGORY_NOUN[signal.category];
  return `あわせて、「${secondaryFactLabel}」という点も、今回の${noun}と重なっています。`;
}

function buildSecondarySignalLine(signal: UsableSignal, primaryFactLabel: string): string {
  const noun = CATEGORY_NOUN[signal.category];
  const quoted = signal.evidenceTexts[0];
  return `あわせて、「${quoted}」という${noun}も、「${primaryFactLabel}」という点と重なっています。`;
}

/**
 * Builds Deep Recommendation Reason v1: 1-2 lines expressing why THIS
 * shrine was surfaced for THIS consultation, by explicitly pairing one
 * Structured Consultation Context signal's literal evidence with the
 * Recommendation Evidence fact(s) actually used. Every substantive claim
 * in `lines` traces to at least one entry in `sources.consultation` and
 * `sources.recommendation` by construction -- only the signal(s)/fact(s)
 * actually quoted are ever added to `sources`.
 *
 * Returns null when:
 * - context.validity.deepReasonValid is false;
 * - consultation evidence is insufficient (no signal carries a non-empty
 *   evidence span, even if signal entries exist);
 * - recommendation evidence is insufficient (no primary reason fact with a
 *   non-empty type and label);
 * - both exist -- the relationship is established structurally by pairing
 *   the most salient consultation signal with the primary Recommendation
 *   Evidence fact resolved for this same recommendation; no other
 *   compatibility judgment is specified by the Deep Recommendation Reason
 *   Output Contract v1, so this pairing is the only case this builder
 *   evaluates.
 *
 * Never returns an empty object and never generates fallback prose --
 * absence of a supported relationship is expressed as null, not as an
 * empty DeepRecommendationReason.
 */
export function buildDeepRecommendationReason(
  context: PremiumMeaningContext,
): DeepRecommendationReasonResult {
  if (!context.validity.deepReasonValid) return null;

  const usableSignals = collectUsableSignals(context.consultation);
  if (usableSignals.length === 0) return null;

  const primaryFact = context.recommendationEvidence.primaryReasonFact;
  const primaryFactType = clean(primaryFact?.type);
  const primaryFactLabel = factLabel(primaryFact);
  if (!primaryFact || !primaryFactType || !primaryFactLabel) return null;

  const [primarySignal, ...restSignals] = usableSignals;

  const lines: string[] = [buildPrimaryLine(primarySignal, primaryFactLabel)];
  const consultationSources: DeepRecommendationReasonConsultationSource[] = [
    toConsultationSource(primarySignal),
  ];
  const recommendationSources: DeepRecommendationReasonRecommendationSource[] = [
    { role: "primary", text: primaryFactLabel },
  ];

  const secondaryFact = context.recommendationEvidence.secondaryReasonFacts.find((fact) => {
    const label = factLabel(fact);
    return label.length > 0 && label !== primaryFactLabel;
  });

  if (secondaryFact) {
    const secondaryFactLabel = factLabel(secondaryFact);
    lines.push(buildSecondaryFactLine(primarySignal, secondaryFactLabel));
    recommendationSources.push({ role: "secondary", text: secondaryFactLabel });
  } else {
    const secondSignal = restSignals.find(
      (s) => s.type !== primarySignal.type || s.category !== primarySignal.category,
    );
    if (secondSignal) {
      lines.push(buildSecondarySignalLine(secondSignal, primaryFactLabel));
      consultationSources.push(toConsultationSource(secondSignal));
    }
  }

  return {
    lines,
    sources: {
      consultation: consultationSources,
      recommendation: recommendationSources,
    },
  };
}
