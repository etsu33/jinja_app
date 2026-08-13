import { describe, expect, it } from "vitest";

import {
  normalizeRecommendationInstanceId,
  recommendationAnalyticsProperties,
  recommendationAnalyticsProvenance,
} from "../../../../packages/shared/recommendationAnalyticsProvenance";

describe("Mobile recommendation provenance parity", () => {
  it.each(["need_tag", "history_theme", "fallback"])("Primary %sをWebと同じfieldで送る", (type) => {
    const properties = recommendationAnalyticsProperties(recommendationAnalyticsProvenance({
      reasonFacts: [{ type, label: type, score: 1, evidence: [], is_primary: true }],
    }));
    expect(properties).toMatchObject({
      primaryReasonSource: type,
      isFallbackRecommendation: type === "fallback",
    });
  });

  it.each([
    ["fallback", []],
    ["action_context", ["ranked_history_theme", "action_catalog"]],
  ])("Action grounding %sをWebと同じfieldで送る", (source, sourceKeys) => {
    const properties = recommendationAnalyticsProperties(recommendationAnalyticsProvenance({
      actionSuggestionPreview: { actionSource: { source }, sourceKeys },
    }));
    expect(properties.actionSource).toBe(source);
    expect(properties.actionSourceKeys).toBe(sourceKeys.length > 0 ? sourceKeys.join(",") : undefined);
  });
});

// docs/audit/recommendation-instance-identity-propagation.md: Mobile must read the same
// Backend-issued rid as Web, via the same shared normalizer -- never generate its own.
describe("normalizeRecommendationInstanceId parity", () => {
  it("WebとMobileが同じBackend値を同じ結果へ正規化する", () => {
    expect(normalizeRecommendationInstanceId("a1b2c3d4")).toBe("a1b2c3d4");
  });

  it.each([undefined, null, "", "   "])("欠損値(%p)はnullのまま、合成しない", (raw) => {
    expect(normalizeRecommendationInstanceId(raw)).toBeNull();
  });
});
