import { describe, it, expect } from "vitest";
import { detailHrefFromRecommendation } from "../detailHref";

describe("detailHrefFromRecommendation", () => {
  it("registered: shrine_id があれば /shrines/:id を返す（ctx/tid 付き）", () => {
    const href = detailHrefFromRecommendation({ shrine_id: 100001, place_id: "ChIJxxx" } as any, {
      ctx: "concierge",
      tid: 139,
    });
    expect(href).toBe("/shrines/100001?ctx=concierge&tid=139");
  });

  it("unregistered: shrine_id が無く place_id があれば /shrines/resolve にフォールバックする", () => {
    const href = detailHrefFromRecommendation({ place_id: "ChIJxxx" } as any, {
      ctx: "concierge",
      tid: 139,
    });
    expect(href).toBe("/shrines/resolve?place_id=ChIJxxx&ctx=concierge&tid=139");
  });

  it("placeId / place_id どちらでも拾う（揺れ耐性）", () => {
    expect(detailHrefFromRecommendation({ placeId: "A" } as any)).toBe("/shrines/resolve?place_id=A&ctx=concierge");
    expect(detailHrefFromRecommendation({ place_id: "B" } as any)).toBe("/shrines/resolve?place_id=B&ctx=concierge");
  });

  it("どちらも無ければ null（導線を出さない用）", () => {
    expect(detailHrefFromRecommendation({} as any)).toBeNull();
  });

  it("分析用 query は URL に載せない", () => {
    const analytics = {
      ctx: "concierge",
      tid: 139,
      mode: "need" as const,
      flow: "A" as const,
      hasBirthdate: true,
      recommendationCount: 3,
    };

    expect(detailHrefFromRecommendation({ shrine_id: 100001 } as any, analytics)).toBe(
      "/shrines/100001?ctx=concierge&tid=139",
    );
    expect(detailHrefFromRecommendation({ place_id: "ChIJxxx" } as any, analytics)).toBe(
      "/shrines/resolve?place_id=ChIJxxx&ctx=concierge&tid=139",
    );
  });
});

// ---------------------------------------------------------------------------
// F-3.1 / F-4: identity resolution status を潰さないことの回帰テスト。
//
// 旧実装（pickShrineId）は number | null しか返さなかったため、
// 「identity が無い」と「identity が壊れている／食い違っている」が同じ null に
// 潰れ、どちらも place_id fallback へ落ちていた。conflict / invalid が
// /shrines/resolve へ流れるのは FAIL_CLOSED_ON_CONFLICT 違反であり、
// F-6 の place_id shadow identity 経路へ入る。
//
// docs/audit/shared-shrine-identity-resolver-design.md §13
// ---------------------------------------------------------------------------
describe("detailHrefFromRecommendation: F-3.1 identity resolution status", () => {
  it("conflict（shrine_id と shrineId が食い違う）は null。place_id へ落とさない", () => {
    const href = detailHrefFromRecommendation({
      shrine_id: 42,
      shrineId: 99,
      place_id: "ChIJxxx",
    } as any);

    expect(href).toBeNull();
    // null であること自体が「/shrines/resolve を生成していない」ことの証明だが、
    // 退行時に何が起きたか読めるよう明示的にも確認する。
    expect(String(href)).not.toContain("/shrines/resolve");
  });

  it("conflict（shrine_id と shrine.id が食い違う）も null。place_id へ落とさない", () => {
    const href = detailHrefFromRecommendation({
      shrine_id: 42,
      shrine: { id: 99 },
      place_id: "ChIJxxx",
    } as any);

    expect(href).toBeNull();
  });

  it("invalid（正規化できない shrine_id）は null。place_id へ落とさない", () => {
    const href = detailHrefFromRecommendation({
      shrine_id: "bad",
      place_id: "ChIJxxx",
    } as any);

    expect(href).toBeNull();
  });

  it("invalid の各種（0 / 負数 / 浮動小数 / boolean / 空文字）も null", () => {
    for (const bad of [0, -1, 1.5, true, "", "   "]) {
      expect(detailHrefFromRecommendation({ shrine_id: bad, place_id: "ChIJxxx" } as any)).toBeNull();
    }
  });

  it("absent（許可 alias が1つも無い）は既存の /shrines/resolve 挙動を保つ", () => {
    expect(detailHrefFromRecommendation({ place_id: "ChIJxxx" } as any)).toBe(
      "/shrines/resolve?place_id=ChIJxxx&ctx=concierge",
    );
  });

  it("shrine_id: null（未登録候補の backend 表現）は absent として place_id へ落ちる", () => {
    // backend concierge_candidate_normalize.normalize_candidate() が未登録候補の
    // shrine_id を None で埋めるため、ここを invalid にすると導線が全滅する。
    expect(detailHrefFromRecommendation({ shrine_id: null, place_id: "ChIJxxx" } as any)).toBe(
      "/shrines/resolve?place_id=ChIJxxx&ctx=concierge",
    );
  });

  it("generic `id` は identity にならない（id だけなら place_id fallback）", () => {
    expect(detailHrefFromRecommendation({ id: 999, place_id: "ChIJxxx" } as any)).toBe(
      "/shrines/resolve?place_id=ChIJxxx&ctx=concierge",
    );
    expect(detailHrefFromRecommendation({ id: 999 } as any)).toBeNull();
  });

  it("shrine_id と generic id が食い違っても conflict にはならず shrine_id を使う", () => {
    expect(detailHrefFromRecommendation({ shrine_id: 42, id: 999 } as any, { ctx: "concierge" })).toBe(
      "/shrines/42?ctx=concierge",
    );
  });

  it("shrineId / shrine.id の alias は registered_compat として解決される", () => {
    expect(detailHrefFromRecommendation({ shrineId: 100001 } as any, { ctx: "concierge" })).toBe(
      "/shrines/100001?ctx=concierge",
    );
    expect(detailHrefFromRecommendation({ shrine: { id: 100001 } } as any, { ctx: "concierge" })).toBe(
      "/shrines/100001?ctx=concierge",
    );
  });

  it("文字列 shrine_id は number へ正規化されたうえで href になる", () => {
    expect(detailHrefFromRecommendation({ shrine_id: "100001" } as any, { ctx: "concierge" })).toBe(
      "/shrines/100001?ctx=concierge",
    );
  });
});
