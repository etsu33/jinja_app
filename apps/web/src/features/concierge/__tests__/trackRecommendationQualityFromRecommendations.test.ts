import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getAnalyticsProvider } from "@/lib/analytics/providers";
import { trackRecommendationQualityFromRecommendations } from "@/features/concierge/hooks";
import type { ConciergeRecommendation } from "@/lib/api/concierge";

vi.mock("@/lib/analytics/providers", () => ({
  getAnalyticsProvider: vi.fn(),
}));

const mockedGetAnalyticsProvider = vi.mocked(getAnalyticsProvider);

function rec(overrides: Partial<ConciergeRecommendation> = {}): ConciergeRecommendation {
  return {
    name: "テスト神社",
    shrine_id: 1,
    ...overrides,
  };
}

describe("trackRecommendationQualityFromRecommendations: Knowledge品質property契約", () => {
  const trackMock = vi.fn();

  beforeEach(() => {
    trackMock.mockReset();
    mockedGetAnalyticsProvider.mockReturnValue({ track: trackMock });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("knowledge_backing_class=FULLY_KNOWLEDGE_BACKEDをそのまま転送する", () => {
    trackRecommendationQualityFromRecommendations({
      recommendations: [
        rec({
          recommendation_reason_quality: {
            shrine_data_rate: 0.5,
            knowledge_backing_class: "FULLY_KNOWLEDGE_BACKED",
            deity_knowledge_used: true,
            history_knowledge_used: false,
          },
        }),
      ],
      threadId: "thread-1",
      accessLevel: "free",
    });

    expect(trackMock).toHaveBeenCalledWith(
      "recommendation_quality",
      expect.objectContaining({
        knowledge_backing_class: "FULLY_KNOWLEDGE_BACKED",
        deity_knowledge_used: true,
        history_knowledge_used: false,
      }),
    );
  });

  it.each(["PARTIALLY_KNOWLEDGE_BACKED", "LEGACY_BACKED", "UNKNOWN"] as const)(
    "knowledge_backing_class=%sをそのまま転送する",
    (backingClass) => {
      trackRecommendationQualityFromRecommendations({
        recommendations: [
          rec({
            recommendation_reason_quality: { knowledge_backing_class: backingClass },
          }),
        ],
        threadId: null,
        accessLevel: null,
      });

      expect(trackMock).toHaveBeenCalledWith(
        "recommendation_quality",
        expect.objectContaining({ knowledge_backing_class: backingClass }),
      );
    },
  );

  it("deity/history使用有無の4パターンをそれぞれ正しく転送する", () => {
    const cases: Array<[boolean, boolean]> = [
      [true, true],
      [true, false],
      [false, true],
      [false, false],
    ];

    cases.forEach(([deityUsed, historyUsed], index) => {
      trackMock.mockClear();
      trackRecommendationQualityFromRecommendations({
        recommendations: [
          rec({
            shrine_id: index,
            recommendation_reason_quality: {
              deity_knowledge_used: deityUsed,
              history_knowledge_used: historyUsed,
            },
          }),
        ],
        threadId: "thread-x",
        accessLevel: "anonymous",
      });

      expect(trackMock).toHaveBeenCalledWith(
        "recommendation_quality",
        expect.objectContaining({
          deity_knowledge_used: deityUsed,
          history_knowledge_used: historyUsed,
        }),
      );
    });
  });

  it("新規propertyが未定義の場合、送信payloadから省かれる（既存のnull-stripping契約に従う、後方互換）", () => {
    trackRecommendationQualityFromRecommendations({
      recommendations: [rec({ recommendation_reason_quality: { shrine_data_rate: 0.25 } })],
      threadId: "thread-1",
      accessLevel: "premium",
    });

    const payload = trackMock.mock.calls[0]?.[1] as Record<string, unknown>;
    // serializeSearchAnalyticsPayload()がnull/undefinedを送信前にstripする既存契約
    // （searchEvents.ts）と同じ挙動になることを確認する。
    expect(payload).not.toHaveProperty("knowledge_backing_class");
    expect(payload).not.toHaveProperty("deity_knowledge_used");
    expect(payload).not.toHaveProperty("history_knowledge_used");
    expect(payload.shrine_data_rate).toBe(0.25);
  });

  it("既存の7 propertyは変更されない", () => {
    trackRecommendationQualityFromRecommendations({
      recommendations: [
        rec({
          recommendation_reason_quality: {
            shrine_data_rate: 0.5,
            consultation_reflection_rate: 0.25,
            fallback_reason_rate: 0.0,
            evidence_rate: 0.5,
            action_grounding_rate: 0.33,
            is_ai_inference_only: false,
            fallback_source: "fallback",
            knowledge_backing_class: "FULLY_KNOWLEDGE_BACKED",
          },
        }),
      ],
      threadId: "thread-1",
      accessLevel: "free",
    });

    const payload = trackMock.mock.calls[0]?.[1];
    expect(payload).toMatchObject({
      shrine_data_rate: 0.5,
      consultation_reflection_rate: 0.25,
      fallback_reason_rate: 0.0,
      evidence_rate: 0.5,
      action_grounding_rate: 0.33,
      is_ai_inference_only: false,
      fallback_source: "fallback",
    });
  });

  it("recommendation_reason_qualityが存在しない候補はイベントを送信しない", () => {
    trackRecommendationQualityFromRecommendations({
      recommendations: [rec({ recommendation_reason_quality: null })],
      threadId: "thread-1",
      accessLevel: null,
    });

    expect(trackMock).not.toHaveBeenCalled();
  });

  it("Fact本文・Source URL・相談本文に相当するkeyをpayloadへ含めない", () => {
    trackRecommendationQualityFromRecommendations({
      recommendations: [
        rec({
          recommendation_reason_quality: { knowledge_backing_class: "FULLY_KNOWLEDGE_BACKED" },
        }),
      ],
      threadId: "thread-1",
      accessLevel: null,
    });

    const payload = trackMock.mock.calls[0]?.[1] as Record<string, unknown>;
    expect(payload).not.toHaveProperty("deity");
    expect(payload).not.toHaveProperty("shrine_history");
    expect(payload).not.toHaveProperty("source_url");
    expect(payload).not.toHaveProperty("consultation");
    expect(payload).not.toHaveProperty("query");
  });
});
