import { describe, expect, it } from "vitest";

import type { DetailFactSection } from "@/components/shrine/detail/types";
import type { ShrineHighlight } from "@/lib/api/types";
import {
  attachHighlightLinksToFactSection,
  buildShrineHighlightSection,
  formatObservedOn,
  shrineHighlightAnchorId,
  shrineHistoryAnchorId,
} from "@/lib/shrine/buildShrineHighlightSection";

function highlight(overrides: Partial<ShrineHighlight> = {}): ShrineHighlight {
  return {
    id: 1,
    category: "architecture",
    sort_order: 0,
    name: "拝殿の彫刻",
    description: "正面上部の龍の彫刻を見る。",
    historical_connection: "",
    location_hint: "",
    linked_history_ids: [],
    sources: [],
    observed_on: null,
    ...overrides,
  };
}

function factSection(historyIds: number[]): DetailFactSection {
  return {
    kind: "fact",
    heading: "神社について",
    deities: [],
    histories: historyIds.map((id, index) => ({
      id,
      history_type: "tradition",
      history_type_label: "伝承",
      title: `伝承${id}`,
      content: "本文",
      period_text: "",
      sort_order: index,
      displayState: "full" as const,
    })),
  };
}

describe("buildShrineHighlightSection", () => {
  it("見どころが無ければ null（節を出さない）", () => {
    expect(buildShrineHighlightSection({}, null)).toBeNull();
    expect(buildShrineHighlightSection({ highlights: [] }, null)).toBeNull();
  });

  it("文章を整え、カテゴリーを日本語の名前にする", () => {
    const section = buildShrineHighlightSection(
      {
        highlights: [
          highlight({
            name: " 拝殿の彫刻 ",
            historical_connection: "再建のときに彫られた。",
            location_hint: "鳥居をくぐって正面",
            observed_on: "2026-11-21",
          }),
        ],
      },
      null,
    );
    expect(section?.heading).toBe("ここで見られるもの");
    expect(section?.items[0]).toMatchObject({
      id: 1,
      categoryLabel: "建築",
      name: "拝殿の彫刻",
      historicalConnection: "再建のときに彫られた。",
      locationHint: "鳥居をくぐって正面",
      observedOnLabel: "2026年11月21日",
    });
  });

  it("未知のカテゴリーは内部の英語キーを出さない", () => {
    const section = buildShrineHighlightSection({ highlights: [highlight({ category: "unknown_kind" })] }, null);
    expect(section?.items[0].categoryLabel).toBe("");
  });

  it("参道の順番（sort_order, id）で並べる", () => {
    const section = buildShrineHighlightSection(
      {
        highlights: [
          highlight({ id: 3, sort_order: 2, name: "拝殿" }),
          highlight({ id: 2, sort_order: 0, name: "手水舎" }),
          highlight({ id: 1, sort_order: 0, name: "鳥居" }),
        ],
      },
      null,
    );
    expect(section?.items.map((item) => item.name)).toEqual(["鳥居", "手水舎", "拝殿"]);
  });

  it("名前か説明が空のものは出さない", () => {
    const section = buildShrineHighlightSection(
      { highlights: [highlight({ id: 1, description: "  " }), highlight({ id: 2, name: "" }), highlight({ id: 3 })] },
      null,
    );
    expect(section?.items.map((item) => item.id)).toEqual([3]);
  });

  it("由緒・歴史へのリンクは Fact Section に出ているものだけ（リンク切れを作らない）", () => {
    const section = buildShrineHighlightSection(
      { highlights: [highlight({ linked_history_ids: [20, 99, 10] })] },
      factSection([10, 20]),
    );
    expect(section?.items[0].linkedHistories).toEqual([
      { id: 20, title: "伝承20" },
      { id: 10, title: "伝承10" },
    ]);
  });

  it("Fact Section が無ければ由緒・歴史へのリンクは出さない", () => {
    const section = buildShrineHighlightSection({ highlights: [highlight({ linked_history_ids: [10] })] }, null);
    expect(section?.items[0].linkedHistories).toEqual([]);
  });
});

describe("attachHighlightLinksToFactSection", () => {
  it("由緒・歴史に、それを確かめられる見どころへのリンクを足す", () => {
    const facts = factSection([10, 20]);
    const highlights = buildShrineHighlightSection(
      {
        highlights: [
          highlight({ id: 1, name: "龍の彫刻", linked_history_ids: [10] }),
          highlight({ id: 2, sort_order: 1, name: "御神木", linked_history_ids: [10, 20] }),
        ],
      },
      facts,
    );
    const result = attachHighlightLinksToFactSection(facts, highlights);
    expect(result?.histories[0].highlightLinks).toEqual([
      { id: 1, name: "龍の彫刻" },
      { id: 2, name: "御神木" },
    ]);
    expect(result?.histories[1].highlightLinks).toEqual([{ id: 2, name: "御神木" }]);
    // 元の Fact Section は書き換えない
    expect(facts.histories[0].highlightLinks).toBeUndefined();
  });

  it("つながりが無ければ Fact Section をそのまま返す", () => {
    const facts = factSection([10]);
    const highlights = buildShrineHighlightSection({ highlights: [highlight()] }, facts);
    expect(attachHighlightLinksToFactSection(facts, highlights)).toBe(facts);
    expect(attachHighlightLinksToFactSection(facts, null)).toBe(facts);
    expect(attachHighlightLinksToFactSection(null, highlights)).toBeNull();
  });
});

describe("補助関数", () => {
  it("観察日を日本語の日付にする。形が違えば null", () => {
    expect(formatObservedOn("2026-01-05")).toBe("2026年1月5日");
    expect(formatObservedOn("2026/01/05")).toBeNull();
    expect(formatObservedOn(null)).toBeNull();
  });

  it("画面内リンクの id", () => {
    expect(shrineHighlightAnchorId(3)).toBe("shrine-highlight-3");
    expect(shrineHistoryAnchorId(4)).toBe("shrine-history-4");
  });
});
