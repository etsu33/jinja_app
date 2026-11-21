import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, it, expect, vi } from "vitest";
import { normalizeConciergeCandidates } from "../../../../packages/shared/conciergeCandidates";
import { recommendationAnalyticsProvenance } from "../../../../packages/shared/recommendationAnalyticsProvenance";
import { trackConciergeResultImpressions } from "../conciergePresentation";
const fixture = JSON.parse(
  readFileSync(resolve(process.cwd(), "../../docs/audit/fixtures/concierge-web-mobile-parity.json"), "utf8"),
);
describe("shared Concierge order contract", () => {
  it.each(
    fixture.presentation_cases as Array<{
      name: string;
      records: any[];
      registered: number[];
      references: string[];
      ranks: number[];
    }>,
  )("$name", (scenario) => {
    const p = normalizeConciergeCandidates(scenario.records);
    expect(p.registered.map((c) => c.shrineId)).toEqual(scenario.registered);
    expect(p.references.map((c) => c.placeId)).toEqual(scenario.references);
    expect(p.registered.map((c) => c.recommendationRank)).toEqual(scenario.ranks);
    expect(p.references.every((c) => c.shrineId === null && c.recommendationRank === null)).toBe(true);
    for (const c of p.ordered) expect(c.record).toBe(scenario.records[c.sourceIndex]);
    expect(p.ordered.map((c) => c.sourceIndex)).toEqual(p.ordered.map((c) => c.sourceIndex).sort((a, b) => a - b));
  });
  it("never enriches the first authoritative record from later duplicate metadata", () => {
    const first = { shrine_id: 31, reason: null, breakdown: null, recommendation_instance_id: null };
    const later = { shrine_id: 31, reason: "later", breakdown: { score: 99 }, recommendation_instance_id: "later" };
    expect(normalizeConciergeCandidates([first, later]).registered[0].record).toBe(first);
    expect(first).toEqual({ shrine_id: 31, reason: null, breakdown: null, recommendation_instance_id: null });
  });
  it("emits registered-only ranks once per entity and Backend instance", () => {
    const emit = vi.fn(),
      seen = new Set<string>(),
      analyticsProvenance = recommendationAnalyticsProvenance({});
    const cards = [
      { kind: "place" as const, placeId: "A", recommendationInstanceId: "first", analyticsProvenance },
      {
        kind: "registered" as const,
        shrineId: "31",
        placeId: null,
        recommendationInstanceId: "first",
        analyticsProvenance,
      },
      {
        kind: "registered" as const,
        shrineId: "12",
        placeId: null,
        recommendationInstanceId: "first",
        analyticsProvenance,
      },
    ];
    trackConciergeResultImpressions(cards, seen, emit);
    trackConciergeResultImpressions(cards, seen, emit);
    expect(emit.mock.calls.map(([n, p]) => [n, p.shrineId, p.recommendationRank, p.recommendationInstanceId])).toEqual([
      ["concierge_result_impression", "31", 1, "first"],
      ["concierge_result_impression", "12", 2, "first"],
    ]);
    expect(emit.mock.calls[0][1].resultSetId).toBe("unknown:1:31|2:12");
    trackConciergeResultImpressions(
      cards.map((c) => ({ ...c, recommendationInstanceId: "new" })),
      seen,
      emit,
    );
    expect(emit).toHaveBeenCalledTimes(4);
  });
});
