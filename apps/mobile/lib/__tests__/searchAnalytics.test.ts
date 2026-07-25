import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { vi } from "vitest";

// __DEV__ は Metro/React Native が注入するグローバルで、vitest実行環境には存在しないため定義する。
(globalThis as unknown as { __DEV__: boolean }).__DEV__ = false;

import { setAnalyticsProvider, type AnalyticsProvider } from "../analytics";
import {
  trackMapMarkerSelect,
  trackRouteOpen,
  trackSearchEntryClick,
  trackSearchScreenView,
  trackShrineCardClick,
} from "../searchAnalytics";

describe("searchAnalytics", () => {
  const trackSpy = vi.fn();

  beforeEach(() => {
    const customProvider: AnalyticsProvider = { track: trackSpy };
    setAnalyticsProvider(customProvider);
  });

  afterEach(() => {
    trackSpy.mockClear();
    setAnalyticsProvider(null);
  });

  it("trackSearchEntryClickはsource:home/platform:mobileのみを送る", () => {
    trackSearchEntryClick();

    expect(trackSpy).toHaveBeenCalledWith("search_entry_click", { source: "home", platform: "mobile" });
    expect(trackSpy).toHaveBeenCalledTimes(1);
  });

  it("trackSearchScreenViewはsource:mobile_search/platform:mobileを送る", () => {
    trackSearchScreenView();

    expect(trackSpy).toHaveBeenCalledWith("search_screen_view", { source: "mobile_search", platform: "mobile" });
  });

  it("trackShrineCardClickはposition:listでsource:mobile_searchを送る", () => {
    trackShrineCardClick({ shrineId: "1", position: "list" });

    expect(trackSpy).toHaveBeenCalledWith("shrine_card_click", {
      source: "mobile_search",
      shrineId: "1",
      position: "list",
      platform: "mobile",
    });
  });

  it("trackShrineCardClickはposition:popularでsource:mobile_searchを送り、一覧と区別できる", () => {
    trackShrineCardClick({ shrineId: "2", position: "popular" });

    expect(trackSpy).toHaveBeenCalledWith("shrine_card_click", {
      source: "mobile_search",
      shrineId: "2",
      position: "popular",
      platform: "mobile",
    });
  });

  it("trackShrineCardClickはposition:mapでsource:mapを送る(選択カードからの詳細遷移)", () => {
    trackShrineCardClick({ shrineId: "3", position: "map" });

    expect(trackSpy).toHaveBeenCalledWith("shrine_card_click", {
      source: "map",
      shrineId: "3",
      position: "map",
      platform: "mobile",
    });
  });

  it("trackMapMarkerSelectはsource:map/position:mapを送り、shrine_card_clickとは別Event名である", () => {
    trackMapMarkerSelect({ shrineId: "4" });

    expect(trackSpy).toHaveBeenCalledWith("map_marker_select", {
      source: "map",
      shrineId: "4",
      position: "map",
      platform: "mobile",
    });
    expect(trackSpy.mock.calls[0][0]).not.toBe("shrine_card_click");
  });

  it("trackRouteOpenはsource:shrine_detail/routeTarget:google_mapsを送る(URL・住所・緯度経度は含まない)", () => {
    trackRouteOpen({ shrineId: 5 });

    expect(trackSpy).toHaveBeenCalledWith("route_open", {
      source: "shrine_detail",
      shrineId: 5,
      routeTarget: "google_maps",
      platform: "mobile",
    });
    const payload = trackSpy.mock.calls[0][1] as Record<string, unknown>;
    expect(payload).not.toHaveProperty("url");
    expect(payload).not.toHaveProperty("address");
    expect(payload).not.toHaveProperty("latitude");
    expect(payload).not.toHaveProperty("longitude");
  });

  it("全EventのPayloadはprimitive値のみで構成される(nested object・配列を含まない)", () => {
    trackSearchEntryClick();
    trackSearchScreenView();
    trackShrineCardClick({ shrineId: "1", position: "list" });
    trackMapMarkerSelect({ shrineId: "1" });
    trackRouteOpen({ shrineId: "1" });

    for (const call of trackSpy.mock.calls) {
      const payload = call[1] as Record<string, unknown>;
      for (const value of Object.values(payload)) {
        expect(value === null || ["string", "number", "boolean"].includes(typeof value)).toBe(true);
      }
    }
  });

  it("禁止属性(相談文・検索語・住所・緯度経度・style URL・APIキー等)を一切含まない", () => {
    trackSearchEntryClick();
    trackSearchScreenView();
    trackShrineCardClick({ shrineId: "1", position: "popular" });
    trackMapMarkerSelect({ shrineId: "1" });
    trackRouteOpen({ shrineId: "1" });

    const forbiddenKeys = [
      "query",
      "consultationText",
      "address",
      "stationName",
      "prefecture",
      "latitude",
      "longitude",
      "birthdate",
      "plannedVisitDate",
      "supportText",
      "styleUrl",
      "apiKey",
      "mapTilerKey",
      "googleMapsUrl",
      "username",
      "email",
      "token",
      "cookie",
    ];

    for (const call of trackSpy.mock.calls) {
      const payload = call[1] as Record<string, unknown>;
      for (const key of forbiddenKeys) {
        expect(payload).not.toHaveProperty(key);
      }
    }
  });
});
