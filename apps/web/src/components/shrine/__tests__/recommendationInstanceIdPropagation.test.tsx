import { fireEvent, render } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// docs/audit/recommendation-instance-identity-propagation.md:
// detail -> route/save/visit/reflection must carry the identical recommendationInstanceId
// that was resolved server-side from the thread snapshot (page.tsx). Direct detail access
// (no recommendationInstanceId prop) must never synthesize one.

const { trackSearchEvent, trackShrineInteraction } = vi.hoisted(() => ({
  trackSearchEvent: vi.fn(),
  trackShrineInteraction: vi.fn(),
}));
vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent }));
vi.mock("@/lib/api/shrineInteractions", () => ({ trackShrineInteraction }));

import { ShrineDetailViewTracker } from "../ShrineDetailViewTracker";
import GoogleMapRouteLink from "../GoogleMapRouteLink";

const routeHref = "https://www.google.com/maps/dir/?api=1&destination=35,139";

describe("Recommendation Instance Identity: detail -> route", () => {
  beforeEach(() => {
    trackSearchEvent.mockClear();
    trackShrineInteraction.mockClear();
  });

  it("ShrineDetailViewTrackerとGoogleMapRouteLinkが同じrecommendationInstanceIdを送る", () => {
    const recommendationInstanceId = "a1b2c3d4";

    render(
      <ShrineDetailViewTracker
        shrineId={42}
        ctx="concierge"
        tid="768"
        recommendationInstanceId={recommendationInstanceId}
      />,
    );

    expect(trackSearchEvent).toHaveBeenCalledWith(
      "shrine_detail_view",
      expect.objectContaining({ shrineId: 42, recommendationInstanceId }),
    );
    expect(trackShrineInteraction).toHaveBeenCalledWith(
      expect.objectContaining({
        shrineId: 42,
        actionType: "detail_view",
        metadata: expect.objectContaining({ recommendation_instance_id: recommendationInstanceId }),
      }),
    );

    const { getByRole } = render(
      <GoogleMapRouteLink
        href={routeHref}
        label="Googleマップで経路案内"
        shrineId={42}
        ctx="concierge"
        tid="768"
        recommendationInstanceId={recommendationInstanceId}
      />,
    );
    fireEvent.click(getByRole("link", { name: "Googleマップで経路案内" }));

    const routeOpenCall = trackSearchEvent.mock.calls.find(([name]) => name === "route_open");
    expect(routeOpenCall?.[1]).toMatchObject({ shrineId: 42, recommendationInstanceId });
  });

  it("Direct detail access(recommendationInstanceId無し)ではidentityを合成せずnullのまま送る", () => {
    render(<ShrineDetailViewTracker shrineId={7} ctx={null} tid={null} />);

    expect(trackSearchEvent).toHaveBeenCalledWith(
      "shrine_detail_view",
      expect.objectContaining({ recommendationInstanceId: null }),
    );
    expect(trackShrineInteraction).toHaveBeenCalledWith(
      expect.objectContaining({
        metadata: expect.objectContaining({ recommendation_instance_id: null }),
      }),
    );
  });
});
