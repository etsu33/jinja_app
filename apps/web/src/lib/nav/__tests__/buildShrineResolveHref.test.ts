import { describe, it, expect } from "vitest";
import { buildShrineResolveHref } from "../buildShrineResolveHref";

describe("buildShrineResolveHref", () => {
  it("基本: place_id だけを付ける", () => {
    expect(buildShrineResolveHref("pid")).toBe("/shrines/resolve?place_id=pid");
  });

  it("ctx と tid を付ける（ctxはmap/concierge）", () => {
    const href = buildShrineResolveHref("pid", { ctx: "map", tid: "t1" });
    expect(href).toContain("/shrines/resolve?");
    expect(href).toContain("place_id=pid");
    expect(href).toContain("ctx=map");
    expect(href).toContain("tid=t1");
  });

  it("query は toast のみ許可し、分析用 query は無視される", () => {
    const href = buildShrineResolveHref("pid", {
      query: {
        toast: "ok",
        mode: "need",
        flow: "A",
        hasBirthdate: "true",
        recommendationCount: "3",
        a: "",
        b: "   ",
        c: null,
        d: undefined,
      },
    });

    const url = new URL(href, "http://localhost");
    const p = url.searchParams;

    expect(url.pathname).toBe("/shrines/resolve");
    expect(p.get("place_id")).toBe("pid");
    expect(p.get("toast")).toBe("ok");
    expect(p.has("mode")).toBe(false);
    expect(p.has("flow")).toBe(false);
    expect(p.has("hasBirthdate")).toBe(false);
    expect(p.has("recommendationCount")).toBe(false);
    expect(p.has("a")).toBe(false);
    expect(p.has("b")).toBe(false);
    expect(p.has("c")).toBe(false);
    expect(p.has("d")).toBe(false);
  });

  it("query に place_id/ctx/tid が入っていても、必須パラメータが上書きする", () => {
    const href = buildShrineResolveHref("pid-real", {
      ctx: "concierge",
      tid: "tid-real",
      query: {
        place_id: "pid-fake",
        ctx: "map",
        tid: "tid-fake",
        toast: "saved",
        extra: "x",
      },
    });

    expect(href).toContain("toast=saved");
    expect(href).toContain("place_id=pid-real");
    expect(href).toContain("ctx=concierge");
    expect(href).toContain("tid=tid-real");
    expect(href).not.toContain("place_id=pid-fake");
    expect(href).not.toContain("ctx=map");
    expect(href).not.toContain("tid=tid-fake");
    expect(href).not.toContain("extra=");
  });

  it("ctx=null は付与されない。tid は空白なら付与されない", () => {
    const href = buildShrineResolveHref("pid", { ctx: null, tid: "   " });
    expect(href).toBe("/shrines/resolve?place_id=pid");
  });
});
