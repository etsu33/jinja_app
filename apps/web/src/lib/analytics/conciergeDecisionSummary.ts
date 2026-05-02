

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
  decisionRate: string;
  returnRate: string;
  saveDecisions: number;
  routeDecisions: number;
  saveRate: string;
  routeRate: string;
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

  for (const event of events) {
    if (
      event.eventName === "concierge_result_click" ||
      event.eventName === "shrine_detail_view" ||
      event.eventName === "shrine_decision" ||
      event.eventName === "concierge_return_after_detail"
    ) {
      sessionIds.add(getSessionId(event));
    }
  }

  const saveDecisions = decisions.filter((event) => event.payload?.action === "save").length;
  const routeDecisions = decisions.filter((event) => event.payload?.action === "route").length;

  return {
    totalSessions: sessionIds.size,
    detailViews: detailViews.length,
    decisions: decisions.length,
    returnsAfterDetail: returnsAfterDetail.length,
    decisionRate: percent(decisions.length, detailViews.length),
    returnRate: percent(returnsAfterDetail.length, detailViews.length),
    saveDecisions,
    routeDecisions,
    saveRate: percent(saveDecisions, decisions.length),
    routeRate: percent(routeDecisions, decisions.length),
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
