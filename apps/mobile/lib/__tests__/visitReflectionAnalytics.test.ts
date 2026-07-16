import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// __DEV__ は Metro/React Native が注入するグローバルで、vitest実行環境には存在しないため定義する。
(globalThis as unknown as { __DEV__: boolean }).__DEV__ = false;

import { setAnalyticsProvider, type AnalyticsProvider } from "../analytics";
import { trackReflectionPromptView, trackReflectionSaved, trackVisitDone } from "../visitReflectionAnalytics";

describe("visitReflectionAnalytics", () => {
  const trackSpy = vi.fn();

  beforeEach(() => {
    const customProvider: AnalyticsProvider = { track: trackSpy };
    setAnalyticsProvider(customProvider);
  });

  afterEach(() => {
    trackSpy.mockClear();
    setAnalyticsProvider(null);
  });

  it("trackVisitDoneはsource/platform/shrineId/historyThemeを送る", () => {
    trackVisitDone({ shrineId: 17, historyTheme: "静寂" });

    expect(trackSpy).toHaveBeenCalledWith("visit_done", {
      source: "shrine_detail",
      platform: "mobile",
      shrineId: 17,
      historyTheme: "静寂",
    });
  });

  it("trackVisitDoneはhistoryTheme/threadIdが未取得の場合キー自体を送らない", () => {
    trackVisitDone({ shrineId: 17, historyTheme: "" });

    expect(trackSpy).toHaveBeenCalledWith("visit_done", {
      source: "shrine_detail",
      platform: "mobile",
      shrineId: 17,
    });
  });

  it("trackReflectionPromptViewはreflectionFormType/reflectionContextを送る", () => {
    trackReflectionPromptView({
      shrineId: 17,
      historyTheme: "静寂",
      reflectionFormType: "one_line",
      reflectionContext: "visit_done",
    });

    expect(trackSpy).toHaveBeenCalledWith("reflection_prompt_view", {
      source: "shrine_detail",
      platform: "mobile",
      shrineId: 17,
      historyTheme: "静寂",
      reflectionFormType: "one_line",
      reflectionContext: "visit_done",
    });
  });

  it("trackReflectionSavedはanswerLengthを送り、moodBefore/moodAfterが空なら送らない", () => {
    trackReflectionSaved({
      shrineId: 17,
      historyTheme: "静寂",
      reflectionFormType: "one_line",
      reflectionContext: "visit_done",
      answerLength: 12,
      moodBefore: "",
      moodAfter: "",
    });

    expect(trackSpy).toHaveBeenCalledWith("reflection_saved", {
      source: "shrine_detail",
      platform: "mobile",
      shrineId: 17,
      historyTheme: "静寂",
      reflectionFormType: "one_line",
      reflectionContext: "visit_done",
      answerLength: 12,
    });
  });

  it("threadIdが取得できた場合はpayloadに含める", () => {
    trackVisitDone({ shrineId: 17, threadId: 42, historyTheme: "静寂" });

    expect(trackSpy).toHaveBeenCalledWith("visit_done", {
      source: "shrine_detail",
      platform: "mobile",
      shrineId: 17,
      threadId: 42,
      historyTheme: "静寂",
    });
  });
});
