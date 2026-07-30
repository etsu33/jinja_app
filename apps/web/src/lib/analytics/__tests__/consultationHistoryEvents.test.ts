import { beforeEach, describe, expect, it, vi } from "vitest";

const trackMock = vi.fn();

vi.mock("@/lib/analytics/track", () => ({
  track: (...args: unknown[]) => trackMock(...args),
}));

import {
  trackConsultationHistoryDetailOpened,
  trackConsultationHistoryDetailViewed,
  trackConsultationHistoryEntryClicked,
  trackConsultationHistoryListViewed,
  trackConsultationHistoryShrineOpened,
} from "../consultationHistoryEvents";

const FORBIDDEN_KEYS = [
  "consultationSummary",
  "title",
  "content",
  "message",
  "reason",
  "recommendationReason",
  "address",
  "lat",
  "lng",
  "latitude",
  "longitude",
];

describe("consultationHistoryEvents", () => {
  beforeEach(() => {
    trackMock.mockReset();
  });

  it("trackConsultationHistoryEntryClicked: event名・platform・固定sourceを送る", () => {
    trackConsultationHistoryEntryClicked();

    expect(trackMock).toHaveBeenCalledWith("consultation_history_entry_clicked", {
      platform: "web",
      source: "mypage",
    });
  });

  it("trackConsultationHistoryListViewed: historyCountを送る", () => {
    trackConsultationHistoryListViewed({ historyCount: 3 });

    expect(trackMock).toHaveBeenCalledWith("consultation_history_list_viewed", {
      platform: "web",
      source: "consultation_history",
      historyCount: 3,
    });
  });

  it("trackConsultationHistoryListViewed: 0件でもhistoryCount:0を送る", () => {
    trackConsultationHistoryListViewed({ historyCount: 0 });

    expect(trackMock).toHaveBeenCalledWith(
      "consultation_history_list_viewed",
      expect.objectContaining({ historyCount: 0 }),
    );
  });

  it("trackConsultationHistoryDetailOpened: threadId・positionを送る", () => {
    trackConsultationHistoryDetailOpened({ threadId: 42, position: 1 });

    expect(trackMock).toHaveBeenCalledWith("consultation_history_detail_opened", {
      platform: "web",
      source: "consultation_history_list",
      threadId: 42,
      position: 1,
    });
  });

  it("trackConsultationHistoryDetailViewed: threadId・recommendationCount・messageCountを送る", () => {
    trackConsultationHistoryDetailViewed({ threadId: "42", recommendationCount: 2, messageCount: 5 });

    expect(trackMock).toHaveBeenCalledWith("consultation_history_detail_viewed", {
      platform: "web",
      source: "consultation_history_detail",
      threadId: "42",
      recommendationCount: 2,
      messageCount: 5,
    });
  });

  it("trackConsultationHistoryShrineOpened: threadId・shrineId・recommendationRankを送る", () => {
    trackConsultationHistoryShrineOpened({ threadId: 42, shrineId: 5, recommendationRank: 2 });

    expect(trackMock).toHaveBeenCalledWith("consultation_history_shrine_opened", {
      platform: "web",
      source: "consultation_history_detail",
      threadId: 42,
      shrineId: 5,
      recommendationRank: 2,
    });
  });

  it("禁止Payload: いずれのEventも相談本文・タイトル・住所等のkeyを含まない", () => {
    trackConsultationHistoryEntryClicked();
    trackConsultationHistoryListViewed({ historyCount: 1 });
    trackConsultationHistoryDetailOpened({ threadId: 1, position: 1 });
    trackConsultationHistoryDetailViewed({ threadId: 1, recommendationCount: 1, messageCount: 1 });
    trackConsultationHistoryShrineOpened({ threadId: 1, shrineId: 1, recommendationRank: 1 });

    for (const call of trackMock.mock.calls) {
      const payload = call[1] as Record<string, unknown>;
      for (const forbiddenKey of FORBIDDEN_KEYS) {
        expect(payload).not.toHaveProperty(forbiddenKey);
      }
    }
  });

  it("Helperはtrack()を薄くラップするのみで、独自のtry/catchを持たない", () => {
    // track()自体(apps/web/src/lib/analytics/track.ts)が本番環境での送信失敗を
    // 内部で握り潰す実装であることは track.test.ts で検証済み。
    // ここでは、本Helperがtrack()の例外をさらに握り潰す独自のtry/catchを持たない
    // (=障害の握り潰しをtrack()へ一本化している)ことを、mockの例外がそのまま
    // 伝播することで確認する。
    trackMock.mockImplementationOnce(() => {
      throw new Error("track failed");
    });

    expect(() => trackConsultationHistoryEntryClicked()).toThrow("track failed");
  });
});
