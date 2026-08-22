import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// docs/audit/compass-route-attribution-contract.md (PR4) found that
// route_open never received Compass ctx/recommendationInstanceId, because
// this page passed downstreamCtx/conciergeRecommendationInstanceId to
// <ShrineDetailShell> (the ancestor of GoogleMapRouteLink) instead of the
// same ctx/detailRecommendationInstanceId that the sibling Favorite/Visit/
// Reflection action boundary already received correctly. PR5 fixes only
// that propagation -- these tests exercise the real ShrineDetailShell and
// GoogleMapRouteLink (not mocked) so the actual route_open event is
// asserted end-to-end, not just the intermediate prop.

const { trackSearchEvent, trackShrineInteraction } = vi.hoisted(() => ({
  trackSearchEvent: vi.fn(),
  trackShrineInteraction: vi.fn().mockResolvedValue(undefined),
}));
vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent }));
vi.mock("@/lib/api/shrineInteractions", () => ({ trackShrineInteraction }));

const getShrineDetailServerMock = vi.fn();
vi.mock("@/lib/api/shrines.server", () => ({
  getShrineDetailServer: (...args: unknown[]) => getShrineDetailServerMock(...args),
}));

const getConciergeThreadServerMock = vi.fn();
const getConciergeThreadsServerMock = vi.fn();
vi.mock("@/lib/api/concierge.server", () => ({
  getConciergeThreadServer: (...args: unknown[]) => getConciergeThreadServerMock(...args),
  getConciergeThreadsServer: (...args: unknown[]) => getConciergeThreadsServerMock(...args),
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
  latitude: 35.0,
  longitude: 139.0,
  goriyaku_tags: [],
  goriyaku: null,
} as unknown;

async function renderPage(searchParams: Record<string, string>) {
  const { default: Page } = await import("../page");
  const element = await Page({
    params: Promise.resolve({ id: "42" }),
    searchParams: Promise.resolve(searchParams),
  });
  render(element);
}

function routeOpenPayload() {
  const call = trackSearchEvent.mock.calls.find(([name]) => name === "route_open");
  return call?.[1];
}

describe("/shrines/[id] page -- route_open Compass attribution (PR5)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getShrineDetailServerMock.mockResolvedValue(baseShrine);
  });

  it("Compass起点: route_openへctx=compassと同じrecommendationInstanceIdを渡す", async () => {
    await renderPage({
      ctx: "compass",
      recommendation_instance_id: "compass01",
      recommendation_rank: "2",
    });

    fireEvent.click(screen.getByRole("link", { name: "Googleマップで経路案内" }));

    expect(routeOpenPayload()).toMatchObject({
      source: "shrine_detail",
      ctx: "compass",
      recommendationInstanceId: "compass01",
      shrineId: 42,
    });
  });

  it("直接アクセス(ctx無し): route_openはctx/recommendationInstanceIdを捏造しない", async () => {
    await renderPage({});

    fireEvent.click(screen.getByRole("link", { name: "Googleマップで経路案内" }));

    expect(routeOpenPayload()).toMatchObject({
      ctx: null,
      recommendationInstanceId: null,
      shrineId: 42,
    });
  });

  it("Concierge起点: 既存のroute_open帰属は変化しない(回帰なし)", async () => {
    getConciergeThreadServerMock.mockResolvedValue({
      id: 768,
      recommendations: [{ shrine_id: 42, id: 42, recommendation_instance_id: "concierge99" }],
    });
    getConciergeThreadsServerMock.mockResolvedValue([]);

    await renderPage({ ctx: "concierge", tid: "768" });

    fireEvent.click(screen.getByRole("link", { name: "Googleマップで経路案内" }));

    expect(routeOpenPayload()).toMatchObject({
      ctx: "concierge",
      recommendationInstanceId: "concierge99",
      shrineId: 42,
    });
  });

  it("Compass起点でもshrine_detail_view(既存の正しい兄弟属性)は変化しない", async () => {
    await renderPage({
      ctx: "compass",
      recommendation_instance_id: "compass01",
      recommendation_rank: "2",
    });

    expect(trackSearchEvent).toHaveBeenCalledWith(
      "shrine_detail_view",
      expect.objectContaining({
        source: "compass",
        shrineId: 42,
        recommendationInstanceId: "compass01",
        recommendationRank: 2,
      }),
    );
  });
});
