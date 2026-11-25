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
    mockedGetAnalyticsProvider.mockReturnValue({ track: trackMock, identify: vi.fn(), reset: vi.fn() });
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
            shrine_id: index + 1,
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

// ---------------------------------------------------------------------------
// F-4: live recommendation analytics の Shrine identity。
//
// SHRINE_IDENTITY_AUTHORITY = Shrine.id / PUBLIC_IDENTITY_KEY = shrine_id。
// generic `id` は COMPATIBILITY_FIELD であり identity authority ではない。
// 移行前は `rec.shrine_id ?? rec.id` で generic `id` へ fallback していた。
//
// docs/audit/shared-shrine-identity-resolver-design.md §14
// ---------------------------------------------------------------------------
describe("trackRecommendationQualityFromRecommendations: F-4 Shrine identity契約", () => {
  const trackMock = vi.fn();

  beforeEach(() => {
    trackMock.mockReset();
    mockedGetAnalyticsProvider.mockReturnValue({ track: trackMock, identify: vi.fn(), reset: vi.fn() });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shrine_idとidが食い違う場合、analyticsのshrineIdはshrine_id側を使う", () => {
    trackRecommendationQualityFromRecommendations({
      recommendations: [
        {
          name: "食い違い神社",
          shrine_id: 42,
          id: 999,
          recommendation_reason_quality: { shrine_data_rate: 0.5 },
        } as ConciergeRecommendation,
      ],
      threadId: "thread-1",
      accessLevel: "free",
    });

    const payload = trackMock.mock.calls[0]?.[1] as Record<string, unknown>;
    expect(payload.shrineId).toBe(42);
    expect(payload.shrineId).not.toBe(999);
    // resultSetId も同じ identity で構成される（generic `id` を混ぜない）。
    expect(payload.resultSetId).toBe("thread-1:1:42");
  });

  it("id のみの live recommendation では generic `id` を shrineId にしない", () => {
    trackRecommendationQualityFromRecommendations({
      recommendations: [
        {
          name: "id のみ神社",
          id: 999,
          recommendation_reason_quality: { shrine_data_rate: 0.5 },
        } as ConciergeRecommendation,
      ],
      threadId: "thread-1",
      accessLevel: "free",
    });

    expect(trackMock).not.toHaveBeenCalled(); // Unsupported identity is not a registered recommendation.
  });

  it("shrine_id と shrineId が食い違う場合は conflict として shrineId を送らない", () => {
    trackRecommendationQualityFromRecommendations({
      recommendations: [
        {
          name: "conflict神社",
          shrine_id: 42,
          shrineId: 99,
          recommendation_reason_quality: { shrine_data_rate: 0.5 },
        } as unknown as ConciergeRecommendation,
      ],
      threadId: "thread-1",
      accessLevel: "free",
    });

    expect(trackMock).not.toHaveBeenCalled(); // Conflicting aliases fail closed.
  });

  it("混在・重複でも最初の品質・instanceと登録連番を保持する", () => {
    trackRecommendationQualityFromRecommendations({
      recommendations: [
        { place_id: "A", name: "reference", recommendation_reason_quality: { shrine_data_rate: 1 } },
        {
          shrine_id: 31,
          name: "first",
          recommendation_instance_id: "first-instance",
          recommendation_reason_quality: { shrine_data_rate: 0.25 },
        },
        {
          shrine_id: 12,
          name: "second",
          recommendation_instance_id: "first-instance",
          recommendation_reason_quality: { shrine_data_rate: 0.5 },
        },
        {
          shrine_id: 31,
          name: "later",
          recommendation_instance_id: "later-instance",
          recommendation_reason_quality: { shrine_data_rate: 1 },
        },
      ] as ConciergeRecommendation[],
      threadId: "thread-1",
      accessLevel: "free",
    });
    expect(trackMock).toHaveBeenCalledTimes(2);
    expect(
      trackMock.mock.calls.map(([, p]) => [
        p.shrineId,
        p.recommendationRank,
        p.recommendationInstanceId,
        p.shrine_data_rate,
      ]),
    ).toEqual([
      [31, 1, "first-instance", 0.25],
      [12, 2, "first-instance", 0.5],
    ]);
  });

  it("正常な shrine_id はそのまま shrineId になる（既存挙動の維持）", () => {
    trackRecommendationQualityFromRecommendations({
      recommendations: [rec({ shrine_id: 7, recommendation_reason_quality: { shrine_data_rate: 0.5 } })],
      threadId: "thread-1",
      accessLevel: "free",
    });

    const payload = trackMock.mock.calls[0]?.[1] as Record<string, unknown>;
    expect(payload.shrineId).toBe(7);
  });
});
