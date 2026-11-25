// H-3（zod 4.4.3 → 4.6.6）: pins the parse / reject behaviour of the Web API schemas.
import { describe, expect, it } from "vitest";
import { DirectionsResponse, NearestResponse, PopularsResponse, ShrineLite } from "../api";

const shrine = { id: 1, name: "明治神宮", lat: 35.676, lng: 139.699 };

describe("ShrineLite", () => {
  it("accepts the minimal shape and keeps optional / nullable address as given", () => {
    expect(ShrineLite.parse(shrine)).toEqual(shrine);
    expect(ShrineLite.parse({ ...shrine, address: null })).toEqual({ ...shrine, address: null });
    expect(ShrineLite.parse({ ...shrine, address: "東京都" }).address).toBe("東京都");
  });

  it("strips unknown keys（default object behaviour）", () => {
    expect(ShrineLite.parse({ ...shrine, extra: "x" })).toEqual(shrine);
  });

  it.each([
    ["non-integer id", { ...shrine, id: 1.5 }],
    ["string id", { ...shrine, id: "1" }],
    ["missing name", { id: 1, lat: 0, lng: 0 }],
    ["string lat", { ...shrine, lat: "35" }],
    ["NaN lng", { ...shrine, lng: Number.NaN }],
    ["numeric address", { ...shrine, address: 1 }],
  ])("rejects %s", (_label, value) => {
    const r = ShrineLite.safeParse(value);
    expect(r.success).toBe(false);
  });

  it("reports the failing path in issues", () => {
    const r = ShrineLite.safeParse({ ...shrine, id: "1" });
    expect(r.success).toBe(false);
    if (!r.success) expect(r.error.issues.map((i) => i.path.join("."))).toContain("id");
  });
});

describe("response schemas", () => {
  it("PopularsResponse: integer period_days is optional", () => {
    expect(PopularsResponse.parse({ items: [{ shrine, score: 0.5 }] }).items).toHaveLength(1);
    expect(PopularsResponse.safeParse({ items: [{ shrine, score: 1, period_days: 1.2 }] }).success).toBe(false);
  });

  it("NearestResponse: integer distance, nullable optional minutes", () => {
    const ok = { items: [{ shrine, distance_m: 120, walking_minutes: null }] };
    expect(NearestResponse.parse(ok)).toEqual(ok);
    expect(NearestResponse.safeParse({ items: [{ shrine, distance_m: 1.5 }] }).success).toBe(false);
    expect(NearestResponse.safeParse({ items: "x" }).success).toBe(false);
  });

  it("DirectionsResponse: mode enum, integer distance", () => {
    const ok = { mode: "walking", distance_m: 800, duration_min: 10.5, polyline: "abc" };
    expect(DirectionsResponse.parse(ok)).toEqual(ok);
    expect(DirectionsResponse.safeParse({ ...ok, mode: "cycling" }).success).toBe(false);
    expect(DirectionsResponse.safeParse({ ...ok, distance_m: 1.1 }).success).toBe(false);
    expect(DirectionsResponse.safeParse({ ...ok, polyline: undefined }).success).toBe(false);
  });
});
