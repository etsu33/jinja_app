import { describe, expect, it } from "vitest";

import { buildPayloadFromUnified } from "../buildPayloadFromUnified";
import { highlightHrefFromRecommendation } from "../detailHref";
import { normalizeHighlightPick } from "../highlightPick";

// 見どころ単位の推薦 PR-3：backend の highlight_pick を画面用に整える。

const rawPick = {
  highlight_id: 2,
  shrine_id: 61,
  name: "芸能浅間神社",
  need_tag: "career",
  answer_text: "焼けた社殿を建て直した由来が、今の気持ちと重なるかもしれない。",
};

describe("highlightHrefFromRecommendation", () => {
  it("登録済みの神社は詳細の見どころの位置へ（ctx・tid つき）", () => {
    expect(highlightHrefFromRecommendation({ shrine_id: 61 }, 2, { ctx: "concierge", tid: 9 })).toBe(
      "/shrines/61?ctx=concierge&tid=9#shrine-highlight-2",
    );
  });

  it("place_id だけ（未登録）は null", () => {
    expect(highlightHrefFromRecommendation({ place_id: "P1" }, 2)).toBeNull();
  });

  it("見どころの神社と推薦の神社が違えば null", () => {
    expect(highlightHrefFromRecommendation({ shrine_id: 61 }, 2, { expectedShrineId: 62 })).toBeNull();
  });

  it("見どころの id が不正なら null", () => {
    expect(highlightHrefFromRecommendation({ shrine_id: 61 }, 0)).toBeNull();
  });
});

describe("normalizeHighlightPick", () => {
  it("そろっていれば画面用に整える", () => {
    expect(normalizeHighlightPick({ shrine_id: 61, highlight_pick: rawPick }, { ctx: "concierge", tid: 9 })).toEqual({
      highlightId: 2,
      name: "芸能浅間神社",
      needTag: "career",
      answerText: "焼けた社殿を建て直した由来が、今の気持ちと重なるかもしれない。",
      href: "/shrines/61?ctx=concierge&tid=9#shrine-highlight-2",
    });
  });

  it("無い・null なら null", () => {
    expect(normalizeHighlightPick({ shrine_id: 61 })).toBeNull();
    expect(normalizeHighlightPick({ shrine_id: 61, highlight_pick: null })).toBeNull();
  });

  it.each([
    ["name", { name: "  " }],
    ["answer_text", { answer_text: "" }],
    ["highlight_id", { highlight_id: null }],
    ["need_tag", { need_tag: undefined }],
  ])("%s が欠けていれば null", (_label, override) => {
    expect(normalizeHighlightPick({ shrine_id: 61, highlight_pick: { ...rawPick, ...override } })).toBeNull();
  });

  it("別の神社の見どころなら null", () => {
    expect(normalizeHighlightPick({ shrine_id: 99, highlight_pick: rawPick })).toBeNull();
  });
});

describe("buildPayloadFromUnified - highlightPick", () => {
  const baseFilterState: any = {
    isOpen: false,
    goriyakuTags: [],
    selectedTagIds: [],
    tagsLoading: false,
    tagsError: null,
    extraCondition: "",
  };

  function itemsOf(recommendations: any[]) {
    const p = buildPayloadFromUnified({ data: { recommendations }, thread: { id: 5 } } as any, baseFilterState);
    return (p?.sections.find((s: any) => s.type === "recommendations") as any)?.items;
  }

  it("登録済みの推薦に highlightPick が入る", () => {
    const items = itemsOf([{ shrine_id: 61, display_name: "花園神社", reason: "R", highlight_pick: rawPick }]);
    expect(items[0].highlightPick?.href).toBe("/shrines/61?ctx=concierge&tid=5#shrine-highlight-2");
  });

  it("無ければ null", () => {
    const items = itemsOf([{ shrine_id: 61, display_name: "花園神社", reason: "R" }]);
    expect(items[0].highlightPick).toBeNull();
  });
});
