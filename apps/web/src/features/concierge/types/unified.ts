import type { ConciergeThread, ConciergeRecommendation, ConciergeNeed } from "@/lib/api/concierge";
import type { ConciergeMonthDirection } from "../../../../../../packages/shared/monthDirection";

export type StopReason = "design" | "paywall" | null;

export type ConciergeModeSignal = {
  flow: "A" | "B";
  weights: { element: number; need: number; popular: number };
  astro_bonus_enabled: boolean;
  description?: string;
  ui_label_ja?: string;
  ui_note_ja?: string;
};

export type ConciergeSignals = {
  mode?: ConciergeModeSignal;
  astro?: unknown;
  need_tags?: unknown;
  user_filters?: unknown;
};

export type ViewerPlan = "anonymous" | "free" | "premium";

export type UnifiedConciergeResponse = {
  ok: boolean;
  stop_reason: StopReason;
  reply?: string | null;
  plan?: ViewerPlan | null;
  remaining?: number | null;
  limit?: number | null;
  limitReached?: boolean;
  thread_id?: string | null;

  thread?: ConciergeThread | null;

  /** 今月の方角（生年月日を登録したログイン中の人だけ。並び順には使わない）。packages/shared/monthDirection.ts */
  month_direction?: ConciergeMonthDirection | null;

  data: {
    recommendations: ConciergeRecommendation[];
    recommendations_v2?: ConciergeRecommendation[];
    _need?: ConciergeNeed;
    _astro?: any;
    _signals?: ConciergeSignals;
  };
};
