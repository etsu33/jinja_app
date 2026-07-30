import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// __DEV__ は Metro/React Native が注入するグローバルで、vitest実行環境には存在しないため定義する。
(globalThis as unknown as { __DEV__: boolean }).__DEV__ = false;

import { setAnalyticsProvider, type AnalyticsProvider } from "../analytics";
import {
  shouldTrackConsultationHistoryViewEvent,
  trackConsultationHistoryDetailOpened,
  trackConsultationHistoryDetailViewed,
  trackConsultationHistoryEntryClicked,
  trackConsultationHistoryListViewed,
  trackConsultationHistoryShrineOpened,
} from "../consultationHistoryAnalytics";

describe("consultationHistoryAnalytics", () => {
  const trackSpy = vi.fn();

  beforeEach(() => {
    const customProvider: AnalyticsProvider = { track: trackSpy };
    setAnalyticsProvider(customProvider);
  });

  afterEach(() => {
    trackSpy.mockClear();
    setAnalyticsProvider(null);
  });

  it("trackConsultationHistoryEntryClicked: platform:mobile/source:mypageを送る", () => {
    trackConsultationHistoryEntryClicked();

    expect(trackSpy).toHaveBeenCalledWith("consultation_history_entry_clicked", {
      platform: "mobile",
      source: "mypage",
    });
  });

  it("trackConsultationHistoryListViewed: historyCountを送る", () => {
    trackConsultationHistoryListViewed({ historyCount: 3 });

    expect(trackSpy).toHaveBeenCalledWith("consultation_history_list_viewed", {
      platform: "mobile",
      source: "consultation_history",
      historyCount: 3,
    });
  });

  it("trackConsultationHistoryListViewed: 0件でもhistoryCount:0を送る", () => {
    trackConsultationHistoryListViewed({ historyCount: 0 });

    expect(trackSpy).toHaveBeenCalledWith(
      "consultation_history_list_viewed",
      expect.objectContaining({ historyCount: 0 }),
    );
  });

  it("trackConsultationHistoryDetailOpened: threadId・positionを送る", () => {
    trackConsultationHistoryDetailOpened({ threadId: 42, position: 1 });

    expect(trackSpy).toHaveBeenCalledWith("consultation_history_detail_opened", {
      platform: "mobile",
      source: "consultation_history_list",
      threadId: 42,
      position: 1,
    });
  });

  it("trackConsultationHistoryDetailViewed: threadId・recommendationCount・messageCountを送る", () => {
    trackConsultationHistoryDetailViewed({ threadId: "42", recommendationCount: 2, messageCount: 5 });

    expect(trackSpy).toHaveBeenCalledWith("consultation_history_detail_viewed", {
      platform: "mobile",
      source: "consultation_history_detail",
      threadId: "42",
      recommendationCount: 2,
      messageCount: 5,
    });
  });

  it("trackConsultationHistoryShrineOpened: threadId・shrineId・recommendationRankを送る", () => {
    trackConsultationHistoryShrineOpened({ threadId: 42, shrineId: 5, recommendationRank: 2 });

    expect(trackSpy).toHaveBeenCalledWith("consultation_history_shrine_opened", {
      platform: "mobile",
      source: "consultation_history_detail",
      threadId: 42,
      shrineId: 5,
      recommendationRank: 2,
    });
  });

  it("全EventのPayloadはprimitive値のみで構成される(nested object・配列を含まない)", () => {
    trackConsultationHistoryEntryClicked();
    trackConsultationHistoryListViewed({ historyCount: 1 });
    trackConsultationHistoryDetailOpened({ threadId: 1, position: 1 });
    trackConsultationHistoryDetailViewed({ threadId: 1, recommendationCount: 1, messageCount: 1 });
    trackConsultationHistoryShrineOpened({ threadId: 1, shrineId: 1, recommendationRank: 1 });

    for (const call of trackSpy.mock.calls) {
      const payload = call[1] as Record<string, unknown>;
      for (const value of Object.values(payload)) {
        expect(["string", "number", "boolean"].includes(typeof value)).toBe(true);
      }
    }
  });

  it("禁止Payload: 相談本文・タイトル・住所・緯度経度等を一切含まない", () => {
    trackConsultationHistoryEntryClicked();
    trackConsultationHistoryListViewed({ historyCount: 1 });
    trackConsultationHistoryDetailOpened({ threadId: 1, position: 1 });
    trackConsultationHistoryDetailViewed({ threadId: 1, recommendationCount: 1, messageCount: 1 });
    trackConsultationHistoryShrineOpened({ threadId: 1, shrineId: 1, recommendationRank: 1 });

    const forbiddenKeys = [
      "title",
      "content",
      "message",
      "lastMessage",
      "reasonText",
      "recommendationReason",
      "address",
      "latitude",
      "longitude",
      "username",
      "email",
      "token",
    ];

    for (const call of trackSpy.mock.calls) {
      const payload = call[1] as Record<string, unknown>;
      for (const key of forbiddenKeys) {
        expect(payload).not.toHaveProperty(key);
      }
    }
  });

  it("providerが例外を投げてもUI側(呼び出し元)へ伝播しない", () => {
    setAnalyticsProvider({
      track: () => {
        throw new Error("provider failed");
      },
    });

    expect(() => trackConsultationHistoryEntryClicked()).not.toThrow();
    expect(() => trackConsultationHistoryListViewed({ historyCount: 0 })).not.toThrow();
  });
});

describe("shouldTrackConsultationHistoryViewEvent", () => {
  it("readyかつ未送信ならtrueを返す", () => {
    expect(shouldTrackConsultationHistoryViewEvent({ isReady: true, alreadyTracked: false })).toBe(true);
  });

  it("readyだが送信済みならfalseを返す(重複防止)", () => {
    expect(shouldTrackConsultationHistoryViewEvent({ isReady: true, alreadyTracked: true })).toBe(false);
  });

  it("ready未達(loading/unauthenticated/fetchFailed等)ならfalseを返す", () => {
    expect(shouldTrackConsultationHistoryViewEvent({ isReady: false, alreadyTracked: false })).toBe(false);
    expect(shouldTrackConsultationHistoryViewEvent({ isReady: false, alreadyTracked: true })).toBe(false);
  });
});
