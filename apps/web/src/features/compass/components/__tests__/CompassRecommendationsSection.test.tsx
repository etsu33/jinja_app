import { render, screen } from "@testing-library/react";
import CompassRecommendationsSection from "../CompassRecommendationsSection";

describe("CompassRecommendationsSection", () => {
  it("既存ShrineCardCompactへ神社別の理由をそのまま渡す（方向で上書きしない）", () => {
    render(
      <CompassRecommendationsSection
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
        recommendations={[{ shrine_id: 42, name: "北西神社" }]}
      />,
    );

    expect(screen.getByText("詳細だけ見る").closest("a")).toHaveAttribute(
      "href",
      "/shrines/42?ctx=compass",
    );
  });

  it("複数の推薦をリストとして描画する", () => {
    render(
      <CompassRecommendationsSection
        recommendations={[
          { shrine_id: 1, name: "神社A" },
          { shrine_id: 2, name: "神社B" },
        ]}
      />,
    );

    expect(screen.getByText("神社A")).toBeInTheDocument();
    expect(screen.getByText("神社B")).toBeInTheDocument();
  });
});
