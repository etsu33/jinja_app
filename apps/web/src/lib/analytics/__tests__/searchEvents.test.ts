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

  it("historyThemeがnull/undefinedの場合、payloadからキー自体が省略される(空文字は送らない)", () => {
    trackSearchEvent("visit_done", {
      source: "shrine_detail",
      shrineId: 1,
      historyTheme: null,
    });

    expect(trackMock).toHaveBeenCalledTimes(1);
    const [, payload] = trackMock.mock.calls[0] ?? [];
    expect(payload).not.toHaveProperty("historyTheme");
    expect(payload?.historyTheme).not.toBe("");
  });

  it("visit_doneはhistoryThemeの有無にかかわらず必ず送信される", () => {
    trackSearchEvent("visit_done", { source: "shrine_detail", shrineId: 1 });
    trackSearchEvent("visit_done", { source: "shrine_detail", shrineId: 2, historyTheme: "縁" });

    expect(trackMock).toHaveBeenCalledTimes(2);
    expect(trackMock).toHaveBeenNthCalledWith(1, "visit_done", expect.objectContaining({ shrineId: 1 }));
    expect(trackMock).toHaveBeenNthCalledWith(
      2,
      "visit_done",
      expect.objectContaining({ shrineId: 2, historyTheme: "縁" }),
    );
  });

  it("modeはctx由来の値のみを受け付け、ctxというキー自体は型として存在しない", () => {
    trackSearchEvent("visit_done", {
      source: "shrine_detail",
      shrineId: 1,
      mode: "need",
    });

    expect(trackMock).toHaveBeenCalledWith(
      "visit_done",
      expect.objectContaining({ mode: "need" }),
    );
    expect(trackMock.mock.calls[0]?.[1]).not.toHaveProperty("ctx");
  });
});
