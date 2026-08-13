// apps/web/src/lib/api/concierge/types.ts

export type ConciergeThread = {
  id: number;
  title: string;
  last_message: string;
  last_message_at: string | null;
  message_count: number;
};

export type ConciergeMessage = {
  id: number;
  thread_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
};


export type ConciergeChatRequest = {
  query: string;
  thread_id?: number | string | null;
};

export type ConciergeChatData = {
  recommendations?: ConciergeRecommendation[];
  raw?: string;
  reply?: string;
  message?: string | null;

  _need?: ConciergeNeed;
  _astro?: any;
  _signals?: Record<string, unknown> | null;
};

export type ConciergeChatResponse = {
  ok: boolean;
  data?: ConciergeChatData;
  reply?: string;
  thread?: ConciergeThread;

  plan?: "anonymous" | "free" | "premium" | null;
  remaining?: number | null;
  limit?: number | null;
  limitReached?: boolean;
};

// Backend契約(GET /api/concierge-threads/{pk}/, ConciergeThreadDetailView)は
// id/title/last_message/last_message_at/message_countをトップレベルに返す
// フラットな構造であり、`thread`というネストしたキーは存在しない。
export type ConciergeThreadDetail = {
  id: number;
  title: string;
  last_message: string;
  last_message_at: string | null;
  message_count: number;
  messages: ConciergeMessage[];
  recommendations?: ConciergeRecommendation[];
  recommendations_v2?: ConciergeRecommendation[];
};

export type ConciergeNeed = {
  tags?: string[];
  hits?: Record<string, string[]>;
};

export type ConciergeBreakdown = {
  score_element: number; // 0/1/2
  score_need: number;
  score_popular: number; // 0..1
  score_total: number;
  weights: {
    element: number;
    need: number;
    popular: number;
  };
  matched_need_tags: string[];
};

export type KnowledgeBackingClass =
  | "FULLY_KNOWLEDGE_BACKED"
  | "PARTIALLY_KNOWLEDGE_BACKED"
  | "LEGACY_BACKED"
  | "UNKNOWN";

export type RecommendationReasonQuality = {
  shrine_data_rate?: number | null;
  consultation_reflection_rate?: number | null;
  fallback_reason_rate?: number | null;
  evidence_rate?: number | null;
  action_grounding_rate?: number | null;
  is_ai_inference_only?: boolean | null;
  fallback_source?: string | null;
  knowledge_backing_class?: KnowledgeBackingClass | null;
  deity_knowledge_used?: boolean | null;
  history_knowledge_used?: boolean | null;
};

export type ConciergeReasonFactAxis =
  | "need"
  | "benefit"
  | "feature"
  | "element"
  | "distance"
  | "popularity"
  | "fallback";

export type RecommendationReasonV4Fact = {
  label: string;
  name: string | null;
  deity: string | null;
  shrine_history: string | null;
  place_context: string | null;
  history_theme: string | null;
  goriyaku: string | null;
  visit_style_tags: string[];
  evidence: string[];
};

export type RecommendationReasonV4Interpretation = {
  theme: string;
  text: string;
};

export type RecommendationReasonV4Action = {
  text: string;
  source: string;
};

export type RecommendationReasonV4Detail = {
  version: "v4";
  reason_text: string;
  fact: RecommendationReasonV4Fact;
  interpretation: RecommendationReasonV4Interpretation;
  action: RecommendationReasonV4Action;
};

export type ConciergeReasonFact = {
  type: string;
  label: string;
  evidence: string[];
  score: number;
  is_primary?: boolean;
};

/** Backend wire contract. This is intentionally not the legacy aggregate object shape. */
export type ConciergeReasonFacts = ConciergeReasonFact[];

export type ConciergeRecommendation = {
  id?: number | null;
  shrine_id?: number | null;
  place_id?: string | null;
  /** Backend-issued per-request rid, reused as-is. Never generated/derived on Frontend. */
  recommendation_instance_id?: string | null;

  name: string;
  display_name?: string;

  address?: string | null;
  display_address?: string | null;

  location?: string | null;

  lat?: number | null;
  lng?: number | null;

  distance_m?: number | null;
  duration_min?: number | null;
  score?: number | null;
  popular_score?: number | null;
  breakdown?: ConciergeBreakdown | null;
  breakdown_detail?: any | null;

  action_state?: "reflected" | "visited" | "saved" | "none" | null;

  trust_metadata?: {
    rank_class?: string | null;
    cultural_status?: string[] | null;
    lineage?: string | null;
    origin_summary?: string | null;
  } | null;

  tags?: string[];
  deities?: string[];

  reason?: string | null;
  reason_source?: string | null;
  recommendation_reason_v4?: string | null;
  recommendation_reason_quality?: RecommendationReasonQuality | null;
  recommendation_reason_v4_detail?: RecommendationReasonV4Detail | null;

  bullets?: string[] | null;
  explanation?: {
    version?: number | null;
    summary?: string | null;
    reasons?: Array<{
      code?: string | null;
      label?: string | null;
      text?: string | null;
      strength?: "low" | "mid" | "high" | null;
      evidence?: Record<string, unknown> | null;
    }> | null;
    disclaimer?: string | null;
  } | null;

  reason_facts?: ConciergeReasonFacts | null;

  rank_explanation?: ConciergeRankExplanation | null;
  rank_comparison?: ConciergeRankComparison | null;

  photo_url?: string | null;
  is_dummy?: boolean;
  __dummy?: boolean;
  direction_reference?: import("../../../../../../packages/shared/directionReference").DirectionReference | null;
};

export type ConciergeRankExplanation = {
  version: number;
  summary?: string | null;
  primary_axis?: string | null;
  primary_axis_ja?: string | null;
  primary_label?: string | null;
  primary_label_ja?: string | null;
};

export type ConciergeRankComparison = {
  version: number;
  rank?: number;
  is_top?: boolean;
  top_name?: string | null;
  gap_from_top?: number;
  comparison_summary?: string | null;
};
