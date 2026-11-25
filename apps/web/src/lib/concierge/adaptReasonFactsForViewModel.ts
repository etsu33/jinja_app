import type { ConciergeReasonFacts } from "@/lib/api/concierge";
import { toDisplayLabel } from "./displayLabel";

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
  /**
   * 表示用の名前(label_ja、無ければ label)。英字・数字・記号だけの内部名は null。
   * 比較や判定には使わない(判定は primary_fact_type / shrine_benefit などを使う)。
   */
  primary_fact_display_label?: string | null;
  /** goriyaku_tag Primary の表示用の名前。shrine_benefit は判定用として値を変えない。 */
  shrine_benefit_display_label?: string | null;
  /** history_theme / text_hint Primary の表示用の名前。shrine_feature は判定用として値を変えない。 */
  shrine_feature_display_label?: string | null;
  /** visit_style Primary の表示用の名前。常に null(下の NAME_FREE_PRIMARY_FACT_TYPES を参照)。 */
  visit_fit_display_label?: string | null;
};

/**
 * 名前を文に入れない Primary の種類。
 * - element: 日本語名「生年月日との相性」を入れると「生年月日から見た「生年月日との相性」の要素との相性」と重なる。
 * - visit_style: 日本語名「参拝スタイル」は分類名で、中身(静か・自然など)を表さない。
 * - fallback: 日本語名「近い候補」は単語だけで、文にならない。
 * これらは、名前を使わない既存の文に任せる。
 */
export const NAME_FREE_PRIMARY_FACT_TYPES: ReadonlySet<string> = new Set(["element", "visit_style", "fallback"]);

/**
 * Adapts the Backend wire fact chosen by Backend into existing display slots.
 * It never compares scores, infers from array position, or duplicates Backend type priority.
 */
export function adaptReasonFactsForViewModel(reasonFacts: ConciergeReasonFacts | null | undefined): RecommendationReasonViewFacts | null {
  if (!Array.isArray(reasonFacts)) return null;
  const primary = reasonFacts.find((fact) => fact.is_primary === true);
  if (!primary) return null;

  const displayLabel = NAME_FREE_PRIMARY_FACT_TYPES.has(primary.type)
    ? null
    : toDisplayLabel(primary.label_ja, primary.label);
  const base = {
    primary_fact_type: primary.type,
    primary_fact_label: primary.label,
    primary_fact_display_label: displayLabel,
  } satisfies RecommendationReasonViewFacts;

  switch (primary.type) {
    case "element":
      return { ...base, primary_axis: "element", matched_element: primary.label };
    case "need_tag":
      return { ...base, primary_axis: "need", matched_need_tags: [primary.label] };
    case "user_selected_tag":
      return { ...base, primary_axis: "need", matched_need_tags: [primary.label] };
    case "goriyaku_tag":
      return {
        ...base,
        primary_axis: "benefit",
        shrine_benefit: primary.label,
        shrine_benefit_display_label: displayLabel,
      };
    case "history_theme":
    case "text_hint":
      return {
        ...base,
        primary_axis: "feature",
        shrine_feature: primary.label,
        shrine_feature_display_label: displayLabel,
      };
    case "visit_style":
      return { ...base, primary_axis: "feature", visit_fit: primary.label, visit_fit_display_label: null };
    case "fallback":
      return { ...base, primary_axis: "fallback", fallback_reason: primary.label };
    default:
      return null;
  }
}
