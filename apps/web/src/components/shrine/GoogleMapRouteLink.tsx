"use client";

import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import { trackShrineInteraction } from "@/lib/api/shrineInteractions";
import { trackWebDirection } from "@/lib/analytics/directionEvents";
import type { DirectionRouteContext } from "@/lib/analytics/directionRouteContext";

type Props = {
  href: string;
  label: string;
  shrineId?: number | string | null;
  ctx?: string | null;
  tid?: string | number | null;
  historyTheme?: string | null;
  className?: string;
  directionRouteContext?: DirectionRouteContext | null;
};

export default function GoogleMapRouteLink({
  href,
  label,
  shrineId = null,
  ctx = null,
  tid = null,
  historyTheme = null,
  className,
  directionRouteContext = null,
}: Props) {
  let routeUrl: URL | null = null;
  try {
    routeUrl = new URL(href);
  } catch {
    // Invalid or missing external route URLs degrade to an unavailable notice.
  }
  if (!routeUrl || routeUrl.protocol !== "https:") {
    return <span role="status" className={className}>経路リンクを利用できません</span>;
  }

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={className}
      onClick={() => {
        if (directionRouteContext?.matched) {
          try {
            trackWebDirection("direction_match_route_clicked", {
              matched: true,
              candidate_position: directionRouteContext.candidatePosition,
            });
          } catch {
            // Analytics must never delay or block the external route navigation.
          }
        }
        try {
          trackSearchEvent("route_open", {
            source: "shrine_detail",
            routeTarget: "google_maps",
            shrineId: shrineId ?? undefined,
            threadId: tid != null ? String(tid) : undefined,
            historyTheme: historyTheme ?? undefined,
            ctx,
          });
        } catch {
          console.warn("route_analytics_delivery_failed");
        }
        const shrineIdNumber = shrineId != null ? Number(shrineId) : null;

        if (shrineIdNumber != null && Number.isFinite(shrineIdNumber) && shrineIdNumber > 0) {
          try {
            void trackShrineInteraction({
              shrineId: shrineIdNumber,
              actionType: "route_open",
              source: "shrine_detail",
              threadId: tid,
              metadata: {
                event: "route_open",
                routeTarget: "google_maps",
                historyTheme,
                ctx,
              },
            }).catch(() => console.warn("route_interaction_delivery_failed"));
          } catch {
            console.warn("route_interaction_delivery_failed");
          }
        }
      }}
    >
      {label}
    </a>
  );
}
