import { describe, expect, it } from "vitest";

import { buildTravelChatPayload, pickTravelRecommendations } from "../buildTravelChatPayload";

describe("buildTravelChatPayload", () => {
  it("sends travel mode and English, with the current location", () => {
    expect(buildTravelChatPayload("  Somewhere quiet  ", { lat: 35.68, lng: 139.76 })).toEqual({
      query: "Somewhere quiet",
      mode: "travel",
      language: "en",
      lat: 35.68,
      lng: 139.76,
    });
  });

  it("omits lat/lng when the location is unavailable", () => {
    expect(buildTravelChatPayload("quiet forest", null)).toEqual({
      query: "quiet forest",
      mode: "travel",
      language: "en",
    });
  });

  it("returns null for an empty consultation", () => {
    expect(buildTravelChatPayload("   ", { lat: 1, lng: 2 })).toBeNull();
  });

  it("never sends birthdate or profile fields", () => {
    const payload = buildTravelChatPayload("quiet", { lat: 1, lng: 2 }) as Record<string, unknown>;
    expect(Object.keys(payload).sort()).toEqual(["language", "lat", "lng", "mode", "query"]);
  });
});

describe("pickTravelRecommendations", () => {
  it("keeps name, detail link, English reason, address and distance", () => {
    const body = {
      data: {
        recommendations: [
          {
            name: "赤坂氷川神社",
            shrine_id: 60,
            reason: "静かな杜",
            travel_reason_en: { type: "matches", text: "Matches your interests: sacred forest, quiet" },
            address: "東京都港区",
            distance_m: 1200,
          },
          { display_name: "日枝神社", id: "43" },
        ],
      },
    };
    expect(pickTravelRecommendations(body)).toEqual([
      {
        key: "shrine-60",
        name: "赤坂氷川神社",
        href: "/shrines/60",
        reason: "Matches your interests: sacred forest, quiet",
        address: "東京都港区",
        distanceM: 1200,
      },
      { key: "shrine-43", name: "日枝神社", href: "/shrines/43", reason: null, address: null, distanceM: null },
    ]);
  });

  it("never shows the Japanese reason on the English page", () => {
    const [rec] = pickTravelRecommendations({
      data: { recommendations: [{ name: "神社", shrine_id: 1, reason: "日本語の理由", travel_reason_en: null }] },
    });
    expect(rec.reason).toBeNull();
  });

  it("skips rows without a name and tolerates odd shapes", () => {
    expect(pickTravelRecommendations({ data: { recommendations: [{ shrine_id: 1 }, null, { name: "  " }] } })).toEqual([]);
    expect(pickTravelRecommendations(null)).toEqual([]);
    expect(pickTravelRecommendations({ data: {} })).toEqual([]);
  });

  it("has no detail link when the id is missing or invalid", () => {
    const [rec] = pickTravelRecommendations({ data: { recommendations: [{ name: "神社", shrine_id: "abc" }] } });
    expect(rec.href).toBeNull();
    expect(rec.key).toBe("rec-0");
  });
});
