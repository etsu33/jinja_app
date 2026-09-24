import { describe, expect, it } from "vitest";

import { resolveShrineId, resolveShrineIdentity } from "../resolveShrineId";

// F-3.1 / F-4 の resolver 契約テスト。
//   docs/audit/shared-shrine-identity-resolver-design.md §13（F-3.1）/ §14（F-4）
//
// 検証する契約:
//   - status が absent / invalid / conflict / resolved を潰さずに保つこと
//   - generic `id` / place_id が identity に一切参加しないこと
//   - conflict が FAIL_CLOSED であること
//   - wrapper が resolveShrineIdentity に委譲するだけであること

describe("resolveShrineIdentity: public_strict", () => {
  it("1. shrine_id: 42 -> resolved 42", () => {
    expect(resolveShrineIdentity({ shrine_id: 42 }, "public_strict")).toEqual({
      status: "resolved",
      shrineId: 42,
    });
  });

  it("2. shrine_id: \"42\" -> resolved 42（number へ正規化される）", () => {
    expect(resolveShrineIdentity({ shrine_id: "42" }, "public_strict")).toEqual({
      status: "resolved",
      shrineId: 42,
    });
  });

  it("3. generic id のみ -> absent（id は identity authority ではない）", () => {
    expect(resolveShrineIdentity({ id: 999 }, "public_strict")).toEqual({
      status: "absent",
      shrineId: null,
    });
  });

  it("4. shrineId のみ -> absent（public_strict は alias を許可しない）", () => {
    expect(resolveShrineIdentity({ shrineId: 42 }, "public_strict")).toEqual({
      status: "absent",
      shrineId: null,
    });
  });

  it("5. shrine.id のみ -> absent（public_strict は alias を許可しない）", () => {
    expect(resolveShrineIdentity({ shrine: { id: 42 } }, "public_strict")).toEqual({
      status: "absent",
      shrineId: null,
    });
  });

  it("6. 正規化できない shrine_id -> invalid（absent と区別される）", () => {
    const rejected: unknown[] = [0, -1, 1.5, "", "   ", "abc", "1.5", "-1", "1e3", NaN, Infinity, -Infinity, {}, []];
    for (const value of rejected) {
      expect(resolveShrineIdentity({ shrine_id: value }, "public_strict")).toEqual({
        status: "invalid",
        shrineId: null,
      });
    }
  });
});

describe("resolveShrineIdentity: registered_compat", () => {
  it("7. shrine_id -> resolved", () => {
    expect(resolveShrineIdentity({ shrine_id: 42 }, "registered_compat")).toEqual({
      status: "resolved",
      shrineId: 42,
    });
  });

  it("8. shrineId -> resolved", () => {
    expect(resolveShrineIdentity({ shrineId: 42 }, "registered_compat")).toEqual({
      status: "resolved",
      shrineId: 42,
    });
  });

  it("9. shrine.id -> resolved", () => {
    expect(resolveShrineIdentity({ shrine: { id: 42 } }, "registered_compat")).toEqual({
      status: "resolved",
      shrineId: 42,
    });
  });

  it("10. 全 alias が正規化後に一致 -> resolved（\"42\" と 42 は一致扱い）", () => {
    expect(
      resolveShrineIdentity({ shrine_id: 42, shrineId: "42", shrine: { id: 42 } }, "registered_compat"),
    ).toEqual({ status: "resolved", shrineId: 42 });
  });

  it("11. shrine_id 42 + shrineId 99 -> conflict（先頭値を黙って採らない）", () => {
    expect(resolveShrineIdentity({ shrine_id: 42, shrineId: 99 }, "registered_compat")).toEqual({
      status: "conflict",
      shrineId: null,
    });
  });

  it("12. shrine_id 42 + shrine.id 99 -> conflict", () => {
    expect(resolveShrineIdentity({ shrine_id: 42, shrine: { id: 99 } }, "registered_compat")).toEqual({
      status: "conflict",
      shrineId: null,
    });
  });

  it("13. generic id=999 は shrine_id=42 に影響しない（conflict にもならない）", () => {
    expect(resolveShrineIdentity({ shrine_id: 42, id: 999 }, "registered_compat")).toEqual({
      status: "resolved",
      shrineId: 42,
    });
    expect(resolveShrineIdentity({ shrine_id: 42, id: 999 }, "public_strict")).toEqual({
      status: "resolved",
      shrineId: 42,
    });
  });

  it("14. place_id は identity に参加しない（place_id のみなら absent）", () => {
    expect(resolveShrineIdentity({ place_id: "ChIJxxx" }, "registered_compat")).toEqual({
      status: "absent",
      shrineId: null,
    });
    expect(resolveShrineIdentity({ placeId: "ChIJxxx" }, "registered_compat")).toEqual({
      status: "absent",
      shrineId: null,
    });
    expect(resolveShrineIdentity({ place: { id: "ChIJxxx" } }, "registered_compat")).toEqual({
      status: "absent",
      shrineId: null,
    });
    // place_id が同居しても shrine_id の解決結果は変わらない。
    expect(resolveShrineIdentity({ shrine_id: 42, place_id: "ChIJxxx" }, "registered_compat")).toEqual({
      status: "resolved",
      shrineId: 42,
    });
  });

  it("15. boolean は invalid（Number(true) === 1 で Shrine 1 に化けさせない）", () => {
    expect(resolveShrineIdentity({ shrine_id: true }, "registered_compat")).toEqual({
      status: "invalid",
      shrineId: null,
    });
    expect(resolveShrineIdentity({ shrine_id: false }, "registered_compat")).toEqual({
      status: "invalid",
      shrineId: null,
    });
  });

  it("16. object でない入力 -> absent（throw しない）", () => {
    const nonObjects: unknown[] = [null, undefined, 42, "42", true, false, Symbol("x"), () => 1];
    for (const input of nonObjects) {
      expect(() => resolveShrineIdentity(input, "registered_compat")).not.toThrow();
      expect(resolveShrineIdentity(input, "registered_compat")).toEqual({
        status: "absent",
        shrineId: null,
      });
    }
  });
});

