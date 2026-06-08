"use client";

import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import { trackShrineInteraction } from "@/lib/api/shrineInteractions";

type Props = {
  href: string;
  label: string;
  shrineId?: number | string | null;
  ctx?: string | null;
  tid?: string | number | null;
  historyTheme?: string | null;
  className?: string;
};

export default function GoogleMapRouteLink({
  href,
  label,
  shrineId = null,
  ctx = null,
  tid = null,
  historyTheme = null,
  className,
}: Props) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={className}
      onClick={() => {
        trackSearchEvent("route_open", {
          source: "shrine_detail",
          routeTarget: "google_maps",
          shrineId: shrineId ?? undefined,
          threadId: tid != null ? String(tid) : undefined,
          historyTheme: historyTheme ?? undefined,
          ctx,
        });
        const shrineIdNumber = shrineId != null ? Number(shrineId) : null;

        if (shrineIdNumber != null && Number.isFinite(shrineIdNumber) && shrineIdNumber > 0) {
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
          });
        }
      }}
    >
      {label}
    </a>
  );
}
