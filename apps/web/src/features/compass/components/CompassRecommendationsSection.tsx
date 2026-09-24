"use client";

// Compass Candidate Card v2. Reuses the existing ShrineCardCompact via its
// opt-in "candidate" layout (Phase 5 brief Section 11: "Do not invent a
// parallel shrine-card system solely for Compass"). This component only maps
// already-Authority-decided Public Contract fields straight through:
//
//   Meaning     -> reason_facts (primary only)
//   Shrine Fact -> shrine_facts
//   Distance    -> distance_m
//   Identity    -> shrine_id
//
// It never re-decides, re-ranks, summarizes, or falls back to legacy `reason`.
import DetailSection from "@/components/shrine/DetailSection";
import GoogleMapRouteLink from "@/components/shrine/GoogleMapRouteLink";
import ShrineCardCompact, { formatDistance, SHRINE_CARD_CANDIDATE_CTA_CLASS } from "@/components/shrines/ShrineCardCompact";
import { trackCardEvent } from "@/lib/analytics/cardEvents";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import { resolveShrineId } from "@/lib/identity/resolveShrineId";
import { buildGoogleMapsDirUrl } from "@/lib/maps/googleMaps";
import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import { useEffect, useRef } from "react";
import {
  resolveCompassCandidateMeaning,
  resolveCompassCandidateShrineFacts,
  type CompassCandidateMeaning,
  type CompassCandidateShrineFacts,
} from "../resolveCompassCandidatePresentation";
import type { CompassRecommendation } from "../types";

const SECTION_LABEL_CLASS = "text-[11px] font-semibold text-[var(--kt-color-text-secondary)]";

function CandidateMeaningBlock({ meaning }: { meaning: CompassCandidateMeaning }) {
  return (
    <div data-testid="compass-candidate-meaning">
      <p className={SECTION_LABEL_CLASS}>今のあなたとの接点</p>
      <p className="mt-1 break-words text-sm leading-6 text-[var(--kt-color-text-primary)]">
        {meaning.text}
        {meaning.isKamiMusubiInterpretation ? (
          <span className="text-xs text-[var(--kt-color-text-muted)]">（KAMI MUSUBIの解釈）</span>
        ) : null}
      </p>
    </div>
  );
}

function CandidateShrineFactsBlock({ facts }: { facts: CompassCandidateShrineFacts }) {
  return (
    <div data-testid="compass-candidate-shrine-facts">
      <p className={SECTION_LABEL_CLASS}>この神社について</p>
      {facts.deityName ? (
        <p className="mt-1 break-words text-sm leading-6 text-[var(--kt-color-text-primary)]" data-testid="compass-candidate-deity">
          <span className="mr-2 text-xs text-[var(--kt-color-text-muted)]">祭神</span>
          {facts.deityName}
        </p>
      ) : null}
      {facts.history ? (
        <div className="mt-1">
          {facts.history.typeLabel ? (
            <p className="text-xs text-[var(--kt-color-text-muted)]" data-testid="compass-candidate-history-type">
              {facts.history.typeLabel}
            </p>
          ) : null}
          <p
            className="line-clamp-2 break-words text-sm leading-6 text-[var(--kt-color-text-secondary)]"
            data-testid="compass-candidate-history"
          >
            {facts.history.content}
          </p>
        </div>
      ) : null}
    </div>
  );
}

export type CompassRecommendationsSectionProps = {
  recommendations: CompassRecommendation[];
  recommendationInstanceId: string;
  // The origin actually submitted with this Compass request (the same
  // coordinates the backend used for direction/distance). Used only as the
  // Google Maps route origin; omitted/invalid -> destination-only route.
  origin?: { lat: number; lng: number } | null;
};

export default function CompassRecommendationsSection({
  recommendations,
  recommendationInstanceId,
  origin = null,
}: CompassRecommendationsSectionProps) {
  const trackedImpressionsRef = useRef(new Set<string>());

  useEffect(() => {
    recommendations.forEach((rec, index) => {
      // F-1: Shrine identity は shrine_id のみ。`id` は COMPATIBILITY_FIELD で
      // identity authority ではないため fallback に使わない
      // （docs/audit/compass-shrine-id-presence-audit.md §14）。
      // F-4: その判定を共有 resolver へ集約。public_strict は shrine_id のみを
      // 許可し、alias も generic `id` も一切参照しない
      // （docs/audit/shared-shrine-identity-resolver-design.md §14）。
      const shrineId = resolveShrineId(rec, "public_strict");
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
          // F-1 / F-4: navigation / click analytics も shrine_id のみを identity とする。
          const shrineId = resolveShrineId(rec, "public_strict");
          const rank = index + 1;
          const key = String(shrineId ?? rec.name ?? Math.random());
          const distanceM = typeof rec.distance_m === "number" ? rec.distance_m : null;
          const formattedDistance = formatDistance(distanceM);
          const name = String(rec.name ?? "");
          const address = typeof rec.address === "string" ? rec.address : null;
          const meaning = resolveCompassCandidateMeaning(rec);
          const shrineFacts = resolveCompassCandidateShrineFacts(rec);
          // destination: address -> name fallback（座標は公開Contractに無い）。
          // 解決できなければ null を返すので、経路CTAを出さない。
          const routeHref = buildGoogleMapsDirUrl({
            origin,
            destination: { address: address ?? undefined, fallbackName: name },
          });
          return (
            <ShrineCardCompact
              key={key}
              layout="candidate"
              name={name}
              address={address}
              distanceLabel={formattedDistance ? `約${formattedDistance}` : null}
              detailLabel="神社を見る"
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
              secondaryAction={
                routeHref ? (
                  <GoogleMapRouteLink
                    href={routeHref}
                    label="経路を見る"
                    source="compass"
                    shrineId={shrineId}
                    ctx="compass"
                    recommendationInstanceId={recommendationInstanceId}
                    className={SHRINE_CARD_CANDIDATE_CTA_CLASS}
                  />
                ) : null
              }
            >
              {meaning || shrineFacts ? (
                <>
                  {meaning ? <CandidateMeaningBlock meaning={meaning} /> : null}
                  {meaning && shrineFacts ? (
                    <hr className="my-3 border-[var(--kt-color-border-default)]" data-testid="compass-candidate-divider" />
                  ) : null}
                  {shrineFacts ? <CandidateShrineFactsBlock facts={shrineFacts} /> : null}
                </>
              ) : null}
            </ShrineCardCompact>
          );
        })}
      </div>
    </DetailSection>
  );
}
