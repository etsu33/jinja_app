import { normalizeConciergeCandidates } from "../../../packages/shared/conciergeCandidates";
import {
  buildRecommendationImpressionDedupKey,
  buildRecommendationResultSetId,
  recommendationAnalyticsProperties,
  type RecommendationAnalyticsProvenance,
} from "../../../packages/shared/recommendationAnalyticsProvenance";
type PresentedCard = {
  kind: "registered" | "place";
  shrineId?: string;
  placeId: string | null;
  recommendationInstanceId: string | null;
  analyticsProvenance: RecommendationAnalyticsProvenance;
};
/** Keep event names and instance dedup; references never enter the registered funnel. */
export function trackConciergeResultImpressions(
  cards: readonly PresentedCard[],
  seen: Set<string>,
  emit: (name: string, properties: Record<string, unknown>) => void,
) {
  const registered = normalizeConciergeCandidates(cards.filter((c) => c.kind === "registered")).registered;
  const resultSetId = buildRecommendationResultSetId(
    null,
    registered.map((c) => ({ shrineId: c.shrineId })),
  );
  for (const { record: card, shrineId, recommendationRank } of registered) {
    const key = buildRecommendationImpressionDedupKey({
      recommendationInstanceId: card.recommendationInstanceId,
      resultSetId,
      shrineId: String(shrineId),
      rank: recommendationRank,
    });
    if (seen.has(key)) continue;
    seen.add(key);
    emit("concierge_result_impression", {
      source: "concierge_result",
      platform: "mobile",
      resultSetId,
      shrineId: String(shrineId),
      recommendationRank,
      recommendationInstanceId: card.recommendationInstanceId,
      ...recommendationAnalyticsProperties(card.analyticsProvenance),
    });
  }
}
