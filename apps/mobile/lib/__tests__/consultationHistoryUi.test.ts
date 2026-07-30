import { describe, expect, it } from "vitest";

import {
  ACTION_STATE_LABEL,
  classifyThreadDetailLoadError,
  classifyThreadsLoadError,
  extractRecommendationShrineId,
  formatThreadDate,
  formatThreadDateGroupLabel,
  formatThreadDateTime,
  groupThreadsByDate,
  normalizeThreadPreview,
} from "../consultationHistoryUi";
import { HttpError, UnauthenticatedError } from "../http";
import type { ConciergeThreadListItem } from "../consultationHistory";

describe("classifyThreadsLoadError", () => {
  it("UnauthenticatedErrorはunauthenticatedに分類する", () => {
    expect(classifyThreadsLoadError(new UnauthenticatedError())).toBe("unauthenticated");
  });

  it("回帰テスト: 403(HttpError)はunauthenticatedではなくerrorに分類する(同一メッセージへ握り潰さない)", () => {
    expect(classifyThreadsLoadError(new HttpError(403, "HTTP 403: Forbidden"))).toBe("error");
  });

  it("network error等はerrorに分類する", () => {
    expect(classifyThreadsLoadError(new TypeError("Network request failed"))).toBe("error");
  });
});

describe("classifyThreadDetailLoadError", () => {
  it("UnauthenticatedErrorはunauthenticatedに分類する(401相当)", () => {
    expect(classifyThreadDetailLoadError(new UnauthenticatedError())).toBe("unauthenticated");
  });

  it("status=404のHttpErrorはnot_foundに分類する(不正または存在しないtid)", () => {
    expect(classifyThreadDetailLoadError(new HttpError(404, "HTTP 404: Not Found"))).toBe("not_found");
  });

  it("回帰テスト: status=403のHttpErrorはunauthenticated/not_foundどちらでもなくerrorに分類する", () => {
    expect(classifyThreadDetailLoadError(new HttpError(403, "HTTP 403: Forbidden"))).toBe("error");
  });

  it("status=500等その他のHttpErrorはerrorに分類する", () => {
    expect(classifyThreadDetailLoadError(new HttpError(500, "HTTP 500: Server Error"))).toBe("error");
  });

  it("network error等はerrorに分類する", () => {
    expect(classifyThreadDetailLoadError(new TypeError("Network request failed"))).toBe("error");
  });
});

describe("formatThreadDate / formatThreadDateTime / formatThreadDateGroupLabel", () => {
  it("nullはすべて未記録文言を返す", () => {
    expect(formatThreadDate(null)).toBe("日付未記録");
    expect(formatThreadDateTime(null)).toBe("日時未記録");
    expect(formatThreadDateGroupLabel(null)).toBe("日付未記録");
  });

  it("不正な日付文字列は未記録文言を返す", () => {
    expect(formatThreadDate("not-a-date")).toBe("日付未記録");
    expect(formatThreadDateTime("not-a-date")).toBe("日時未記録");
  });

  it("正しいISO日時は整形して返す", () => {
    expect(formatThreadDate("2026-01-05T00:00:00Z")).toMatch(/2026/);
    expect(formatThreadDateTime("2026-01-05T00:00:00Z")).toMatch(/2026/);
  });
});

describe("normalizeThreadPreview", () => {
  it("空・未記録は既定文言にfallbackする", () => {
    expect(normalizeThreadPreview(null)).toBe("相談内容はまだ記録されていません。");
    expect(normalizeThreadPreview("   ")).toBe("相談内容はまだ記録されていません。");
  });

  it("連続空白は1つに正規化する", () => {
    expect(normalizeThreadPreview("こんにちは\n\n次の行")).toBe("こんにちは 次の行");
  });
});

describe("groupThreadsByDate", () => {
  it("同じ日付ラベルのスレッドをまとめる", () => {
    const threads: ConciergeThreadListItem[] = [
      { id: 1, title: "A", last_message: "", last_message_at: "2026-01-05T01:00:00Z", message_count: 1 },
      { id: 2, title: "B", last_message: "", last_message_at: "2026-01-05T05:00:00Z", message_count: 1 },
      { id: 3, title: "C", last_message: "", last_message_at: "2026-01-06T01:00:00Z", message_count: 1 },
    ];

    const groups = groupThreadsByDate(threads);

    expect(groups).toHaveLength(2);
    expect(groups[0].items).toHaveLength(2);
    expect(groups[1].items).toHaveLength(1);
  });

  it("空配列は空配列を返す", () => {
    expect(groupThreadsByDate([])).toEqual([]);
  });
});

describe("extractRecommendationShrineId", () => {
  it("shrine_idを優先して数値文字列を返す", () => {
    expect(extractRecommendationShrineId({ shrine_id: 5, id: 999 })).toBe("5");
  });

  it("shrine_idが無ければidを使う", () => {
    expect(extractRecommendationShrineId({ id: 7 })).toBe("7");
  });

  it("どちらも無い/数値化できない場合はnullを返す", () => {
    expect(extractRecommendationShrineId({})).toBeNull();
    expect(extractRecommendationShrineId({ shrine_id: "abc" })).toBeNull();
  });
});

describe("ACTION_STATE_LABEL", () => {
  it("saved/visited/reflectedにラベルを持つ", () => {
    expect(ACTION_STATE_LABEL.saved).toBe("気になる登録済み");
    expect(ACTION_STATE_LABEL.visited).toBe("参拝済み");
    expect(ACTION_STATE_LABEL.reflected).toBe("振り返り済み");
  });

  it("noneにはラベルを持たない(バッジを表示しない)", () => {
    expect(ACTION_STATE_LABEL.none).toBeUndefined();
  });
});