describe("resolveShrineIdentity: presence / precedence の追加契約", () => {
  it("shrine_id: null は absent（invalid ではない）", () => {
    // backend の concierge_candidate_normalize.normalize_candidate() が未登録候補に
    // 対して shrine_id を None で埋めるため。ここを invalid にすると place_id 導線が
    // 全滅する（docs/audit/shared-shrine-identity-resolver-design.md §13.3）。
    expect(resolveShrineIdentity({ shrine_id: null, place_id: "ChIJxxx" }, "registered_compat")).toEqual({
      status: "absent",
      shrineId: null,
    });
    expect(resolveShrineIdentity({ shrine_id: undefined }, "registered_compat")).toEqual({
      status: "absent",
      shrineId: null,
    });
  });

  it("有効な alias と壊れた alias が同居した場合は invalid が勝つ（fail closed）", () => {
    expect(resolveShrineIdentity({ shrine_id: 42, shrineId: "bad" }, "registered_compat")).toEqual({
      status: "invalid",
      shrineId: null,
    });
  });

  it("shrine が object でなければ shrine.id は present 扱いにならない", () => {
    expect(resolveShrineIdentity({ shrine: null }, "registered_compat")).toEqual({
      status: "absent",
      shrineId: null,
    });
    expect(resolveShrineIdentity({ shrine: "42" }, "registered_compat")).toEqual({
      status: "absent",
      shrineId: null,
    });
  });
});

describe("resolveShrineId: convenience wrapper", () => {
  it("17. resolved -> number を返す", () => {
    expect(resolveShrineId({ shrine_id: 42 }, "public_strict")).toBe(42);
    expect(resolveShrineId({ shrine_id: "42" }, "public_strict")).toBe(42);
    expect(resolveShrineId({ shrineId: 7 }, "registered_compat")).toBe(7);
  });

  it("18. absent / invalid / conflict -> すべて null を返す", () => {
    expect(resolveShrineId({ id: 999 }, "public_strict")).toBeNull();
    expect(resolveShrineId({ shrine_id: "bad" }, "public_strict")).toBeNull();
    expect(resolveShrineId({ shrine_id: 42, shrineId: 99 }, "registered_compat")).toBeNull();
  });

  it("wrapper は resolveShrineIdentity.shrineId をそのまま返す（実装は1つ）", () => {
    const inputs: unknown[] = [
      { shrine_id: 42 },
      { shrine_id: "42", shrineId: 42 },
      { shrine_id: 42, shrineId: 99 },
      { shrine_id: "bad" },
      { id: 999 },
      null,
    ];
    for (const input of inputs) {
      expect(resolveShrineId(input, "registered_compat")).toBe(
        resolveShrineIdentity(input, "registered_compat").shrineId,
      );
      expect(resolveShrineId(input, "public_strict")).toBe(
        resolveShrineIdentity(input, "public_strict").shrineId,
      );
    }
  });
});
