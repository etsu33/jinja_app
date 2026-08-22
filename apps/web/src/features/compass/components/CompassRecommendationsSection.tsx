// Reuses the existing ShrineCardCompact as-is (Phase 5 brief Section 11:
// "Do not invent a parallel shrine-card system solely for Compass"). This
"use client";

// component only supplies a contextual heading and maps already-Authority-
// decided fields (name/reason/address/distance) straight through -- it
// never re-decides or rewrites the shrine-specific reason.
import DetailSection from "@/components/shrine/DetailSection";
import ShrineCardCompact, { formatDistance } from "@/components/shrines/ShrineCardCompact";
import { trackCardEvent } from "@/lib/analytics/cardEvents";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import { useEffect, useRef } from "react";
import type { CompassRecommendation } from "../types";

export type CompassRecommendationsSectionProps = {
  recommendations: CompassRecommendation[];
  recommendationInstanceId: string;
};

export default function CompassRecommendationsSection({
  recommendations,
  recommendationInstanceId,
}: CompassRecommendationsSectionProps) {
  const trackedImpressionsRef = useRef(new Set<string>());

  useEffect(() => {
    recommendations.forEach((rec, index) => {
      const shrineId = rec.shrine_id ?? rec.id;
      if (shrineId == null) return;
      const rank = index + 1;
      const key = `${recommendationInstanceId}:${shrineId}:${rank}`;
      if (trackedImpressionsRef.current.has(key)) return;
      trackedImpressionsRef.current.add(key);

      trackCardEvent({
        event: "card_view",
        cardId: "shrine_compact",
        source: "compass",
        visibility: "visible",
        shrineId,
        recommendationRank: rank,
        recommendationInstanceId,
      });
    });
  }, [recommendations, recommendationInstanceId]);

  return (
    <DetailSection title="この方向の参拝候補" variant="secondary">
      <div className="space-y-3">
        {recommendations.map((rec, index) => {
          const shrineId = rec.shrine_id ?? rec.id;
          const rank = index + 1;
          const key = String(shrineId ?? rec.name ?? Math.random());
          const distanceM = typeof rec.distance_m === "number" ? rec.distance_m : null;
          // Result Experience audit (docs/audit/compass-result-experience.md
          // Section 26-3, P2 finding): distance_m already exists in the
          // Compass recommendation payload but ShrineCardCompact's own
          // address-vs-distance row (below) never shows it here, since
          // Compass candidates always carry a non-empty address
          // (concierge_chat_candidates.py requires it). No new data is
          // fetched or derived -- this only surfaces an existing field via
          // the opt-in distanceLabel prop, which no other caller sets.
          const formattedDistance = formatDistance(distanceM);
          return (
            <ShrineCardCompact
              key={key}
              name={String(rec.name ?? "")}
              address={typeof rec.address === "string" ? rec.address : null}
              distanceM={distanceM}
              distanceLabel={formattedDistance ? `約${formattedDistance}` : null}
              reason={typeof rec.reason === "string" ? rec.reason : null}
              href={
                shrineId != null
                  ? buildShrineHref(shrineId, {
                      ctx: "compass",
                      recommendationInstanceId,
                      recommendationRank: rank,
                    })
                  : null
              }
              onDetailClick={
                shrineId != null
                  ? () =>
                      trackSearchEvent("shrine_detail_transition", {
                        source: "compass",
                        shrineId,
                        recommendationRank: rank,
                        recommendationInstanceId,
                        position: "compact",
                      })
                  : undefined
              }
            />
          );
        })}
      </div>
    </DetailSection>
  );
}
