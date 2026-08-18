// Reuses the existing ShrineCardCompact as-is (Phase 5 brief Section 11:
// "Do not invent a parallel shrine-card system solely for Compass"). This
// component only supplies a contextual heading and maps already-Authority-
// decided fields (name/reason/address/distance) straight through -- it
// never re-decides or rewrites the shrine-specific reason.
import DetailSection from "@/components/shrine/DetailSection";
import ShrineCardCompact from "@/components/shrines/ShrineCardCompact";
import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import type { CompassRecommendation } from "../types";

export type CompassRecommendationsSectionProps = {
  recommendations: CompassRecommendation[];
};

export default function CompassRecommendationsSection({ recommendations }: CompassRecommendationsSectionProps) {
  return (
    <DetailSection title="この方向の参拝候補" variant="secondary">
      <div className="space-y-3">
        {recommendations.map((rec) => {
          const shrineId = rec.shrine_id ?? rec.id;
          const key = String(shrineId ?? rec.name ?? Math.random());
          return (
            <ShrineCardCompact
              key={key}
              name={String(rec.name ?? "")}
              address={typeof rec.address === "string" ? rec.address : null}
              distanceM={typeof rec.distance_m === "number" ? rec.distance_m : null}
              reason={typeof rec.reason === "string" ? rec.reason : null}
              href={shrineId != null ? buildShrineHref(shrineId, { ctx: "compass" }) : null}
            />
          );
        })}
      </div>
    </DetailSection>
  );
}
