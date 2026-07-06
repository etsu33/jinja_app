import { describe, it, expect } from "vitest";
import { buildShrineHref } from "../buildShrineHref";

describe("buildShrineHref", () => {
  it("基本: /shrines/:id（idはencode）", () => {
    expect(buildShrineHref(123)).toBe("/shrines/123");
    expect(buildShrineHref("a b")).toBe("/shrines/a%20b");
  });

  it("ctx/tid をクエリに載せる。tidはnull/undefined/空白は無視", () => {
    expect(buildShrineHref(1, { ctx: "concierge", tid: 99 })).toBe("/shrines/1?ctx=concierge&tid=99");
    expect(buildShrineHref(1, { tid: "   " })).toBe("/shrines/1");
    expect(buildShrineHref(1, { tid: "" })).toBe("/shrines/1");
    expect(buildShrineHref(1, { tid: null })).toBe("/shrines/1");
  });

  it("query: place_id/toast のみ許可し、それ以外は無視", () => {
    const href = buildShrineHref(1, {
      query: {
        toast: "ok",
        place_id: "abc",
        mode: "need",
        flow: "A",
        recommendationReason: "long text",
        empty: "",
        space: "   ",
        n: 0,
        t: true,
        f: false,
        nu: null,
        un: undefined,
      },
    });

    const url = new URL(href, "http://localhost");
    const p = url.searchParams;

    expect(url.pathname).toBe("/shrines/1");
    expect(p.get("toast")).toBe("ok");
    expect(p.get("place_id")).toBe("abc");
    expect(p.has("mode")).toBe(false);
    expect(p.has("flow")).toBe(false);
    expect(p.has("recommendationReason")).toBe(false);
    expect(p.has("empty")).toBe(false);
    expect(p.has("space")).toBe(false);
    expect(p.has("n")).toBe(false);
    expect(p.has("t")).toBe(false);
    expect(p.has("f")).toBe(false);
    expect(p.has("nu")).toBe(false);
    expect(p.has("un")).toBe(false);
  });

  it("query 内の ctx/tid は opts 相当として扱う", () => {
    expect(
      buildShrineHref(1, {
        query: { ctx: "concierge", tid: "42", toast: "saved" },
      }),
    ).toBe("/shrines/1?ctx=concierge&tid=42&toast=saved");
  });

  it("subpath: 先頭スラッシュを除去して付与。空白/nullは無視", () => {
    expect(buildShrineHref(1, { subpath: "goshuins" })).toBe("/shrines/1/goshuins");
    expect(buildShrineHref(1, { subpath: "/goshuins" })).toBe("/shrines/1/goshuins");
    expect(buildShrineHref(1, { subpath: "   " })).toBe("/shrines/1");
    expect(buildShrineHref(1, { subpath: null })).toBe("/shrines/1");
  });

  it("hash: #あり/なし両対応で末尾に付与。空白は無視", () => {
    expect(buildShrineHref(1, { hash: "goshuins" })).toBe("/shrines/1#goshuins");
    expect(buildShrineHref(1, { hash: "#goshuins" })).toBe("/shrines/1#goshuins");
    expect(buildShrineHref(1, { hash: "   " })).toBe("/shrines/1");
  });

  it("全部盛り", () => {
    const href = buildShrineHref("x", {
      ctx: "concierge",
      tid: "42",
      query: { place_id: "abc", toast: true },
      subpath: "/goshuins",
      hash: "#top",
    });

    expect(href).toContain("/shrines/x/goshuins?");
    expect(href).toContain("ctx=concierge");
    expect(href).toContain("tid=42");
    expect(href).toContain("place_id=abc");
    expect(href).toContain("toast=1");
    expect(href.endsWith("#top")).toBe(true);
  });
});
