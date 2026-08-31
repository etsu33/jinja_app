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
// ./premiumMeaningContext (the contract types stay exactly as approved).
//
// PR-D review correction (Mother Ship, PR #2655 CHANGES_REQUIRED):
//
// The first version of this builder produced `lines` whenever BOTH a
// Structured Consultation Context signal AND a valid primary
// Recommendation Evidence fact existed, using a generic template. That is
// a contract violation: presence of both is not proof they are RELATED,
// and the Output Contract v1 null rule requires null when "both exist but
// a supported relationship cannot be established."
//
// Investigation into whether current data can prove such a relationship
// (see PR #2655 review thread for the full writeup):
//
//   1. What Recommendation Evidence currently contains --
//      ConciergeReasonFact.type (backend: concierge_chat_ranking.
//      _build_reason_facts) is one of: history_theme / culture_translation
//      / user_selected_tag / need_tag / goriyaku_tag / text_hint /
//      visit_style / element / fallback. Its `evidence` field is a list of
//      synthetic bookkeeping strings ("score_element:2", "text_score:3",
//      "matched_need_tags", a raw need_tag/goriyaku_tag slug, etc.) --
//      never a literal free_text span.
//
//   2. Why that is insufficient for a safe relationship judgment -- every
//      one of those fact types is produced by a system architecturally
//      separate from Consultation Meaning v1 extraction
//      (consultation_meaning.py, PR-C): need_tag keyword matching
//      (domain/need_tags.py), consultation_axis keyword matching
//      (domain/consultation_axis.py, itself a THIRD independent keyword
//      vocabulary gating history_theme_candidate_boost), birthdate/element
//      compatibility, or explicit UI-selected goriyaku/visit-style
//      preferences. None of them read or reference
//      situationSignals/desiredOutcomeSignals/explicitConstraintSignals,
//      and no field anywhere carries a link back to a specific Consultation
//      Meaning v1 signal. Proving a relationship would require either
//      reading raw free_text and comparing it against evidence spans (bars:
//      "Do NOT use raw free_text"), or treating label/keyword overlap
//      across these disjoint vocabularies as meaningful (bars: "Do NOT
//      infer this from label similarity unless that mapping is already
//      part of the approved Recommendation contract" -- no such contract
//      exists).
//
//   3. Minimum additional stable contract that would be required -- a
//      Backend-emitted field (e.g. on ConciergeReasonFact, populated by
//      _build_reason_facts / _resolve_primary_reason) that records which
//      specific Consultation Meaning v1 signal(s) (by category + type)
//      actually contributed to that fact's ranking authority, following
//      the same evidence-required, no-inference discipline as PR-C's own
//      Extraction Contract. That contract does not exist yet and is not
//      designed here -- inventing one in this builder would be exactly the
//      workaround this review explicitly prohibits.
//
// Until that contract exists, this builder cannot honestly ever return a
// non-null DeepRecommendationReason, so it always returns null. The output
// types below are kept exactly as approved so a future implementation can
// fill in the real gate without changing the contract. There is no
// semantic pairing logic here: no "重なっています" relationship-generation
// template, no situation > desired_outcome > explicit_constraint priority,
// no automatic pairing, and no assumption that co-presence of a valid
// Structured Consultation Context and valid Recommendation Evidence
// proves relevance between them.

import type { PremiumMeaningContext } from "./premiumMeaningContext";

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

/**
 * Builds Deep Recommendation Reason v1. Always returns null -- see the
 * module doc above. No compatibility gate is implemented because no
 * existing, already-approved field proves a relationship between any
 * Recommendation Evidence fact and any Structured Consultation Context
 * signal; fabricating one (via label similarity, raw free_text, shrine
 * facts, or inference) is explicitly out of scope for this correction.
 */
export function buildDeepRecommendationReason(
  context: PremiumMeaningContext,
): DeepRecommendationReasonResult {
  void context;
  return null;
}
