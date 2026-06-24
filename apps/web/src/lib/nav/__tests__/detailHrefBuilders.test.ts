import { describe, expect, it } from "vitest";
import { buildConciergeDetailHref } from "../buildConciergeDetailHref";
import { buildMapDetailHref } from "../buildMapDetailHref";

describe("detail href builders", () => {
  it("buildConciergeDetailHref は shrineId があれば shrine detail href を返す", () => {
    expect(buildConciergeDetailHref({ shrineId: 17, tid: 306 })).toBe("/shrines/17?ctx=concierge&tid=306");
  });

  it("buildConciergeDetailHref は shrineId がなければ place resolve href を返す", () => {
    expect(buildConciergeDetailHref({ placeId: "place-123", tid: "abc" })).toBe(
      "/shrines/resolve?place_id=place-123&ctx=concierge&tid=abc",
    );
  });

  it("buildConciergeDetailHref は shrineId/placeId がなければ undefined を返す", () => {
    expect(buildConciergeDetailHref({})).toBeUndefined();
  });

  it("buildMapDetailHref は shrineId があれば map ctx の shrine detail href を返す", () => {
    expect(buildMapDetailHref({ shrineId: 17, tid: 306 })).toBe("/shrines/17?ctx=map&tid=306");
  });

  it("buildMapDetailHref は shrineId がなければ map ctx の place resolve href を返す", () => {
    expect(buildMapDetailHref({ placeId: "place-123", tid: "abc" })).toBe(
      "/shrines/resolve?place_id=place-123&ctx=map&tid=abc",
    );
  });

  it("buildMapDetailHref は shrineId/placeId がなければ undefined を返す", () => {
    expect(buildMapDetailHref({})).toBeUndefined();
  });
});
