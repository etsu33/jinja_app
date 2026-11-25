import { render, screen } from "@testing-library/react";
import CompassDirectionVisual from "../CompassDirectionVisual";

describe("CompassDirectionVisual", () => {
  it("方向をaria-labelと本文の両方で色に依らず伝える", () => {
    render(<CompassDirectionVisual referenceDirections={["北西", "西"]} />);

    expect(screen.getByRole("img", { name: "今月意識したい方向: 北西・西" })).toBeInTheDocument();
    expect(screen.getByText("今月意識したい方向: 北西・西")).toBeInTheDocument();
  });

  it("方向が空でもクラッシュせず、算出できなかった旨を伝える", () => {
    render(<CompassDirectionVisual referenceDirections={[]} />);
    expect(screen.getByRole("img", { name: "今月意識したい方向は算出されていません" })).toBeInTheDocument();
  });

  it("装飾用のセクター/ラベルはaria-hiddenで読み上げから除外される", () => {
    const { container } = render(<CompassDirectionVisual referenceDirections={["北"]} />);
    expect(container.querySelector('g[aria-hidden="true"]')).not.toBeNull();
  });
});
