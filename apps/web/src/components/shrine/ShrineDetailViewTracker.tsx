"use client";

import { useEffect, useRef } from "react";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import { trackShrineInteraction } from "@/lib/api/shrineInteractions";

type Props = {
  shrineId: number;
  ctx?: "map" | "concierge" | null;
  tid?: string | null;
};

export function ShrineDetailViewTracker({ shrineId, ctx = null, tid = null }: Props) {
  const trackedRef = useRef(false);

  useEffect(() => {
    if (trackedRef.current) return;

    trackedRef.current = true;
    const source = ctx === "map" ? "map" : ctx === "concierge" ? "concierge_result" : "shrine_detail";

    trackSearchEvent("shrine_detail_view", {
      source,
      shrineId,
      threadId: tid ?? undefined,
    });

    void trackShrineInteraction({
      shrineId,
      actionType: "detail_view",
      source,
      threadId: tid,
      metadata: {
        event: "shrine_detail_view",
        ctx,
      },
    });
  }, [shrineId, ctx, tid]);

  return null;
}
