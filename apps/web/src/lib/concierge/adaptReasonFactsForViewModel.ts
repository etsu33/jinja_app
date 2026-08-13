import type { ConciergeReasonFacts } from "@/lib/api/concierge";

export type RecommendationReasonViewFacts = {
  primary_axis?: "need" | "benefit" | "feature" | "element" | "distance" | "popularity" | "fallback" | null;
  matched_need_tags?: string[] | null;
  matched_element?: string | null;
  shrine_benefit?: string | null;
  shrine_feature?: string | null;
  visit_fit?: string | null;
  fallback_reason?: string | null;
  primary_fact_type?: string | null;
  primary_fact_label?: string | null;
};

/**
 * Adapts the Backend wire fact chosen by Backend into existing display slots.
 * It never compares scores, infers from array position, or duplicates Backend type priority.
 */
export function adaptReasonFactsForViewModel(reasonFacts: ConciergeReasonFacts | null | undefined): RecommendationReasonViewFacts | null {
  if (!Array.isArray(reasonFacts)) return null;
  const primary = reasonFacts.find((fact) => fact.is_primary === true);
  if (!primary) return null;

  const base = {
    primary_fact_type: primary.type,
    primary_fact_label: primary.label,
  } satisfies RecommendationReasonViewFacts;

  switch (primary.type) {
    case "element":
      return { ...base, primary_axis: "element", matched_element: primary.label };
    case "need_tag":
      return { ...base, primary_axis: "need", matched_need_tags: [primary.label] };
    case "user_selected_tag":
      return { ...base, primary_axis: "need", matched_need_tags: [primary.label] };
    case "goriyaku_tag":
      return { ...base, primary_axis: "benefit", shrine_benefit: primary.label };
    case "history_theme":
    case "text_hint":
      return { ...base, primary_axis: "feature", shrine_feature: primary.label };
    case "visit_style":
      return { ...base, primary_axis: "feature", visit_fit: primary.label };
    case "fallback":
      return { ...base, primary_axis: "fallback", fallback_reason: primary.label };
    default:
      return null;
  }
}
