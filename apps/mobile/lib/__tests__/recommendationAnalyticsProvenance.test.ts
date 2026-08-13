import { describe, expect, it } from "vitest";

import {
  buildRecommendationImpressionDedupKey,
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

// docs/audit/recommendation-strict-funnel-readiness.md §6, §14-2: Mobileも同じ
// buildRecommendationImpressionDedupKey()をWebと共有し、同一semantic contractでdedupする。
describe("buildRecommendationImpressionDedupKey parity", () => {
  it("同一instance + 同一shrine/rankは同じkeyになる(rerenderでdedupされる)", () => {
    const first = buildRecommendationImpressionDedupKey({
      recommendationInstanceId: "gen-a",
      resultSetId: "unknown:1:1",
      shrineId: "1",
      rank: 1,
    });
    const second = buildRecommendationImpressionDedupKey({
      recommendationInstanceId: "gen-a",
      resultSetId: "unknown:1:1",
      shrineId: "1",
      rank: 1,
    });
    expect(first).toBe(second);
  });

  it("同じshrine/rankでも新instanceなら別keyになる(新generationは抑制されない)", () => {
    const genA = buildRecommendationImpressionDedupKey({
      recommendationInstanceId: "gen-a",
      resultSetId: "unknown:1:1",
      shrineId: "1",
      rank: 1,
    });
    const genB = buildRecommendationImpressionDedupKey({
      recommendationInstanceId: "gen-b",
      resultSetId: "unknown:1:1",
      shrineId: "1",
      rank: 1,
    });
    expect(genA).not.toBe(genB);
  });

  it("Mobileの常にunknown prefixなresultSetIdでも、recommendationInstanceIdがあれば別threadを衝突させない", () => {
    // Mobileの resultSetId は threadId を含まないため常に "unknown:..." になり得るが、
    // recommendationInstanceId (Backend rid) が異なれば依然として別keyになる。
    const threadOne = buildRecommendationImpressionDedupKey({
      recommendationInstanceId: "rid-thread-1",
      resultSetId: "unknown:1:1",
      shrineId: "1",
      rank: 1,
    });
    const threadTwo = buildRecommendationImpressionDedupKey({
      recommendationInstanceId: "rid-thread-2",
      resultSetId: "unknown:1:1",
      shrineId: "1",
      rank: 1,
    });
    expect(threadOne).not.toBe(threadTwo);
  });

  it("malformed/null recommendationInstanceIdでもクラッシュしない", () => {
    expect(() =>
      buildRecommendationImpressionDedupKey({
        recommendationInstanceId: null,
        resultSetId: "unknown:empty",
        shrineId: undefined,
        rank: 1,
      }),
    ).not.toThrow();
  });
});
