import { describe, expect, it } from "vitest";

import {
  recommendationAnalyticsProperties,
  recommendationAnalyticsProvenance,
} from "../../../../../../packages/shared/recommendationAnalyticsProvenance";

describe("Web recommendation provenance", () => {
  it.each(["need_tag", "history_theme", "fallback"])("Primary %sをそのまま送る", (type) => {
    const provenance = recommendationAnalyticsProvenance({
      reasonFacts: [{ type, label: type, score: 1, evidence: [], is_primary: true }],
    });
    expect(recommendationAnalyticsProperties(provenance)).toMatchObject({
      primaryReasonSource: type,
      isFallbackRecommendation: type === "fallback",
    });
  });

  it("culture_translationをPrimary化せずAction sourceだけ保持する", () => {
    const provenance = recommendationAnalyticsProvenance({
      reasonFacts: [{ type: "culture_translation", is_primary: false }],
      actionSuggestionPreview: {
        action_source: { source: "action_context" },
        source_keys: ["recommendation_reason_v4", "culture_translation"],
      },
    });
    expect(provenance.primaryReasonSource).toBeNull();
    expect(provenance.actionSourceKeys).toContain("culture_translation");
  });

  it.each([
    ["fallback", []],
    ["action_context", ["ranked_history_theme", "action_catalog"]],
  ])("Action grounding %sを再ラベルしない", (source, sourceKeys) => {
    const provenance = recommendationAnalyticsProvenance({
      actionSuggestionPreview: { action_source: { source }, source_keys: sourceKeys },
    });
    expect(provenance.actionSource).toBe(source);
    expect(provenance.actionSourceKeys).toEqual(sourceKeys);
  });
});
