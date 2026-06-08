import type { CardAnalyticsEvent } from "@/lib/analytics/cardEvents";
import type { CardId, CardVisibilityState } from "@/lib/premium/cardVisibility";

export type ConciergeCardRenderRoute = {
  cardId: CardId;
  visibility: Exclude<CardVisibilityState, "hidden">;
  viewEvent: Extract<CardAnalyticsEvent, "card_view" | "card_partial_view" | "card_teaser_view">;
};

export function resolveConciergeCardViewEvent(
  visibility: Exclude<CardVisibilityState, "hidden">,
): ConciergeCardRenderRoute["viewEvent"] {
  if (visibility === "partial") return "card_partial_view";
  if (visibility === "teaser") return "card_teaser_view";
  return "card_view";
}

export function buildConciergeCardRoutes(
  entries: Array<{ cardId: CardId; visibility: CardVisibilityState }>,
): ConciergeCardRenderRoute[] {
  return entries
    .filter((entry): entry is { cardId: CardId; visibility: Exclude<CardVisibilityState, "hidden"> } =>
      entry.visibility !== "hidden",
    )
    .map((entry) => ({
      cardId: entry.cardId,
      visibility: entry.visibility,
      viewEvent: resolveConciergeCardViewEvent(entry.visibility),
    }));
}
