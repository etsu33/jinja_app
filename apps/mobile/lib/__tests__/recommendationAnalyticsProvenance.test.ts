import { describe, expect, it } from "vitest";

import {
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
