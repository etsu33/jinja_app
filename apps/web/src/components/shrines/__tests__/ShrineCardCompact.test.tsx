import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ShrineCardCompact from "../ShrineCardCompact";

describe("ShrineCardCompact", () => {
  it("shows address when address is present", () => {
    render(
      <ShrineCardCompact
        name="検証神社"
        href="/shrines/1?ctx=concierge"
        address="東京都千代田区1-1-1"
        distanceM={500}
      />,
    );

    expect(screen.getByText("東京都千代田区1-1-1")).toBeInTheDocument();
    expect(screen.queryByText("500m")).not.toBeInTheDocument();
  });

  it("falls back to distance when address is missing", () => {
    render(<ShrineCardCompact name="検証神社" href="/shrines/1?ctx=concierge" address={null} distanceM={500} />);

    expect(screen.getByText("500m")).toBeInTheDocument();
  });

  it("shows no supplementary line when both address and distance are missing", () => {
    render(<ShrineCardCompact name="検証神社" address={null} distanceM={null} />);

    expect(screen.queryByText(/m$/)).not.toBeInTheDocument();
    expect(screen.queryByText(/km$/)).not.toBeInTheDocument();
  });

  it("renders a single reason block, not tags", () => {
    render(
      <ShrineCardCompact
        name="検証神社"
        href="/shrines/1?ctx=concierge"
        reason="短い理由"
        tags={["mental", "rest"]}
      />,
    );

    expect(screen.getByText("短い理由")).toBeInTheDocument();
    expect(screen.queryByText("mental")).not.toBeInTheDocument();
    expect(screen.getByTestId("recommendation-match-reason")).toBeInTheDocument();
    expect(screen.queryByTestId("recommendation-standard-reason")).not.toBeInTheDocument();
  });

  it("does not render reason when it is null", () => {
    const { container } = render(
      <ShrineCardCompact name="検証神社" href="/shrines/1?ctx=concierge" reason={null} />,
    );

    expect(container.querySelectorAll("p")).toHaveLength(0);
  });

  it("renders explanationOnlyFactText as a small separate line, distinct from the reason block", () => {
    render(
      <ShrineCardCompact
        name="検証神社"
        href="/shrines/1?ctx=concierge"
        reason="仕事運のご利益と一致するため、この神社が候補に入っています。"
        explanationOnlyFactText="須佐之男命"
      />,
    );

    const reasonBlock = screen.getByTestId("recommendation-match-reason");
    expect(reasonBlock).not.toHaveTextContent("須佐之男命");

    const explanationOnly = screen.getByTestId("recommendation-compact-explanation-only-fact");
    expect(explanationOnly).toHaveTextContent("参考情報");
    expect(explanationOnly).toHaveTextContent("須佐之男命");
  });

  it("does not render explanationOnlyFactText when absent", () => {
    render(
      <ShrineCardCompact name="検証神社" href="/shrines/1?ctx=concierge" reason="短い理由" explanationOnlyFactText={null} />,
    );

    expect(screen.queryByTestId("recommendation-compact-explanation-only-fact")).not.toBeInTheDocument();
    expect(screen.queryByText("参考情報")).not.toBeInTheDocument();
  });

  describe("Design Token参照 (Semantic Token契約、CSS文字列全体の比較はしない)", () => {
    it("radius-card / radius-image / text-primary / text-mutedを参照する", () => {
      const { container } = render(
        <ShrineCardCompact
          name="検証神社"
          href="/shrines/1?ctx=concierge"
          address="東京都千代田区1-1-1"
          reason="短い理由"
        />,
      );

      const article = container.querySelector("article");
      expect(article?.className).toContain("rounded-[var(--kt-radius-card)]");

      const imageWrap = container.querySelector("article > div > div");
      expect(imageWrap?.className).toContain("rounded-[var(--kt-radius-image)]");

      expect(screen.getByText("検証神社").className).toContain("text-[var(--kt-color-text-primary)]");
      expect(screen.getByText("東京都千代田区1-1-1").className).toContain("text-[var(--kt-color-text-muted)]");
      expect(screen.getByText("短い理由").className).toContain("text-[var(--kt-color-text-muted)]");
    });
  });
});
