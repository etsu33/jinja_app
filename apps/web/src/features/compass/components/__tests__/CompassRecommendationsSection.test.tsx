import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

const analyticsMocks = vi.hoisted(() => ({
  trackCardEvent: vi.fn(),
  trackSearchEvent: vi.fn(),
}));
vi.mock("@/lib/analytics/cardEvents", () => ({ trackCardEvent: analyticsMocks.trackCardEvent }));
vi.mock("@/lib/analytics/searchEvents", () => ({ trackSearchEvent: analyticsMocks.trackSearchEvent }));
import CompassRecommendationsSection from "../CompassRecommendationsSection";

describe("CompassRecommendationsSection", () => {
  beforeEach(() => {
    analyticsMocks.trackCardEvent.mockClear();
    analyticsMocks.trackSearchEvent.mockClear();
  });

  it("既存ShrineCardCompactへ神社別の理由をそのまま渡す（方向で上書きしない）", () => {
    render(
      <CompassRecommendationsSection
        recommendationInstanceId="compass01"
        recommendations={[
          {
            shrine_id: 1,
            name: "北西神社",
            address: "東京都千代田区",
            distance_m: 1200,
            reason: "仕事運とのご利益一致",
          },
        ]}
      />,
    );

    expect(screen.getByText("この方向の参拝候補")).toBeInTheDocument();
    expect(screen.getByText("北西神社")).toBeInTheDocument();
    expect(screen.getByTestId("recommendation-match-reason")).toHaveTextContent("仕事運とのご利益一致");
  });

  it("Shrine Detailへのリンクはctx=compassを付与する", () => {
    render(
      <CompassRecommendationsSection
        recommendationInstanceId="compass01"
        recommendations={[{ shrine_id: 42, name: "北西神社" }]}
      />,
    );

    expect(screen.getByText("詳細だけ見る").closest("a")).toHaveAttribute(
      "href",
      "/shrines/42?ctx=compass&recommendation_instance_id=compass01&recommendation_rank=1",
    );
  });

  it("複数の推薦をリストとして描画する", () => {
    render(
      <CompassRecommendationsSection
        recommendationInstanceId="compass01"
        recommendations={[
          { shrine_id: 1, name: "神社A" },
          { shrine_id: 2, name: "神社B" },
        ]}
      />,
    );

    expect(screen.getByText("神社A")).toBeInTheDocument();
    expect(screen.getByText("神社B")).toBeInTheDocument();
  });

  it("共通impression/clickイベントへ同じCompass attributionを渡す", () => {
    render(
      <CompassRecommendationsSection
        recommendationInstanceId="compass01"
        recommendations={[
          { shrine_id: 10, name: "神社A" },
          { shrine_id: 20, name: "神社B" },
        ]}
      />,
    );

    expect(analyticsMocks.trackCardEvent).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        event: "card_view",
        source: "compass",
        shrineId: 20,
        recommendationRank: 2,
        recommendationInstanceId: "compass01",
      }),
    );

    fireEvent.click(screen.getAllByRole("link", { name: "詳細だけ見る" })[1]);
    expect(analyticsMocks.trackSearchEvent).toHaveBeenCalledWith("shrine_detail_transition", {
      source: "compass",
      shrineId: 20,
      recommendationRank: 2,
      recommendationInstanceId: "compass01",
      position: "compact",
    });
  });
});
