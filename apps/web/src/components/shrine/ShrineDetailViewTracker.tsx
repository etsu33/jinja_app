"use client";

import { useEffect, useRef } from "react";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";

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
    trackSearchEvent("shrine_detail_view", {
      source: ctx === "map" ? "map" : ctx === "concierge" ? "concierge_result" : "shrine_detail",
      shrineId,
      threadId: tid ?? undefined,
    });
  }, [shrineId, ctx, tid]);

  return null;
}
