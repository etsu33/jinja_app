"use client";

import { useEffect, useRef } from "react";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import { trackShrineInteraction } from "@/lib/api/shrineInteractions";
import {
  recommendationAnalyticsProperties,
  type RecommendationAnalyticsProvenance,
} from "../../../../../packages/shared/recommendationAnalyticsProvenance";

type Props = {
  shrineId: number;
  ctx?: "map" | "concierge" | null;
  tid?: string | null;
  analyticsProvenance?: RecommendationAnalyticsProvenance;
  recommendationInstanceId?: string | null;
};

export function ShrineDetailViewTracker({
  shrineId,
  ctx = null,
  tid = null,
  analyticsProvenance,
  recommendationInstanceId = null,
}: Props) {
  const trackedRef = useRef(false);

  useEffect(() => {
    if (trackedRef.current) return;

    trackedRef.current = true;
    const source = ctx === "map" ? "map" : ctx === "concierge" ? "concierge_result" : "shrine_detail";

    trackSearchEvent("shrine_detail_view", {
      source,
      shrineId,
      threadId: tid ?? undefined,
      recommendationInstanceId,
      ...(analyticsProvenance ? recommendationAnalyticsProperties(analyticsProvenance) : {}),
    });

    void trackShrineInteraction({
      shrineId,
      actionType: "detail_view",
      source,
      threadId: tid,
      metadata: {
        event: "shrine_detail_view",
        ctx,
        recommendation_instance_id: recommendationInstanceId,
        ...(analyticsProvenance ? recommendationAnalyticsProperties(analyticsProvenance) : {}),
      },
    });
  }, [shrineId, ctx, tid, analyticsProvenance, recommendationInstanceId]);

  return null;
}
