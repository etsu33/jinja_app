"use client";

import { useEffect, useRef } from "react";
import { track } from "@/lib/analytics/track";

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
    track("shrine_detail_view", {
      shrineId,
      ctx,
      tid,
    });
  }, [shrineId, ctx, tid]);

  return null;
}
