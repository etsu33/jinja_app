import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// __DEV__ は Metro/React Native が注入するグローバルで、vitest実行環境には存在しないため定義する。
(globalThis as unknown as { __DEV__: boolean }).__DEV__ = false;

import { setAnalyticsProvider, type AnalyticsProvider } from "../analytics";
import {
  trackReflectionPromptView,
  trackReflectionSaved,
  trackReflectionToConsultationClick,
  trackVisitDone,
} from "../visitReflectionAnalytics";

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

  describe("trackReflectionToConsultationClick", () => {
    it("source/platform/shrineId/reflectionSaved(true固定)を送る", () => {
      trackReflectionToConsultationClick({ shrineId: 17, historyTheme: "静寂" });

      expect(trackSpy).toHaveBeenCalledWith("reflection_to_consultation_click", {
        source: "shrine_detail",
        platform: "mobile",
        shrineId: 17,
        historyTheme: "静寂",
        reflectionSaved: true,
      });
    });

    it("reflectionSavedは呼び出し元の値に関わらず常にtrueで送る", () => {
      // BasePayloadParamsにreflectionSavedというfieldは存在しないため、
      // 呼び出し元が誤った値を渡す余地がなく、関数内部で固定される。
      trackReflectionToConsultationClick({ shrineId: 1 });

      const payload = trackSpy.mock.calls[0][1] as Record<string, unknown>;
      expect(payload.reflectionSaved).toBe(true);
    });

    it("historyTheme/threadIdが未取得の場合キー自体を送らない", () => {
      trackReflectionToConsultationClick({ shrineId: 17 });

      expect(trackSpy).toHaveBeenCalledWith("reflection_to_consultation_click", {
        source: "shrine_detail",
        platform: "mobile",
        shrineId: 17,
        reflectionSaved: true,
      });
    });

    it("Reflection本文・相談文・住所・緯度経度等の禁止属性を含まない", () => {
      trackReflectionToConsultationClick({ shrineId: 17, threadId: 42, historyTheme: "静寂" });

      const payload = trackSpy.mock.calls[0][1] as Record<string, unknown>;
      const forbiddenKeys = [
        "answer",
        "query",
        "consultation",
        "address",
        "latitude",
        "longitude",
        "birthdate",
        "moodBefore",
        "moodAfter",
        "reasonFacts",
        "email",
        "token",
      ];
      for (const key of forbiddenKeys) {
        expect(payload).not.toHaveProperty(key);
      }
    });

    it("payloadはprimitive値のみで構成される", () => {
      trackReflectionToConsultationClick({ shrineId: 17, threadId: 42, historyTheme: "静寂" });

      const payload = trackSpy.mock.calls[0][1] as Record<string, unknown>;
      for (const value of Object.values(payload)) {
        expect(["string", "number", "boolean"]).toContain(typeof value);
      }
    });
  });
});
