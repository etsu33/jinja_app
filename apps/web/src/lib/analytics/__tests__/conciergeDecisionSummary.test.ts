import { describe, expect, it } from "vitest";
import { buildConciergeDecisionSummary } from "../conciergeDecisionSummary";

describe("buildConciergeDecisionSummary", () => {
  it("counts concierge result click positions and actions", () => {
    const summary = buildConciergeDecisionSummary([
      {
        eventName: "concierge_result_click",
        payload: {
          sessionId: "s1",
          action: "route",
          position: "hero_primary",
        },
        timestamp: "2026-05-03T00:00:00.000Z",
      },
      {
        eventName: "concierge_result_click",
        payload: {
          sessionId: "s2",
          action: "detail",
          position: "hero_secondary",
        },
        timestamp: "2026-05-03T00:00:01.000Z",
      },
      {
        eventName: "concierge_result_click",
        payload: {
          sessionId: "s3",
          action: "detail",
          position: "compact",
        },
        timestamp: "2026-05-03T00:00:02.000Z",
      },
    ]);

    expect(summary.resultClicks).toBe(3);
    expect(summary.routeClicks).toBe(1);
    expect(summary.detailClicks).toBe(2);
    expect(summary.heroPrimaryClicks).toBe(1);
    expect(summary.heroSecondaryClicks).toBe(1);
    expect(summary.detailRate).toBe("67%");
    expect(summary.primaryClickRate).toBe("33%");
    expect(summary.secondaryClickRate).toBe("33%");
  });
});
