// /shrines/[id] の経路案内CTAが destination contract どおりに判定されることの検証。
// 座標が無効なら住所や名前へは落とさず、CTA自体を出さない（既存挙動の維持）。
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent: vi.fn() }));
vi.mock("@/lib/api/shrineInteractions", () => ({ trackShrineInteraction: vi.fn().mockResolvedValue(undefined) }));

const getShrineDetailServerMock = vi.fn();
vi.mock("@/lib/api/shrines.server", () => ({
  getShrineDetailServer: (...args: unknown[]) => getShrineDetailServerMock(...args),
}));

vi.mock("@/lib/api/concierge.server", () => ({
  getConciergeThreadServer: vi.fn(),
  getConciergeThreadsServer: vi.fn(),
}));
vi.mock("@/lib/api/billing.server", () => ({
  getBillingStatusServer: vi.fn().mockResolvedValue({ plan: "free", is_active: false }),
}));
vi.mock("@/lib/api/publicGoshuins.server", () => ({
  fetchPublicGoshuinsForShrineServer: vi.fn().mockResolvedValue([]),
}));
vi.mock("@/lib/server/favorites.server", () => ({
  getShrineFavoriteInitialState: vi.fn().mockResolvedValue({ fav: false, favorite_id: null, guestMode: true }),
}));
vi.mock("@/lib/api/shrineMeaning.server", () => ({
  fetchShrineMeaningPayloadV2Server: vi.fn().mockResolvedValue(null),
}));
vi.mock("@/lib/shrine/buildShrineDetailModel", () => ({
  buildShrineDetailModel: vi.fn().mockReturnValue({}),
}));
vi.mock("@/components/shrine/detail/ShrineDetailArticle", () => ({
  default: () => <div data-testid="shrine-detail-article-stub" />,
}));

const baseShrine = {
  id: 42,
  name_jp: "検証神社",
  address: "東京都千代田区1-1",
  goriyaku_tags: [],
  goriyaku: null,
};

async function renderWithCoords(latitude: unknown, longitude: unknown) {
  getShrineDetailServerMock.mockResolvedValue({ ...baseShrine, latitude, longitude } as unknown);
  const { default: Page } = await import("../page");
  // Page は Suspense 境界だけを返すため、境界内の async content を同じ props で解決して描画する。
  const content = Page({ params: Promise.resolve({ id: "42" }), searchParams: Promise.resolve({}) }).props.children;
  render(await content.type(content.props));
}

function routeCta() {
  return screen.queryByRole("link", { name: "Googleマップで経路案内" });
}

describe("/shrines/[id] 経路案内CTAのdestination判定", () => {
  beforeEach(() => vi.clearAllMocks());

  it("valid lat/lng ではCTAを出し座標destinationを使う（既存正常ケース維持）", async () => {
    await renderWithCoords(35.0, 139.0);
    expect(routeCta()?.getAttribute("href")).toContain("destination=35%2C139");
  });

  it("APIがstringで返す座標も数値化して判定する（既存挙動の維持）", async () => {
    await renderWithCoords("35.0", "139.0");
    expect(routeCta()?.getAttribute("href")).toContain("destination=35%2C139");
  });

  it("NaN ではCTAを出さない", async () => {
    await renderWithCoords(NaN, 139.0);
    expect(routeCta()).not.toBeInTheDocument();
  });

  it("Infinity ではCTAを出さない", async () => {
    await renderWithCoords(35.0, Infinity);
    expect(routeCta()).not.toBeInTheDocument();
  });

  it("latitude range外ではCTAを出さない", async () => {
    await renderWithCoords(90.1, 139.0);
    expect(routeCta()).not.toBeInTheDocument();
  });

  it("longitude range外ではCTAを出さない", async () => {
    await renderWithCoords(35.0, 180.1);
    expect(routeCta()).not.toBeInTheDocument();
  });

  it("latのみ / lngのみではCTAを出さない", async () => {
    await renderWithCoords(35.0, null);
    expect(routeCta()).not.toBeInTheDocument();

    vi.clearAllMocks();
    await renderWithCoords(null, 139.0);
    expect(routeCta()).not.toBeInTheDocument();
  });

  it("座標が無効でも住所・名前をdestinationへ流用しない（東京駅も使わない）", async () => {
    await renderWithCoords(null, null);
    expect(routeCta()).not.toBeInTheDocument();

    for (const link of screen.queryAllByRole("link")) {
      const href = link.getAttribute("href") ?? "";
      expect(href).not.toContain("maps/dir/");
    }
  });
});
