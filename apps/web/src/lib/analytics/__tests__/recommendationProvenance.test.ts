import { describe, expect, it } from "vitest";

import {
  normalizeRecommendationInstanceId,
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

// docs/audit/recommendation-instance-identity-propagation.md: this only normalizes a
// Backend-issued value (rid). It must never generate/guess/reconstruct an id.
describe("normalizeRecommendationInstanceId", () => {
  it("Backendのrecommendation_instance_idをそのまま通す", () => {
    expect(normalizeRecommendationInstanceId("a1b2c3d4")).toBe("a1b2c3d4");
  });

  it("前後の空白を取り除く", () => {
    expect(normalizeRecommendationInstanceId("  a1b2c3d4  ")).toBe("a1b2c3d4");
  });

  it.each([undefined, null, "", "   ", 123, {}, []])(
    "存在しない値(%p)はnullへfallbackし、合成しない",
    (raw) => {
      expect(normalizeRecommendationInstanceId(raw)).toBeNull();
    },
  );

  it("同一入力に対して常に同じ値を返す(再renderで不変)", () => {
    const first = normalizeRecommendationInstanceId("a1b2c3d4");
    const second = normalizeRecommendationInstanceId("a1b2c3d4");
    expect(first).toBe(second);
  });
});
