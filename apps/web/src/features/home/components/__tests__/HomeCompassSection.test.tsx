import { render, screen } from "@testing-library/react";
import { HomeCompassSection } from "../HomeCompassSection";

describe("HomeCompassSection", () => {
  it("Compassの入口として題名・説明・CTAを表示する", () => {
    render(<HomeCompassSection />);

    expect(screen.getByText("今月から探す")).toBeInTheDocument();
    expect(screen.getByText("今月の流れと方向から、参拝のきっかけを見つけます。")).toBeInTheDocument();
  });

  it("CTAは/compassへのプレーンなリンクで、クエリパラメータを付与しない", () => {
    render(<HomeCompassSection />);

    const link = screen.getByRole("link", { name: "参拝コンパスを見る" });
    expect(link).toHaveAttribute("href", "/compass");
  });

  it("既存SUB PATHSカードと同型の視覚トークンを使う（新しい色・radiusを発明しない）", () => {
    const { container } = render(<HomeCompassSection />);
    const card = container.firstElementChild;
    expect(card?.className).toContain("rounded-3xl");
    expect(card?.className).toContain("border-stone-200/25");
  });
});
