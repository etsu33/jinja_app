type TrackPayload = Record<string, unknown>;

type TrackEventDetail = {
  eventName: string;
  payload: TrackPayload;
  timestamp: string;
};

export type ConciergeDecisionSummary = {
  totalSessions: number;
  detailViews: number;
  decisions: number;
  returnsAfterDetail: number;
  resultClicks: number;
  premiumClicks: number;
  heroPrimaryClicks: number;
  heroSecondaryClicks: number;
  detailClicks: number;
  routeClicks: number;
  decisionRate: string;
  returnRate: string;
  detailRate: string;
  primaryClickRate: string;
  secondaryClickRate: string;
  saveDecisions: number;
  mapSearchDecisions: number;
  saveRate: string;
  mapSearchRate: string;
};

function percent(numerator: number, denominator: number): string {
  if (denominator <= 0) return "0%";
  return `${Math.round((numerator / denominator) * 100)}%`;
}

function getSessionId(event: TrackEventDetail): string {
  const id = event.payload?.sessionId;
  return typeof id === "string" && id.length > 0 ? id : "unknown";
}

export function buildConciergeDecisionSummary(events: TrackEventDetail[]): ConciergeDecisionSummary {
  const sessionIds = new Set<string>();

  const detailViews = events.filter((event) => event.eventName === "shrine_detail_view");
  const decisions = events.filter((event) => event.eventName === "shrine_decision");
  const returnsAfterDetail = events.filter((event) => event.eventName === "concierge_return_after_detail");
  const resultClicks = events.filter((event) => event.eventName === "concierge_result_click");
  const premiumClicks = events.filter((event) => event.eventName === "concierge_premium_click");

  for (const event of events) {
    if (
      event.eventName === "concierge_result_click" ||
      event.eventName === "concierge_premium_click" ||
      event.eventName === "shrine_detail_view" ||
      event.eventName === "shrine_decision" ||
      event.eventName === "concierge_return_after_detail"
    ) {
      sessionIds.add(getSessionId(event));
    }
  }

  const saveDecisions = decisions.filter((event) => event.payload?.action === "save").length;
  const mapSearchDecisions = decisions.filter((event) => event.payload?.action === "map_search").length;
  const detailClicks = resultClicks.filter((event) => event.payload?.action === "detail").length;
  const routeClicks = resultClicks.filter((event) => event.payload?.action === "route").length;
  const heroPrimaryClicks = resultClicks.filter((event) => event.payload?.position === "hero_primary").length;
  const heroSecondaryClicks = resultClicks.filter((event) => event.payload?.position === "hero_secondary").length;

  return {
    totalSessions: sessionIds.size,
    detailViews: detailViews.length,
    decisions: decisions.length,
    returnsAfterDetail: returnsAfterDetail.length,
    resultClicks: resultClicks.length,
    premiumClicks: premiumClicks.length,
    heroPrimaryClicks,
    heroSecondaryClicks,
    detailClicks,
    routeClicks,
    decisionRate: percent(decisions.length, detailViews.length),
    returnRate: percent(returnsAfterDetail.length, detailViews.length),
    detailRate: percent(detailClicks, resultClicks.length),
    primaryClickRate: percent(heroPrimaryClicks, resultClicks.length),
    secondaryClickRate: percent(heroSecondaryClicks, resultClicks.length),
    saveDecisions,
    mapSearchDecisions,
    saveRate: percent(saveDecisions, decisions.length),
    mapSearchRate: percent(mapSearchDecisions, decisions.length),
  };
}

export function buildConciergeDecisionSummaryFromStorage(raw: string | null): ConciergeDecisionSummary {
  if (!raw) return buildConciergeDecisionSummary([]);

  try {
    const parsed = JSON.parse(raw);
    return buildConciergeDecisionSummary(Array.isArray(parsed) ? parsed : []);
  } catch {
    return buildConciergeDecisionSummary([]);
  }
}
