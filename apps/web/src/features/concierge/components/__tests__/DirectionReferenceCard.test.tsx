import { render, screen } from "@testing-library/react";
import DirectionReferenceCard from "../DirectionReferenceCard";

const reference = {
  visit_date: "2026-09-15",
  actual_direction: "東",
  reference_directions: ["東", "北西"],
  matched: true,
  calculation_method: "annual_monthly_kyusei_v1" as const,
  note: "年盤と月盤による参考情報です。日盤は使用していません。",
};

describe("DirectionReferenceCard", () => {
  it("Backend契約がある場合だけ非断定的な方位情報を表示する", () => {
    const { rerender } = render(<DirectionReferenceCard reference={reference} />);
    expect(screen.getByRole("heading", { level: 3, name: "方位の参考情報" })).toBeInTheDocument();
    expect(screen.getByText("現在地から見た方角が、予定日の参考方位と一致しています。")).toBeInTheDocument();
    expect(screen.queryByText(/運気が上がる|行くべき|吉方位/)).not.toBeInTheDocument();

    rerender(<DirectionReferenceCard reference={null} />);
    expect(screen.queryByText("方位の参考情報")).not.toBeInTheDocument();
  });

  it("不一致を優劣ではなく差異として表示する", () => {
    render(<DirectionReferenceCard reference={{ ...reference, matched: false }} />);
    expect(screen.getByText("現在地から見た方角は、予定日の参考方位とは異なります。")).toBeInTheDocument();
  });
});
