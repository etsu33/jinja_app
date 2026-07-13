import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getAnalyticsProvider } from "@/lib/analytics/providers";
import {
  serializeSearchAnalyticsPayload,
  trackSearchEvent,
} from "@/lib/analytics/searchEvents";

vi.mock("@/lib/analytics/providers", () => ({
  getAnalyticsProvider: vi.fn(),
}));

const mockedGetAnalyticsProvider = vi.mocked(getAnalyticsProvider);

describe("searchEvents契約", () => {
  const trackMock = vi.fn();

  beforeEach(() => {
    trackMock.mockReset();
    mockedGetAnalyticsProvider.mockReturnValue({ track: trackMock });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("reflection_prompt_view / reflection_saved は reflectionFormType と reflectionContext を運ぶ", () => {
    trackSearchEvent("reflection_prompt_view", {
      source: "shrine_detail",
      shrineId: 1,
      historyTheme: "静寂",
      reflectionFormType: "mood_delta",
      reflectionContext: "visit_done",
    });

    expect(trackMock).toHaveBeenCalledWith(
      "reflection_prompt_view",
      expect.objectContaining({
        reflectionFormType: "mood_delta",
        reflectionContext: "visit_done",
      }),
    );
    expect(trackMock.mock.calls[0]?.[1]).not.toHaveProperty("promptType");
  });

  it("action_suggestion_reflection_preview_view は actionPromptType を運び、reflectionFormType を持たない", () => {
    trackSearchEvent("action_suggestion_reflection_preview_view", {
      source: "concierge_result",
      shrineId: 1,
      actionPromptType: "before_visit",
    });

    expect(trackMock).toHaveBeenCalledWith(
      "action_suggestion_reflection_preview_view",
      expect.objectContaining({ actionPromptType: "before_visit" }),
    );
    expect(trackMock.mock.calls[0]?.[1]).not.toHaveProperty("reflectionFormType");
    expect(trackMock.mock.calls[0]?.[1]).not.toHaveProperty("promptType");
  });

  it("serializeSearchAnalyticsPayloadはreflectionFormType/reflectionContext/actionPromptTypeを保持する", () => {
    const serialized = serializeSearchAnalyticsPayload({
      reflectionFormType: "mood_delta",
      reflectionContext: "visit_done",
      actionPromptType: "emotion",
    });

    expect(serialized).toEqual({
      reflectionFormType: "mood_delta",
      reflectionContext: "visit_done",
      actionPromptType: "emotion",
    });
  });
});
