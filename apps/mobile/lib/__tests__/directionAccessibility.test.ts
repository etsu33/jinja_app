import { describe, expect, it } from "vitest";
import { originSearchAnnouncement, originSelectionAnnouncement } from "../../../../packages/shared/directionAccessibility";

describe("direction accessibility announcements", () => {
  it("検索中・0件・失敗・候補件数を明確に読み上げる", () => {
    expect(originSearchAnnouncement("searching")).toContain("検索中");
    expect(originSearchAnnouncement("empty")).toContain("候補が見つかりません");
    expect(originSearchAnnouncement("error")).toContain("検索できませんでした");
    expect(originSearchAnnouncement("idle", 2)).toBe("2件の候補が見つかりました。候補を選択してください。");
  });

  it("現在選択中の地点と精度を読み上げる", () => {
    expect(originSelectionAnnouncement(null)).toBe("出発地点は設定されていません。");
    expect(originSelectionAnnouncement({ latitude: 35.67, longitude: 139.65, source: "prefecture", displayName: "東京都", accuracy: "approximate" }))
      .toBe("現在の出発地点は東京都、おおよその位置です。");
  });
});
