import type { AccessLevel } from "../premium/accessLevel";
import type { CardId, CardVisibilityState } from "../premium/cardVisibility";
import { getAnalyticsProvider, type AnalyticsPayload } from "@/lib/analytics/providers";

export type AnalyticsSource = "concierge_result" | "compass" | "shrine_detail" | "billing_upgrade" | "mypage";

export type CtaType =
  | "organize"
  | "save"
  | "login_to_save"
  | "view_shrine_detail"
  | "open_route"
  | "compare_previous"
  | "continue_with_premium"
  | "filter_apply"
  | "back_to_entry"
  | "upgrade"
  | "checkout";

export type CardAnalyticsEvent =
  | "card_view"
  | "card_teaser_view"
  | "card_partial_view"
  | "card_cta_click"
  | "premium_preview_click"
  | "save_prompt_view"
  | "save_prompt_click";

export type CardAnalyticsPayload = {
  event: CardAnalyticsEvent;
  cardId: CardId;
  source: AnalyticsSource;
  accessLevel?: AccessLevel;
  visibility: CardVisibilityState;
  ctaType?: CtaType;
  shrineId?: number | string;
  historyTheme?: string | null;
  consultationAxis?: string | null;
  recommendationRank?: number;
  mode?: "need" | "compat";
  flow?: "A" | "B";
  hasBirthdate?: boolean;
  recommendationCount?: number;
  payloadSource?: "v2" | "fallback";
  // legacy compatibility: analyticsSessionId is injected by track.ts.
  sessionId?: string;
  threadId?: string;
  resultSetId?: string;
  // Result <-> Detail duplicate-exposure join key (with shrineId), Backend rid
  // persisted on the thread snapshot -- see docs/audit/
  // recommendation-result-detail-instrumentation-contract.md §7.
  recommendationInstanceId?: string | null;
};

type SerializedCardAnalyticsPayloadInput = Omit<CardAnalyticsPayload, "event">;

function serializeCardAnalyticsPayload(payload: SerializedCardAnalyticsPayloadInput): AnalyticsPayload {
  return Object.fromEntries(Object.entries(payload).filter(([, value]) => value !== undefined)) as AnalyticsPayload;
}

export function trackCardEvent(payload: CardAnalyticsPayload) {
  if (process.env.NODE_ENV !== "production") {
    console.log("CARD_ANALYTICS_EVENT", payload.event, payload);
  }

  const { event, ...rest } = payload;
  try {
    getAnalyticsProvider().track(event, serializeCardAnalyticsPayload(rest));
  } catch (error) {
    if (process.env.NODE_ENV === "development") {
      console.warn("CARD_ANALYTICS_EVENT_FAILED", event, error);
    }
  }
}
