// /map の経路案内CTAが destination contract どおりに縮退することの検証。
// origin仕様・Nearby検索の東京駅fallback・analyticsは対象外。
import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

vi.mock("@/lib/analytics/searchEvents", () => ({
  trackSearchEvent: vi.fn(),
  trackNearbyFetch: vi.fn(),
}));
vi.mock("@/lib/api/shrineInteractions", () => ({ trackShrineInteraction: vi.fn() }));

const mockSearchParams = new Map<string, string>();
vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: (key: string) => mockSearchParams.get(key) ?? null }),
}));

import NearbyShrineCardListClient from "../NearbyShrineCardListClient";

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

async function renderWith(results: unknown[]) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ results }) }));
  render(<NearbyShrineCardListClient />);
  await waitFor(() => expect(screen.getByText("近くの神社")).toBeInTheDocument());
}

describe("/map 経路案内CTAのdestination縮退", () => {
  beforeEach(() => {
    mockSearchParams.clear();
    vi.clearAllMocks();
    mockGeolocationSuccess();
  });

  it("有効座標の候補では従来どおり座標destinationのCTAを出す（既存正常ケース維持）", async () => {
    await renderWith([
      { place_id: "p1", name: "有効神社", address: "東京都千代田区", lat: 35.681236, lng: 139.767125 },
    ]);

    const cta = await screen.findByRole("link", { name: "経路案内" });
    expect(cta.getAttribute("href")).toContain("destination=35.681236%2C139.767125");
  });

  it("座標が無効なら住所destinationへ落ちる", async () => {
    await renderWith([{ place_id: "p2", name: "座標なし神社", address: "東京都港区2-2", lat: null, lng: null }]);

    const cta = await screen.findByRole("link", { name: "経路案内" });
    expect(cta.getAttribute("href")).toContain("destination=%E6%9D%B1%E4%BA%AC%E9%83%BD%E6%B8%AF%E5%8C%BA2-2");
  });

  it("座標も住所も無ければ名前destinationへ落ちる", async () => {
    await renderWith([{ place_id: "p3", name: "名前だけ神社", address: null, lat: null, lng: null }]);

    const cta = await screen.findByRole("link", { name: "経路案内" });
    expect(cta.getAttribute("href")).toContain("destination=%E5%90%8D%E5%89%8D%E3%81%A0%E3%81%91%E7%A5%9E%E7%A4%BE");
  });

  it("range外の座標は座標として使わず次の候補へ落ちる", async () => {
    await renderWith([{ place_id: "p4", name: "範囲外神社", address: "東京都港区2-2", lat: 999, lng: 139.7 }]);

    const cta = await screen.findByRole("link", { name: "経路案内" });
    expect(cta.getAttribute("href")).not.toContain("999");
    expect(cta.getAttribute("href")).toContain("destination=%E6%9D%B1%E4%BA%AC%E9%83%BD%E6%B8%AF%E5%8C%BA2-2");
  });

  it("destination候補が全て無い候補では経路案内CTAを表示しない", async () => {
    await renderWith([{ place_id: "p5", name: "   ", address: "   ", lat: NaN, lng: NaN }]);

    // place_idがある候補なので1列目は「詳細を見る」になる（カード自体は描画される）。
    await waitFor(() => expect(screen.getByText("詳細を見る")).toBeInTheDocument());
    expect(screen.queryByRole("link", { name: "経路案内" })).not.toBeInTheDocument();
  });

  it("東京駅が暗黙のdestinationとして使われない", async () => {
    await renderWith([{ place_id: "p6", name: "", address: "", lat: null, lng: null }]);

    // place_idがある候補なので1列目は「詳細を見る」になる（カード自体は描画される）。
    await waitFor(() => expect(screen.getByText("詳細を見る")).toBeInTheDocument());
    expect(screen.queryByRole("link", { name: "経路案内" })).not.toBeInTheDocument();

    // 画面上のどのリンクにも東京駅destinationが現れないこと。
    for (const link of screen.queryAllByRole("link")) {
      const href = link.getAttribute("href") ?? "";
      expect(href).not.toContain("destination=%E6%9D%B1%E4%BA%AC%E9%A7%85");
      expect(href).not.toContain("destination=35.681236%2C139.767125");
    }
  });

  it("有効な候補と縮退する候補が混在しても、有効な方だけCTAを出す", async () => {
    await renderWith([
      { place_id: "p7", name: "有効神社", address: "東京都千代田区", lat: 35.1, lng: 139.2 },
      { place_id: "p8", name: "  ", address: "  ", lat: NaN, lng: NaN },
    ]);

    await waitFor(() => expect(screen.getAllByRole("link", { name: "経路案内" })).toHaveLength(1));
  });
});
