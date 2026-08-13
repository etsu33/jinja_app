import { describe, expect, it } from "vitest";

import {
  buildRecommendationImpressionDedupKey,
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

// docs/audit/recommendation-strict-funnel-readiness.md §6, §14-1/2: Impression dedup must
// key off recommendationInstanceId (the true instance boundary), not resultSetId alone.
describe("buildRecommendationImpressionDedupKey", () => {
  it("同一instanceの同一shrine/rankは同じkeyになる(dedupが機能する)", () => {
    const first = buildRecommendationImpressionDedupKey({
      recommendationInstanceId: "gen-a",
      resultSetId: "thread-1:1:1",
      shrineId: 1,
      position: "hero",
      rank: 1,
    });
    const second = buildRecommendationImpressionDedupKey({
      recommendationInstanceId: "gen-a",
      resultSetId: "thread-1:1:1",
      shrineId: 1,
      position: "hero",
      rank: 1,
    });
    expect(first).toBe(second);
  });

  it("同じshrine/rankでもrecommendationInstanceIdが違えば別keyになる(新generationは抑制されない)", () => {
    const genA = buildRecommendationImpressionDedupKey({
      recommendationInstanceId: "gen-a",
      resultSetId: "thread-1:1:1",
      shrineId: 1,
      position: "hero",
      rank: 1,
    });
    const genB = buildRecommendationImpressionDedupKey({
      recommendationInstanceId: "gen-b",
      resultSetId: "thread-1:1:1",
      shrineId: 1,
      position: "hero",
      rank: 1,
    });
    expect(genA).not.toBe(genB);
  });

  it("recommendationInstanceIdがnull/undefinedならresultSetIdへfallbackする(合成しない)", () => {
    const key = buildRecommendationImpressionDedupKey({
      recommendationInstanceId: null,
      resultSetId: "thread-1:1:1",
      shrineId: 1,
      position: "hero",
      rank: 1,
    });
    expect(key).toContain("thread-1:1:1");
  });

  it("shrineId/positionが欠損してもクラッシュしない", () => {
    expect(() =>
      buildRecommendationImpressionDedupKey({
        recommendationInstanceId: undefined,
        resultSetId: "unknown:empty",
        shrineId: null,
        position: undefined,
        rank: 1,
      }),
    ).not.toThrow();
  });
});
