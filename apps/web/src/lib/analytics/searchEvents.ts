import { getAnalyticsProvider } from "@/lib/analytics/providers";

export type SearchAnalyticsEventName =
  | "shrine_search"
  | "map_search"
  | "route_open"
  | "visit_done"
  | "reflection_prompt_view"
  | "reflection_saved"
  | "shrine_detail_transition"
  | "concierge_result_impression"
  | "recommendation_quality"
  | "action_suggestion_view"
  | "action_suggestion_click"
  | "action_suggestion_reflection_preview_view"
  | "action_started"
  | "action_completed"
  | "action_done"
  | "action_suggestion_preview_view"
  | "primary_action_click"
  | "secondary_action_click"
  | "empty_state_view"
  | "add_shrine_click"
  | "shrine_card_click"
  | "shrine_detail_view";

type SearchAnalyticsPrimitive = string | number | boolean | null | undefined;

export type SearchAnalyticsPayload = {
  source?: "concierge_result" | "shrine_detail" | "map" | "shrines" | null;
  analyticsSessionId?: string | null;
  threadId?: string | null;
  resultSetId?: string | null;
  shrineId?: number | string | null;
  recommendationRank?: number | null;
  /**
   * 遷移元URLの `ctx` クエリパラメータから導出する（`ctx === "concierge"` の場合 `"need"`）。
   * `ctx` の値自体をpayloadへ直接送信しない。
   */
  mode?: "need" | "compat" | null;
  accessLevel?: "anonymous" | "free" | "premium" | null;
  shrine_data_rate?: number | null;
  consultation_reflection_rate?: number | null;
  fallback_reason_rate?: number | null;
  evidence_rate?: number | null;
  action_grounding_rate?: number | null;
  is_ai_inference_only?: boolean | null;
  fallback_source?: string | null;
  primaryReasonSource?: string | null;
  isFallbackRecommendation?: boolean | null;
  actionSource?: string | null;
  actionSourceKeys?: string | null;
  position?: "hero_primary" | "compact" | "map" | "list" | null;
  firstClick?: boolean | null;
  query?: string | null;
  routeTarget?: "google_maps" | "internal_map" | null;
  historyTheme?: string | null;
  consultationAxis?: string | null;
  actionTheme?: string | null;
  /**
   * 実際のReflection入力UI（reflection_prompt_view / reflection_saved）でのみ使用する。
   * どのフォーム構造で入力させたかを表す。
   */
  reflectionFormType?: "one_line" | "mood_delta" | "theme_reflection" | null;
  /**
   * 実際のReflection入力UI（reflection_prompt_view / reflection_saved）でのみ使用する。
   * Reflectionがどの文脈で表示されたかを表す。
   */
  reflectionContext?: "visit_done" | "mypage" | "night_reflection" | null;
  /**
   * Action Suggestion v4のreflection_prompt.prompt_typeをそのまま転記する。
   * action_suggestion_preview_view / action_suggestion_reflection_preview_viewでのみ使用する。
   */
  actionPromptType?: "before_visit" | "after_visit" | "decision" | "emotion" | "constraint" | null;
  answerLength?: number | null;
  moodBefore?: string | null;
  moodAfter?: string | null;
  [key: string]: SearchAnalyticsPrimitive;
};

export type SerializedSearchAnalyticsPayload = Record<string, string | number | boolean>;

function isSearchAnalyticsPrimitive(value: unknown): value is SearchAnalyticsPrimitive {
  return (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean" ||
    value === null ||
    value === undefined
  );
}

export function serializeSearchAnalyticsPayload(
  payload: SearchAnalyticsPayload = {},
): SerializedSearchAnalyticsPayload {
  const serialized: SerializedSearchAnalyticsPayload = {};

  for (const [key, value] of Object.entries(payload)) {
    if (value === null || value === undefined) continue;
    if (!isSearchAnalyticsPrimitive(value)) continue;

    serialized[key] = value;
  }

  return serialized;
}

export function trackSearchEvent(eventName: SearchAnalyticsEventName, payload: SearchAnalyticsPayload = {}) {
  const serializedPayload = serializeSearchAnalyticsPayload(payload);

  try {
    getAnalyticsProvider().track(eventName, serializedPayload);
  } catch (error) {
    if (process.env.NODE_ENV === "development") {
      console.warn("[search analytics]", eventName, serializedPayload, error);
    }
  }
}

export type RecommendationQualityAnalyticsPayload = {
  source: "concierge_result" | "shrine_detail";
  threadId?: string | null;
  shrineId?: number | string | null;
  recommendationRank?: number | null;
  resultSetId?: string | null;
  accessLevel?: "anonymous" | "free" | "premium" | null;
  shrine_data_rate?: number | null;
  consultation_reflection_rate?: number | null;
  fallback_reason_rate?: number | null;
  evidence_rate?: number | null;
  action_grounding_rate?: number | null;
  is_ai_inference_only?: boolean | null;
  fallback_source?: string | null;
  primaryReasonSource?: string | null;
  isFallbackRecommendation?: boolean | null;
  actionSource?: string | null;
  actionSourceKeys?: string | null;
  // docs/audit/knowledge-recommendation-analytics-contract.md 提案の最小Contract。
  // Backend recommendation_reason_quality（PR2382のbuild_shrine_reason_provenance()を
  // 再利用して算出）から受け取るのみで、Web側では再計算しない。
  knowledge_backing_class?:
    | "FULLY_KNOWLEDGE_BACKED"
    | "PARTIALLY_KNOWLEDGE_BACKED"
    | "LEGACY_BACKED"
    | "UNKNOWN"
    | null;
  deity_knowledge_used?: boolean | null;
  history_knowledge_used?: boolean | null;
};

export function trackRecommendationQuality(payload: RecommendationQualityAnalyticsPayload) {
  trackSearchEvent("recommendation_quality", payload);
}
