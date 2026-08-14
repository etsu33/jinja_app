// apps/web/src/features/concierge/buildHeroConclusion.ts
//
// Recommendation Result Hero Card consolidation adapter
// (docs/product/recommendation-result-information-architecture.md §6, §13, §15 PR2).
//
// Pure presentation-layer composition ONLY. Every input string here has already been
// decided by Backend + the existing Reason V4 / reason_facts adapters
// (buildHeroReasonV4Sections.ts, buildRecommendationReasonViewModel.ts). This module
// never scores, re-prioritizes, invents a resolver, or promotes Explanation-only
// Knowledge facts -- it only decides which already-approved strings go into which of
// the two Hero blocks (Conclusion, Next Action), and in what order. Signal Authority
// stays entirely with Backend and those existing adapters
// (docs/product/recommendation-signal-authority.md).
//
// Fixed order for the Conclusion block (never derived from score/type):
//   1. Consultation understanding (interpretationText, when Reason V4 is structured)
//   2. Shrine-side supporting fact/selection meaning (factText, or primaryReason when
//      Reason V4 is not structured -- primaryReason already IS Backend's confirmed
//      "why this shrine" phrase, built from the reason_facts entry Backend itself
//      marked is_primary)
// Shrine fact never leads; it always follows the consultation-understanding line when
// one exists, so it reads as supporting evidence, not the headline claim.

export function buildHeroConclusionLines(params: {
  hasStructured: boolean;
  interpretationText: string | null;
  factText: string | null;
  primaryReason: string | null;
  fallbackText: string | null;
}): string[] {
  const candidates = params.hasStructured
    ? [params.interpretationText, params.factText]
    : [params.primaryReason, params.fallbackText];

  return candidates.filter((line): line is string => Boolean(line && line.trim()));
}

// Next Action block: merges the Reason V4 action advice (actionText, tied to the same
// interpretation/fact narrative above) with the Action Suggestion preview summary
// (actionSuggestionSummary, a separate Backend feature with its own grounding/
// actionSource -- already resolved and gated by the caller before this function sees
// it). Both are shown, verbatim, inside a single block instead of two independent
// cards; neither is dropped, re-worded, or re-attributed to the other's grounding.
// Exact duplicate strings are shown once.
export function buildHeroNextActionLines(params: {
  actionText: string | null;
  actionSuggestionSummary: string | null;
}): string[] {
  const lines = [params.actionText, params.actionSuggestionSummary].filter(
    (line): line is string => Boolean(line && line.trim()),
  );

  return Array.from(new Set(lines));
}
