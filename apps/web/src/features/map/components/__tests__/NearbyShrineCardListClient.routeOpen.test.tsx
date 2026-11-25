// /map の「経路案内」CTAが GoogleMapRouteLink 経由で route_open を記録することの検証。
// URL生成（buildGoogleMapsDirUrl）・origin仕様・destination validationは対象外で、
// ここで見るのは analytics / ShrineInteractionLog への結線のみ。
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { trackSearchEvent, trackShrineInteraction, trackNearbyFetch } = vi.hoisted(() => ({
  trackSearchEvent: vi.fn(),
  trackShrineInteraction: vi.fn(),
  trackNearbyFetch: vi.fn(),
}));

vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent, trackNearbyFetch }));
vi.mock("@/lib/api/shrineInteractions", () => ({ trackShrineInteraction }));

const mockSearchParams = new Map<string, string>();
vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: (key: string) => mockSearchParams.get(key) ?? null }),
}));

import NearbyShrineCardListClient from "../NearbyShrineCardListClient";

// 1件目: DB登録済み（shrine_id あり）/ 2件目: Google Places-only（shrine_id なし）
const results = [
  {
    place_id: "p1",
    shrine_id: 42,
    name: "登録済み神社",
    address: "東京都千代田区1-1",
    lat: 35.681236,
    lng: 139.767125,
  },
  {
    place_id: "p2",
    name: "Placesのみ神社",
    address: "東京都港区2-2",
    lat: 35.6,
    lng: 139.7,
  },
];

function mockGeolocationSuccess() {
  Object.defineProperty(navigator, "geolocation", {
    configurable: true,
    value: {
      getCurrentPosition: vi.fn((success: PositionCallback) => {
        success({
          coords: {
            latitude: 35.68,
            longitude: 139.76,
            accuracy: 10,
            altitude: null,
            altitudeAccuracy: null,
            heading: null,
            speed: null,
          },
          timestamp: Date.now(),
        } as GeolocationPosition);
      }),
    },
  });
}

async function renderWithResults() {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ results }) }));
  render(<NearbyShrineCardListClient />);
  await waitFor(() => expect(screen.getAllByRole("link", { name: "経路案内" })).toHaveLength(2));
  return screen.getAllByRole("link", { name: "経路案内" });
}

describe("/map 経路案内CTAのroute_open記録", () => {
  beforeEach(() => {
    mockSearchParams.clear();
    vi.clearAllMocks();
    mockGeolocationSuccess();
  });

  it("shrine_idを持つ候補では source=\"map\" で analytics と Backend操作記録の両方を送る", async () => {
    const [registered] = await renderWithResults();
    fireEvent.click(registered);

    expect(trackSearchEvent).toHaveBeenCalledWith(
      "route_open",
      expect.objectContaining({ source: "map", routeTarget: "google_maps", shrineId: 42 }),
    );
    expect(trackShrineInteraction).toHaveBeenCalledWith(
      expect.objectContaining({ source: "map", actionType: "route_open", shrineId: 42 }),
    );
  });

  it("Google Places-only候補ではanalyticsのみ送りBackendへは送らない", async () => {
    const [, placesOnly] = await renderWithResults();
    fireEvent.click(placesOnly);

    expect(trackSearchEvent).toHaveBeenCalledWith(
      "route_open",
      expect.objectContaining({ source: "map", shrineId: undefined }),
    );
    expect(trackShrineInteraction).not.toHaveBeenCalled();
  });

  it("tidがある場合だけthreadIdとして伝播する", async () => {
    mockSearchParams.set("tid", "1234");
    const [registered] = await renderWithResults();
    fireEvent.click(registered);

    expect(trackSearchEvent).toHaveBeenCalledWith("route_open", expect.objectContaining({ threadId: "1234" }));
    expect(trackShrineInteraction).toHaveBeenCalledWith(expect.objectContaining({ threadId: "1234" }));
  });

  it("tidがなければthreadIdを送らない", async () => {
    const [registered] = await renderWithResults();
    fireEvent.click(registered);

    // analytics payloadからは落ちる（serializerがundefinedを除外する）。
    expect(trackSearchEvent.mock.calls[0][1].threadId).toBeUndefined();
    // Backendへは既存のShrine Detailと同じくthread_id=null相当で渡る。
    expect(trackShrineInteraction.mock.calls[0][0].threadId).toBeNull();
  });

  it("URL・座標・住所をanalytics payloadへ含めない", async () => {
    const [registered] = await renderWithResults();
    fireEvent.click(registered);

    const payload = trackSearchEvent.mock.calls[0][1];
    const interaction = trackShrineInteraction.mock.calls[0][0];
    const serialized = JSON.stringify([payload, interaction]);

    expect(serialized).not.toContain("google.com");
    expect(serialized).not.toContain("35.681236");
    expect(serialized).not.toContain("139.767125");
    expect(serialized).not.toContain("東京都千代田区");
  });

  it("analyticsが例外でも外部遷移用のhrefを壊さない", async () => {
    vi.spyOn(console, "warn").mockImplementation(() => undefined);
    trackSearchEvent.mockImplementationOnce(() => {
      throw new Error("analytics unavailable");
    });
    trackShrineInteraction.mockImplementationOnce(() => {
      throw new Error("interaction unavailable");
    });

    const [registered] = await renderWithResults();
    expect(() => fireEvent.click(registered)).not.toThrow();

    expect(registered.getAttribute("href")).toContain("https://www.google.com/maps/dir/");
    expect(registered).toHaveAttribute("target", "_blank");
    vi.restoreAllMocks();
  });
});
